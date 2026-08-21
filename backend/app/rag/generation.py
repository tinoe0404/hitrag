# Generation Module for HITRAG (Phase 17 → Phase 18: Grounded Answers)
"""
Generation utilities that take retrieved chunks, build a prompt, and call the Gemini LLM.

We deliberately keep generation separate from the embedding client because the two APIs have
different request shapes, model names, and error handling semantics.

The module mirrors the embedding module's disciplined retry/backoff logic and defines a
clear ``GenerationError`` exception type.

Phase 18 adds grounded‑answer enforcement:
- The prompt now requires a JSON response with ``status`` and ``answer`` fields.
- ``generate_answer`` returns a ``GenerationResult`` dataclass instead of a plain string.
- A robust ``parse_model_output`` function handles well‑formed JSON, JSON buried in
  surrounding text (regex extraction), and completely unparseable output.

**Why JSON instead of a delimiter‑based format?**
JSON is unambiguous, universally supported by every language, trivially parseable with
``json.loads``, and naturally extensible (we can add a ``citations`` field in Phase 19
without changing the parsing skeleton).  Delimiter‑based formats (e.g. ``STATUS: …\\n---\\nANSWER: …``)
are fragile when the answer itself contains the delimiter characters, and require custom
parsing logic that doesn't generalize.

Future phases will add citation extraction (Phase 19) and the public ``/chat`` endpoint
(Phase 20).
"""

import json
import re
import time
import logging
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional

from google import genai

from app.core.config import settings
from sqlalchemy import select
from app.models.chunk import Chunk
from app.db.session import SessionLocal
logger = logging.getLogger("hitrag.generation")

# ---------------------------------------------------------------------------
# Configuration – choose a balanced Gemini model
# ---------------------------------------------------------------------------
GENERATION_MODEL = "gemini-3.6-flash"  # fast, low‑latency, cost‑effective model
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1.0

# ---------------------------------------------------------------------------
# Caller‑facing message for the NOT_ENOUGH_INFORMATION status.
# This is a legitimate, expected response – not an error.
# ---------------------------------------------------------------------------
NOT_ENOUGH_INFO_MESSAGE = (
    "I don't have enough information in the available documents to answer that."
)

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class GenerationResult:
    """Structured result from ``generate_answer``.

    ``status`` is one of:
      - ``"ANSWERED"`` – the model found sufficient context and produced an answer.
      - ``"NOT_ENOUGH_INFORMATION"`` – the model determined the context does not
        support a confident answer.  This is a normal, expected outcome.
      - ``"PARSE_ERROR"`` – the model's raw output could not be parsed as valid
        JSON with the expected schema.  Internally distinct from
        ``NOT_ENOUGH_INFORMATION`` so callers can log / metric it separately,
        but user‑facing text may be identical.
    """
    status: str
    answer: str
    citations: List[Dict[str, Any]] = field(default_factory=list)


class GenerationError(Exception):
    """Raised when the Gemini generation API fails after retries."""
    pass


def _get_client() -> genai.Client:
    """Create a Gemini client using the API key from settings.

    Mirrors the embedding module's client creation – raises ``GenerationError`` if the key is
    missing so that callers get a clear, typed exception.
    """
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise GenerationError(
            'GEMINI_API_KEY is not set. Add it to your .env file: GEMINI_API_KEY="your-api-key"'
        )
    return genai.Client(api_key=api_key)

# ---------------------------------------------------------------------------
# Prompt builder (Phase 18 – grounded JSON format)
# ---------------------------------------------------------------------------

def build_prompt(query: str, chunks: List[Dict[str, Any]]) -> str:
    """Create a prompt that instructs the LLM to answer using only the provided context.

    The model is instructed to respond with a single JSON object containing:
      - ``"status"``: ``"ANSWERED"`` or ``"NOT_ENOUGH_INFORMATION"``
      - ``"answer"``: the answer text (empty string when status is NOT_ENOUGH_INFORMATION)

    The prompt explicitly forbids hedge‑then‑answer behaviour: if the context
    doesn't fully support a confident answer, the model must refuse rather than
    partially answer.
    """
    lines: List[str] = []

    # System instruction block
    lines.append(
        "You are a strict question‑answering assistant. "
        "Answer the following question using ONLY the provided context. "
        "Do not rely on any external or prior knowledge."
    )
    lines.append("")
    lines.append("## Response rules")
    lines.append(
        "1. If the context **fully and confidently** supports an answer, respond with:"
    )
    lines.append('   {"status": "ANSWERED", "answer": "<your answer>"}')
    lines.append(
        "2. If the context does NOT contain enough information to answer the question "
        "completely and confidently, respond with:"
    )
    lines.append('   {"status": "NOT_ENOUGH_INFORMATION", "answer": ""}')
    lines.append(
        "3. Do NOT hedge. Do NOT partially answer when you are unsure. "
        "If you cannot fully answer, choose NOT_ENOUGH_INFORMATION."
    )
    lines.append("")
    lines.append(
        "**IMPORTANT:** Respond *only* with the JSON object on a single line. "
        "No surrounding text, no markdown fences, no explanation outside the JSON."
    )
    lines.append("")
    lines.append(f"Question: {query}")
    lines.append("")
    lines.append("Context:")
    lines.append("----")
    for i, chunk in enumerate(chunks, start=1):
        title = chunk.get("document_title", "<unknown doc>")
        page = chunk.get("page_number", "?")
        content = chunk.get("content", "")
        lines.append(f"{i}. {title} (Page {page})")
        lines.append(content.strip())
        lines.append("----")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# Response parsing (Phase 18)
# ---------------------------------------------------------------------------

# Pre‑compiled regex to extract the first JSON object from surrounding text.
_JSON_OBJECT_RE = re.compile(r"\{[^{}]*\}", re.DOTALL)

_VALID_STATUSES = {"ANSWERED", "NOT_ENOUGH_INFORMATION"}


def parse_model_output(raw: str) -> GenerationResult:
    """Parse the model's raw text into a ``GenerationResult``.

    Strategy (three tiers):
    1. Try ``json.loads`` on the stripped output directly.
    2. If that fails, use a regex to extract the first ``{…}`` block and parse it.
    3. If both fail, return ``status="PARSE_ERROR"`` – never silently guess
       ``ANSWERED`` when the format didn't parse.

    Even after successful JSON parsing, we validate that ``status`` is one of the
    two expected values and that the required keys are present.
    """
    stripped = raw.strip()

    # --- Tier 1: direct parse ---
    parsed = _try_json_loads(stripped)

    # --- Tier 2: regex extraction ---
    if parsed is None:
        match = _JSON_OBJECT_RE.search(stripped)
        if match:
            parsed = _try_json_loads(match.group(0))

    # --- Tier 3: give up ---
    if parsed is None:
        logger.warning("parse_model_output: could not extract valid JSON from model output.")
        return GenerationResult(status="PARSE_ERROR", answer="")

    # Validate schema
    status = parsed.get("status", "").strip().upper()
    answer = parsed.get("answer", "")

    if status not in _VALID_STATUSES:
        logger.warning(
            "parse_model_output: unexpected status '%s' in model output.", status
        )
        return GenerationResult(status="PARSE_ERROR", answer="")

    # If model says NOT_ENOUGH_INFORMATION but still stuffed an answer in, clear it.
    if status == "NOT_ENOUGH_INFORMATION":
        answer = ""

    return GenerationResult(status=status, answer=answer.strip() if answer else "")


def _try_json_loads(text: str) -> Optional[dict]:
    """Attempt ``json.loads``; return ``None`` on any failure instead of raising."""
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    return None


# ---------------------------------------------------------------------------
# Gemini API call with retry
# ---------------------------------------------------------------------------

def _call_generation_api(client: genai.Client, prompt: str) -> str:
    """Invoke Gemini generation with exponential backoff retry logic.

    Returns the plain text response from the model. Any non‑retriable error raises ``GenerationError``.
    """
    backoff = INITIAL_BACKOFF_SECONDS
    last_error: Optional[Exception] = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=GENERATION_MODEL,
                contents=prompt,
            )
            if response.candidates and response.candidates[0].content.parts:
                return response.candidates[0].content.parts[0].text.strip()
            else:
                raise GenerationError("Empty response from Gemini generation API.")
        except Exception as e:
            last_error = e
            err_str = str(e).lower()
            retryable = (
                "429" in err_str
                or "rate" in err_str
                or "timeout" in err_str
                or "unavailable" in err_str
                or "connection" in err_str
            )
            if retryable and attempt < MAX_RETRIES:
                logger.warning(
                    f"Generation API error (attempt {attempt}/{MAX_RETRIES}), retrying in {backoff}s: {e}"
                )
                time.sleep(backoff)
                backoff *= 2
            else:
                break
    raise GenerationError(
        f"Generation failed after {MAX_RETRIES} attempts. Last error: {type(last_error).__name__}: {last_error}"
    )

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_answer(query: str, chunks: List[Dict[str, Any]]) -> GenerationResult:
    """High‑level API used by the backend to produce a grounded answer.

    Returns a ``GenerationResult`` with one of three statuses:
      - ``ANSWERED`` – context was sufficient; ``answer`` contains the response.
      - ``NOT_ENOUGH_INFORMATION`` – context was insufficient; this is a normal,
        expected outcome (not an error).
      - ``PARSE_ERROR`` – the model's output could not be parsed.  Internally
        distinct so it can be logged/metriced, but callers may present the same
        user‑facing text as ``NOT_ENOUGH_INFORMATION``.

    If ``chunks`` is empty we short‑circuit with ``NOT_ENOUGH_INFORMATION``
    without calling the model – there is no context to ground an answer on.
    """
    if not chunks:
        logger.info("generate_answer called with empty context – short‑circuiting to NOT_ENOUGH_INFORMATION.")
        return GenerationResult(status="NOT_ENOUGH_INFORMATION", answer="", citations=[])

    prompt = build_prompt(query, chunks)
    client = _get_client()
    raw_output = _call_generation_api(client, prompt)
    result = parse_model_output(raw_output)

    if result.status == "PARSE_ERROR":
        logger.warning("generate_answer: model output failed to parse. Raw: %s", raw_output[:500])
    elif result.status == "NOT_ENOUGH_INFORMATION":
        # Normal, expected outcome – log at INFO, not WARNING.
        logger.info("generate_answer: model classified query as NOT_ENOUGH_INFORMATION.")
    elif result.status == "ANSWERED":
        # -----------------------------------------------------------------------
        # CITATION POLICY LIMITATION NOTE:
        # In this phase, we implement a simplified attribution model. We cite every
        # chunk that was included in the prompt's context for an ANSWERED response.
        # We do not attempt to verify which specific chunk the model actually
        # drew from for which part of the generated text (fine-grained attribution).
        # This is a known limitation of the current citation tracking system.
        # -----------------------------------------------------------------------
        seen_citations = {}
        for chunk in chunks:
            doc_id = chunk.get("document_id")
            page_num = chunk.get("page_number")
            # Deduplicate citations by (document_id, page_number)
            key = (doc_id, page_num)
            chunk_id = chunk.get("chunk_id")
            if key not in seen_citations:
                seen_citations[key] = {
                    "document_id": doc_id,
                    "document_title": chunk.get("document_title", "<unknown doc>"),
                    "page_number": page_num,
                    "chunk_id": chunk_id,
                    "chunk_ids": [chunk_id] if chunk_id is not None else []
                }
            else:
                # Keep underlying chunk_ids for traceability
                if chunk_id is not None:
                    seen_citations[key]["chunk_ids"].append(chunk_id)

        # Validate chunk IDs exist in DB to avoid citing non‑existent chunks
        input_chunk_ids = [c.get("chunk_id") for c in chunks if c.get("chunk_id") is not None]
        existing_ids: set[int] = set()
        if input_chunk_ids:
            db = SessionLocal()
            try:
                existing = db.scalars(select(Chunk.id).where(Chunk.id.in_(input_chunk_ids))).all()
                existing_ids = set(existing)
            finally:
                db.close()
        filtered_citations = []
        for citation in seen_citations.values():
            cid = citation.get("chunk_id")
            if cid is None or cid in existing_ids:
                filtered_citations.append(citation)
        result.citations = filtered_citations

    return result


__all__ = [
    "GenerationError",
    "GenerationResult",
    "NOT_ENOUGH_INFO_MESSAGE",
    "build_prompt",
    "generate_answer",
    "parse_model_output",
]

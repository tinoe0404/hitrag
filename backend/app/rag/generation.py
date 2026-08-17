# Generation Module for HITRAG (Phase 17)
"""
Generation utilities that take retrieved chunks, build a prompt, and call the Gemini LLM.

We deliberately keep generation separate from the embedding client because the two APIs have
different request shapes, model names, and error handling semantics.

The module mirrors the embedding module's disciplined retry/backoff logic and defines a
clear ``GenerationError`` exception type.

Only the minimal functionality needed for Phase 17 is provided – a prompt builder, the
``generate_answer`` function, and short‑circuit handling for empty context.

Future phases will extend this with grounding enforcement, citation extraction, and the
public ``/chat`` endpoint.
"""

import time
import logging
from typing import List, Dict, Any, Optional

from google import genai

from app.core.config import settings

logger = logging.getLogger("hitrag.generation")

# ---------------------------------------------------------------------------
# Configuration – choose a balanced Gemini model
# ---------------------------------------------------------------------------
GENERATION_MODEL = "gemini-3.6-flash"  # fast, low‑latency, cost‑effective model
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1.0

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

def build_prompt(query: str, chunks: List[Dict[str, Any]]) -> str:
    """Create a prompt that instructs the LLM to answer using only the provided context.

    The prompt format:
    Answer the following question **using ONLY the provided context**. Do not rely on any external knowledge.
    If the answer cannot be derived from the context, respond with "I don't know based on the given information."

    Question: <query>

    Context:
    ----
    1. <Document Title> (Page <page_number>)
    <chunk content>
    ----
    ...
    """
    lines = []
    lines.append(
        "Answer the following question **using ONLY the provided context**. Do not rely on any external knowledge. If the answer cannot be derived from the context, respond with \"I don't know based on the given information.\""
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

def generate_answer(query: str, chunks: List[Dict[str, Any]]) -> str:
    """High‑level API used by the backend to produce an answer.

    * If ``chunks`` is empty we short‑circuit and return a clear message.
    * Otherwise we build the prompt, call the Gemini generation endpoint and return the answer text.
    """
    if not chunks:
        logger.info("generate_answer called with empty context – returning placeholder.")
        return "No context available for this query."
    prompt = build_prompt(query, chunks)
    client = _get_client()
    return _call_generation_api(client, prompt)

__all__ = ["GenerationError", "build_prompt", "generate_answer"]

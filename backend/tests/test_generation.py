import json
import pytest
from unittest.mock import patch, MagicMock

from app.rag.generation import (
    generate_answer,
    build_prompt,
    parse_model_output,
    GenerationError,
    GenerationResult,
    NOT_ENOUGH_INFO_MESSAGE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _chunk(title="Doc", page=1, content="Sample content."):
    """Create a minimal chunk dict for testing."""
    return {"document_title": title, "page_number": page, "content": content}


def _mock_gemini_text(text: str):
    """Return a MagicMock that simulates a Gemini response containing ``text``."""
    mock_part = MagicMock()
    mock_part.text = text
    mock_candidate = MagicMock()
    mock_candidate.content.parts = [mock_part]
    mock_response = MagicMock()
    mock_response.candidates = [mock_candidate]
    return mock_response


# ---------------------------------------------------------------------------
# Prompt tests
# ---------------------------------------------------------------------------

def test_build_prompt_contains_context_and_instruction():
    query = "What is the policy?"
    chunks = [_chunk("Policy Doc", 2, "The policy states X.")]
    prompt = build_prompt(query, chunks)
    assert "using ONLY the provided context" in prompt
    assert "Question: What is the policy?" in prompt
    assert "1. Policy Doc (Page 2)" in prompt
    assert "The policy states X." in prompt


def test_build_prompt_includes_json_format_instruction():
    prompt = build_prompt("test?", [_chunk()])
    assert '"status"' in prompt
    assert "ANSWERED" in prompt
    assert "NOT_ENOUGH_INFORMATION" in prompt
    assert "IMPORTANT" in prompt


# ---------------------------------------------------------------------------
# parse_model_output tests (Phase 18 requirement §6)
# ---------------------------------------------------------------------------

def test_parse_well_formed_answered():
    """Well‑formed ANSWERED JSON parses correctly."""
    raw = '{"status": "ANSWERED", "answer": "The grading scale is A–F."}'
    result = parse_model_output(raw)
    assert result.status == "ANSWERED"
    assert result.answer == "The grading scale is A–F."


def test_parse_well_formed_not_enough_info():
    """Well‑formed NOT_ENOUGH_INFORMATION JSON parses correctly."""
    raw = '{"status": "NOT_ENOUGH_INFORMATION", "answer": ""}'
    result = parse_model_output(raw)
    assert result.status == "NOT_ENOUGH_INFORMATION"
    assert result.answer == ""


def test_parse_not_enough_info_clears_sneaky_answer():
    """If model says NOT_ENOUGH_INFORMATION but stuffs an answer, we clear it."""
    raw = '{"status": "NOT_ENOUGH_INFORMATION", "answer": "Well actually maybe..."}'
    result = parse_model_output(raw)
    assert result.status == "NOT_ENOUGH_INFORMATION"
    assert result.answer == ""


def test_parse_json_with_surrounding_text():
    """JSON embedded in surrounding prose is extracted via regex fallback."""
    raw = 'Sure! Here is your answer:\n{"status": "ANSWERED", "answer": "42"}\nHope that helps!'
    result = parse_model_output(raw)
    assert result.status == "ANSWERED"
    assert result.answer == "42"


def test_parse_malformed_non_json_returns_parse_error():
    """Completely non‑JSON output is caught as PARSE_ERROR, not misclassified."""
    raw = "I'm sorry, I can't answer that based on the context."
    result = parse_model_output(raw)
    assert result.status == "PARSE_ERROR"
    assert result.answer == ""


def test_parse_invalid_status_returns_parse_error():
    """JSON with an unexpected status value returns PARSE_ERROR."""
    raw = '{"status": "MAYBE", "answer": "could be"}'
    result = parse_model_output(raw)
    assert result.status == "PARSE_ERROR"


def test_parse_empty_string_returns_parse_error():
    """Empty string returns PARSE_ERROR."""
    result = parse_model_output("")
    assert result.status == "PARSE_ERROR"


# ---------------------------------------------------------------------------
# generate_answer integration tests (mocked Gemini)
# ---------------------------------------------------------------------------

@patch("app.rag.generation._get_client")
def test_generate_answer_answered(mock_get_client):
    """A well‑formed ANSWERED response from the model is returned correctly."""
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = _mock_gemini_text(
        '{"status": "ANSWERED", "answer": "Generated answer."}'
    )
    mock_get_client.return_value = mock_client

    result = generate_answer("Explain X", [_chunk(content="X is defined as Y.")])
    assert isinstance(result, GenerationResult)
    assert result.status == "ANSWERED"
    assert result.answer == "Generated answer."
    # Verify model name
    _, kwargs = mock_client.models.generate_content.call_args
    assert kwargs["model"] == "gemini-3.6-flash"


@patch("app.rag.generation._get_client")
def test_generate_answer_not_enough_info(mock_get_client):
    """Model returning NOT_ENOUGH_INFORMATION is parsed correctly."""
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = _mock_gemini_text(
        '{"status": "NOT_ENOUGH_INFORMATION", "answer": ""}'
    )
    mock_get_client.return_value = mock_client

    result = generate_answer("Unrelated question?", [_chunk()])
    assert result.status == "NOT_ENOUGH_INFORMATION"
    assert result.answer == ""


@patch("app.rag.generation._get_client")
def test_generate_answer_parse_error_on_malformed(mock_get_client):
    """Malformed model output → PARSE_ERROR, not silently ANSWERED."""
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = _mock_gemini_text(
        "Here is your answer: the policy says blah blah."
    )
    mock_get_client.return_value = mock_client

    result = generate_answer("What is the policy?", [_chunk()])
    assert result.status == "PARSE_ERROR"
    assert result.answer == ""


def test_generate_answer_empty_chunks_returns_not_enough_info():
    """Empty chunks (Phase 17's short‑circuit) returns NOT_ENOUGH_INFORMATION,
    not a raw string and not skipping classification entirely."""
    result = generate_answer("any query", [])
    assert isinstance(result, GenerationResult)
    assert result.status == "NOT_ENOUGH_INFORMATION"
    assert result.answer == ""


# ---------------------------------------------------------------------------
# Retry / error tests (carried over from Phase 17, updated for new return type)
# ---------------------------------------------------------------------------

@patch("app.rag.generation._get_client")
def test_generation_retry_on_rate_limit(mock_get_client):
    mock_client = MagicMock()
    error = Exception("429 Rate Limit")
    mock_client.models.generate_content.side_effect = [
        error,
        _mock_gemini_text('{"status": "ANSWERED", "answer": "OK"}'),
    ]
    mock_get_client.return_value = mock_client
    result = generate_answer("test", [_chunk()])
    assert result.status == "ANSWERED"
    assert result.answer == "OK"
    assert mock_client.models.generate_content.call_count == 2


@patch("app.rag.generation._get_client")
def test_generation_failure_raises_generation_error(mock_get_client):
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("Permanent failure")
    mock_get_client.return_value = mock_client
    with pytest.raises(GenerationError):
        generate_answer("q", [_chunk()])


# ---------------------------------------------------------------------------
# Phase 19: Citation tracking tests
# ---------------------------------------------------------------------------

@patch("app.rag.generation._get_client")
def test_generate_answer_attaches_correct_citations(mock_get_client):
    """Verify that an ANSWERED result includes citations matching the input chunks."""
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = _mock_gemini_text(
        '{"status": "ANSWERED", "answer": "HIT has a strict admissions policy."}'
    )
    mock_get_client.return_value = mock_client

    chunks = [
        {"chunk_id": 101, "document_id": 1, "document_title": "Admissions Handbook", "page_number": 2, "content": "Req A"},
        {"chunk_id": 102, "document_id": 2, "document_title": "Grading Handbook", "page_number": 5, "content": "Req B"}
    ]

    result = generate_answer("admissions reqs", chunks)
    assert result.status == "ANSWERED"
    assert len(result.citations) == 2
    
    # Assert citation contents
    c1 = result.citations[0]
    assert c1["document_id"] == 1
    assert c1["document_title"] == "Admissions Handbook"
    assert c1["page_number"] == 2
    assert c1["chunk_id"] == 101
    assert c1["chunk_ids"] == [101]

    c2 = result.citations[1]
    assert c2["document_id"] == 2
    assert c2["document_title"] == "Grading Handbook"
    assert c2["page_number"] == 5
    assert c2["chunk_id"] == 102
    assert c2["chunk_ids"] == [102]


@patch("app.rag.generation._get_client")
def test_generate_answer_deduplicates_citations(mock_get_client):
    """Verify that citations are collapsed/deduplicated by (document_id, page_number)."""
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = _mock_gemini_text(
        '{"status": "ANSWERED", "answer": "Deduplicated answer."}'
    )
    mock_get_client.return_value = mock_client

    chunks = [
        {"chunk_id": 201, "document_id": 1, "document_title": "Handbook", "page_number": 3, "content": "Part 1"},
        {"chunk_id": 202, "document_id": 1, "document_title": "Handbook", "page_number": 3, "content": "Part 2"},
        {"chunk_id": 203, "document_id": 2, "document_title": "Other", "page_number": 1, "content": "Other part"}
    ]

    result = generate_answer("query text", chunks)
    assert result.status == "ANSWERED"
    # Three input chunks, but only two unique document+page pairs.
    assert len(result.citations) == 2

    # Check deduplicated entry for (document_id=1, page_number=3)
    c_handbook = [c for c in result.citations if c["document_id"] == 1][0]
    assert c_handbook["document_title"] == "Handbook"
    assert c_handbook["page_number"] == 3
    # The representative chunk_id can be the first one seen (201)
    assert c_handbook["chunk_id"] == 201
    # Full list of chunks is kept for traceability
    assert c_handbook["chunk_ids"] == [201, 202]

    # Check entry for (document_id=2, page_number=1)
    c_other = [c for c in result.citations if c["document_id"] == 2][0]
    assert c_other["document_title"] == "Other"
    assert c_other["page_number"] == 1
    assert c_other["chunk_id"] == 203
    assert c_other["chunk_ids"] == [203]


@patch("app.rag.generation._get_client")
def test_generate_answer_empty_citations_for_non_answered(mock_get_client):
    """Verify that NOT_ENOUGH_INFORMATION and PARSE_ERROR always have empty citations."""
    mock_client = MagicMock()
    # Mock NOT_ENOUGH_INFORMATION
    mock_client.models.generate_content.return_value = _mock_gemini_text(
        '{"status": "NOT_ENOUGH_INFORMATION", "answer": ""}'
    )
    mock_get_client.return_value = mock_client

    chunks = [{"chunk_id": 301, "document_id": 1, "document_title": "Doc", "page_number": 1, "content": "x"}]
    result_nei = generate_answer("query", chunks)
    assert result_nei.status == "NOT_ENOUGH_INFORMATION"
    assert result_nei.citations == []

    # Mock PARSE_ERROR
    mock_client.models.generate_content.return_value = _mock_gemini_text(
        "totally unparseable output"
    )
    result_pe = generate_answer("query", chunks)
    assert result_pe.status == "PARSE_ERROR"
    assert result_pe.citations == []


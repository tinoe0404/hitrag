import builtins
import pytest
from unittest.mock import patch, MagicMock

from app.rag.generation import generate_answer, build_prompt, GenerationError

# Helper to create a simple chunk dict
def _chunk(title="Doc", page=1, content="Sample content."):
    return {"document_title": title, "page_number": page, "content": content}

def test_build_prompt_contains_context_and_instruction():
    query = "What is the policy?"
    chunks = [_chunk("Policy Doc", 2, "The policy states X.")]
    prompt = build_prompt(query, chunks)
    assert "using ONLY the provided context" in prompt
    assert "Question: What is the policy?" in prompt
    assert "1. Policy Doc (Page 2)" in prompt
    assert "The policy states X." in prompt

@patch("app.rag.generation._get_client")
def test_generate_answer_calls_gemini_and_returns_text(mock_get_client):
    # Mock the client and its generate_content method
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_candidate = MagicMock()
    mock_part = MagicMock()
    mock_part.text = "Generated answer."
    mock_candidate.content.parts = [mock_part]
    mock_response.candidates = [mock_candidate]
    mock_client.models.generate_content.return_value = mock_response
    mock_get_client.return_value = mock_client

    query = "Explain X"
    chunks = [_chunk(content="X is defined as Y.")]
    answer = generate_answer(query, chunks)
    assert answer == "Generated answer."
    # Ensure generate_content was called with our prompt
    args, kwargs = mock_client.models.generate_content.call_args
    # Verify that the generation uses the configured gemini-3.6-flash model
    assert kwargs["model"] == "gemini-3.6-flash"

@patch("app.rag.generation._get_client")
def test_generate_answer_empty_chunks_short_circuits(mock_get_client):
    answer = generate_answer("any query", [])
    assert answer == "No context available for this query."
    mock_get_client.assert_not_called()

@patch("app.rag.generation._get_client")
def test_generation_retry_on_rate_limit(mock_get_client):
    mock_client = MagicMock()
    # First call raises rate limit, second succeeds
    error = Exception("429 Rate Limit")
    mock_client.models.generate_content.side_effect = [error, MagicMock(candidates=[MagicMock(content=MagicMock(parts=[MagicMock(text="OK")]))])]
    mock_get_client.return_value = mock_client
    answer = generate_answer("test", [_chunk()])
    assert answer == "OK"
    # Should have been called twice
    assert mock_client.models.generate_content.call_count == 2

@patch("app.rag.generation._get_client")
def test_generation_failure_raises_generation_error(mock_get_client):
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("Permanent failure")
    mock_get_client.return_value = mock_client
    with pytest.raises(GenerationError):
        generate_answer("q", [_chunk()])

"""
Tests for Phase 11: Gemini Embeddings
=====================================
Tests embed_text() and embed_texts() with mocked API calls.
Also tests error handling: missing API key, rate limiting with retry, empty input.
"""

import pytest
from unittest.mock import patch, MagicMock
from types import SimpleNamespace

from app.rag.embeddings import (
    embed_text,
    embed_texts,
    EmbeddingError,
    EMBEDDING_DIMENSIONALITY,
    BATCH_SIZE,
)


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _make_mock_response(vectors: list[list[float]]):
    """Build a mock response matching google.genai embed_content output."""
    embeddings = [SimpleNamespace(values=v) for v in vectors]
    return SimpleNamespace(embeddings=embeddings)


def _fake_vector(seed: float = 1.0) -> list[float]:
    """Return a fake 768-d embedding vector."""
    return [seed * 0.001 * i for i in range(EMBEDDING_DIMENSIONALITY)]


# ─── embed_text ────────────────────────────────────────────────────────────────

class TestEmbedText:
    """Test embed_text() — single string embedding."""

    @patch("app.rag.embeddings._get_client")
    def test_returns_768d_vector(self, mock_get_client):
        """embed_text returns a list of 768 floats."""
        fake_vec = _fake_vector(1.0)
        mock_client = MagicMock()
        mock_client.models.embed_content.return_value = _make_mock_response([fake_vec])
        mock_get_client.return_value = mock_client

        result = embed_text("Hello world")

        assert isinstance(result, list)
        assert len(result) == EMBEDDING_DIMENSIONALITY
        assert result == fake_vec

    def test_empty_string_returns_empty_list(self):
        """embed_text('') returns [] without calling the API."""
        assert embed_text("") == []

    def test_whitespace_only_returns_empty_list(self):
        """embed_text('   ') returns [] without calling the API."""
        assert embed_text("   ") == []


# ─── embed_texts (batch) ──────────────────────────────────────────────────────

class TestEmbedTexts:
    """Test embed_texts() — batch embedding."""

    @patch("app.rag.embeddings._get_client")
    def test_batch_of_three(self, mock_get_client):
        """embed_texts with 3 texts returns 3 vectors, correct order."""
        vecs = [_fake_vector(i) for i in range(1, 4)]
        mock_client = MagicMock()
        mock_client.models.embed_content.return_value = _make_mock_response(vecs)
        mock_get_client.return_value = mock_client

        result = embed_texts(["text1", "text2", "text3"])

        assert len(result) == 3
        for i in range(3):
            assert len(result[i]) == EMBEDDING_DIMENSIONALITY

    @patch("app.rag.embeddings._get_client")
    def test_mixed_empty_and_real(self, mock_get_client):
        """Empty texts get [] while real texts get embeddings, preserving order."""
        fake_vec = _fake_vector(1.0)
        mock_client = MagicMock()
        mock_client.models.embed_content.return_value = _make_mock_response([fake_vec])
        mock_get_client.return_value = mock_client

        result = embed_texts(["", "real text", "  "])

        assert len(result) == 3
        assert result[0] == []  # empty
        assert len(result[1]) == EMBEDDING_DIMENSIONALITY  # real
        assert result[2] == []  # whitespace-only

    def test_empty_list_returns_empty(self):
        """embed_texts([]) returns [] without calling the API."""
        assert embed_texts([]) == []

    @patch("app.rag.embeddings._get_client")
    def test_batching_splits_large_input(self, mock_get_client):
        """More than BATCH_SIZE texts triggers multiple API calls."""
        num_texts = BATCH_SIZE + 10
        texts = [f"text {i}" for i in range(num_texts)]

        mock_client = MagicMock()
        # First call returns BATCH_SIZE vectors, second call returns 10
        vecs_batch1 = [_fake_vector(1.0)] * BATCH_SIZE
        vecs_batch2 = [_fake_vector(2.0)] * 10
        mock_client.models.embed_content.side_effect = [
            _make_mock_response(vecs_batch1),
            _make_mock_response(vecs_batch2),
        ]
        mock_get_client.return_value = mock_client

        result = embed_texts(texts)

        assert len(result) == num_texts
        assert mock_client.models.embed_content.call_count == 2


# ─── Error handling ───────────────────────────────────────────────────────────

class TestEmbeddingErrors:
    """Test error handling: missing key, rate limiting, non-retryable errors."""

    @patch("app.rag.embeddings.settings")
    def test_missing_api_key_raises(self, mock_settings):
        """Missing GEMINI_API_KEY raises EmbeddingError immediately."""
        mock_settings.GEMINI_API_KEY = None

        with pytest.raises(EmbeddingError, match="GEMINI_API_KEY is not set"):
            embed_text("test")

    @patch("app.rag.embeddings._get_client")
    @patch("app.rag.embeddings.time.sleep")  # Don't actually sleep in tests
    def test_rate_limit_retries_then_fails(self, mock_sleep, mock_get_client):
        """429 rate limit triggers retries with exponential backoff, then raises."""
        mock_client = MagicMock()
        mock_client.models.embed_content.side_effect = Exception("429 Resource exhausted")
        mock_get_client.return_value = mock_client

        with pytest.raises(EmbeddingError, match="Embedding failed after"):
            embed_text("test")

        # Should have retried MAX_RETRIES times
        assert mock_client.models.embed_content.call_count == 3

    @patch("app.rag.embeddings._get_client")
    @patch("app.rag.embeddings.time.sleep")
    def test_rate_limit_recovers_on_retry(self, mock_sleep, mock_get_client):
        """429 on first call, success on second — returns the embedding."""
        fake_vec = _fake_vector(1.0)
        mock_client = MagicMock()
        mock_client.models.embed_content.side_effect = [
            Exception("429 Resource exhausted"),
            _make_mock_response([fake_vec]),
        ]
        mock_get_client.return_value = mock_client

        result = embed_text("test")

        assert len(result) == EMBEDDING_DIMENSIONALITY
        assert mock_client.models.embed_content.call_count == 2

    @patch("app.rag.embeddings._get_client")
    def test_non_retryable_error_fails_fast(self, mock_get_client):
        """Non-retryable errors (e.g. invalid model) fail immediately without retrying."""
        mock_client = MagicMock()
        mock_client.models.embed_content.side_effect = Exception("Model not found")
        mock_get_client.return_value = mock_client

        with pytest.raises(EmbeddingError, match="Embedding failed after"):
            embed_text("test")

        # Non-retryable: only called once (fails on attempt 1, no retry)
        assert mock_client.models.embed_content.call_count == 1


# ─── DB Integration Tests ──────────────────────────────────────────────────────

from app.db.session import SessionLocal
from app.models.document import Document
from app.models.chunk import Chunk
from app.models.enums import UserRole, DocumentStatus
from app.models.user import User

class TestVectorStoreIntegration:
    """Integration tests with real PostgreSQL vector storage and search."""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        self.db = SessionLocal()
        # Find an uploader user from the db
        uploader = self.db.query(User).first()
        self.uploader_id = uploader.id if uploader else 1

        self.doc = Document(
            title="Test Vector Integration Doc",
            filename="test_vector_integration.pdf",
            storage_path="/tmp/test_vector_integration.pdf",
            access_tier=UserRole.PUBLIC,
            uploaded_by=self.uploader_id,
            status=DocumentStatus.PENDING
        )
        self.db.add(self.doc)
        self.db.commit()
        self.db.refresh(self.doc)

        yield

        # Cleanup
        self.db.delete(self.doc)
        self.db.commit()
        self.db.close()

    def test_insert_and_read_vector(self):
        """Test that we can insert a chunk with a 768d vector and read it back."""
        fake_vec = [float(i) * 0.001 for i in range(768)]
        chunk = Chunk(
            document_id=self.doc.id,
            content="This is a test chunk with embedding.",
            chunk_index=0,
            page_number=1,
            embedding=fake_vec
        )
        self.db.add(chunk)
        self.db.commit()
        self.db.refresh(chunk)

        # Retrieve and verify
        db_chunk = self.db.query(Chunk).filter(Chunk.id == chunk.id).one()
        assert db_chunk.embedding is not None
        assert len(db_chunk.embedding) == 768
        # Verify first few values
        for i in range(5):
            assert abs(db_chunk.embedding[i] - fake_vec[i]) < 1e-6

    def test_vector_similarity_query(self):
        """Test that a basic cosine similarity query runs without error against real data."""
        # Insert 3 chunks with different vectors
        vec1 = [0.1] * 768
        vec2 = [0.5] * 768
        vec3 = [0.9] * 768

        chunk1 = Chunk(
            document_id=self.doc.id, content="Chunk 1", chunk_index=0, page_number=1, embedding=vec1
        )
        chunk2 = Chunk(
            document_id=self.doc.id, content="Chunk 2", chunk_index=1, page_number=1, embedding=vec2
        )
        chunk3 = Chunk(
            document_id=self.doc.id, content="Chunk 3", chunk_index=2, page_number=1, embedding=vec3
        )
        self.db.add_all([chunk1, chunk2, chunk3])
        self.db.commit()

        # Query using cosine similarity (closest to [0.1] * 768)
        query_vec = [0.12] * 768
        results = (
            self.db.query(Chunk)
            .filter(Chunk.document_id == self.doc.id)
            .order_by(Chunk.embedding.cosine_distance(query_vec))
            .all()
        )

        assert len(results) == 3
        # Closest should be Chunk 1 (vec1), then Chunk 2, then Chunk 3
        assert results[0].content == "Chunk 1"
        assert results[1].content == "Chunk 2"
        assert results[2].content == "Chunk 3"


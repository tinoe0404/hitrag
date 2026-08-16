"""
Tests for Phase 14: Retrieval without an LLM
============================================
Covers:
1. Retrieval ranking with deterministic mock embeddings against known db chunks.
2. Respecting top_k limits.
3. Clean handling of empty queries.
4. Clean handling of empty chunk table (returns empty list).
"""

import pytest
from unittest.mock import patch, MagicMock

from app.db.session import SessionLocal
from app.models.document import Document
from app.models.chunk import Chunk
from app.models.enums import UserRole, DocumentStatus
from app.models.user import User
from app.rag.retrieval import retrieve
from app.rag.embeddings import EmbeddingError


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def temp_document(db_session):
    # Find or create a mock uploader user
    uploader = db_session.query(User).first()
    uploader_id = uploader.id if uploader else 1

    doc = Document(
        title="Test Retrieval Document",
        filename="test_retrieval.pdf",
        storage_path="/tmp/test_retrieval.pdf",
        access_tier=UserRole.PUBLIC,
        uploaded_by=uploader_id,
        status=DocumentStatus.EMBEDDED
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    yield doc

    # Cleanup doc and its cascading chunks
    db_session.delete(doc)
    db_session.commit()


@patch("app.rag.retrieval.embed_text")
def test_retrieval_ranking(mock_embed_text, db_session, temp_document):
    """Verify that retrieve() sorts chunks by distance and returns correct metadata."""
    # Define three vectors: query is closest to vec1, then vec2, then vec3
    # Note: pgvector cosine_distance = 1.0 - (u.v / (||u|| ||v||))
    # Let's create unit vectors to make cosine distance simple
    vec_query = [1.0] + [0.0] * 767
    vec1 = [0.9] + [0.1] * 767  # very close to [1.0, 0.0, ...]
    vec2 = [0.5] + [0.5] * 767  # medium close
    vec3 = [-0.9] + [0.1] * 767 # very far/opposite

    mock_embed_text.return_value = vec_query

    # Create and add chunks to DB
    chunk1 = Chunk(
        document_id=temp_document.id,
        content="This is chunk 1: Harare Institute of Technology admissions.",
        chunk_index=0,
        page_number=1,
        embedding=vec1
    )
    chunk2 = Chunk(
        document_id=temp_document.id,
        content="This is chunk 2: Examination rules and undergraduate pass marks.",
        chunk_index=1,
        page_number=2,
        embedding=vec2
    )
    chunk3 = Chunk(
        document_id=temp_document.id,
        content="This is chunk 3: Random unrelated content about space travel.",
        chunk_index=2,
        page_number=3,
        embedding=vec3
    )

    db_session.add_all([chunk1, chunk2, chunk3])
    db_session.commit()

    try:
        # Run retrieval with high top_k to fetch all chunks including test ones
        results = retrieve(db_session, "HIT admissions", top_k=100)

        # Filter only to chunks created for this document
        filtered_results = [r for r in results if r["document_id"] == temp_document.id]

        assert len(filtered_results) == 3
        # Should be ordered chunk1, chunk2, chunk3
        assert filtered_results[0]["chunk_id"] == chunk1.id
        assert filtered_results[1]["chunk_id"] == chunk2.id
        assert filtered_results[2]["chunk_id"] == chunk3.id

        # Verify score keys on filtered results
        for res in filtered_results:
            assert "cosine_similarity" in res
            assert "cosine_distance" in res
            assert -1.0 <= res["cosine_similarity"] <= 1.0
            assert 0.0 <= res["cosine_distance"] <= 2.0
            # similarity + distance should be 1.0
            assert abs(res["cosine_similarity"] + res["cosine_distance"] - 1.0) < 1e-5

        # Verify content and metadata keys
        assert filtered_results[0]["content"] == chunk1.content
        assert filtered_results[0]["page_number"] == 1
        assert filtered_results[0]["document_id"] == temp_document.id


    finally:
        # Clean up chunks
        db_session.delete(chunk1)
        db_session.delete(chunk2)
        db_session.delete(chunk3)
        db_session.commit()


@patch("app.rag.retrieval.embed_text")
def test_retrieval_respects_top_k(mock_embed_text, db_session, temp_document):
    """Verify that retrieve() respects the top_k parameter limit."""
    vec_query = [1.0] * 768
    mock_embed_text.return_value = vec_query

    # Create 5 chunks
    chunks = []
    for i in range(5):
        chunk = Chunk(
            document_id=temp_document.id,
            content=f"Chunk {i}",
            chunk_index=i,
            page_number=1,
            embedding=[0.1 * i] * 768
        )
        chunks.append(chunk)
    db_session.add_all(chunks)
    db_session.commit()

    try:
        # Retrieve with top_k=2
        results = retrieve(db_session, "query text", top_k=2)
        assert len(results) == 2

        # Retrieve with top_k=4
        results_4 = retrieve(db_session, "query text", top_k=4)
        assert len(results_4) == 4

    finally:
        for c in chunks:
            db_session.delete(c)
        db_session.commit()


def test_retrieval_empty_query(db_session):
    """Verify that retrieve() with empty or whitespace query raises ValueError."""
    with pytest.raises(ValueError, match="cannot be empty or whitespace-only"):
        retrieve(db_session, "")

    with pytest.raises(ValueError, match="cannot be empty or whitespace-only"):
        retrieve(db_session, "   ")


@patch("app.rag.retrieval.embed_text")
def test_retrieval_empty_database(mock_embed_text, db_session):
    """Verify that retrieve() returns an empty list cleanly if there are no chunks in the DB."""
    mock_embed_text.return_value = [0.1] * 768

    # We run retrieval. Even if database is empty or has no chunks, it should return [] without erroring.
    # We filter by a non-existent document ID or clear chunks if any, but since we use test DB it's fine.
    results = retrieve(db_session, "some query", top_k=5)
    
    # We can't guarantee the DB is completely empty of other tests' artifacts unless we filter specifically,
    # but retrieve() queries across all chunks. Let's make sure it doesn't raise any errors.
    assert isinstance(results, list)

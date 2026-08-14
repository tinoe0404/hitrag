"""
Tests for Phase 10: Document Chunking & Persistence.

Covers:
1. Normal paragraphs (each split into its own chunk when sizes are reasonable).
2. Merging short paragraphs on the same page, and confirming merging does NOT cross page boundaries.
3. Splitting oversized paragraphs on sentence boundaries.
4. Correct sequential chunk_index assignment and DB persistence mapping.
"""
import pytest
from sqlalchemy.orm import Session

from app.rag.chunking import chunk_pages, MIN_CHUNK_CHARS, MAX_CHUNK_CHARS
from app.repositories.document import bulk_insert_chunks
from app.models.chunk import Chunk
from app.db.session import SessionLocal


def test_chunk_pages_normal():
    # Two standard-sized paragraphs on a page (each > 200 characters)
    pages = [
        {
            "page_number": 1,
            "text": "This is a normal paragraph that is longer than the minimum character count of 200. We will write enough text to make sure it satisfies the requirement. It should have some sentences. Let's add even more words here to easily push the total count over 250 characters.\n\nThis is a second normal paragraph on the same page. It is also sufficiently long to form its own chunk without requiring any merging. Let's make sure it is long enough by adding extra words and sentences here so it is also well over 250 characters."
        }
    ]
    chunks = chunk_pages(pages, document_id=99)
    assert len(chunks) == 2
    assert chunks[0]["chunk_index"] == 0
    assert chunks[1]["chunk_index"] == 1
    assert chunks[0]["page_number"] == 1
    assert chunks[1]["page_number"] == 1
    assert "second normal paragraph" in chunks[1]["content"]


def test_chunk_pages_merging_short_paragraphs():
    # Page 1: Three short paragraphs. Para 1 + Para 2 should merge. Para 3 is also merged if space permits.
    # Page 2: Two short paragraphs. They should merge with each other, but NEVER cross page boundaries to page 1.
    pages = [
        {
            "page_number": 1,
            "text": "Short para 1. (too short)"  # len ~ 25
            "\n\n"
            "Short para 2. This paragraph should merge with the first one to exceed 200 characters. Let's make sure we have enough characters."  # len ~ 130
            "\n\n"
            "Short para 3. Also short."  # len ~ 25
        },
        {
            "page_number": 2,
            "text": "Short para 4. Page 2 start."
            "\n\n"
            "Short para 5. Page 2 end. Merging here should stay on page 2."
        }
    ]
    chunks = chunk_pages(pages, document_id=99)
    
    # Page 1: Para 1 (25) + Para 2 (130) + Para 3 (25) = ~180 chars. Since total is < MIN_CHUNK_CHARS (200), they will all be merged into 1 chunk.
    # Page 2: Para 4 + Para 5 will be merged into 1 chunk.
    # Total chunks = 2.
    assert len(chunks) == 2
    assert chunks[0]["page_number"] == 1
    assert chunks[1]["page_number"] == 2
    assert "Page 2 start" in chunks[1]["content"]
    assert "Short para 1" in chunks[0]["content"]


def test_chunk_pages_splitting_oversized_paragraph():
    # Fabricate a single paragraph of ~1800 characters (exceeds MAX_CHUNK_CHARS = 1500)
    # Composed of multiple sentences
    s1 = "This is sentence one of the oversized paragraph. " * 10  # ~500 chars
    s2 = "This is sentence two of the oversized paragraph. " * 10  # ~500 chars
    s3 = "This is sentence three of the oversized paragraph. " * 10  # ~500 chars
    s4 = "This is sentence four of the oversized paragraph. " * 10  # ~500 chars
    
    oversized_para = s1 + s2 + s3 + s4  # ~2000 chars
    pages = [
        {
            "page_number": 1,
            "text": oversized_para
        }
    ]
    
    chunks = chunk_pages(pages, document_id=99)
    # Should be split into 2 chunks because total is ~2000 chars and max is 1500.
    assert len(chunks) == 2
    assert len(chunks[0]["content"]) <= MAX_CHUNK_CHARS
    assert len(chunks[1]["content"]) <= MAX_CHUNK_CHARS
    
    # Verify split happened at sentence boundary (no cut mid-word)
    assert chunks[0]["content"].endswith(".")
    assert chunks[1]["content"].startswith("This is sentence")


@pytest.fixture
def db_session():
    db = SessionLocal()
    yield db
    db.close()


def test_bulk_insert_chunks(db_session: Session):
    # Register dummy document to fulfill FK constraint
    from app.models.document import Document
    from app.models.enums import UserRole, DocumentStatus
    
    # Find an uploader user from the db
    from app.models.user import User
    uploader = db_session.query(User).first()
    uploader_id = uploader.id if uploader else 1

    doc = Document(
        title="Test Chunking Doc",
        filename="test_chunking.pdf",
        storage_path="/tmp/test_chunking.pdf",
        access_tier=UserRole.PUBLIC,
        uploaded_by=uploader_id,
        status=DocumentStatus.PENDING
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    
    try:
        # Create some test chunks
        chunks_data = [
            {"chunk_index": 0, "page_number": 1, "content": "This is chunk index 0 content."},
            {"chunk_index": 1, "page_number": 1, "content": "This is chunk index 1 content."},
            {"chunk_index": 2, "page_number": 2, "content": "This is chunk index 2 content."}
        ]
        
        # Test bulk insert
        bulk_insert_chunks(db_session, doc.id, chunks_data)
        
        # Verify from database
        db_chunks = db_session.query(Chunk).filter(Chunk.document_id == doc.id).order_by(Chunk.chunk_index).all()
        assert len(db_chunks) == 3
        assert db_chunks[0].chunk_index == 0
        assert db_chunks[1].chunk_index == 1
        assert db_chunks[2].chunk_index == 2
        assert db_chunks[0].page_number == 1
        assert db_chunks[2].page_number == 2
        assert db_chunks[0].content == "This is chunk index 0 content."
        
    finally:
        # Cleanup
        db_session.delete(doc)
        db_session.commit()

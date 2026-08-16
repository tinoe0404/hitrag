"""
Tests for Phase 13: Manual Ingestion Trigger & Status Pipeline.
Covers:
1. Successful manually triggered ingestion run with mock embeddings.
2. Failure handling at extraction step setting status to EXT_FAILED.
3. Re-ingestion prevention semantics (400 Bad Request) and force-reingest override.
"""

import io
import time
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models.document import Document
from app.models.chunk import Chunk
from app.models.enums import DocumentStatus, UserRole

client = TestClient(app)


# ─── Auth and PDF Helpers ──────────────────────────────────────────────────────

def create_auth_headers(prefix: str, role: str = "LECTURER"):
    """Register and login a user, returning auth headers."""
    email = f"ingest_{prefix}_{int(time.time()*1000)}@hit.ac.zw"
    pwd = "Password123!"
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": pwd,
        "full_name": f"Ingest User {prefix}",
        "role": role
    })
    res = client.post("/api/v1/auth/login", data={"username": email, "password": pwd})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def make_valid_pdf_bytes():
    """Generate a small valid PDF file using PyMuPDF to write real text."""
    import fitz
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 72), "HARARE INSTITUTE OF TECHNOLOGY\n\nSection 1: Admission Requirements\n"
                              "Applicants must possess 5 O-Level passes including English and Mathematics. "
                              "This is a longer paragraph to exceed the minimum size requirement of 200 characters.", fontsize=12)
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes


# ─── Pipeline Tests ────────────────────────────────────────────────────────────

@patch("app.rag.embeddings.embed_texts")
def test_manual_ingestion_success(mock_embed_texts):
    """Test full successful manual ingestion pipeline flow."""
    # Mock Gemini embedding to return a fake 768d vector
    mock_vector = [0.1] * 768
    mock_embed_texts.return_value = [mock_vector]

    headers = create_auth_headers("admin", role="ADMIN")
    pdf_bytes = make_valid_pdf_bytes()
    
    # 1. Upload Document
    files = {"file": ("handbook.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    upload_res = client.post(
        "/api/v1/documents",
        headers=headers,
        files=files,
        data={"title": "HIT Student Handbook Ingestion", "access_tier": "PUBLIC"}
    )
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]
    assert upload_res.json()["status"] == "UPLOADED"

    # 2. Trigger Ingestion manual POST endpoint
    ingest_res = client.post(f"/api/v1/documents/{doc_id}/ingest", headers=headers)
    assert ingest_res.status_code == 200
    
    res_data = ingest_res.json()
    assert res_data["document_id"] == doc_id
    assert res_data["status"] == "EMBEDDED"
    assert res_data["total_chunks"] == 1
    assert res_data["embedded_chunks"] == 1
    assert res_data["failed_chunks"] == 0
    assert res_data["time_taken_seconds"] > 0

    # 3. Verify status and chunks exist in DB
    db = SessionLocal()
    try:
        db_doc = db.query(Document).filter(Document.id == doc_id).first()
        assert db_doc.status == DocumentStatus.EMBEDDED

        db_chunks = db.query(Chunk).filter(Chunk.document_id == doc_id).all()
        assert len(db_chunks) == 1
        assert len(db_chunks[0].embedding) == 768
        assert list(db_chunks[0].embedding) == mock_vector

        # Cleanup
        db.delete(db_doc)
        db.commit()
    finally:
        db.close()


def test_manual_ingestion_extraction_failure():
    """Test that a corrupted PDF fails during extraction and sets EXT_FAILED."""
    headers = create_auth_headers("lecturer", role="LECTURER")
    # Must start with %PDF- to bypass the upload magic-bytes validator, but be invalid after that
    corrupted_bytes = b"%PDF-1.4\nTHIS IS GARBAGE BYTES NOT A VALID PDF FILE"
    
    # Upload Document
    files = {"file": ("corrupted.pdf", io.BytesIO(corrupted_bytes), "application/pdf")}
    upload_res = client.post(
        "/api/v1/documents",
        headers=headers,
        files=files,
        data={"title": "Corrupted Doc", "access_tier": "PUBLIC"}
    )
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    # Trigger Ingestion -> fails with 422 Unprocessable Entity
    ingest_res = client.post(f"/api/v1/documents/{doc_id}/ingest", headers=headers)
    assert ingest_res.status_code == 422
    assert "Extraction failed" in ingest_res.json()["detail"]

    # Verify status in DB is updated to EXT_FAILED and no chunks exist
    db = SessionLocal()
    try:
        db_doc = db.query(Document).filter(Document.id == doc_id).first()
        assert db_doc.status == DocumentStatus.EXT_FAILED

        db_chunks = db.query(Chunk).filter(Chunk.document_id == doc_id).all()
        assert len(db_chunks) == 0

        # Cleanup
        db.delete(db_doc)
        db.commit()
    finally:
        db.close()


@patch("app.rag.embeddings.embed_texts")
def test_manual_ingestion_reingestion_block_and_force(mock_embed_texts):
    """Test re-ingestion prevention semantics and force-reingest override."""
    mock_vector = [0.2] * 768
    mock_embed_texts.return_value = [mock_vector]

    headers = create_auth_headers("admin_reingest", role="ADMIN")
    pdf_bytes = make_valid_pdf_bytes()

    # Upload
    files = {"file": ("handbook_re.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    upload_res = client.post(
        "/api/v1/documents",
        headers=headers,
        files=files,
        data={"title": "HIT Handbook Reingest", "access_tier": "PUBLIC"}
    )
    doc_id = upload_res.json()["id"]

    # First ingestion -> Success (embedded)
    ingest_res = client.post(f"/api/v1/documents/{doc_id}/ingest", headers=headers)
    assert ingest_res.status_code == 200

    # Second ingestion without force -> Blocked with 400 Bad Request
    reingest_res = client.post(f"/api/v1/documents/{doc_id}/ingest", headers=headers)
    assert reingest_res.status_code == 400
    assert "already fully ingested and embedded" in reingest_res.json()["detail"]

    # Third ingestion with force=True -> Success (overwrites and embeds)
    force_res = client.post(f"/api/v1/documents/{doc_id}/ingest?force=true", headers=headers)
    assert force_res.status_code == 200
    assert force_res.json()["status"] == "EMBEDDED"

    # Cleanup
    db = SessionLocal()
    try:
        db_doc = db.query(Document).filter(Document.id == doc_id).first()
        db.delete(db_doc)
        db.commit()
    finally:
        db.close()


def test_ingestion_rbac_permissions():
    """Verify that a STUDENT cannot manually trigger ingestion (403 Forbidden)."""
    headers_student = create_auth_headers("student_user", role="STUDENT")
    headers_admin = create_auth_headers("admin_user", role="ADMIN")
    pdf_bytes = make_valid_pdf_bytes()

    # Admin Uploads
    files = {"file": ("student_rules.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    upload_res = client.post(
        "/api/v1/documents",
        headers=headers_admin,
        files=files,
        data={"title": "Student Rules", "access_tier": "PUBLIC"}
    )
    doc_id = upload_res.json()["id"]

    # Student triggers ingestion -> 403 Forbidden
    student_ingest = client.post(f"/api/v1/documents/{doc_id}/ingest", headers=headers_student)
    assert student_ingest.status_code == 403

    # Cleanup
    db = SessionLocal()
    try:
        db_doc = db.query(Document).filter(Document.id == doc_id).first()
        db.delete(db_doc)
        db.commit()
    finally:
        db.close()

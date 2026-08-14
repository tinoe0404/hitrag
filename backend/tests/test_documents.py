import io
import time
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def create_auth_headers(prefix: str, role: str = "STUDENT"):
    email = f"doc_{prefix}_{int(time.time()*1000)}@hit.ac.zw"
    pwd = "Password123!"
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": pwd,
        "full_name": f"Doc {prefix}",
        "role": role
    })
    res = client.post("/api/v1/auth/login", data={"username": email, "password": pwd})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# Helper to create dummy PDF bytes with valid magic header
def make_dummy_pdf(content: str = "HIT Policy Content"):
    return b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n" + content.encode("utf-8")


def test_pdf_upload_success_and_metadata():
    headers = create_auth_headers("admin_uploader", role="ADMIN")
    pdf_bytes = make_dummy_pdf("Sample Academic Policy")

    files = {"file": ("hit_policy.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    data = {"title": "HIT General Academic Regulations", "access_tier": "PUBLIC"}

    res = client.post("/api/v1/documents", headers=headers, files=files, data=data)
    assert res.status_code == 201
    doc = res.json()
    assert doc["title"] == "HIT General Academic Regulations"
    assert doc["filename"] == "hit_policy.pdf"
    assert doc["access_tier"] == "PUBLIC"
    assert "storage_path" not in doc  # Ensures internal storage_path is unexposed


def test_non_pdf_file_rejection():
    headers = create_auth_headers("text_uploader", role="ADMIN")

    # 1. Reject invalid extension
    files_txt = {"file": ("notes.txt", io.BytesIO(b"Plain text notes"), "text/plain")}
    res_txt = client.post("/api/v1/documents", headers=headers, files=files_txt, data={"title": "Notes"})
    assert res_txt.status_code == 400
    assert "Invalid file format" in res_txt.json()["detail"]

    # 2. Reject fake PDF (renamed .txt with invalid magic bytes)
    fake_pdf_bytes = b"Hello world this is not a pdf file!"
    files_fake = {"file": ("fake.pdf", io.BytesIO(fake_pdf_bytes), "application/pdf")}
    res_fake = client.post("/api/v1/documents", headers=headers, files=files_fake, data={"title": "Fake PDF"})
    assert res_fake.status_code == 400
    assert "Magic byte signature check failed" in res_fake.json()["detail"]


def test_oversized_file_rejection():
    headers = create_auth_headers("large_uploader", role="ADMIN")

    # Construct mock oversized file > 20MB
    # Header starts with %PDF- followed by 21MB of padded bytes
    large_bytes = b"%PDF-1.4\n" + b"X" * (21 * 1024 * 1024)
    files = {"file": ("large_doc.pdf", io.BytesIO(large_bytes), "application/pdf")}

    res = client.post("/api/v1/documents", headers=headers, files=files, data={"title": "Large Doc"})
    assert res.status_code == 413
    assert "File size exceeds maximum allowed limit" in res.json()["detail"]


def test_tier_escalation_restriction():
    headers_student = create_auth_headers("tier_student", role="STUDENT")
    pdf_bytes = make_dummy_pdf("Student Paper")

    files = {"file": ("paper.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    # Student attempting to upload LECTURER tier doc -> 403 Forbidden
    data = {"title": "Attempted Lecturer Doc", "access_tier": "LECTURER"}

    res = client.post("/api/v1/documents", headers=headers_student, files=files, data=data)
    assert res.status_code == 403
    assert "not permitted to set access tier" in res.json()["detail"]


def test_document_rbac_listing_and_404_isolation():
    headers_admin = create_auth_headers("doc_admin", role="ADMIN")
    headers_student = create_auth_headers("doc_student", role="STUDENT")

    pdf_bytes = make_dummy_pdf("Confidential Staff Appraisal")

    # Admin uploads LECTURER-tier document
    files_lec = {"file": ("staff_appraisal.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    res_upload = client.post(
        "/api/v1/documents",
        headers=headers_admin,
        files=files_lec,
        data={"title": "Staff Appraisal 2026", "access_tier": "LECTURER"}
    )
    doc_id = res_upload.json()["id"]

    # 1. Student lists documents -> LECTURER-tier doc should NOT be in student's list
    res_list_student = client.get("/api/v1/documents", headers=headers_student)
    assert res_list_student.status_code == 200
    student_doc_ids = [d["id"] for d in res_list_student.json()]
    assert doc_id not in student_doc_ids

    # 2. Admin lists documents -> LECTURER-tier doc IS in admin's list
    res_list_admin = client.get("/api/v1/documents", headers=headers_admin)
    assert res_list_admin.status_code == 200
    admin_doc_ids = [d["id"] for d in res_list_admin.json()]
    assert doc_id in admin_doc_ids

    # 3. Student attempts direct GET of LECTURER-tier document ID -> 404 Not Found
    res_get_student = client.get(f"/api/v1/documents/{doc_id}", headers=headers_student)
    assert res_get_student.status_code == 404
    assert res_get_student.json()["detail"] == "Document not found"

    # 4. Admin GET of LECTURER-tier document ID -> 200 OK
    res_get_admin = client.get(f"/api/v1/documents/{doc_id}", headers=headers_admin)
    assert res_get_admin.status_code == 200
    assert res_get_admin.json()["id"] == doc_id

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture
def student_headers():
    # Register student
    reg_payload = {
        "email": "rbac_student@hit.ac.zw",
        "password": "StudentPassword123!",
        "full_name": "RBAC Student User",
        "role": "STUDENT"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    # Login
    login_data = {"username": "rbac_student@hit.ac.zw", "password": "StudentPassword123!"}
    res = client.post("/api/v1/auth/login", data=login_data)
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def lecturer_headers():
    # Register lecturer
    reg_payload = {
        "email": "rbac_lecturer@hit.ac.zw",
        "password": "LecturerPassword123!",
        "full_name": "RBAC Lecturer User",
        "role": "LECTURER"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    # Login
    login_data = {"username": "rbac_lecturer@hit.ac.zw", "password": "LecturerPassword123!"}
    res = client.post("/api/v1/auth/login", data=login_data)
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_headers():
    # Register admin
    reg_payload = {
        "email": "rbac_admin@hit.ac.zw",
        "password": "AdminPassword123!",
        "full_name": "RBAC Admin User",
        "role": "ADMIN"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    # Login
    login_data = {"username": "rbac_admin@hit.ac.zw", "password": "AdminPassword123!"}
    res = client.post("/api/v1/auth/login", data=login_data)
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_rbac_admin_only_authorization(student_headers, admin_headers):
    # 1. Student accessing admin-only route -> 403 Forbidden
    res_student = client.get("/api/v1/debug/admin-only", headers=student_headers)
    assert res_student.status_code == 403
    assert "is not authorized" in res_student.json()["detail"]

    # 2. Admin accessing admin-only route -> 200 OK
    res_admin = client.get("/api/v1/debug/admin-only", headers=admin_headers)
    assert res_admin.status_code == 200
    assert res_admin.json()["role"] == "ADMIN"


def test_rbac_allowed_tiers_mapping(student_headers, lecturer_headers, admin_headers):
    # 1. Student tiers -> PUBLIC, STUDENT
    res_student = client.get("/api/v1/debug/my-tiers", headers=student_headers)
    assert res_student.status_code == 200
    assert res_student.json() == ["PUBLIC", "STUDENT"]

    # 2. Lecturer tiers -> PUBLIC, STUDENT, LECTURER
    res_lecturer = client.get("/api/v1/debug/my-tiers", headers=lecturer_headers)
    assert res_lecturer.status_code == 200
    assert res_lecturer.json() == ["PUBLIC", "STUDENT", "LECTURER"]

    # 3. Admin tiers -> PUBLIC, STUDENT, LECTURER, ADMIN
    res_admin = client.get("/api/v1/debug/my-tiers", headers=admin_headers)
    assert res_admin.status_code == 200
    assert res_admin.json() == ["PUBLIC", "STUDENT", "LECTURER", "ADMIN"]

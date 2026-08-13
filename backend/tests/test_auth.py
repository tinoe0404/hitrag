import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_auth_full_flow():
    # 1. Register User
    register_payload = {
        "email": "auth_test_user@hit.ac.zw",
        "password": "SecurePassword123!",
        "full_name": "Auth Test Student",
        "role": "STUDENT"
    }

    res_reg = client.post("/api/v1/auth/register", json=register_payload)
    assert res_reg.status_code == 201
    data_reg = res_reg.json()
    assert data_reg["email"] == "auth_test_user@hit.ac.zw"
    assert "hashed_password" not in data_reg

    # 2. Login User (OAuth2 Form Data)
    login_data = {
        "username": "auth_test_user@hit.ac.zw",
        "password": "SecurePassword123!"
    }
    res_login = client.post("/api/v1/auth/login", data=login_data)
    assert res_login.status_code == 200
    token_data = res_login.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    token = token_data["access_token"]

    # 3. Read Current User /me with Bearer token
    headers = {"Authorization": f"Bearer {token}"}
    res_me = client.get("/api/v1/auth/me", headers=headers)
    assert res_me.status_code == 200
    user_me = res_me.json()
    assert user_me["email"] == "auth_test_user@hit.ac.zw"
    assert user_me["role"] == "STUDENT"

    # 4. Attempt /me with invalid token -> 401
    bad_headers = {"Authorization": "Bearer invalid_token_xyz"}
    res_bad = client.get("/api/v1/auth/me", headers=bad_headers)
    assert res_bad.status_code == 401

import time
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def get_auth_header(email_prefix: str, role: str = "STUDENT"):
    email = f"{email_prefix}_{int(time.time()*1000)}@hit.ac.zw"
    pwd = "Password123!"
    # Register
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": pwd,
        "full_name": f"User {email_prefix}",
        "role": role
    })
    # Login
    res = client.post("/api/v1/auth/login", data={"username": email, "password": pwd})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_conversation_lifecycle_and_messages():
    headers_a = get_auth_header("conv_user_a")

    # 1. Create conversation for User A
    res_create = client.post(
        "/api/v1/conversations",
        json={"title": "Academic Regulation Query"},
        headers=headers_a
    )
    assert res_create.status_code == 201
    conv_a = res_create.json()
    conv_id = conv_a["id"]
    assert conv_a["title"] == "Academic Regulation Query"

    # 2. List conversations (most recent first)
    res_list = client.get("/api/v1/conversations", headers=headers_a)
    assert res_list.status_code == 200
    conv_list = res_list.json()
    assert len(conv_list) >= 1
    assert conv_list[0]["id"] == conv_id

    # 3. Add user message
    res_msg1 = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"role": "user", "content": "What is the passing mark for Part II modules?"},
        headers=headers_a
    )
    assert res_msg1.status_code == 201
    msg1 = res_msg1.json()
    assert msg1["role"].lower() == "user"

    # 4. Add assistant message (posted by client for Phase 6)
    res_msg2 = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"role": "assistant", "content": "The passing mark for all Part II undergraduate modules is 50%."},
        headers=headers_a
    )
    assert res_msg2.status_code == 201
    msg2 = res_msg2.json()
    assert msg2["role"].lower() == "assistant"

    # 5. List messages in chronological order
    res_msgs = client.get(f"/api/v1/conversations/{conv_id}/messages", headers=headers_a)
    assert res_msgs.status_code == 200
    messages = res_msgs.json()
    assert len(messages) == 2
    assert messages[0]["id"] == msg1["id"]
    assert messages[1]["id"] == msg2["id"]


def test_conversation_tenancy_isolation_ownership():
    headers_a = get_auth_header("tenancy_user_a")
    headers_b = get_auth_header("tenancy_user_b")

    # Create conversation owned by User A
    res_create = client.post(
        "/api/v1/conversations",
        json={"title": "Private User A Session"},
        headers=headers_a
    )
    conv_a_id = res_create.json()["id"]

    # User B tries to GET User A's conversation -> 404 Not Found
    res_get_b = client.get(f"/api/v1/conversations/{conv_a_id}", headers=headers_b)
    assert res_get_b.status_code == 404
    assert res_get_b.json()["detail"] == "Conversation not found"

    # User B tries to post a message to User A's conversation -> 404 Not Found
    res_post_b = client.post(
        f"/api/v1/conversations/{conv_a_id}/messages",
        json={"role": "user", "content": "Hacked message"},
        headers=headers_b
    )
    assert res_post_b.status_code == 404

    # User B tries to list messages from User A's conversation -> 404 Not Found
    res_list_b = client.get(f"/api/v1/conversations/{conv_a_id}/messages", headers=headers_b)
    assert res_list_b.status_code == 404

    # User B tries to DELETE User A's conversation -> 404 Not Found
    res_del_b = client.delete(f"/api/v1/conversations/{conv_a_id}", headers=headers_b)
    assert res_del_b.status_code == 404

    # User A successfully DELETES their own conversation -> 204 No Content
    res_del_a = client.delete(f"/api/v1/conversations/{conv_a_id}", headers=headers_a)
    assert res_del_a.status_code == 204

    # Confirm conversation is gone
    res_get_a = client.get(f"/api/v1/conversations/{conv_a_id}", headers=headers_a)
    assert res_get_a.status_code == 404

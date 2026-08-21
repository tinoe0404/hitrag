import time
import pytest
from unittest.mock import patch, MagicMock
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

def _mock_gemini_text(text: str):
    mock_part = MagicMock()
    mock_part.text = text
    mock_candidate = MagicMock()
    mock_candidate.content.parts = [mock_part]
    mock_response = MagicMock()
    mock_response.candidates = [mock_candidate]
    return mock_response

@pytest.fixture
def mock_embed_and_gemini():
    with patch("app.rag.retrieval.embed_text") as mock_embed, \
         patch("app.rag.generation._get_client") as mock_gen_client:
        
        # Mock embedding to return a dummy 768 float list
        mock_embed.return_value = [0.1] * 768
        
        # Mock Gemini generation client
        mock_client = MagicMock()
        mock_gen_client.return_value = mock_client
        
        yield mock_client

def test_chat_creates_new_conversation_and_messages(mock_embed_and_gemini):
    mock_client = mock_embed_and_gemini
    mock_client.models.generate_content.return_value = _mock_gemini_text(
        '{"status": "ANSWERED", "answer": "The passing mark is 50%."}'
    )
    
    headers = get_auth_header("chat_new")
    
    # 1. Ask a question omitting conversation_id
    response = client.post(
        "/api/v1/chat",
        json={"question": "What is the passing mark?"},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    
    conv_id = data["conversation_id"]
    message_id = data["message_id"]
    assert conv_id > 0
    assert message_id > 0
    assert data["status"] == "ANSWERED"
    assert data["answer"] == "The passing mark is 50%."
    assert isinstance(data["citations"], list)
    
    # 2. Verify messages are persisted in chronological order
    res_msgs = client.get(f"/api/v1/conversations/{conv_id}/messages", headers=headers)
    assert res_msgs.status_code == 200
    messages = res_msgs.json()
    assert len(messages) == 2
    
    assert messages[0]["role"].lower() == "user"
    assert messages[0]["content"] == "What is the passing mark?"
    
    assert messages[1]["role"].lower() == "assistant"
    assert messages[1]["content"] == "The passing mark is 50%."
    assert messages[1]["id"] == message_id

def test_chat_appends_to_existing_conversation(mock_embed_and_gemini):
    mock_client = mock_embed_and_gemini
    mock_client.models.generate_content.return_value = _mock_gemini_text(
        '{"status": "ANSWERED", "answer": "Yes, that is correct."}'
    )
    
    headers = get_auth_header("chat_existing")
    
    # 1. Create a conversation first via endpoints
    res_conv = client.post(
        "/api/v1/conversations",
        json={"title": "Custom Chat Session"},
        headers=headers
    )
    conv_id = res_conv.json()["id"]
    
    # 2. Ask a question targeting this conversation_id
    response = client.post(
        "/api/v1/chat",
        json={"question": "Is attendance mandatory?", "conversation_id": conv_id},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["conversation_id"] == conv_id
    
    # 3. Verify messages lists
    res_msgs = client.get(f"/api/v1/conversations/{conv_id}/messages", headers=headers)
    messages = res_msgs.json()
    assert len(messages) == 2
    assert messages[0]["role"].lower() == "user"
    assert messages[1]["role"].lower() == "assistant"

def test_chat_unauthorized_conversation_ownership(mock_embed_and_gemini):
    headers_a = get_auth_header("chat_owner_a")
    headers_b = get_auth_header("chat_owner_b")
    
    # Create conversation owned by User A
    res_conv = client.post(
        "/api/v1/conversations",
        json={"title": "User A Private Chat"},
        headers=headers_a
    )
    conv_a_id = res_conv.json()["id"]
    
    # User B tries to POST to User A's conversation -> 404 Not Found
    response = client.post(
        "/api/v1/chat",
        json={"question": "Can I see this?", "conversation_id": conv_a_id},
        headers=headers_b
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Conversation not found"

def test_chat_refusal_returns_not_enough_information(mock_embed_and_gemini):
    mock_client = mock_embed_and_gemini
    mock_client.models.generate_content.return_value = _mock_gemini_text(
        '{"status": "NOT_ENOUGH_INFORMATION", "answer": ""}'
    )
    
    headers = get_auth_header("chat_refusal")
    
    # Ask a gardening question that should refuse
    response = client.post(
        "/api/v1/chat",
        json={"question": "How do I grow tomatoes?"},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "NOT_ENOUGH_INFORMATION"
    assert data["answer"] == ""
    assert data["citations"] == []
    
    # Confirm it gets persisted as a message with NOT_ENOUGH_INFO_MESSAGE
    conv_id = data["conversation_id"]
    res_msgs = client.get(f"/api/v1/conversations/{conv_id}/messages", headers=headers)
    messages = res_msgs.json()
    assert len(messages) == 2
    assert messages[0]["role"].lower() == "user"
    assert messages[1]["role"].lower() == "assistant"
    # User-facing text stored in DB
    from app.rag.generation import NOT_ENOUGH_INFO_MESSAGE
    assert messages[1]["content"] == NOT_ENOUGH_INFO_MESSAGE

def test_chat_parse_error_is_persisted_with_debug_text(mock_embed_and_gemini):
    mock_client = mock_embed_and_gemini
    # Completely non-JSON response trigger PARSE_ERROR
    mock_client.models.generate_content.return_value = _mock_gemini_text(
        "I cannot answer that based on the context."
    )
    
    headers = get_auth_header("chat_parse_error")
    
    response = client.post(
        "/api/v1/chat",
        json={"question": "Unparseable query?"},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PARSE_ERROR"
    assert data["answer"] == ""
    assert data["citations"] == []
    
    # Confirm persisted assistant message has the distinguishable parse error text
    conv_id = data["conversation_id"]
    res_msgs = client.get(f"/api/v1/conversations/{conv_id}/messages", headers=headers)
    messages = res_msgs.json()
    assert len(messages) == 2
    assert messages[0]["role"].lower() == "user"
    assert messages[1]["role"].lower() == "assistant"
    from app.rag.generation import NOT_ENOUGH_INFO_MESSAGE
    assert messages[1]["content"] == f"[System Parse Error] {NOT_ENOUGH_INFO_MESSAGE}"

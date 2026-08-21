#!/usr/bin/env python3
"""Execute real chat requests against the running FastAPI server.
Verifies Phase 20 RAG chat endpoint works end-to-end.
"""
import time
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def main():
    print("=" * 80)
    print("PHASE 20: CHAT END-TO-END DEMO")
    print("=" * 80)

    # 1. Register a test user
    email = f"chat_tester_{int(time.time())}@hit.ac.zw"
    password = "Password123!"
    reg_url = f"{BASE_URL}/api/v1/auth/register"
    print(f"\n1. Registering user '{email}'...")
    res = requests.post(reg_url, json={
        "email": email,
        "password": password,
        "full_name": "Chat Tester",
        "role": "ADMIN"  # Admin role can query admissions and other regulations
    })
    print(f"   Registration status: {res.status_code}")

    # 2. Login to obtain access token
    login_url = f"{BASE_URL}/api/v1/auth/login"
    print(f"\n2. Logging in...")
    res = requests.post(login_url, data={
        "username": email,
        "password": password
    })
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"   Login success. Token: {token[:20]}...")

    # 3. Start a new conversation via Chat (Question 1)
    chat_url = f"{BASE_URL}/api/v1/chat"
    q1 = "What are the admissions requirements for undergraduate engineering at HIT?"
    print(f"\n3. Chat Q1 (New Conversation): '{q1}'")
    res = requests.post(chat_url, json={"question": q1}, headers=headers)
    assert res.status_code == 200, res.text
    r1 = res.json()
    print("   Response:")
    print(json.dumps(r1, indent=2))

    conv_id = r1["conversation_id"]

    # 4. Continue same conversation (Question 2)
    q2 = "What is the grading structure and what percentage is needed for a first class?"
    print(f"\n4. Chat Q2 (Continue Conversation {conv_id}): '{q2}'")
    res = requests.post(chat_url, json={"question": q2, "conversation_id": conv_id}, headers=headers)
    assert res.status_code == 200, res.text
    r2 = res.json()
    print("   Response:")
    print(json.dumps(r2, indent=2))

    # 5. Ask a refusal question in the same conversation
    q3 = "How do I set up a hydroponics system for tomatoes?"
    print(f"\n5. Chat Q3 (Refusal in Conversation {conv_id}): '{q3}'")
    res = requests.post(chat_url, json={"question": q3, "conversation_id": conv_id}, headers=headers)
    assert res.status_code == 200, res.text
    r3 = res.json()
    print("   Response:")
    print(json.dumps(r3, indent=2))

    print("\n" + "=" * 80)
    print("Demo completed successfully.")
    print("=" * 80)

if __name__ == "__main__":
    main()

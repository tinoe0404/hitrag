#!/usr/bin/env python3
"""
Developer Helper Script for Phase 15 Access Verification
=========================================================
Generates a restricted PDF document with the secret fact: "the internal audit code is XJ-9",
registers a temporary admin, uploads the document under ADMIN-tier, and triggers the manual ingestion pipeline.
"""

import sys
import os
import time
import httpx
import fitz

BASE_URL = "http://localhost:8000"


def main():
    print("Generating synthetic restricted PDF...")
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 72), "CONFIDENTIAL HARARE INSTITUTE OF TECHNOLOGY SYSTEM AUDIT.\n\n"
                              "This document is classified under the ADMIN-only tier.\n"
                              "Verification details: The internal audit code is XJ-9.\n"
                              "Unauthorized disclosure of the XJ-9 code is strictly prohibited.", fontsize=12)
    pdf_bytes = doc.write()
    doc.close()

    # Create client
    client = httpx.Client(base_url=BASE_URL, timeout=30.0)

    # 1. Register temporary Admin
    admin_email = f"audit_admin_{int(time.time())}@hit.ac.zw"
    password = "Password123!"
    print(f"Registering temporary admin: {admin_email}")
    reg_res = client.post("/api/v1/auth/register", json={
        "email": admin_email,
        "password": password,
        "full_name": "Audit Verification Admin",
        "role": "ADMIN"
    })
    if reg_res.status_code not in (200, 201):
        print(f"Failed to register admin: {reg_res.text}")
        sys.exit(1)

    # 2. Login to get Auth Token
    print("Logging in to obtain OAuth2 token...")
    login_res = client.post("/api/v1/auth/login", data={
        "username": admin_email,
        "password": password
    })
    if login_res.status_code != 200:
        print(f"Login failed: {login_res.text}")
        sys.exit(1)
    
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Upload restricted document under ADMIN tier
    print("Uploading restricted PDF under ADMIN access tier...")
    files = {"file": ("restricted_audit.pdf", pdf_bytes, "application/pdf")}
    upload_res = client.post(
        "/api/v1/documents",
        headers=headers,
        files=files,
        data={"title": "Confidential System Audit 2026", "access_tier": "ADMIN"}
    )
    if upload_res.status_code != 201:
        print(f"Upload failed: {upload_res.text}")
        sys.exit(1)

    doc_id = upload_res.json()["id"]
    print(f"Document uploaded successfully! ID: {doc_id}")

    # 4. Trigger Ingestion manual pipeline (Phase 13 endpoint)
    print(f"Triggering pipeline ingestion for document {doc_id}...")
    ingest_res = client.post(f"/api/v1/documents/{doc_id}/ingest", headers=headers)
    if ingest_res.status_code != 200:
        print(f"Ingestion failed: {ingest_res.text}")
        sys.exit(1)

    print("\nIngestion Result:")
    print(ingest_res.json())
    print("\nSuccess! Synthetic restricted document XJ-9 is now indexed and searchable under ADMIN tier.")


if __name__ == "__main__":
    main()

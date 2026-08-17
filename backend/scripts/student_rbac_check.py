#!/usr/bin/env python3
"""Run admissions query through the full pipeline as a STUDENT-role user."""
import sys
sys.path.insert(0, ".")

from app.db.session import SessionLocal
from app.models.enums import UserRole
from app.rag.retrieval import retrieve
from app.rag.generation import generate_answer

def main():
    db = SessionLocal()
    # STUDENT role allowed tiers
    allowed_tiers = [UserRole.PUBLIC, UserRole.STUDENT]
    query = "What are the admissions requirements for undergraduate engineering at HIT?"

    print("=" * 80)
    print("STUDENT Role Generation & Citation Check")
    print("=" * 80)

    # 1. Retrieve chunks with STUDENT tiers
    chunks = retrieve(db=db, query=query, allowed_tiers=allowed_tiers, top_k=5)
    print(f"Retrieved {len(chunks)} chunks:")
    for idx, c in enumerate(chunks, start=1):
        print(f"  [{idx}] Chunk ID: {c['chunk_id']}, Doc: {c['document_title']} (Page {c['page_number']})")

    # 2. Generate answer
    result = generate_answer(query, chunks)
    print("\nResult:")
    print(f"  Status    : {result.status}")
    print(f"  Answer    : {result.answer}")
    print(f"  Citations :")
    for idx, cite in enumerate(result.citations, start=1):
        print(f"    [{idx}] {cite['document_title']} (Page {cite['page_number']})")
        print(f"        document_id : {cite['document_id']}")
        print(f"        chunk_ids   : {cite['chunk_ids']}")

    # 3. Explicit check for leak of doc 106 (Confidential System Audit 2026)
    doc_106_found = any(c['document_id'] == 106 for c in result.citations)
    print("\nRBAC Audit:")
    if doc_106_found:
        print("  WARNING: SECURITY LEAK! Document 106 is cited!")
    else:
        print("  PASS: No security leak. Document 106 is NOT cited.")

    db.close()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Run retrieval directly for the three working questions as ADMIN."""
import sys
sys.path.insert(0, ".")

from app.db.session import SessionLocal
from app.models.enums import UserRole
from app.rag.retrieval import retrieve

WORKING_QUESTIONS = [
    "What are the admissions requirements for undergraduate engineering at HIT?",
    "What is the grading structure and what percentage is needed for a first class?",
    "How long is the industrial attachment and when does it take place?",
]

def main():
    db = SessionLocal()
    allowed_tiers = [UserRole.PUBLIC, UserRole.STUDENT, UserRole.LECTURER, UserRole.ADMIN]

    print("=" * 80)
    print("Direct Retrieval Check (top_k=5, ADMIN-tier)")
    print("=" * 80)

    for i, q in enumerate(WORKING_QUESTIONS, start=1):
        print(f"\nQuestion {i}: {q}")
        results = retrieve(db=db, query=q, allowed_tiers=allowed_tiers, top_k=5)
        for idx, r in enumerate(results, start=1):
            print(f"  [{idx}] Chunk ID: {r['chunk_id']}, Doc: {r['document_title']} (Page {r['page_number']})")
            print(f"      Similarity : {r['cosine_similarity']:.6f} (Distance: {r['cosine_distance']:.6f})")

    db.close()

if __name__ == "__main__":
    main()

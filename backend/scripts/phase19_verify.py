#!/usr/bin/env python3
"""Phase 19 verification script.

Runs all 3 Phase-17/18 working questions through generate_answer()
and prints the raw status, answer, AND citations for each.

Usage:
    cd backend && .venv/bin/python scripts/phase19_verify.py
"""
import sys
import json
sys.path.insert(0, ".")

from app.db.session import SessionLocal
from app.models.enums import UserRole
from app.rag.retrieval import retrieve
from app.rag.generation import generate_answer, NOT_ENOUGH_INFO_MESSAGE


# Phase 17's 3 working questions (should be ANSWERED with citations)
WORKING_QUESTIONS = [
    "What are the admissions requirements for undergraduate engineering at HIT?",
    "What is the grading structure and what percentage is needed for a first class?",
    "How long is the industrial attachment and when does it take place?",
]

# Phase 18's refusal questions (should be NOT_ENOUGH_INFORMATION with no citations)
REFUSAL_QUESTIONS = [
    "How do I set up a hydroponics system for tomatoes?",
    "What is the process for appealing a grade?",
]


def main():
    db = SessionLocal()
    # Use ADMIN tiers so retrieval isn't access-restricted
    allowed_tiers = [UserRole.PUBLIC, UserRole.STUDENT, UserRole.LECTURER, UserRole.ADMIN]

    print("=" * 72)
    print("Phase 19 Verification: Citation Tracking on Grounded Answers")
    print("=" * 72)

    print("\n--- Running Working Questions ---")
    for i, question in enumerate(WORKING_QUESTIONS, start=1):
        print(f"\nQuestion {i}: {question}")
        try:
            # Retrieve chunks
            chunks = retrieve(db=db, query=question, allowed_tiers=allowed_tiers, top_k=5)
            
            # Generate answer (with citations)
            result = generate_answer(question, chunks)
            
            print(f"  Status    : {result.status}")
            print(f"  Answer    : {result.answer}")
            print(f"  Citations :")
            if result.citations:
                for idx, cite in enumerate(result.citations, start=1):
                    print(f"    [{idx}] {cite['document_title']} (Page {cite['page_number']})")
                    print(f"        document_id : {cite['document_id']}")
                    print(f"        chunk_id    : {cite['chunk_id']}")
                    print(f"        chunk_ids   : {cite['chunk_ids']}")
            else:
                print("    (No citations attached)")
        except Exception as e:
            print(f"  ERROR     : {type(e).__name__}: {e}")

    print("\n--- Running Refusal Questions ---")
    for i, question in enumerate(REFUSAL_QUESTIONS, start=1):
        print(f"\nRefusal Question {i}: {question}")
        try:
            # Retrieve chunks (irrelevant context)
            chunks = retrieve(db=db, query=question, allowed_tiers=allowed_tiers, top_k=5)
            
            # Generate answer
            result = generate_answer(question, chunks)
            
            print(f"  Status    : {result.status}")
            print(f"  Answer    : {result.answer if result.answer else '(empty)'}")
            print(f"  Citations : {result.citations}")
        except Exception as e:
            print(f"  ERROR     : {type(e).__name__}: {e}")

    print("\n" + "=" * 72)
    print("Done.")
    db.close()


if __name__ == "__main__":
    main()

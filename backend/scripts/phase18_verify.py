#!/usr/bin/env python3
"""Phase 18 verification script.

Runs all 3 Phase-17 working questions and both refusal questions through
generate_answer() and prints the raw status + answer for each.

Usage:
    cd backend && .venv/bin/python scripts/phase18_verify.py
"""
import sys
sys.path.insert(0, ".")

from app.db.session import SessionLocal
from app.models.enums import UserRole
from app.rag.retrieval import retrieve
from app.rag.generation import generate_answer, NOT_ENOUGH_INFO_MESSAGE


# Phase 17's 3 working questions (should be ANSWERED)
WORKING_QUESTIONS = [
    "What are the admissions requirements for undergraduate engineering at HIT?",
    "What is the grading structure and what percentage is needed for a first class?",
    "How long is the industrial attachment and when does it take place?",
]

# Phase 18 refusal questions (should be NOT_ENOUGH_INFORMATION)
REFUSAL_QUESTIONS = [
    "How do I set up a hydroponics system for tomatoes?",
    "What is the process for appealing a grade?",
]


def main():
    db = SessionLocal()
    # Use ADMIN tiers so retrieval isn't access-restricted
    allowed_tiers = [UserRole.PUBLIC, UserRole.STUDENT, UserRole.LECTURER, UserRole.ADMIN]

    print("=" * 72)
    print("Phase 18 Verification: Grounded Answer Classification")
    print("=" * 72)

    all_questions = [
        ("WORKING", q) for q in WORKING_QUESTIONS
    ] + [
        ("REFUSAL", q) for q in REFUSAL_QUESTIONS
    ]

    for label, question in all_questions:
        print(f"\n--- [{label}] {question}")
        try:
            chunks = retrieve(db=db, query=question, allowed_tiers=allowed_tiers, top_k=5)
            result = generate_answer(question, chunks)
            print(f"    status : {result.status}")
            print(f"    answer : {result.answer[:300] if result.answer else '(empty)'}")
        except Exception as e:
            print(f"    ERROR  : {type(e).__name__}: {e}")

    print("\n" + "=" * 72)
    print("Done.")
    db.close()


if __name__ == "__main__":
    main()

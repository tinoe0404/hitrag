#!/usr/bin/env python3
"""
scripts/embed_check.py — Phase 11 Smoke Test
=============================================
Quick script to verify Gemini embedding API connectivity with a real call.

Usage:
    cd backend
    ./.venv/bin/python scripts/embed_check.py

Expects GEMINI_API_KEY in .env (or environment variable).
"""

import sys
import os

# Ensure the backend app is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rag.embeddings import embed_text, embed_texts, EMBEDDING_DIMENSIONALITY, EmbeddingError


def main():
    print("=" * 60)
    print("Phase 11: Gemini Embedding Smoke Test")
    print("=" * 60)

    # Test 1: Single text embedding
    print("\n[1] embed_text('Hello, Harare Institute of Technology')")
    try:
        vec = embed_text("Hello, Harare Institute of Technology")
        print(f"    ✅ Got vector of length {len(vec)}")
        print(f"    Expected dimensionality: {EMBEDDING_DIMENSIONALITY}")
        assert len(vec) == EMBEDDING_DIMENSIONALITY, f"Expected {EMBEDDING_DIMENSIONALITY}, got {len(vec)}"
        print(f"    First 5 values: {vec[:5]}")
        print(f"    Last 5 values:  {vec[-5:]}")
    except EmbeddingError as e:
        print(f"    ❌ EmbeddingError: {e}")
        sys.exit(1)

    # Test 2: Batch embedding
    print("\n[2] embed_texts(['Academic regulations', 'Exam grading', 'Industrial attachment'])")
    try:
        texts = ["Academic regulations", "Exam grading", "Industrial attachment"]
        vecs = embed_texts(texts)
        print(f"    ✅ Got {len(vecs)} vectors")
        for i, v in enumerate(vecs):
            print(f"    Vector {i}: len={len(v)}, first 3 values={v[:3]}")
        assert all(len(v) == EMBEDDING_DIMENSIONALITY for v in vecs)
    except EmbeddingError as e:
        print(f"    ❌ EmbeddingError: {e}")
        sys.exit(1)

    # Test 3: Empty text returns empty list (no API call)
    print("\n[3] embed_text('')  — should return [] without API call")
    result = embed_text("")
    assert result == [], f"Expected [], got {result}"
    print(f"    ✅ Got {result}")

    # Test 4: Mixed batch with empty texts
    print("\n[4] embed_texts(['', 'Real text', '  '])  — mixed empty/real")
    try:
        vecs = embed_texts(["", "Real text", "  "])
        print(f"    ✅ Got {len(vecs)} results")
        print(f"    [0] empty: len={len(vecs[0])}")
        print(f"    [1] real:  len={len(vecs[1])}")
        print(f"    [2] empty: len={len(vecs[2])}")
        assert vecs[0] == []
        assert len(vecs[1]) == EMBEDDING_DIMENSIONALITY
        assert vecs[2] == []
    except EmbeddingError as e:
        print(f"    ❌ EmbeddingError: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✅ All smoke tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()

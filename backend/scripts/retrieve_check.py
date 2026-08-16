#!/usr/bin/env python3
"""
Developer Helper Script for Phase 14 Retrieval Verification
============================================================
Allows quick testing of semantic search queries against the database chunks.

Usage:
  python scripts/retrieve_check.py "your search query here" --top_k 5
"""

import sys
import argparse
import os

# Adjust path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.rag.retrieval import retrieve
from app.rag.embeddings import EmbeddingError


def main():
    parser = argparse.ArgumentParser(description="Test retrieval query against postgres vector index.")
    parser.add_argument("query", type=str, help="The query string to embed and search for.")
    parser.add_argument("--top_k", type=int, default=5, help="Number of top results to return.")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        print(f"\nSearching for: '{args.query}' (top_k={args.top_k})\n" + "=" * 80)
        results = retrieve(db, args.query, top_k=args.top_k)
        
        if not results:
            print("No matching chunks found in database.")
            return

        for idx, res in enumerate(results, 1):
            print(f"\n[Result {idx}] Score: {res['cosine_similarity']:.6f} | Distance: {res['cosine_distance']:.6f}")
            print(f"Doc ID: {res['document_id']} | Page: {res['page_number']} | Chunk ID: {res['chunk_id']}")
            print("-" * 80)
            print(res["content"].strip())
            print("=" * 80)

    except ValueError as e:
        print(f"Validation Error: {e}", file=sys.stderr)
    except EmbeddingError as e:
        print(f"Embedding API Error: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
    finally:
        db.close()


if __name__ == "__main__":
    main()

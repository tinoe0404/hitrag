#!/usr/bin/env python3
"""
scripts/pipeline_check.py — Phase 12 End-to-End Ingestion Pipeline Verification
=============================================================================
Runs the full ingestion pipeline:
Extract -> Clean -> Chunk -> Embed -> Persist
against a stored document (default ID: 24).

Usage:
    cd backend
    ./.venv/bin/python scripts/pipeline_check.py [document_id]
"""

import sys
import os

# Ensure the backend app is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.document import Document
from app.models.chunk import Chunk
from app.services.document import extract_document


def main():
    print("=" * 70)
    print("Phase 12: End-to-End Ingestion Pipeline Verification")
    print("=" * 70)

    # Determine document ID
    doc_id = 24
    if len(sys.argv) > 1:
        try:
            doc_id = int(sys.argv[1])
        except ValueError:
            print(f"❌ Invalid document ID argument: {sys.argv[1]}. Using default 24.")

    db = SessionLocal()
    try:
        # 1. Fetch document metadata
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            print(f"❌ Document with ID {doc_id} not found in the database.")
            # List available documents for user reference
            docs = db.query(Document).all()
            if docs:
                print("Available documents:")
                for d in docs:
                    print(f"  - ID: {d.id}, Title: {d.title}, Status: {d.status}")
            sys.exit(1)

        print(f"📄 Found document: '{doc.title}' (ID: {doc.id})")
        print(f"   Storage path: {doc.storage_path}")
        print(f"   Initial status: {doc.status}")

        # 2. Run the end-to-end pipeline
        print("\n⚙️ Running pipeline (Extract -> Clean -> Chunk -> Embed -> Persist)...")
        result = extract_document(db, doc.id)

        # Refresh doc row from DB
        db.refresh(doc)
        print(f"✅ Pipeline completed successfully!")
        print(f"   Updated status: {doc.status}")

        # 3. Retrieve chunks and embeddings from database
        chunks = db.query(Chunk).filter(Chunk.document_id == doc.id).order_by(Chunk.chunk_index).all()
        print(f"\n📊 Persistence Statistics:")
        print(f"   Total chunks created: {len(chunks)}")
        
        non_null_embeddings_count = sum(1 for c in chunks if c.embedding is not None)
        print(f"   Chunks with non-null embeddings: {non_null_embeddings_count}")

        # Validate dimensionality
        dims_match = True
        for c in chunks:
            if c.embedding is not None:
                if len(c.embedding) != 768:
                    dims_match = False
                    print(f"   ❌ Dimensionality error for chunk {c.chunk_index}: length is {len(c.embedding)}")

        if dims_match and non_null_embeddings_count == len(chunks):
            print(f"   ✅ All chunks have correct vector dimensionality (768).")
        else:
            print(f"   ❌ Some chunks have incorrect or missing embeddings.")

        # 4. Display a sample of the first chunk and its vector
        if chunks:
            sample = chunks[0]
            print(f"\n🔍 Sample Chunk (Index {sample.chunk_index}, Page {sample.page_number}):")
            print("-" * 50)
            print(sample.content[:150] + "..." if len(sample.content) > 150 else sample.content)
            print("-" * 50)
            print(f"Vector preview (first 5 elements): {sample.embedding[:5]}")
            print(f"Vector preview (last 5 elements):  {sample.embedding[-5:]}")

    except Exception as e:
        print(f"\n❌ Error during pipeline execution: {e}")
        # Clean up session
        db.rollback()
        raise e
    finally:
        db.close()

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()

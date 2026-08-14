#!/usr/bin/env python3
"""
scripts/extract_check.py — Dev/testing convenience for Phase 8 extraction.

Usage:
    PYTHONPATH=. ./.venv/bin/python scripts/extract_check.py <document_id>

Triggers text extraction for a given document ID, prints per-page output summary,
and writes the full extracted JSON to uploads/<uuid>.extracted.json.

This script is a manual testing tool and is NOT part of the production pipeline.
The real ingestion pipeline is built at Phase 13.
"""
import sys
import json

# Ensure app modules are importable
from app.db.session import SessionLocal
from app.services.document import extract_document
from app.repositories.document import get_document_by_id


def main():
    if len(sys.argv) < 2:
        print("Usage: PYTHONPATH=. ./.venv/bin/python scripts/extract_check.py <document_id>")
        sys.exit(1)

    doc_id = int(sys.argv[1])
    db = SessionLocal()

    try:
        doc = get_document_by_id(db, doc_id)
        if not doc:
            print(f"ERROR: Document ID {doc_id} not found in database.")
            sys.exit(1)

        print(f"--- Extracting Document ID={doc.id} ---")
        print(f"    Title:        {doc.title}")
        print(f"    Filename:     {doc.filename}")
        print(f"    Storage Path: {doc.storage_path}")
        print(f"    Status:       {doc.status}")
        print()

        result = extract_document(db, doc_id)

        print(f"--- Extraction Complete ---")
        print(f"    Total Pages:        {result.total_pages}")
        print(f"    Pages With Text:    {result.pages_with_text}")
        print(f"    Pages Without Text: {result.pages_without_text}")
        print(f"    Extraction Status:  {result.extraction_status}")
        print()

        # Print first 500 chars of each page as a preview
        for page in result.pages:
            preview = page.text[:500].replace('\n', '\\n') if page.text else "(empty)"
            status_icon = "✓" if page.has_text else "✗"
            print(f"  [{status_icon}] Page {page.page_number}: {preview}")
            if len(page.text) > 500:
                print(f"      ... ({len(page.text)} total chars)")
            print()

        # Show JSON output path
        json_path = doc.storage_path.rsplit(".", 1)[0] + ".extracted.json"
        print(f"Full extracted JSON written to: {json_path}")

        # Refresh doc to show updated status
        db.refresh(doc)
        print(f"Document status updated to: {doc.status}")

    finally:
        db.close()


if __name__ == "__main__":
    main()

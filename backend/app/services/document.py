from typing import List
import json
import os
import time
import logging
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session

logger = logging.getLogger("hitrag.ingestion")

from app.models.document import Document
from app.models.enums import UserRole, DocumentStatus
from app.models.user import User
from app.core.files import save_upload, delete_upload_file
from app.rag.extraction import extract_pages, ExtractionResult, ExtractionError
import app.repositories.document as repo

def service_upload_document(
    db: Session,
    user: User,
    file: UploadFile,
    title: str,
    access_tier: UserRole,
) -> Document:
    """
    Business logic for uploading document:
    1. Validates tier authorization (STUDENT/PUBLIC users cannot set access_tier above STUDENT).
    2. Streams file to disk via save_upload().
    3. Saves Document row with status="PENDING".
    """
    # Enforce tier escalation restriction: STUDENT cannot set LECTURER or ADMIN access tier
    if user.role in (UserRole.STUDENT, UserRole.PUBLIC) and access_tier in (UserRole.LECTURER, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Users with role '{user.role.value}' are not permitted to set access tier to '{access_tier.value}'."
        )

    clean_title = title.strip() if title and title.strip() else (file.filename or "Untitled Document")

    # Stream & save file
    generated_filename, storage_path = save_upload(file)

    # Persist DB record
    return repo.create_document(
        db=db,
        title=clean_title,
        filename=file.filename or generated_filename,
        storage_path=storage_path,
        access_tier=access_tier,
        uploaded_by=user.id,
        status=DocumentStatus.UPLOADED,
    )

def service_list_documents(db: Session, allowed_tiers: List[UserRole]) -> List[Document]:
    """Retrieve list of documents filtered to tiers accessible to user."""
    return repo.list_documents_for_tiers(db, allowed_tiers)

def service_get_document(db: Session, document_id: int, allowed_tiers: List[UserRole]) -> Document:
    """
    Retrieve document by ID.
    Returns 404 Not Found if document does not exist OR if document access_tier is not in allowed_tiers,
    preventing document existence leakage across security boundaries.
    """
    doc = repo.get_document_by_id(db, document_id)
    if not doc or doc.access_tier not in allowed_tiers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    return doc

def service_delete_document(db: Session, document_id: int, allowed_tiers: List[UserRole]) -> None:
    """
    Delete document DB record and disk file.
    Enforces document visibility check (returns 404 if inaccessible).
    Handles missing disk files gracefully without failing.
    """
    doc = service_get_document(db, document_id, allowed_tiers)
    
    # Clean up disk file
    delete_upload_file(doc.storage_path)
    
    # Delete DB record
    repo.delete_document_record(db, doc)


def extract_document(db: Session, document_id: int) -> ExtractionResult:
    """
    Trigger text extraction for a stored document.

    Design decision — extracted text storage:
    The extracted per-page JSON is written to a .json file alongside the original PDF
    under uploads/ (e.g. abc123.pdf -> abc123.extracted.json). This approach:
    - Keeps the DB lean (no large TEXT blobs in rows).
    - Gives Phase 9 (cleaning) and Phase 10 (chunking) a simple file path to read from.
    - Is easy to inspect/debug by eyeballing the JSON on disk.
    - Avoids needing a new DB table just for raw extraction output that is transient
      (it gets consumed and replaced by cleaned chunks in later phases).

    On success: Document.status -> EXTRACTED, returns ExtractionResult.
    On failure: Document.status -> EXT_FAILED, raises HTTPException.
    """
    doc = repo.get_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Update status to PROCESSING
    doc.status = DocumentStatus.PROCESSING
    db.commit()

    try:
        result = extract_pages(doc.storage_path)
    except ExtractionError as e:
        doc.status = DocumentStatus.EXT_FAILED
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Extraction failed for document {document_id}: {str(e)}"
        )

    # Clean the extracted pages in-place
    from app.rag.cleaning import clean_pages
    cleaned_dicts = clean_pages(result.to_dict_list())
    for idx, p_dict in enumerate(cleaned_dicts):
        result.pages[idx].text = p_dict["text"]
        result.pages[idx].has_text = p_dict["has_text"]

    # Write extracted JSON alongside the PDF
    json_path = doc.storage_path.rsplit(".", 1)[0] + ".extracted.json"
    extraction_data = {
        "document_id": doc.id,
        "total_pages": result.total_pages,
        "pages_with_text": result.pages_with_text,
        "pages_without_text": result.pages_without_text,
        "extraction_status": result.extraction_status,
        "pages": result.to_dict_list(),
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(extraction_data, f, ensure_ascii=False, indent=2)

    # Chunk the cleaned text pages (Phase 10)
    from app.rag.chunking import chunk_pages
    chunks = chunk_pages(result.to_dict_list(), doc.id)
    repo.bulk_insert_chunks(db, doc.id, chunks)

    # Update document status to CHUNKED
    doc.status = DocumentStatus.CHUNKED
    db.commit()

    # Embed and persist chunk vectors (Phase 12)
    from app.rag.embeddings import embed_document_chunks
    embed_document_chunks(db, doc.id)

    db.refresh(doc)
    return result


def ingest_document(db: Session, document_id: int, force: bool = False) -> dict:
    """
    Manually triggers the end-to-end ingestion pipeline:
    Extract ➔ Clean ➔ Chunk ➔ Embed ➔ Persist.
    
    Semantics of re-running:
    - If status is already EMBEDDED, raise HTTPException (400 Bad Request) unless force=True.
    - If force=True, re-run everything (overwriting/recreating chunks and embeddings).
    """
    doc = repo.get_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Check state where ingestion makes sense
    if doc.status == DocumentStatus.EMBEDDED and not force:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document is already fully ingested and embedded. Use force=True to re-ingest."
        )

    start_time = time.time()
    chunk_count = 0
    embedded_count = 0
    failed_embed_count = 0

    try:
        # --- 1. Extraction ---
        doc.status = DocumentStatus.EXTRACTING
        db.commit()

        try:
            extraction_result = extract_pages(doc.storage_path)
        except ExtractionError as e:
            doc.status = DocumentStatus.EXT_FAILED
            db.commit()
            logger.error(f"Ingestion extraction failed for doc {document_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Extraction failed: {str(e)}"
            )

        doc.status = DocumentStatus.EXTRACTED
        db.commit()

        # --- 2. Cleaning ---
        doc.status = DocumentStatus.CLEANING
        db.commit()

        from app.rag.cleaning import clean_pages
        cleaned_pages = clean_pages(extraction_result.to_dict_list())

        # Update in-memory extraction result pages with cleaned text
        for idx, p_dict in enumerate(cleaned_pages):
            extraction_result.pages[idx].text = p_dict["text"]
            extraction_result.pages[idx].has_text = p_dict["has_text"]

        # Write the cleaned/extracted JSON on disk alongside the PDF
        json_path = doc.storage_path.rsplit(".", 1)[0] + ".extracted.json"
        extraction_data = {
            "document_id": doc.id,
            "total_pages": extraction_result.total_pages,
            "pages_with_text": extraction_result.pages_with_text,
            "pages_without_text": extraction_result.pages_without_text,
            "extraction_status": extraction_result.extraction_status,
            "pages": extraction_result.to_dict_list(),
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(extraction_data, f, ensure_ascii=False, indent=2)

        doc.status = DocumentStatus.CLEANED
        db.commit()

        # --- 3. Chunking ---
        doc.status = DocumentStatus.CHUNKING
        db.commit()

        from app.rag.chunking import chunk_pages
        chunks = chunk_pages(extraction_result.to_dict_list(), doc.id)
        repo.bulk_insert_chunks(db, doc.id, chunks)
        chunk_count = len(chunks)

        doc.status = DocumentStatus.CHUNKED
        db.commit()

        # --- 4. Embedding ---
        doc.status = DocumentStatus.EMBEDDING
        db.commit()

        try:
            from app.rag.embeddings import embed_document_chunks, EmbeddingError
            embed_document_chunks(db, doc.id)
        except Exception as e:
            # Catch embedding exceptions
            doc.status = DocumentStatus.EMB_FAILED
            db.commit()
            logger.error(f"Ingestion embedding failed for doc {document_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Embedding failed: {str(e)}"
            )

        # Retrieve count of successful vs failed embeddings
        from app.models.chunk import Chunk
        db_chunks = db.query(Chunk).filter(Chunk.document_id == doc.id).all()
        embedded_count = sum(1 for c in db_chunks if c.embedding is not None)
        failed_embed_count = len(db_chunks) - embedded_count

        db.refresh(doc)

    except HTTPException:
        # Re-raise HTTPExceptions as-is so FastAPI returns them directly
        raise
    except Exception as e:
        # Fallback general exception catcher
        doc.status = DocumentStatus.FAILED
        db.commit()
        logger.error(f"Ingestion pipeline failed unexpectedly for doc {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed due to an unexpected error: {str(e)}"
        )

    total_time = time.time() - start_time
    return {
        "document_id": doc.id,
        "status": doc.status,
        "total_chunks": chunk_count,
        "embedded_chunks": embedded_count,
        "failed_chunks": failed_embed_count,
        "time_taken_seconds": round(total_time, 2),
    }



from typing import List
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.enums import UserRole, DocumentStatus
from app.models.user import User
from app.core.files import save_upload, delete_upload_file
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
        status=DocumentStatus.PENDING,
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

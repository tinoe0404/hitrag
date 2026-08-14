from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.enums import UserRole
from app.core.deps import get_current_user, get_allowed_tiers, require_role
from app.schemas.document import DocumentOut
import app.services.document as service

documents_router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])

@documents_router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def upload_document(
    title: str = Form(...),
    access_tier: UserRole = Form(UserRole.PUBLIC),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a PDF document.
    Expects multipart/form-data with file, title, and access_tier fields.
    Validates PDF format, streams to uploads/ directory, and persists metadata.
    """
    return service.service_upload_document(
        db=db,
        user=current_user,
        file=file,
        title=title,
        access_tier=access_tier,
    )

@documents_router.get("", response_model=List[DocumentOut])
def list_documents(
    db: Session = Depends(get_db),
    allowed_tiers: List[UserRole] = Depends(get_allowed_tiers),
):
    """List documents filtered to tiers accessible to current user role."""
    return service.service_list_documents(db, allowed_tiers)

@documents_router.get("/{id}", response_model=DocumentOut)
def get_document(
    id: int,
    db: Session = Depends(get_db),
    allowed_tiers: List[UserRole] = Depends(get_allowed_tiers),
):
    """Get single document metadata (returns 404 if not found or if user tier is insufficient)."""
    return service.service_get_document(db, document_id=id, allowed_tiers=allowed_tiers)

@documents_router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    id: int,
    db: Session = Depends(get_db),
    allowed_tiers: List[UserRole] = Depends(get_allowed_tiers),
    admin_or_lecturer: User = Depends(require_role(UserRole.LECTURER, UserRole.ADMIN)),
):
    """
    Delete a document and its file on disk.
    Requires LECTURER or ADMIN role.
    """
    service.service_delete_document(db, document_id=id, allowed_tiers=allowed_tiers)

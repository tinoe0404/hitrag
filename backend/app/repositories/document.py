from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.models.document import Document
from app.models.enums import UserRole, DocumentStatus

def create_document(
    db: Session,
    title: str,
    filename: str,
    storage_path: str,
    access_tier: UserRole,
    uploaded_by: int,
    status: DocumentStatus = DocumentStatus.PENDING,
) -> Document:
    """Create and persist a new Document record into PostgreSQL."""
    doc = Document(
        title=title,
        filename=filename,
        storage_path=storage_path,
        access_tier=access_tier,
        uploaded_by=uploaded_by,
        status=status,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

def get_document_by_id(db: Session, document_id: int) -> Optional[Document]:
    """Retrieve a document by its primary key ID."""
    return db.scalar(select(Document).where(Document.id == document_id))

def list_documents_for_tiers(db: Session, allowed_tiers: List[UserRole]) -> List[Document]:
    """List documents whose access_tier is in the user's allowed_tiers list, most recent first."""
    stmt = (
        select(Document)
        .where(Document.access_tier.in_(allowed_tiers))
        .order_by(desc(Document.created_at), desc(Document.id))
    )
    return list(db.scalars(stmt).all())

def delete_document_record(db: Session, doc: Document) -> None:
    """Delete a document record from PostgreSQL (cascading related chunks)."""
    db.delete(doc)
    db.commit()

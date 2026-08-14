from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.models.user import User
from app.core.deps import require_role, get_allowed_tiers, get_current_user
from app.db.session import get_db
from app.services.document import extract_document

# ==============================================================================
# DEBUG / VERIFICATION ROUTER (Phase 5+ Proof of Concept)
#
# NOTE: These endpoints exist exclusively for automated pytest and manual
# verification. They are gated behind non-production debug routers and will be
# removed/hardened in Phase 30.
# ==============================================================================

debug_router = APIRouter(prefix="/api/v1/debug", tags=["Debug Verification"])

@debug_router.get("/admin-only")
def debug_admin_only(admin_user: User = Depends(require_role(UserRole.ADMIN))):
    """Debug route accessible ONLY to users with ADMIN role."""
    return {
        "message": "Access granted to admin-only resource.",
        "admin_email": admin_user.email,
        "role": admin_user.role,
    }

@debug_router.get("/my-tiers", response_model=List[UserRole])
def debug_my_tiers(allowed_tiers: List[UserRole] = Depends(get_allowed_tiers)):
    """Debug route returning the list of document access tiers accessible to current user."""
    return allowed_tiers

@debug_router.post("/extract/{document_id}")
def debug_extract_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.LECTURER, UserRole.ADMIN)),
):
    """
    DEBUG: Trigger text extraction for a single document.
    This is a dev/testing convenience endpoint for Phase 8 verification.
    The real ingestion pipeline endpoint is built at Phase 13.
    """
    result = extract_document(db, document_id)
    return {
        "document_id": document_id,
        "total_pages": result.total_pages,
        "pages_with_text": result.pages_with_text,
        "pages_without_text": result.pages_without_text,
        "extraction_status": result.extraction_status,
        "pages_preview": [
            {
                "page_number": p.page_number,
                "has_text": p.has_text,
                "text_length": len(p.text),
                "text_preview": p.text[:300] if p.text else "",
            }
            for p in result.pages
        ],
    }


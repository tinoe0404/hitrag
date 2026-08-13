from typing import List
from fastapi import APIRouter, Depends

from app.models.enums import UserRole
from app.models.user import User
from app.core.deps import require_role, get_allowed_tiers

# ==============================================================================
# DEBUG / VERIFICATION ROUTER (Phase 5 RBAC Proof of Concept)
#
# NOTE: These endpoints exist exclusively for Phase 5 automated pytest and manual
# verification of Role-Based Access Control dependencies. They are gated behind
# non-production debug routers and will be removed/hardened in Phase 30.
# ==============================================================================

debug_router = APIRouter(prefix="/api/v1/debug", tags=["Debug RBAC Verification"])

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

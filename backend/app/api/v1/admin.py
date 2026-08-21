from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth import UserOut
from app.schemas.user_role import RoleUpdate
from app.repositories.user import update_user_role, get_user_by_id
from app.core.deps import require_role

admin_router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])

@admin_router.put("/users/{user_id}/role", response_model=UserOut)
def update_user_role_endpoint(
    user_id: int,
    role_update: RoleUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN)),
):
    """Admin-only endpoint to change a user's role.

    Returns the updated user representation (UserOut).
    """
    target_user = get_user_by_id(db, user_id)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    updated_user = update_user_role(db, user_id, role_update.role)
    return updated_user

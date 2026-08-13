from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.enums import UserRole
from app.core.security import decode_access_token
from app.repositories.user import get_user_by_email

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Dependency extracting Bearer token, decoding subject email, loading user, and enforcing active status."""
    payload = decode_access_token(token)
    email: str = payload.get("sub")

    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_email(db, email=email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with token not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )

    return user

def require_role(*allowed_roles: UserRole):
    """
    Dependency factory verifying that the authenticated user possesses one of the allowed roles.
    Raises HTTP 403 Forbidden (NOT 401) if authenticated user role is unauthorized.
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{current_user.role.value}' is not authorized to access this resource."
            )
        return current_user

    return role_checker

def get_allowed_tiers(current_user: User = Depends(get_current_user)) -> List[UserRole]:
    """
    Dependency returning the list of document access tiers accessible to the authenticated user.
    Used by future RAG retrieval pipelines (Phase 15) for query filtering.
    """
    from app.core.access import get_access_tiers_for_role
    return get_access_tiers_for_role(current_user.role)

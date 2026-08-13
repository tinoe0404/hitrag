from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.auth import UserCreate
from app.core.security import hash_password, verify_password
from app.repositories.user import get_user_by_email, create_user_record

def register_user(db: Session, user_in: UserCreate) -> User:
    """Business logic for user registration: checks email uniqueness, hashes password, saves record."""
    existing_user = get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists."
        )

    hashed_pw = hash_password(user_in.password)

    new_user = User(
        email=user_in.email,
        hashed_password=hashed_pw,
        full_name=user_in.full_name,
        role=user_in.role,
        is_active=True,
    )

    return create_user_record(db, new_user)

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Verifies email and password credentials, returning the user if valid."""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

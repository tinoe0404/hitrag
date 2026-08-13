from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.user import User

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Retrieve a user by their unique email address."""
    return db.scalar(select(User).where(User.email == email))

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Retrieve a user by primary key ID."""
    return db.scalar(select(User).where(User.id == user_id))

def create_user_record(db: Session, user_obj: User) -> User:
    """Persist a new User model instance into the database."""
    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)
    return user_obj

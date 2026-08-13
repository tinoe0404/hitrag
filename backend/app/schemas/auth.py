from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from app.models.enums import UserRole

# User Registration Payload
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Optional[UserRole] = UserRole.STUDENT

# Public User Response Model (never includes hashed_password)
class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Token OAuth2 Standard Response
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Decoded Token Payload Schema
class TokenData(BaseModel):
    sub: Optional[str] = None

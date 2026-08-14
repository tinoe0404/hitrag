from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.enums import UserRole, DocumentStatus

class DocumentCreate(BaseModel):
    title: str
    access_tier: Optional[UserRole] = UserRole.PUBLIC

class DocumentOut(BaseModel):
    id: int
    title: str
    filename: str
    access_tier: UserRole
    uploaded_by: int
    status: DocumentStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

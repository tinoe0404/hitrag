from pydantic import BaseModel
from app.models.enums import UserRole

class RoleUpdate(BaseModel):
    """Schema for updating a user's role via admin endpoint."""
    role: UserRole

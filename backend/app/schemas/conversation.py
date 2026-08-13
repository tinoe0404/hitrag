from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.models.enums import MessageRole

# --- Conversation Schemas ---

class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"

class ConversationOut(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Message Schemas ---

class MessageCreate(BaseModel):
    role: MessageRole
    content: str

class MessageOut(BaseModel):
    id: int
    conversation_id: int
    role: MessageRole
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

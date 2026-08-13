from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.core.deps import get_current_user
from app.schemas.conversation import (
    ConversationCreate,
    ConversationOut,
    MessageCreate,
    MessageOut,
)
import app.services.conversation as service

conversations_router = APIRouter(prefix="/api/v1/conversations", tags=["Conversations"])

@conversations_router.post("", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
def create_conversation(
    conv_in: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new conversation session for the authenticated user."""
    return service.service_create_conversation(db, current_user.id, conv_in)

@conversations_router.get("", response_model=List[ConversationOut])
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all conversations for the authenticated user (most recent first)."""
    return service.service_list_conversations(db, current_user.id)

@conversations_router.get("/{id}", response_model=ConversationOut)
def get_conversation(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single conversation by ID (returns 404 if not found or not owned by user)."""
    return service.service_get_conversation(db, conversation_id=id, user_id=current_user.id)

@conversations_router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a conversation and cascade its messages (returns 404 if not found or not owned by user)."""
    service.service_delete_conversation(db, conversation_id=id, user_id=current_user.id)

@conversations_router.post("/{id}/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
def add_message(
    id: int,
    msg_in: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a message to a conversation (returns 404 if not found or not owned by user)."""
    return service.service_add_message(db, conversation_id=id, user_id=current_user.id, msg_in=msg_in)

@conversations_router.get("/{id}/messages", response_model=List[MessageOut])
def list_messages(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all messages in a conversation in chronological order (returns 404 if not found or not owned by user)."""
    return service.service_list_messages(db, conversation_id=id, user_id=current_user.id)

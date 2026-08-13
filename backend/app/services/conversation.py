from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.conversation import ConversationCreate, MessageCreate
import app.repositories.conversation as repo

def get_user_conversation_or_404(db: Session, conversation_id: int, user_id: int) -> Conversation:
    """
    Retrieve a conversation enforcing user ownership.
    Returns 404 Not Found if the conversation does not exist OR does not belong to the user
    to prevent leaking resource existence across tenancy boundaries.
    """
    conv = repo.get_conversation_by_id(db, conversation_id)
    if not conv or conv.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    return conv

def service_create_conversation(db: Session, user_id: int, conv_in: ConversationCreate) -> Conversation:
    """Create a new conversation for the authenticated user."""
    title = conv_in.title.strip() if conv_in.title and conv_in.title.strip() else "New Conversation"
    return repo.create_conversation(db, user_id=user_id, title=title)

def service_list_conversations(db: Session, user_id: int) -> List[Conversation]:
    """Retrieve all conversations for the authenticated user."""
    return repo.list_conversations_for_user(db, user_id)

def service_get_conversation(db: Session, conversation_id: int, user_id: int) -> Conversation:
    """Retrieve a single conversation enforcing ownership check."""
    return get_user_conversation_or_404(db, conversation_id, user_id)

def service_delete_conversation(db: Session, conversation_id: int, user_id: int) -> None:
    """Delete a conversation enforcing ownership check."""
    conv = get_user_conversation_or_404(db, conversation_id, user_id)
    repo.delete_conversation(db, conv)

def service_add_message(db: Session, conversation_id: int, user_id: int, msg_in: MessageCreate) -> Message:
    """Add a message to a conversation enforcing ownership check."""
    get_user_conversation_or_404(db, conversation_id, user_id)
    return repo.create_message(db, conversation_id=conversation_id, role=msg_in.role, content=msg_in.content)

def service_list_messages(db: Session, conversation_id: int, user_id: int) -> List[Message]:
    """List all messages in a conversation in chronological order enforcing ownership check."""
    get_user_conversation_or_404(db, conversation_id, user_id)
    return repo.list_messages_for_conversation(db, conversation_id)

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.models.conversation import Conversation
from app.models.message import Message

def create_conversation(db: Session, user_id: int, title: str) -> Conversation:
    """Create and persist a new conversation for a given user."""
    conv = Conversation(user_id=user_id, title=title)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv

def get_conversation_by_id(db: Session, conversation_id: int) -> Optional[Conversation]:
    """Retrieve a conversation by its primary key ID."""
    return db.scalar(select(Conversation).where(Conversation.id == conversation_id))

def list_conversations_for_user(db: Session, user_id: int) -> List[Conversation]:
    """List all conversations belonging to a user ordered by created_at descending."""
    stmt = (
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(desc(Conversation.created_at))
    )
    return list(db.scalars(stmt).all())

def delete_conversation(db: Session, conv: Conversation) -> None:
    """Delete a conversation record (cascading messages via DB/ORM)."""
    db.delete(conv)
    db.commit()

def create_message(db: Session, conversation_id: int, role: str, content: str) -> Message:
    """Create and persist a message within a conversation."""
    msg = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

def list_messages_for_conversation(db: Session, conversation_id: int) -> List[Message]:
    """List all messages within a conversation ordered by created_at ascending."""
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc(), Message.id.asc())
    )
    return list(db.scalars(stmt).all())

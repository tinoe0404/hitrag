import pytest
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models import User, UserRole, Document, DocumentStatus, Chunk, Conversation, Message, MessageRole
from app.db.session import get_db

def test_models_roundtrip_and_cascade_delete():
    # Obtain session from dependency
    db: Session = next(get_db())

    test_email = "pytest_model_user@hit.ac.zw"

    try:
        # 1. Create User
        user = User(
            email=test_email,
            hashed_password="hashed_secret_test",
            full_name="Pytest Model User",
            role=UserRole.LECTURER,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        assert user.id is not None
        assert user.role == UserRole.LECTURER

        # 2. Create Document for User
        doc = Document(
            title="HIT Academic Assessment Guidelines",
            filename="assessment_policy.pdf",
            storage_path="/uploads/assessment_policy.pdf",
            access_tier=UserRole.LECTURER,
            uploaded_by=user.id,
            status=DocumentStatus.COMPLETED,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        assert doc.id is not None
        assert doc.uploaded_by == user.id

        # 3. Create Chunk for Document
        chunk = Chunk(
            document_id=doc.id,
            content="Continuous assessment marks constitute 40% of total module evaluation.",
            chunk_index=0,
            page_number=1,
        )
        db.add(chunk)
        db.commit()
        db.refresh(chunk)

        assert chunk.id is not None
        assert chunk.document_id == doc.id

        # 4. Create Conversation & Message
        conv = Conversation(
            user_id=user.id,
            title="Assessment Grading Policy",
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)

        msg = Message(
            conversation_id=conv.id,
            role=MessageRole.USER,
            content="What is the continuous assessment weight?",
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)

        assert conv.id is not None
        assert msg.id is not None

        # 5. Query and Assert Relationships
        queried_user = db.scalar(select(User).where(User.id == user.id))
        assert queried_user is not None
        assert len(queried_user.documents) == 1
        assert len(queried_user.documents[0].chunks) == 1
        assert len(queried_user.conversations) == 1
        assert len(queried_user.conversations[0].messages) == 1

        # 6. Test Cascade Delete: deleting User should delete Doc, Chunk, Conv, Msg
        db.delete(user)
        db.commit()

        assert db.scalar(select(User).where(User.id == user.id)) is None
        assert db.scalar(select(Document).where(Document.id == doc.id)) is None
        assert db.scalar(select(Chunk).where(Chunk.id == chunk.id)) is None
        assert db.scalar(select(Conversation).where(Conversation.id == conv.id)) is None
        assert db.scalar(select(Message).where(Message.id == msg.id)) is None

    finally:
        # Cleanup safety net
        cleanup_user = db.scalar(select(User).where(User.email == test_email))
        if cleanup_user:
            db.delete(cleanup_user)
            db.commit()
        db.close()

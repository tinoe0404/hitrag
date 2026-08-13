from app.core.config import get_settings
from app.db.session import get_db
from app.models import User, UserRole, Document, DocumentStatus, Chunk, Conversation, Message, MessageRole
from sqlalchemy import select

def main():
    print("--- Starting HITRAG Backend Model Smoke Test ---")
    settings = get_settings()
    db = next(get_db())

    try:
        # 1. Insert Dummy User
        test_email = "smoke_test_user@hit.ac.zw"
        user = User(
            email=test_email,
            hashed_password="mock_hashed_password_123",
            full_name="Smoke Test Student",
            role=UserRole.STUDENT,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✓ Inserted User: ID={user.id}, Email={user.email}, Role={user.role}")

        # 2. Insert Dummy Document
        doc = Document(
            title="HIT Industrial Attachment Regulations 2026",
            filename="hit_attachment_2026.pdf",
            storage_path="/uploads/hit_attachment_2026.pdf",
            access_tier=UserRole.STUDENT,
            uploaded_by=user.id,
            status=DocumentStatus.COMPLETED,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        print(f"✓ Inserted Document: ID={doc.id}, Title='{doc.title}', UploaderID={doc.uploaded_by}")

        # 3. Insert Dummy Chunk
        chunk = Chunk(
            document_id=doc.id,
            content="Part II Software Engineering students proceeding to attachment must clear all prerequisite modules.",
            chunk_index=0,
            page_number=3,
        )
        db.add(chunk)
        db.commit()
        db.refresh(chunk)
        print(f"✓ Inserted Chunk: ID={chunk.id}, DocID={chunk.document_id}, ContentSnippet='{chunk.content[:40]}...'")

        # 4. Insert Dummy Conversation & Message
        conv = Conversation(
            user_id=user.id,
            title="Industrial Attachment Query",
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)

        msg = Message(
            conversation_id=conv.id,
            role=MessageRole.USER,
            content="What are the attachment prerequisites?",
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        print(f"✓ Inserted Conversation: ID={conv.id}, MessageID={msg.id}")

        # 5. Read back & verify relationships
        queried_user = db.scalar(select(User).where(User.id == user.id))
        assert queried_user is not None
        assert len(queried_user.documents) == 1
        assert len(queried_user.documents[0].chunks) == 1
        print("✓ Successfully queried models and verified relationships end-to-end!")

    finally:
        # 6. Cleanup (Cascade deletes documents, chunks, conversations, messages)
        print("--- Cleaning up Smoke Test Data ---")
        user_to_delete = db.scalar(select(User).where(User.email == "smoke_test_user@hit.ac.zw"))
        if user_to_delete:
            db.delete(user_to_delete)
            db.commit()
            print("✓ Deleted test user (CASCADE deleted related documents, chunks, and conversations).")
        
        db.close()
        print("--- Smoke Test Completed Successfully ---")

if __name__ == "__main__":
    main()

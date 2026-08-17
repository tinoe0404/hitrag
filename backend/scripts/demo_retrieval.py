#!/usr/bin/env python3
"""Demo script to show tier‑aware retrieval.
Runs inside the project's virtual environment.
"""
import json
import sys
sys.path.append('.')  # Ensure project root is on PYTHONPATH

from app.db.session import SessionLocal
from app.models.enums import UserRole, DocumentStatus
from app.models.document import Document
from app.models.chunk import Chunk
from app.models.user import User
import app.rag.retrieval as retrieval_mod

# Monkey‑patch embed_text to avoid external API calls
retrieval_mod.embed_text = lambda _: [0.0] * 768

def print_compiled_sql(stmt):
    compiled = stmt.statement.compile(
        dialect=stmt.session.get_bind().dialect,
        compile_kwargs={"literal_binds": True},
    )
    print("--- Compiled SQL ---")
    print(compiled)
    print("--- End SQL ---\n")

def get_demo_user(db):
    user = db.query(User).filter(User.email == "demo_user@hit.ac.zw").first()
    if not user:
        user = User(
            email="demo_user@hit.ac.zw",
            full_name="Demo User",
            hashed_password="dummy",  # In real app this would be a hash
            role=UserRole.ADMIN,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def main():
    db = SessionLocal()
    try:
        # Clean up any previous demo data
        db.query(Chunk).filter(Chunk.content.like("Demo%" )).delete(synchronize_session=False)
        db.query(Document).filter(Document.title.like("Demo%" )).delete(synchronize_session=False)
        db.commit()

        demo_user = get_demo_user(db)

        # Create a PUBLIC document and a LECTURER‑tier document
        public_doc = Document(
            title="Demo PUBLIC Document",
            filename="demo_public.pdf",
            storage_path="/tmp/demo_public.pdf",
            access_tier=UserRole.PUBLIC,
            uploaded_by=demo_user.id,
            status=DocumentStatus.PENDING,
        )
        lecturer_doc = Document(
            title="Demo LECTURER Document",
            filename="demo_lecturer.pdf",
            storage_path="/tmp/demo_lecturer.pdf",
            access_tier=UserRole.LECTURER,
            uploaded_by=demo_user.id,
            status=DocumentStatus.PENDING,
        )
        db.add_all([public_doc, lecturer_doc])
        db.commit()
        db.refresh(public_doc)
        db.refresh(lecturer_doc)

        # Add several chunks: 3 public, 2 lecturer
        public_chunks = []
        for i in range(3):
            public_chunks.append(
                Chunk(
                    document_id=public_doc.id,
                    content=f"Demo PUBLIC Chunk {i} about admissions.",
                    chunk_index=i,
                    page_number=1,
                    embedding=[0.1] * 768,
                )
            )
        lecturer_chunks = []
        for i in range(2):
            lecturer_chunks.append(
                Chunk(
                    document_id=lecturer_doc.id,
                    content=f"Demo LECTURER Chunk {i} about confidential policy.",
                    chunk_index=i,
                    page_number=1,
                    embedding=[0.9] * 768,
                )
            )
        db.add_all(public_chunks + lecturer_chunks)
        db.commit()

        query = "admissions"
        top_k = 5

        # Show the exact SQL that retrieve will execute (replicated here)
        query_vec = retrieval_mod.embed_text(query)
        distance_expr = Chunk.embedding.cosine_distance(query_vec)
        stmt = (
            db.query(Chunk, distance_expr)
            .join(Document, Chunk.document_id == Document.id)
            .filter(Chunk.embedding.is_not(None))
            .filter(Document.access_tier.in_([UserRole.PUBLIC, UserRole.STUDENT, UserRole.LECTURER, UserRole.ADMIN]))
            .order_by(distance_expr)
            .limit(top_k)
        )
        print_compiled_sql(stmt)

        # ADMIN can see all 5 chunks
        admin_results = retrieval_mod.retrieve(
            db, query, top_k=top_k, allowed_tiers=[UserRole.PUBLIC, UserRole.STUDENT, UserRole.LECTURER, UserRole.ADMIN]
        )
        # STUDENT can see only the 3 public chunks
        student_results = retrieval_mod.retrieve(
            db, query, top_k=top_k, allowed_tiers=[UserRole.PUBLIC, UserRole.STUDENT]
        )

        print("ADMIN results (should contain 5 chunks):")
        print(json.dumps(admin_results, indent=2))
        print("\nSTUDENT results (should contain 3 public chunks):")
        print(json.dumps(student_results, indent=2))

        # Zero‑accessible case: delete all public chunks so student has no access
        for pc in public_chunks:
            db.delete(pc)
        db.commit()
        zero_results = retrieval_mod.retrieve(
            db, query, top_k=top_k, allowed_tiers=[UserRole.PUBLIC, UserRole.STUDENT]
        )
        print("\nZero‑accessible results (should be empty list):")
        print(zero_results)
    finally:
        db.close()

if __name__ == "__main__":
    main()

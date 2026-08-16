"""add_embedding_to_chunks

Revision ID: bcb2de06f8b8
Revises: 93288b4e2a96
Create Date: 2026-08-14 09:57:50.626873

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector


# revision identifiers, used by Alembic.
revision: str = 'bcb2de06f8b8'
down_revision: Union[str, Sequence[str], None] = '93288b4e2a96'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Ensure pgvector extension is created in the DB
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    
    # Add embedding column using pgvector's Vector type (768 dimensions)
    op.add_column('chunks', sa.Column('embedding', pgvector.sqlalchemy.Vector(dim=768), nullable=True))
    
    # Create HNSW index on the embedding column using cosine distance similarity.
    # Cosine distance is the standard choice for text embeddings like Gemini.
    op.create_index(
        'ix_chunks_embedding_hnsw',
        'chunks',
        ['embedding'],
        postgresql_using='hnsw',
        postgresql_ops={'embedding': 'vector_cosine_ops'}
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_chunks_embedding_hnsw', table_name='chunks')
    op.drop_column('chunks', 'embedding')

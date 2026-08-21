"""
Retrieval Module for HITRAG
===========================
Phase 14: Retrieval without an LLM

Performs semantic vector search against chunk embeddings stored in PostgreSQL using pgvector.
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.models.document import Document
from app.models.enums import UserRole
from app.rag.embeddings import embed_text, EmbeddingError


def retrieve(
    db: Session,
    query: str,
    top_k: int = 5,
    allowed_tiers: List[UserRole] | None = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve the top_k most semantically similar chunks for a text query,
    filtering for documents the user has access to.
    
    Design Decision — SQL-level Filtering vs Python-side Filtering:
    We perform the access-tier filtering directly in the SQL query using a JOIN and WHERE clause:
      `filter(Document.access_tier.in_(allowed_tiers))`
    Doing this at the database level ensures that the pgvector index retrieval returns exactly
    up to `top_k` results that are *already authorized* for the user. If we retrieved the top_k unfiltered
    results first and then filtered them in Python, we could easily end up returning fewer than `top_k`
    results, or even zero results, if all top-ranked chunks belonged to documents at a higher tier.
    
    Returns a list of dicts, sorted by similarity descending.
    Each dict contains: chunk_id, document_id, page_number, content, cosine_similarity, and cosine_distance.
    
    Raises:
        ValueError: If query is empty or whitespace-only.
        EmbeddingError: If the Gemini embedding API call fails.
    """
    if not query or not query.strip():
        raise ValueError("Query string cannot be empty or whitespace-only.")

    # If allowed_tiers is None, default to all tiers
    if allowed_tiers is None:
        allowed_tiers = list(UserRole)
    # If the user has access to no tiers, return empty list immediately
    if not allowed_tiers:
        return []

    # Embed the query using the identical model configuration from Phase 11
    query_vec = embed_text(query)
    
    if not query_vec:
        raise EmbeddingError("Failed to generate embedding for query.")

    # Cosine distance operator from pgvector
    distance_expr = Chunk.embedding.cosine_distance(query_vec)

    # Query db for chunks ordered by distance ascending, joined on document access tier
    results = (
        db.query(Chunk, Document.title, Document.access_tier, Document.created_at, distance_expr)
        .join(Document, Chunk.document_id == Document.id)
        .filter(Chunk.embedding.is_not(None))
        .filter(Document.access_tier.in_(allowed_tiers))
        .order_by(distance_expr)
        .limit(top_k)
        .all()
    )

    retrieved_chunks = []
    for chunk, title, access_tier, created_at, distance in results:
        dist_val = float(distance) if distance is not None else 0.0
        retrieved_chunks.append({
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "document_title": title,
            "page_number": chunk.page_number,
            "content": chunk.content,
            "access_tier": access_tier,
            "created_at": created_at,
            "cosine_similarity": round(1.0 - dist_val, 6),
            "cosine_distance": round(dist_val, 6),
        })

    return retrieved_chunks


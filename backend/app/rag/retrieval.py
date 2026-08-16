"""
Retrieval Module for HITRAG
===========================
Phase 14: Retrieval without an LLM

Performs semantic vector search against chunk embeddings stored in PostgreSQL using pgvector.
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.rag.embeddings import embed_text, EmbeddingError


def retrieve(db: Session, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Retrieve the top_k most semantically similar chunks for a text query.
    
    Returns a list of dicts, sorted by similarity descending.
    Each dict contains: chunk_id, document_id, page_number, content, cosine_similarity, and cosine_distance.
    
    Raises:
        ValueError: If query is empty or whitespace-only.
        EmbeddingError: If the Gemini embedding API call fails.
    """
    if not query or not query.strip():
        raise ValueError("Query string cannot be empty or whitespace-only.")

    # Embed the query using the identical model configuration from Phase 11
    query_vec = embed_text(query)
    
    if not query_vec:
        raise EmbeddingError("Failed to generate embedding for query.")

    # Cosine distance operator from pgvector
    distance_expr = Chunk.embedding.cosine_distance(query_vec)

    # Query db for chunks ordered by distance ascending
    results = (
        db.query(Chunk, distance_expr)
        .filter(Chunk.embedding.is_not(None))
        .order_by(distance_expr)
        .limit(top_k)
        .all()
    )

    retrieved_chunks = []
    for chunk, distance in results:
        dist_val = float(distance) if distance is not None else 0.0
        retrieved_chunks.append({
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "page_number": chunk.page_number,
            "content": chunk.content,
            "cosine_similarity": round(1.0 - dist_val, 6),
            "cosine_distance": round(dist_val, 6),
        })

    return retrieved_chunks

"""
Embedding Module for HITRAG
============================
Phase 11: Gemini Embeddings

Uses the `google-genai` unified SDK (NOT the deprecated `google-generativeai` package).

Model: gemini-embedding-001
  - General-purpose text embedding model from Google
  - Output dimensionality: 768 floats per vector
  - This dimensionality is important for Phase 12's pgvector column definition

Batch limits:
  - The Gemini embedding API accepts up to 100 texts per call via embed_content.
  - We batch in groups of 100 to minimize API round-trips.
"""

import time
import logging
from typing import List, Optional
from sqlalchemy.orm import Session

from google import genai
from google.genai import types

from app.core.config import settings

logger = logging.getLogger("hitrag.embeddings")

# Configuration
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONALITY = 768  # Output vector size — needed for Phase 12 pgvector column
BATCH_SIZE = 100  # Gemini embed_content max texts per request
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1.0


class EmbeddingError(Exception):
    """Raised when embedding fails after retries."""
    pass


def _get_client() -> genai.Client:
    """Get a configured Gemini API client. Fails fast if API key is missing."""
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise EmbeddingError(
            "GEMINI_API_KEY is not set. Add it to your .env file: "
            "GEMINI_API_KEY=\"your-api-key-here\""
        )
    return genai.Client(api_key=api_key)


def embed_text(text: str) -> List[float]:
    """
    Embed a single text string using Gemini's embedding model.
    
    Returns a list of floats (768-dimensional vector).
    Skips empty/whitespace-only text by returning an empty list.
    """
    if not text or not text.strip():
        return []

    result = embed_texts([text])
    return result[0]


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Embed multiple texts in batched API calls.
    
    Handles:
    - Empty/whitespace texts: returns empty list [] for those positions
    - Batching: groups texts into chunks of BATCH_SIZE for API efficiency
    - Retries: exponential backoff on rate limit (429) and network errors
    
    Returns a list of embedding vectors, same length and order as input texts.
    """
    if not texts:
        return []

    client = _get_client()
    
    # Pre-process: track which indices have real content vs empty
    results: List[List[float]] = [[] for _ in range(len(texts))]
    non_empty_indices: List[int] = []
    non_empty_texts: List[str] = []
    
    for i, t in enumerate(texts):
        if t and t.strip():
            non_empty_indices.append(i)
            non_empty_texts.append(t)

    if not non_empty_texts:
        return results

    # Process in batches
    for batch_start in range(0, len(non_empty_texts), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(non_empty_texts))
        batch = non_empty_texts[batch_start:batch_end]
        
        batch_embeddings = _embed_batch_with_retry(client, batch)
        
        for j, emb in enumerate(batch_embeddings):
            original_idx = non_empty_indices[batch_start + j]
            results[original_idx] = emb

    return results


def _embed_batch_with_retry(client: genai.Client, texts: List[str]) -> List[List[float]]:
    """
    Call the Gemini embedding API for a batch of texts with exponential backoff retry.
    
    Retries on:
    - Rate limiting (429)
    - Network/timeout errors
    
    Raises EmbeddingError after MAX_RETRIES failures.
    """
    backoff = INITIAL_BACKOFF_SECONDS
    last_error: Optional[Exception] = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=texts,
                config=types.EmbedContentConfig(
                    output_dimensionality=EMBEDDING_DIMENSIONALITY
                ),
            )
            # Extract embedding vectors from response
            vectors = []
            for embedding in response.embeddings:
                vectors.append(list(embedding.values))
            return vectors

        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            
            # Check for rate limiting or transient errors worth retrying
            is_retryable = (
                "429" in error_str
                or "rate" in error_str
                or "timeout" in error_str
                or "unavailable" in error_str
                or "connection" in error_str
            )
            
            if is_retryable and attempt < MAX_RETRIES:
                logger.warning(
                    f"Embedding API error (attempt {attempt}/{MAX_RETRIES}), "
                    f"retrying in {backoff}s: {e}"
                )
                time.sleep(backoff)
                backoff *= 2  # Exponential backoff
            else:
                break

    raise EmbeddingError(
        f"Embedding failed after {MAX_RETRIES} attempts. "
        f"Last error: {type(last_error).__name__}: {last_error}"
    )


def embed_document_chunks(db: Session, document_id: int) -> None:
    """
    Fetch all chunks for a document, embed their text contents using Gemini API,
    and persist the embedding vectors to PostgreSQL.
    
    Updates the document status to DocumentStatus.EMBEDDED on completion.
    Logs warnings for chunks that failed to embed.
    """
    from sqlalchemy.orm import Session
    from app.models.chunk import Chunk
    from app.models.document import Document
    from app.models.enums import DocumentStatus

    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise ValueError(f"Document with ID {document_id} not found.")

    chunks = db.query(Chunk).filter(Chunk.document_id == document_id).order_by(Chunk.chunk_index).all()
    if not chunks:
        # No chunks to embed, immediately mark as EMBEDDED
        doc.status = DocumentStatus.EMBEDDED
        db.commit()
        return

    # Gather texts
    texts = [c.content for c in chunks]

    # Generate embeddings (handles batching, retries internally)
    try:
        embeddings = embed_texts(texts)
    except EmbeddingError as e:
        logger.error(f"Failed to embed chunks for document {document_id}: {e}")
        doc.status = DocumentStatus.FAILED
        db.commit()
        raise

    # Write embeddings to database
    failed_count = 0
    for idx, chunk in enumerate(chunks):
        vec = embeddings[idx]
        if vec:
            chunk.embedding = vec
        else:
            # Check if this text was actually non-empty
            if chunk.content and chunk.content.strip():
                failed_count += 1
                logger.warning(
                    f"Chunk {chunk.id} (index {chunk.chunk_index}) has non-empty content "
                    f"but returned an empty embedding vector."
                )

    if failed_count > 0:
        logger.warning(f"Document {document_id}: {failed_count} chunks failed to embed.")

    doc.status = DocumentStatus.EMBEDDED
    db.commit()


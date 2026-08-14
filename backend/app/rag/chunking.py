"""
Paragraph-Based Chunking Module for HITRAG
===========================================
Phase 10: Document Chunking

This module implements paragraph-level document chunking with a min/max size policy.
It operates as a pure function mapping list of pages to list of chunk dictionaries.

Key Constraints & Decisions:
1. MIN_CHUNK_CHARS = 200:
   - A chunk shorter than ~40 words lacks semantic context for embeddings and vector search retrieval,
     which makes matching low-quality. Short paragraphs are merged with neighbors to boost semantic signals.
2. MAX_CHUNK_CHARS = 1500:
   - A chunk longer than ~250 words dilutes embeddings (averaging out multiple distinct topics) and
     exhausts context windows. Oversized paragraphs are split on sentence boundaries.
3. Page-spanning Policy:
   - Chunks NEVER cross page boundaries. If a paragraph is split between page N and N+1 in the PDF,
     the pages are chunked independently to preserve the exact page-level mapping. This ensures
     100% precise page citations in Phase 19 (e.g. page_number matches the exact page of the text).
"""

import re
from typing import List, Dict

# Configuration Constants
MIN_CHUNK_CHARS = 200
MAX_CHUNK_CHARS = 1500


def split_oversized_paragraph(text: str) -> List[str]:
    """
    Split a paragraph that exceeds MAX_CHUNK_CHARS into sub-paragraphs on sentence boundaries.
    
    If a single sentence is longer than MAX_CHUNK_CHARS, it is split by character limit.
    """
    # Simple regex to split sentences on (.!?) followed by space/newline
    sentence_ends = re.compile(r"(?<=[.!?])\s+")
    raw_sentences = sentence_ends.split(text)
    
    sentences: List[str] = []
    for s in raw_sentences:
        s = s.strip()
        if not s:
            continue
        # Handle rare case of a single sentence exceeding the character limit
        if len(s) > MAX_CHUNK_CHARS:
            start = 0
            while start < len(s):
                sentences.append(s[start:start + MAX_CHUNK_CHARS])
                start += MAX_CHUNK_CHARS
        else:
            sentences.append(s)

    sub_paragraphs: List[str] = []
    buffer: List[str] = []
    buffer_len = 0

    for s in sentences:
        # Check if adding this sentence exceeds MAX_CHUNK_CHARS
        addition_len = len(s) + (1 if buffer else 0)
        if buffer_len + addition_len <= MAX_CHUNK_CHARS:
            buffer.append(s)
            buffer_len += addition_len
        else:
            if buffer:
                sub_paragraphs.append(" ".join(buffer))
            buffer = [s]
            buffer_len = len(s)

    if buffer:
        sub_paragraphs.append(" ".join(buffer))

    return sub_paragraphs


def chunk_pages(pages: List[Dict], document_id: int) -> List[Dict]:
    """
    Pure function that chunks cleaned per-page text based on paragraph boundaries.
    
    Args:
        pages: List of dictionaries of shape [{"page_number": int, "text": str}]
        document_id: The ID of the document being chunked
        
    Returns:
        List of chunk dictionaries of shape:
        [{
            "document_id": int,
            "chunk_index": int,     # 0-indexed sequential index across the document
            "page_number": int,     # exact page this content belongs to
            "content": str
        }]
    """
    chunks: List[Dict] = []
    chunk_index = 0

    for page in pages:
        page_num = page["page_number"]
        text = page.get("text", "").strip()
        
        if not text:
            continue

        # Split on paragraph boundaries (double newlines)
        raw_paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        
        # Step 1: Pre-split any oversized paragraphs
        processed_paragraphs: List[str] = []
        for p in raw_paragraphs:
            if len(p) > MAX_CHUNK_CHARS:
                processed_paragraphs.extend(split_oversized_paragraph(p))
            else:
                processed_paragraphs.append(p)

        # Step 2: Merge short paragraphs (staying strictly within the page boundary)
        current_chunk = ""
        
        for p in processed_paragraphs:
            if not current_chunk:
                if len(p) >= MIN_CHUNK_CHARS:
                    # Save paragraph immediately if it meets the size requirement
                    chunks.append({
                        "document_id": document_id,
                        "chunk_index": chunk_index,
                        "page_number": page_num,
                        "content": p
                    })
                    chunk_index += 1
                else:
                    current_chunk = p
            else:
                # Check if merging exceeds MAX_CHUNK_CHARS
                if len(current_chunk) + 2 + len(p) <= MAX_CHUNK_CHARS:
                    current_chunk = current_chunk + "\n\n" + p
                    if len(current_chunk) >= MIN_CHUNK_CHARS:
                        chunks.append({
                            "document_id": document_id,
                            "chunk_index": chunk_index,
                            "page_number": page_num,
                            "content": current_chunk
                        })
                        chunk_index += 1
                        current_chunk = ""
                else:
                    # Save current_chunk as is (even if under MIN_CHUNK_CHARS) and start new one
                    chunks.append({
                        "document_id": document_id,
                        "chunk_index": chunk_index,
                        "page_number": page_num,
                        "content": current_chunk
                    })
                    chunk_index += 1
                    
                    if len(p) >= MIN_CHUNK_CHARS:
                        chunks.append({
                            "document_id": document_id,
                            "chunk_index": chunk_index,
                            "page_number": page_num,
                            "content": p
                        })
                        chunk_index += 1
                        current_chunk = ""
                    else:
                        current_chunk = p

        # At the end of the page, save any remaining chunk buffer
        if current_chunk:
            chunks.append({
                "document_id": document_id,
                "chunk_index": chunk_index,
                "page_number": page_num,
                "content": current_chunk
            })
            chunk_index += 1

    return chunks

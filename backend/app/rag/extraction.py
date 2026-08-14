"""
PDF Text Extraction Module for HITRAG
======================================
Library choice: PyMuPDF (fitz)

Tradeoff analysis:
- pypdf:       Pure Python, lightweight, decent for simple single-column PDFs. Poor on
               multi-column layouts (merges columns into jumbled lines). No image/table
               extraction. Fastest install but weakest extraction quality.

- pdfplumber:  Built on pdfminer.six. Good text positioning awareness, reasonable multi-column
               handling. Has table extraction via line/rect detection. Slower than PyMuPDF,
               pure Python. No built-in image extraction.

- PyMuPDF:     C-backed (MuPDF engine), fastest extraction by 5-10x. Best handling of
               multi-column layouts via its text block ordering algorithm. Built-in image
               extraction, table detection (v1.23+), and page rendering. Slightly larger
               binary dependency but the extraction quality advantage is significant for
               institutional documents (multi-column policies, academic regulations, etc.).

Decision: PyMuPDF — institutional PDFs at HIT contain multi-column layouts, headers/footers,
tables of academic regulations, and potentially scanned pages. PyMuPDF gives us the best
extraction fidelity now and a clear upgrade path to image/table extraction in later phases
without swapping libraries.
"""

from dataclasses import dataclass, field
from typing import List
import fitz  # PyMuPDF


class ExtractionError(Exception):
    """Raised when PDF extraction fails due to corruption, unreadable format, or I/O errors."""
    pass


@dataclass
class PageResult:
    """Extraction result for a single PDF page."""
    page_number: int        # 1-indexed, matching human-visible page numbers
    text: str               # Raw extracted text (may be empty for scanned/image-only pages)
    has_text: bool          # False if the page yielded no extractable text


@dataclass
class ExtractionResult:
    """Complete extraction result for a PDF document."""
    pages: List[PageResult]
    total_pages: int
    pages_with_text: int
    pages_without_text: int
    extraction_status: str  # "success", "partial" (some blank pages), "no_text" (all blank)

    def to_dict_list(self) -> List[dict]:
        """Serialize pages to list of dicts for downstream consumption (Phase 9 cleaning)."""
        return [
            {
                "page_number": p.page_number,
                "text": p.text,
                "has_text": p.has_text,
            }
            for p in self.pages
        ]


def extract_pages(pdf_path: str) -> ExtractionResult:
    """
    Extract raw text from each page of a PDF file using PyMuPDF.

    Returns an ExtractionResult with per-page text and metadata.
    Pages are 1-indexed to match human-visible page numbers.

    Failure modes:
    - Corrupted/unreadable file -> raises ExtractionError
    - Scanned/image-only pages -> returns pages with has_text=False and empty text
    - Empty pages in a normal PDF -> returns empty text for that page, continues extraction

    The extracted text is intentionally raw and uncleaned — Phase 9 handles cleaning.
    """
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        raise ExtractionError(
            f"Failed to open PDF at '{pdf_path}': {type(e).__name__}: {e}"
        )

    pages: List[PageResult] = []
    pages_with_text = 0
    pages_without_text = 0

    try:
        for page_idx in range(len(doc)):
            try:
                page = doc[page_idx]
                # Extract text using PyMuPDF's "text" mode (preserves reading order)
                raw_text = page.get_text("text")
                text = raw_text.strip() if raw_text else ""
                has_text = len(text) > 0

                if has_text:
                    pages_with_text += 1
                else:
                    pages_without_text += 1

                pages.append(PageResult(
                    page_number=page_idx + 1,  # 1-indexed
                    text=text,
                    has_text=has_text,
                ))
            except Exception as e:
                # Individual page extraction failure — don't break the whole document
                pages_without_text += 1
                pages.append(PageResult(
                    page_number=page_idx + 1,
                    text="",
                    has_text=False,
                ))
    finally:
        doc.close()

    total_pages = len(pages)

    if total_pages == 0:
        extraction_status = "no_text"
    elif pages_with_text == 0:
        extraction_status = "no_text"
    elif pages_without_text > 0:
        extraction_status = "partial"
    else:
        extraction_status = "success"

    return ExtractionResult(
        pages=pages,
        total_pages=total_pages,
        pages_with_text=pages_with_text,
        pages_without_text=pages_without_text,
        extraction_status=extraction_status,
    )

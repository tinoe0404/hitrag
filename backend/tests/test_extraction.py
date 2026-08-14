"""
Tests for Phase 8: PDF text extraction.

Uses real small PDF fixtures generated in-test to cover:
1. Successful multi-page extraction with correct 1-indexed page numbers.
2. Blank/scanned page detection (pages with no extractable text).
3. Corrupted file handling (ExtractionError raised cleanly).
"""
import os
import tempfile
import fitz  # PyMuPDF — used to generate test PDF fixtures
import pytest

from app.rag.extraction import extract_pages, ExtractionError, ExtractionResult


@pytest.fixture
def multi_page_pdf(tmp_path):
    """Create a 3-page PDF with real text content using PyMuPDF."""
    pdf_path = str(tmp_path / "multi_page_test.pdf")
    doc = fitz.open()

    # Page 1
    page1 = doc.new_page(width=612, height=792)
    page1.insert_text((72, 72), "HARARE INSTITUTE OF TECHNOLOGY", fontsize=16)
    page1.insert_text((72, 100), "Academic Regulations Document", fontsize=12)
    page1.insert_text((72, 130), "Section 1: Admission Requirements", fontsize=12)
    page1.insert_text((72, 160), "Students must have a minimum of 5 O-Level passes including Mathematics and English.", fontsize=10)

    # Page 2
    page2 = doc.new_page(width=612, height=792)
    page2.insert_text((72, 72), "Section 2: Examination Regulations", fontsize=14)
    page2.insert_text((72, 100), "The pass mark for all undergraduate modules is 50%.", fontsize=10)
    page2.insert_text((72, 130), "Students who fail more than two modules must repeat the semester.", fontsize=10)

    # Page 3
    page3 = doc.new_page(width=612, height=792)
    page3.insert_text((72, 72), "Section 3: Industrial Attachment", fontsize=14)
    page3.insert_text((72, 100), "All Part II students must complete a minimum of 8 months industrial attachment.", fontsize=10)

    doc.save(pdf_path)
    doc.close()
    return pdf_path


@pytest.fixture
def blank_page_pdf(tmp_path):
    """Create a 2-page PDF where page 2 is completely blank (no text)."""
    pdf_path = str(tmp_path / "blank_page_test.pdf")
    doc = fitz.open()

    # Page 1 — has text
    page1 = doc.new_page(width=612, height=792)
    page1.insert_text((72, 72), "This page has text content.", fontsize=12)

    # Page 2 — completely blank (no text inserted)
    doc.new_page(width=612, height=792)

    doc.save(pdf_path)
    doc.close()
    return pdf_path


@pytest.fixture
def corrupted_pdf(tmp_path):
    """Create a file with .pdf extension but garbage bytes inside."""
    pdf_path = str(tmp_path / "corrupted.pdf")
    with open(pdf_path, "wb") as f:
        f.write(b"THIS IS NOT A PDF FILE AT ALL - JUST GARBAGE BYTES 12345")
    return pdf_path


def test_multi_page_extraction(multi_page_pdf):
    """Verify successful extraction of a 3-page PDF with correct page numbers."""
    result = extract_pages(multi_page_pdf)

    assert isinstance(result, ExtractionResult)
    assert result.total_pages == 3
    assert result.pages_with_text == 3
    assert result.pages_without_text == 0
    assert result.extraction_status == "success"

    # Verify 1-indexed page numbers
    assert result.pages[0].page_number == 1
    assert result.pages[1].page_number == 2
    assert result.pages[2].page_number == 3

    # Verify all pages have text
    for page in result.pages:
        assert page.has_text is True
        assert len(page.text) > 0

    # Verify specific content is extracted
    assert "HARARE INSTITUTE OF TECHNOLOGY" in result.pages[0].text
    assert "pass mark" in result.pages[1].text.lower()
    assert "Industrial Attachment" in result.pages[2].text

    # Verify to_dict_list serialization
    dict_list = result.to_dict_list()
    assert len(dict_list) == 3
    assert dict_list[0]["page_number"] == 1
    assert dict_list[0]["has_text"] is True


def test_blank_page_detection(blank_page_pdf):
    """Verify blank pages are detected with has_text=False, extraction_status='partial'."""
    result = extract_pages(blank_page_pdf)

    assert result.total_pages == 2
    assert result.pages_with_text == 1
    assert result.pages_without_text == 1
    assert result.extraction_status == "partial"

    # Page 1 has text
    assert result.pages[0].has_text is True
    assert "text content" in result.pages[0].text.lower()

    # Page 2 is blank
    assert result.pages[1].has_text is False
    assert result.pages[1].text == ""


def test_corrupted_file_raises_extraction_error(corrupted_pdf):
    """Verify corrupted PDF raises ExtractionError, not a raw library exception."""
    with pytest.raises(ExtractionError) as exc_info:
        extract_pages(corrupted_pdf)

    assert "Failed to open PDF" in str(exc_info.value)

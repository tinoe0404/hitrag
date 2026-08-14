"""
Tests for Phase 9: Document Cleaning.

Covers:
1. Whitespace normalization (collapsing spaces/tabs, limit 2 consecutive newlines, trim).
2. De-hyphenation (merging split words, keeping legitimate compounds like 'well-known').
3. Control character stripping.
4. Header/footer detection and stripping using a multi-page test fixture.
5. Verification that genuinely repeated mid-page sentences survive.
"""
import pytest

from app.rag.cleaning import (
    clean_pages,
    normalize_whitespace,
    de_hyphenate,
    clean_control_characters,
    detect_headers_footers
)


def test_clean_control_characters():
    # Null byte, form feed, BEL, ESC should be stripped
    raw = "Hello\x00 World\x0c!\x07 This is \x1b[31mclean\x1b[0m."
    cleaned = clean_control_characters(raw)
    assert cleaned == "Hello World! This is [31mclean[0m."


def test_normalize_whitespace():
    # Multiple spaces and tabs collapsed, consecutive newlines limited to 2
    raw = "  Hello \t   world!   \n\n\n\nThis is paragraph 2.\n\n\n\n\nParagraph 3.   "
    cleaned = normalize_whitespace(raw)
    assert cleaned == "Hello world!\n\nThis is paragraph 2.\n\nParagraph 3."


def test_de_hyphenate():
    # 1. Non-word split -> should merge
    assert de_hyphenate("infor-\nmation") == "information"
    assert de_hyphenate("institu-\n  tional") == "institutional"
    
    # 2. Legitimate hyphenated compound split -> should keep hyphen on one line
    # "well-known" has "well" in LEGITIMATE_HYPHEN_PREFIXES
    assert de_hyphenate("well-\nknown") == "well-known"
    
    # 3. Legitimate split where both are complete words not in prefix list -> should keep hyphen
    assert de_hyphenate("part-\ntime") == "part-time"


def test_header_footer_stripping():
    # Fabricate 4 pages where:
    # Line 1 is a header on all pages: "HIT REGULATIONS 2026"
    # Line 2 is content
    # Line 3 is content
    # Last line is a footer on 3 out of 4 pages (75% > 65% threshold): "Page X of 4"
    # Mid-page contains a repeated sentence on all pages: "This is a standard mid-page clause."
    
    pages = [
        {
            "page_number": 1,
            "text": "HIT REGULATIONS 2026\nIntroduction to regulations.\nThis is a standard mid-page clause.\nPage 1 of 4"
        },
        {
            "page_number": 2,
            "text": "HIT REGULATIONS 2026\nChapter 1: Enrollment.\nThis is a standard mid-page clause.\nPage 2 of 4"
        },
        {
            "page_number": 3,
            "text": "HIT REGULATIONS 2026\nChapter 2: Coursework requirements.\nThis is a standard mid-page clause.\nPage 3 of 4"
        },
        {
            "page_number": 4,
            "text": "HIT REGULATIONS 2026\nChapter 3: Final graduation rules.\nThis is a standard mid-page clause.\nSome different footer text here"
        }
    ]

    # Verify detection directly first
    headers, footers = detect_headers_footers(pages)
    assert "HIT REGULATIONS 2026" in headers
    
    # Verify footer is NOT detected because each page has a unique footer line ("Page 1 of 4", "Page 2 of 4", etc.)
    # This proves dynamic text like page numbers is not falsely matched by exact matching
    assert len(footers) == 0

    # Let's make a test case where the footer is identical on all pages
    pages_identical_footers = [
        {
            "page_number": 1,
            "text": "HIT REGULATIONS 2026\nIntro.\nThis is a standard mid-page clause.\nHitrag Footer text"
        },
        {
            "page_number": 2,
            "text": "HIT REGULATIONS 2026\nChapter 1.\nThis is a standard mid-page clause.\nHitrag Footer text"
        },
        {
            "page_number": 3,
            "text": "HIT REGULATIONS 2026\nChapter 2.\nThis is a standard mid-page clause.\nHitrag Footer text"
        }
    ]

    headers, footers = detect_headers_footers(pages_identical_footers)
    assert "HIT REGULATIONS 2026" in headers
    assert "Hitrag Footer text" in footers

    # Clean the pages using clean_pages
    cleaned = clean_pages(pages_identical_footers)
    
    # Header and footer must be stripped
    assert "HIT REGULATIONS 2026" not in cleaned[0]["text"]
    assert "Hitrag Footer text" not in cleaned[0]["text"]
    
    # Genuinely repeated mid-page sentence MUST survive
    assert "This is a standard mid-page clause." in cleaned[0]["text"]
    assert "This is a standard mid-page clause." in cleaned[1]["text"]
    assert "This is a standard mid-page clause." in cleaned[2]["text"]

    # Basic contents must survive
    assert "Intro." in cleaned[0]["text"]
    assert "Chapter 1." in cleaned[1]["text"]

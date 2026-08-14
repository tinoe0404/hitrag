"""
Text Cleaning & Normalization Module for HITRAG
================================================
Phase 9: Document Cleaning

This module provides functions to clean and normalize raw extracted text from PDFs.
It operates as a pure function list-to-list mapping to remain easily testable.

Key Operations:
1. Whitespace normalization: collapses multiple spaces/tabs, trims, preserves paragraph breaks (max 2 consecutive newlines).
2. De-hyphenation: rejoins words split across line breaks (e.g., "infor-\nmation" -> "information") using a hybrid dictionary heuristic.
3. Header/Footer detection and removal: automatically detects and strips repeated running headers/footers.
4. Control character removal: strips non-printable control characters while preserving unicode and legitimate punctuation.
"""

import os
import re
import logging
from typing import List, Dict, Set, Tuple

logger = logging.getLogger("hitrag.cleaning")

# Configuration Constants
MAX_CONSECUTIVE_NEWLINES = 2
HEADER_FOOTER_LINES_TO_CHECK = 3  # Check first/last 3 lines of each page
HEADER_FOOTER_THRESHOLD = 0.65     # If a line appears in > 65% of pages, strip it

# Path to standard system dictionary (available on macOS and most Unix environments)
SYSTEM_DICT_PATH = "/usr/share/dict/words"

# Fallback set of common English words/prefixes/suffixes if system dictionary is missing
FALLBACK_WORDS = {
    "the", "of", "and", "a", "to", "in", "is", "you", "that", "it", "he", "was", "for", "on", "are", "as",
    "with", "his", "they", "i", "at", "be", "this", "have", "from", "or", "one", "had", "by", "word",
    "but", "not", "what", "all", "were", "we", "when", "your", "can", "said", "there", "use", "an", "each",
    "which", "she", "do", "how", "their", "if", "will", "up", "other", "about", "out", "many", "then",
    "them", "these", "so", "some", "her", "would", "make", "like", "him", "into", "time", "has", "look",
    "two", "more", "write", "go", "see", "number", "no", "way", "could", "people", "my", "than", "first",
    "water", "been", "call", "who", "oil", "its", "now", "find", "long", "down", "day", "did", "get",
    "come", "made", "may", "part", "well", "known", "time", "side", "self", "evaluation", "academic",
    "regulations", "attachment", "policy", "student", "lecturer", "university", "institute", "technology"
}

# Common legitimate prefixes/words that form hyphenated compounds (e.g. "self-esteem", "well-known")
LEGITIMATE_HYPHEN_PREFIXES = {
    "self", "well", "co", "pre", "post", "anti", "non", "ex", "vice", "sub", "cross", "multi", "part",
    "state", "out", "in", "off", "on", "up", "down", "ill", "all", "half", "quarter"
}


def _load_dictionary() -> Set[str]:
    """Load system dictionary or fallback set for word validation."""
    words: Set[str] = set()
    if os.path.exists(SYSTEM_DICT_PATH):
        try:
            with open(SYSTEM_DICT_PATH, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    word = line.strip().lower()
                    if word:
                        words.add(word)
            logger.info(f"Loaded {len(words)} words from system dictionary at {SYSTEM_DICT_PATH}.")
            return words
        except Exception as e:
            logger.warning(f"Failed to load system dictionary, falling back to built-in list: {e}")
    
    logger.info("Using fallback word list for de-hyphenation validation.")
    return FALLBACK_WORDS


# Initialize dictionary set
DICTIONARY = _load_dictionary()


def clean_control_characters(text: str) -> str:
    """Strip ASCII control characters (except tab, newline, carriage return) and non-printables."""
    # Matches character ranges: 0-8, 11-12, 14-31, and 127-159 (DEL and C1 control codes)
    control_char_re = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")
    return control_char_re.sub("", text)


def normalize_whitespace(text: str) -> str:
    """Collapse repeated spaces and tabs; limit consecutive newlines to at most 2."""
    # Strip trailing whitespaces on each line
    text = "\n".join(line.rstrip() for line in text.splitlines())
    # Collapse horizontal spaces/tabs
    text = re.sub(r"[ \t]+", " ", text)
    # Collapse 3+ consecutive newlines/carriage returns to exactly 2
    text = re.sub(r"(\r?\n){3,}", "\n\n", text)
    return text.strip()


def de_hyphenate(text: str) -> str:
    """
    Detect and rejoin words split across line breaks by a hyphen.
    
    Heuristic Rationale:
    1. Match the pattern: word_part1 + '-' + newline + word_part2.
    2. Check if either part is not a valid word in the dictionary, OR if the combined word is a valid word.
       - If either part is not a standalone word (e.g. "infor-" and "mation"), it is almost certainly a jetted column break. We merge them: "information".
       - If BOTH parts are valid standalone words (e.g. "well" and "known"), we check if the prefix belongs to a list of common hyphenated compounds (e.g. "well-known"). If so, we keep the hyphen but place it on a single line: "well-known".
       - If both are valid words but not a typical compound, we keep the hyphen: "part-time".
    """
    pattern = re.compile(r"(\b[a-zA-Z]+)-\s*\n\s*([a-zA-Z]+\b)")
    
    def replace_match(match: re.Match) -> str:
        w1 = match.group(1)
        w2 = match.group(2)
        w1_lower = w1.lower()
        w2_lower = w2.lower()
        joined = w1 + w2
        joined_lower = joined.lower()

        # If joined word is in dictionary, merge
        if joined_lower in DICTIONARY:
            return joined
            
        # If either part is not a valid standalone word, merge
        if w1_lower not in DICTIONARY or w2_lower not in DICTIONARY:
            return joined
            
        # If the prefix is a common compound prefix, keep hyphen
        if w1_lower in LEGITIMATE_HYPHEN_PREFIXES:
            return f"{w1}-{w2}"
            
        # Default: keep hyphen
        return f"{w1}-{w2}"

    return pattern.sub(replace_match, text)


def detect_headers_footers(pages: List[Dict]) -> Tuple[Set[str], Set[str]]:
    """
    Compare the first and last N lines of all non-empty pages.
    Any line that appears identically on more than HEADER_FOOTER_THRESHOLD of pages
    is classified as a header or footer.
    
    Returns:
        A tuple of (headers_to_strip, footers_to_strip)
    """
    non_empty_pages = [p for p in pages if p.get("text") and p["text"].strip()]
    total_pages = len(non_empty_pages)
    
    if total_pages < 2:
        return set(), set()

    header_counts: Dict[str, int] = {}
    footer_counts: Dict[str, int] = {}

    for page in non_empty_pages:
        lines = [line.strip() for line in page["text"].split("\n") if line.strip()]
        
        # Prevent overlapping header/footer regions in short pages by keeping the middle 1/3 safe
        third_len = len(lines) // 3
        num_header_lines = min(HEADER_FOOTER_LINES_TO_CHECK, third_len)
        num_footer_lines = min(HEADER_FOOTER_LINES_TO_CHECK, third_len)

        # Check first N lines
        seen_headers = set(lines[:num_header_lines] if num_header_lines > 0 else [])
        for line in seen_headers:
            header_counts[line] = header_counts.get(line, 0) + 1
            
        # Check last N lines
        seen_footers = set(lines[-num_footer_lines:] if num_footer_lines > 0 else [])
        for line in seen_footers:
            footer_counts[line] = footer_counts.get(line, 0) + 1

    headers_to_strip = {
        line for line, count in header_counts.items()
        if (count / total_pages) > HEADER_FOOTER_THRESHOLD
    }
    
    footers_to_strip = {
        line for line, count in footer_counts.items()
        if (count / total_pages) > HEADER_FOOTER_THRESHOLD
    }

    return headers_to_strip, footers_to_strip


def clean_pages(pages: List[Dict]) -> List[Dict]:
    """
    Clean and normalize raw extracted pages of a document.
    
    Applies:
    1. Control character removal.
    2. De-hyphenation.
    3. Whitespace normalization.
    4. Header/Footer detection and removal (conservative, same-document scope).
    
    Args:
        pages: List of dictionaries of shape [{"page_number": int, "text": str}]
        
    Returns:
        Cleaned list of dictionaries in the same shape.
    """
    cleaned_pages: List[Dict] = []
    
    # First pass: clean control chars, de-hyphenate, and normalize whitespace
    temp_pages: List[Dict] = []
    for page in pages:
        page_num = page["page_number"]
        raw_text = page.get("text", "")
        
        if not raw_text.strip():
            temp_pages.append({"page_number": page_num, "text": "", "has_text": False})
            continue

        text = clean_control_characters(raw_text)
        text = de_hyphenate(text)
        text = normalize_whitespace(text)
        
        temp_pages.append({
            "page_number": page_num,
            "text": text,
            "has_text": len(text) > 0
        })

    # Second pass: detect running headers/footers
    headers, footers = detect_headers_footers(temp_pages)
    
    if headers:
        logger.info(f"Stripping detected headers: {headers}")
        print(f"Stripping detected headers: {headers}")
    if footers:
        logger.info(f"Stripping detected footers: {footers}")
        print(f"Stripping detected footers: {footers}")

    # Third pass: remove detected headers and footers from pages
    for page in temp_pages:
        text = page["text"]
        if not text:
            cleaned_pages.append({
                "page_number": page["page_number"],
                "text": "",
                "has_text": False
            })
            continue

        lines = text.split("\n")
        cleaned_lines: List[str] = []
        
        for idx, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Remove header line if it's in the first N lines
            if idx < HEADER_FOOTER_LINES_TO_CHECK and line_stripped in headers:
                continue
                
            # Remove footer line if it's in the last N lines
            if idx >= (len(lines) - HEADER_FOOTER_LINES_TO_CHECK) and line_stripped in footers:
                continue
                
            cleaned_lines.append(line)

        cleaned_text = "\n".join(cleaned_lines)
        # Re-normalize whitespace after line stripping
        cleaned_text = normalize_whitespace(cleaned_text)
        
        cleaned_pages.append({
            "page_number": page["page_number"],
            "text": cleaned_text,
            "has_text": len(cleaned_text) > 0
        })

    return cleaned_pages

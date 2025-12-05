"""Text utility functions for artwork title matching and normalization."""

import re


def normalize_title(title: str) -> str:
    """
    Normalize artwork title for comparison.

    Removes punctuation, extra spaces, and standardizes common variations.
    Used for matching artwork records across different sources.

    Args:
        title: The artwork title to normalize

    Returns:
        Normalized lowercase string suitable for comparison
    """
    normalized = title.lower()

    # Replace & with 'and'
    normalized = normalized.replace('&', 'and')

    # Remove all common punctuation
    for char in [',', '.', '!', '?', "'", '"', ':', ';', '-', '(', ')', '[', ']']:
        normalized = normalized.replace(char, ' ')

    # Replace multiple spaces with single space
    normalized = ' '.join(normalized.split())

    return normalized.strip()


def titles_match(title1: str, title2: str) -> bool:
    """
    Check if two artwork titles match, accounting for common variations.

    Handles exact matches after normalization and partial substring matching
    for truncated titles.

    Args:
        title1: First title to compare
        title2: Second title to compare

    Returns:
        True if titles are considered a match
    """
    norm1 = normalize_title(title1)
    norm2 = normalize_title(title2)

    # Direct match
    if norm1 == norm2:
        return True

    # Check if one is substring of other (for truncated titles)
    if len(norm1) > 10 and len(norm2) > 10:
        if norm1 in norm2 or norm2 in norm1:
            return True

    return False


def extract_year(text: str) -> int | None:
    """
    Extract a year from text (e.g., from signed dates, descriptions).

    Args:
        text: Text that may contain a year

    Returns:
        Extracted year as int, or None if not found
    """
    # Look for 4-digit years between 1950 and 2025
    match = re.search(r'\b(19[5-9]\d|20[0-2]\d)\b', text)
    if match:
        return int(match.group(1))
    return None


def clean_filename(title: str, max_length: int = 50) -> str:
    """
    Convert artwork title to a safe filename.

    Args:
        title: The artwork title
        max_length: Maximum length for the filename

    Returns:
        Safe filename string
    """
    # Remove unsafe characters
    safe = re.sub(r'[^\w\s-]', '', title)
    # Replace spaces with underscores
    safe = re.sub(r'\s+', '_', safe)
    # Truncate
    return safe[:max_length]

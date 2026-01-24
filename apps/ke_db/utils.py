"""Utility functions for ke_db."""

import hashlib
import re
from pathlib import Path


def compute_sha256(file_path: str | Path) -> str:
    """Compute SHA256 hash of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal SHA256 hash string.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def validate_doc_id(doc_id: str) -> bool:
    """Validate document ID format.

    Format: XXX-NNNN (3 uppercase letters, dash, 4+ digits)
    Examples: DOC-0001, RFC-8446, ISO-27001

    Args:
        doc_id: Document ID to validate.

    Returns:
        True if valid, False otherwise.
    """
    pattern = r"^[A-Z]{3}-[0-9]{4,}$"
    return bool(re.match(pattern, doc_id))


def validate_confidence(value: float) -> bool:
    """Validate confidence score is in valid range.

    Args:
        value: Confidence score.

    Returns:
        True if 0.0 <= value <= 1.0.
    """
    return 0.0 <= value <= 1.0

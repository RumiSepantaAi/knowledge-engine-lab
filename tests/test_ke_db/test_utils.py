"""Tests for ke_db utilities."""

import tempfile
from pathlib import Path

import pytest

from apps.ke_db.utils import compute_sha256, validate_confidence, validate_doc_id


class TestValidateDocId:
    """Tests for doc_id validation."""

    def test_valid_doc_ids(self) -> None:
        """Valid doc_id formats should pass."""
        assert validate_doc_id("DOC-0001") is True
        assert validate_doc_id("RFC-8446") is True
        assert validate_doc_id("ISO-27001") is True
        assert validate_doc_id("ABC-12345") is True

    def test_invalid_doc_ids(self) -> None:
        """Invalid doc_id formats should fail."""
        assert validate_doc_id("doc-0001") is False  # lowercase
        assert validate_doc_id("DOC0001") is False  # no dash
        assert validate_doc_id("DOCX-001") is False  # 4 letters
        assert validate_doc_id("DO-0001") is False  # 2 letters
        assert validate_doc_id("DOC-123") is False  # 3 digits
        assert validate_doc_id("DOC-") is False  # no digits
        assert validate_doc_id("") is False  # empty


class TestValidateConfidence:
    """Tests for confidence validation."""

    def test_valid_confidence(self) -> None:
        """Valid confidence values should pass."""
        assert validate_confidence(0.0) is True
        assert validate_confidence(0.5) is True
        assert validate_confidence(1.0) is True
        assert validate_confidence(0.75) is True

    def test_invalid_confidence(self) -> None:
        """Invalid confidence values should fail."""
        assert validate_confidence(-0.1) is False
        assert validate_confidence(1.1) is False
        assert validate_confidence(-1.0) is False


class TestComputeSha256:
    """Tests for SHA256 computation."""

    def test_computes_correct_hash(self) -> None:
        """Should compute correct SHA256 hash."""
        # Create a temp file with known content
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Hello, World!")
            temp_path = Path(f.name)

        try:
            result = compute_sha256(temp_path)
            # Known SHA256 of "Hello, World!"
            expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
            assert result == expected
        finally:
            temp_path.unlink()

    def test_different_content_different_hash(self) -> None:
        """Different content should produce different hash."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f1:
            f1.write("Content A")
            path1 = Path(f1.name)

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f2:
            f2.write("Content B")
            path2 = Path(f2.name)

        try:
            hash1 = compute_sha256(path1)
            hash2 = compute_sha256(path2)
            assert hash1 != hash2
        finally:
            path1.unlink()
            path2.unlink()

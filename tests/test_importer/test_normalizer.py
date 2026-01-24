"""Unit tests for the normalizer module."""

import pytest

from meta.importer.normalizer import (
    apply_typo_correction,
    build_taxon_path,
    dedupe,
    generate_taxon_id,
    generate_term_id,
    normalize_term,
    trim,
)


class TestTrim:
    """Tests for trim function."""

    def test_basic_trim(self) -> None:
        """Test basic whitespace trimming."""
        assert trim("  hello  ") == "hello"

    def test_no_whitespace(self) -> None:
        """Test string without whitespace."""
        assert trim("hello") == "hello"

    def test_only_whitespace(self) -> None:
        """Test whitespace-only string."""
        assert trim("   ") == ""

    def test_empty_string(self) -> None:
        """Test empty string."""
        assert trim("") == ""

    def test_none_value(self) -> None:
        """Test None value."""
        assert trim(None) == ""

    def test_tabs_and_newlines(self) -> None:
        """Test tabs and newlines are trimmed."""
        assert trim("\t\nhello\t\n") == "hello"


class TestTypoCorrection:
    """Tests for typo correction."""

    def test_known_typo(self) -> None:
        """Test correction of known typo."""
        assert apply_typo_correction("Artifical Intelligence") == "Artificial Intelligence"

    def test_case_insensitive(self) -> None:
        """Test typo matching is case-insensitive."""
        assert apply_typo_correction("ARTIFICAL INTELLIGENCE") == "Artificial Intelligence"

    def test_no_typo(self) -> None:
        """Test value without typo is returned unchanged."""
        assert apply_typo_correction("Machine Learning") == "Machine Learning"

    def test_unknown_value(self) -> None:
        """Test unknown value is returned unchanged."""
        assert apply_typo_correction("Some Random Term") == "Some Random Term"


class TestNormalizeTerm:
    """Tests for normalize_term function."""

    def test_trim_and_typo(self) -> None:
        """Test combined trim and typo correction."""
        assert normalize_term("  Artifical Intelligence  ") == "Artificial Intelligence"

    def test_just_trim(self) -> None:
        """Test when only trim is needed."""
        assert normalize_term("  Machine Learning  ") == "Machine Learning"


class TestDedupe:
    """Tests for dedupe function."""

    def test_basic_dedupe(self) -> None:
        """Test basic deduplication."""
        assert dedupe(["A", "B", "A", "C"]) == ["A", "B", "C"]

    def test_preserves_order(self) -> None:
        """Test that first occurrence order is preserved."""
        assert dedupe(["C", "A", "B", "A", "C"]) == ["C", "A", "B"]

    def test_no_duplicates(self) -> None:
        """Test list without duplicates."""
        assert dedupe(["A", "B", "C"]) == ["A", "B", "C"]

    def test_all_duplicates(self) -> None:
        """Test list with all duplicates."""
        assert dedupe(["A", "A", "A"]) == ["A"]

    def test_empty_list(self) -> None:
        """Test empty list."""
        assert dedupe([]) == []

    def test_case_sensitive(self) -> None:
        """Test that deduplication is case-sensitive."""
        assert dedupe(["A", "a", "A"]) == ["A", "a"]


class TestGenerateTaxonId:
    """Tests for generate_taxon_id function."""

    def test_deterministic(self) -> None:
        """Test that same input produces same output."""
        path = "AI > Machine Learning > Supervised"
        id1 = generate_taxon_id(path)
        id2 = generate_taxon_id(path)
        assert id1 == id2

    def test_different_paths_different_ids(self) -> None:
        """Test that different paths produce different IDs."""
        id1 = generate_taxon_id("AI > Machine Learning > Supervised")
        id2 = generate_taxon_id("AI > Machine Learning > Unsupervised")
        assert id1 != id2

    def test_valid_uuid_format(self) -> None:
        """Test that output is valid UUID format."""
        result = generate_taxon_id("AI > Machine Learning > Supervised")
        # UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        assert len(result) == 36
        assert result.count("-") == 4


class TestGenerateTermId:
    """Tests for generate_term_id function."""

    def test_deterministic(self) -> None:
        """Test that same inputs produce same output."""
        taxon_id = "11111111-2222-3333-4444-555555555555"
        term = "Linear Regression"
        id1 = generate_term_id(taxon_id, term)
        id2 = generate_term_id(taxon_id, term)
        assert id1 == id2

    def test_different_terms_different_ids(self) -> None:
        """Test that different terms produce different IDs."""
        taxon_id = "11111111-2222-3333-4444-555555555555"
        id1 = generate_term_id(taxon_id, "Linear Regression")
        id2 = generate_term_id(taxon_id, "Logistic Regression")
        assert id1 != id2

    def test_different_taxons_different_ids(self) -> None:
        """Test that same term under different taxons produces different IDs."""
        term = "Same Term"
        id1 = generate_term_id("11111111-2222-3333-4444-555555555555", term)
        id2 = generate_term_id("22222222-3333-4444-5555-666666666666", term)
        assert id1 != id2


class TestBuildTaxonPath:
    """Tests for build_taxon_path function."""

    def test_basic_path(self) -> None:
        """Test basic path building."""
        result = build_taxon_path("AI", "Machine Learning", "Supervised")
        assert result == "AI > Machine Learning > Supervised"

    def test_empty_levels(self) -> None:
        """Test with empty levels."""
        result = build_taxon_path("", "", "")
        assert result == " >  > "

    def test_whitespace_preserved(self) -> None:
        """Test that input whitespace is preserved (not trimmed)."""
        result = build_taxon_path("AI ", " ML", " Deep")
        assert result == "AI  >  ML >  Deep"

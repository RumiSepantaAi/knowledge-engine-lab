"""Unit tests for the semicolon splitter."""

import pytest

from meta.importer.splitter import split_level4


class TestSplitLevel4:
    """Tests for split_level4 function."""

    def test_simple_split(self) -> None:
        """Test basic semicolon splitting."""
        assert split_level4("A; B; C") == ["A", "B", "C"]

    def test_no_semicolon(self) -> None:
        """Test string without semicolons."""
        assert split_level4("Single Term") == ["Single Term"]

    def test_preserves_parens(self) -> None:
        """Test that semicolons inside parentheses are preserved."""
        result = split_level4("3-Layer Vector DB (Evidence; Implication; Playbook)")
        assert result == ["3-Layer Vector DB (Evidence; Implication; Playbook)"]

    def test_mixed_parens_and_split(self) -> None:
        """Test splitting with some terms containing parentheses."""
        result = split_level4("Foo (a; b); Bar")
        assert result == ["Foo (a; b)", "Bar"]

    def test_nested_parens(self) -> None:
        """Test nested parentheses handling."""
        result = split_level4("A (B (C; D)); E")
        assert result == ["A (B (C; D))", "E"]

    def test_empty_string(self) -> None:
        """Test empty string input."""
        assert split_level4("") == []

    def test_whitespace_only(self) -> None:
        """Test whitespace-only input."""
        assert split_level4("   ") == []

    def test_trims_whitespace(self) -> None:
        """Test that results are trimmed."""
        result = split_level4("  A  ;  B  ;  C  ")
        assert result == ["A", "B", "C"]

    def test_empty_segments_removed(self) -> None:
        """Test that empty segments between semicolons are removed."""
        result = split_level4("A;; B; ; C")
        assert result == ["A", "B", "C"]

    def test_transformer_example(self) -> None:
        """Test the transformer example from requirements."""
        result = split_level4("Transformer (Attention; Self-Attention)")
        assert result == ["Transformer (Attention; Self-Attention)"]

    def test_multiple_parenthetical_groups(self) -> None:
        """Test multiple separate parenthetical groups."""
        result = split_level4("A (x; y); B (p; q); C")
        assert result == ["A (x; y)", "B (p; q)", "C"]

    def test_unclosed_paren_graceful(self) -> None:
        """Test graceful handling of unclosed parenthesis."""
        # Should not crash, depth goes negative but is clamped to 0
        result = split_level4("A (unclosed; B; C")
        # The unclosed paren means everything after it stays together
        assert result == ["A (unclosed; B; C"]

    def test_extra_close_paren_graceful(self) -> None:
        """Test graceful handling of extra close parenthesis."""
        result = split_level4("A ); B; C")
        assert result == ["A )", "B", "C"]

    def test_real_world_vector_db(self) -> None:
        """Test the exact 3-Layer Vector DB example from requirements."""
        input_str = "K-Means; 3-Layer Vector DB (Evidence; Implication; Playbook)"
        result = split_level4(input_str)
        assert result == [
            "K-Means",
            "3-Layer Vector DB (Evidence; Implication; Playbook)",
        ]


class TestSplitLevel4EdgeCases:
    """Edge case tests for split_level4."""

    @pytest.mark.parametrize(
        "input_str,expected",
        [
            ("A", ["A"]),
            ("A;", ["A"]),
            (";A", ["A"]),
            ("A;B", ["A", "B"]),
            ("(A; B)", ["(A; B)"]),
            ("();A", ["()", "A"]),
        ],
    )
    def test_edge_cases(self, input_str: str, expected: list[str]) -> None:
        """Parametrized edge case tests."""
        assert split_level4(input_str) == expected

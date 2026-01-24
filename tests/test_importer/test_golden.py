"""Golden tests for the taxonomy importer.

These tests verify end-to-end processing by comparing generated output
against known-good expected files.
"""

import json
import tempfile
from pathlib import Path

import pytest

from meta.importer.import_taxonomy import process_taxonomy
from meta.importer.outputs import (
    build_taxonomy_tree,
    write_taxonomy_clean,
    write_taxonomy_tree_json,
    write_taxonomy_tree_yaml,
    write_terms_normalized,
)
from meta.importer.dq_report import generate_dq_report

# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
EXPECTED_DIR = FIXTURES_DIR / "expected"


class TestGoldenOutputs:
    """Golden tests comparing against expected outputs."""

    @pytest.fixture
    def processed_terms(self) -> tuple:
        """Process the sample taxonomy fixture."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            terms, stats = process_taxonomy(FIXTURES_DIR, output_dir, strict=False)
            yield terms, stats, output_dir

    def test_taxonomy_tree_json_structure(self, processed_terms: tuple) -> None:
        """Test that JSON tree has correct structure."""
        terms, _, output_dir = processed_terms

        # Write JSON
        json_path = output_dir / "taxonomy_tree.json"
        write_taxonomy_tree_json(terms, json_path)

        # Load and verify structure
        with open(json_path) as f:
            tree = json.load(f)

        # Check top-level keys
        assert "AI" in tree
        assert "Data" in tree

        # Check nested structure
        assert "Machine Learning" in tree["AI"]
        assert "Deep Learning" in tree["AI"]
        assert "Supervised" in tree["AI"]["Machine Learning"]
        assert "Unsupervised" in tree["AI"]["Machine Learning"]

        # Check terms
        assert "Linear Regression" in tree["AI"]["Machine Learning"]["Supervised"]
        assert "K-Means" in tree["AI"]["Machine Learning"]["Unsupervised"]

        # Check parentheses preserved
        unsupervised_terms = tree["AI"]["Machine Learning"]["Unsupervised"]
        vector_db_found = any(
            "3-Layer Vector DB (Evidence; Implication; Playbook)" in t
            for t in unsupervised_terms
        )
        assert vector_db_found, "Parenthetical term should be preserved"

    def test_taxonomy_tree_json_matches_expected(self, processed_terms: tuple) -> None:
        """Test that JSON tree matches expected output byte-for-byte."""
        terms, _, output_dir = processed_terms

        # Write JSON
        json_path = output_dir / "taxonomy_tree.json"
        write_taxonomy_tree_json(terms, json_path)

        # Compare with expected
        expected_path = EXPECTED_DIR / "taxonomy_tree.json"
        assert expected_path.exists(), f"Expected file not found: {expected_path}"

        actual_content = json_path.read_text(encoding="utf-8")
        expected_content = expected_path.read_text(encoding="utf-8")
        assert actual_content == expected_content, "JSON tree should match expected output"

    def test_taxonomy_tree_yaml_matches_expected(self, processed_terms: tuple) -> None:
        """Test that YAML tree matches expected output byte-for-byte."""
        terms, _, output_dir = processed_terms

        # Write YAML
        yaml_path = output_dir / "taxonomy_tree.yaml"
        write_taxonomy_tree_yaml(terms, yaml_path)

        # Compare with expected
        expected_path = EXPECTED_DIR / "taxonomy_tree.yaml"
        assert expected_path.exists(), f"Expected file not found: {expected_path}"

        actual_content = yaml_path.read_text(encoding="utf-8")
        expected_content = expected_path.read_text(encoding="utf-8")
        assert actual_content == expected_content, "YAML tree should match expected output"

    def test_taxonomy_clean_csv_matches_expected(self, processed_terms: tuple) -> None:
        """Test that clean CSV matches expected output byte-for-byte."""
        terms, _, output_dir = processed_terms

        # Write CSV
        csv_path = output_dir / "taxonomy_clean.csv"
        write_taxonomy_clean(terms, csv_path)

        # Compare with expected
        expected_path = EXPECTED_DIR / "taxonomy_clean.csv"
        assert expected_path.exists(), f"Expected file not found: {expected_path}"

        actual_content = csv_path.read_text(encoding="utf-8")
        expected_content = expected_path.read_text(encoding="utf-8")
        assert actual_content == expected_content, "Clean CSV should match expected output"

    def test_terms_normalized_csv_matches_expected(self, processed_terms: tuple) -> None:
        """Test that normalized CSV matches expected output byte-for-byte."""
        terms, _, output_dir = processed_terms

        # Write CSV
        csv_path = output_dir / "terms_normalized.csv"
        write_terms_normalized(terms, csv_path)

        # Compare with expected
        expected_path = EXPECTED_DIR / "terms_normalized.csv"
        assert expected_path.exists(), f"Expected file not found: {expected_path}"

        actual_content = csv_path.read_text(encoding="utf-8")
        expected_content = expected_path.read_text(encoding="utf-8")
        assert actual_content == expected_content, "Normalized CSV should match expected output"

    def test_dq_report_matches_expected(self, processed_terms: tuple) -> None:
        """Test that DQ report matches expected output byte-for-byte."""
        _, stats, output_dir = processed_terms

        # Generate report
        dq_report = generate_dq_report(stats)
        report_path = output_dir / "dq_report.md"
        report_path.write_text(dq_report, encoding="utf-8")

        # Compare with expected
        expected_path = EXPECTED_DIR / "dq_report.md"
        assert expected_path.exists(), f"Expected file not found: {expected_path}"

        actual_content = report_path.read_text(encoding="utf-8")
        expected_content = expected_path.read_text(encoding="utf-8")
        assert actual_content == expected_content, "DQ report should match expected output"

    def test_taxonomy_clean_csv_structure(self, processed_terms: tuple) -> None:
        """Test that clean CSV has correct structure."""
        terms, _, output_dir = processed_terms

        # Write CSV
        csv_path = output_dir / "taxonomy_clean.csv"
        write_taxonomy_clean(terms, csv_path)

        # Read and verify
        content = csv_path.read_text()
        lines = content.strip().split("\n")

        # Check header
        assert lines[0] == "level_1,level_2,level_3,level_4"

        # Check we have data rows
        assert len(lines) > 1

        # Verify no duplicate rows (deduplication worked)
        data_lines = lines[1:]
        assert len(data_lines) == len(set(data_lines)), "Should have no duplicate rows"

    def test_terms_normalized_csv_columns(self, processed_terms: tuple) -> None:
        """Test that normalized CSV has all required columns."""
        terms, _, output_dir = processed_terms

        # Write CSV
        csv_path = output_dir / "terms_normalized.csv"
        write_terms_normalized(terms, csv_path)

        # Read and verify header
        content = csv_path.read_text()
        header = content.strip().split("\n")[0]

        required_columns = [
            "taxon_path",
            "level1",
            "level2",
            "level3",
            "term_raw",
            "term_norm",
            "term_id",
            "taxon_id",
            "source_file",
            "row_index",
        ]

        for col in required_columns:
            assert col in header, f"Missing required column: {col}"

    def test_stats_counts(self, processed_terms: tuple) -> None:
        """Test that statistics are correctly calculated."""
        _, stats, _ = processed_terms

        # Check file count
        assert stats.files_processed == 1  # sample_taxonomy.csv

        # Check we processed rows
        assert stats.total_rows == 6  # 6 data rows in sample

        # Check we have unique values at each level
        assert len(stats.level1_values) == 2  # AI, Data
        assert len(stats.level2_values) >= 3  # Machine Learning, Deep Learning, Storage, Processing
        assert len(stats.level3_values) >= 3
        assert stats.unique_terms >= 10

    def test_duplicate_detection(self, processed_terms: tuple) -> None:
        """Test that duplicates are detected."""
        _, stats, _ = processed_terms

        # PostgreSQL appears twice in the sample
        assert stats.term_counts.get("PostgreSQL", 0) >= 2

    def test_tree_sorting(self, processed_terms: tuple) -> None:
        """Test that tree output is sorted for determinism."""
        terms, _, _ = processed_terms

        tree = build_taxonomy_tree(terms)

        # Check L1 sorted
        l1_keys = list(tree.keys())
        assert l1_keys == sorted(l1_keys)

        # Check L2 sorted within each L1
        for l1, l2_dict in tree.items():
            l2_keys = list(l2_dict.keys())
            assert l2_keys == sorted(l2_keys), f"L2 keys under {l1} not sorted"

            # Check L3 sorted within each L2
            for l2, l3_dict in l2_dict.items():
                l3_keys = list(l3_dict.keys())
                assert l3_keys == sorted(l3_keys), f"L3 keys under {l1}/{l2} not sorted"

                # Check terms sorted within each L3
                for l3, terms_list in l3_dict.items():
                    assert terms_list == sorted(terms_list), f"Terms under {l1}/{l2}/{l3} not sorted"

    def test_raw_norm_mapping_correctness(self, processed_terms: tuple) -> None:
        """Test that term_raw correctly maps to term_norm after normalization."""
        terms, _, _ = processed_terms

        for term in terms:
            # After normalization, term_raw should normalize to term_norm
            from meta.importer.normalizer import normalize_term
            assert normalize_term(term.term_raw) == term.term_norm, (
                f"term_raw '{term.term_raw}' should normalize to term_norm '{term.term_norm}'"
            )


class TestParenthesisPreservation:
    """Tests specifically for semicolon-in-parentheses preservation."""

    def test_vector_db_example_preserved(self) -> None:
        """Test the exact example from requirements is preserved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            terms, _ = process_taxonomy(FIXTURES_DIR, output_dir, strict=False)

            # Find the Vector DB term
            vector_db_terms = [
                t for t in terms
                if "Vector DB" in t.term_norm
            ]

            assert len(vector_db_terms) >= 1
            term = vector_db_terms[0]

            # Verify the semicolons inside parentheses are preserved
            assert "(Evidence; Implication; Playbook)" in term.term_norm

    def test_transformer_example_preserved(self) -> None:
        """Test Transformer (Attention; Self-Attention) is preserved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            terms, _ = process_taxonomy(FIXTURES_DIR, output_dir, strict=False)

            # Find the Transformer term
            transformer_terms = [
                t for t in terms
                if "Transformer" in t.term_norm
            ]

            assert len(transformer_terms) >= 1
            term = transformer_terms[0]

            # Verify the semicolon inside parentheses is preserved
            assert "(Attention; Self-Attention)" in term.term_norm

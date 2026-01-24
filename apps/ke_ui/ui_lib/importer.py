"""Importer wrapper for UI."""

import tempfile
from dataclasses import dataclass
from pathlib import Path

from meta.importer.dq_report import DQStats, generate_dq_report
from meta.importer.import_taxonomy import process_taxonomy
from meta.importer.outputs import (
    write_taxonomy_clean,
    write_taxonomy_tree_json,
    write_taxonomy_tree_yaml,
    write_terms_normalized,
)


@dataclass
class ImportResult:
    """Result of taxonomy import operation."""

    success: bool
    message: str
    output_dir: Path | None = None
    stats: DQStats | None = None
    files: dict[str, Path] | None = None


def run_import(
    input_files: list[tuple[str, bytes]],
    strict: bool = False,
) -> ImportResult:
    """Run taxonomy import on uploaded files.

    Args:
        input_files: List of (filename, content) tuples
        strict: Whether to fail on DQ issues

    Returns:
        ImportResult with paths to generated files
    """
    try:
        # Create temp directories
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "input"
            output_dir = Path(tmpdir) / "output"
            input_dir.mkdir()
            output_dir.mkdir()

            # Write uploaded files
            for filename, content in input_files:
                filepath = input_dir / filename
                filepath.write_bytes(content)

            # Run importer
            terms, stats = process_taxonomy(input_dir, output_dir, strict=strict)

            # Write outputs
            files = {}

            clean_csv = output_dir / "taxonomy_clean.csv"
            write_taxonomy_clean(terms, clean_csv)
            files["taxonomy_clean.csv"] = clean_csv

            norm_csv = output_dir / "terms_normalized.csv"
            write_terms_normalized(terms, norm_csv)
            files["terms_normalized.csv"] = norm_csv

            tree_json = output_dir / "taxonomy_tree.json"
            write_taxonomy_tree_json(terms, tree_json)
            files["taxonomy_tree.json"] = tree_json

            tree_yaml = output_dir / "taxonomy_tree.yaml"
            write_taxonomy_tree_yaml(terms, tree_yaml)
            files["taxonomy_tree.yaml"] = tree_yaml

            dq_report = output_dir / "dq_report.md"
            dq_report.write_text(generate_dq_report(stats), encoding="utf-8")
            files["dq_report.md"] = dq_report

            # Read file contents for result (since temp dir will be deleted)
            file_contents = {}
            for name, path in files.items():
                file_contents[name] = path.read_bytes()

            return ImportResult(
                success=True,
                message=f"Processed {stats.files_processed} file(s), {len(terms)} terms",
                stats=stats,
                files=file_contents,  # type: ignore
            )

    except Exception as e:
        return ImportResult(
            success=False,
            message=f"Import failed: {e}",
        )

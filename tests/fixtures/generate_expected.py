#!/usr/bin/env python3
"""Generate expected golden fixtures for tests.

Run this script once to generate the expected output files:
    python tests/fixtures/generate_expected.py

The generated files should be committed to the repository.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from meta.importer.import_taxonomy import process_taxonomy
from meta.importer.outputs import (
    write_taxonomy_clean,
    write_taxonomy_tree_json,
    write_taxonomy_tree_yaml,
    write_terms_normalized,
)
from meta.importer.dq_report import generate_dq_report


def main() -> None:
    """Generate all expected fixture files."""
    fixtures_dir = Path(__file__).parent
    expected_dir = fixtures_dir / "expected"
    expected_dir.mkdir(exist_ok=True)

    print(f"Generating expected fixtures in: {expected_dir}")

    # Process the sample taxonomy
    terms, stats = process_taxonomy(fixtures_dir, expected_dir, strict=False)

    print(f"  Processed {len(terms)} terms from {stats.files_processed} files")

    # Write all outputs
    write_taxonomy_clean(terms, expected_dir / "taxonomy_clean.csv")
    print("  ✓ taxonomy_clean.csv")

    write_terms_normalized(terms, expected_dir / "terms_normalized.csv")
    print("  ✓ terms_normalized.csv")

    write_taxonomy_tree_json(terms, expected_dir / "taxonomy_tree.json")
    print("  ✓ taxonomy_tree.json")

    write_taxonomy_tree_yaml(terms, expected_dir / "taxonomy_tree.yaml")
    print("  ✓ taxonomy_tree.yaml")

    dq_report = generate_dq_report(stats)
    (expected_dir / "dq_report.md").write_text(dq_report, encoding="utf-8")
    print("  ✓ dq_report.md")

    print("\n✅ All fixtures generated successfully!")
    print("   Commit these files to the repository.")


if __name__ == "__main__":
    main()

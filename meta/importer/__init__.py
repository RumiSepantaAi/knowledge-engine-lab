"""Meta-Blueprint Importer - CSV taxonomy import and normalization.

This package provides tools for importing, normalizing, and exporting
taxonomy data from CSV files.

Main entry point:
    python -m meta.importer.import_taxonomy --in meta/input --out meta/output

Modules:
    - parser: CSV parsing with column alias detection
    - splitter: Parenthesis-aware semicolon splitting
    - normalizer: Trim, typo correction, deduplication, ID generation
    - outputs: CSV, JSON, YAML output generation
    - dq_report: Data quality report generation
    - typo_map: Configurable typo corrections
"""

from meta.importer.normalizer import (
    build_taxon_path,
    dedupe,
    generate_taxon_id,
    generate_term_id,
    normalize_term,
    trim,
)
from meta.importer.outputs import NormalizedTerm
from meta.importer.parser import TaxonomyRow, parse_csv, parse_directory
from meta.importer.splitter import split_level4

__all__ = [
    # Splitter
    "split_level4",
    # Normalizer
    "trim",
    "normalize_term",
    "dedupe",
    "generate_taxon_id",
    "generate_term_id",
    "build_taxon_path",
    # Parser
    "TaxonomyRow",
    "parse_csv",
    "parse_directory",
    # Outputs
    "NormalizedTerm",
]

"""Output generators for taxonomy data.

Produces:
- taxonomy_clean.csv: Cleaned CSV with normalized columns
- terms_normalized.csv: Fully normalized terms with IDs
- taxonomy_tree.json: Hierarchical JSON structure
- taxonomy_tree.yaml: Hierarchical YAML structure
"""

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class NormalizedTerm:
    """A fully normalized taxonomy term."""

    taxon_path: str
    level1: str
    level2: str
    level3: str
    term_raw: str
    term_norm: str
    term_id: str
    taxon_id: str
    source_file: str
    row_index: int


def write_taxonomy_clean(terms: list[NormalizedTerm], output_path: Path) -> None:
    """Write the cleaned taxonomy CSV.

    Args:
        terms: List of normalized terms (should be pre-sorted).
        output_path: Path to write the CSV.
    """
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["level_1", "level_2", "level_3", "level_4"])

        # Dedupe by (L1, L2, L3, term_norm) while preserving input order
        seen: set[tuple[str, str, str, str]] = set()
        for term in terms:
            key = (term.level1, term.level2, term.level3, term.term_norm)
            if key not in seen:
                seen.add(key)
                writer.writerow([term.level1, term.level2, term.level3, term.term_norm])


def write_terms_normalized(terms: list[NormalizedTerm], output_path: Path) -> None:
    """Write the fully normalized terms CSV.

    Args:
        terms: List of normalized terms (should be pre-sorted).
        output_path: Path to write the CSV.
    """
    fieldnames = [
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

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for term in terms:
            writer.writerow({
                "taxon_path": term.taxon_path,
                "level1": term.level1,
                "level2": term.level2,
                "level3": term.level3,
                "term_raw": term.term_raw,
                "term_norm": term.term_norm,
                "term_id": term.term_id,
                "taxon_id": term.taxon_id,
                "source_file": term.source_file,
                "row_index": term.row_index,
            })


def build_taxonomy_tree(terms: list[NormalizedTerm]) -> dict[str, Any]:
    """Build a hierarchical taxonomy tree.

    Args:
        terms: List of normalized terms.

    Returns:
        Nested dict: L1 -> L2 -> L3 -> [terms], fully sorted for determinism.
    """
    tree: dict[str, Any] = {}

    for term in terms:
        l1, l2, l3 = term.level1, term.level2, term.level3

        if l1 not in tree:
            tree[l1] = {}
        if l2 not in tree[l1]:
            tree[l1][l2] = {}
        if l3 not in tree[l1][l2]:
            tree[l1][l2][l3] = []

        # Add term if not already present (dedupe)
        if term.term_norm not in tree[l1][l2][l3]:
            tree[l1][l2][l3].append(term.term_norm)

    # Sort for deterministic output
    sorted_tree: dict[str, Any] = {}
    for l1 in sorted(tree.keys()):
        sorted_tree[l1] = {}
        for l2 in sorted(tree[l1].keys()):
            sorted_tree[l1][l2] = {}
            for l3 in sorted(tree[l1][l2].keys()):
                sorted_tree[l1][l2][l3] = sorted(tree[l1][l2][l3])

    return sorted_tree


def write_taxonomy_tree_json(terms: list[NormalizedTerm], output_path: Path) -> None:
    """Write the taxonomy tree as JSON.

    Args:
        terms: List of normalized terms.
        output_path: Path to write the JSON.
    """
    tree = build_taxonomy_tree(terms)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(tree, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")  # Trailing newline for POSIX compliance


def write_taxonomy_tree_yaml(terms: list[NormalizedTerm], output_path: Path) -> None:
    """Write the taxonomy tree as YAML.

    Args:
        terms: List of normalized terms.
        output_path: Path to write the YAML.
    """
    tree = build_taxonomy_tree(terms)

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(tree, f, default_flow_style=False, allow_unicode=True, sort_keys=True)

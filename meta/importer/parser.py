"""CSV parser with column alias detection.

Handles:
- Multiple column name variations (aliases)
- UTF-8 with BOM support
- Header normalization
"""

import csv
from pathlib import Path
from typing import Iterator

# Column alias mappings: canonical -> list of aliases
# All matching is case-insensitive and whitespace-normalized
COLUMN_ALIASES: dict[str, list[str]] = {
    "level_1": ["level 1", "l1", "domain", "category", "level1", "lv1"],
    "level_2": ["level 2", "l2", "subdomain", "subcategory", "level2", "lv2"],
    "level_3": ["level 3", "l3", "topic", "area", "level3", "lv3"],
    "level_4": ["level 4", "l4", "term", "item", "terms", "level4", "lv4"],
}


def _normalize_header(header: str) -> str:
    """Normalize a header for matching.

    Args:
        header: Raw header string.

    Returns:
        Lowercased, trimmed, whitespace-normalized header.
    """
    return " ".join(header.lower().strip().split())


def _resolve_column_name(header: str) -> str | None:
    """Resolve a header to its canonical column name.

    Args:
        header: The raw header from the CSV.

    Returns:
        Canonical column name, or None if not recognized.
    """
    normalized = _normalize_header(header)

    for canonical, aliases in COLUMN_ALIASES.items():
        # Check canonical name itself
        if normalized == canonical.replace("_", " ") or normalized == canonical:
            return canonical
        # Check all aliases
        if normalized in [a.lower() for a in aliases]:
            return canonical

    return None


def detect_columns(headers: list[str]) -> dict[str, str]:
    """Detect which columns map to which canonical names.

    Args:
        headers: List of raw headers from the CSV.

    Returns:
        Dict mapping canonical names to original headers.

    Raises:
        ValueError: If required columns are missing.
    """
    mapping: dict[str, str] = {}

    for header in headers:
        canonical = _resolve_column_name(header)
        if canonical:
            mapping[canonical] = header

    # Validate required columns (at least level_4 is required)
    if "level_4" not in mapping:
        raise ValueError(
            f"Missing required column 'level_4'. Found headers: {headers}. "
            f"Accepted aliases: {COLUMN_ALIASES['level_4']}"
        )

    return mapping


class TaxonomyRow:
    """Represents a parsed row from a taxonomy CSV."""

    def __init__(
        self,
        level1: str,
        level2: str,
        level3: str,
        level4_raw: str,
        source_file: str,
        row_index: int,
    ) -> None:
        self.level1 = level1
        self.level2 = level2
        self.level3 = level3
        self.level4_raw = level4_raw
        self.source_file = source_file
        self.row_index = row_index

    def __repr__(self) -> str:
        return (
            f"TaxonomyRow(L1={self.level1!r}, L2={self.level2!r}, "
            f"L3={self.level3!r}, L4={self.level4_raw!r})"
        )


def parse_csv(filepath: Path) -> Iterator[TaxonomyRow]:
    """Parse a taxonomy CSV file.

    Args:
        filepath: Path to the CSV file.

    Yields:
        TaxonomyRow objects for each row.

    Raises:
        ValueError: If required columns are missing.
        FileNotFoundError: If file doesn't exist.
    """
    with open(filepath, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        if reader.fieldnames is None:
            raise ValueError(f"Empty CSV file: {filepath}")

        # Detect column mappings
        column_map = detect_columns(list(reader.fieldnames))

        for row_index, row in enumerate(reader, start=2):  # 1-indexed, skip header
            yield TaxonomyRow(
                level1=row.get(column_map.get("level_1", ""), "") or "",
                level2=row.get(column_map.get("level_2", ""), "") or "",
                level3=row.get(column_map.get("level_3", ""), "") or "",
                level4_raw=row.get(column_map.get("level_4", ""), "") or "",
                source_file=filepath.name,
                row_index=row_index,
            )


def parse_directory(dirpath: Path) -> Iterator[TaxonomyRow]:
    """Parse all CSV files in a directory.

    Args:
        dirpath: Path to directory containing CSV files.

    Yields:
        TaxonomyRow objects from all CSV files.
    """
    csv_files = sorted(dirpath.glob("*.csv"))

    if not csv_files:
        raise ValueError(f"No CSV files found in {dirpath}")

    for csv_file in csv_files:
        yield from parse_csv(csv_file)

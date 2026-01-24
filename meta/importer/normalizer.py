"""Normalization pipeline for taxonomy terms.

Provides functions for:
- Trimming whitespace
- Applying typo corrections
- Deduplicating while preserving order
- Generating deterministic UUIDs
"""

import uuid

from meta.importer.typo_map import NAMESPACE_META, get_typo_map

# Parse the namespace UUID from the constant
_NAMESPACE_UUID = uuid.UUID(NAMESPACE_META)


def trim(value: str | None) -> str:
    """Trim whitespace from a value.

    Args:
        value: The value to trim.

    Returns:
        Trimmed string, or empty string if None.
    """
    if value is None:
        return ""
    return value.strip()


def apply_typo_correction(value: str) -> str:
    """Apply typo corrections to a value.

    Args:
        value: The value to correct.

    Returns:
        Corrected value, or original if no typo found.
    """
    typo_map = get_typo_map()
    lower = value.lower()
    return typo_map.get(lower, value)


def normalize_term(value: str) -> str:
    """Normalize a single term: trim and apply typo correction.

    Args:
        value: The raw term value.

    Returns:
        Normalized term.
    """
    trimmed = trim(value)
    return apply_typo_correction(trimmed)


def dedupe(items: list[str]) -> list[str]:
    """Remove duplicates while preserving order.

    Args:
        items: List of items to dedupe.

    Returns:
        Deduped list with original order preserved.
    """
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def generate_taxon_id(taxon_path: str) -> str:
    """Generate a deterministic UUID for a taxon path.

    Args:
        taxon_path: Normalized taxon path (e.g., "L1 > L2 > L3").

    Returns:
        UUID string (lowercase with hyphens).
    """
    return str(uuid.uuid5(_NAMESPACE_UUID, taxon_path))


def generate_term_id(taxon_id: str, term_norm: str) -> str:
    """Generate a deterministic UUID for a term.

    Args:
        taxon_id: The parent taxon UUID.
        term_norm: Normalized term value.

    Returns:
        UUID string (lowercase with hyphens).
    """
    composite = f"{taxon_id}|{term_norm}"
    return str(uuid.uuid5(_NAMESPACE_UUID, composite))


def build_taxon_path(level1: str, level2: str, level3: str) -> str:
    """Build a normalized taxon path from levels.

    Args:
        level1: Level 1 value.
        level2: Level 2 value.
        level3: Level 3 value.

    Returns:
        Taxon path in format "L1 > L2 > L3".
    """
    return f"{level1} > {level2} > {level3}"

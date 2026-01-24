"""Configurable typo correction mapping.

This module contains the mapping of common typos to their corrected forms.
Extend the TYPO_MAP dictionary to add new corrections.
"""

# Fixed namespace for deterministic UUID generation
# Generated once, never changes: uuid.uuid5(uuid.NAMESPACE_DNS, "knowledge-engine.meta")
NAMESPACE_META = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"  # UUID as string for portability

# Typo correction mapping: {typo: correction}
# Keys are normalized to lowercase for matching
TYPO_MAP: dict[str, str] = {
    # AI/ML typos
    "artifical intelligence": "Artificial Intelligence",
    "artifical inteligence": "Artificial Intelligence",
    "machine learing": "Machine Learning",
    "machien learning": "Machine Learning",
    "deep learing": "Deep Learning",
    "nueral networks": "Neural Networks",
    "neural netwoks": "Neural Networks",
    # Data typos
    "postgre sql": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "mongo db": "MongoDB",
    "mongod b": "MongoDB",
    # Common abbreviation expansions (optional, can be disabled)
    # "ml": "Machine Learning",
    # "ai": "Artificial Intelligence",
    # "nlp": "Natural Language Processing",
}


def get_typo_map() -> dict[str, str]:
    """Return the typo correction mapping.

    Returns:
        Dictionary mapping lowercase typos to their corrected forms.
    """
    return TYPO_MAP.copy()


def add_typo_correction(typo: str, correction: str) -> None:
    """Add a new typo correction to the map.

    Args:
        typo: The typo string (will be lowercased).
        correction: The correct string.
    """
    TYPO_MAP[typo.lower()] = correction

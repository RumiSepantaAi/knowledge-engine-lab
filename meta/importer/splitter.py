"""Semicolon splitter with parenthesis awareness.

Splits Level-4 taxonomy terms on semicolons, but ONLY when the semicolon
is outside of parentheses. This preserves terms like:
    "3-Layer Vector DB (Evidence; Implication; Playbook)"
as a single item.
"""


def split_level4(value: str) -> list[str]:
    """Split a string on semicolons, but only when outside parentheses.

    Args:
        value: The string to split (typically a Level-4 taxonomy field).

    Returns:
        A list of trimmed, non-empty strings.

    Examples:
        >>> split_level4("A; B; C")
        ['A', 'B', 'C']
        >>> split_level4("3-Layer Vector DB (Evidence; Implication; Playbook)")
        ['3-Layer Vector DB (Evidence; Implication; Playbook)']
        >>> split_level4("Foo (a; b); Bar")
        ['Foo (a; b)', 'Bar']
    """
    if not value or not value.strip():
        return []

    results: list[str] = []
    current: list[str] = []
    depth = 0

    for char in value:
        if char == "(":
            depth += 1
            current.append(char)
        elif char == ")":
            depth = max(0, depth - 1)
            current.append(char)
        elif char == ";" and depth == 0:
            # Split point: outside parentheses
            term = "".join(current).strip()
            if term:
                results.append(term)
            current = []
        else:
            current.append(char)

    # Don't forget the last segment
    if current:
        term = "".join(current).strip()
        if term:
            results.append(term)

    return results

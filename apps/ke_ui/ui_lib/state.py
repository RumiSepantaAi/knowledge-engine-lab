"""Session state management for UI."""

import json
from pathlib import Path

import streamlit as st


def get_last_import_results() -> dict | None:
    """Get results from the last import run from session state."""
    return st.session_state.get("last_import_results")


def set_last_import_results(results: dict) -> None:
    """Store import results in session state."""
    st.session_state["last_import_results"] = results


def get_taxonomy_tree() -> dict | None:
    """Get taxonomy tree from session state or fallback files.

    Returns:
        Taxonomy tree dict or None if not available.
    """
    # First check session state
    results = get_last_import_results()
    if results and "taxonomy_tree.json" in results.get("files", {}):
        content = results["files"]["taxonomy_tree.json"]
        if isinstance(content, bytes):
            return json.loads(content.decode("utf-8"))
        return json.loads(content)

    # Fallback to meta/output
    fallback_paths = [
        Path("meta/output/taxonomy_tree.json"),
        Path("tests/fixtures/expected/taxonomy_tree.json"),
    ]

    for path in fallback_paths:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))

    return None


def get_dq_report() -> str | None:
    """Get DQ report from session state or fallback files.

    Returns:
        DQ report markdown or None if not available.
    """
    # First check session state
    results = get_last_import_results()
    if results and "dq_report.md" in results.get("files", {}):
        content = results["files"]["dq_report.md"]
        if isinstance(content, bytes):
            return content.decode("utf-8")
        return content

    # Fallback to meta/output
    fallback_paths = [
        Path("meta/output/dq_report.md"),
        Path("tests/fixtures/expected/dq_report.md"),
    ]

    for path in fallback_paths:
        if path.exists():
            return path.read_text(encoding="utf-8")

    return None

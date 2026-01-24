"""Data quality report generator.

Analyzes taxonomy data and produces a Markdown report with:
- Summary statistics
- Counts by level
- Missing levels
- Duplicate terms
- Empty terms
- Suspicious split candidates
"""

from dataclasses import dataclass, field


@dataclass
class DQIssue:
    """A single data quality issue."""

    category: str
    row_index: int
    source_file: str
    description: str


@dataclass
class DQStats:
    """Data quality statistics."""

    files_processed: int = 0
    total_rows: int = 0
    unique_terms: int = 0
    level1_values: set[str] = field(default_factory=set)
    level2_values: set[str] = field(default_factory=set)
    level3_values: set[str] = field(default_factory=set)
    level4_values: set[str] = field(default_factory=set)
    issues: list[DQIssue] = field(default_factory=list)
    term_counts: dict[str, int] = field(default_factory=dict)

    def add_issue(
        self, category: str, row_index: int, source_file: str, description: str
    ) -> None:
        """Add a data quality issue."""
        self.issues.append(DQIssue(category, row_index, source_file, description))

    def get_issues_by_category(self, category: str) -> list[DQIssue]:
        """Get all issues of a specific category."""
        return [i for i in self.issues if i.category == category]


def check_suspicious_splits(term: str) -> list[str]:
    """Check for potential split candidates that weren't split.

    Args:
        term: The term to check.

    Returns:
        List of suspicious patterns found.
    """
    suspicious: list[str] = []

    # Check for common separators that might indicate need for splitting
    if "/" in term and "http" not in term.lower():
        suspicious.append('contains "/" - consider splitting?')
    if " or " in term.lower():
        suspicious.append('contains " or " - consider splitting?')
    if " and " in term.lower() and len(term) > 50:
        suspicious.append('long term with " and " - consider splitting?')

    return suspicious


def generate_dq_report(stats: DQStats) -> str:
    """Generate a Markdown data quality report.

    Args:
        stats: The collected statistics.

    Returns:
        Markdown-formatted report string.
    """
    lines: list[str] = []

    # Header
    lines.append("# Data Quality Report")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Files processed: {stats.files_processed}")
    lines.append(f"- Total rows: {stats.total_rows}")
    lines.append(f"- Unique terms: {stats.unique_terms}")
    lines.append("")

    # Counts by level
    lines.append("## Counts by Level")
    lines.append("")
    lines.append("| Level | Unique Values |")
    lines.append("|-------|---------------|")
    lines.append(f"| L1    | {len(stats.level1_values):>13} |")
    lines.append(f"| L2    | {len(stats.level2_values):>13} |")
    lines.append(f"| L3    | {len(stats.level3_values):>13} |")
    lines.append(f"| L4    | {len(stats.level4_values):>13} |")
    lines.append("")

    # Issues section
    lines.append("## Issues Found")
    lines.append("")

    # Missing levels - count unique rows, not total issues
    missing = stats.get_issues_by_category("missing_level")
    if missing:
        # Count unique rows affected
        missing_rows = {(issue.source_file, issue.row_index) for issue in missing}
        unique_row_count = len(missing_rows)

        # Count by level type
        missing_l1 = sum(1 for i in missing if i.description == "Missing L1")
        missing_l2 = sum(1 for i in missing if i.description == "Missing L2")
        missing_l3 = sum(1 for i in missing if i.description == "Missing L3")

        lines.append(f"### Missing Levels ({unique_row_count} rows)")
        lines.append("")
        lines.append("| Level | Count |")
        lines.append("|-------|-------|")
        lines.append(f"| L1    | {missing_l1:>5} |")
        lines.append(f"| L2    | {missing_l2:>5} |")
        lines.append(f"| L3    | {missing_l3:>5} |")
        lines.append("")

        # List individual issues (sorted for determinism)
        sorted_missing = sorted(missing, key=lambda i: (i.source_file, i.row_index, i.description))
        for issue in sorted_missing[:20]:
            lines.append(f"- Row {issue.row_index} ({issue.source_file}): {issue.description}")
        if len(sorted_missing) > 20:
            lines.append(f"- ... and {len(sorted_missing) - 20} more")
        lines.append("")
    else:
        lines.append("### Missing Levels")
        lines.append("")
        lines.append("None found.")
        lines.append("")

    # Duplicate terms
    duplicates = [(term, count) for term, count in stats.term_counts.items() if count > 1]
    duplicates.sort(key=lambda x: (-x[1], x[0]))  # Sort by count desc, then term asc
    if duplicates:
        lines.append(f"### Duplicate Terms ({len(duplicates)} terms)")
        lines.append("")
        for term, count in duplicates[:20]:
            lines.append(f'- "{term}" appears {count}x')
        if len(duplicates) > 20:
            lines.append(f"- ... and {len(duplicates) - 20} more")
        lines.append("")
    else:
        lines.append("### Duplicate Terms")
        lines.append("")
        lines.append("None found.")
        lines.append("")

    # Empty terms
    empty = stats.get_issues_by_category("empty_term")
    if empty:
        # Sort for determinism
        sorted_empty = sorted(empty, key=lambda i: (i.source_file, i.row_index))
        lines.append(f"### Empty Terms ({len(sorted_empty)} rows)")
        lines.append("")
        for issue in sorted_empty[:20]:
            lines.append(f"- Row {issue.row_index} ({issue.source_file}): {issue.description}")
        if len(sorted_empty) > 20:
            lines.append(f"- ... and {len(sorted_empty) - 20} more")
        lines.append("")
    else:
        lines.append("### Empty Terms")
        lines.append("")
        lines.append("None found.")
        lines.append("")

    # Suspicious split candidates - include row/file info
    suspicious = stats.get_issues_by_category("suspicious_split")
    if suspicious:
        # Sort for determinism
        sorted_suspicious = sorted(
            suspicious, key=lambda i: (i.source_file, i.row_index, i.description)
        )
        lines.append(f"### Suspicious Split Candidates ({len(sorted_suspicious)} terms)")
        lines.append("")
        for issue in sorted_suspicious[:20]:
            lines.append(f"- Row {issue.row_index} ({issue.source_file}): {issue.description}")
        if len(sorted_suspicious) > 20:
            lines.append(f"- ... and {len(sorted_suspicious) - 20} more")
        lines.append("")
    else:
        lines.append("### Suspicious Split Candidates")
        lines.append("")
        lines.append("None found.")
        lines.append("")

    return "\n".join(lines)

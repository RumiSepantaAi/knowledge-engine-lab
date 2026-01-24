"""CLI entry point for the taxonomy importer.

Usage:
    python -m meta.importer.import_taxonomy --in meta/input --out meta/output
    python -m meta.importer.import_taxonomy --in meta/input --out meta/output --strict
"""

from pathlib import Path

import typer
from rich.console import Console

from meta.importer.dq_report import DQStats, check_suspicious_splits, generate_dq_report
from meta.importer.normalizer import (
    build_taxon_path,
    generate_taxon_id,
    generate_term_id,
    normalize_term,
    trim,
)
from meta.importer.outputs import (
    NormalizedTerm,
    write_taxonomy_clean,
    write_taxonomy_tree_json,
    write_taxonomy_tree_yaml,
    write_terms_normalized,
)
from meta.importer.parser import parse_directory
from meta.importer.splitter import split_level4

app = typer.Typer(
    name="import_taxonomy",
    help="Import and normalize taxonomy CSV files.",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()


def _dedupe_with_raw_mapping(raw_terms: list[str]) -> list[tuple[str, str]]:
    """Dedupe terms by normalized value while preserving first raw string.

    Args:
        raw_terms: List of raw term strings.

    Returns:
        List of (term_raw, term_norm) tuples in stable order, deduped by term_norm.
    """
    seen: set[str] = set()
    first_raw: dict[str, str] = {}
    order: list[str] = []

    for raw in raw_terms:
        norm = normalize_term(raw)
        if norm not in seen:
            seen.add(norm)
            first_raw[norm] = raw
            order.append(norm)

    return [(first_raw[norm], norm) for norm in order]


def _sort_terms(terms: list[NormalizedTerm]) -> list[NormalizedTerm]:
    """Sort terms deterministically for stable output.

    Args:
        terms: List of normalized terms.

    Returns:
        Sorted list by (taxon_path, term_norm, source_file, row_index).
    """
    return sorted(
        terms,
        key=lambda t: (t.taxon_path, t.term_norm, t.source_file, t.row_index),
    )


def process_taxonomy(
    input_dir: Path,
    output_dir: Path,
    strict: bool = False,
) -> tuple[list[NormalizedTerm], DQStats]:
    """Process taxonomy CSV files and generate outputs.

    Args:
        input_dir: Directory containing input CSV files.
        output_dir: Directory to write output files.
        strict: If True, fail on any DQ issues.

    Returns:
        Tuple of (normalized terms, DQ stats).
    """
    stats = DQStats()
    terms: list[NormalizedTerm] = []
    processed_files: set[str] = set()

    # Parse all CSV files
    for row in parse_directory(input_dir):
        # Track files
        if row.source_file not in processed_files:
            processed_files.add(row.source_file)
            stats.files_processed += 1

        stats.total_rows += 1

        # Normalize levels
        l1 = trim(row.level1)
        l2 = trim(row.level2)
        l3 = trim(row.level3)

        # Track unique values
        if l1:
            stats.level1_values.add(l1)
        if l2:
            stats.level2_values.add(l2)
        if l3:
            stats.level3_values.add(l3)

        # Check for missing levels
        if not l1:
            stats.add_issue("missing_level", row.row_index, row.source_file, "Missing L1")
        if not l2:
            stats.add_issue("missing_level", row.row_index, row.source_file, "Missing L2")
        if not l3:
            stats.add_issue("missing_level", row.row_index, row.source_file, "Missing L3")

        # Build taxon path and ID
        taxon_path = build_taxon_path(l1, l2, l3)
        taxon_id = generate_taxon_id(taxon_path)

        # Split Level 4 terms
        raw_terms = split_level4(row.level4_raw)

        if not raw_terms:
            stats.add_issue(
                "empty_term", row.row_index, row.source_file, "Empty L4 after split"
            )
            continue

        # Dedupe terms while preserving correct raw↔norm mapping
        deduped_pairs = _dedupe_with_raw_mapping(raw_terms)

        for term_raw, term_norm in deduped_pairs:
            # Generate term ID
            term_id = generate_term_id(taxon_id, term_norm)

            # Track for stats
            stats.level4_values.add(term_norm)
            stats.term_counts[term_norm] = stats.term_counts.get(term_norm, 0) + 1

            # Check for suspicious patterns
            suspicious = check_suspicious_splits(term_norm)
            for s in suspicious:
                stats.add_issue(
                    "suspicious_split",
                    row.row_index,
                    row.source_file,
                    f"{term_norm}: {s}",
                )

            # Create normalized term
            terms.append(NormalizedTerm(
                taxon_path=taxon_path,
                level1=l1,
                level2=l2,
                level3=l3,
                term_raw=term_raw,
                term_norm=term_norm,
                term_id=term_id,
                taxon_id=taxon_id,
                source_file=row.source_file,
                row_index=row.row_index,
            ))

    stats.unique_terms = len(stats.level4_values)

    # Sort terms deterministically
    terms = _sort_terms(terms)

    return terms, stats


@app.command()
def main(
    input_dir: Path = typer.Option(
        ...,
        "--in",
        "-i",
        help="Input directory containing CSV files",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    output_dir: Path = typer.Option(
        ...,
        "--out",
        "-o",
        help="Output directory for generated files",
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        "-s",
        help="Fail on any data quality issues",
    ),
) -> None:
    """Import and normalize taxonomy CSV files."""
    console.print(f"[bold]Importing taxonomy from:[/bold] {input_dir}")
    console.print(f"[bold]Output directory:[/bold] {output_dir}")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Process taxonomy
        terms, stats = process_taxonomy(input_dir, output_dir, strict)

        if not terms:
            console.print("[red]Error:[/red] No terms extracted from input files")
            raise typer.Exit(2)

        # Write outputs (terms are already sorted)
        console.print("[dim]Writing taxonomy_clean.csv...[/dim]")
        write_taxonomy_clean(terms, output_dir / "taxonomy_clean.csv")

        console.print("[dim]Writing terms_normalized.csv...[/dim]")
        write_terms_normalized(terms, output_dir / "terms_normalized.csv")

        console.print("[dim]Writing taxonomy_tree.json...[/dim]")
        write_taxonomy_tree_json(terms, output_dir / "taxonomy_tree.json")

        console.print("[dim]Writing taxonomy_tree.yaml...[/dim]")
        write_taxonomy_tree_yaml(terms, output_dir / "taxonomy_tree.yaml")

        # Write DQ report
        console.print("[dim]Writing dq_report.md...[/dim]")
        dq_report = generate_dq_report(stats)
        (output_dir / "dq_report.md").write_text(dq_report, encoding="utf-8")

        # Summary
        console.print("")
        console.print("[bold green]✅ Import complete![/bold green]")
        console.print(f"   Files: {stats.files_processed}")
        console.print(f"   Rows: {stats.total_rows}")
        console.print(f"   Terms: {stats.unique_terms}")
        console.print(f"   Issues: {len(stats.issues)}")

        # Check for issues in strict mode
        if strict and stats.issues:
            console.print("")
            console.print(f"[red]Strict mode: {len(stats.issues)} issues found[/red]")
            console.print("See dq_report.md for details.")
            raise typer.Exit(1)

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(2) from e
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(2) from e


if __name__ == "__main__":
    app()

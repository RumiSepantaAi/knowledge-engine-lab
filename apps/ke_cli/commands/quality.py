"""ke quality - Quality gate commands."""

from uuid import UUID

import typer
from rich.console import Console
from rich.table import Table

from apps.ke_db.connection import get_connection
from apps.ke_db.documents import get_document_by_doc_id
from apps.ke_db.quality import (
    check_quality_gate,
    get_claims_without_evidence,
    set_document_validated,
)

app = typer.Typer(help="Quality gate commands")
console = Console()


@app.command("gate")
def run_quality_gate(
    revision_id: str = typer.Argument(..., help="Revision UUID"),
    validate: bool = typer.Option(
        False, "--validate", "-v", help="Set document to validated if passing"
    ),
) -> None:
    """Run quality gate check for a revision."""
    console.print("\n[bold cyan]🔍 Quality Gate Check[/bold cyan]\n")

    rev_uuid = UUID(revision_id)

    try:
        with get_connection() as conn:
            result = check_quality_gate(conn, rev_uuid)

            console.print(f"  Total claims: {result['total_claims']}")
            console.print(f"  With evidence: {result['claims_with_evidence']}")
            console.print(f"  Without evidence: {result['claims_without_evidence']}")
            console.print()

            if result["passed"]:
                console.print("[bold green]✅ PASS[/bold green] - All claims have evidence!")

                if validate:
                    # Get document ID from revision
                    cur = conn.cursor()
                    cur.execute(
                        "SELECT document_id FROM evidence.document_revision WHERE id = %s",
                        (rev_uuid,),
                    )
                    row = cur.fetchone()
                    if row:
                        doc_id = row[0]
                        if set_document_validated(conn, doc_id):
                            conn.commit()
                            console.print("[green]  Document status set to 'validated'[/green]")
                        else:
                            console.print("[dim]  Document already validated[/dim]")
            else:
                console.print("[bold red]❌ FAIL[/bold red] - Claims without evidence found:")

                # Show claims without evidence
                missing = get_claims_without_evidence(conn, rev_uuid)
                if missing:
                    table = Table()
                    table.add_column("Claim ID")
                    table.add_column("Type")
                    table.add_column("Preview")

                    for c in missing[:10]:  # Limit to 10
                        table.add_row(
                            str(c["id"])[:8] + "...",
                            c["claim_type"],
                            c["preview"],
                        )

                    console.print(table)

                    if len(missing) > 10:
                        console.print(f"  [dim]... and {len(missing) - 10} more[/dim]")

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Abort()


@app.command("status")
def check_status(doc_id: str = typer.Argument(..., help="Document ID")) -> None:
    """Check validation status of a document."""
    try:
        with get_connection() as conn:
            doc = get_document_by_doc_id(conn, doc_id)

        if not doc:
            console.print(f"[yellow]Document not found: {doc_id}[/yellow]")
            return

        status = doc["status"]
        if status == "validated":
            console.print(f"[green]✅ {doc_id}: VALIDATED[/green]")
        else:
            console.print(f"[yellow]⏳ {doc_id}: {status}[/yellow]")

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")

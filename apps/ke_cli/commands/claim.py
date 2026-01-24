"""ke claim - Claim management commands."""

from uuid import UUID

import typer
from rich.console import Console
from rich.table import Table

from apps.ke_db.claims import create_claim, list_claims_for_revision
from apps.ke_db.connection import get_connection

app = typer.Typer(help="Claim management commands")
console = Console()

CLAIM_TYPES = ["fact", "definition", "requirement", "recommendation", "metric", "other"]


@app.command("add")
def add_claims(
    revision_id: str = typer.Option(..., "--revision", "-r", help="Revision UUID"),
    count: int = typer.Option(10, "--count", "-n", help="Number of claims to add"),
) -> None:
    """Add claims to a revision interactively."""
    console.print("\n[bold cyan]📝 Add Claims[/bold cyan]\n")

    if count < 1 or count > 50:
        console.print("[red]❌ Count must be between 1 and 50[/red]")
        raise typer.Abort()

    rev_uuid = UUID(revision_id)
    claims_data = []

    for i in range(count):
        console.print(f"\n[bold]Claim #{i + 1}[/bold]")

        claim_text = typer.prompt("Claim text")

        console.print(f"  Types: {', '.join(CLAIM_TYPES)}")
        claim_type = typer.prompt("Type", default="other")
        if claim_type not in CLAIM_TYPES:
            console.print(f"[yellow]⚠️  Unknown type, using 'other'[/yellow]")
            claim_type = "other"

        conf_str = typer.prompt("Confidence (0.0-1.0)", default="0.70")
        try:
            confidence = float(conf_str)
            if confidence < 0 or confidence > 1:
                raise ValueError()
        except ValueError:
            console.print("[yellow]⚠️  Invalid confidence, using 0.70[/yellow]")
            confidence = 0.70

        claims_data.append({
            "claim_text": claim_text,
            "claim_type": claim_type,
            "confidence": confidence,
        })

        if i < count - 1:
            if not typer.confirm("Continue to next claim?", default=True):
                break

    # Summary
    console.print(f"\n[bold]Summary: {len(claims_data)} claim(s)[/bold]")
    table = Table()
    table.add_column("#")
    table.add_column("Type")
    table.add_column("Conf")
    table.add_column("Preview")

    for i, c in enumerate(claims_data, 1):
        table.add_row(
            str(i),
            c["claim_type"],
            f"{c['confidence']:.2f}",
            c["claim_text"][:50] + "..." if len(c["claim_text"]) > 50 else c["claim_text"],
        )

    console.print(table)

    if not typer.confirm("\nCommit to database?", default=False):
        console.print("[yellow]Aborted.[/yellow]")
        raise typer.Abort()

    # Insert
    try:
        with get_connection() as conn:
            for c in claims_data:
                create_claim(
                    conn,
                    revision_id=rev_uuid,
                    claim_text=c["claim_text"],
                    claim_type=c["claim_type"],
                    confidence=c["confidence"],
                )
            conn.commit()

        console.print(f"\n[green]✅ {len(claims_data)} claim(s) created![/green]")

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Abort()


@app.command("list")
def list_claims(
    revision_id: str = typer.Argument(..., help="Revision UUID"),
) -> None:
    """List claims for a revision."""
    try:
        rev_uuid = UUID(revision_id)
        with get_connection() as conn:
            claims = list_claims_for_revision(conn, rev_uuid)

        if not claims:
            console.print("[yellow]No claims found.[/yellow]")
            return

        table = Table(title="Claims")
        table.add_column("ID")
        table.add_column("Type")
        table.add_column("Conf")
        table.add_column("Preview")

        for c in claims:
            table.add_row(
                str(c["id"])[:8] + "...",
                c["claim_type"],
                f"{c['confidence']:.2f}",
                c["preview"],
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")

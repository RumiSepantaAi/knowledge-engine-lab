"""ke evidence - Evidence span management commands."""

from uuid import UUID

import typer
from rich.console import Console
from rich.table import Table

from apps.ke_db.connection import get_connection
from apps.ke_db.evidence import create_evidence_span, list_evidence_for_claim

app = typer.Typer(help="Evidence span management commands")
console = Console()

EVIDENCE_ROLES = ["supports", "contradicts", "mentions"]


@app.command("add")
def add_evidence(
    claim_id: str = typer.Option(..., "--claim", "-c", help="Claim UUID"),
    chunk_id: str = typer.Option(..., "--chunk", "-k", help="Chunk UUID"),
) -> None:
    """Add evidence linking claim to chunk."""
    console.print("\n[bold cyan]🔗 Add Evidence Span[/bold cyan]\n")

    claim_uuid = UUID(claim_id)
    chunk_uuid = UUID(chunk_id)

    console.print(f"  Roles: {', '.join(EVIDENCE_ROLES)}")
    role = typer.prompt("Role", default="supports")
    if role not in EVIDENCE_ROLES:
        console.print(f"[yellow]⚠️  Unknown role, using 'supports'[/yellow]")
        role = "supports"

    page_str = typer.prompt("Page number", default="", show_default=False)
    page_no = int(page_str) if page_str else None

    snippet = typer.prompt("Evidence snippet (quote)")

    strength_str = typer.prompt("Support strength (0.0-1.0)", default="0.80")
    try:
        support_strength = float(strength_str)
        if support_strength < 0 or support_strength > 1:
            raise ValueError()
    except ValueError:
        console.print("[yellow]⚠️  Invalid strength, using 0.80[/yellow]")
        support_strength = 0.80

    # Summary
    console.print("\n[bold]Summary:[/bold]")
    table = Table(show_header=False, box=None)
    table.add_column("Field", style="dim")
    table.add_column("Value")
    table.add_row("Claim", claim_id[:16] + "...")
    table.add_row("Chunk", chunk_id[:16] + "...")
    table.add_row("Role", role)
    table.add_row("Page", str(page_no) if page_no else "(none)")
    table.add_row("Strength", f"{support_strength:.2f}")
    table.add_row("Snippet", snippet[:60] + "..." if len(snippet) > 60 else snippet)
    console.print(table)

    if not typer.confirm("\nCommit to database?", default=False):
        console.print("[yellow]Aborted.[/yellow]")
        raise typer.Abort()

    # Insert
    try:
        with get_connection() as conn:
            span_uuid = create_evidence_span(
                conn,
                claim_id=claim_uuid,
                chunk_id=chunk_uuid,
                snippet=snippet,
                role=role,
                page_no=page_no,
                support_strength=support_strength,
            )
            conn.commit()

        console.print("\n[green]✅ Evidence span created![/green]")
        console.print(f"  Span UUID: [cyan]{span_uuid}[/cyan]")

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Abort()


@app.command("list")
def list_evidence(
    claim_id: str = typer.Argument(..., help="Claim UUID"),
) -> None:
    """List evidence spans for a claim."""
    try:
        claim_uuid = UUID(claim_id)
        with get_connection() as conn:
            spans = list_evidence_for_claim(conn, claim_uuid)

        if not spans:
            console.print("[yellow]No evidence found for this claim.[/yellow]")
            return

        table = Table(title="Evidence Spans")
        table.add_column("ID")
        table.add_column("Role")
        table.add_column("Strength")
        table.add_column("Preview")

        for s in spans:
            table.add_row(
                str(s["id"])[:8] + "...",
                s["role"],
                f"{s['support_strength']:.2f}",
                s["preview"],
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")

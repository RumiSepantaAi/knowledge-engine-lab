"""Knowledge Engine CLI - Main entry point.

This module provides the interactive CLI for managing the Knowledge Engine.
"""

import typer
from rich.console import Console

from apps.ke_cli.commands import doc, chunk, claim, evidence, quality, embed

app = typer.Typer(
    name="ke",
    help="Knowledge Engine CLI - Manage knowledge graphs and evidence.",
    add_completion=False,
)
console = Console()

# Register command groups
app.add_typer(doc.app, name="doc", help="Document management")
app.add_typer(chunk.app, name="chunk", help="Chunk management")
app.add_typer(claim.app, name="claim", help="Claim management")
app.add_typer(evidence.app, name="evidence", help="Evidence management")
app.add_typer(quality.app, name="quality", help="Quality gates")
app.add_typer(embed.app, name="embed", help="Embedding generation")


@app.command()
def hello() -> None:
    """Verify CLI is working."""
    console.print("[green]✅ Knowledge Engine CLI ready.[/green]")


@app.command()
def version() -> None:
    """Show version information."""
    console.print("[bold]Knowledge Engine[/bold] v0.1.0")


@app.command()
def status() -> None:
    """Show system status."""
    from apps.ke_db.connection import get_connection

    console.print("[bold]System Status[/bold]\n")

    # Check DB connection
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                console.print("  Database: [green]✅ Connected[/green]")

                # Check if schema exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = 'evidence' AND table_name = 'document'
                    )
                """)
                schema_exists = cur.fetchone()[0]

                if not schema_exists:
                    console.print("  Schema: [red]❌ Missing[/red]")
                    console.print(
                        "\n  [yellow]⚠️  Database schema not initialized.[/yellow]"
                    )
                    console.print("  Run: [bold cyan]make db-migrate[/bold cyan]")
                    return

                console.print("  Schema: [green]✅ Initialized[/green]")

                # Count documents
                cur.execute("SELECT COUNT(*) FROM evidence.document")
                doc_count = cur.fetchone()[0]
                console.print(f"  Documents: {doc_count}")

                # Count claims
                cur.execute("SELECT COUNT(*) FROM evidence.claim")
                claim_count = cur.fetchone()[0]
                console.print(f"  Claims: {claim_count}")

    except Exception as e:
        console.print(f"  Database: [red]❌ Error: {e}[/red]")


if __name__ == "__main__":
    app()

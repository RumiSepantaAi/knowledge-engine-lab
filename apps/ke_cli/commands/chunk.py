"""ke chunk - Chunk management commands."""

from uuid import UUID

import typer
from rich.console import Console
from rich.table import Table

from apps.ke_db.chunks import create_chunk, get_next_chunk_no, list_chunks_for_revision
from apps.ke_db.connection import get_connection

app = typer.Typer(help="Chunk management commands")
console = Console()


@app.command("add")
def add_chunks(
    revision_id: str = typer.Option(..., "--revision", "-r", help="Revision UUID"),
    count: int = typer.Option(4, "--count", "-n", help="Number of chunks to add (4-8)"),
) -> None:
    """Add chunks to a revision interactively."""
    console.print("\n[bold cyan]📦 Add Chunks[/bold cyan]\n")

    if count < 1 or count > 20:
        console.print("[red]❌ Count must be between 1 and 20[/red]")
        raise typer.Abort()

    rev_uuid = UUID(revision_id)
    chunks_data = []

    try:
        with get_connection() as conn:
            start_no = get_next_chunk_no(conn, rev_uuid)

        for i in range(count):
            chunk_no = start_no + i
            console.print(f"\n[bold]Chunk #{chunk_no}[/bold]")

            text = typer.prompt("Text content")
            page_str = typer.prompt("Page number", default="", show_default=False)
            page = int(page_str) if page_str else None

            section = typer.prompt("Section path", default="", show_default=False) or None

            chunks_data.append({
                "chunk_no": chunk_no,
                "text": text,
                "page_start": page,
                "page_end": page,
                "section_path": section,
            })

            if i < count - 1:
                if not typer.confirm("Continue to next chunk?", default=True):
                    break

        # Summary
        console.print(f"\n[bold]Summary: {len(chunks_data)} chunk(s)[/bold]")
        table = Table()
        table.add_column("#")
        table.add_column("Page")
        table.add_column("Preview")

        for c in chunks_data:
            table.add_row(
                str(c["chunk_no"]),
                str(c["page_start"] or "-"),
                c["text"][:50] + "..." if len(c["text"]) > 50 else c["text"],
            )

        console.print(table)

        if not typer.confirm("\nCommit to database?", default=False):
            console.print("[yellow]Aborted.[/yellow]")
            raise typer.Abort()

        # Insert
        with get_connection() as conn:
            for c in chunks_data:
                create_chunk(
                    conn,
                    revision_id=rev_uuid,
                    chunk_no=c["chunk_no"],
                    text=c["text"],
                    page_start=c["page_start"],
                    page_end=c["page_end"],
                    section_path=c["section_path"],
                )
            conn.commit()

        console.print(f"\n[green]✅ {len(chunks_data)} chunk(s) created![/green]")

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Abort()


@app.command("list")
def list_chunks(
    revision_id: str = typer.Argument(..., help="Revision UUID"),
) -> None:
    """List chunks for a revision."""
    try:
        rev_uuid = UUID(revision_id)
        with get_connection() as conn:
            chunks = list_chunks_for_revision(conn, rev_uuid)

        if not chunks:
            console.print("[yellow]No chunks found.[/yellow]")
            return

        table = Table(title="Chunks")
        table.add_column("#")
        table.add_column("Page")
        table.add_column("Preview")
        table.add_column("ID")

        for c in chunks:
            table.add_row(
                str(c["chunk_no"]),
                str(c["page_start"] or "-"),
                c["preview"],
                str(c["id"])[:8] + "...",
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")

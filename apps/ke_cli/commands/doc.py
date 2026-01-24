"""ke doc - Document management commands."""

from datetime import date
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from apps.ke_db.connection import get_connection
from apps.ke_db.documents import (
    create_document,
    create_revision,
    get_document_by_doc_id,
    list_documents,
)
from apps.ke_db.utils import compute_sha256, validate_doc_id

app = typer.Typer(help="Document management commands")
console = Console()


@app.command("add")
def add_document() -> None:
    """Add a new document interactively."""
    console.print("\n[bold cyan]📄 Add New Document[/bold cyan]\n")

    # Prompt for required fields
    doc_id = typer.prompt("Document ID (e.g. DOC-0001)")
    if not validate_doc_id(doc_id):
        console.print(f"[red]❌ Invalid doc_id format. Use XXX-NNNN (e.g. DOC-0001)[/red]")
        raise typer.Abort()

    title = typer.prompt("Title")

    # Prompt for optional fields
    authors = typer.prompt("Authors", default="", show_default=False) or None
    publisher_org = typer.prompt("Publisher Organization", default="", show_default=False) or None

    pub_date_str = typer.prompt("Published Date (YYYY-MM-DD)", default="", show_default=False)
    published_date: date | None = None
    if pub_date_str:
        try:
            published_date = date.fromisoformat(pub_date_str)
        except ValueError:
            console.print("[yellow]⚠️  Invalid date format, skipping.[/yellow]")

    source_url = typer.prompt("Source URL", default="", show_default=False) or None
    file_path = typer.prompt("File path (PDF)")

    # Validate file exists
    path = Path(file_path)
    if not path.exists():
        console.print(f"[red]❌ File not found: {file_path}[/red]")
        raise typer.Abort()

    tags_str = typer.prompt("Tags (comma-separated)", default="", show_default=False)
    tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []

    # Compute SHA256
    console.print("\n[dim]Computing SHA256...[/dim]")
    sha256 = compute_sha256(path)
    console.print(f"  SHA256: [cyan]{sha256[:16]}...[/cyan]")

    # Summary
    console.print("\n[bold]Summary:[/bold]")
    table = Table(show_header=False, box=None)
    table.add_column("Field", style="dim")
    table.add_column("Value")
    table.add_row("Doc ID", doc_id)
    table.add_row("Title", title)
    table.add_row("Authors", authors or "(none)")
    table.add_row("Publisher", publisher_org or "(none)")
    table.add_row("Published", str(published_date) if published_date else "(none)")
    table.add_row("File", str(path))
    table.add_row("SHA256", f"{sha256[:32]}...")
    table.add_row("Tags", ", ".join(tags) if tags else "(none)")
    console.print(table)

    # Confirm
    if not typer.confirm("\nCommit to database?", default=False):
        console.print("[yellow]Aborted.[/yellow]")
        raise typer.Abort()

    # Insert
    try:
        with get_connection() as conn:
            doc_uuid = create_document(
                conn,
                doc_id=doc_id,
                title=title,
                file_uri=str(path.absolute()),
                sha256=sha256,
                authors=authors,
                publisher_org=publisher_org,
                published_date=published_date,
                source_url=source_url,
                tags=tags,
            )

            # Create initial revision
            rev_uuid = create_revision(
                conn,
                document_id=doc_uuid,
                revision_no=1,
                sha256=sha256,
                file_uri=str(path.absolute()),
                parser_version="manual/v1",
                notes="Initial revision",
            )

            conn.commit()

            console.print("\n[green]✅ Document created successfully![/green]")
            console.print(f"  Document UUID: [cyan]{doc_uuid}[/cyan]")
            console.print(f"  Revision UUID: [cyan]{rev_uuid}[/cyan]")

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Abort()


@app.command("list")
def list_docs(limit: int = typer.Option(20, help="Maximum documents to show")) -> None:
    """List recent documents."""
    try:
        with get_connection() as conn:
            docs = list_documents(conn, limit=limit)

        if not docs:
            console.print("[yellow]No documents found.[/yellow]")
            return

        table = Table(title="Documents")
        table.add_column("Doc ID")
        table.add_column("Title")
        table.add_column("Status")
        table.add_column("Created")

        for doc in docs:
            table.add_row(
                doc["doc_id"],
                doc["title"][:40],
                doc["status"],
                str(doc["created_at"].date()),
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")


@app.command("show")
def show_document(doc_id: str = typer.Argument(..., help="Document ID")) -> None:
    """Show document details."""
    try:
        with get_connection() as conn:
            doc = get_document_by_doc_id(conn, doc_id)

        if not doc:
            console.print(f"[yellow]Document not found: {doc_id}[/yellow]")
            return

        console.print(f"\n[bold]{doc['doc_id']}[/bold] - {doc['title']}")
        console.print(f"  Status: {doc['status']}")
        console.print(f"  UUID: {doc['id']}")
        console.print(f"  Created: {doc['created_at']}")

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")

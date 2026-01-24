"""ke embed - Embedding generation commands."""

import logging
from uuid import UUID

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from apps.ke_db.chunks import list_chunks_for_revision
from apps.ke_db.connection import get_connection
from apps.ke_db.embeddings import get_provider
from apps.ke_db.retrieval import update_chunk_embedding

app = typer.Typer(help="Embedding generation commands")
console = Console()

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@app.command("revision")
def embed_revision(
    revision_id: str = typer.Option(..., "--revision-id", "-r", help="Revision UUID"),
    provider: str = typer.Option("auto", "--provider", "-p", help="Provider: auto, dummy, openai"),
    batch_size: int = typer.Option(50, "--batch-size", "-b", help="Batch size for embedding"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be embedded"),
) -> None:
    """Generate embeddings for chunks in a revision.

    Only fills NULL embeddings (idempotent).
    """
    console.print("\n[bold cyan]🧮 Generate Embeddings[/bold cyan]\n")

    rev_uuid = UUID(revision_id)
    logger.info(f"Starting embedding generation for revision {revision_id}")

    try:
        # Get provider
        embedding_provider = get_provider(provider)
        console.print(f"Provider: [cyan]{type(embedding_provider).__name__}[/cyan]")
        console.print(f"Dimension: [cyan]{embedding_provider.dimension}[/cyan]")

        # Get chunks needing embeddings
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, chunk_no, LEFT(text, 100) AS preview, text
                    FROM evidence.chunk
                    WHERE revision_id = %s AND embedding IS NULL
                    ORDER BY chunk_no
                    """,
                    (rev_uuid,),
                )
                chunks = cur.fetchall()

        if not chunks:
            console.print("[green]✅ All chunks already have embeddings![/green]")
            logger.info("No chunks need embeddings")
            return

        console.print(f"Chunks needing embeddings: [yellow]{len(chunks)}[/yellow]")

        if dry_run:
            console.print("\n[dim]Dry run - no changes made[/dim]")
            for chunk_id, chunk_no, preview, _ in chunks[:10]:
                console.print(f"  • Chunk #{chunk_no}: {preview}...")
            if len(chunks) > 10:
                console.print(f"  ... and {len(chunks) - 10} more")
            return

        # Confirm
        if not typer.confirm(f"\nEmbed {len(chunks)} chunk(s)?", default=True):
            console.print("[yellow]Aborted.[/yellow]")
            raise typer.Abort()

        # Process in batches
        chunk_ids = [row[0] for row in chunks]
        chunk_texts = [row[3] for row in chunks]

        embedded_count = 0
        failed_count = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating embeddings...", total=len(chunks))

            for i in range(0, len(chunks), batch_size):
                batch_ids = chunk_ids[i : i + batch_size]
                batch_texts = chunk_texts[i : i + batch_size]

                logger.info(f"Processing batch {i // batch_size + 1}, size {len(batch_ids)}")

                try:
                    # Generate embeddings
                    embeddings = embedding_provider.embed_texts(batch_texts)

                    # Update database
                    with get_connection() as conn:
                        for chunk_id, embedding in zip(batch_ids, embeddings):
                            try:
                                update_chunk_embedding(conn, chunk_id, embedding)
                                embedded_count += 1
                            except Exception as e:
                                logger.error(f"Failed to update chunk {chunk_id}: {e}")
                                failed_count += 1
                        conn.commit()

                    progress.update(task, advance=len(batch_ids))

                except Exception as e:
                    logger.error(f"Batch failed: {e}")
                    failed_count += len(batch_ids)
                    progress.update(task, advance=len(batch_ids))

        # Summary
        console.print()
        console.print(f"[green]✅ Embedded: {embedded_count}[/green]")
        if failed_count > 0:
            console.print(f"[red]❌ Failed: {failed_count}[/red]")

        logger.info(f"Embedding complete: {embedded_count} success, {failed_count} failed")

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        logger.exception("Embedding failed")
        raise typer.Abort()


@app.command("status")
def embedding_status(
    revision_id: str = typer.Argument(..., help="Revision UUID"),
) -> None:
    """Show embedding status for a revision."""
    rev_uuid = UUID(revision_id)

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        COUNT(*) AS total,
                        COUNT(embedding) AS with_embedding,
                        COUNT(*) - COUNT(embedding) AS without_embedding
                    FROM evidence.chunk
                    WHERE revision_id = %s
                    """,
                    (rev_uuid,),
                )
                total, with_emb, without_emb = cur.fetchone()

        console.print(f"\n[bold]Embedding Status[/bold]\n")
        console.print(f"  Total chunks: {total}")
        console.print(f"  With embeddings: [green]{with_emb}[/green]")
        console.print(f"  Without embeddings: [yellow]{without_emb}[/yellow]")

        if without_emb == 0:
            console.print("\n[green]✅ All chunks have embeddings![/green]")
        else:
            console.print(f"\n💡 Run: ke embed revision -r {revision_id}")

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")

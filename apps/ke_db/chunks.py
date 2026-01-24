"""Chunk CRUD operations."""

from typing import Any
from uuid import UUID

import psycopg


def create_chunk(
    conn: psycopg.Connection,
    *,
    revision_id: UUID,
    chunk_no: int,
    text: str,
    page_start: int | None = None,
    page_end: int | None = None,
    section_path: str | None = None,
    char_start: int | None = None,
    char_end: int | None = None,
    token_count: int | None = None,
    tags: list[str] | None = None,
) -> UUID:
    """Create a new chunk.

    Args:
        conn: Database connection.
        revision_id: Parent revision UUID.
        chunk_no: Chunk number (must be positive, unique per revision).
        text: Chunk text content.
        page_start: Optional starting page.
        page_end: Optional ending page.
        section_path: Optional section path.
        char_start: Optional character start offset.
        char_end: Optional character end offset.
        token_count: Optional token count.
        tags: Optional list of tags.

    Returns:
        UUID of the created chunk.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO evidence.chunk
                (revision_id, chunk_no, text, page_start, page_end,
                 section_path, char_start, char_end, token_count, tags)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                revision_id,
                chunk_no,
                text,
                page_start,
                page_end,
                section_path,
                char_start,
                char_end,
                token_count,
                tags or [],
            ),
        )
        result = cur.fetchone()
        return result[0] if result else None  # type: ignore


def list_chunks_for_revision(
    conn: psycopg.Connection, revision_id: UUID
) -> list[dict[str, Any]]:
    """List chunks for a revision.

    Args:
        conn: Database connection.
        revision_id: Revision UUID.

    Returns:
        List of chunk dicts.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, chunk_no, LEFT(text, 80) AS preview, page_start, created_at
            FROM evidence.chunk
            WHERE revision_id = %s
            ORDER BY chunk_no
            """,
            (revision_id,),
        )
        return [
            {
                "id": row[0],
                "chunk_no": row[1],
                "preview": row[2],
                "page_start": row[3],
                "created_at": row[4],
            }
            for row in cur.fetchall()
        ]


def get_next_chunk_no(conn: psycopg.Connection, revision_id: UUID) -> int:
    """Get the next chunk number for a revision.

    Args:
        conn: Database connection.
        revision_id: Revision UUID.

    Returns:
        Next chunk number.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COALESCE(MAX(chunk_no), 0) + 1
            FROM evidence.chunk
            WHERE revision_id = %s
            """,
            (revision_id,),
        )
        result = cur.fetchone()
        return result[0] if result else 1

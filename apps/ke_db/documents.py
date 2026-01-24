"""Document and revision CRUD operations."""

from datetime import date
from typing import Any
from uuid import UUID

import psycopg


def create_document(
    conn: psycopg.Connection,
    *,
    doc_id: str,
    title: str,
    file_uri: str,
    sha256: str,
    authors: str | None = None,
    publisher_org: str | None = None,
    published_date: date | None = None,
    source_url: str | None = None,
    tags: list[str] | None = None,
) -> UUID:
    """Create a new document.

    Args:
        conn: Database connection.
        doc_id: Human-readable document ID (e.g. DOC-0001).
        title: Document title.
        file_uri: Path to the file.
        sha256: SHA256 hash of the file.
        authors: Optional authors string.
        publisher_org: Optional publisher organization.
        published_date: Optional publication date.
        source_url: Optional source URL.
        tags: Optional list of tags.

    Returns:
        UUID of the created document.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO evidence.document
                (doc_id, title, file_uri, sha256, authors, publisher_org,
                 published_date, source_url, tags)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                doc_id,
                title,
                file_uri,
                sha256,
                authors,
                publisher_org,
                published_date,
                source_url,
                tags or [],
            ),
        )
        result = cur.fetchone()
        return result[0] if result else None  # type: ignore


def create_revision(
    conn: psycopg.Connection,
    *,
    document_id: UUID,
    revision_no: int,
    sha256: str,
    file_uri: str,
    parser_version: str | None = None,
    notes: str | None = None,
) -> UUID:
    """Create a document revision.

    Args:
        conn: Database connection.
        document_id: Parent document UUID.
        revision_no: Revision number (must be positive).
        sha256: SHA256 hash of this revision.
        file_uri: Path to the file for this revision.
        parser_version: Optional parser version.
        notes: Optional notes.

    Returns:
        UUID of the created revision.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO evidence.document_revision
                (document_id, revision_no, sha256, file_uri, parser_version, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (document_id, revision_no, sha256, file_uri, parser_version, notes),
        )
        result = cur.fetchone()
        return result[0] if result else None  # type: ignore


def get_document_by_doc_id(
    conn: psycopg.Connection, doc_id: str
) -> dict[str, Any] | None:
    """Get document by doc_id.

    Args:
        conn: Database connection.
        doc_id: Human-readable document ID.

    Returns:
        Document dict or None if not found.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, doc_id, title, status, created_at
            FROM evidence.document
            WHERE doc_id = %s
            """,
            (doc_id,),
        )
        row = cur.fetchone()
        if row:
            return {
                "id": row[0],
                "doc_id": row[1],
                "title": row[2],
                "status": row[3],
                "created_at": row[4],
            }
        return None


def list_revisions(conn: psycopg.Connection, document_id: UUID) -> list[dict[str, Any]]:
    """List revisions for a document.

    Args:
        conn: Database connection.
        document_id: Document UUID.

    Returns:
        List of revision dicts.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, revision_no, sha256, created_at
            FROM evidence.document_revision
            WHERE document_id = %s
            ORDER BY revision_no DESC
            """,
            (document_id,),
        )
        return [
            {"id": row[0], "revision_no": row[1], "sha256": row[2], "created_at": row[3]}
            for row in cur.fetchall()
        ]


def list_documents(conn: psycopg.Connection, limit: int = 20) -> list[dict[str, Any]]:
    """List recent documents.

    Args:
        conn: Database connection.
        limit: Maximum number of documents to return.

    Returns:
        List of document dicts.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, doc_id, title, status, created_at
            FROM evidence.document
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (limit,),
        )
        return [
            {
                "id": row[0],
                "doc_id": row[1],
                "title": row[2],
                "status": row[3],
                "created_at": row[4],
            }
            for row in cur.fetchall()
        ]

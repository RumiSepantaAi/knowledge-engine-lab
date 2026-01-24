"""Claim CRUD operations."""

from typing import Any
from uuid import UUID

import psycopg


def create_claim(
    conn: psycopg.Connection,
    *,
    revision_id: UUID,
    claim_text: str,
    claim_type: str = "other",
    confidence: float = 0.70,
    tags: list[str] | None = None,
    structured: dict[str, Any] | None = None,
    created_by: str = "manual",
) -> UUID:
    """Create a new claim.

    Args:
        conn: Database connection.
        revision_id: Parent revision UUID.
        claim_text: The claim text.
        claim_type: Claim type (fact, definition, requirement, etc.).
        confidence: Confidence score (0.0 to 1.0).
        tags: Optional list of tags.
        structured: Optional structured JSON data.
        created_by: Creator identifier.

    Returns:
        UUID of the created claim.
    """
    import json

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO evidence.claim
                (revision_id, claim_text, claim_type, confidence, tags, structured, created_by)
            VALUES (%s, %s, %s::evidence.claim_type, %s, %s, %s::jsonb, %s)
            RETURNING id
            """,
            (
                revision_id,
                claim_text,
                claim_type,
                confidence,
                tags or [],
                json.dumps(structured) if structured else "{}",
                created_by,
            ),
        )
        result = cur.fetchone()
        return result[0] if result else None  # type: ignore


def list_claims_for_revision(
    conn: psycopg.Connection, revision_id: UUID
) -> list[dict[str, Any]]:
    """List claims for a revision.

    Args:
        conn: Database connection.
        revision_id: Revision UUID.

    Returns:
        List of claim dicts.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, claim_type, LEFT(claim_text, 80) AS preview, confidence, created_at
            FROM evidence.claim
            WHERE revision_id = %s
            ORDER BY created_at
            """,
            (revision_id,),
        )
        return [
            {
                "id": row[0],
                "claim_type": row[1],
                "preview": row[2],
                "confidence": row[3],
                "created_at": row[4],
            }
            for row in cur.fetchall()
        ]


def get_claim_by_id(conn: psycopg.Connection, claim_id: UUID) -> dict[str, Any] | None:
    """Get claim by ID.

    Args:
        conn: Database connection.
        claim_id: Claim UUID.

    Returns:
        Claim dict or None.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, revision_id, claim_type, claim_text, confidence, created_at
            FROM evidence.claim
            WHERE id = %s
            """,
            (claim_id,),
        )
        row = cur.fetchone()
        if row:
            return {
                "id": row[0],
                "revision_id": row[1],
                "claim_type": row[2],
                "claim_text": row[3],
                "confidence": row[4],
                "created_at": row[5],
            }
        return None

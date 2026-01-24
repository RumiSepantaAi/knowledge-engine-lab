"""Evidence span CRUD operations."""

from typing import Any
from uuid import UUID

import psycopg


def create_evidence_span(
    conn: psycopg.Connection,
    *,
    claim_id: UUID,
    chunk_id: UUID,
    snippet: str,
    role: str = "supports",
    page_no: int | None = None,
    start_char: int | None = None,
    end_char: int | None = None,
    support_strength: float = 0.80,
) -> UUID:
    """Create an evidence span linking claim to chunk.

    Args:
        conn: Database connection.
        claim_id: Claim UUID.
        chunk_id: Chunk UUID.
        snippet: Evidence snippet text (max 2000 chars).
        role: Evidence role (supports, contradicts, mentions).
        page_no: Optional page number.
        start_char: Optional character start offset.
        end_char: Optional character end offset.
        support_strength: Support strength (0.0 to 1.0).

    Returns:
        UUID of the created evidence span.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO evidence.evidence_span
                (claim_id, chunk_id, snippet, role, page_no, start_char, end_char, support_strength)
            VALUES (%s, %s, %s, %s::evidence.evidence_role, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                claim_id,
                chunk_id,
                snippet[:2000],  # Enforce max length
                role,
                page_no,
                start_char,
                end_char,
                support_strength,
            ),
        )
        result = cur.fetchone()
        return result[0] if result else None  # type: ignore


def list_evidence_for_claim(
    conn: psycopg.Connection, claim_id: UUID
) -> list[dict[str, Any]]:
    """List evidence spans for a claim.

    Args:
        conn: Database connection.
        claim_id: Claim UUID.

    Returns:
        List of evidence span dicts.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, chunk_id, role, LEFT(snippet, 60) AS preview, support_strength, created_at
            FROM evidence.evidence_span
            WHERE claim_id = %s
            ORDER BY created_at
            """,
            (claim_id,),
        )
        return [
            {
                "id": row[0],
                "chunk_id": row[1],
                "role": row[2],
                "preview": row[3],
                "support_strength": row[4],
                "created_at": row[5],
            }
            for row in cur.fetchall()
        ]

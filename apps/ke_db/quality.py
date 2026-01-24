"""Quality gate queries."""

from typing import Any
from uuid import UUID

import psycopg


def get_claims_without_evidence(
    conn: psycopg.Connection, revision_id: UUID
) -> list[dict[str, Any]]:
    """Get claims without evidence for a revision.

    Args:
        conn: Database connection.
        revision_id: Revision UUID.

    Returns:
        List of claim dicts without evidence.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT c.id, c.claim_type, LEFT(c.claim_text, 80) AS preview
            FROM evidence.claim c
            LEFT JOIN evidence.evidence_span es ON c.id = es.claim_id
            WHERE c.revision_id = %s AND es.id IS NULL
            ORDER BY c.created_at
            """,
            (revision_id,),
        )
        return [
            {"id": row[0], "claim_type": row[1], "preview": row[2]}
            for row in cur.fetchall()
        ]


def check_quality_gate(
    conn: psycopg.Connection, revision_id: UUID
) -> dict[str, Any]:
    """Check quality gate for a revision.

    Args:
        conn: Database connection.
        revision_id: Revision UUID.

    Returns:
        Dict with pass/fail status and counts.
    """
    with conn.cursor() as cur:
        # Count total claims
        cur.execute(
            "SELECT COUNT(*) FROM evidence.claim WHERE revision_id = %s",
            (revision_id,),
        )
        total = cur.fetchone()[0]

        # Count claims without evidence (using DISTINCT to handle multiple spans)
        cur.execute(
            """
            SELECT COUNT(DISTINCT c.id)
            FROM evidence.claim c
            LEFT JOIN evidence.evidence_span es ON c.id = es.claim_id
            WHERE c.revision_id = %s AND es.id IS NULL
            """,
            (revision_id,),
        )
        without_evidence = cur.fetchone()[0]

    passed = without_evidence == 0 and total > 0
    return {
        "passed": passed,
        "total_claims": total,
        "claims_without_evidence": without_evidence,
        "claims_with_evidence": total - without_evidence,
    }


def set_document_validated(conn: psycopg.Connection, document_id: UUID) -> bool:
    """Set document status to validated.

    Args:
        conn: Database connection.
        document_id: Document UUID.

    Returns:
        True if updated, False otherwise.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE evidence.document
            SET status = 'validated'
            WHERE id = %s AND status != 'validated'
            """,
            (document_id,),
        )
        return cur.rowcount > 0

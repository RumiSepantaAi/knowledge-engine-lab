"""ke_db - Database access layer for Knowledge Engine.

Provides parameterized queries for CLI/UI/API.
Connection via environment variables.
"""

from apps.ke_db.connection import get_connection, get_connection_string
from apps.ke_db.documents import (
    create_document,
    create_revision,
    get_document_by_doc_id,
    list_revisions,
)
from apps.ke_db.chunks import create_chunk, list_chunks_for_revision
from apps.ke_db.claims import create_claim, list_claims_for_revision
from apps.ke_db.evidence import create_evidence_span, list_evidence_for_claim
from apps.ke_db.quality import check_quality_gate, get_claims_without_evidence
from apps.ke_db.utils import compute_sha256, validate_doc_id

__all__ = [
    "get_connection",
    "get_connection_string",
    "create_document",
    "create_revision",
    "get_document_by_doc_id",
    "list_revisions",
    "create_chunk",
    "list_chunks_for_revision",
    "create_claim",
    "list_claims_for_revision",
    "create_evidence_span",
    "list_evidence_for_claim",
    "check_quality_gate",
    "get_claims_without_evidence",
    "compute_sha256",
    "validate_doc_id",
]

"""Knowledge Engine API - FastAPI Application.

Run with: uvicorn apps.ke_api.main:app --reload
Or via Makefile: make api
"""

from uuid import UUID

from fastapi import FastAPI, HTTPException

from apps.ke_api.models import (
    ChunkCreate,
    ChunkResponse,
    ClaimCreate,
    ClaimResponse,
    DocumentCreate,
    DocumentResponse,
    EvidenceCreate,
    EvidenceResponse,
    HealthResponse,
    QualityGateResponse,
)
from apps.ke_db.chunks import create_chunk
from apps.ke_db.claims import create_claim
from apps.ke_db.connection import get_connection
from apps.ke_db.documents import create_document, create_revision
from apps.ke_db.evidence import create_evidence_span
from apps.ke_db.quality import check_quality_gate

app = FastAPI(
    title="Knowledge Engine API",
    description="REST API for managing knowledge graphs and evidence.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.on_event("startup")
def check_schema_on_startup() -> None:
    """Check if database schema is initialized on startup."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = 'evidence' AND table_name = 'document'
                    )
                """)
                schema_exists = cur.fetchone()[0]
                if not schema_exists:
                    print("⚠️  WARNING: Database schema not initialized.")
                    print("   Run: make db-migrate")
    except Exception as e:
        print(f"⚠️  WARNING: Could not connect to database: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/healthz", response_model=HealthResponse, tags=["System"])
def health_check() -> HealthResponse:
    """Check API and database health."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)[:50]}"

    return HealthResponse(
        status="ok" if db_status == "connected" else "degraded",
        database=db_status,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Documents
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/docs", response_model=DocumentResponse, tags=["Documents"], status_code=201)
def create_doc(doc: DocumentCreate) -> DocumentResponse:
    """Create a new document with initial revision."""
    try:
        with get_connection() as conn:
            # Create document
            doc_uuid = create_document(
                conn,
                doc_id=doc.doc_id,
                title=doc.title,
                file_uri=doc.file_uri,
                sha256=doc.sha256,
                authors=doc.authors,
                publisher_org=doc.publisher_org,
                published_date=doc.published_date,
                source_url=doc.source_url,
                tags=doc.tags,
            )

            # Create initial revision
            rev_uuid = create_revision(
                conn,
                document_id=doc_uuid,
                revision_no=1,
                sha256=doc.sha256,
                file_uri=doc.file_uri,
                parser_version="api/v1",
                notes="Created via API",
            )

            conn.commit()

            return DocumentResponse(
                id=doc_uuid,
                doc_id=doc.doc_id,
                title=doc.title,
                status="inbox",
                revision_id=rev_uuid,
            )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Chunks
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/chunks", response_model=ChunkResponse, tags=["Chunks"], status_code=201)
def create_chunk_endpoint(chunk: ChunkCreate) -> ChunkResponse:
    """Create a new chunk."""
    try:
        with get_connection() as conn:
            chunk_uuid = create_chunk(
                conn,
                revision_id=chunk.revision_id,
                chunk_no=chunk.chunk_no,
                text=chunk.text,
                page_start=chunk.page_start,
                page_end=chunk.page_end,
                section_path=chunk.section_path,
                char_start=chunk.char_start,
                char_end=chunk.char_end,
                token_count=chunk.token_count,
                tags=chunk.tags,
            )
            conn.commit()

            return ChunkResponse(
                id=chunk_uuid,
                chunk_no=chunk.chunk_no,
                revision_id=chunk.revision_id,
            )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Claims
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/claims", response_model=ClaimResponse, tags=["Claims"], status_code=201)
def create_claim_endpoint(claim: ClaimCreate) -> ClaimResponse:
    """Create a new claim."""
    try:
        with get_connection() as conn:
            claim_uuid = create_claim(
                conn,
                revision_id=claim.revision_id,
                claim_text=claim.claim_text,
                claim_type=claim.claim_type,
                confidence=claim.confidence,
                tags=claim.tags,
                structured=claim.structured,
                created_by=claim.created_by,
            )
            conn.commit()

            return ClaimResponse(
                id=claim_uuid,
                claim_type=claim.claim_type,
                revision_id=claim.revision_id,
            )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Evidence
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/evidence", response_model=EvidenceResponse, tags=["Evidence"], status_code=201)
def create_evidence_endpoint(evidence: EvidenceCreate) -> EvidenceResponse:
    """Create a new evidence span linking claim to chunk."""
    try:
        with get_connection() as conn:
            span_uuid = create_evidence_span(
                conn,
                claim_id=evidence.claim_id,
                chunk_id=evidence.chunk_id,
                snippet=evidence.snippet,
                role=evidence.role,
                page_no=evidence.page_no,
                start_char=evidence.start_char,
                end_char=evidence.end_char,
                support_strength=evidence.support_strength,
            )
            conn.commit()

            return EvidenceResponse(
                id=span_uuid,
                claim_id=evidence.claim_id,
                chunk_id=evidence.chunk_id,
                role=evidence.role,
            )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Quality Gate
# ─────────────────────────────────────────────────────────────────────────────
@app.get(
    "/quality/{revision_id}",
    response_model=QualityGateResponse,
    tags=["Quality"],
)
def get_quality_gate(revision_id: UUID) -> QualityGateResponse:
    """Check quality gate for a revision."""
    try:
        with get_connection() as conn:
            result = check_quality_gate(conn, revision_id)

            return QualityGateResponse(
                revision_id=revision_id,
                passed=result["passed"],
                total_claims=result["total_claims"],
                claims_with_evidence=result["claims_with_evidence"],
                claims_without_evidence=result["claims_without_evidence"],
            )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

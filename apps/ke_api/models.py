"""Pydantic models for API validation."""

import re
from datetime import date
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────────────────────────────────────────
# Document Models
# ─────────────────────────────────────────────────────────────────────────────
class DocumentCreate(BaseModel):
    """Request model for creating a document."""

    doc_id: str = Field(..., description="Document ID (format: XXX-NNNN)")
    title: str = Field(..., min_length=1, max_length=500)
    file_uri: str = Field(..., description="Path to the document file")
    sha256: str = Field(..., min_length=64, max_length=64)
    authors: str | None = None
    publisher_org: str | None = None
    published_date: date | None = None
    source_url: str | None = None
    tags: list[str] = Field(default_factory=list)

    @field_validator("doc_id")
    @classmethod
    def validate_doc_id(cls, v: str) -> str:
        if not re.match(r"^[A-Z]{3}-[0-9]{4,}$", v):
            raise ValueError("doc_id must match format XXX-NNNN (e.g. DOC-0001)")
        return v

    @field_validator("sha256")
    @classmethod
    def validate_sha256(cls, v: str) -> str:
        if not re.match(r"^[a-f0-9]{64}$", v):
            raise ValueError("sha256 must be 64 hex characters")
        return v.lower()


class DocumentResponse(BaseModel):
    """Response model for document."""

    id: UUID
    doc_id: str
    title: str
    status: str
    revision_id: UUID


# ─────────────────────────────────────────────────────────────────────────────
# Chunk Models
# ─────────────────────────────────────────────────────────────────────────────
class ChunkCreate(BaseModel):
    """Request model for creating a chunk."""

    revision_id: UUID
    chunk_no: int = Field(..., gt=0)
    text: str = Field(..., min_length=1)
    page_start: int | None = Field(None, ge=1)
    page_end: int | None = Field(None, ge=1)
    section_path: str | None = None
    char_start: int | None = Field(None, ge=0)
    char_end: int | None = Field(None, ge=0)
    token_count: int | None = Field(None, ge=0)
    tags: list[str] = Field(default_factory=list)


class ChunkResponse(BaseModel):
    """Response model for chunk."""

    id: UUID
    chunk_no: int
    revision_id: UUID


# ─────────────────────────────────────────────────────────────────────────────
# Claim Models
# ─────────────────────────────────────────────────────────────────────────────
CLAIM_TYPES = ["fact", "definition", "requirement", "recommendation", "metric", "other"]


class ClaimCreate(BaseModel):
    """Request model for creating a claim."""

    revision_id: UUID
    claim_text: str = Field(..., min_length=1)
    claim_type: str = Field(default="other")
    confidence: float = Field(default=0.70, ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)
    structured: dict[str, Any] = Field(default_factory=dict)
    created_by: str = Field(default="api")

    @field_validator("claim_type")
    @classmethod
    def validate_claim_type(cls, v: str) -> str:
        if v not in CLAIM_TYPES:
            raise ValueError(f"claim_type must be one of: {', '.join(CLAIM_TYPES)}")
        return v


class ClaimResponse(BaseModel):
    """Response model for claim."""

    id: UUID
    claim_type: str
    revision_id: UUID


# ─────────────────────────────────────────────────────────────────────────────
# Evidence Models
# ─────────────────────────────────────────────────────────────────────────────
EVIDENCE_ROLES = ["supports", "contradicts", "mentions"]


class EvidenceCreate(BaseModel):
    """Request model for creating an evidence span."""

    claim_id: UUID
    chunk_id: UUID
    snippet: str = Field(..., min_length=1, max_length=2000)
    role: str = Field(default="supports")
    page_no: int | None = Field(None, ge=1)
    start_char: int | None = Field(None, ge=0)
    end_char: int | None = Field(None, ge=0)
    support_strength: float = Field(default=0.80, ge=0.0, le=1.0)

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in EVIDENCE_ROLES:
            raise ValueError(f"role must be one of: {', '.join(EVIDENCE_ROLES)}")
        return v


class EvidenceResponse(BaseModel):
    """Response model for evidence span."""

    id: UUID
    claim_id: UUID
    chunk_id: UUID
    role: str


# ─────────────────────────────────────────────────────────────────────────────
# Quality Gate Models
# ─────────────────────────────────────────────────────────────────────────────
class QualityGateResponse(BaseModel):
    """Response model for quality gate result."""

    revision_id: UUID
    passed: bool
    total_claims: int
    claims_with_evidence: int
    claims_without_evidence: int


# ─────────────────────────────────────────────────────────────────────────────
# Health Models
# ─────────────────────────────────────────────────────────────────────────────
class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str
    database: str
    version: str = "0.1.0"

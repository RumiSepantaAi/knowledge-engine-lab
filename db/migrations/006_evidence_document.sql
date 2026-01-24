-- ─────────────────────────────────────────────────────────────────────────────
-- Migration: 006_evidence_document.sql
-- Description: Create evidence.document table for source documents
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE evidence.document (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id          TEXT NOT NULL UNIQUE,
    title           TEXT NOT NULL,
    authors         TEXT,
    publisher_org   TEXT,
    published_date  DATE,
    source_url      TEXT,
    retrieved_at    TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    file_uri        TEXT NOT NULL,
    sha256          TEXT NOT NULL,
    mime_type       TEXT NOT NULL DEFAULT 'application/pdf',
    license_rights  TEXT,
    access_class    TEXT NOT NULL DEFAULT 'public',
    version_label   TEXT NOT NULL DEFAULT 'v1',
    tags            TEXT[] NOT NULL DEFAULT '{}',
    status          evidence.doc_status NOT NULL DEFAULT 'inbox',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Validate doc_id format: 3 uppercase letters, dash, 4+ digits
    CONSTRAINT chk_document_doc_id_format
        CHECK (doc_id ~ '^[A-Z]{3}-[0-9]{4,}$')
);

-- Indexes
CREATE INDEX idx_document_status ON evidence.document(status);
CREATE INDEX idx_document_tags ON evidence.document USING gin(tags);
CREATE INDEX idx_document_published_date ON evidence.document(published_date);

-- Updated_at trigger
CREATE TRIGGER trg_document_updated_at
    BEFORE UPDATE ON evidence.document
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();

-- Comments
COMMENT ON TABLE evidence.document IS
    'Source documents ingested into the evidence graph';
COMMENT ON COLUMN evidence.document.doc_id IS
    'Human-readable document ID, format: XXX-NNNN (e.g. RFC-8446, ISO-27001)';
COMMENT ON COLUMN evidence.document.sha256 IS
    'SHA-256 hash of the original file for integrity verification';
COMMENT ON COLUMN evidence.document.access_class IS
    'Access classification: public, internal, confidential, restricted';

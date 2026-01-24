-- ─────────────────────────────────────────────────────────────────────────────
-- Migration: 007_evidence_revision.sql
-- Description: Create evidence.document_revision table for document versions
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE evidence.document_revision (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES evidence.document(id) ON DELETE CASCADE,
    revision_no     INT NOT NULL,
    sha256          TEXT NOT NULL,
    file_uri        TEXT NOT NULL,
    parser_version  TEXT,
    extracted_at    TIMESTAMPTZ,
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Uniqueness constraints
    CONSTRAINT uq_revision_document_no UNIQUE (document_id, revision_no),
    CONSTRAINT uq_revision_document_sha UNIQUE (document_id, sha256),

    -- Ensure revision_no is positive
    CONSTRAINT chk_revision_no_positive CHECK (revision_no > 0)
);

-- Index for efficient lookup by document
CREATE INDEX idx_document_revision_doc_rev
    ON evidence.document_revision(document_id, revision_no DESC);

-- Comments
COMMENT ON TABLE evidence.document_revision IS
    'Versioned snapshots of documents for tracking re-parses and updates';
COMMENT ON COLUMN evidence.document_revision.parser_version IS
    'Version of the parser/extractor used for this revision';
COMMENT ON COLUMN evidence.document_revision.extracted_at IS
    'When the text extraction was completed';

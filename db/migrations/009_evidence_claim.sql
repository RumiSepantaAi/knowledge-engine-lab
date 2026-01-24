-- ─────────────────────────────────────────────────────────────────────────────
-- Migration: 009_evidence_claim.sql
-- Description: Create evidence.claim table for extracted claims
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE evidence.claim (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    revision_id     UUID NOT NULL REFERENCES evidence.document_revision(id) ON DELETE CASCADE,
    claim_type      evidence.claim_type NOT NULL DEFAULT 'other',
    claim_text      TEXT NOT NULL,
    confidence      NUMERIC(3,2) NOT NULL DEFAULT 0.70,
    tags            TEXT[] NOT NULL DEFAULT '{}',
    structured      JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by      TEXT NOT NULL DEFAULT 'manual',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Validate confidence is between 0 and 1
    CONSTRAINT chk_claim_confidence_range CHECK (confidence >= 0 AND confidence <= 1)
);

-- Indexes
CREATE INDEX idx_claim_revision ON evidence.claim(revision_id);
CREATE INDEX idx_claim_type ON evidence.claim(claim_type);
CREATE INDEX idx_claim_tags ON evidence.claim USING gin(tags);
CREATE INDEX idx_claim_structured ON evidence.claim USING gin(structured);

-- Updated_at trigger
CREATE TRIGGER trg_claim_updated_at
    BEFORE UPDATE ON evidence.claim
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();

-- Comments
COMMENT ON TABLE evidence.claim IS
    'Claims extracted from documents that require evidential support';
COMMENT ON COLUMN evidence.claim.confidence IS
    'Extraction confidence score (0.0 to 1.0)';
COMMENT ON COLUMN evidence.claim.structured IS
    'Structured data for claim-type-specific fields (e.g., metric value, risk category)';
COMMENT ON COLUMN evidence.claim.created_by IS
    'Creator identifier: "manual", "gpt-4", "claude-3", etc.';

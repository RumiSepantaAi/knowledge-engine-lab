-- ─────────────────────────────────────────────────────────────────────────────
-- Migration: 010_evidence_span.sql
-- Description: Create evidence.evidence_span table linking claims to chunks
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE evidence.evidence_span (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id            UUID NOT NULL REFERENCES evidence.claim(id) ON DELETE CASCADE,
    chunk_id            UUID NOT NULL REFERENCES evidence.chunk(id) ON DELETE RESTRICT,
    role                evidence.evidence_role NOT NULL DEFAULT 'supports',
    page_no             INT,
    start_char          INT,
    end_char            INT,
    snippet             TEXT NOT NULL,
    quote_sha256        TEXT,
    support_strength    NUMERIC(3,2) NOT NULL DEFAULT 0.80,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Validate char range
    CONSTRAINT chk_span_char_range CHECK (
        (start_char IS NULL AND end_char IS NULL) OR
        (start_char IS NOT NULL AND end_char IS NOT NULL AND start_char <= end_char)
    ),

    -- Validate support_strength is between 0 and 1
    CONSTRAINT chk_span_strength_range CHECK (support_strength >= 0 AND support_strength <= 1),

    -- Validate snippet is not too long (summary, not full text)
    CONSTRAINT chk_span_snippet_length CHECK (length(snippet) <= 2000)
);

-- Indexes for efficient lookups
CREATE INDEX idx_evidence_span_claim ON evidence.evidence_span(claim_id);
CREATE INDEX idx_evidence_span_chunk ON evidence.evidence_span(chunk_id);
CREATE INDEX idx_evidence_span_role ON evidence.evidence_span(role);

-- Comments
COMMENT ON TABLE evidence.evidence_span IS
    'Links claims to their supporting/contradicting evidence in document chunks';
COMMENT ON COLUMN evidence.evidence_span.snippet IS
    'Short excerpt (max 2000 chars) showing the evidence text';
COMMENT ON COLUMN evidence.evidence_span.quote_sha256 IS
    'Hash of exact quote for deduplication and verification';
COMMENT ON COLUMN evidence.evidence_span.support_strength IS
    'How strongly this evidence supports/contradicts the claim (0.0 to 1.0)';

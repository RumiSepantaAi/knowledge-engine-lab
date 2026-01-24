-- ─────────────────────────────────────────────────────────────────────────────
-- Migration: 005_evidence_enums.sql
-- Description: Create enum types for the evidence schema
-- ─────────────────────────────────────────────────────────────────────────────

-- Document processing status
CREATE TYPE evidence.doc_status AS ENUM (
    'inbox',        -- Newly ingested, not yet processed
    'annotated',    -- Chunked and embeddings generated
    'claims_done',  -- Claims extracted
    'validated',    -- All claims have supporting evidence
    'deprecated'    -- No longer active
);

-- Types of claims that can be extracted
CREATE TYPE evidence.claim_type AS ENUM (
    'definition',       -- Defines a term or concept
    'metric',           -- Quantitative measurement or KPI
    'method',           -- Describes a process or methodology
    'recommendation',   -- Suggests an action or best practice
    'risk',             -- Identifies a risk or warning
    'observation',      -- Factual observation
    'other'             -- Uncategorized
);

-- Relationship between evidence spans and claims
CREATE TYPE evidence.evidence_role AS ENUM (
    'supports',     -- Evidence supports the claim
    'contradicts',  -- Evidence contradicts the claim
    'mentions'      -- Evidence mentions without supporting/contradicting
);

-- Comments
COMMENT ON TYPE evidence.doc_status IS
    'Processing status lifecycle for documents';
COMMENT ON TYPE evidence.claim_type IS
    'Classification of extracted claims';
COMMENT ON TYPE evidence.evidence_role IS
    'Relationship between evidence span and its linked claim';
</Parameter>
<parameter name="Complexity">3

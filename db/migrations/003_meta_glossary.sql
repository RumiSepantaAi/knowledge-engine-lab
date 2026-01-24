-- ─────────────────────────────────────────────────────────────────────────────
-- Migration: 003_meta_glossary.sql
-- Description: Create meta.glossary_term table for term definitions
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE meta.glossary_term (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    term                TEXT NOT NULL UNIQUE,
    definition          TEXT NOT NULL,
    taxonomy_node_id    UUID REFERENCES meta.taxonomy_node(id) ON DELETE SET NULL,
    tags                TEXT[] NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_glossary_term_taxonomy_node ON meta.glossary_term(taxonomy_node_id);
CREATE INDEX idx_glossary_term_tags ON meta.glossary_term USING gin(tags);

-- Updated_at trigger
CREATE TRIGGER trg_glossary_term_updated_at
    BEFORE UPDATE ON meta.glossary_term
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();

-- Comments
COMMENT ON TABLE meta.glossary_term IS
    'Glossary of terms with definitions, linked to taxonomy nodes';
COMMENT ON COLUMN meta.glossary_term.tags IS
    'Array of tags for categorization and filtering';

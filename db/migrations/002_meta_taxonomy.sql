-- ─────────────────────────────────────────────────────────────────────────────
-- Migration: 002_meta_taxonomy.sql
-- Description: Create meta.taxonomy_node table for hierarchical taxonomy
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE meta.taxonomy_node (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id       UUID REFERENCES meta.taxonomy_node(id) ON DELETE SET NULL,
    name            TEXT NOT NULL,
    level           SMALLINT NOT NULL CHECK (level BETWEEN 1 AND 4),
    description     TEXT,
    path            TEXT NOT NULL UNIQUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Uniqueness constraint: no duplicate names under the same parent
    CONSTRAINT uq_taxonomy_parent_name UNIQUE (parent_id, name)
);

-- Indexes for efficient lookups
CREATE INDEX idx_taxonomy_node_parent_id ON meta.taxonomy_node(parent_id);
CREATE INDEX idx_taxonomy_node_level ON meta.taxonomy_node(level);
CREATE INDEX idx_taxonomy_node_path_pattern ON meta.taxonomy_node USING btree (path text_pattern_ops);

-- Updated_at trigger
CREATE TRIGGER trg_taxonomy_node_updated_at
    BEFORE UPDATE ON meta.taxonomy_node
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();

-- Comments
COMMENT ON TABLE meta.taxonomy_node IS
    'Hierarchical taxonomy nodes (Level 1-4) for organizing knowledge domains';
COMMENT ON COLUMN meta.taxonomy_node.path IS
    'Materialized path, e.g. "AI > Machine Learning > Supervised"';
COMMENT ON COLUMN meta.taxonomy_node.level IS
    '1=Domain, 2=Category, 3=Subcategory, 4=Term';

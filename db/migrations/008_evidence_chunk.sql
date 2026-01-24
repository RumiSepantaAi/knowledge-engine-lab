-- ─────────────────────────────────────────────────────────────────────────────
-- Migration: 008_evidence_chunk.sql
-- Description: Create evidence.chunk table for document text chunks
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE evidence.chunk (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    revision_id     UUID NOT NULL REFERENCES evidence.document_revision(id) ON DELETE CASCADE,
    chunk_no        INT NOT NULL,
    page_start      INT,
    page_end        INT,
    section_path    TEXT,
    char_start      INT,
    char_end        INT,
    text            TEXT NOT NULL,
    token_count     INT,
    tags            TEXT[] NOT NULL DEFAULT '{}',
    embedding       vector(1536),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Uniqueness: one chunk_no per revision
    CONSTRAINT uq_chunk_revision_no UNIQUE (revision_id, chunk_no),

    -- Validate chunk_no is positive
    CONSTRAINT chk_chunk_no_positive CHECK (chunk_no > 0),

    -- Validate page range
    CONSTRAINT chk_chunk_page_range CHECK (
        (page_start IS NULL AND page_end IS NULL) OR
        (page_start IS NOT NULL AND page_end IS NOT NULL AND page_start <= page_end)
    ),

    -- Validate char range
    CONSTRAINT chk_chunk_char_range CHECK (
        (char_start IS NULL AND char_end IS NULL) OR
        (char_start IS NOT NULL AND char_end IS NOT NULL AND char_start <= char_end)
    )
);

-- Indexes
CREATE INDEX idx_chunk_revision_no ON evidence.chunk(revision_id, chunk_no);
CREATE INDEX idx_chunk_tags ON evidence.chunk USING gin(tags);
CREATE INDEX idx_chunk_text_search ON evidence.chunk USING gin(to_tsvector('simple', text));

-- ─────────────────────────────────────────────────────────────────────────────
-- NOTE: Vector index for similarity search
-- Uncomment when you have enough data (>1000 chunks) and need fast ANN search
-- ─────────────────────────────────────────────────────────────────────────────
-- CREATE INDEX idx_chunk_embedding_hnsw ON evidence.chunk
--     USING hnsw (embedding vector_cosine_ops)
--     WITH (m = 16, ef_construction = 64);

-- Comments
COMMENT ON TABLE evidence.chunk IS
    'Text chunks extracted from document revisions with optional embeddings';
COMMENT ON COLUMN evidence.chunk.section_path IS
    'Hierarchical section path, e.g. "Chapter 1 > Introduction > Background"';
COMMENT ON COLUMN evidence.chunk.embedding IS
    'Vector embedding for semantic search (1536-dim for OpenAI ada-002)';
COMMENT ON COLUMN evidence.chunk.token_count IS
    'Approximate token count for context window management';

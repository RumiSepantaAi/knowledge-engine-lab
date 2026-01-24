-- ─────────────────────────────────────────────────────────────────────────────
-- Migration: 012_vector_ann_index.sql
-- Description: Create HNSW index for vector similarity search
-- ─────────────────────────────────────────────────────────────────────────────
-- ke:no_tx
--
-- NOTE: This creates an HNSW index for fast approximate nearest neighbor (ANN)
-- search on chunk embeddings. The index is created CONCURRENTLY to avoid
-- blocking writes during index creation.
--
-- WHEN TO ENABLE:
-- - You have >1000 chunks with embeddings
-- - You need fast vector similarity search (<100ms)
-- - You're okay with approximate (not exact) results
--
-- HOW TO ENABLE:
-- 1. Uncomment the CREATE INDEX statement below
-- 2. Run: make db-migrate
-- 3. Monitor: SELECT * FROM pg_stat_progress_create_index;
--
-- INDEX PARAMETERS:
-- - m = 16: Maximum connections per layer (higher = better recall, more memory)
-- - ef_construction = 64: Search width during build (higher = better recall, slower build)
--
-- For production tuning, see: https://github.com/pgvector/pgvector#indexing
-- ─────────────────────────────────────────────────────────────────────────────

-- Uncomment when ready to enable ANN search:

-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chunk_embedding_hnsw
--     ON evidence.chunk USING hnsw (embedding vector_cosine_ops)
--     WITH (m = 16, ef_construction = 64);

-- Optional: Set default search parameters for queries
-- SET hnsw.ef_search = 40;  -- Higher = better recall, slower search

-- Placeholder to make migration valid (does nothing)
SELECT 'ANN index migration placeholder - uncomment to enable' AS status;

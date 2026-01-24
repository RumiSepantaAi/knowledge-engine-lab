-- ─────────────────────────────────────────────────────────────────────────────
-- Migration: 000_schema_migrations.sql
-- Description: Create migration tracking table with drift detection
-- ─────────────────────────────────────────────────────────────────────────────

-- Migration tracking table with sha256 for drift detection
CREATE TABLE IF NOT EXISTS public.schema_migrations (
    filename        TEXT PRIMARY KEY,
    content_sha256  TEXT,
    applied_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Add sha256 column if table already exists (idempotent upgrade)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'schema_migrations'
        AND column_name = 'content_sha256'
    ) THEN
        ALTER TABLE public.schema_migrations ADD COLUMN content_sha256 TEXT;
    END IF;
END $$;

COMMENT ON TABLE public.schema_migrations IS
    'Tracks applied database migrations with content hash for drift detection';

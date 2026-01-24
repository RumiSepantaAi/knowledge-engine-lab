-- ─────────────────────────────────────────────────────────────────────────────
-- Migration: 001_extensions_and_helpers.sql
-- Description: Enable required extensions and create shared helper functions
-- ─────────────────────────────────────────────────────────────────────────────

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ─────────────────────────────────────────────────────────────────────────────
-- Shared helper function: set_updated_at()
-- Automatically updates the updated_at column on row modification
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION public.set_updated_at() IS
    'Trigger function to auto-update updated_at timestamp on row modification';

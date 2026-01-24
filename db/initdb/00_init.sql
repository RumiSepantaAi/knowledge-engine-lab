-- ─────────────────────────────────────────────────────────────────────────────
-- Knowledge Engine - Database Initialization
-- ─────────────────────────────────────────────────────────────────────────────

-- Enable pgvector extension for embedding storage
CREATE EXTENSION IF NOT EXISTS vector;

-- Create schemas for logical separation
CREATE SCHEMA IF NOT EXISTS meta;
CREATE SCHEMA IF NOT EXISTS evidence;

-- Grant usage on schemas
GRANT USAGE ON SCHEMA meta TO PUBLIC;
GRANT USAGE ON SCHEMA evidence TO PUBLIC;

-- ─────────────────────────────────────────────────────────────────────────────
-- Placeholder comment: Full table definitions will be added in migrations
-- ─────────────────────────────────────────────────────────────────────────────

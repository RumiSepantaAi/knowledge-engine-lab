-- ─────────────────────────────────────────────────────────────────────────────
-- Migration: 013_db_roles.sql
-- Description: Create application roles with least privilege
-- ─────────────────────────────────────────────────────────────────────────────
-- ke:no_tx
--
-- This migration creates:
-- - ke_app: Read/write role for application use
-- - ke_ro: Read-only role for analytics/reporting
--
-- The default ke_user (admin) should only be used for migrations.
-- ─────────────────────────────────────────────────────────────────────────────

-- Create roles if they don't exist (idempotent)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'ke_app') THEN
        CREATE ROLE ke_app LOGIN PASSWORD 'changeme_app';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'ke_ro') THEN
        CREATE ROLE ke_ro LOGIN PASSWORD 'changeme_ro';
    END IF;
END
$$;

-- Grant schema usage
GRANT USAGE ON SCHEMA public TO ke_app, ke_ro;
GRANT USAGE ON SCHEMA meta TO ke_app, ke_ro;
GRANT USAGE ON SCHEMA evidence TO ke_app, ke_ro;

-- ─────────────────────────────────────────────────────────────────────────────
-- ke_app: Read/Write (DML only, no DDL)
-- ─────────────────────────────────────────────────────────────────────────────
-- Public schema
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ke_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ke_app;

-- Meta schema
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA meta TO ke_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA meta TO ke_app;

-- Evidence schema
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA evidence TO ke_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA evidence TO ke_app;

-- Default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ke_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA meta GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ke_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA evidence GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ke_app;

-- ─────────────────────────────────────────────────────────────────────────────
-- ke_ro: Read-Only
-- ─────────────────────────────────────────────────────────────────────────────
-- Public schema
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ke_ro;

-- Meta schema
GRANT SELECT ON ALL TABLES IN SCHEMA meta TO ke_ro;

-- Evidence schema
GRANT SELECT ON ALL TABLES IN SCHEMA evidence TO ke_ro;

-- Default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO ke_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA meta GRANT SELECT ON TABLES TO ke_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA evidence GRANT SELECT ON TABLES TO ke_ro;

-- Confirm
SELECT 'Roles ke_app and ke_ro created/updated' AS status;

-- ─────────────────────────────────────────────────────────────────────────────
-- Migration: 004_meta_controls.sql
-- Description: Create meta.control table for governance controls
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE meta.control (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code            TEXT NOT NULL UNIQUE,
    title           TEXT NOT NULL,
    description     TEXT NOT NULL,
    category        TEXT,
    severity        SMALLINT NOT NULL DEFAULT 3 CHECK (severity BETWEEN 1 AND 5),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_control_category ON meta.control(category);
CREATE INDEX idx_control_severity ON meta.control(severity);

-- Updated_at trigger
CREATE TRIGGER trg_control_updated_at
    BEFORE UPDATE ON meta.control
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();

-- Comments
COMMENT ON TABLE meta.control IS
    'Governance controls with severity levels (1=Info, 5=Critical)';
COMMENT ON COLUMN meta.control.code IS
    'Unique control identifier, e.g. CTRL-001';
COMMENT ON COLUMN meta.control.severity IS
    '1=Informational, 2=Low, 3=Medium, 4=High, 5=Critical';

#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Create Database Roles
# ─────────────────────────────────────────────────────────────────────────────
# Creates ke_app (RW) and ke_ro (read-only) roles with least privilege.
# Run this after initial setup or use migration 013_db_roles.sql.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

POSTGRES_USER="${POSTGRES_USER:-ke_user}"
POSTGRES_DB="${POSTGRES_DB:-knowledge_engine}"

# Passwords for new roles (override via environment)
KE_APP_PASSWORD="${KE_APP_PASSWORD:-changeme_app}"
KE_RO_PASSWORD="${KE_RO_PASSWORD:-changeme_ro}"

echo "🔐 Creating database roles..."

docker compose -f "${PROJECT_ROOT}/db/docker-compose.yml" exec -T postgres psql \
    -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" <<EOF

-- Create roles if they don't exist
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'ke_app') THEN
        CREATE ROLE ke_app LOGIN PASSWORD '${KE_APP_PASSWORD}';
        RAISE NOTICE 'Created role: ke_app';
    ELSE
        ALTER ROLE ke_app PASSWORD '${KE_APP_PASSWORD}';
        RAISE NOTICE 'Updated password for: ke_app';
    END IF;
    
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'ke_ro') THEN
        CREATE ROLE ke_ro LOGIN PASSWORD '${KE_RO_PASSWORD}';
        RAISE NOTICE 'Created role: ke_ro';
    ELSE
        ALTER ROLE ke_ro PASSWORD '${KE_RO_PASSWORD}';
        RAISE NOTICE 'Updated password for: ke_ro';
    END IF;
END
\$\$;

-- Grant schema usage
GRANT USAGE ON SCHEMA public, meta, evidence TO ke_app, ke_ro;

-- ke_app: Read/Write
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ke_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA meta TO ke_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA evidence TO ke_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ke_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA meta TO ke_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA evidence TO ke_app;

-- ke_ro: Read-Only
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ke_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA meta TO ke_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA evidence TO ke_ro;

SELECT 'Roles created successfully' AS status;
EOF

echo "✅ Roles created: ke_app (RW), ke_ro (read-only)"
echo ""
echo "Connection strings:"
echo "  ke_app: postgresql://ke_app:${KE_APP_PASSWORD}@localhost:5432/${POSTGRES_DB}"
echo "  ke_ro:  postgresql://ke_ro:${KE_RO_PASSWORD}@localhost:5432/${POSTGRES_DB}"

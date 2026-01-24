#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Verify Database Permissions
# ─────────────────────────────────────────────────────────────────────────────
# Checks that ke_app and ke_ro have expected permissions.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

POSTGRES_USER="${POSTGRES_USER:-ke_user}"
POSTGRES_DB="${POSTGRES_DB:-knowledge_engine}"

echo "🔍 Verifying database permissions..."
echo ""

# Check roles exist
echo "Checking roles..."
docker compose -f "${PROJECT_ROOT}/db/docker-compose.yml" exec -T postgres psql \
    -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c \
    "SELECT rolname, rolcanlogin FROM pg_roles WHERE rolname IN ('ke_app', 'ke_ro')"

echo ""
echo "Checking ke_app permissions on evidence.document..."
docker compose -f "${PROJECT_ROOT}/db/docker-compose.yml" exec -T postgres psql \
    -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c \
    "SELECT grantee, privilege_type FROM information_schema.table_privileges 
     WHERE table_schema = 'evidence' AND table_name = 'document' AND grantee = 'ke_app'"

echo ""
echo "Checking ke_ro permissions on evidence.document..."
docker compose -f "${PROJECT_ROOT}/db/docker-compose.yml" exec -T postgres psql \
    -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c \
    "SELECT grantee, privilege_type FROM information_schema.table_privileges 
     WHERE table_schema = 'evidence' AND table_name = 'document' AND grantee = 'ke_ro'"

echo ""
echo "✅ Permission check complete."
echo ""
echo "Expected:"
echo "  ke_app: SELECT, INSERT, UPDATE, DELETE"
echo "  ke_ro:  SELECT only"

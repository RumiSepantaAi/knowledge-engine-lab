#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Restore Database (Local-First)
# ─────────────────────────────────────────────────────────────────────────────
# Usage: ./db/scripts/db_restore.sh <backup_file>

set -euo pipefail

if [ -z "${1:-}" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

backup_file="$1"

if [ ! -f "${backup_file}" ]; then
    echo "❌ Backup file not found: ${backup_file}"
    exit 1
fi

echo "⚠️  WARNING: This will overwrite the current database!"
read -p "Are you sure? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo "📦 Restoring database from ${backup_file}..."

# Use psql to restore (since backup is plain SQL structure+data)
# We pipe the unzipped content into psql inside container
gunzip -c "${backup_file}" | \
    docker compose -f db/docker-compose.yml exec -T postgres \
    psql -U ke_user -d knowledge_engine

echo "✅ Restore complete."

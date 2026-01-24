#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Backup Database (Local-First)
# ─────────────────────────────────────────────────────────────────────────────
# Usage: ./db/scripts/db_backup.sh [output_file]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BACKUP_DIR="${PROJECT_ROOT}/backups"

timestamp=$(date +%Y%m%d_%H%M%S)
output_file="${1:-${BACKUP_DIR}/ke_backup_${timestamp}.sql.gz}"

mkdir -p "${BACKUP_DIR}"

echo "📦 Backing up database to ${output_file}..."

# Use pg_dump from within the container
docker compose -f "${PROJECT_ROOT}/db/docker-compose.yml" exec -T postgres \
    pg_dump -U ke_user -d knowledge_engine --clean --if-exists | gzip > "${output_file}"

echo "✅ Backup complete: ${output_file}"
echo "   Size: $(du -h "${output_file}" | cut -f1)"

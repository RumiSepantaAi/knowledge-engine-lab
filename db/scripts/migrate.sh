#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Knowledge Engine - Database Migration Runner (Production-Grade)
# ─────────────────────────────────────────────────────────────────────────────
#
# Features:
#   - Tracks applied migrations in public.schema_migrations
#   - Skips already-applied migrations (rerunnable)
#   - Advisory lock prevents parallel corruption
#   - SHA256 drift detection warns if applied file changed
#   - Supports "-- ke:no_tx" header for non-transactional migrations
#
# Usage:
#   ./db/scripts/migrate.sh                    # Run from host (docker exec)
#   INSIDE_CONTAINER=1 ./db/scripts/migrate.sh # Run inside container
#
# Environment:
#   POSTGRES_USER    - Database user (default: ke_user)
#   POSTGRES_DB      - Database name (default: knowledge_engine)
#   INSIDE_CONTAINER - Set to 1 if running inside the container
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

POSTGRES_USER="${POSTGRES_USER:-ke_user}"
POSTGRES_DB="${POSTGRES_DB:-knowledge_engine}"
INSIDE_CONTAINER="${INSIDE_CONTAINER:-0}"

# Advisory lock ID (arbitrary but consistent)
LOCK_ID=123456789

# Set migrations directory based on context
if [[ "${INSIDE_CONTAINER}" == "1" ]]; then
    MIGRATIONS_DIR="/migrations"
else
    MIGRATIONS_DIR="${PROJECT_ROOT}/db/migrations"
fi

# ─────────────────────────────────────────────────────────────────────────────
# Colors
# ─────────────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_skip()  { echo -e "${BLUE}[SKIP]${NC} $1"; }

# ─────────────────────────────────────────────────────────────────────────────
# Helper: Run psql command (returns output)
# ─────────────────────────────────────────────────────────────────────────────
run_psql() {
    local cmd="$1"
    if [[ "${INSIDE_CONTAINER}" == "1" ]]; then
        psql -X -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
            -v ON_ERROR_STOP=1 \
            -c "$cmd"
    else
        docker compose -f "${PROJECT_ROOT}/db/docker-compose.yml" exec -T postgres \
            psql -X -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
            -v ON_ERROR_STOP=1 \
            -c "$cmd"
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Helper: Run psql query (returns value only, no headers)
# ─────────────────────────────────────────────────────────────────────────────
run_psql_query() {
    local cmd="$1"
    if [[ "${INSIDE_CONTAINER}" == "1" ]]; then
        psql -X -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -tAc "$cmd" 2>/dev/null || echo ""
    else
        docker compose -f "${PROJECT_ROOT}/db/docker-compose.yml" exec -T postgres \
            psql -X -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -tAc "$cmd" 2>/dev/null || echo ""
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Helper: Run psql file (with or without transaction based on header)
# ─────────────────────────────────────────────────────────────────────────────
run_psql_file() {
    local filepath="$1"
    local filename="$2"
    local use_tx="$3"  # "1" for transaction, "0" for no transaction

    local tx_flag=""
    if [[ "$use_tx" == "1" ]]; then
        tx_flag="-1"
    fi

    if [[ "${INSIDE_CONTAINER}" == "1" ]]; then
        psql -X ${tx_flag} -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
            -v ON_ERROR_STOP=1 \
            -f "$filepath"
    else
        docker compose -f "${PROJECT_ROOT}/db/docker-compose.yml" exec -T postgres \
            psql -X ${tx_flag} -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
            -v ON_ERROR_STOP=1 \
            -f "/migrations/${filename}"
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Helper: Compute SHA256 of file content
# ─────────────────────────────────────────────────────────────────────────────
compute_sha256() {
    local filepath="$1"
    if command -v sha256sum &>/dev/null; then
        sha256sum "$filepath" | cut -d' ' -f1
    elif command -v shasum &>/dev/null; then
        shasum -a 256 "$filepath" | cut -d' ' -f1
    else
        # Fallback: use openssl
        openssl dgst -sha256 "$filepath" | awk '{print $NF}'
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Helper: Check if file has "-- ke:no_tx" header (first 5 lines)
# ─────────────────────────────────────────────────────────────────────────────
needs_no_transaction() {
    local filepath="$1"
    head -n 5 "$filepath" 2>/dev/null | grep -q '-- ke:no_tx'
}

# ─────────────────────────────────────────────────────────────────────────────
# Helper: Check if migration was already applied (returns sha256 if exists)
# ─────────────────────────────────────────────────────────────────────────────
get_applied_sha256() {
    local filename="$1"
    # Use dollar-quoting to prevent SQL injection
    run_psql_query "SELECT content_sha256 FROM public.schema_migrations WHERE filename = \$\$${filename}\$\$"
}

# ─────────────────────────────────────────────────────────────────────────────
# Helper: Record migration as applied
# ─────────────────────────────────────────────────────────────────────────────
record_migration() {
    local filename="$1"
    local sha256="$2"
    # Use dollar-quoting and ON CONFLICT for safety
    run_psql "INSERT INTO public.schema_migrations (filename, content_sha256) VALUES (\$\$${filename}\$\$, \$\$${sha256}\$\$) ON CONFLICT (filename) DO NOTHING" >/dev/null
}

# ─────────────────────────────────────────────────────────────────────────────
# Helper: Acquire advisory lock
# ─────────────────────────────────────────────────────────────────────────────
acquire_lock() {
    local result
    result=$(run_psql_query "SELECT pg_try_advisory_lock(${LOCK_ID})")
    if [[ "$result" != "t" ]]; then
        log_error "Could not acquire migration lock. Another migration may be running."
        exit 1
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Helper: Release advisory lock
# ─────────────────────────────────────────────────────────────────────────────
release_lock() {
    run_psql_query "SELECT pg_advisory_unlock(${LOCK_ID})" >/dev/null 2>&1 || true
}

# ─────────────────────────────────────────────────────────────────────────────
# Bootstrap: Ensure schema_migrations table exists
# ─────────────────────────────────────────────────────────────────────────────
bootstrap_migrations_table() {
    run_psql "CREATE TABLE IF NOT EXISTS public.schema_migrations (
        filename TEXT PRIMARY KEY,
        content_sha256 TEXT,
        applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )" >/dev/null 2>&1

    # Add sha256 column if missing (upgrade path)
    run_psql "DO \$\$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = 'schema_migrations'
            AND column_name = 'content_sha256'
        ) THEN
            ALTER TABLE public.schema_migrations ADD COLUMN content_sha256 TEXT;
        END IF;
    END \$\$" >/dev/null 2>&1
}

# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
main() {
    log_info "Starting database migration..."
    log_info "Migrations directory: ${MIGRATIONS_DIR}"

    # Check migrations directory exists (host mode only)
    if [[ "${INSIDE_CONTAINER}" != "1" && ! -d "${MIGRATIONS_DIR}" ]]; then
        log_error "Migrations directory not found: ${MIGRATIONS_DIR}"
        exit 1
    fi

    # Get list of migration files (sorted) - portable for macOS/Linux
    local migrations=()
    while IFS= read -r -d '' file; do
        migrations+=("$file")
    done < <(find "${MIGRATIONS_DIR}" -maxdepth 1 -name '*.sql' -type f -print0 2>/dev/null | sort -z)

    if [[ ${#migrations[@]} -eq 0 ]]; then
        log_warn "No migration files found in ${MIGRATIONS_DIR}"
        exit 0
    fi

    log_info "Found ${#migrations[@]} migration file(s)"

    # Bootstrap migrations table
    bootstrap_migrations_table

    # Acquire advisory lock
    acquire_lock
    trap release_lock EXIT

    # Run each migration
    local applied=0
    local skipped=0
    local drifted=0

    for migration in "${migrations[@]}"; do
        local filename
        filename=$(basename "${migration}")
        local current_sha256
        current_sha256=$(compute_sha256 "${migration}")

        # Check if already applied
        local stored_sha256
        stored_sha256=$(get_applied_sha256 "${filename}")

        if [[ -n "$stored_sha256" ]]; then
            # Migration was applied - check for drift
            if [[ "$stored_sha256" != "$current_sha256" && -n "$stored_sha256" ]]; then
                log_warn "${filename} DRIFT DETECTED! File changed since applied."
                log_warn "  Stored:  ${stored_sha256:0:16}..."
                log_warn "  Current: ${current_sha256:0:16}..."
                drifted=$((drifted + 1))
            fi
            log_skip "${filename} (already applied)"
            skipped=$((skipped + 1))
            continue
        fi

        # Check if needs non-transactional mode
        local use_tx="1"
        if needs_no_transaction "${migration}"; then
            log_info "Applying (no-tx): ${filename}"
            use_tx="0"
        else
            log_info "Applying: ${filename}"
        fi

        # Run migration
        run_psql_file "${migration}" "${filename}" "${use_tx}"

        # Record as applied with sha256
        record_migration "${filename}" "${current_sha256}"

        applied=$((applied + 1))
    done

    # Release lock (also done by trap)
    release_lock

    log_info "Migration complete: ${applied} applied, ${skipped} skipped"
    if [[ $drifted -gt 0 ]]; then
        log_warn "⚠️  ${drifted} migration(s) have drifted since application!"
    fi
}

main "$@"

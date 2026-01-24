# Database Migrations

Production-grade migration system with drift detection and concurrency safety.

## Quick Reference

See [docs/db.md](docs/db.md) for full operations runbook (Backup/Restore).

```bash
make db-up           # Start database
make db-migrate      # Run migrations (rerunnable, skips applied)
make db-migrations   # Show applied migrations with SHA256
make db-status       # Show schema tables
make db-psql         # Interactive psql session
CONFIRM=YES make db-reset  # Reset database (destroys data)
```

## Dev vs Prod Separation

- **Fresh Install (Dev)**: `db/initdb/` scripts run automatically on fresh volume creation to set up extensions and basic schemas.
- **Updates (Prod/Dev)**: `make db-migrate` runs `db/scripts/migrate.sh` to apply changes safely. **Always** use migrations for schema changes, never edit `initdb` scripts for existing databases.

## Features

### Rerunnable Migrations
Migrations are tracked in `public.schema_migrations`. Re-running `make db-migrate` safely skips already-applied files.

### SHA256 Drift Detection
Each migration's content hash is stored. If you modify an already-applied migration file, you'll see:
```
[WARN] 002_meta_taxonomy.sql DRIFT DETECTED! File changed since applied.
```

### Advisory Lock
PostgreSQL advisory lock prevents parallel migration runs from corrupting state.

### Non-Transactional Migrations
For DDL that can't run in a transaction (e.g., `CREATE INDEX CONCURRENTLY`), add this header to your migration file:
```sql
-- ke:no_tx
CREATE INDEX CONCURRENTLY ...
```

## Directory Structure

```
db/
├── docker-compose.yml
├── migrations/
│   ├── 000_schema_migrations.sql  # Tracking table
│   ├── 001_extensions_and_helpers.sql
│   ├── 002_meta_taxonomy.sql
│   └── ...
└── scripts/
    └── migrate.sh                 # Migration runner
```

## Adding a Migration

1. Create file with next number:
   ```bash
   touch db/migrations/012_my_feature.sql
   ```

2. Write SQL (idempotent preferred):
   ```sql
   CREATE TABLE IF NOT EXISTS ...
   CREATE INDEX IF NOT EXISTS ...
   ```

3. For non-transactional DDL, add header:
   ```sql
   -- ke:no_tx
   CREATE INDEX CONCURRENTLY IF NOT EXISTS ...
   ```

4. Run: `make db-migrate`

## Schema Overview

### Meta Schema (`meta.*`)
- `taxonomy_node` - Hierarchical taxonomy (L1-L4)
- `glossary_term` - Term definitions
- `control` - Governance controls

### Evidence Schema (`evidence.*`)
- `document` - Source documents
- `document_revision` - Versioned snapshots
- `chunk` - Text chunks with embeddings
- `claim` - Extracted claims
- `evidence_span` - Claim-to-chunk links

## Quality Gates

```sql
-- Claims missing evidence
SELECT * FROM evidence.v_claims_without_evidence;

-- Validate document (fails if claims lack evidence)
SELECT * FROM evidence.validate_document('doc-uuid');
```

## Troubleshooting

### "Could not acquire migration lock"
Another migration is running. Wait or check for stuck processes.

### Drift Warnings
If you intentionally changed an applied migration, the warning is expected. The migration won't re-run. To re-apply, you'd need to reset the database.

### Full Reset
```bash
CONFIRM=YES make db-reset
sleep 3
make db-migrate
```

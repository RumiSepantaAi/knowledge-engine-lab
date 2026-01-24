# Database Runbook

## Overview

The Knowledge Engine uses PostgreSQL 16 with `pgvector` for embedding storage.

- **Port**: 5432 (mapped to host)
- **User**: `ke_user`
- **Database**: `knowledge_engine`
- **Schemas**: `public` (migrations), `meta` (taxonomy), `evidence` (chunks, claims)

## Daily Operations

### Start/Stop
```bash
make db-up    # Start in background
make db-down  # Stop and remove container
```

### Connect
```bash
make db-psql  # Interactive shell
```

### Logs
```bash
make db-logs
```

## Maintenance

### Migrations
All schema changes must be done via migrations.

```bash
# Apply pending migrations
make db-migrate

# Check status
make db-migrations
make db-status
```

### Backup & Restore
Backups are stored in `backups/` as gzip-compressed SQL dumps.

```bash
# Create backup (filename auto-generated with timestamp)
make db-backup

# Restore from specific file
make db-restore FILE=backups/ke_backup_20240101_120000.sql.gz
```

### Seeding Data
To populate the database with initial/stub data:

```bash
make db-seed
```

## Emergency / Disaster Recovery

### Reset Database
**WARNING: This destroys all data!**

```bash
CONFIRM=YES make db-reset
# Re-applies all migrations automatically
make db-migrate
```

### Troubleshooting Locks
If `make db-migrate` says "Could not acquire migration lock":
1. Check for running migration processes.
2. If verified stuck (e.g. killed process), manually unlock:
   ```sql
   SELECT pg_advisory_unlock(123456789);
   ```

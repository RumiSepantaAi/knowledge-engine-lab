# Security Baseline

## Overview

This document covers security practices for the Knowledge Engine.

## Secret Handling

### Environment Variables

All secrets are loaded from environment variables, never committed to git:

| Secret | Variable | Usage |
|--------|----------|-------|
| Database password | `POSTGRES_PASSWORD` | DB connection |
| OpenAI API key | `OPENAI_API_KEY` | Embeddings |

### Best Practices

1. Copy `.env.example` to `.env`
2. Never commit `.env` to git (already in `.gitignore`)
3. Use different credentials per environment (dev/staging/prod)
4. Rotate keys periodically

## Database Roles

### Principle of Least Privilege

| Role | Purpose | Permissions |
|------|---------|-------------|
| `ke_admin` | Migrations, DDL | Full privileges |
| `ke_app` | Application RW | SELECT, INSERT, UPDATE, DELETE on tables |
| `ke_ro` | Read-only queries | SELECT only |

### Role Usage

| Component | Role | Why |
|-----------|------|-----|
| `make db-migrate` | `ke_admin` | Needs DDL for schema changes |
| CLI/UI/API writes | `ke_app` | Limited to DML only |
| Analytics/reporting | `ke_ro` | Read-only, no write risk |

### Create Roles

```bash
make db-create-roles
```

### Verify Permissions

```bash
make db-verify-permissions
```

## Prompt Injection Risks

### Attack Vectors

1. **Claim text injection**: Malicious content in claim_text that could manipulate downstream LLM processing
2. **Tag injection**: Tags containing executable patterns
3. **Snippet injection**: Evidence snippets with embedded instructions

### Mitigations

| Risk | Mitigation |
|------|------------|
| SQL injection | Parameterized queries only (enforced in `ke_db`) |
| XSS in UI | Streamlit auto-escapes output |
| LLM prompt injection | Sanitize before embedding; use system prompts |
| API abuse | Rate limiting (future); input validation (Pydantic) |

### Code Practices

```python
# NEVER do this:
cur.execute(f"SELECT * FROM chunks WHERE text = '{user_input}'")

# ALWAYS do this:
cur.execute("SELECT * FROM chunks WHERE text = %s", (user_input,))
```

All `ke_db` functions use parameterized queries.

## Backup/Restore

### Cadence

| Environment | Backup Frequency | Retention |
|-------------|------------------|-----------|
| Development | On-demand | 7 days |
| Staging | Daily | 14 days |
| Production | Daily + before migrations | 90 days |

### Commands

```bash
# Create backup
make db-backup

# Restore from backup
make db-restore FILE=backups/ke_backup_YYYYMMDD_HHMMSS.sql.gz
```

### Pre-Migration Backup

Always backup before running migrations in production:

```bash
make db-backup
make db-migrate
```

## Authentication (Future)

Current: No authentication (local-first development).

Planned structure:
- Session-based auth for UI
- API key auth for API
- Role-based access control (RBAC)

## Audit Logging (Future)

Tables have `created_at` and `updated_at` timestamps. Full audit logging can be added via:
- PostgreSQL `pgaudit` extension
- Application-level event logging

## Checklist

- [x] Secrets in environment only
- [x] `.env.example` template (no secrets)
- [x] Parameterized queries everywhere
- [x] DB role separation
- [x] Backup/restore scripts
- [ ] Rate limiting (future)
- [ ] Authentication (future)
- [ ] Audit logging (future)

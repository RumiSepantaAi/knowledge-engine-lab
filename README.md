# AI Knowledge Engine Control Plane

A production-grade foundation for managing knowledge graphs with Meta-Graph taxonomy and Evidence-Graph provenance.

## Overview

The Knowledge Engine provides:
- **Meta-Graph**: Taxonomy, glossary, and control definitions
- **Evidence-Graph**: Document citations, claims, and provenance tracking
- **CLI**: Interactive workflow for managing knowledge entities

## Prerequisites

- Python 3.11+
- Docker Desktop (for PostgreSQL)
- [uv](https://docs.astral.sh/uv/) — install with `curl -LsSf https://astral.sh/uv/install.sh | sh`

## Quick Start

### 1. Bootstrap Development Environment

```bash
# Clone and enter the repository
cd knowledge-engine

# Run bootstrap (requires uv to be installed)
make bootstrap

# Or auto-install uv during bootstrap:
UV_INSTALL=YES make bootstrap

# Activate the virtual environment
source .venv/bin/activate
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings (optional for local dev)
```

### 3. Start Database

```bash
# Start PostgreSQL with pgvector
make db-up

# Run database migrations (required on first setup)
make db-migrate

# Verify connection and schema
make db-psql
```

> **Note**: The Knowledge Engine uses two PostgreSQL schemas:
> - `meta` — Taxonomy, glossary, and control definitions
> - `evidence` — Documents, claims, chunks, and evidence spans

### 4. Run Tests

```bash
make test
```

## Development Commands

| Command | Description |
|---------|-------------|
| `make bootstrap` | Install dependencies and set up environment |
| `make lint` | Run ruff linter |
| `make fmt` | Format code with ruff |
| `make test` | Run pytest |
| `make test-cov` | Run tests with coverage report |
| `make typecheck` | Run mypy type checker |
| `make clean` | Remove build artifacts and caches |
| `make db-up` | Start PostgreSQL container |
| `make db-down` | Stop PostgreSQL container |
| `make db-migrate` | Run database migrations (rerunnable) |
| `make db-migrations` | Show applied migrations with SHA256 |
| `make db-status` | Show database schema tables |
| `make db-logs` | Tail container logs |
| `make db-psql` | Connect to database via psql |
| `make help` | Show all available commands |

## Project Structure

```
├── apps/ke_cli/      # Interactive CLI application
├── db/               # Docker compose + migrations
├── docs/             # Architecture and runbooks
├── meta/             # Taxonomy, glossary, controls, importer
├── tests/            # Test suite
└── tools/            # Development tooling
```

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full overview of Meta-Graph vs Evidence-Graph design.

## Implemented Components

1. **Meta-Blueprint Importer**: CSV taxonomy import with normalization (`meta/importer/`)
2. **Database Schema**: PostgreSQL + pgvector with migrations (`db/migrations/`)
3. **Quality Gates**: Evidence validation views and functions
4. **CLI**: Taxonomy import CLI (`python -m meta.importer.import_taxonomy`)
5. **Web UI**: Streamlit dashboard (`apps/ke_ui/`)

See [docs/db_migrations.md](docs/db_migrations.md) and [docs/meta_importer.md](docs/meta_importer.md).

## Web UI (Optional)

The Knowledge Engine includes an optional Streamlit-based web interface.

### Install UI Dependencies

```bash
# Install both dev and ui extras
uv sync --extra dev --extra ui
```

### Run the UI

```bash
make ui
# Opens atttp://localhost:8501
```

### UI Pages

| Page | Description |
|------|-------------|
| **Status** | System health, env vars, DB connectivity |
| **Importer** | Upload CSVs and process taxonomy |
| **Taxonomy Browser** | Search and explore taxonomy tree |
| **DQ Report** | View data quality reports |
| **DB Migrations** | View applied migrations + drift warnings |

## Contributing

1. Install pre-commit hooks: `pre-commit install`
2. Run linting before commits: `make lint`
3. Ensure tests pass: `make test`
## License

MIT License

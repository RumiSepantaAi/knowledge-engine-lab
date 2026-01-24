# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of Knowledge Engine
- **ke_db**: Shared database access layer with parameterized queries
- **ke_cli**: Typer CLI with doc, chunk, claim, evidence, quality, embed commands
- **ke_ui**: Streamlit web interface with dashboard and workflow pages
- **ke_api**: FastAPI REST API with OpenAPI documentation
- **Retrieval**: Full-text, vector, and hybrid search
- **Embeddings**: Provider interface with DummyProvider and RemoteProvider
- **Security**: DB roles (ke_app, ke_ro), secret handling, parameterized queries
- **CI/CD**: GitHub Actions workflows for lint, typecheck, tests, integration

### Database
- PostgreSQL 16 with pgvector extension
- 13 migrations for meta and evidence schemas
- Quality gate views for claim validation

## [0.1.0] - 2026-01-24

### Added
- Initial project structure
- Meta-Blueprint Importer with CSV parsing
- Database migrations with drift detection
- Production-grade migrate.sh with advisory locks

---

## Versioning Strategy

This project uses [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.0.0): Breaking changes to API, CLI, or database schema
- **MINOR** (0.1.0): New features, backward-compatible
- **PATCH** (0.1.1): Bug fixes, backward-compatible

### Version Locations

Update version in:
1. `pyproject.toml` → `version = "X.Y.Z"`
2. `CHANGELOG.md` → Add release entry
3. Git tag → `git tag v0.1.0`

### Release Checklist

1. Update `CHANGELOG.md` with release notes
2. Update version in `pyproject.toml`
3. Run `make ci` to validate
4. Commit: `git commit -m "Release vX.Y.Z"`
5. Tag: `git tag vX.Y.Z`
6. Push: `git push && git push --tags`

.PHONY: bootstrap lint fmt typecheck test test-cov ci clean db-up db-down db-logs db-psql db-reset db-migrate db-status db-seed db-migrations db-backup db-restore db-create-roles db-verify-permissions ui api api-test help

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────
PYTHON := python3
UV := uv
VENV := .venv
DOCKER_COMPOSE := docker compose -f db/docker-compose.yml

# Load environment variables if .env exists
ifneq (,$(wildcard .env))
    include .env
    export
endif

# Default target
.DEFAULT_GOAL := help

# ─────────────────────────────────────────────────────────────────────────────
# Development Setup
# ─────────────────────────────────────────────────────────────────────────────
bootstrap: ## Install dependencies and set up development environment
	@echo "🚀 Bootstrapping development environment..."
	@command -v $(UV) >/dev/null 2>&1 || { \
		if [ "$${UV_INSTALL}" = "YES" ]; then \
			echo "Installing uv..."; \
			curl -LsSf https://astral.sh/uv/install.sh | sh; \
		else \
			echo "❌ uv is not installed."; \
			echo "   Install manually: curl -LsSf https://astral.sh/uv/install.sh | sh"; \
			echo "   Or run: UV_INSTALL=YES make bootstrap"; \
			exit 1; \
		fi; \
	}
	@test -f uv.lock || $(UV) lock
	$(UV) sync --extra dev
	$(UV) run pre-commit install
	@echo "✅ Bootstrap complete! Activate venv with: source $(VENV)/bin/activate"

# ─────────────────────────────────────────────────────────────────────────────
# Code Quality
# ─────────────────────────────────────────────────────────────────────────────
lint: ## Run ruff linter
	@echo "🔍 Running linter..."
	$(UV) run ruff check apps meta tests

fmt: ## Format code with ruff
	@echo "✨ Formatting code..."
	$(UV) run ruff format apps meta tests
	$(UV) run ruff check --fix apps meta tests

typecheck: ## Run mypy type checker
	@echo "🔬 Running type checker..."
	$(UV) run mypy apps meta

# ─────────────────────────────────────────────────────────────────────────────
# Testing
# ─────────────────────────────────────────────────────────────────────────────
test: ## Run pytest
	@echo "🧪 Running tests..."
	$(UV) run pytest

test-cov: ## Run pytest with coverage
	@echo "🧪 Running tests with coverage..."
	$(UV) run pytest --cov=apps --cov=meta --cov-report=html

ci: lint typecheck test ## Run full CI pipeline locally (mirrors GitHub Actions)
	@echo "✅ CI passed!"

# ─────────────────────────────────────────────────────────────────────────────
# Database
# ─────────────────────────────────────────────────────────────────────────────
db-up: ## Start PostgreSQL container
	@echo "🐘 Starting PostgreSQL..."
	$(DOCKER_COMPOSE) up -d
	@echo "✅ PostgreSQL started. Connect with: make db-psql"

db-down: ## Stop PostgreSQL container
	@echo "🛑 Stopping PostgreSQL..."
	$(DOCKER_COMPOSE) down

db-logs: ## Tail PostgreSQL container logs
	$(DOCKER_COMPOSE) logs -f

db-psql: ## Connect to PostgreSQL via psql
	@echo "🔌 Connecting to PostgreSQL..."
	$(DOCKER_COMPOSE) exec postgres psql -X -U $${POSTGRES_USER:-ke_user} -d $${POSTGRES_DB:-knowledge_engine}

db-reset: ## Reset database (WARNING: destroys data, requires CONFIRM=YES)
	@if [ "$${CONFIRM}" != "YES" ]; then \
		echo "❌ db-reset is a destructive operation."; \
		echo "   Run with: CONFIRM=YES make db-reset"; \
		exit 1; \
	fi
	@echo "⚠️  Resetting database..."
	$(DOCKER_COMPOSE) down -v
	$(DOCKER_COMPOSE) up -d

db-migrate: ## Run database migrations (rerunnable, skips applied)
	@echo "🔄 Running database migrations..."
	@chmod +x db/scripts/migrate.sh
	@db/scripts/migrate.sh

db-migrations: ## Show applied migrations
	@echo "📋 Applied migrations:"
	@$(DOCKER_COMPOSE) exec -T postgres psql -X -U $${POSTGRES_USER:-ke_user} -d $${POSTGRES_DB:-knowledge_engine} -c \
		"SELECT filename, LEFT(content_sha256, 16) || '...' AS sha256, applied_at FROM public.schema_migrations ORDER BY filename;"

db-status: ## Show database schema status
	@echo "📊 Database schema status..."
	@$(DOCKER_COMPOSE) exec -T postgres psql -X -U $${POSTGRES_USER:-ke_user} -d $${POSTGRES_DB:-knowledge_engine} -c "\
		SELECT schemaname, tablename FROM pg_tables \
		WHERE schemaname IN ('meta', 'evidence', 'public') ORDER BY schemaname, tablename;"

db-seed: ## Seed database with sample data
	@echo "🌱 Seeding database..."
	@$(DOCKER_COMPOSE) exec -T postgres psql -U $${POSTGRES_USER:-ke_user} -d $${POSTGRES_DB:-knowledge_engine} -f /docker-entrypoint-initdb.d/002_seed_taxonomy.sql
	@echo "✅ Seed complete!"

db-backup: ## Backup database to backups/ (Usage: make db-backup [FILE=...])
	@db/scripts/db_backup.sh $(FILE)

db-restore: ## Restore database from backup (Usage: make db-restore FILE=...)
	@db/scripts/db_restore.sh $(FILE)

db-create-roles: ## Create ke_app and ke_ro roles
	@echo "🔐 Creating database roles..."
	@chmod +x db/scripts/create_roles.sh
	@db/scripts/create_roles.sh

db-verify-permissions: ## Verify role permissions
	@echo "🔍 Verifying permissions..."
	@chmod +x db/scripts/verify_permissions.sh
	@db/scripts/verify_permissions.sh

# ─────────────────────────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────────────────────────
ui: ## Run Streamlit UI (requires: uv sync --extra ui)
	@echo "🌐 Starting Knowledge Engine UI..."
	@$(UV) run streamlit run apps/ke_ui/app.py --server.headless true

# ─────────────────────────────────────────────────────────────────────────────
# API
# ─────────────────────────────────────────────────────────────────────────────
api: ## Run FastAPI server (requires: uv sync --extra api)
	@echo "🚀 Starting Knowledge Engine API..."
	@$(UV) run uvicorn apps.ke_api.main:app --reload --port 8000

api-test: ## Run API integration tests
	@echo "🧪 Running API tests..."
	@$(UV) run pytest tests/test_api/ -v

# ─────────────────────────────────────────────────────────────────────────────
# Cleanup
# ─────────────────────────────────────────────────────────────────────────────
clean: ## Remove build artifacts and caches
	@echo "🧹 Cleaning up..."
	rm -rf $(VENV)
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	rm -rf htmlcov .coverage
	rm -rf dist build *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Clean complete!"

# ─────────────────────────────────────────────────────────────────────────────
# Help
# ─────────────────────────────────────────────────────────────────────────────
help: ## Show this help message
	@echo "Knowledge Engine - Development Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

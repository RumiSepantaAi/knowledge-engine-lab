# ─────────────────────────────────────────────────────────────────────────────
# Knowledge Engine API - Production Dockerfile
# ─────────────────────────────────────────────────────────────────────────────
# Build: docker build -t knowledge-engine:latest .
# Run:   docker run -p 8000:8000 --env-file .env knowledge-engine:latest
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim AS builder

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock* ./

# Install dependencies (without dev extras)
RUN uv sync --no-dev --extra api --frozen

# ─────────────────────────────────────────────────────────────────────────────
# Production stage
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy uv and virtual environment from builder
COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY apps/ ./apps/
COPY meta/ ./meta/
COPY pyproject.toml ./

# Set environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')" || exit 1

# Run API server
CMD ["uvicorn", "apps.ke_api.main:app", "--host", "0.0.0.0", "--port", "8000"]

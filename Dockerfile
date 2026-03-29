# Multi-stage build for minimal image size
# Stage 1: Build
FROM python:3.12.11-slim AS builder

WORKDIR /app

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:0.7.12 /uv /usr/local/bin/uv

# Copy dependency files first (cache layer)
COPY pyproject.toml uv.lock ./

# Create venv and install production dependencies
RUN uv venv .venv && \
    uv sync --no-dev --no-editable --no-install-project

# Copy source
COPY src/ src/

# Install the package itself (no deps, already installed)
RUN uv pip install --no-deps .

# Stage 2: Runtime
FROM python:3.12.11-slim AS runtime

# Create non-root user for security
RUN addgroup --system meridian && adduser --system --ingroup meridian meridian

WORKDIR /app

# Copy installed venv from builder
COPY --from=builder /app/.venv /app/.venv

# Copy source (needed by the installed package)
COPY src/ src/

# Set ownership
RUN chown -R meridian:meridian /app

USER meridian

# Set PATH to use venv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Default port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import httpx; r = httpx.get('http://localhost:8000/health'); assert r.status_code == 200"

# Run with uvicorn
CMD ["uvicorn", "meridian.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

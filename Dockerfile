# ─────────────────────────────────────────────────────────────────
# Stage 1: dependency builder
# ─────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build tools only in this stage
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip --quiet \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt

# ─────────────────────────────────────────────────────────────────
# Stage 2: final runtime image (~180 MB)
# ─────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Security: run as non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app -s /sbin/nologin appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY app/ ./app/

# Set ownership
RUN chown -R appuser:appgroup /app

USER appuser

# Cloud Run requires port 8080
EXPOSE 8080

# Health check (Cloud Run also performs its own)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/health')"

# Environment defaults (override via Cloud Run env vars)
ENV PORT=8080 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=INFO

# Start Uvicorn (ASGI, production-grade)
CMD ["python", "-m", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8080", \
     "--workers", "2", \
     "--log-level", "info", \
     "--no-access-log"]

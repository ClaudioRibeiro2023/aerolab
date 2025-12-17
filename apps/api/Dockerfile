# Backend Dockerfile
# Multi-stage build for smaller image

# ==================== BUILD STAGE ====================
FROM python:3.13-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir build && \
    pip wheel --no-cache-dir --wheel-dir /wheels -e ".[rag,all-domains]"

# ==================== PRODUCTION STAGE ====================
FROM python:3.13-slim as production

WORKDIR /app

# Create non-root user
RUN groupadd -r agno && useradd -r -g agno agno

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels

# Copy application code
COPY src/ ./src/
COPY app.py ./
COPY server.py ./
COPY requirements.txt ./

# Create data directories
RUN mkdir -p data/databases data/vectorstore data/logs && \
    chown -R agno:agno /app

# Switch to non-root user
USER agno

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    AGENTOS_HOST=0.0.0.0 \
    AGENTOS_PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Expose port
EXPOSE 8000

# Run application
# Run application (unified server with Flow Studio)
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]

# =============================================================================
# Xcapit FHE-ML Platform - Django Backend
# =============================================================================
# Multi-stage build for optimized production image
# Django 5.2 LTS - Supported until April 2028
#
# Build targets:
#   - builder:     Compiles dependencies
#   - production:  Minimal production image (~200MB)
#   - development: Includes dev tools for local development
#
# Usage:
#   Production:  docker build -t xcapit-fhe-django .
#   Development: docker build --target development -t xcapit-fhe-django:dev .
# =============================================================================

# ============ Build Stage ============
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# ============ Production Stage ============
FROM python:3.12-slim AS production

# Labels for container metadata
LABEL org.opencontainers.image.title="Xcapit FHE-ML Platform API"
LABEL org.opencontainers.image.description="Privacy-preserving ML using Fully Homomorphic Encryption"
LABEL org.opencontainers.image.version="2.0.0"
LABEL org.opencontainers.image.vendor="Xcapit"

# Python optimizations
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install runtime dependencies (combined for fewer layers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    # Create non-root user
    && useradd --create-home --shell /bin/bash --uid 1000 django \
    # Create directories
    && mkdir -p /app/staticfiles /app/logs \
    && chown -R django:django /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code (as root, then fix permissions)
COPY --chown=django:django . .

# Ensure entrypoint is executable
RUN chmod +x /app/docker-entrypoint.sh

# Switch to non-root user
USER django

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Entrypoint handles migrations and startup
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Production command: gunicorn with optimized settings
# - workers: 2-4 x CPU cores (4 is good default for 2 cores)
# - threads: 2-4 per worker for I/O bound work
# - timeout: 30s to prevent hanging workers
# - graceful-timeout: 10s for clean shutdown
# - max-requests: restart workers after N requests to prevent memory leaks
CMD ["gunicorn", "config.wsgi:application", \
    "--bind", "0.0.0.0:8000", \
    "--workers", "4", \
    "--threads", "2", \
    "--timeout", "30", \
    "--graceful-timeout", "10", \
    "--max-requests", "1000", \
    "--max-requests-jitter", "50", \
    "--access-logfile", "-", \
    "--error-logfile", "-", \
    "--capture-output", \
    "--enable-stdio-inheritance"]

# ============ Development Stage ============
FROM production AS development

USER root

# Install development dependencies
RUN pip install --no-cache-dir \
    pytest>=8.0.0 \
    pytest-cov>=5.0.0 \
    pytest-django>=4.8.0 \
    black>=24.0.0 \
    ruff>=0.4.0 \
    ipython>=8.0.0 \
    django-debug-toolbar>=4.3.0

USER django

# Development uses Django's runserver with auto-reload
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

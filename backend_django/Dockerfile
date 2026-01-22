# Xcapit FHE-ML Platform - Django Backend
# Multi-stage build for optimized production image

# ============ Build Stage ============
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ============ Production Stage ============
FROM python:3.11-slim as production

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash django \
    && chown -R django:django /app

# Create static files directory
RUN mkdir -p /app/staticfiles && chown django:django /app/staticfiles

USER django

# Collect static files
RUN python manage.py collectstatic --noinput 2>/dev/null || true

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v2/health/ || exit 1

# Default command: run with gunicorn
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2"]

# ============ Development Stage ============
FROM production as development

USER root

# Install development dependencies
RUN pip install --no-cache-dir \
    pytest>=7.4.0 \
    pytest-cov>=4.1.0 \
    pytest-django>=4.7.0 \
    black>=23.0.0 \
    ruff>=0.1.0 \
    ipython>=8.0.0

USER django

# Development command: run with auto-reload
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

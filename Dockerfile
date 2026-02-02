# Xcapit FHE-ML Platform Docker Image
# Multi-stage build for optimized image size

# ============ Build Stage ============
FROM python:3.14-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY pyproject.toml .
COPY requirements-dev.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install base dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install SDK dependencies (without FHE libs for lighter image)
RUN pip install --no-cache-dir \
    numpy>=1.24.0 \
    pandas>=2.0.0 \
    scikit-learn>=1.3.0 \
    web3>=6.0.0 \
    eth-account>=0.10.0 \
    fastapi>=0.104.0 \
    uvicorn>=0.24.0 \
    pydantic>=2.5.0

# ============ Production Stage ============
FROM python:3.14-slim as production

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy SDK code
COPY sdk/ ./sdk/
COPY pyproject.toml .

# Install SDK in editable mode
RUN pip install -e .

# Create non-root user
RUN useradd --create-home --shell /bin/bash fheml
USER fheml

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command: run API server
CMD ["uvicorn", "sdk.api.server:app", "--host", "0.0.0.0", "--port", "8000"]

# ============ Development Stage ============
FROM production as development

USER root

# Install development dependencies
RUN pip install --no-cache-dir \
    pytest>=7.4.0 \
    pytest-cov>=4.1.0 \
    black>=23.0.0 \
    ruff>=0.1.0 \
    jupyter>=1.0.0 \
    ipykernel>=6.25.0

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

USER fheml

# Expose Jupyter port
EXPOSE 8888

# ============ FHE Stage (with TenSEAL) ============
FROM production as fhe

USER root

# Install TenSEAL dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Install TenSEAL (heavy, so separate stage)
RUN pip install --no-cache-dir tenseal>=0.3.14

USER fheml

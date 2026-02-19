# Installation Guide

This guide covers all installation methods for the Xcapit FHE-ML Platform.

## Prerequisites

- Python 3.9 or higher
- Node.js 18+ (for dashboard and TypeScript SDK)
- Docker (optional, for containerized deployment)

## Installation Methods

### 1. Python SDK (pip)

```bash
# Basic installation
pip install xcapit-fhe-ml

# With API server support
pip install xcapit-fhe-ml[api]

# With all optional dependencies
pip install xcapit-fhe-ml[all]

# Development installation
pip install xcapit-fhe-ml[dev]
```

### 2. From Source

```bash
git clone https://github.com/xcapit/Xcapit-FHE-ML-Platform.git
cd Xcapit-FHE-ML-Platform

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

### 3. TypeScript SDK (npm)

```bash
npm install @xcapit/fhe-ml-sdk
# or
yarn add @xcapit/fhe-ml-sdk
```

### 4. Docker

```bash
# Production
docker pull xcapit/fhe-ml:latest
docker run -p 8000:8000 xcapit/fhe-ml:latest

# Development with docker-compose
docker-compose --profile dev up
```

## Verification

### Python SDK

```python
from sdk.models import LinearRegression, FHEModel
from sdk import __version__

print(f"Xcapit FHE-ML SDK v{__version__}")

# Test model creation
model = FHEModel.LinearRegression(learning_rate=0.01)
print("Installation successful!")
```

### CLI

```bash
xcapit-fhe --version
xcapit-fhe --help
```

### API Server

```bash
xcapit-fhe-api
# Server starts at http://localhost:8000
# Docs at http://localhost:8000/docs
```

## Platform-Specific Notes

### macOS

```bash
# Install dependencies via Homebrew
brew install python@3.11 node
```

### Ubuntu/Debian

```bash
sudo apt update
sudo apt install python3.11 python3.11-venv nodejs npm
```

### Windows

Use Windows Subsystem for Linux (WSL2) for best compatibility:

```powershell
wsl --install -d Ubuntu
```

## Troubleshooting

### TenSEAL Installation Issues

If TenSEAL fails to install:

```bash
# Install build dependencies
pip install cmake pybind11

# Try installing TenSEAL separately
pip install tenseal --no-cache-dir
```

### Concrete-ML Issues

Concrete-ML requires specific versions:

```bash
pip install concrete-ml==1.5.0
```

## Next Steps

- [Quick Start Guide](05-quickstart.md)
- [ML Models Guide](03-ml-models.md)
- [Architecture Overview](01-architecture.md)

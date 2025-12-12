# Xcapit FHE-ML Platform

Privacy-preserving machine learning platform using Fully Homomorphic Encryption (FHE).

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)

## Overview

Xcapit FHE-ML enables machine learning on encrypted data. Train models and make predictions without ever exposing the underlying data - perfect for healthcare, finance, and any sensitive data applications.

```python
from sdk import FHEModel, SecureDataLoader, FHEContextManager

# Setup encryption
context = FHEContextManager()
context.generate_context(poly_modulus_degree=8192)

# Encrypt data
loader = SecureDataLoader(context)
encrypted_data = loader.encrypt_dataset(X, y)

# Train on encrypted data
model = FHEModel.LogisticRegression()
model.fit(encrypted_data)

# Predict on encrypted inputs
predictions = model.predict(encrypted_test)
```

## Features

- **4 ML Models**: LinearRegression, LogisticRegression, DecisionTree, KMeans
- **CKKS Encryption**: 128/192/256-bit security levels
- **Blockchain Audit**: Arbitrum integration for model verification
- **REST API**: FastAPI server for production deployments
- **CLI Tool**: Command-line interface for all operations
- **Docker Ready**: Multi-stage builds for dev/prod/fhe

## Installation

```bash
# Basic installation
pip install xcapit-fhe-ml

# With API support
pip install xcapit-fhe-ml[api]

# With FHE support (TenSEAL)
pip install xcapit-fhe-ml tenseal

# Development
pip install xcapit-fhe-ml[dev]
```

## Quick Start

### 1. CLI Usage

```bash
# Initialize FHE context
xcapit-fhe init --output ./workspace

# Encrypt data
xcapit-fhe encrypt -i data.csv -o encrypted.bin -t target_column

# Train model
xcapit-fhe train -m logistic-regression -d encrypted.bin -o model.bin

# Predict
xcapit-fhe predict -m model.bin -i test_encrypted.bin -o predictions.npy
```

### 2. Python SDK

```python
from sdk import (
    LinearRegression,
    LogisticRegression,
    DecisionTreeClassifier,
    KMeans,
    ModelConfig,
)

# Configure and train
config = ModelConfig(learning_rate=0.1, n_epochs=100)
model = LinearRegression(config=config)

# Train on plaintext (for development)
model._fit_plaintext(X_train, y_train)

# Evaluate
predictions = model._predict_plaintext(X_test)
```

### 3. REST API

```bash
# Start server
uvicorn sdk.api.server:app --reload

# Or with Docker
docker-compose up api
```

```bash
# Create model
curl -X POST http://localhost:8000/models \
  -H "Content-Type: application/json" \
  -d '{"model_type": "logistic_regression"}'

# Train
curl -X POST http://localhost:8000/models/{model_id}/train \
  -H "Content-Type: application/json" \
  -d '{"X": [[1,2,3], [4,5,6]], "y": [0, 1]}'

# Predict
curl -X POST http://localhost:8000/models/{model_id}/predict \
  -H "Content-Type: application/json" \
  -d '{"X": [[1,2,3]]}'
```

## Models

| Model | Task | FHE Compatible |
|-------|------|----------------|
| LinearRegression | Regression | ✅ |
| LogisticRegression | Binary Classification | ✅ |
| DecisionTreeClassifier | Classification | ✅ |
| DecisionTreeRegressor | Regression | ✅ |
| KMeans | Clustering | ✅ |
| MiniBatchKMeans | Large-scale Clustering | ✅ |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Xcapit FHE-ML Platform                  │
├─────────────────────────────────────────────────────────────┤
│  CLI (xcapit-fhe)  │  REST API (FastAPI)  │  Python SDK    │
├─────────────────────────────────────────────────────────────┤
│                        ML Models                            │
│  LinearRegression │ LogisticRegression │ DecisionTree │ KMeans │
├─────────────────────────────────────────────────────────────┤
│                     Encryption Layer                        │
│              CKKS (TenSEAL) │ Key Management               │
├─────────────────────────────────────────────────────────────┤
│                   Blockchain Integration                    │
│         ModelRegistry │ ComputationVerifier (Arbitrum)     │
└─────────────────────────────────────────────────────────────┘
```

## Docker

```bash
# Production API
docker-compose up api

# Development with hot reload
docker-compose --profile dev up

# With full FHE support
docker-compose --profile fhe up

# Run tests
docker-compose --profile test up

# Jupyter notebooks
docker-compose --profile jupyter up
```

## Blockchain Integration

Deploy smart contracts to Arbitrum for model verification:

```bash
# Set private key
export DEPLOYER_PRIVATE_KEY=0x...

# Deploy to testnet
python scripts/deploy_contracts.py --network arbitrum-sepolia

# Deploy to mainnet
python scripts/deploy_contracts.py --network arbitrum-one
```

### Smart Contracts

- **ModelRegistry**: Register models, save checkpoints, track training history
- **ComputationVerifier**: Audit trail for predictions, GDPR/HIPAA compliance

## Live Demo & Dashboard

Try the platform live at **[https://xcapit-privacy.vercel.app](https://xcapit-privacy.vercel.app)**

The dashboard includes:
- **Interactive Demos**: Watch FHE encryption and multi-party ML collaboration in action
- **Governance Dashboard**: Blockchain-backed audit trail, voting system, contribution tracking
- **Compliance Dashboard**: Automated GDPR/HIPAA/SOC2/PCI-DSS verification
- **Data Quality Score**: Quality metrics without accessing underlying data
- **Multi-language Support**: Spanish and English

### Running the Dashboard Locally

```bash
cd dashboard
npm install
npm run dev
```

## Examples

See the [examples/](examples/) directory:

- `01_quickstart.ipynb` - Getting started guide
- `02_linear_regression.ipynb` - Regression with sklearn comparison
- `03_healthcare_demo.ipynb` - Patient risk prediction (HIPAA compliant)
- `04_decision_tree_kmeans.ipynb` - Classification and clustering

## Benchmarks

```bash
# Run all benchmarks
python benchmarks/benchmark_models.py

# Specific models
python benchmarks/benchmark_models.py --models linear-regression logistic-regression

# Custom dataset sizes
python benchmarks/benchmark_models.py --sizes 100 500 1000 5000
```

## API Reference

### Models

```python
# Linear Regression
from sdk import LinearRegression, ModelConfig
model = LinearRegression(config=ModelConfig(learning_rate=0.01, n_epochs=100))

# Logistic Regression
from sdk import LogisticRegression
model = LogisticRegression()

# Decision Tree
from sdk import DecisionTreeClassifier, TreeConfig
model = DecisionTreeClassifier(config=TreeConfig(max_depth=4))

# K-Means
from sdk import KMeans, KMeansConfig
model = KMeans(config=KMeansConfig(n_clusters=3))
```

### Serialization

```python
from sdk.utils import save_model, load_model

# Save trained model
save_model(model, "model.pkl", metadata={"version": "1.0"})

# Load model
loaded_model = load_model("model.pkl")
```

### Encryption

```python
from sdk import FHEContextManager, CKKSEncryptor, SecurityLevel

# Create context
ctx = FHEContextManager()
ctx.generate_context(
    poly_modulus_degree=8192,
    security_level=SecurityLevel.TC128
)

# Encrypt/decrypt
encryptor = CKKSEncryptor(ctx)
encrypted = encryptor.encrypt_vector([1.0, 2.0, 3.0])
decrypted = encryptor.decrypt_vector(encrypted)
```

## Security

- **Encryption**: CKKS scheme with configurable security levels (128/192/256-bit)
- **Key Management**: Separate public/private keys, secure storage
- **Audit Trail**: Blockchain-based computation verification
- **Compliance**: HIPAA, GDPR, LGPD ready by design

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest tests/ -v`
5. Submit a pull request

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.

## About Xcapit

Built by the team behind [QuarkID](https://quarkid.org) (3.6M+ users), bringing enterprise-grade privacy to machine learning.

---

**Links**: [Documentation](docs/) | [Examples](examples/) | [API Docs](http://localhost:8000/docs)

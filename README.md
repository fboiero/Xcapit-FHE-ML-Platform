# Xcapit FHE-ML Platform

Privacy-preserving machine learning platform using Fully Homomorphic Encryption (FHE).

[![CI](https://github.com/xcapit/Xcapit-FHE-ML-Platform/actions/workflows/ci.yml/badge.svg)](https://github.com/xcapit/Xcapit-FHE-ML-Platform/actions/workflows/ci.yml)
[![CodeQL](https://github.com/xcapit/Xcapit-FHE-ML-Platform/actions/workflows/codeql.yml/badge.svg)](https://github.com/xcapit/Xcapit-FHE-ML-Platform/actions/workflows/codeql.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178c6.svg)](https://www.typescriptlang.org/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-566%20passing-brightgreen.svg)](#testing)
[![Security Audit](https://img.shields.io/badge/security-audited-blue.svg)](docs/SECURITY_AUDIT_REPORT.md)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![DCO](https://img.shields.io/badge/DCO-required-blue.svg)](DCO)

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

## Key Features

- **4 ML Models**: LinearRegression, LogisticRegression, DecisionTree, KMeans
- **CKKS Encryption**: 128/192/256-bit security levels with optimized FHE engine
- **Blockchain Audit**: Arbitrum integration for model verification and governance
- **Multi-Party Learning**: Consortium-based federated learning with contribution tracking
- **REST API**: FastAPI server with OpenAPI 3.1 documentation
- **TypeScript SDK**: Full-featured SDK for web applications
- **CLI Tool**: Command-line interface for all operations
- **Docker Ready**: Multi-stage builds for dev/prod/fhe
- **Compliance**: Built-in GDPR, HIPAA, SOC2, PCI-DSS verification

## Live Demo

Try the platform live at **[https://xcapit-privacy.vercel.app](https://xcapit-privacy.vercel.app)**

The dashboard includes:
- **Interactive Demos**: Watch FHE encryption and multi-party ML collaboration
- **Governance Dashboard**: Blockchain-backed audit trail, voting system, contribution tracking
- **Compliance Dashboard**: Automated regulatory verification
- **Data Quality Score**: Quality metrics without accessing underlying data
- **Multi-language Support**: Spanish and English

## Installation

### Python SDK

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

### TypeScript SDK

```bash
npm install @xcapit/fhe-ml-sdk
# or
yarn add @xcapit/fhe-ml-sdk
```

## Quick Start

### Python SDK

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
model._fit_plaintext(X_train, y_train)

# Evaluate
predictions = model._predict_plaintext(X_test)
```

### TypeScript SDK

```typescript
import { createClient, ModelType } from '@xcapit/fhe-ml-sdk';

const client = createClient({
  apiUrl: 'https://api.xcapit.io',
  apiKey: process.env.XCAPIT_API_KEY,
});

// Create a model
const model = await client.models.create({
  name: 'Credit Scoring Model',
  type: ModelType.LogisticRegression,
});

// Train the model
const result = await client.models.train({
  modelId: model.id,
  encryptedData: myEncryptedTrainingData,
  epochs: 100,
});

// Make predictions
const prediction = await client.predictions.predict({
  modelId: model.id,
  encryptedInput: encryptedFeatures,
});
```

### CLI Usage

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

### REST API

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

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Xcapit FHE-ML Platform                           │
├─────────────────────────────────────────────────────────────────────────┤
│   CLI (xcapit-fhe)  │  REST API (FastAPI)  │  TypeScript SDK  │ Python │
├─────────────────────────────────────────────────────────────────────────┤
│                            ML Models                                     │
│    LinearRegression │ LogisticRegression │ DecisionTree │ KMeans        │
├─────────────────────────────────────────────────────────────────────────┤
│                      Optimized FHE Engine                                │
│   CKKS (TenSEAL) │ Context Pooling │ Parallel Batch │ Lazy Evaluation   │
├─────────────────────────────────────────────────────────────────────────┤
│                      Blockchain Integration                              │
│  ModelRegistry │ ComputationVerifier │ ConsortiumGovernance (Arbitrum)  │
├─────────────────────────────────────────────────────────────────────────┤
│                         Compliance Layer                                 │
│              GDPR │ HIPAA │ SOC2 │ PCI-DSS │ LGPD                        │
└─────────────────────────────────────────────────────────────────────────┘
```

## Models

| Model | Task | FHE Compatible | Status |
|-------|------|----------------|--------|
| LinearRegression | Regression | ✅ | Production |
| LogisticRegression | Binary Classification | ✅ | Production |
| DecisionTreeClassifier | Classification | ✅ | Production |
| DecisionTreeRegressor | Regression | ✅ | Production |
| KMeans | Clustering | ✅ | Production |
| MiniBatchKMeans | Large-scale Clustering | ✅ | Production |

## Consortium Module

The platform includes a comprehensive consortium management system for multi-party machine learning:

| Module | Features |
|--------|----------|
| **Core** | Company management, consortium creation, membership, invitations |
| **Governance** | Proposals, voting system, audit trail (hash chain), reward distribution |
| **Compliance** | GDPR, HIPAA, SOC2, PCI-DSS frameworks with automated checks |
| **Data Quality** | Quality assessments, rules, alerts, dashboard |
| **Marketplace** | Model catalog, deployments, reviews, featured models |
| **Sandbox** | Testing environments, synthetic datasets, experiments |
| **Federated** | Inference endpoints, edge nodes, model deployment |
| **Explainability** | SHAP values, feature importance, decision paths, counterfactuals |
| **Competitive Insights** | Industry benchmarks, trend analysis, positioning |
| **Ensemble** | Multi-model ensembles (voting, averaging, weighted, stacking) |

```python
from sdk.api.consortium import ConsortiumManager

manager = ConsortiumManager()

# Create consortium
consortium = manager.create_consortium(
    name="Healthcare AI Consortium",
    description="Privacy-preserving medical ML",
    created_by="hospital_a",
    model_type="logistic_regression"
)

# Add governance proposal
proposal = manager.create_proposal(
    consortium_id=consortium.id,
    title="Add new member",
    proposal_type="add_member",
    created_by="hospital_a"
)

# Get compliance dashboard
dashboard = manager.get_compliance_dashboard(consortium.id)
```

## Documentation

| Document | Description |
|----------|-------------|
| [API Reference](docs/openapi.yaml) | OpenAPI 3.1 specification |
| [Security Audit](docs/SECURITY_AUDIT_REPORT.md) | Smart contract security audit |
| [Getting Started](docs/getting-started.md) | Quick start guide |
| [Architecture](docs/guides/01-architecture.md) | System architecture |
| [ML Models](docs/guides/03-ml-models.md) | Model documentation |
| [FHE Theory](docs/theory/) | Homomorphic encryption theory |

## Smart Contracts

Production-ready V2 contracts with security fixes:

| Contract | Purpose | Features |
|----------|---------|----------|
| [ModelRegistryV2](contracts/v2/ModelRegistryV2.sol) | Model registration | Trusted verifiers, checkpoints |
| [ComputationVerifierV2](contracts/v2/ComputationVerifierV2.sol) | Audit trail | Merkle proofs, batch verification |
| [ConsortiumGovernanceV2](contracts/v2/ConsortiumGovernanceV2.sol) | Multi-party governance | Pull-over-push rewards, DoS protection |

```bash
# Deploy to testnet
export DEPLOYER_PRIVATE_KEY=0x...
python scripts/deploy_contracts.py --network arbitrum-sepolia

# Deploy to mainnet (after audit)
python scripts/deploy_contracts.py --network arbitrum-one
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

## Testing

```bash
# Run all tests (566 passing)
pytest tests/ -v

# With coverage
pytest tests/ --cov=sdk --cov-report=html

# Specific test categories
pytest tests/test_models.py -v
pytest tests/test_api/ -v
pytest tests/test_blockchain/ -v
```

## Running the Dashboard

```bash
cd dashboard
npm install
npm run dev
```

## Benchmarks

```bash
# Run all benchmarks
python benchmarks/benchmark_models.py

# Specific models
python benchmarks/benchmark_models.py --models linear-regression logistic-regression

# Custom dataset sizes
python benchmarks/benchmark_models.py --sizes 100 500 1000 5000
```

## Security

- **Encryption**: CKKS scheme with configurable security levels (128/192/256-bit)
- **Key Management**: Separate public/private keys, secure storage
- **Audit Trail**: Blockchain-based computation verification
- **Smart Contracts**: [Security audit completed](docs/SECURITY_AUDIT_REPORT.md) with V2 secure contracts
- **Compliance**: HIPAA, GDPR, SOC2, PCI-DSS, LGPD ready by design

## Project Structure

```
xcapit-fhe-ml/
├── sdk/                    # Python SDK
│   ├── models/             # ML model implementations
│   ├── encryption/         # FHE encryption layer
│   ├── api/                # FastAPI server
│   │   ├── consortium/     # Modular consortium management
│   │   │   ├── core.py           # Company, Consortium, Membership
│   │   │   ├── governance.py     # Proposals, voting, audit, rewards
│   │   │   ├── compliance.py     # GDPR, HIPAA, SOC2, PCI-DSS
│   │   │   ├── data_quality.py   # Quality assessments & alerts
│   │   │   ├── marketplace.py    # Model marketplace
│   │   │   ├── sandbox.py        # Testing environments
│   │   │   ├── federated.py      # Federated inference & edge nodes
│   │   │   ├── explainability.py # SHAP, feature importance
│   │   │   ├── competitive_insights.py  # Industry benchmarks
│   │   │   └── ensemble.py       # Multi-model ensembles
│   │   └── *_routes.py     # API endpoints
│   ├── blockchain/         # Smart contract integration
│   └── quality/            # Data quality calculator
├── sdk-typescript/         # TypeScript SDK
│   └── src/
│       ├── client.ts       # API client
│       └── types.ts        # Type definitions
├── contracts/              # Solidity smart contracts
│   ├── v2/                 # Secure V2 contracts
│   └── *.sol               # Original contracts
├── dashboard/              # React dashboard
├── docs/                   # Documentation
├── tests/                  # Test suite (566 tests)
├── pilots/                 # Pilot implementations
│   └── gobierno/           # Government pilot (Córdoba)
├── examples/               # Jupyter notebooks
└── benchmarks/             # Performance benchmarks
```

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

**Links**: [Documentation](docs/) | [Examples](examples/) | [API Docs](docs/openapi.yaml) | [Live Demo](https://xcapit-privacy.vercel.app)

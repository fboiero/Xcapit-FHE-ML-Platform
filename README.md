# Xcapit Privacy — Data Consortium Platform

The platform where companies collaborate on data without sharing it. Form data consortiums, train joint ML models, and preserve total privacy with Fully Homomorphic Encryption (FHE).

[![CI](https://github.com/xcapit/Xcapit-FHE-ML-Platform/actions/workflows/ci.yml/badge.svg)](https://github.com/xcapit/Xcapit-FHE-ML-Platform/actions/workflows/ci.yml)
[![CodeQL](https://github.com/xcapit/Xcapit-FHE-ML-Platform/actions/workflows/codeql.yml/badge.svg)](https://github.com/xcapit/Xcapit-FHE-ML-Platform/actions/workflows/codeql.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Django 5.2](https://img.shields.io/badge/Django-5.2%20LTS-green.svg)](https://www.djangoproject.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178c6.svg)](https://www.typescriptlang.org/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-435%20passing-brightgreen.svg)](#testing)
[![Security Audit](https://img.shields.io/badge/security-audited-blue.svg)](docs/SECURITY_AUDIT_REPORT.md)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![DCO](https://img.shields.io/badge/DCO-required-blue.svg)](DCO)

## Overview

Xcapit Privacy enables organizations to form data consortiums where multiple companies train joint ML models without exposing their data to each other. Powered by Fully Homomorphic Encryption (FHE), the platform ensures cryptographic privacy throughout the entire lifecycle — from data contribution to model training to prediction.

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

- **Data Consortiums**: Multi-party collaboration with governance, voting, and contribution tracking
- **Cryptographic Privacy**: CKKS homomorphic encryption (128/192/256-bit security levels)
- **Blockchain Governance**: Arbitrum integration for audit trails, proposals, and verification
- **4 ML Models**: LinearRegression, LogisticRegression, DecisionTree, KMeans on encrypted data
- **Compliance**: Built-in GDPR, HIPAA, SOC2, PCI-DSS automated verification
- **REST API**: Django REST Framework with OpenAPI 3.0 documentation
- **CLI Tool**: Command-line interface for all operations
- **Docker Ready**: Multi-stage builds for dev/prod

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

### REST API (Django)

```bash
# Start development server
cd backend_django
python manage.py runserver

# Or with Docker
docker-compose up backend
```

```bash
# Get JWT token
curl -X POST http://localhost:8000/api/v2/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Create model (with auth)
curl -X POST http://localhost:8000/api/v2/models/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Model", "model_type": "logistic_regression"}'

# API Documentation
# Swagger UI: http://localhost:8000/api/v2/docs/
# OpenAPI Schema: http://localhost:8000/api/v2/schema/
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  Xcapit Privacy — Data Consortium Platform               │
├─────────────────────────────────────────────────────────────────────────┤
│   CLI (xcapit-fhe)  │  REST API (Django)   │  TypeScript SDK  │ Python │
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

```bash
# Create consortium via API
curl -X POST http://localhost:8000/api/v2/consortiums/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Healthcare AI Consortium",
    "description": "Privacy-preserving medical ML",
    "model_type": "logistic_regression"
  }'

# Create governance proposal
curl -X POST http://localhost:8000/api/v2/governance/proposals/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "consortium": "<consortium_id>",
    "title": "Add new member",
    "proposal_type": "add_member"
  }'

# Get compliance dashboard
curl http://localhost:8000/api/v2/compliance/assessments/ \
  -H "Authorization: Bearer <token>"
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
# Run Django backend tests (435 passing)
cd backend_django
pytest --cov=apps --cov-report=term-missing

# Run SDK library tests
cd ..
pytest tests/ -v

# Specific test categories
pytest tests/test_models.py -v          # ML models
pytest tests/test_encryption.py -v      # FHE encryption
pytest tests/test_blockchain.py -v      # Blockchain integration
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
├── backend_django/         # Django REST API (main backend)
│   ├── apps/               # Django applications
│   │   ├── core/           # Users, companies, API keys, audit
│   │   ├── consortiums/    # Consortium management
│   │   ├── governance/     # Blockchain governance
│   │   ├── compliance/     # Regulatory compliance (GDPR, HIPAA, etc.)
│   │   ├── marketplace/    # Model marketplace
│   │   ├── sandbox/        # Testing environments
│   │   ├── federated/      # Federated learning
│   │   ├── models/         # ML model management
│   │   ├── data_quality/   # Data quality assessment
│   │   ├── competitive_insights/  # Industry benchmarks
│   │   ├── ensemble/       # Ensemble methods
│   │   └── explainability/ # Model explainability (SHAP, etc.)
│   ├── config/             # Django settings
│   └── tests/              # Backend tests (435 tests)
├── sdk/                    # Python SDK (library only)
│   ├── models/             # ML model implementations
│   ├── encryption/         # FHE encryption layer (CKKS/TenSEAL)
│   ├── blockchain/         # Smart contract integration
│   ├── cli/                # Command-line interface
│   ├── quality/            # Data quality calculator
│   └── utils/              # Utilities
├── dashboard/              # React frontend (Vite + TailwindCSS)
├── contracts/              # Solidity smart contracts
│   └── src/v2/             # Secure V2 contracts
├── docs/                   # Documentation
├── tests/                  # SDK library tests
├── examples/               # Jupyter notebooks & demos
└── docker-compose.yml      # Full stack Docker setup
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

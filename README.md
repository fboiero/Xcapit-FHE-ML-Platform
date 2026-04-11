# Xcapit Privacy — Data Consortium Platform

The platform where companies collaborate on data without sharing it. Form data consortiums, train joint ML models, and preserve total privacy with 4 cryptographic layers: FHE, ZKP, MPC, and Differential Privacy.

[![CI](https://github.com/xcapit/Xcapit-FHE-ML-Platform/actions/workflows/ci.yml/badge.svg)](https://github.com/xcapit/Xcapit-FHE-ML-Platform/actions/workflows/ci.yml)
[![CodeQL](https://github.com/xcapit/Xcapit-FHE-ML-Platform/actions/workflows/codeql.yml/badge.svg)](https://github.com/xcapit/Xcapit-FHE-ML-Platform/actions/workflows/codeql.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Django 5.2](https://img.shields.io/badge/Django-5.2%20LTS-green.svg)](https://www.djangoproject.com/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-2,116%20passing-brightgreen.svg)](#testing)
[![Coverage](https://img.shields.io/badge/coverage-96.23%25-brightgreen.svg)](#testing)
[![Security Audit](https://img.shields.io/badge/security-audited-blue.svg)](docs/SECURITY_AUDIT_REPORT.md)

[Version en Espanol](README_ES.md)

## Overview

Xcapit Privacy enables organizations to form data consortiums where multiple companies train joint ML models without exposing their data to each other. Powered by 4 cryptographic layers, the platform ensures privacy throughout the entire lifecycle — from data contribution to model training to prediction.

```python
from sdk import CKKSEncryptor, CKKSParameters, SecurityLevel

# Setup encryption
params = CKKSParameters(
    poly_modulus_degree=8192,
    security_level=SecurityLevel.BITS_128,
)

# Encrypt data
encryptor = CKKSEncryptor(params)
encrypted = encryptor.encrypt_vector([1.0, 2.0, 3.0])

# Compute on encrypted data (no decryption needed)
result = encrypted + encrypted   # Homomorphic addition
result = encrypted * 2.5         # Scalar multiplication
```

## 4 Cryptographic Privacy Layers

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **FHE** | TenSEAL CKKS (128/192/256-bit) | Compute on encrypted data without decrypting |
| **ZKP** | Pedersen/Schnorr | Prove data properties without revealing data |
| **MPC** | Shamir/Pairwise Masking | Multi-party computation without centralizing data |
| **DP** | Laplace/Gaussian/Renyi | Calibrated noise for differential privacy guarantees |

## Key Features

- **Data Consortiums**: Multi-party collaboration with governance, voting, and contribution tracking
- **24+ ML Models**: LinearRegression, LogisticRegression, DecisionTree, KMeans, RandomForest, SVM, NeuralNetwork, and more
- **Blockchain Governance**: Arbitrum smart contracts for audit trails, proposals, and verification
- **Compliance**: Built-in GDPR, HIPAA, SOC2, PCI-DSS, ISO 27001 automated verification
- **REST API**: Django REST Framework with 391 endpoints and OpenAPI 3.0 documentation
- **Dashboard**: React 18 + Vite 5 with 45+ pages, bilingual (ES/EN)
- **CLI Tool**: Command-line interface for all operations
- **Docker Ready**: Multi-stage builds for dev/prod with health checks
- **Sandbox/Freemium**: Try without registration, 4 subscription tiers

## Live Demo

Try the platform live at **[https://xcapit-privacy.vercel.app](https://xcapit-privacy.vercel.app)**

The dashboard includes:
- **Interactive Demos**: Watch FHE encryption and multi-party ML collaboration
- **Governance Dashboard**: Blockchain-backed audit trail, voting system, contribution tracking
- **Compliance Dashboard**: Automated regulatory verification
- **Data Quality Score**: Quality metrics without accessing underlying data
- **Sandbox Mode**: Full platform demo without registration
- **Multi-language**: Spanish and English

## Installation

### Backend (Django)

```bash
cd backend_django
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Dashboard (React)

```bash
cd dashboard
npm install
npm run dev
```

### SDK

```bash
# Basic
pip install xcapit-fhe-ml

# With FHE support (TenSEAL)
pip install xcapit-fhe-ml tenseal

# With blockchain support (Web3)
pip install xcapit-fhe-ml web3
```

### Docker

```bash
# Full stack
docker compose --profile dev up

# Production
docker compose up
```

## Quick Start

### Python SDK

```python
from sdk import LinearRegression, ModelConfig

config = ModelConfig(learning_rate=0.01, n_epochs=100)
model = LinearRegression(config=config)
model._fit_plaintext(X_train, y_train)
predictions = model._predict_plaintext(X_test)
```

### CLI

```bash
xcapit-fhe init --output ./workspace
xcapit-fhe encrypt -i data.csv -o encrypted.bin -t target_column
xcapit-fhe train -m logistic-regression -d encrypted.bin -o model.bin
xcapit-fhe predict -m model.bin -i test_encrypted.bin -o predictions.npy
```

### REST API

```bash
# Get JWT token
curl -X POST http://localhost:8000/api/v2/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Create consortium
curl -X POST http://localhost:8000/api/v2/consortiums/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Healthcare AI", "model_type": "logistic_regression"}'
```

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                  Xcapit Privacy — Data Consortium Platform                │
├──────────────────────────────────────────────────────────────────────────┤
│  Dashboard (React)  │  REST API (Django)  │  SDK (Python)  │  CLI       │
├──────────────────────────────────────────────────────────────────────────┤
│                     4 Cryptographic Privacy Layers                       │
│   FHE (CKKS)  │  ZKP (Pedersen/Schnorr)  │  MPC (Shamir)  │  DP        │
├──────────────────────────────────────────────────────────────────────────┤
│                          24+ ML Models                                   │
│  Linear │ Logistic │ DecisionTree │ KMeans │ RF │ SVM │ NN │ Ensemble   │
├──────────────────────────────────────────────────────────────────────────┤
│                     Blockchain Integration (Arbitrum)                    │
│  ModelRegistry │ ComputationVerifier │ ConsortiumGovernance             │
├──────────────────────────────────────────────────────────────────────────┤
│                        Compliance & Governance                          │
│     GDPR │ HIPAA │ SOC2 │ PCI-DSS │ ISO 27001 │ Voting │ Audit        │
└──────────────────────────────────────────────────────────────────────────┘
```

## Platform Modules

| Module | Features |
|--------|----------|
| **Core** | Company management, JWT auth, API keys, audit logs, webhooks |
| **Consortiums** | CRUD, membership, invitations, contribution proofs |
| **Governance** | Proposals, weighted voting, audit trail (hash chain), rewards |
| **Compliance** | GDPR, HIPAA, SOC2, PCI-DSS frameworks with automated checks |
| **Data Quality** | Assessments, validation rules, alerts, dashboard |
| **Marketplace** | Model catalog, deployments, reviews, featured models |
| **Sandbox** | Testing environments, synthetic datasets, experiments, demos |
| **Federated** | Inference endpoints, edge nodes, model deployment |
| **Explainability** | SHAP values, feature importance, decision paths, insights |
| **Competitive Insights** | Industry benchmarks, trend analysis, positioning |
| **Ensemble** | Multi-model ensembles (voting, averaging, weighted, stacking) |
| **Blockchain** | Arbitrum transactions, smart contracts, on-chain verification |

## Smart Contracts

Production-ready V2 contracts with security fixes:

| Contract | Purpose | Features |
|----------|---------|----------|
| ModelRegistryV2 | Model registration | Trusted verifiers, checkpoints, training runs |
| ConsortiumGovernanceV2 | Multi-party governance | Commit-reveal voting, pull-over-push rewards |
| ComputationVerifierV2 | Computation verification | Proof validation, result caching |

## Testing

```bash
# Backend tests (1,496+ passing, 96.23% coverage)
cd backend_django
DJANGO_SETTINGS_MODULE=config.settings_test pytest --cov=apps --cov-fail-under=90

# SDK tests (620+ passing)
pytest sdk/tests/ -v

# Security tests (27 passing)
pytest tests/test_security_idor.py -v
```

## Documentation

| Document | Description |
|----------|-------------|
| [User Manual](docs/USER_MANUAL.md) | Complete user manual (Spanish) |
| [Release Notes RC1](docs/RELEASE_NOTES_RC1.md) | RC1 release notes |
| [API Reference](docs/openapi.yaml) | OpenAPI 3.0 specification |
| [Security Audit](docs/SECURITY_AUDIT_REPORT.md) | Security audit report |
| [Architecture](docs/guides/01-architecture.md) | System architecture |
| [FHE Theory](docs/theory/) | Homomorphic encryption theory (4 chapters) |
| [Onboarding Guide](docs/ONBOARDING_PASO_A_PASO.md) | Step-by-step onboarding |
| [ISO 27001](docs/compliance/) | ISO 27001 compliance |

## Pricing Tiers

| Feature | Free | Starter | Professional | Enterprise |
|---------|:----:|:-------:|:------------:|:----------:|
| Rate limit | 10/min | 100/min | 500/min | 2,000/min |
| Daily requests | 100 | 5,000 | 50,000 | Unlimited |
| Models | 2 | 10 | 50 | Unlimited |
| Consortiums | 1 | 5 | 20 | Unlimited |
| Upload limit | 50 MB | 1 GB | 10 GB | Unlimited |

## Project Structure

```
xcapit-fhe-ml/
├── backend_django/         # Django REST API (13 apps, 391 endpoints)
│   ├── apps/               # Django applications
│   ├── config/             # Django settings
│   └── tests/              # Backend tests (1,496+)
├── sdk/                    # Python SDK v0.7.0 (24+ models, 4 crypto layers)
│   ├── models/             # ML model implementations
│   ├── encryption/         # FHE encryption layer (CKKS/TenSEAL)
│   ├── zkp/                # Zero-Knowledge Proofs
│   ├── mpc/                # Multi-Party Computation
│   ├── privacy/            # Differential Privacy
│   ├── blockchain/         # Smart contract integration
│   └── cli/                # Command-line interface
├── dashboard/              # React 18 frontend (45+ pages, ES/EN)
├── contracts/              # Solidity smart contracts (Foundry)
│   └── src/v2/             # Secure V2 contracts
├── docs/                   # Documentation (43+ files)
├── examples/               # Jupyter notebooks (7)
└── docker-compose.yml      # Full stack Docker setup
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest --cov=apps`
5. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## License

AGPL v3 - See [LICENSE](LICENSE) for details.

## About Xcapit

Built by the team behind [QuarkID](https://quarkid.org) (3.6M+ users), bringing enterprise-grade privacy to machine learning.

---

**Links**: [Documentation](docs/) | [User Manual](docs/USER_MANUAL.md) | [Examples](examples/) | [API Docs](docs/openapi.yaml) | [Live Demo](https://xcapit-privacy.vercel.app)

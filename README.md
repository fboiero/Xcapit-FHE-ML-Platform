# Xcapit Privacy — Data Consortium Platform

The platform where companies collaborate on data without sharing it. Form data consortiums, train joint ML models, and preserve total privacy with 4 cryptographic layers: FHE, ZKP, MPC, and Differential Privacy.

[![CI](https://github.com/xcapit/Xcapit-FHE-ML-Platform/actions/workflows/ci.yml/badge.svg)](https://github.com/xcapit/Xcapit-FHE-ML-Platform/actions/workflows/ci.yml)
[![CodeQL](https://github.com/xcapit/Xcapit-FHE-ML-Platform/actions/workflows/codeql.yml/badge.svg)](https://github.com/xcapit/Xcapit-FHE-ML-Platform/actions/workflows/codeql.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Django 5.2](https://img.shields.io/badge/Django-5.2%20LTS-green.svg)](https://www.djangoproject.com/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-2,191%20passing-brightgreen.svg)](#testing)
[![Coverage](https://img.shields.io/badge/coverage-96.23%25-brightgreen.svg)](#testing)
[![Security Audit](https://img.shields.io/badge/security-audited-blue.svg)](docs/SECURITY_AUDIT_REPORT.md)
[![API Docs](https://img.shields.io/badge/API-OpenAPI%203.0-orange.svg)](#api-documentation)
[![Whitepaper](https://img.shields.io/badge/whitepaper-available-purple.svg)](docs/WHITEPAPER.md)

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

### One-Command Setup (recommended)

```bash
make setup    # creates venv, installs deps, configures everything
make dev      # starts full stack (Docker) — API, Dashboard, DB, Redis
```

### Python SDK

```python
from sdk.models import LinearRegression, FHELevel, ModelConfig
from sdk.encryption import CKKSEncryptor, CKKSParameters, SecurityLevel

# Train a model
model = LinearRegression(config=ModelConfig(learning_rate=0.01, n_epochs=100))
model.fit(X_train, y_train)

# Predict on encrypted data (FHE FULL — no decryption needed)
params = CKKSParameters(poly_modulus_degree=8192, security_level=SecurityLevel.BITS_128)
encryptor = CKKSEncryptor(params)
encrypted_input = encryptor.encrypt_vector(X_test[0])
encrypted_prediction = model.predict_encrypted(encrypted_input)

print(model.fhe_level)  # FHELevel.FULL
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

## API Documentation

Interactive API docs are available when the backend is running:

| URL | Format |
|-----|--------|
| `/api/v2/docs/` | **Swagger UI** — interactive API explorer |
| `/api/v2/redoc/` | **ReDoc** — clean API reference |
| `/api/v2/schema/` | **OpenAPI 3.0** YAML — import into Postman/Insomnia |

305 endpoints, 451 operations, 13 tagged groups, dual auth (JWT + API Key).

Schema also available at [docs/api-schema.yaml](docs/api-schema.yaml).

## Testing

```bash
make test           # Django backend (1,968 tests, 96.23% coverage)
make sdk-test       # SDK (195 tests — MPC, ZKP, DP, encryption)
make test-security  # Security tests (IDOR, SSRF, tenant isolation)
make e2e-test       # Playwright E2E (28 specs — auth, consortium, sandbox)
make perf-test      # Locust performance (SLO enforcement, 10 endpoints)
```

Full testing strategy: [docs/TESTING.md](docs/TESTING.md)

## Documentation

| Document | Description |
|----------|-------------|
| [Technical Whitepaper](docs/WHITEPAPER.md) | 4-layer crypto architecture, honest FHE assessment, comparison |
| [User Manual](docs/USER_MANUAL.md) | Complete user manual (Spanish) |
| [API Schema](docs/api-schema.yaml) | OpenAPI 3.0 specification (305 endpoints) |
| [Testing Strategy](docs/TESTING.md) | 4-layer testing pyramid with SLO targets |
| [Release Notes RC2](docs/RELEASE_NOTES_RC1.md) | Latest release notes |
| [Security Audit](docs/SECURITY_AUDIT_REPORT.md) | Security audit report |
| [ISO 27001](docs/compliance/) | ISO 27001 compliance documentation |
| [Design Partners](docs/design-partners/) | Pilot program kit for organizations |
| [Deployment Guide](deploy/terraform/README.md) | AWS deployment with Terraform |

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
├── sdk/                    # Python SDK (65 model classes, 4 crypto layers)
│   ├── models/             # 65 ML model implementations (4 FHE levels)
│   ├── encryption/         # FHE encryption layer (CKKS/TenSEAL)
│   ├── zkp/                # Zero-Knowledge Proofs (Pedersen/Schnorr/R1CS)
│   ├── mpc/                # Multi-Party Computation (Shamir/SecureAgg)
│   ├── privacy/            # Differential Privacy (DP-SGD, RDP accounting)
│   ├── blockchain/         # Smart contract integration (Arbitrum)
│   └── cli/                # Command-line interface
├── dashboard/              # React 18 frontend (45+ pages, ES/EN)
│   └── e2e/                # Playwright E2E tests (28 specs)
├── contracts/              # Solidity smart contracts (Foundry)
│   └── src/v2/             # Secure V2 contracts (3 contracts)
├── deploy/                 # Deployment infrastructure
│   ├── terraform/          # AWS IaC (VPC, ECS, RDS, Redis, ALB)
│   ├── aws/                # CodeBuild + ECS task definitions
│   ├── nginx/              # Production nginx config (TLS, rate limiting)
│   └── openbao/            # Secrets management (Vault alternative)
├── docs/                   # Documentation (50+ files)
│   ├── design-partners/    # Design Partners program kit (7 docs)
│   └── WHITEPAPER.md       # Technical whitepaper
├── examples/               # Jupyter notebooks (7)
├── Makefile                # 27+ targets (setup, dev, test, deploy, docs)
└── docker-compose.yml      # Full stack Docker setup (6 services)
```

## Deployment

### Docker (single host)

```bash
docker compose --profile dev up     # development
docker compose up                   # production
```

### AWS (Terraform)

```bash
cd deploy/terraform
cp terraform.tfvars.example terraform.tfvars  # fill in secrets
terraform init && terraform apply             # VPC + ECS + RDS + Redis + ALB
```

See [deploy/terraform/README.md](deploy/terraform/README.md) for full guide (~15 min to running platform).

## Design Partners

We're recruiting 3-5 organizations for our Design Partners program (banking, healthcare, insurance). 90-day pilot with full platform access and direct roadmap input.

See [docs/design-partners/](docs/design-partners/) for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests: `make test && make e2e-test`
4. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## License

AGPL v3 - See [LICENSE](LICENSE) for details.

## About Xcapit

Built by the team behind [QuarkID](https://quarkid.org) (3.6M+ users), bringing enterprise-grade privacy to machine learning.

Read our [Technical Whitepaper](docs/WHITEPAPER.md) for a deep dive into the 4-layer cryptographic architecture.

---

**Links**: [Documentation](docs/) | [User Manual](docs/USER_MANUAL.md) | [Examples](examples/) | [API Docs](docs/openapi.yaml) | [Live Demo](https://xcapit-privacy.vercel.app)

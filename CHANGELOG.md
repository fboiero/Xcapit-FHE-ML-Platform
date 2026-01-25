# Changelog

All notable changes to the Xcapit FHE-ML Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2026-01-25

### Changed

- **Backend Migration**: Migrated from FastAPI to Django 5.2 LTS
  - Full REST API now powered by Django REST Framework
  - JWT authentication with token blacklist support
  - OpenAPI 3.0 documentation at `/api/v2/docs/`
  - 435 tests passing with 88% coverage

- **SDK Refactored**: SDK is now a pure Python library (v0.2.0)
  - Removed `sdk/api/` directory (FastAPI server, routes, consortium logic)
  - CLI api_keys commands now redirect to Django API
  - Core functionality preserved: encryption, models, blockchain, utils

### Added

- **New Django Apps**:
  - `apps/data_quality/` - Data quality assessment and alerts
  - `apps/competitive_insights/` - Industry benchmarks and metrics
  - `apps/ensemble/` - Multi-model ensemble methods
  - `apps/explainability/` - Model explainability (SHAP, feature importance)

- **Infrastructure**:
  - Docker configuration updated for Django
  - Multi-stage Dockerfile with Python 3.12
  - Health checks and proper entrypoint scripts
  - Redis support for caching

- **Security**:
  - django-axes for brute-force protection
  - django-ratelimit for API rate limiting
  - JWT token blacklist for secure logout

### Removed

- `sdk/api/server.py` - FastAPI server
- `sdk/api/*_routes.py` - FastAPI route files (10 files)
- `sdk/api/consortium/` - Consortium logic (13 files, migrated to Django)
- `sdk/api/database.py` and `sdk/api/database_pg.py` - Direct DB access
- FastAPI-related tests (25+ test files)

### Migration Guide

API endpoints changed from FastAPI to Django:

```bash
# Old: uvicorn sdk.api.server:app
# New: cd backend_django && python manage.py runserver

# Authentication now required:
POST /api/v2/auth/token/ -> {"access": "...", "refresh": "..."}

# All endpoints under /api/v2/ with Bearer token auth
```

## [1.0.0] - 2025-12-13

### Added

#### Python SDK
- Linear Regression with FHE support (CKKS scheme)
- Logistic Regression with encrypted inference
- Decision Tree Classifier/Regressor
- KMeans and MiniBatchKMeans clustering
- Secure data loader with normalization
- Model serialization utilities
- Training history tracking
- FHE Model Factory pattern

#### REST API
- FastAPI-based REST API
- JWT authentication
- Model management endpoints (CRUD)
- Training and prediction endpoints
- Health check and versioning
- OpenAPI documentation

#### CLI
- Command-line interface (`xcapit-fhe`)
- Model training commands
- Prediction commands
- Configuration management

#### TypeScript SDK
- `@xcapit/fhe-ml-sdk` npm package
- Full API client coverage
- TypeScript definitions
- ESM and CJS builds

#### Dashboard
- React 18 + Vite + TypeScript
- Governance dashboard
- Compliance monitoring (GDPR, HIPAA, SOC2, PCI-DSS, LGPD)
- Data quality metrics
- Model explainability views
- Federated inference UI
- Multi-model ensemble
- Marketplace integration
- i18n support (English, Spanish)

#### Smart Contracts (V2)
- ModelRegistryV2.sol - Model registration on Arbitrum
- ComputationVerifierV2.sol - Proof verification
- ConsortiumGovernanceV2.sol - DAO governance
- Security audit completed (20 findings fixed)

#### Documentation
- README.md (English)
- README_ES.md (Spanish)
- Getting Started guide
- API Reference (OpenAPI)
- Architecture documentation
- FHE Theory documentation
- Security Audit Report

### Security
- ReentrancyGuard on all contracts
- DoS protection with MAX_MEMBERS limit
- Pull-over-push pattern for rewards
- Access control with Ownable2Step
- Input validation throughout
- Custom errors for gas efficiency

## [0.1.0] - 2025-10-01

### Added
- Initial project structure
- Basic Linear Regression model
- Prototype FHE integration
- Basic REST API

---

[Unreleased]: https://github.com/xcapit/Xcapit-FHE-ML-Platform/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/xcapit/Xcapit-FHE-ML-Platform/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/xcapit/Xcapit-FHE-ML-Platform/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/xcapit/Xcapit-FHE-ML-Platform/releases/tag/v0.1.0

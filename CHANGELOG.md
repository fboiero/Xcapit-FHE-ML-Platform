# Changelog

All notable changes to the Xcapit FHE-ML Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0-rc.1] - 2026-03-02

First release candidate. All 20 user stories (HU-01 to HU-20) implemented,
tested, and verified. Platform is feature-complete for v1.0.0.

### Added

#### FHE Encryption Layer (HU-01)
- CKKS encryption with TenSEAL (128/192/256-bit security levels)
- `FHEContextManager` for context lifecycle management
- Lazy TenSEAL import to avoid blocking non-FHE workflows

#### ML Models (HU-02, HU-15)
- 4 core FHE-compatible models: Linear Regression, Logistic Regression, Decision Tree, KMeans
- 6 advanced models: Neural Network, Random Forest, Gradient Boosting, SVM, Time Series, PCA
- Polynomial approximations for encrypted inference
- Ensemble methods (weighted, stacking, boosting)

#### Blockchain Integration (HU-03, HU-14)
- Arbitrum smart contracts (V2): ModelRegistry, ComputationVerifier, ConsortiumGovernance
- Backend blockchain services with OpenBao/Vault secret management
- Transaction recording and explorer URL generation

#### SDK (HU-04, HU-11)
- Python SDK v0.7.0 with CLI (`xcapit-fhe` commands)
- Encryption, training, prediction, blockchain, and API key commands
- Complete test suite for SDK routes

#### Dashboard (HU-05, HU-06, HU-07)
- React 18 + Vite 5 dashboard with auth flow and core pages
- 15+ feature pages: Governance, Compliance, Data Quality, Marketplace, Sandbox, etc.
- Vertical landing pages with i18n (ES/EN)
- TailwindCSS 3 with professional dark theme

#### Django Backend (HU-08, HU-09, HU-10, HU-12, HU-13)
- Django 5.2 LTS + DRF with JWT auth and service layer pattern
- 15 Django apps: core, consortiums, blockchain, data_quality, compliance, explainability, governance, ensemble, marketplace, federated, models, competitive_insights, sandbox
- Consortium management with governance, voting, and member lifecycle
- Compliance audit trails, marketplace, and sandbox experimentation
- Federated learning coordination and ML model management
- Data quality assessment, explainability (SHAP), ensemble methods

#### Infrastructure (HU-16, HU-17)
- Docker containerization with multi-stage builds (Python 3.12)
- Production-hardened: non-root user, read-only FS, health checks, tmpfs
- Gunicorn with 4 workers, Celery worker + beat, PostgreSQL 16, Redis 7
- CI/CD: GitHub Actions (10 jobs) + GitLab CI (9 jobs)
- Security scanning: pip-audit, safety, TruffleHog, container scanning

#### Security (HU-18)
- django-axes brute-force protection
- django-ratelimit API rate limiting
- JWT token blacklist for secure logout
- Removed hardcoded secret key fallback (now raises RuntimeError)
- Password min_length aligned to 12 across all validators
- MeView uses serializer validation instead of raw setattr

#### Testing & Coverage (HU-19, HU-20)
- 1,496 Django tests + ~620 SDK tests = ~2,116 total
- 96% code coverage (threshold: 90%)
- Full E2E integration test: 3-organization platform simulation across 7 acts
- Kanban board traceability document

### Fixed

- **Security**: Hardened auth, permissions, and frontend-backend alignment
- **Config**: Hardened configuration, aligned frontend endpoints
- **Data Quality**: Aligned rules and alerts endpoints with query param pattern
- **Frontend**: All API clients updated from `/api/v1` to `/api/v2`
- **Frontend**: Auth header changed from `X-API-Key` to `Authorization: ApiKey`
- **SDK**: TenSEAL import made lazy to unblock non-FHE tests
- **Auth**: RegisterSerializer now includes Company.email
- **Auth**: CreateAPIKeyView uses correct model fields (`created_by`, `prefix`)
- **Permissions**: Owner implicitly a member in `IsConsortiumMember`

### Dependencies

- Foundry contract dependencies: forge-std, openzeppelin-contracts v5.6.1

## [0.8.0] - 2026-01-29

### Added

- **Automatic Consortium Activation**: Consortiums now auto-activate when minimum member count is reached
  - Signal-based activation on membership changes
  - Email notification to owner when activated

- **Automatic Contribution Verification**: Contributions are verified automatically on creation
  - Validates SHA-256 hash format
  - Validates record count, feature count, schema version
  - Verifies contributor is active member
  - New `VerificationStatus` enum (pending, verified, failed)

- **Email Notification System**: Comprehensive email notifications for consortium events
  - Invitation emails with accept link
  - Invitation acceptance notifications
  - Consortium activation alerts
  - Training started/completed notifications
  - 5 responsive HTML email templates
  - Console backend for development, SMTP/SendGrid for production

- **Celery Training Tasks**: Real FHE model training via async tasks
  - `train_consortium_model` task with retry logic
  - `FHETrainingService` for training orchestration
  - Training progress tracking with `TrainingResult` model
  - `task_id` returned immediately for status polling

- **Blockchain Registration**: Immutable audit trail on Arbitrum
  - `BlockchainRegistrationService` for contributions and results
  - Automatic registration after verification
  - Transaction hash and timestamp stored
  - Explorer URL generation

- **Integration Tests**: Comprehensive E2E test suite
  - `test_complete_consortium_flow`: Full 3-hospital workflow
  - `test_serializers_return_ids`: Validates ID returns
  - `test_contribution_auto_verification`: Validates auto-verify
  - `test_consortium_auto_activation`: Validates auto-activation

### Changed

- **Serializers**: Create serializers now return `id` in response
  - `ConsortiumCreateSerializer`
  - `ContributionProofCreateSerializer`
  - `ConsortiumInvitationCreateSerializer`

- **Training Endpoint**: `/start_training/` now returns `task_id` and `training_result_id`

- **ContributionProof Model**: Added new fields
  - `verification_status` (enum)
  - `verification_message` (text)
  - `schema_version` (default "1.0")
  - `blockchain_registered_at` (datetime)

### New Files

- `apps/consortiums/signals.py` - Django signals for automation
- `apps/consortiums/tasks.py` - Celery async tasks
- `apps/consortiums/emails.py` - Email notification service
- `apps/consortiums/services/verification.py` - Verification logic
- `apps/consortiums/services/training.py` - FHE training service
- `apps/consortiums/services/blockchain.py` - Blockchain registration
- `templates/emails/*.html` - 5 email templates
- `tests/integration/test_consortium_flow.py` - E2E tests

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

[Unreleased]: https://github.com/xcapit/Xcapit-FHE-ML-Platform/compare/v1.0.0-rc.1...HEAD
[1.0.0-rc.1]: https://github.com/xcapit/Xcapit-FHE-ML-Platform/compare/v0.8.0...v1.0.0-rc.1
[0.8.0]: https://github.com/xcapit/Xcapit-FHE-ML-Platform/compare/v2.0.0...v0.8.0
[2.0.0]: https://github.com/xcapit/Xcapit-FHE-ML-Platform/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/xcapit/Xcapit-FHE-ML-Platform/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/xcapit/Xcapit-FHE-ML-Platform/releases/tag/v0.1.0

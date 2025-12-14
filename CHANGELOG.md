# Changelog

All notable changes to the Xcapit FHE-ML Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub issue and PR templates
- Pre-commit hooks configuration
- EditorConfig for consistent formatting

### Changed
- Updated documentation for open source best practices

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

[Unreleased]: https://github.com/xcapit/Xcapit-FHE-ML-Platform/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/xcapit/Xcapit-FHE-ML-Platform/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/xcapit/Xcapit-FHE-ML-Platform/releases/tag/v0.1.0

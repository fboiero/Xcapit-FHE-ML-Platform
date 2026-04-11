# Changelog

All notable changes to Xcapit FHE-ML Platform will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0-rc1] - 2026-03-14

### Added

#### 4 Cryptographic Privacy Layers
- **FHE (Fully Homomorphic Encryption)**: TenSEAL CKKS scheme with 128/192/256-bit security levels
- **ZKP (Zero-Knowledge Proofs)**: Pedersen commitments, Schnorr proofs, contribution proofs, arithmetic circuits, on-chain serialization
- **MPC (Multi-Party Computation)**: Shamir Secret Sharing (secp256k1), SecureAggregator with pairwise masking, ThresholdDecryptor, KeyCeremony DKG
- **Differential Privacy**: Laplace/Gaussian/Exponential mechanisms, Renyi DP accountant, DP-SGD trainer, gradient clipping, subsampled amplification

#### SDK (v0.7.0)
- Complete `sdk/zkp/` module: proofs, circuits, on-chain serialization
- Complete `sdk/mpc/` module: secret sharing, secure aggregation, threshold decryption
- Complete `sdk/privacy/` module: mechanisms, accountant, DP data loader, DP-SGD trainer
- 24+ ML models (LinearRegression, LogisticRegression, DecisionTree, KMeans, RandomForest, SVM, NeuralNetwork, etc.)
- Data preprocessing: scalers, encoders, imputers, transformers
- Evaluation: metrics calculator, cross-validation, grid/random search
- Feature engineering, selection, and outlier detection
- ML pipeline composition and model persistence
- Blockchain connector with Arbitrum support (One/Sepolia, Ethereum Mainnet/Sepolia)
- CLI tool: encryption, training, prediction, blockchain, benchmarking
- 620+ SDK tests

#### Django Backend (13 apps, 35+ models, 391 endpoints)
- **core**: Users, companies, API keys, webhooks, audit logs, reports, workflows, scheduled tasks
- **consortiums**: Consortium CRUD, membership, invitations, contribution proofs, training results
- **governance**: Proposals, voting (weighted by contributions), audit trail (hash chain), reward distribution
- **marketplace**: Model catalog, deployments, reviews, featured/popular/top-rated
- **compliance**: GDPR/HIPAA/SOC2/PCI-DSS frameworks, checks, reports, attestations, DPR
- **data_quality**: Quality assessments, validation rules, alerts, dashboard
- **federated**: Federated models, inference endpoints, edge nodes
- **ensemble**: Multi-model ensembles (voting, averaging, weighted, stacking)
- **explainability**: SHAP values, feature importance, decision paths, model insights
- **competitive_insights**: Industry benchmarks, trend analysis, competitive reports
- **sandbox**: Trial environments, synthetic datasets, experiments, lead capture
- **blockchain**: Transaction tracking, smart contract registry, on-chain operations
- Crypto service layer: CryptoService, MPCService, PrivacyService
- 7 crypto API endpoints: ZKP verification, MPC setup/aggregation, DP privatization/budget
- JWT auth with token blacklist, django-axes, django-ratelimit
- Tier-based access control (free/starter/professional/enterprise)
- Service layer pattern (BaseService/ServiceResult) for all business logic
- 1,496+ Django tests, 96.23% coverage

#### Dashboard Frontend (45+ pages)
- Authentication: login, register, user settings
- Core: main dashboard, consortium create/detail/join, data upload/explorer
- ML: model builder, training dashboard, metrics, comparison, deployment, results
- Governance: proposals, voting, audit trail viewer
- Compliance: regulatory status, automated checks
- Advanced: marketplace, federated inference, explainability, competitive insights, ensemble
- Operations: real-time monitoring, notification center, workflow automation, report builder
- Admin: admin panel, team management, billing, API playground
- Sandbox: demo mode with guided onboarding, industry-specific demos (bank, retail, insurance)
- Bilingual support (ES/EN) via react-i18next
- Error boundary, skeleton loading, API error components, 404 page

#### Smart Contracts (Solidity 0.8.20 / Foundry)
- **ModelRegistryV2**: Model registration, checkpoints, training runs, trusted verifiers
- **ConsortiumGovernanceV2**: Multi-member governance, commit-reveal voting, contribution tracking, pull-over-push rewards
- **ComputationVerifierV2**: On-chain ZKP verification, computation proof validation
- Reentrancy guards, pausable, two-step ownership, custom errors
- Full test suite + security edge cases

#### Infrastructure
- Docker multi-stage builds with non-root user and health checks
- GitHub Actions CI (10 jobs) + GitLab CI (9 jobs)
- Pre-commit hooks (ruff, black, pytest)
- Sentry integration for error monitoring
- PostgreSQL + Redis + Celery async task processing
- OpenBao for secret management

#### Documentation
- 43+ documentation files in `/docs/`
- 4 FHE theory chapters
- 5 architecture/installation guides
- 21 SVG architectural diagrams
- 7 Jupyter notebook examples
- ISO 27001 compliance documentation
- OpenAPI 3.0 specification
- ADR (Architecture Decision Records)
- Traceability matrix with user stories

### Security Fixes (RC1 Hardening)

#### CRITICAL — Privilege Escalation
- **Tier upgrade without payment**: `TrialService.request_upgrade()` now creates PENDING subscription instead of directly changing tier; actual upgrade requires `confirm_upgrade()` with payment gateway validation

#### HIGH — IDOR (Insecure Direct Object Reference)
- **IsConsortiumMember bypass via query params**: Permission returned `True` for list views without `pk` in kwargs, allowing any user to read data from any consortium via `?consortium_id=`
- **GovernanceConfigViewSet**: Non-members could read governance config — now scoped to user's consortiums
- **ProposalViewSet**: Non-members could list proposals — now membership-validated in `get_queryset()`
- **AuditEventViewSet**: Non-members could read full audit trail — now membership-validated
- **RewardDistributionViewSet**: Non-members could see reward distributions — now membership-validated
- **DeploymentViewSet**: Non-members could list deployments — now membership-validated
- **Marketplace purchase()**: Non-members could deploy models to foreign consortiums — consortium membership check added
- **6 serializers** (governance, marketplace, data_quality, compliance, explainability): Added `validate_consortium()` blocking non-member writes

#### HIGH — Tenant Isolation
- **FeatureImportanceViewSet**: Fell through to `.objects.all()` exposing all consortiums' data — now scoped to user's consortiums
- **ModelInsightViewSet**: Same `.objects.all()` fallback — now scoped to user's consortiums

#### HIGH — SSRF Prevention
- **WebhookCreateSerializer**: Added `validate_url()` blocking localhost, 127.0.0.1, metadata endpoints (169.254.x.x), private IPs via DNS rebinding, non-HTTP schemes

#### HIGH — Cryptographic Fixes (SDK)
- **ZKP timing attack**: Replaced Python `==` with `hmac.compare_digest()` in Pedersen/Schnorr verification
- **Schnorr proof forgery**: Added subgroup membership validation (rejects Y=1 trivial forgery)
- **Non-crypto PRNG**: DP mechanisms replaced `np.random` (Mersenne Twister) with `secrets`-backed CSPRNG
- **Privacy budget bug**: `delta=0` (pure epsilon-DP) no longer immediately triggers `is_exhausted`

#### MEDIUM — Input Validation
- **Sandbox extension negative days**: Now validates `1 <= days <= 30` with type checking
- **ALLOWED_HOSTS in test settings**: Changed from `["*"]` to `["localhost", "127.0.0.1", "testserver"]`
- **Audit trail verify endpoint**: Added consortium membership check
- **Reward distribute endpoint**: Added consortium membership check

#### Previously Fixed (v0.7.0 → RC1)
- Removed hardcoded fallback secret key (raises RuntimeError)
- Consortium permission hardening (owner implicit membership)
- Password min_length aligned to 12 across all validators
- MeView uses serializer validation instead of raw setattr
- RegisterSerializer.create() missing Company.email field
- CreateAPIKeyView using non-existent model fields
- API clients updated from `/api/v1` to `/api/v2`
- Auth header changed from `X-API-Key` to `Authorization: ApiKey`
- TenSEAL lazy imports preventing SDK load without optional dep
- Migration dependency chain conflicts resolved

### Security Tests
- 27 security tests covering IDOR, SSRF, tenant isolation, privilege escalation, and input validation
- TestIDORConsortiumValidation (6 tests): serializer-level consortium membership blocking
- TestSSRFPrevention (6 tests): webhook URL validation against internal networks
- TestIDORViewQueryParamBypass (6 tests): ViewSet queryset-level membership enforcement
- TestTenantIsolation (4 tests): explainability views tenant scoping
- TestTierUpgradeProtection (3 tests): payment verification for tier upgrades
- TestSandboxExtensionValidation (2 tests): negative/zero days rejection

## [0.7.0] - 2026-02-15

### Added
- Initial FHE encryption pipeline with CKKS scheme
- Core consortium management (CRUD, membership, invitations)
- Federated learning training loop
- Basic dashboard with authentication flow
- SDK v0.7.0 with encryption module

# Project Overview

Xcapit FHE-ML Platform: privacy-preserving machine learning using Fully Homomorphic Encryption (FHE). Enables ML on encrypted data without exposing underlying information. Targets healthcare, finance, government, and sensitive data verticals.

## Project Structure

```
/
├── backend_django/             # Django 5.2 LTS backend (main API)
│   ├── config/                 # Settings, URLs, WSGI, Celery
│   ├── apps/                   # 13 Django applications
│   ├── tests/                  # 1,442+ tests (95% coverage)
│   ├── Dockerfile              # Multi-stage production build
│   └── requirements.txt        # Python dependencies
├── sdk/                        # Python SDK v0.2.0 (pure library)
│   ├── encryption/             # TenSEAL CKKS encryption/decryption
│   ├── models/                 # FHE-aware ML model implementations
│   ├── blockchain/             # Web3/Arbitrum + DAO governance
│   ├── cli/                    # CLI tools (xcapit-fhe command)
│   ├── quality/                # Data quality calculators
│   └── utils/                  # Common utilities
├── dashboard/                  # React 18 + Vite 5 frontend
│   ├── src/pages/              # Page components
│   ├── src/components/         # UI components (ui/, sandbox/)
│   ├── src/api/                # API client functions
│   ├── src/i18n/               # Translations (ES/EN)
│   └── src/context/            # React Context (DemoContext)
├── contracts/                  # Solidity smart contracts (Foundry)
│   └── src/v2/                 # ConsortiumGovernance, ModelRegistry, ComputationVerifier
├── docs/                       # Technical documentation (40+ files)
└── docker-compose.yml          # Full stack (postgres, redis, django, celery, openbao)
```

## Django Apps Map

| App | Responsibility |
|-----|----------------|
| `core` | User, Company, APIKey, AuditLog, Webhook, Report, Workflow, ScheduledTask |
| `consortiums` | Consortium, ConsortiumMember, ContributionProof, TrainingResult, ConsortiumInvitation |
| `models` | MLModel, ModelVersion, TrainingRun, PredictionLog, BatchPredictionJob, ModelExport, ModelShare |
| `governance` | Proposals, Voting (blockchain DAO governance) |
| `compliance` | Regulatory compliance tracking |
| `marketplace` | Model marketplace and sharing |
| `sandbox` | Testing sandbox environment |
| `federated` | Federated learning, InferenceEndpoint |
| `data_quality` | QualityAssessment, QualityRule, QualityAlert |
| `competitive_insights` | IndustryBenchmark, CompanyMetric, CompetitiveReport |
| `ensemble` | Ensemble model configurations |
| `explainability` | ExplanationRequest, ModelInsight (SHAP) |
| `blockchain` | Blockchain services, contract interactions, key management |

## Multi-Tenancy Model

```
User → Company → [all resources]
```

Every resource is scoped to a Company. All queries MUST filter by `request.user.company`. Users cannot access other companies' resources.

## Key URLs

- **Frontend**: https://appfhe.xcapit.com (Vercel)
- **API**: https://apifhe.xcapit.com
- **Swagger**: /api/v2/docs/
- **Schema**: /api/v2/schema/
- **Health**: /health/, /health/live/, /health/ready/

## Landing Pages Design System

Each vertical landing page follows: Hero → Stats → How It Works → Use Cases → Compliance Badges → Contact Form.

Color themes:
- **Hub**: Gradient purple/blue
- **Fintech**: `blue-500` / `indigo-600`
- **Healthcare**: `emerald-500` / `teal-600`
- **Government**: `slate-600` / `gray-700`
- **Other Industries**: `purple-500` / `indigo-600`

## Known Bugs (Pre-existing, Not Yet Fixed)

1. `core/serializers.py` — `RegisterSerializer.create()` calls `Company.objects.create(name=...)` without setting `Company.email` (unique+required) → IntegrityError
2. `core/views.py` — `CreateAPIKeyView.post()` uses `created_by` and `prefix` in `APIKey.objects.create()` but model lacks those fields → TypeError
3. `core/authentication.py` — `APIKeyAuthentication.authenticate()` does `select_related("company", "created_by")` but `APIKey` has no `created_by` field
4. `federated/views.py:140` — `endpoint.model.version` should be `endpoint.model.current_version` → AttributeError

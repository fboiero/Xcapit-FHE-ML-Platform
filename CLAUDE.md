# Xcapit FHE-ML Platform - Claude Context

## Project Overview

Privacy-preserving machine learning platform using Fully Homomorphic Encryption (FHE). Enables ML on encrypted data without exposing underlying information - targeting healthcare, finance, government, and other sensitive data verticals.

## Tech Stack

### Backend (Python - Django)
- **Framework**: Django 5.2 LTS (supported until April 2028) + Django REST Framework
- **Database**: PostgreSQL (required in production), Redis for caching
- **FHE Engine**: TenSEAL (CKKS scheme) - 128/192/256-bit security
- **Blockchain**: Arbitrum integration for audit trails (Web3.py)
- **Authentication**: JWT (djangorestframework-simplejwt) with token blacklist
- **Security**: django-axes (brute-force protection), django-ratelimit
- **Testing**: pytest-django (1,258+ tests, 93% coverage)
- **Deployment**: Docker + docker-compose, Gunicorn + WhiteNoise

### Frontend (React/Vite)
- **Framework**: React 18 + Vite 5
- **Styling**: TailwindCSS 3
- **i18n**: react-i18next (ES/EN)
- **State**: React Context (DemoContext)
- **Forms**: Web3Forms API for contact submissions
- **Deployment**: Vercel

### Smart Contracts (Solidity)
- ConsortiumGovernance.sol - Voting and member management
- ModelRegistry.sol - Model versioning and verification
- ComputationVerifier.sol - Proof verification

## Project Structure

```
/
├── backend_django/             # Django backend (main API)
│   ├── config/                 # Django settings & configuration
│   │   ├── settings.py         # Main settings
│   │   ├── settings_test.py    # Test settings
│   │   ├── urls.py             # URL routing
│   │   └── wsgi.py             # WSGI application
│   ├── apps/                   # Django applications
│   │   ├── core/               # Users, companies, API keys, audit
│   │   ├── consortiums/        # Consortium management
│   │   ├── governance/         # Blockchain governance
│   │   ├── compliance/         # Regulatory compliance
│   │   ├── marketplace/        # Model marketplace
│   │   ├── sandbox/            # Testing sandbox
│   │   ├── federated/          # Federated learning
│   │   ├── models/             # ML model management
│   │   ├── data_quality/       # Data quality assessment
│   │   ├── competitive_insights/ # Competitive analysis
│   │   ├── ensemble/           # Ensemble methods
│   │   └── explainability/     # Model explainability
│   ├── tests/                  # Test files
│   ├── docker-entrypoint.sh    # Docker entrypoint
│   ├── Dockerfile              # Production Dockerfile
│   └── requirements.txt        # Python dependencies
├── sdk/                        # Python SDK (FHE models, encryption)
├── api/                        # Legacy FastAPI backend (deprecated)
├── dashboard/                  # React frontend
│   ├── src/
│   │   ├── pages/              # Page components
│   │   ├── components/         # UI components
│   │   ├── api/                # API client functions
│   │   ├── i18n/               # Translations
│   │   └── context/            # React context
│   └── public/videos/          # Demo videos (es/en)
├── contracts/                  # Solidity smart contracts
├── docs/                       # Documentation
└── docker-compose.yml          # Full stack Docker setup
```

## Django App Architecture

Each app follows this structure:
```
apps/example_app/
├── __init__.py
├── models.py           # Django models
├── serializers.py      # DRF serializers
├── views.py            # ViewSets and API views
├── urls.py             # URL routing
├── permissions.py      # Custom permissions
├── filters.py          # Django-filter filtersets
├── services/           # Business logic (service layer)
│   ├── __init__.py
│   └── example.py      # Service classes
├── migrations/         # Database migrations
└── tests.py            # App-specific tests
```

### Service Layer Pattern

Business logic is encapsulated in service classes:

```python
from apps.core.services.base import BaseService, ServiceResult

class ExampleService(BaseService):
    """Service for example operations."""

    def process(self, data: dict) -> ServiceResult[Model]:
        # Validate
        if not data.get("field"):
            return ServiceResult.fail("Field is required", error_code="validation_error")

        # Process
        result = Model.objects.create(**data)

        # Audit log (if request available)
        if self.request:
            AuditService.log_from_request(
                self.request,
                action="created",
                resource_type="model",
                resource_id=result.id,
            )

        return ServiceResult.ok(result)
```

### Key Services

- `apps.core.services.AuditService` - Audit logging
- `apps.consortiums.services.ConsortiumService` - Consortium operations
- `apps.consortiums.services.MemberService` - Member management
- `apps.data_quality.services.QualityAssessmentService` - Data quality scoring

## Key URLs

- **Platform App (Frontend)**: https://appfhe.xcapit.com (Vercel)
- **API (Backend)**: https://apifhe.xcapit.com (DNS pending)
- **API Docs**: /api/v2/docs/ (Swagger UI)
- **API Schema**: /api/v2/schema/

Note: The commercial website (privacy.xcapit.com) is in a separate repository.

## Development Commands

```bash
# Backend Django
cd backend_django
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run development server
python manage.py runserver

# Run tests
pytest --cov=apps --cov-report=term-missing

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Dashboard
cd dashboard
npm install
npm run dev          # Dev server (localhost:5173)
npm run build        # Production build
vercel --prod --yes  # Deploy to Vercel

# Docker (Full Stack)
docker-compose up --build
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Environment Variables

Backend requires these environment variables:

```bash
# Required
DJANGO_SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://localhost:6379/0

# Optional
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=https://your-frontend.com
JWT_SIGNING_KEY=separate-jwt-key  # Falls back to SECRET_KEY
FHE_SECURITY_LEVEL=128  # 128, 192, or 256
SENTRY_DSN=https://...@sentry.io/...
```

## Testing Configuration

```python
# config/settings_test.py
# Uses SQLite for speed, disables rate limiting and caching

# Run tests:
DJANGO_SETTINGS_MODULE=config.settings_test pytest

# With coverage:
pytest --cov=apps --cov-report=html
```

## API Authentication

JWT Bearer token authentication:

```bash
# Obtain tokens
POST /api/v2/auth/token/
{"email": "user@example.com", "password": "password"}

# Use access token
Authorization: Bearer <access_token>

# Refresh token
POST /api/v2/auth/token/refresh/
{"refresh": "<refresh_token>"}

# Logout (blacklist token)
POST /api/v2/auth/logout/
{"refresh": "<refresh_token>"}
```

## REST API Standards

- Pagination: `?page=1&page_size=50` (max 200)
- Filtering: Django-filter with `?field=value`
- Ordering: `?ordering=-created_at`
- Search: `?search=term`

Error responses follow RFC 7807 format:
```json
{
  "error": {
    "code": "validation_error",
    "message": "Human-readable message",
    "status": 400,
    "details": {"field": ["error message"]}
  }
}
```

## FHE Technical Details

- **Scheme**: CKKS (Cheon-Kim-Kim-Song) for approximate arithmetic
- **Security Levels**: 128, 192, 256 bits
- **Supported Models**: LinearRegression, LogisticRegression, DecisionTree, KMeans
- **Key Features**:
  - Encrypt data client-side
  - Train/predict on encrypted data server-side
  - Decrypt results client-side only
  - Multi-party consortium support

## Landing Pages Design System

Each vertical landing page follows this structure:
1. **Hero Section** - Animated SVG illustration + headline + CTA
2. **Stats Section** - 3 key metrics with icons
3. **How It Works** - 4-step process
4. **Use Cases** - 3 cards with specific applications
5. **Compliance Badges** - Industry-specific certifications
6. **Contact Form** - Web3Forms integration

### Color Themes by Vertical
- **Hub**: Gradient purple/blue
- **Fintech**: Blue/Indigo (`blue-500`, `indigo-600`)
- **Healthcare**: Emerald/Teal (`emerald-500`, `teal-600`)
- **Government**: Slate/Gray (`slate-600`, `gray-700`)
- **Other Industries**: Purple/Indigo (`purple-500`, `indigo-600`)

## Notes for Future Sessions

- Backend migrated from FastAPI to Django 5.2 LTS (January 2026)
- 1,258 Django tests passing, 93% coverage
- Docker build produces ~654MB image, uses multi-stage build
- Build takes ~3 minutes, produces warning about chunk size >500KB (acceptable)
- Vercel deployment is automatic on push to main
- User prefers Spanish communication
- Design feedback: Should look professional, like a security/privacy company
- Always use type hints in new Python code
- Follow service layer pattern for business logic
- Run `pytest` before committing to ensure tests pass

---

## Estado Actual del Plan de Migración (Enero 2026)

### Progreso General
La migración de FastAPI a Django está **~95% completada**.

### ✅ COMPLETADO

#### Fase 1: Apps Django Creadas
- `apps/data_quality/` - Evaluación de calidad de datos
- `apps/competitive_insights/` - Benchmarks de industria
- `apps/ensemble/` - Modelos multi-ensemble
- `apps/explainability/` - Explicabilidad de modelos (SHAP, etc.)
- Apps agregadas a `INSTALLED_APPS`
- Migraciones creadas y ejecutadas

#### Fase 2: Lógica de Negocio Migrada
- Modelos Django creados para todas las apps
- Serializers DRF implementados
- ViewSets y vistas API creadas
- URLs configuradas en `config/urls.py`
- Service layer pattern implementado

#### Fase 3: SDK Limpio (25 Enero 2026)
- Eliminado `sdk/api/` completo (FastAPI, rutas, database, consortium)
- SDK actualizado a versión 0.2.0
- CLI `api_keys` actualizado para mostrar mensaje de migración
- SDK ahora es librería pura: encryption, models, blockchain, utils, cli

#### Fase 4: Tests Actualizados
- Tests de FastAPI eliminados (15+ archivos)
- Tests de CLI actualizados para nuevo comportamiento
- Tests de SDK (librería) mantenidos: encryption, models, blockchain, utils

#### Fase 5: Configuración Docker
- Dockerfile actualizado a Python 3.12
- `docker-entrypoint.sh` con manejo de migraciones
- Health checks configurados
- `docker-compose.yml` mejorado

### ✅ COMPLETADO

#### Fase 6: Documentación (25 Enero 2026)
- [x] Actualizar README.md principal (Django en lugar de FastAPI)
- [x] Actualizar CHANGELOG.md con versión 2.0.0
- [x] Ejecutar suite completa de tests (1,258 pasando, 93% coverage)

### Estructura Final del SDK
```
sdk/
├── __init__.py       # v0.2.0
├── blockchain/       # Integración blockchain
├── cli/              # CLI tool (api_keys migrado)
├── encryption/       # FHE/CKKS
├── models/           # Modelos ML
├── quality/          # Calculadores
├── utils/            # Utilidades
└── monitoring.py     # Métricas
```

### Archivos de Referencia
- `MIGRATION_PLAN.md` - Plan detallado de migración
- `dashboard/MARKETING_PLAN.md` - Plan de marketing y validación

### Migración Completada
La migración de FastAPI a Django está **100% completada**.

- SDK versión 0.2.0 (librería pura)
- Django backend con 1,258 tests pasando (93% coverage)
- Documentación actualizada (README, CHANGELOG)

---

## Estado Actual (2 Febrero 2026)

### CI/CD
- **GitLab CI**: Pipeline verde (9/9 jobs)
- **GitHub Actions**: Pipeline verde (10/10 jobs) — repo: `fboiero/Xcapit-FHE-ML-Platform`
- **GitHub remote**: `github` → `https://github.com/fboiero/Xcapit-FHE-ML-Platform.git`
- **GitLab remote**: `origin` → `git@gitlab.com:xcapit/privacy-platform.git`
- Ambos pipelines corren en push a main
- `--cov-fail-under` subido de 75 → 80 → **90** en ambos pipelines
- CodeQL action actualizado de v3 a **v4** en ci.yml y codeql.yml

### Tests y Coverage
- **Django tests**: 1,258 tests pasando, **93% coverage** (`--cov-fail-under=90` en CI)
- **SDK tests root** (`tests/` + `sdk/tests/`): ~620 tests pasando
- **Total**: ~1,878 tests

### Historial de Coverage
- **77% → 80%**: 115 tests (consortium services, quality assessment, competitive emails, coverage boost)
- **80% → 84%**: 116 tests (FHE training, blockchain services/views, Celery tasks)
- **84% → 91%**: 191 tests (models views, core views, ensemble views, competitive insights views, explainability views, consortiums views)
- **91% → 93%**: 103 tests (cache, audit, json_schemas, permissions, blockchain services, consortium services)

### Tests por archivo
- `test_consortium_services.py` — 53 tests (MemberService, InvitationService, ContributionService, ConsortiumService)
- `test_quality_assessment_service.py` — 30 tests (scores, quality rules, dashboard)
- `test_competitive_emails.py` — 16 tests (competitive tasks + email service)
- `test_coverage_boost.py` — 16 tests (audit log branches, BaseService, weakness paths)
- `test_consortium_tasks_training.py` — 49 tests (FHETrainingService, BlockchainRegistrationService, Celery tasks, email helper)
- `test_blockchain_services_views.py` — 67 tests (BlockchainService, ConsortiumService, ModelRegistryService, ComputationVerifierService, todas las views)
- `test_models_views.py` — 124 tests (MLModelViewSet actions, TrainingRunViewSet, BatchPredictionJobViewSet, ModelVersionViewSet, ModelExportViewSet, ModelShareViewSet, ModelShareRequestViewSet, PredictionLogViewSet)
- `test_views_extended.py` — 67 tests (WebhookViewSet, WebhookDeliveryViewSet, UsageStatsViewSet, ReportViewSet, WorkflowViewSet, WorkflowRunViewSet, ScheduledTaskViewSet, EnsembleViewSet, IndustryBenchmarkViewSet, CompanyMetricViewSet, CompetitiveReportViewSet, ExplanationRequestViewSet, ModelInsightViewSet, ExplainabilityDashboardView, ConsortiumViewSet, ConsortiumMemberViewSet, ContributionProofViewSet, ConsortiumInvitationViewSet)
- `test_coverage_modules.py` — 103 tests (LRUMemoryCache, ResilientCache, cached decorator, AuditService, JSONSchemaValidator, ProposalDataField, QualityRuleConditionField, 8 permission classes, ConsortiumService stats/rankings, BlockchainService connection)

### Coverage por módulo (evolución completa)
- `models/views.py`: 37% → **96%**
- `core/views.py`: 66% → **91%**
- `ensemble/views.py`: 49% → **94%**
- `competitive_insights/views.py`: 53% → **90%**
- `consortiums/views.py`: 67% → **97%**
- `consortiums/services/training.py`: 38% → **99%**
- `consortiums/services/blockchain.py`: 19% → **89%**
- `consortiums/tasks.py`: 18% → **100%**
- `blockchain/services.py`: 30% → **67%**
- `explainability/views.py`: 69% → **80%**
- `core/cache.py`: 56% → **97%**
- `core/validators/json_schemas.py`: 61% → **94%**
- `core/permissions.py`: 63% → **~100%**
- `core/services/audit.py`: 58% → **~100%**
- `consortiums/services/consortium.py`: 69% → **~100%**

### Módulos con coverage restante más bajo (<85%)
- `blockchain/services.py`: **67%** (72 líneas — requiere Web3/blockchain mocking complejo)
- `core/logging.py`: **75%** (19 líneas)
- `blockchain/secrets.py`: **75%** (26 líneas)
- `core/exceptions.py`: **76%** (24 líneas)
- `core/authentication.py`: **78%** (35 líneas)
- `consortiums/signals.py`: **79%** (16 líneas)
- `data_quality/views.py`: **80%** (18 líneas)
- `explainability/views.py`: **80%** (23 líneas)
- `core/healthchecks.py`: **81%** (23 líneas)
- `models/models.py`: **82%** (80 líneas)
- `core/serializers.py`: **84%** (49 líneas)

### Fixes de CI
- `.github/workflows/ci.yml`: Corregido `sdk-ts` → `sdk-typescript`, `npm ci` → `npm install`
- `.github/workflows/ci.yml`: Agregado `permissions: security-events: write` para SARIF upload
- `sdk-typescript/.eslintrc.json`: Creado (faltaba config de ESLint)
- `sdk-typescript/package.json`: Agregado `@typescript-eslint/parser` y `eslint-plugin`
- `sdk-typescript/src/client.ts`: Fix TS18046 (`data` de type `unknown` en strict mode)
- `sdk-typescript/src/index.ts`: Reemplazado `require()` con ES import

### Bugs Corregidos (2 Feb 2026)

#### 6 Bugs en Consortium Services
- `ConsortiumMember.Status.REJECTED` agregado al modelo (migración 0004)
- `ConsortiumInvitation.Status.CANCELLED` agregado al modelo (migración 0004)
- `ContributionProof` update_fields: eliminado `updated_at` inexistente en `ContributionService.verify_contribution()`
- `ConsortiumService.get_stats()`: corregido `ContributionProof.Status.VERIFIED` → `ContributionProof.VerificationStatus.VERIFIED` y campo `status` → `verification_status`
- `ConsortiumService.get_member_rankings()`: corregido campo `contributor` → `company` y mismo fix de VerificationStatus
- `InvitationService.create_invitation()`: agregado `expires_at=timezone.now() + timedelta(days=7)`

#### 2 Bugs adicionales en training.py
- `FHETrainingService.train()`: faltaba `from apps.consortiums.models import TrainingResult` (NameError en runtime)
- `FHETrainingService._fail_training()`: mismo import faltante de `TrainingResult`

### Próximos Pasos Posibles
- Subir coverage a **95%+** cubriendo los 11 módulos que están entre 67-84%
- Agregar integration tests end-to-end para flujos completos (auth → create consortium → train → predict)
- Configurar Codecov/Coveralls para tracking de coverage en PRs
- Agregar tests de performance/load con locust o similar

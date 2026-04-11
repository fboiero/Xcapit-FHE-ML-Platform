# Release Notes — v1.0.0-rc1

**Fecha**: 14 de marzo de 2026
**Estado**: Release Candidate 1

---

## Resumen Ejecutivo

Xcapit FHE-ML Platform v1.0.0-rc1 es la primera version candidata a produccion. Incluye las 4 capas criptograficas completas (FHE, ZKP, MPC, DP), 13 aplicaciones Django con 391 endpoints, un dashboard con 45+ paginas, un SDK Python con 24+ modelos ML, y smart contracts en Arbitrum.

### Estadisticas Clave

| Metrica | Valor |
|---------|-------|
| Tests Django | 1,496+ |
| Tests SDK | 620+ |
| Tests Seguridad | 27 |
| Cobertura | 96.23% |
| Endpoints API | 391 |
| Paginas Frontend | 45+ |
| Modelos ML | 24+ |
| Apps Django | 13 |
| Smart Contracts | 3 (v2) |
| CI/CD Jobs | 19 (10 GitHub + 9 GitLab) |
| Documentacion | 43+ archivos |
| Diagramas | 21 SVG |

---

## Componentes

### 1. Backend Django

**Stack**: Django 5.2 LTS + DRF + PostgreSQL + Redis + Celery

**13 Aplicaciones**:

| App | Modelos | Endpoints | Descripcion |
|-----|---------|-----------|-------------|
| core | User, Company, APIKey, AuditLog, Webhook, Report, Workflow, ScheduledTask | ~40 | Autenticacion, multi-tenancy, auditoria |
| consortiums | Consortium, ConsortiumMember, ContributionProof, TrainingResult, Invitation | ~25 | Gestion de consorcios |
| governance | Proposal, Vote, AuditEvent, RewardDistribution | ~20 | Gobernanza on-chain |
| marketplace | MarketplaceModel, Category, Deployment, Review | ~30 | Catalogo de modelos |
| compliance | Framework, Check, Report, Attestation, DPR, Settings | ~35 | Cumplimiento regulatorio |
| data_quality | Assessment, Rule, Alert | ~20 | Calidad de datos |
| federated | FederatedModel, InferenceEndpoint, InferenceRequest, EdgeNode | ~20 | Aprendizaje federado |
| ensemble | EnsembleModel, EnsembleComponent | ~15 | Modelos ensemble |
| explainability | ExplanationRequest, FeatureImportance, ModelInsight | ~15 | Interpretabilidad |
| competitive_insights | Benchmark, CompanyMetric, Report | ~10 | Analisis competitivo |
| sandbox | Sandbox, Template, Dataset, Experiment, SandboxLead, Subscription | ~30 | Ambiente de pruebas |
| blockchain | Transaction, SmartContract, BlockchainKey | ~25 | Blockchain |
| models | (migrated to federated) | — | Modelos ML (legacy) |

**Autenticacion**:
- JWT (simplejwt) con token blacklist
- API Keys por empresa
- Sandbox Tokens (7 dias, sin registro)
- django-axes (proteccion brute-force)
- django-ratelimit (por tier)

**Tiers**:
- Free: 10 req/min, 100/dia, 2 modelos, 1 consorcio
- Starter: 100 req/min, 5K/dia, 10 modelos, 5 consorcios
- Professional: 500 req/min, 50K/dia, 50 modelos, 20 consorcios
- Enterprise: 2K req/min, ilimitado

### 2. Dashboard Frontend

**Stack**: React 18 + Vite 5 + TailwindCSS 3 + react-i18next

**45+ Paginas** organizadas en:
- Autenticacion (login, registro, perfil)
- Core (dashboard, consorcios, datos)
- ML (model builder, training, metricas, deployment)
- Gobernanza (propuestas, votacion, auditoria)
- Marketplace, Cumplimiento, Calidad, Explicabilidad
- Operaciones (monitoreo, notificaciones, workflows)
- Admin (panel, equipo, facturacion, API playground)
- Sandbox y Demos (5 demos industriales)

**Soporte bilingue**: Espanol e Ingles completo.

### 3. SDK Python (v0.7.0)

**Modulos**:
- `encryption/` — CKKS (TenSEAL) con 128/192/256-bit
- `models/` — 24+ modelos ML (regression, classification, clustering, NLP, deep learning)
- `preprocessing/` — Scalers, encoders, imputers, transformers
- `evaluation/` — Metricas, cross-validation, grid/random search
- `zkp/` — Pedersen, Schnorr, contribution proofs, arithmetic circuits
- `mpc/` — Shamir, secure aggregation, threshold decryption, key ceremony
- `privacy/` — Laplace, Gaussian, exponential mechanisms, DP-SGD, accountant
- `blockchain/` — Arbitrum connector, model registry
- `cli/` — Encryption, training, prediction, blockchain, benchmark commands
- `pipeline.py` — ML pipeline composition
- `persistence.py` — Model serialization
- `feature_engineering.py`, `feature_selection.py` — Feature tools
- `validation.py`, `outlier.py`, `impute.py` — Data tools
- `monitoring.py` — Training/inference monitoring

### 4. Smart Contracts

**Stack**: Solidity 0.8.20 + Foundry + OpenZeppelin

| Contrato | Tamaño | Seguridad |
|----------|--------|-----------|
| ModelRegistryV2 | 14 KB | ReentrancyGuard, Pausable, Ownable2Step |
| ConsortiumGovernanceV2 | 28 KB | Commit-reveal voting, pull-over-push rewards |
| ComputationVerifierV2 | 13 KB | Proof validation, result caching |

**Redes**: Arbitrum One/Sepolia, Ethereum Mainnet/Sepolia

### 5. Infraestructura

- Docker multi-stage (dev/prod) con non-root user
- GitHub Actions: lint, test, build, security scan, deploy (10 jobs)
- GitLab CI: test, build, staging, production (9 jobs)
- Pre-commit: ruff, black, pytest
- Sentry para error monitoring
- OpenBao para gestion de secretos

---

## Auditoria de Seguridad RC1

### Vulnerabilidades Encontradas y Corregidas

#### CRITICAL (1)
- **Escalacion de privilegios via tier upgrade** — `TrialService.request_upgrade()` cambiaba el tier directamente sin verificacion de pago. Corregido: ahora crea suscripcion PENDING que requiere `confirm_upgrade()` con validacion del gateway de pago.

#### HIGH (12)
- **IDOR via query params** (6 ViewSets) — `IsConsortiumMember` retornaba `True` en list views sin `pk` en kwargs. Corregido en GovernanceConfig, Proposals, AuditEvents, RewardDistributions, Deployments con membership check en `get_queryset()`.
- **IDOR en serializers** (6) — Serializers aceptaban `consortium` como campo escribible sin validar membresia. Corregido con `validate_consortium()` en governance, marketplace, data_quality, compliance, explainability.
- **SSRF en webhooks** — URLs de webhook no validaban contra IPs internas. Corregido con `validate_url()` bloqueando localhost, 127.0.0.1, metadata (169.254.x.x), IPs privadas via DNS.
- **Tenant isolation missing** (2 ViewSets) — FeatureImportance y ModelInsight caian a `.objects.all()`. Corregido con scoping a consorcios del usuario.
- **Marketplace purchase sin check** — `purchase()` no verificaba membresia al consorcio. Corregido.
- **ZKP timing attack** — Verificacion usaba Python `==` en lugar de `hmac.compare_digest()`. Corregido.
- **Schnorr proof forgery** — Sin validacion de subgrupo (Y=1 forja trivialmente). Corregido.
- **PRNG inseguro en DP** — `np.random` (Mersenne Twister) reemplazado por CSPRNG (`secrets`).
- **Bug de budget DP** — `delta=0` disparaba `is_exhausted` inmediatamente. Corregido.

#### MEDIUM (4)
- **Sandbox extension con dias negativos** — Validacion `1 <= days <= 30` agregada.
- **ALLOWED_HOSTS = ["*"]** en test settings — Restringido a localhost/testserver.
- **Audit verify sin membership check** — Agregado.
- **Reward distribute sin membership check** — Agregado.

#### Previamente corregidos (v0.7.0 → RC1)
- Secret key hardcodeada removida
- Consortium permissions hardened
- Password min_length alineada a 12
- MeView usa serializer validation
- RegisterSerializer.create() fix
- CreateAPIKeyView fix
- API v1 → v2 migration
- Auth header X-API-Key → Authorization: ApiKey

### Tests de Seguridad (27)

| Suite | Tests | Cobertura |
|-------|-------|-----------|
| TestIDORConsortiumValidation | 6 | Serializer-level consortium blocking |
| TestSSRFPrevention | 6 | Webhook URL validation |
| TestIDORViewQueryParamBypass | 6 | ViewSet queryset membership |
| TestTenantIsolation | 4 | Explainability tenant scoping |
| TestTierUpgradeProtection | 3 | Payment verification |
| TestSandboxExtensionValidation | 2 | Input validation |

---

## Documentacion Incluida

| Documento | Descripcion |
|-----------|-------------|
| [USER_MANUAL.md](USER_MANUAL.md) | Manual de usuario completo (ES) |
| [RELEASE_NOTES_RC1.md](RELEASE_NOTES_RC1.md) | Este documento |
| [TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md) | Arquitectura tecnica |
| [API_REFERENCE.md](API_REFERENCE.md) | Referencia API |
| [SECURITY_AUDIT_REPORT.md](SECURITY_AUDIT_REPORT.md) | Auditoria de seguridad |
| [ONBOARDING_PASO_A_PASO.md](ONBOARDING_PASO_A_PASO.md) | Guia de onboarding |
| [FHE Theory](theory/) | 4 capitulos de teoria FHE |
| [Architecture Guides](guides/) | 5 guias de arquitectura |
| [ADR](adr/) | 4 Architecture Decision Records |
| [SDK Docs](sdk/) | Arquitectura, troubleshooting, tutoriales |
| [ISO 27001](compliance/) | Documentacion de cumplimiento ISO |
| [Traceability](traceability/) | Matriz de trazabilidad, user stories |
| [Diagrams](diagrams/) | 21 diagramas SVG |
| [Examples](../examples/) | 7 Jupyter notebooks |

---

## Breaking Changes desde v0.7.0

1. **API base path**: `/api/v1/` → `/api/v2/`
2. **Auth header**: `X-API-Key` → `Authorization: ApiKey`
3. **Tier upgrade**: Ya no es instantaneo — requiere flujo de pago
4. **Subscription model**: Nuevo status `PENDING` para upgrades
5. **Models app**: Modelos migrados a `federated` app (models app vaciada)

---

## Requisitos de Sistema

| Componente | Version Minima |
|-----------|---------------|
| Python | 3.11+ |
| Node.js | 18+ |
| PostgreSQL | 14+ |
| Redis | 7+ |
| Docker | 24+ |
| Foundry | Latest |

### Variables de Entorno Requeridas

```bash
DJANGO_SECRET_KEY=<random-64-chars>
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://localhost:6379/0
```

### Opcionales
```bash
DJANGO_DEBUG=False
FHE_SECURITY_LEVEL=128
SENTRY_DSN=https://...@sentry.io/...
FIELD_ENCRYPTION_KEY=<base64-32-bytes>
```

---

## Proximos Pasos (RC1 → GA)

1. **Crypto hardening pendiente**:
   - ContributionProof: no filtrar blinding factors en serializacion
   - ZKP: agregar nonces/session binding al hash Fiat-Shamir (replay protection)
   - KeyCeremony: no almacenar todos los secretos en memoria
   - Secure aggregation: derivar seeds de intercambio de claves (no de indices)

2. **Testing**:
   - Resolver 12 archivos de test con errores de importacion
   - Agregar tests de integracion end-to-end
   - Performance testing bajo carga

3. **Operaciones**:
   - Configurar alerting (PagerDuty/OpsGenie)
   - Runbook de operaciones completado
   - Disaster recovery plan

4. **Documentacion**:
   - API reference autogenerada desde OpenAPI spec
   - Video tutoriales
   - Documentacion de deployment en cloud (AWS/GCP/Azure)

---

*Xcapit FHE-ML Platform v1.0.0-rc1*
*Equipo: [Xcapit](https://xcapit.com) / [QuarkID](https://quarkid.org) (3.6M+ usuarios)*

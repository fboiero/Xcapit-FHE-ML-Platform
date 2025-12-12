# Xcapit Privacy - Product Roadmap

## Vision
La plataforma donde empresas colaboran con datos sin compartirlos.

## Tiers de Desarrollo

---

### TIER 1: Core Platform (MVP)
**Status:** Completed
**Objetivo:** Flujo completo de consorcio funcionando

| Feature | Descripcion | Status |
|---------|-------------|--------|
| Consortium Dashboard | Crear consorcio, invitar empresas, ver miembros y estado | Done |
| Encrypted Data Upload | Cada empresa sube datos encriptados localmente con su clave | Done |
| Model Training Pipeline | Entrenar modelo ML con datos combinados de N empresas | Done |
| Results Download | Cada empresa descarga predicciones encriptadas para su clave | Done |

**Entregable:** Una empresa puede crear un consorcio, invitar otras, todas suben datos, entrenan un modelo compartido, y cada una baja sus predicciones.

**Archivos principales:**
- Backend API: `sdk/api/consortium.py`, `sdk/api/consortium_routes.py`
- Frontend Dashboard: `dashboard/src/`
- FHE Encryption: `sdk/encryption/ckks_wrapper.py`

---

### TIER 2: Trust & Governance
**Status:** Completed
**Objetivo:** Confianza entre participantes sin intermediario central

| Feature | Descripcion | Status |
|---------|-------------|--------|
| Contribution Proof | Registro blockchain de aportes (cantidad, no contenido) | Done |
| Voting System | Decisiones por votacion: agregar/remover miembros, cambiar modelo | Done |
| Audit Trail | Log inmutable de todas las operaciones del consorcio | Done |
| Fair Revenue Split | Distribucion automatica de valor segun contribucion | Done |

**Entregable:** Gobernanza descentralizada del consorcio con pruebas criptograficas de participacion.

**Archivos principales:**
- Smart Contract: `contracts/ConsortiumGovernance.sol`
- Blockchain Client: `sdk/blockchain/governance.py`
- API Routes: `sdk/api/governance_routes.py`
- Backend Methods: `sdk/api/consortium.py` (governance methods)
- Frontend Dashboard: `dashboard/src/pages/Governance.jsx`
- Tests: `tests/test_governance.py` (31 tests)

---

### TIER 3: Enterprise Features
**Status:** Completed
**Objetivo:** Features que desbloquean ventas enterprise

| Feature | Descripcion | Status |
|---------|-------------|--------|
| Compliance Dashboard | Verificacion automatica GDPR/HIPAA/SOC2/PCI-DSS | Done |
| Data Quality Score | Metricas de calidad de datos sin acceso al contenido | Done |
| Model Marketplace | Modelos pre-entrenados por industria (fraude, credit, salud) | Done |
| Sandbox Mode | Ambiente de prueba con datos sinteticos | Done |

**Entregable:** Suite enterprise-ready con compliance automatico y onboarding simplificado.

**Archivos principales (Compliance):**
- Backend Schema: `sdk/api/consortium.py` (compliance methods)
- API Routes: `sdk/api/compliance_routes.py`
- Frontend Dashboard: `dashboard/src/pages/Compliance.jsx`
- Tests: `tests/test_compliance.py` (27 tests)

**Archivos principales (Data Quality):**
- Backend Schema: `sdk/api/consortium.py` (data quality methods)
- API Routes: `sdk/api/data_quality_routes.py`
- Frontend Dashboard: `dashboard/src/pages/DataQuality.jsx`
- Tests: `tests/test_data_quality.py` (20 tests)

**Archivos principales (Model Marketplace):**
- Backend Schema: `sdk/api/consortium.py` (marketplace methods)
- API Routes: `sdk/api/marketplace_routes.py`
- Frontend Dashboard: `dashboard/src/pages/Marketplace.jsx`
- Tests: `tests/test_marketplace.py` (34 tests)

**Archivos principales (Sandbox Mode):**
- Backend Schema: `sdk/api/consortium.py` (sandbox methods)
- API Routes: `sdk/api/sandbox_routes.py`
- Frontend Dashboard: `dashboard/src/pages/Sandbox.jsx`
- Tests: `tests/test_sandbox.py` (34 tests)

---

### TIER 4: Diferenciadores
**Status:** Completed
**Objetivo:** Ventajas competitivas unicas en el mercado

| Feature | Descripcion | Status |
|---------|-------------|--------|
| Federated Inference | Predicciones sin mover datos a la nube | Done |
| Model Explainability | Explicar decisiones ML sin revelar datos de training | Done |
| Competitive Insights | Benchmarks anonimos vs industria | Done |
| Multi-Model Ensemble | Combinar multiples modelos de diferentes consorcios | Done |

**Entregable:** Capacidades unicas que no existen en el mercado actual.

**Archivos principales (Federated Inference):**
- Backend Schema: `sdk/api/consortium.py` (federated inference methods)
- API Routes: `sdk/api/federated_routes.py`
- Frontend Dashboard: `dashboard/src/pages/FederatedInference.jsx`
- Tests: `tests/test_federated.py`

**Archivos principales (Model Explainability):**
- Backend Schema: `sdk/api/consortium.py` (explainability methods)
- API Routes: `sdk/api/explainability_routes.py`
- Frontend Dashboard: `dashboard/src/pages/ModelExplainability.jsx`
- Tests: `tests/test_explainability.py` (34 tests)

**Archivos principales (Competitive Insights):**
- Backend Schema: `sdk/api/consortium.py` (competitive insights methods)
- API Routes: `sdk/api/competitive_routes.py`
- Frontend Dashboard: `dashboard/src/pages/CompetitiveInsights.jsx`

**Archivos principales (Multi-Model Ensemble):**
- Backend Schema: `sdk/api/consortium.py` (ensemble methods)
- API Routes: `sdk/api/ensemble_routes.py`
- Frontend Dashboard: `dashboard/src/pages/MultiModelEnsemble.jsx`

---

## Arquitectura Tier 1

```
+------------------+     +------------------+     +------------------+
|    Empresa A     |     |    Empresa B     |     |    Empresa C     |
|                  |     |                  |     |                  |
| datos.csv        |     | datos.csv        |     | datos.csv        |
|      |           |     |      |           |     |      |           |
|      v           |     |      v           |     |      v           |
| [Encrypt FHE]    |     | [Encrypt FHE]    |     | [Encrypt FHE]    |
| (clave privada)  |     | (clave privada)  |     | (clave privada)  |
|      |           |     |      |           |     |      |           |
+------|----------+     +------|----------+     +------|----------+
       |                       |                       |
       v                       v                       v
+------------------------------------------------------------------+
|                     XCAPIT PRIVACY PLATFORM                       |
|                                                                   |
|  +--------------------+  +--------------------+                   |
|  | Consortium Manager |  | Encrypted Storage  |                   |
|  | - Create/Join      |  | - enc_a.fhe        |                   |
|  | - Invite members   |  | - enc_b.fhe        |                   |
|  | - View status      |  | - enc_c.fhe        |                   |
|  +--------------------+  +--------------------+                   |
|                                  |                                |
|                                  v                                |
|                    +------------------------+                     |
|                    | FHE Training Engine    |                     |
|                    | - Linear Regression    |                     |
|                    | - Logistic Regression  |                     |
|                    | - K-Means Clustering   |                     |
|                    | - Decision Trees       |                     |
|                    +------------------------+                     |
|                                  |                                |
|                                  v                                |
|                    +------------------------+                     |
|                    | Encrypted Model        |                     |
|                    | (shared weights)       |                     |
|                    +------------------------+                     |
|                                  |                                |
+----------------------------------|-------------------------------+
                                   |
       +---------------------------+---------------------------+
       |                           |                           |
       v                           v                           v
+------------------+     +------------------+     +------------------+
|    Empresa A     |     |    Empresa B     |     |    Empresa C     |
|                  |     |                  |     |                  |
| [Decrypt FHE]    |     | [Decrypt FHE]    |     | [Decrypt FHE]    |
| (su clave)       |     | (su clave)       |     | (su clave)       |
|      |           |     |      |           |     |      |           |
|      v           |     |      v           |     |      v           |
| predictions.csv  |     | predictions.csv  |     | predictions.csv  |
+------------------+     +------------------+     +------------------+
```

## Stack Tecnico

- **Frontend:** React + TypeScript + TailwindCSS
- **Backend:** FastAPI (Python)
- **FHE Engine:** TenSEAL (CKKS scheme)
- **Storage:** PostgreSQL + S3-compatible (encrypted blobs)
- **Blockchain:** Arbitrum (contribution proofs)
- **Auth:** API Keys + OAuth2 (enterprise SSO)

## Metricas de Exito

### Tier 1
- [ ] Tiempo de setup de consorcio < 5 minutos
- [ ] Upload de datos encriptados < 30 segundos (1GB)
- [ ] Training time comparable a cleartext (+20% max overhead)
- [ ] 0 datos en claro en servidor (verificable)

### Tier 2
- [ ] Proof of contribution en < 1 minuto post-training
- [ ] Votaciones resueltas en < 24hs
- [ ] Audit trail queryable por reguladores

### Tier 3
- [ ] Compliance check automatico < 5 minutos
- [ ] Data quality score sin false positives
- [ ] Onboarding con sandbox < 1 hora

---

## Changelog

| Fecha | Version | Cambios |
|-------|---------|---------|
| 2024-12-08 | 0.1.0 | Roadmap inicial creado |
| 2024-12-09 | 0.2.0 | TIER 2 completado: Governance system con voting, audit trail, contribution proofs y rewards |
| 2024-12-09 | 0.3.0 | TIER 3 iniciado: Compliance Dashboard con GDPR/HIPAA/SOC2/PCI-DSS verificacion automatica |
| 2024-12-09 | 0.4.0 | TIER 3 continuado: Data Quality Score con metricas de calidad sin acceso al contenido |
| 2024-12-10 | 0.5.0 | TIER 3 continuado: Model Marketplace con modelos pre-entrenados por industria, deploy a consorcios, reviews y estadisticas |
| 2024-12-10 | 0.6.0 | TIER 3 completado: Sandbox Mode con ambientes de prueba, generacion de datos sinteticos, experimentos y templates por industria |
| 2024-12-10 | 0.7.0 | TIER 4 iniciado: Federated Inference con endpoints de inferencia, modelos federados, edge nodes y predicciones encriptadas |
| 2024-12-10 | 0.8.0 | TIER 4 continuado: Model Explainability con explicaciones privacy-preserving (feature importance, SHAP, decision path, counterfactual, summary) |
| 2024-12-10 | 0.9.0 | TIER 4 completado: Competitive Insights con benchmarks anonimos por industria y Multi-Model Ensemble para combinar modelos de diferentes consorcios |

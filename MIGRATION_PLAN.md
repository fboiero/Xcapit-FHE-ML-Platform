# Plan de Migración y Ordenamiento del Backend

## Resumen Ejecutivo

Este plan detalla la migración del backend FastAPI (`sdk/api/`) al backend Django (`backend_django/`), manteniendo el SDK como librería Python independiente.

## Estado Actual

### Estructura Actual
```
├── sdk/                          # SDK Python (Librería + API FastAPI)
│   ├── api/                      # ❌ API REST FastAPI (a deprecar)
│   │   ├── server.py             # Servidor FastAPI
│   │   ├── *_routes.py           # 10 archivos de rutas
│   │   ├── database*.py          # Acceso a BD
│   │   └── consortium/           # Lógica de negocio (13 archivos)
│   ├── models/                   # ✅ Modelos ML (mantener)
│   ├── encryption/               # ✅ CKKS/FHE (mantener)
│   ├── blockchain/               # ✅ Integración blockchain (mantener)
│   ├── cli/                      # ✅ CLI tool (mantener)
│   ├── utils/                    # ✅ Utilidades (mantener)
│   └── quality/                  # ✅ Calculadores (mantener)
│
├── backend_django/               # Backend Django (API v2)
│   └── apps/
│       ├── core/                 # ✅ Autenticación, modelos base
│       ├── consortiums/          # ✅ Gestión de consorcios
│       ├── compliance/           # ✅ Cumplimiento normativo
│       ├── federated/            # ✅ Aprendizaje federado
│       ├── governance/           # ✅ Gobernanza
│       ├── marketplace/          # ✅ Marketplace de modelos
│       ├── models/               # ✅ Gestión de modelos ML
│       └── sandbox/              # ✅ Ambiente de pruebas
```

### Apps Faltantes en Django
| Módulo SDK | Tamaño | Funcionalidad |
|------------|--------|---------------|
| `data_quality` | 22KB | Evaluación de calidad de datos |
| `competitive_insights` | 13KB | Benchmarks de industria |
| `ensemble` | 13KB | Modelos multi-ensemble |
| `explainability` | 19KB | Explicabilidad de modelos (SHAP, etc.) |

---

## Fase 1: Crear Apps Django Faltantes

### 1.1 App: `data_quality`

```bash
cd backend_django
python manage.py startapp data_quality apps/data_quality
```

**Archivos a crear:**
- `apps/data_quality/models.py` - Modelos: QualityAssessment, QualityRule, QualityAlert
- `apps/data_quality/serializers.py` - Serializers DRF
- `apps/data_quality/views.py` - ViewSets
- `apps/data_quality/urls.py` - Rutas
- `apps/data_quality/services.py` - Lógica de negocio (migrada de SDK)

### 1.2 App: `competitive_insights`

```bash
python manage.py startapp competitive_insights apps/competitive_insights
```

**Archivos a crear:**
- `apps/competitive_insights/models.py` - Modelos: IndustryBenchmark, CompanyMetric
- `apps/competitive_insights/serializers.py`
- `apps/competitive_insights/views.py`
- `apps/competitive_insights/urls.py`
- `apps/competitive_insights/services.py`

### 1.3 App: `ensemble`

```bash
python manage.py startapp ensemble apps/ensemble
```

**Archivos a crear:**
- `apps/ensemble/models.py` - Modelos: Ensemble, EnsembleModel, EnsemblePrediction
- `apps/ensemble/serializers.py`
- `apps/ensemble/views.py`
- `apps/ensemble/urls.py`
- `apps/ensemble/services.py`

### 1.4 App: `explainability`

```bash
python manage.py startapp explainability apps/explainability
```

**Archivos a crear:**
- `apps/explainability/models.py` - Modelos: ExplanationRequest, FeatureImportance
- `apps/explainability/serializers.py`
- `apps/explainability/views.py`
- `apps/explainability/urls.py`
- `apps/explainability/services.py`

---

## Fase 2: Migrar Lógica de Negocio

### 2.1 Mapeo de Modelos SDK → Django

| SDK (consortium/) | Django Model | Tabla |
|-------------------|--------------|-------|
| QualityAssessment | `data_quality.QualityAssessment` | `data_quality_assessment` |
| QualityRule | `data_quality.QualityRule` | `data_quality_rule` |
| IndustryBenchmark | `competitive_insights.Benchmark` | `competitive_benchmark` |
| ModelEnsemble | `ensemble.Ensemble` | `ensemble_ensemble` |
| ExplanationRequest | `explainability.ExplanationRequest` | `explainability_request` |

### 2.2 Migrar Services

Extraer la lógica de negocio de los managers del SDK y convertirla en services de Django:

```python
# sdk/api/consortium/data_quality.py → backend_django/apps/data_quality/services.py
class DataQualityService:
    @staticmethod
    def assess_quality(contribution, metrics):
        # Lógica migrada del DataQualityManager
        pass
```

### 2.3 Actualizar URLs

Agregar las nuevas apps a `config/urls.py`:

```python
path("api/v2/", include([
    # ... existentes ...
    path("data-quality/", include("apps.data_quality.urls")),
    path("competitive/", include("apps.competitive_insights.urls")),
    path("ensemble/", include("apps.ensemble.urls")),
    path("explainability/", include("apps.explainability.urls")),
]))
```

---

## Fase 3: Reorganizar el SDK

### 3.1 Estructura Final del SDK (solo librería)

```
sdk/                              # Renombrar a xcapit_fhe/
├── __init__.py                   # Exports públicos
├── models/                       # Modelos ML
│   ├── __init__.py
│   ├── base.py
│   ├── linear_regression.py
│   ├── logistic_regression.py
│   ├── decision_tree.py
│   └── kmeans.py
├── encryption/                   # FHE/CKKS
│   ├── __init__.py
│   ├── ckks_wrapper.py
│   ├── context_manager.py
│   └── optimized_engine.py
├── blockchain/                   # Integración blockchain
│   ├── __init__.py
│   ├── connector.py
│   ├── registry.py
│   └── governance/
├── cli/                          # CLI tool
│   ├── __init__.py
│   └── commands/
├── utils/                        # Utilidades
│   ├── __init__.py
│   ├── data_loader.py
│   ├── serialization.py
│   └── validators.py
├── quality/                      # Calculadores de calidad
│   ├── __init__.py
│   └── calculator.py
└── monitoring.py                 # Métricas
```

### 3.2 Archivos a ELIMINAR del SDK

```bash
# Eliminar API FastAPI
rm sdk/api/server.py
rm sdk/api/auth.py
rm sdk/api/client.py
rm sdk/api/database.py
rm sdk/api/database_pg.py
rm sdk/api/*_routes.py

# Eliminar directorio consortium (lógica migrada a Django)
rm -rf sdk/api/consortium/

# Eliminar directorio api vacío
rm -rf sdk/api/
```

### 3.3 Actualizar `sdk/__init__.py`

```python
"""Xcapit FHE-ML SDK - Privacy-preserving machine learning library."""

from .encryption import (
    CKKSEncryptor,
    CKKSParameters,
    FHEContextManager,
    SecurityLevel,
)
from .models import (
    LinearRegression,
    LogisticRegression,
    DecisionTreeClassifier,
    KMeans,
)
from .blockchain import BlockchainConnector, ModelRegistryClient
from .utils import SecureDataLoader, EncryptedDataset

__version__ = "0.2.0"
```

---

## Fase 4: Actualizar Tests

### 4.1 Tests a Mover/Actualizar

| Test Actual | Acción |
|-------------|--------|
| `tests/test_api.py` | Eliminar (API FastAPI deprecada) |
| `tests/test_*_routes.py` | Eliminar (rutas FastAPI) |
| `tests/test_consortium*.py` | Actualizar para usar Django |
| `tests/test_models.py` | Mantener (librería) |
| `tests/test_encryption.py` | Mantener (librería) |
| `tests/test_blockchain.py` | Mantener (librería) |

### 4.2 Crear Tests Django

```
backend_django/tests/
├── test_data_quality.py
├── test_competitive_insights.py
├── test_ensemble.py
└── test_explainability.py
```

---

## Fase 5: Actualizar Configuración

### 5.1 Actualizar `pyproject.toml`

```toml
[project]
name = "xcapit-fhe-ml"
version = "0.2.0"
description = "Privacy-preserving ML library using FHE"

[project.optional-dependencies]
api = ["django>=4.2", "djangorestframework>=3.14"]
```

### 5.2 Actualizar `docker-compose.yml`

Eliminar servicio de API FastAPI, mantener solo Django.

### 5.3 Actualizar CI/CD

Actualizar `.github/workflows/ci.yml` para:
- Ejecutar tests de Django
- No ejecutar tests de API FastAPI eliminada

---

## Checklist de Ejecución

### Fase 1: Crear Apps Django ✅ COMPLETADO
- [x] Crear app `data_quality`
- [x] Crear app `competitive_insights`
- [x] Crear app `ensemble`
- [x] Crear app `explainability`
- [x] Agregar apps a `INSTALLED_APPS`
- [x] Crear migraciones

### Fase 2: Migrar Lógica ✅ COMPLETADO
- [x] Migrar modelos de data_quality
- [x] Migrar modelos de competitive_insights
- [x] Migrar modelos de ensemble
- [x] Migrar modelos de explainability
- [x] Crear serializers
- [x] Crear views
- [x] Crear urls
- [x] Actualizar config/urls.py

### Fase 3: Limpiar SDK ✅ COMPLETADO
- [x] Eliminar sdk/api/server.py
- [x] Eliminar sdk/api/*_routes.py
- [x] Eliminar sdk/api/consortium/
- [x] Eliminar sdk/api/database*.py
- [x] Actualizar sdk/__init__.py (versión 0.2.0)
- [x] Verificar imports
- [x] Actualizar CLI api_keys (ahora muestra mensaje de migración)

### Fase 4: Tests ✅ COMPLETADO
- [x] Eliminar tests de API FastAPI
- [x] Crear tests para nuevas apps Django
- [ ] Ejecutar suite completa de tests

### Fase 5: Configuración Docker ✅ COMPLETADO
- [x] Actualizar Dockerfile a Python 3.12
- [x] Crear docker-entrypoint.sh con manejo de migraciones
- [x] Actualizar health checks
- [x] Mejorar docker-compose.yml

### Fase 6: Documentación ✅ COMPLETADO
- [x] Actualizar README.md
- [x] Actualizar CHANGELOG.md (versión 2.0.0)
- [x] Ejecutar suite completa de tests (435 pasando)

---

## Estimación de Archivos

| Acción | Archivos |
|--------|----------|
| Crear nuevos | ~20 archivos (4 apps × 5 archivos) |
| Eliminar | ~25 archivos (api/, consortium/, routes) |
| Modificar | ~10 archivos (configs, tests, docs) |

---

## Notas Importantes

1. **Backward Compatibility**: El SDK seguirá funcionando como librería Python independiente
2. **API Versioning**: La API v1 (FastAPI) se depreca, solo queda API v2 (Django)
3. **Database**: Django ORM reemplaza SQLite directo
4. **Auth**: JWT (Django) reemplaza API Keys (FastAPI)

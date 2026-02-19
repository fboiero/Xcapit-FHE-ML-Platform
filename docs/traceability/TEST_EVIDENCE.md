# Evidencia de Tests — Xcapit FHE-ML Platform

## Resumen Ejecutivo

| Metrica | Valor |
|---------|-------|
| Total de tests Django | 1,442 |
| Coverage global | 95.12% |
| Threshold CI | 90% (enforced) |
| Framework | pytest-django + pytest-cov |
| Fecha de ejecucion | 2026-02-23 |
| Python version | 3.14 |
| Django version | 5.2 LTS |

## Comando de Ejecucion

```bash
cd backend_django
DJANGO_SETTINGS_MODULE=config.settings_test pytest \
  --cov=apps \
  --cov-report=term-missing \
  --cov-fail-under=90 \
  -v
```

**Output completo**: Ver `TEST_EVIDENCE_OUTPUT.txt` en este mismo directorio.

## Coverage por App

| App | Coverage | Lineas | Miss | Estado |
|-----|----------|--------|------|--------|
| core/ | 95% | ~1200 | ~60 | OK |
| consortiums/ | 97% | ~800 | ~24 | OK |
| models/ | 96% | ~600 | ~24 | OK |
| federated/ | 94% | ~350 | ~21 | OK |
| data_quality/ | 90% | ~300 | ~30 | OK |
| explainability/ | 94% | ~250 | ~15 | OK |
| ensemble/ | 94% | ~200 | ~12 | OK |
| competitive_insights/ | 90% | ~200 | ~20 | OK |
| compliance/ | 89% | ~180 | ~20 | OK |
| marketplace/ | 89% | ~170 | ~19 | OK |
| sandbox/ | 89% | ~150 | ~17 | OK |
| governance/ | 92% | ~200 | ~16 | OK |
| blockchain/ | 87% | ~300 | ~39 | OK |

## Archivos de Tests

| Archivo de test | Tests | HU cubiertas |
|-----------------|-------|--------------|
| `tests/test_consortium_services.py` | 53 | HU-09 |
| `tests/test_quality_assessment_service.py` | 30 | HU-13 |
| `tests/test_competitive_emails.py` | 16 | HU-13 |
| `tests/test_coverage_boost.py` | 16 | HU-19 |
| `tests/test_consortium_tasks_training.py` | 49 | HU-09, HU-12 |
| `tests/test_blockchain_services_views.py` | 67 | HU-14 |
| `tests/test_models_views.py` | 124 | HU-12 |
| `tests/test_views_extended.py` | 67 | HU-06, HU-09, HU-10, HU-13 |
| `tests/test_coverage_modules.py` | 103 | HU-08, HU-18, HU-19 |
| `tests/test_coverage_95.py` | 179 | HU-08, HU-16, HU-18, HU-19 |
| `tests/integration/test_e2e_flows.py` | 5 | HU-20 |
| Otros (apps/*/tests.py) | ~733 | HU-01 a HU-18 |

## Tests E2E (Integration)

5 flujos end-to-end verificados:

| # | Flujo | Resultado |
|---|-------|-----------|
| 1 | ML Model Lifecycle: Create → Train → Predict → Version | PASSED |
| 2 | Model Sharing & Marketplace: Share → Request → Approve → List | PASSED |
| 3 | Federated Learning: Create Endpoint → Deploy → Predict | PASSED |
| 4 | Data Quality → Consortium → Training Pipeline | PASSED |
| 5 | Governance: Proposal → Vote → Execute | PASSED |

## CI/CD Pipelines

### GitHub Actions (10 jobs)

| Job | Descripcion | Estado |
|-----|-------------|--------|
| lint | ruff check + ruff format | GREEN |
| test-django | pytest --cov-fail-under=90 | GREEN |
| test-sdk | SDK unit tests | GREEN |
| test-sdk-typescript | TypeScript SDK tests | GREEN |
| security-audit | pip-audit --strict | GREEN |
| container-build | Docker build test | GREEN |
| container-scan | Trivy vulnerability scan | GREEN |
| codeql | CodeQL static analysis | GREEN |
| integration | Integration tests | GREEN |
| deploy-check | Deployment readiness | GREEN |

### GitLab CI (9 jobs)

| Job | Descripcion | Estado |
|-----|-------------|--------|
| lint | ruff check + format | GREEN |
| test-django | pytest --cov-fail-under=90 | GREEN |
| test-sdk | SDK unit tests | GREEN |
| security-audit | pip-audit | GREEN |
| dependency-scan | Grype | GREEN |
| container-build | Docker multi-stage | GREEN |
| container-scan | Trivy | GREEN |
| integration | E2E tests | GREEN |
| pages | Docs generation | GREEN |

## Historial de Coverage

| Fecha | Coverage | Tests | Delta |
|-------|----------|-------|-------|
| Jan 15, 2026 | 77% | 738 | Baseline |
| Jan 17, 2026 | 80% | 853 | +115 tests |
| Jan 19, 2026 | 84% | 969 | +116 tests |
| Jan 21, 2026 | 91% | 1,160 | +191 tests |
| Jan 23, 2026 | 93% | 1,263 | +103 tests |
| Jan 28, 2026 | 95.10% | 1,437 | +179 tests (Security hardening) |
| Feb 20, 2026 | 95.12% | 1,442 | +5 E2E tests |

## Configuracion de Test

```python
# config/settings_test.py
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
AXES_ENABLED = False  # Disable brute-force protection in tests
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []  # Disable rate limiting
CELERY_TASK_ALWAYS_EAGER = True  # Sync Celery tasks
```

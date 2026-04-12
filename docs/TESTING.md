# Testing Strategy — Xcapit FHE-ML Platform

Testing pyramid completa: unit → integration → E2E → performance. Cada capa tiene su propia herramienta, su propia cadencia, y su propio exit criteria.

---

## La pirámide

```
       /\         ← Performance (Locust) — CI on main + manual
      /  \
     /----\       ← E2E (Playwright) — CI on PRs + main
    /      \
   /--------\     ← Integration (Django TestCase + DRF APIClient) — CI on every commit
  /          \
 /------------\   ← Unit (pytest + SDK tests) — CI on every commit
```

## Cobertura actual (2026-04-12)

| Capa | Cantidad | Coverage | Tooling | CI trigger |
|------|----------|----------|---------|------------|
| Unit + Integration Django | 1,968 tests | 96.23% | pytest | Cada commit |
| Unit SDK | 195 tests | — | pytest | Cada commit |
| Tests de seguridad (IDOR/SSRF) | 27 | 100% | pytest | Cada commit |
| E2E dashboard | 6 spec files | — | Playwright | En desarrollo — ver `dashboard/e2e/` |
| Performance | 3 scenarios | — | Locust | En desarrollo — ver `backend_django/tests/performance/` |
| Visual regression | — | — | — | No existe todavía |

---

## Capa 1 — Unit tests

### Backend (Django + SDK)

**Ubicación**: `backend_django/tests/` + `sdk/tests/`
**Tooling**: pytest con DJANGO_SETTINGS_MODULE=config.settings_test

```bash
make test           # suite completo backend
make test-verbose   # con output detallado
make coverage       # con threshold 90%
make sdk-test       # solo SDK
make test-security  # solo seguridad IDOR
```

**Exit criteria (CI gate)**: todos pasan + coverage ≥ 90%.

---

## Capa 2 — Integration tests

Viven en `backend_django/tests/integration/` y usan el cliente DRF con database real.

Ejemplos críticos:
- `test_e2e_flows.py` — flujos completos multi-step (consortium lifecycle)
- `test_platform_simulation.py` — simulación de 3 empresas con 7 actos

**Diferencia con unit**: usan la DB de verdad (sqlite en test_settings.py) y arman escenarios cross-app.

---

## Capa 3 — E2E tests (Playwright)

**Ubicación**: `dashboard/e2e/`
**Doc detallada**: [dashboard/e2e/README.md](../dashboard/e2e/README.md)

```bash
make e2e-install    # instala Playwright + browsers
make e2e-test       # headless
make e2e-test-ui    # UI mode interactivo
```

### Qué cubre

| Spec | Flujo crítico |
|------|---------------|
| `smoke.spec.js` | Stack up: dashboard responde, backend health, páginas públicas no 5xx |
| `auth.spec.js` | Login, register, protected routes, pricing redirect |
| `consortium.spec.js` | Create, list, detail — el flujo más crítico del producto |
| `sandbox.spec.js` | Demo público sin auth — lead generation |
| `marketplace.spec.js` | Browse + deployment — flujo post-conversión |
| `trial.spec.js` | Trial dashboard, billing, settings |

### Qué NO cubre (todavía)

- Flows con FHE end-to-end (requieren consorcio multi-party real)
- MPC aggregation real
- Upload de datasets completo
- Visual regression (snapshots)

### Exit criteria (CI gate)

- Smoke: 100% passing (blocking)
- Resto: 100% passing (blocking en main, warning en PRs)

---

## Capa 4 — Performance tests (Locust)

**Ubicación**: `backend_django/tests/performance/`
**Doc detallada**: [backend_django/tests/performance/README.md](../backend_django/tests/performance/README.md)

```bash
make perf-install     # instala Locust
make perf-test-seed   # crea usuario de prueba
make perf-test        # load test 50 users 3min
make perf-test-ui     # web UI en :8089
make perf-test-fhe    # FHE stress test 5 users 10min
make perf-test-soak   # soak test 50 users 2h
```

### SLO targets (enforced en CI)

| Endpoint group | p50 | p95 | p99 | Failure rate |
|----------------|-----|-----|-----|--------------|
| Health / Liveness | <20ms | <200ms | <500ms | <0.1% |
| Auth (login/register) | <100ms | <500ms | <1s | <0.5% |
| Standard API | <100ms | <500ms | <1s | <0.5% |
| FHE / MPC operations | <2s | <5s | <10s | <1% |

### Exit criteria (CI gate)

- Todos los SLO p95 respetados
- Failure rate total <1%
- Sin memory leaks detectados en soak test de 2h (métrica manual en el run)

---

## Cadencia de ejecución

| Capa | Every commit | Every PR | Main push | Nightly | Pre-release |
|------|--------------|----------|-----------|---------|-------------|
| Unit Django | ✅ | ✅ | ✅ | ✅ | ✅ |
| Unit SDK | ✅ | ✅ | ✅ | ✅ | ✅ |
| Integration | ✅ | ✅ | ✅ | ✅ | ✅ |
| E2E smoke | ✅ | ✅ | ✅ | ✅ | ✅ |
| E2E full | — | ✅ | ✅ | ✅ | ✅ |
| E2E cross-browser | — | — | — | ✅ | ✅ |
| Perf baseline | — | label `perf-test` | ✅ | — | ✅ |
| Perf FHE stress | — | — | — | ✅ | ✅ |
| Perf soak 2h | — | — | — | — | ✅ |

---

## Principios de testing (no negociables)

1. **Tests independientes** — cada uno crea su propio estado, no depende del orden
2. **Selectores semánticos** — `getByRole` / `getByLabel`, NO clases CSS ni IDs generados
3. **Timeouts realistas** — FHE puede tardar 2-5s, calibrar en consecuencia
4. **Flaky test = bug del test** — tres retries nunca cubre una race condition
5. **Un test, una intención** — no combinar "login + crear consorcio + upload data" en un solo test
6. **Seedear via API pública** — nunca escribir directo en la DB desde E2E

---

## Troubleshooting común

### Playwright: "browser not found"
```bash
cd dashboard && npx playwright install --with-deps chromium
```

### Locust: "connection refused"
El backend no está corriendo. `make dev` primero.

### E2E: "login failed 401"
El usuario de prueba no existe. El helper `registerTestUser` lo crea automaticamente, pero si cambió la API de registro, actualizar `dashboard/e2e/helpers/auth.js`.

### Perf: "SLO BREACH p95 > threshold"
Investigar:
1. ¿Backend corriendo en modo DEBUG? (eso degrada perf ~3x) — usar `DJANGO_DEBUG=False`
2. ¿Hay queries N+1? — activar `django-silk` y profile
3. ¿Redis está caído? — las rate limits caen a full-DB lookup

---

## Roadmap de testing

Próximos gaps a cerrar (orden de prioridad):

1. **FHE end-to-end E2E** — requiere coordinar 2+ clients simulados
2. **Visual regression** — Playwright snapshots con threshold de diff
3. **Chaos engineering** — simular DB/Redis caídos en perf tests
4. **Mutation testing** — `mutmut` en módulos críticos de auth/crypto
5. **Contract testing** — entre SDK Python, SDK TS, y backend (Pact o similar)

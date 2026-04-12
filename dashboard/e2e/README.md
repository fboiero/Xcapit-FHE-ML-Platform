# E2E Tests (Playwright)

End-to-end tests for the Xcapit dashboard using [Playwright](https://playwright.dev).

## Quick start

```bash
# 1. Install Playwright + browsers (one time)
cd dashboard && npm install
npm run e2e:install  # instala Chromium con dependencies

# 2. Make sure both stacks are running
make dev             # backend on :8000
cd dashboard && npm run dev  # frontend on :5173

# 3. Run tests
npm run e2e          # headless
npm run e2e:ui       # interactive UI mode (recommended for dev)
npm run e2e:debug    # step through with inspector
npm run e2e:report   # open last HTML report
```

Desde el root del proyecto también podés usar:
```bash
make e2e-install
make e2e-test
make e2e-test-ui
```

## Estructura

```
e2e/
├── tests/                  # Specs por área funcional
│   ├── smoke.spec.js       # primera línea — si falla, pará todo
│   ├── auth.spec.js        # login, register, protected routes
│   ├── consortium.spec.js  # create, list, detail
│   ├── sandbox.spec.js     # public sandbox demo, pricing, join
│   ├── marketplace.spec.js # marketplace + deployment
│   └── trial.spec.js       # trial dashboard, billing, settings
├── helpers/
│   └── auth.js             # registerTestUser, loginViaAPI, createAuthenticatedUser
├── fixtures/
│   └── test-data.js        # factories de datos sintéticos
└── README.md
```

## Variables de entorno

| Variable | Default | Uso |
|----------|---------|-----|
| `E2E_BASE_URL` | `http://localhost:5173` | URL del dashboard (frontend) |
| `E2E_BACKEND_URL` | `http://localhost:8000` | URL del backend Django |
| `CI` | unset en local | Cuando está seteada activa retries, 1 worker, reporters especiales |

## Convenciones de test

### Principios

1. **Tests independientes**: cada test crea su propio usuario via API (`createAuthenticatedUser`). Nunca compartir estado entre tests.
2. **Lenient selectors**: usar `getByRole`, `getByLabel` con regex case-insensitive. La copy del UI puede cambiar; la intención no.
3. **Timeouts generosos**: 15s para navegaciones (el backend con FHE puede tardar), 10s para asserts.
4. **Skippable cuando el UI cambia**: si un form field ya no existe, `test.skip(true, 'reason')` en lugar de fallar.

### Anti-patrones

- ❌ `page.waitForTimeout(5000)` — usar `waitForLoadState` o `toBeVisible` con timeout
- ❌ Selectores por clase CSS (`.btn-primary`) — usar roles o testids
- ❌ Tests que dependen del orden de ejecución
- ❌ Seedear datos en DB directamente — siempre via API pública

## Integración con CI

Ver `.github/workflows/ci.yml` — el job `e2e-tests` corre después de `test-django` y levanta ambos stacks via docker-compose profile `test`.

Artefactos que suben en fallas:
- `playwright-report/` — reporte HTML con screenshots
- `test-results/` — videos y traces

## Correr en paralelo con performance tests

NO correr E2E y Locust contra el mismo backend simultaneamente — Locust satura el backend y los E2E van a timeout. CI los corre en jobs separados con stacks aislados.

## Debugging

```bash
# Debug un test específico
npx playwright test auth.spec.js --debug

# Ver traces de un test que falló
npx playwright show-trace test-results/<test-name>/trace.zip

# Correr solo smoke tests (rápido, para validar que el stack responde)
npx playwright test smoke.spec.js

# Correr con retry local si sospechás de flakiness
npx playwright test --retries=3
```

## Cross-browser testing

Por default solo Chromium. Para activar Firefox/WebKit, descomentar los proyectos en `playwright.config.js` y correr:

```bash
npx playwright test --project=firefox
npx playwright test --project=webkit
```

Recomendación: correr cross-browser en CI nightly, no en PRs.

## Gaps conocidos (2026-04-12)

- No hay tests de flows con FHE real end-to-end (requieren consorcio con 2+ miembros coordinados)
- No hay tests de MPC aggregation (ídem — requiere multi-party setup)
- Tests de upload de datasets no están completos — esperando fix en el form de upload
- No hay visual regression testing todavía (candidato: Playwright snapshots o Percy)

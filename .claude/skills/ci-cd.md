# CI/CD Pipelines

## GitHub Actions (`.github/workflows/ci.yml`)

Triggers: push to `main`/`develop`, PRs to `main`.

| Job | Runtime | What It Does |
|-----|---------|--------------|
| `lint` | Ubuntu, Python 3.12 | `ruff check` + `ruff format` on sdk/ and tests/ |
| `test-python` | Ubuntu, Python 3.9/3.10/3.11 | SDK tests with coverage |
| `test-django` | Ubuntu, Python 3.12 | Django tests, `--cov-fail-under=90` |
| `test-contracts` | Ubuntu | `forge test` + `forge coverage` |
| `test-typescript` | Ubuntu, Node 18 | TypeScript SDK build + ESLint |
| `build-dashboard` | Ubuntu, Node 18 | `npm run build` (React/Vite) |
| `security-scan` | Ubuntu | pip-audit, TruffleHog secrets scan |
| `container-scan` | Ubuntu | Docker build + Trivy + Grype vulnerability scan |

## GitLab CI (`.gitlab-ci.yml`)

Equivalent pipeline, 9 jobs across 4 stages: `lint` → `test` → `build` → `security`.

Coverage reports in Cobertura format.

## Coverage Thresholds

| Component | Threshold | Current |
|-----------|-----------|---------|
| Django backend | `--cov-fail-under=90` | 95.12% |
| SDK | Tracked (no hard floor) | ~85% |
| Contracts | Forge coverage (non-blocking) | — |

## Docker Build

- **Dockerfile**: `backend_django/Dockerfile` (multi-stage)
- **Stages**: builder → production → development
- **Image size**: ~654MB
- **Build time**: ~3 minutes
- **Entry point**: `docker-entrypoint.sh` (handles migrations)
- **WSGI**: Gunicorn, 4 workers, 2 threads

```bash
# Dev
docker compose --profile dev up

# Production
docker compose --profile production up -d

# Tests
docker compose --profile test up django-test
```

## Key CI Requirements

All must pass before merge:
1. Ruff linting (Python)
2. All tests pass (Django + SDK + contracts)
3. Django coverage >= 90%
4. No security vulnerabilities (pip-audit)
5. No secrets in code (TruffleHog)
6. Dashboard builds successfully

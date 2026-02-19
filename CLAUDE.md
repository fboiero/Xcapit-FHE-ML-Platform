# Xcapit FHE-ML Platform

Privacy-preserving machine learning platform using Fully Homomorphic Encryption (FHE). Enables ML on encrypted data without exposing underlying information.

## Tech Stack

- **Backend**: Django 5.2 LTS + DRF, PostgreSQL, Redis, Celery
- **Frontend**: React 18 + Vite 5, TailwindCSS 3, react-i18next (ES/EN), Vercel
- **FHE**: TenSEAL CKKS scheme (128/192/256-bit security)
- **Blockchain**: Arbitrum (Web3.py), Solidity/Foundry smart contracts
- **SDK**: Python v0.2.0 (pure library: encryption, models, blockchain, cli)
- **Auth**: JWT (simplejwt) with token blacklist, django-axes, django-ratelimit

## Quick Start

```bash
# Backend
cd backend_django
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Tests
DJANGO_SETTINGS_MODULE=config.settings_test pytest --cov=apps --cov-fail-under=90

# Dashboard
cd dashboard && npm install && npm run dev

# Docker
docker compose --profile dev up
```

## Environment Variables

```bash
# Required
DJANGO_SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://localhost:6379/0

# Optional
DJANGO_DEBUG=False
FHE_SECURITY_LEVEL=128
SENTRY_DSN=https://...@sentry.io/...
```

## Skills Reference

Detailed patterns and conventions are in `.claude/skills/`:

| Skill | What It Covers |
|-------|---------------|
| `project-overview` | App map, directory structure, multi-tenancy model, known bugs |
| `django-architecture` | Service layer (BaseService/ServiceResult), model & ViewSet conventions |
| `django-api` | REST standards, JWT auth, pagination, RFC 7807 errors, serializers |
| `django-testing` | pytest fixtures, test patterns, coverage requirements (90%+) |
| `django-rules` | Type hints, import order, naming, security rules — mandatory |
| `fhe-domain` | CKKS scheme, supported models, encryption workflow, SDK |
| `blockchain-domain` | Arbitrum, smart contracts, Celery tasks, key management |
| `commit-messages` | Conventional Commits format with project scopes |
| `git-workflow` | Dual remotes (GitHub+GitLab), pre-commit hooks, safety rules |
| `ci-cd` | GitHub Actions (10 jobs) + GitLab CI (9 jobs), Docker build |
| `security-audit` | Security middleware, auth controls, FHE security, container scanning |
| `code-review` | Architecture, API, testing, and security review checklists |

## Commands

- `/start-task` — Load context, identify scope, check tests, plan before coding
- `/finish-task` — Run tests, lint, verify coverage, commit

## User Preferences

- Spanish communication preferred
- Professional security/privacy company aesthetic
- Type hints required in all new Python code
- Follow service layer pattern for business logic
- Run `pytest` before committing to ensure tests pass

## Current Stats

- **Tests**: 1,442 Django + ~620 SDK = ~2,062 total
- **Coverage**: 95.12% (`--cov-fail-under=90` in CI)
- **CI/CD**: GitHub Actions (10 jobs) + GitLab CI (9 jobs), both green

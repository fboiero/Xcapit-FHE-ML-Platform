# Xcapit FHE-ML Platform

Privacy-preserving ML platform with 4 cryptographic layers (FHE, ZKP, MPC, DP). Enables multi-party ML on encrypted data via data consortiums without exposing underlying information.

**Version**: 1.0.0-rc1

## Tech Stack

- **Backend**: Django 5.2 LTS + DRF, PostgreSQL, Redis, Celery (13 apps, 391 endpoints)
- **Frontend**: React 18 + Vite 5, TailwindCSS 3, react-i18next (ES/EN), Vercel (45+ pages)
- **Crypto**: FHE (TenSEAL CKKS), ZKP (Pedersen/Schnorr), MPC (Shamir), DP (Laplace/Gaussian)
- **Blockchain**: Arbitrum (Web3.py), Solidity 0.8.20/Foundry smart contracts (3 v2 contracts)
- **SDK**: Python v0.7.0 (24+ models, encryption, blockchain, zkp, mpc, privacy, cli)
- **Auth**: JWT (simplejwt) with token blacklist, django-axes, django-ratelimit
- **Tiers**: free/starter/professional/enterprise with rate limiting

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
| `dashboard-frontend` | React/Vite conventions, components, API client, i18n, theming |
| `sdk-development` | SDK modules, FHE models, encryption, blockchain, CLI, test patterns |
| `smart-contracts` | Foundry/Solidity, contract functions, deployment, Django integration |

## Commands

- `/start-task` — Load context, identify scope, check tests, plan before coding
- `/finish-task` — Run tests, lint, verify coverage, commit
- `/fix-bugs` — Resolve known pre-existing bugs documented in project-overview
- `/coverage-report` — Run coverage analysis and identify modules below 95%
- `/deploy-check` — Full pre-deployment checklist (tests, lint, security, Docker, contracts)
- `/review-app` — Code review a Django app against project standards

## User Preferences

- Spanish communication preferred
- Professional security/privacy company aesthetic
- Type hints required in all new Python code
- Follow service layer pattern for business logic
- Run `pytest` before committing to ensure tests pass

## Current Stats

- **Tests**: 1,496+ Django + ~620 SDK + 27 security = ~2,143 total
- **Coverage**: 96.23% (`--cov-fail-under=90` in CI)
- **Security tests**: 27 (IDOR, SSRF, tenant isolation, privilege escalation)
- **CI/CD**: GitHub Actions (10 jobs) + GitLab CI (9 jobs), both green
- **Docs**: 43+ files in `/docs/`, 21 SVG diagrams, 7 Jupyter notebooks

## Key Documentation

- [User Manual](docs/USER_MANUAL.md) — Complete user manual (Spanish)
- [Release Notes RC1](docs/RELEASE_NOTES_RC1.md) — RC1 release notes with security audit
- [CHANGELOG](CHANGELOG.md) — Full version history

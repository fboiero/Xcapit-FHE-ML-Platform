# Git Workflow

## Dual Remotes

| Remote | URL | Platform |
|--------|-----|----------|
| `github` | `https://github.com/fboiero/Xcapit-FHE-ML-Platform.git` | GitHub |
| `origin` | `git@gitlab.com:xcapit/privacy-platform.git` | GitLab |

Both pipelines run on push to `main`. Push to both remotes when changes are ready.

## Pre-Commit Hooks (`.pre-commit-config.yaml`)

Enforced automatically:
- **On commit**: trailing whitespace, JSON/YAML validation, file size <1MB, merge conflict detection, secrets detection, black formatting, ruff linting
- **On push**: mypy type checking (sdk/ only), pytest

## Safety Rules

- NEVER force push to `main`
- NEVER commit `.env` files, credentials, API keys, or private keys
- NEVER commit files >1MB without discussion
- Always verify staged files before committing: `git diff --cached --name-only`
- Run `pytest` before committing to ensure tests pass

## Branch Strategy

- `main` — production-ready code
- Feature branches for new work
- All changes go through CI before merge

## Sensitive Files

Already in `.gitignore` — verify before `git add`:
- `.env`, `.env.local`, `.env.production`
- `*.pem`, `*.key`
- `credentials.json`
- `db.sqlite3`
- `node_modules/`, `__pycache__/`, `.venv/`

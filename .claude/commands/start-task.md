When starting a new development task:

1. **Load context** — Read the relevant skill files from `.claude/skills/` based on what the task involves:
   - Backend changes → `django-architecture.md`, `django-rules.md`, `django-api.md`
   - Tests → `django-testing.md`
   - FHE/encryption → `fhe-domain.md`
   - Blockchain → `blockchain-domain.md`
   - Security-sensitive → `security-audit.md`

2. **Identify scope** — Determine which Django apps in `backend_django/apps/` are affected. Read their `models.py` and `views.py` to understand current state.

3. **Check test status** — Run a quick check to see what tests exist:
   ```bash
   cd backend_django && DJANGO_SETTINGS_MODULE=config.settings_test pytest --co -q 2>/dev/null | tail -5
   ```

4. **Review recent changes** — Check recent commits for context:
   ```bash
   git log --oneline -10
   ```

5. **Plan before coding** — Enter plan mode for non-trivial tasks. Consider:
   - Which services need changes?
   - What new tests are needed?
   - Are there permission or multi-tenancy implications?
   - Will this affect the API contract?

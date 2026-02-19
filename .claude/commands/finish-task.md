Before marking a task as complete, run these verification steps:

1. **Run full test suite with coverage**:
   ```bash
   cd backend_django && DJANGO_SETTINGS_MODULE=config.settings_test pytest --cov=apps --cov-report=term-missing --cov-fail-under=90
   ```

2. **Run linting**:
   ```bash
   cd backend_django && ruff check apps/ && ruff format --check apps/
   ```

3. **Verify no sensitive files staged**:
   ```bash
   git diff --cached --name-only | grep -E '\.(env|key|pem|secret)' && echo "WARNING: Sensitive files detected!" || echo "OK: No sensitive files"
   ```

4. **Verify coverage threshold** — Confirm output shows >= 90% coverage and all tests pass.

5. **Review changes** — Run `git diff` to review all modifications before committing.

6. **Commit** — Use conventional commit format (see `.claude/skills/commit-messages.md`):
   ```
   type(scope): description
   ```

7. **Summary** — Provide a brief summary of what was done, tests added, and any remaining work.

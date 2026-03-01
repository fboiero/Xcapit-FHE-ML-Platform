Fix the known pre-existing bugs documented in `.claude/skills/project-overview.md` under "Known Bugs".

For each bug:

1. **Read the affected file** to understand the current code
2. **Identify the root cause** from the bug description
3. **Implement the fix** following project conventions (see `.claude/skills/django-rules.md`)
4. **Write or update tests** to cover the fix (see `.claude/skills/django-testing.md`)
5. **Verify** the fix doesn't break existing tests:
   ```bash
   cd backend_django && DJANGO_SETTINGS_MODULE=config.settings_test pytest --cov=apps --cov-fail-under=90 -q
   ```

Known bugs to fix:
1. `core/serializers.py` — `RegisterSerializer.create()` missing `Company.email`
2. `core/views.py` — `CreateAPIKeyView.post()` uses non-existent fields `created_by`, `prefix`
3. `core/authentication.py` — `APIKeyAuthentication` select_related uses non-existent `created_by`
4. `federated/views.py:140` — `endpoint.model.version` should be `endpoint.model.current_version`

After fixing all bugs, update the "Known Bugs" section in `.claude/skills/project-overview.md` to reflect resolved status.

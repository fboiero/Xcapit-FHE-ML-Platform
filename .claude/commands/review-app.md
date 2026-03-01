Perform a code review of a specific Django app against project standards.

**Usage**: `/review-app <app_name>` (e.g., `/review-app governance`)

Steps:

1. **Read the app** — Load all key files from `backend_django/apps/$APP_NAME/`:
   - `models.py` — Check UUID PKs, TextChoices, timestamps, indexes
   - `views.py` — Check ViewSet patterns, permissions, company scoping
   - `serializers.py` — Check read/create separation, validation
   - `services/` — Check BaseService/ServiceResult pattern
   - `urls.py` — Check router registration

2. **Architecture checklist** (from `.claude/skills/code-review.md`):
   - [ ] Business logic in service layer, not views
   - [ ] ServiceResult used for all service returns
   - [ ] Multi-tenancy: queries filter by company
   - [ ] DB operations wrapped in transactions where needed

3. **API checklist**:
   - [ ] RFC 7807 error format
   - [ ] Separate read/create serializers
   - [ ] Pagination on list endpoints
   - [ ] Proper permission classes (IsAuthenticated + company scoping)
   - [ ] Query params validated

4. **Testing checklist**:
   - [ ] Happy path tests exist
   - [ ] Error/edge case tests exist
   - [ ] Multi-tenancy isolation tested
   - [ ] Coverage >= 90% for the app

5. **Security checklist**:
   - [ ] No PII in logs
   - [ ] No hardcoded secrets
   - [ ] Input validation on all user inputs
   - [ ] Rate limiting on sensitive endpoints

6. **Code quality**:
   - [ ] Type hints on new code
   - [ ] Import order (stdlib → django → drf → apps)
   - [ ] Ruff-clean
   - [ ] Meaningful naming

7. **Report** — Present findings as:
   | Area | Status | Issues Found |
   |------|--------|-------------|

   With specific file:line references for any issues.

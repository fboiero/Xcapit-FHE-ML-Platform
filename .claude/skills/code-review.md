# Code Review Checklist

## Architecture

- [ ] Business logic is in service classes (`services/`), not views
- [ ] Services return `ServiceResult[T]` (not raw exceptions for business errors)
- [ ] `ServiceResult.fail()` includes `error_code`
- [ ] Queries are scoped to `request.user.company` (multi-tenancy)
- [ ] `AuditService.log_from_request()` for significant state changes
- [ ] `@transaction.atomic` for multi-step database operations
- [ ] Models have UUID PKs, TextChoices, auto timestamps

## API Endpoints

- [ ] Error responses follow RFC 7807 format
- [ ] Separate read/create serializers where appropriate
- [ ] Pagination configured (StandardPagination default)
- [ ] Filter backends: DjangoFilterBackend, SearchFilter, OrderingFilter
- [ ] Permissions: `[IsAuthenticated, IsCompanyMember]` minimum
- [ ] `get_queryset()` filters by user's company
- [ ] `perform_create()` sets `owner=request.user.company`
- [ ] Custom actions use `@action(detail=True/False)`

## Testing

- [ ] Happy path tested
- [ ] Error/edge cases tested
- [ ] Multi-tenancy isolation tested (`other_auth_client` gets 0 results)
- [ ] Unauthenticated access returns 401
- [ ] Uses conftest fixtures (not manual user/company creation)
- [ ] Tests marked with `@pytest.mark.django_db`
- [ ] Coverage stays above 90%

## Security

- [ ] No PII in logs
- [ ] No secrets in code
- [ ] Input validated on all endpoints
- [ ] Rate limiting on public/sensitive endpoints
- [ ] Error responses don't expose internals
- [ ] No raw SQL
- [ ] `select_related`/`prefetch_related` only on existing fields

## Code Quality

- [ ] Type hints on all new functions
- [ ] `from __future__ import annotations` if using forward refs
- [ ] Import order: stdlib → django → third-party → local
- [ ] ruff check passes
- [ ] Naming conventions followed (see `django-rules.md`)
- [ ] No unnecessary complexity (YAGNI)
- [ ] Docstrings on public classes and methods

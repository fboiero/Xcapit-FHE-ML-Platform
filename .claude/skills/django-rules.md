# Django Coding Rules

These are mandatory rules for all new code. Not suggestions — enforced conventions.

## Type Hints

- Required on all new functions (parameters + return types)
- Use `from __future__ import annotations` for forward references
- Use `TYPE_CHECKING` guard for circular imports:

```python
from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from apps.core.models import Company, User
```

## Import Order

1. `__future__` imports
2. Standard library (`os`, `uuid`, `datetime`, etc.)
3. Django (`django.db`, `django.conf`, etc.)
4. Third-party (`rest_framework`, `django_filters`, `celery`, etc.)
5. Local apps (`apps.core`, `apps.consortiums`, etc.)

Enforced by ruff.

## Service Layer Rules

- Business logic goes in `services/`, NEVER in views
- Return `ServiceResult[T]` for expected outcomes (success/failure)
- Use `ServiceResult.fail("message", error_code="code")` for expected errors
- Raise exceptions ONLY for programming errors (bugs)
- Always provide `error_code` in `ServiceResult.fail()`
- Use `@transaction.atomic` for multi-step operations
- Use `AuditService.log_from_request()` for significant operations

## Model Rules

- UUID primary keys on all models
- `TextChoices` for all enums (never IntegerChoices, never raw strings)
- `JSONField` for flexible data (NEVER pickle)
- `auto_now_add=True` for `created_at`, `auto_now=True` for `updated_at`
- `on_delete=models.PROTECT` for important ForeignKeys (not CASCADE)
- `__str__` method on all models
- Indexes on status fields, ForeignKeys, and commonly filtered fields

## Security Rules

- NEVER expose internal error details in API responses
- NEVER store raw API keys — SHA-256 hash only
- NEVER log PII (email, passwords, tokens, IP addresses in non-security contexts)
- ALWAYS scope queries to `request.user.company` (multi-tenancy)
- ALWAYS validate permissions before data access
- NEVER use `select_related` or `prefetch_related` on fields that don't exist

## Code Quality

- Linting: `ruff check` + `ruff format` (enforced in CI)
- No raw SQL — use Django ORM. If unavoidable, use parameterized queries
- Use `F()` expressions for counter increments
- Use `select_related()` for FK joins, `prefetch_related()` for M2M
- Prefer `get_queryset()` filtering over manual QuerySet construction in views
- No wildcard imports (`from module import *`)

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Models | PascalCase | `MLModel`, `ConsortiumMember` |
| Fields | snake_case | `model_type`, `created_at` |
| Methods | snake_case | `get_queryset()`, `perform_create()` |
| Serializers | `{Model}Serializer` | `MLModelSerializer`, `MLModelCreateSerializer` |
| Services | `{Entity}Service` | `ConsortiumService`, `AuditService` |
| Permissions | `Is{Condition}` | `IsCompanyMember`, `IsResourceOwner` |
| URLs | kebab-case | `data-quality/`, `competitive/` |

## Docstrings

- Module-level docstring on every `.py` file
- Google-style docstrings on public classes and methods
- Keep them concise — don't document the obvious

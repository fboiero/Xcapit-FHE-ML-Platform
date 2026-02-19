# Django REST API Standards

## DRF Configuration (from `config/settings.py`)

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.core.exceptions.custom_exception_handler",
}
```

## JWT Authentication Flow

```bash
# 1. Obtain tokens
POST /api/v2/auth/token/
{"email": "user@example.com", "password": "password"}
# Returns: {"access": "...", "refresh": "..."}

# 2. Use access token (30-min lifetime)
Authorization: Bearer <access_token>

# 3. Refresh token (7-day lifetime, rotation enabled)
POST /api/v2/auth/token/refresh/
{"refresh": "<refresh_token>"}

# 4. Logout (blacklists refresh token)
POST /api/v2/auth/logout/
{"refresh": "<refresh_token>"}
```

## Query Parameters

| Parameter | Example | Description |
|-----------|---------|-------------|
| `page` | `?page=2` | Page number (default: 1) |
| `page_size` | `?page_size=100` | Items per page (default: 50, max: 200) |
| `ordering` | `?ordering=-created_at` | Sort field (prefix `-` for descending) |
| `search` | `?search=term` | Full-text search across search_fields |
| `field=value` | `?status=active` | Django-filter exact match |

## Pagination Response Format

```json
{
  "count": 150,
  "total_pages": 3,
  "current_page": 1,
  "page_size": 50,
  "next": "http://api/v2/models/?page=2",
  "previous": null,
  "results": [...]
}
```

## Error Response Format (RFC 7807)

All errors follow this structure:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Human-readable message",
    "status": 400,
    "details": {"field": ["error message"]}
  }
}
```

## Custom Exceptions (from `apps/core/exceptions.py`)

| Exception | Status | Code |
|-----------|--------|------|
| `ServiceUnavailable` | 503 | `service_unavailable` |
| `ConflictError` | 409 | `conflict` |
| `RateLimitExceeded` | 429 | `rate_limit_exceeded` |
| `InsufficientPermissions` | 403 | `insufficient_permissions` |
| `ResourceNotFound` | 404 | `not_found` |

The custom exception handler (`custom_exception_handler`) sanitizes all errors — never exposes internal details or stack traces.

## Serializer Patterns

### Separate Read/Create Serializers

```python
class MyModelSerializer(serializers.ModelSerializer):
    """Read serializer — includes computed/nested fields."""
    owner_name = serializers.CharField(source="owner.name", read_only=True)

    class Meta:
        model = MyModel
        fields = ["id", "name", "owner", "owner_name", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "owner", "status", "created_at", "updated_at"]


class MyModelCreateSerializer(serializers.ModelSerializer):
    """Write serializer — minimal fields for creation."""
    class Meta:
        model = MyModel
        fields = ["id", "name", "description", "config"]
        read_only_fields = ["id"]

    def validate_name(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Name must be at least 3 characters.")
        return value
```

### Validation

- Use `validate_<field>()` for single-field validation
- Use `validate()` for cross-field validation
- Raise `serializers.ValidationError` with descriptive messages

## Rate Limiting

- Anonymous: 100 requests/hour
- Authenticated: 1,000 requests/hour
- Enforced by django-ratelimit + DRF throttling

## API Versioning

All endpoints are under `/api/v2/`. API docs via drf-spectacular at `/api/v2/docs/` (Swagger UI) and `/api/v2/schema/` (OpenAPI JSON).

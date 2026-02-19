# Django Testing

## Test Configuration

```bash
# Run all tests
cd backend_django && DJANGO_SETTINGS_MODULE=config.settings_test pytest

# With coverage
pytest --cov=apps --cov-report=term-missing --cov-fail-under=90

# Specific test file
pytest tests/test_models_views.py -v

# Specific test
pytest tests/test_models_views.py::TestMLModelViewSet::test_create_model -v
```

## Test Settings (`config/settings_test.py`)

- **Database**: SQLite (in-memory, fast)
- **Cache**: DummyCache (no-op)
- **Rate limiting**: Disabled (RATELIMIT_ENABLE=False)
- **Axes**: Disabled (AXES_ENABLED=False)
- **Password hasher**: MD5 (fastest for tests)
- **Password validation**: Min 8 chars only

## Fixtures (from `tests/conftest.py`)

| Fixture | Returns | Description |
|---------|---------|-------------|
| `api_client` | `APIClient` | Unauthenticated REST client |
| `company` | `Company` | Test company (technology industry) |
| `other_company` | `Company` | Second company (finance industry) |
| `user` | `User` | Regular user with `company` |
| `other_user` | `User` | User with `other_company` |
| `admin_user` | `User` | Superuser with `company` |
| `auth_client` | `APIClient` | JWT-authenticated as `user` |
| `other_auth_client` | `APIClient` | JWT-authenticated as `other_user` |
| `admin_client` | `APIClient` | JWT-authenticated as `admin_user` |
| `consortium` | `Consortium` | Active consortium owned by `company` |
| `ml_model` | `MLModel` | Trained logistic regression model |

### Authentication Pattern

```python
from rest_framework_simplejwt.tokens import RefreshToken

refresh = RefreshToken.for_user(user)
api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
```

## Test Patterns

### API Endpoint Test

```python
@pytest.mark.django_db
class TestMyModelViewSet:
    def test_list_returns_only_own_company(self, auth_client, other_auth_client, company):
        """Users only see their own company's resources."""
        MyModel.objects.create(name="Mine", owner=company)
        response = auth_client.get("/api/v2/mymodel/")
        assert response.status_code == 200
        assert response.data["count"] == 1

    def test_other_company_cannot_access(self, other_auth_client, company):
        """Multi-tenancy isolation: other company gets 0 results."""
        MyModel.objects.create(name="Not yours", owner=company)
        response = other_auth_client.get("/api/v2/mymodel/")
        assert response.data["count"] == 0

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get("/api/v2/mymodel/")
        assert response.status_code == 401

    def test_create(self, auth_client):
        response = auth_client.post("/api/v2/mymodel/", {"name": "New Model"})
        assert response.status_code == 201
        assert response.data["name"] == "New Model"
```

### Service Test

```python
@pytest.mark.django_db
class TestMyService:
    def test_process_success(self, user, company):
        context = ServiceContext(user=user, company=company)
        service = MyService(context=context)
        result = service.process({"field": "value"})
        assert result.success is True
        assert result.data is not None

    def test_process_validation_failure(self, user, company):
        context = ServiceContext(user=user, company=company)
        service = MyService(context=context)
        result = service.process({})
        assert result.success is False
        assert result.error_code == "validation_error"
```

### Custom Action Test

```python
def test_custom_action(self, auth_client, ml_model):
    response = auth_client.post(f"/api/v2/models/{ml_model.id}/train/", {"epochs": 10})
    assert response.status_code == 200
```

## Coverage Requirements

- **CI enforces**: `--cov-fail-under=90`
- **Current**: 95.12% (1,442 tests)
- **Total tests**: ~2,062 (1,442 Django + ~620 SDK)

### Modules Below 90% Coverage

| Module | Coverage | Remaining Lines |
|--------|----------|-----------------|
| `blockchain/services.py` | 67% | 71 lines (Web3 mocking complexity) |
| `blockchain/resilience.py` | 87% | 23 lines |
| `sandbox/services/sandbox.py` | 89% | 7 lines |
| `consortiums/services/blockchain.py` | 89% | 10 lines |

## Testing Rules

1. Always test multi-tenancy isolation (use `other_auth_client`)
2. Always test unauthenticated access returns 401
3. Test both happy path and error cases
4. Use conftest fixtures — don't create users/companies manually
5. Mark DB tests with `@pytest.mark.django_db` (or use fixtures with `db`)
6. Run `pytest` before committing

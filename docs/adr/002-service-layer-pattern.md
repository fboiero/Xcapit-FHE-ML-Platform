# ADR-002: Service Layer Pattern

## Status
Accepted

## Date
2026-01-24

## Context

The Django REST Framework ViewSets were accumulating business logic, leading to:

1. **ViewSets over 400 lines**: `sandbox/views.py`, `federated/views.py`, `consortiums/views.py`
2. **Code duplication**: Similar logic scattered across ViewSets
3. **Testing difficulty**: Business logic mixed with HTTP handling
4. **Reusability issues**: Logic not accessible outside HTTP context

### Problem Examples

```python
# Before: Business logic in ViewSet (bad)
class SyntheticDatasetViewSet(viewsets.ModelViewSet):
    @action(detail=False, methods=["post"])
    def generate(self, request):
        # 80+ lines of business logic
        features = self._get_default_features(dataset_type)
        preview = self._generate_preview(features, count)
        statistics = self._calculate_statistics(features, record_count)
        # More logic...
```

## Decision

Adopt a **Service Layer Pattern** where:

1. **ViewSets handle HTTP concerns only**
   - Request/response serialization
   - Permission checking
   - HTTP status codes

2. **Services contain business logic**
   - Data validation beyond schema
   - Complex operations
   - Cross-model transactions
   - Audit logging

3. **Follow existing `BaseService` pattern**
   - Located in `apps/core/services/base.py`
   - Uses `ServiceResult` for consistent return values
   - Accepts `ServiceContext` for user/request context

### Service Structure

```
apps/<app_name>/services/
├── __init__.py          # Exports all services
├── <domain>.py          # Domain-specific service
└── ...
```

### Service Pattern

```python
from apps.core.services.base import BaseService, ServiceResult, ServiceContext

class ExperimentService(BaseService):
    """Service for experiment operations."""

    def run_experiment(self, experiment: Experiment) -> ServiceResult[dict]:
        # Validate
        if experiment.status != "pending":
            return ServiceResult.fail("Invalid status", error_code="invalid_status")

        # Process
        with transaction.atomic():
            results = self._execute(experiment)
            experiment.complete(results)

        # Audit
        if self.request:
            AuditService.log_from_request(...)

        return ServiceResult.ok(results)
```

## Implementation

### Phase 1: Sandbox & Federated (Completed)
- `apps/sandbox/services/data_generation.py`
- `apps/sandbox/services/experiment.py`
- `apps/sandbox/services/sandbox.py`
- `apps/federated/services/inference.py`
- `apps/federated/services/federated_model.py`
- `apps/federated/services/edge_node.py`

### Phase 2: Consortiums (Completed)
- `apps/consortiums/services/invitation.py`
- `apps/consortiums/services/contribution.py`
- Existing: `consortium.py`, `member.py`

### ViewSet Integration

```python
# After: ViewSet delegates to service (good)
class ExperimentViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=["post"])
    def run(self, request, pk=None):
        experiment = self.get_object()

        service = ExperimentService(ServiceContext.from_request(request))
        result = service.run_experiment(experiment)

        if not result.success:
            return Response(
                {"detail": result.error},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({
            "status": experiment.status,
            "results": result.data,
        })
```

## Consequences

### Positive
- **Testability**: Services can be unit tested without HTTP
- **Reusability**: Logic accessible from Celery tasks, management commands
- **Maintainability**: Clear separation of concerns
- **Consistency**: `ServiceResult` provides uniform error handling

### Negative
- **More files**: Each domain has a service file
- **Indirection**: Extra layer between ViewSet and Model
- **Learning curve**: Team must adopt pattern consistently

### Neutral
- **No performance impact**: Minimal overhead
- **Gradual adoption**: ViewSets can be migrated incrementally

## Testing Strategy

```python
# Unit test for service (no HTTP)
def test_run_experiment_success():
    experiment = ExperimentFactory(status="pending")
    service = ExperimentService()

    result = service.run_experiment(experiment)

    assert result.success
    assert experiment.status == "completed"
```

## Related Decisions
- ADR-001: JSONField Usage (services receive validated data)
- ADR-003: Blockchain Resilience (services handle retries)

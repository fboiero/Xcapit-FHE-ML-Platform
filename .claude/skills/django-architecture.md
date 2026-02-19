# Django Architecture

## App File Structure

Every Django app follows this structure:

```
apps/example_app/
├── __init__.py
├── models.py           # Django models
├── serializers.py      # DRF serializers
├── views.py            # ViewSets and API views
├── urls.py             # URL routing (DefaultRouter)
├── permissions.py      # Custom permissions (optional)
├── filters.py          # Django-filter filtersets (optional)
├── services/           # Business logic (service layer)
│   ├── __init__.py
│   └── example.py      # Service classes
├── migrations/         # Database migrations
└── tests.py            # App-specific tests (optional)
```

## Service Layer Pattern

All business logic MUST go in service classes, never in views. Views handle HTTP concerns only.

### Core Classes (from `apps/core/services/base.py`)

```python
from apps.core.services.base import BaseService, ServiceResult, ServiceContext

# Create context from request
context = ServiceContext.from_request(request)

# Initialize service
service = MyService(context=context)

# Return results
ServiceResult.ok(data)                                    # Success
ServiceResult.fail("message", error_code="code")          # Expected failure
ServiceResult.fail("msg", error_code="code", details={})  # With details
```

### Service Implementation Pattern

```python
from apps.core.services.base import BaseService, ServiceResult

class ExampleService(BaseService):
    def process(self, data: dict) -> ServiceResult[Model]:
        # 1. Validate
        if not data.get("field"):
            return ServiceResult.fail("Field is required", error_code="validation_error")

        # 2. Process (use @transaction.atomic for multi-step)
        result = Model.objects.create(**data)

        # 3. Audit log
        if self.request:
            from apps.core.services.audit import AuditService
            AuditService.log_from_request(
                self.request,
                action="created",
                resource_type="model",
                resource_id=result.id,
            )

        return ServiceResult.ok(result)
```

### BaseService Helpers

- `self.user` — Current authenticated user (or None)
- `self.company` — Current user's company (or None)
- `self.request` — Current HTTP request (or None)
- `self.require_user()` — Raises PermissionError if not authenticated
- `self.require_company()` — Raises PermissionError if no company

## Model Conventions

```python
import uuid
from django.db import models

class MyModel(models.Model):
    # Always UUID primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Always auto timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Always TextChoices for enums (never IntegerChoices, never raw strings)
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    # Company-scoped (multi-tenancy)
    owner = models.ForeignKey("core.Company", on_delete=models.PROTECT, related_name="my_models")

    # JSONField for flexible config (NEVER pickle)
    config = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["owner"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return self.name
```

## ViewSet Pattern

```python
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.permissions import IsCompanyMember, IsResourceOwner

class MyModelViewSet(viewsets.ModelViewSet):
    serializer_class = MyModelSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "model_type"]
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "name"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Always filter by authenticated user's company."""
        if self.request.user.company:
            return MyModel.objects.filter(
                owner=self.request.user.company
            ).select_related("owner")
        return MyModel.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return MyModelCreateSerializer
        return MyModelSerializer

    def get_permissions(self):
        if self.action in ["update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsResourceOwner()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user.company)

    @action(detail=True, methods=["post"])
    def custom_action(self, request, pk=None):
        obj = self.get_object()
        # Use service layer for business logic
        context = ServiceContext.from_request(request)
        service = MyService(context=context)
        result = service.process(obj)
        if not result.success:
            return Response({"error": result.error}, status=400)
        return Response(MyModelSerializer(result.data).data)
```

## Permission Classes (from `apps/core/permissions.py`)

| Class | Checks |
|-------|--------|
| `IsCompanyMember` | User has a company assigned |
| `IsConsortiumMember` | User's company is active member of consortium |
| `IsConsortiumOwner` | User's company owns the consortium |
| `IsConsortiumAdmin` | User's company is owner or admin of consortium |
| `IsResourceOwner` | Object's `owner` or `company` matches user's company |
| `HasAPIKeyPermission` | API key has required permission level |
| `ReadOnly` | Only SAFE_METHODS (GET, HEAD, OPTIONS) |
| `IsActiveUser` | User.is_active is True |
| `IsVerifiedCompany` | Company.is_verified is True |

## URL Registration

```python
# apps/example/urls.py
from rest_framework.routers import DefaultRouter
from .views import MyModelViewSet

router = DefaultRouter()
router.register(r"", MyModelViewSet, basename="mymodel")

urlpatterns = router.urls

# config/urls.py — all under /api/v2/
path("api/v2/example/", include("apps.example.urls")),
```

## Key Services

- `apps.core.services.AuditService` — Audit logging for all operations
- `apps.consortiums.services.ConsortiumService` — Consortium CRUD + stats + rankings
- `apps.consortiums.services.MemberService` — Member management + invitations
- `apps.consortiums.services.FHETrainingService` — FHE training orchestration
- `apps.data_quality.services.QualityAssessmentService` — Data quality scoring

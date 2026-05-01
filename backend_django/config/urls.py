"""
Root URL configuration for Xcapit FHE-ML Platform.
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.core.healthchecks import HealthCheckView, LivenessCheckView, ReadinessCheckView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Health checks
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("health/live/", LivenessCheckView.as_view(), name="health-liveness"),
    path("health/ready/", ReadinessCheckView.as_view(), name="health-readiness"),
    # API documentation (OpenAPI 3.0)
    path("api/v2/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v2/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/v2/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # API endpoints
    path("api/v2/", include("apps.core.urls")),
    path("api/v2/sandbox/", include("apps.sandbox.urls")),
    path("api/v2/", include("apps.consortiums.urls")),
    path("api/v2/blockchain/", include("apps.blockchain.urls")),
    path("api/v2/governance/", include("apps.governance.urls")),
    path("api/v2/marketplace/", include("apps.marketplace.urls")),
    path("api/v2/compliance/", include("apps.compliance.urls")),
    path("api/v2/data-quality/", include("apps.data_quality.urls")),
    path("api/v2/federated/", include("apps.federated.urls")),
    path("api/v2/models/", include("apps.models.urls")),
    path("api/v2/ensemble/", include("apps.ensemble.urls")),
    path("api/v2/competitive/", include("apps.competitive_insights.urls")),
    path("api/v2/explainability/", include("apps.explainability.urls")),
]

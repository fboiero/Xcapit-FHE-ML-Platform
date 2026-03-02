"""
URL Configuration for Xcapit FHE-ML Platform.

API v2 using Django REST Framework.
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.core.healthchecks import HealthCheckView, LivenessCheckView, ReadinessCheckView

urlpatterns = [
    # Health checks (enhanced)
    path("health/", HealthCheckView.as_view(), name="health"),
    path("health/live/", LivenessCheckView.as_view(), name="liveness"),
    path("health/ready/", ReadinessCheckView.as_view(), name="readiness"),
    # Legacy health check (django-health-check)
    path("health/legacy/", include("health_check.urls")),
    # API v2
    path(
        "api/v2/",
        include(
            [
                # Authentication
                path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain"),
                path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
                # Core
                path("", include("apps.core.urls")),
                # Consortiums
                path("consortiums/", include("apps.consortiums.urls")),
                # Governance
                path("governance/", include("apps.governance.urls")),
                # Models
                path("models/", include("apps.models.urls")),
                # Compliance
                path("compliance/", include("apps.compliance.urls")),
                # Marketplace
                path("marketplace/", include("apps.marketplace.urls")),
                # Sandbox
                path("sandbox/", include("apps.sandbox.urls")),
                # Federated
                path("federated/", include("apps.federated.urls")),
                # Data Quality (New)
                path("data-quality/", include("apps.data_quality.urls")),
                # Competitive Insights (New)
                path("competitive/", include("apps.competitive_insights.urls")),
                # Ensemble (New)
                path("ensemble/", include("apps.ensemble.urls")),
                # Explainability (New)
                path("explainability/", include("apps.explainability.urls")),
                # Blockchain
                path("blockchain/", include("apps.blockchain.urls")),
            ]
        ),
    ),
]

# Admin and API docs only available in DEBUG mode
if settings.DEBUG:
    urlpatterns += [
        path("admin/", admin.site.urls),
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        path(
            "api/docs/",
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="swagger-ui",
        ),
        path(
            "api/redoc/",
            SpectacularRedocView.as_view(url_name="schema"),
            name="redoc",
        ),
    ]

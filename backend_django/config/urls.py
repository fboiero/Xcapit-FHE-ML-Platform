"""
URL Configuration for Xcapit FHE-ML Platform.

API v2 using Django REST Framework.
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # Health check
    path("health/", include("health_check.urls")),
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
            ]
        ),
    ),
    # API Documentation
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

"""
Explainability URL configuration.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ExplainabilityDashboardView,
    ExplanationRequestViewSet,
    FeatureImportanceViewSet,
    ModelInsightViewSet,
)

router = DefaultRouter()
router.register(r"requests", ExplanationRequestViewSet, basename="explanation-request")
router.register(r"features", FeatureImportanceViewSet, basename="feature-importance")
router.register(r"insights", ModelInsightViewSet, basename="model-insight")
router.register(r"dashboard", ExplainabilityDashboardView, basename="explainability-dashboard")

urlpatterns = [
    path("", include(router.urls)),
]

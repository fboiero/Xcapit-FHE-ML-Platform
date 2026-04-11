"""
Data quality URL configuration for Xcapit FHE-ML Platform.
"""

from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    QualityAlertViewSet,
    QualityAssessmentViewSet,
    QualityDashboardView,
    QualityRuleViewSet,
)

router = DefaultRouter()
router.register(r"assessments", QualityAssessmentViewSet, basename="quality-assessment")
router.register(r"rules", QualityRuleViewSet, basename="quality-rule")
router.register(r"alerts", QualityAlertViewSet, basename="quality-alert")
router.register(r"dashboard", QualityDashboardView, basename="quality-dashboard")

urlpatterns = [
    path("", include(router.urls)),
]

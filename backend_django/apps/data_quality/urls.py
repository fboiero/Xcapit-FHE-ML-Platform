"""
Data quality URL configuration.
"""

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
router.register(r"alerts", QualityAlertViewSet, basename="quality-alert")
router.register(r"dashboard", QualityDashboardView, basename="quality-dashboard")

# Nested router for rules under consortiums
rules_router = DefaultRouter()
rules_router.register(r"rules", QualityRuleViewSet, basename="quality-rule")

urlpatterns = [
    path("", include(router.urls)),
]

"""
Compliance URL configuration for Xcapit FHE-ML Platform.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"frameworks", views.ComplianceFrameworkViewSet, basename="framework")
router.register(r"settings", views.ConsortiumComplianceViewSet, basename="compliance-settings")
router.register(r"checks", views.ComplianceCheckViewSet, basename="compliance-check")
router.register(r"reports", views.ComplianceReportViewSet, basename="compliance-report")
router.register(r"attestations", views.AttestationViewSet, basename="attestation")
router.register(r"data-processing", views.DataProcessingRecordViewSet, basename="data-processing")

urlpatterns = [
    path("", include(router.urls)),
]

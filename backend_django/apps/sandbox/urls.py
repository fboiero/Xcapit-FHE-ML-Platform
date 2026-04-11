"""
Sandbox URL configuration for Xcapit FHE-ML Platform.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"templates", views.SandboxTemplateViewSet, basename="sandbox-template")
router.register(r"datasets", views.SyntheticDatasetViewSet, basename="synthetic-dataset")
router.register(r"experiments", views.ExperimentViewSet, basename="experiment")
router.register(r"sandboxes", views.SandboxViewSet, basename="sandbox")

urlpatterns = [
    # Public endpoints (no auth required)
    path("leads/", views.SandboxLeadView.as_view(), name="sandbox-lead"),
    path("leads/verify/", views.SandboxLeadVerifyView.as_view(), name="sandbox-lead-verify"),
    # Consortium demo (public with sandbox token)
    path("consortium-demo/", views.ConsortiumDemoView.as_view(), name="consortium-demo"),
    path("consortium-demo/limits/", views.ConsortiumDemoLimitsView.as_view(), name="consortium-demo-limits"),
    # Plans comparison (public)
    path("plans/", views.PlansComparisonView.as_view(), name="plans-comparison"),
    # Trial management (authenticated)
    path("trial/start/", views.TrialStartView.as_view(), name="trial-start"),
    path("trial/status/", views.TrialStatusView.as_view(), name="trial-status"),
    path("trial/usage/", views.TrialUsageView.as_view(), name="trial-usage"),
    path("trial/upgrade/", views.TrialUpgradeView.as_view(), name="trial-upgrade"),
    path("trial/upload-data/", views.TrialUploadDataView.as_view(), name="trial-upload-data"),
    # Authenticated endpoints
    path("", include(router.urls)),
]

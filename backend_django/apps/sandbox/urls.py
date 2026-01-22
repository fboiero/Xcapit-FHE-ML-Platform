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
    path("", include(router.urls)),
]

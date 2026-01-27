"""
ML Model URL configuration for Xcapit FHE-ML Platform.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

# Note: specific routes must be registered before the catch-all empty prefix route
router = DefaultRouter()
router.register(r"training-runs", views.TrainingRunViewSet, basename="training-run")
router.register(r"predictions", views.PredictionLogViewSet, basename="prediction-log")
router.register(r"batch-jobs", views.BatchPredictionJobViewSet, basename="batch-job")
router.register(r"versions", views.ModelVersionViewSet, basename="model-version")
router.register(r"exports", views.ModelExportViewSet, basename="model-export")
router.register(r"shares", views.ModelShareViewSet, basename="model-share")
router.register(r"share-requests", views.ModelShareRequestViewSet, basename="model-share-request")
router.register(r"", views.MLModelViewSet, basename="model")

urlpatterns = [
    path("", include(router.urls)),
]

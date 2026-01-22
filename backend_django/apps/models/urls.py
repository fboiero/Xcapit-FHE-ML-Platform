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
router.register(r"", views.MLModelViewSet, basename="model")

urlpatterns = [
    path("", include(router.urls)),
]

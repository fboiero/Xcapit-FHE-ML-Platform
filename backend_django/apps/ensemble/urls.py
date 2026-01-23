"""
Ensemble URL configuration.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import EnsemblePredictionViewSet, EnsembleViewSet

router = DefaultRouter()
router.register(r"", EnsembleViewSet, basename="ensemble")
router.register(r"predictions", EnsemblePredictionViewSet, basename="ensemble-prediction")

urlpatterns = [
    path("", include(router.urls)),
]

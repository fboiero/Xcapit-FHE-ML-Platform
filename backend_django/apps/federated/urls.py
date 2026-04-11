"""
Federated inference URL configuration for Xcapit FHE-ML Platform.
"""

from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"models", views.FederatedModelViewSet, basename="federated-model")
router.register(r"endpoints", views.InferenceEndpointViewSet, basename="inference-endpoint")
router.register(r"requests", views.InferenceRequestViewSet, basename="inference-request")
router.register(r"nodes", views.EdgeNodeViewSet, basename="edge-node")

urlpatterns = [
    path("", include(router.urls)),
]

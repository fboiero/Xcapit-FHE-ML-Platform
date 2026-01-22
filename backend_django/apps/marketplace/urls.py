"""
Marketplace URL configuration for Xcapit FHE-ML Platform.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"categories", views.CategoryViewSet, basename="category")
router.register(r"models", views.MarketplaceModelViewSet, basename="marketplace-model")
router.register(r"deployments", views.DeploymentViewSet, basename="deployment")
router.register(r"reviews", views.ReviewViewSet, basename="review")

urlpatterns = [
    path("", include(router.urls)),
]

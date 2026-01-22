"""
Consortium URL configuration for Xcapit FHE-ML Platform.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from . import views

# Main router - specific routes must be registered before the catch-all empty prefix
router = DefaultRouter()
router.register(r"invitations", views.ConsortiumInvitationViewSet, basename="invitation")
router.register(r"", views.ConsortiumViewSet, basename="consortium")

# Nested router for consortium resources
consortium_router = routers.NestedDefaultRouter(router, r"", lookup="consortium")
consortium_router.register(r"members", views.ConsortiumMemberViewSet, basename="consortium-members")
consortium_router.register(
    r"contributions", views.ContributionProofViewSet, basename="consortium-contributions"
)

urlpatterns = [
    path("", include(router.urls)),
    path("", include(consortium_router.urls)),
]

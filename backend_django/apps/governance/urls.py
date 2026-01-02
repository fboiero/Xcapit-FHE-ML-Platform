"""
Governance URL configuration for Xcapit FHE-ML Platform.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"proposals", views.ProposalViewSet, basename="proposal")
router.register(r"votes", views.VoteViewSet, basename="vote")
router.register(r"audit-events", views.AuditEventViewSet, basename="audit")
router.register(r"rewards", views.RewardDistributionViewSet, basename="reward")

urlpatterns = [
    path("", include(router.urls)),
]

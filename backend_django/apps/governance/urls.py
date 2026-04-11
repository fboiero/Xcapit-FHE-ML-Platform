"""
Governance URL configuration for Xcapit FHE-ML Platform.
"""

from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"proposals", views.ProposalViewSet, basename="proposal")
router.register(r"votes", views.VoteViewSet, basename="vote")
router.register(r"config", views.GovernanceConfigViewSet, basename="governance-config")
router.register(r"audit-events", views.AuditEventViewSet, basename="audit")
router.register(r"rewards", views.RewardDistributionViewSet, basename="reward")

urlpatterns = [
    path("", include(router.urls)),
]

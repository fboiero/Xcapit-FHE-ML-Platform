"""
Core URL configuration for Xcapit FHE-ML Platform.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from .authentication import (
    ChangePasswordView,
    CreateAPIKeyView,
    LoginView,
    LogoutView,
    MeView,
    RegisterView,
)

router = DefaultRouter()
router.register(r"companies", views.CompanyViewSet, basename="company")
router.register(r"users", views.UserViewSet, basename="user")
router.register(r"api-keys", views.APIKeyViewSet, basename="apikey")
router.register(r"audit-logs", views.AuditLogViewSet, basename="auditlog")
router.register(r"webhooks", views.WebhookViewSet, basename="webhook")
router.register(r"webhook-deliveries", views.WebhookDeliveryViewSet, basename="webhook-delivery")
router.register(r"usage-stats", views.UsageStatsViewSet, basename="usage-stats")
router.register(r"reports", views.ReportViewSet, basename="report")
router.register(r"workflows", views.WorkflowViewSet, basename="workflow")
router.register(r"workflow-runs", views.WorkflowRunViewSet, basename="workflow-run")
router.register(r"scheduled-tasks", views.ScheduledTaskViewSet, basename="scheduled-task")
router.register(r"scheduled-task-runs", views.ScheduledTaskRunViewSet, basename="scheduled-task-run")

urlpatterns = [
    path("", include(router.urls)),
    path("health/", views.HealthCheckView.as_view(), name="health"),
    # Authentication endpoints
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("auth/api-keys/create/", CreateAPIKeyView.as_view(), name="create-api-key"),
]

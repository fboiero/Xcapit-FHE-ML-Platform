"""
Core views for Xcapit FHE-ML Platform.

Provides endpoints for user management, company management,
API keys, and system health.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.views import APIView

from .models import (
    APIKey,
    AuditLog,
    Company,
    Report,
    ScheduledTask,
    ScheduledTaskRun,
    UsageTracking,
    Webhook,
    WebhookDelivery,
    Workflow,
    WorkflowRun,
)
from .permissions import IsCompanyMember
from .serializers import (
    APIKeyCreateSerializer,
    APIKeyResponseSerializer,
    APIKeySerializer,
    AuditLogSerializer,
    ChangePasswordSerializer,
    CompanyCreateSerializer,
    CompanySerializer,
    HealthCheckSerializer,
    ReportCreateSerializer,
    ReportSerializer,
    ScheduledTaskCreateSerializer,
    ScheduledTaskRunSerializer,
    ScheduledTaskSerializer,
    UsageStatsSerializer,
    UsageTrackingSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
    WebhookCreateSerializer,
    WebhookDeliverySerializer,
    WebhookResponseSerializer,
    WebhookSerializer,
    WorkflowCreateSerializer,
    WorkflowRunCreateSerializer,
    WorkflowRunSerializer,
    WorkflowSerializer,
)

if TYPE_CHECKING:
    pass

User = get_user_model()


class HealthCheckView(APIView):
    """
    System health check endpoint.

    Returns system status and version information.
    """

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        """Return health status."""
        data = {
            "status": "healthy",
            "version": "2.0.0",
            "timestamp": timezone.now(),
        }
        serializer = HealthCheckSerializer(data)
        return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def ratelimited_error(request: Request, exception: Exception | None = None) -> Response:
    """Custom view for rate limit exceeded responses."""
    return Response(
        {
            "error": {
                "code": "rate_limit_exceeded",
                "message": "Rate limit exceeded. Please try again later.",
                "status": 429,
            }
        },
        status=status.HTTP_429_TOO_MANY_REQUESTS,
    )


class CompanyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Company management.

    Only users can view/edit their own company.
    """

    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self) -> QuerySet[Company]:
        """Filter to user's company only."""
        user = self.request.user
        if user.company:
            return Company.objects.filter(id=user.company.id)
        return Company.objects.none()

    def get_serializer_class(self) -> type[Serializer]:
        """Use different serializer for create."""
        if self.action == "create":
            return CompanyCreateSerializer
        return CompanySerializer

    @action(detail=False, methods=["get"])
    def me(self, request: Request) -> Response:
        """Get current user's company."""
        company = request.user.company
        if not company:
            return Response(
                {"detail": "No company associated with this user."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(company)
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User management.

    Users can only view/edit their own profile.
    Company admins can view users in their company.
    """

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        """Filter to users in the same company."""
        user = self.request.user
        if user.company:
            return User.objects.filter(company=user.company)
        return User.objects.filter(id=user.id)

    def get_serializer_class(self) -> type[Serializer]:
        """Use different serializers for different actions."""
        if self.action == "create":
            return UserCreateSerializer
        if self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        return UserSerializer

    @action(detail=False, methods=["get", "patch"])
    def me(self, request: Request) -> Response:
        """Get or update current user's profile."""
        user = request.user

        if request.method == "PATCH":
            serializer = UserUpdateSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            # Log profile update
            AuditLog.log(
                request,
                action="profile_updated",
                resource_type="user",
                resource_id=user.id,
            )

        serializer = UserSerializer(user)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def change_password(self, request: Request) -> Response:
        """Change current user's password."""
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        # Set new password
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()

        # Log password change
        AuditLog.log(
            request,
            action="password_changed",
            resource_type="user",
            resource_id=request.user.id,
        )

        return Response({"detail": "Password changed successfully."})


class APIKeyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for API Key management.

    Users can create and manage API keys for their company.
    """

    serializer_class = APIKeySerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self) -> QuerySet[APIKey]:
        """Filter to company's API keys."""
        user = self.request.user
        if user.company:
            return APIKey.objects.filter(company=user.company)
        return APIKey.objects.none()

    def get_serializer_class(self) -> type[Serializer]:
        """Use different serializers for create and response."""
        if self.action == "create":
            return APIKeyCreateSerializer
        return APIKeySerializer

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Create new API key and return with raw key (once)."""
        serializer = APIKeyCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        api_key = serializer.save()

        # Log API key creation
        AuditLog.log(
            request,
            action="api_key_created",
            resource_type="api_key",
            resource_id=api_key.id,
            extra_data={"name": api_key.name},
        )

        # Return with raw key
        response_serializer = APIKeyResponseSerializer(api_key)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def revoke(self, request: Request, pk: str | None = None) -> Response:
        """Revoke an API key."""
        api_key = self.get_object()
        api_key.is_active = False
        api_key.save(update_fields=["is_active"])

        # Log revocation
        AuditLog.log(
            request,
            action="api_key_revoked",
            resource_type="api_key",
            resource_id=api_key.id,
            extra_data={"name": api_key.name},
        )

        return Response({"detail": "API key revoked successfully."})

    @action(detail=True, methods=["post"])
    def regenerate(self, request: Request, pk: str | None = None) -> Response:
        """Regenerate an API key (creates new key, deactivates old)."""
        old_key = self.get_object()

        # Create new key with same settings
        raw_key, key_hash = APIKey.generate_key()
        new_key = APIKey.objects.create(
            company=old_key.company,
            name=old_key.name,
            key_hash=key_hash,
            permissions=old_key.permissions,
            rate_limit=old_key.rate_limit,
            expires_at=old_key.expires_at,
        )
        new_key._raw_key = raw_key

        # Deactivate old key
        old_key.is_active = False
        old_key.save(update_fields=["is_active"])

        # Log regeneration
        AuditLog.log(
            request,
            action="api_key_regenerated",
            resource_type="api_key",
            resource_id=new_key.id,
            extra_data={"old_key_id": str(old_key.id)},
        )

        response_serializer = APIKeyResponseSerializer(new_key)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing audit logs (read-only).

    Users can view audit logs for their company.
    """

    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self) -> QuerySet[AuditLog]:
        """Filter to company's audit logs."""
        user = self.request.user
        if user.company:
            queryset = AuditLog.objects.filter(company=user.company)

            # Optional filters
            action = self.request.query_params.get("action")
            resource_type = self.request.query_params.get("resource_type")

            if action:
                queryset = queryset.filter(action=action)
            if resource_type:
                queryset = queryset.filter(resource_type=resource_type)

            return queryset.order_by("-created_at")

        return AuditLog.objects.none()


class WebhookViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Webhook management (CRUD).

    Users can create and manage webhooks for their company.
    """

    serializer_class = WebhookSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self) -> QuerySet[Webhook]:
        """Filter to company's webhooks."""
        user = self.request.user
        if user.company:
            return Webhook.objects.filter(company=user.company)
        return Webhook.objects.none()

    def get_serializer_class(self) -> type[Serializer]:
        """Use different serializers for create and response."""
        if self.action == "create":
            return WebhookCreateSerializer
        return WebhookSerializer

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Create new webhook and return with secret (once)."""
        serializer = WebhookCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        webhook = serializer.save()

        # Log webhook creation
        AuditLog.log(
            request,
            action="webhook_created",
            resource_type="webhook",
            resource_id=webhook.id,
            extra_data={"name": webhook.name, "events": webhook.events},
        )

        # Return with secret visible
        response_serializer = WebhookResponseSerializer(webhook)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Update webhook."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Log webhook update
        AuditLog.log(
            request,
            action="webhook_updated",
            resource_type="webhook",
            resource_id=instance.id,
            extra_data={"name": instance.name},
        )

        return Response(serializer.data)

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delete webhook."""
        instance = self.get_object()
        webhook_name = instance.name
        webhook_id = str(instance.id)
        self.perform_destroy(instance)

        # Log webhook deletion
        AuditLog.log(
            request,
            action="webhook_deleted",
            resource_type="webhook",
            resource_id=webhook_id,
            extra_data={"name": webhook_name},
        )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def _is_internal_url(url: str) -> bool:
        """Check if a URL resolves to an internal/private IP address."""
        import ipaddress
        from urllib.parse import urlparse

        parsed = urlparse(url)
        hostname = parsed.hostname or ""

        # Block obvious internal hostnames
        if hostname in ("localhost", "127.0.0.1", "0.0.0.0", "::1"):
            return True

        try:
            import socket
            resolved = socket.getaddrinfo(hostname, None)
            for _, _, _, _, addr in resolved:
                ip = ipaddress.ip_address(addr[0])
                if ip.is_private or ip.is_loopback or ip.is_link_local:
                    return True
        except (socket.gaierror, ValueError):
            pass

        return False

    @action(detail=True, methods=["post"])
    def test(self, request: Request, pk: str | None = None) -> Response:
        """Send a test event to the webhook."""
        import json
        import time

        import requests

        webhook = self.get_object()

        # SSRF protection: reject internal/private URLs
        if self._is_internal_url(webhook.url):
            return Response(
                {"detail": "Webhook URL must not resolve to an internal address."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create test payload
        test_payload = {
            "event": "test.ping",
            "timestamp": timezone.now().isoformat(),
            "data": {
                "message": "This is a test webhook delivery",
                "webhook_id": str(webhook.id),
                "webhook_name": webhook.name,
            },
        }

        payload_str = json.dumps(test_payload)
        signature = webhook.generate_signature(payload_str)

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Webhook-Event": "test.ping",
            **webhook.custom_headers,
        }

        try:
            start_time = time.time()
            response = requests.post(
                webhook.url,
                data=payload_str,
                headers=headers,
                timeout=webhook.timeout_seconds,
            )
            latency_ms = (time.time() - start_time) * 1000

            success = 200 <= response.status_code < 300

            # Log test delivery
            AuditLog.log(
                request,
                action="webhook_tested",
                resource_type="webhook",
                resource_id=webhook.id,
                extra_data={
                    "success": success,
                    "status_code": response.status_code,
                    "latency_ms": latency_ms,
                },
            )

            return Response({
                "success": success,
                "status_code": response.status_code,
                "latency_ms": round(latency_ms, 2),
                "response_body": response.text[:500] if response.text else "",
            })

        except requests.exceptions.Timeout:
            return Response(
                {"success": False, "error": "Request timed out"},
                status=status.HTTP_408_REQUEST_TIMEOUT,
            )
        except requests.exceptions.RequestException as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

    @action(detail=True, methods=["post"])
    def regenerate_secret(self, request: Request, pk: str | None = None) -> Response:
        """Regenerate webhook secret."""
        import secrets as py_secrets

        webhook = self.get_object()
        webhook.secret = py_secrets.token_urlsafe(32)
        webhook.save(update_fields=["secret", "updated_at"])

        # Log secret regeneration
        AuditLog.log(
            request,
            action="webhook_secret_regenerated",
            resource_type="webhook",
            resource_id=webhook.id,
        )

        response_serializer = WebhookResponseSerializer(webhook)
        return Response(response_serializer.data)


class WebhookDeliveryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing webhook delivery logs (read-only).

    Users can view delivery logs for their company's webhooks.
    """

    serializer_class = WebhookDeliverySerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self) -> QuerySet[WebhookDelivery]:
        """Filter to company's webhook deliveries."""
        user = self.request.user
        if user.company:
            queryset = WebhookDelivery.objects.filter(webhook__company=user.company)

            # Optional filters
            webhook_id = self.request.query_params.get("webhook_id")
            event_type = self.request.query_params.get("event_type")
            delivery_status = self.request.query_params.get("status")

            if webhook_id:
                queryset = queryset.filter(webhook_id=webhook_id)
            if event_type:
                queryset = queryset.filter(event_type=event_type)
            if delivery_status:
                queryset = queryset.filter(status=delivery_status)

            return queryset.order_by("-created_at")

        return WebhookDelivery.objects.none()

    @action(detail=True, methods=["post"])
    def retry(self, request: Request, pk: str | None = None) -> Response:
        """Manually retry a failed delivery."""
        delivery = self.get_object()

        if delivery.status not in ["failed", "retrying"]:
            return Response(
                {"detail": "Only failed or retrying deliveries can be retried."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Reset for retry
        delivery.status = WebhookDelivery.Status.PENDING
        delivery.next_retry_at = None
        delivery.save(update_fields=["status", "next_retry_at"])

        # Log manual retry
        AuditLog.log(
            request,
            action="webhook_delivery_retried",
            resource_type="webhook_delivery",
            resource_id=delivery.id,
        )

        return Response({"detail": "Delivery queued for retry."})


class UsageStatsViewSet(viewsets.ViewSet):
    """
    ViewSet for viewing usage statistics.

    Provides endpoints for daily, monthly, and overall usage stats.
    """

    permission_classes = [IsAuthenticated, IsCompanyMember]

    def list(self, request: Request) -> Response:
        """Get usage statistics summary."""
        from datetime import timedelta

        from django.db.models import Sum

        user = request.user
        if not user.company:
            return Response(
                {"detail": "No company associated."},
                status=status.HTTP_404_NOT_FOUND,
            )

        company = user.company
        today = timezone.now().date()
        month_start = today.replace(day=1)

        # Today's usage
        today_usage = UsageTracking.objects.filter(
            company=company, date=today
        ).first()

        # Monthly usage (aggregate)
        monthly_usage = UsageTracking.objects.filter(
            company=company,
            date__gte=month_start,
            date__lte=today,
        ).aggregate(
            total_requests=Sum("api_requests"),
            total_predictions=Sum("predictions"),
            total_training_runs=Sum("training_runs"),
            total_data_bytes=Sum("data_uploads_bytes"),
            total_rate_limit_hits=Sum("rate_limit_hits"),
        )

        data = {
            "tier": company.tier,
            "limits": {
                "rate_limit_per_minute": company.rate_limit,
                "daily_requests": company.daily_limit,
                "max_models": company.model_limit,
                "max_consortiums": company.consortium_limit,
            },
            "today": {
                "api_requests": today_usage.api_requests if today_usage else 0,
                "predictions": today_usage.predictions if today_usage else 0,
                "training_runs": today_usage.training_runs if today_usage else 0,
                "data_uploads_bytes": today_usage.data_uploads_bytes if today_usage else 0,
                "rate_limit_hits": today_usage.rate_limit_hits if today_usage else 0,
            },
            "month": {
                "api_requests": monthly_usage["total_requests"] or 0,
                "predictions": monthly_usage["total_predictions"] or 0,
                "training_runs": monthly_usage["total_training_runs"] or 0,
                "data_uploads_bytes": monthly_usage["total_data_bytes"] or 0,
                "rate_limit_hits": monthly_usage["total_rate_limit_hits"] or 0,
            },
        }

        serializer = UsageStatsSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def daily(self, request: Request) -> Response:
        """Get daily usage history (last 30 days)."""
        from datetime import timedelta

        user = request.user
        if not user.company:
            return Response(
                {"detail": "No company associated."},
                status=status.HTTP_404_NOT_FOUND,
            )

        today = timezone.now().date()
        start_date = today - timedelta(days=30)

        usage_records = UsageTracking.objects.filter(
            company=user.company,
            date__gte=start_date,
            date__lte=today,
        ).order_by("date")

        serializer = UsageTrackingSerializer(usage_records, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def monthly(self, request: Request) -> Response:
        """Get monthly usage aggregates (last 12 months)."""
        from datetime import timedelta

        from django.db.models import Sum
        from django.db.models.functions import TruncMonth

        user = request.user
        if not user.company:
            return Response(
                {"detail": "No company associated."},
                status=status.HTTP_404_NOT_FOUND,
            )

        today = timezone.now().date()
        start_date = (today.replace(day=1) - timedelta(days=365)).replace(day=1)

        monthly_usage = (
            UsageTracking.objects.filter(
                company=user.company,
                date__gte=start_date,
            )
            .annotate(month=TruncMonth("date"))
            .values("month")
            .annotate(
                total_requests=Sum("api_requests"),
                total_predictions=Sum("predictions"),
                total_training_runs=Sum("training_runs"),
                total_data_bytes=Sum("data_uploads_bytes"),
                total_rate_limit_hits=Sum("rate_limit_hits"),
            )
            .order_by("month")
        )

        return Response(list(monthly_usage))

    @action(detail=False, methods=["get"])
    def limits(self, request: Request) -> Response:
        """Get current usage limits and remaining quota."""
        user = request.user
        if not user.company:
            return Response(
                {"detail": "No company associated."},
                status=status.HTTP_404_NOT_FOUND,
            )

        company = user.company
        today = timezone.now().date()

        today_usage = UsageTracking.objects.filter(
            company=company, date=today
        ).first()

        today_requests = today_usage.api_requests if today_usage else 0
        daily_limit = company.daily_limit

        data = {
            "tier": company.tier,
            "rate_limit_per_minute": company.rate_limit,
            "daily_limit": daily_limit,
            "daily_used": today_requests,
            "daily_remaining": (
                daily_limit - today_requests if daily_limit != -1 else -1
            ),
            "model_limit": company.model_limit,
            "models_used": company.models.count() if hasattr(company, "models") else 0,
            "consortium_limit": company.consortium_limit,
            "consortiums_used": company.memberships.filter(status="active").count()
            if hasattr(company, "memberships")
            else 0,
        }

        return Response(data)


class ReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Report management.

    Users can create, view, and download reports for their company.
    """

    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self) -> QuerySet[Report]:
        """Filter to company's reports."""
        user = self.request.user
        if user.company:
            queryset = Report.objects.filter(company=user.company)

            # Optional filters
            report_type = self.request.query_params.get("type")
            report_status = self.request.query_params.get("status")

            if report_type:
                queryset = queryset.filter(report_type=report_type)
            if report_status:
                queryset = queryset.filter(status=report_status)

            return queryset.order_by("-created_at")

        return Report.objects.none()

    def get_serializer_class(self) -> type[Serializer]:
        """Use different serializers for create."""
        if self.action == "create":
            return ReportCreateSerializer
        return ReportSerializer

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Create a new report and start generation."""
        serializer = ReportCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        report = serializer.save()

        # Log report creation
        AuditLog.log(
            request,
            action="report_created",
            resource_type="report",
            resource_id=report.id,
            extra_data={"name": report.name, "type": report.report_type},
        )

        response_serializer = ReportSerializer(report)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def generate(self, request: Request, pk: str | None = None) -> Response:
        """Trigger report generation (for pending reports)."""
        report = self.get_object()

        if report.status not in ["pending", "failed"]:
            return Response(
                {"detail": "Only pending or failed reports can be generated."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        report.mark_generating()

        # In a real implementation, this would queue a background task
        # For now, we simulate instant completion
        import uuid

        file_path = f"/reports/{uuid.uuid4()}.{report.format}"
        file_size = 1024 * 50  # 50KB simulated
        report.mark_completed(file_path, file_size)

        # Log generation
        AuditLog.log(
            request,
            action="report_generated",
            resource_type="report",
            resource_id=report.id,
        )

        serializer = ReportSerializer(report)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def download(self, request: Request, pk: str | None = None) -> Response:
        """Get download URL for a completed report."""
        report = self.get_object()

        if report.status != "completed":
            return Response(
                {"detail": "Report is not ready for download."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if report.download_expires_at and report.download_expires_at < timezone.now():
            return Response(
                {"detail": "Download link has expired. Please regenerate the report."},
                status=status.HTTP_410_GONE,
            )

        # Log download
        AuditLog.log(
            request,
            action="report_downloaded",
            resource_type="report",
            resource_id=report.id,
        )

        return Response({
            "download_url": report.download_url or f"/api/v2/reports/{report.id}/file/",
            "expires_at": report.download_expires_at,
            "file_size": report.file_size,
            "format": report.format,
        })


class WorkflowViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Workflow management.

    Users can create, view, and manage workflows for their company.
    """

    serializer_class = WorkflowSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self) -> QuerySet[Workflow]:
        """Filter to company's workflows."""
        user = self.request.user
        if user.company:
            queryset = Workflow.objects.filter(company=user.company)

            # Optional filters
            workflow_status = self.request.query_params.get("status")

            if workflow_status:
                queryset = queryset.filter(status=workflow_status)

            return queryset.order_by("-created_at")

        return Workflow.objects.none()

    def get_serializer_class(self) -> type[Serializer]:
        """Use different serializers for create."""
        if self.action == "create":
            return WorkflowCreateSerializer
        return WorkflowSerializer

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Create a new workflow."""
        serializer = WorkflowCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        workflow = serializer.save()

        # Log workflow creation
        AuditLog.log(
            request,
            action="workflow_created",
            resource_type="workflow",
            resource_id=workflow.id,
            extra_data={"name": workflow.name},
        )

        response_serializer = WorkflowSerializer(workflow)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def run(self, request: Request, pk: str | None = None) -> Response:
        """Manually trigger a workflow run."""
        workflow = self.get_object()

        if workflow.status != "active":
            return Response(
                {"detail": "Only active workflows can be run."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create a workflow run
        run_serializer = WorkflowRunCreateSerializer(data=request.data)
        run_serializer.is_valid(raise_exception=True)

        workflow_run = WorkflowRun.objects.create(
            workflow=workflow,
            triggered_by=request.user,
            trigger_type="manual",
            input_data=run_serializer.validated_data.get("input_data", {}),
        )

        # Start the run (in real implementation, this would be async)
        workflow_run.start()

        # Simulate step execution
        for i, step in enumerate(workflow.steps):
            workflow_run.log_step(
                step_name=step.get("name", f"step_{i}"),
                status="completed",
                output={"result": "success"},
            )

        workflow_run.complete(output_data={"summary": "Workflow completed successfully"})

        # Log workflow run
        AuditLog.log(
            request,
            action="workflow_run_triggered",
            resource_type="workflow",
            resource_id=workflow.id,
            extra_data={"run_id": str(workflow_run.id)},
        )

        serializer = WorkflowRunSerializer(workflow_run)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def activate(self, request: Request, pk: str | None = None) -> Response:
        """Activate a draft workflow."""
        workflow = self.get_object()

        if workflow.status not in ["draft", "paused"]:
            return Response(
                {"detail": "Only draft or paused workflows can be activated."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        workflow.status = Workflow.Status.ACTIVE
        workflow.save(update_fields=["status", "updated_at"])

        # Log activation
        AuditLog.log(
            request,
            action="workflow_activated",
            resource_type="workflow",
            resource_id=workflow.id,
        )

        serializer = WorkflowSerializer(workflow)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def pause(self, request: Request, pk: str | None = None) -> Response:
        """Pause an active workflow."""
        workflow = self.get_object()

        if workflow.status != "active":
            return Response(
                {"detail": "Only active workflows can be paused."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        workflow.status = Workflow.Status.PAUSED
        workflow.save(update_fields=["status", "updated_at"])

        # Log pause
        AuditLog.log(
            request,
            action="workflow_paused",
            resource_type="workflow",
            resource_id=workflow.id,
        )

        serializer = WorkflowSerializer(workflow)
        return Response(serializer.data)


class WorkflowRunViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing workflow run history (read-only).

    Users can view run history for their company's workflows.
    """

    serializer_class = WorkflowRunSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self) -> QuerySet[WorkflowRun]:
        """Filter to company's workflow runs."""
        user = self.request.user
        if user.company:
            queryset = WorkflowRun.objects.filter(workflow__company=user.company)

            # Optional filters
            workflow_id = self.request.query_params.get("workflow_id")
            run_status = self.request.query_params.get("status")

            if workflow_id:
                queryset = queryset.filter(workflow_id=workflow_id)
            if run_status:
                queryset = queryset.filter(status=run_status)

            return queryset.order_by("-created_at")

        return WorkflowRun.objects.none()

    @action(detail=True, methods=["post"])
    def cancel(self, request: Request, pk: str | None = None) -> Response:
        """Cancel a running workflow run."""
        workflow_run = self.get_object()

        if workflow_run.status not in ["pending", "running"]:
            return Response(
                {"detail": "Only pending or running workflow runs can be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        workflow_run.status = WorkflowRun.Status.CANCELLED
        workflow_run.completed_at = timezone.now()
        workflow_run.save(update_fields=["status", "completed_at"])

        # Log cancellation
        AuditLog.log(
            request,
            action="workflow_run_cancelled",
            resource_type="workflow_run",
            resource_id=workflow_run.id,
        )

        serializer = WorkflowRunSerializer(workflow_run)
        return Response(serializer.data)


class ScheduledTaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ScheduledTask management.

    Users can create, view, and manage scheduled tasks for their company.
    """

    serializer_class = ScheduledTaskSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self) -> QuerySet[ScheduledTask]:
        """Filter to company's scheduled tasks."""
        user = self.request.user
        if user.company:
            queryset = ScheduledTask.objects.filter(company=user.company)

            # Optional filters
            task_type = self.request.query_params.get("type")
            task_status = self.request.query_params.get("status")

            if task_type:
                queryset = queryset.filter(task_type=task_type)
            if task_status:
                queryset = queryset.filter(status=task_status)

            return queryset.order_by("-created_at")

        return ScheduledTask.objects.none()

    def get_serializer_class(self) -> type[Serializer]:
        """Use different serializers for create."""
        if self.action == "create":
            return ScheduledTaskCreateSerializer
        return ScheduledTaskSerializer

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Create a new scheduled task."""
        serializer = ScheduledTaskCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        task = serializer.save()

        # Log task creation
        AuditLog.log(
            request,
            action="scheduled_task_created",
            resource_type="scheduled_task",
            resource_id=task.id,
            extra_data={"name": task.name, "cron": task.cron_expression},
        )

        response_serializer = ScheduledTaskSerializer(task)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def run_now(self, request: Request, pk: str | None = None) -> Response:
        """Manually trigger a scheduled task run."""
        task = self.get_object()

        if task.status != "active":
            return Response(
                {"detail": "Only active tasks can be run."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create a task run
        task_run = ScheduledTaskRun.objects.create(
            task=task,
            scheduled_at=timezone.now(),
        )
        task_run.start()

        # Simulate execution based on task type
        if task.task_type == "workflow" and task.workflow:
            # Create workflow run
            workflow_run = WorkflowRun.objects.create(
                workflow=task.workflow,
                trigger_type="schedule",
            )
            workflow_run.start()
            workflow_run.complete()
            task_run.workflow_run = workflow_run
            task_run.complete(output={"workflow_run_id": str(workflow_run.id)})
        elif task.task_type == "report" and task.report:
            task_run.complete(output={"report_id": str(task.report.id)})
        else:
            task_run.complete(output={"result": "Task executed successfully"})

        # Log manual run
        AuditLog.log(
            request,
            action="scheduled_task_manual_run",
            resource_type="scheduled_task",
            resource_id=task.id,
            extra_data={"run_id": str(task_run.id)},
        )

        serializer = ScheduledTaskRunSerializer(task_run)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def pause(self, request: Request, pk: str | None = None) -> Response:
        """Pause a scheduled task."""
        task = self.get_object()

        if task.status != "active":
            return Response(
                {"detail": "Only active tasks can be paused."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task.status = ScheduledTask.Status.PAUSED
        task.save(update_fields=["status", "updated_at"])

        # Log pause
        AuditLog.log(
            request,
            action="scheduled_task_paused",
            resource_type="scheduled_task",
            resource_id=task.id,
        )

        serializer = ScheduledTaskSerializer(task)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def resume(self, request: Request, pk: str | None = None) -> Response:
        """Resume a paused scheduled task."""
        task = self.get_object()

        if task.status != "paused":
            return Response(
                {"detail": "Only paused tasks can be resumed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task.status = ScheduledTask.Status.ACTIVE
        task.calculate_next_run()
        task.save(update_fields=["status", "updated_at"])

        # Log resume
        AuditLog.log(
            request,
            action="scheduled_task_resumed",
            resource_type="scheduled_task",
            resource_id=task.id,
        )

        serializer = ScheduledTaskSerializer(task)
        return Response(serializer.data)


class ScheduledTaskRunViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing scheduled task run history (read-only).

    Users can view run history for their company's scheduled tasks.
    """

    serializer_class = ScheduledTaskRunSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self) -> QuerySet[ScheduledTaskRun]:
        """Filter to company's scheduled task runs."""
        user = self.request.user
        if user.company:
            queryset = ScheduledTaskRun.objects.filter(task__company=user.company)

            # Optional filters
            task_id = self.request.query_params.get("task_id")
            run_status = self.request.query_params.get("status")

            if task_id:
                queryset = queryset.filter(task_id=task_id)
            if run_status:
                queryset = queryset.filter(status=run_status)

            return queryset.order_by("-created_at")

        return ScheduledTaskRun.objects.none()



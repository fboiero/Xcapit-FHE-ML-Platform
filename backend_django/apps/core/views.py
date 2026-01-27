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

from .models import APIKey, AuditLog, Company, UsageTracking, Webhook, WebhookDelivery
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
    UsageStatsSerializer,
    UsageTrackingSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
    WebhookCreateSerializer,
    WebhookDeliverySerializer,
    WebhookResponseSerializer,
    WebhookSerializer,
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

    @action(detail=True, methods=["post"])
    def test(self, request: Request, pk: str | None = None) -> Response:
        """Send a test event to the webhook."""
        import json
        import time

        import requests

        webhook = self.get_object()

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



"""
Core views for Xcapit FHE-ML Platform.
"""

import secrets

import requests as req_lib
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    AuditLog,
    Company,
    APIKey,
    Report,
    ScheduledTask,
    ScheduledTaskRun,
    UsageTracking,
    User,
    Webhook,
    WebhookDelivery,
    Workflow,
    WorkflowRun,
)
from .serializers import (
    APIKeyCreateSerializer,
    APIKeySerializer,
    AuditLogSerializer,
    CompanyDetailSerializer,
    CompanySerializer,
    ReportCreateSerializer,
    ReportSerializer,
    ScheduledTaskCreateSerializer,
    ScheduledTaskRunSerializer,
    ScheduledTaskSerializer,
    UsageTrackingSerializer,
    UserSerializer,
    WebhookCreateSerializer,
    WebhookDeliverySerializer,
    WebhookSerializer,
    WorkflowCreateSerializer,
    WorkflowRunSerializer,
    WorkflowSerializer,
)


class HealthCheckView(APIView):
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        from django.utils import timezone
        from django.conf import settings

        return Response({
            "status": "healthy",
            "version": getattr(settings, "SPECTACULAR_SETTINGS", {}).get("VERSION", "2.0.0"),
            "timestamp": timezone.now().isoformat(),
        })


class CompanyViewSet(viewsets.ModelViewSet):
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.company:
            return Company.objects.filter(id=user.company_id)
        return Company.objects.none()

    def get_serializer_class(self):
        if self.action in ("retrieve", "me"):
            return CompanyDetailSerializer
        return CompanySerializer

    def get_object(self):
        """Allow 'me' as a special pk that resolves to the user's company."""
        if self.kwargs.get(self.lookup_field) == "me":
            user = self.request.user
            if not user.company:
                from rest_framework.exceptions import NotFound
                raise NotFound("No company associated with this account.")
            return user.company
        return super().get_object()

    @action(detail=False, methods=["get", "patch"])
    def me(self, request):
        """Return or update the current user's company."""
        if not request.user.company:
            return Response({"detail": "No company associated."}, status=status.HTTP_404_NOT_FOUND)
        company = request.user.company
        if request.method == "PATCH":
            serializer = self.get_serializer(company, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        serializer = self.get_serializer(company)
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)

    def get_object(self):
        """Allow 'me' as a special pk that resolves to the current user."""
        if self.kwargs.get(self.lookup_field) == "me":
            return self.request.user
        return super().get_object()

    @action(detail=False, methods=["get", "patch"])
    def me(self, request):
        """Return or update the current user's profile."""
        user = request.user
        if request.method == "PATCH":
            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        serializer = self.get_serializer(user)
        return Response(serializer.data)


class APIKeyViewSet(viewsets.ModelViewSet):
    serializer_class = APIKeySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.company:
            return APIKey.objects.filter(company=user.company)
        return APIKey.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return APIKeyCreateSerializer
        return APIKeySerializer

    def perform_create(self, serializer):
        user = self.request.user
        raw_key, key_hash = APIKey.generate_key()
        serializer.save(
            company=user.company,
            created_by=user,
            key_hash=key_hash,
            prefix=raw_key[: len(APIKey.PREFIX) + 9],  # prefix + _ + 8 chars
        )
        # Store the raw key on the instance so the response can include it
        serializer.instance._raw_key = raw_key

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.validate(serializer.initial_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # Return the full key details plus the raw key (shown only once)
        response_serializer = APIKeySerializer(serializer.instance)
        data = response_serializer.data
        data["raw_key"] = serializer.instance._raw_key
        return Response(data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def revoke(self, request, pk=None):
        """Revoke (deactivate) an API key."""
        api_key = self.get_object()
        api_key.is_active = False
        api_key.save(update_fields=["is_active"])
        return Response({"detail": "API key revoked successfully."}, status=status.HTTP_200_OK)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.company:
            qs = AuditLog.objects.filter(company=user.company)
            action_filter = self.request.query_params.get("action")
            if action_filter:
                qs = qs.filter(action=action_filter)
            return qs
        return AuditLog.objects.none()


class WebhookViewSet(viewsets.ModelViewSet):
    serializer_class = WebhookSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.company:
            return Webhook.objects.filter(company=user.company)
        return Webhook.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return WebhookCreateSerializer
        return WebhookSerializer

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)

    @action(detail=True, methods=["post"])
    def test(self, request, pk=None):
        """Send a test payload to the webhook URL."""
        webhook = self.get_object()
        payload = {"event": "test", "timestamp": timezone.now().isoformat()}
        try:
            resp = req_lib.post(
                webhook.url,
                json=payload,
                timeout=webhook.timeout_seconds,
            )
            return Response(
                {"success": True, "status_code": resp.status_code, "response": resp.text[:500]},
                status=status.HTTP_200_OK,
            )
        except req_lib.exceptions.Timeout:
            return Response(
                {"detail": "Request timed out."},
                status=status.HTTP_408_REQUEST_TIMEOUT,
            )
        except req_lib.exceptions.ConnectionError as exc:
            return Response(
                {"detail": f"Connection error: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

    @action(detail=True, methods=["post"], url_path="regenerate_secret")
    def regenerate_secret(self, request, pk=None):
        """Generate a new HMAC secret for this webhook."""
        webhook = self.get_object()
        webhook.secret = secrets.token_hex(32)
        webhook.save(update_fields=["secret", "updated_at"])
        return Response(
            {"detail": "Secret regenerated successfully.", "secret": webhook.secret},
            status=status.HTTP_200_OK,
        )


class WebhookDeliveryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WebhookDeliverySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.company:
            return WebhookDelivery.objects.filter(webhook__company=user.company)
        return WebhookDelivery.objects.none()

    @action(detail=True, methods=["post"])
    def retry(self, request, pk=None):
        """Re-queue a failed delivery."""
        delivery = self.get_object()
        if delivery.status != WebhookDelivery.Status.FAILED:
            return Response(
                {"detail": "Only failed deliveries can be retried."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        delivery.status = WebhookDelivery.Status.PENDING
        delivery.save(update_fields=["status"])
        return Response(WebhookDeliverySerializer(delivery).data)


class UsageStatsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UsageTrackingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.company:
            return UsageTracking.objects.filter(company=user.company)
        return UsageTracking.objects.none()

    def list(self, request, *args, **kwargs):
        """Override list to include tier info at the top level."""
        user = request.user
        if not user.company:
            return Response(
                {"detail": "No company associated."},
                status=status.HTTP_403_FORBIDDEN,
            )
        response = super().list(request, *args, **kwargs)
        response.data["tier"] = user.company.tier
        return response

    @action(detail=False, methods=["get"])
    def daily(self, request):
        """Daily usage summary for today."""
        user = request.user
        if not user.company:
            return Response(
                {"detail": "No company associated."},
                status=status.HTTP_403_FORBIDDEN,
            )
        today = timezone.now().date()
        tracking = UsageTracking.objects.filter(
            company=user.company, date=today
        ).first()
        data = UsageTrackingSerializer(tracking).data if tracking else {}
        return Response(data)

    @action(detail=False, methods=["get"])
    def monthly(self, request):
        """Monthly aggregated usage."""
        user = request.user
        if not user.company:
            return Response(
                {"detail": "No company associated."},
                status=status.HTTP_403_FORBIDDEN,
            )
        now = timezone.now()
        records = UsageTracking.objects.filter(
            company=user.company,
            date__year=now.year,
            date__month=now.month,
        )
        data = UsageTrackingSerializer(records, many=True).data
        return Response({"month": f"{now.year}-{now.month:02d}", "records": data})

    @action(detail=False, methods=["get"])
    def limits(self, request):
        """Current tier limits."""
        user = request.user
        if not user.company:
            return Response(
                {"detail": "No company associated."},
                status=status.HTTP_403_FORBIDDEN,
            )
        company = user.company
        return Response(
            {
                "tier": company.tier,
                "daily_limit": company.daily_limit,
                "rate_limit": company.rate_limit,
                "model_limit": company.model_limit,
                "consortium_limit": company.consortium_limit,
            }
        )


class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.company:
            return Report.objects.filter(company=user.company)
        return Report.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return ReportCreateSerializer
        return ReportSerializer

    def perform_create(self, serializer):
        serializer.save(
            company=self.request.user.company,
            created_by=self.request.user,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        response_serializer = ReportSerializer(
            serializer.instance, context={"request": request}
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def generate(self, request, pk=None):
        """Trigger generation of a pending or failed report."""
        report = self.get_object()
        if report.status == Report.Status.COMPLETED:
            return Response(
                {"detail": "Report is already completed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        report.mark_generating()
        # Simulate completion (in production this would be async)
        report.mark_completed(
            file_path=f"/reports/{report.id}.pdf",
            file_size=1024,
            download_url=f"/api/v2/reports/{report.id}/download/",
        )
        return Response(ReportSerializer(report).data)

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        """Return a download URL for a completed report."""
        report = self.get_object()
        if report.status != Report.Status.COMPLETED:
            return Response(
                {"detail": "Report is not ready for download."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if report.download_expires_at and report.download_expires_at < timezone.now():
            return Response(
                {"detail": "Download link has expired."},
                status=status.HTTP_410_GONE,
            )
        return Response(
            {
                "download_url": report.download_url or f"/reports/{report.id}.pdf",
                "expires_at": report.download_expires_at,
                "file_size": report.file_size,
            }
        )


class WorkflowViewSet(viewsets.ModelViewSet):
    serializer_class = WorkflowSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.company:
            return Workflow.objects.filter(company=user.company)
        return Workflow.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return WorkflowCreateSerializer
        return WorkflowSerializer

    def perform_create(self, serializer):
        serializer.save(
            company=self.request.user.company,
            created_by=self.request.user,
        )

    @action(detail=True, methods=["post"])
    def run(self, request, pk=None):
        """Trigger a manual run of the workflow."""
        workflow = self.get_object()
        if workflow.status != Workflow.Status.ACTIVE:
            return Response(
                {"detail": "Workflow must be active to run."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        now = timezone.now()
        run = WorkflowRun.objects.create(
            workflow=workflow,
            triggered_by=request.user,
            trigger_type="manual",
            status=WorkflowRun.Status.COMPLETED,
            input_data=request.data.get("input_data", {}),
            started_at=now,
            completed_at=now,
        )
        return Response(WorkflowRunSerializer(run).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """Activate a draft or paused workflow."""
        workflow = self.get_object()
        if workflow.status == Workflow.Status.ACTIVE:
            return Response(
                {"detail": "Workflow is already active."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        workflow.status = Workflow.Status.ACTIVE
        workflow.save(update_fields=["status", "updated_at"])
        return Response(WorkflowSerializer(workflow).data)

    @action(detail=True, methods=["post"])
    def pause(self, request, pk=None):
        """Pause an active workflow."""
        workflow = self.get_object()
        if workflow.status != Workflow.Status.ACTIVE:
            return Response(
                {"detail": "Only active workflows can be paused."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        workflow.status = Workflow.Status.PAUSED
        workflow.save(update_fields=["status", "updated_at"])
        return Response(WorkflowSerializer(workflow).data)


class WorkflowRunViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WorkflowRunSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.company:
            return WorkflowRun.objects.filter(workflow__company=user.company)
        return WorkflowRun.objects.none()

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a running workflow run."""
        run = self.get_object()
        if run.status != WorkflowRun.Status.RUNNING:
            return Response(
                {"detail": "Only running workflow runs can be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        run.status = WorkflowRun.Status.CANCELLED
        run.completed_at = timezone.now()
        run.save(update_fields=["status", "completed_at"])
        return Response(WorkflowRunSerializer(run).data)


class ScheduledTaskViewSet(viewsets.ModelViewSet):
    serializer_class = ScheduledTaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.company:
            return ScheduledTask.objects.filter(company=user.company)
        return ScheduledTask.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return ScheduledTaskCreateSerializer
        return ScheduledTaskSerializer

    def perform_create(self, serializer):
        instance = serializer.save(
            company=self.request.user.company,
            created_by=self.request.user,
        )
        instance.calculate_next_run()

    @action(detail=True, methods=["post"])
    def run_now(self, request, pk=None):
        """Trigger immediate execution of a scheduled task."""
        task = self.get_object()
        if task.status != ScheduledTask.Status.ACTIVE:
            return Response(
                {"detail": "Only active tasks can be run immediately."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # If this is a workflow task, trigger the workflow
        if task.task_type == ScheduledTask.TaskType.WORKFLOW and task.workflow:
            now = timezone.now()
            run = WorkflowRun.objects.create(
                workflow=task.workflow,
                triggered_by=request.user,
                trigger_type="scheduled",
                status=WorkflowRun.Status.COMPLETED,
                started_at=now,
                completed_at=now,
            )
            return Response(
                {"detail": "Workflow triggered.", "run_id": str(run.id), "status": "completed"},
                status=status.HTTP_201_CREATED,
            )
        # If this is a report task, generate the report
        if task.task_type == ScheduledTask.TaskType.REPORT and task.report:
            task.report.mark_generating()
            task.report.mark_completed(
                file_path=f"/reports/{task.report.id}.pdf",
                file_size=1024,
            )
            return Response(
                {
                    "detail": "Report generation started.",
                    "report_id": str(task.report.id),
                    "status": "completed",
                },
                status=status.HTTP_201_CREATED,
            )
        # Generic task run
        task_run = ScheduledTaskRun.objects.create(
            task=task,
            scheduled_at=timezone.now(),
            status=ScheduledTaskRun.Status.COMPLETED,
        )
        return Response(
            {"detail": "Task executed.", "run_id": str(task_run.id), "status": "completed"},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def pause(self, request, pk=None):
        """Pause an active scheduled task."""
        task = self.get_object()
        if task.status != ScheduledTask.Status.ACTIVE:
            return Response(
                {"detail": "Only active tasks can be paused."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        task.status = ScheduledTask.Status.PAUSED
        task.save(update_fields=["status", "updated_at"])
        return Response(ScheduledTaskSerializer(task).data)

    @action(detail=True, methods=["post"])
    def resume(self, request, pk=None):
        """Resume a paused scheduled task."""
        task = self.get_object()
        if task.status != ScheduledTask.Status.PAUSED:
            return Response(
                {"detail": "Only paused tasks can be resumed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        task.status = ScheduledTask.Status.ACTIVE
        task.save(update_fields=["status", "updated_at"])
        return Response(ScheduledTaskSerializer(task).data)


class ScheduledTaskRunViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ScheduledTaskRunSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.company:
            return ScheduledTaskRun.objects.filter(task__company=user.company)
        return ScheduledTaskRun.objects.none()

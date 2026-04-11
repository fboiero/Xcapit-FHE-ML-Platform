"""
Core serializers for Xcapit FHE-ML Platform.

ModelSerializer classes for all core models with proper field definitions,
read-only constraints, and nested representations where appropriate.
"""

from rest_framework import serializers

from .models import (
    AuditLog,
    APIKey,
    Company,
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


# ── Company Serializers ───────────────────────────────────────────────


class CompanySerializer(serializers.ModelSerializer):
    """
    Standard Company serializer.

    Tier-related limits are read-only computed fields; name, email,
    industry, website, and description are writable.
    """

    rate_limit = serializers.IntegerField(read_only=True)
    daily_limit = serializers.IntegerField(read_only=True)
    model_limit = serializers.IntegerField(read_only=True)
    consortium_limit = serializers.IntegerField(read_only=True)
    upload_limit = serializers.IntegerField(read_only=True)
    training_limit = serializers.IntegerField(read_only=True)
    sandbox_limit = serializers.IntegerField(read_only=True)

    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "email",
            "tier",
            "industry",
            "website",
            "description",
            "is_active",
            "is_verified",
            "rate_limit",
            "daily_limit",
            "model_limit",
            "consortium_limit",
            "upload_limit",
            "training_limit",
            "sandbox_limit",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "tier",
            "is_active",
            "is_verified",
            "created_at",
            "updated_at",
        ]


class CompanyDetailSerializer(CompanySerializer):
    """
    Extended Company serializer with trial information, subscription
    status, and current usage limits.
    """

    is_trial = serializers.BooleanField(read_only=True)
    trial_expired = serializers.BooleanField(read_only=True)
    trial_days_remaining = serializers.IntegerField(read_only=True)
    user_count = serializers.SerializerMethodField()
    api_key_count = serializers.SerializerMethodField()

    class Meta(CompanySerializer.Meta):
        fields = CompanySerializer.Meta.fields + [
            "trial_started_at",
            "trial_expires_at",
            "custom_rate_limit",
            "custom_daily_limit",
            "is_trial",
            "trial_expired",
            "trial_days_remaining",
            "user_count",
            "api_key_count",
        ]
        read_only_fields = CompanySerializer.Meta.read_only_fields + [
            "trial_started_at",
            "trial_expires_at",
            "custom_rate_limit",
            "custom_daily_limit",
        ]

    def get_user_count(self, obj):
        return obj.users.count()

    def get_api_key_count(self, obj):
        return obj.api_keys.filter(is_active=True).count()


# ── User Serializer ───────────────────────────────────────────────────


class UserSerializer(serializers.ModelSerializer):
    """
    User serializer.

    Password is write-only, company is read-only (set via business logic).
    """

    full_name = serializers.CharField(source="get_full_name", read_only=True)
    company_name = serializers.CharField(
        source="company.name", read_only=True, default=None
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "company",
            "company_name",
            "is_active",
            "is_staff",
            "date_joined",
            "last_login",
        ]
        read_only_fields = [
            "id",
            "email",
            "company",
            "is_active",
            "is_staff",
            "date_joined",
            "last_login",
        ]


# ── APIKey Serializer ─────────────────────────────────────────────────


class APIKeySerializer(serializers.ModelSerializer):
    """
    API Key serializer.

    ``key_hash`` is **never** exposed. The raw key is only returned once
    at creation time via a separate view; this serializer is for listing
    and managing existing keys.
    """

    created_by_email = serializers.EmailField(
        source="created_by.email", read_only=True, default=None
    )
    company_name = serializers.CharField(
        source="company.name", read_only=True
    )

    class Meta:
        model = APIKey
        fields = [
            "id",
            "name",
            "prefix",
            "company",
            "company_name",
            "created_by",
            "created_by_email",
            "permissions",
            "rate_limit",
            "is_active",
            "created_at",
            "last_used_at",
            "expires_at",
        ]
        read_only_fields = [
            "id",
            "prefix",
            "company",
            "created_by",
            "created_at",
            "last_used_at",
        ]
        # Ensure key_hash is never serialised — it is not in `fields`.


class APIKeyCreateSerializer(serializers.ModelSerializer):
    """
    Serializer used when creating a new API key.

    Only accepts name, permissions, rate_limit, and expires_at.
    The company and created_by are set in the view from request context.
    """

    class Meta:
        model = APIKey
        fields = [
            "name",
            "permissions",
            "rate_limit",
            "expires_at",
        ]

    def validate_permissions(self, value):
        valid = {"read", "write", "admin"}
        if not isinstance(value, list):
            raise serializers.ValidationError("Permissions must be a list.")
        for perm in value:
            if perm not in valid:
                raise serializers.ValidationError(
                    f"Invalid permission '{perm}'. Valid options: {sorted(valid)}"
                )
        return value

    def validate_rate_limit(self, value: int) -> int:
        max_rate_limit = 10000  # requests per minute cap
        if value > max_rate_limit:
            raise serializers.ValidationError(
                f"Rate limit cannot exceed {max_rate_limit} requests per minute."
            )
        if value < 1:
            raise serializers.ValidationError(
                "Rate limit must be at least 1 request per minute."
            )
        return value


class CompanyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a company."""

    class Meta:
        model = Company
        fields = ["name", "email", "industry", "website", "description"]

    def validate_email(self, value: str) -> str:
        if Company.objects.filter(email=value).exists():
            raise serializers.ValidationError("A company with this email already exists.")
        return value


class UserCreateSerializer(serializers.Serializer):
    """Serializer for creating a user with password confirmation."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=12)
    password_confirm = serializers.CharField(write_only=True, min_length=12)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    company = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(), required=False, allow_null=True
    )

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("password_confirm"):
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm", None)
        return User.objects.create_user(**validated_data)


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing a user's password."""

    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=12)
    new_password_confirm = serializers.CharField(write_only=True, min_length=12)

    def validate_old_password(self, value: str) -> str:
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def validate(self, attrs):
        if attrs.get("new_password") != attrs.get("new_password_confirm"):
            raise serializers.ValidationError(
                {"new_password_confirm": "New passwords do not match."}
            )
        return attrs


class APIKeyResponseSerializer(serializers.ModelSerializer):
    """Serializer that includes the raw API key (only at creation time)."""

    key = serializers.SerializerMethodField()

    class Meta:
        model = APIKey
        fields = [
            "id",
            "name",
            "prefix",
            "company",
            "key",
            "permissions",
            "is_active",
            "created_at",
            "expires_at",
        ]
        read_only_fields = fields

    def get_key(self, obj) -> str | None:
        return getattr(obj, "_raw_key", None)


# ── AuditLog Serializer ───────────────────────────────────────────────


class AuditLogSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for audit log entries.
    """

    user_email = serializers.EmailField(
        source="user.email", read_only=True, default=None
    )
    company_name = serializers.CharField(
        source="company.name", read_only=True, default=None
    )

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "user",
            "user_email",
            "company",
            "company_name",
            "api_key_name",
            "action",
            "resource_type",
            "resource_id",
            "ip_address",
            "user_agent",
            "request_path",
            "request_method",
            "response_status",
            "extra_data",
            "created_at",
        ]
        read_only_fields = fields


# ── UsageTracking Serializer ──────────────────────────────────────────


class UsageTrackingSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for daily usage tracking records.
    """

    company_name = serializers.CharField(
        source="company.name", read_only=True
    )
    within_daily_limit = serializers.SerializerMethodField()

    class Meta:
        model = UsageTracking
        fields = [
            "id",
            "company",
            "company_name",
            "date",
            "api_requests",
            "predictions",
            "training_runs",
            "data_uploads_bytes",
            "rate_limit_hits",
            "within_daily_limit",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_within_daily_limit(self, obj):
        return obj.check_daily_limit()


# ── Webhook Serializers ───────────────────────────────────────────────


class WebhookSerializer(serializers.ModelSerializer):
    """
    Webhook serializer for list/detail views.

    The ``secret`` field is write-only (never returned in responses).
    Delivery statistics are read-only.
    """

    company_name = serializers.CharField(
        source="company.name", read_only=True
    )

    class Meta:
        model = Webhook
        fields = [
            "id",
            "company",
            "company_name",
            "name",
            "url",
            "secret",
            "events",
            "custom_headers",
            "is_active",
            "is_verified",
            "max_retries",
            "timeout_seconds",
            "total_deliveries",
            "successful_deliveries",
            "failed_deliveries",
            "last_delivery_at",
            "last_success_at",
            "last_failure_at",
            "last_error",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "company",
            "is_verified",
            "total_deliveries",
            "successful_deliveries",
            "failed_deliveries",
            "last_delivery_at",
            "last_success_at",
            "last_failure_at",
            "last_error",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "secret": {"write_only": True},
        }


class WebhookCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a webhook.

    Company is set from request context. Accepts name, url, secret,
    events, and optional configuration.
    """

    class Meta:
        model = Webhook
        fields = [
            "name",
            "url",
            "secret",
            "events",
            "custom_headers",
            "max_retries",
            "timeout_seconds",
        ]

    def validate_url(self, value: str) -> str:
        """SECURITY: Block internal/private network URLs to prevent SSRF."""
        import ipaddress
        from urllib.parse import urlparse

        parsed = urlparse(value)
        hostname = parsed.hostname or ""

        # Block non-HTTP(S) schemes
        if parsed.scheme not in ("http", "https"):
            raise serializers.ValidationError(
                "Only http and https URLs are allowed."
            )

        # Block obviously internal hostnames
        blocked_hosts = {
            "localhost", "127.0.0.1", "0.0.0.0", "::1",
            "metadata.google.internal", "169.254.169.254",
        }
        if hostname.lower() in blocked_hosts:
            raise serializers.ValidationError(
                "Internal network URLs are not allowed."
            )

        # Resolve and block private/reserved IP ranges
        try:
            import socket
            resolved = socket.getaddrinfo(hostname, None)
            for _, _, _, _, sockaddr in resolved:
                ip = ipaddress.ip_address(sockaddr[0])
                if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                    raise serializers.ValidationError(
                        "URLs resolving to private/internal IPs are not allowed."
                    )
        except (socket.gaierror, OSError):
            # Can't resolve — allow (might be a valid external host)
            pass

        return value

    def validate_events(self, value):
        if not isinstance(value, list) or len(value) == 0:
            raise serializers.ValidationError(
                "Events must be a non-empty list of event types."
            )
        valid_events = {choice[0] for choice in Webhook.EventType.choices}
        for event in value:
            if event not in valid_events:
                raise serializers.ValidationError(
                    f"Invalid event type '{event}'."
                )
        return value

    def validate_max_retries(self, value):
        if value < 0 or value > 10:
            raise serializers.ValidationError(
                "max_retries must be between 0 and 10."
            )
        return value

    def validate_timeout_seconds(self, value):
        if value < 1 or value > 120:
            raise serializers.ValidationError(
                "timeout_seconds must be between 1 and 120."
            )
        return value


# ── WebhookDelivery Serializer ────────────────────────────────────────


class WebhookDeliverySerializer(serializers.ModelSerializer):
    """
    Read-only serializer for webhook delivery records.
    """

    webhook_name = serializers.CharField(
        source="webhook.name", read_only=True
    )

    class Meta:
        model = WebhookDelivery
        fields = [
            "id",
            "webhook",
            "webhook_name",
            "event_type",
            "event_id",
            "payload",
            "status",
            "attempt_count",
            "max_attempts",
            "response_status_code",
            "response_body",
            "response_headers",
            "latency_ms",
            "error_message",
            "created_at",
            "delivered_at",
            "next_retry_at",
        ]
        read_only_fields = fields


# ── Report Serializers ────────────────────────────────────────────────


class ReportSerializer(serializers.ModelSerializer):
    """
    Report serializer for list/detail views.
    """

    created_by_email = serializers.EmailField(
        source="created_by.email", read_only=True, default=None
    )
    company_name = serializers.CharField(
        source="company.name", read_only=True
    )

    class Meta:
        model = Report
        fields = [
            "id",
            "company",
            "company_name",
            "created_by",
            "created_by_email",
            "name",
            "report_type",
            "format",
            "date_from",
            "date_to",
            "sections",
            "parameters",
            "status",
            "file_path",
            "file_size",
            "download_url",
            "download_expires_at",
            "error_message",
            "created_at",
            "updated_at",
            "completed_at",
        ]
        read_only_fields = [
            "id",
            "company",
            "created_by",
            "status",
            "file_path",
            "file_size",
            "download_url",
            "download_expires_at",
            "error_message",
            "created_at",
            "updated_at",
            "completed_at",
        ]


class ReportCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a report.

    Company and created_by are set from request context.
    """

    class Meta:
        model = Report
        fields = [
            "name",
            "report_type",
            "format",
            "date_from",
            "date_to",
            "sections",
            "parameters",
        ]

    def validate_report_type(self, value):
        valid = {choice[0] for choice in Report.ReportType.choices}
        if value not in valid:
            raise serializers.ValidationError(
                f"Invalid report type '{value}'."
            )
        return value

    def validate_format(self, value):
        valid = {choice[0] for choice in Report.Format.choices}
        if value not in valid:
            raise serializers.ValidationError(
                f"Invalid format '{value}'."
            )
        return value

    def validate(self, attrs):
        date_from = attrs.get("date_from")
        date_to = attrs.get("date_to")
        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError(
                {"date_to": "date_to must be on or after date_from."}
            )
        return attrs


# ── Workflow Serializers ──────────────────────────────────────────────


class WorkflowSerializer(serializers.ModelSerializer):
    """
    Workflow serializer for list/detail views.
    """

    created_by_email = serializers.EmailField(
        source="created_by.email", read_only=True, default=None
    )
    company_name = serializers.CharField(
        source="company.name", read_only=True
    )
    success_rate = serializers.FloatField(read_only=True)

    class Meta:
        model = Workflow
        fields = [
            "id",
            "company",
            "company_name",
            "created_by",
            "created_by_email",
            "name",
            "description",
            "steps",
            "trigger",
            "status",
            "total_runs",
            "successful_runs",
            "failed_runs",
            "last_run_at",
            "last_success_at",
            "last_failure_at",
            "success_rate",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "company",
            "created_by",
            "total_runs",
            "successful_runs",
            "failed_runs",
            "last_run_at",
            "last_success_at",
            "last_failure_at",
            "created_at",
            "updated_at",
        ]


class WorkflowCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a workflow.

    Company and created_by are set from request context.
    """

    class Meta:
        model = Workflow
        fields = [
            "name",
            "description",
            "steps",
            "trigger",
            "status",
        ]

    def validate_steps(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Steps must be a list.")
        for idx, step in enumerate(value):
            if not isinstance(step, dict):
                raise serializers.ValidationError(
                    f"Step {idx} must be a dictionary."
                )
            if "name" not in step:
                raise serializers.ValidationError(
                    f"Step {idx} is missing required field 'name'."
                )
            if "type" not in step:
                raise serializers.ValidationError(
                    f"Step {idx} is missing required field 'type'."
                )
        return value

    def validate_trigger(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Trigger must be a dictionary.")
        valid_types = {"manual", "schedule", "event"}
        trigger_type = value.get("type")
        if trigger_type and trigger_type not in valid_types:
            raise serializers.ValidationError(
                f"Invalid trigger type '{trigger_type}'. "
                f"Valid options: {sorted(valid_types)}"
            )
        if trigger_type == "schedule" and not value.get("schedule"):
            raise serializers.ValidationError(
                "Schedule trigger requires a 'schedule' field (e.g. cron expression)."
            )
        if trigger_type == "event" and not value.get("event"):
            raise serializers.ValidationError(
                "Event trigger requires an 'event' field specifying the event name."
            )
        return value

    def validate_status(self, value):
        # New workflows can only be created as draft or active
        valid_initial = {Workflow.Status.DRAFT, Workflow.Status.ACTIVE}
        if value not in valid_initial:
            raise serializers.ValidationError(
                "New workflows can only be created with status 'draft' or 'active'."
            )
        return value


# ── WorkflowRun Serializer ───────────────────────────────────────────


class WorkflowRunSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for workflow run records.
    """

    workflow_name = serializers.CharField(
        source="workflow.name", read_only=True
    )
    triggered_by_email = serializers.EmailField(
        source="triggered_by.email", read_only=True, default=None
    )

    class Meta:
        model = WorkflowRun
        fields = [
            "id",
            "workflow",
            "workflow_name",
            "triggered_by",
            "triggered_by_email",
            "trigger_type",
            "trigger_event",
            "status",
            "step_logs",
            "current_step",
            "input_data",
            "output_data",
            "error_message",
            "duration_seconds",
            "created_at",
            "started_at",
            "completed_at",
        ]
        read_only_fields = fields


# ── ScheduledTask Serializers ─────────────────────────────────────────


class ScheduledTaskSerializer(serializers.ModelSerializer):
    """
    Scheduled task serializer for list/detail views.
    """

    created_by_email = serializers.EmailField(
        source="created_by.email", read_only=True, default=None
    )
    company_name = serializers.CharField(
        source="company.name", read_only=True
    )

    class Meta:
        model = ScheduledTask
        fields = [
            "id",
            "company",
            "company_name",
            "created_by",
            "created_by_email",
            "name",
            "description",
            "task_type",
            "cron_expression",
            "timezone",
            "config",
            "report",
            "workflow",
            "status",
            "next_run_at",
            "last_run_at",
            "total_runs",
            "successful_runs",
            "failed_runs",
            "consecutive_failures",
            "max_consecutive_failures",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "company",
            "created_by",
            "next_run_at",
            "last_run_at",
            "total_runs",
            "successful_runs",
            "failed_runs",
            "consecutive_failures",
            "created_at",
            "updated_at",
        ]


class ScheduledTaskCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a scheduled task.

    Company and created_by are set from request context.
    """

    class Meta:
        model = ScheduledTask
        fields = [
            "name",
            "description",
            "task_type",
            "cron_expression",
            "timezone",
            "config",
            "report",
            "workflow",
            "max_consecutive_failures",
        ]

    def validate_task_type(self, value):
        valid = {choice[0] for choice in ScheduledTask.TaskType.choices}
        if value not in valid:
            raise serializers.ValidationError(
                f"Invalid task type '{value}'."
            )
        return value

    def validate_cron_expression(self, value):
        parts = value.strip().split()
        if len(parts) != 5:
            raise serializers.ValidationError(
                "Cron expression must have exactly 5 fields: "
                "minute hour day month day_of_week."
            )
        return value

    def validate_max_consecutive_failures(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "max_consecutive_failures must be >= 0."
            )
        return value

    def validate(self, attrs):
        task_type = attrs.get("task_type")
        if task_type == "workflow" and not attrs.get("workflow"):
            raise serializers.ValidationError(
                {"workflow": "Workflow is required for task type 'workflow'."}
            )
        if task_type == "report" and not attrs.get("report"):
            raise serializers.ValidationError(
                {"report": "Report is required for task type 'report'."}
            )
        return attrs


# ── ScheduledTaskRun Serializer ───────────────────────────────────────


class ScheduledTaskRunSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for scheduled task run records.
    """

    task_name = serializers.CharField(
        source="task.name", read_only=True
    )

    class Meta:
        model = ScheduledTaskRun
        fields = [
            "id",
            "task",
            "task_name",
            "status",
            "scheduled_at",
            "started_at",
            "completed_at",
            "duration_seconds",
            "output",
            "error_message",
            "workflow_run",
            "report",
            "created_at",
        ]
        read_only_fields = fields

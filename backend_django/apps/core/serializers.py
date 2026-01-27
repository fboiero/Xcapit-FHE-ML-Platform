"""
Core serializers for Xcapit FHE-ML Platform.

Provides validation and serialization for User, Company, and APIKey models.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import APIKey, AuditLog, Company, UsageTracking, Webhook, WebhookDelivery

User = get_user_model()


class CompanySerializer(serializers.ModelSerializer):
    """Serializer for Company model."""

    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "email",
            "industry",
            "website",
            "description",
            "is_active",
            "is_verified",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "is_verified", "created_at", "updated_at"]


class CompanyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a Company."""

    class Meta:
        model = Company
        fields = ["name", "email", "industry", "website", "description"]

    def validate_email(self, value):
        """Ensure email is unique and lowercase."""
        value = value.lower()
        if Company.objects.filter(email=value).exists():
            raise serializers.ValidationError("A company with this email already exists.")
        return value


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""

    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "company",
            "company_name",
            "is_active",
            "date_joined",
            "last_login",
        ]
        read_only_fields = ["id", "date_joined", "last_login"]


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a User with password validation."""

    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "company",
        ]

    def validate_email(self, value):
        """Ensure email is unique and lowercase."""
        value = value.lower()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, attrs):
        """Validate password match and strength."""
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})

        # Validate password strength
        validate_password(attrs["password"])

        return attrs

    def create(self, validated_data):
        """Create user with hashed password."""
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating User profile."""

    class Meta:
        model = User
        fields = ["first_name", "last_name"]


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change."""

    old_password = serializers.CharField(
        required=True,
        style={"input_type": "password"},
    )
    new_password = serializers.CharField(
        required=True,
        style={"input_type": "password"},
    )
    new_password_confirm = serializers.CharField(
        required=True,
        style={"input_type": "password"},
    )

    def validate_old_password(self, value):
        """Verify current password is correct."""
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, attrs):
        """Validate new password match and strength."""
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password": "Passwords do not match."})
        validate_password(attrs["new_password"])
        return attrs


class APIKeySerializer(serializers.ModelSerializer):
    """Serializer for APIKey model (read-only, no actual key exposed)."""

    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = APIKey
        fields = [
            "id",
            "name",
            "company",
            "company_name",
            "permissions",
            "rate_limit",
            "is_active",
            "created_at",
            "last_used_at",
            "expires_at",
        ]
        read_only_fields = [
            "id",
            "company",
            "created_at",
            "last_used_at",
        ]


class APIKeyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an APIKey."""

    class Meta:
        model = APIKey
        fields = ["name", "permissions", "rate_limit", "expires_at"]

    def validate_permissions(self, value):
        """Validate permissions list."""
        valid_permissions = ["read", "write", "admin"]
        for perm in value:
            if perm not in valid_permissions:
                raise serializers.ValidationError(
                    f"Invalid permission '{perm}'. Valid: {valid_permissions}"
                )
        return value

    def validate_rate_limit(self, value):
        """Validate rate limit is reasonable."""
        if value < 1 or value > 10000:
            raise serializers.ValidationError("Rate limit must be between 1 and 10000.")
        return value

    def create(self, validated_data):
        """Create API key and return with raw key (only time it's visible)."""
        company = self.context["request"].user.company
        raw_key, key_hash = APIKey.generate_key()

        api_key = APIKey.objects.create(
            company=company,
            key_hash=key_hash,
            **validated_data,
        )

        # Attach raw key for response (not saved to DB)
        api_key._raw_key = raw_key
        return api_key


class APIKeyResponseSerializer(APIKeySerializer):
    """Serializer for API key creation response (includes raw key once)."""

    key = serializers.SerializerMethodField()

    class Meta(APIKeySerializer.Meta):
        fields = APIKeySerializer.Meta.fields + ["key"]

    def get_key(self, obj):
        """Return raw key if available (only on creation)."""
        return getattr(obj, "_raw_key", None)


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for AuditLog model (read-only)."""

    user_email = serializers.CharField(source="user.email", read_only=True)
    company_name = serializers.CharField(source="company.name", read_only=True)

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
            "request_path",
            "request_method",
            "response_status",
            "created_at",
        ]
        read_only_fields = fields


class HealthCheckSerializer(serializers.Serializer):
    """Serializer for health check response."""

    status = serializers.CharField()
    version = serializers.CharField()
    timestamp = serializers.DateTimeField()


class CompanyWithTierSerializer(serializers.ModelSerializer):
    """Serializer for Company model with tier information."""

    rate_limit = serializers.IntegerField(read_only=True)
    daily_limit = serializers.IntegerField(read_only=True)
    model_limit = serializers.IntegerField(read_only=True)
    consortium_limit = serializers.IntegerField(read_only=True)

    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "email",
            "tier",
            "custom_rate_limit",
            "custom_daily_limit",
            "industry",
            "website",
            "description",
            "is_active",
            "is_verified",
            "rate_limit",
            "daily_limit",
            "model_limit",
            "consortium_limit",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "tier",
            "is_verified",
            "created_at",
            "updated_at",
        ]


class UsageTrackingSerializer(serializers.ModelSerializer):
    """Serializer for UsageTracking model."""

    company_name = serializers.CharField(source="company.name", read_only=True)

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
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class WebhookSerializer(serializers.ModelSerializer):
    """Serializer for Webhook model."""

    class Meta:
        model = Webhook
        fields = [
            "id",
            "name",
            "url",
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


class WebhookCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a Webhook."""

    secret = serializers.CharField(required=False, write_only=True)

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

    def validate_events(self, value):
        """Validate event types."""
        valid_events = [choice[0] for choice in Webhook.EventType.choices]
        for event in value:
            if event not in valid_events:
                raise serializers.ValidationError(
                    f"Invalid event type '{event}'. Valid types: {valid_events}"
                )
        return value

    def validate_url(self, value):
        """Validate webhook URL."""
        if not value.startswith("https://"):
            raise serializers.ValidationError("Webhook URL must use HTTPS.")
        return value

    def validate_max_retries(self, value):
        """Validate max retries."""
        if value < 0 or value > 10:
            raise serializers.ValidationError("Max retries must be between 0 and 10.")
        return value

    def validate_timeout_seconds(self, value):
        """Validate timeout."""
        if value < 5 or value > 60:
            raise serializers.ValidationError("Timeout must be between 5 and 60 seconds.")
        return value

    def create(self, validated_data):
        """Create webhook with generated secret if not provided."""
        import secrets as py_secrets

        company = self.context["request"].user.company
        if "secret" not in validated_data or not validated_data.get("secret"):
            validated_data["secret"] = py_secrets.token_urlsafe(32)

        webhook = Webhook.objects.create(company=company, **validated_data)
        return webhook


class WebhookResponseSerializer(WebhookSerializer):
    """Serializer for Webhook creation response (includes secret once)."""

    secret = serializers.CharField(read_only=True)

    class Meta(WebhookSerializer.Meta):
        fields = WebhookSerializer.Meta.fields + ["secret"]


class WebhookDeliverySerializer(serializers.ModelSerializer):
    """Serializer for WebhookDelivery model."""

    webhook_name = serializers.CharField(source="webhook.name", read_only=True)

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
            "latency_ms",
            "error_message",
            "created_at",
            "delivered_at",
            "next_retry_at",
        ]
        read_only_fields = fields


class UsageStatsSerializer(serializers.Serializer):
    """Serializer for usage statistics response."""

    tier = serializers.CharField()
    limits = serializers.DictField()
    today = serializers.DictField()
    month = serializers.DictField()

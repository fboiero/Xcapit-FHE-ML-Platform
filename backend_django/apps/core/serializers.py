"""
Core serializers for Xcapit FHE-ML Platform.

Provides validation and serialization for User, Company, and APIKey models.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import APIKey, AuditLog, Company

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

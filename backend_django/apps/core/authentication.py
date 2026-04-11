"""
Authentication module for Xcapit FHE-ML Platform.

Provides JWT authentication, API key authentication, and user management.
"""

import hashlib
import secrets

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken

from .models import APIKey, AuditLog, Company, User


class RegisterSerializer(serializers.Serializer):
    """Serializer for user registration."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=12)
    password_confirm = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    company_name = serializers.CharField(max_length=255, required=False)
    industry = serializers.CharField(max_length=100, required=False, allow_blank=True)

    def validate_email(self, value):
        """Check email is not already registered."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value.lower()

    def validate_password(self, value):
        """Validate password strength."""
        validate_password(value)
        return value

    def validate(self, attrs):
        """Check passwords match."""
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        """Create user and optionally company. Auto-starts 14-day trial."""
        validated_data.pop("password_confirm")
        company_name = validated_data.pop("company_name", None)
        industry = validated_data.pop("industry", "")

        # Create company if provided
        company = None
        if company_name:
            company = Company.objects.create(
                name=company_name,
                email=validated_data["email"],
                industry=industry,
            )
            # Auto-start 14-day trial
            company.start_trial()

            # Create subscription record
            from apps.sandbox.models import Subscription

            Subscription.objects.create(
                company=company,
                plan="free",
                status=Subscription.Status.TRIALING,
                trial_end=company.trial_expires_at,
                current_period_start=company.trial_started_at,
                current_period_end=company.trial_expires_at,
            )

        # Create user
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            company=company,
        )

        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Authenticate user."""
        email = attrs["email"].lower()
        password = attrs["password"]

        user = authenticate(email=email, password=password)

        if not user:
            raise serializers.ValidationError("Invalid credentials.")

        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")

        attrs["user"] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change."""

    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=12)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        """Validate new password strength."""
        validate_password(value)
        return value

    def validate(self, attrs):
        """Check new passwords match."""
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "Passwords do not match."}
            )
        return attrs


class APIKeyAuthentication(BaseAuthentication):
    """
    API Key authentication.

    Clients should pass the API key in the Authorization header:
    Authorization: ApiKey <key>
    """

    keyword = "ApiKey"

    def authenticate(self, request):
        """Authenticate using API key."""
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")

        if not auth_header.startswith(f"{self.keyword} "):
            return None

        key = auth_header[len(self.keyword) + 1:].strip()

        if not key:
            return None

        # Hash the key for lookup
        key_hash = hashlib.sha256(key.encode()).hexdigest()

        try:
            api_key = APIKey.objects.select_related("company", "created_by").get(
                key_hash=key_hash,
                is_active=True,
            )
        except APIKey.DoesNotExist:
            raise AuthenticationFailed("Invalid API key.")

        # Check expiration
        if api_key.expires_at and api_key.expires_at < timezone.now():
            raise AuthenticationFailed("API key has expired.")

        # Update last used
        api_key.last_used_at = timezone.now()
        api_key.save(update_fields=["last_used_at"])

        # Store API key info on request for logging
        request.api_key = api_key

        # Return the user who created the key (or a system user)
        return (api_key.created_by, api_key)

    def authenticate_header(self, request):
        """Return the authentication scheme."""
        return self.keyword


class RegisterView(APIView):
    """User registration endpoint."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Register a new user."""
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        # Log registration
        AuditLog.objects.create(
            action="user_registered",
            resource_type="user",
            resource_id=user.id,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        response_data = {
            "detail": "Registration successful.",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
        }

        # Include trial info if company was created
        if user.company:
            response_data["trial"] = {
                "active": user.company.is_trial,
                "days_remaining": user.company.trial_days_remaining,
                "expires_at": user.company.trial_expires_at,
                "tier": user.company.tier,
                "limits": {
                    "daily_requests": user.company.daily_limit,
                    "upload_bytes": user.company.upload_limit,
                    "training_runs_per_day": user.company.training_limit,
                    "max_consortiums": user.company.consortium_limit,
                    "max_models": user.company.model_limit,
                },
            }

        return Response(response_data, status=status.HTTP_201_CREATED)

    def _get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")


class LoginView(APIView):
    """User login endpoint."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Login and return tokens."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        # Update last login
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        # Log login
        AuditLog.log(
            request,
            action="user_logged_in",
            resource_type="user",
            resource_id=user.id,
        )

        return Response({
            "detail": "Login successful.",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "company_id": str(user.company_id) if user.company_id else None,
            },
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
        })


class LogoutView(APIView):
    """User logout endpoint."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Logout and blacklist refresh token."""
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass  # Token might already be blacklisted

        # Log logout
        AuditLog.log(
            request,
            action="user_logged_out",
            resource_type="user",
            resource_id=request.user.id,
        )

        return Response({"detail": "Logout successful."})


class ChangePasswordView(APIView):
    """Change password endpoint."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Change user password."""
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        # Check current password
        if not user.check_password(serializer.validated_data["current_password"]):
            return Response(
                {"detail": "Current password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Set new password
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        # Invalidate all outstanding refresh tokens for this user
        outstanding = OutstandingToken.objects.filter(user=user)
        for token in outstanding:
            BlacklistedToken.objects.get_or_create(token=token)

        # Log password change
        AuditLog.log(
            request,
            action="password_changed",
            resource_type="user",
            resource_id=user.id,
        )

        return Response({"detail": "Password changed successfully."})


class MeView(APIView):
    """Current user endpoint."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get current user info."""
        user = request.user
        return Response({
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "company": {
                "id": str(user.company.id),
                "name": user.company.name,
            } if user.company else None,
            "is_staff": user.is_staff,
            "date_joined": user.date_joined,
            "last_login": user.last_login,
        })

    def patch(self, request):
        """Update current user info."""
        user = request.user

        allowed_fields = {"first_name", "last_name"}
        update_data = {
            k: v for k, v in request.data.items() if k in allowed_fields
        }

        if update_data:
            serializer = serializers.Serializer(data=update_data)
            serializer.fields["first_name"] = serializers.CharField(
                max_length=150, required=False
            )
            serializer.fields["last_name"] = serializers.CharField(
                max_length=150, required=False
            )
            serializer.is_valid(raise_exception=True)

            for field, value in serializer.validated_data.items():
                setattr(user, field, value)
            user.save(update_fields=list(serializer.validated_data.keys()))

        return Response({
            "detail": "Profile updated.",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
        })


class CreateAPIKeyView(APIView):
    """Create API key endpoint."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Create a new API key."""
        user = request.user

        if not user.company:
            return Response(
                {"detail": "You must belong to a company to create API keys."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        name = request.data.get("name", "")
        if not name:
            return Response(
                {"detail": "API key name is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate secure key
        raw_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        prefix = raw_key[:8]

        # Create API key
        api_key = APIKey.objects.create(
            company=user.company,
            created_by=user,
            name=name,
            key_hash=key_hash,
            prefix=prefix,
        )

        # Log creation
        AuditLog.log(
            request,
            action="api_key_created",
            resource_type="api_key",
            resource_id=api_key.id,
            extra_data={"name": name},
        )

        return Response({
            "detail": "API key created. Save this key - it won't be shown again.",
            "api_key": {
                "id": str(api_key.id),
                "name": api_key.name,
                "key": raw_key,  # Only shown once!
                "prefix": prefix,
                "created_at": api_key.created_at,
            },
        }, status=status.HTTP_201_CREATED)

"""
Core views for Xcapit FHE-ML Platform.

Provides endpoints for user management, company management,
API keys, and system health.
"""

from django.contrib.auth import get_user_model
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import APIKey, AuditLog, Company
from .permissions import IsCompanyMember, IsResourceOwner
from .serializers import (
    APIKeyCreateSerializer,
    APIKeyResponseSerializer,
    APIKeySerializer,
    AuditLogSerializer,
    ChangePasswordSerializer,
    CompanyCreateSerializer,
    CompanySerializer,
    HealthCheckSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)

User = get_user_model()


class HealthCheckView(APIView):
    """
    System health check endpoint.

    Returns system status and version information.
    """

    permission_classes = [AllowAny]

    def get(self, request):
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
def ratelimited_error(request, exception=None):
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

    def get_queryset(self):
        """Filter to user's company only."""
        user = self.request.user
        if user.company:
            return Company.objects.filter(id=user.company.id)
        return Company.objects.none()

    def get_serializer_class(self):
        """Use different serializer for create."""
        if self.action == "create":
            return CompanyCreateSerializer
        return CompanySerializer

    @action(detail=False, methods=["get"])
    def me(self, request):
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

    def get_queryset(self):
        """Filter to users in the same company."""
        user = self.request.user
        if user.company:
            return User.objects.filter(company=user.company)
        return User.objects.filter(id=user.id)

    def get_serializer_class(self):
        """Use different serializers for different actions."""
        if self.action == "create":
            return UserCreateSerializer
        if self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        return UserSerializer

    @action(detail=False, methods=["get", "patch"])
    def me(self, request):
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
    def change_password(self, request):
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

    def get_queryset(self):
        """Filter to company's API keys."""
        user = self.request.user
        if user.company:
            return APIKey.objects.filter(company=user.company)
        return APIKey.objects.none()

    def get_serializer_class(self):
        """Use different serializers for create and response."""
        if self.action == "create":
            return APIKeyCreateSerializer
        return APIKeySerializer

    def create(self, request, *args, **kwargs):
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
    def revoke(self, request, pk=None):
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
    def regenerate(self, request, pk=None):
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

    def get_queryset(self):
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



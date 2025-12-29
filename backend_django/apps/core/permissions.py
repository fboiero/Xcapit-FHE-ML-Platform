"""
Custom permissions for Xcapit FHE-ML Platform.

Provides consortium-based access control and role-based permissions.
"""

from rest_framework import permissions


class IsCompanyMember(permissions.BasePermission):
    """
    Permission that requires user to be a member of the company.
    """

    message = "You must be a member of this company."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.company is not None


class IsConsortiumMember(permissions.BasePermission):
    """
    Permission that requires user to be a member of the consortium.

    Requires consortium_id in the URL kwargs or request data.
    """

    message = "You are not a member of this consortium."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Get consortium_id from various sources
        consortium_id = (
            view.kwargs.get("consortium_id")
            or request.data.get("consortium_id")
            or request.query_params.get("consortium_id")
        )

        if not consortium_id:
            return True  # Let view handle missing consortium_id

        # Check membership via the ConsortiumMember model
        from apps.consortiums.models import ConsortiumMember

        return ConsortiumMember.objects.filter(
            consortium_id=consortium_id,
            company=request.user.company,
            status="active",
        ).exists()


class IsConsortiumOwner(permissions.BasePermission):
    """
    Permission that requires user to be the owner of the consortium.
    """

    message = "Only the consortium owner can perform this action."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        consortium_id = (
            view.kwargs.get("consortium_id")
            or request.data.get("consortium_id")
            or request.query_params.get("consortium_id")
        )

        if not consortium_id:
            return True  # Let view handle missing consortium_id

        from apps.consortiums.models import Consortium

        return Consortium.objects.filter(
            id=consortium_id,
            owner=request.user.company,
        ).exists()


class IsConsortiumAdmin(permissions.BasePermission):
    """
    Permission that requires user to be owner or admin of the consortium.
    """

    message = "Only consortium owners or admins can perform this action."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        consortium_id = (
            view.kwargs.get("consortium_id")
            or request.data.get("consortium_id")
            or request.query_params.get("consortium_id")
        )

        if not consortium_id:
            return True  # Let view handle missing consortium_id

        from apps.consortiums.models import Consortium, ConsortiumMember

        # Check if owner
        if Consortium.objects.filter(id=consortium_id, owner=request.user.company).exists():
            return True

        # Check if admin
        return ConsortiumMember.objects.filter(
            consortium_id=consortium_id,
            company=request.user.company,
            role__in=["admin", "owner"],
            status="active",
        ).exists()


class HasAPIKeyPermission(permissions.BasePermission):
    """
    Permission based on API key permissions.

    Usage in views:
        permission_classes = [HasAPIKeyPermission]
        required_permissions = ['read']  # or ['write'], ['admin']
    """

    message = "API key does not have required permissions."

    def has_permission(self, request, view):
        # Get required permissions from view
        required_permissions = getattr(view, "required_permissions", [])

        if not required_permissions:
            return True  # No specific permissions required

        # Check if request has API key auth
        api_key = getattr(request, "auth", None)
        if not api_key or not hasattr(api_key, "has_permission"):
            return False

        # Check all required permissions
        for permission in required_permissions:
            if not api_key.has_permission(permission):
                return False

        return True


class IsResourceOwner(permissions.BasePermission):
    """
    Permission that checks if user's company owns the resource.

    Requires the model to have an `owner` or `company` field.
    """

    message = "You do not own this resource."

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Check for owner field
        if hasattr(obj, "owner"):
            return obj.owner == request.user.company

        # Check for company field
        if hasattr(obj, "company"):
            return obj.company == request.user.company

        return False


class ReadOnly(permissions.BasePermission):
    """
    Permission that allows only safe (read-only) methods.
    """

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class IsActiveUser(permissions.BasePermission):
    """
    Permission that requires user to be active.
    """

    message = "Your account is not active."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_active


class IsVerifiedCompany(permissions.BasePermission):
    """
    Permission that requires user's company to be verified.
    """

    message = "Your company must be verified to perform this action."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        company = request.user.company
        return company is not None and company.is_verified

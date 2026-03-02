"""
Custom permissions for Xcapit FHE-ML Platform.

Provides consortium-based access control and role-based permissions.

Security policy: fail-closed for write operations without consortium context.
Read operations without consortium context defer to view queryset scoping.
"""

from rest_framework import permissions


def _get_consortium_id(request, view) -> str | None:
    """Extract consortium_id from URL kwargs, request data, or query params.

    Checks multiple sources to support:
    - Direct kwargs (consortium_id)
    - Nested routers (consortium_pk)
    - Request data (consortium_id or consortium)
    - Query params (consortium_id)
    """
    return (
        view.kwargs.get("consortium_id")
        or view.kwargs.get("consortium_pk")
        or request.data.get("consortium_id")
        or request.data.get("consortium")
        or request.query_params.get("consortium_id")
    )


def _resolve_consortium_from_pk(view) -> str | None:
    """Resolve consortium_id from view's pk kwarg for direct-consortium views.

    When a view operates directly on a Consortium (e.g. ConsortiumViewSet actions),
    pk IS the consortium_id. Validates that the pk actually references a Consortium.
    """
    pk = view.kwargs.get("pk")
    if not pk:
        return None
    from apps.consortiums.models import Consortium

    if Consortium.objects.filter(id=pk).exists():
        return pk
    return None


def _check_consortium_context(request, view) -> tuple[str | None, bool]:
    """Determine consortium context and whether to allow the request.

    Returns (consortium_id, should_continue):
    - (id, True): consortium found, proceed with membership check
    - (None, True): no consortium but safe method, defer to queryset scoping
    - (None, False): no consortium and unsafe method, deny access
    """
    consortium_id = _get_consortium_id(request, view)
    if consortium_id:
        return consortium_id, True

    # No consortium_id found in standard locations
    if request.method in permissions.SAFE_METHODS:
        # Read operations: defer to view's queryset scoping
        return None, True

    # Unsafe methods: try pk as consortium_id (for ConsortiumViewSet actions)
    consortium_id = _resolve_consortium_from_pk(view)
    if consortium_id:
        return consortium_id, True

    # Fail-closed: deny write operations without consortium context
    return None, False


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

    Fail-closed for write operations without consortium context.
    Read operations without consortium context defer to queryset scoping.
    """

    message = "You are not a member of this consortium."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        consortium_id, should_continue = _check_consortium_context(request, view)

        if not should_continue:
            return False  # Fail-closed: no consortium context for write operation

        if not consortium_id:
            return True  # Safe method without consortium: defer to queryset scoping

        from apps.consortiums.models import Consortium, ConsortiumMember

        # Owner is implicitly a member
        if Consortium.objects.filter(id=consortium_id, owner=request.user.company).exists():
            return True

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

        consortium_id, should_continue = _check_consortium_context(request, view)

        if not should_continue:
            return False  # Fail-closed: no consortium context for write operation

        if not consortium_id:
            return True  # Safe method without consortium: defer to queryset scoping

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

        consortium_id, should_continue = _check_consortium_context(request, view)

        if not should_continue:
            return False  # Fail-closed: no consortium context for write operation

        if not consortium_id:
            return True  # Safe method without consortium: defer to queryset scoping

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

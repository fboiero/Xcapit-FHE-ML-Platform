"""
Custom permissions for Xcapit FHE-ML Platform.
"""

from rest_framework.permissions import BasePermission


class IsCompanyMember(BasePermission):
    """Requires the user to belong to a company."""

    message = "You must belong to a company to perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "company", None) is not None
        )


class IsConsortiumMember(BasePermission):
    """Requires the user's company to be an active member of the consortium."""

    message = "Your company is not a member of this consortium."

    def has_permission(self, request, view):
        from apps.consortiums.models import Consortium, ConsortiumMember

        user = request.user
        if not user or not user.is_authenticated or not user.company:
            return False

        # Prefer explicit consortium_id from query params or URL kwargs over the
        # generic "pk" kwarg, which may belong to a different resource (e.g. an
        # InferenceEndpoint UUID for detail actions on endpoint views).
        consortium_pk = (
            view.kwargs.get("consortium_pk")
            or view.kwargs.get("consortium_id")
            or request.query_params.get("consortium_id")
            or request.data.get("consortium")
        )
        if not consortium_pk:
            # Fall back to pk only for views registered directly on consortiums
            # (i.e., when the view's basename suggests it's a consortium view).
            basename = getattr(view, "basename", "") or ""
            if "consortium" in basename.lower():
                consortium_pk = view.kwargs.get("pk")

        if not consortium_pk:
            return True  # List views without consortium context pass through

        try:
            consortium = Consortium.objects.get(pk=consortium_pk)
        except (Consortium.DoesNotExist, Exception):
            return False

        # Owner is implicitly a member
        if consortium.owner_id == user.company_id:
            return True

        return ConsortiumMember.objects.filter(
            consortium=consortium,
            company=user.company,
            status="active",
        ).exists()


class IsConsortiumOwner(BasePermission):
    """Requires the user's company to own the consortium."""

    message = "You must be the consortium owner to perform this action."

    def has_permission(self, request, view):
        from apps.consortiums.models import Consortium

        user = request.user
        if not user or not user.is_authenticated:
            return False

        company = getattr(user, "company", None)
        if not company:
            return False

        consortium_id = (
            view.kwargs.get("consortium_id")
            or view.kwargs.get("consortium_pk")
            or view.kwargs.get("pk")
        )
        if not consortium_id:
            return True

        try:
            consortium = Consortium.objects.get(pk=consortium_id)
        except Consortium.DoesNotExist:
            return False

        return consortium.owner_id == company.id


class IsConsortiumAdmin(BasePermission):
    """Requires the user's company to be an admin (or owner) of the consortium."""

    message = "You must be a consortium admin to perform this action."

    def has_permission(self, request, view):
        from apps.consortiums.models import Consortium, ConsortiumMember

        user = request.user
        if not user or not user.is_authenticated:
            return False

        company = getattr(user, "company", None)
        if not company:
            return False

        consortium_id = (
            view.kwargs.get("consortium_id")
            or view.kwargs.get("consortium_pk")
            or view.kwargs.get("pk")
        )
        if not consortium_id:
            return True

        try:
            consortium = Consortium.objects.get(pk=consortium_id)
        except Consortium.DoesNotExist:
            return False

        # Owner is implicitly an admin
        if consortium.owner_id == company.id:
            return True

        return ConsortiumMember.objects.filter(
            consortium=consortium,
            company=company,
            role__in=[ConsortiumMember.Role.ADMIN, ConsortiumMember.Role.OWNER],
            status=ConsortiumMember.Status.ACTIVE,
        ).exists()


class HasAPIKeyPermission(BasePermission):
    """Checks that the API key has the permissions required by the view."""

    message = "Your API key does not have the required permissions."

    def has_permission(self, request, view):
        required = getattr(view, "required_permissions", None)
        if not required:
            return True

        auth = getattr(request, "auth", None)
        if auth is None:
            return False

        return auth.has_permission(required[0] if len(required) == 1 else required)


class IsResourceOwner(BasePermission):
    """Object-level permission: the request user's company must own the object."""

    message = "You do not have permission to access this resource."

    def has_object_permission(self, request, view, obj):
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return False

        company = getattr(user, "company", None)
        if not company:
            return False

        obj_company = getattr(obj, "owner", None) or getattr(obj, "company", None)
        if obj_company is None:
            return False

        return obj_company.id == company.id


class ReadOnly(BasePermission):
    """Only allows safe (read-only) HTTP methods."""

    def has_permission(self, request, view):
        return request.method in ("GET", "HEAD", "OPTIONS")


class IsActiveUser(BasePermission):
    """Requires the user to be active and authenticated."""

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return user.is_active


class IsVerifiedCompany(BasePermission):
    """Requires the user's company to be verified."""

    message = "Your company must be verified to perform this action."

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return False
        company = getattr(user, "company", None)
        if not company:
            return False
        return getattr(company, "is_verified", False)


class IsTrialActive(BasePermission):
    """Blocks access when the company's trial has expired."""

    message = "Your trial has expired. Please upgrade to continue."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        company = getattr(user, "company", None)
        if not company:
            return False

        # Non-trial companies (paid tiers) always pass
        if not company.is_trial:
            return True

        # Trial companies pass only if trial hasn't expired
        return not company.trial_expired

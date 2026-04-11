"""
Base service classes for Xcapit FHE-ML Platform.
"""

from __future__ import annotations

import functools
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from django.db import transaction

if TYPE_CHECKING:
    from django.http import HttpRequest

T = TypeVar("T")
logger = logging.getLogger(__name__)


@dataclass
class ServiceContext:
    """Request context passed to service layer operations.

    Encapsulates the authenticated user, their company, and the
    originating HTTP request so services can make authorisation
    decisions without depending on the view layer.
    """

    user: Any | None = None
    company: Any | None = None
    request: HttpRequest | None = None

    @classmethod
    def from_request(cls, request: HttpRequest) -> ServiceContext:
        """Build a *ServiceContext* from a Django/DRF request.

        If the user is authenticated the company is resolved via the
        ``company`` attribute present on the custom User model.
        """
        user = getattr(request, "user", None)
        if user and getattr(user, "is_authenticated", False):
            company = getattr(user, "company", None)
            return cls(user=user, company=company, request=request)
        return cls(user=None, company=None, request=request)


@dataclass
class ServiceResult(Generic[T]):
    """Standardised result wrapper for service layer operations."""

    success: bool
    data: T | None = None
    error: str | None = None
    error_code: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def details(self) -> dict[str, Any]:
        """Shortcut to access ``metadata['details']``."""
        return self.metadata.get("details", {})

    @classmethod
    def ok(cls, data: T = None, **metadata: Any) -> ServiceResult[T]:
        return cls(success=True, data=data, metadata=metadata)

    @classmethod
    def fail(
        cls, error: str, error_code: str | None = None, **metadata: Any
    ) -> ServiceResult[T]:
        return cls(
            success=False, error=error, error_code=error_code, metadata=metadata
        )


class BaseService:
    """Thin base class for services — provides logger and optional context."""

    def __init__(self, context: ServiceContext | None = None):
        self.logger = logging.getLogger(self.__class__.__module__)
        self.context = context

    # ------------------------------------------------------------------
    # Convenience accessors
    # ------------------------------------------------------------------

    @property
    def request(self) -> HttpRequest | None:
        """Return the originating HTTP request from the context, if available."""
        return self.context.request if self.context else None

    @property
    def user(self) -> Any | None:
        """Return the authenticated user from the context, if available."""
        return self.context.user if self.context else None

    @property
    def company(self) -> Any | None:
        """Return the company from the context, if available."""
        return self.context.company if self.context else None

    def require_user(self) -> Any:
        """Return the user or raise *PermissionError*."""
        if self.user is None:
            raise PermissionError("Authentication required")
        return self.user

    def require_company(self) -> Any:
        """Return the company or raise *PermissionError*."""
        if self.company is None:
            raise PermissionError("Company membership required")
        return self.company

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def atomic(fn):
        """Decorator that wraps a function in a database transaction."""

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            with transaction.atomic():
                return fn(*args, **kwargs)

        return wrapper

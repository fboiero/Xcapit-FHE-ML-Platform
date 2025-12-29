"""
Base service class for Xcapit FHE-ML Platform.

Provides common functionality for all services including:
- Request context management
- Audit logging integration
- Error handling utilities
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from django.db import models, transaction

if TYPE_CHECKING:
    from apps.core.models import Company, User
    from django.http import HttpRequest


T = TypeVar("T", bound=models.Model)


@dataclass
class ServiceContext:
    """Context for service operations."""

    user: User | None = None
    company: Company | None = None
    request: HttpRequest | None = None

    @classmethod
    def from_request(cls, request: HttpRequest) -> ServiceContext:
        """Create context from HTTP request."""
        user = request.user if request.user.is_authenticated else None
        company = getattr(user, "company", None) if user else None
        return cls(user=user, company=company, request=request)


@dataclass
class ServiceResult(Generic[T]):
    """
    Result wrapper for service operations.

    Provides a consistent way to return success/failure from services.
    """

    success: bool
    data: T | None = None
    error: str | None = None
    error_code: str | None = None
    details: dict[str, Any] | None = None

    @classmethod
    def ok(cls, data: T | None = None) -> ServiceResult[T]:
        """Create a successful result."""
        return cls(success=True, data=data)

    @classmethod
    def fail(
        cls,
        error: str,
        error_code: str = "error",
        details: dict[str, Any] | None = None,
    ) -> ServiceResult[T]:
        """Create a failed result."""
        return cls(
            success=False,
            error=error,
            error_code=error_code,
            details=details,
        )


class BaseService:
    """
    Base class for all services.

    Provides common functionality:
    - Context management (user, company, request)
    - Transaction handling
    - Audit logging hooks
    """

    def __init__(self, context: ServiceContext | None = None) -> None:
        """Initialize service with optional context."""
        self.context = context or ServiceContext()

    @property
    def user(self) -> User | None:
        """Get current user from context."""
        return self.context.user

    @property
    def company(self) -> Company | None:
        """Get current company from context."""
        return self.context.company

    @property
    def request(self) -> HttpRequest | None:
        """Get current request from context."""
        return self.context.request

    def require_user(self) -> User:
        """Require authenticated user, raise if not present."""
        if not self.user:
            raise PermissionError("Authentication required")
        return self.user

    def require_company(self) -> Company:
        """Require user with company, raise if not present."""
        if not self.company:
            raise PermissionError("Company membership required")
        return self.company

    @staticmethod
    def atomic(func):
        """Decorator for atomic transactions."""
        def wrapper(*args, **kwargs):
            with transaction.atomic():
                return func(*args, **kwargs)
        return wrapper

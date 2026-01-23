"""
Audit service for Xcapit FHE-ML Platform.

Provides centralized audit logging functionality.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import BaseService, ServiceContext

if TYPE_CHECKING:
    from uuid import UUID

    from django.http import HttpRequest


class AuditService(BaseService):
    """
    Service for audit logging operations.

    Centralizes all audit logging to ensure consistency
    and proper handling of sensitive data.
    """

    def log(
        self,
        action: str,
        resource_type: str,
        resource_id: str | UUID = "",
        extra_data: dict[str, Any] | None = None,
    ) -> None:
        """
        Log an audit event.

        Args:
            action: The action performed (e.g., 'created', 'updated', 'deleted')
            resource_type: Type of resource affected (e.g., 'consortium', 'model')
            resource_id: Unique identifier of the resource
            extra_data: Additional context (sanitized, no PII)
        """
        from apps.core.models import AuditLog

        if self.request:
            AuditLog.log(
                request=self.request,
                action=action,
                resource_type=resource_type,
                resource_id=str(resource_id),
                extra_data=extra_data,
            )

    @classmethod
    def log_from_request(
        cls,
        request: HttpRequest,
        action: str,
        resource_type: str,
        resource_id: str | UUID = "",
        extra_data: dict[str, Any] | None = None,
    ) -> None:
        """
        Convenience method to log directly from a request.

        Args:
            request: The HTTP request
            action: The action performed
            resource_type: Type of resource affected
            resource_id: Unique identifier of the resource
            extra_data: Additional context
        """
        service = cls(ServiceContext.from_request(request))
        service.log(action, resource_type, resource_id, extra_data)

"""
Core services for Xcapit FHE-ML Platform.

This module provides the service layer that encapsulates business logic,
following the Service Layer pattern for better separation of concerns.
"""

from .audit import AuditService
from .base import BaseService, ServiceContext, ServiceResult
from .rate_limiting import RateLimitMiddleware, RateLimitResult, RateLimitService
from .webhook import WebhookService, trigger_webhook_event

__all__ = [
    "BaseService",
    "ServiceContext",
    "ServiceResult",
    "AuditService",
    "RateLimitService",
    "RateLimitResult",
    "RateLimitMiddleware",
    "WebhookService",
    "trigger_webhook_event",
]

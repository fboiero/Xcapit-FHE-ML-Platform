"""
Core services for Xcapit FHE-ML Platform.

This module provides the service layer that encapsulates business logic,
following the Service Layer pattern for better separation of concerns.
"""

from .base import BaseService
from .audit import AuditService

__all__ = ["BaseService", "AuditService"]

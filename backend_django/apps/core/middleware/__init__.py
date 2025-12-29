"""
Middleware for Xcapit FHE-ML Platform.

Provides:
- CorrelationIdMiddleware: Request correlation tracking
- RequestLoggingMiddleware: Structured request/response logging
"""

from .correlation import CorrelationIdMiddleware
from .request_logging import RequestLoggingMiddleware

__all__ = [
    "CorrelationIdMiddleware",
    "RequestLoggingMiddleware",
]

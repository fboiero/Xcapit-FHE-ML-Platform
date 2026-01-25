"""
Correlation ID middleware for request tracing.

Generates or propagates correlation IDs for distributed tracing
across service boundaries.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Callable

from django.http import HttpRequest, HttpResponse

from apps.core.logging import (
    clear_correlation_id,
    clear_request_context,
    set_correlation_id,
    set_request_context,
)

if TYPE_CHECKING:
    pass


# Standard header names for correlation ID
CORRELATION_ID_HEADERS = [
    "HTTP_X_CORRELATION_ID",
    "HTTP_X_REQUEST_ID",
    "HTTP_X_TRACE_ID",
]

RESPONSE_HEADER = "X-Correlation-ID"


class CorrelationIdMiddleware:
    """
    Middleware that manages correlation IDs for request tracing.

    Features:
    - Extracts correlation ID from incoming request headers
    - Generates a new correlation ID if none provided
    - Adds correlation ID to response headers
    - Makes correlation ID available via context variables for logging

    Supported incoming headers (in priority order):
    - X-Correlation-ID
    - X-Request-ID
    - X-Trace-ID
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        """Initialize middleware."""
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process request with correlation ID."""
        # Extract or generate correlation ID
        correlation_id = self._extract_correlation_id(request)
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Set correlation ID in context variable
        set_correlation_id(correlation_id)

        # Set request context for logging enrichment
        request_context = self._build_request_context(request)
        set_request_context(request_context)

        # Store on request object for easy access in views
        request.correlation_id = correlation_id  # type: ignore[attr-defined]

        try:
            # Process request
            response = self.get_response(request)

            # Add correlation ID to response headers
            response[RESPONSE_HEADER] = correlation_id

            return response
        finally:
            # Clean up context variables
            clear_correlation_id()
            clear_request_context()

    def _extract_correlation_id(self, request: HttpRequest) -> str | None:
        """
        Extract correlation ID from request headers.

        Checks multiple header names in priority order.
        """
        for header in CORRELATION_ID_HEADERS:
            correlation_id = request.META.get(header)
            if correlation_id:
                return correlation_id
        return None

    def _build_request_context(self, request: HttpRequest) -> dict:
        """Build context dictionary for logging enrichment."""
        context = {
            "path": request.path,
            "method": request.method,
        }

        # Add user info if authenticated
        if hasattr(request, "user") and request.user.is_authenticated:
            context["user_id"] = str(request.user.id)
            if hasattr(request.user, "company_id") and request.user.company_id:
                context["company_id"] = str(request.user.company_id)

        return context

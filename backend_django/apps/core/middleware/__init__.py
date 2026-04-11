"""
Core middleware for Xcapit FHE-ML Platform.
"""

import logging
import uuid

from django.utils import timezone

logger = logging.getLogger(__name__)


class CorrelationIdMiddleware:
    """Adds a unique correlation ID to every request for distributed tracing."""

    HEADER = "X-Correlation-ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        correlation_id = request.META.get(
            f"HTTP_{self.HEADER.upper().replace('-', '_')}",
            str(uuid.uuid4()),
        )
        request.correlation_id = correlation_id
        response = self.get_response(request)
        response[self.HEADER] = correlation_id
        return response


class RequestLoggingMiddleware:
    """Logs request method, path, status, and duration."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = timezone.now()
        response = self.get_response(request)
        duration = (timezone.now() - start).total_seconds()

        if request.path.startswith("/api/"):
            logger.info(
                "%s %s %s %.3fs",
                request.method,
                request.path,
                response.status_code,
                duration,
            )

        return response

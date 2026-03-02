"""
Request logging middleware for structured HTTP request/response logging.

Provides detailed logging of API requests with timing metrics.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Callable

from django.http import HttpRequest, HttpResponse

from apps.core.logging import get_correlation_id

if TYPE_CHECKING:
    pass


logger = logging.getLogger("apps.api.requests")

# Paths to exclude from detailed logging
EXCLUDED_PATHS = {
    "/health/",
    "/api/health/",
    "/favicon.ico",
    "/robots.txt",
}

# Sensitive headers to redact
SENSITIVE_HEADERS = {
    "HTTP_AUTHORIZATION",
    "HTTP_X_API_KEY",
    "HTTP_COOKIE",
}


class RequestLoggingMiddleware:
    """
    Middleware for structured request/response logging.

    Logs:
    - Request method, path, and query parameters
    - Response status code
    - Request duration
    - User and correlation context
    - Client IP and user agent

    Excludes:
    - Health check endpoints
    - Static files
    - Favicon requests
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        """Initialize middleware."""
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process request with logging."""
        # Skip logging for excluded paths
        if self._should_skip(request):
            return self.get_response(request)

        # Record start time
        start_time = time.perf_counter()

        # Extract request metadata before processing
        request_metadata = self._extract_request_metadata(request)

        # Log request start (debug level)
        logger.debug(
            "Request started",
            extra={
                "event": "request_start",
                **request_metadata,
            },
        )

        # Process request
        response = self.get_response(request)

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Log request completion
        self._log_request_completion(
            request_metadata,
            response,
            duration_ms,
        )

        return response

    def _should_skip(self, request: HttpRequest) -> bool:
        """Check if request should be skipped from logging."""
        return request.path in EXCLUDED_PATHS

    def _extract_request_metadata(self, request: HttpRequest) -> dict:
        """Extract metadata from request for logging."""
        metadata = {
            "method": request.method,
            "path": request.path,
            "correlation_id": get_correlation_id() or "-",
        }

        # Query parameters (exclude sensitive ones)
        if request.GET:
            safe_params = {
                k: v for k, v in request.GET.items()
                if k.lower() not in {"password", "token", "key", "secret"}
            }
            if safe_params:
                metadata["query_params"] = safe_params

        # Client info
        metadata["client_ip"] = self._get_client_ip(request)
        metadata["user_agent"] = request.META.get("HTTP_USER_AGENT", "-")[:200]

        # User info (if authenticated) — no PII logged
        if hasattr(request, "user") and request.user.is_authenticated:
            metadata["user_id"] = str(request.user.id)

        # Content type and length
        content_type = request.content_type
        if content_type:
            metadata["content_type"] = content_type

        content_length = request.META.get("CONTENT_LENGTH")
        if content_length:
            metadata["content_length"] = int(content_length)

        return metadata

    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP, handling proxies."""
        # Check for forwarded header (when behind proxy/load balancer)
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            # Take the first IP (client IP)
            return x_forwarded_for.split(",")[0].strip()

        # Check for real IP header
        x_real_ip = request.META.get("HTTP_X_REAL_IP")
        if x_real_ip:
            return x_real_ip

        # Fall back to remote addr
        return request.META.get("REMOTE_ADDR", "-")

    def _log_request_completion(
        self,
        request_metadata: dict,
        response: HttpResponse,
        duration_ms: float,
    ) -> None:
        """Log request completion with response details."""
        log_data = {
            "event": "request_complete",
            **request_metadata,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        }

        # Add response content length if available
        content_length = response.get("Content-Length")
        if content_length:
            log_data["response_size"] = int(content_length)

        # Determine log level based on status code
        if response.status_code >= 500:
            level = logging.ERROR
            log_data["error"] = True
        elif response.status_code >= 400:
            level = logging.WARNING
            log_data["client_error"] = True
        else:
            level = logging.INFO

        # Format log message
        message = (
            f"{request_metadata['method']} {request_metadata['path']} "
            f"{response.status_code} {duration_ms:.2f}ms"
        )

        logger.log(level, message, extra=log_data)

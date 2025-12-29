"""
Custom exception handling for Xcapit FHE-ML Platform.

Provides sanitized error responses that don't leak internal information.
"""

import logging

from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    Throttled,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


class ServiceUnavailable(APIException):
    """503 Service Unavailable exception."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Service temporarily unavailable. Please try again later."
    default_code = "service_unavailable"


class ConflictError(APIException):
    """409 Conflict exception."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "Resource conflict."
    default_code = "conflict"


class RateLimitExceeded(APIException):
    """429 Rate Limit Exceeded exception."""

    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = "Rate limit exceeded. Please try again later."
    default_code = "rate_limit_exceeded"


class InsufficientPermissions(APIException):
    """403 Insufficient Permissions exception."""

    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "You do not have permission to perform this action."
    default_code = "insufficient_permissions"


class ResourceNotFound(APIException):
    """404 Resource Not Found exception."""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Resource not found."
    default_code = "not_found"


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF.

    Provides sanitized error responses and logging.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # Get request info for logging
    request = context.get("request")
    view = context.get("view")

    # Log the exception
    _log_exception(exc, request, view)

    if response is not None:
        # Standardize error response format
        response.data = _format_error_response(exc, response.status_code)

        # Add security headers
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"

        return response

    # Handle exceptions not handled by DRF
    if isinstance(exc, Http404):
        return Response(
            _format_error_response(ResourceNotFound(), status.HTTP_404_NOT_FOUND),
            status=status.HTTP_404_NOT_FOUND,
        )

    if isinstance(exc, PermissionDenied):
        return Response(
            _format_error_response(InsufficientPermissions(), status.HTTP_403_FORBIDDEN),
            status=status.HTTP_403_FORBIDDEN,
        )

    # Log unhandled exceptions with full traceback
    logger.exception(
        "Unhandled exception in %s: %s",
        view.__class__.__name__ if view else "unknown",
        str(exc),
    )

    # Return generic 500 error (never expose internal details)
    return Response(
        {
            "error": {
                "code": "internal_error",
                "message": "An internal error occurred. Please try again later.",
                "status": 500,
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _format_error_response(exc, status_code):
    """
    Format exception into standardized error response.

    Response format:
    {
        "error": {
            "code": "error_code",
            "message": "Human-readable message",
            "status": 400,
            "details": {}  # Optional validation errors
        }
    }
    """
    error_response = {
        "error": {
            "code": _get_error_code(exc),
            "message": _get_error_message(exc),
            "status": status_code,
        }
    }

    # Add validation details for ValidationError
    if isinstance(exc, ValidationError):
        error_response["error"]["details"] = _sanitize_validation_errors(exc.detail)

    # Add retry-after for rate limiting
    if isinstance(exc, (Throttled, RateLimitExceeded)):
        if hasattr(exc, "wait") and exc.wait:
            error_response["error"]["retry_after"] = int(exc.wait)

    return error_response


def _get_error_code(exc):
    """Get error code from exception."""
    if hasattr(exc, "default_code"):
        return exc.default_code

    # Map common exceptions to codes
    exception_codes = {
        ValidationError: "validation_error",
        AuthenticationFailed: "authentication_failed",
        NotAuthenticated: "not_authenticated",
        PermissionDenied: "permission_denied",
        Throttled: "rate_limit_exceeded",
    }

    for exc_class, code in exception_codes.items():
        if isinstance(exc, exc_class):
            return code

    return "error"


def _get_error_message(exc):
    """Get sanitized error message from exception."""
    if hasattr(exc, "detail"):
        detail = exc.detail

        # Handle list of errors
        if isinstance(detail, list):
            return detail[0] if detail else "An error occurred."

        # Handle dict of errors (validation)
        if isinstance(detail, dict):
            return "Validation error. See details for more information."

        return str(detail)

    return str(exc) if str(exc) else "An error occurred."


def _sanitize_validation_errors(errors):
    """Sanitize validation errors to remove sensitive information."""
    if isinstance(errors, dict):
        sanitized = {}
        for field, error_list in errors.items():
            if isinstance(error_list, list):
                sanitized[field] = [str(e) for e in error_list]
            else:
                sanitized[field] = [str(error_list)]
        return sanitized

    if isinstance(errors, list):
        return [str(e) for e in errors]

    return {"non_field_errors": [str(errors)]}


def _log_exception(exc, request, view):
    """Log exception with appropriate level and context."""
    view_name = view.__class__.__name__ if view else "unknown"

    # Don't log expected client errors at warning/error level
    if isinstance(exc, (ValidationError, NotAuthenticated, AuthenticationFailed)):
        logger.info(
            "Client error in %s: %s - %s",
            view_name,
            exc.__class__.__name__,
            str(exc.detail) if hasattr(exc, "detail") else str(exc),
        )
        return

    if isinstance(exc, (Throttled, RateLimitExceeded)):
        logger.warning(
            "Rate limit hit in %s from %s",
            view_name,
            _get_client_ip(request) if request else "unknown",
        )
        return

    if isinstance(exc, PermissionDenied):
        logger.warning(
            "Permission denied in %s for user %s",
            view_name,
            request.user if request and request.user.is_authenticated else "anonymous",
        )
        return

    # Log other exceptions as errors
    logger.error(
        "Exception in %s: %s - %s",
        view_name,
        exc.__class__.__name__,
        str(exc),
        exc_info=True,
    )


def _get_client_ip(request):
    """Get client IP from request."""
    if not request:
        return "unknown"

    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")

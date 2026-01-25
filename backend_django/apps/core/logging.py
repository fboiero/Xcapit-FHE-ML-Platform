"""
Structured JSON logging for Xcapit FHE-ML Platform.

Provides:
- JSON-formatted log output for production
- Correlation ID injection
- Request context enrichment
- Performance metrics logging
"""

from __future__ import annotations

import logging
import time
import uuid
from contextvars import ContextVar
from typing import Any

from pythonjsonlogger import jsonlogger


# Context variable for correlation ID (thread-safe)
correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)
request_context_var: ContextVar[dict[str, Any]] = ContextVar(
    "request_context", default={}
)


def get_correlation_id() -> str | None:
    """Get the current correlation ID from context."""
    return correlation_id_var.get()


def set_correlation_id(correlation_id: str | None = None) -> str:
    """Set a correlation ID in context, generating one if not provided."""
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    correlation_id_var.set(correlation_id)
    return correlation_id


def clear_correlation_id() -> None:
    """Clear the correlation ID from context."""
    correlation_id_var.set(None)


def get_request_context() -> dict[str, Any]:
    """Get the current request context."""
    return request_context_var.get()


def set_request_context(context: dict[str, Any]) -> None:
    """Set request context for logging enrichment."""
    request_context_var.set(context)


def clear_request_context() -> None:
    """Clear request context."""
    request_context_var.set({})


class CorrelationIdFilter(logging.Filter):
    """
    Logging filter that adds correlation ID to log records.

    This filter injects the current correlation ID from the context
    variable into every log record.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation_id to the log record."""
        record.correlation_id = get_correlation_id() or "-"

        # Add request context
        context = get_request_context()
        record.user_id = context.get("user_id", "-")
        record.company_id = context.get("company_id", "-")
        record.path = context.get("path", "-")
        record.method = context.get("method", "-")

        return True


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter for structured logging.

    Adds standard fields to all log messages:
    - timestamp
    - level
    - correlation_id
    - service name
    - environment info
    """

    def __init__(
        self,
        *args: Any,
        service_name: str = "xcapit-fheml",
        environment: str = "development",
        **kwargs: Any,
    ) -> None:
        """Initialize formatter with service metadata."""
        super().__init__(*args, **kwargs)
        self.service_name = service_name
        self.environment = environment

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        """Add custom fields to the JSON log record."""
        super().add_fields(log_record, record, message_dict)

        # Standard fields
        log_record["timestamp"] = self.formatTime(record)
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["service"] = self.service_name
        log_record["environment"] = self.environment

        # Correlation and context
        log_record["correlation_id"] = getattr(record, "correlation_id", "-")
        log_record["user_id"] = getattr(record, "user_id", "-")
        log_record["company_id"] = getattr(record, "company_id", "-")

        # Request info (if available)
        if hasattr(record, "path") and record.path != "-":
            log_record["request"] = {
                "path": record.path,
                "method": getattr(record, "method", "-"),
            }

        # Exception info
        if record.exc_info:
            log_record["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
            }

        # Remove redundant fields
        for field in ["asctime", "created", "msecs", "relativeCreated"]:
            log_record.pop(field, None)


class PerformanceLogger:
    """
    Context manager for logging performance metrics.

    Usage:
        with PerformanceLogger("database_query", logger) as perf:
            result = execute_query()
            perf.add_metadata(rows=len(result))
    """

    def __init__(
        self,
        operation: str,
        logger: logging.Logger,
        level: int = logging.INFO,
    ) -> None:
        """Initialize performance logger."""
        self.operation = operation
        self.logger = logger
        self.level = level
        self.start_time: float = 0
        self.metadata: dict[str, Any] = {}

    def add_metadata(self, **kwargs: Any) -> None:
        """Add metadata to be included in the log."""
        self.metadata.update(kwargs)

    def __enter__(self) -> PerformanceLogger:
        """Start timing."""
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Log performance metrics."""
        duration_ms = (time.perf_counter() - self.start_time) * 1000

        log_data = {
            "operation": self.operation,
            "duration_ms": round(duration_ms, 2),
            "success": exc_type is None,
            **self.metadata,
        }

        if exc_type:
            log_data["error"] = str(exc_val)
            self.logger.log(logging.ERROR, f"Operation failed: {self.operation}", extra=log_data)
        else:
            self.logger.log(self.level, f"Operation completed: {self.operation}", extra=log_data)


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


# Convenience function for structured logging
def log_event(
    logger: logging.Logger,
    event: str,
    level: int = logging.INFO,
    **kwargs: Any,
) -> None:
    """
    Log a structured event with additional context.

    Args:
        logger: Logger instance
        event: Event name/description
        level: Log level
        **kwargs: Additional fields to include
    """
    logger.log(level, event, extra=kwargs)

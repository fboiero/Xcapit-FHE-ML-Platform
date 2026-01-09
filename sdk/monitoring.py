"""Monitoring module for Xcapit FHE-ML Platform.

Provides structured logging, metrics collection, and performance monitoring.
"""

import json
import logging
import sys
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar

# ========== Structured Logger ==========


class StructuredFormatter(logging.Formatter):
    """JSON-based structured log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        extra_fields = {
            k: v
            for k, v in record.__dict__.items()
            if k
            not in {
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "exc_info",
                "exc_text",
                "thread",
                "threadName",
                "message",
                "asctime",
            }
        }
        if extra_fields:
            log_entry["extra"] = extra_fields

        return json.dumps(log_entry)


class ConsoleFormatter(logging.Formatter):
    """Human-readable console log formatter with colors."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record for console output."""
        color = self.COLORS.get(record.levelname, "")
        timestamp = datetime.utcnow().strftime("%H:%M:%S")

        # Build base message
        msg = f"{color}[{timestamp}] {record.levelname:8}{self.RESET} {record.getMessage()}"

        # Add extra context
        extra_fields = {
            k: v
            for k, v in record.__dict__.items()
            if k
            not in {
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "exc_info",
                "exc_text",
                "thread",
                "threadName",
                "message",
                "asctime",
            }
        }
        if extra_fields:
            msg += f" | {extra_fields}"

        return msg


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    json_format: bool = False,
    console: bool = True,
) -> logging.Logger:
    """Setup logging configuration.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional file path for log output.
        json_format: Use JSON format for file logs.
        console: Enable console output.

    Returns:
        Root logger configured.
    """
    logger = logging.getLogger("fheml")
    logger.setLevel(getattr(logging, level.upper()))
    logger.handlers.clear()

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ConsoleFormatter())
        logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(str(log_file))
        if json_format:
            file_handler.setFormatter(StructuredFormatter())
        else:
            file_handler.setFormatter(
                logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
            )
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "fheml") -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (hierarchical, e.g., "fheml.api.server").

    Returns:
        Logger instance.
    """
    return logging.getLogger(name)


# ========== Metrics Collection ==========


@dataclass
class MetricPoint:
    """A single metric data point."""

    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """Collects and aggregates metrics.

    Thread-safe metrics collection for counters, gauges, and histograms.
    """

    def __init__(self):
        self._counters: dict[str, float] = {}
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = {}
        self._lock = threading.Lock()
        self._start_time = time.time()

    def increment(
        self, name: str, value: float = 1.0, tags: Optional[dict[str, str]] = None
    ) -> None:
        """Increment a counter.

        Args:
            name: Metric name.
            value: Value to add (default: 1).
            tags: Optional tags for the metric.
        """
        key = self._make_key(name, tags)
        with self._lock:
            self._counters[key] = self._counters.get(key, 0) + value

    def gauge(self, name: str, value: float, tags: Optional[dict[str, str]] = None) -> None:
        """Set a gauge value.

        Args:
            name: Metric name.
            value: Current value.
            tags: Optional tags for the metric.
        """
        key = self._make_key(name, tags)
        with self._lock:
            self._gauges[key] = value

    def histogram(self, name: str, value: float, tags: Optional[dict[str, str]] = None) -> None:
        """Record a histogram value.

        Args:
            name: Metric name.
            value: Value to record.
            tags: Optional tags for the metric.
        """
        key = self._make_key(name, tags)
        with self._lock:
            if key not in self._histograms:
                self._histograms[key] = []
            self._histograms[key].append(value)

    @contextmanager
    def timer(self, name: str, tags: Optional[dict[str, str]] = None):
        """Context manager to time operations.

        Args:
            name: Metric name.
            tags: Optional tags for the metric.

        Usage:
            with metrics.timer("prediction_time"):
                result = model.predict(data)
        """
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self.histogram(name, elapsed_ms, tags)

    def _make_key(self, name: str, tags: Optional[dict[str, str]] = None) -> str:
        """Create a unique key from name and tags."""
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"

    def get_counter(self, name: str, tags: Optional[dict[str, str]] = None) -> float:
        """Get current counter value."""
        key = self._make_key(name, tags)
        with self._lock:
            return self._counters.get(key, 0)

    def get_gauge(self, name: str, tags: Optional[dict[str, str]] = None) -> float:
        """Get current gauge value."""
        key = self._make_key(name, tags)
        with self._lock:
            return self._gauges.get(key, 0)

    def get_histogram_stats(
        self, name: str, tags: Optional[dict[str, str]] = None
    ) -> dict[str, float]:
        """Get histogram statistics.

        Returns:
            Dict with count, sum, min, max, avg, p50, p95, p99.
        """
        key = self._make_key(name, tags)
        with self._lock:
            values = self._histograms.get(key, [])

        if not values:
            return {"count": 0}

        values_sorted = sorted(values)
        count = len(values)

        return {
            "count": count,
            "sum": sum(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / count,
            "p50": values_sorted[int(count * 0.5)],
            "p95": values_sorted[int(count * 0.95)] if count >= 20 else values_sorted[-1],
            "p99": values_sorted[int(count * 0.99)] if count >= 100 else values_sorted[-1],
        }

    def get_all_metrics(self) -> dict[str, Any]:
        """Get all metrics as a dict.

        Returns:
            Dict with counters, gauges, and histograms.
        """
        with self._lock:
            return {
                "uptime_seconds": time.time() - self._start_time,
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {k: self._get_stats(v) for k, v in self._histograms.items()},
            }

    def _get_stats(self, values: list[float]) -> dict[str, float]:
        """Calculate statistics for a list of values."""
        if not values:
            return {"count": 0}
        sorted(values)
        count = len(values)
        return {
            "count": count,
            "sum": sum(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / count,
        }

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._start_time = time.time()


# Global metrics instance
_metrics: Optional[MetricsCollector] = None


def get_metrics() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics
    if _metrics is None:
        _metrics = MetricsCollector()
    return _metrics


# ========== Decorators ==========

F = TypeVar("F", bound=Callable[..., Any])


def log_call(logger: Optional[logging.Logger] = None, level: str = "DEBUG") -> Callable[[F], F]:
    """Decorator to log function calls.

    Args:
        logger: Logger to use (default: fheml logger).
        level: Log level for the message.

    Returns:
        Decorated function.
    """

    def decorator(func: F) -> F:
        log = logger or get_logger()

        @wraps(func)
        def wrapper(*args, **kwargs):
            log_level = getattr(logging, level.upper())
            log.log(
                log_level,
                f"Calling {func.__name__}",
                extra={
                    "args_count": len(args),
                    "kwargs": list(kwargs.keys()),
                },
            )
            try:
                result = func(*args, **kwargs)
                log.log(log_level, f"Completed {func.__name__}")
                return result
            except Exception as e:
                log.error(f"Error in {func.__name__}: {e}")
                raise

        return wrapper  # type: ignore

    return decorator


def timed(
    metric_name: Optional[str] = None, tags: Optional[dict[str, str]] = None
) -> Callable[[F], F]:
    """Decorator to time function execution.

    Args:
        metric_name: Name for the metric (default: function name).
        tags: Tags for the metric.

    Returns:
        Decorated function.
    """

    def decorator(func: F) -> F:
        name = metric_name or f"{func.__module__}.{func.__name__}"

        @wraps(func)
        def wrapper(*args, **kwargs):
            with get_metrics().timer(name, tags):
                return func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator


def count_calls(
    metric_name: Optional[str] = None, tags: Optional[dict[str, str]] = None
) -> Callable[[F], F]:
    """Decorator to count function calls.

    Args:
        metric_name: Name for the counter (default: function name + "_calls").
        tags: Tags for the metric.

    Returns:
        Decorated function.
    """

    def decorator(func: F) -> F:
        name = metric_name or f"{func.__module__}.{func.__name__}_calls"

        @wraps(func)
        def wrapper(*args, **kwargs):
            get_metrics().increment(name, tags=tags)
            return func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator


# ========== Health Check ==========


@dataclass
class HealthStatus:
    """System health status."""

    status: str  # healthy, degraded, unhealthy
    checks: dict[str, bool]
    metrics: dict[str, Any]
    uptime_seconds: float


def get_health_status() -> HealthStatus:
    """Get system health status.

    Returns:
        HealthStatus with current system state.
    """
    metrics = get_metrics()
    all_metrics = metrics.get_all_metrics()

    checks = {
        "metrics_collecting": True,
    }

    # Determine overall status
    if all(checks.values()):
        status = "healthy"
    elif any(checks.values()):
        status = "degraded"
    else:
        status = "unhealthy"

    return HealthStatus(
        status=status,
        checks=checks,
        metrics=all_metrics,
        uptime_seconds=all_metrics["uptime_seconds"],
    )


# ========== Standard Metrics Names ==========


class Metrics:
    """Standard metric names for the platform."""

    # API metrics
    API_REQUESTS = "api.requests"
    API_LATENCY = "api.latency_ms"
    API_ERRORS = "api.errors"

    # Model metrics
    MODEL_TRAININGS = "model.trainings"
    MODEL_PREDICTIONS = "model.predictions"
    MODEL_TRAINING_TIME = "model.training_time_ms"
    MODEL_PREDICTION_TIME = "model.prediction_time_ms"

    # Encryption metrics
    ENCRYPTION_OPS = "encryption.operations"
    ENCRYPTION_TIME = "encryption.time_ms"
    DECRYPTION_TIME = "decryption.time_ms"

    # Database metrics
    DB_QUERIES = "db.queries"
    DB_QUERY_TIME = "db.query_time_ms"

    # Blockchain metrics
    BLOCKCHAIN_TXS = "blockchain.transactions"
    BLOCKCHAIN_TX_TIME = "blockchain.tx_time_ms"

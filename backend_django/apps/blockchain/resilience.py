"""
Resilience patterns for blockchain and external service interactions.

Provides:
- Retry with exponential backoff
- Circuit breaker pattern
- Timeout handling
- Graceful degradation
"""

from __future__ import annotations

import functools
import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from threading import Lock
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5  # Failures before opening circuit
    recovery_timeout: int = 30  # Seconds before trying again
    success_threshold: int = 2  # Successes needed to close circuit
    excluded_exceptions: tuple = ()  # Exceptions that don't count as failures


@dataclass
class CircuitBreakerState:
    """Internal state of a circuit breaker."""

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: datetime | None = None
    last_success_time: datetime | None = None


class CircuitBreaker:
    """
    Circuit breaker for external service calls.

    Prevents cascading failures by failing fast when a service is down.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service is failing, requests rejected immediately
    - HALF_OPEN: Testing if service has recovered

    Usage:
        circuit = CircuitBreaker("blockchain_rpc", failure_threshold=5)

        @circuit
        def call_blockchain():
            # External call here
            pass

        # Or as context manager
        with circuit:
            result = risky_operation()
    """

    _instances: dict[str, CircuitBreaker] = {}
    _lock = Lock()

    def __new__(cls, name: str, **kwargs) -> CircuitBreaker:
        """Singleton per circuit name."""
        with cls._lock:
            if name not in cls._instances:
                instance = super().__new__(cls)
                cls._instances[name] = instance
            return cls._instances[name]

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        success_threshold: int = 2,
        excluded_exceptions: tuple = (),
    ) -> None:
        """Initialize circuit breaker."""
        # Only initialize once (singleton)
        if hasattr(self, "_initialized"):
            return

        self.name = name
        self.config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            success_threshold=success_threshold,
            excluded_exceptions=excluded_exceptions,
        )
        self._state = CircuitBreakerState()
        self._state_lock = Lock()
        self._initialized = True

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state.state

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self._state.state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (failing fast)."""
        self._check_recovery_timeout()
        return self._state.state == CircuitState.OPEN

    def _check_recovery_timeout(self) -> None:
        """Check if recovery timeout has elapsed."""
        with self._state_lock:
            if self._state.state != CircuitState.OPEN:
                return

            if self._state.last_failure_time is None:
                return

            elapsed = datetime.now(UTC) - self._state.last_failure_time
            if elapsed > timedelta(seconds=self.config.recovery_timeout):
                logger.info(f"Circuit {self.name}: OPEN -> HALF_OPEN (recovery timeout)")
                self._state.state = CircuitState.HALF_OPEN
                self._state.success_count = 0

    def record_success(self) -> None:
        """Record a successful call."""
        with self._state_lock:
            self._state.last_success_time = datetime.now(UTC)

            if self._state.state == CircuitState.HALF_OPEN:
                self._state.success_count += 1

                if self._state.success_count >= self.config.success_threshold:
                    logger.info(f"Circuit {self.name}: HALF_OPEN -> CLOSED (recovered)")
                    self._state.state = CircuitState.CLOSED
                    self._state.failure_count = 0
                    self._state.success_count = 0

            elif self._state.state == CircuitState.CLOSED:
                # Reset failure count on success
                self._state.failure_count = 0

    def record_failure(self, exception: Exception | None = None) -> None:
        """Record a failed call."""
        # Check if exception should be excluded
        if exception and isinstance(exception, self.config.excluded_exceptions):
            logger.debug(f"Circuit {self.name}: Excluded exception {type(exception).__name__}")
            return

        with self._state_lock:
            self._state.last_failure_time = datetime.now(UTC)
            self._state.failure_count += 1

            if self._state.state == CircuitState.HALF_OPEN:
                # Any failure in half-open returns to open
                logger.warning(f"Circuit {self.name}: HALF_OPEN -> OPEN (failure during recovery)")
                self._state.state = CircuitState.OPEN
                self._state.success_count = 0

            elif self._state.state == CircuitState.CLOSED:
                if self._state.failure_count >= self.config.failure_threshold:
                    logger.warning(
                        f"Circuit {self.name}: CLOSED -> OPEN "
                        f"(failures={self._state.failure_count})"
                    )
                    self._state.state = CircuitState.OPEN

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator usage."""

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            return self.call(func, *args, **kwargs)

        return wrapper

    def __enter__(self) -> CircuitBreaker:
        """Context manager entry."""
        if self.is_open:
            raise CircuitBreakerOpen(self.name)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """Context manager exit."""
        if exc_type is None:
            self.record_success()
        else:
            self.record_failure(exc_val)
        return False  # Don't suppress exceptions

    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute function with circuit breaker protection."""
        if self.is_open:
            raise CircuitBreakerOpen(self.name)

        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure(e)
            raise

    def reset(self) -> None:
        """Manually reset the circuit breaker."""
        with self._state_lock:
            self._state = CircuitBreakerState()
            logger.info(f"Circuit {self.name}: Manually reset to CLOSED")

    def get_stats(self) -> dict:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self._state.state.value,
            "failure_count": self._state.failure_count,
            "success_count": self._state.success_count,
            "last_failure": (
                self._state.last_failure_time.isoformat()
                if self._state.last_failure_time
                else None
            ),
            "last_success": (
                self._state.last_success_time.isoformat()
                if self._state.last_success_time
                else None
            ),
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold,
            },
        }


class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open."""

    def __init__(self, circuit_name: str) -> None:
        self.circuit_name = circuit_name
        super().__init__(f"Circuit breaker '{circuit_name}' is open")


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    backoff_base: float = 1.0  # Base delay in seconds
    backoff_factor: float = 2.0  # Exponential factor
    backoff_max: float = 60.0  # Maximum delay
    retryable_exceptions: tuple = (Exception,)
    non_retryable_exceptions: tuple = ()


def with_retry(
    max_attempts: int = 3,
    backoff_base: float = 1.0,
    backoff_factor: float = 2.0,
    backoff_max: float = 60.0,
    retryable_exceptions: tuple = (Exception,),
    non_retryable_exceptions: tuple = (),
    on_retry: Callable[[int, Exception], None] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for retry with exponential backoff.

    Usage:
        @with_retry(max_attempts=3, backoff_base=1.0)
        def call_external_service():
            # May fail and be retried
            pass

    Args:
        max_attempts: Maximum number of attempts (including initial)
        backoff_base: Initial delay in seconds
        backoff_factor: Multiplier for each retry
        backoff_max: Maximum delay cap
        retryable_exceptions: Exceptions that trigger retry
        non_retryable_exceptions: Exceptions that should not be retried
        on_retry: Optional callback on each retry (attempt_number, exception)
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        backoff_base=backoff_base,
        backoff_factor=backoff_factor,
        backoff_max=backoff_max,
        retryable_exceptions=retryable_exceptions,
        non_retryable_exceptions=non_retryable_exceptions,
    )

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None

            for attempt in range(1, config.max_attempts + 1):
                try:
                    return func(*args, **kwargs)

                except config.non_retryable_exceptions as e:
                    # Don't retry these
                    raise

                except config.retryable_exceptions as e:
                    last_exception = e

                    if attempt == config.max_attempts:
                        logger.error(
                            f"Retry exhausted for {func.__name__} "
                            f"after {attempt} attempts: {e}"
                        )
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(
                        config.backoff_base * (config.backoff_factor ** (attempt - 1)),
                        config.backoff_max,
                    )

                    logger.warning(
                        f"Retry {attempt}/{config.max_attempts} for {func.__name__} "
                        f"after {delay:.2f}s: {e}"
                    )

                    if on_retry:
                        on_retry(attempt, e)

                    time.sleep(delay)

            # Should not reach here, but just in case
            raise last_exception  # type: ignore

        return wrapper

    return decorator


def with_timeout(seconds: float) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to add timeout to a function.

    Note: This uses signals and only works in the main thread on Unix.
    For cross-platform support, use concurrent.futures.

    Usage:
        @with_timeout(5.0)
        def slow_operation():
            # Will raise TimeoutError after 5 seconds
            pass
    """
    import signal
    import platform

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Signal-based timeout only works on Unix main thread
            if platform.system() != "Windows":
                try:
                    def timeout_handler(signum, frame):
                        raise TimeoutError(f"{func.__name__} timed out after {seconds}s")

                    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                    signal.setitimer(signal.ITIMER_REAL, seconds)

                    try:
                        return func(*args, **kwargs)
                    finally:
                        signal.setitimer(signal.ITIMER_REAL, 0)
                        signal.signal(signal.SIGALRM, old_handler)

                except ValueError:
                    # Not in main thread, fall through to non-signal version
                    pass

            # Fallback: no timeout enforcement (or use threading)
            return func(*args, **kwargs)

        return wrapper

    return decorator


# Pre-configured circuit breakers for common services
blockchain_circuit = CircuitBreaker(
    "blockchain_rpc",
    failure_threshold=5,
    recovery_timeout=30,
    success_threshold=2,
)

redis_circuit = CircuitBreaker(
    "redis",
    failure_threshold=3,
    recovery_timeout=10,
    success_threshold=1,
)

"""
Resilient cache layer with fallback support.

Provides:
- Redis cache with graceful fallback to local memory
- Circuit breaker protection
- Automatic recovery when Redis comes back
"""

from __future__ import annotations

import functools
import logging
import time
from collections import OrderedDict
from threading import Lock
from typing import Any, Callable, TypeVar

from django.conf import settings
from django.core.cache import cache as django_cache
from django.core.cache.backends.base import DEFAULT_TIMEOUT

from apps.blockchain.resilience import CircuitBreaker, CircuitBreakerOpen

logger = logging.getLogger(__name__)

T = TypeVar("T")


class LRUMemoryCache:
    """
    Simple thread-safe LRU memory cache for fallback.

    Used when Redis is unavailable.
    """

    def __init__(self, max_size: int = 1000, default_timeout: int = 300) -> None:
        """Initialize LRU cache."""
        self.max_size = max_size
        self.default_timeout = default_timeout
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._lock = Lock()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from cache."""
        with self._lock:
            if key not in self._cache:
                return default

            value, expires_at = self._cache[key]

            # Check expiration
            if expires_at is not None and time.time() > expires_at:
                del self._cache[key]
                return default

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return value

    def set(self, key: str, value: Any, timeout: int | None = None) -> None:
        """Set a value in cache."""
        if timeout is None:
            timeout = self.default_timeout

        expires_at = time.time() + timeout if timeout > 0 else None

        with self._lock:
            # Remove oldest entries if at capacity
            while len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)

            self._cache[key] = (value, expires_at)

    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all entries."""
        with self._lock:
            self._cache.clear()

    def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values."""
        result = {}
        for key in keys:
            value = self.get(key)
            if value is not None:
                result[key] = value
        return result

    def set_many(self, mapping: dict[str, Any], timeout: int | None = None) -> None:
        """Set multiple values."""
        for key, value in mapping.items():
            self.set(key, value, timeout)

    def delete_many(self, keys: list[str]) -> None:
        """Delete multiple keys."""
        for key in keys:
            self.delete(key)

    def __len__(self) -> int:
        """Return number of cached items."""
        return len(self._cache)


# Global fallback cache instance
_fallback_cache = LRUMemoryCache(
    max_size=int(getattr(settings, "CACHE_FALLBACK_MAX_SIZE", 1000)),
    default_timeout=int(getattr(settings, "CACHE_FALLBACK_TIMEOUT", 300)),
)

# Circuit breaker for Redis
_redis_circuit = CircuitBreaker(
    "redis_cache",
    failure_threshold=3,
    recovery_timeout=15,
    success_threshold=2,
)


class ResilientCache:
    """
    Cache wrapper with automatic fallback to memory cache.

    Attempts Redis first, falls back to local memory if Redis fails.
    Uses circuit breaker to avoid hammering failed Redis.

    Usage:
        from apps.core.cache import resilient_cache

        # Same interface as Django cache
        resilient_cache.set("key", value, timeout=300)
        value = resilient_cache.get("key")
    """

    def __init__(
        self,
        primary_cache=None,
        fallback_cache: LRUMemoryCache | None = None,
        circuit: CircuitBreaker | None = None,
    ) -> None:
        """Initialize resilient cache."""
        self._primary = primary_cache if primary_cache is not None else django_cache
        self._fallback = fallback_cache if fallback_cache is not None else _fallback_cache
        self._circuit = circuit if circuit is not None else _redis_circuit
        self._using_fallback = False

    @property
    def is_using_fallback(self) -> bool:
        """Check if currently using fallback cache."""
        return self._using_fallback or self._circuit.is_open

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from cache with fallback."""
        # Try primary (Redis) if circuit is closed
        if not self._circuit.is_open:
            try:
                with self._circuit:
                    value = self._primary.get(key, default)
                    self._using_fallback = False
                    return value
            except CircuitBreakerOpen:
                pass
            except Exception as e:
                logger.warning(f"Redis get failed, using fallback: {e}")

        # Fallback to memory
        self._using_fallback = True
        return self._fallback.get(key, default)

    def set(
        self,
        key: str,
        value: Any,
        timeout: int | None = DEFAULT_TIMEOUT,
    ) -> bool:
        """Set a value in cache with fallback."""
        success = False

        # Normalize timeout for fallback (DEFAULT_TIMEOUT is a sentinel)
        fallback_timeout = timeout if isinstance(timeout, int) else 300

        # Try primary (Redis) if circuit is closed
        if not self._circuit.is_open:
            try:
                with self._circuit:
                    self._primary.set(key, value, timeout)
                    self._using_fallback = False
                    success = True
            except CircuitBreakerOpen:
                pass
            except Exception as e:
                logger.warning(f"Redis set failed, using fallback: {e}")

        # Always set in fallback as backup
        try:
            self._fallback.set(key, value, fallback_timeout)
            if not success:
                self._using_fallback = True
            return True
        except Exception as e:
            logger.error(f"Fallback cache set failed: {e}")
            return success

    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        redis_success = False
        fallback_success = False

        # Try primary
        if not self._circuit.is_open:
            try:
                with self._circuit:
                    self._primary.delete(key)
                    redis_success = True
            except Exception as e:
                logger.warning(f"Redis delete failed: {e}")

        # Always delete from fallback too
        fallback_success = self._fallback.delete(key)

        return redis_success or fallback_success

    def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values from cache."""
        if not self._circuit.is_open:
            try:
                with self._circuit:
                    return self._primary.get_many(keys)
            except Exception as e:
                logger.warning(f"Redis get_many failed, using fallback: {e}")

        return self._fallback.get_many(keys)

    def set_many(
        self,
        mapping: dict[str, Any],
        timeout: int | None = DEFAULT_TIMEOUT,
    ) -> list[str]:
        """Set multiple values in cache."""
        failed_keys = []

        # Try primary
        if not self._circuit.is_open:
            try:
                with self._circuit:
                    failed_keys = self._primary.set_many(mapping, timeout)
            except Exception as e:
                logger.warning(f"Redis set_many failed: {e}")
                failed_keys = list(mapping.keys())

        # Set in fallback
        self._fallback.set_many(mapping, timeout if isinstance(timeout, int) else 300)

        return failed_keys

    def delete_many(self, keys: list[str]) -> None:
        """Delete multiple keys from cache."""
        # Try primary
        if not self._circuit.is_open:
            try:
                with self._circuit:
                    self._primary.delete_many(keys)
            except Exception as e:
                logger.warning(f"Redis delete_many failed: {e}")

        # Always delete from fallback
        self._fallback.delete_many(keys)

    def clear(self) -> None:
        """Clear all entries from cache."""
        if not self._circuit.is_open:
            try:
                with self._circuit:
                    self._primary.clear()
            except Exception as e:
                logger.warning(f"Redis clear failed: {e}")

        self._fallback.clear()

    def get_or_set(
        self,
        key: str,
        default: Callable[[], T] | T,
        timeout: int | None = DEFAULT_TIMEOUT,
    ) -> T:
        """Get from cache or set default if not present."""
        value = self.get(key)
        if value is None:
            if callable(default):
                value = default()
            else:
                value = default
            self.set(key, value, timeout)
        return value

    def get_stats(self) -> dict:
        """Get cache statistics."""
        return {
            "using_fallback": self.is_using_fallback,
            "circuit_state": self._circuit.state.value,
            "fallback_size": len(self._fallback),
            "circuit_stats": self._circuit.get_stats(),
        }


# Global resilient cache instance
resilient_cache = ResilientCache()


def cached(
    key_prefix: str,
    timeout: int = 300,
    key_func: Callable[..., str] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for caching function results with fallback.

    Usage:
        @cached("user_profile", timeout=600)
        def get_user_profile(user_id: int) -> dict:
            # Expensive operation
            return {"id": user_id, ...}

        # With custom key function
        @cached("model", timeout=3600, key_func=lambda m: f"{m.id}:{m.version}")
        def load_model(model: Model) -> Any:
            pass
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Build cache key
            if key_func:
                key_suffix = key_func(*args, **kwargs)
            else:
                # Default: use all args as key
                key_parts = [str(a) for a in args]
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                key_suffix = ":".join(key_parts) if key_parts else "default"

            cache_key = f"{key_prefix}:{key_suffix}"

            # Try to get from cache
            cached_value = resilient_cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Compute and cache
            result = func(*args, **kwargs)
            resilient_cache.set(cache_key, result, timeout)
            return result

        # Add cache control methods
        wrapper.invalidate = lambda *args, **kwargs: resilient_cache.delete(
            f"{key_prefix}:{key_func(*args, **kwargs) if key_func else ':'.join(str(a) for a in args)}"
        )

        return wrapper

    return decorator

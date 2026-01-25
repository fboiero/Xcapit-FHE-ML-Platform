"""
Tests for resilience patterns: circuit breaker, retry, and cache fallback.
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from apps.blockchain.resilience import (
    CircuitBreaker,
    CircuitBreakerOpen,
    CircuitState,
    with_retry,
)
from apps.core.cache import LRUMemoryCache, ResilientCache


class TestCircuitBreaker:
    """Tests for circuit breaker pattern."""

    def test_initial_state_is_closed(self):
        """Circuit should start in closed state."""
        circuit = CircuitBreaker("test_closed", failure_threshold=5)
        circuit.reset()  # Ensure clean state

        assert circuit.state == CircuitState.CLOSED
        assert circuit.is_closed is True
        assert circuit.is_open is False

    def test_opens_after_threshold_failures(self):
        """Circuit should open after reaching failure threshold."""
        circuit = CircuitBreaker("test_open", failure_threshold=3)
        circuit.reset()

        # Record failures up to threshold
        for i in range(3):
            circuit.record_failure(Exception(f"Failure {i}"))

        assert circuit.state == CircuitState.OPEN
        assert circuit.is_open is True

    def test_rejects_calls_when_open(self):
        """Circuit should reject calls when open."""
        circuit = CircuitBreaker("test_reject", failure_threshold=1)
        circuit.reset()

        circuit.record_failure(Exception("Trigger open"))

        with pytest.raises(CircuitBreakerOpen) as exc_info:
            with circuit:
                pass

        assert "test_reject" in str(exc_info.value)

    def test_transitions_to_half_open_after_timeout(self):
        """Circuit should transition to half-open after recovery timeout."""
        circuit = CircuitBreaker(
            "test_half_open",
            failure_threshold=1,
            recovery_timeout=1,  # 1 second
        )
        circuit.reset()

        circuit.record_failure(Exception("Trigger open"))
        assert circuit.state == CircuitState.OPEN

        # Wait for recovery timeout
        time.sleep(1.5)

        # Accessing is_open should trigger check
        _ = circuit.is_open
        assert circuit.state == CircuitState.HALF_OPEN

    def test_closes_after_success_in_half_open(self):
        """Circuit should close after successes in half-open state."""
        circuit = CircuitBreaker(
            "test_close",
            failure_threshold=1,
            recovery_timeout=0,  # Immediate
            success_threshold=2,
        )
        circuit.reset()

        # Open the circuit
        circuit.record_failure(Exception("Open"))

        # Force half-open
        circuit._state.state = CircuitState.HALF_OPEN
        circuit._state.success_count = 0

        # Record successes
        circuit.record_success()
        assert circuit.state == CircuitState.HALF_OPEN  # Not yet

        circuit.record_success()
        assert circuit.state == CircuitState.CLOSED  # Now closed

    def test_reopens_on_failure_in_half_open(self):
        """Circuit should reopen on failure during half-open."""
        circuit = CircuitBreaker("test_reopen", failure_threshold=1)
        circuit.reset()

        # Open and force half-open
        circuit.record_failure(Exception("Open"))
        circuit._state.state = CircuitState.HALF_OPEN

        # Failure in half-open
        circuit.record_failure(Exception("Reopen"))

        assert circuit.state == CircuitState.OPEN

    def test_success_resets_failure_count(self):
        """Success in closed state should reset failure count."""
        circuit = CircuitBreaker("test_reset", failure_threshold=3)
        circuit.reset()

        # Record some failures
        circuit.record_failure(Exception("1"))
        circuit.record_failure(Exception("2"))
        assert circuit._state.failure_count == 2

        # Success resets
        circuit.record_success()
        assert circuit._state.failure_count == 0

    def test_decorator_usage(self):
        """Test circuit breaker as decorator."""
        circuit = CircuitBreaker("test_decorator", failure_threshold=2)
        circuit.reset()

        call_count = 0

        @circuit
        def risky_function(should_fail=False):
            nonlocal call_count
            call_count += 1
            if should_fail:
                raise ValueError("Failed")
            return "success"

        # Successful calls
        assert risky_function() == "success"
        assert risky_function() == "success"

        # Failures
        with pytest.raises(ValueError):
            risky_function(should_fail=True)
        with pytest.raises(ValueError):
            risky_function(should_fail=True)

        # Circuit is now open
        with pytest.raises(CircuitBreakerOpen):
            risky_function()

    def test_excluded_exceptions(self):
        """Excluded exceptions should not count as failures."""
        circuit = CircuitBreaker(
            "test_excluded",
            failure_threshold=2,
            excluded_exceptions=(ValueError,),
        )
        circuit.reset()

        # ValueErrors should be excluded
        circuit.record_failure(ValueError("Excluded"))
        circuit.record_failure(ValueError("Excluded"))
        circuit.record_failure(ValueError("Excluded"))

        assert circuit.state == CircuitState.CLOSED  # Still closed

        # Other exceptions should count
        circuit.record_failure(TypeError("Counted"))
        circuit.record_failure(TypeError("Counted"))

        assert circuit.state == CircuitState.OPEN

    def test_get_stats(self):
        """Test getting circuit statistics."""
        circuit = CircuitBreaker("test_stats", failure_threshold=5)
        circuit.reset()

        circuit.record_success()
        circuit.record_failure(Exception("Test"))

        stats = circuit.get_stats()

        assert stats["name"] == "test_stats"
        assert stats["state"] == "closed"
        assert stats["failure_count"] == 1
        assert "config" in stats


class TestRetryDecorator:
    """Tests for retry with backoff decorator."""

    def test_succeeds_on_first_try(self):
        """Function should succeed without retry if no error."""
        call_count = 0

        @with_retry(max_attempts=3)
        def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = success_func()

        assert result == "success"
        assert call_count == 1

    def test_retries_on_failure(self):
        """Function should retry on retryable exception."""
        call_count = 0

        @with_retry(max_attempts=3, backoff_base=0.01)
        def fail_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Transient failure")
            return "success"

        result = fail_twice()

        assert result == "success"
        assert call_count == 3

    def test_exhausts_retries(self):
        """Should raise after exhausting retries."""
        call_count = 0

        @with_retry(max_attempts=3, backoff_base=0.01)
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Permanent failure")

        with pytest.raises(ConnectionError):
            always_fail()

        assert call_count == 3

    def test_non_retryable_exception(self):
        """Non-retryable exceptions should not be retried."""
        call_count = 0

        @with_retry(
            max_attempts=3,
            backoff_base=0.01,
            retryable_exceptions=(ConnectionError,),
            non_retryable_exceptions=(ValueError,),
        )
        def raise_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Not retryable")

        with pytest.raises(ValueError):
            raise_value_error()

        assert call_count == 1  # No retries

    def test_retry_callback(self):
        """Retry callback should be called on each retry."""
        retries = []

        def on_retry(attempt, exc):
            retries.append((attempt, str(exc)))

        @with_retry(max_attempts=3, backoff_base=0.01, on_retry=on_retry)
        def fail_twice():
            if len(retries) < 2:
                raise ConnectionError("Transient")
            return "ok"

        result = fail_twice()

        assert result == "ok"
        assert len(retries) == 2


class TestLRUMemoryCache:
    """Tests for LRU memory cache."""

    def test_set_and_get(self):
        """Basic set and get operations."""
        cache = LRUMemoryCache(max_size=100)

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_default_value(self):
        """Get should return default for missing keys."""
        cache = LRUMemoryCache()

        assert cache.get("missing") is None
        assert cache.get("missing", "default") == "default"

    def test_expiration(self):
        """Values should expire after timeout."""
        cache = LRUMemoryCache(default_timeout=1)

        cache.set("expires", "value", timeout=1)
        assert cache.get("expires") == "value"

        time.sleep(1.5)
        assert cache.get("expires") is None

    def test_lru_eviction(self):
        """Oldest entries should be evicted when at capacity."""
        cache = LRUMemoryCache(max_size=3)

        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)

        # Access 'a' to make it recently used
        cache.get("a")

        # Add new item, should evict 'b' (oldest)
        cache.set("d", 4)

        assert cache.get("a") == 1  # Still there
        assert cache.get("b") is None  # Evicted
        assert cache.get("c") == 3
        assert cache.get("d") == 4

    def test_delete(self):
        """Delete should remove key."""
        cache = LRUMemoryCache()

        cache.set("key", "value")
        assert cache.delete("key") is True
        assert cache.get("key") is None
        assert cache.delete("key") is False

    def test_get_many(self):
        """Get multiple keys at once."""
        cache = LRUMemoryCache()

        cache.set("a", 1)
        cache.set("b", 2)

        result = cache.get_many(["a", "b", "c"])

        assert result == {"a": 1, "b": 2}

    def test_set_many(self):
        """Set multiple keys at once."""
        cache = LRUMemoryCache()

        cache.set_many({"a": 1, "b": 2, "c": 3})

        assert cache.get("a") == 1
        assert cache.get("b") == 2
        assert cache.get("c") == 3


class TestResilientCache:
    """Tests for resilient cache with fallback."""

    def test_uses_primary_when_available(self):
        """Should use primary cache when available."""
        primary = MagicMock()
        primary.get.return_value = "from_primary"

        fallback = LRUMemoryCache()
        circuit = CircuitBreaker("test_primary", failure_threshold=5)
        circuit.reset()

        cache = ResilientCache(
            primary_cache=primary,
            fallback_cache=fallback,
            circuit=circuit,
        )

        result = cache.get("key")

        assert result == "from_primary"
        assert cache.is_using_fallback is False
        primary.get.assert_called_once()

    def test_falls_back_on_primary_failure(self):
        """Should fall back to memory cache when primary fails."""
        primary = MagicMock()
        primary.get.side_effect = ConnectionError("Redis down")

        fallback = LRUMemoryCache()
        fallback.set("key", "from_fallback")

        circuit = CircuitBreaker("test_fallback", failure_threshold=1)
        circuit.reset()

        cache = ResilientCache(
            primary_cache=primary,
            fallback_cache=fallback,
            circuit=circuit,
        )

        result = cache.get("key")

        assert result == "from_fallback"
        assert cache.is_using_fallback is True

    def test_set_writes_to_fallback(self):
        """Set should always write to fallback as backup."""
        primary = MagicMock()
        fallback = LRUMemoryCache()
        circuit = CircuitBreaker("test_set", failure_threshold=5)
        circuit.reset()

        cache = ResilientCache(
            primary_cache=primary,
            fallback_cache=fallback,
            circuit=circuit,
        )

        cache.set("key", "value")

        # Should be in both
        primary.set.assert_called_once()
        assert fallback.get("key") == "value"

    def test_get_stats(self):
        """Should return cache statistics."""
        cache = ResilientCache()

        stats = cache.get_stats()

        assert "using_fallback" in stats
        assert "circuit_state" in stats
        assert "fallback_size" in stats

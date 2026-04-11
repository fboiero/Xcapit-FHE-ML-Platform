"""
Enhanced health checks for Xcapit FHE-ML Platform.

Provides detailed health check endpoints for:
- Database connectivity
- Redis cache connectivity
- Blockchain RPC connectivity
- Overall system status
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.views import View

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health check status values."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    """Health status of a single component."""

    name: str
    status: HealthStatus
    latency_ms: float | None = None
    message: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "name": self.name,
            "status": self.status.value,
        }
        if self.latency_ms is not None:
            result["latency_ms"] = round(self.latency_ms, 2)
        if self.message:
            result["message"] = self.message
        if self.details:
            result["details"] = self.details
        return result


class HealthChecker:
    """
    Health check executor for all system components.

    Runs health checks in sequence and aggregates results.
    """

    def __init__(self) -> None:
        """Initialize health checker."""
        self.checks = [
            self._check_database,
            self._check_redis,
            self._check_blockchain_rpc,
        ]

    def run_all_checks(self) -> tuple[HealthStatus, list[ComponentHealth]]:
        """
        Run all health checks and return aggregate status.

        Returns:
            Tuple of (overall_status, list of component health results)
        """
        results = []
        overall_status = HealthStatus.HEALTHY

        for check in self.checks:
            try:
                result = check()
                results.append(result)

                # Update overall status based on component status
                if result.status == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
                elif result.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED

            except Exception as e:
                logger.exception(f"Health check failed: {check.__name__}")
                results.append(
                    ComponentHealth(
                        name=check.__name__.replace("_check_", ""),
                        status=HealthStatus.UNHEALTHY,
                        message=str(e),
                    )
                )
                overall_status = HealthStatus.UNHEALTHY

        return overall_status, results

    def _check_database(self) -> ComponentHealth:
        """Check database connectivity and latency."""
        start = time.perf_counter()

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()

            latency = (time.perf_counter() - start) * 1000

            # Check latency thresholds
            if latency > 1000:  # > 1 second
                return ComponentHealth(
                    name="database",
                    status=HealthStatus.DEGRADED,
                    latency_ms=latency,
                    message="High latency detected",
                )

            return ComponentHealth(
                name="database",
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                details={
                    "engine": settings.DATABASES["default"]["ENGINE"].split(".")[-1],
                },
            )

        except Exception as e:
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                latency_ms=(time.perf_counter() - start) * 1000,
                message=f"Connection failed: {str(e)[:100]}",
            )

    def _check_redis(self) -> ComponentHealth:
        """Check Redis cache connectivity and latency."""
        start = time.perf_counter()

        try:
            # Test set/get operation
            test_key = "health_check_test"
            test_value = "test_value"

            cache.set(test_key, test_value, timeout=10)
            retrieved = cache.get(test_key)
            cache.delete(test_key)

            latency = (time.perf_counter() - start) * 1000

            if retrieved != test_value:
                return ComponentHealth(
                    name="redis",
                    status=HealthStatus.DEGRADED,
                    latency_ms=latency,
                    message="Cache read/write mismatch",
                )

            # Check latency thresholds
            if latency > 100:  # > 100ms
                return ComponentHealth(
                    name="redis",
                    status=HealthStatus.DEGRADED,
                    latency_ms=latency,
                    message="High latency detected",
                )

            return ComponentHealth(
                name="redis",
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
            )

        except Exception as e:
            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                latency_ms=(time.perf_counter() - start) * 1000,
                message=f"Connection failed: {str(e)[:100]}",
            )

    def _check_blockchain_rpc(self) -> ComponentHealth:
        """Check blockchain RPC connectivity."""
        start = time.perf_counter()

        try:
            # Import here to avoid circular imports
            from web3 import Web3

            rpc_url = settings.BLOCKCHAIN_CONFIG.get("rpc_url")
            if not rpc_url:
                return ComponentHealth(
                    name="blockchain",
                    status=HealthStatus.DEGRADED,
                    message="RPC URL not configured",
                )

            # Connect and get block number
            w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 5}))

            if not w3.is_connected():
                return ComponentHealth(
                    name="blockchain",
                    status=HealthStatus.UNHEALTHY,
                    latency_ms=(time.perf_counter() - start) * 1000,
                    message="Cannot connect to RPC",
                )

            block_number = w3.eth.block_number
            latency = (time.perf_counter() - start) * 1000

            # Check latency thresholds
            if latency > 5000:  # > 5 seconds
                return ComponentHealth(
                    name="blockchain",
                    status=HealthStatus.DEGRADED,
                    latency_ms=latency,
                    message="High latency detected",
                    details={
                        "network": settings.BLOCKCHAIN_CONFIG.get("network"),
                        "block_number": block_number,
                    },
                )

            return ComponentHealth(
                name="blockchain",
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                details={
                    "network": settings.BLOCKCHAIN_CONFIG.get("network"),
                    "chain_id": settings.BLOCKCHAIN_CONFIG.get("chain_id"),
                    "block_number": block_number,
                },
            )

        except ImportError:
            return ComponentHealth(
                name="blockchain",
                status=HealthStatus.DEGRADED,
                message="web3 not installed",
            )
        except Exception as e:
            return ComponentHealth(
                name="blockchain",
                status=HealthStatus.DEGRADED,  # Degraded, not unhealthy - blockchain is optional
                latency_ms=(time.perf_counter() - start) * 1000,
                message=f"RPC error: {str(e)[:100]}",
            )


class HealthCheckView(View):
    """
    Enhanced health check endpoint.

    Returns detailed health status of all system components.

    Response format:
    {
        "status": "healthy|degraded|unhealthy",
        "timestamp": "2024-01-15T10:30:00Z",
        "version": "2.0.0",
        "components": [
            {"name": "database", "status": "healthy", "latency_ms": 1.5},
            {"name": "redis", "status": "healthy", "latency_ms": 0.8},
            {"name": "blockchain", "status": "healthy", "latency_ms": 150.2}
        ]
    }
    """

    def get(self, request) -> JsonResponse:
        """Handle GET request for health check."""
        checker = HealthChecker()
        overall_status, components = checker.run_all_checks()

        response_data = {
            "status": overall_status.value,
            "timestamp": datetime.now(UTC).isoformat(),
            "version": getattr(settings, "SPECTACULAR_SETTINGS", {}).get("VERSION", "2.0.0"),
            "environment": "production" if not settings.DEBUG else "development",
            "components": [c.to_dict() for c in components],
        }

        # Set status code based on health
        if overall_status == HealthStatus.HEALTHY:
            status_code = 200
        elif overall_status == HealthStatus.DEGRADED:
            status_code = 200  # Still 200 for degraded (service is up)
        else:
            status_code = 503  # Service unavailable

        return JsonResponse(response_data, status=status_code)


class LivenessCheckView(View):
    """
    Simple liveness check for Kubernetes.

    Returns 200 if the process is alive, regardless of dependencies.
    """

    def get(self, request) -> JsonResponse:
        """Handle GET request for liveness check."""
        return JsonResponse({"status": "alive"}, status=200)


class ReadinessCheckView(View):
    """
    Readiness check for Kubernetes.

    Returns 200 only if the service is ready to accept traffic
    (database and cache are available).
    """

    def get(self, request) -> JsonResponse:
        """Handle GET request for readiness check."""
        checker = HealthChecker()

        # Only check critical components
        db_health = checker._check_database()
        redis_health = checker._check_redis()

        if (
            db_health.status == HealthStatus.UNHEALTHY
            or redis_health.status == HealthStatus.UNHEALTHY
        ):
            return JsonResponse(
                {
                    "status": "not_ready",
                    "database": db_health.status.value,
                    "redis": redis_health.status.value,
                },
                status=503,
            )

        return JsonResponse({"status": "ready"}, status=200)

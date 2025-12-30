"""
Tests for correlation ID middleware and request logging.
"""

import json
import uuid

import pytest
from django.test import RequestFactory

from apps.core.logging import (
    CorrelationIdFilter,
    get_correlation_id,
    set_correlation_id,
    clear_correlation_id,
    get_request_context,
    set_request_context,
    clear_request_context,
    PerformanceLogger,
    get_logger,
)
from apps.core.middleware.correlation import CorrelationIdMiddleware, RESPONSE_HEADER
from apps.core.middleware.request_logging import RequestLoggingMiddleware


class TestCorrelationIdContext:
    """Tests for correlation ID context management."""

    def test_set_and_get_correlation_id(self):
        """Test setting and getting correlation ID."""
        clear_correlation_id()

        # Initially None
        assert get_correlation_id() is None

        # Set explicit ID
        test_id = "test-correlation-123"
        result = set_correlation_id(test_id)

        assert result == test_id
        assert get_correlation_id() == test_id

        # Cleanup
        clear_correlation_id()
        assert get_correlation_id() is None

    def test_auto_generate_correlation_id(self):
        """Test auto-generating correlation ID when none provided."""
        clear_correlation_id()

        result = set_correlation_id()

        assert result is not None
        assert get_correlation_id() == result
        # Should be a valid UUID
        uuid.UUID(result)

        clear_correlation_id()

    def test_request_context(self):
        """Test request context management."""
        clear_request_context()

        assert get_request_context() == {}

        context = {"user_id": "123", "path": "/api/test"}
        set_request_context(context)

        assert get_request_context() == context

        clear_request_context()
        assert get_request_context() == {}


class TestCorrelationIdFilter:
    """Tests for the logging filter."""

    def test_filter_adds_correlation_id(self):
        """Test that filter adds correlation_id to log records."""
        import logging

        set_correlation_id("test-123")
        set_request_context({"user_id": "user-456", "path": "/api/test"})

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        filter_obj = CorrelationIdFilter()
        result = filter_obj.filter(record)

        assert result is True
        assert record.correlation_id == "test-123"
        assert record.user_id == "user-456"
        assert record.path == "/api/test"

        clear_correlation_id()
        clear_request_context()

    def test_filter_uses_placeholder_when_no_id(self):
        """Test that filter uses placeholder when no correlation ID."""
        import logging

        clear_correlation_id()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        filter_obj = CorrelationIdFilter()
        filter_obj.filter(record)

        assert record.correlation_id == "-"


@pytest.mark.django_db
class TestCorrelationIdMiddleware:
    """Tests for the correlation ID middleware."""

    def test_generates_correlation_id(self):
        """Test that middleware generates correlation ID when not provided."""
        factory = RequestFactory()
        request = factory.get("/api/test")

        def get_response(request):
            from django.http import HttpResponse
            return HttpResponse("OK")

        middleware = CorrelationIdMiddleware(get_response)
        response = middleware(request)

        # Should have correlation ID in response header
        assert RESPONSE_HEADER in response
        # Should be a valid UUID
        uuid.UUID(response[RESPONSE_HEADER])

    def test_propagates_existing_correlation_id(self):
        """Test that middleware propagates existing correlation ID."""
        factory = RequestFactory()
        existing_id = "existing-correlation-id-123"
        request = factory.get("/api/test", HTTP_X_CORRELATION_ID=existing_id)

        def get_response(request):
            from django.http import HttpResponse
            return HttpResponse("OK")

        middleware = CorrelationIdMiddleware(get_response)
        response = middleware(request)

        assert response[RESPONSE_HEADER] == existing_id

    def test_propagates_request_id_header(self):
        """Test that middleware accepts X-Request-ID header."""
        factory = RequestFactory()
        request_id = "request-id-456"
        request = factory.get("/api/test", HTTP_X_REQUEST_ID=request_id)

        def get_response(request):
            from django.http import HttpResponse
            return HttpResponse("OK")

        middleware = CorrelationIdMiddleware(get_response)
        response = middleware(request)

        assert response[RESPONSE_HEADER] == request_id

    def test_stores_correlation_id_on_request(self):
        """Test that correlation ID is stored on request object."""
        factory = RequestFactory()
        request = factory.get("/api/test")
        stored_id = None

        def get_response(req):
            nonlocal stored_id
            stored_id = req.correlation_id
            from django.http import HttpResponse
            return HttpResponse("OK")

        middleware = CorrelationIdMiddleware(get_response)
        response = middleware(request)

        assert stored_id is not None
        assert stored_id == response[RESPONSE_HEADER]


class TestPerformanceLogger:
    """Tests for performance logging context manager."""

    def test_logs_successful_operation(self, caplog):
        """Test logging of successful operation."""
        import logging

        logger = get_logger("test.perf")

        with caplog.at_level(logging.INFO):
            with PerformanceLogger("test_operation", logger) as perf:
                perf.add_metadata(items=10)

        assert "Operation completed: test_operation" in caplog.text

    def test_logs_failed_operation(self, caplog):
        """Test logging of failed operation."""
        import logging

        logger = get_logger("test.perf")

        with caplog.at_level(logging.ERROR):
            try:
                with PerformanceLogger("failing_operation", logger):
                    raise ValueError("Test error")
            except ValueError:
                pass

        assert "Operation failed: failing_operation" in caplog.text


@pytest.mark.django_db
class TestHealthCheckEndpoints:
    """Tests for health check endpoints."""

    def test_health_endpoint(self, api_client):
        """Test main health endpoint."""
        response = api_client.get("/health/")

        assert response.status_code in [200, 503]
        data = response.json()

        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "timestamp" in data
        assert "components" in data
        assert isinstance(data["components"], list)

    def test_liveness_endpoint(self, api_client):
        """Test liveness endpoint."""
        response = api_client.get("/health/live/")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "alive"

    def test_readiness_endpoint(self, api_client):
        """Test readiness endpoint."""
        response = api_client.get("/health/ready/")

        # May be 200 or 503 depending on DB/Redis availability
        assert response.status_code in [200, 503]
        data = response.json()

        assert "status" in data


@pytest.mark.django_db
class TestRequestLoggingMiddleware:
    """Tests for request logging middleware."""

    def test_logs_request(self, caplog, api_client):
        """Test that requests are logged."""
        import logging

        with caplog.at_level(logging.INFO, logger="apps.api.requests"):
            response = api_client.get("/api/v2/auth/token/")

        # Should have logged the request (even if it's a 401/405)
        assert any("api/v2/auth/token" in record.message for record in caplog.records)

    def test_excludes_health_check_from_logging(self, caplog, api_client):
        """Test that health check requests are not logged."""
        import logging

        with caplog.at_level(logging.INFO, logger="apps.api.requests"):
            api_client.get("/health/")

        # Should not log health check
        request_logs = [r for r in caplog.records if "apps.api.requests" in r.name]
        health_logs = [r for r in request_logs if "/health/" in r.message]
        assert len(health_logs) == 0

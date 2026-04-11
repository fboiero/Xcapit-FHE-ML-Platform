"""
Tests targeting modules with <85% coverage to reach 95%+ overall.

Covers: exceptions, logging, healthchecks, authentication, signals,
blockchain/secrets, blockchain/services, models/models, serializers,
data_quality/views, explainability/views.
"""

import logging
import sys
import time
from datetime import timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.test import RequestFactory, override_settings
from django.utils import timezone
from rest_framework.exceptions import (
    AuthenticationFailed,
    NotAuthenticated,
    Throttled,
    ValidationError,
)
from rest_framework.test import APIClient

from apps.core.models import APIKey, Company

User = get_user_model()


# =============================================================================
# core/exceptions.py
# =============================================================================


class TestCustomExceptionHandler:
    """Tests for custom_exception_handler and helpers."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.factory = RequestFactory()
        request = self.factory.get("/")
        request.user = Mock(is_authenticated=False)
        self.context = {"request": request, "view": Mock()}

    def test_validation_error_handled(self):
        from apps.core.exceptions import custom_exception_handler

        exc = ValidationError({"field": ["Required."]})
        response = custom_exception_handler(exc, self.context)
        assert response.status_code == 400
        assert "details" in response.data["error"]
        assert response["X-Content-Type-Options"] == "nosniff"

    def test_throttled_includes_retry_after(self):
        from apps.core.exceptions import custom_exception_handler

        exc = Throttled(wait=30)
        response = custom_exception_handler(exc, self.context)
        assert response.status_code == 429
        assert response.data["error"]["retry_after"] == 30

    def test_unhandled_exception_returns_500(self):
        from apps.core.exceptions import custom_exception_handler

        response = custom_exception_handler(RuntimeError("boom"), self.context)
        assert response.status_code == 500
        assert response.data["error"]["code"] == "internal_error"

    def test_unhandled_exception_no_view(self):
        from apps.core.exceptions import custom_exception_handler

        request = self.factory.get("/")
        request.user = Mock(is_authenticated=False)
        context = {"request": request, "view": None}
        response = custom_exception_handler(RuntimeError("boom"), context)
        assert response.status_code == 500

    def test_format_error_response_list_detail(self):
        from apps.core.exceptions import _get_error_message

        exc = Mock()
        exc.detail = ["Error one", "Error two"]
        assert _get_error_message(exc) == "Error one"

    def test_format_error_response_empty_list(self):
        from apps.core.exceptions import _get_error_message

        exc = Mock()
        exc.detail = []
        assert _get_error_message(exc) == "An error occurred."

    def test_format_error_response_dict_detail(self):
        from apps.core.exceptions import _get_error_message

        exc = Mock()
        exc.detail = {"field": "error"}
        assert "Validation error" in _get_error_message(exc)

    def test_format_error_response_no_detail(self):
        from apps.core.exceptions import _get_error_message

        assert _get_error_message(RuntimeError("oops")) == "oops"

    def test_get_error_code_no_default_code(self):
        from apps.core.exceptions import _get_error_code

        exc = Mock(spec=[])
        assert _get_error_code(exc) == "error"

    def test_sanitize_validation_errors_list(self):
        from apps.core.exceptions import _sanitize_validation_errors

        result = _sanitize_validation_errors(["err1", "err2"])
        assert result == ["err1", "err2"]

    def test_sanitize_validation_errors_single(self):
        from apps.core.exceptions import _sanitize_validation_errors

        result = _sanitize_validation_errors("single error")
        assert result == {"non_field_errors": ["single error"]}

    def test_sanitize_validation_errors_dict(self):
        from apps.core.exceptions import _sanitize_validation_errors

        result = _sanitize_validation_errors({"field": ["err1"]})
        assert result == {"field": ["err1"]}

    def test_sanitize_validation_errors_dict_single_value(self):
        from apps.core.exceptions import _sanitize_validation_errors

        result = _sanitize_validation_errors({"field": "single"})
        assert result == {"field": ["single"]}

    def test_log_exception_client_error(self):
        from apps.core.exceptions import _log_exception

        _log_exception(NotAuthenticated(), Mock(), Mock())

    def test_log_exception_throttled(self):
        from apps.core.exceptions import _log_exception

        request = Mock()
        request.META = {"HTTP_X_FORWARDED_FOR": "1.2.3.4"}
        _log_exception(Throttled(), request, Mock())

    def test_log_exception_permission_denied(self):
        from apps.core.exceptions import _log_exception

        request = Mock()
        request.user = Mock(is_authenticated=True)
        _log_exception(PermissionDenied(), request, Mock())

    def test_log_exception_permission_denied_anonymous(self):
        from apps.core.exceptions import _log_exception

        request = Mock()
        request.user = Mock(is_authenticated=False)
        _log_exception(PermissionDenied(), request, Mock())

    def test_get_client_ip_no_request(self):
        from apps.core.exceptions import _get_client_ip

        assert _get_client_ip(None) == "unknown"

    def test_get_client_ip_forwarded(self):
        from apps.core.exceptions import _get_client_ip

        request = Mock()
        request.META = {"HTTP_X_FORWARDED_FOR": "1.2.3.4, 5.6.7.8"}
        assert _get_client_ip(request) == "1.2.3.4"

    def test_get_client_ip_remote_addr(self):
        from apps.core.exceptions import _get_client_ip

        request = Mock()
        request.META = {"REMOTE_ADDR": "10.0.0.1"}
        assert _get_client_ip(request) == "10.0.0.1"

    def test_custom_exception_classes(self):
        from apps.core.exceptions import (
            ConflictError,
            InsufficientPermissions,
            RateLimitExceeded,
            ResourceNotFound,
            ServiceUnavailable,
        )

        assert ServiceUnavailable.status_code == 503
        assert ConflictError.status_code == 409
        assert RateLimitExceeded.status_code == 429
        assert InsufficientPermissions.status_code == 403
        assert ResourceNotFound.status_code == 404


# =============================================================================
# core/logging.py
# =============================================================================


class TestLogging:
    """Tests for structured logging module."""

    def test_custom_json_formatter_init(self):
        from apps.core.logging import CustomJsonFormatter

        fmt = CustomJsonFormatter(service_name="test-svc", environment="test")
        assert fmt.service_name == "test-svc"
        assert fmt.environment == "test"

    def test_custom_json_formatter_add_fields_with_request(self):
        from apps.core.logging import CustomJsonFormatter

        fmt = CustomJsonFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="test message", args=(), exc_info=None,
        )
        record.correlation_id = "test-123"
        record.user_id = "u1"
        record.company_id = "c1"
        record.path = "/api/test"
        record.method = "GET"

        log_record = {}
        fmt.add_fields(log_record, record, {})

        assert log_record["service"] == "xcapit-fheml"
        assert log_record["correlation_id"] == "test-123"
        assert "request" in log_record
        assert log_record["request"]["path"] == "/api/test"

    def test_custom_json_formatter_with_exception(self):
        from apps.core.logging import CustomJsonFormatter

        fmt = CustomJsonFormatter()
        try:
            raise ValueError("test error")
        except ValueError:
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="", lineno=0,
            msg="error", args=(), exc_info=exc_info,
        )
        record.correlation_id = "-"
        record.user_id = "-"
        record.company_id = "-"
        record.path = "-"

        log_record = {}
        fmt.add_fields(log_record, record, {})
        assert log_record["exception"]["type"] == "ValueError"
        assert log_record["exception"]["message"] == "test error"

    def test_custom_json_formatter_no_path(self):
        from apps.core.logging import CustomJsonFormatter

        fmt = CustomJsonFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="msg", args=(), exc_info=None,
        )
        record.correlation_id = "-"
        record.user_id = "-"
        record.company_id = "-"
        record.path = "-"

        log_record = {}
        fmt.add_fields(log_record, record, {})
        assert "request" not in log_record

    def test_performance_logger_success(self):
        from apps.core.logging import PerformanceLogger

        logger = logging.getLogger("perf_test")
        with PerformanceLogger("test_op", logger) as perf:
            perf.add_metadata(rows=10)
            time.sleep(0.001)

    def test_performance_logger_failure(self):
        from apps.core.logging import PerformanceLogger

        logger = logging.getLogger("perf_test")
        with pytest.raises(ValueError):
            with PerformanceLogger("test_op", logger):
                raise ValueError("boom")

    def test_log_event(self):
        from apps.core.logging import log_event

        logger = logging.getLogger("event_test")
        log_event(logger, "test_event", foo="bar")

    def test_get_logger(self):
        from apps.core.logging import get_logger

        lg = get_logger("test.module")
        assert lg.name == "test.module"

    def test_correlation_id_functions(self):
        from apps.core.logging import (
            clear_correlation_id,
            get_correlation_id,
            set_correlation_id,
        )

        cid = set_correlation_id("custom-id")
        assert cid == "custom-id"
        assert get_correlation_id() == "custom-id"

        auto_id = set_correlation_id()
        assert auto_id is not None
        assert len(auto_id) > 0

        clear_correlation_id()
        assert get_correlation_id() is None

    def test_request_context_functions(self):
        from apps.core.logging import (
            clear_request_context,
            get_request_context,
            set_request_context,
        )

        set_request_context({"user_id": "u1"})
        assert get_request_context()["user_id"] == "u1"
        clear_request_context()
        assert get_request_context() == {}

    def test_correlation_id_filter(self):
        from apps.core.logging import CorrelationIdFilter, set_correlation_id, set_request_context

        set_correlation_id("filter-test")
        set_request_context({"user_id": "u2", "company_id": "c2", "path": "/p", "method": "POST"})

        f = CorrelationIdFilter()
        record = logging.LogRecord("test", logging.INFO, "", 0, "msg", (), None)
        result = f.filter(record)
        assert result is True
        assert record.correlation_id == "filter-test"
        assert record.user_id == "u2"


# =============================================================================
# core/healthchecks.py
# =============================================================================


@pytest.mark.django_db
class TestHealthChecks:
    """Tests for health check system."""

    def test_health_checker_database_healthy(self):
        from apps.core.healthchecks import HealthChecker, HealthStatus

        checker = HealthChecker()
        result = checker._check_database()
        assert result.status == HealthStatus.HEALTHY

    def test_health_checker_database_unhealthy(self):
        from apps.core.healthchecks import HealthChecker, HealthStatus

        checker = HealthChecker()
        with patch("apps.core.healthchecks.connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.__enter__ = Mock(side_effect=Exception("DB down"))
            mock_conn.cursor.return_value = mock_cursor
            result = checker._check_database()
            assert result.status == HealthStatus.UNHEALTHY

    def test_health_checker_redis_unhealthy(self):
        from apps.core.healthchecks import HealthChecker, HealthStatus

        checker = HealthChecker()
        with patch("apps.core.healthchecks.cache") as mock_cache:
            mock_cache.set.side_effect = Exception("Redis down")
            result = checker._check_redis()
            assert result.status == HealthStatus.UNHEALTHY

    def test_health_checker_redis_mismatch(self):
        from apps.core.healthchecks import HealthChecker, HealthStatus

        checker = HealthChecker()
        with patch("apps.core.healthchecks.cache") as mock_cache:
            mock_cache.set.return_value = None
            mock_cache.get.return_value = "wrong_value"
            result = checker._check_redis()
            assert result.status == HealthStatus.DEGRADED

    def test_run_all_checks_aggregates_degraded(self):
        from apps.core.healthchecks import ComponentHealth, HealthChecker, HealthStatus

        checker = HealthChecker()
        checker.checks = [
            lambda: ComponentHealth(name="a", status=HealthStatus.HEALTHY),
            lambda: ComponentHealth(name="b", status=HealthStatus.DEGRADED),
        ]
        overall, results = checker.run_all_checks()
        assert overall == HealthStatus.DEGRADED
        assert len(results) == 2

    def test_run_all_checks_unhealthy(self):
        from apps.core.healthchecks import ComponentHealth, HealthChecker, HealthStatus

        checker = HealthChecker()
        checker.checks = [
            lambda: ComponentHealth(name="a", status=HealthStatus.UNHEALTHY),
        ]
        overall, results = checker.run_all_checks()
        assert overall == HealthStatus.UNHEALTHY

    def test_run_all_checks_exception(self):
        from apps.core.healthchecks import HealthChecker, HealthStatus

        checker = HealthChecker()

        def failing_check():
            raise RuntimeError("check failed")

        failing_check.__name__ = "_check_failing"
        checker.checks = [failing_check]
        overall, results = checker.run_all_checks()
        assert overall == HealthStatus.UNHEALTHY
        assert results[0].name == "failing"

    def test_component_health_to_dict_full(self):
        from apps.core.healthchecks import ComponentHealth, HealthStatus

        ch = ComponentHealth(
            name="test", status=HealthStatus.HEALTHY,
            latency_ms=1.5, message="ok", details={"key": "val"},
        )
        d = ch.to_dict()
        assert d["latency_ms"] == 1.5
        assert d["message"] == "ok"
        assert d["details"]["key"] == "val"

    def test_component_health_to_dict_minimal(self):
        from apps.core.healthchecks import ComponentHealth, HealthStatus

        ch = ComponentHealth(name="test", status=HealthStatus.HEALTHY)
        d = ch.to_dict()
        assert "latency_ms" not in d
        assert "message" not in d
        assert "details" not in d

    def test_health_check_view_healthy(self):
        from apps.core.healthchecks import ComponentHealth, HealthCheckView, HealthChecker, HealthStatus

        view = HealthCheckView()
        request = RequestFactory().get("/health/")
        with patch.object(HealthChecker, "run_all_checks") as mock:
            mock.return_value = (HealthStatus.HEALTHY, [
                ComponentHealth(name="db", status=HealthStatus.HEALTHY),
            ])
            response = view.get(request)
            assert response.status_code == 200

    def test_health_check_view_unhealthy(self):
        from apps.core.healthchecks import ComponentHealth, HealthCheckView, HealthChecker, HealthStatus

        view = HealthCheckView()
        request = RequestFactory().get("/health/")
        with patch.object(HealthChecker, "run_all_checks") as mock:
            mock.return_value = (HealthStatus.UNHEALTHY, [
                ComponentHealth(name="db", status=HealthStatus.UNHEALTHY),
            ])
            response = view.get(request)
            assert response.status_code == 503

    def test_health_check_view_degraded(self):
        from apps.core.healthchecks import ComponentHealth, HealthCheckView, HealthChecker, HealthStatus

        view = HealthCheckView()
        request = RequestFactory().get("/health/")
        with patch.object(HealthChecker, "run_all_checks") as mock:
            mock.return_value = (HealthStatus.DEGRADED, [
                ComponentHealth(name="redis", status=HealthStatus.DEGRADED),
            ])
            response = view.get(request)
            assert response.status_code == 200

    def test_liveness_check_view(self):
        from apps.core.healthchecks import LivenessCheckView

        view = LivenessCheckView()
        request = RequestFactory().get("/liveness/")
        response = view.get(request)
        assert response.status_code == 200

    def test_readiness_check_view_ready(self):
        from apps.core.healthchecks import ComponentHealth, HealthChecker, HealthStatus, ReadinessCheckView

        view = ReadinessCheckView()
        request = RequestFactory().get("/readiness/")
        with patch.object(HealthChecker, "_check_database") as mock_db, \
             patch.object(HealthChecker, "_check_redis") as mock_redis:
            mock_db.return_value = ComponentHealth(name="db", status=HealthStatus.HEALTHY)
            mock_redis.return_value = ComponentHealth(name="redis", status=HealthStatus.HEALTHY)
            response = view.get(request)
            assert response.status_code == 200

    def test_readiness_check_view_not_ready(self):
        from apps.core.healthchecks import ComponentHealth, HealthChecker, HealthStatus, ReadinessCheckView

        view = ReadinessCheckView()
        request = RequestFactory().get("/readiness/")
        with patch.object(HealthChecker, "_check_database") as mock_db, \
             patch.object(HealthChecker, "_check_redis") as mock_redis:
            mock_db.return_value = ComponentHealth(name="db", status=HealthStatus.UNHEALTHY, message="down")
            mock_redis.return_value = ComponentHealth(name="redis", status=HealthStatus.HEALTHY)
            response = view.get(request)
            assert response.status_code == 503


# =============================================================================
# core/authentication.py
# =============================================================================


@pytest.mark.django_db
class TestAuthentication:
    """Tests for authentication views and serializers."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = APIClient()
        self.company = Company.objects.create(name="Auth Co")
        self.user = User.objects.create_user(
            email="auth@test.com", password="TestPass123!", company=self.company,
            first_name="Auth", last_name="User",
        )

    def test_register_view(self):
        response = self.client.post("/api/v2/auth/register/", {
            "email": "new@test.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
            "first_name": "New",
            "last_name": "User",
        }, format="json")
        assert response.status_code == 201
        assert "tokens" in response.data

    def test_register_with_company(self):
        response = self.client.post("/api/v2/auth/register/", {
            "email": "new2@test.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
            "first_name": "New",
            "last_name": "User",
            "company_name": "New Co",
        }, format="json")
        assert response.status_code == 201
        # Verify company was created with user's email
        user = User.objects.get(email="new2@test.com")
        assert user.company is not None
        assert user.company.name == "New Co"
        assert user.company.email == "new2@test.com"

    def test_register_duplicate_email(self):
        response = self.client.post("/api/v2/auth/register/", {
            "email": "auth@test.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
            "first_name": "New",
            "last_name": "User",
        }, format="json")
        assert response.status_code == 400

    def test_register_password_mismatch(self):
        response = self.client.post("/api/v2/auth/register/", {
            "email": "mismatch@test.com",
            "password": "StrongPass123!",
            "password_confirm": "Different123!",
            "first_name": "New",
            "last_name": "User",
        }, format="json")
        assert response.status_code == 400

    def test_login_view(self):
        response = self.client.post("/api/v2/auth/login/", {
            "email": "auth@test.com",
            "password": "TestPass123!",
        }, format="json")
        assert response.status_code == 200
        assert "tokens" in response.data

    def test_login_invalid_credentials(self):
        response = self.client.post("/api/v2/auth/login/", {
            "email": "auth@test.com",
            "password": "WrongPass!",
        }, format="json")
        assert response.status_code == 400

    def test_login_inactive_user(self):
        self.user.is_active = False
        self.user.save()
        response = self.client.post("/api/v2/auth/login/", {
            "email": "auth@test.com",
            "password": "TestPass123!",
        }, format="json")
        assert response.status_code == 400

    def test_logout_view(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/v2/auth/logout/", {"refresh": "invalid"}, format="json")
        assert response.status_code == 200

    def test_change_password(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/v2/auth/change-password/", {
            "current_password": "TestPass123!",
            "new_password": "NewStrongPass456!",
            "new_password_confirm": "NewStrongPass456!",
        }, format="json")
        assert response.status_code == 200

    def test_change_password_wrong_current(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/v2/auth/change-password/", {
            "current_password": "Wrong!",
            "new_password": "NewStrongPass456!",
            "new_password_confirm": "NewStrongPass456!",
        }, format="json")
        assert response.status_code == 400

    def test_change_password_mismatch(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/v2/auth/change-password/", {
            "current_password": "TestPass123!",
            "new_password": "NewStrongPass456!",
            "new_password_confirm": "Different789!",
        }, format="json")
        assert response.status_code == 400

    def test_me_view_get(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/v2/auth/me/")
        assert response.status_code == 200
        assert response.data["email"] == "auth@test.com"

    def test_me_view_patch(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch("/api/v2/auth/me/", {"first_name": "Updated"}, format="json")
        assert response.status_code == 200

    def test_create_api_key(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/v2/auth/api-keys/create/", {"name": "test-key"}, format="json")
        assert response.status_code == 201
        assert "key" in response.data["api_key"]
        assert response.data["api_key"]["name"] == "test-key"
        assert "prefix" in response.data["api_key"]

    def test_create_api_key_no_company(self):
        user_no_co = User.objects.create_user(
            email="noco@test.com", password="TestPass123!",
        )
        self.client.force_authenticate(user=user_no_co)
        response = self.client.post("/api/v2/auth/api-keys/create/", {"name": "key"}, format="json")
        assert response.status_code == 400

    def test_create_api_key_no_name(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/v2/auth/api-keys/create/", {}, format="json")
        assert response.status_code == 400

    def test_api_key_authenticate_header(self):
        from apps.core.authentication import APIKeyAuthentication

        auth = APIKeyAuthentication()
        assert auth.authenticate_header(Mock()) == "ApiKey"

    def test_api_key_auth_no_header(self):
        from apps.core.authentication import APIKeyAuthentication

        auth = APIKeyAuthentication()
        request = RequestFactory().get("/")
        request.META["HTTP_AUTHORIZATION"] = "Bearer token"
        assert auth.authenticate(request) is None

    def test_api_key_auth_empty_key(self):
        from apps.core.authentication import APIKeyAuthentication

        auth = APIKeyAuthentication()
        request = RequestFactory().get("/")
        request.META["HTTP_AUTHORIZATION"] = "ApiKey "
        assert auth.authenticate(request) is None


# =============================================================================
# consortiums/signals.py
# =============================================================================


@pytest.mark.django_db
class TestConsortiumSignals:
    """Tests for consortium signal handlers error paths."""

    def test_send_invitation_email_import_error(self):
        from apps.consortiums.signals import _send_invitation_email

        invitation = Mock(id="test-id")
        # Simulate ImportError on local import
        with patch.dict(sys.modules, {"apps.consortiums.emails": None}):
            _send_invitation_email(invitation)

    def test_send_invitation_email_exception(self):
        from apps.consortiums.signals import _send_invitation_email

        invitation = Mock(id="test-id")
        mock_module = MagicMock()
        mock_module.ConsortiumEmailService.return_value.send_invitation.side_effect = Exception("fail")
        with patch.dict(sys.modules, {"apps.consortiums.emails": mock_module}):
            _send_invitation_email(invitation)

    def test_send_invitation_accepted_email_import_error(self):
        from apps.consortiums.signals import _send_invitation_accepted_email

        invitation = Mock(id="test-id")
        with patch.dict(sys.modules, {"apps.consortiums.emails": None}):
            _send_invitation_accepted_email(invitation)

    def test_send_invitation_accepted_email_exception(self):
        from apps.consortiums.signals import _send_invitation_accepted_email

        invitation = Mock(id="test-id")
        mock_module = MagicMock()
        mock_module.ConsortiumEmailService.return_value.send_invitation_accepted.side_effect = Exception("fail")
        with patch.dict(sys.modules, {"apps.consortiums.emails": mock_module}):
            _send_invitation_accepted_email(invitation)

    def test_send_consortium_activated_email_import_error(self):
        from apps.consortiums.signals import _send_consortium_activated_email

        consortium = Mock(id="test-id")
        with patch.dict(sys.modules, {"apps.consortiums.emails": None}):
            _send_consortium_activated_email(consortium)

    def test_send_consortium_activated_email_exception(self):
        from apps.consortiums.signals import _send_consortium_activated_email

        consortium = Mock(id="test-id")
        mock_module = MagicMock()
        mock_module.ConsortiumEmailService.return_value.send_consortium_activated.side_effect = Exception("fail")
        with patch.dict(sys.modules, {"apps.consortiums.emails": mock_module}):
            _send_consortium_activated_email(consortium)

    def test_queue_blockchain_registration_import_error(self):
        from apps.consortiums.signals import _queue_blockchain_registration

        contribution = Mock(id="test-id")
        with patch.dict(sys.modules, {"apps.consortiums.tasks": None}):
            _queue_blockchain_registration(contribution)

    def test_queue_blockchain_registration_exception(self):
        from apps.consortiums.signals import _queue_blockchain_registration

        contribution = Mock(id="test-id")
        mock_module = MagicMock()
        mock_module.register_contribution_blockchain.delay.side_effect = Exception("celery down")
        with patch.dict(sys.modules, {"apps.consortiums.tasks": mock_module}):
            _queue_blockchain_registration(contribution)


# =============================================================================
# blockchain/secrets.py
# =============================================================================


class TestBlockchainSecrets:
    """Tests for blockchain secrets management."""

    def test_blockchain_wallet_repr(self):
        from apps.blockchain.secrets import BlockchainWallet

        w = BlockchainWallet(address="0x1234567890abcdef", private_key="secret", name="test")
        assert "secret" not in repr(w)
        assert "0x12345678" in repr(w)

    def test_rpc_config_arbitrum(self):
        from apps.blockchain.secrets import RPCConfig

        config = RPCConfig(arbitrum_url="https://custom.rpc")
        assert config.get_url("arbitrum") == "https://custom.rpc"

    def test_rpc_config_sepolia_default(self):
        from apps.blockchain.secrets import RPCConfig

        config = RPCConfig()
        url = config.get_url("arbitrum_sepolia")
        assert "sepolia" in url

    def test_secrets_manager_get_secret_cached(self):
        from apps.blockchain.secrets import BlockchainSecretsManager

        mgr = BlockchainSecretsManager()
        with patch("apps.blockchain.secrets.secrets") as mock_secrets:
            mock_secrets.get.return_value = "value1"
            val1 = mgr._get_secret("path", "key")
            val2 = mgr._get_secret("path", "key")
            assert val1 == val2
            assert mock_secrets.get.call_count == 1

    def test_secrets_manager_get_secret_default(self):
        from apps.blockchain.secrets import BlockchainSecretsManager

        mgr = BlockchainSecretsManager()
        with patch("apps.blockchain.secrets.secrets") as mock_secrets:
            mock_secrets.get.return_value = None
            val = mgr._get_secret("path", "key", default="default")
            assert val == "default"

    def test_secrets_manager_clear_cache(self):
        from apps.blockchain.secrets import BlockchainSecretsManager

        mgr = BlockchainSecretsManager()
        mgr._cache["key"] = "value"
        mgr.clear_cache()
        assert len(mgr._cache) == 0

    def test_get_wallet_from_vault(self):
        from apps.blockchain.secrets import BlockchainSecretsManager

        mgr = BlockchainSecretsManager()
        with patch.object(mgr, "_get_secret") as mock_get:
            mock_get.side_effect = lambda path, key, **kw: {
                ("deployer", "private_key"): "0xabc",
                ("deployer", "address"): "0x1234",
            }.get((path, key))
            wallet = mgr.get_wallet("deployer")
            assert wallet is not None
            assert wallet.private_key == "0xabc"

    def test_get_wallet_from_env(self):
        from apps.blockchain.secrets import BlockchainSecretsManager

        mgr = BlockchainSecretsManager()
        with patch.object(mgr, "_get_secret", return_value=None):
            with patch.dict("os.environ", {
                "DEPLOYER_PRIVATE_KEY": "0xenv_key",
                "DEPLOYER_ADDRESS": "0xenv_addr",
            }):
                wallet = mgr.get_wallet("deployer")
                assert wallet is not None
                assert wallet.address == "0xenv_addr"

    def test_get_wallet_not_configured(self):
        from apps.blockchain.secrets import BlockchainSecretsManager

        mgr = BlockchainSecretsManager()
        with patch.object(mgr, "_get_secret", return_value=None):
            with patch.dict("os.environ", {}, clear=True):
                wallet = mgr.get_wallet("deployer")
                assert wallet is None

    def test_get_wallet_derive_address(self):
        from apps.blockchain.secrets import BlockchainSecretsManager

        mgr = BlockchainSecretsManager()
        with patch.object(mgr, "_get_secret") as mock_get:
            mock_get.side_effect = lambda path, key, **kw: {
                ("deployer", "private_key"): "0xabc",
                ("deployer", "address"): None,
            }.get((path, key))
            with patch.object(mgr, "_derive_address", return_value="0xderived"):
                wallet = mgr.get_wallet("deployer")
                assert wallet.address == "0xderived"

    def test_get_contracts_from_vault(self):
        from apps.blockchain.secrets import BlockchainSecretsManager

        mgr = BlockchainSecretsManager()
        with patch.object(mgr, "_get_all_secrets") as mock_get:
            mock_get.return_value = {"governance": "0xgov", "model_registry": "0xreg"}
            contracts = mgr.get_contracts()
            assert contracts.governance == "0xgov"

    def test_get_contracts_from_env(self):
        from apps.blockchain.secrets import BlockchainSecretsManager

        mgr = BlockchainSecretsManager()
        with patch.object(mgr, "_get_all_secrets", return_value=None):
            with patch.dict("os.environ", {"GOVERNANCE_CONTRACT_ADDRESS": "0xenv_gov"}):
                contracts = mgr.get_contracts()
                assert contracts.governance == "0xenv_gov"

    def test_get_rpc_config(self):
        from apps.blockchain.secrets import BlockchainSecretsManager

        mgr = BlockchainSecretsManager()
        with patch.object(mgr, "_get_all_secrets") as mock_get:
            mock_get.return_value = {"arbitrum_url": "https://rpc1"}
            config = mgr.get_rpc_config()
            assert config.arbitrum_url == "https://rpc1"

    def test_get_rpc_config_empty(self):
        from apps.blockchain.secrets import BlockchainSecretsManager

        mgr = BlockchainSecretsManager()
        with patch.object(mgr, "_get_all_secrets", return_value=None):
            config = mgr.get_rpc_config()
            assert config.arbitrum_url is None

    def test_derive_address_no_eth_account(self):
        from apps.blockchain.secrets import BlockchainSecretsManager

        mgr = BlockchainSecretsManager()
        # Force ImportError by temporarily removing eth_account from modules
        original = sys.modules.get("eth_account")
        sys.modules["eth_account"] = None
        try:
            result = mgr._derive_address("0xkey")
            assert result == ""
        finally:
            if original is not None:
                sys.modules["eth_account"] = original
            else:
                sys.modules.pop("eth_account", None)

    def test_store_contract_address(self):
        from apps.blockchain.secrets import BlockchainSecretsManager

        mgr = BlockchainSecretsManager()
        with patch.object(mgr, "_get_all_secrets", return_value={}):
            with patch("apps.blockchain.secrets.secrets") as mock_secrets:
                mock_secrets.put.return_value = True
                result = mgr.store_contract_address("governance", "0x123")
                assert result is True

    def test_store_contract_address_failure(self):
        from apps.blockchain.secrets import BlockchainSecretsManager

        mgr = BlockchainSecretsManager()
        with patch.object(mgr, "_get_all_secrets", side_effect=Exception("vault down")):
            result = mgr.store_contract_address("governance", "0x123")
            assert result is False

    def test_convenience_functions(self):
        from apps.blockchain.secrets import (
            get_contract_addresses,
            get_consortium_signer_wallet,
            get_deployer_wallet,
            get_rpc_url,
            get_verifier_wallet,
        )

        with patch("apps.blockchain.secrets.blockchain_secrets") as mock_mgr:
            mock_mgr.get_deployer.return_value = None
            assert get_deployer_wallet() is None

            mock_mgr.get_consortium_signer.return_value = None
            assert get_consortium_signer_wallet() is None

            mock_mgr.get_verifier.return_value = None
            assert get_verifier_wallet() is None

            mock_mgr.get_rpc_url.return_value = "https://rpc"
            assert get_rpc_url() == "https://rpc"

            mock_mgr.get_contracts.return_value = Mock()
            assert get_contract_addresses() is not None


# =============================================================================
# blockchain/services.py
# =============================================================================


class TestBlockchainServices:
    """Tests for blockchain service classes."""

    def test_transaction_result_bool(self):
        from apps.blockchain.services import TransactionResult

        assert bool(TransactionResult(success=True)) is True
        assert bool(TransactionResult(success=False)) is False

    def test_blockchain_service_init(self):
        from apps.blockchain.services import BlockchainService

        svc = BlockchainService(network="arbitrum")
        assert svc.network == "arbitrum"
        assert svc._web3 is None

    def test_blockchain_service_is_connected_circuit_open(self):
        from apps.blockchain.services import BlockchainService

        svc = BlockchainService()
        svc._circuit = MagicMock()
        svc._circuit.is_open = True
        assert svc.is_connected() is False

    def test_blockchain_service_is_connected_no_web3(self):
        from apps.blockchain.services import BlockchainService

        svc = BlockchainService()
        svc._circuit = MagicMock()
        svc._circuit.is_open = False
        svc._web3 = None
        assert svc.is_connected() is False

    def test_blockchain_service_is_connected_web3_exception(self):
        from apps.blockchain.services import BlockchainService

        svc = BlockchainService()
        svc._circuit = MagicMock()
        svc._circuit.is_open = False
        svc._web3 = MagicMock()
        svc._web3.is_connected.side_effect = Exception("error")
        assert svc.is_connected() is False

    def test_blockchain_service_get_circuit_status(self):
        from apps.blockchain.services import BlockchainService

        svc = BlockchainService()
        svc._circuit = MagicMock()
        svc._circuit.get_stats.return_value = {"state": "closed"}
        assert svc.get_circuit_status() == {"state": "closed"}

    def test_connect_circuit_open(self):
        from apps.blockchain.services import BlockchainService, CircuitBreakerOpen

        svc = BlockchainService()
        svc._circuit = MagicMock()
        svc._circuit.is_open = True
        svc._circuit.name = "test"
        with pytest.raises(CircuitBreakerOpen):
            svc._connect()

    def test_load_contract_abi_not_found(self):
        from apps.blockchain.services import BlockchainService

        svc = BlockchainService()
        svc._web3 = MagicMock()
        with pytest.raises(FileNotFoundError):
            svc._load_contract_abi("NonExistentContract")

    def test_chain_id_property_cached(self):
        from apps.blockchain.services import BlockchainService

        svc = BlockchainService()
        svc._chain_id = 42
        assert svc.chain_id == 42

    def test_sign_and_send_circuit_open(self):
        from apps.blockchain.secrets import BlockchainWallet
        from apps.blockchain.services import BlockchainService

        svc = BlockchainService()
        svc._circuit = MagicMock()
        svc._circuit.is_open = True
        svc._circuit.name = "test"

        wallet = BlockchainWallet(address="0x123", private_key="0xabc", name="test")
        result = svc._sign_and_send_with_retry(wallet, {})
        assert result.success is False
        assert "Circuit breaker" in result.error

    def test_consortium_service_no_wallet(self):
        from apps.blockchain.services import ConsortiumService

        svc = ConsortiumService(contract_address="0x123")
        svc._circuit = MagicMock()
        svc._circuit.is_open = False

        with patch("apps.blockchain.services.get_consortium_signer_wallet", return_value=None):
            result = svc.create_consortium("test", 50, 3600, b"\x00" * 32)
            assert result.success is False

    def test_consortium_service_add_member_no_wallet(self):
        from apps.blockchain.services import ConsortiumService

        svc = ConsortiumService(contract_address="0x123")
        with patch("apps.blockchain.services.get_consortium_signer_wallet", return_value=None):
            result = svc.add_member(b"\x00" * 32, "0xaddr")
            assert result.success is False

    def test_consortium_service_record_contribution_no_wallet(self):
        from apps.blockchain.services import ConsortiumService

        svc = ConsortiumService(contract_address="0x123")
        with patch("apps.blockchain.services.get_consortium_signer_wallet", return_value=None):
            result = svc.record_contribution(b"\x00" * 32, 100, 10, b"\x00" * 32, b"\x00" * 32)
            assert result.success is False

    def test_model_registry_service_no_wallet(self):
        from apps.blockchain.services import ModelRegistryService

        svc = ModelRegistryService(contract_address="0x123")
        with patch("apps.blockchain.services.get_consortium_signer_wallet", return_value=None):
            result = svc.register_model("linear_regression", "1.0.0")
            assert result.success is False

    def test_model_registry_save_checkpoint_no_wallet(self):
        from apps.blockchain.services import ModelRegistryService

        svc = ModelRegistryService(contract_address="0x123")
        with patch("apps.blockchain.services.get_consortium_signer_wallet", return_value=None):
            result = svc.save_checkpoint(b"\x00" * 32, 1, b"\x00" * 32, b"\x00" * 32)
            assert result.success is False

    def test_computation_verifier_no_wallet(self):
        from apps.blockchain.services import ComputationVerifierService

        svc = ComputationVerifierService(contract_address="0x123")
        with patch("apps.blockchain.services.get_consortium_signer_wallet", return_value=None):
            result = svc.register_computation(b"\x00" * 32, b"\x00" * 32, b"\x00" * 32)
            assert result.success is False

    def test_computation_verifier_batch_no_wallet(self):
        from apps.blockchain.services import ComputationVerifierService

        svc = ComputationVerifierService(contract_address="0x123")
        with patch("apps.blockchain.services.get_consortium_signer_wallet", return_value=None):
            result = svc.register_batch(b"\x00" * 32, [], [])
            assert result.success is False


# =============================================================================
# models/models.py
# =============================================================================


@pytest.mark.django_db
class TestMLModels:
    """Tests for ML model classes and methods."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.company = Company.objects.create(name="Model Co")
        from apps.models.models import MLModel

        self.model = MLModel.objects.create(
            name="Test Model", model_type="linear_regression",
            owner=self.company, config={"lr": 0.01},
            params={"weights": [1.0, 2.0]}, n_features=2,
            feature_names=["a", "b"],
        )

    def test_model_str(self):
        assert "Test Model" in str(self.model)

    def test_model_mark_trained(self):
        self.model.mark_trained(epochs=10, loss=0.5, params={"weights": [3.0, 4.0]})
        self.model.refresh_from_db()
        assert self.model.status == "trained"
        assert self.model.training_epochs == 10

    def test_model_create_version_patch(self):
        version = self.model.create_version(bump_type="patch", changelog="First version")
        assert version.version == "1.0.0"
        assert self.model.current_version == "1.0.0"

    def test_model_create_version_minor(self):
        self.model.create_version(bump_type="patch")
        v2 = self.model.create_version(bump_type="minor")
        assert v2.version == "1.1.0"

    def test_model_create_version_major(self):
        self.model.create_version(bump_type="patch")
        v2 = self.model.create_version(bump_type="major")
        assert v2.version == "2.0.0"

    def test_model_get_latest_version(self):
        self.model.create_version()
        latest = self.model.get_latest_version()
        assert latest is not None

    def test_model_export(self):
        self.model.trained_at = timezone.now()
        self.model.save()
        export = self.model.export(exported_by=self.company)
        assert export is not None
        assert export.checksum_sha256

    def test_model_version_publish(self):
        version = self.model.create_version()
        version.publish()
        version.refresh_from_db()
        assert version.status == "published"

    def test_model_version_deprecate(self):
        version = self.model.create_version()
        version.deprecate()
        version.refresh_from_db()
        assert version.status == "deprecated"

    def test_training_run_lifecycle(self):
        from apps.models.models import TrainingRun

        run = TrainingRun.objects.create(model=self.model)
        run.start()
        assert run.status == "running"
        run.complete(final_loss=0.1, metrics={"accuracy": 0.95})
        assert run.status == "completed"
        assert run.duration_seconds is not None

    def test_training_run_fail(self):
        from apps.models.models import TrainingRun

        run = TrainingRun.objects.create(model=self.model)
        run.start()
        run.fail("OOM error")
        assert run.status == "failed"

    def test_training_run_duration_none(self):
        from apps.models.models import TrainingRun

        run = TrainingRun.objects.create(model=self.model)
        assert run.duration_seconds is None

    def test_batch_prediction_lifecycle(self):
        from apps.models.models import BatchPredictionJob

        job = BatchPredictionJob.objects.create(
            model=self.model, requester=self.company,
            input_data=[[1, 2], [3, 4]], n_samples=2,
        )
        job.start()
        assert job.status == "processing"
        job.update_progress(1)
        assert job.progress_percent == 50.0
        job.complete(predictions=[0.5, 0.8], total_latency_ms=100.0)
        assert job.status == "completed"
        assert job.avg_latency_per_sample_ms == 50.0

    def test_batch_prediction_fail(self):
        from apps.models.models import BatchPredictionJob

        job = BatchPredictionJob.objects.create(
            model=self.model, requester=self.company, n_samples=0,
        )
        job.fail("bad input")
        assert job.status == "failed"

    def test_model_share_lifecycle(self):
        from apps.consortiums.models import Consortium
        from apps.models.models import ModelShare

        c1 = Consortium.objects.create(name="Source", owner=self.company)
        c2 = Consortium.objects.create(name="Target", owner=self.company)

        share = ModelShare.objects.create(
            model=self.model, source_consortium=c1,
            shared_by=self.company, target_consortium=c2,
        )
        assert not share.is_active

        share.approve(approved_by=self.company, message="ok")
        share.refresh_from_db()
        assert share.status == "approved"
        assert share.is_active
        assert share.can_predict
        assert not share.can_retrain

    def test_model_share_full_access(self):
        from apps.consortiums.models import Consortium
        from apps.models.models import ModelShare

        c1 = Consortium.objects.create(name="SourceFA", owner=self.company)
        c2 = Consortium.objects.create(name="TargetFA", owner=self.company)

        share = ModelShare.objects.create(
            model=self.model, source_consortium=c1,
            shared_by=self.company, target_consortium=c2,
            share_type="full_access",
        )
        share.approve()
        assert share.can_retrain

    def test_model_share_reject(self):
        from apps.consortiums.models import Consortium
        from apps.models.models import ModelShare

        c1 = Consortium.objects.create(name="SourceR", owner=self.company)
        c2 = Consortium.objects.create(name="TargetR", owner=self.company)

        share = ModelShare.objects.create(
            model=self.model, source_consortium=c1,
            shared_by=self.company, target_consortium=c2,
        )
        share.reject(message="no")
        assert share.status == "rejected"

    def test_model_share_revoke(self):
        from apps.consortiums.models import Consortium
        from apps.models.models import ModelShare

        c1 = Consortium.objects.create(name="SourceV", owner=self.company)
        c2 = Consortium.objects.create(name="TargetV", owner=self.company)

        share = ModelShare.objects.create(
            model=self.model, source_consortium=c1,
            shared_by=self.company, target_consortium=c2,
        )
        share.approve()
        share.revoke(message="revoked")
        assert share.status == "revoked"

    def test_model_share_increment_predictions_expire(self):
        from apps.consortiums.models import Consortium
        from apps.models.models import ModelShare

        c1 = Consortium.objects.create(name="SourceI", owner=self.company)
        c2 = Consortium.objects.create(name="TargetI", owner=self.company)

        share = ModelShare.objects.create(
            model=self.model, source_consortium=c1,
            shared_by=self.company, target_consortium=c2,
            max_predictions=2,
        )
        share.approve()
        share.increment_predictions(2)
        share.refresh_from_db()
        assert share.status == "expired"

    def test_model_share_validity_period_future(self):
        from apps.consortiums.models import Consortium
        from apps.models.models import ModelShare

        c1 = Consortium.objects.create(name="SourceP", owner=self.company)
        c2 = Consortium.objects.create(name="TargetP", owner=self.company)

        share = ModelShare.objects.create(
            model=self.model, source_consortium=c1,
            shared_by=self.company, target_consortium=c2,
            valid_from=timezone.now() + timedelta(days=1),
        )
        share.approve()
        assert not share.is_active

    def test_model_share_valid_until_expired(self):
        from apps.consortiums.models import Consortium
        from apps.models.models import ModelShare

        c1 = Consortium.objects.create(name="SourceE", owner=self.company)
        c2 = Consortium.objects.create(name="TargetE", owner=self.company)

        share = ModelShare.objects.create(
            model=self.model, source_consortium=c1,
            shared_by=self.company, target_consortium=c2,
            valid_until=timezone.now() - timedelta(days=1),
        )
        share.approve()
        assert not share.is_active

    def test_model_export_str(self):
        from apps.models.models import ModelExport

        export = ModelExport.objects.create(
            model=self.model, format="fheml_json",
            export_data={"test": True}, checksum_sha256="abc",
        )
        assert "Test Model" in str(export)

    def test_set_get_params(self):
        self.model.set_params({"weights": [1.0, 2.0], "bias": 0.5})
        self.model.save()
        params = self.model.get_params()
        assert "weights" in params

    def test_batch_prediction_str(self):
        from apps.models.models import BatchPredictionJob

        job = BatchPredictionJob.objects.create(
            model=self.model, requester=self.company, n_samples=5,
        )
        assert "5 samples" in str(job)

    def test_model_checkpoint_str(self):
        from apps.models.models import ModelCheckpoint

        cp = ModelCheckpoint.objects.create(
            model=self.model, epoch=1, weights_hash="abc123",
        )
        assert "Epoch 1" in str(cp)

    def test_prediction_log_str(self):
        from apps.models.models import PredictionLog

        pl = PredictionLog.objects.create(
            model=self.model, requester=self.company,
            n_samples=10, latency_ms=50.0,
        )
        assert "10 samples" in str(pl)


# =============================================================================
# core/serializers.py — validation tests
# =============================================================================


@pytest.mark.django_db
class TestCoreSerializers:
    """Tests for serializer validation methods."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.company = Company.objects.create(name="Serializer Co", email="co@test.com")
        self.user = User.objects.create_user(
            email="ser@test.com", password="TestPass123!", company=self.company,
            first_name="Ser", last_name="User",
        )

    def test_company_create_duplicate_email(self):
        from apps.core.serializers import CompanyCreateSerializer

        ser = CompanyCreateSerializer(data={"name": "Dup Co", "email": "co@test.com"})
        assert not ser.is_valid()

    def test_user_create_duplicate_email(self):
        from apps.core.serializers import UserCreateSerializer

        ser = UserCreateSerializer(data={
            "email": "ser@test.com", "password": "NewPass123!",
            "password_confirm": "NewPass123!", "first_name": "A", "last_name": "B",
        })
        assert not ser.is_valid()

    def test_user_create_password_mismatch(self):
        from apps.core.serializers import UserCreateSerializer

        ser = UserCreateSerializer(data={
            "email": "new@test.com", "password": "StrongPass123!",
            "password_confirm": "Different456!", "first_name": "A", "last_name": "B",
        })
        assert not ser.is_valid()

    def test_user_create_success(self):
        from apps.core.serializers import UserCreateSerializer

        ser = UserCreateSerializer(data={
            "email": "valid@test.com", "password": "StrongPass123!",
            "password_confirm": "StrongPass123!", "first_name": "A", "last_name": "B",
            "company": str(self.company.id),
        })
        assert ser.is_valid(), ser.errors
        user = ser.save()
        assert user.check_password("StrongPass123!")

    def test_change_password_wrong_old(self):
        from apps.core.serializers import ChangePasswordSerializer

        request = Mock()
        request.user = self.user
        ser = ChangePasswordSerializer(data={
            "old_password": "Wrong!", "new_password": "NewPass123!",
            "new_password_confirm": "NewPass123!",
        }, context={"request": request})
        assert not ser.is_valid()

    def test_change_password_mismatch(self):
        from apps.core.serializers import ChangePasswordSerializer

        request = Mock()
        request.user = self.user
        ser = ChangePasswordSerializer(data={
            "old_password": "TestPass123!", "new_password": "NewPass123!",
            "new_password_confirm": "Different456!",
        }, context={"request": request})
        assert not ser.is_valid()

    def test_api_key_create_invalid_permission(self):
        from apps.core.serializers import APIKeyCreateSerializer

        request = Mock()
        request.user = self.user
        ser = APIKeyCreateSerializer(data={
            "name": "key", "permissions": ["read", "invalid"], "rate_limit": 100,
        }, context={"request": request})
        assert not ser.is_valid()

    def test_api_key_create_invalid_rate_limit(self):
        from apps.core.serializers import APIKeyCreateSerializer

        request = Mock()
        request.user = self.user
        ser = APIKeyCreateSerializer(data={
            "name": "key", "permissions": ["read"], "rate_limit": 99999,
        }, context={"request": request})
        assert not ser.is_valid()

    def test_webhook_create_not_https(self):
        from apps.core.serializers import WebhookCreateSerializer

        request = Mock()
        request.user = self.user
        ser = WebhookCreateSerializer(data={
            "name": "hook", "url": "http://insecure.com/webhook",
            "events": ["model.trained"],
        }, context={"request": request})
        assert not ser.is_valid()

    def test_webhook_create_invalid_event(self):
        from apps.core.serializers import WebhookCreateSerializer

        request = Mock()
        request.user = self.user
        ser = WebhookCreateSerializer(data={
            "name": "hook", "url": "https://secure.com/webhook",
            "events": ["invalid_event"],
        }, context={"request": request})
        assert not ser.is_valid()

    def test_webhook_create_invalid_retries(self):
        from apps.core.serializers import WebhookCreateSerializer

        request = Mock()
        request.user = self.user
        ser = WebhookCreateSerializer(data={
            "name": "hook", "url": "https://secure.com/webhook",
            "events": ["model.trained"], "max_retries": 99,
        }, context={"request": request})
        assert not ser.is_valid()

    def test_webhook_create_invalid_timeout(self):
        from apps.core.serializers import WebhookCreateSerializer

        request = Mock()
        request.user = self.user
        ser = WebhookCreateSerializer(data={
            "name": "hook", "url": "https://secure.com/webhook",
            "events": ["model.trained"], "timeout_seconds": 1,
        }, context={"request": request})
        assert not ser.is_valid()

    def test_report_create_invalid_date_range(self):
        from apps.core.serializers import ReportCreateSerializer

        request = Mock()
        request.user = self.user
        ser = ReportCreateSerializer(data={
            "name": "Report", "report_type": "usage", "format": "pdf",
            "date_from": "2026-02-01", "date_to": "2026-01-01",
        }, context={"request": request})
        assert not ser.is_valid()

    def test_workflow_create_invalid_steps_not_list(self):
        from apps.core.serializers import WorkflowCreateSerializer

        request = Mock()
        request.user = self.user
        ser = WorkflowCreateSerializer(data={
            "name": "WF", "steps": "not-a-list",
            "trigger": {"type": "manual"},
        }, context={"request": request})
        assert not ser.is_valid()

    def test_workflow_create_step_missing_type(self):
        from apps.core.serializers import WorkflowCreateSerializer

        request = Mock()
        request.user = self.user
        ser = WorkflowCreateSerializer(data={
            "name": "WF", "steps": [{"name": "step1"}],
            "trigger": {"type": "manual"},
        }, context={"request": request})
        assert not ser.is_valid()

    def test_workflow_create_step_missing_name(self):
        from apps.core.serializers import WorkflowCreateSerializer

        request = Mock()
        request.user = self.user
        ser = WorkflowCreateSerializer(data={
            "name": "WF", "steps": [{"type": "action"}],
            "trigger": {"type": "manual"},
        }, context={"request": request})
        assert not ser.is_valid()

    def test_workflow_create_invalid_trigger_type(self):
        from apps.core.serializers import WorkflowCreateSerializer

        request = Mock()
        request.user = self.user
        ser = WorkflowCreateSerializer(data={
            "name": "WF", "steps": [{"type": "action", "name": "s1"}],
            "trigger": {"type": "invalid"},
        }, context={"request": request})
        assert not ser.is_valid()

    def test_workflow_create_schedule_trigger_missing_schedule(self):
        from apps.core.serializers import WorkflowCreateSerializer

        request = Mock()
        request.user = self.user
        ser = WorkflowCreateSerializer(data={
            "name": "WF", "steps": [{"type": "action", "name": "s1"}],
            "trigger": {"type": "schedule"},
        }, context={"request": request})
        assert not ser.is_valid()

    def test_workflow_create_event_trigger_missing_event(self):
        from apps.core.serializers import WorkflowCreateSerializer

        request = Mock()
        request.user = self.user
        ser = WorkflowCreateSerializer(data={
            "name": "WF", "steps": [{"type": "action", "name": "s1"}],
            "trigger": {"type": "event"},
        }, context={"request": request})
        assert not ser.is_valid()

    def test_scheduled_task_create_invalid_cron(self):
        from apps.core.serializers import ScheduledTaskCreateSerializer

        request = Mock()
        request.user = self.user
        ser = ScheduledTaskCreateSerializer(data={
            "name": "Task", "task_type": "custom", "cron_expression": "* *",
        }, context={"request": request})
        assert not ser.is_valid()

    def test_scheduled_task_report_without_report(self):
        from apps.core.serializers import ScheduledTaskCreateSerializer

        request = Mock()
        request.user = self.user
        ser = ScheduledTaskCreateSerializer(data={
            "name": "Task", "task_type": "report", "cron_expression": "* * * * *",
        }, context={"request": request})
        assert not ser.is_valid()

    def test_scheduled_task_workflow_without_workflow(self):
        from apps.core.serializers import ScheduledTaskCreateSerializer

        request = Mock()
        request.user = self.user
        ser = ScheduledTaskCreateSerializer(data={
            "name": "Task", "task_type": "workflow", "cron_expression": "* * * * *",
        }, context={"request": request})
        assert not ser.is_valid()

    def test_api_key_response_serializer_with_raw_key(self):
        from apps.core.serializers import APIKeyResponseSerializer

        api_key = APIKey.objects.create(company=self.company, name="test", key_hash="abc")
        api_key._raw_key = "raw-key-value"
        ser = APIKeyResponseSerializer(api_key)
        assert ser.data["key"] == "raw-key-value"

    def test_api_key_response_serializer_no_raw_key(self):
        from apps.core.serializers import APIKeyResponseSerializer

        api_key = APIKey.objects.create(company=self.company, name="test2", key_hash="def")
        ser = APIKeyResponseSerializer(api_key)
        assert ser.data["key"] is None


# =============================================================================
# data_quality/views.py
# =============================================================================


@pytest.mark.django_db
class TestDataQualityViews:
    """Tests for data quality views."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = APIClient()
        self.company = Company.objects.create(name="DQ Co")
        self.user = User.objects.create_user(
            email="dq@test.com", password="TestPass123!", company=self.company,
        )
        self.client.force_authenticate(user=self.user)

    def test_quality_assessment_list(self):
        response = self.client.get("/api/v2/data-quality/assessments/")
        assert response.status_code == 200

    def test_quality_assessment_filter_by_consortium(self):
        from apps.consortiums.models import Consortium

        c = Consortium.objects.create(name="DQ Consortium", owner=self.company)
        response = self.client.get(f"/api/v2/data-quality/assessments/?consortium={c.id}")
        assert response.status_code == 200

    def test_quality_alert_list(self):
        response = self.client.get("/api/v2/data-quality/alerts/")
        assert response.status_code == 200

    def test_quality_alert_filter_by_status(self):
        response = self.client.get("/api/v2/data-quality/alerts/?status=open")
        assert response.status_code == 200

    def test_quality_alert_open_count(self):
        response = self.client.get("/api/v2/data-quality/alerts/open_count/")
        assert response.status_code == 200

    def test_quality_dashboard(self):
        response = self.client.get("/api/v2/data-quality/dashboard/")
        assert response.status_code == 200

    def test_quality_dashboard_no_company(self):
        user_no_co = User.objects.create_user(email="nocodq@test.com", password="TestPass123!")
        self.client.force_authenticate(user=user_no_co)
        response = self.client.get("/api/v2/data-quality/dashboard/")
        assert response.status_code == 403


# =============================================================================
# explainability/views.py
# =============================================================================


@pytest.mark.django_db
class TestExplainabilityViews:
    """Tests for explainability views."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = APIClient()
        self.company = Company.objects.create(name="Explainability Co")
        self.user = User.objects.create_user(
            email="explain@test.com", password="TestPass123!", company=self.company,
        )
        self.client.force_authenticate(user=self.user)

    def test_explanation_request_list(self):
        response = self.client.get("/api/v2/explainability/requests/")
        assert response.status_code == 200

    def test_explanation_request_filter_consortium(self):
        from apps.consortiums.models import Consortium

        c = Consortium.objects.create(name="Explain C", owner=self.company)
        response = self.client.get(f"/api/v2/explainability/requests/?consortium={c.id}")
        assert response.status_code == 200

    def test_explanation_request_filter_status(self):
        response = self.client.get("/api/v2/explainability/requests/?status=pending")
        assert response.status_code == 200

    def test_model_insight_list(self):
        response = self.client.get("/api/v2/explainability/insights/")
        assert response.status_code == 200

    def test_model_insight_include_inactive(self):
        response = self.client.get("/api/v2/explainability/insights/?include_inactive=true")
        assert response.status_code == 200

    def test_feature_importance_list(self):
        response = self.client.get("/api/v2/explainability/features/")
        assert response.status_code == 200

    def test_feature_importance_top(self):
        response = self.client.get("/api/v2/explainability/features/top/?n=5")
        assert response.status_code == 200

    def test_explainability_dashboard(self):
        response = self.client.get("/api/v2/explainability/dashboard/")
        assert response.status_code == 200

    def test_explainability_dashboard_no_company(self):
        user_no_co = User.objects.create_user(email="nocoex@test.com", password="TestPass123!")
        self.client.force_authenticate(user=user_no_co)
        response = self.client.get("/api/v2/explainability/dashboard/")
        assert response.status_code == 403

    def test_explanation_create_feature_importance(self):
        from apps.consortiums.models import Consortium, ConsortiumMember

        c = Consortium.objects.create(name="FI Consortium", owner=self.company)
        ConsortiumMember.objects.create(
            consortium=c, company=self.company,
            role=ConsortiumMember.Role.OWNER, status=ConsortiumMember.Status.ACTIVE,
        )
        response = self.client.post("/api/v2/explainability/requests/", {
            "consortium": str(c.id), "explanation_type": "feature_importance",
        }, format="json")
        assert response.status_code == 201

    def test_explanation_create_shap(self):
        from apps.consortiums.models import Consortium, ConsortiumMember

        c = Consortium.objects.create(name="SHAP Consortium", owner=self.company)
        ConsortiumMember.objects.create(
            consortium=c, company=self.company,
            role=ConsortiumMember.Role.OWNER, status=ConsortiumMember.Status.ACTIVE,
        )
        response = self.client.post("/api/v2/explainability/requests/", {
            "consortium": str(c.id), "explanation_type": "shap",
        }, format="json")
        assert response.status_code == 201

    def test_explanation_create_decision_path(self):
        from apps.consortiums.models import Consortium, ConsortiumMember

        c = Consortium.objects.create(name="DP Consortium", owner=self.company)
        ConsortiumMember.objects.create(
            consortium=c, company=self.company,
            role=ConsortiumMember.Role.OWNER, status=ConsortiumMember.Status.ACTIVE,
        )
        response = self.client.post("/api/v2/explainability/requests/", {
            "consortium": str(c.id), "explanation_type": "decision_path",
        }, format="json")
        assert response.status_code == 201

    def test_explanation_create_summary(self):
        from apps.consortiums.models import Consortium, ConsortiumMember

        c = Consortium.objects.create(name="Sum Consortium", owner=self.company)
        ConsortiumMember.objects.create(
            consortium=c, company=self.company,
            role=ConsortiumMember.Role.OWNER, status=ConsortiumMember.Status.ACTIVE,
        )
        response = self.client.post("/api/v2/explainability/requests/", {
            "consortium": str(c.id), "explanation_type": "summary",
        }, format="json")
        assert response.status_code == 201

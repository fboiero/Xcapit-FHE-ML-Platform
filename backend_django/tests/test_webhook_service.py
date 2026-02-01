"""
Tests for WebhookService.

Covers event triggering, delivery, signature generation, retries, and lifecycle.
"""

from unittest.mock import MagicMock, patch

import pytest
import requests
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.core.models import Company, Webhook, WebhookDelivery
from apps.core.services.base import ServiceContext
from apps.core.services.webhook import WebhookService, trigger_webhook_event

User = get_user_model()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def wh_company(db):
    return Company.objects.create(name="Webhook Co", email="wh@co.com", industry="tech")


@pytest.fixture
def wh_user(db, wh_company):
    return User.objects.create_user(
        email="whuser@co.com",
        password="password123",
        company=wh_company,
    )


@pytest.fixture
def webhook(db, wh_company):
    return Webhook.objects.create(
        company=wh_company,
        name="Test Hook",
        url="https://example.com/webhook",
        secret="test-secret-key-123",
        events=["model.trained", "model.failed"],
        custom_headers={"X-Custom": "value"},
        is_active=True,
    )


@pytest.fixture
def inactive_webhook(db, wh_company):
    return Webhook.objects.create(
        company=wh_company,
        name="Inactive Hook",
        url="https://example.com/disabled",
        secret="secret",
        events=["model.trained"],
        is_active=False,
    )


@pytest.fixture
def all_events_webhook(db, wh_company):
    return Webhook.objects.create(
        company=wh_company,
        name="All Events",
        url="https://example.com/all",
        secret="all-secret",
        events=["*"],
        is_active=True,
    )


# ===========================================================================
# WebhookService - trigger_event Tests
# ===========================================================================


@pytest.mark.django_db
class TestWebhookServiceTriggerEvent:
    def test_trigger_event_creates_deliveries(self, wh_company, webhook):
        service = WebhookService()
        result = service.trigger_event(
            "model.trained",
            {"model_id": "123"},
            company=wh_company,
        )

        assert result.success
        deliveries = result.data
        assert len(deliveries) == 1
        assert deliveries[0].event_type == "model.trained"

    def test_trigger_event_skips_non_matching(self, wh_company, webhook):
        service = WebhookService()
        result = service.trigger_event(
            "data.uploaded",
            {"data_id": "456"},
            company=wh_company,
        )

        assert result.success
        assert len(result.data) == 0

    def test_trigger_event_no_company_fails(self):
        service = WebhookService()
        result = service.trigger_event("model.trained", {"x": 1})

        assert not result.success
        assert result.error_code == "no_company"

    def test_trigger_event_uses_context_company(self, wh_company, webhook):
        context = ServiceContext(company=wh_company)
        service = WebhookService(context)
        result = service.trigger_event("model.trained", {"x": 1})

        assert result.success
        assert len(result.data) == 1

    def test_trigger_event_skips_inactive_webhooks(self, wh_company, inactive_webhook):
        service = WebhookService()
        result = service.trigger_event(
            "model.trained",
            {"x": 1},
            company=wh_company,
        )

        assert result.success
        assert len(result.data) == 0

    @patch.object(WebhookService, "_send_delivery")
    def test_trigger_event_sync_sends_immediately(self, mock_send, wh_company, webhook):
        mock_send.return_value = True

        service = WebhookService()
        result = service.trigger_event(
            "model.trained",
            {"x": 1},
            company=wh_company,
            async_send=False,
        )

        assert result.success
        mock_send.assert_called_once()


# ===========================================================================
# WebhookService - _send_delivery Tests
# ===========================================================================


@pytest.mark.django_db
class TestWebhookServiceSendDelivery:
    def _create_delivery(self, webhook, event_type="model.trained"):
        return WebhookDelivery.objects.create(
            webhook=webhook,
            event_type=event_type,
            payload={"test": True},
            max_attempts=3,
        )

    @patch("requests.Session.post")
    def test_send_delivery_success(self, mock_post, webhook):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_post.return_value = mock_response

        delivery = self._create_delivery(webhook)
        service = WebhookService()
        result = service._send_delivery(delivery)

        assert result is True
        delivery.refresh_from_db()
        assert delivery.status == WebhookDelivery.Status.DELIVERED

    @patch("requests.Session.post")
    def test_send_delivery_http_error(self, mock_post, webhook):
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        delivery = self._create_delivery(webhook)
        service = WebhookService()
        result = service._send_delivery(delivery)

        assert result is False
        delivery.refresh_from_db()
        assert delivery.status in [
            WebhookDelivery.Status.FAILED,
            WebhookDelivery.Status.RETRYING,
        ]

    @patch("requests.Session.post")
    def test_send_delivery_timeout(self, mock_post, webhook):
        mock_post.side_effect = requests.exceptions.Timeout("Timeout")

        delivery = self._create_delivery(webhook)
        service = WebhookService()
        result = service._send_delivery(delivery)

        assert result is False

    @patch("requests.Session.post")
    def test_send_delivery_connection_error(self, mock_post, webhook):
        mock_post.side_effect = requests.exceptions.ConnectionError("Refused")

        delivery = self._create_delivery(webhook)
        service = WebhookService()
        result = service._send_delivery(delivery)

        assert result is False

    @patch("requests.Session.post")
    def test_send_delivery_unexpected_error(self, mock_post, webhook):
        mock_post.side_effect = RuntimeError("Unexpected")

        delivery = self._create_delivery(webhook)
        service = WebhookService()
        result = service._send_delivery(delivery)

        assert result is False


# ===========================================================================
# WebhookService - Signature Tests
# ===========================================================================


class TestWebhookServiceSignature:
    def test_generate_signature_deterministic(self):
        sig1 = WebhookService._generate_signature("secret", "payload")
        sig2 = WebhookService._generate_signature("secret", "payload")

        assert sig1 == sig2

    def test_generate_signature_hmac_sha256(self):
        import hashlib
        import hmac

        secret = "my-secret"
        payload = '{"event":"test"}'
        expected = hmac.new(
            secret.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()

        result = WebhookService._generate_signature(secret, payload)

        assert result == expected

    def test_different_secret_different_signature(self):
        sig1 = WebhookService._generate_signature("secret1", "payload")
        sig2 = WebhookService._generate_signature("secret2", "payload")

        assert sig1 != sig2

    def test_different_payload_different_signature(self):
        sig1 = WebhookService._generate_signature("secret", "payload1")
        sig2 = WebhookService._generate_signature("secret", "payload2")

        assert sig1 != sig2


# ===========================================================================
# WebhookService - Retry Tests
# ===========================================================================


@pytest.mark.django_db
class TestWebhookServiceRetry:
    @patch.object(WebhookService, "_send_delivery")
    def test_retry_pending_deliveries(self, mock_send, webhook):
        mock_send.return_value = True

        delivery = WebhookDelivery.objects.create(
            webhook=webhook,
            event_type="model.trained",
            payload={"x": 1},
            status=WebhookDelivery.Status.RETRYING,
            next_retry_at=timezone.now(),
        )

        service = WebhookService()
        result = service.retry_pending_deliveries()

        assert result.success
        assert result.data >= 1
        mock_send.assert_called_once()

    @patch.object(WebhookService, "_send_delivery")
    def test_retry_skips_inactive_webhook(self, mock_send, wh_company):
        inactive = Webhook.objects.create(
            company=wh_company,
            name="Dead",
            url="https://dead.com",
            secret="s",
            events=["*"],
            is_active=False,
        )
        WebhookDelivery.objects.create(
            webhook=inactive,
            event_type="test",
            payload={},
            status=WebhookDelivery.Status.RETRYING,
            next_retry_at=timezone.now(),
        )

        service = WebhookService()
        result = service.retry_pending_deliveries()

        assert result.success
        mock_send.assert_not_called()

    @patch.object(WebhookService, "_send_delivery")
    def test_retry_skips_future_deliveries(self, mock_send, webhook):
        from datetime import timedelta

        WebhookDelivery.objects.create(
            webhook=webhook,
            event_type="test",
            payload={},
            status=WebhookDelivery.Status.RETRYING,
            next_retry_at=timezone.now() + timedelta(hours=1),
        )

        service = WebhookService()
        result = service.retry_pending_deliveries()

        assert result.success
        assert result.data == 0


# ===========================================================================
# WebhookService - Lifecycle Tests
# ===========================================================================


@pytest.mark.django_db
class TestWebhookServiceLifecycle:
    def test_create_webhook(self, wh_company, wh_user):
        context = ServiceContext(user=wh_user, company=wh_company)
        service = WebhookService(context)
        result = service.create_webhook(
            name="New Hook",
            url="https://example.com/new",
            events=["model.trained"],
        )

        assert result.success
        wh = result.data
        assert wh.name == "New Hook"
        assert wh.url == "https://example.com/new"
        assert wh.secret  # Auto-generated
        assert wh.company == wh_company

    def test_create_webhook_with_custom_secret(self, wh_company, wh_user):
        context = ServiceContext(user=wh_user, company=wh_company)
        service = WebhookService(context)
        result = service.create_webhook(
            name="Custom Secret",
            url="https://example.com/cs",
            events=["*"],
            secret="my-custom-secret",
        )

        assert result.success
        assert result.data.secret == "my-custom-secret"

    @patch("requests.Session.post")
    def test_verify_webhook_success(self, mock_post, wh_company, webhook):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        context = ServiceContext(company=wh_company)
        service = WebhookService(context)
        result = service.verify_webhook(str(webhook.id))

        assert result.success
        webhook.refresh_from_db()
        assert webhook.is_verified is True

    @patch("requests.Session.post")
    def test_verify_webhook_failure(self, mock_post, wh_company, webhook):
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        context = ServiceContext(company=wh_company)
        service = WebhookService(context)
        result = service.verify_webhook(str(webhook.id))

        assert not result.success
        assert result.error_code == "verification_failed"

    def test_verify_webhook_not_found(self, wh_company):
        context = ServiceContext(company=wh_company)
        service = WebhookService(context)
        result = service.verify_webhook("00000000-0000-0000-0000-000000000000")

        assert not result.success
        assert result.error_code == "not_found"

    @patch("requests.Session.post")
    def test_verify_webhook_connection_error(self, mock_post, wh_company, webhook):
        mock_post.side_effect = requests.exceptions.ConnectionError("Refused")

        context = ServiceContext(company=wh_company)
        service = WebhookService(context)
        result = service.verify_webhook(str(webhook.id))

        assert not result.success
        assert result.error_code == "connection_error"


# ===========================================================================
# Convenience Function Tests
# ===========================================================================


@pytest.mark.django_db
class TestTriggerWebhookEvent:
    @patch.object(WebhookService, "_send_delivery")
    def test_trigger_webhook_event_convenience(self, mock_send, wh_company, webhook):
        mock_send.return_value = True

        trigger_webhook_event("model.trained", {"id": "123"}, wh_company)

        # Should have created a delivery and attempted to send
        assert WebhookDelivery.objects.filter(
            webhook=webhook,
            event_type="model.trained",
        ).exists()

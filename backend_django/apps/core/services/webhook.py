"""
Webhook service for sending event notifications.

Handles webhook delivery with retry logic and signature verification.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

import requests
from django.db import transaction
from django.utils import timezone

from .base import BaseService, ServiceContext, ServiceResult

if TYPE_CHECKING:
    from apps.core.models import Company, Webhook, WebhookDelivery

logger = logging.getLogger(__name__)


class WebhookService(BaseService):
    """
    Service for managing webhooks and sending event notifications.

    Features:
    - Event-based webhook triggering
    - HMAC-SHA256 signature verification
    - Automatic retry with exponential backoff
    - Delivery status tracking
    """

    SIGNATURE_HEADER = "X-FHE-Signature"
    EVENT_HEADER = "X-FHE-Event"
    DELIVERY_ID_HEADER = "X-FHE-Delivery-ID"
    TIMESTAMP_HEADER = "X-FHE-Timestamp"

    def __init__(self, context: ServiceContext | None = None) -> None:
        super().__init__(context)
        self._session = None

    @property
    def session(self) -> requests.Session:
        """Get or create HTTP session for connection pooling."""
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({
                "Content-Type": "application/json",
                "User-Agent": "FHE-ML-Platform-Webhook/1.0",
            })
        return self._session

    def trigger_event(
        self,
        event_type: str,
        payload: dict[str, Any],
        company: Company | None = None,
        async_send: bool = True,
    ) -> ServiceResult[list]:
        """
        Trigger a webhook event for all subscribed webhooks.

        Args:
            event_type: The type of event (e.g., "model.trained")
            payload: Event payload data
            company: Company to send webhooks for (uses context if not provided)
            async_send: If True, queue for async delivery; if False, send immediately

        Returns:
            ServiceResult with list of WebhookDelivery objects
        """
        from apps.core.models import Webhook, WebhookDelivery

        target_company = company or self.company
        if not target_company:
            return ServiceResult.fail("No company specified", error_code="no_company")

        # Find all webhooks that should receive this event
        webhooks = Webhook.objects.filter(
            company=target_company,
            is_active=True,
        )

        deliveries = []
        for webhook in webhooks:
            if not webhook.should_receive_event(event_type):
                continue

            # Create delivery record
            delivery = WebhookDelivery.objects.create(
                webhook=webhook,
                event_type=event_type,
                payload=payload,
                max_attempts=webhook.max_retries,
            )
            deliveries.append(delivery)

            if not async_send:
                # Send immediately
                self._send_delivery(delivery)

        logger.info(
            f"Triggered event {event_type} for company {target_company.id}, "
            f"created {len(deliveries)} deliveries"
        )

        return ServiceResult.ok(deliveries)

    def _send_delivery(self, delivery: WebhookDelivery) -> bool:
        """
        Send a single webhook delivery.

        Returns:
            True if successful, False otherwise
        """
        webhook = delivery.webhook
        payload = delivery.payload

        # Add metadata to payload
        enriched_payload = {
            "event": delivery.event_type,
            "delivery_id": str(delivery.id),
            "timestamp": timezone.now().isoformat(),
            "data": payload,
        }

        payload_json = json.dumps(enriched_payload, separators=(",", ":"), sort_keys=True)

        # Generate signature
        signature = self._generate_signature(webhook.secret, payload_json)

        # Prepare headers
        headers = {
            self.SIGNATURE_HEADER: f"sha256={signature}",
            self.EVENT_HEADER: delivery.event_type,
            self.DELIVERY_ID_HEADER: str(delivery.id),
            self.TIMESTAMP_HEADER: str(int(time.time())),
        }
        headers.update(webhook.custom_headers)

        try:
            start_time = time.time()
            response = self.session.post(
                webhook.url,
                data=payload_json,
                headers=headers,
                timeout=webhook.timeout_seconds,
            )
            latency_ms = (time.time() - start_time) * 1000

            if response.ok:
                delivery.mark_delivered(
                    status_code=response.status_code,
                    body=response.text[:10000],
                    latency_ms=latency_ms,
                )
                logger.info(f"Webhook delivery {delivery.id} successful")
                return True
            else:
                delivery.mark_failed(
                    error=f"HTTP {response.status_code}: {response.text[:500]}",
                    status_code=response.status_code,
                    retry=True,
                )
                logger.warning(
                    f"Webhook delivery {delivery.id} failed: {response.status_code}"
                )
                return False

        except requests.exceptions.Timeout:
            delivery.mark_failed(error="Request timeout", retry=True)
            logger.warning(f"Webhook delivery {delivery.id} timed out")
            return False

        except requests.exceptions.ConnectionError as e:
            delivery.mark_failed(error=f"Connection error: {str(e)}", retry=True)
            logger.warning(f"Webhook delivery {delivery.id} connection error: {e}")
            return False

        except Exception as e:
            delivery.mark_failed(error=f"Unexpected error: {str(e)}", retry=False)
            logger.error(f"Webhook delivery {delivery.id} unexpected error: {e}")
            return False

    @staticmethod
    def _generate_signature(secret: str, payload: str) -> str:
        """Generate HMAC-SHA256 signature for payload."""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

    def retry_pending_deliveries(self) -> ServiceResult[int]:
        """
        Retry all pending webhook deliveries that are due.

        Returns:
            ServiceResult with count of retried deliveries
        """
        from apps.core.models import WebhookDelivery

        now = timezone.now()
        pending = WebhookDelivery.objects.filter(
            status=WebhookDelivery.Status.RETRYING,
            next_retry_at__lte=now,
        ).select_related("webhook")

        retried_count = 0
        for delivery in pending:
            if delivery.webhook.is_active:
                self._send_delivery(delivery)
                retried_count += 1

        return ServiceResult.ok(retried_count)

    def create_webhook(
        self,
        name: str,
        url: str,
        events: list[str],
        secret: str | None = None,
        custom_headers: dict | None = None,
    ) -> ServiceResult:
        """
        Create a new webhook for the current company.

        Args:
            name: Display name for the webhook
            url: Target URL for webhook delivery
            events: List of event types to subscribe to
            secret: Optional custom secret (generated if not provided)
            custom_headers: Optional custom headers to include

        Returns:
            ServiceResult with created Webhook
        """
        import secrets as py_secrets

        from apps.core.models import Webhook

        company = self.require_company()

        if not secret:
            secret = py_secrets.token_urlsafe(32)

        with transaction.atomic():
            webhook = Webhook.objects.create(
                company=company,
                name=name,
                url=url,
                secret=secret,
                events=events,
                custom_headers=custom_headers or {},
            )

        logger.info(f"Created webhook {webhook.id} for company {company.id}")
        return ServiceResult.ok(webhook)

    def verify_webhook(self, webhook_id: str) -> ServiceResult:
        """
        Verify a webhook by sending a test event.

        Returns:
            ServiceResult indicating success or failure
        """
        from apps.core.models import Webhook

        try:
            webhook = Webhook.objects.get(id=webhook_id, company=self.company)
        except Webhook.DoesNotExist:
            return ServiceResult.fail("Webhook not found", error_code="not_found")

        # Send test event
        test_payload = {
            "event": "webhook.test",
            "webhook_id": str(webhook.id),
            "timestamp": timezone.now().isoformat(),
        }

        payload_json = json.dumps(test_payload, separators=(",", ":"), sort_keys=True)
        signature = self._generate_signature(webhook.secret, payload_json)

        headers = {
            self.SIGNATURE_HEADER: f"sha256={signature}",
            self.EVENT_HEADER: "webhook.test",
            self.TIMESTAMP_HEADER: str(int(time.time())),
        }

        try:
            response = self.session.post(
                webhook.url,
                data=payload_json,
                headers=headers,
                timeout=10,
            )

            if response.ok:
                webhook.is_verified = True
                webhook.save(update_fields=["is_verified"])
                return ServiceResult.ok({"verified": True, "status_code": response.status_code})
            else:
                return ServiceResult.fail(
                    f"Verification failed: HTTP {response.status_code}",
                    error_code="verification_failed",
                    details={"status_code": response.status_code},
                )

        except Exception as e:
            return ServiceResult.fail(
                f"Verification failed: {str(e)}",
                error_code="connection_error",
            )


def trigger_webhook_event(
    event_type: str,
    payload: dict[str, Any],
    company: Company,
) -> None:
    """
    Convenience function to trigger a webhook event.

    This is the main entry point for other services to trigger webhooks.
    """
    context = ServiceContext(company=company)
    service = WebhookService(context)
    service.trigger_event(event_type, payload, async_send=False)

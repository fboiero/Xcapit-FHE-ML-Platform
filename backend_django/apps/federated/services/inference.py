"""
Inference service for federated learning.

Handles:
- Encrypted inference requests
- Result generation and storage
- Endpoint statistics
"""

from __future__ import annotations

import base64
import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from django.db import transaction
from django.utils import timezone

from apps.core.services.base import BaseService, ServiceResult

if TYPE_CHECKING:
    from apps.core.models import Company
    from apps.federated.models import InferenceEndpoint, InferenceRequest

logger = logging.getLogger(__name__)


@dataclass
class InferenceResultData:
    """Data class for inference result."""

    request_id: str
    encrypted_output: str
    latency_ms: float
    metadata: dict[str, Any]


class InferenceService(BaseService):
    """
    Service for handling inference requests.

    Encapsulates:
    - Request validation and creation
    - Encrypted prediction generation
    - Result storage and retrieval
    - Endpoint statistics updates
    """

    def predict(
        self,
        endpoint: InferenceEndpoint,
        requester: Company,
        input_data: list[dict[str, Any]],
        encryption_key_id: str = "",
        priority: str = "normal",
    ) -> ServiceResult[InferenceResultData]:
        """
        Execute an encrypted prediction through the endpoint.

        Args:
            endpoint: The inference endpoint to use
            requester: Company making the request
            input_data: List of input samples
            encryption_key_id: Optional encryption key ID
            priority: Request priority (low, normal, high)

        Returns:
            ServiceResult with inference result data
        """
        from apps.federated.models import (
            InferenceEndpoint,
            InferenceRequest,
            InferenceResult,
        )

        # Validate endpoint status
        if endpoint.status != InferenceEndpoint.Status.ACTIVE:
            return ServiceResult.fail(
                "Endpoint is not active",
                error_code="endpoint_inactive",
            )

        start_time = time.time()

        # Map priority string to enum
        priority_map = {
            "low": InferenceRequest.Priority.LOW,
            "normal": InferenceRequest.Priority.NORMAL,
            "high": InferenceRequest.Priority.HIGH,
        }
        priority_enum = priority_map.get(priority, InferenceRequest.Priority.NORMAL)

        try:
            with transaction.atomic():
                # Create request record
                inference_request = InferenceRequest.objects.create(
                    endpoint=endpoint,
                    requester=requester,
                    input_hash=InferenceRequest.hash_input(input_data),
                    encryption_key_id=encryption_key_id,
                    priority=priority_enum,
                )

                # Start processing
                inference_request.started_at = timezone.now()
                inference_request.status = InferenceRequest.Status.PROCESSING
                inference_request.save()

                # Execute encrypted prediction
                encrypted_output, output_metadata = self._execute_prediction(
                    endpoint, input_data
                )

                latency_ms = (time.time() - start_time) * 1000

                # Create result
                n_samples = len(input_data)
                result = InferenceResult.objects.create(
                    request=inference_request,
                    encrypted_output=encrypted_output,
                    output_metadata=output_metadata,
                    confidence_scores=[0.95] * n_samples,  # Simulated
                )

                # Update request
                inference_request.status = InferenceRequest.Status.COMPLETED
                inference_request.completed_at = timezone.now()
                inference_request.latency_ms = latency_ms
                inference_request.save()

                # Update endpoint statistics
                self._update_endpoint_stats(endpoint, latency_ms)

                logger.info(
                    f"Inference completed: endpoint={endpoint.id}, "
                    f"samples={n_samples}, latency={latency_ms:.2f}ms"
                )

                return ServiceResult.ok(
                    InferenceResultData(
                        request_id=str(inference_request.id),
                        encrypted_output=encrypted_output,
                        latency_ms=round(latency_ms, 2),
                        metadata=output_metadata,
                    )
                )

        except Exception as e:
            logger.error(f"Inference failed: {e}")
            return ServiceResult.fail(
                str(e),
                error_code="inference_error",
            )

    def _execute_prediction(
        self,
        endpoint: InferenceEndpoint,
        input_data: list[dict[str, Any]],
    ) -> tuple[str, dict[str, Any]]:
        """
        Execute the actual encrypted prediction.

        In production, this would call the FHE inference engine.
        Currently returns simulated encrypted output.
        """
        n_samples = len(input_data)

        # Simulated encrypted prediction
        # In production: actual FHE computation
        encrypted_output = base64.b64encode(
            f"encrypted_predictions_{n_samples}_samples_{time.time()}".encode()
        ).decode()

        model_version = (
            endpoint.model.version if endpoint.model else "1.0.0"
        )

        output_metadata = {
            "n_samples": n_samples,
            "model_version": model_version,
            "endpoint_type": endpoint.endpoint_type,
            "encryption_scheme": "CKKS",
            "timestamp": timezone.now().isoformat(),
        }

        return encrypted_output, output_metadata

    def _update_endpoint_stats(
        self,
        endpoint: InferenceEndpoint,
        latency_ms: float,
    ) -> None:
        """Update endpoint request statistics."""
        endpoint.request_count += 1
        endpoint.total_latency_ms += latency_ms
        endpoint.save(update_fields=["request_count", "total_latency_ms"])

    def get_request_result(
        self,
        inference_request: InferenceRequest,
    ) -> ServiceResult[dict]:
        """
        Get the result for a completed inference request.

        Args:
            inference_request: The request to get result for

        Returns:
            ServiceResult with result data
        """
        from apps.federated.models import InferenceRequest, InferenceResult

        if inference_request.status != InferenceRequest.Status.COMPLETED:
            return ServiceResult.fail(
                f"Request is {inference_request.status}",
                error_code="invalid_status",
            )

        try:
            result = inference_request.result
            return ServiceResult.ok({
                "request_id": str(inference_request.id),
                "encrypted_output": result.encrypted_output,
                "output_metadata": result.output_metadata,
                "confidence_scores": result.confidence_scores,
                "created_at": result.created_at.isoformat(),
            })
        except InferenceResult.DoesNotExist:
            return ServiceResult.fail(
                "Result not found",
                error_code="not_found",
            )

    def get_endpoint_stats(self, endpoint: InferenceEndpoint) -> dict[str, Any]:
        """
        Get statistics for an endpoint.

        Args:
            endpoint: The endpoint to get stats for

        Returns:
            Dictionary with endpoint statistics
        """
        from apps.federated.models import InferenceRequest

        # Get request counts by status
        requests = InferenceRequest.objects.filter(endpoint=endpoint)
        completed = requests.filter(
            status=InferenceRequest.Status.COMPLETED
        ).count()
        failed = requests.filter(
            status=InferenceRequest.Status.FAILED
        ).count()

        return {
            "endpoint_id": str(endpoint.id),
            "name": endpoint.name,
            "status": endpoint.status,
            "request_count": endpoint.request_count,
            "avg_latency_ms": endpoint.avg_latency_ms,
            "success_rate": (
                (completed / (completed + failed) * 100)
                if (completed + failed) > 0
                else 100.0
            ),
            "uptime_percent": 99.9,  # Simulated
            "model": (
                {
                    "id": str(endpoint.model.id),
                    "name": endpoint.model.name,
                    "version": endpoint.model.version,
                }
                if endpoint.model
                else None
            ),
        }

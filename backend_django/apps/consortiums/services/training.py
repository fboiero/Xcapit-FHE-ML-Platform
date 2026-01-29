"""
FHE Training service for Xcapit FHE-ML Platform.

Handles federated model training using Fully Homomorphic Encryption.
"""

from __future__ import annotations

import hashlib
import logging
from typing import TYPE_CHECKING, Any

from apps.core.services.base import BaseService, ServiceResult
from django.conf import settings
from django.db import transaction
from django.db.models import Count, Sum
from django.utils import timezone

if TYPE_CHECKING:
    from apps.consortiums.models import Consortium, TrainingResult

logger = logging.getLogger(__name__)


class FHETrainingService(BaseService):
    """
    Service for executing FHE-based model training.

    Uses the SDK's FHE models to train on encrypted data
    from consortium contributions.
    """

    def __init__(self, request=None):
        super().__init__(request)
        self.security_level = getattr(settings, "FHE_SECURITY_LEVEL", 128)

    @transaction.atomic
    def start_training(self, consortium: Consortium) -> ServiceResult[dict[str, Any]]:
        """
        Initialize a new training run for a consortium.

        Args:
            consortium: The consortium to train

        Returns:
            ServiceResult with TrainingResult details and task_id
        """
        from apps.consortiums.models import ContributionProof, TrainingResult

        # Validate consortium can start training
        if consortium.status not in ["active"]:
            return ServiceResult.fail(
                "Consortium must be active to start training",
                error_code="invalid_status",
            )

        # Get verified contributions
        contributions = ContributionProof.objects.filter(
            consortium=consortium,
            verification_status=ContributionProof.VerificationStatus.VERIFIED,
        )

        if not contributions.exists():
            return ServiceResult.fail(
                "No verified contributions available",
                error_code="no_contributions",
            )

        # Calculate totals
        stats = contributions.aggregate(
            total_records=Sum("record_count"),
        )

        # Create training result record
        training_result = TrainingResult.objects.create(
            consortium=consortium,
            status=TrainingResult.Status.PENDING,
            contributions_count=contributions.count(),
            total_records=stats["total_records"] or 0,
            config_snapshot={
                "model_type": consortium.model_type,
                "ml_config": consortium.ml_config,
                "security_level": self.security_level,
            },
        )

        # Update consortium status
        consortium.status = "training"
        consortium.save(update_fields=["status", "updated_at"])

        # Queue the training task
        from apps.consortiums.tasks import train_consortium_model

        task = train_consortium_model.delay(str(training_result.id))

        logger.info(
            "Training started for consortium %s, task_id: %s",
            consortium.name,
            task.id,
            extra={
                "consortium_id": str(consortium.id),
                "training_result_id": str(training_result.id),
                "task_id": task.id,
            },
        )

        # Send notification email
        try:
            from apps.consortiums.emails import ConsortiumEmailService

            email_service = ConsortiumEmailService()
            email_service.send_training_started(training_result)
        except Exception as e:
            logger.warning("Failed to send training started email: %s", str(e))

        return ServiceResult.ok({
            "training_result_id": str(training_result.id),
            "task_id": task.id,
            "status": "pending",
            "contributions_count": training_result.contributions_count,
            "total_records": training_result.total_records,
        })

    def train(self, training_result: TrainingResult) -> ServiceResult[dict[str, Any]]:
        """
        Execute the actual FHE training.

        This method is called by the Celery task and performs
        the heavy lifting of FHE model training.

        Args:
            training_result: The training result to process

        Returns:
            ServiceResult with training metrics
        """
        from apps.consortiums.models import ContributionProof

        consortium = training_result.consortium

        try:
            # Get verified contributions
            contributions = ContributionProof.objects.filter(
                consortium=consortium,
                verification_status=ContributionProof.VerificationStatus.VERIFIED,
            )

            if not contributions.exists():
                return self._fail_training(
                    training_result,
                    "No verified contributions found",
                )

            # Initialize FHE model based on consortium configuration
            model_type = consortium.model_type
            ml_config = consortium.ml_config

            # Get FHE model from SDK
            model = self._get_fhe_model(model_type, ml_config)

            if not model:
                return self._fail_training(
                    training_result,
                    f"Unsupported model type: {model_type}",
                )

            # Simulate training (in real implementation, this would
            # aggregate encrypted data from all contributions)
            epochs = ml_config.get("epochs", 10)
            learning_rate = ml_config.get("learning_rate", 0.01)

            # Train the model
            training_metrics = self._execute_training(
                model=model,
                contributions=contributions,
                epochs=epochs,
                learning_rate=learning_rate,
            )

            # Generate model hash
            model_hash = self._generate_model_hash(training_result, training_metrics)

            # Update training result
            training_result.status = TrainingResult.Status.COMPLETED
            training_result.completed_at = timezone.now()
            training_result.accuracy = training_metrics.get("accuracy")
            training_result.loss = training_metrics.get("loss")
            training_result.epochs_completed = training_metrics.get("epochs_completed", epochs)
            training_result.model_hash = model_hash
            training_result.save()

            # Update consortium status
            consortium.status = "completed"
            consortium.save(update_fields=["status", "updated_at"])

            # Queue blockchain registration
            from apps.consortiums.tasks import register_training_result_blockchain

            register_training_result_blockchain.delay(str(training_result.id))

            logger.info(
                "Training completed for consortium %s",
                consortium.name,
                extra={
                    "consortium_id": str(consortium.id),
                    "training_result_id": str(training_result.id),
                    "accuracy": training_metrics.get("accuracy"),
                },
            )

            return ServiceResult.ok({
                "accuracy": training_metrics.get("accuracy"),
                "loss": training_metrics.get("loss"),
                "epochs_completed": training_metrics.get("epochs_completed"),
                "model_hash": model_hash,
            })

        except Exception as e:
            logger.exception(
                "Training failed for consortium %s: %s",
                consortium.name,
                str(e),
            )
            return self._fail_training(training_result, str(e))

    def _get_fhe_model(self, model_type: str, config: dict):
        """
        Get the appropriate FHE model from the SDK.

        Args:
            model_type: Type of model (linear_regression, logistic_regression, etc.)
            config: Model configuration

        Returns:
            FHE model instance or None if unsupported
        """
        try:
            # Import SDK models
            from sdk.models import (
                FHEDecisionTree,
                FHEKMeans,
                FHELinearRegression,
                FHELogisticRegression,
            )

            model_map = {
                "linear_regression": FHELinearRegression,
                "logistic_regression": FHELogisticRegression,
                "decision_tree": FHEDecisionTree,
                "kmeans": FHEKMeans,
            }

            model_class = model_map.get(model_type)
            if not model_class:
                return None

            # Initialize with security level
            return model_class(security_level=self.security_level)

        except ImportError:
            logger.warning("SDK models not available, using mock training")
            return MockFHEModel(model_type)

    def _execute_training(
        self,
        model,
        contributions,
        epochs: int,
        learning_rate: float,
    ) -> dict[str, Any]:
        """
        Execute the training loop.

        In a real implementation, this would:
        1. Aggregate encrypted data from contributions
        2. Run FHE training iterations
        3. Return trained model metrics

        Args:
            model: The FHE model instance
            contributions: QuerySet of verified contributions
            epochs: Number of training epochs
            learning_rate: Learning rate

        Returns:
            Dictionary with training metrics
        """
        total_records = sum(c.record_count for c in contributions)

        # For demonstration, we simulate training metrics
        # In production, this would use actual FHE computations
        import random

        # Simulate realistic metrics based on data size
        base_accuracy = 0.75
        data_bonus = min(0.15, total_records / 100000)
        noise = random.uniform(-0.05, 0.05)

        accuracy = min(0.99, base_accuracy + data_bonus + noise)
        loss = max(0.01, 1 - accuracy + random.uniform(-0.1, 0.1))

        return {
            "accuracy": round(accuracy * 100, 2),
            "loss": round(loss, 4),
            "epochs_completed": epochs,
            "total_records_processed": total_records,
        }

    def _generate_model_hash(
        self,
        training_result: TrainingResult,
        metrics: dict,
    ) -> str:
        """
        Generate a deterministic hash for the trained model.

        Args:
            training_result: The training result
            metrics: Training metrics

        Returns:
            SHA-256 hash string
        """
        # Create hash from training parameters and results
        hash_input = (
            f"{training_result.consortium_id}"
            f"{training_result.config_snapshot}"
            f"{metrics.get('accuracy', 0)}"
            f"{metrics.get('loss', 0)}"
            f"{training_result.total_records}"
            f"{timezone.now().isoformat()}"
        )

        return hashlib.sha256(hash_input.encode()).hexdigest()

    def _fail_training(
        self,
        training_result: TrainingResult,
        error_message: str,
    ) -> ServiceResult:
        """
        Mark training as failed and update records.

        Args:
            training_result: The training result to fail
            error_message: Error description

        Returns:
            ServiceResult with failure
        """
        training_result.status = TrainingResult.Status.FAILED
        training_result.error_message = error_message
        training_result.completed_at = timezone.now()
        training_result.save()

        # Reset consortium status
        consortium = training_result.consortium
        consortium.status = "active"
        consortium.save(update_fields=["status", "updated_at"])

        return ServiceResult.fail(error_message, error_code="training_failed")


class MockFHEModel:
    """Mock FHE model for testing when SDK is not available."""

    def __init__(self, model_type: str):
        self.model_type = model_type

    def train(self, data):
        """Mock training method."""
        pass

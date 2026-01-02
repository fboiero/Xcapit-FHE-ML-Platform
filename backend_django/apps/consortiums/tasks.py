"""
Celery tasks for consortium operations.

Handles asynchronous processing of:
- Model training
- Blockchain registration
- Batch notifications
"""

import logging
from typing import Any

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_kwargs={"max_retries": 3},
    name="consortiums.train_model",
)
def train_consortium_model(
    self,
    training_result_id: str,
) -> dict[str, Any]:
    """
    Execute FHE model training for a consortium.

    Args:
        training_result_id: UUID of the TrainingResult to process

    Returns:
        Dictionary with training results
    """
    from apps.consortiums.models import TrainingResult
    from apps.consortiums.services.training import FHETrainingService

    logger.info(
        "Starting training task for result %s",
        training_result_id,
        extra={"training_result_id": training_result_id, "task_id": self.request.id},
    )

    try:
        training_result = TrainingResult.objects.select_related("consortium").get(
            id=training_result_id
        )
    except TrainingResult.DoesNotExist:
        logger.error("TrainingResult %s not found", training_result_id)
        return {"error": "TrainingResult not found", "status": "failed"}

    # Update task ID
    training_result.task_id = self.request.id
    training_result.status = TrainingResult.Status.RUNNING
    training_result.started_at = timezone.now()
    training_result.save(update_fields=["task_id", "status", "started_at"])

    # Execute training
    service = FHETrainingService()
    result = service.train(training_result)

    if result.success:
        logger.info(
            "Training completed successfully for %s",
            training_result_id,
            extra={
                "training_result_id": training_result_id,
                "accuracy": result.data.get("accuracy") if result.data else None,
            },
        )

        # Send completion email
        _send_training_complete_email(training_result)

        return {
            "status": "completed",
            "training_result_id": training_result_id,
            **result.data,
        }
    else:
        logger.error(
            "Training failed for %s: %s",
            training_result_id,
            result.error,
            extra={"training_result_id": training_result_id},
        )
        return {
            "status": "failed",
            "training_result_id": training_result_id,
            "error": result.error,
        }


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
    name="consortiums.register_contribution_blockchain",
)
def register_contribution_blockchain(
    self,
    contribution_id: str,
) -> dict[str, Any]:
    """
    Register a contribution proof on the blockchain.

    Args:
        contribution_id: UUID of the ContributionProof to register

    Returns:
        Dictionary with registration result
    """
    from apps.consortiums.models import ContributionProof
    from apps.consortiums.services.blockchain import BlockchainRegistrationService

    logger.info(
        "Registering contribution %s on blockchain",
        contribution_id,
        extra={"contribution_id": contribution_id, "task_id": self.request.id},
    )

    try:
        contribution = ContributionProof.objects.get(id=contribution_id)
    except ContributionProof.DoesNotExist:
        logger.error("ContributionProof %s not found", contribution_id)
        return {"error": "ContributionProof not found", "status": "failed"}

    service = BlockchainRegistrationService()
    result = service.register_contribution(contribution)

    if result.success:
        logger.info(
            "Contribution %s registered on blockchain: %s",
            contribution_id,
            result.data.get("tx_hash") if result.data else None,
        )
        return {
            "status": "registered",
            "contribution_id": contribution_id,
            **result.data,
        }
    else:
        logger.error(
            "Failed to register contribution %s: %s",
            contribution_id,
            result.error,
        )
        return {
            "status": "failed",
            "contribution_id": contribution_id,
            "error": result.error,
        }


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
    name="consortiums.register_training_result_blockchain",
)
def register_training_result_blockchain(
    self,
    training_result_id: str,
) -> dict[str, Any]:
    """
    Register a training result on the blockchain.

    Args:
        training_result_id: UUID of the TrainingResult to register

    Returns:
        Dictionary with registration result
    """
    from apps.consortiums.models import TrainingResult
    from apps.consortiums.services.blockchain import BlockchainRegistrationService

    logger.info(
        "Registering training result %s on blockchain",
        training_result_id,
        extra={"training_result_id": training_result_id, "task_id": self.request.id},
    )

    try:
        training_result = TrainingResult.objects.get(id=training_result_id)
    except TrainingResult.DoesNotExist:
        logger.error("TrainingResult %s not found", training_result_id)
        return {"error": "TrainingResult not found", "status": "failed"}

    service = BlockchainRegistrationService()
    result = service.register_training_result(training_result)

    if result.success:
        logger.info(
            "Training result %s registered on blockchain: %s",
            training_result_id,
            result.data.get("tx_hash") if result.data else None,
        )
        return {
            "status": "registered",
            "training_result_id": training_result_id,
            **result.data,
        }
    else:
        logger.error(
            "Failed to register training result %s: %s",
            training_result_id,
            result.error,
        )
        return {
            "status": "failed",
            "training_result_id": training_result_id,
            "error": result.error,
        }


def _send_training_complete_email(training_result):
    """Send training completion email notification."""
    try:
        from apps.consortiums.emails import ConsortiumEmailService

        email_service = ConsortiumEmailService()
        email_service.send_training_complete(training_result)
    except Exception as e:
        logger.error(
            "Failed to send training complete email: %s",
            str(e),
            extra={"training_result_id": str(training_result.id)},
        )

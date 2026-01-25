"""
Federated model management service.

Handles:
- Model lifecycle (training, deployment)
- Model status transitions
- Training coordination
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from django.db import transaction

from apps.core.services.base import BaseService, ServiceResult

if TYPE_CHECKING:
    from apps.consortiums.models import Consortium
    from apps.federated.models import FederatedModel

logger = logging.getLogger(__name__)


class FederatedModelService(BaseService):
    """
    Service for managing federated models.

    Handles:
    - Model creation and configuration
    - Training initiation and coordination
    - Deployment management
    - Status transitions
    """

    def create_model(
        self,
        consortium: Consortium,
        name: str,
        model_type: str,
        config: dict[str, Any] | None = None,
    ) -> ServiceResult[FederatedModel]:
        """
        Create a new federated model.

        Args:
            consortium: Owner consortium
            name: Model name
            model_type: Type of model (logistic_regression, etc.)
            config: Optional model configuration

        Returns:
            ServiceResult with created model
        """
        from apps.federated.models import FederatedModel

        # Check consortium is active
        if consortium.status != consortium.Status.ACTIVE:
            return ServiceResult.fail(
                "Consortium is not active",
                error_code="consortium_inactive",
            )

        with transaction.atomic():
            model = FederatedModel.objects.create(
                consortium=consortium,
                name=name,
                model_type=model_type,
                config=config or {},
                version="1.0.0",
            )

            logger.info(
                f"Created federated model {model.id} "
                f"for consortium {consortium.id}"
            )

            return ServiceResult.ok(model)

    def start_training(
        self,
        model: FederatedModel,
        training_config: dict[str, Any] | None = None,
    ) -> ServiceResult[FederatedModel]:
        """
        Start federated training for a model.

        Args:
            model: The model to train
            training_config: Optional training configuration override

        Returns:
            ServiceResult with updated model
        """
        from apps.federated.models import FederatedModel

        # Validate model can be trained
        if model.status == FederatedModel.Status.TRAINING:
            return ServiceResult.fail(
                "Model is already training",
                error_code="invalid_status",
            )

        if model.status == FederatedModel.Status.DEPLOYED:
            return ServiceResult.fail(
                "Cannot train a deployed model",
                error_code="invalid_status",
            )

        # Update config if provided
        if training_config:
            model.config.update(training_config)

        model.status = FederatedModel.Status.TRAINING
        model.save(update_fields=["status", "config", "updated_at"])

        logger.info(f"Started training for model {model.id}")

        # In production, this would trigger async training job
        # For now, we just mark it as training

        return ServiceResult.ok(model)

    def complete_training(
        self,
        model: FederatedModel,
        metrics: dict[str, Any],
        weights_hash: str = "",
    ) -> ServiceResult[FederatedModel]:
        """
        Mark model training as complete.

        Args:
            model: The model that completed training
            metrics: Training metrics (accuracy, loss, etc.)
            weights_hash: Hash of trained weights

        Returns:
            ServiceResult with updated model
        """
        from apps.federated.models import FederatedModel

        if model.status != FederatedModel.Status.TRAINING:
            return ServiceResult.fail(
                "Model is not training",
                error_code="invalid_status",
            )

        model.status = FederatedModel.Status.READY
        model.training_metrics = metrics
        if weights_hash:
            model.weights_hash = weights_hash

        # Increment version
        version_parts = model.version.split(".")
        version_parts[-1] = str(int(version_parts[-1]) + 1)
        model.version = ".".join(version_parts)

        model.save()

        logger.info(f"Training completed for model {model.id}: v{model.version}")

        return ServiceResult.ok(model)

    def deploy_model(self, model: FederatedModel) -> ServiceResult[FederatedModel]:
        """
        Deploy a model for inference.

        Args:
            model: The model to deploy

        Returns:
            ServiceResult with deployed model
        """
        from apps.federated.models import FederatedModel

        if model.status != FederatedModel.Status.READY:
            return ServiceResult.fail(
                "Model must be ready before deployment",
                error_code="invalid_status",
            )

        model.status = FederatedModel.Status.DEPLOYED
        model.save(update_fields=["status", "updated_at"])

        logger.info(f"Deployed model {model.id}")

        return ServiceResult.ok(model)

    def undeploy_model(self, model: FederatedModel) -> ServiceResult[FederatedModel]:
        """
        Undeploy a model (return to ready status).

        Args:
            model: The model to undeploy

        Returns:
            ServiceResult with updated model
        """
        from apps.federated.models import FederatedModel

        if model.status != FederatedModel.Status.DEPLOYED:
            return ServiceResult.fail(
                "Model is not deployed",
                error_code="invalid_status",
            )

        model.status = FederatedModel.Status.READY
        model.save(update_fields=["status", "updated_at"])

        logger.info(f"Undeployed model {model.id}")

        return ServiceResult.ok(model)

    def archive_model(self, model: FederatedModel) -> ServiceResult[FederatedModel]:
        """
        Archive a model (soft delete).

        Args:
            model: The model to archive

        Returns:
            ServiceResult with archived model
        """
        from apps.federated.models import FederatedModel

        if model.status == FederatedModel.Status.TRAINING:
            return ServiceResult.fail(
                "Cannot archive a model that is training",
                error_code="invalid_status",
            )

        model.status = FederatedModel.Status.ARCHIVED
        model.save(update_fields=["status", "updated_at"])

        logger.info(f"Archived model {model.id}")

        return ServiceResult.ok(model)

    def get_model_status(self, model: FederatedModel) -> dict[str, Any]:
        """
        Get comprehensive model status.

        Args:
            model: The model to check

        Returns:
            Dictionary with model status information
        """
        from apps.federated.models import EdgeNode

        # Get deployment info
        edge_nodes = EdgeNode.objects.filter(deployed_models=model)

        return {
            "id": str(model.id),
            "name": model.name,
            "version": model.version,
            "status": model.status,
            "model_type": model.model_type,
            "training_metrics": model.training_metrics,
            "deployed_nodes": [
                {
                    "id": str(node.id),
                    "name": node.name,
                    "status": node.status,
                }
                for node in edge_nodes
            ],
            "node_count": edge_nodes.count(),
            "created_at": model.created_at.isoformat(),
            "updated_at": model.updated_at.isoformat(),
        }

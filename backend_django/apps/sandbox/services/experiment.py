"""
Experiment execution service.

Handles:
- Experiment validation and execution
- Result generation for different experiment types
- Status management
"""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING, Any

from django.db import transaction

from apps.core.services.base import BaseService, ServiceResult

if TYPE_CHECKING:
    from apps.sandbox.models import Experiment

logger = logging.getLogger(__name__)


class ExperimentService(BaseService):
    """
    Service for executing sandbox experiments.

    Encapsulates experiment execution logic including:
    - Training experiments
    - Evaluation experiments
    - Clustering experiments
    - Encryption benchmarks
    """

    def run_experiment(self, experiment: Experiment) -> ServiceResult[dict]:
        """
        Execute an experiment and update its status.

        Args:
            experiment: The experiment to run

        Returns:
            ServiceResult with experiment results
        """
        from apps.sandbox.models import Experiment as ExperimentModel

        # Validate experiment can be run
        if experiment.status not in [
            ExperimentModel.Status.PENDING,
            ExperimentModel.Status.FAILED,
        ]:
            return ServiceResult.fail(
                f"Experiment is already {experiment.status}",
                error_code="invalid_status",
            )

        # Check sandbox status
        if experiment.sandbox.is_expired:
            return ServiceResult.fail(
                "Sandbox has expired",
                error_code="sandbox_expired",
            )

        if experiment.sandbox.status != experiment.sandbox.Status.ACTIVE:
            return ServiceResult.fail(
                "Sandbox is not active",
                error_code="sandbox_inactive",
            )

        # Start experiment
        experiment.start()
        logger.info(f"Started experiment {experiment.id}: {experiment.name}")

        try:
            with transaction.atomic():
                results = self._execute(experiment)
                experiment.complete(results)

                logger.info(
                    f"Completed experiment {experiment.id}: "
                    f"{experiment.experiment_type}"
                )

                return ServiceResult.ok(results)

        except Exception as e:
            error_message = str(e)
            experiment.fail(error_message)
            logger.error(f"Experiment {experiment.id} failed: {error_message}")

            return ServiceResult.fail(
                error_message,
                error_code="execution_error",
            )

    def _execute(self, experiment: Experiment) -> dict[str, Any]:
        """
        Execute the experiment based on its type.

        This is a simulation - in production, this would call
        actual ML/FHE operations.
        """
        from apps.sandbox.models import Experiment as ExperimentModel

        exp_type = experiment.experiment_type
        config = experiment.config or {}

        if exp_type == ExperimentModel.ExperimentType.TRAINING:
            return self._run_training(config)
        elif exp_type == ExperimentModel.ExperimentType.EVALUATION:
            return self._run_evaluation(config)
        elif exp_type == ExperimentModel.ExperimentType.CLUSTERING:
            return self._run_clustering(config)
        elif exp_type == ExperimentModel.ExperimentType.ENCRYPTION_BENCHMARK:
            return self._run_encryption_benchmark(config)
        else:
            return {"status": "completed", "type": exp_type}

    def _run_training(self, config: dict[str, Any]) -> dict[str, Any]:
        """Simulate training experiment."""
        epochs = config.get("epochs", 10)
        learning_rate = config.get("learning_rate", 0.01)
        batch_size = config.get("batch_size", 32)

        # Simulate learning curve
        base_accuracy = random.uniform(0.70, 0.80)
        improvement = random.uniform(0.10, 0.20)
        final_accuracy = min(base_accuracy + improvement, 0.99)

        base_loss = random.uniform(0.30, 0.50)
        loss_reduction = random.uniform(0.15, 0.30)
        final_loss = max(base_loss - loss_reduction, 0.01)

        return {
            "accuracy": round(final_accuracy, 4),
            "loss": round(final_loss, 4),
            "epochs_completed": epochs,
            "training_time_seconds": random.randint(10, 120),
            "config": {
                "learning_rate": learning_rate,
                "batch_size": batch_size,
                "epochs": epochs,
            },
            "history": {
                "accuracy": [
                    round(base_accuracy + (improvement * i / epochs), 4)
                    for i in range(epochs + 1)
                ],
                "loss": [
                    round(base_loss - (loss_reduction * i / epochs), 4)
                    for i in range(epochs + 1)
                ],
            },
        }

    def _run_evaluation(self, config: dict[str, Any]) -> dict[str, Any]:
        """Simulate evaluation experiment."""
        # Generate realistic metrics
        accuracy = random.uniform(0.70, 0.90)
        precision = random.uniform(0.70, 0.90)
        recall = random.uniform(0.70, 0.90)

        # F1 score is harmonic mean of precision and recall
        f1 = 2 * (precision * recall) / (precision + recall)

        return {
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "auc_roc": round(random.uniform(0.75, 0.95), 4),
            "confusion_matrix": {
                "true_positive": random.randint(800, 900),
                "true_negative": random.randint(800, 900),
                "false_positive": random.randint(50, 150),
                "false_negative": random.randint(50, 150),
            },
        }

    def _run_clustering(self, config: dict[str, Any]) -> dict[str, Any]:
        """Simulate clustering experiment."""
        n_clusters = config.get("n_clusters", 3)

        # Generate cluster sizes (roughly equal)
        total_points = config.get("n_samples", 1000)
        base_size = total_points // n_clusters
        cluster_sizes = [base_size] * n_clusters
        cluster_sizes[-1] += total_points - sum(cluster_sizes)

        return {
            "n_clusters": n_clusters,
            "inertia": round(random.uniform(100, 1000), 2),
            "silhouette_score": round(random.uniform(0.3, 0.8), 4),
            "davies_bouldin_score": round(random.uniform(0.5, 1.5), 4),
            "cluster_sizes": cluster_sizes,
            "iterations": random.randint(10, 50),
        }

    def _run_encryption_benchmark(self, config: dict[str, Any]) -> dict[str, Any]:
        """Simulate FHE encryption benchmark."""
        security_level = config.get("security_level", 128)

        # Higher security = longer times
        security_multiplier = security_level / 128

        return {
            "encryption_time_ms": round(
                random.uniform(10, 50) * security_multiplier, 2
            ),
            "decryption_time_ms": round(
                random.uniform(5, 25) * security_multiplier, 2
            ),
            "computation_time_ms": round(
                random.uniform(50, 200) * security_multiplier, 2
            ),
            "ciphertext_size_kb": int(
                random.randint(100, 500) * security_multiplier
            ),
            "security_level": security_level,
            "operations_tested": ["add", "multiply", "compare"],
            "throughput_ops_per_second": round(
                random.uniform(100, 1000) / security_multiplier, 2
            ),
        }

    def cancel_experiment(self, experiment: Experiment) -> ServiceResult[None]:
        """
        Cancel a running experiment.

        Args:
            experiment: The experiment to cancel

        Returns:
            ServiceResult indicating success or failure
        """
        from apps.sandbox.models import Experiment as ExperimentModel

        if experiment.status != ExperimentModel.Status.RUNNING:
            return ServiceResult.fail(
                "Experiment is not running",
                error_code="invalid_status",
            )

        experiment.fail("Cancelled by user")
        logger.info(f"Cancelled experiment {experiment.id}")

        return ServiceResult.ok(None)

    def get_experiment_status(self, experiment: Experiment) -> dict[str, Any]:
        """
        Get current status and details of an experiment.

        Args:
            experiment: The experiment to check

        Returns:
            Dictionary with status information
        """
        return {
            "id": str(experiment.id),
            "name": experiment.name,
            "status": experiment.status,
            "experiment_type": experiment.experiment_type,
            "started_at": experiment.started_at.isoformat() if experiment.started_at else None,
            "completed_at": experiment.completed_at.isoformat() if experiment.completed_at else None,
            "results": experiment.results,
            "error_message": experiment.error_message,
        }

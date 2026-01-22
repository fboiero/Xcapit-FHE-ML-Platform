"""
ML Model management for Xcapit FHE-ML Platform.

Handles model storage, training runs, and prediction logging.
Note: Uses JSON instead of pickle for secure serialization.
"""

import json
import uuid

from django.db import models
from django.utils import timezone


class MLModel(models.Model):
    """
    Machine Learning model with FHE support.

    Parameters are serialized as JSON for security (no pickle).
    """

    class ModelType(models.TextChoices):
        LINEAR_REGRESSION = "linear_regression", "Linear Regression"
        LOGISTIC_REGRESSION = "logistic_regression", "Logistic Regression"
        DECISION_TREE = "decision_tree", "Decision Tree"
        KMEANS = "kmeans", "K-Means Clustering"

    class Status(models.TextChoices):
        CREATED = "created", "Created"
        TRAINING = "training", "Training"
        TRAINED = "trained", "Trained"
        FAILED = "failed", "Failed"
        ARCHIVED = "archived", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)

    # Type and configuration
    model_type = models.CharField(
        max_length=50,
        choices=ModelType.choices,
        db_index=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CREATED,
        db_index=True,
    )

    # Configuration (JSON, validated by serializer)
    config = models.JSONField(default=dict, blank=True)

    # Model parameters (JSON serialization, NOT pickle)
    # For complex numpy arrays, store as lists
    params = models.JSONField(default=dict, blank=True)

    # Feature information
    n_features = models.IntegerField(null=True, blank=True)
    feature_names = models.JSONField(default=list, blank=True)

    # Training info
    trained_at = models.DateTimeField(null=True, blank=True)
    training_epochs = models.IntegerField(null=True, blank=True)
    final_loss = models.FloatField(null=True, blank=True)

    # Association (optional - for consortium models)
    consortium = models.ForeignKey(
        "consortiums.Consortium",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="models",
    )
    owner = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="models",
        null=True,
        blank=True,
    )

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "ML model"
        verbose_name_plural = "ML models"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["model_type"]),
            models.Index(fields=["status"]),
            models.Index(fields=["consortium"]),
            models.Index(fields=["owner"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.model_type})"

    def set_params(self, params_dict):
        """
        Safely set model parameters.

        Converts numpy arrays to lists for JSON serialization.
        """
        import numpy as np

        def convert_to_serializable(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, (np.float32, np.float64)):
                return float(obj)
            elif isinstance(obj, (np.int32, np.int64)):
                return int(obj)
            elif isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(v) for v in obj]
            return obj

        self.params = convert_to_serializable(params_dict)

    def get_params(self):
        """
        Get model parameters, converting lists back to numpy arrays.
        """
        import numpy as np

        def convert_to_numpy(obj, key=None):
            if isinstance(obj, list) and obj and isinstance(obj[0], (int, float, list)):
                return np.array(obj)
            elif isinstance(obj, dict):
                return {k: convert_to_numpy(v, k) for k, v in obj.items()}
            return obj

        return convert_to_numpy(self.params)

    def mark_trained(self, epochs=None, loss=None, params=None):
        """Mark model as trained with results."""
        self.status = self.Status.TRAINED
        self.trained_at = timezone.now()
        if epochs is not None:
            self.training_epochs = epochs
        if loss is not None:
            self.final_loss = loss
        if params is not None:
            self.set_params(params)
        self.save()


class TrainingRun(models.Model):
    """
    Record of a model training run.
    """

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    model = models.ForeignKey(
        MLModel,
        on_delete=models.CASCADE,
        related_name="training_runs",
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.QUEUED,
        db_index=True,
    )

    # Training progress
    epochs_completed = models.IntegerField(default=0)
    epochs_total = models.IntegerField(null=True, blank=True)
    current_loss = models.FloatField(null=True, blank=True)
    final_loss = models.FloatField(null=True, blank=True)

    # Metrics (JSON)
    metrics = models.JSONField(default=dict, blank=True)

    # Error handling
    error_message = models.TextField(blank=True)

    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "training run"
        verbose_name_plural = "training runs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["model"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Training {self.model.name} ({self.status})"

    @property
    def duration_seconds(self):
        """Get training duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def start(self):
        """Mark training as started."""
        self.status = self.Status.RUNNING
        self.started_at = timezone.now()
        self.save(update_fields=["status", "started_at"])

    def complete(self, final_loss=None, metrics=None):
        """Mark training as completed."""
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        if final_loss is not None:
            self.final_loss = final_loss
        if metrics:
            self.metrics = metrics
        self.save()

    def fail(self, error_message):
        """Mark training as failed."""
        self.status = self.Status.FAILED
        self.completed_at = timezone.now()
        self.error_message = error_message
        self.save()


class PredictionLog(models.Model):
    """
    Log of prediction requests for monitoring and billing.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    model = models.ForeignKey(
        MLModel,
        on_delete=models.CASCADE,
        related_name="prediction_logs",
    )
    requester = models.ForeignKey(
        "core.Company",
        on_delete=models.SET_NULL,
        null=True,
        related_name="predictions",
    )

    # Request details
    n_samples = models.IntegerField()
    encrypted = models.BooleanField(default=False)
    latency_ms = models.FloatField()

    # API key used (name only, not the key itself)
    api_key_name = models.CharField(max_length=255, blank=True)

    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "prediction log"
        verbose_name_plural = "prediction logs"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["model"]),
            models.Index(fields=["requester"]),
            models.Index(fields=["timestamp"]),
            models.Index(fields=["encrypted"]),
        ]

    def __str__(self):
        return f"{self.n_samples} samples on {self.model.name}"


class ModelCheckpoint(models.Model):
    """
    Model checkpoint for federated learning rounds.

    Stores encrypted model weights after each training round.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    model = models.ForeignKey(
        MLModel,
        on_delete=models.CASCADE,
        related_name="checkpoints",
    )

    # Checkpoint info
    epoch = models.IntegerField()
    loss = models.FloatField(null=True, blank=True)

    # Encrypted weights (JSON, not pickle)
    weights_encrypted = models.JSONField(default=dict)

    # Hash for verification
    weights_hash = models.CharField(max_length=64)

    # Blockchain
    blockchain_tx = models.CharField(max_length=66, blank=True)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "model checkpoint"
        verbose_name_plural = "model checkpoints"
        unique_together = ["model", "epoch"]
        ordering = ["-epoch"]
        indexes = [
            models.Index(fields=["model", "epoch"]),
            models.Index(fields=["weights_hash"]),
        ]

    def __str__(self):
        return f"{self.model.name} - Epoch {self.epoch}"

"""
Ensemble models for Xcapit FHE-ML Platform.

Handles multi-model ensemble creation, aggregation, and predictions.
"""

import uuid

from django.db import models


class Ensemble(models.Model):
    """
    A multi-model ensemble that aggregates predictions from multiple models.
    """

    class EnsembleType(models.TextChoices):
        VOTING = "voting", "Voting (Majority)"
        AVERAGING = "averaging", "Averaging"
        WEIGHTED = "weighted", "Weighted Average"
        STACKING = "stacking", "Stacking"
        BOOSTING = "boosting", "Boosting"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        TRAINING = "training", "Training"
        DEPLOYED = "deployed", "Deployed"
        ARCHIVED = "archived", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Basic info
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Ownership
    owner = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="owned_ensembles",
    )

    # Configuration
    ensemble_type = models.CharField(
        max_length=20,
        choices=EnsembleType.choices,
        default=EnsembleType.VOTING,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )

    # Aggregation config (for weighted ensembles)
    aggregation_config = models.JSONField(default=dict, blank=True)

    # Performance metrics
    accuracy = models.FloatField(null=True, blank=True)
    f1_score = models.FloatField(null=True, blank=True)
    ensemble_improvement = models.FloatField(
        null=True,
        blank=True,
        help_text="Improvement over best single model (%)",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "ensemble"
        verbose_name_plural = "ensembles"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.ensemble_type})"

    @property
    def model_count(self):
        """Get number of models in ensemble."""
        return self.ensemble_models.count()


class EnsembleModel(models.Model):
    """
    A model that is part of an ensemble.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    ensemble = models.ForeignKey(
        Ensemble,
        on_delete=models.CASCADE,
        related_name="ensemble_models",
    )

    # Model reference
    model = models.ForeignKey(
        "models.MLModel",
        on_delete=models.CASCADE,
        related_name="ensemble_memberships",
    )

    # Weight (for weighted ensembles)
    weight = models.FloatField(default=1.0)

    # Performance contribution
    individual_accuracy = models.FloatField(null=True, blank=True)
    contribution_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Model's contribution to ensemble performance",
    )

    # Status
    is_active = models.BooleanField(default=True)

    # Timestamps
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "ensemble model"
        verbose_name_plural = "ensemble models"
        unique_together = ["ensemble", "model"]
        indexes = [
            models.Index(fields=["ensemble"]),
            models.Index(fields=["model"]),
        ]

    def __str__(self):
        return f"{self.model.name} in {self.ensemble.name}"


class EnsemblePrediction(models.Model):
    """
    A prediction made by an ensemble.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    ensemble = models.ForeignKey(
        Ensemble,
        on_delete=models.CASCADE,
        related_name="predictions",
    )

    # Request info
    requester = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="ensemble_predictions",
    )

    # Input/Output
    input_hash = models.CharField(max_length=64)  # Hash of input data
    n_samples = models.IntegerField()

    # Aggregated prediction
    prediction = models.JSONField()  # Aggregated result
    confidence = models.FloatField(null=True, blank=True)

    # Individual model predictions (for transparency)
    model_predictions = models.JSONField(default=dict)

    # Performance
    latency_ms = models.FloatField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "ensemble prediction"
        verbose_name_plural = "ensemble predictions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["ensemble"]),
            models.Index(fields=["requester"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Prediction by {self.ensemble.name} ({self.n_samples} samples)"


class EnsembleEvaluation(models.Model):
    """
    Evaluation results for an ensemble.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    ensemble = models.ForeignKey(
        Ensemble,
        on_delete=models.CASCADE,
        related_name="evaluations",
    )

    # Evaluation metrics
    accuracy = models.FloatField()
    precision = models.FloatField(null=True, blank=True)
    recall = models.FloatField(null=True, blank=True)
    f1_score = models.FloatField(null=True, blank=True)
    auc_roc = models.FloatField(null=True, blank=True)

    # Comparison with individual models
    best_individual_accuracy = models.FloatField()
    improvement_over_best = models.FloatField()

    # Dataset info
    test_samples = models.IntegerField()
    test_data_hash = models.CharField(max_length=64)

    # Timestamps
    evaluated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "ensemble evaluation"
        verbose_name_plural = "ensemble evaluations"
        ordering = ["-evaluated_at"]

    def __str__(self):
        return f"Evaluation of {self.ensemble.name}: {self.accuracy:.2%}"

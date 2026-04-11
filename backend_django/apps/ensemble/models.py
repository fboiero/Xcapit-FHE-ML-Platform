"""
Ensemble models for Xcapit FHE-ML Platform.

Modelos de ensamble, sus componentes individuales,
predicciones y evaluaciones de rendimiento.
"""

import uuid

from django.db import models


class Ensemble(models.Model):
    """Modelo de ensamble compuesto por múltiples modelos base."""

    class EnsembleType(models.TextChoices):
        BAGGING = "bagging", "Bagging"
        BOOSTING = "boosting", "Boosting"
        STACKING = "stacking", "Stacking"
        VOTING = "voting", "Voting"
        WEIGHTED = "weighted", "Weighted"
        CUSTOM = "custom", "Custom"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        TRAINING = "training", "Training"
        READY = "ready", "Ready"
        ARCHIVED = "archived", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    owner = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="ensembles",
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
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
    aggregation_config = models.JSONField(default=dict, blank=True)

    accuracy = models.DecimalField(
        max_digits=7, decimal_places=4, null=True, blank=True
    )
    f1_score = models.DecimalField(
        max_digits=7, decimal_places=4, null=True, blank=True
    )
    ensemble_improvement = models.DecimalField(
        max_digits=7, decimal_places=4, null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "ensemble"
        verbose_name_plural = "ensembles"
        indexes = [
            models.Index(fields=["owner", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.ensemble_type} / {self.status})"

    @property
    def model_count(self) -> int:
        """Cantidad de modelos activos en el ensamble."""
        return self.ensemble_models.filter(is_active=True).count()


class EnsembleModel(models.Model):
    """Modelo individual dentro de un ensamble."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    ensemble = models.ForeignKey(
        Ensemble,
        on_delete=models.CASCADE,
        related_name="ensemble_models",
    )
    model = models.ForeignKey(
        "models.MLModel",
        on_delete=models.SET_NULL,
        related_name="ensemble_memberships",
        null=True,
        blank=True,
    )

    weight = models.DecimalField(max_digits=7, decimal_places=4, default=1.0)
    individual_accuracy = models.DecimalField(
        max_digits=7, decimal_places=4, null=True, blank=True
    )
    contribution_score = models.DecimalField(
        max_digits=7, decimal_places=4, null=True, blank=True
    )
    is_active = models.BooleanField(default=True, db_index=True)

    added_at = models.DateTimeField(auto_now_add=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "ensemble model"
        verbose_name_plural = "ensemble models"
        unique_together = [("ensemble", "model")]
        indexes = [
            models.Index(fields=["ensemble", "is_active"]),
        ]

    def __str__(self) -> str:
        model_name = self.model.name if self.model else "unknown"
        return f"{model_name} in {self.ensemble.name} (w={self.weight})"


class EnsemblePrediction(models.Model):
    """Solicitud y resultado de predicción del ensamble."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    ensemble = models.ForeignKey(
        Ensemble,
        on_delete=models.CASCADE,
        related_name="predictions",
    )
    requester = models.ForeignKey(
        "core.Company",
        on_delete=models.SET_NULL,
        related_name="ensemble_predictions",
        null=True,
        blank=True,
    )

    input_hash = models.CharField(max_length=66, blank=True)
    n_samples = models.IntegerField(default=0)
    prediction = models.JSONField(default=dict, blank=True)
    confidence = models.DecimalField(
        max_digits=7, decimal_places=4, null=True, blank=True
    )
    model_predictions = models.JSONField(default=dict, blank=True)
    latency_ms = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "ensemble prediction"
        verbose_name_plural = "ensemble predictions"
        indexes = [
            models.Index(fields=["ensemble"]),
        ]

    def __str__(self) -> str:
        return f"Prediction — {self.ensemble.name} ({self.n_samples} samples)"


class EnsembleEvaluation(models.Model):
    """Evaluación de rendimiento del ensamble."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    ensemble = models.ForeignKey(
        Ensemble,
        on_delete=models.CASCADE,
        related_name="evaluations",
    )

    accuracy = models.DecimalField(
        max_digits=7, decimal_places=4, null=True, blank=True
    )
    precision = models.DecimalField(
        max_digits=7, decimal_places=4, null=True, blank=True
    )
    recall = models.DecimalField(
        max_digits=7, decimal_places=4, null=True, blank=True
    )
    f1_score = models.DecimalField(
        max_digits=7, decimal_places=4, null=True, blank=True
    )
    auc_roc = models.DecimalField(
        max_digits=7, decimal_places=4, null=True, blank=True
    )
    best_individual_accuracy = models.DecimalField(
        max_digits=7, decimal_places=4, null=True, blank=True
    )
    improvement_over_best = models.DecimalField(
        max_digits=7, decimal_places=4, null=True, blank=True
    )
    test_samples = models.IntegerField(null=True, blank=True)
    test_data_hash = models.CharField(max_length=66, blank=True)

    evaluated_at = models.DateTimeField(auto_now_add=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "ensemble evaluation"
        verbose_name_plural = "ensemble evaluations"
        indexes = [
            models.Index(fields=["ensemble"]),
        ]

    def __str__(self) -> str:
        return f"Evaluation — {self.ensemble.name} (acc={self.accuracy})"

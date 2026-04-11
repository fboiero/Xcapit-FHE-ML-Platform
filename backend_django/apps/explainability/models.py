"""
Explainability models for Xcapit FHE-ML Platform.

Solicitudes de explicabilidad, importancia de features e
insights generados automáticamente sobre los modelos.
"""

import uuid

from django.db import models


class ExplanationRequest(models.Model):
    """Solicitud de explicación de un modelo."""

    class ExplanationType(models.TextChoices):
        FEATURE_IMPORTANCE = "feature_importance", "Feature Importance"
        SHAP = "shap", "SHAP"
        LIME = "lime", "LIME"
        COUNTERFACTUAL = "counterfactual", "Counterfactual"
        PARTIAL_DEPENDENCE = "partial_dependence", "Partial Dependence"
        ANCHOR = "anchor", "Anchor"
        DECISION_PATH = "decision_path", "Decision Path"
        SUMMARY = "summary", "Summary"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    consortium = models.ForeignKey(
        "consortiums.Consortium",
        on_delete=models.CASCADE,
        related_name="explanation_requests",
    )
    requester = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="explanation_requests",
    )
    model = models.ForeignKey(
        "models.MLModel",
        on_delete=models.SET_NULL,
        related_name="explanation_requests",
        null=True,
        blank=True,
    )

    explanation_type = models.CharField(
        max_length=30,
        choices=ExplanationType.choices,
    )
    input_data = models.JSONField(null=True, blank=True)
    prediction_id = models.CharField(max_length=255, blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    error_message = models.TextField(blank=True)
    explanation = models.JSONField(null=True, blank=True)

    completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "explanation request"
        verbose_name_plural = "explanation requests"
        indexes = [
            models.Index(fields=["consortium", "status"]),
            models.Index(fields=["requester"]),
        ]

    def __str__(self) -> str:
        return f"{self.explanation_type} — {self.status}"

    def mark_completed(self, explanation: dict) -> None:
        """Mark this explanation request as completed."""
        from django.utils import timezone as tz

        self.status = self.Status.COMPLETED
        self.explanation = explanation
        self.completed_at = tz.now()
        self.save(update_fields=["status", "explanation", "completed_at", "updated_at"])

    def mark_failed(self, error_message: str) -> None:
        """Mark this explanation request as failed."""
        from django.utils import timezone as tz

        self.status = self.Status.FAILED
        self.error_message = error_message
        self.completed_at = tz.now()
        self.save(update_fields=["status", "error_message", "completed_at", "updated_at"])


class FeatureImportance(models.Model):
    """Resultado de importancia de feature para un modelo."""

    class ComputationMethod(models.TextChoices):
        PERMUTATION = "permutation", "Permutation"
        SHAP = "shap", "SHAP"
        GAIN = "gain", "Gain"
        SPLIT = "split", "Split"
        CORRELATION = "correlation", "Correlation"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    consortium = models.ForeignKey(
        "consortiums.Consortium",
        on_delete=models.CASCADE,
        related_name="feature_importances",
    )
    model = models.ForeignKey(
        "models.MLModel",
        on_delete=models.SET_NULL,
        related_name="feature_importances",
        null=True,
        blank=True,
    )

    feature_name = models.CharField(max_length=255)
    importance_score = models.DecimalField(max_digits=10, decimal_places=6)
    importance_rank = models.IntegerField()
    computation_method = models.CharField(
        max_length=20,
        choices=ComputationMethod.choices,
        default=ComputationMethod.PERMUTATION,
    )
    std_deviation = models.DecimalField(
        max_digits=10, decimal_places=6, null=True, blank=True
    )

    computed_at = models.DateTimeField(auto_now_add=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["importance_rank"]
        verbose_name = "feature importance"
        verbose_name_plural = "feature importances"
        indexes = [
            models.Index(fields=["consortium", "model"]),
            models.Index(fields=["importance_rank"]),
        ]

    def __str__(self) -> str:
        return f"{self.feature_name} — rank {self.importance_rank} ({self.importance_score})"


class ModelInsight(models.Model):
    """Insight generado automáticamente sobre el comportamiento de un modelo."""

    class InsightType(models.TextChoices):
        DRIFT = "drift", "Drift"
        PERFORMANCE = "performance", "Performance"
        FAIRNESS = "fairness", "Fairness"
        FEATURE = "feature", "Feature"
        DATA_QUALITY = "data_quality", "Data Quality"

    class Severity(models.TextChoices):
        INFO = "info", "Info"
        WARNING = "warning", "Warning"
        CRITICAL = "critical", "Critical"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    consortium = models.ForeignKey(
        "consortiums.Consortium",
        on_delete=models.CASCADE,
        related_name="model_insights",
    )

    insight_type = models.CharField(
        max_length=20,
        choices=InsightType.choices,
        db_index=True,
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    severity = models.CharField(
        max_length=10,
        choices=Severity.choices,
        default=Severity.INFO,
    )

    data = models.JSONField(default=dict, blank=True)
    recommendations = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(
        "core.User",
        on_delete=models.SET_NULL,
        related_name="acknowledged_insights",
        null=True,
        blank=True,
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "model insight"
        verbose_name_plural = "model insights"
        indexes = [
            models.Index(fields=["consortium", "insight_type"]),
            models.Index(fields=["severity", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"[{self.severity}] {self.title}"

    def acknowledge(self, user) -> None:
        """Mark this insight as acknowledged by *user*."""
        from django.utils import timezone as tz

        self.acknowledged = True
        self.acknowledged_by = user
        self.acknowledged_at = tz.now()
        self.save(
            update_fields=["acknowledged", "acknowledged_by", "acknowledged_at", "updated_at"]
        )

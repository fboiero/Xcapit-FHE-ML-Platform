"""
Explainability models for Xcapit FHE-ML Platform.

Handles explanation requests, feature importance, and model insights.
"""

import uuid

from django.db import models
from django.utils import timezone


class ExplanationRequest(models.Model):
    """
    Request for model explanation.

    Supports various explanation types: SHAP, feature importance,
    decision paths, and counterfactuals.
    """

    class ExplanationType(models.TextChoices):
        FEATURE_IMPORTANCE = "feature_importance", "Feature Importance"
        SHAP = "shap", "SHAP Values"
        DECISION_PATH = "decision_path", "Decision Path"
        COUNTERFACTUAL = "counterfactual", "Counterfactual"
        SUMMARY = "summary", "Model Summary"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Associations
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
        on_delete=models.CASCADE,
        related_name="explanation_requests",
        null=True,
        blank=True,
    )

    # Request configuration
    explanation_type = models.CharField(
        max_length=20,
        choices=ExplanationType.choices,
        default=ExplanationType.FEATURE_IMPORTANCE,
    )
    input_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Input data for instance-level explanations",
    )
    prediction_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Reference to specific prediction to explain",
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    error_message = models.TextField(blank=True)

    # Results
    explanation = models.JSONField(default=dict, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "explanation request"
        verbose_name_plural = "explanation requests"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["consortium"]),
            models.Index(fields=["requester"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.explanation_type} for {self.consortium.name}"

    def mark_completed(self, explanation):
        """Mark request as completed with results."""
        self.status = self.Status.COMPLETED
        self.explanation = explanation
        self.completed_at = timezone.now()
        self.save()

    def mark_failed(self, error_message):
        """Mark request as failed with error."""
        self.status = self.Status.FAILED
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.save()


class FeatureImportance(models.Model):
    """
    Feature importance scores for a model.

    Stores global feature importance computed across the training data.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Associations
    consortium = models.ForeignKey(
        "consortiums.Consortium",
        on_delete=models.CASCADE,
        related_name="feature_importances",
    )
    model = models.ForeignKey(
        "models.MLModel",
        on_delete=models.CASCADE,
        related_name="feature_importances",
        null=True,
        blank=True,
    )

    # Feature data
    feature_name = models.CharField(max_length=255)
    importance_score = models.FloatField()
    importance_rank = models.IntegerField()

    # Computation method
    computation_method = models.CharField(
        max_length=50,
        default="model_native",
        help_text="Method used: model_native, permutation, shap",
    )

    # Additional metrics
    std_deviation = models.FloatField(
        null=True,
        blank=True,
        help_text="Standard deviation of importance across folds",
    )

    # Timestamps
    computed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "feature importance"
        verbose_name_plural = "feature importances"
        ordering = ["importance_rank"]
        indexes = [
            models.Index(fields=["consortium"]),
            models.Index(fields=["importance_rank"]),
        ]

    def __str__(self):
        return f"{self.feature_name}: {self.importance_score:.4f}"


class ModelInsight(models.Model):
    """
    Aggregated model insight for a consortium.

    Provides high-level understanding of model behavior without
    exposing individual company data.
    """

    class InsightType(models.TextChoices):
        PERFORMANCE = "performance", "Performance Insight"
        FEATURE = "feature", "Feature Insight"
        BIAS = "bias", "Bias Detection"
        DRIFT = "drift", "Data Drift"
        ANOMALY = "anomaly", "Anomaly Detection"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Association
    consortium = models.ForeignKey(
        "consortiums.Consortium",
        on_delete=models.CASCADE,
        related_name="model_insights",
    )

    # Insight details
    insight_type = models.CharField(
        max_length=20,
        choices=InsightType.choices,
    )
    title = models.CharField(max_length=255)
    description = models.TextField()

    # Severity/Importance
    severity = models.CharField(
        max_length=20,
        choices=[
            ("info", "Info"),
            ("warning", "Warning"),
            ("critical", "Critical"),
        ],
        default="info",
    )

    # Supporting data (anonymized)
    data = models.JSONField(default=dict)

    # Actionable recommendations
    recommendations = models.JSONField(default=list)

    # Status
    is_active = models.BooleanField(default=True)
    acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(
        "core.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "model insight"
        verbose_name_plural = "model insights"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["consortium"]),
            models.Index(fields=["insight_type"]),
            models.Index(fields=["severity"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.insight_type})"

    def acknowledge(self, user):
        """Mark insight as acknowledged."""
        self.acknowledged = True
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.save()

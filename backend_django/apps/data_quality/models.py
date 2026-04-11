"""
Data quality models for Xcapit FHE-ML Platform.

Evaluaciones de calidad de datos, reglas de validación y alertas
para garantizar la integridad de las contribuciones al consorcio.
"""

import uuid

from django.db import models
from django.utils import timezone


class QualityAssessment(models.Model):
    """Evaluación de calidad de datos de una contribución."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    consortium = models.ForeignKey(
        "consortiums.Consortium",
        on_delete=models.CASCADE,
        related_name="quality_assessments",
    )
    company = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="quality_assessments",
    )
    contribution = models.ForeignKey(
        "consortiums.ContributionProof",
        on_delete=models.SET_NULL,
        related_name="quality_assessments",
        null=True,
        blank=True,
    )

    record_count = models.IntegerField(default=0)
    feature_count = models.IntegerField(default=0)

    # Issue counts
    null_count = models.IntegerField(default=0)
    duplicate_count = models.IntegerField(default=0)
    outlier_count = models.IntegerField(default=0)
    schema_violations = models.IntegerField(default=0)
    format_violations = models.IntegerField(default=0)
    range_violations = models.IntegerField(default=0)

    # Scores (0-100)
    completeness_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    consistency_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    accuracy_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    timeliness_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    overall_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    last_assessed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "quality assessment"
        verbose_name_plural = "quality assessments"
        indexes = [
            models.Index(fields=["consortium", "company"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"Assessment — {self.company.name} ({self.overall_score or 'N/A'})"

    def calculate_scores(self) -> None:
        """Calcula los puntajes de calidad basados en las métricas de problemas."""
        if self.record_count == 0:
            self.completeness_score = 0
            self.consistency_score = 0
            self.accuracy_score = 0
            self.timeliness_score = 0
            self.overall_score = 0
            self.status = self.Status.COMPLETED
            self.last_assessed_at = timezone.now()
            self.save(
                update_fields=[
                    "completeness_score",
                    "consistency_score",
                    "accuracy_score",
                    "timeliness_score",
                    "overall_score",
                    "status",
                    "last_assessed_at",
                ]
            )
            return

        total = self.record_count

        # Completeness: based on null count
        self.completeness_score = max(
            0, round(100 * (1 - self.null_count / total), 2)
        )

        # Consistency: based on schema + format violations
        violation_count = self.schema_violations + self.format_violations
        self.consistency_score = max(
            0, round(100 * (1 - violation_count / total), 2)
        )

        # Accuracy: based on range violations + outliers
        issue_count = self.range_violations + self.outlier_count
        self.accuracy_score = max(
            0, round(100 * (1 - issue_count / total), 2)
        )

        # Timeliness: based on duplicates (proxy)
        self.timeliness_score = max(
            0, round(100 * (1 - self.duplicate_count / total), 2)
        )

        # Overall: weighted average
        scores = [
            self.completeness_score,
            self.consistency_score,
            self.accuracy_score,
            self.timeliness_score,
        ]
        self.overall_score = round(sum(scores) / len(scores), 2)
        self.status = self.Status.COMPLETED
        self.last_assessed_at = timezone.now()
        self.save(
            update_fields=[
                "completeness_score",
                "consistency_score",
                "accuracy_score",
                "timeliness_score",
                "overall_score",
                "status",
                "last_assessed_at",
            ]
        )


class QualityRule(models.Model):
    """Regla de validación de calidad de datos."""

    class RuleType(models.TextChoices):
        COMPLETENESS = "completeness", "Completeness"
        RANGE = "range", "Range"
        FORMAT = "format", "Format"
        UNIQUENESS = "uniqueness", "Uniqueness"
        REFERENTIAL = "referential", "Referential"
        THRESHOLD = "threshold", "Threshold"
        CUSTOM = "custom", "Custom"

    class Severity(models.TextChoices):
        INFO = "info", "Info"
        WARNING = "warning", "Warning"
        ERROR = "error", "Error"
        CRITICAL = "critical", "Critical"

    class Condition(models.TextChoices):
        GREATER_THAN = "gt", "Greater Than"
        LESS_THAN = "lt", "Less Than"
        EQUAL = "eq", "Equal"
        NOT_EQUAL = "ne", "Not Equal"
        BETWEEN = "between", "Between"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    consortium = models.ForeignKey(
        "consortiums.Consortium",
        on_delete=models.CASCADE,
        related_name="quality_rules",
        null=True,
        blank=True,
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    rule_type = models.CharField(max_length=20, choices=RuleType.choices)
    metric = models.CharField(max_length=100, blank=True)
    condition = models.JSONField(
        default=dict,
        help_text="Condition dict with 'operator' and 'value' keys, e.g. {'operator': '>=', 'value': 80}",
    )
    severity = models.CharField(
        max_length=10,
        choices=Severity.choices,
        default=Severity.WARNING,
    )
    is_active = models.BooleanField(default=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "quality rule"
        verbose_name_plural = "quality rules"
        indexes = [
            models.Index(fields=["consortium", "is_active"]),
            models.Index(fields=["rule_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.rule_type} / {self.severity})"


class QualityAlert(models.Model):
    """Alerta disparada por una regla de calidad."""

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        ACKNOWLEDGED = "acknowledged", "Acknowledged"
        RESOLVED = "resolved", "Resolved"
        DISMISSED = "dismissed", "Dismissed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    rule = models.ForeignKey(
        QualityRule,
        on_delete=models.CASCADE,
        related_name="alerts",
    )
    assessment = models.ForeignKey(
        QualityAssessment,
        on_delete=models.SET_NULL,
        related_name="alerts",
        null=True,
        blank=True,
    )
    company = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="quality_alerts",
    )

    message = models.TextField()
    actual_value = models.CharField(max_length=255, blank=True)
    expected_value = models.CharField(max_length=255, blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
        db_index=True,
    )

    resolved_by = models.ForeignKey(
        "core.User",
        on_delete=models.SET_NULL,
        related_name="resolved_quality_alerts",
        null=True,
        blank=True,
    )
    resolution_note = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "quality alert"
        verbose_name_plural = "quality alerts"
        indexes = [
            models.Index(fields=["rule", "status"]),
            models.Index(fields=["company"]),
        ]

    def __str__(self) -> str:
        return f"Alert — {self.rule.name}: {self.message[:60]}"

    def resolve(self, resolved_by, resolution_note: str = "") -> None:
        """Mark this alert as resolved."""
        self.status = self.Status.RESOLVED
        self.resolved_by = resolved_by
        self.resolution_note = resolution_note
        self.resolved_at = timezone.now()
        self.save(
            update_fields=[
                "status",
                "resolved_by",
                "resolution_note",
                "resolved_at",
                "updated_at",
            ]
        )

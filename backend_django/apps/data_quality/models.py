"""
Data quality models for Xcapit FHE-ML Platform.

Handles quality assessments, rules, and alerts for consortium data.
"""

import uuid

from django.db import models
from django.utils import timezone


class QualityAssessment(models.Model):
    """
    Assessment of data quality for a contribution.

    Evaluates encrypted data metadata without accessing actual content.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Associations
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
        on_delete=models.CASCADE,
        related_name="quality_assessments",
        null=True,
        blank=True,
    )

    # Input metrics
    record_count = models.IntegerField(default=0)
    feature_count = models.IntegerField(default=0)
    null_count = models.IntegerField(default=0)
    duplicate_count = models.IntegerField(default=0)
    outlier_count = models.IntegerField(default=0)
    schema_violations = models.IntegerField(default=0)
    format_violations = models.IntegerField(default=0)
    range_violations = models.IntegerField(default=0)

    # Calculated scores (0-100)
    completeness_score = models.FloatField(default=0)
    consistency_score = models.FloatField(default=0)
    accuracy_score = models.FloatField(default=0)
    timeliness_score = models.FloatField(default=0)
    overall_score = models.FloatField(default=0)

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_assessed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "quality assessment"
        verbose_name_plural = "quality assessments"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["consortium", "company"]),
            models.Index(fields=["status"]),
            models.Index(fields=["overall_score"]),
        ]

    def __str__(self):
        return f"Assessment for {self.company.name} - Score: {self.overall_score:.1f}"

    def calculate_scores(self):
        """Calculate quality scores from input metrics."""
        # Completeness: based on null values
        if self.record_count > 0:
            total_cells = self.record_count * max(self.feature_count, 1)
            self.completeness_score = max(0, 100 - (self.null_count / total_cells * 100))
        else:
            self.completeness_score = 0

        # Consistency: based on schema and format violations
        if self.record_count > 0:
            violation_rate = (self.schema_violations + self.format_violations) / self.record_count
            self.consistency_score = max(0, 100 - violation_rate * 100)
        else:
            self.consistency_score = 0

        # Accuracy: based on outliers and range violations
        if self.record_count > 0:
            error_rate = (self.outlier_count + self.range_violations) / self.record_count
            self.accuracy_score = max(0, 100 - error_rate * 100)
        else:
            self.accuracy_score = 0

        # Timeliness: based on duplicates (assuming duplicates indicate stale data)
        if self.record_count > 0:
            duplicate_rate = self.duplicate_count / self.record_count
            self.timeliness_score = max(0, 100 - duplicate_rate * 100)
        else:
            self.timeliness_score = 0

        # Overall: weighted average
        self.overall_score = (
            self.completeness_score * 0.3
            + self.consistency_score * 0.25
            + self.accuracy_score * 0.25
            + self.timeliness_score * 0.2
        )

        self.status = self.Status.COMPLETED
        self.last_assessed_at = timezone.now()
        self.save()


class QualityRule(models.Model):
    """
    Quality rule for validating data contributions.
    """

    class RuleType(models.TextChoices):
        THRESHOLD = "threshold", "Threshold"
        RANGE = "range", "Range"
        PATTERN = "pattern", "Pattern"
        CUSTOM = "custom", "Custom"

    class Severity(models.TextChoices):
        INFO = "info", "Info"
        WARNING = "warning", "Warning"
        ERROR = "error", "Error"
        CRITICAL = "critical", "Critical"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Association
    consortium = models.ForeignKey(
        "consortiums.Consortium",
        on_delete=models.CASCADE,
        related_name="quality_rules",
    )

    # Rule definition
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    rule_type = models.CharField(
        max_length=20,
        choices=RuleType.choices,
        default=RuleType.THRESHOLD,
    )
    metric = models.CharField(max_length=100)  # e.g., "completeness_score"
    condition = models.JSONField(default=dict)  # e.g., {"operator": ">=", "value": 80}

    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        default=Severity.WARNING,
    )

    # Status
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "quality rule"
        verbose_name_plural = "quality rules"
        indexes = [
            models.Index(fields=["consortium"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.severity})"


class QualityAlert(models.Model):
    """
    Alert generated when a quality rule is violated.
    """

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        ACKNOWLEDGED = "acknowledged", "Acknowledged"
        RESOLVED = "resolved", "Resolved"
        IGNORED = "ignored", "Ignored"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Associations
    rule = models.ForeignKey(
        QualityRule,
        on_delete=models.CASCADE,
        related_name="alerts",
    )
    assessment = models.ForeignKey(
        QualityAssessment,
        on_delete=models.CASCADE,
        related_name="alerts",
    )
    company = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="quality_alerts",
    )

    # Alert details
    message = models.TextField()
    actual_value = models.FloatField(null=True, blank=True)
    expected_value = models.CharField(max_length=255, blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
        db_index=True,
    )

    # Resolution
    resolved_by = models.ForeignKey(
        "core.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_alerts",
    )
    resolution_note = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "quality alert"
        verbose_name_plural = "quality alerts"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["company"]),
        ]

    def __str__(self):
        return f"Alert: {self.rule.name} - {self.status}"

    def resolve(self, user, note=""):
        """Mark alert as resolved."""
        self.status = self.Status.RESOLVED
        self.resolved_by = user
        self.resolution_note = note
        self.resolved_at = timezone.now()
        self.save()

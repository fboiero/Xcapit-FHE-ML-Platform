"""
Competitive insights models for Xcapit FHE-ML Platform.

Handles industry benchmarks and anonymized competitive analysis.
"""

import uuid

from django.db import models


class IndustryBenchmark(models.Model):
    """
    Anonymized industry benchmark for competitive comparison.

    Stores aggregated metrics across multiple companies without
    exposing individual company data.
    """

    class MetricType(models.TextChoices):
        ACCURACY = "accuracy", "Accuracy"
        PERFORMANCE = "performance", "Performance"
        EFFICIENCY = "efficiency", "Efficiency"
        QUALITY = "quality", "Quality"
        GROWTH = "growth", "Growth"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Industry classification
    industry = models.CharField(max_length=100, db_index=True)
    sub_industry = models.CharField(max_length=100, blank=True)

    # Metric definition
    metric_name = models.CharField(max_length=100)
    metric_type = models.CharField(
        max_length=20,
        choices=MetricType.choices,
        default=MetricType.PERFORMANCE,
    )
    unit = models.CharField(max_length=50, blank=True)  # e.g., "%", "ms", "count"

    # Benchmark values (percentiles)
    p10_value = models.FloatField(help_text="10th percentile")
    p25_value = models.FloatField(help_text="25th percentile")
    p50_value = models.FloatField(help_text="Median (50th percentile)")
    p75_value = models.FloatField(help_text="75th percentile")
    p90_value = models.FloatField(help_text="90th percentile")

    # Sample info (anonymized)
    sample_size = models.IntegerField(help_text="Number of companies in sample")

    # Validity period
    period_start = models.DateField()
    period_end = models.DateField()
    valid_until = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "industry benchmark"
        verbose_name_plural = "industry benchmarks"
        ordering = ["-period_start"]
        indexes = [
            models.Index(fields=["industry"]),
            models.Index(fields=["metric_name"]),
            models.Index(fields=["period_start", "period_end"]),
        ]
        unique_together = ["industry", "metric_name", "period_start"]

    def __str__(self):
        return f"{self.industry} - {self.metric_name} ({self.period_start})"

    def get_percentile_rank(self, value):
        """Get percentile rank for a given value."""
        if value <= self.p10_value:
            return 10
        elif value <= self.p25_value:
            return 25
        elif value <= self.p50_value:
            return 50
        elif value <= self.p75_value:
            return 75
        elif value <= self.p90_value:
            return 90
        else:
            return 95


class CompanyMetric(models.Model):
    """
    Company-specific metric for competitive comparison.

    Stores company metrics that can be compared against industry benchmarks.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Associations
    company = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="competitive_metrics",
    )
    benchmark = models.ForeignKey(
        IndustryBenchmark,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="company_metrics",
    )

    # Metric data
    metric_name = models.CharField(max_length=100)
    value = models.FloatField()

    # Calculated position
    percentile_rank = models.FloatField(null=True, blank=True)

    # Period
    period_start = models.DateField()
    period_end = models.DateField()

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "company metric"
        verbose_name_plural = "company metrics"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["company"]),
            models.Index(fields=["metric_name"]),
            models.Index(fields=["period_start"]),
        ]

    def __str__(self):
        return f"{self.company.name} - {self.metric_name}: {self.value}"

    def calculate_percentile(self):
        """Calculate percentile rank against industry benchmark."""
        if self.benchmark:
            self.percentile_rank = self.benchmark.get_percentile_rank(self.value)
            self.save(update_fields=["percentile_rank"])


class CompetitiveReport(models.Model):
    """
    Competitive analysis report for a company.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        GENERATING = "generating", "Generating"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Association
    company = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="competitive_reports",
    )

    # Report details
    title = models.CharField(max_length=255)
    industry = models.CharField(max_length=100)
    period_start = models.DateField()
    period_end = models.DateField()

    # Analysis results (JSON)
    summary = models.JSONField(default=dict)
    strengths = models.JSONField(default=list)
    weaknesses = models.JSONField(default=list)
    opportunities = models.JSONField(default=list)
    recommendations = models.JSONField(default=list)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "competitive report"
        verbose_name_plural = "competitive reports"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.company.name} - {self.title}"

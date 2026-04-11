"""
Competitive insights models for Xcapit FHE-ML Platform.

Benchmarks de industria, métricas de empresa y reportes
comparativos para posicionamiento competitivo.
"""

import uuid
from decimal import Decimal

from django.db import models


class IndustryBenchmark(models.Model):
    """Benchmark a nivel de industria para comparación."""

    class MetricType(models.TextChoices):
        ACCURACY = "accuracy", "Accuracy"
        LATENCY = "latency", "Latency"
        COST = "cost", "Cost"
        THROUGHPUT = "throughput", "Throughput"
        PRIVACY_SCORE = "privacy_score", "Privacy Score"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    industry = models.CharField(max_length=100, db_index=True)
    sub_industry = models.CharField(max_length=100, blank=True)
    metric_name = models.CharField(max_length=100)
    metric_type = models.CharField(
        max_length=20,
        choices=MetricType.choices,
    )
    unit = models.CharField(max_length=50, blank=True)

    p10_value = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True
    )
    p25_value = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True
    )
    p50_value = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True
    )
    p75_value = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True
    )
    p90_value = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True
    )

    sample_size = models.IntegerField(default=0)
    period_start = models.DateField()
    period_end = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "industry benchmark"
        verbose_name_plural = "industry benchmarks"
        unique_together = [("industry", "metric_name", "period_start")]
        indexes = [
            models.Index(fields=["industry", "metric_name"]),
            models.Index(fields=["period_start", "period_end"]),
        ]

    def __str__(self) -> str:
        return f"{self.industry} — {self.metric_name} ({self.period_start}–{self.period_end})"

    def get_percentile_rank(self, value: float) -> int:
        """Return the approximate percentile rank (10-95) for *value*."""
        from decimal import Decimal

        val = Decimal(str(value))
        if self.p90_value is not None and val >= self.p90_value:
            return 95
        if self.p75_value is not None and val >= self.p75_value:
            return 75
        if self.p50_value is not None and val >= self.p50_value:
            return 50
        if self.p25_value is not None and val >= self.p25_value:
            return 25
        return 10


class CompanyMetric(models.Model):
    """Métrica individual de una empresa para comparación con benchmarks."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    company = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="competitive_metrics",
    )
    benchmark = models.ForeignKey(
        IndustryBenchmark,
        on_delete=models.SET_NULL,
        related_name="company_metrics",
        null=True,
        blank=True,
    )

    metric_name = models.CharField(max_length=100)
    value = models.DecimalField(max_digits=12, decimal_places=4)
    percentile_rank = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    period_start = models.DateField()
    period_end = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "company metric"
        verbose_name_plural = "company metrics"
        indexes = [
            models.Index(fields=["company", "metric_name"]),
            models.Index(fields=["benchmark"]),
        ]

    def __str__(self) -> str:
        return f"{self.company.name} — {self.metric_name}: {self.value}"

    def calculate_percentile(self) -> None:
        """Calcula el percentil de la empresa según el benchmark asociado."""
        if not self.benchmark:
            return

        bm = self.benchmark
        percentile_map = [
            (bm.p10_value, Decimal("10")),
            (bm.p25_value, Decimal("25")),
            (bm.p50_value, Decimal("50")),
            (bm.p75_value, Decimal("75")),
            (bm.p90_value, Decimal("90")),
        ]

        self.percentile_rank = Decimal("0")
        for threshold, pct in percentile_map:
            if threshold is not None and self.value >= threshold:
                self.percentile_rank = pct

        self.save(update_fields=["percentile_rank"])


class CompetitiveReport(models.Model):
    """Reporte comparativo generado para una empresa."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        GENERATING = "generating", "Generating"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    company = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="competitive_reports",
    )

    title = models.CharField(max_length=255)
    industry = models.CharField(max_length=100)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)

    summary = models.JSONField(default=dict, blank=True)
    strengths = models.JSONField(default=list, blank=True)
    weaknesses = models.JSONField(default=list, blank=True)
    opportunities = models.JSONField(default=list, blank=True)
    recommendations = models.JSONField(default=list, blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.GENERATING,
        db_index=True,
    )

    completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "competitive report"
        verbose_name_plural = "competitive reports"
        indexes = [
            models.Index(fields=["company", "industry"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} — {self.company.name} ({self.status})"

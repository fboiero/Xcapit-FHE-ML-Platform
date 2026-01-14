"""
Competitive insights admin configuration.
"""

from django.contrib import admin

from .models import CompanyMetric, CompetitiveReport, IndustryBenchmark


@admin.register(IndustryBenchmark)
class IndustryBenchmarkAdmin(admin.ModelAdmin):
    """Admin for IndustryBenchmark model."""

    list_display = [
        "industry",
        "metric_name",
        "metric_type",
        "p50_value",
        "sample_size",
        "period_start",
    ]
    list_filter = ["industry", "metric_type"]
    search_fields = ["industry", "metric_name"]


@admin.register(CompanyMetric)
class CompanyMetricAdmin(admin.ModelAdmin):
    """Admin for CompanyMetric model."""

    list_display = [
        "company",
        "metric_name",
        "value",
        "percentile_rank",
        "period_start",
    ]
    list_filter = ["metric_name", "period_start"]
    search_fields = ["company__name", "metric_name"]


@admin.register(CompetitiveReport)
class CompetitiveReportAdmin(admin.ModelAdmin):
    """Admin for CompetitiveReport model."""

    list_display = ["company", "title", "industry", "status", "created_at"]
    list_filter = ["status", "industry"]
    search_fields = ["company__name", "title"]

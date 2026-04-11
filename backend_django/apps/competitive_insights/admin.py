"""Django admin configuration for competitive_insights app."""

from django.contrib import admin

from .models import CompanyMetric, CompetitiveReport, IndustryBenchmark


@admin.register(IndustryBenchmark)
class IndustryBenchmarkAdmin(admin.ModelAdmin):
    """Admin for IndustryBenchmark model."""

    list_display = [
        "id",
        "industry",
        "metric_name",
        "metric_type",
        "sample_size",
        "period_start",
    ]
    list_filter = ["metric_type", "industry"]
    search_fields = ["industry", "sub_industry", "metric_name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(CompanyMetric)
class CompanyMetricAdmin(admin.ModelAdmin):
    """Admin for CompanyMetric model."""

    list_display = [
        "id",
        "company",
        "metric_name",
        "value",
        "percentile_rank",
        "period_start",
    ]
    list_filter = ["company", "benchmark"]
    search_fields = ["metric_name", "company__name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(CompetitiveReport)
class CompetitiveReportAdmin(admin.ModelAdmin):
    """Admin for CompetitiveReport model."""

    list_display = [
        "id",
        "title",
        "company",
        "industry",
        "status",
        "created_at",
    ]
    list_filter = ["status", "industry"]
    search_fields = ["title", "company__name", "industry", "summary"]
    readonly_fields = ["id", "created_at", "updated_at"]

"""
Data quality admin configuration.
"""

from django.contrib import admin

from .models import QualityAlert, QualityAssessment, QualityRule


@admin.register(QualityAssessment)
class QualityAssessmentAdmin(admin.ModelAdmin):
    """Admin for QualityAssessment model."""

    list_display = [
        "id",
        "company",
        "consortium",
        "overall_score",
        "status",
        "created_at",
    ]
    list_filter = ["status", "consortium", "created_at"]
    search_fields = ["company__name", "consortium__name"]
    readonly_fields = [
        "completeness_score",
        "consistency_score",
        "accuracy_score",
        "timeliness_score",
        "overall_score",
    ]


@admin.register(QualityRule)
class QualityRuleAdmin(admin.ModelAdmin):
    """Admin for QualityRule model."""

    list_display = ["name", "consortium", "rule_type", "severity", "is_active"]
    list_filter = ["rule_type", "severity", "is_active"]
    search_fields = ["name", "consortium__name"]


@admin.register(QualityAlert)
class QualityAlertAdmin(admin.ModelAdmin):
    """Admin for QualityAlert model."""

    list_display = ["id", "rule", "company", "status", "created_at"]
    list_filter = ["status", "rule__severity", "created_at"]
    search_fields = ["company__name", "rule__name"]

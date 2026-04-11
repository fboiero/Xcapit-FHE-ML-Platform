"""Django admin configuration for data_quality app."""

from django.contrib import admin

from .models import QualityAlert, QualityAssessment, QualityRule


@admin.register(QualityAssessment)
class QualityAssessmentAdmin(admin.ModelAdmin):
    """Admin for QualityAssessment model."""

    list_display = [
        "id",
        "consortium",
        "company",
        "overall_score",
        "status",
        "created_at",
    ]
    list_filter = ["status", "consortium"]
    search_fields = ["company__name", "consortium__name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(QualityRule)
class QualityRuleAdmin(admin.ModelAdmin):
    """Admin for QualityRule model."""

    list_display = [
        "id",
        "name",
        "rule_type",
        "severity",
        "is_active",
        "created_at",
    ]
    list_filter = ["rule_type", "severity", "is_active"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(QualityAlert)
class QualityAlertAdmin(admin.ModelAdmin):
    """Admin for QualityAlert model."""

    list_display = [
        "id",
        "rule",
        "company",
        "status",
        "message",
        "created_at",
    ]
    list_filter = ["status", "rule__severity"]
    search_fields = ["message", "company__name", "rule__name"]
    readonly_fields = ["id", "created_at", "updated_at"]

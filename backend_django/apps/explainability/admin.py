"""
Explainability admin configuration.
"""

from django.contrib import admin

from .models import ExplanationRequest, FeatureImportance, ModelInsight


@admin.register(ExplanationRequest)
class ExplanationRequestAdmin(admin.ModelAdmin):
    """Admin for ExplanationRequest model."""

    list_display = [
        "id",
        "consortium",
        "requester",
        "explanation_type",
        "status",
        "created_at",
    ]
    list_filter = ["explanation_type", "status", "created_at"]
    search_fields = ["consortium__name", "requester__name"]


@admin.register(FeatureImportance)
class FeatureImportanceAdmin(admin.ModelAdmin):
    """Admin for FeatureImportance model."""

    list_display = [
        "feature_name",
        "consortium",
        "importance_score",
        "importance_rank",
        "computed_at",
    ]
    list_filter = ["consortium", "computation_method"]
    search_fields = ["feature_name"]


@admin.register(ModelInsight)
class ModelInsightAdmin(admin.ModelAdmin):
    """Admin for ModelInsight model."""

    list_display = [
        "title",
        "consortium",
        "insight_type",
        "severity",
        "acknowledged",
        "created_at",
    ]
    list_filter = ["insight_type", "severity", "acknowledged"]
    search_fields = ["title", "consortium__name"]

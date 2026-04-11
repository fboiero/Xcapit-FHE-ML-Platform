"""Django admin configuration for explainability app."""

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
    list_filter = ["explanation_type", "status"]
    search_fields = ["requester__name", "consortium__name", "prediction_id"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(FeatureImportance)
class FeatureImportanceAdmin(admin.ModelAdmin):
    """Admin for FeatureImportance model."""

    list_display = [
        "id",
        "feature_name",
        "importance_score",
        "importance_rank",
        "computation_method",
        "created_at",
    ]
    list_filter = ["computation_method", "consortium"]
    search_fields = ["feature_name", "consortium__name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(ModelInsight)
class ModelInsightAdmin(admin.ModelAdmin):
    """Admin for ModelInsight model."""

    list_display = [
        "id",
        "title",
        "insight_type",
        "severity",
        "is_active",
        "created_at",
    ]
    list_filter = ["insight_type", "severity", "is_active"]
    search_fields = ["title", "description", "consortium__name"]
    readonly_fields = ["id", "created_at", "updated_at"]

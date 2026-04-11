"""Django admin configuration for ensemble app."""

from django.contrib import admin

from .models import Ensemble, EnsembleEvaluation, EnsembleModel, EnsemblePrediction


@admin.register(Ensemble)
class EnsembleAdmin(admin.ModelAdmin):
    """Admin for Ensemble model."""

    list_display = [
        "id",
        "name",
        "owner",
        "ensemble_type",
        "status",
        "accuracy",
    ]
    list_filter = ["ensemble_type", "status"]
    search_fields = ["name", "description", "owner__name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(EnsembleModel)
class EnsembleModelAdmin(admin.ModelAdmin):
    """Admin for EnsembleModel model."""

    list_display = [
        "id",
        "ensemble",
        "model",
        "weight",
        "individual_accuracy",
        "is_active",
    ]
    list_filter = ["is_active", "ensemble"]
    search_fields = ["ensemble__name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(EnsemblePrediction)
class EnsemblePredictionAdmin(admin.ModelAdmin):
    """Admin for EnsemblePrediction model."""

    list_display = [
        "id",
        "ensemble",
        "n_samples",
        "latency_ms",
        "created_at",
    ]
    list_filter = ["ensemble"]
    search_fields = ["ensemble__name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(EnsembleEvaluation)
class EnsembleEvaluationAdmin(admin.ModelAdmin):
    """Admin for EnsembleEvaluation model."""

    list_display = [
        "id",
        "ensemble",
        "accuracy",
        "f1_score",
        "improvement_over_best",
        "created_at",
    ]
    list_filter = ["ensemble"]
    search_fields = ["ensemble__name"]
    readonly_fields = ["id", "created_at", "updated_at"]

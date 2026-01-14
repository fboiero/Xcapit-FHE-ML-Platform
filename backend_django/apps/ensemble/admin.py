"""
Ensemble admin configuration.
"""

from django.contrib import admin

from .models import Ensemble, EnsembleEvaluation, EnsembleModel, EnsemblePrediction


class EnsembleModelInline(admin.TabularInline):
    """Inline for EnsembleModel."""

    model = EnsembleModel
    extra = 0


@admin.register(Ensemble)
class EnsembleAdmin(admin.ModelAdmin):
    """Admin for Ensemble model."""

    list_display = ["name", "owner", "ensemble_type", "status", "model_count", "accuracy"]
    list_filter = ["ensemble_type", "status"]
    search_fields = ["name", "owner__name"]
    inlines = [EnsembleModelInline]

    def model_count(self, obj):
        return obj.model_count

    model_count.short_description = "Models"


@admin.register(EnsembleModel)
class EnsembleModelAdmin(admin.ModelAdmin):
    """Admin for EnsembleModel."""

    list_display = ["ensemble", "model", "weight", "is_active", "added_at"]
    list_filter = ["is_active", "ensemble"]


@admin.register(EnsemblePrediction)
class EnsemblePredictionAdmin(admin.ModelAdmin):
    """Admin for EnsemblePrediction."""

    list_display = ["ensemble", "requester", "n_samples", "latency_ms", "created_at"]
    list_filter = ["ensemble", "created_at"]


@admin.register(EnsembleEvaluation)
class EnsembleEvaluationAdmin(admin.ModelAdmin):
    """Admin for EnsembleEvaluation."""

    list_display = ["ensemble", "accuracy", "improvement_over_best", "evaluated_at"]
    list_filter = ["evaluated_at"]

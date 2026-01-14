"""Ensemble app configuration."""

from django.apps import AppConfig


class EnsembleConfig(AppConfig):
    """Configuration for ensemble app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ensemble"
    verbose_name = "Model Ensemble"

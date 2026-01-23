"""Explainability app configuration."""

from django.apps import AppConfig


class ExplainabilityConfig(AppConfig):
    """Configuration for explainability app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.explainability"
    verbose_name = "Model Explainability"

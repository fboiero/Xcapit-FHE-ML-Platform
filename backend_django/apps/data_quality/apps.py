"""Data quality app configuration."""

from django.apps import AppConfig


class DataQualityConfig(AppConfig):
    """Configuration for data_quality app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.data_quality"
    verbose_name = "Data Quality"

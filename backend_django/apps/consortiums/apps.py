"""
Consortiums app configuration for Xcapit FHE-ML Platform.
"""

from django.apps import AppConfig


class ConsortiumsConfig(AppConfig):
    """Configuration for the consortiums app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.consortiums"
    verbose_name = "Consortiums"

    def ready(self):
        """Import signals when app is ready."""
        # Import signals to register them
        from . import signals  # noqa: F401

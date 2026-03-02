"""
Test settings for Xcapit FHE-ML Platform.

Overrides production settings for testing.
"""

import os

# Set required environment variables for testing
os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key-for-testing-only-not-production")
os.environ.setdefault("DJANGO_DEBUG", "True")
os.environ.setdefault("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver")
os.environ.setdefault(
    "FIELD_ENCRYPTION_KEY",
    "DuabLX5GaTUmK-QMnxftxbXDBeSb7ZfzMKpbnNrVYtQ=",
)

# Now import base settings
from .settings import *  # noqa: F401,F403

# Override database for development - use SQLite file
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Override cache for testing - use dummy cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# Disable rate limiting in tests
RATELIMIT_ENABLE = False
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {}

# Disable axes in tests
AXES_ENABLED = False

# Silence system checks for development/testing
SILENCED_SYSTEM_CHECKS = [
    "django_ratelimit.E003",  # Cache backend warning
    "django_ratelimit.W001",  # Cache backend not officially supported
    "axes.W003",  # AxesStandaloneBackend warning
    "axes.W004",  # Deprecated setting warning
]

# Weaker password validation for testing
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
]

# Use simple authentication backends for testing
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

# Faster password hashing for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable logging during tests
LOGGING = {}

# Disable cache health check since we use DummyCache
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "health_check.cache"]

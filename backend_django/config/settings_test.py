"""
Test settings for Xcapit FHE-ML Platform.

Overrides production settings for testing.
"""

import os

# Set required environment variables for testing
os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key-for-testing-only-not-production")
os.environ.setdefault("DJANGO_DEBUG", "True")
os.environ.setdefault("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver")

# Now import base settings
from .settings import *  # noqa: F401,F403

# Override database for testing - use SQLite for speed
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Override cache for testing - use local memory
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Disable rate limiting in tests
RATELIMIT_ENABLE = False
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {}

# Disable axes in tests
AXES_ENABLED = False

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

# Add rest_framework.authtoken for token blacklisting in tests
INSTALLED_APPS.append("rest_framework_simplejwt.token_blacklist")

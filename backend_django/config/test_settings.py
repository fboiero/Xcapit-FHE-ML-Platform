"""
Test settings for Xcapit FHE-ML Platform.

Overrides production requirements (env vars, PostgreSQL) with
in-memory SQLite and safe defaults for fast test execution.
"""

import os
from pathlib import Path

# Provide required env vars before importing base settings
os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("FIELD_ENCRYPTION_KEY", "dGVzdC1lbmNyeXB0aW9uLWtleS0xMjM0NTY3OA==")
os.environ["DJANGO_DEBUG"] = "True"

# Bypass the env-var checks in base settings
SECRET_KEY = "test-secret-key-not-for-production"
DEBUG = True

BUILD_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = BUILD_DIR

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]
CSRF_TRUSTED_ORIGINS = ["http://localhost"]

FIELD_ENCRYPTION_KEY = "Q9s0aiO10IiB9nvbqlkdQQXox2-lfr49lYzl4Ug1JWA="

# ── Database ──────────────────────────────────────────────────

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# ── Apps ──────────────────────────────────────────────────────

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "apps.core",
    "apps.consortiums",
    "apps.governance",
    "apps.compliance",
    "apps.marketplace",
    "apps.sandbox",
    "apps.federated",
    "apps.models",
    "apps.data_quality",
    "apps.competitive_insights",
    "apps.ensemble",
    "apps.explainability",
    "apps.blockchain",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

AUTH_USER_MODEL = "core.User"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── REST Framework ────────────────────────────────────────────

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardPagination",
    "PAGE_SIZE": 50,
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

# ── JWT ───────────────────────────────────────────────────────

from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

# ── Static ────────────────────────────────────────────────────

STATIC_URL = "/static/"

# ── Security (relaxed for tests) ──────────────────────────────

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# ── Skip migrations (create tables from models) ──────────────

MIGRATION_MODULES = {
    app.split(".")[-1]: None
    for app in INSTALLED_APPS
    if app.startswith("apps.")
}
MIGRATION_MODULES.update({
    "auth": None,
    "contenttypes": None,
    "sessions": None,
    "admin": None,
    "token_blacklist": None,
})

# ── Celery (eager mode for tests) ────────────────────────────

CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_TASK_ROUTES = {
    "apps.competitive_insights.tasks.*": {"queue": "reports"},
    "apps.governance.tasks.*": {"queue": "governance"},
    "consortiums.train_model": {"queue": "training"},
    "consortiums.register_contribution_blockchain": {"queue": "blockchain"},
    "consortiums.register_training_result_blockchain": {"queue": "blockchain"},
}

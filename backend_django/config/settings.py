"""
Django settings for Xcapit FHE-ML Platform.

Django 5.2 LTS - Security-hardened configuration.
Supported until April 2028.
"""

import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

load_dotenv()

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# =============================================================================
# SECURITY SETTINGS (CRITICAL)
# =============================================================================

# SECURITY WARNING: keep the secret key secret in production!
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("DJANGO_SECRET_KEY environment variable is required")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() == "true"

# Hosts allowed to connect
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# CSRF Configuration
CSRF_TRUSTED_ORIGINS = os.environ.get(
    "CSRF_TRUSTED_ORIGINS", "https://apifhe.xcapit.com"
).split(",")
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True

# Session Security
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# Security Middleware Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# X-Frame-Options
X_FRAME_OPTIONS = "DENY"

# Referrer Policy
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# Content-Security-Policy (via middleware or nginx recommended for complex rules)
# Basic CSP headers for API-only backend
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"

# =============================================================================
# APPLICATION DEFINITION
# =============================================================================

INSTALLED_APPS = [
    # Django Core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",  # JWT token revocation
    "corsheaders",
    "django_ratelimit",
    "axes",  # Brute-force protection
    "drf_spectacular",  # API documentation
    "django_filters",  # Filtering support
    "health_check",
    "health_check.db",
    "health_check.cache",
    # Local Apps
    "apps.core",
    "apps.consortiums",
    "apps.governance",
    "apps.compliance",
    "apps.marketplace",
    "apps.sandbox",
    "apps.federated",
    "apps.models",
    # New Apps (Phase 1 Migration)
    "apps.data_quality",
    "apps.competitive_insights",
    "apps.ensemble",
    "apps.explainability",
    # Blockchain Services
    "apps.blockchain",
]

MIDDLEWARE = [
    # Correlation ID (must be first for tracing)
    "apps.core.middleware.CorrelationIdMiddleware",
    # Security
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # Session & Auth
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Brute-force protection (must be after auth)
    "axes.middleware.AxesMiddleware",
    # Request logging (after auth to capture user info)
    "apps.core.middleware.RequestLoggingMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "config.wsgi.application"

# =============================================================================
# DATABASE
# =============================================================================

# NEVER use SQLite in production
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    if DEBUG:
        # Development only - PostgreSQL recommended even for dev
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": "fheml_dev",
                "USER": "postgres",
                "PASSWORD": "postgres",
                "HOST": "localhost",
                "PORT": "5432",
            }
        }
    else:
        raise ValueError("DATABASE_URL environment variable is required in production")
else:
    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }

# Enforce PostgreSQL in production
if not DEBUG and "postgresql" not in DATABASES["default"].get("ENGINE", ""):
    raise ValueError("PostgreSQL is required in production")

# =============================================================================
# CACHE (Redis)
# =============================================================================

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "PARSER_CLASS": "redis.connection.HiredisParser",
            "CONNECTION_POOL_KWARGS": {"max_connections": 50},
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
        },
        "KEY_PREFIX": "fheml",
    }
}

# =============================================================================
# AUTHENTICATION
# =============================================================================

AUTH_USER_MODEL = "core.User"

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",  # Brute-force protection
    "django.contrib.auth.backends.ModelBackend",
]

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# =============================================================================
# DJANGO REST FRAMEWORK
# =============================================================================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
    },
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.core.exceptions.custom_exception_handler",
    # Pagination
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardPagination",
    "PAGE_SIZE": 50,
    # Filtering
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
}

# =============================================================================
# JWT SETTINGS
# =============================================================================

# Use separate JWT signing key if provided, otherwise fall back to SECRET_KEY
JWT_SIGNING_KEY = os.environ.get("JWT_SIGNING_KEY", SECRET_KEY)

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": JWT_SIGNING_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainPairSerializer",
    "TOKEN_BLACKLIST_ENABLED": True,
}

# =============================================================================
# CORS SETTINGS
# =============================================================================

CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS",
    "https://xcapit-privacy.vercel.app,https://appfhe.xcapit.com,https://privacy.xcapit.com,http://localhost:5173,http://localhost:3000",
).split(",")

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# =============================================================================
# RATE LIMITING (django-ratelimit)
# =============================================================================

RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = "default"
RATELIMIT_VIEW = "apps.core.views.ratelimited_error"

# =============================================================================
# BRUTE-FORCE PROTECTION (django-axes)
# =============================================================================

AXES_ENABLED = True
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=30)
AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP = True
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_TEMPLATE = None
AXES_LOCKOUT_URL = None

# =============================================================================
# LOGGING
# =============================================================================

# Use JSON logging in production, simple format in development
LOG_FORMAT = os.environ.get("LOG_FORMAT", "json" if not DEBUG else "simple")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
        "json": {
            "()": "apps.core.logging.CustomJsonFormatter",
            "service_name": "xcapit-fheml",
            "environment": "production" if not DEBUG else "development",
        },
    },
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "correlation_id": {
            "()": "apps.core.logging.CorrelationIdFilter",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": LOG_FORMAT,
            "filters": ["correlation_id"],
        },
        "console_json": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "json",
            "filters": ["correlation_id"],
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console", "mail_admins"],
            "level": "WARNING",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        "apps.api.requests": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# =============================================================================
# API DOCUMENTATION
# =============================================================================

SPECTACULAR_SETTINGS = {
    "TITLE": "Xcapit FHE-ML Platform API",
    "DESCRIPTION": "Privacy-preserving machine learning using Fully Homomorphic Encryption",
    "VERSION": "2.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SECURITY": [{"Bearer": []}],
    "SCHEMA_PATH_PREFIX": "/api/v2/",
}

# =============================================================================
# SENTRY (Error Tracking)
# =============================================================================

SENTRY_DSN = os.environ.get("SENTRY_DSN")
if SENTRY_DSN and not DEBUG:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.redis import RedisIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        # Performance monitoring
        traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.25")),
        profiles_sample_rate=float(os.environ.get("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
        # Privacy
        send_default_pii=False,
        # Environment
        environment=os.environ.get("SENTRY_ENVIRONMENT", "production"),
        release=os.environ.get("SENTRY_RELEASE", "2.0.0"),
    )

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# =============================================================================
# STATIC FILES
# =============================================================================

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Django 5.x uses STORAGES instead of STATICFILES_STORAGE
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# =============================================================================
# OPENBAO / VAULT CONFIGURATION
# =============================================================================

# Enable vault-based secret management
VAULT_ENABLED = os.environ.get("VAULT_ENABLED", "false").lower() == "true"
VAULT_ADDR = os.environ.get("VAULT_ADDR") or os.environ.get("BAO_ADDR", "")
VAULT_TOKEN = os.environ.get("VAULT_TOKEN") or os.environ.get("BAO_TOKEN", "")
VAULT_MOUNT_POINT = os.environ.get("VAULT_MOUNT_POINT", "xcapit")

# Log vault status
if VAULT_ENABLED and VAULT_ADDR:
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Vault integration enabled: {VAULT_ADDR}")

# =============================================================================
# FHE CONFIGURATION
# =============================================================================

FHE_SECURITY_LEVEL = int(os.environ.get("FHE_SECURITY_LEVEL", "128"))
if FHE_SECURITY_LEVEL not in [128, 192, 256]:
    raise ValueError("FHE_SECURITY_LEVEL must be 128, 192, or 256")

# =============================================================================
# CELERY CONFIGURATION
# =============================================================================

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", REDIS_URL)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes max per task
CELERY_RESULT_EXPIRES = 60 * 60 * 24  # Results expire after 24 hours

# Task routing
CELERY_TASK_ROUTES = {
    "apps.competitive_insights.tasks.*": {"queue": "reports"},
    "apps.governance.tasks.*": {"queue": "governance"},
    "consortiums.train_model": {"queue": "training"},
    "consortiums.register_contribution_blockchain": {"queue": "blockchain"},
    "consortiums.register_training_result_blockchain": {"queue": "blockchain"},
}

# =============================================================================
# BLOCKCHAIN CONFIGURATION
# =============================================================================

# Environment: "testnet" (sandbox) or "mainnet" (production)
BLOCKCHAIN_ENV = os.environ.get("BLOCKCHAIN_ENV", "testnet")

# RPC URLs
ARBITRUM_SEPOLIA_RPC_URL = os.environ.get(
    "ARBITRUM_SEPOLIA_RPC_URL",
    "https://sepolia-rollup.arbitrum.io/rpc",
)
ARBITRUM_ONE_RPC_URL = os.environ.get(
    "ARBITRUM_ONE_RPC_URL",
    "https://arb1.arbitrum.io/rpc",
)

# Contract Addresses - Testnet (Sandbox)
TESTNET_CONTRACTS = {
    "network": "arbitrum-sepolia",
    "chain_id": 421614,
    "rpc_url": ARBITRUM_SEPOLIA_RPC_URL,
    "explorer": "https://sepolia.arbiscan.io",
    "governance": "0xda52326d106A91A1F22A0c41Be2dc1F531C01F11",
    "model_registry": "0x1296cCeF7803Bff51FB690afCFc586E7012417b8",
    "computation_verifier": "0xa5f04E0aefe55173C91b949Aa2385f0228dd2921",
}

# Contract Addresses - Mainnet (Production)
MAINNET_CONTRACTS = {
    "network": "arbitrum-one",
    "chain_id": 42161,
    "rpc_url": ARBITRUM_ONE_RPC_URL,
    "explorer": "https://arbiscan.io",
    "governance": os.environ.get("MAINNET_GOVERNANCE_ADDRESS", ""),
    "model_registry": os.environ.get("MAINNET_MODEL_REGISTRY_ADDRESS", ""),
    "computation_verifier": os.environ.get("MAINNET_COMPUTATION_VERIFIER_ADDRESS", ""),
}

# Active blockchain config based on environment
BLOCKCHAIN_CONFIG = TESTNET_CONTRACTS if BLOCKCHAIN_ENV == "testnet" else MAINNET_CONTRACTS

# Validate mainnet contracts are set in production
if not DEBUG and BLOCKCHAIN_ENV == "mainnet":
    if not MAINNET_CONTRACTS["governance"]:
        raise ValueError(
            "MAINNET_GOVERNANCE_ADDRESS is required when BLOCKCHAIN_ENV=mainnet"
        )

# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================

# Email backend - use console in development, SMTP in production
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend" if DEBUG
    else "django.core.mail.backends.smtp.EmailBackend",
)

# SMTP Configuration (SendGrid recommended for production)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.sendgrid.net")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "true").lower() == "true"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "apikey")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")

# Default sender
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "Xcapit FHE-ML <noreply@xcapit.com>")
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Platform URL for email links
PLATFORM_URL = os.environ.get("PLATFORM_URL", "https://appfhe.xcapit.com")

# =============================================================================
# DEFAULT PRIMARY KEY
# =============================================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

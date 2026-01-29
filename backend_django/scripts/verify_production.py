#!/usr/bin/env python3
"""
Production Verification Script for Xcapit FHE-ML Platform

Runs Django's deployment checks and verifies production configuration.
Should be run after deployment to verify the environment is correctly configured.

Usage:
    python manage.py shell < scripts/verify_production.py
    # or from project root:
    cd backend_django && python scripts/verify_production.py

Exit codes:
    0 - All checks passed
    1 - Critical issues found
"""

import os
import sys
from pathlib import Path

# Setup Django if not already configured
if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    # Add parent directory to path for imports
    backend_dir = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(backend_dir))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    import django
    django.setup()


from django.conf import settings
from django.core.management import call_command
from io import StringIO


class Colors:
    """ANSI color codes for terminal output."""
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    NC = "\033[0m"


def print_header(text: str) -> None:
    """Print a section header."""
    print(f"\n{Colors.BLUE}{text}{Colors.NC}")


def print_check(name: str, passed: bool, message: str = "") -> None:
    """Print a check result."""
    status = f"{Colors.GREEN}PASS{Colors.NC}" if passed else f"{Colors.RED}FAIL{Colors.NC}"
    detail = f" - {message}" if message else ""
    print(f"  [{status}] {name}{detail}")


def run_deploy_check() -> tuple[bool, list[str]]:
    """Run Django's --deploy check and capture output."""
    output = StringIO()
    errors: list[str] = []

    try:
        call_command("check", "--deploy", stdout=output, stderr=output)
        return True, []
    except SystemExit:
        # Check command exits with error code if issues found
        output_text = output.getvalue()
        for line in output_text.split("\n"):
            if line.strip() and not line.startswith("System check"):
                errors.append(line.strip())
        return False, errors


def check_security_settings() -> list[tuple[str, bool, str]]:
    """Check critical security settings."""
    checks: list[tuple[str, bool, str]] = []

    # DEBUG should be False
    debug_ok = not settings.DEBUG
    checks.append(("DEBUG is False", debug_ok, str(settings.DEBUG)))

    # SECRET_KEY should not be the default insecure key
    secret_ok = (
        settings.SECRET_KEY and
        not settings.SECRET_KEY.startswith("django-insecure-") and
        len(settings.SECRET_KEY) >= 50
    )
    checks.append(("SECRET_KEY is secure", secret_ok, f"{len(settings.SECRET_KEY)} chars"))

    # ALLOWED_HOSTS should be set
    hosts_ok = bool(settings.ALLOWED_HOSTS) and "*" not in settings.ALLOWED_HOSTS
    checks.append(("ALLOWED_HOSTS configured", hosts_ok, str(settings.ALLOWED_HOSTS)))

    # Security middleware settings
    csrf_cookie_secure = getattr(settings, "CSRF_COOKIE_SECURE", False)
    checks.append(("CSRF_COOKIE_SECURE", csrf_cookie_secure, ""))

    session_cookie_secure = getattr(settings, "SESSION_COOKIE_SECURE", False)
    checks.append(("SESSION_COOKIE_SECURE", session_cookie_secure, ""))

    secure_ssl_redirect = getattr(settings, "SECURE_SSL_REDIRECT", False)
    checks.append(("SECURE_SSL_REDIRECT", secure_ssl_redirect, "(can be handled by proxy)"))

    hsts_seconds = getattr(settings, "SECURE_HSTS_SECONDS", 0)
    hsts_ok = hsts_seconds >= 31536000  # 1 year
    checks.append(("SECURE_HSTS_SECONDS >= 1 year", hsts_ok, str(hsts_seconds)))

    hsts_subdomains = getattr(settings, "SECURE_HSTS_INCLUDE_SUBDOMAINS", False)
    checks.append(("SECURE_HSTS_INCLUDE_SUBDOMAINS", hsts_subdomains, ""))

    hsts_preload = getattr(settings, "SECURE_HSTS_PRELOAD", False)
    checks.append(("SECURE_HSTS_PRELOAD", hsts_preload, ""))

    content_type_nosniff = getattr(settings, "SECURE_CONTENT_TYPE_NOSNIFF", False)
    checks.append(("SECURE_CONTENT_TYPE_NOSNIFF", content_type_nosniff, ""))

    return checks


def check_database_config() -> list[tuple[str, bool, str]]:
    """Check database configuration."""
    checks: list[tuple[str, bool, str]] = []

    default_db = settings.DATABASES.get("default", {})
    engine = default_db.get("ENGINE", "")

    # Should use PostgreSQL in production
    is_postgres = "postgresql" in engine or "psycopg" in engine
    checks.append(("Database is PostgreSQL", is_postgres, engine.split(".")[-1]))

    # Connection settings
    conn_max_age = default_db.get("CONN_MAX_AGE", 0)
    conn_ok = conn_max_age > 0 or conn_max_age is None  # None = persistent
    checks.append(("Connection pooling enabled", conn_ok, f"CONN_MAX_AGE={conn_max_age}"))

    return checks


def check_cache_config() -> list[tuple[str, bool, str]]:
    """Check cache configuration."""
    checks: list[tuple[str, bool, str]] = []

    caches = getattr(settings, "CACHES", {})
    default_cache = caches.get("default", {})
    backend = default_cache.get("BACKEND", "")

    # Should use Redis or Memcached in production
    is_production_cache = (
        "redis" in backend.lower() or
        "memcached" in backend.lower()
    )
    backend_name = backend.split(".")[-1] if backend else "Not configured"
    checks.append(("Production cache backend", is_production_cache, backend_name))

    return checks


def check_middleware() -> list[tuple[str, bool, str]]:
    """Check middleware configuration."""
    checks: list[tuple[str, bool, str]] = []
    middleware = settings.MIDDLEWARE

    # SecurityMiddleware should be first
    security_first = (
        middleware and
        "django.middleware.security.SecurityMiddleware" in middleware[0]
    )
    checks.append(("SecurityMiddleware is first", security_first, ""))

    # Required middleware
    required = [
        "django.middleware.security.SecurityMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
    ]

    for mw in required:
        present = mw in middleware
        short_name = mw.split(".")[-1]
        checks.append((f"{short_name} present", present, ""))

    return checks


def check_logging() -> list[tuple[str, bool, str]]:
    """Check logging configuration."""
    checks: list[tuple[str, bool, str]] = []

    logging_config = getattr(settings, "LOGGING", {})

    # Should have logging configured
    has_logging = bool(logging_config)
    checks.append(("Logging configured", has_logging, ""))

    # Check for Sentry
    sentry_dsn = os.environ.get("SENTRY_DSN", "")
    has_sentry = bool(sentry_dsn)
    checks.append(("Sentry DSN configured", has_sentry, "(recommended for production)"))

    return checks


def main() -> int:
    """Run all production verification checks."""
    print(f"\n{Colors.GREEN}=== Xcapit FHE-ML Platform Production Verification ==={Colors.NC}")

    all_passed = True
    critical_failed = False

    # Run Django's deploy check
    print_header("Django Deployment Checks")
    deploy_ok, deploy_errors = run_deploy_check()
    print_check("manage.py check --deploy", deploy_ok)
    if deploy_errors:
        for error in deploy_errors[:5]:  # Show first 5 errors
            print(f"    {Colors.RED}{error}{Colors.NC}")
        if len(deploy_errors) > 5:
            print(f"    ... and {len(deploy_errors) - 5} more")
    all_passed = all_passed and deploy_ok

    # Security settings
    print_header("Security Settings")
    security_checks = check_security_settings()
    for name, passed, message in security_checks:
        print_check(name, passed, message)
        if not passed and name in ("DEBUG is False", "SECRET_KEY is secure", "ALLOWED_HOSTS configured"):
            critical_failed = True
        all_passed = all_passed and passed

    # Database configuration
    print_header("Database Configuration")
    db_checks = check_database_config()
    for name, passed, message in db_checks:
        print_check(name, passed, message)
        if not passed and name == "Database is PostgreSQL":
            critical_failed = True
        all_passed = all_passed and passed

    # Cache configuration
    print_header("Cache Configuration")
    cache_checks = check_cache_config()
    for name, passed, message in cache_checks:
        print_check(name, passed, message)
        # Cache is recommended but not critical
        all_passed = all_passed and passed

    # Middleware configuration
    print_header("Middleware Configuration")
    middleware_checks = check_middleware()
    for name, passed, message in middleware_checks:
        print_check(name, passed, message)
        all_passed = all_passed and passed

    # Logging configuration
    print_header("Logging Configuration")
    logging_checks = check_logging()
    for name, passed, message in logging_checks:
        print_check(name, passed, message)
        # Logging is recommended but not critical

    # Summary
    print_header("=== Summary ===")

    if critical_failed:
        print(f"{Colors.RED}CRITICAL ISSUES FOUND{Colors.NC}")
        print("The application should not be deployed with these issues.\n")
        return 1

    if not all_passed:
        print(f"{Colors.YELLOW}SOME CHECKS FAILED{Colors.NC}")
        print("Review the failed checks and consider fixing them.\n")
        return 0  # Non-critical failures don't block

    print(f"{Colors.GREEN}ALL CHECKS PASSED{Colors.NC}")
    print("The application is configured correctly for production.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

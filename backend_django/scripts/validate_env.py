#!/usr/bin/env python3
"""
Environment Validation Script for Xcapit FHE-ML Platform

Validates environment variables before deployment to ensure all required
configuration is present and properly set.

Usage:
    python scripts/validate_env.py
    python scripts/validate_env.py --strict  # Fail on warnings too

Exit codes:
    0 - All checks passed
    1 - Critical errors found
    2 - Warnings found (only with --strict)
"""

import os
import re
import sys
from typing import NamedTuple


class ValidationResult(NamedTuple):
    """Result of a validation check."""
    passed: bool
    message: str
    severity: str  # "error", "warning", "info"


class Colors:
    """ANSI color codes for terminal output."""
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    NC = "\033[0m"  # No Color


def print_result(result: ValidationResult) -> None:
    """Print a validation result with appropriate coloring."""
    if result.severity == "error":
        icon = f"{Colors.RED}[ERROR]{Colors.NC}"
    elif result.severity == "warning":
        icon = f"{Colors.YELLOW}[WARN]{Colors.NC}"
    else:
        icon = f"{Colors.BLUE}[INFO]{Colors.NC}"

    status = f"{Colors.GREEN}PASS{Colors.NC}" if result.passed else f"{Colors.RED}FAIL{Colors.NC}"
    print(f"  {icon} {result.message}: {status}")


def check_required_var(name: str, min_length: int | None = None) -> ValidationResult:
    """Check that a required environment variable is set."""
    value = os.environ.get(name)

    if not value:
        return ValidationResult(
            passed=False,
            message=f"{name} is required but not set",
            severity="error"
        )

    if min_length and len(value) < min_length:
        return ValidationResult(
            passed=False,
            message=f"{name} must be at least {min_length} characters",
            severity="error"
        )

    return ValidationResult(
        passed=True,
        message=f"{name} is set",
        severity="info"
    )


def check_recommended_var(name: str) -> ValidationResult:
    """Check that a recommended environment variable is set."""
    value = os.environ.get(name)

    if not value:
        return ValidationResult(
            passed=False,
            message=f"{name} is recommended but not set",
            severity="warning"
        )

    return ValidationResult(
        passed=True,
        message=f"{name} is set",
        severity="info"
    )


def check_debug_disabled() -> ValidationResult:
    """Check that DEBUG is disabled for production."""
    debug = os.environ.get("DJANGO_DEBUG", "True")

    if debug.lower() in ("true", "1", "yes"):
        return ValidationResult(
            passed=False,
            message="DJANGO_DEBUG should be False in production",
            severity="error"
        )

    return ValidationResult(
        passed=True,
        message="DJANGO_DEBUG is disabled",
        severity="info"
    )


def check_allowed_hosts() -> ValidationResult:
    """Check that ALLOWED_HOSTS is properly configured."""
    hosts = os.environ.get("DJANGO_ALLOWED_HOSTS", "")

    if not hosts:
        return ValidationResult(
            passed=False,
            message="DJANGO_ALLOWED_HOSTS is not set",
            severity="error"
        )

    if "*" in hosts:
        return ValidationResult(
            passed=False,
            message="DJANGO_ALLOWED_HOSTS should not contain wildcard (*)",
            severity="warning"
        )

    return ValidationResult(
        passed=True,
        message="DJANGO_ALLOWED_HOSTS is configured",
        severity="info"
    )


def check_secret_key_strength() -> ValidationResult:
    """Check that SECRET_KEY has sufficient entropy."""
    key = os.environ.get("DJANGO_SECRET_KEY", "")

    if not key:
        return ValidationResult(
            passed=False,
            message="DJANGO_SECRET_KEY is not set",
            severity="error"
        )

    if len(key) < 50:
        return ValidationResult(
            passed=False,
            message=f"DJANGO_SECRET_KEY is too short ({len(key)} chars, need 50+)",
            severity="error"
        )

    # Check for common weak patterns
    weak_patterns = [
        r"^django-insecure-",
        r"^changeme",
        r"^secret",
        r"^password",
        r"^12345",
    ]

    for pattern in weak_patterns:
        if re.match(pattern, key.lower()):
            return ValidationResult(
                passed=False,
                message="DJANGO_SECRET_KEY appears to be a default/weak value",
                severity="error"
            )

    # Check character diversity
    has_lower = any(c.islower() for c in key)
    has_upper = any(c.isupper() for c in key)
    has_digit = any(c.isdigit() for c in key)
    has_special = any(not c.isalnum() for c in key)

    diversity = sum([has_lower, has_upper, has_digit, has_special])

    if diversity < 3:
        return ValidationResult(
            passed=False,
            message="DJANGO_SECRET_KEY lacks character diversity",
            severity="warning"
        )

    return ValidationResult(
        passed=True,
        message="DJANGO_SECRET_KEY appears strong",
        severity="info"
    )


def check_database_url() -> ValidationResult:
    """Check that DATABASE_URL is properly configured for production."""
    url = os.environ.get("DATABASE_URL", "")

    if not url:
        return ValidationResult(
            passed=False,
            message="DATABASE_URL is not set",
            severity="error"
        )

    if "sqlite" in url.lower():
        return ValidationResult(
            passed=False,
            message="SQLite should not be used in production",
            severity="error"
        )

    if "localhost" in url or "127.0.0.1" in url:
        return ValidationResult(
            passed=False,
            message="DATABASE_URL points to localhost (OK for Docker internal)",
            severity="warning"
        )

    return ValidationResult(
        passed=True,
        message="DATABASE_URL is configured",
        severity="info"
    )


def check_redis_url() -> ValidationResult:
    """Check that REDIS_URL is configured."""
    url = os.environ.get("REDIS_URL", "")

    if not url:
        return ValidationResult(
            passed=False,
            message="REDIS_URL is not set (caching disabled)",
            severity="warning"
        )

    return ValidationResult(
        passed=True,
        message="REDIS_URL is configured",
        severity="info"
    )


def check_cors_origins() -> ValidationResult:
    """Check that CORS_ALLOWED_ORIGINS is properly configured."""
    origins = os.environ.get("CORS_ALLOWED_ORIGINS", "")

    if not origins:
        return ValidationResult(
            passed=False,
            message="CORS_ALLOWED_ORIGINS is not set",
            severity="warning"
        )

    if "*" in origins:
        return ValidationResult(
            passed=False,
            message="CORS_ALLOWED_ORIGINS should not allow all origins",
            severity="error"
        )

    return ValidationResult(
        passed=True,
        message="CORS_ALLOWED_ORIGINS is configured",
        severity="info"
    )


def main() -> int:
    """Run all validation checks."""
    strict_mode = "--strict" in sys.argv

    print(f"\n{Colors.GREEN}=== Xcapit FHE-ML Platform Environment Validation ==={Colors.NC}\n")

    errors: list[ValidationResult] = []
    warnings: list[ValidationResult] = []

    # Required variables
    print(f"{Colors.BLUE}Checking required variables...{Colors.NC}")
    checks = [
        check_required_var("DJANGO_SECRET_KEY", min_length=50),
        check_database_url(),
    ]

    for result in checks:
        print_result(result)
        if not result.passed:
            if result.severity == "error":
                errors.append(result)
            else:
                warnings.append(result)

    # Security checks
    print(f"\n{Colors.BLUE}Checking security settings...{Colors.NC}")
    checks = [
        check_debug_disabled(),
        check_allowed_hosts(),
        check_secret_key_strength(),
        check_cors_origins(),
    ]

    for result in checks:
        print_result(result)
        if not result.passed:
            if result.severity == "error":
                errors.append(result)
            else:
                warnings.append(result)

    # Recommended variables
    print(f"\n{Colors.BLUE}Checking recommended variables...{Colors.NC}")
    checks = [
        check_redis_url(),
        check_recommended_var("JWT_SIGNING_KEY"),
        check_recommended_var("SENTRY_DSN"),
    ]

    for result in checks:
        print_result(result)
        if not result.passed and result.severity == "warning":
            warnings.append(result)

    # Summary
    print(f"\n{Colors.BLUE}=== Summary ==={Colors.NC}")

    if errors:
        print(f"{Colors.RED}Errors: {len(errors)}{Colors.NC}")
        for e in errors:
            print(f"  - {e.message}")
    else:
        print(f"{Colors.GREEN}Errors: 0{Colors.NC}")

    if warnings:
        print(f"{Colors.YELLOW}Warnings: {len(warnings)}{Colors.NC}")
        for w in warnings:
            print(f"  - {w.message}")
    else:
        print(f"{Colors.GREEN}Warnings: 0{Colors.NC}")

    print()

    if errors:
        print(f"{Colors.RED}FAILED: Critical issues must be resolved before deployment.{Colors.NC}\n")
        return 1

    if warnings and strict_mode:
        print(f"{Colors.YELLOW}FAILED (strict mode): Warnings must be resolved.{Colors.NC}\n")
        return 2

    if warnings:
        print(f"{Colors.YELLOW}PASSED with warnings: Review recommended settings.{Colors.NC}\n")
    else:
        print(f"{Colors.GREEN}PASSED: All checks passed successfully.{Colors.NC}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
Secret management service using OpenBao/Vault.

This module provides a unified interface for retrieving secrets from
OpenBao (or HashiCorp Vault) with fallback to environment variables.

Usage:
    from apps.core.secrets import secrets

    # Get a single secret
    db_password = secrets.get("database/postgres", "password")

    # Get all secrets at a path
    db_config = secrets.get_all("database/postgres")

    # Check if using vault
    if secrets.is_vault_enabled:
        print("Using OpenBao for secrets")
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)


class SecretsManager:
    """
    Manages secrets retrieval from OpenBao/Vault with environment fallback.

    Supports both KV v1 and v2 secrets engines.
    """

    def __init__(self) -> None:
        self._client = None
        self._vault_addr = os.environ.get("VAULT_ADDR") or os.environ.get("BAO_ADDR")
        self._vault_token = os.environ.get("VAULT_TOKEN") or os.environ.get("BAO_TOKEN")
        self._vault_role_id = os.environ.get("VAULT_ROLE_ID")
        self._vault_secret_id = os.environ.get("VAULT_SECRET_ID")
        self._mount_point = os.environ.get("VAULT_MOUNT_POINT", "xcapit")
        self._kv_version = int(os.environ.get("VAULT_KV_VERSION", "2"))
        self._initialized = False
        self._cache: dict[str, dict[str, Any]] = {}

    @property
    def is_vault_enabled(self) -> bool:
        """Check if vault is configured and available."""
        return bool(self._vault_addr) and self._ensure_client()

    def _ensure_client(self) -> bool:
        """Lazily initialize the vault client."""
        if self._initialized:
            return self._client is not None

        self._initialized = True

        if not self._vault_addr:
            logger.info("Vault address not configured, using environment variables")
            return False

        try:
            import hvac

            self._client = hvac.Client(url=self._vault_addr)

            # Authenticate
            if self._vault_token:
                self._client.token = self._vault_token
            elif self._vault_role_id and self._vault_secret_id:
                # AppRole authentication
                self._client.auth.approle.login(
                    role_id=self._vault_role_id,
                    secret_id=self._vault_secret_id,
                )
            else:
                logger.warning("No vault authentication method configured")
                return False

            # Verify connection
            if self._client.is_authenticated():
                logger.info(f"Connected to vault at {self._vault_addr}")
                return True
            else:
                logger.warning("Vault authentication failed")
                self._client = None
                return False

        except ImportError:
            logger.warning("hvac library not installed, using environment variables")
            return False
        except Exception as e:
            logger.warning(f"Failed to connect to vault: {e}")
            self._client = None
            return False

    def get(self, path: str, key: str, default: Any = None) -> Any:
        """
        Get a single secret value.

        Args:
            path: The secret path (e.g., "database/postgres")
            key: The key within the secret (e.g., "password")
            default: Default value if not found

        Returns:
            The secret value or default
        """
        secrets_data = self.get_all(path)
        return secrets_data.get(key, default)

    def get_all(self, path: str) -> dict[str, Any]:
        """
        Get all secrets at a path.

        Args:
            path: The secret path (e.g., "database/postgres")

        Returns:
            Dictionary of all secrets at that path
        """
        # Check cache first
        if path in self._cache:
            return self._cache[path]

        # Try vault
        if self._ensure_client() and self._client:
            try:
                if self._kv_version == 2:
                    response = self._client.secrets.kv.v2.read_secret_version(
                        path=path,
                        mount_point=self._mount_point,
                    )
                    data = response.get("data", {}).get("data", {})
                else:
                    response = self._client.secrets.kv.v1.read_secret(
                        path=path,
                        mount_point=self._mount_point,
                    )
                    data = response.get("data", {})

                # Cache the result
                self._cache[path] = data
                return data

            except Exception as e:
                logger.warning(f"Failed to read secret at {path}: {e}")

        # Fallback to environment variables
        return self._get_from_env(path)

    def _get_from_env(self, path: str) -> dict[str, Any]:
        """
        Fallback to environment variables.

        Converts path like "database/postgres" to prefix "DATABASE_POSTGRES_"
        """
        prefix = path.replace("/", "_").upper() + "_"
        result = {}

        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Remove prefix and convert to lowercase
                secret_key = key[len(prefix) :].lower()
                result[secret_key] = value

        return result

    def clear_cache(self) -> None:
        """Clear the secrets cache."""
        self._cache.clear()

    def refresh(self, path: str | None = None) -> None:
        """
        Refresh secrets from vault.

        Args:
            path: Specific path to refresh, or None for all
        """
        if path:
            self._cache.pop(path, None)
        else:
            self._cache.clear()


# Singleton instance
secrets = SecretsManager()


# Helper functions for common secrets
@lru_cache(maxsize=1)
def get_django_secret_key() -> str:
    """Get Django secret key from vault or environment."""
    key = secrets.get("django/config", "secret_key")
    if key:
        return key
    return os.environ.get("DJANGO_SECRET_KEY", "insecure-dev-key-change-in-production")


@lru_cache(maxsize=1)
def get_database_url() -> str:
    """Get database URL from vault or environment."""
    # Check if DATABASE_URL is set directly
    if db_url := os.environ.get("DATABASE_URL"):
        return db_url

    # Try to build from vault secrets
    db = secrets.get_all("database/postgres")
    if db:
        host = db.get("host", "localhost")
        port = db.get("port", "5432")
        name = db.get("name", "fheml")
        user = db.get("user", "xcapit")
        password = db.get("password", "")
        return f"postgresql://{user}:{password}@{host}:{port}/{name}"

    # Fallback
    return "sqlite:///db.sqlite3"


@lru_cache(maxsize=1)
def get_redis_url() -> str:
    """Get Redis URL from vault or environment."""
    if redis_url := os.environ.get("REDIS_URL"):
        return redis_url

    redis = secrets.get_all("database/redis")
    if redis:
        host = redis.get("host", "localhost")
        port = redis.get("port", "6379")
        password = redis.get("password", "")
        if password:
            return f"redis://:{password}@{host}:{port}/0"
        return f"redis://{host}:{port}/0"

    return "redis://localhost:6379/0"


@lru_cache(maxsize=1)
def get_jwt_signing_key() -> str | None:
    """Get JWT signing key from vault or environment."""
    key = secrets.get("api-keys/jwt", "signing_key")
    if key:
        return key
    return os.environ.get("JWT_SIGNING_KEY")

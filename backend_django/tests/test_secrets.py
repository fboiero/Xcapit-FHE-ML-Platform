"""
Tests for the secrets management module.

Tests OpenBao/Vault integration and environment variable fallback.
"""

import os
from unittest.mock import MagicMock, patch

import pytest


class TestSecretsManager:
    """Tests for SecretsManager class."""

    def test_init_with_vault_addr(self):
        """Test initialization reads vault address from environment."""
        with patch.dict(os.environ, {"BAO_ADDR": "http://vault:8200"}, clear=False):
            from apps.core.secrets import SecretsManager

            manager = SecretsManager()
            assert manager._vault_addr == "http://vault:8200"

    def test_init_with_vault_token(self):
        """Test initialization reads vault token from environment."""
        with patch.dict(
            os.environ,
            {"BAO_ADDR": "http://vault:8200", "BAO_TOKEN": "test-token"},
            clear=False,
        ):
            from apps.core.secrets import SecretsManager

            manager = SecretsManager()
            assert manager._vault_token == "test-token"

    def test_init_with_approle_credentials(self):
        """Test initialization reads AppRole credentials from environment."""
        with patch.dict(
            os.environ,
            {
                "VAULT_ROLE_ID": "role-123",
                "VAULT_SECRET_ID": "secret-456",
            },
            clear=False,
        ):
            from apps.core.secrets import SecretsManager

            manager = SecretsManager()
            assert manager._vault_role_id == "role-123"
            assert manager._vault_secret_id == "secret-456"

    def test_init_default_mount_point(self):
        """Test default mount point is 'xcapit'."""
        from apps.core.secrets import SecretsManager

        manager = SecretsManager()
        assert manager._mount_point == "xcapit"

    def test_init_custom_mount_point(self):
        """Test custom mount point from environment."""
        with patch.dict(os.environ, {"VAULT_MOUNT_POINT": "custom"}, clear=False):
            from apps.core.secrets import SecretsManager

            manager = SecretsManager()
            assert manager._mount_point == "custom"

    def test_init_default_kv_version(self):
        """Test default KV version is 2."""
        from apps.core.secrets import SecretsManager

        manager = SecretsManager()
        assert manager._kv_version == 2

    def test_init_custom_kv_version(self):
        """Test custom KV version from environment."""
        with patch.dict(os.environ, {"VAULT_KV_VERSION": "1"}, clear=False):
            from apps.core.secrets import SecretsManager

            manager = SecretsManager()
            assert manager._kv_version == 1

    def test_is_vault_enabled_no_address(self):
        """Test vault is disabled when no address configured."""
        with patch.dict(os.environ, {}, clear=True):
            # Clear vault-related env vars
            env_copy = os.environ.copy()
            for key in ["VAULT_ADDR", "BAO_ADDR", "VAULT_TOKEN", "BAO_TOKEN"]:
                env_copy.pop(key, None)

            with patch.dict(os.environ, env_copy, clear=True):
                from apps.core.secrets import SecretsManager

                manager = SecretsManager()
                assert not manager.is_vault_enabled

    def test_is_vault_enabled_no_auth(self):
        """Test vault is disabled when no authentication configured."""
        with patch.dict(
            os.environ,
            {"BAO_ADDR": "http://vault:8200"},
            clear=True,
        ):
            from apps.core.secrets import SecretsManager

            manager = SecretsManager()
            # Should return False because no token or approle configured
            assert not manager.is_vault_enabled

    def test_is_vault_enabled_with_token(self):
        """Test vault is enabled with valid token authentication."""
        import sys

        mock_hvac = MagicMock()
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_hvac.Client.return_value = mock_client

        with patch.dict(
            os.environ,
            {"BAO_ADDR": "http://vault:8200", "BAO_TOKEN": "test-token"},
            clear=True,
        ):
            with patch.dict(sys.modules, {"hvac": mock_hvac}):
                from apps.core.secrets import SecretsManager

                manager = SecretsManager()
                assert manager.is_vault_enabled
                mock_hvac.Client.assert_called_once_with(url="http://vault:8200")
                assert mock_client.token == "test-token"

    def test_is_vault_enabled_with_approle(self):
        """Test vault is enabled with AppRole authentication."""
        import sys

        mock_hvac = MagicMock()
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_hvac.Client.return_value = mock_client

        with patch.dict(
            os.environ,
            {
                "BAO_ADDR": "http://vault:8200",
                "VAULT_ROLE_ID": "role-123",
                "VAULT_SECRET_ID": "secret-456",
            },
            clear=True,
        ):
            with patch.dict(sys.modules, {"hvac": mock_hvac}):
                from apps.core.secrets import SecretsManager

                manager = SecretsManager()
                assert manager.is_vault_enabled
                mock_client.auth.approle.login.assert_called_once_with(
                    role_id="role-123",
                    secret_id="secret-456",
                )

    def test_is_vault_enabled_auth_failed(self):
        """Test vault is disabled when authentication fails."""
        import sys

        mock_hvac = MagicMock()
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = False
        mock_hvac.Client.return_value = mock_client

        with patch.dict(
            os.environ,
            {"BAO_ADDR": "http://vault:8200", "BAO_TOKEN": "bad-token"},
            clear=True,
        ):
            with patch.dict(sys.modules, {"hvac": mock_hvac}):
                from apps.core.secrets import SecretsManager

                manager = SecretsManager()
                assert not manager.is_vault_enabled

    def test_is_vault_enabled_hvac_not_installed(self):
        """Test vault is disabled when hvac library is not installed."""
        import sys

        with patch.dict(
            os.environ,
            {"BAO_ADDR": "http://vault:8200", "BAO_TOKEN": "test-token"},
            clear=True,
        ):
            # Remove hvac from modules to simulate not installed
            hvac_backup = sys.modules.get("hvac")
            sys.modules["hvac"] = None

            try:
                from apps.core.secrets import SecretsManager

                manager = SecretsManager()
                # Force re-initialization
                manager._initialized = False

                # _ensure_client should handle the import error
                result = manager._ensure_client()
                # When hvac module is None, import fails
                assert not result or manager._client is None
            finally:
                if hvac_backup:
                    sys.modules["hvac"] = hvac_backup

    def test_is_vault_enabled_connection_error(self):
        """Test vault is disabled when connection fails."""
        import sys

        mock_hvac = MagicMock()
        mock_hvac.Client.side_effect = Exception("Connection refused")

        with patch.dict(
            os.environ,
            {"BAO_ADDR": "http://vault:8200", "BAO_TOKEN": "test-token"},
            clear=True,
        ):
            with patch.dict(sys.modules, {"hvac": mock_hvac}):
                from apps.core.secrets import SecretsManager

                manager = SecretsManager()
                assert not manager.is_vault_enabled

    def test_get_from_env_basic(self):
        """Test getting secrets from environment variables."""
        with patch.dict(
            os.environ,
            {
                "DATABASE_POSTGRES_HOST": "localhost",
                "DATABASE_POSTGRES_PORT": "5432",
                "DATABASE_POSTGRES_USER": "testuser",
            },
            clear=False,
        ):
            from apps.core.secrets import SecretsManager

            manager = SecretsManager()
            result = manager._get_from_env("database/postgres")

            assert result["host"] == "localhost"
            assert result["port"] == "5432"
            assert result["user"] == "testuser"

    def test_get_from_env_empty(self):
        """Test getting secrets from env when none match."""
        from apps.core.secrets import SecretsManager

        manager = SecretsManager()
        result = manager._get_from_env("nonexistent/path")
        assert result == {}

    def test_get_with_default(self):
        """Test get method returns default when key not found."""
        from apps.core.secrets import SecretsManager

        manager = SecretsManager()
        manager._cache["test/path"] = {"existing_key": "value"}

        result = manager.get("test/path", "missing_key", "default_value")
        assert result == "default_value"

    def test_get_existing_key(self):
        """Test get method returns value when key exists."""
        from apps.core.secrets import SecretsManager

        manager = SecretsManager()
        manager._cache["test/path"] = {"my_key": "my_value"}

        result = manager.get("test/path", "my_key")
        assert result == "my_value"

    def test_get_all_from_cache(self):
        """Test get_all returns cached data."""
        from apps.core.secrets import SecretsManager

        manager = SecretsManager()
        manager._cache["cached/path"] = {"key1": "value1", "key2": "value2"}

        result = manager.get_all("cached/path")
        assert result == {"key1": "value1", "key2": "value2"}

    def test_get_all_from_vault_kv2(self):
        """Test get_all reads from vault KV v2."""
        import sys

        mock_hvac = MagicMock()
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"secret_key": "secret_value"}}
        }
        mock_hvac.Client.return_value = mock_client

        with patch.dict(
            os.environ,
            {"BAO_ADDR": "http://vault:8200", "BAO_TOKEN": "test-token"},
            clear=True,
        ):
            with patch.dict(sys.modules, {"hvac": mock_hvac}):
                from apps.core.secrets import SecretsManager

                manager = SecretsManager()
                result = manager.get_all("django/config")

                assert result == {"secret_key": "secret_value"}
                mock_client.secrets.kv.v2.read_secret_version.assert_called_once_with(
                    path="django/config",
                    mount_point="xcapit",
                )

    def test_get_all_from_vault_kv1(self):
        """Test get_all reads from vault KV v1."""
        import sys

        mock_hvac = MagicMock()
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v1.read_secret.return_value = {
            "data": {"secret_key": "secret_value"}
        }
        mock_hvac.Client.return_value = mock_client

        with patch.dict(
            os.environ,
            {
                "BAO_ADDR": "http://vault:8200",
                "BAO_TOKEN": "test-token",
                "VAULT_KV_VERSION": "1",
            },
            clear=True,
        ):
            with patch.dict(sys.modules, {"hvac": mock_hvac}):
                from apps.core.secrets import SecretsManager

                manager = SecretsManager()
                result = manager.get_all("django/config")

                assert result == {"secret_key": "secret_value"}
                mock_client.secrets.kv.v1.read_secret.assert_called_once_with(
                    path="django/config",
                    mount_point="xcapit",
                )

    def test_get_all_caches_result(self):
        """Test get_all caches the result."""
        import sys

        mock_hvac = MagicMock()
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"key": "value"}}
        }
        mock_hvac.Client.return_value = mock_client

        with patch.dict(
            os.environ,
            {"BAO_ADDR": "http://vault:8200", "BAO_TOKEN": "test-token"},
            clear=True,
        ):
            with patch.dict(sys.modules, {"hvac": mock_hvac}):
                from apps.core.secrets import SecretsManager

                manager = SecretsManager()

                # First call
                manager.get_all("test/path")
                # Second call should use cache
                manager.get_all("test/path")

                # Should only call vault once
                assert mock_client.secrets.kv.v2.read_secret_version.call_count == 1

    def test_get_all_vault_error_falls_back_to_env(self):
        """Test get_all falls back to env vars on vault error."""
        import sys

        mock_hvac = MagicMock()
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.side_effect = Exception("Vault error")
        mock_hvac.Client.return_value = mock_client

        with patch.dict(
            os.environ,
            {
                "BAO_ADDR": "http://vault:8200",
                "BAO_TOKEN": "test-token",
                "TEST_PATH_KEY": "env_value",
            },
            clear=True,
        ):
            with patch.dict(sys.modules, {"hvac": mock_hvac}):
                from apps.core.secrets import SecretsManager

                manager = SecretsManager()
                result = manager.get_all("test/path")

                assert result == {"key": "env_value"}

    def test_clear_cache(self):
        """Test clear_cache removes all cached data."""
        from apps.core.secrets import SecretsManager

        manager = SecretsManager()
        manager._cache = {"path1": {"k": "v"}, "path2": {"k": "v"}}

        manager.clear_cache()

        assert manager._cache == {}

    def test_refresh_specific_path(self):
        """Test refresh removes specific path from cache."""
        from apps.core.secrets import SecretsManager

        manager = SecretsManager()
        manager._cache = {"path1": {"k": "v"}, "path2": {"k": "v"}}

        manager.refresh("path1")

        assert "path1" not in manager._cache
        assert "path2" in manager._cache

    def test_refresh_all_paths(self):
        """Test refresh with None removes all paths from cache."""
        from apps.core.secrets import SecretsManager

        manager = SecretsManager()
        manager._cache = {"path1": {"k": "v"}, "path2": {"k": "v"}}

        manager.refresh()

        assert manager._cache == {}

    def test_refresh_nonexistent_path(self):
        """Test refresh with nonexistent path doesn't error."""
        from apps.core.secrets import SecretsManager

        manager = SecretsManager()
        manager._cache = {"existing": {"k": "v"}}

        # Should not raise
        manager.refresh("nonexistent")
        assert manager._cache == {"existing": {"k": "v"}}


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_get_django_secret_key_from_env(self):
        """Test get_django_secret_key reads from environment."""
        # Clear the lru_cache first
        from apps.core import secrets as secrets_module

        secrets_module.get_django_secret_key.cache_clear()

        with patch.dict(
            os.environ,
            {"DJANGO_SECRET_KEY": "env-secret-key"},
            clear=False,
        ):
            # Mock secrets.get to return None (not from vault)
            with patch.object(secrets_module.secrets, "get", return_value=None):
                result = secrets_module.get_django_secret_key()
                assert result == "env-secret-key"

    def test_get_django_secret_key_from_vault(self):
        """Test get_django_secret_key reads from vault."""
        from apps.core import secrets as secrets_module

        secrets_module.get_django_secret_key.cache_clear()

        with patch.object(secrets_module.secrets, "get", return_value="vault-secret-key"):
            result = secrets_module.get_django_secret_key()
            assert result == "vault-secret-key"

    def test_get_django_secret_key_raises_when_missing(self):
        """Test get_django_secret_key raises RuntimeError when not configured."""
        from apps.core import secrets as secrets_module

        secrets_module.get_django_secret_key.cache_clear()

        env_without_key = {k: v for k, v in os.environ.items() if k != "DJANGO_SECRET_KEY"}
        with patch.dict(os.environ, env_without_key, clear=True):
            with patch.object(secrets_module.secrets, "get", return_value=None):
                with pytest.raises(RuntimeError, match="DJANGO_SECRET_KEY"):
                    secrets_module.get_django_secret_key()

    def test_get_database_url_from_env(self):
        """Test get_database_url reads from DATABASE_URL env var."""
        from apps.core import secrets as secrets_module

        secrets_module.get_database_url.cache_clear()

        with patch.dict(
            os.environ,
            {"DATABASE_URL": "postgresql://user:pass@host:5432/db"},
            clear=False,
        ):
            result = secrets_module.get_database_url()
            assert result == "postgresql://user:pass@host:5432/db"

    def test_get_database_url_from_vault(self):
        """Test get_database_url builds URL from vault secrets."""
        from apps.core import secrets as secrets_module

        secrets_module.get_database_url.cache_clear()

        env_without_db = {k: v for k, v in os.environ.items() if k != "DATABASE_URL"}
        with patch.dict(os.environ, env_without_db, clear=True):
            with patch.object(
                secrets_module.secrets,
                "get_all",
                return_value={
                    "host": "vault-host",
                    "port": "5433",
                    "name": "vault-db",
                    "user": "vault-user",
                    "password": "vault-pass",
                },
            ):
                result = secrets_module.get_database_url()
                assert result == "postgresql://vault-user:vault-pass@vault-host:5433/vault-db"

    def test_get_database_url_default(self):
        """Test get_database_url returns sqlite default when not configured."""
        from apps.core import secrets as secrets_module

        secrets_module.get_database_url.cache_clear()

        env_without_db = {k: v for k, v in os.environ.items() if k != "DATABASE_URL"}
        with patch.dict(os.environ, env_without_db, clear=True):
            with patch.object(secrets_module.secrets, "get_all", return_value={}):
                result = secrets_module.get_database_url()
                assert result == "sqlite:///db.sqlite3"

    def test_get_redis_url_from_env(self):
        """Test get_redis_url reads from REDIS_URL env var."""
        from apps.core import secrets as secrets_module

        secrets_module.get_redis_url.cache_clear()

        with patch.dict(
            os.environ,
            {"REDIS_URL": "redis://custom:6380/1"},
            clear=False,
        ):
            result = secrets_module.get_redis_url()
            assert result == "redis://custom:6380/1"

    def test_get_redis_url_from_vault_without_password(self):
        """Test get_redis_url builds URL from vault without password."""
        from apps.core import secrets as secrets_module

        secrets_module.get_redis_url.cache_clear()

        env_without_redis = {k: v for k, v in os.environ.items() if k != "REDIS_URL"}
        with patch.dict(os.environ, env_without_redis, clear=True):
            with patch.object(
                secrets_module.secrets,
                "get_all",
                return_value={"host": "vault-redis", "port": "6380", "password": ""},
            ):
                result = secrets_module.get_redis_url()
                assert result == "redis://vault-redis:6380/0"

    def test_get_redis_url_from_vault_with_password(self):
        """Test get_redis_url builds URL from vault with password."""
        from apps.core import secrets as secrets_module

        secrets_module.get_redis_url.cache_clear()

        env_without_redis = {k: v for k, v in os.environ.items() if k != "REDIS_URL"}
        with patch.dict(os.environ, env_without_redis, clear=True):
            with patch.object(
                secrets_module.secrets,
                "get_all",
                return_value={"host": "vault-redis", "port": "6380", "password": "secret"},
            ):
                result = secrets_module.get_redis_url()
                assert result == "redis://:secret@vault-redis:6380/0"

    def test_get_redis_url_default(self):
        """Test get_redis_url returns default when not configured."""
        from apps.core import secrets as secrets_module

        secrets_module.get_redis_url.cache_clear()

        env_without_redis = {k: v for k, v in os.environ.items() if k != "REDIS_URL"}
        with patch.dict(os.environ, env_without_redis, clear=True):
            with patch.object(secrets_module.secrets, "get_all", return_value={}):
                result = secrets_module.get_redis_url()
                assert result == "redis://localhost:6379/0"

    def test_get_jwt_signing_key_from_vault(self):
        """Test get_jwt_signing_key reads from vault."""
        from apps.core import secrets as secrets_module

        secrets_module.get_jwt_signing_key.cache_clear()

        with patch.object(secrets_module.secrets, "get", return_value="vault-jwt-key"):
            result = secrets_module.get_jwt_signing_key()
            assert result == "vault-jwt-key"

    def test_get_jwt_signing_key_from_env(self):
        """Test get_jwt_signing_key reads from environment."""
        from apps.core import secrets as secrets_module

        secrets_module.get_jwt_signing_key.cache_clear()

        with patch.dict(
            os.environ,
            {"JWT_SIGNING_KEY": "env-jwt-key"},
            clear=False,
        ):
            with patch.object(secrets_module.secrets, "get", return_value=None):
                result = secrets_module.get_jwt_signing_key()
                assert result == "env-jwt-key"

    def test_get_jwt_signing_key_none(self):
        """Test get_jwt_signing_key returns None when not configured."""
        from apps.core import secrets as secrets_module

        secrets_module.get_jwt_signing_key.cache_clear()

        env_without_jwt = {k: v for k, v in os.environ.items() if k != "JWT_SIGNING_KEY"}
        with patch.dict(os.environ, env_without_jwt, clear=True):
            with patch.object(secrets_module.secrets, "get", return_value=None):
                result = secrets_module.get_jwt_signing_key()
                assert result is None


class TestSecretsManagerIntegration:
    """Integration-style tests for SecretsManager."""

    def test_full_flow_env_fallback(self):
        """Test complete flow with environment variable fallback."""
        with patch.dict(
            os.environ,
            {
                "MYAPP_CONFIG_API_KEY": "test-api-key",
                "MYAPP_CONFIG_DEBUG": "true",
            },
            clear=False,
        ):
            from apps.core.secrets import SecretsManager

            manager = SecretsManager()

            # Should fall back to env vars
            config = manager.get_all("myapp/config")
            assert config["api_key"] == "test-api-key"
            assert config["debug"] == "true"

            # Single value
            api_key = manager.get("myapp/config", "api_key")
            assert api_key == "test-api-key"

            # With default
            missing = manager.get("myapp/config", "missing", "default")
            assert missing == "default"

    def test_cache_invalidation_flow(self):
        """Test cache invalidation workflow."""
        from apps.core.secrets import SecretsManager

        manager = SecretsManager()

        # Manually populate cache
        manager._cache["path1"] = {"key": "cached_value"}
        manager._cache["path2"] = {"key": "cached_value2"}

        # Verify cached
        assert manager.get_all("path1") == {"key": "cached_value"}

        # Refresh specific path
        manager.refresh("path1")
        assert "path1" not in manager._cache
        assert "path2" in manager._cache

        # Clear all
        manager._cache["path1"] = {"key": "new_value"}
        manager.clear_cache()
        assert manager._cache == {}

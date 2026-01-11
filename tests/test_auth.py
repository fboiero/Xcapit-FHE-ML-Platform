"""Tests for API authentication module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from sdk.api.auth import (
    RateLimiter,
    generate_api_key,
    check_rate_limit,
)


class TestGenerateApiKey:
    """Tests for API key generation."""

    def test_generate_api_key_default_prefix(self):
        """Test API key generation with default prefix."""
        key = generate_api_key()
        assert key.startswith("fheml_")
        assert len(key) > 10

    def test_generate_api_key_custom_prefix(self):
        """Test API key generation with custom prefix."""
        key = generate_api_key(prefix="custom")
        assert key.startswith("custom_")

    def test_generate_api_key_unique(self):
        """Test that generated keys are unique."""
        keys = [generate_api_key() for _ in range(100)]
        assert len(set(keys)) == 100

    def test_generate_api_key_sufficient_entropy(self):
        """Test that generated keys have sufficient length."""
        key = generate_api_key()
        # Should have prefix + underscore + 43 chars from 32 bytes base64
        assert len(key) >= 40


class TestRateLimiter:
    """Tests for rate limiting functionality."""

    def test_rate_limiter_init(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter()
        assert limiter._window_seconds == 60
        assert limiter._requests == {}

    def test_check_rate_limit_none_key(self):
        """Test rate limit check with None key."""
        limiter = RateLimiter()
        assert limiter.check_rate_limit(None) is True

    def test_check_rate_limit_within_limit(self):
        """Test rate limit check within allowed limit."""
        limiter = RateLimiter()
        key_info = {"name": "test_key", "rate_limit": 100}

        # Should allow requests within limit
        for _ in range(50):
            assert limiter.check_rate_limit(key_info) is True

    def test_check_rate_limit_exceeds_limit(self):
        """Test rate limit check when exceeding limit."""
        limiter = RateLimiter()
        key_info = {"name": "test_key", "rate_limit": 5}

        # Use up the limit
        for _ in range(5):
            limiter.check_rate_limit(key_info)

        # Next request should be rate limited
        assert limiter.check_rate_limit(key_info) is False

    def test_check_rate_limit_default_rate(self):
        """Test rate limit uses default when not specified."""
        limiter = RateLimiter()
        key_info = {"name": "test_key"}  # No rate_limit specified

        # Should use default of 100
        for _ in range(99):
            assert limiter.check_rate_limit(key_info) is True

    def test_get_remaining_none_key(self):
        """Test get remaining with None key."""
        limiter = RateLimiter()
        assert limiter.get_remaining(None) == 100

    def test_get_remaining_no_requests(self):
        """Test get remaining with no previous requests."""
        limiter = RateLimiter()
        key_info = {"name": "new_key", "rate_limit": 50}
        assert limiter.get_remaining(key_info) == 50

    def test_get_remaining_after_requests(self):
        """Test get remaining after some requests."""
        limiter = RateLimiter()
        key_info = {"name": "test_key", "rate_limit": 10}

        # Make 3 requests
        for _ in range(3):
            limiter.check_rate_limit(key_info)

        assert limiter.get_remaining(key_info) == 7

    def test_get_remaining_anonymous(self):
        """Test get remaining for anonymous key."""
        limiter = RateLimiter()
        key_info = {}  # No name or rate_limit
        remaining = limiter.get_remaining(key_info)
        assert remaining == 100  # Default rate limit

    def test_rate_limiter_multiple_keys(self):
        """Test rate limiter handles multiple keys independently."""
        limiter = RateLimiter()
        key1 = {"name": "key1", "rate_limit": 5}
        key2 = {"name": "key2", "rate_limit": 5}

        # Use up key1's limit
        for _ in range(5):
            limiter.check_rate_limit(key1)

        # key1 should be rate limited
        assert limiter.check_rate_limit(key1) is False

        # key2 should still work
        assert limiter.check_rate_limit(key2) is True


class TestCheckRateLimit:
    """Tests for check_rate_limit dependency."""

    def test_check_rate_limit_none_key(self):
        """Test check_rate_limit with None key."""
        # Should not raise
        check_rate_limit(None)

    def test_check_rate_limit_within_limit(self):
        """Test check_rate_limit within limit."""
        key_info = {"name": "test", "rate_limit": 1000}
        # Should not raise
        check_rate_limit(key_info)

    def test_check_rate_limit_exceeds(self):
        """Test check_rate_limit when exceeded."""
        from fastapi import HTTPException
        from sdk.api.auth import rate_limiter

        # Reset the global rate limiter
        rate_limiter._requests = {}

        key_info = {"name": "limited_key", "rate_limit": 1}

        # First request OK
        check_rate_limit(key_info)

        # Second request should fail
        with pytest.raises(HTTPException) as exc_info:
            check_rate_limit(key_info)

        assert exc_info.value.status_code == 429
        assert "Rate limit exceeded" in str(exc_info.value.detail)


class TestCreateApiKey:
    """Tests for create_api_key function."""

    def test_create_api_key_returns_tuple(self):
        """Test create_api_key returns key and hash."""
        with patch("sdk.api.auth.get_database") as mock_db:
            mock_instance = MagicMock()
            mock_instance.create_api_key.return_value = "hash123"
            mock_db.return_value = mock_instance

            from sdk.api.auth import create_api_key
            key, key_hash = create_api_key("test_key")

            assert key.startswith("fheml_")
            assert key_hash == "hash123"

    def test_create_api_key_with_permissions(self):
        """Test create_api_key with custom permissions."""
        with patch("sdk.api.auth.get_database") as mock_db:
            mock_instance = MagicMock()
            mock_instance.create_api_key.return_value = "hash456"
            mock_db.return_value = mock_instance

            from sdk.api.auth import create_api_key
            key, _ = create_api_key("admin_key", permissions=["read", "write", "admin"])

            mock_instance.create_api_key.assert_called_once()
            call_kwargs = mock_instance.create_api_key.call_args
            assert call_kwargs[1]["permissions"] == ["read", "write", "admin"]


class TestListApiKeys:
    """Tests for list_api_keys function."""

    def test_list_api_keys_empty(self):
        """Test list_api_keys with no keys."""
        with patch("sdk.api.auth.get_database") as mock_db:
            mock_instance = MagicMock()
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_conn.cursor.return_value = mock_cursor
            mock_conn.__enter__ = MagicMock(return_value=mock_conn)
            mock_conn.__exit__ = MagicMock(return_value=False)
            mock_instance._get_connection.return_value = mock_conn
            mock_db.return_value = mock_instance

            from sdk.api.auth import list_api_keys
            keys = list_api_keys()

            assert keys == []

    def test_list_api_keys_with_keys(self):
        """Test list_api_keys returns formatted keys."""
        mock_row = {
            "key_hash": "abcdef123456789012345678901234567890",
            "name": "test_key",
            "created_at": "2024-01-01",
            "last_used_at": None,
            "is_active": 1,
            "permissions": '["read", "write"]',
            "rate_limit": 100,
        }

        with patch("sdk.api.auth.get_database") as mock_db:
            mock_instance = MagicMock()
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = [mock_row]
            mock_conn.cursor.return_value = mock_cursor
            mock_conn.__enter__ = MagicMock(return_value=mock_conn)
            mock_conn.__exit__ = MagicMock(return_value=False)
            mock_instance._get_connection.return_value = mock_conn
            mock_db.return_value = mock_instance

            from sdk.api.auth import list_api_keys
            keys = list_api_keys()

            assert len(keys) == 1
            assert keys[0]["name"] == "test_key"
            assert keys[0]["key_hash"] == "abcdef123456..."  # Truncated


class TestRevokeApiKey:
    """Tests for revoke_api_key function."""

    def test_revoke_api_key_success(self):
        """Test revoking an API key successfully."""
        with patch("sdk.api.auth.get_database") as mock_db:
            mock_instance = MagicMock()
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.rowcount = 1
            mock_conn.cursor.return_value = mock_cursor
            mock_conn.__enter__ = MagicMock(return_value=mock_conn)
            mock_conn.__exit__ = MagicMock(return_value=False)
            mock_instance._get_connection.return_value = mock_conn
            mock_db.return_value = mock_instance

            from sdk.api.auth import revoke_api_key
            result = revoke_api_key("abcdef123456")

            assert result is True

    def test_revoke_api_key_not_found(self):
        """Test revoking non-existent API key."""
        with patch("sdk.api.auth.get_database") as mock_db:
            mock_instance = MagicMock()
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.rowcount = 0
            mock_conn.cursor.return_value = mock_cursor
            mock_conn.__enter__ = MagicMock(return_value=mock_conn)
            mock_conn.__exit__ = MagicMock(return_value=False)
            mock_instance._get_connection.return_value = mock_conn
            mock_db.return_value = mock_instance

            from sdk.api.auth import revoke_api_key
            result = revoke_api_key("nonexistent")

            assert result is False


class TestRequireApiKey:
    """Tests for require_api_key dependency factory."""

    @pytest.mark.asyncio
    async def test_require_api_key_auth_disabled(self):
        """Test require_api_key when auth is disabled."""
        from sdk.api.auth import require_api_key

        with patch.dict(os.environ, {"FHEML_AUTH_DISABLED": "true"}):
            dependency = require_api_key()
            result = await dependency(None)

            assert result["name"] == "anonymous"
            assert "read" in result["permissions"]

    @pytest.mark.asyncio
    async def test_require_api_key_optional_no_key(self):
        """Test optional auth with no key."""
        from sdk.api.auth import require_api_key

        with patch.dict(os.environ, {"FHEML_AUTH_DISABLED": "false"}, clear=False):
            # Ensure auth is not disabled
            os.environ.pop("FHEML_AUTH_DISABLED", None)

            dependency = require_api_key(optional=True)
            result = await dependency(None)

            assert result is None

    @pytest.mark.asyncio
    async def test_require_api_key_required_no_key(self):
        """Test required auth with no key raises exception."""
        from fastapi import HTTPException
        from sdk.api.auth import require_api_key

        # Ensure auth is not disabled
        os.environ.pop("FHEML_AUTH_DISABLED", None)

        dependency = require_api_key(optional=False)

        with pytest.raises(HTTPException) as exc_info:
            await dependency(None)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_require_api_key_with_permissions(self):
        """Test require_api_key checks permissions."""
        from sdk.api.auth import require_api_key

        os.environ.pop("FHEML_AUTH_DISABLED", None)

        key_info = {"name": "test", "permissions": ["read"]}
        dependency = require_api_key(permissions=["read"])
        result = await dependency(key_info)

        assert result == key_info

    @pytest.mark.asyncio
    async def test_require_api_key_missing_permission(self):
        """Test require_api_key fails when permission missing."""
        from fastapi import HTTPException
        from sdk.api.auth import require_api_key

        os.environ.pop("FHEML_AUTH_DISABLED", None)

        key_info = {"name": "test", "permissions": ["read"]}
        dependency = require_api_key(permissions=["admin"])

        with pytest.raises(HTTPException) as exc_info:
            await dependency(key_info)

        assert exc_info.value.status_code == 403
        assert "admin" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_require_api_key_admin_bypasses(self):
        """Test admin permission bypasses other requirements."""
        from sdk.api.auth import require_api_key

        os.environ.pop("FHEML_AUTH_DISABLED", None)

        key_info = {"name": "admin_user", "permissions": ["admin"]}
        dependency = require_api_key(permissions=["special_permission"])
        result = await dependency(key_info)

        assert result == key_info


class TestGetCurrentCompany:
    """Tests for get_current_company dependency."""

    @pytest.mark.asyncio
    async def test_get_current_company_auth_disabled(self):
        """Test get_current_company when auth disabled."""
        from sdk.api.auth import get_current_company

        with patch.dict(os.environ, {"FHEML_AUTH_DISABLED": "true"}):
            result = await get_current_company(None)

            assert result["id"] == "demo_company"
            assert result["name"] == "Demo Company"

    @pytest.mark.asyncio
    async def test_get_current_company_no_key(self):
        """Test get_current_company with no key raises exception."""
        from fastapi import HTTPException
        from sdk.api.auth import get_current_company

        os.environ.pop("FHEML_AUTH_DISABLED", None)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_company(None)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_company_with_key(self):
        """Test get_current_company extracts company info."""
        from sdk.api.auth import get_current_company

        os.environ.pop("FHEML_AUTH_DISABLED", None)

        key_info = {
            "name": "test_company",
            "company_id": "comp_123",
            "company_name": "Test Corp",
            "permissions": ["read", "write"],
        }

        result = await get_current_company(key_info)

        assert result["id"] == "comp_123"
        assert result["name"] == "Test Corp"
        assert result["permissions"] == ["read", "write"]

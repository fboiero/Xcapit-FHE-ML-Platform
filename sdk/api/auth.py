"""API Key authentication for Xcapit FHE-ML API.

This module provides API key authentication middleware and utilities.
"""

import os
import secrets
from datetime import datetime
from functools import wraps
from typing import Callable, List, Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, APIKeyQuery

from .database import get_database


# API key header and query parameter names
API_KEY_HEADER_NAME = "X-API-Key"
API_KEY_QUERY_NAME = "api_key"

# Security schemes
api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)
api_key_query = APIKeyQuery(name=API_KEY_QUERY_NAME, auto_error=False)


# Environment variable for master key (optional)
MASTER_API_KEY_ENV = "FHEML_MASTER_API_KEY"


def generate_api_key(prefix: str = "fheml") -> str:
    """Generate a new API key.

    Args:
        prefix: Prefix for the key (default: "fheml").

    Returns:
        Generated API key string.
    """
    # Generate 32 random bytes (256 bits of entropy)
    random_part = secrets.token_urlsafe(32)
    return f"{prefix}_{random_part}"


def create_api_key(
    name: str,
    permissions: Optional[List[str]] = None,
    rate_limit: int = 100,
) -> tuple:
    """Create a new API key and store it in the database.

    Args:
        name: Human-readable name for the key.
        permissions: List of permissions (default: ["read", "write"]).
        rate_limit: Requests per minute limit.

    Returns:
        Tuple of (api_key, key_hash) - Store the key securely!
    """
    key = generate_api_key()
    db = get_database()
    key_hash = db.create_api_key(
        key=key,
        name=name,
        permissions=permissions,
        rate_limit=rate_limit,
    )
    return key, key_hash


async def get_api_key(
    header_key: Optional[str] = Security(api_key_header),
    query_key: Optional[str] = Security(api_key_query),
) -> Optional[dict]:
    """Extract and validate API key from request.

    Checks header first, then query parameter.

    Args:
        header_key: API key from header.
        query_key: API key from query parameter.

    Returns:
        API key info dict if valid, None if no key provided.

    Raises:
        HTTPException: If key is invalid.
    """
    # Get key from header or query
    api_key = header_key or query_key

    if not api_key:
        return None

    # Check master key from environment (for admin access)
    master_key = os.environ.get(MASTER_API_KEY_ENV)
    if master_key and api_key == master_key:
        return {
            "name": "master",
            "permissions": ["read", "write", "admin"],
            "rate_limit": 10000,
            "is_master": True,
        }

    # Validate against database
    db = get_database()
    key_info = db.validate_api_key(api_key)

    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return key_info


def require_api_key(
    permissions: Optional[List[str]] = None,
    optional: bool = False,
):
    """Dependency to require API key authentication.

    Args:
        permissions: Required permissions (e.g., ["read"], ["write"]).
        optional: If True, allows unauthenticated access with limited features.

    Returns:
        FastAPI dependency function.
    """
    async def dependency(
        key_info: Optional[dict] = Depends(get_api_key),
    ) -> Optional[dict]:
        # Check if authentication is disabled via environment
        if os.environ.get("FHEML_AUTH_DISABLED", "").lower() == "true":
            return {"name": "anonymous", "permissions": ["read", "write"]}

        if key_info is None:
            if optional:
                return None
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        # Check permissions
        if permissions:
            key_permissions = key_info.get("permissions", [])
            for required in permissions:
                if required not in key_permissions and "admin" not in key_permissions:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission '{required}' required",
                    )

        return key_info

    return dependency


# Convenience dependencies
require_read = require_api_key(permissions=["read"])
require_write = require_api_key(permissions=["write"])
require_admin = require_api_key(permissions=["admin"])
optional_auth = require_api_key(optional=True)


class RateLimiter:
    """Simple in-memory rate limiter.

    For production, use Redis or similar distributed cache.
    """

    def __init__(self):
        self._requests: dict = {}  # {key_hash: [(timestamp, count), ...]}
        self._window_seconds = 60  # 1 minute window

    def check_rate_limit(self, key_info: dict) -> bool:
        """Check if request is within rate limit.

        Args:
            key_info: API key info with rate_limit.

        Returns:
            True if allowed, False if rate limited.
        """
        if not key_info:
            return True

        key_name = key_info.get("name", "anonymous")
        rate_limit = key_info.get("rate_limit", 100)

        now = datetime.utcnow().timestamp()
        window_start = now - self._window_seconds

        # Clean old entries and count recent requests
        if key_name in self._requests:
            self._requests[key_name] = [
                (ts, count) for ts, count in self._requests[key_name]
                if ts > window_start
            ]
            recent_count = sum(count for _, count in self._requests[key_name])
        else:
            self._requests[key_name] = []
            recent_count = 0

        # Check limit
        if recent_count >= rate_limit:
            return False

        # Record this request
        self._requests[key_name].append((now, 1))
        return True

    def get_remaining(self, key_info: dict) -> int:
        """Get remaining requests in current window.

        Args:
            key_info: API key info.

        Returns:
            Number of remaining requests.
        """
        if not key_info:
            return 100

        key_name = key_info.get("name", "anonymous")
        rate_limit = key_info.get("rate_limit", 100)

        now = datetime.utcnow().timestamp()
        window_start = now - self._window_seconds

        if key_name not in self._requests:
            return rate_limit

        recent_count = sum(
            count for ts, count in self._requests[key_name]
            if ts > window_start
        )
        return max(0, rate_limit - recent_count)


# Global rate limiter instance
rate_limiter = RateLimiter()


def check_rate_limit(key_info: Optional[dict] = None):
    """Dependency to check rate limit.

    Args:
        key_info: API key info.

    Raises:
        HTTPException: If rate limited.
    """
    if key_info and not rate_limiter.check_rate_limit(key_info):
        remaining = rate_limiter.get_remaining(key_info)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(key_info.get("rate_limit", 100)),
                "X-RateLimit-Remaining": str(remaining),
                "Retry-After": "60",
            },
        )


# CLI helper functions
def list_api_keys() -> List[dict]:
    """List all API keys (for admin use).

    Returns:
        List of API key records (without actual keys).
    """
    db = get_database()
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT key_hash, name, created_at, last_used_at, is_active, permissions, rate_limit
            FROM api_keys
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()

        return [
            {
                "key_hash": row["key_hash"][:12] + "...",  # Truncated for display
                "name": row["name"],
                "created_at": row["created_at"],
                "last_used_at": row["last_used_at"],
                "is_active": bool(row["is_active"]),
                "permissions": row["permissions"],
                "rate_limit": row["rate_limit"],
            }
            for row in rows
        ]


def revoke_api_key(key_hash_prefix: str) -> bool:
    """Revoke an API key by hash prefix.

    Args:
        key_hash_prefix: First 12 characters of key hash.

    Returns:
        True if revoked.
    """
    db = get_database()
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE api_keys SET is_active = 0
            WHERE key_hash LIKE ?
        """, (key_hash_prefix + "%",))
        return cursor.rowcount > 0


async def get_current_company(
    key_info: Optional[dict] = Depends(get_api_key),
) -> dict:
    """Get the current authenticated company.

    This dependency provides company information based on the API key.
    For demo purposes, it creates a mock company if auth is disabled.

    Args:
        key_info: API key info from authentication.

    Returns:
        Company dict with at least 'id' and 'name'.

    Raises:
        HTTPException: If not authenticated.
    """
    # Check if authentication is disabled via environment
    if os.environ.get("FHEML_AUTH_DISABLED", "").lower() == "true":
        return {"id": "demo_company", "name": "Demo Company"}

    if key_info is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # For API key auth, the company_id might be stored with the key
    # For now, return a company based on the key info
    company_id = key_info.get("company_id", key_info.get("name", "unknown"))
    company_name = key_info.get("company_name", key_info.get("name", "API User"))

    return {
        "id": company_id,
        "name": company_name,
        "permissions": key_info.get("permissions", []),
    }

"""API key management commands.

NOTE: These commands are temporarily disabled.
API key management has been migrated to the Django backend.
Use the REST API at /api/v2/auth/ for API key operations.
"""


def cmd_api_key_create(args) -> int:
    """Create a new API key."""
    print("API key management has been migrated to the Django backend.")
    print("Use the REST API at /api/v2/auth/ for API key operations.")
    print("\nExample with curl:")
    print("  curl -X POST https://apifhe.xcapit.com/api/v2/auth/token/ \\")
    print('       -d \'{"email": "user@example.com", "password": "password"}\'')
    return 1


def cmd_api_key_list(args) -> int:
    """List all API keys."""
    print("API key management has been migrated to the Django backend.")
    print("Use the REST API at /api/v2/auth/ for API key operations.")
    return 1


def cmd_api_key_revoke(args) -> int:
    """Revoke an API key."""
    print("API key management has been migrated to the Django backend.")
    print("Use the REST API at /api/v2/auth/logout/ to revoke tokens.")
    return 1


__all__ = ["cmd_api_key_create", "cmd_api_key_list", "cmd_api_key_revoke"]

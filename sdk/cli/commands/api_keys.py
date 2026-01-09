"""API key management commands."""


def cmd_api_key_create(args) -> int:
    """Create a new API key."""
    from ...api.auth import create_api_key

    permissions = args.permissions.split(",") if args.permissions else ["read", "write"]

    print(f"Creating API key '{args.name}'...")
    print(f"  Permissions: {permissions}")
    print(f"  Rate limit: {args.rate_limit} req/min")

    api_key, key_hash = create_api_key(
        name=args.name,
        permissions=permissions,
        rate_limit=args.rate_limit,
    )

    print("\n" + "=" * 60)
    print("API KEY CREATED SUCCESSFULLY")
    print("=" * 60)
    print(f"\nAPI Key: {api_key}")
    print(f"Hash:    {key_hash[:12]}...")
    print("\nIMPORTANT: Save this API key now. It cannot be recovered!")
    print("=" * 60)

    return 0


def cmd_api_key_list(args) -> int:
    """List all API keys."""
    from ...api.auth import list_api_keys

    keys = list_api_keys()

    if not keys:
        print("No API keys found.")
        print("\nCreate one with: xcapit-fhe api-key create --name 'my-key'")
        return 0

    print(f"Found {len(keys)} API key(s):\n")
    print(f"{'Name':<20} {'Hash':<15} {'Permissions':<25} {'Active':<8} {'Rate Limit'}")
    print("-" * 90)

    for key in keys:
        active = "Yes" if key["is_active"] else "No"
        print(f"{key['name']:<20} {key['key_hash']:<15} {key['permissions']:<25} {active:<8} {key['rate_limit']}")

    return 0


def cmd_api_key_revoke(args) -> int:
    """Revoke an API key."""
    from ...api.auth import revoke_api_key

    print(f"Revoking API key with hash prefix: {args.key_hash}...")

    if revoke_api_key(args.key_hash):
        print("API key revoked successfully.")
        return 0
    else:
        print("Error: API key not found.")
        return 1


__all__ = ["cmd_api_key_create", "cmd_api_key_list", "cmd_api_key_revoke"]

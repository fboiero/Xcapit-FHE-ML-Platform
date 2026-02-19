#!/bin/bash
# =============================================================================
# OpenBao Initialization Script
# =============================================================================
# This script initializes OpenBao and configures secrets for Xcapit FHE-ML
# Run this ONCE after first OpenBao deployment
# =============================================================================

set -e

OPENBAO_ADDR="${OPENBAO_ADDR:-http://localhost:8200}"
export BAO_ADDR="$OPENBAO_ADDR"

echo "=============================================="
echo "OpenBao Initialization for Xcapit FHE-ML"
echo "=============================================="

# Check if OpenBao is running
until bao status 2>/dev/null | grep -q "Sealed"; do
    echo "Waiting for OpenBao to start..."
    sleep 2
done

echo "[1/6] Checking initialization status..."

# Check if already initialized
if bao status 2>/dev/null | grep -q "Initialized.*true"; then
    echo "OpenBao is already initialized."

    # Check if sealed
    if bao status 2>/dev/null | grep -q "Sealed.*true"; then
        echo "OpenBao is sealed. Please unseal manually with:"
        echo "  bao operator unseal <unseal-key>"
        exit 1
    fi

    echo "OpenBao is unsealed and ready."
else
    echo "[2/6] Initializing OpenBao..."

    # Initialize with 1 key share and 1 threshold (dev mode)
    # For production: use 5 shares with threshold of 3
    INIT_OUTPUT=$(bao operator init -key-shares=1 -key-threshold=1 -format=json)

    # Extract keys
    UNSEAL_KEY=$(echo "$INIT_OUTPUT" | jq -r '.unseal_keys_b64[0]')
    ROOT_TOKEN=$(echo "$INIT_OUTPUT" | jq -r '.root_token')

    # Save keys securely (in production, use secure key management!)
    echo "=============================================="
    echo "IMPORTANT: Save these credentials securely!"
    echo "=============================================="
    echo "Unseal Key: $UNSEAL_KEY"
    echo "Root Token: $ROOT_TOKEN"
    echo "=============================================="

    # Save to file (dev only - NEVER in production!)
    cat > /openbao/init-keys.json << EOF
{
  "unseal_key": "$UNSEAL_KEY",
  "root_token": "$ROOT_TOKEN",
  "warning": "DEVELOPMENT ONLY - Never store keys in files in production!"
}
EOF
    chmod 600 /openbao/init-keys.json

    echo "[3/6] Unsealing OpenBao..."
    bao operator unseal "$UNSEAL_KEY"

    # Login with root token
    export BAO_TOKEN="$ROOT_TOKEN"
fi

# If we have init keys file, use it
if [ -f /openbao/init-keys.json ]; then
    export BAO_TOKEN=$(cat /openbao/init-keys.json | jq -r '.root_token')
fi

echo "[4/6] Enabling secrets engines..."

# Enable KV secrets engine v2 for application secrets
bao secrets enable -path=xcapit -version=2 kv 2>/dev/null || echo "KV engine already enabled"

# Enable database secrets engine for dynamic credentials
bao secrets enable -path=database database 2>/dev/null || echo "Database engine already enabled"

# Enable PKI for certificate management
bao secrets enable -path=pki pki 2>/dev/null || echo "PKI engine already enabled"

echo "[5/6] Creating application policies..."

# Create Django application policy
bao policy write django-app - << 'EOF'
# Xcapit FHE-ML Django Application Policy

# Read application secrets
path "xcapit/data/django/*" {
  capabilities = ["read", "list"]
}

# Read database credentials
path "xcapit/data/database/*" {
  capabilities = ["read"]
}

# Read API keys
path "xcapit/data/api-keys/*" {
  capabilities = ["read", "list"]
}

# Read encryption keys (FHE)
path "xcapit/data/fhe/*" {
  capabilities = ["read"]
}

# No write access to secrets (read-only for app)
EOF

# Create admin policy
bao policy write xcapit-admin - << 'EOF'
# Xcapit FHE-ML Admin Policy

# Full access to xcapit secrets
path "xcapit/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Manage database connections
path "database/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Manage PKI
path "pki/*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}
EOF

echo "[6/6] Creating initial secrets..."

# Create Django secrets
bao kv put xcapit/django/config \
    secret_key="$(openssl rand -hex 32)" \
    debug="false" \
    allowed_hosts="localhost,127.0.0.1,apifhe.xcapit.com"

# Create database credentials
bao kv put xcapit/database/postgres \
    host="postgres" \
    port="5432" \
    name="fheml" \
    user="xcapit" \
    password="$(openssl rand -hex 16)"

# Create Redis credentials
bao kv put xcapit/database/redis \
    host="redis" \
    port="6379" \
    password=""

# Create JWT signing key
bao kv put xcapit/api-keys/jwt \
    signing_key="$(openssl rand -hex 32)"

# Create placeholder for FHE keys
bao kv put xcapit/fhe/master \
    note="FHE master key placeholder - generate with TenSEAL"

echo "=============================================="
echo "OpenBao initialization complete!"
echo "=============================================="
echo ""
echo "Access UI at: ${OPENBAO_ADDR}/ui"
echo ""
echo "Create AppRole for Django:"
echo "  bao auth enable approle"
echo "  bao write auth/approle/role/django-app \\"
echo "      token_policies=\"django-app\" \\"
echo "      token_ttl=1h \\"
echo "      token_max_ttl=4h"
echo ""

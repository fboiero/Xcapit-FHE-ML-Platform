#!/bin/bash
# =============================================================================
# Initialize OpenBao with blockchain secrets
# =============================================================================
#
# This script sets up the blockchain-related secrets in OpenBao.
# Run this after the main OpenBao initialization.
#
# Usage:
#   ./init-blockchain-secrets.sh
#
# Environment variables:
#   BAO_ADDR - OpenBao address (default: http://127.0.0.1:8200)
#   BAO_TOKEN - OpenBao token (default: dev-root-token for dev)
# =============================================================================

set -e

# Configuration
BAO_ADDR="${BAO_ADDR:-http://127.0.0.1:8200}"
BAO_TOKEN="${BAO_TOKEN:-dev-root-token}"
MOUNT_POINT="${VAULT_MOUNT_POINT:-xcapit}"

echo "=== OpenBao Blockchain Secrets Initialization ==="
echo "Address: $BAO_ADDR"
echo "Mount: $MOUNT_POINT"
echo ""

# Check if bao CLI is available
if ! command -v bao &> /dev/null; then
    echo "Error: bao CLI not found. Please install OpenBao."
    exit 1
fi

# Export for bao CLI
export BAO_ADDR
export BAO_TOKEN

# Check connection
echo "Checking OpenBao connection..."
if ! bao status &> /dev/null; then
    echo "Error: Cannot connect to OpenBao at $BAO_ADDR"
    exit 1
fi

# Check if KV engine is enabled
echo "Checking KV secrets engine..."
if ! bao secrets list | grep -q "^${MOUNT_POINT}/"; then
    echo "Enabling KV v2 secrets engine at ${MOUNT_POINT}..."
    bao secrets enable -path="${MOUNT_POINT}" kv-v2
fi

echo ""
echo "=== Creating Blockchain Secrets ==="

# Generate development wallets (DO NOT USE IN PRODUCTION!)
# In production, these should be imported from secure key management
generate_dev_wallet() {
    # Generate a random private key for development
    openssl rand -hex 32
}

# Deployer wallet
echo "Creating deployer wallet..."
DEPLOYER_KEY=$(generate_dev_wallet)
DEPLOYER_ADDRESS="0x$(echo -n "$DEPLOYER_KEY" | xxd -r -p | openssl dgst -sha256 | cut -d' ' -f2 | tail -c 41)"
bao kv put -mount="${MOUNT_POINT}" blockchain/deployer \
    private_key="$DEPLOYER_KEY" \
    address="$DEPLOYER_ADDRESS" \
    description="Contract deployment wallet"

# Consortium signer wallet
echo "Creating consortium-signer wallet..."
SIGNER_KEY=$(generate_dev_wallet)
SIGNER_ADDRESS="0x$(echo -n "$SIGNER_KEY" | xxd -r -p | openssl dgst -sha256 | cut -d' ' -f2 | tail -c 41)"
bao kv put -mount="${MOUNT_POINT}" blockchain/consortium-signer \
    private_key="$SIGNER_KEY" \
    address="$SIGNER_ADDRESS" \
    description="Consortium operations wallet"

# Verifier wallet
echo "Creating verifier wallet..."
VERIFIER_KEY=$(generate_dev_wallet)
VERIFIER_ADDRESS="0x$(echo -n "$VERIFIER_KEY" | xxd -r -p | openssl dgst -sha256 | cut -d' ' -f2 | tail -c 41)"
bao kv put -mount="${MOUNT_POINT}" blockchain/verifier \
    private_key="$VERIFIER_KEY" \
    address="$VERIFIER_ADDRESS" \
    description="Computation verification wallet"

# RPC endpoints
echo "Creating RPC configuration..."
bao kv put -mount="${MOUNT_POINT}" blockchain/rpc \
    arbitrum_url="https://arb1.arbitrum.io/rpc" \
    arbitrum_sepolia_url="https://sepolia-rollup.arbitrum.io/rpc"

# Contract addresses (empty initially, populated after deployment)
echo "Creating contract addresses placeholder..."
bao kv put -mount="${MOUNT_POINT}" blockchain/contracts/arbitrum_sepolia \
    governance="" \
    model_registry="" \
    computation_verifier="" \
    deployed_at=""

bao kv put -mount="${MOUNT_POINT}" blockchain/contracts/arbitrum \
    governance="" \
    model_registry="" \
    computation_verifier="" \
    deployed_at=""

echo ""
echo "=== Creating Blockchain Policy ==="

# Create policy for blockchain operations
cat <<EOF | bao policy write blockchain-app -
# Blockchain application policy
# Read blockchain wallets
path "${MOUNT_POINT}/data/blockchain/deployer" {
  capabilities = ["read"]
}

path "${MOUNT_POINT}/data/blockchain/consortium-signer" {
  capabilities = ["read"]
}

path "${MOUNT_POINT}/data/blockchain/verifier" {
  capabilities = ["read"]
}

# Read and update contract addresses
path "${MOUNT_POINT}/data/blockchain/contracts/*" {
  capabilities = ["read", "create", "update"]
}

# Read RPC configuration
path "${MOUNT_POINT}/data/blockchain/rpc" {
  capabilities = ["read"]
}

# List blockchain secrets
path "${MOUNT_POINT}/metadata/blockchain/*" {
  capabilities = ["list"]
}
EOF

echo ""
echo "=== Verification ==="

# Verify secrets were created
echo "Verifying deployer wallet..."
bao kv get -mount="${MOUNT_POINT}" -field=address blockchain/deployer

echo "Verifying consortium-signer wallet..."
bao kv get -mount="${MOUNT_POINT}" -field=address blockchain/consortium-signer

echo "Verifying verifier wallet..."
bao kv get -mount="${MOUNT_POINT}" -field=address blockchain/verifier

echo ""
echo "=== Summary ==="
echo "Blockchain secrets initialized successfully!"
echo ""
echo "Secret paths:"
echo "  - ${MOUNT_POINT}/blockchain/deployer"
echo "  - ${MOUNT_POINT}/blockchain/consortium-signer"
echo "  - ${MOUNT_POINT}/blockchain/verifier"
echo "  - ${MOUNT_POINT}/blockchain/rpc"
echo "  - ${MOUNT_POINT}/blockchain/contracts/arbitrum_sepolia"
echo "  - ${MOUNT_POINT}/blockchain/contracts/arbitrum"
echo ""
echo "Policy: blockchain-app"
echo ""
echo "⚠️  WARNING: Development keys generated. DO NOT use in production!"
echo "    Import production keys manually with proper key management."
echo ""
echo "To retrieve a private key:"
echo "  bao kv get -mount=${MOUNT_POINT} -field=private_key blockchain/deployer"
echo ""
echo "To export for Foundry:"
echo "  export DEPLOYER_PRIVATE_KEY=\$(bao kv get -mount=${MOUNT_POINT} -field=private_key blockchain/deployer)"

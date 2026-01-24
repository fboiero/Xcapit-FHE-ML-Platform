"""
Blockchain secrets management via OpenBao/Vault.

This module provides secure access to blockchain private keys and configuration
stored in OpenBao (Vault fork). Keys are never logged or exposed in error messages.

Secret Paths:
    xcapit/blockchain/deployer - Deployment wallet
    xcapit/blockchain/consortium-signer - Consortium operations
    xcapit/blockchain/verifier - Computation verification
    xcapit/blockchain/contracts - Deployed contract addresses
    xcapit/blockchain/rpc - RPC endpoint URLs
"""

import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from apps.core.secrets import secrets

logger = logging.getLogger(__name__)


@dataclass
class BlockchainWallet:
    """Represents a blockchain wallet with private key from Vault."""

    address: str
    private_key: str
    name: str

    def __repr__(self) -> str:
        """Safe repr that doesn't expose private key."""
        return f"BlockchainWallet(name={self.name}, address={self.address[:10]}...)"


@dataclass
class ContractAddresses:
    """Deployed contract addresses."""

    governance: Optional[str] = None
    model_registry: Optional[str] = None
    computation_verifier: Optional[str] = None
    network: str = "arbitrum_sepolia"


@dataclass
class RPCConfig:
    """RPC endpoint configuration."""

    arbitrum_url: Optional[str] = None
    arbitrum_sepolia_url: Optional[str] = None

    def get_url(self, network: str = "arbitrum_sepolia") -> str:
        """Get RPC URL for specified network."""
        if network == "arbitrum":
            return self.arbitrum_url or os.getenv(
                "ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc"
            )
        return self.arbitrum_sepolia_url or os.getenv(
            "ARBITRUM_SEPOLIA_RPC_URL", "https://sepolia-rollup.arbitrum.io/rpc"
        )


class BlockchainSecretsManager:
    """
    Manages blockchain secrets from OpenBao/Vault.

    Usage:
        from apps.blockchain.secrets import blockchain_secrets

        # Get deployer wallet
        deployer = blockchain_secrets.get_deployer()
        print(deployer.address)

        # Get RPC URL
        rpc_url = blockchain_secrets.get_rpc_url("arbitrum_sepolia")

        # Get contract addresses
        contracts = blockchain_secrets.get_contracts()
    """

    VAULT_PATH_PREFIX = "blockchain"

    def __init__(self):
        self._cache = {}

    def _get_secret(self, path: str, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a secret from Vault with caching."""
        full_path = f"{self.VAULT_PATH_PREFIX}/{path}"
        cache_key = f"{full_path}:{key}"

        if cache_key not in self._cache:
            value = secrets.get(full_path, key)
            self._cache[cache_key] = value if value else default

        return self._cache[cache_key]

    def _get_all_secrets(self, path: str) -> dict:
        """Get all secrets at a path."""
        full_path = f"{self.VAULT_PATH_PREFIX}/{path}"
        return secrets.get_all(full_path)

    def clear_cache(self) -> None:
        """Clear the secrets cache. Useful after key rotation."""
        self._cache.clear()
        logger.info("Blockchain secrets cache cleared")

    def get_wallet(self, wallet_type: str) -> Optional[BlockchainWallet]:
        """
        Get a wallet by type (deployer, consortium-signer, verifier).

        Args:
            wallet_type: One of 'deployer', 'consortium-signer', 'verifier'

        Returns:
            BlockchainWallet or None if not configured
        """
        private_key = self._get_secret(wallet_type, "private_key")
        address = self._get_secret(wallet_type, "address")

        if not private_key:
            # Fallback to environment variables
            env_prefix = wallet_type.upper().replace("-", "_")
            private_key = os.getenv(f"{env_prefix}_PRIVATE_KEY")
            address = os.getenv(f"{env_prefix}_ADDRESS")

        if not private_key:
            logger.warning(f"Wallet '{wallet_type}' not configured in Vault or environment")
            return None

        # Derive address from private key if not provided
        if not address:
            address = self._derive_address(private_key)

        return BlockchainWallet(
            address=address,
            private_key=private_key,
            name=wallet_type,
        )

    def get_deployer(self) -> Optional[BlockchainWallet]:
        """Get the deployer wallet."""
        return self.get_wallet("deployer")

    def get_consortium_signer(self) -> Optional[BlockchainWallet]:
        """Get the consortium operations wallet."""
        return self.get_wallet("consortium-signer")

    def get_verifier(self) -> Optional[BlockchainWallet]:
        """Get the verifier wallet."""
        return self.get_wallet("verifier")

    def get_contracts(self, network: str = "arbitrum_sepolia") -> ContractAddresses:
        """Get deployed contract addresses."""
        data = self._get_all_secrets(f"contracts/{network}")

        if not data:
            # Fallback to environment variables
            return ContractAddresses(
                governance=os.getenv("GOVERNANCE_CONTRACT_ADDRESS"),
                model_registry=os.getenv("MODEL_REGISTRY_CONTRACT_ADDRESS"),
                computation_verifier=os.getenv("COMPUTATION_VERIFIER_CONTRACT_ADDRESS"),
                network=network,
            )

        return ContractAddresses(
            governance=data.get("governance"),
            model_registry=data.get("model_registry"),
            computation_verifier=data.get("computation_verifier"),
            network=network,
        )

    def get_rpc_config(self) -> RPCConfig:
        """Get RPC endpoint configuration."""
        data = self._get_all_secrets("rpc")

        return RPCConfig(
            arbitrum_url=data.get("arbitrum_url") if data else None,
            arbitrum_sepolia_url=data.get("arbitrum_sepolia_url") if data else None,
        )

    def get_rpc_url(self, network: str = "arbitrum_sepolia") -> str:
        """Get RPC URL for specified network."""
        return self.get_rpc_config().get_url(network)

    def _derive_address(self, private_key: str) -> str:
        """Derive Ethereum address from private key."""
        try:
            from eth_account import Account

            if not private_key.startswith("0x"):
                private_key = f"0x{private_key}"
            account = Account.from_key(private_key)
            return account.address
        except ImportError:
            logger.warning("eth_account not installed, cannot derive address")
            return ""
        except Exception as e:
            logger.error(f"Failed to derive address: {e}")
            return ""

    def store_contract_address(
        self, contract_name: str, address: str, network: str = "arbitrum_sepolia"
    ) -> bool:
        """
        Store a deployed contract address in Vault.

        Args:
            contract_name: One of 'governance', 'model_registry', 'computation_verifier'
            address: The deployed contract address
            network: Target network

        Returns:
            True if successful
        """
        try:
            # Get existing data
            path = f"contracts/{network}"
            existing = self._get_all_secrets(path) or {}
            existing[contract_name] = address

            # Store updated data
            full_path = f"{self.VAULT_PATH_PREFIX}/{path}"
            return secrets.put(full_path, existing)
        except Exception as e:
            logger.error(f"Failed to store contract address: {e}")
            return False


# Singleton instance
blockchain_secrets = BlockchainSecretsManager()


# Convenience functions
def get_deployer_wallet() -> Optional[BlockchainWallet]:
    """Get the deployer wallet."""
    return blockchain_secrets.get_deployer()


def get_consortium_signer_wallet() -> Optional[BlockchainWallet]:
    """Get the consortium signer wallet."""
    return blockchain_secrets.get_consortium_signer()


def get_verifier_wallet() -> Optional[BlockchainWallet]:
    """Get the verifier wallet."""
    return blockchain_secrets.get_verifier()


def get_rpc_url(network: str = "arbitrum_sepolia") -> str:
    """Get RPC URL for the specified network."""
    return blockchain_secrets.get_rpc_url(network)


def get_contract_addresses(network: str = "arbitrum_sepolia") -> ContractAddresses:
    """Get deployed contract addresses."""
    return blockchain_secrets.get_contracts(network)

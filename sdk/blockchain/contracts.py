"""Contract addresses and deployment configuration.

This module provides deployed contract addresses for different networks,
supporting both testnet (sandbox) and mainnet (production) environments.
"""

from dataclasses import dataclass
from typing import Optional

from .connector import Network


@dataclass
class ContractAddresses:
    """Deployed contract addresses for a network."""

    governance: str
    model_registry: str
    computation_verifier: str
    deployer: Optional[str] = None
    deployed_at: Optional[str] = None


# =============================================================================
# Testnet (Sandbox) - Arbitrum Sepolia
# =============================================================================
# Use this for development, testing, and integration validation
# Deployed: 2026-01-24

ARBITRUM_SEPOLIA_CONTRACTS = ContractAddresses(
    governance="0xda52326d106A91A1F22A0c41Be2dc1F531C01F11",
    model_registry="0x1296cCeF7803Bff51FB690afCFc586E7012417b8",
    computation_verifier="0xa5f04E0aefe55173C91b949Aa2385f0228dd2921",
    deployer="0x1EFeA870E80aCa0E140A9C77d921FEd68F1D653D",
    deployed_at="2026-01-24",
)

# =============================================================================
# Mainnet (Production) - Arbitrum One
# =============================================================================
# Use this for production with real customers
# Deployed: TBD (requires audit + multi-sig setup)

ARBITRUM_ONE_CONTRACTS = ContractAddresses(
    governance="",  # TBD after mainnet deployment
    model_registry="",  # TBD after mainnet deployment
    computation_verifier="",  # TBD after mainnet deployment
    deployer="",
    deployed_at="",
)

# =============================================================================
# Local Development - Anvil/Hardhat
# =============================================================================

LOCAL_CONTRACTS = ContractAddresses(
    governance="",  # Set dynamically during local deployment
    model_registry="",
    computation_verifier="",
)

# =============================================================================
# Network to Contracts Mapping
# =============================================================================

NETWORK_CONTRACTS: dict[Network, ContractAddresses] = {
    Network.ARBITRUM_SEPOLIA: ARBITRUM_SEPOLIA_CONTRACTS,
    Network.ARBITRUM_ONE: ARBITRUM_ONE_CONTRACTS,
    Network.LOCAL: LOCAL_CONTRACTS,
}


def get_contracts(network: Network) -> ContractAddresses:
    """Get contract addresses for a network.

    Args:
        network: Target network.

    Returns:
        ContractAddresses for the network.

    Raises:
        ValueError: If network has no deployed contracts.
    """
    if network not in NETWORK_CONTRACTS:
        raise ValueError(f"No contracts configured for network: {network}")

    contracts = NETWORK_CONTRACTS[network]

    # Validate contracts are deployed (for non-local networks)
    if network != Network.LOCAL and not contracts.governance:
        raise ValueError(
            f"Contracts not yet deployed on {network.value}. "
            "Use ARBITRUM_SEPOLIA for testing."
        )

    return contracts


def is_testnet(network: Network) -> bool:
    """Check if network is a testnet.

    Args:
        network: Network to check.

    Returns:
        True if testnet, False if mainnet.
    """
    return network in {
        Network.ARBITRUM_SEPOLIA,
        Network.ETHEREUM_SEPOLIA,
        Network.LOCAL,
    }


def get_explorer_url(network: Network, address: str) -> str:
    """Get block explorer URL for a contract address.

    Args:
        network: Target network.
        address: Contract address.

    Returns:
        Explorer URL.
    """
    explorers = {
        Network.ARBITRUM_ONE: "https://arbiscan.io",
        Network.ARBITRUM_SEPOLIA: "https://sepolia.arbiscan.io",
        Network.ETHEREUM_MAINNET: "https://etherscan.io",
        Network.ETHEREUM_SEPOLIA: "https://sepolia.etherscan.io",
    }

    base_url = explorers.get(network, "")
    if not base_url:
        return ""

    return f"{base_url}/address/{address}"


__all__ = [
    "ContractAddresses",
    "ARBITRUM_SEPOLIA_CONTRACTS",
    "ARBITRUM_ONE_CONTRACTS",
    "LOCAL_CONTRACTS",
    "NETWORK_CONTRACTS",
    "get_contracts",
    "is_testnet",
    "get_explorer_url",
]

"""Blockchain integration for model verification.

This module provides blockchain connectivity and smart contract
interaction for registering ML models and verifying computations
on Arbitrum and other EVM-compatible chains.
"""

from .connector import (
    BlockchainConnector,
    Network,
    NetworkConfig,
    NETWORK_CONFIGS,
)
from .registry import (
    ModelRegistryClient,
    ModelInfo,
    CheckpointInfo,
)

__all__ = [
    # Connector
    "BlockchainConnector",
    "Network",
    "NetworkConfig",
    "NETWORK_CONFIGS",
    # Registry
    "ModelRegistryClient",
    "ModelInfo",
    "CheckpointInfo",
]

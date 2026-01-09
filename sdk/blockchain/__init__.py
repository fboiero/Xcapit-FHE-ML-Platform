"""Blockchain integration for model verification and governance.

This module provides blockchain connectivity and smart contract
interaction for registering ML models, verifying computations,
and consortium governance on Arbitrum and other EVM-compatible chains.
"""

from .connector import (
    NETWORK_CONFIGS,
    BlockchainConnector,
    Network,
    NetworkConfig,
)
from .governance import (
    AuditEvent,
    AuditEventType,
    ConsortiumInfo,
    ConsortiumStatus,
    ContributionInfo,
    GovernanceClient,
    MemberInfo,
    MemberStatus,
    ProposalInfo,
    ProposalStatus,
    ProposalType,
)
from .registry import (
    CheckpointInfo,
    ModelInfo,
    ModelRegistryClient,
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
    # Governance
    "GovernanceClient",
    "ConsortiumStatus",
    "MemberStatus",
    "ProposalType",
    "ProposalStatus",
    "AuditEventType",
    "ConsortiumInfo",
    "MemberInfo",
    "ContributionInfo",
    "ProposalInfo",
    "AuditEvent",
]

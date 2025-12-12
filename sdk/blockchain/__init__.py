"""Blockchain integration for model verification and governance.

This module provides blockchain connectivity and smart contract
interaction for registering ML models, verifying computations,
and consortium governance on Arbitrum and other EVM-compatible chains.
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
from .governance import (
    GovernanceClient,
    ConsortiumStatus,
    MemberStatus,
    ProposalType,
    ProposalStatus,
    AuditEventType,
    ConsortiumInfo,
    MemberInfo,
    ContributionInfo,
    ProposalInfo,
    AuditEvent,
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

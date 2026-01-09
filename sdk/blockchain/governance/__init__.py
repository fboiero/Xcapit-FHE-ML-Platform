"""Consortium Governance client for blockchain interaction.

This package provides Python interface to the ConsortiumGovernance smart contract,
enabling contribution proofs, voting, and audit trail functionality.
"""

from .abi import GOVERNANCE_ABI
from .client import GovernanceClient
from .models import (
    AuditEvent,
    AuditEventType,
    ConsortiumInfo,
    ConsortiumStatus,
    ContributionInfo,
    MemberInfo,
    MemberStatus,
    ProposalInfo,
    ProposalStatus,
    ProposalType,
)

__all__ = [
    # Client
    "GovernanceClient",
    # ABI
    "GOVERNANCE_ABI",
    # Enums
    "ConsortiumStatus",
    "MemberStatus",
    "ProposalType",
    "ProposalStatus",
    "AuditEventType",
    # Dataclasses
    "ConsortiumInfo",
    "MemberInfo",
    "ContributionInfo",
    "ProposalInfo",
    "AuditEvent",
]

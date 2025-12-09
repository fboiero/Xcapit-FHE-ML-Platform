"""Consortium Governance client for blockchain interaction.

This module is a wrapper for backward compatibility.
The actual implementation is in the sdk/blockchain/governance/ package.
"""

from .governance import (
    GOVERNANCE_ABI,
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

__all__ = [
    "GovernanceClient",
    "GOVERNANCE_ABI",
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

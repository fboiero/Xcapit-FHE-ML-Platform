"""Governance models: enums and dataclasses."""

from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from typing import Optional


class ConsortiumStatus(IntEnum):
    """Consortium status enum matching Solidity."""
    ACTIVE = 0
    PAUSED = 1
    COMPLETED = 2
    DISSOLVED = 3


class MemberStatus(IntEnum):
    """Member status enum matching Solidity."""
    PENDING = 0
    ACTIVE = 1
    SUSPENDED = 2
    REMOVED = 3


class ProposalType(IntEnum):
    """Proposal type enum matching Solidity."""
    ADD_MEMBER = 0
    REMOVE_MEMBER = 1
    CHANGE_MODEL = 2
    START_TRAINING = 3
    DISTRIBUTE_REWARDS = 4
    UPDATE_CONFIG = 5
    DISSOLVE = 6


class ProposalStatus(IntEnum):
    """Proposal status enum matching Solidity."""
    ACTIVE = 0
    PASSED = 1
    REJECTED = 2
    EXECUTED = 3
    CANCELLED = 4


class AuditEventType(IntEnum):
    """Audit event type enum matching Solidity."""
    CONSORTIUM_CREATED = 0
    MEMBER_JOINED = 1
    MEMBER_LEFT = 2
    MEMBER_REMOVED = 3
    DATA_CONTRIBUTED = 4
    TRAINING_STARTED = 5
    TRAINING_COMPLETED = 6
    PROPOSAL_CREATED = 7
    PROPOSAL_VOTED = 8
    PROPOSAL_EXECUTED = 9
    REWARDS_DISTRIBUTED = 10
    CONFIG_UPDATED = 11


@dataclass
class ConsortiumInfo:
    """Consortium information."""
    id: bytes
    name: str
    owner: str
    status: ConsortiumStatus
    member_count: int
    total_contributions: int
    min_voting_quorum: int
    voting_duration: int


@dataclass
class MemberInfo:
    """Member information."""
    address: str
    status: MemberStatus
    joined_at: datetime
    contribution_count: int
    contribution_weight: int
    last_contribution_at: Optional[datetime]


@dataclass
class ContributionInfo:
    """Contribution proof information."""
    id: bytes
    consortium_id: bytes
    contributor: str
    record_count: int
    feature_count: int
    data_hash: bytes
    checksum_hash: bytes
    timestamp: datetime
    verified: bool


@dataclass
class ProposalInfo:
    """Proposal information."""
    id: bytes
    consortium_id: bytes
    proposal_type: ProposalType
    proposer: str
    status: ProposalStatus
    yes_votes: int
    no_votes: int
    expires_at: datetime
    executed: bool


@dataclass
class AuditEvent:
    """Audit event information."""
    id: bytes
    event_type: AuditEventType
    actor: str
    target_id: bytes
    timestamp: datetime
    previous_hash: bytes


__all__ = [
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

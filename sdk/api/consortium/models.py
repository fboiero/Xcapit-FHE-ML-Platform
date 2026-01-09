"""Data models for consortium management.

This module contains all enums and dataclasses used across
the consortium package.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class ConsortiumStatus(str, Enum):
    """Status of a consortium."""

    DRAFT = "draft"  # Being configured, not yet active
    ACTIVE = "active"  # Accepting data and training
    TRAINING = "training"  # Model training in progress
    COMPLETED = "completed"  # Training done, results available
    ARCHIVED = "archived"  # No longer active


class MemberRole(str, Enum):
    """Role of a company in a consortium."""

    OWNER = "owner"  # Created the consortium, full control
    ADMIN = "admin"  # Can manage members and settings
    CONTRIBUTOR = "contributor"  # Can upload data and get results
    VIEWER = "viewer"  # Can only view results


class MemberStatus(str, Enum):
    """Status of a membership."""

    PENDING = "pending"  # Invitation sent, not yet accepted
    ACTIVE = "active"  # Full member
    SUSPENDED = "suspended"  # Temporarily disabled
    LEFT = "left"  # Voluntarily left
    REMOVED = "removed"  # Removed by admin


class InviteStatus(str, Enum):
    """Status of an invitation."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"
    REVOKED = "revoked"


@dataclass
class Company:
    """A company/organization that can participate in consortiums."""

    id: str
    name: str
    email: str
    api_key_hash: str
    created_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Consortium:
    """A data collaboration consortium."""

    id: str
    name: str
    description: str
    owner_id: str
    status: ConsortiumStatus
    model_type: str  # linear_regression, logistic_regression, etc.
    model_config: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    training_started_at: Optional[datetime] = None
    training_completed_at: Optional[datetime] = None
    model_id: Optional[str] = None  # Reference to trained model
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Membership:
    """A company's membership in a consortium."""

    id: str
    consortium_id: str
    company_id: str
    role: MemberRole
    status: MemberStatus
    joined_at: datetime
    data_uploaded: bool = False
    data_record_count: int = 0
    last_upload_at: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Invitation:
    """An invitation to join a consortium."""

    id: str
    consortium_id: str
    invited_by: str  # company_id
    invite_email: str
    invite_code: str
    role: MemberRole
    status: InviteStatus
    created_at: datetime
    expires_at: datetime
    accepted_at: Optional[datetime] = None
    accepted_by: Optional[str] = None  # company_id


@dataclass
class DataContribution:
    """Record of encrypted data contributed by a company."""

    id: str
    consortium_id: str
    company_id: str
    encrypted_blob_path: str
    record_count: int
    feature_count: int
    uploaded_at: datetime
    checksum: str
    metadata: dict[str, Any] = field(default_factory=dict)


__all__ = [
    "ConsortiumStatus",
    "MemberRole",
    "MemberStatus",
    "InviteStatus",
    "Company",
    "Consortium",
    "Membership",
    "Invitation",
    "DataContribution",
]

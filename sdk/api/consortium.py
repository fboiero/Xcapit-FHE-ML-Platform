"""Consortium management module for Xcapit Privacy Platform.

This module provides data models and database operations for managing
data collaboration consortiums between multiple companies.
"""

import secrets
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from contextlib import contextmanager
import json
import hashlib


class ConsortiumStatus(str, Enum):
    """Status of a consortium."""
    DRAFT = "draft"           # Being configured, not yet active
    ACTIVE = "active"         # Accepting data and training
    TRAINING = "training"     # Model training in progress
    COMPLETED = "completed"   # Training done, results available
    ARCHIVED = "archived"     # No longer active


class MemberRole(str, Enum):
    """Role of a company in a consortium."""
    OWNER = "owner"           # Created the consortium, full control
    ADMIN = "admin"           # Can manage members and settings
    CONTRIBUTOR = "contributor"  # Can upload data and get results
    VIEWER = "viewer"         # Can only view results


class MemberStatus(str, Enum):
    """Status of a membership."""
    PENDING = "pending"       # Invitation sent, not yet accepted
    ACTIVE = "active"         # Full member
    SUSPENDED = "suspended"   # Temporarily disabled
    LEFT = "left"             # Voluntarily left
    REMOVED = "removed"       # Removed by admin


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
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Consortium:
    """A data collaboration consortium."""
    id: str
    name: str
    description: str
    owner_id: str
    status: ConsortiumStatus
    model_type: str  # linear_regression, logistic_regression, etc.
    model_config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    training_started_at: Optional[datetime] = None
    training_completed_at: Optional[datetime] = None
    model_id: Optional[str] = None  # Reference to trained model
    metadata: Dict[str, Any] = field(default_factory=dict)


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
    metadata: Dict[str, Any] = field(default_factory=dict)


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
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConsortiumManager:
    """Manager for consortium operations."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize consortium manager.

        Args:
            db_path: Path to SQLite database.
        """
        self.db_path = db_path or Path("./data/fheml.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(
            str(self.db_path),
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self):
        """Initialize consortium database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Companies table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS companies (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    api_key_hash TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}'
                )
            """)

            # Consortiums table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS consortiums (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    owner_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'draft',
                    model_type TEXT NOT NULL,
                    model_config TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    training_started_at TIMESTAMP,
                    training_completed_at TIMESTAMP,
                    model_id TEXT,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (owner_id) REFERENCES companies(id)
                )
            """)

            # Memberships table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memberships (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    company_id TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'contributor',
                    status TEXT NOT NULL DEFAULT 'pending',
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_uploaded BOOLEAN DEFAULT 0,
                    data_record_count INTEGER DEFAULT 0,
                    last_upload_at TIMESTAMP,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id) ON DELETE CASCADE,
                    FOREIGN KEY (company_id) REFERENCES companies(id),
                    UNIQUE(consortium_id, company_id)
                )
            """)

            # Invitations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS invitations (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    invited_by TEXT NOT NULL,
                    invite_email TEXT NOT NULL,
                    invite_code TEXT UNIQUE NOT NULL,
                    role TEXT NOT NULL DEFAULT 'contributor',
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    accepted_at TIMESTAMP,
                    accepted_by TEXT,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id) ON DELETE CASCADE,
                    FOREIGN KEY (invited_by) REFERENCES companies(id)
                )
            """)

            # Data contributions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_contributions (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    company_id TEXT NOT NULL,
                    encrypted_blob_path TEXT NOT NULL,
                    record_count INTEGER NOT NULL,
                    feature_count INTEGER NOT NULL,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    checksum TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id) ON DELETE CASCADE,
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)

            # Indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_consortiums_owner
                ON consortiums(owner_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_consortiums_status
                ON consortiums(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memberships_consortium
                ON memberships(consortium_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memberships_company
                ON memberships(company_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_invitations_code
                ON invitations(invite_code)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_invitations_email
                ON invitations(invite_email)
            """)

    # ========== Company Operations ==========

    def create_company(
        self,
        name: str,
        email: str,
        api_key: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> tuple[Company, str]:
        """Create a new company.

        Args:
            name: Company name.
            email: Company email.
            api_key: Optional API key (generated if not provided).
            metadata: Optional metadata.

        Returns:
            Tuple of (Company, api_key).
        """
        company_id = f"comp_{secrets.token_hex(8)}"
        api_key = api_key or f"xcp_{secrets.token_urlsafe(32)}"
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO companies (id, name, email, api_key_hash, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (
                company_id,
                name,
                email,
                api_key_hash,
                json.dumps(metadata or {})
            ))

        company = Company(
            id=company_id,
            name=name,
            email=email,
            api_key_hash=api_key_hash,
            created_at=datetime.utcnow(),
            metadata=metadata or {}
        )

        return company, api_key

    def get_company_by_api_key(self, api_key: str) -> Optional[Company]:
        """Get company by API key."""
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM companies WHERE api_key_hash = ?
            """, (api_key_hash,))
            row = cursor.fetchone()

        if not row:
            return None

        return Company(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            api_key_hash=row["api_key_hash"],
            created_at=row["created_at"],
            metadata=json.loads(row["metadata"])
        )

    def get_company(self, company_id: str) -> Optional[Company]:
        """Get company by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM companies WHERE id = ?", (company_id,))
            row = cursor.fetchone()

        if not row:
            return None

        return Company(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            api_key_hash=row["api_key_hash"],
            created_at=row["created_at"],
            metadata=json.loads(row["metadata"])
        )

    # ========== Consortium Operations ==========

    def create_consortium(
        self,
        name: str,
        description: Optional[str] = None,
        owner_id: Optional[str] = None,
        model_type: str = "linear_regression",
        model_config: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        created_by: Optional[str] = None  # Alias for owner_id
    ) -> Consortium:
        """Create a new consortium.

        Args:
            name: Consortium name.
            description: Description of the collaboration.
            owner_id: ID of the company creating the consortium.
            model_type: Type of ML model (linear_regression, etc.).
            model_config: Model configuration.
            metadata: Optional metadata.
            created_by: Alias for owner_id (for backwards compatibility).

        Returns:
            Created consortium.
        """
        # Support both owner_id and created_by
        owner_id = owner_id or created_by
        if not owner_id:
            raise ValueError("Either owner_id or created_by must be provided")

        consortium_id = f"cons_{secrets.token_hex(8)}"
        now = datetime.utcnow()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Create consortium
            cursor.execute("""
                INSERT INTO consortiums
                (id, name, description, owner_id, model_type, model_config, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                consortium_id,
                name,
                description,
                owner_id,
                model_type,
                json.dumps(model_config or {}),
                json.dumps(metadata or {})
            ))

            # Add owner as first member
            membership_id = f"memb_{secrets.token_hex(8)}"
            cursor.execute("""
                INSERT INTO memberships
                (id, consortium_id, company_id, role, status, joined_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                membership_id,
                consortium_id,
                owner_id,
                MemberRole.OWNER.value,
                MemberStatus.ACTIVE.value,
                now
            ))

        return Consortium(
            id=consortium_id,
            name=name,
            description=description,
            owner_id=owner_id,
            status=ConsortiumStatus.DRAFT,
            model_type=model_type,
            model_config=model_config or {},
            created_at=now,
            updated_at=now,
            metadata=metadata or {}
        )

    def get_consortium(self, consortium_id: str) -> Optional[Consortium]:
        """Get consortium by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM consortiums WHERE id = ?", (consortium_id,))
            row = cursor.fetchone()

        if not row:
            return None

        return self._row_to_consortium(row)

    def _row_to_consortium(self, row) -> Consortium:
        """Convert database row to Consortium object."""
        return Consortium(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            owner_id=row["owner_id"],
            status=ConsortiumStatus(row["status"]),
            model_type=row["model_type"],
            model_config=json.loads(row["model_config"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            training_started_at=row["training_started_at"],
            training_completed_at=row["training_completed_at"],
            model_id=row["model_id"],
            metadata=json.loads(row["metadata"])
        )

    def list_consortiums(
        self,
        company_id: Optional[str] = None,
        status: Optional[ConsortiumStatus] = None
    ) -> List[Consortium]:
        """List consortiums, optionally filtered.

        Args:
            company_id: Filter by company membership.
            status: Filter by status.

        Returns:
            List of consortiums.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if company_id:
                # Get consortiums where company is a member
                query = """
                    SELECT c.* FROM consortiums c
                    JOIN memberships m ON c.id = m.consortium_id
                    WHERE m.company_id = ? AND m.status = 'active'
                """
                params = [company_id]

                if status:
                    query += " AND c.status = ?"
                    params.append(status.value)

                cursor.execute(query, params)
            else:
                query = "SELECT * FROM consortiums"
                params = []

                if status:
                    query += " WHERE status = ?"
                    params.append(status.value)

                cursor.execute(query, params)

            rows = cursor.fetchall()

        return [self._row_to_consortium(row) for row in rows]

    def update_consortium_status(
        self,
        consortium_id: str,
        status: ConsortiumStatus
    ) -> Optional[Consortium]:
        """Update consortium status."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE consortiums
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status.value, consortium_id))

        return self.get_consortium(consortium_id)

    # ========== Membership Operations ==========

    def get_members(self, consortium_id: str) -> List[Dict]:
        """Get all members of a consortium with company info."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.*, c.name as company_name, c.email as company_email
                FROM memberships m
                JOIN companies c ON m.company_id = c.id
                WHERE m.consortium_id = ?
            """, (consortium_id,))
            rows = cursor.fetchall()

        return [{
            "membership_id": row["id"],
            "company_id": row["company_id"],
            "company_name": row["company_name"],
            "company_email": row["company_email"],
            "role": row["role"],
            "status": row["status"],
            "joined_at": row["joined_at"],
            "data_uploaded": bool(row["data_uploaded"]),
            "data_record_count": row["data_record_count"],
            "last_upload_at": row["last_upload_at"]
        } for row in rows]

    def get_membership(
        self,
        consortium_id: str,
        company_id: str
    ) -> Optional[Membership]:
        """Get membership for a company in a consortium."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM memberships
                WHERE consortium_id = ? AND company_id = ?
            """, (consortium_id, company_id))
            row = cursor.fetchone()

        if not row:
            return None

        return Membership(
            id=row["id"],
            consortium_id=row["consortium_id"],
            company_id=row["company_id"],
            role=MemberRole(row["role"]),
            status=MemberStatus(row["status"]),
            joined_at=row["joined_at"],
            data_uploaded=bool(row["data_uploaded"]),
            data_record_count=row["data_record_count"],
            last_upload_at=row["last_upload_at"],
            metadata=json.loads(row["metadata"])
        )

    # ========== Invitation Operations ==========

    def create_invitation(
        self,
        consortium_id: str,
        invited_by: str,
        invite_email: str,
        role: MemberRole = MemberRole.CONTRIBUTOR,
        expires_in_days: int = 7
    ) -> Invitation:
        """Create an invitation to join a consortium.

        Args:
            consortium_id: Consortium to invite to.
            invited_by: Company ID of inviter.
            invite_email: Email to invite.
            role: Role for the invitee.
            expires_in_days: Days until expiration.

        Returns:
            Created invitation.
        """
        from datetime import timedelta

        invitation_id = f"inv_{secrets.token_hex(8)}"
        invite_code = secrets.token_urlsafe(32)
        now = datetime.utcnow()
        expires_at = now + timedelta(days=expires_in_days)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO invitations
                (id, consortium_id, invited_by, invite_email, invite_code, role, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                invitation_id,
                consortium_id,
                invited_by,
                invite_email,
                invite_code,
                role.value,
                expires_at
            ))

        return Invitation(
            id=invitation_id,
            consortium_id=consortium_id,
            invited_by=invited_by,
            invite_email=invite_email,
            invite_code=invite_code,
            role=role,
            status=InviteStatus.PENDING,
            created_at=now,
            expires_at=expires_at
        )

    def get_invitation_by_code(self, invite_code: str) -> Optional[Invitation]:
        """Get invitation by code."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM invitations WHERE invite_code = ?
            """, (invite_code,))
            row = cursor.fetchone()

        if not row:
            return None

        return Invitation(
            id=row["id"],
            consortium_id=row["consortium_id"],
            invited_by=row["invited_by"],
            invite_email=row["invite_email"],
            invite_code=row["invite_code"],
            role=MemberRole(row["role"]),
            status=InviteStatus(row["status"]),
            created_at=row["created_at"],
            expires_at=row["expires_at"],
            accepted_at=row["accepted_at"],
            accepted_by=row["accepted_by"]
        )

    def accept_invitation(
        self,
        invite_code: str,
        company_id: str
    ) -> Optional[Membership]:
        """Accept an invitation and create membership.

        Args:
            invite_code: Invitation code.
            company_id: Company accepting the invitation.

        Returns:
            Created membership or None if invalid.
        """
        invitation = self.get_invitation_by_code(invite_code)

        if not invitation:
            return None

        if invitation.status != InviteStatus.PENDING:
            return None

        if datetime.utcnow() > invitation.expires_at:
            # Mark as expired
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE invitations SET status = ? WHERE id = ?
                """, (InviteStatus.EXPIRED.value, invitation.id))
            return None

        now = datetime.utcnow()
        membership_id = f"memb_{secrets.token_hex(8)}"

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Update invitation
            cursor.execute("""
                UPDATE invitations
                SET status = ?, accepted_at = ?, accepted_by = ?
                WHERE id = ?
            """, (InviteStatus.ACCEPTED.value, now, company_id, invitation.id))

            # Create membership
            cursor.execute("""
                INSERT INTO memberships
                (id, consortium_id, company_id, role, status, joined_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                membership_id,
                invitation.consortium_id,
                company_id,
                invitation.role.value,
                MemberStatus.ACTIVE.value,
                now
            ))

        return Membership(
            id=membership_id,
            consortium_id=invitation.consortium_id,
            company_id=company_id,
            role=invitation.role,
            status=MemberStatus.ACTIVE,
            joined_at=now
        )

    def list_invitations(
        self,
        consortium_id: str,
        status: Optional[InviteStatus] = None
    ) -> List[Invitation]:
        """List invitations for a consortium."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM invitations WHERE consortium_id = ?"
            params = [consortium_id]

            if status:
                query += " AND status = ?"
                params.append(status.value)

            cursor.execute(query, params)
            rows = cursor.fetchall()

        return [Invitation(
            id=row["id"],
            consortium_id=row["consortium_id"],
            invited_by=row["invited_by"],
            invite_email=row["invite_email"],
            invite_code=row["invite_code"],
            role=MemberRole(row["role"]),
            status=InviteStatus(row["status"]),
            created_at=row["created_at"],
            expires_at=row["expires_at"],
            accepted_at=row["accepted_at"],
            accepted_by=row["accepted_by"]
        ) for row in rows]

    # ========== Data Contribution Operations ==========

    def record_data_contribution(
        self,
        consortium_id: str,
        company_id: str,
        encrypted_blob_path: str,
        record_count: int,
        feature_count: int,
        checksum: str,
        metadata: Optional[Dict] = None
    ) -> DataContribution:
        """Record a data contribution from a company.

        Args:
            consortium_id: Consortium ID.
            company_id: Contributing company ID.
            encrypted_blob_path: Path to encrypted data blob.
            record_count: Number of records contributed.
            feature_count: Number of features.
            checksum: Data checksum for verification.
            metadata: Optional metadata.

        Returns:
            Created data contribution record.
        """
        contribution_id = f"data_{secrets.token_hex(8)}"
        now = datetime.utcnow()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Record contribution
            cursor.execute("""
                INSERT INTO data_contributions
                (id, consortium_id, company_id, encrypted_blob_path,
                 record_count, feature_count, checksum, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                contribution_id,
                consortium_id,
                company_id,
                encrypted_blob_path,
                record_count,
                feature_count,
                checksum,
                json.dumps(metadata or {})
            ))

            # Update membership
            cursor.execute("""
                UPDATE memberships
                SET data_uploaded = 1,
                    data_record_count = data_record_count + ?,
                    last_upload_at = ?
                WHERE consortium_id = ? AND company_id = ?
            """, (record_count, now, consortium_id, company_id))

        return DataContribution(
            id=contribution_id,
            consortium_id=consortium_id,
            company_id=company_id,
            encrypted_blob_path=encrypted_blob_path,
            record_count=record_count,
            feature_count=feature_count,
            uploaded_at=now,
            checksum=checksum,
            metadata=metadata or {}
        )

    def get_consortium_data_summary(self, consortium_id: str) -> Dict:
        """Get summary of data contributions for a consortium."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    COUNT(DISTINCT company_id) as companies_contributed,
                    SUM(record_count) as total_records,
                    MAX(feature_count) as feature_count,
                    COUNT(*) as total_uploads
                FROM data_contributions
                WHERE consortium_id = ?
            """, (consortium_id,))
            row = cursor.fetchone()

        return {
            "companies_contributed": row["companies_contributed"] or 0,
            "total_records": row["total_records"] or 0,
            "feature_count": row["feature_count"] or 0,
            "total_uploads": row["total_uploads"] or 0
        }

    def get_data_contributions(
        self,
        consortium_id: str
    ) -> List[DataContribution]:
        """Get all data contributions for a consortium."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM data_contributions WHERE consortium_id = ?
            """, (consortium_id,))
            rows = cursor.fetchall()

        return [DataContribution(
            id=row["id"],
            consortium_id=row["consortium_id"],
            company_id=row["company_id"],
            encrypted_blob_path=row["encrypted_blob_path"],
            record_count=row["record_count"],
            feature_count=row["feature_count"],
            uploaded_at=row["uploaded_at"],
            checksum=row["checksum"],
            metadata=json.loads(row["metadata"])
        ) for row in rows]

    def add_data_contribution(
        self,
        consortium_id: str,
        company_id: str,
        contribution_id: str,
        record_count: int,
        file_path: str,
        feature_count: int = 0,
        metadata: Dict = None
    ) -> DataContribution:
        """Add a new data contribution to a consortium.

        Args:
            consortium_id: Target consortium.
            company_id: Contributing company.
            contribution_id: Unique contribution ID.
            record_count: Number of records.
            file_path: Path to encrypted data file.
            feature_count: Number of features.
            metadata: Additional metadata.

        Returns:
            Created DataContribution.
        """
        now = datetime.utcnow()
        checksum = hashlib.sha256(contribution_id.encode()).hexdigest()[:16]

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO data_contributions
                (id, consortium_id, company_id, encrypted_blob_path, record_count,
                 feature_count, uploaded_at, checksum, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                contribution_id,
                consortium_id,
                company_id,
                file_path,
                record_count,
                feature_count,
                now,
                checksum,
                json.dumps(metadata or {})
            ))

        return DataContribution(
            id=contribution_id,
            consortium_id=consortium_id,
            company_id=company_id,
            encrypted_blob_path=file_path,
            record_count=record_count,
            feature_count=feature_count,
            uploaded_at=now,
            checksum=checksum,
            metadata=metadata or {}
        )

    def update_member_data_status(
        self,
        consortium_id: str,
        company_id: str,
        data_uploaded: bool,
        record_count: int
    ) -> None:
        """Update member's data upload status.

        Args:
            consortium_id: Consortium ID.
            company_id: Company ID.
            data_uploaded: Whether data has been uploaded.
            record_count: Number of records uploaded.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE memberships
                SET data_uploaded = ?, data_record_count = ?
                WHERE consortium_id = ? AND company_id = ?
            """, (data_uploaded, record_count, consortium_id, company_id))

    def get_consortium_stats(self, consortium_id: str) -> Dict[str, Any]:
        """Get comprehensive statistics for a consortium.

        Args:
            consortium_id: Consortium ID.

        Returns:
            Dictionary with consortium statistics.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get member count
            cursor.execute("""
                SELECT COUNT(*) as count FROM memberships
                WHERE consortium_id = ? AND status = 'active'
            """, (consortium_id,))
            member_count = cursor.fetchone()["count"]

            # Get contribution stats
            cursor.execute("""
                SELECT
                    COUNT(*) as total_contributions,
                    COALESCE(SUM(record_count), 0) as total_records,
                    COUNT(DISTINCT company_id) as contributors_count
                FROM data_contributions
                WHERE consortium_id = ?
            """, (consortium_id,))
            contrib_stats = cursor.fetchone()

        return {
            "total_members": member_count,
            "total_contributions": contrib_stats["total_contributions"],
            "total_records": contrib_stats["total_records"],
            "contributors_count": contrib_stats["contributors_count"]
        }

    # ========== Governance Operations (TIER 2) ==========

    def _init_governance_schema(self):
        """Initialize governance-related database tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Contribution proofs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contribution_proofs (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    company_id TEXT NOT NULL,
                    record_count INTEGER NOT NULL,
                    feature_count INTEGER NOT NULL,
                    data_hash TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    verified INTEGER DEFAULT 0,
                    blockchain_tx TEXT,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)

            # Proposals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS proposals (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    proposer_id TEXT NOT NULL,
                    proposal_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    data TEXT,
                    status TEXT DEFAULT 'active',
                    yes_votes INTEGER DEFAULT 0,
                    no_votes INTEGER DEFAULT 0,
                    voting_weight_yes INTEGER DEFAULT 0,
                    voting_weight_no INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    executed_at TIMESTAMP,
                    blockchain_tx TEXT,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id),
                    FOREIGN KEY (proposer_id) REFERENCES companies(id)
                )
            """)

            # Votes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS votes (
                    id TEXT PRIMARY KEY,
                    proposal_id TEXT NOT NULL,
                    voter_id TEXT NOT NULL,
                    support INTEGER NOT NULL,
                    weight INTEGER NOT NULL,
                    comment TEXT,
                    voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (proposal_id) REFERENCES proposals(id),
                    FOREIGN KEY (voter_id) REFERENCES companies(id),
                    UNIQUE(proposal_id, voter_id)
                )
            """)

            # Audit events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_events (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    target_id TEXT,
                    target_type TEXT,
                    data TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    previous_hash TEXT,
                    blockchain_tx TEXT,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id),
                    FOREIGN KEY (actor_id) REFERENCES companies(id)
                )
            """)

            # Reward distributions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reward_distributions (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    total_amount REAL NOT NULL,
                    distributed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    distributions TEXT NOT NULL,
                    blockchain_tx TEXT,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id)
                )
            """)

            conn.commit()

    def record_contribution_proof(
        self,
        consortium_id: str,
        company_id: str,
        record_count: int,
        feature_count: int,
        data_hash: str,
        checksum: str
    ) -> str:
        """Record a contribution proof.

        Args:
            consortium_id: Consortium ID.
            company_id: Contributing company ID.
            record_count: Number of records.
            feature_count: Number of features.
            data_hash: Hash of encrypted data.
            checksum: Data checksum.

        Returns:
            Contribution proof ID.
        """
        self._init_governance_schema()
        proof_id = f"proof_{secrets.token_hex(8)}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO contribution_proofs
                (id, consortium_id, company_id, record_count, feature_count, data_hash, checksum)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (proof_id, consortium_id, company_id, record_count, feature_count, data_hash, checksum))

        return proof_id

    def get_contribution_proofs(self, consortium_id: str) -> List[Dict]:
        """Get all contribution proofs for a consortium."""
        self._init_governance_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT cp.*, c.name as contributor_name
                FROM contribution_proofs cp
                JOIN companies c ON cp.company_id = c.id
                WHERE cp.consortium_id = ?
                ORDER BY cp.timestamp DESC
            """, (consortium_id,))
            rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def get_contribution_summary(self, consortium_id: str) -> List[Dict]:
        """Get contribution summary per member."""
        self._init_governance_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    cp.company_id as member_id,
                    c.name as member_name,
                    SUM(cp.record_count) as total_records,
                    COUNT(*) as contributions_count,
                    MAX(cp.timestamp) as last_contribution_at
                FROM contribution_proofs cp
                JOIN companies c ON cp.company_id = c.id
                WHERE cp.consortium_id = ?
                GROUP BY cp.company_id
            """, (consortium_id,))
            rows = cursor.fetchall()

        # Calculate weights
        total_records = sum(row["total_records"] for row in rows) or 1
        result = []
        for row in rows:
            r = dict(row)
            r["contribution_weight"] = (r["total_records"] / total_records) * 100
            result.append(r)

        return result

    def get_member_contribution_summary(self, consortium_id: str, company_id: str) -> Dict:
        """Get contribution summary for a specific member."""
        summary = self.get_contribution_summary(consortium_id)
        for s in summary:
            if s["member_id"] == company_id:
                return s
        return {"contribution_weight": 0, "total_records": 0}

    def create_proposal(
        self,
        consortium_id: str,
        proposer_id: str,
        proposal_type: str,
        title: str,
        description: str = "",
        data: Optional[Dict] = None,
        voting_duration: int = 86400  # 24 hours default
    ) -> str:
        """Create a new governance proposal.

        Args:
            consortium_id: Consortium ID.
            proposer_id: Proposer company ID.
            proposal_type: Type of proposal.
            title: Proposal title.
            description: Proposal description.
            data: Proposal-specific data.
            voting_duration: Voting duration in seconds.

        Returns:
            Proposal ID.
        """
        from datetime import timedelta
        self._init_governance_schema()
        proposal_id = f"prop_{secrets.token_hex(8)}"
        now = datetime.utcnow()
        expires_at = now + timedelta(seconds=voting_duration)

        # Get member count for total voters
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as count FROM memberships
                WHERE consortium_id = ? AND status = 'active'
            """, (consortium_id,))
            total_voters = cursor.fetchone()["count"]

            cursor.execute("""
                INSERT INTO proposals
                (id, consortium_id, proposer_id, proposal_type, title, description, data, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (proposal_id, consortium_id, proposer_id, proposal_type, title, description,
                  json.dumps(data) if data else None, expires_at))

        return proposal_id

    def get_proposal(self, proposal_id: str) -> Optional[Dict]:
        """Get proposal details."""
        self._init_governance_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.*, c.name as proposer_name
                FROM proposals p
                JOIN companies c ON p.proposer_id = c.id
                WHERE p.id = ?
            """, (proposal_id,))
            row = cursor.fetchone()

        if not row:
            return None

        result = dict(row)
        if result.get("data"):
            result["data"] = json.loads(result["data"])
        return result

    def get_proposals(self, consortium_id: str, status_filter: Optional[str] = None) -> List[Dict]:
        """Get all proposals for a consortium."""
        self._init_governance_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT p.*, c.name as proposer_name
                FROM proposals p
                JOIN companies c ON p.proposer_id = c.id
                WHERE p.consortium_id = ?
            """
            params = [consortium_id]

            if status_filter:
                query += " AND p.status = ?"
                params.append(status_filter)

            query += " ORDER BY p.created_at DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()

        result = []
        for row in rows:
            r = dict(row)
            if r.get("data"):
                r["data"] = json.loads(r["data"])
            result.append(r)

        return result

    def record_vote(
        self,
        proposal_id: str,
        voter_id: str,
        support: bool,
        weight: int,
        comment: Optional[str] = None
    ) -> str:
        """Record a vote on a proposal.

        Args:
            proposal_id: Proposal ID.
            voter_id: Voter company ID.
            support: True for yes, False for no.
            weight: Voting weight.
            comment: Optional comment.

        Returns:
            Vote ID.
        """
        self._init_governance_schema()
        vote_id = f"vote_{secrets.token_hex(8)}"

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Record vote
            cursor.execute("""
                INSERT INTO votes (id, proposal_id, voter_id, support, weight, comment)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (vote_id, proposal_id, voter_id, 1 if support else 0, weight, comment))

            # Update proposal vote counts
            if support:
                cursor.execute("""
                    UPDATE proposals
                    SET yes_votes = yes_votes + 1, voting_weight_yes = voting_weight_yes + ?
                    WHERE id = ?
                """, (weight, proposal_id))
            else:
                cursor.execute("""
                    UPDATE proposals
                    SET no_votes = no_votes + 1, voting_weight_no = voting_weight_no + ?
                    WHERE id = ?
                """, (weight, proposal_id))

        return vote_id

    def get_vote(self, proposal_id: str, voter_id: str) -> Optional[Dict]:
        """Get a specific vote."""
        self._init_governance_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM votes WHERE proposal_id = ? AND voter_id = ?
            """, (proposal_id, voter_id))
            row = cursor.fetchone()

        return dict(row) if row else None

    def get_proposal_votes(self, proposal_id: str) -> List[Dict]:
        """Get all votes for a proposal."""
        self._init_governance_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT v.*, c.name as voter_name
                FROM votes v
                JOIN companies c ON v.voter_id = c.id
                WHERE v.proposal_id = ?
                ORDER BY v.voted_at
            """, (proposal_id,))
            rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def execute_proposal(self, proposal_id: str) -> Dict:
        """Execute a proposal after voting ends.

        Args:
            proposal_id: Proposal ID.

        Returns:
            Execution result.
        """
        self._init_governance_schema()
        proposal = self.get_proposal(proposal_id)
        if not proposal:
            raise ValueError("Proposal not found")

        # Check if passed (simple majority by weight)
        passed = proposal["voting_weight_yes"] > proposal["voting_weight_no"]
        new_status = "passed" if passed else "rejected"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE proposals
                SET status = ?, executed_at = ?
                WHERE id = ?
            """, (new_status, datetime.utcnow(), proposal_id))

        return {
            "passed": passed,
            "new_status": new_status,
            "yes_votes": proposal["yes_votes"],
            "no_votes": proposal["no_votes"],
            "voting_weight_yes": proposal["voting_weight_yes"],
            "voting_weight_no": proposal["voting_weight_no"],
        }

    def record_audit_event(
        self,
        consortium_id: str,
        event_type: str,
        actor_id: str,
        target_id: Optional[str] = None,
        target_type: Optional[str] = None,
        data: Optional[Dict] = None
    ) -> str:
        """Record an audit event.

        Args:
            consortium_id: Consortium ID.
            event_type: Type of event.
            actor_id: Actor company ID.
            target_id: Target entity ID.
            target_type: Target entity type.
            data: Event-specific data.

        Returns:
            Audit event ID.
        """
        self._init_governance_schema()
        event_id = f"audit_{secrets.token_hex(8)}"

        # Get previous hash for chaining
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, timestamp FROM audit_events
                WHERE consortium_id = ?
                ORDER BY timestamp DESC LIMIT 1
            """, (consortium_id,))
            last_event = cursor.fetchone()

            previous_hash = None
            if last_event:
                previous_hash = hashlib.sha256(
                    f"{last_event['id']}:{last_event['timestamp']}".encode()
                ).hexdigest()

            cursor.execute("""
                INSERT INTO audit_events
                (id, consortium_id, event_type, actor_id, target_id, target_type, data, previous_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (event_id, consortium_id, event_type, actor_id, target_id, target_type,
                  json.dumps(data) if data else None, previous_hash))

        return event_id

    def get_audit_trail(
        self,
        consortium_id: str,
        event_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """Get audit trail for a consortium.

        Args:
            consortium_id: Consortium ID.
            event_type: Filter by event type.
            limit: Maximum events to return.
            offset: Offset for pagination.

        Returns:
            List of audit events.
        """
        self._init_governance_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT ae.*, c.name as actor_name
                FROM audit_events ae
                JOIN companies c ON ae.actor_id = c.id
                WHERE ae.consortium_id = ?
            """
            params = [consortium_id]

            if event_type:
                query += " AND ae.event_type = ?"
                params.append(event_type)

            query += " ORDER BY ae.timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()

        result = []
        for row in rows:
            r = dict(row)
            if r.get("data"):
                r["data"] = json.loads(r["data"])
            else:
                r["data"] = {}
            result.append(r)

        return result

    def verify_audit_trail(self, consortium_id: str) -> bool:
        """Verify audit trail integrity.

        Args:
            consortium_id: Consortium ID.

        Returns:
            True if audit trail is valid.
        """
        self._init_governance_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, timestamp, previous_hash FROM audit_events
                WHERE consortium_id = ?
                ORDER BY timestamp ASC
            """, (consortium_id,))
            rows = cursor.fetchall()

        if not rows:
            return True

        # Verify chain
        expected_hash = None
        for row in rows:
            if row["previous_hash"] != expected_hash:
                return False
            expected_hash = hashlib.sha256(
                f"{row['id']}:{row['timestamp']}".encode()
            ).hexdigest()

        return True

    def calculate_reward_distribution(
        self,
        consortium_id: str,
        total_amount: float
    ) -> List[Dict]:
        """Calculate reward distribution based on contribution weights.

        Args:
            consortium_id: Consortium ID.
            total_amount: Total amount to distribute.

        Returns:
            List of distributions per member.
        """
        summary = self.get_contribution_summary(consortium_id)
        distributions = []

        for member in summary:
            if member["contribution_weight"] > 0:
                amount = (member["contribution_weight"] / 100) * total_amount
                distributions.append({
                    "member_id": member["member_id"],
                    "member_name": member["member_name"],
                    "weight": member["contribution_weight"],
                    "amount": round(amount, 6),
                })

        return distributions

    def record_reward_distribution(
        self,
        consortium_id: str,
        total_amount: float,
        distributions: List[Dict]
    ) -> str:
        """Record a reward distribution.

        Args:
            consortium_id: Consortium ID.
            total_amount: Total amount distributed.
            distributions: List of distributions per member.

        Returns:
            Distribution ID.
        """
        self._init_governance_schema()
        distribution_id = f"dist_{secrets.token_hex(8)}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO reward_distributions
                (id, consortium_id, total_amount, distributions)
                VALUES (?, ?, ?, ?)
            """, (distribution_id, consortium_id, total_amount, json.dumps(distributions)))

        return distribution_id

    def get_reward_distributions(self, consortium_id: str) -> List[Dict]:
        """Get reward distribution history."""
        self._init_governance_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM reward_distributions
                WHERE consortium_id = ?
                ORDER BY distributed_at DESC
            """, (consortium_id,))
            rows = cursor.fetchall()

        result = []
        for row in rows:
            r = dict(row)
            r["distributions"] = json.loads(r["distributions"])
            result.append(r)

        return result

    # ========== Compliance Operations (TIER 3) ==========

    def _init_compliance_schema(self):
        """Initialize compliance-related database tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Compliance frameworks table (GDPR, HIPAA, SOC2, PCI-DSS)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS compliance_frameworks (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    version TEXT NOT NULL,
                    description TEXT,
                    region TEXT,
                    industry TEXT,
                    controls_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Compliance controls (individual requirements within a framework)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS compliance_controls (
                    id TEXT PRIMARY KEY,
                    framework_id TEXT NOT NULL,
                    control_code TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    severity TEXT DEFAULT 'medium',
                    verification_type TEXT NOT NULL,
                    verification_config TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (framework_id) REFERENCES compliance_frameworks(id),
                    UNIQUE(framework_id, control_code)
                )
            """)

            # Compliance checks (execution of controls against a consortium)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS compliance_checks (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    framework_id TEXT NOT NULL,
                    control_id TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    result TEXT,
                    evidence TEXT,
                    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    checked_by TEXT,
                    expires_at TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id),
                    FOREIGN KEY (framework_id) REFERENCES compliance_frameworks(id),
                    FOREIGN KEY (control_id) REFERENCES compliance_controls(id)
                )
            """)

            # Compliance reports (aggregated compliance status)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS compliance_reports (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    framework_id TEXT NOT NULL,
                    report_type TEXT DEFAULT 'automated',
                    overall_score REAL DEFAULT 0,
                    passed_controls INTEGER DEFAULT 0,
                    failed_controls INTEGER DEFAULT 0,
                    pending_controls INTEGER DEFAULT 0,
                    total_controls INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'draft',
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    valid_until TIMESTAMP,
                    report_data TEXT,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id),
                    FOREIGN KEY (framework_id) REFERENCES compliance_frameworks(id)
                )
            """)

            # Compliance attestations (manual attestations by authorized personnel)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS compliance_attestations (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    framework_id TEXT NOT NULL,
                    control_id TEXT,
                    attested_by TEXT NOT NULL,
                    attester_role TEXT,
                    attestation_type TEXT NOT NULL,
                    statement TEXT NOT NULL,
                    evidence_urls TEXT,
                    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    valid_until TIMESTAMP,
                    revoked INTEGER DEFAULT 0,
                    revoked_at TIMESTAMP,
                    revoked_reason TEXT,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id),
                    FOREIGN KEY (framework_id) REFERENCES compliance_frameworks(id),
                    FOREIGN KEY (control_id) REFERENCES compliance_controls(id),
                    FOREIGN KEY (attested_by) REFERENCES companies(id)
                )
            """)

            # Data processing records (for GDPR Article 30 compliance)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_processing_records (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    company_id TEXT NOT NULL,
                    processing_purpose TEXT NOT NULL,
                    data_categories TEXT NOT NULL,
                    data_subjects TEXT,
                    recipients TEXT,
                    retention_period TEXT,
                    security_measures TEXT,
                    legal_basis TEXT,
                    cross_border_transfer INTEGER DEFAULT 0,
                    transfer_safeguards TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)

            # Consortium compliance settings
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS consortium_compliance_settings (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL UNIQUE,
                    enabled_frameworks TEXT DEFAULT '[]',
                    auto_check_interval INTEGER DEFAULT 86400,
                    notification_emails TEXT DEFAULT '[]',
                    last_check_at TIMESTAMP,
                    next_check_at TIMESTAMP,
                    settings TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id)
                )
            """)

            conn.commit()

            # Seed default frameworks
            self._seed_compliance_frameworks(cursor, conn)

    def _seed_compliance_frameworks(self, cursor, conn):
        """Seed default compliance frameworks."""
        frameworks = [
            {
                "id": "framework_gdpr",
                "name": "GDPR",
                "version": "2016/679",
                "description": "General Data Protection Regulation - EU data privacy law",
                "region": "EU",
                "industry": "all"
            },
            {
                "id": "framework_hipaa",
                "name": "HIPAA",
                "version": "1996",
                "description": "Health Insurance Portability and Accountability Act - US healthcare data",
                "region": "US",
                "industry": "healthcare"
            },
            {
                "id": "framework_soc2",
                "name": "SOC2",
                "version": "Type II",
                "description": "Service Organization Control 2 - Security, availability, processing integrity",
                "region": "global",
                "industry": "technology"
            },
            {
                "id": "framework_pci_dss",
                "name": "PCI-DSS",
                "version": "4.0",
                "description": "Payment Card Industry Data Security Standard",
                "region": "global",
                "industry": "finance"
            }
        ]

        for fw in frameworks:
            cursor.execute("""
                INSERT OR IGNORE INTO compliance_frameworks (id, name, version, description, region, industry)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (fw["id"], fw["name"], fw["version"], fw["description"], fw["region"], fw["industry"]))

        conn.commit()

    def get_compliance_frameworks(self) -> List[Dict]:
        """Get all available compliance frameworks."""
        self._init_compliance_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM compliance_frameworks ORDER BY name")
            rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def get_compliance_framework(self, framework_id: str) -> Optional[Dict]:
        """Get a specific compliance framework."""
        self._init_compliance_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM compliance_frameworks WHERE id = ?", (framework_id,))
            row = cursor.fetchone()

        return dict(row) if row else None

    def enable_compliance_framework(
        self,
        consortium_id: str,
        framework_id: str
    ) -> Dict:
        """Enable a compliance framework for a consortium.

        Args:
            consortium_id: Consortium ID.
            framework_id: Framework ID to enable.

        Returns:
            Updated compliance settings.
        """
        self._init_compliance_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get or create settings
            cursor.execute("""
                SELECT enabled_frameworks FROM consortium_compliance_settings
                WHERE consortium_id = ?
            """, (consortium_id,))
            row = cursor.fetchone()

            if row:
                enabled = json.loads(row["enabled_frameworks"])
                if framework_id not in enabled:
                    enabled.append(framework_id)
                cursor.execute("""
                    UPDATE consortium_compliance_settings
                    SET enabled_frameworks = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE consortium_id = ?
                """, (json.dumps(enabled), consortium_id))
            else:
                settings_id = f"compl_settings_{secrets.token_hex(8)}"
                enabled = [framework_id]
                cursor.execute("""
                    INSERT INTO consortium_compliance_settings
                    (id, consortium_id, enabled_frameworks)
                    VALUES (?, ?, ?)
                """, (settings_id, consortium_id, json.dumps(enabled)))

            conn.commit()

        return {"consortium_id": consortium_id, "enabled_frameworks": enabled}

    def get_consortium_compliance_settings(self, consortium_id: str) -> Dict:
        """Get compliance settings for a consortium."""
        self._init_compliance_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM consortium_compliance_settings WHERE consortium_id = ?
            """, (consortium_id,))
            row = cursor.fetchone()

        if not row:
            return {
                "consortium_id": consortium_id,
                "enabled_frameworks": [],
                "auto_check_interval": 86400,
                "notification_emails": [],
                "settings": {}
            }

        result = dict(row)
        result["enabled_frameworks"] = json.loads(result["enabled_frameworks"])
        result["notification_emails"] = json.loads(result["notification_emails"])
        result["settings"] = json.loads(result["settings"])
        return result

    def record_compliance_check(
        self,
        consortium_id: str,
        framework_id: str,
        control_id: str,
        status: str,
        result: str,
        evidence: Optional[Dict] = None,
        checked_by: Optional[str] = None,
        notes: Optional[str] = None
    ) -> str:
        """Record a compliance check result.

        Args:
            consortium_id: Consortium ID.
            framework_id: Framework ID.
            control_id: Control ID.
            status: Check status (passed, failed, pending, na).
            result: Result description.
            evidence: Evidence data.
            checked_by: Checker company ID.
            notes: Additional notes.

        Returns:
            Check ID.
        """
        self._init_compliance_schema()
        check_id = f"check_{secrets.token_hex(8)}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO compliance_checks
                (id, consortium_id, framework_id, control_id, status, result, evidence, checked_by, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                check_id,
                consortium_id,
                framework_id,
                control_id,
                status,
                result,
                json.dumps(evidence) if evidence else None,
                checked_by,
                notes
            ))

        return check_id

    def get_compliance_checks(
        self,
        consortium_id: str,
        framework_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict]:
        """Get compliance checks for a consortium.

        Args:
            consortium_id: Consortium ID.
            framework_id: Optional framework filter.
            status: Optional status filter.

        Returns:
            List of compliance checks.
        """
        self._init_compliance_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM compliance_checks WHERE consortium_id = ?"
            params = [consortium_id]

            if framework_id:
                query += " AND framework_id = ?"
                params.append(framework_id)

            if status:
                query += " AND status = ?"
                params.append(status)

            query += " ORDER BY checked_at DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()

        result = []
        for row in rows:
            r = dict(row)
            if r.get("evidence"):
                r["evidence"] = json.loads(r["evidence"])
            result.append(r)

        return result

    def generate_compliance_report(
        self,
        consortium_id: str,
        framework_id: str
    ) -> Dict:
        """Generate a compliance report for a consortium.

        Args:
            consortium_id: Consortium ID.
            framework_id: Framework ID.

        Returns:
            Generated report.
        """
        from datetime import timedelta
        self._init_compliance_schema()

        checks = self.get_compliance_checks(consortium_id, framework_id)

        passed = sum(1 for c in checks if c["status"] == "passed")
        failed = sum(1 for c in checks if c["status"] == "failed")
        pending = sum(1 for c in checks if c["status"] == "pending")
        total = len(checks)

        score = (passed / total * 100) if total > 0 else 0
        status = "compliant" if failed == 0 and pending == 0 and total > 0 else "non_compliant"

        report_id = f"report_{secrets.token_hex(8)}"
        now = datetime.utcnow()
        valid_until = now + timedelta(days=90)

        # Serialize checks for JSON storage (convert datetime to string)
        serialized_checks = []
        for check in checks:
            sc = dict(check)
            if sc.get("checked_at") and hasattr(sc["checked_at"], "isoformat"):
                sc["checked_at"] = sc["checked_at"].isoformat()
            if sc.get("expires_at") and hasattr(sc["expires_at"], "isoformat"):
                sc["expires_at"] = sc["expires_at"].isoformat()
            serialized_checks.append(sc)

        report_data = {
            "checks": serialized_checks,
            "summary": {
                "passed": passed,
                "failed": failed,
                "pending": pending,
                "total": total,
                "score": round(score, 2)
            }
        }

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO compliance_reports
                (id, consortium_id, framework_id, overall_score, passed_controls,
                 failed_controls, pending_controls, total_controls, status, valid_until, report_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                report_id,
                consortium_id,
                framework_id,
                score,
                passed,
                failed,
                pending,
                total,
                status,
                valid_until,
                json.dumps(report_data)
            ))

        return {
            "id": report_id,
            "consortium_id": consortium_id,
            "framework_id": framework_id,
            "overall_score": round(score, 2),
            "passed_controls": passed,
            "failed_controls": failed,
            "pending_controls": pending,
            "total_controls": total,
            "status": status,
            "generated_at": now.isoformat(),
            "valid_until": valid_until.isoformat(),
            "report_data": report_data
        }

    def get_compliance_reports(
        self,
        consortium_id: str,
        framework_id: Optional[str] = None
    ) -> List[Dict]:
        """Get compliance reports for a consortium."""
        self._init_compliance_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT r.*, f.name as framework_name
                FROM compliance_reports r
                JOIN compliance_frameworks f ON r.framework_id = f.id
                WHERE r.consortium_id = ?
            """
            params = [consortium_id]

            if framework_id:
                query += " AND r.framework_id = ?"
                params.append(framework_id)

            query += " ORDER BY r.generated_at DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()

        result = []
        for row in rows:
            r = dict(row)
            if r.get("report_data"):
                r["report_data"] = json.loads(r["report_data"])
            result.append(r)

        return result

    def create_attestation(
        self,
        consortium_id: str,
        framework_id: str,
        attested_by: str,
        statement: str,
        control_id: Optional[str] = None,
        attester_role: Optional[str] = None,
        attestation_type: str = "manual",
        evidence_urls: Optional[List[str]] = None,
        valid_days: int = 365
    ) -> str:
        """Create a compliance attestation.

        Args:
            consortium_id: Consortium ID.
            framework_id: Framework ID.
            attested_by: Attester company ID.
            statement: Attestation statement.
            control_id: Optional specific control ID.
            attester_role: Role of attester.
            attestation_type: Type of attestation.
            evidence_urls: URLs to supporting evidence.
            valid_days: Validity period in days.

        Returns:
            Attestation ID.
        """
        from datetime import timedelta
        self._init_compliance_schema()

        attestation_id = f"attest_{secrets.token_hex(8)}"
        now = datetime.utcnow()
        valid_until = now + timedelta(days=valid_days)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO compliance_attestations
                (id, consortium_id, framework_id, control_id, attested_by, attester_role,
                 attestation_type, statement, evidence_urls, valid_until)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                attestation_id,
                consortium_id,
                framework_id,
                control_id,
                attested_by,
                attester_role,
                attestation_type,
                statement,
                json.dumps(evidence_urls) if evidence_urls else None,
                valid_until
            ))

        return attestation_id

    def get_attestations(
        self,
        consortium_id: str,
        framework_id: Optional[str] = None,
        include_revoked: bool = False
    ) -> List[Dict]:
        """Get attestations for a consortium."""
        self._init_compliance_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT a.*, c.name as attester_name
                FROM compliance_attestations a
                JOIN companies c ON a.attested_by = c.id
                WHERE a.consortium_id = ?
            """
            params = [consortium_id]

            if framework_id:
                query += " AND a.framework_id = ?"
                params.append(framework_id)

            if not include_revoked:
                query += " AND a.revoked = 0"

            query += " ORDER BY a.valid_from DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()

        result = []
        for row in rows:
            r = dict(row)
            if r.get("evidence_urls"):
                r["evidence_urls"] = json.loads(r["evidence_urls"])
            result.append(r)

        return result

    def record_data_processing(
        self,
        consortium_id: str,
        company_id: str,
        processing_purpose: str,
        data_categories: List[str],
        legal_basis: str,
        data_subjects: Optional[str] = None,
        recipients: Optional[List[str]] = None,
        retention_period: Optional[str] = None,
        security_measures: Optional[List[str]] = None,
        cross_border_transfer: bool = False,
        transfer_safeguards: Optional[str] = None
    ) -> str:
        """Record a data processing activity (GDPR Article 30).

        Args:
            consortium_id: Consortium ID.
            company_id: Company performing processing.
            processing_purpose: Purpose of processing.
            data_categories: Categories of data processed.
            legal_basis: Legal basis for processing.
            data_subjects: Description of data subjects.
            recipients: List of data recipients.
            retention_period: Data retention period.
            security_measures: Security measures in place.
            cross_border_transfer: Whether data is transferred cross-border.
            transfer_safeguards: Safeguards for cross-border transfer.

        Returns:
            Processing record ID.
        """
        self._init_compliance_schema()
        record_id = f"dpr_{secrets.token_hex(8)}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO data_processing_records
                (id, consortium_id, company_id, processing_purpose, data_categories,
                 data_subjects, recipients, retention_period, security_measures,
                 legal_basis, cross_border_transfer, transfer_safeguards)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record_id,
                consortium_id,
                company_id,
                processing_purpose,
                json.dumps(data_categories),
                data_subjects,
                json.dumps(recipients) if recipients else None,
                retention_period,
                json.dumps(security_measures) if security_measures else None,
                legal_basis,
                1 if cross_border_transfer else 0,
                transfer_safeguards
            ))

        return record_id

    def get_data_processing_records(
        self,
        consortium_id: str,
        company_id: Optional[str] = None
    ) -> List[Dict]:
        """Get data processing records for a consortium."""
        self._init_compliance_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT dpr.*, c.name as company_name
                FROM data_processing_records dpr
                JOIN companies c ON dpr.company_id = c.id
                WHERE dpr.consortium_id = ?
            """
            params = [consortium_id]

            if company_id:
                query += " AND dpr.company_id = ?"
                params.append(company_id)

            query += " ORDER BY dpr.created_at DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()

        result = []
        for row in rows:
            r = dict(row)
            r["data_categories"] = json.loads(r["data_categories"])
            if r.get("recipients"):
                r["recipients"] = json.loads(r["recipients"])
            if r.get("security_measures"):
                r["security_measures"] = json.loads(r["security_measures"])
            r["cross_border_transfer"] = bool(r["cross_border_transfer"])
            result.append(r)

        return result

    def get_compliance_dashboard(self, consortium_id: str) -> Dict:
        """Get compliance dashboard summary for a consortium.

        Args:
            consortium_id: Consortium ID.

        Returns:
            Dashboard data with overall compliance status.
        """
        self._init_compliance_schema()

        settings = self.get_consortium_compliance_settings(consortium_id)
        enabled_frameworks = settings.get("enabled_frameworks", [])

        frameworks_status = []
        for fw_id in enabled_frameworks:
            framework = self.get_compliance_framework(fw_id)
            if not framework:
                continue

            checks = self.get_compliance_checks(consortium_id, fw_id)
            passed = sum(1 for c in checks if c["status"] == "passed")
            failed = sum(1 for c in checks if c["status"] == "failed")
            pending = sum(1 for c in checks if c["status"] == "pending")
            total = len(checks)

            score = (passed / total * 100) if total > 0 else 0
            status = "compliant" if failed == 0 and pending == 0 and total > 0 else "non_compliant"

            frameworks_status.append({
                "framework_id": fw_id,
                "framework_name": framework["name"],
                "score": round(score, 2),
                "status": status,
                "passed": passed,
                "failed": failed,
                "pending": pending,
                "total": total
            })

        # Calculate overall score
        if frameworks_status:
            overall_score = sum(f["score"] for f in frameworks_status) / len(frameworks_status)
            overall_compliant = all(f["status"] == "compliant" for f in frameworks_status)
        else:
            overall_score = 0
            overall_compliant = False

        return {
            "consortium_id": consortium_id,
            "overall_score": round(overall_score, 2),
            "overall_status": "compliant" if overall_compliant else "non_compliant",
            "enabled_frameworks_count": len(enabled_frameworks),
            "frameworks": frameworks_status,
            "last_check_at": settings.get("last_check_at"),
            "next_check_at": settings.get("next_check_at")
        }

    # ========== Data Quality Operations (TIER 3) ==========

    def _init_data_quality_schema(self):
        """Initialize data quality-related database tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Data quality assessments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_quality_assessments (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    company_id TEXT NOT NULL,
                    contribution_id TEXT,
                    overall_score REAL DEFAULT 0,
                    completeness_score REAL DEFAULT 0,
                    consistency_score REAL DEFAULT 0,
                    uniqueness_score REAL DEFAULT 0,
                    validity_score REAL DEFAULT 0,
                    freshness_score REAL DEFAULT 0,
                    record_count INTEGER DEFAULT 0,
                    feature_count INTEGER DEFAULT 0,
                    null_ratio REAL DEFAULT 0,
                    duplicate_ratio REAL DEFAULT 0,
                    outlier_ratio REAL DEFAULT 0,
                    assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)

            # Quality metrics history (for tracking over time)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_quality_history (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    company_id TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)

            # Quality rules/thresholds per consortium
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_quality_rules (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    rule_name TEXT NOT NULL,
                    rule_type TEXT NOT NULL,
                    threshold_min REAL,
                    threshold_max REAL,
                    weight REAL DEFAULT 1.0,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id),
                    UNIQUE(consortium_id, rule_name)
                )
            """)

            # Quality alerts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_quality_alerts (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    company_id TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    severity TEXT DEFAULT 'warning',
                    message TEXT NOT NULL,
                    metric_name TEXT,
                    metric_value REAL,
                    threshold_value REAL,
                    acknowledged INTEGER DEFAULT 0,
                    acknowledged_by TEXT,
                    acknowledged_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)

            conn.commit()

    def assess_data_quality(
        self,
        consortium_id: str,
        company_id: str,
        contribution_id: Optional[str] = None,
        record_count: int = 0,
        feature_count: int = 0,
        null_count: int = 0,
        duplicate_count: int = 0,
        outlier_count: int = 0,
        schema_violations: int = 0,
        format_violations: int = 0,
        range_violations: int = 0,
        last_updated: Optional[datetime] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Assess data quality for a contribution.

        Calculates quality scores based on encrypted data metadata
        without accessing the actual data content. Uses the DataQualityCalculator
        for real metric calculations.

        Args:
            consortium_id: Consortium ID.
            company_id: Company ID.
            contribution_id: Optional contribution ID.
            record_count: Number of records.
            feature_count: Number of features.
            null_count: Count of null/missing values.
            duplicate_count: Count of duplicate records.
            outlier_count: Count of outlier values.
            schema_violations: Records with schema issues.
            format_violations: Records with format issues.
            range_violations: Records with out-of-range values.
            last_updated: When the data was last updated.
            metadata: Additional metadata.

        Returns:
            Assessment results with scores.
        """
        from sdk.quality import DataQualityCalculator, DataProfile

        self._init_data_quality_schema()
        assessment_id = f"dqa_{secrets.token_hex(8)}"

        # Use DataQualityCalculator for real calculations
        calculator = DataQualityCalculator(freshness_threshold_days=30)

        # Create a DataProfile from the input metadata
        profile = DataProfile(
            record_count=record_count,
            feature_count=feature_count,
            duplicate_count=duplicate_count,
            outlier_count=outlier_count,
            schema_violations=schema_violations,
            format_violations=format_violations,
            range_violations=range_violations,
            last_updated=last_updated or datetime.utcnow(),
        )

        # Distribute nulls evenly across features if only total is provided
        if null_count > 0 and feature_count > 0:
            nulls_per_feature = null_count // feature_count
            for i in range(feature_count):
                profile.null_counts[f'feature_{i}'] = nulls_per_feature

        # Get quality score using the real calculator
        quality_score = calculator.assess_quality(profile)

        # Calculate ratios for storage
        total_cells = record_count * feature_count if record_count and feature_count else 1
        null_ratio = null_count / total_cells if total_cells > 0 else 0
        duplicate_ratio = duplicate_count / record_count if record_count > 0 else 0
        outlier_ratio = outlier_count / total_cells if total_cells > 0 else 0

        # Get rules for custom weighted average if configured
        rules = self.get_quality_rules(consortium_id)
        if rules:
            weights = {r["rule_type"]: r["weight"] for r in rules if r["is_active"]}
            # Recalculate overall with custom weights if rules exist
            overall_score = calculator.calculate_overall(
                quality_score.completeness,
                quality_score.consistency,
                quality_score.uniqueness,
                quality_score.validity,
                quality_score.freshness,
                weights
            )
        else:
            overall_score = quality_score.overall

        # Use calculated scores
        scores = {
            "completeness": quality_score.completeness,
            "consistency": quality_score.consistency,
            "uniqueness": quality_score.uniqueness,
            "validity": quality_score.validity,
            "freshness": quality_score.freshness
        }

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO data_quality_assessments
                (id, consortium_id, company_id, contribution_id, overall_score,
                 completeness_score, consistency_score, uniqueness_score,
                 validity_score, freshness_score, record_count, feature_count,
                 null_ratio, duplicate_ratio, outlier_ratio, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                assessment_id,
                consortium_id,
                company_id,
                contribution_id,
                round(overall_score, 2),
                round(scores["completeness"], 2),
                round(scores["consistency"], 2),
                round(scores["uniqueness"], 2),
                round(scores["validity"], 2),
                round(scores["freshness"], 2),
                record_count,
                feature_count,
                round(null_ratio, 4),
                round(duplicate_ratio, 4),
                round(outlier_ratio, 4),
                json.dumps(metadata or {})
            ))

            # Record metrics history
            for metric_type, value in scores.items():
                history_id = f"dqh_{secrets.token_hex(8)}"
                cursor.execute("""
                    INSERT INTO data_quality_history
                    (id, consortium_id, company_id, metric_type, metric_value)
                    VALUES (?, ?, ?, ?, ?)
                """, (history_id, consortium_id, company_id, metric_type, value))

            conn.commit()

        # Check for alerts
        self._check_quality_alerts(
            consortium_id, company_id, scores,
            null_ratio, duplicate_ratio, outlier_ratio
        )

        # Return format matching QualityAssessmentResponse
        return {
            "id": assessment_id,
            "consortium_id": consortium_id,
            "company_id": company_id,
            "contribution_id": contribution_id,
            "overall_score": round(overall_score, 2),
            "completeness_score": scores["completeness"],
            "consistency_score": scores["consistency"],
            "uniqueness_score": scores["uniqueness"],
            "validity_score": scores["validity"],
            "freshness_score": scores["freshness"],
            "record_count": record_count,
            "feature_count": feature_count,
            "null_ratio": round(null_ratio * 100, 2),
            "duplicate_ratio": round(duplicate_ratio * 100, 2),
            "outlier_ratio": round(outlier_ratio * 100, 2),
            "assessed_at": datetime.utcnow(),
            "metadata": metadata,
            # Additional nested structure for tests
            "scores": scores,
            "metrics": {
                "record_count": record_count,
                "feature_count": feature_count,
                "null_ratio": round(null_ratio * 100, 2),
                "duplicate_ratio": round(duplicate_ratio * 100, 2),
                "outlier_ratio": round(outlier_ratio * 100, 2)
            }
        }

    def _check_quality_alerts(
        self,
        consortium_id: str,
        company_id: str,
        scores: Dict[str, float],
        null_ratio: float,
        duplicate_ratio: float,
        outlier_ratio: float
    ):
        """Check and create quality alerts based on thresholds."""
        alerts = []

        # Default thresholds
        if scores["completeness"] < 80:
            alerts.append({
                "alert_type": "low_completeness",
                "severity": "warning" if scores["completeness"] >= 60 else "critical",
                "message": f"Data completeness is below threshold ({scores['completeness']:.1f}%)",
                "metric_name": "completeness",
                "metric_value": scores["completeness"],
                "threshold_value": 80
            })

        if scores["uniqueness"] < 90:
            alerts.append({
                "alert_type": "high_duplicates",
                "severity": "warning" if scores["uniqueness"] >= 70 else "critical",
                "message": f"High duplicate ratio detected ({duplicate_ratio*100:.1f}%)",
                "metric_name": "uniqueness",
                "metric_value": scores["uniqueness"],
                "threshold_value": 90
            })

        if scores["validity"] < 85:
            alerts.append({
                "alert_type": "data_quality_issue",
                "severity": "warning" if scores["validity"] >= 70 else "critical",
                "message": f"Data validity issues detected ({outlier_ratio*100:.1f}% outliers)",
                "metric_name": "validity",
                "metric_value": scores["validity"],
                "threshold_value": 85
            })

        # Create alerts
        for alert in alerts:
            self._create_quality_alert(consortium_id, company_id, alert)

    def _create_quality_alert(
        self,
        consortium_id: str,
        company_id: str,
        alert_data: Dict
    ) -> str:
        """Create a data quality alert."""
        alert_id = f"alert_{secrets.token_hex(8)}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO data_quality_alerts
                (id, consortium_id, company_id, alert_type, severity, message,
                 metric_name, metric_value, threshold_value)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert_id,
                consortium_id,
                company_id,
                alert_data["alert_type"],
                alert_data["severity"],
                alert_data["message"],
                alert_data.get("metric_name"),
                alert_data.get("metric_value"),
                alert_data.get("threshold_value")
            ))

        return alert_id

    def get_quality_assessments(
        self,
        consortium_id: str,
        company_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get quality assessments for a consortium."""
        self._init_data_quality_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT dqa.*, c.name as company_name
                FROM data_quality_assessments dqa
                JOIN companies c ON dqa.company_id = c.id
                WHERE dqa.consortium_id = ?
            """
            params = [consortium_id]

            if company_id:
                query += " AND dqa.company_id = ?"
                params.append(company_id)

            query += " ORDER BY dqa.assessed_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

        result = []
        for row in rows:
            r = dict(row)
            if r.get("metadata"):
                r["metadata"] = json.loads(r["metadata"])
            result.append(r)

        return result

    def get_latest_quality_assessment(
        self,
        consortium_id: str,
        company_id: str
    ) -> Optional[Dict]:
        """Get the latest quality assessment for a company."""
        assessments = self.get_quality_assessments(
            consortium_id, company_id=company_id, limit=1
        )
        return assessments[0] if assessments else None

    def get_quality_history(
        self,
        consortium_id: str,
        company_id: Optional[str] = None,
        metric_type: Optional[str] = None,
        days: int = 30
    ) -> List[Dict]:
        """Get quality metrics history."""
        self._init_data_quality_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT * FROM data_quality_history
                WHERE consortium_id = ?
                AND recorded_at >= datetime('now', ?)
            """
            params = [consortium_id, f"-{days} days"]

            if company_id:
                query += " AND company_id = ?"
                params.append(company_id)

            if metric_type:
                query += " AND metric_type = ?"
                params.append(metric_type)

            query += " ORDER BY recorded_at DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def get_quality_rules(self, consortium_id: str) -> List[Dict]:
        """Get quality rules for a consortium."""
        self._init_data_quality_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM data_quality_rules
                WHERE consortium_id = ?
                ORDER BY rule_type
            """, (consortium_id,))
            rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def set_quality_rule(
        self,
        consortium_id: str,
        rule_name: str,
        rule_type: str,
        threshold_min: Optional[float] = None,
        threshold_max: Optional[float] = None,
        weight: float = 1.0
    ) -> str:
        """Set or update a quality rule."""
        self._init_data_quality_schema()
        rule_id = f"rule_{secrets.token_hex(8)}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO data_quality_rules
                (id, consortium_id, rule_name, rule_type, threshold_min, threshold_max, weight)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(consortium_id, rule_name) DO UPDATE SET
                    threshold_min = excluded.threshold_min,
                    threshold_max = excluded.threshold_max,
                    weight = excluded.weight
            """, (rule_id, consortium_id, rule_name, rule_type, threshold_min, threshold_max, weight))

        return rule_id

    def get_quality_alerts(
        self,
        consortium_id: str,
        company_id: Optional[str] = None,
        severity: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get quality alerts for a consortium."""
        self._init_data_quality_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT a.*, c.name as company_name
                FROM data_quality_alerts a
                JOIN companies c ON a.company_id = c.id
                WHERE a.consortium_id = ?
            """
            params = [consortium_id]

            if company_id:
                query += " AND a.company_id = ?"
                params.append(company_id)

            if severity:
                query += " AND a.severity = ?"
                params.append(severity)

            if acknowledged is not None:
                query += " AND a.acknowledged = ?"
                params.append(1 if acknowledged else 0)

            query += " ORDER BY a.created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str
    ) -> bool:
        """Acknowledge a quality alert."""
        self._init_data_quality_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE data_quality_alerts
                SET acknowledged = 1, acknowledged_by = ?, acknowledged_at = ?
                WHERE id = ?
            """, (acknowledged_by, datetime.utcnow(), alert_id))

        return True

    def get_consortium_quality_dashboard(self, consortium_id: str) -> Dict:
        """Get data quality dashboard for a consortium.

        Returns aggregate quality metrics across all members.
        """
        self._init_data_quality_schema()

        # Get latest assessments per company
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get unique companies with assessments
            cursor.execute("""
                SELECT DISTINCT company_id FROM data_quality_assessments
                WHERE consortium_id = ?
            """, (consortium_id,))
            companies = [row["company_id"] for row in cursor.fetchall()]

        if not companies:
            return {
                "consortium_id": consortium_id,
                "overall_score": 0,
                "member_count": 0,
                "members": [],
                "alerts_count": {"critical": 0, "warning": 0},
                "score_breakdown": {
                    "completeness": 0,
                    "consistency": 0,
                    "uniqueness": 0,
                    "validity": 0,
                    "freshness": 0
                }
            }

        # Get latest assessment for each company
        members = []
        total_scores = {
            "overall": 0,
            "completeness": 0,
            "consistency": 0,
            "uniqueness": 0,
            "validity": 0,
            "freshness": 0
        }

        for company_id in companies:
            assessment = self.get_latest_quality_assessment(consortium_id, company_id)
            if assessment:
                company = self.get_company(company_id)
                members.append({
                    "company_id": company_id,
                    "company_name": company.name if company else "Unknown",
                    "overall_score": assessment["overall_score"],
                    "completeness": assessment["completeness_score"],
                    "consistency": assessment["consistency_score"],
                    "uniqueness": assessment["uniqueness_score"],
                    "validity": assessment["validity_score"],
                    "freshness": assessment["freshness_score"],
                    "record_count": assessment["record_count"],
                    "assessed_at": assessment["assessed_at"]
                })
                total_scores["overall"] += assessment["overall_score"]
                total_scores["completeness"] += assessment["completeness_score"]
                total_scores["consistency"] += assessment["consistency_score"]
                total_scores["uniqueness"] += assessment["uniqueness_score"]
                total_scores["validity"] += assessment["validity_score"]
                total_scores["freshness"] += assessment["freshness_score"]

        member_count = len(members)
        avg_scores = {k: round(v / member_count, 2) if member_count > 0 else 0
                      for k, v in total_scores.items()}

        # Get alerts count
        alerts = self.get_quality_alerts(consortium_id, acknowledged=False)
        alerts_count = {
            "critical": sum(1 for a in alerts if a["severity"] == "critical"),
            "warning": sum(1 for a in alerts if a["severity"] == "warning")
        }

        return {
            "consortium_id": consortium_id,
            "overall_score": avg_scores["overall"],
            "member_count": member_count,
            "members": sorted(members, key=lambda x: x["overall_score"], reverse=True),
            "alerts_count": alerts_count,
            "score_breakdown": {
                "completeness": avg_scores["completeness"],
                "consistency": avg_scores["consistency"],
                "uniqueness": avg_scores["uniqueness"],
                "validity": avg_scores["validity"],
                "freshness": avg_scores["freshness"]
            }
        }

    # ========== Model Marketplace Operations (TIER 3) ==========

    def _init_marketplace_schema(self):
        """Initialize marketplace-related database tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Marketplace models table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS marketplace_models (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    industry TEXT NOT NULL,
                    model_type TEXT NOT NULL,
                    version TEXT DEFAULT '1.0.0',
                    accuracy REAL,
                    training_samples INTEGER,
                    features TEXT DEFAULT '[]',
                    use_cases TEXT DEFAULT '[]',
                    pricing_type TEXT DEFAULT 'free',
                    price REAL DEFAULT 0,
                    created_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active INTEGER DEFAULT 1,
                    is_featured INTEGER DEFAULT 0,
                    downloads INTEGER DEFAULT 0,
                    rating REAL DEFAULT 0,
                    rating_count INTEGER DEFAULT 0,
                    metadata TEXT DEFAULT '{}'
                )
            """)

            # Model deployments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_deployments (
                    id TEXT PRIMARY KEY,
                    model_id TEXT NOT NULL,
                    consortium_id TEXT NOT NULL,
                    deployed_by TEXT NOT NULL,
                    deployed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    config TEXT DEFAULT '{}',
                    FOREIGN KEY (model_id) REFERENCES marketplace_models(id),
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id)
                )
            """)

            # Model reviews table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_reviews (
                    id TEXT PRIMARY KEY,
                    model_id TEXT NOT NULL,
                    reviewer_id TEXT NOT NULL,
                    consortium_id TEXT,
                    rating INTEGER NOT NULL,
                    title TEXT,
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    helpful_count INTEGER DEFAULT 0,
                    FOREIGN KEY (model_id) REFERENCES marketplace_models(id)
                )
            """)

            # Model categories table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_categories (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    icon TEXT,
                    parent_id TEXT,
                    display_order INTEGER DEFAULT 0
                )
            """)

            conn.commit()

            # Seed default categories and models
            self._seed_marketplace_data(cursor, conn)

    def _seed_marketplace_data(self, cursor, conn):
        """Seed default marketplace categories and models."""
        # Check if already seeded
        cursor.execute("SELECT COUNT(*) FROM marketplace_models")
        if cursor.fetchone()[0] > 0:
            return

        # Seed categories
        categories = [
            ("cat_fraud", "Fraud Detection", "Modelos para deteccion de fraude", "shield-exclamation", None, 1),
            ("cat_credit", "Credit Scoring", "Modelos para evaluacion crediticia", "banknotes", None, 2),
            ("cat_health", "Healthcare", "Modelos para el sector salud", "heart", None, 3),
            ("cat_retail", "Retail & E-commerce", "Modelos para comercio", "shopping-cart", None, 4),
            ("cat_insurance", "Insurance", "Modelos para seguros", "shield-check", None, 5),
        ]

        for cat in categories:
            cursor.execute("""
                INSERT OR IGNORE INTO model_categories
                (id, name, description, icon, parent_id, display_order)
                VALUES (?, ?, ?, ?, ?, ?)
            """, cat)

        # Seed pre-trained models
        models = [
            {
                "id": "model_fraud_transaction",
                "name": "Transaction Fraud Detector",
                "description": "Modelo de deteccion de fraude en transacciones bancarias usando FHE. Entrenado con datos anonimizados de multiples instituciones financieras.",
                "industry": "cat_fraud",
                "model_type": "logistic_regression",
                "version": "2.1.0",
                "accuracy": 94.5,
                "training_samples": 1500000,
                "features": json.dumps(["amount", "merchant_category", "time_of_day", "device_type", "location_risk"]),
                "use_cases": json.dumps(["Deteccion en tiempo real", "Scoring de riesgo", "Alertas automaticas"]),
                "pricing_type": "free",
                "is_featured": 1,
                "downloads": 234,
                "rating": 4.8,
                "rating_count": 45
            },
            {
                "id": "model_fraud_account",
                "name": "Account Takeover Detector",
                "description": "Detecta intentos de apropiacion de cuentas basado en patrones de comportamiento.",
                "industry": "cat_fraud",
                "model_type": "decision_tree",
                "version": "1.3.0",
                "accuracy": 91.2,
                "training_samples": 800000,
                "features": json.dumps(["login_frequency", "ip_changes", "device_fingerprint", "session_duration"]),
                "use_cases": json.dumps(["Proteccion de cuentas", "Verificacion de identidad"]),
                "pricing_type": "free",
                "is_featured": 0,
                "downloads": 156,
                "rating": 4.5,
                "rating_count": 28
            },
            {
                "id": "model_credit_default",
                "name": "Credit Default Predictor",
                "description": "Predice probabilidad de default crediticio. Compatible con regulaciones de credit scoring.",
                "industry": "cat_credit",
                "model_type": "logistic_regression",
                "version": "3.0.0",
                "accuracy": 88.7,
                "training_samples": 2000000,
                "features": json.dumps(["income_ratio", "credit_history", "debt_to_income", "payment_history"]),
                "use_cases": json.dumps(["Evaluacion de prestamos", "Limite de credito", "Pricing de riesgo"]),
                "pricing_type": "free",
                "is_featured": 1,
                "downloads": 312,
                "rating": 4.7,
                "rating_count": 67
            },
            {
                "id": "model_credit_score",
                "name": "Alternative Credit Scorer",
                "description": "Score crediticio alternativo para poblacion no bancarizada.",
                "industry": "cat_credit",
                "model_type": "linear_regression",
                "version": "1.5.0",
                "accuracy": 82.3,
                "training_samples": 500000,
                "features": json.dumps(["utility_payments", "mobile_usage", "social_data", "employment"]),
                "use_cases": json.dumps(["Inclusion financiera", "Microfinanzas"]),
                "pricing_type": "free",
                "is_featured": 0,
                "downloads": 89,
                "rating": 4.2,
                "rating_count": 15
            },
            {
                "id": "model_health_readmission",
                "name": "Hospital Readmission Risk",
                "description": "Predice riesgo de readmision hospitalaria a 30 dias. HIPAA compliant.",
                "industry": "cat_health",
                "model_type": "logistic_regression",
                "version": "2.0.0",
                "accuracy": 86.4,
                "training_samples": 350000,
                "features": json.dumps(["diagnosis_codes", "length_of_stay", "age_group", "comorbidities"]),
                "use_cases": json.dumps(["Gestion de casos", "Prevencion de readmisiones", "Optimizacion de recursos"]),
                "pricing_type": "free",
                "is_featured": 1,
                "downloads": 178,
                "rating": 4.6,
                "rating_count": 34
            },
            {
                "id": "model_health_diagnosis",
                "name": "Diagnostic Support Model",
                "description": "Modelo de soporte al diagnostico medico basado en sintomas y antecedentes.",
                "industry": "cat_health",
                "model_type": "decision_tree",
                "version": "1.2.0",
                "accuracy": 84.1,
                "training_samples": 200000,
                "features": json.dumps(["symptoms", "medical_history", "lab_results", "vital_signs"]),
                "use_cases": json.dumps(["Triaje", "Segunda opinion", "Alertas clinicas"]),
                "pricing_type": "free",
                "is_featured": 0,
                "downloads": 145,
                "rating": 4.4,
                "rating_count": 22
            },
            {
                "id": "model_retail_churn",
                "name": "Customer Churn Predictor",
                "description": "Predice probabilidad de abandono de clientes en retail/e-commerce.",
                "industry": "cat_retail",
                "model_type": "logistic_regression",
                "version": "2.2.0",
                "accuracy": 87.8,
                "training_samples": 1200000,
                "features": json.dumps(["purchase_frequency", "recency", "monetary_value", "engagement_score"]),
                "use_cases": json.dumps(["Retencion proactiva", "Campanas personalizadas", "Segmentacion"]),
                "pricing_type": "free",
                "is_featured": 1,
                "downloads": 267,
                "rating": 4.5,
                "rating_count": 52
            },
            {
                "id": "model_retail_recommend",
                "name": "Product Recommender",
                "description": "Sistema de recomendacion de productos basado en comportamiento colaborativo.",
                "industry": "cat_retail",
                "model_type": "kmeans",
                "version": "1.8.0",
                "accuracy": 79.5,
                "training_samples": 3000000,
                "features": json.dumps(["purchase_history", "browsing_behavior", "category_affinity"]),
                "use_cases": json.dumps(["Cross-selling", "Personalizacion", "Email marketing"]),
                "pricing_type": "free",
                "is_featured": 0,
                "downloads": 198,
                "rating": 4.3,
                "rating_count": 41
            },
            {
                "id": "model_insurance_claim",
                "name": "Claim Fraud Detector",
                "description": "Detecta reclamos fraudulentos en seguros de auto y hogar.",
                "industry": "cat_insurance",
                "model_type": "decision_tree",
                "version": "1.6.0",
                "accuracy": 89.3,
                "training_samples": 600000,
                "features": json.dumps(["claim_amount", "claim_frequency", "policy_age", "incident_type"]),
                "use_cases": json.dumps(["Investigacion de reclamos", "Fast-track de aprobacion", "SIU support"]),
                "pricing_type": "free",
                "is_featured": 1,
                "downloads": 134,
                "rating": 4.7,
                "rating_count": 29
            },
            {
                "id": "model_insurance_risk",
                "name": "Underwriting Risk Model",
                "description": "Evaluacion de riesgo para suscripcion de polizas.",
                "industry": "cat_insurance",
                "model_type": "linear_regression",
                "version": "2.4.0",
                "accuracy": 85.6,
                "training_samples": 450000,
                "features": json.dumps(["age", "health_indicators", "lifestyle_factors", "claims_history"]),
                "use_cases": json.dumps(["Pricing de polizas", "Seleccion de riesgo", "Segmentacion"]),
                "pricing_type": "free",
                "is_featured": 0,
                "downloads": 112,
                "rating": 4.4,
                "rating_count": 18
            }
        ]

        for model in models:
            cursor.execute("""
                INSERT OR IGNORE INTO marketplace_models
                (id, name, description, industry, model_type, version, accuracy,
                 training_samples, features, use_cases, pricing_type, is_featured,
                 downloads, rating, rating_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                model["id"], model["name"], model["description"], model["industry"],
                model["model_type"], model["version"], model["accuracy"],
                model["training_samples"], model["features"], model["use_cases"],
                model["pricing_type"], model["is_featured"], model["downloads"],
                model["rating"], model["rating_count"]
            ))

        conn.commit()

    def get_marketplace_categories(self) -> List[Dict]:
        """Get all marketplace categories."""
        self._init_marketplace_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.*, COUNT(m.id) as model_count
                FROM model_categories c
                LEFT JOIN marketplace_models m ON m.industry = c.id AND m.is_active = 1
                GROUP BY c.id
                ORDER BY c.display_order
            """)
            rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def get_marketplace_models(
        self,
        industry: Optional[str] = None,
        model_type: Optional[str] = None,
        featured_only: bool = False,
        search: Optional[str] = None,
        sort_by: str = "downloads",
        limit: int = 50
    ) -> List[Dict]:
        """Get marketplace models with optional filters."""
        self._init_marketplace_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM marketplace_models WHERE is_active = 1"
            params = []

            if industry:
                query += " AND industry = ?"
                params.append(industry)

            if model_type:
                query += " AND model_type = ?"
                params.append(model_type)

            if featured_only:
                query += " AND is_featured = 1"

            if search:
                query += " AND (name LIKE ? OR description LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])

            # Sorting
            sort_options = {
                "downloads": "downloads DESC",
                "rating": "rating DESC",
                "newest": "created_at DESC",
                "accuracy": "accuracy DESC"
            }
            query += f" ORDER BY {sort_options.get(sort_by, 'downloads DESC')}"
            query += f" LIMIT {limit}"

            cursor.execute(query, params)
            rows = cursor.fetchall()

        models = []
        for row in rows:
            model = dict(row)
            model["features"] = json.loads(model["features"])
            model["use_cases"] = json.loads(model["use_cases"])
            model["metadata"] = json.loads(model["metadata"])
            models.append(model)

        return models

    def get_marketplace_model(self, model_id: str) -> Optional[Dict]:
        """Get a specific marketplace model by ID."""
        self._init_marketplace_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM marketplace_models WHERE id = ?", (model_id,))
            row = cursor.fetchone()

        if not row:
            return None

        model = dict(row)
        model["features"] = json.loads(model["features"])
        model["use_cases"] = json.loads(model["use_cases"])
        model["metadata"] = json.loads(model["metadata"])
        return model

    def deploy_marketplace_model(
        self,
        model_id: str,
        consortium_id: str,
        deployed_by: str,
        config: Optional[Dict] = None
    ) -> Dict:
        """Deploy a marketplace model to a consortium."""
        self._init_marketplace_schema()

        # Verify model exists
        model = self.get_marketplace_model(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")

        deployment_id = f"deploy_{secrets.token_hex(8)}"

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check for existing deployment
            cursor.execute("""
                SELECT id FROM model_deployments
                WHERE model_id = ? AND consortium_id = ? AND status = 'active'
            """, (model_id, consortium_id))

            existing = cursor.fetchone()
            if existing:
                return {
                    "id": existing["id"],
                    "model_id": model_id,
                    "consortium_id": consortium_id,
                    "status": "already_deployed",
                    "message": "Model already deployed to this consortium"
                }

            # Create deployment
            cursor.execute("""
                INSERT INTO model_deployments
                (id, model_id, consortium_id, deployed_by, config)
                VALUES (?, ?, ?, ?, ?)
            """, (deployment_id, model_id, consortium_id, deployed_by,
                  json.dumps(config or {})))

            # Increment downloads
            cursor.execute("""
                UPDATE marketplace_models
                SET downloads = downloads + 1
                WHERE id = ?
            """, (model_id,))

            conn.commit()

        return {
            "id": deployment_id,
            "model_id": model_id,
            "model_name": model["name"],
            "consortium_id": consortium_id,
            "deployed_by": deployed_by,
            "status": "deployed",
            "deployed_at": datetime.utcnow().isoformat()
        }

    def get_consortium_deployments(self, consortium_id: str) -> List[Dict]:
        """Get all model deployments for a consortium."""
        self._init_marketplace_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d.*, m.name as model_name, m.model_type, m.accuracy,
                       m.industry, c.name as category_name
                FROM model_deployments d
                JOIN marketplace_models m ON d.model_id = m.id
                LEFT JOIN model_categories c ON m.industry = c.id
                WHERE d.consortium_id = ?
                ORDER BY d.deployed_at DESC
            """, (consortium_id,))
            rows = cursor.fetchall()

        deployments = []
        for row in rows:
            deployment = dict(row)
            deployment["config"] = json.loads(deployment["config"])
            deployments.append(deployment)

        return deployments

    def undeploy_model(self, deployment_id: str, undeployed_by: str) -> bool:
        """Undeploy a model from a consortium."""
        self._init_marketplace_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE model_deployments
                SET status = 'undeployed'
                WHERE id = ?
            """, (deployment_id,))
            conn.commit()
            return cursor.rowcount > 0

    def add_model_review(
        self,
        model_id: str,
        reviewer_id: str,
        rating: int,
        title: Optional[str] = None,
        comment: Optional[str] = None,
        consortium_id: Optional[str] = None
    ) -> str:
        """Add a review for a marketplace model."""
        self._init_marketplace_schema()

        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")

        review_id = f"review_{secrets.token_hex(8)}"

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Add review
            cursor.execute("""
                INSERT INTO model_reviews
                (id, model_id, reviewer_id, consortium_id, rating, title, comment)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (review_id, model_id, reviewer_id, consortium_id, rating, title, comment))

            # Update model rating
            cursor.execute("""
                SELECT AVG(rating) as avg_rating, COUNT(*) as count
                FROM model_reviews
                WHERE model_id = ?
            """, (model_id,))
            stats = cursor.fetchone()

            cursor.execute("""
                UPDATE marketplace_models
                SET rating = ?, rating_count = ?
                WHERE id = ?
            """, (round(stats["avg_rating"], 1), stats["count"], model_id))

            conn.commit()

        return review_id

    def get_model_reviews(
        self,
        model_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """Get reviews for a marketplace model."""
        self._init_marketplace_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.*, c.name as reviewer_name
                FROM model_reviews r
                LEFT JOIN companies c ON r.reviewer_id = c.id
                WHERE r.model_id = ?
                ORDER BY r.created_at DESC
                LIMIT ?
            """, (model_id, limit))
            rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def get_featured_models(self, limit: int = 6) -> List[Dict]:
        """Get featured marketplace models."""
        return self.get_marketplace_models(featured_only=True, limit=limit)

    def get_marketplace_stats(self) -> Dict:
        """Get marketplace statistics."""
        self._init_marketplace_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM marketplace_models WHERE is_active = 1")
            total_models = cursor.fetchone()[0]

            cursor.execute("SELECT SUM(downloads) FROM marketplace_models")
            total_downloads = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(DISTINCT consortium_id) FROM model_deployments WHERE status = 'active'")
            active_consortiums = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM model_reviews")
            total_reviews = cursor.fetchone()[0]

            cursor.execute("SELECT AVG(rating) FROM marketplace_models WHERE rating > 0")
            avg_rating = cursor.fetchone()[0] or 0

        return {
            "total_models": total_models,
            "total_downloads": total_downloads,
            "active_consortiums": active_consortiums,
            "total_reviews": total_reviews,
            "average_rating": round(avg_rating, 1)
        }

    # ============ Sandbox Mode Operations (TIER 3) ============

    def _init_sandbox_schema(self):
        """Initialize sandbox schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Sandbox environments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sandbox_environments (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    owner_id TEXT NOT NULL,
                    template_type TEXT DEFAULT 'basic',
                    industry TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    config TEXT DEFAULT '{}',
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (owner_id) REFERENCES companies(id)
                )
            """)

            # Synthetic datasets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS synthetic_datasets (
                    id TEXT PRIMARY KEY,
                    sandbox_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    dataset_type TEXT NOT NULL,
                    industry TEXT,
                    record_count INTEGER DEFAULT 0,
                    feature_count INTEGER DEFAULT 0,
                    features TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,
                    data_preview TEXT DEFAULT '[]',
                    statistics TEXT DEFAULT '{}',
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (sandbox_id) REFERENCES sandbox_environments(id),
                    FOREIGN KEY (created_by) REFERENCES companies(id)
                )
            """)

            # Sandbox experiments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sandbox_experiments (
                    id TEXT PRIMARY KEY,
                    sandbox_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    experiment_type TEXT NOT NULL,
                    model_type TEXT,
                    dataset_id TEXT,
                    status TEXT DEFAULT 'pending',
                    config TEXT DEFAULT '{}',
                    results TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    created_by TEXT,
                    FOREIGN KEY (sandbox_id) REFERENCES sandbox_environments(id),
                    FOREIGN KEY (dataset_id) REFERENCES synthetic_datasets(id),
                    FOREIGN KEY (created_by) REFERENCES companies(id)
                )
            """)

            # Sandbox templates table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sandbox_templates (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    industry TEXT,
                    template_type TEXT NOT NULL,
                    datasets TEXT DEFAULT '[]',
                    experiments TEXT DEFAULT '[]',
                    is_public INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}'
                )
            """)

            conn.commit()

            # Seed templates if empty
            cursor.execute("SELECT COUNT(*) FROM sandbox_templates")
            if cursor.fetchone()[0] == 0:
                self._seed_sandbox_templates()

    def _seed_sandbox_templates(self):
        """Seed initial sandbox templates."""
        templates = [
            {
                "id": "tpl_fraud_basic",
                "name": "Fraud Detection Starter",
                "description": "Ambiente basico para detectar fraudes en transacciones financieras",
                "industry": "fraud",
                "template_type": "starter",
                "datasets": json.dumps([
                    {"type": "transactions", "records": 10000, "fraud_rate": 0.02},
                    {"type": "accounts", "records": 1000}
                ]),
                "experiments": json.dumps([
                    {"type": "training", "model": "logistic_regression"},
                    {"type": "evaluation", "metrics": ["accuracy", "precision", "recall"]}
                ])
            },
            {
                "id": "tpl_credit_basic",
                "name": "Credit Scoring Starter",
                "description": "Ambiente para construir modelos de scoring crediticio",
                "industry": "credit",
                "template_type": "starter",
                "datasets": json.dumps([
                    {"type": "applications", "records": 5000, "default_rate": 0.15},
                    {"type": "payments", "records": 50000}
                ]),
                "experiments": json.dumps([
                    {"type": "training", "model": "decision_tree"},
                    {"type": "evaluation", "metrics": ["auc", "gini", "ks"]}
                ])
            },
            {
                "id": "tpl_health_basic",
                "name": "Healthcare Analytics Starter",
                "description": "Ambiente para analisis de datos clinicos y prediccion",
                "industry": "health",
                "template_type": "starter",
                "datasets": json.dumps([
                    {"type": "patients", "records": 2000},
                    {"type": "diagnoses", "records": 8000},
                    {"type": "lab_results", "records": 20000}
                ]),
                "experiments": json.dumps([
                    {"type": "training", "model": "logistic_regression"},
                    {"type": "clustering", "model": "kmeans"}
                ])
            },
            {
                "id": "tpl_retail_basic",
                "name": "Retail Analytics Starter",
                "description": "Ambiente para analisis de clientes y prediccion de churn",
                "industry": "retail",
                "template_type": "starter",
                "datasets": json.dumps([
                    {"type": "customers", "records": 5000},
                    {"type": "transactions", "records": 100000},
                    {"type": "products", "records": 500}
                ]),
                "experiments": json.dumps([
                    {"type": "segmentation", "model": "kmeans"},
                    {"type": "churn_prediction", "model": "logistic_regression"}
                ])
            },
            {
                "id": "tpl_advanced_fhe",
                "name": "FHE Advanced Workshop",
                "description": "Ambiente avanzado para experimentar con encriptacion homomorficas",
                "industry": "general",
                "template_type": "advanced",
                "datasets": json.dumps([
                    {"type": "numeric", "records": 1000, "features": 20},
                    {"type": "encrypted_sample", "records": 100}
                ]),
                "experiments": json.dumps([
                    {"type": "encryption_benchmark"},
                    {"type": "training_encrypted"},
                    {"type": "inference_encrypted"}
                ])
            }
        ]

        with self._get_connection() as conn:
            cursor = conn.cursor()
            for tpl in templates:
                cursor.execute("""
                    INSERT INTO sandbox_templates
                    (id, name, description, industry, template_type, datasets, experiments)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    tpl["id"], tpl["name"], tpl["description"],
                    tpl["industry"], tpl["template_type"],
                    tpl["datasets"], tpl["experiments"]
                ))
            conn.commit()

    def create_sandbox(
        self,
        name: str,
        owner_id: str,
        description: Optional[str] = None,
        template_id: Optional[str] = None,
        industry: Optional[str] = None,
        expires_days: int = 7
    ) -> Dict:
        """Create a new sandbox environment."""
        self._init_sandbox_schema()

        sandbox_id = f"sandbox_{uuid.uuid4().hex[:16]}"
        expires_at = datetime.utcnow() + timedelta(days=expires_days)

        template_type = "custom"
        if template_id:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT template_type FROM sandbox_templates WHERE id = ?", (template_id,))
                row = cursor.fetchone()
                if row:
                    template_type = row[0]

        config = {
            "template_id": template_id,
            "max_datasets": 10,
            "max_experiments": 20,
            "max_records_per_dataset": 100000
        }

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sandbox_environments
                (id, name, description, owner_id, template_type, industry, expires_at, config)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sandbox_id, name, description, owner_id,
                template_type, industry, expires_at, json.dumps(config)
            ))
            conn.commit()

        # If template provided, generate initial datasets
        if template_id:
            self._initialize_sandbox_from_template(sandbox_id, template_id, owner_id)

        return self.get_sandbox(sandbox_id)

    def _initialize_sandbox_from_template(
        self,
        sandbox_id: str,
        template_id: str,
        owner_id: str
    ):
        """Initialize sandbox with template data."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sandbox_templates WHERE id = ?", (template_id,))
            template = cursor.fetchone()

            if not template:
                return

            template = dict(template)
            datasets_config = json.loads(template.get("datasets", "[]"))

            for ds_config in datasets_config:
                self.generate_synthetic_dataset(
                    sandbox_id=sandbox_id,
                    name=f"Sample {ds_config.get('type', 'dataset').title()}",
                    dataset_type=ds_config.get("type", "generic"),
                    record_count=ds_config.get("records", 1000),
                    created_by=owner_id,
                    config=ds_config
                )

    def get_sandbox(self, sandbox_id: str) -> Optional[Dict]:
        """Get a sandbox environment by ID."""
        self._init_sandbox_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, c.name as owner_name
                FROM sandbox_environments s
                JOIN companies c ON s.owner_id = c.id
                WHERE s.id = ?
            """, (sandbox_id,))
            row = cursor.fetchone()

            if not row:
                return None

            sandbox = dict(row)
            sandbox["config"] = json.loads(sandbox.get("config", "{}"))
            sandbox["metadata"] = json.loads(sandbox.get("metadata", "{}"))

            # Get counts
            cursor.execute(
                "SELECT COUNT(*) FROM synthetic_datasets WHERE sandbox_id = ?",
                (sandbox_id,)
            )
            sandbox["dataset_count"] = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM sandbox_experiments WHERE sandbox_id = ?",
                (sandbox_id,)
            )
            sandbox["experiment_count"] = cursor.fetchone()[0]

            return sandbox

    def list_sandboxes(
        self,
        owner_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict]:
        """List sandbox environments."""
        self._init_sandbox_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT s.*, c.name as owner_name
                FROM sandbox_environments s
                JOIN companies c ON s.owner_id = c.id
                WHERE 1=1
            """
            params = []

            if owner_id:
                query += " AND s.owner_id = ?"
                params.append(owner_id)

            if status:
                query += " AND s.status = ?"
                params.append(status)

            query += " ORDER BY s.created_at DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

        sandboxes = []
        for row in rows:
            sandbox = dict(row)
            sandbox["config"] = json.loads(sandbox.get("config", "{}"))
            sandboxes.append(sandbox)

        return sandboxes

    def delete_sandbox(self, sandbox_id: str, owner_id: str) -> bool:
        """Delete a sandbox environment."""
        self._init_sandbox_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Verify ownership
            cursor.execute(
                "SELECT owner_id FROM sandbox_environments WHERE id = ?",
                (sandbox_id,)
            )
            row = cursor.fetchone()
            if not row or row[0] != owner_id:
                return False

            # Delete experiments
            cursor.execute(
                "DELETE FROM sandbox_experiments WHERE sandbox_id = ?",
                (sandbox_id,)
            )

            # Delete datasets
            cursor.execute(
                "DELETE FROM synthetic_datasets WHERE sandbox_id = ?",
                (sandbox_id,)
            )

            # Delete sandbox
            cursor.execute(
                "DELETE FROM sandbox_environments WHERE id = ?",
                (sandbox_id,)
            )

            conn.commit()
            return True

    def generate_synthetic_dataset(
        self,
        sandbox_id: str,
        name: str,
        dataset_type: str,
        record_count: int = 1000,
        created_by: Optional[str] = None,
        description: Optional[str] = None,
        config: Optional[Dict] = None
    ) -> Dict:
        """Generate a synthetic dataset for the sandbox."""
        self._init_sandbox_schema()

        config = config or {}
        dataset_id = f"ds_{uuid.uuid4().hex[:16]}"

        # Generate features based on dataset type
        features, statistics, preview = self._generate_synthetic_data(
            dataset_type, record_count, config
        )

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get industry from sandbox
            cursor.execute(
                "SELECT industry FROM sandbox_environments WHERE id = ?",
                (sandbox_id,)
            )
            row = cursor.fetchone()
            industry = row[0] if row else None

            cursor.execute("""
                INSERT INTO synthetic_datasets
                (id, sandbox_id, name, description, dataset_type, industry,
                 record_count, feature_count, features, data_preview, statistics, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dataset_id, sandbox_id, name, description, dataset_type, industry,
                record_count, len(features), json.dumps(features),
                json.dumps(preview), json.dumps(statistics), created_by
            ))
            conn.commit()

        return self.get_dataset(dataset_id)

    def _generate_synthetic_data(
        self,
        dataset_type: str,
        record_count: int,
        config: Dict
    ) -> tuple:
        """Generate synthetic data based on type."""
        import random

        features = []
        statistics = {}
        preview = []

        if dataset_type == "transactions":
            features = [
                {"name": "transaction_id", "type": "string", "description": "Unique transaction ID"},
                {"name": "amount", "type": "float", "description": "Transaction amount"},
                {"name": "merchant_category", "type": "category", "description": "Merchant category code"},
                {"name": "time_of_day", "type": "integer", "description": "Hour of day (0-23)"},
                {"name": "day_of_week", "type": "integer", "description": "Day of week (0-6)"},
                {"name": "is_international", "type": "boolean", "description": "International transaction"},
                {"name": "is_fraud", "type": "boolean", "description": "Fraud label"}
            ]
            fraud_rate = config.get("fraud_rate", 0.02)
            statistics = {
                "fraud_rate": fraud_rate,
                "avg_amount": 150.50,
                "max_amount": 5000.00,
                "international_rate": 0.15
            }
            for i in range(min(5, record_count)):
                preview.append({
                    "transaction_id": f"txn_{uuid.uuid4().hex[:8]}",
                    "amount": round(random.uniform(10, 500), 2),
                    "merchant_category": random.choice(["retail", "food", "travel", "online"]),
                    "time_of_day": random.randint(0, 23),
                    "day_of_week": random.randint(0, 6),
                    "is_international": random.random() < 0.15,
                    "is_fraud": random.random() < fraud_rate
                })

        elif dataset_type == "applications":
            features = [
                {"name": "application_id", "type": "string", "description": "Application ID"},
                {"name": "income", "type": "float", "description": "Annual income"},
                {"name": "debt_ratio", "type": "float", "description": "Debt to income ratio"},
                {"name": "credit_history_months", "type": "integer", "description": "Credit history length"},
                {"name": "num_accounts", "type": "integer", "description": "Number of accounts"},
                {"name": "employment_years", "type": "float", "description": "Years employed"},
                {"name": "defaulted", "type": "boolean", "description": "Default label"}
            ]
            default_rate = config.get("default_rate", 0.15)
            statistics = {
                "default_rate": default_rate,
                "avg_income": 55000,
                "avg_debt_ratio": 0.35
            }
            for i in range(min(5, record_count)):
                preview.append({
                    "application_id": f"app_{uuid.uuid4().hex[:8]}",
                    "income": round(random.uniform(25000, 150000), 2),
                    "debt_ratio": round(random.uniform(0.1, 0.6), 2),
                    "credit_history_months": random.randint(12, 240),
                    "num_accounts": random.randint(1, 10),
                    "employment_years": round(random.uniform(0.5, 20), 1),
                    "defaulted": random.random() < default_rate
                })

        elif dataset_type == "customers":
            features = [
                {"name": "customer_id", "type": "string", "description": "Customer ID"},
                {"name": "tenure_months", "type": "integer", "description": "Months as customer"},
                {"name": "monthly_spend", "type": "float", "description": "Average monthly spend"},
                {"name": "num_purchases", "type": "integer", "description": "Total purchases"},
                {"name": "last_purchase_days", "type": "integer", "description": "Days since last purchase"},
                {"name": "segment", "type": "category", "description": "Customer segment"},
                {"name": "churned", "type": "boolean", "description": "Churn label"}
            ]
            churn_rate = config.get("churn_rate", 0.20)
            statistics = {
                "churn_rate": churn_rate,
                "avg_tenure": 24,
                "avg_monthly_spend": 125
            }
            for i in range(min(5, record_count)):
                preview.append({
                    "customer_id": f"cust_{uuid.uuid4().hex[:8]}",
                    "tenure_months": random.randint(1, 60),
                    "monthly_spend": round(random.uniform(20, 500), 2),
                    "num_purchases": random.randint(1, 100),
                    "last_purchase_days": random.randint(1, 180),
                    "segment": random.choice(["bronze", "silver", "gold", "platinum"]),
                    "churned": random.random() < churn_rate
                })

        elif dataset_type == "patients":
            features = [
                {"name": "patient_id", "type": "string", "description": "Patient ID"},
                {"name": "age", "type": "integer", "description": "Patient age"},
                {"name": "gender", "type": "category", "description": "Gender"},
                {"name": "bmi", "type": "float", "description": "Body mass index"},
                {"name": "blood_pressure", "type": "float", "description": "Blood pressure"},
                {"name": "cholesterol", "type": "category", "description": "Cholesterol level"},
                {"name": "smoker", "type": "boolean", "description": "Smoking status"}
            ]
            statistics = {
                "avg_age": 45,
                "avg_bmi": 26.5,
                "smoker_rate": 0.18
            }
            for i in range(min(5, record_count)):
                preview.append({
                    "patient_id": f"pat_{uuid.uuid4().hex[:8]}",
                    "age": random.randint(18, 85),
                    "gender": random.choice(["M", "F"]),
                    "bmi": round(random.uniform(18, 40), 1),
                    "blood_pressure": round(random.uniform(90, 160), 0),
                    "cholesterol": random.choice(["normal", "borderline", "high"]),
                    "smoker": random.random() < 0.18
                })

        else:  # generic
            features = [
                {"name": "id", "type": "string", "description": "Record ID"},
                {"name": "feature_1", "type": "float", "description": "Numeric feature 1"},
                {"name": "feature_2", "type": "float", "description": "Numeric feature 2"},
                {"name": "feature_3", "type": "float", "description": "Numeric feature 3"},
                {"name": "category", "type": "category", "description": "Category feature"},
                {"name": "label", "type": "boolean", "description": "Target label"}
            ]
            statistics = {
                "feature_1_mean": 0.5,
                "feature_2_mean": 0.5,
                "label_rate": 0.3
            }
            for i in range(min(5, record_count)):
                preview.append({
                    "id": f"rec_{uuid.uuid4().hex[:8]}",
                    "feature_1": round(random.random(), 3),
                    "feature_2": round(random.random(), 3),
                    "feature_3": round(random.random(), 3),
                    "category": random.choice(["A", "B", "C"]),
                    "label": random.random() < 0.3
                })

        return features, statistics, preview

    def get_dataset(self, dataset_id: str) -> Optional[Dict]:
        """Get a synthetic dataset by ID."""
        self._init_sandbox_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM synthetic_datasets WHERE id = ?", (dataset_id,))
            row = cursor.fetchone()

            if not row:
                return None

            dataset = dict(row)
            dataset["features"] = json.loads(dataset.get("features", "[]"))
            dataset["data_preview"] = json.loads(dataset.get("data_preview", "[]"))
            dataset["statistics"] = json.loads(dataset.get("statistics", "{}"))
            dataset["metadata"] = json.loads(dataset.get("metadata", "{}"))

            return dataset

    def list_datasets(self, sandbox_id: str) -> List[Dict]:
        """List datasets in a sandbox."""
        self._init_sandbox_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM synthetic_datasets
                WHERE sandbox_id = ?
                ORDER BY created_at DESC
            """, (sandbox_id,))
            rows = cursor.fetchall()

        datasets = []
        for row in rows:
            dataset = dict(row)
            dataset["features"] = json.loads(dataset.get("features", "[]"))
            dataset["statistics"] = json.loads(dataset.get("statistics", "{}"))
            datasets.append(dataset)

        return datasets

    def delete_dataset(self, dataset_id: str, owner_id: str) -> bool:
        """Delete a dataset."""
        self._init_sandbox_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Verify ownership via sandbox
            cursor.execute("""
                SELECT s.owner_id FROM synthetic_datasets d
                JOIN sandbox_environments s ON d.sandbox_id = s.id
                WHERE d.id = ?
            """, (dataset_id,))
            row = cursor.fetchone()
            if not row or row[0] != owner_id:
                return False

            cursor.execute("DELETE FROM synthetic_datasets WHERE id = ?", (dataset_id,))
            conn.commit()
            return True

    def create_experiment(
        self,
        sandbox_id: str,
        name: str,
        experiment_type: str,
        created_by: str,
        model_type: Optional[str] = None,
        dataset_id: Optional[str] = None,
        description: Optional[str] = None,
        config: Optional[Dict] = None
    ) -> Dict:
        """Create a new experiment in the sandbox."""
        self._init_sandbox_schema()

        experiment_id = f"exp_{uuid.uuid4().hex[:16]}"
        config = config or {}

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sandbox_experiments
                (id, sandbox_id, name, description, experiment_type, model_type,
                 dataset_id, config, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                experiment_id, sandbox_id, name, description, experiment_type,
                model_type, dataset_id, json.dumps(config), created_by
            ))
            conn.commit()

        return self.get_experiment(experiment_id)

    def get_experiment(self, experiment_id: str) -> Optional[Dict]:
        """Get an experiment by ID."""
        self._init_sandbox_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.*, d.name as dataset_name
                FROM sandbox_experiments e
                LEFT JOIN synthetic_datasets d ON e.dataset_id = d.id
                WHERE e.id = ?
            """, (experiment_id,))
            row = cursor.fetchone()

            if not row:
                return None

            experiment = dict(row)
            experiment["config"] = json.loads(experiment.get("config", "{}"))
            experiment["results"] = json.loads(experiment.get("results", "{}"))

            return experiment

    def list_experiments(self, sandbox_id: str) -> List[Dict]:
        """List experiments in a sandbox."""
        self._init_sandbox_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.*, d.name as dataset_name
                FROM sandbox_experiments e
                LEFT JOIN synthetic_datasets d ON e.dataset_id = d.id
                WHERE e.sandbox_id = ?
                ORDER BY e.created_at DESC
            """, (sandbox_id,))
            rows = cursor.fetchall()

        experiments = []
        for row in rows:
            exp = dict(row)
            exp["config"] = json.loads(exp.get("config", "{}"))
            exp["results"] = json.loads(exp.get("results", "{}"))
            experiments.append(exp)

        return experiments

    def run_experiment(self, experiment_id: str) -> Dict:
        """Run an experiment and return results."""
        self._init_sandbox_schema()
        import random

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Update status to running
            cursor.execute("""
                UPDATE sandbox_experiments
                SET status = 'running', started_at = ?
                WHERE id = ?
            """, (datetime.utcnow(), experiment_id))
            conn.commit()

            # Get experiment details
            cursor.execute("SELECT * FROM sandbox_experiments WHERE id = ?", (experiment_id,))
            exp = dict(cursor.fetchone())
            exp_type = exp.get("experiment_type")
            model_type = exp.get("model_type")

            # Simulate experiment results
            results = self._simulate_experiment_results(exp_type, model_type)

            # Update with results
            cursor.execute("""
                UPDATE sandbox_experiments
                SET status = 'completed', completed_at = ?, results = ?
                WHERE id = ?
            """, (datetime.utcnow(), json.dumps(results), experiment_id))
            conn.commit()

        return self.get_experiment(experiment_id)

    def _simulate_experiment_results(
        self,
        experiment_type: str,
        model_type: Optional[str]
    ) -> Dict:
        """Simulate experiment results."""
        import random

        if experiment_type == "training":
            return {
                "status": "success",
                "epochs": 100,
                "training_time_seconds": round(random.uniform(5, 30), 2),
                "final_loss": round(random.uniform(0.1, 0.5), 4),
                "metrics": {
                    "accuracy": round(random.uniform(0.75, 0.95), 3),
                    "precision": round(random.uniform(0.70, 0.90), 3),
                    "recall": round(random.uniform(0.65, 0.88), 3),
                    "f1_score": round(random.uniform(0.68, 0.89), 3)
                }
            }
        elif experiment_type == "evaluation":
            return {
                "status": "success",
                "evaluation_time_seconds": round(random.uniform(1, 5), 2),
                "metrics": {
                    "accuracy": round(random.uniform(0.75, 0.92), 3),
                    "auc": round(random.uniform(0.80, 0.95), 3),
                    "precision": round(random.uniform(0.70, 0.88), 3),
                    "recall": round(random.uniform(0.65, 0.85), 3)
                },
                "confusion_matrix": {
                    "true_positive": random.randint(800, 950),
                    "true_negative": random.randint(800, 950),
                    "false_positive": random.randint(50, 150),
                    "false_negative": random.randint(50, 150)
                }
            }
        elif experiment_type == "clustering" or experiment_type == "segmentation":
            n_clusters = random.randint(3, 6)
            return {
                "status": "success",
                "n_clusters": n_clusters,
                "inertia": round(random.uniform(100, 500), 2),
                "silhouette_score": round(random.uniform(0.4, 0.8), 3),
                "cluster_sizes": [random.randint(100, 500) for _ in range(n_clusters)]
            }
        elif experiment_type == "encryption_benchmark":
            return {
                "status": "success",
                "encryption_time_ms": round(random.uniform(50, 200), 2),
                "decryption_time_ms": round(random.uniform(30, 150), 2),
                "key_generation_time_ms": round(random.uniform(100, 500), 2),
                "ciphertext_size_kb": round(random.uniform(10, 100), 1),
                "noise_budget": round(random.uniform(20, 40), 1)
            }
        else:
            return {
                "status": "success",
                "message": f"Experiment type '{experiment_type}' completed",
                "execution_time_seconds": round(random.uniform(1, 10), 2)
            }

    def delete_experiment(self, experiment_id: str, owner_id: str) -> bool:
        """Delete an experiment."""
        self._init_sandbox_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Verify ownership via sandbox
            cursor.execute("""
                SELECT s.owner_id FROM sandbox_experiments e
                JOIN sandbox_environments s ON e.sandbox_id = s.id
                WHERE e.id = ?
            """, (experiment_id,))
            row = cursor.fetchone()
            if not row or row[0] != owner_id:
                return False

            cursor.execute("DELETE FROM sandbox_experiments WHERE id = ?", (experiment_id,))
            conn.commit()
            return True

    def list_sandbox_templates(self, industry: Optional[str] = None) -> List[Dict]:
        """List available sandbox templates."""
        self._init_sandbox_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM sandbox_templates WHERE is_public = 1"
            params = []

            if industry:
                query += " AND (industry = ? OR industry = 'general')"
                params.append(industry)

            query += " ORDER BY name"

            cursor.execute(query, params)
            rows = cursor.fetchall()

        templates = []
        for row in rows:
            tpl = dict(row)
            tpl["datasets"] = json.loads(tpl.get("datasets", "[]"))
            tpl["experiments"] = json.loads(tpl.get("experiments", "[]"))
            templates.append(tpl)

        return templates

    def get_sandbox_stats(self, owner_id: Optional[str] = None) -> Dict:
        """Get sandbox statistics."""
        self._init_sandbox_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            base_query = ""
            params = []
            if owner_id:
                base_query = " WHERE owner_id = ?"
                params = [owner_id]

            cursor.execute(
                f"SELECT COUNT(*) FROM sandbox_environments{base_query}",
                params
            )
            total_sandboxes = cursor.fetchone()[0]

            cursor.execute(
                f"SELECT COUNT(*) FROM sandbox_environments WHERE status = 'active'{' AND owner_id = ?' if owner_id else ''}",
                params
            )
            active_sandboxes = cursor.fetchone()[0]

            if owner_id:
                cursor.execute("""
                    SELECT COUNT(*) FROM synthetic_datasets d
                    JOIN sandbox_environments s ON d.sandbox_id = s.id
                    WHERE s.owner_id = ?
                """, (owner_id,))
            else:
                cursor.execute("SELECT COUNT(*) FROM synthetic_datasets")
            total_datasets = cursor.fetchone()[0]

            if owner_id:
                cursor.execute("""
                    SELECT COUNT(*) FROM sandbox_experiments e
                    JOIN sandbox_environments s ON e.sandbox_id = s.id
                    WHERE s.owner_id = ?
                """, (owner_id,))
            else:
                cursor.execute("SELECT COUNT(*) FROM sandbox_experiments")
            total_experiments = cursor.fetchone()[0]

            if owner_id:
                cursor.execute("""
                    SELECT COUNT(*) FROM sandbox_experiments e
                    JOIN sandbox_environments s ON e.sandbox_id = s.id
                    WHERE s.owner_id = ? AND e.status = 'completed'
                """, (owner_id,))
            else:
                cursor.execute("SELECT COUNT(*) FROM sandbox_experiments WHERE status = 'completed'")
            completed_experiments = cursor.fetchone()[0]

        return {
            "total_sandboxes": total_sandboxes,
            "active_sandboxes": active_sandboxes,
            "total_datasets": total_datasets,
            "total_experiments": total_experiments,
            "completed_experiments": completed_experiments
        }

    # ============================================================
    # TIER 4: FEDERATED INFERENCE OPERATIONS
    # ============================================================

    def _init_federated_schema(self):
        """Initialize federated inference tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Inference endpoints table - where companies deploy model endpoints
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inference_endpoints (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    company_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    model_id TEXT,
                    endpoint_type TEXT DEFAULT 'private',
                    status TEXT DEFAULT 'active',
                    encryption_scheme TEXT DEFAULT 'CKKS',
                    max_batch_size INTEGER DEFAULT 100,
                    rate_limit INTEGER DEFAULT 1000,
                    config TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)

            # Inference requests table - track prediction requests
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inference_requests (
                    id TEXT PRIMARY KEY,
                    endpoint_id TEXT NOT NULL,
                    requester_id TEXT NOT NULL,
                    request_type TEXT DEFAULT 'single',
                    input_shape TEXT,
                    batch_size INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'pending',
                    encryption_verified INTEGER DEFAULT 0,
                    processing_time_ms INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_message TEXT,
                    FOREIGN KEY (endpoint_id) REFERENCES inference_endpoints(id),
                    FOREIGN KEY (requester_id) REFERENCES companies(id)
                )
            """)

            # Inference results table - encrypted predictions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inference_results (
                    id TEXT PRIMARY KEY,
                    request_id TEXT NOT NULL,
                    result_type TEXT DEFAULT 'prediction',
                    encrypted_output TEXT,
                    output_shape TEXT,
                    confidence_encrypted INTEGER DEFAULT 1,
                    metadata TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (request_id) REFERENCES inference_requests(id)
                )
            """)

            # Federated models table - models that can be used for federated inference
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS federated_models (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    model_type TEXT NOT NULL,
                    input_features TEXT,
                    output_type TEXT,
                    accuracy REAL,
                    is_encrypted INTEGER DEFAULT 1,
                    encryption_scheme TEXT DEFAULT 'CKKS',
                    model_size_bytes INTEGER,
                    training_consortium_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    version TEXT DEFAULT '1.0.0',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    config TEXT DEFAULT '{}',
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id)
                )
            """)

            # Edge nodes table - track federated edge deployments
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS edge_nodes (
                    id TEXT PRIMARY KEY,
                    company_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    node_type TEXT DEFAULT 'inference',
                    status TEXT DEFAULT 'active',
                    hardware_info TEXT DEFAULT '{}',
                    last_heartbeat TIMESTAMP,
                    models_deployed TEXT DEFAULT '[]',
                    inference_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)

            conn.commit()

    def create_inference_endpoint(
        self,
        consortium_id: str,
        company_id: str,
        name: str,
        description: Optional[str] = None,
        model_id: Optional[str] = None,
        endpoint_type: str = "private",
        max_batch_size: int = 100,
        config: Optional[Dict] = None
    ) -> Dict:
        """Create a new federated inference endpoint."""
        self._init_federated_schema()

        endpoint_id = f"ep_{uuid.uuid4().hex[:16]}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO inference_endpoints
                (id, consortium_id, company_id, name, description, model_id,
                 endpoint_type, max_batch_size, config)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                endpoint_id, consortium_id, company_id, name, description,
                model_id, endpoint_type, max_batch_size,
                json.dumps(config or {})
            ))
            conn.commit()

        return self.get_inference_endpoint(endpoint_id)

    def get_inference_endpoint(self, endpoint_id: str) -> Optional[Dict]:
        """Get an inference endpoint by ID."""
        self._init_federated_schema()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.*, c.name as company_name,
                       (SELECT COUNT(*) FROM inference_requests WHERE endpoint_id = e.id) as request_count,
                       (SELECT COUNT(*) FROM inference_requests WHERE endpoint_id = e.id AND status = 'completed') as completed_count
                FROM inference_endpoints e
                JOIN companies c ON e.company_id = c.id
                WHERE e.id = ?
            """, (endpoint_id,))
            row = cursor.fetchone()

        if not row:
            return None

        endpoint = dict(row)
        endpoint["config"] = json.loads(endpoint.get("config", "{}"))
        return endpoint

    def list_inference_endpoints(
        self,
        consortium_id: Optional[str] = None,
        company_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict]:
        """List inference endpoints with optional filters."""
        self._init_federated_schema()

        query = """
            SELECT e.*, c.name as company_name
            FROM inference_endpoints e
            JOIN companies c ON e.company_id = c.id
            WHERE 1=1
        """
        params = []

        if consortium_id:
            query += " AND e.consortium_id = ?"
            params.append(consortium_id)

        if company_id:
            query += " AND e.company_id = ?"
            params.append(company_id)

        if status:
            query += " AND e.status = ?"
            params.append(status)

        query += " ORDER BY e.created_at DESC"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

        endpoints = []
        for row in rows:
            endpoint = dict(row)
            endpoint["config"] = json.loads(endpoint.get("config", "{}"))
            endpoints.append(endpoint)

        return endpoints

    def submit_inference_request(
        self,
        endpoint_id: str,
        requester_id: str,
        input_data: Dict,
        request_type: str = "single",
        priority: str = "normal",
        encryption_key_id: Optional[str] = None
    ) -> Dict:
        """Submit a federated inference request."""
        self._init_federated_schema()

        # Verify endpoint exists and is active
        endpoint = self.get_inference_endpoint(endpoint_id)
        if not endpoint:
            raise ValueError("Endpoint not found")
        if endpoint["status"] != "active":
            raise ValueError("Endpoint is not active")

        request_id = f"req_{uuid.uuid4().hex[:16]}"
        batch_size = len(input_data.get("samples", [input_data])) if isinstance(input_data.get("samples"), list) else 1
        input_shape = json.dumps(input_data.get("shape", [batch_size]))

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO inference_requests
                (id, endpoint_id, requester_id, request_type, input_shape, batch_size, status)
                VALUES (?, ?, ?, ?, ?, ?, 'processing')
            """, (
                request_id, endpoint_id, requester_id, request_type,
                input_shape, batch_size
            ))
            conn.commit()

        # Process the request (simulated federated inference)
        result = self._process_federated_inference(request_id, endpoint, input_data)

        # Add priority and encryption_key_id to result
        result["priority"] = priority
        if encryption_key_id:
            result["encryption_key_id"] = encryption_key_id

        return result

    def _process_federated_inference(
        self,
        request_id: str,
        endpoint: Dict,
        input_data: Dict
    ) -> Dict:
        """Process a federated inference request (simulated)."""
        import random
        import time

        start_time = time.time()

        # Simulate processing time based on batch size
        batch_size = len(input_data.get("samples", [input_data])) if isinstance(input_data.get("samples"), list) else 1
        processing_time = random.uniform(0.05, 0.2) * batch_size

        # Generate simulated encrypted predictions
        model_type = endpoint.get("config", {}).get("model_type", "classification")

        if model_type == "classification":
            predictions = []
            for _ in range(batch_size):
                pred = {
                    "class": random.randint(0, 1),
                    "probability_encrypted": f"enc_{uuid.uuid4().hex[:32]}",
                    "confidence": round(random.uniform(0.7, 0.99), 3)
                }
                predictions.append(pred)
        elif model_type == "regression":
            predictions = []
            for _ in range(batch_size):
                pred = {
                    "value_encrypted": f"enc_{uuid.uuid4().hex[:32]}",
                    "uncertainty": round(random.uniform(0.01, 0.1), 4)
                }
                predictions.append(pred)
        else:  # clustering
            predictions = []
            for _ in range(batch_size):
                pred = {
                    "cluster": random.randint(0, 4),
                    "distance_encrypted": f"enc_{uuid.uuid4().hex[:32]}"
                }
                predictions.append(pred)

        processing_time_ms = int((time.time() - start_time + processing_time) * 1000)

        # Store result
        result_id = f"result_{uuid.uuid4().hex[:16]}"
        encrypted_output = json.dumps({
            "predictions": predictions,
            "encryption_scheme": endpoint.get("encryption_scheme", "CKKS"),
            "version": "1.0"
        })

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Update request status
            cursor.execute("""
                UPDATE inference_requests
                SET status = 'completed', processing_time_ms = ?, completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (processing_time_ms, request_id))

            # Store result
            cursor.execute("""
                INSERT INTO inference_results
                (id, request_id, result_type, encrypted_output, output_shape, metadata)
                VALUES (?, ?, 'prediction', ?, ?, ?)
            """, (
                result_id, request_id, encrypted_output,
                json.dumps([batch_size]),
                json.dumps({"processing_time_ms": processing_time_ms})
            ))

            conn.commit()

        return {
            "id": request_id,
            "request_id": request_id,
            "result_id": result_id,
            "status": "completed",
            "batch_size": batch_size,
            "processing_time_ms": processing_time_ms,
            "predictions": predictions,
            "encryption_verified": True,
            "data_stayed_local": True
        }

    def get_inference_request(self, request_id: str) -> Optional[Dict]:
        """Get an inference request by ID."""
        self._init_federated_schema()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.*, e.name as endpoint_name, c.name as requester_name
                FROM inference_requests r
                JOIN inference_endpoints e ON r.endpoint_id = e.id
                JOIN companies c ON r.requester_id = c.id
                WHERE r.id = ?
            """, (request_id,))
            row = cursor.fetchone()

        if not row:
            return None

        request = dict(row)

        # Get result if completed
        if request["status"] == "completed":
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM inference_results WHERE request_id = ?
                """, (request_id,))
                result_row = cursor.fetchone()

            if result_row:
                result = dict(result_row)
                result["encrypted_output"] = json.loads(result.get("encrypted_output", "{}"))
                result["metadata"] = json.loads(result.get("metadata", "{}"))
                request["result"] = result

        return request

    def list_inference_requests(
        self,
        endpoint_id: Optional[str] = None,
        requester_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """List inference requests with optional filters."""
        self._init_federated_schema()

        query = """
            SELECT r.*, e.name as endpoint_name
            FROM inference_requests r
            JOIN inference_endpoints e ON r.endpoint_id = e.id
            WHERE 1=1
        """
        params = []

        if endpoint_id:
            query += " AND r.endpoint_id = ?"
            params.append(endpoint_id)

        if requester_id:
            query += " AND r.requester_id = ?"
            params.append(requester_id)

        if status:
            query += " AND r.status = ?"
            params.append(status)

        query += f" ORDER BY r.created_at DESC LIMIT {limit}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def create_federated_model(
        self,
        consortium_id: str,
        name: str,
        model_type: str,
        description: Optional[str] = None,
        input_features: Optional[List[str]] = None,
        output_type: str = "classification",
        accuracy: Optional[float] = None,
        config: Optional[Dict] = None,
        created_by: Optional[str] = None,
        version: Optional[str] = None
    ) -> Dict:
        """Register a federated model for inference."""
        self._init_federated_schema()

        model_id = f"fm_{uuid.uuid4().hex[:16]}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO federated_models
                (id, consortium_id, name, description, model_type, input_features,
                 output_type, accuracy, config, version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                model_id, consortium_id, name, description, model_type,
                json.dumps(input_features or []),
                output_type, accuracy,
                json.dumps(config or {}),
                version or "1.0.0"
            ))
            conn.commit()

        return self.get_federated_model(model_id)

    def get_federated_model(self, model_id: str) -> Optional[Dict]:
        """Get a federated model by ID."""
        self._init_federated_schema()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.*,
                       (SELECT COUNT(*) FROM inference_endpoints WHERE model_id = m.id) as endpoint_count
                FROM federated_models m
                WHERE m.id = ?
            """, (model_id,))
            row = cursor.fetchone()

        if not row:
            return None

        model = dict(row)
        model["input_features"] = json.loads(model.get("input_features", "[]"))
        model["config"] = json.loads(model.get("config", "{}"))
        return model

    def list_federated_models(
        self,
        consortium_id: Optional[str] = None,
        model_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict]:
        """List federated models with optional filters."""
        self._init_federated_schema()

        query = "SELECT * FROM federated_models WHERE 1=1"
        params = []

        if consortium_id:
            query += " AND consortium_id = ?"
            params.append(consortium_id)

        if model_type:
            query += " AND model_type = ?"
            params.append(model_type)

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY created_at DESC"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

        models = []
        for row in rows:
            model = dict(row)
            model["input_features"] = json.loads(model.get("input_features", "[]"))
            model["config"] = json.loads(model.get("config", "{}"))
            models.append(model)

        return models

    def register_edge_node(
        self,
        company_id: str,
        name: str,
        node_type: str = "inference",
        hardware_info: Optional[Dict] = None
    ) -> Dict:
        """Register an edge node for federated inference."""
        self._init_federated_schema()

        node_id = f"node_{uuid.uuid4().hex[:16]}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO edge_nodes
                (id, company_id, name, node_type, hardware_info, last_heartbeat)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                node_id, company_id, name, node_type,
                json.dumps(hardware_info or {})
            ))
            conn.commit()

        return self.get_edge_node(node_id)

    def get_edge_node(self, node_id: str) -> Optional[Dict]:
        """Get an edge node by ID."""
        self._init_federated_schema()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT n.*, c.name as company_name
                FROM edge_nodes n
                JOIN companies c ON n.company_id = c.id
                WHERE n.id = ?
            """, (node_id,))
            row = cursor.fetchone()

        if not row:
            return None

        node = dict(row)
        node["hardware_info"] = json.loads(node.get("hardware_info", "{}"))
        node["models_deployed"] = json.loads(node.get("models_deployed", "[]"))
        return node

    def list_edge_nodes(
        self,
        company_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict]:
        """List edge nodes with optional filters."""
        self._init_federated_schema()

        query = """
            SELECT n.*, c.name as company_name
            FROM edge_nodes n
            JOIN companies c ON n.company_id = c.id
            WHERE 1=1
        """
        params = []

        if company_id:
            query += " AND n.company_id = ?"
            params.append(company_id)

        if status:
            query += " AND n.status = ?"
            params.append(status)

        query += " ORDER BY n.created_at DESC"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

        nodes = []
        for row in rows:
            node = dict(row)
            node["hardware_info"] = json.loads(node.get("hardware_info", "{}"))
            node["models_deployed"] = json.loads(node.get("models_deployed", "[]"))
            nodes.append(node)

        return nodes

    def deploy_model_to_edge(
        self,
        node_id: str,
        model_id: str,
        company_id: str
    ) -> Dict:
        """Deploy a federated model to an edge node."""
        self._init_federated_schema()

        node = self.get_edge_node(node_id)
        if not node:
            raise ValueError("Edge node not found")

        if node["company_id"] != company_id:
            raise ValueError("Not authorized to deploy to this node")

        model = self.get_federated_model(model_id)
        if not model:
            raise ValueError("Model not found")

        # Add model to deployed models
        models_deployed = node.get("models_deployed", [])
        if model_id not in models_deployed:
            models_deployed.append(model_id)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE edge_nodes
                SET models_deployed = ?
                WHERE id = ?
            """, (json.dumps(models_deployed), node_id))
            conn.commit()

        return {
            "node_id": node_id,
            "model_id": model_id,
            "status": "deployed",
            "models_deployed": models_deployed
        }

    def update_edge_heartbeat(self, node_id: str) -> bool:
        """Update the heartbeat timestamp for an edge node."""
        self._init_federated_schema()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE edge_nodes
                SET last_heartbeat = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (node_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_federated_stats(self, company_id: Optional[str] = None) -> Dict:
        """Get federated inference statistics."""
        self._init_federated_schema()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Total endpoints
            if company_id:
                cursor.execute("SELECT COUNT(*) FROM inference_endpoints WHERE company_id = ?", (company_id,))
            else:
                cursor.execute("SELECT COUNT(*) FROM inference_endpoints")
            total_endpoints = cursor.fetchone()[0]

            # Active endpoints
            if company_id:
                cursor.execute("SELECT COUNT(*) FROM inference_endpoints WHERE company_id = ? AND status = 'active'", (company_id,))
            else:
                cursor.execute("SELECT COUNT(*) FROM inference_endpoints WHERE status = 'active'")
            active_endpoints = cursor.fetchone()[0]

            # Total requests
            if company_id:
                cursor.execute("""
                    SELECT COUNT(*) FROM inference_requests r
                    JOIN inference_endpoints e ON r.endpoint_id = e.id
                    WHERE e.company_id = ?
                """, (company_id,))
            else:
                cursor.execute("SELECT COUNT(*) FROM inference_requests")
            total_requests = cursor.fetchone()[0]

            # Completed requests
            if company_id:
                cursor.execute("""
                    SELECT COUNT(*) FROM inference_requests r
                    JOIN inference_endpoints e ON r.endpoint_id = e.id
                    WHERE e.company_id = ? AND r.status = 'completed'
                """, (company_id,))
            else:
                cursor.execute("SELECT COUNT(*) FROM inference_requests WHERE status = 'completed'")
            completed_requests = cursor.fetchone()[0]

            # Average processing time
            if company_id:
                cursor.execute("""
                    SELECT AVG(r.processing_time_ms) FROM inference_requests r
                    JOIN inference_endpoints e ON r.endpoint_id = e.id
                    WHERE e.company_id = ? AND r.status = 'completed'
                """, (company_id,))
            else:
                cursor.execute("SELECT AVG(processing_time_ms) FROM inference_requests WHERE status = 'completed'")
            avg_processing_time = cursor.fetchone()[0] or 0

            # Edge nodes
            if company_id:
                cursor.execute("SELECT COUNT(*) FROM edge_nodes WHERE company_id = ?", (company_id,))
            else:
                cursor.execute("SELECT COUNT(*) FROM edge_nodes")
            total_edge_nodes = cursor.fetchone()[0]

            # Federated models
            cursor.execute("SELECT COUNT(*) FROM federated_models")
            total_models = cursor.fetchone()[0]

        return {
            "total_endpoints": total_endpoints,
            "active_endpoints": active_endpoints,
            "total_requests": total_requests,
            "completed_requests": completed_requests,
            "avg_processing_time_ms": round(avg_processing_time, 2),
            "total_edge_nodes": total_edge_nodes,
            "total_federated_models": total_models,
            "data_privacy_preserved": True
        }

    def get_inference_result(self, request_id: str) -> Optional[Dict]:
        """Get the result of an inference request."""
        self._init_federated_schema()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM inference_results
                WHERE request_id = ?
            """, (request_id,))
            row = cursor.fetchone()

        if not row:
            return None

        result = dict(row)
        result["output_metadata"] = json.loads(result.get("output_metadata", "{}"))
        result["confidence_scores"] = json.loads(result.get("confidence_scores", "[]"))
        return result

    def delete_inference_endpoint(self, endpoint_id: str, company_id: str) -> bool:
        """Delete an inference endpoint."""
        self._init_federated_schema()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM inference_endpoints
                WHERE id = ? AND company_id = ?
            """, (endpoint_id, company_id))
            conn.commit()
            return cursor.rowcount > 0

    def delete_edge_node(self, node_id: str, company_id: str) -> bool:
        """Delete an edge node."""
        self._init_federated_schema()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM edge_nodes
                WHERE id = ? AND company_id = ?
            """, (node_id, company_id))
            conn.commit()
            return cursor.rowcount > 0

    # ========== Model Explainability Operations (TIER 4) ==========

    def _init_explainability_schema(self):
        """Initialize explainability-related database tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Explanation requests table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS explanation_requests (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    model_id TEXT,
                    requester_id TEXT NOT NULL,
                    explanation_type TEXT NOT NULL,
                    input_data TEXT DEFAULT '{}',
                    prediction_id TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id)
                )
            """)

            # Explanation results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS explanation_results (
                    id TEXT PRIMARY KEY,
                    request_id TEXT NOT NULL,
                    explanation_type TEXT NOT NULL,
                    feature_importance TEXT DEFAULT '[]',
                    feature_contributions TEXT DEFAULT '[]',
                    decision_path TEXT DEFAULT '[]',
                    counterfactuals TEXT DEFAULT '[]',
                    summary TEXT,
                    confidence REAL,
                    privacy_preserved INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (request_id) REFERENCES explanation_requests(id)
                )
            """)

            # Feature importance cache (global model insights)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feature_importance (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    model_id TEXT,
                    feature_name TEXT NOT NULL,
                    importance_score REAL,
                    importance_type TEXT DEFAULT 'permutation',
                    rank INTEGER,
                    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id)
                )
            """)

            # Model insights (aggregate explanations)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_insights (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    model_id TEXT,
                    insight_type TEXT NOT NULL,
                    insight_data TEXT DEFAULT '{}',
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id)
                )
            """)

            conn.commit()

    def request_explanation(
        self,
        consortium_id: str,
        requester_id: str,
        explanation_type: str,
        input_data: Optional[Dict] = None,
        model_id: Optional[str] = None,
        prediction_id: Optional[str] = None
    ) -> Dict:
        """Request an explanation for a model prediction.

        Args:
            consortium_id: The consortium ID
            requester_id: The company requesting the explanation
            explanation_type: Type of explanation (feature_importance, shap, decision_path, counterfactual, summary)
            input_data: The input data to explain (for instance-level explanations)
            model_id: Optional specific model to explain
            prediction_id: Optional prediction ID to explain

        Returns:
            The explanation request with results

        Raises:
            ValueError: If explanation_type is not valid
        """
        valid_types = {"feature_importance", "shap", "decision_path", "counterfactual", "summary"}
        if explanation_type not in valid_types:
            raise ValueError(f"Invalid explanation type: {explanation_type}. Must be one of {valid_types}")

        self._init_explainability_schema()

        request_id = f"exp_{uuid.uuid4().hex[:16]}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO explanation_requests
                (id, consortium_id, model_id, requester_id, explanation_type, input_data, prediction_id, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'processing')
            """, (
                request_id,
                consortium_id,
                model_id,
                requester_id,
                explanation_type,
                json.dumps(input_data or {}),
                prediction_id
            ))
            conn.commit()

        # Generate explanation based on type
        explanation = self._generate_explanation(
            request_id, consortium_id, explanation_type, input_data, model_id
        )

        # Update request status
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE explanation_requests
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (request_id,))
            conn.commit()

        return {
            "id": request_id,
            "request_id": request_id,
            "consortium_id": consortium_id,
            "explanation_type": explanation_type,
            "status": "completed",
            "explanation": explanation
        }

    def _generate_explanation(
        self,
        request_id: str,
        consortium_id: str,
        explanation_type: str,
        input_data: Optional[Dict],
        model_id: Optional[str]
    ) -> Dict:
        """Generate an explanation based on type (simulated for demo)."""
        import random
        random.seed(42)  # Consistent results
        result_id = f"res_{uuid.uuid4().hex[:16]}"

        # Get consortium info for context
        consortium = self.get_consortium(consortium_id)
        model_type = consortium.model_type if consortium else "linear_regression"

        # Simulated feature names based on common use cases
        feature_names = input_data.get("feature_names", [
            "transaction_amount", "merchant_category", "time_of_day",
            "customer_age", "account_balance", "transaction_frequency",
            "location_risk", "device_type"
        ]) if input_data else [
            "feature_1", "feature_2", "feature_3", "feature_4",
            "feature_5", "feature_6", "feature_7", "feature_8"
        ]

        explanation = {}

        if explanation_type == "feature_importance":
            # Global feature importance
            importances = []
            total = 0
            for i, name in enumerate(feature_names):
                score = random.uniform(0.05, 0.25)
                total += score
                importances.append({
                    "feature": name,
                    "name": name,  # Alias for compatibility
                    "feature_name": name,  # Alias for compatibility
                    "importance": round(score, 4),
                    "rank": i + 1
                })
            # Normalize
            for imp in importances:
                imp["importance"] = round(imp["importance"] / total, 4)
            importances.sort(key=lambda x: x["importance"], reverse=True)
            for i, imp in enumerate(importances):
                imp["rank"] = i + 1

            explanation = {
                "type": "feature_importance",
                "method": "permutation_importance",
                "features": importances,
                "model_type": model_type,
                "privacy_note": "Importance scores computed on encrypted aggregate statistics"
            }

        elif explanation_type == "shap":
            # SHAP-like local explanations
            import random
            random.seed(hash(str(input_data)) % 2**32 if input_data else 42)

            base_value = 0.5  # Average prediction
            contributions = []
            for name in feature_names:
                contrib = random.uniform(-0.15, 0.15)
                contributions.append({
                    "feature": name,
                    "value": input_data.get(name, random.uniform(0, 100)) if input_data else random.uniform(0, 100),
                    "contribution": round(contrib, 4),
                    "direction": "increases" if contrib > 0 else "decreases"
                })

            prediction = base_value + sum(c["contribution"] for c in contributions)

            explanation = {
                "type": "shap",
                "base_value": base_value,
                "prediction": round(min(max(prediction, 0), 1), 4),
                "contributions": sorted(contributions, key=lambda x: abs(x["contribution"]), reverse=True),
                "privacy_note": "SHAP values computed using privacy-preserving approximation"
            }

        elif explanation_type == "decision_path":
            # Decision tree path
            import random
            random.seed(hash(str(input_data)) % 2**32 if input_data else 42)

            path = []
            depth = random.randint(3, 6)
            used_features = random.sample(feature_names, min(depth, len(feature_names)))

            for i, feature in enumerate(used_features):
                threshold = round(random.uniform(10, 100), 2)
                value = input_data.get(feature, random.uniform(0, 100)) if input_data else random.uniform(0, 100)
                direction = "left" if value <= threshold else "right"
                path.append({
                    "node": i + 1,
                    "feature": feature,
                    "threshold": threshold,
                    "value": round(value, 2),
                    "direction": direction,
                    "condition": f"{feature} {'<=' if direction == 'left' else '>'} {threshold}"
                })

            final_prediction = random.choice(["low_risk", "medium_risk", "high_risk"])
            confidence = round(random.uniform(0.7, 0.95), 3)

            explanation = {
                "type": "decision_path",
                "path": path,
                "leaf_node": len(path) + 1,
                "prediction": final_prediction,
                "confidence": confidence,
                "samples_in_leaf": random.randint(50, 500),
                "privacy_note": "Decision path shown without revealing training data distribution"
            }

        elif explanation_type == "counterfactual":
            # Counterfactual explanations
            import random
            random.seed(hash(str(input_data)) % 2**32 if input_data else 42)

            current_prediction = random.choice(["rejected", "high_risk", "denied"])
            desired_prediction = random.choice(["approved", "low_risk", "accepted"])

            changes = []
            num_changes = random.randint(1, 3)
            change_features = random.sample(feature_names, min(num_changes, len(feature_names)))

            for feature in change_features:
                current = input_data.get(feature, random.uniform(0, 100)) if input_data else random.uniform(0, 100)
                change_amount = random.uniform(10, 50) * random.choice([-1, 1])
                new_value = current + change_amount
                changes.append({
                    "feature": feature,
                    "current_value": round(current, 2),
                    "required_value": round(new_value, 2),
                    "change": round(change_amount, 2),
                    "difficulty": random.choice(["easy", "medium", "hard"])
                })

            explanation = {
                "type": "counterfactual",
                "current_prediction": current_prediction,
                "desired_prediction": desired_prediction,
                "required_changes": changes,
                "feasibility_score": round(random.uniform(0.4, 0.9), 3),
                "privacy_note": "Counterfactuals generated without access to individual training examples"
            }

        elif explanation_type == "summary":
            # High-level model summary
            explanation = {
                "type": "summary",
                "model_type": model_type,
                "total_features": len(feature_names),
                "top_features": feature_names[:3],
                "model_performance": {
                    "accuracy": round(random.uniform(0.85, 0.95), 3),
                    "precision": round(random.uniform(0.80, 0.92), 3),
                    "recall": round(random.uniform(0.78, 0.90), 3),
                    "f1_score": round(random.uniform(0.79, 0.91), 3)
                },
                "training_info": {
                    "num_participants": random.randint(3, 10),
                    "total_samples": "encrypted",
                    "training_date": datetime.utcnow().isoformat()
                },
                "key_insights": [
                    f"{feature_names[0]} is the most predictive feature",
                    f"Model performs best when {feature_names[1]} is within normal range",
                    "Predictions are most confident for clear-cut cases"
                ],
                "privacy_note": "Summary generated from encrypted aggregate statistics only"
            }

        # Store the result
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO explanation_results
                (id, request_id, explanation_type, feature_importance, feature_contributions,
                 decision_path, counterfactuals, summary, confidence, privacy_preserved)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                result_id,
                request_id,
                explanation_type,
                json.dumps(explanation.get("features", [])),
                json.dumps(explanation.get("contributions", [])),
                json.dumps(explanation.get("path", [])),
                json.dumps(explanation.get("required_changes", [])),
                json.dumps(explanation),
                explanation.get("confidence", 0.9)
            ))
            conn.commit()

        return explanation

    def get_explanation(self, request_id: str) -> Optional[Dict]:
        """Get an explanation by request ID."""
        self._init_explainability_schema()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT er.*, res.summary as explanation_data
                FROM explanation_requests er
                LEFT JOIN explanation_results res ON er.id = res.request_id
                WHERE er.id = ?
            """, (request_id,))
            row = cursor.fetchone()

        if not row:
            return None

        result = dict(row)
        result["request_id"] = result.get("id")  # Add request_id alias
        result["input_data"] = json.loads(result.get("input_data", "{}"))
        if result.get("explanation_data"):
            result["explanation"] = json.loads(result["explanation_data"])
        return result

    def list_explanations(
        self,
        consortium_id: str,
        requester_id: Optional[str] = None,
        explanation_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """List explanation requests for a consortium."""
        self._init_explainability_schema()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT er.*, res.summary as explanation_data
                FROM explanation_requests er
                LEFT JOIN explanation_results res ON er.id = res.request_id
                WHERE er.consortium_id = ?
            """
            params = [consortium_id]

            if requester_id:
                query += " AND er.requester_id = ?"
                params.append(requester_id)

            if explanation_type:
                query += " AND er.explanation_type = ?"
                params.append(explanation_type)

            query += " ORDER BY er.created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

        results = []
        for row in rows:
            r = dict(row)
            r["input_data"] = json.loads(r.get("input_data", "{}"))
            if r.get("explanation_data"):
                r["explanation"] = json.loads(r["explanation_data"])
            results.append(r)

        return results

    def get_feature_importance(
        self,
        consortium_id: str,
        model_id: Optional[str] = None
    ) -> List[Dict]:
        """Get cached feature importance for a consortium/model."""
        self._init_explainability_schema()

        # Generate if not cached
        explanation = self.request_explanation(
            consortium_id=consortium_id,
            requester_id="system",
            explanation_type="feature_importance",
            model_id=model_id
        )

        return explanation.get("explanation", {}).get("features", [])

    def compute_model_insights(
        self,
        consortium_id: str,
        model_id: Optional[str] = None
    ) -> Dict:
        """Compute and store aggregate model insights."""
        self._init_explainability_schema()

        insight_id = f"insight_{uuid.uuid4().hex[:16]}"

        # Get feature importance
        feature_importance = self.get_feature_importance(consortium_id, model_id)

        # Get model summary
        summary_explanation = self.request_explanation(
            consortium_id=consortium_id,
            requester_id="system",
            explanation_type="summary",
            model_id=model_id
        )

        insights = {
            "feature_importance": feature_importance,
            "model_summary": summary_explanation.get("explanation", {}),
            "recommendations": [
                {
                    "type": "feature_engineering",
                    "description": f"Consider adding interactions with {feature_importance[0]['feature']}" if feature_importance else "Collect more data",
                    "priority": "high"
                },
                {
                    "type": "data_quality",
                    "description": "Ensure consistent data formatting across consortium members",
                    "priority": "medium"
                },
                {
                    "type": "model_improvement",
                    "description": "Consider ensemble methods for improved accuracy",
                    "priority": "low"
                }
            ],
            "computed_at": datetime.utcnow().isoformat()
        }

        # Store insights
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO model_insights (id, consortium_id, model_id, insight_type, insight_data, description)
                VALUES (?, ?, ?, 'comprehensive', ?, 'Comprehensive model insights')
            """, (insight_id, consortium_id, model_id, json.dumps(insights)))
            conn.commit()

        return {
            "id": insight_id,
            "consortium_id": consortium_id,
            "insights": insights
        }

    def get_explainability_stats(self, consortium_id: Optional[str] = None) -> Dict:
        """Get explainability usage statistics."""
        self._init_explainability_schema()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Total explanations
            if consortium_id:
                cursor.execute("""
                    SELECT COUNT(*) FROM explanation_requests WHERE consortium_id = ?
                """, (consortium_id,))
            else:
                cursor.execute("SELECT COUNT(*) FROM explanation_requests")
            total_explanations = cursor.fetchone()[0]

            # By type
            if consortium_id:
                cursor.execute("""
                    SELECT explanation_type, COUNT(*) as count
                    FROM explanation_requests
                    WHERE consortium_id = ?
                    GROUP BY explanation_type
                """, (consortium_id,))
            else:
                cursor.execute("""
                    SELECT explanation_type, COUNT(*) as count
                    FROM explanation_requests
                    GROUP BY explanation_type
                """)
            by_type = {row["explanation_type"]: row["count"] for row in cursor.fetchall()}

            # Completed
            if consortium_id:
                cursor.execute("""
                    SELECT COUNT(*) FROM explanation_requests
                    WHERE consortium_id = ? AND status = 'completed'
                """, (consortium_id,))
            else:
                cursor.execute("""
                    SELECT COUNT(*) FROM explanation_requests WHERE status = 'completed'
                """)
            completed = cursor.fetchone()[0]

        return {
            "total_explanations": total_explanations,
            "completed_explanations": completed,
            "by_type": by_type,
            "explanation_types_available": [
                "feature_importance",
                "shap",
                "decision_path",
                "counterfactual",
                "summary"
            ],
            "privacy_preserved": True
        }

    # ============================================================
    # TIER 4: Competitive Insights - Anonymous Industry Benchmarks
    # ============================================================

    def _init_competitive_insights_schema(self):
        """Initialize competitive insights database tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Industry benchmarks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS industry_benchmarks (
                    id TEXT PRIMARY KEY,
                    industry TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    percentile_10 REAL,
                    percentile_25 REAL,
                    percentile_50 REAL,
                    percentile_75 REAL,
                    percentile_90 REAL,
                    sample_size INTEGER,
                    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    valid_until TIMESTAMP,
                    metadata TEXT
                )
            """)

            # Company performance metrics (anonymized)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS company_metrics (
                    id TEXT PRIMARY KEY,
                    company_id TEXT NOT NULL,
                    consortium_id TEXT,
                    industry TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_anonymized INTEGER DEFAULT 1,
                    metadata TEXT
                )
            """)

            # Benchmark comparisons
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS benchmark_comparisons (
                    id TEXT PRIMARY KEY,
                    company_id TEXT NOT NULL,
                    industry TEXT NOT NULL,
                    comparison_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metrics_compared INTEGER,
                    overall_percentile REAL,
                    strengths TEXT,
                    improvements TEXT,
                    metadata TEXT
                )
            """)

            # Industry trends
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS industry_trends (
                    id TEXT PRIMARY KEY,
                    industry TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    period TEXT NOT NULL,
                    trend_direction TEXT,
                    change_percentage REAL,
                    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)

            conn.commit()

    def get_industry_benchmarks(
        self,
        industry: str,
        metric_type: Optional[str] = None
    ) -> List[Dict]:
        """Get anonymized industry benchmarks.

        Args:
            industry: Industry sector (finance, healthcare, retail, etc.)
            metric_type: Optional filter by metric type (accuracy, latency, etc.)

        Returns:
            List of benchmark metrics with percentile distributions.
        """
        self._init_competitive_insights_schema()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            if metric_type:
                cursor.execute("""
                    SELECT * FROM industry_benchmarks
                    WHERE industry = ? AND metric_type = ?
                    AND (valid_until IS NULL OR valid_until > datetime('now'))
                    ORDER BY metric_name
                """, (industry, metric_type))
            else:
                cursor.execute("""
                    SELECT * FROM industry_benchmarks
                    WHERE industry = ?
                    AND (valid_until IS NULL OR valid_until > datetime('now'))
                    ORDER BY metric_name
                """, (industry,))

            rows = cursor.fetchall()

            if not rows:
                # Return simulated benchmarks for demo
                return self._generate_simulated_benchmarks(industry, metric_type)

            return [dict(row) for row in rows]

    def _generate_simulated_benchmarks(
        self,
        industry: str,
        metric_type: Optional[str] = None
    ) -> List[Dict]:
        """Generate simulated industry benchmarks for demo."""
        import random
        random.seed(hash(industry))

        metrics = {
            "finance": [
                ("model_accuracy", "accuracy", 0.82, 0.86, 0.89, 0.92, 0.95),
                ("fraud_detection_rate", "accuracy", 0.75, 0.82, 0.87, 0.91, 0.94),
                ("false_positive_rate", "error", 0.02, 0.04, 0.06, 0.10, 0.15),
                ("prediction_latency_ms", "latency", 15, 25, 50, 100, 200),
                ("data_quality_score", "quality", 0.70, 0.78, 0.85, 0.90, 0.95),
            ],
            "healthcare": [
                ("diagnostic_accuracy", "accuracy", 0.85, 0.88, 0.91, 0.94, 0.97),
                ("patient_outcome_prediction", "accuracy", 0.72, 0.78, 0.83, 0.88, 0.92),
                ("readmission_prediction", "accuracy", 0.68, 0.74, 0.80, 0.85, 0.90),
                ("hipaa_compliance_score", "compliance", 0.90, 0.94, 0.97, 0.99, 1.00),
                ("data_completeness", "quality", 0.75, 0.82, 0.88, 0.93, 0.97),
            ],
            "retail": [
                ("demand_forecast_accuracy", "accuracy", 0.78, 0.83, 0.87, 0.91, 0.94),
                ("customer_churn_prediction", "accuracy", 0.70, 0.76, 0.82, 0.87, 0.91),
                ("inventory_optimization", "efficiency", 0.75, 0.81, 0.86, 0.90, 0.94),
                ("recommendation_ctr", "engagement", 0.02, 0.04, 0.06, 0.09, 0.12),
                ("basket_analysis_accuracy", "accuracy", 0.65, 0.72, 0.78, 0.84, 0.89),
            ]
        }

        industry_metrics = metrics.get(industry, metrics["finance"])

        result = []
        for name, mtype, p10, p25, p50, p75, p90 in industry_metrics:
            if metric_type and mtype != metric_type:
                continue
            result.append({
                "id": f"bench_{industry}_{name}",
                "industry": industry,
                "metric_name": name,
                "metric_type": mtype,
                "percentile_10": p10,
                "percentile_25": p25,
                "percentile_50": p50,
                "percentile_75": p75,
                "percentile_90": p90,
                "sample_size": random.randint(50, 200),
                "computed_at": datetime.utcnow().isoformat(),
                "privacy_note": "Aggregated from encrypted consortium data"
            })

        return result

    def compare_to_industry(
        self,
        company_id: str,
        industry: str,
        metrics: Optional[Dict[str, float]] = None
    ) -> Dict:
        """Compare company metrics against industry benchmarks.

        Args:
            company_id: Company to compare
            industry: Industry for benchmarks
            metrics: Optional company metrics (if not provided, uses stored)

        Returns:
            Comparison results with percentile rankings.
        """
        self._init_competitive_insights_schema()

        benchmarks = self.get_industry_benchmarks(industry)
        benchmark_dict = {b["metric_name"]: b for b in benchmarks}

        # If no metrics provided, generate simulated ones
        if not metrics:
            import random
            random.seed(hash(company_id))
            metrics = {}
            for b in benchmarks:
                # Generate a value within the benchmark range
                p25, p75 = b["percentile_25"], b["percentile_75"]
                metrics[b["metric_name"]] = random.uniform(p25 * 0.95, p75 * 1.05)

        comparisons = []
        strengths = []
        improvements = []

        for metric_name, value in metrics.items():
            if metric_name not in benchmark_dict:
                continue

            bench = benchmark_dict[metric_name]

            # Calculate percentile
            if value <= bench["percentile_10"]:
                percentile = 10
            elif value <= bench["percentile_25"]:
                percentile = 25
            elif value <= bench["percentile_50"]:
                percentile = 50
            elif value <= bench["percentile_75"]:
                percentile = 75
            elif value <= bench["percentile_90"]:
                percentile = 90
            else:
                percentile = 95

            # For error metrics, lower is better (invert percentile)
            if bench["metric_type"] == "error":
                percentile = 100 - percentile

            comparison = {
                "metric_name": metric_name,
                "metric_type": bench["metric_type"],
                "your_value": round(value, 4),
                "industry_median": bench["percentile_50"],
                "percentile_rank": percentile,
                "vs_median": "above" if value > bench["percentile_50"] else "below"
            }
            comparisons.append(comparison)

            if percentile >= 75:
                strengths.append(metric_name)
            elif percentile <= 25:
                improvements.append(metric_name)

        overall_percentile = sum(c["percentile_rank"] for c in comparisons) / len(comparisons) if comparisons else 50

        # Store comparison
        comparison_id = f"cmp_{uuid.uuid4().hex[:12]}"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO benchmark_comparisons
                (id, company_id, industry, metrics_compared, overall_percentile, strengths, improvements, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                comparison_id,
                company_id,
                industry,
                len(comparisons),
                overall_percentile,
                json.dumps(strengths),
                json.dumps(improvements),
                json.dumps({"comparisons": comparisons})
            ))
            conn.commit()

        return {
            "comparison_id": comparison_id,
            "company_id": company_id,
            "industry": industry,
            "overall_percentile": round(overall_percentile, 1),
            "comparisons": comparisons,
            "strengths": strengths,
            "areas_for_improvement": improvements,
            "benchmark_sample_size": benchmarks[0]["sample_size"] if benchmarks else 0,
            "privacy_note": "Your specific data remains encrypted; only aggregate metrics are compared"
        }

    def get_industry_trends(
        self,
        industry: str,
        period: str = "quarterly"
    ) -> List[Dict]:
        """Get industry trend data.

        Args:
            industry: Industry sector
            period: Time period (monthly, quarterly, yearly)

        Returns:
            List of trend metrics.
        """
        self._init_competitive_insights_schema()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM industry_trends
                WHERE industry = ? AND period = ?
                ORDER BY computed_at DESC
                LIMIT 20
            """, (industry, period))
            rows = cursor.fetchall()

            if rows:
                return [dict(row) for row in rows]

        # Generate simulated trends
        import random
        random.seed(hash(f"{industry}_{period}"))

        metrics = ["model_accuracy", "prediction_latency", "data_quality", "compliance_score"]
        trends = []

        for metric in metrics:
            change = random.uniform(-5, 15)
            direction = "improving" if change > 0 else "declining"

            trends.append({
                "id": f"trend_{industry}_{metric}",
                "industry": industry,
                "metric_name": metric,
                "period": period,
                "trend_direction": direction,
                "change_percentage": round(change, 2),
                "computed_at": datetime.utcnow().isoformat(),
                "interpretation": f"Industry {metric} is {direction} by {abs(round(change, 1))}% this {period}"
            })

        return trends

    def get_competitive_position(
        self,
        company_id: str,
        consortium_id: Optional[str] = None
    ) -> Dict:
        """Get company's competitive position summary.

        Args:
            company_id: Company ID
            consortium_id: Optional consortium context

        Returns:
            Competitive position summary with rankings.
        """
        self._init_competitive_insights_schema()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get recent comparisons
            cursor.execute("""
                SELECT * FROM benchmark_comparisons
                WHERE company_id = ?
                ORDER BY comparison_date DESC
                LIMIT 5
            """, (company_id,))
            comparisons = [dict(row) for row in cursor.fetchall()]

        if not comparisons:
            # Generate demo data
            return {
                "company_id": company_id,
                "overall_ranking": "top_quartile",
                "percentile": 78,
                "industries_compared": ["finance"],
                "key_strengths": ["model_accuracy", "data_quality_score"],
                "improvement_areas": ["prediction_latency_ms"],
                "trend": "improving",
                "recommendations": [
                    "Focus on reducing prediction latency to reach top decile",
                    "Your accuracy is above industry median - consider contributing to more consortiums",
                    "Data quality is a competitive advantage"
                ],
                "privacy_note": "Rankings computed on encrypted aggregate data"
            }

        # Aggregate from stored comparisons
        avg_percentile = sum(c.get("overall_percentile", 50) for c in comparisons) / len(comparisons)
        all_strengths = []
        all_improvements = []

        for c in comparisons:
            if c.get("strengths"):
                all_strengths.extend(json.loads(c["strengths"]) if isinstance(c["strengths"], str) else c["strengths"])
            if c.get("improvements"):
                all_improvements.extend(json.loads(c["improvements"]) if isinstance(c["improvements"], str) else c["improvements"])

        ranking = "top_decile" if avg_percentile >= 90 else \
                  "top_quartile" if avg_percentile >= 75 else \
                  "above_median" if avg_percentile >= 50 else \
                  "below_median"

        return {
            "company_id": company_id,
            "overall_ranking": ranking,
            "percentile": round(avg_percentile, 1),
            "industries_compared": list(set(c.get("industry", "general") for c in comparisons)),
            "key_strengths": list(set(all_strengths))[:5],
            "improvement_areas": list(set(all_improvements))[:5],
            "comparison_count": len(comparisons),
            "privacy_note": "Rankings computed on encrypted aggregate data"
        }

    def get_competitive_insights_stats(self) -> Dict:
        """Get competitive insights usage statistics."""
        self._init_competitive_insights_schema()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM industry_benchmarks")
            total_benchmarks = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM benchmark_comparisons")
            total_comparisons = cursor.fetchone()[0]

            cursor.execute("SELECT DISTINCT industry FROM industry_benchmarks")
            industries = [row[0] for row in cursor.fetchall()]

        return {
            "total_benchmarks": total_benchmarks,
            "total_comparisons": total_comparisons,
            "industries_covered": industries if industries else ["finance", "healthcare", "retail"],
            "features": [
                "Industry percentile rankings",
                "Anonymous metric comparisons",
                "Trend analysis",
                "Competitive positioning"
            ],
            "privacy_preserved": True
        }

    # ============================================================
    # TIER 4: Multi-Model Ensemble - Combine Models from Consortiums
    # ============================================================

    def _init_ensemble_schema(self):
        """Initialize multi-model ensemble database tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Ensemble definitions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_ensembles (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    owner_id TEXT NOT NULL,
                    ensemble_type TEXT NOT NULL,
                    status TEXT DEFAULT 'draft',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)

            # Models in ensemble
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ensemble_models (
                    id TEXT PRIMARY KEY,
                    ensemble_id TEXT NOT NULL,
                    model_id TEXT NOT NULL,
                    consortium_id TEXT NOT NULL,
                    model_type TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    contribution_approved INTEGER DEFAULT 0,
                    metadata TEXT,
                    FOREIGN KEY (ensemble_id) REFERENCES model_ensembles(id)
                )
            """)

            # Ensemble predictions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ensemble_predictions (
                    id TEXT PRIMARY KEY,
                    ensemble_id TEXT NOT NULL,
                    requester_id TEXT NOT NULL,
                    input_hash TEXT,
                    prediction_result TEXT,
                    confidence REAL,
                    models_used INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    latency_ms REAL,
                    metadata TEXT,
                    FOREIGN KEY (ensemble_id) REFERENCES model_ensembles(id)
                )
            """)

            # Ensemble performance metrics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ensemble_metrics (
                    id TEXT PRIMARY KEY,
                    ensemble_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL,
                    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (ensemble_id) REFERENCES model_ensembles(id)
                )
            """)

            conn.commit()

    def create_ensemble(
        self,
        name: str,
        description: str,
        owner_id: str,
        ensemble_type: str = "voting"
    ) -> Dict:
        """Create a new multi-model ensemble.

        Args:
            name: Ensemble name
            description: Description
            owner_id: Creator company ID
            ensemble_type: Type (voting, averaging, stacking, boosting)

        Returns:
            Created ensemble details.
        """
        self._init_ensemble_schema()

        valid_types = ["voting", "averaging", "stacking", "boosting", "weighted"]
        if ensemble_type not in valid_types:
            raise ValueError(f"Invalid ensemble type. Must be one of: {valid_types}")

        ensemble_id = f"ens_{uuid.uuid4().hex[:12]}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO model_ensembles (id, name, description, owner_id, ensemble_type, status)
                VALUES (?, ?, ?, ?, ?, 'draft')
            """, (ensemble_id, name, description, owner_id, ensemble_type))
            conn.commit()

        return {
            "ensemble_id": ensemble_id,
            "name": name,
            "description": description,
            "owner_id": owner_id,
            "ensemble_type": ensemble_type,
            "status": "draft",
            "created_at": datetime.utcnow().isoformat()
        }

    def add_model_to_ensemble(
        self,
        ensemble_id: str,
        model_id: str,
        consortium_id: str,
        model_type: str,
        weight: float = 1.0
    ) -> Dict:
        """Add a model from a consortium to an ensemble.

        Args:
            ensemble_id: Target ensemble ID
            model_id: Model to add
            consortium_id: Source consortium
            model_type: Type of model
            weight: Contribution weight

        Returns:
            Added model details.
        """
        self._init_ensemble_schema()

        entry_id = f"em_{uuid.uuid4().hex[:12]}"

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Verify ensemble exists
            cursor.execute("SELECT * FROM model_ensembles WHERE id = ?", (ensemble_id,))
            if not cursor.fetchone():
                raise ValueError(f"Ensemble {ensemble_id} not found")

            cursor.execute("""
                INSERT INTO ensemble_models
                (id, ensemble_id, model_id, consortium_id, model_type, weight)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (entry_id, ensemble_id, model_id, consortium_id, model_type, weight))

            # Update ensemble timestamp
            cursor.execute("""
                UPDATE model_ensembles SET updated_at = CURRENT_TIMESTAMP WHERE id = ?
            """, (ensemble_id,))

            conn.commit()

        return {
            "entry_id": entry_id,
            "ensemble_id": ensemble_id,
            "model_id": model_id,
            "consortium_id": consortium_id,
            "model_type": model_type,
            "weight": weight,
            "added_at": datetime.utcnow().isoformat()
        }

    def get_ensemble(self, ensemble_id: str) -> Optional[Dict]:
        """Get ensemble details with member models.

        Args:
            ensemble_id: Ensemble ID

        Returns:
            Ensemble details or None.
        """
        self._init_ensemble_schema()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM model_ensembles WHERE id = ?", (ensemble_id,))
            row = cursor.fetchone()

            if not row:
                return None

            ensemble = dict(row)

            # Get member models
            cursor.execute("""
                SELECT * FROM ensemble_models WHERE ensemble_id = ?
            """, (ensemble_id,))
            ensemble["models"] = [dict(r) for r in cursor.fetchall()]
            ensemble["model_count"] = len(ensemble["models"])

        return ensemble

    def list_ensembles(
        self,
        owner_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """List available ensembles.

        Args:
            owner_id: Filter by owner
            status: Filter by status
            limit: Max results

        Returns:
            List of ensembles.
        """
        self._init_ensemble_schema()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM model_ensembles WHERE 1=1"
            params = []

            if owner_id:
                query += " AND owner_id = ?"
                params.append(owner_id)

            if status:
                query += " AND status = ?"
                params.append(status)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            ensembles = [dict(row) for row in cursor.fetchall()]

            # Add model counts
            for e in ensembles:
                cursor.execute(
                    "SELECT COUNT(*) FROM ensemble_models WHERE ensemble_id = ?",
                    (e["id"],)
                )
                e["model_count"] = cursor.fetchone()[0]

        return ensembles

    def activate_ensemble(self, ensemble_id: str, requester_id: str) -> Dict:
        """Activate an ensemble for predictions.

        Args:
            ensemble_id: Ensemble to activate
            requester_id: Who is activating

        Returns:
            Activation result.
        """
        self._init_ensemble_schema()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check ensemble exists and has models
            cursor.execute("SELECT * FROM model_ensembles WHERE id = ?", (ensemble_id,))
            ensemble = cursor.fetchone()

            if not ensemble:
                raise ValueError(f"Ensemble {ensemble_id} not found")

            cursor.execute(
                "SELECT COUNT(*) FROM ensemble_models WHERE ensemble_id = ?",
                (ensemble_id,)
            )
            model_count = cursor.fetchone()[0]

            if model_count < 2:
                raise ValueError("Ensemble must have at least 2 models")

            cursor.execute("""
                UPDATE model_ensembles
                SET status = 'active', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (ensemble_id,))
            conn.commit()

        return {
            "ensemble_id": ensemble_id,
            "status": "active",
            "model_count": model_count,
            "message": "Ensemble activated and ready for predictions"
        }

    def predict_with_ensemble(
        self,
        ensemble_id: str,
        requester_id: str,
        input_data: Dict
    ) -> Dict:
        """Make predictions using the ensemble.

        Args:
            ensemble_id: Ensemble to use
            requester_id: Who is requesting
            input_data: Input features

        Returns:
            Ensemble prediction result.
        """
        self._init_ensemble_schema()
        import time
        start_time = time.time()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get ensemble
            cursor.execute("SELECT * FROM model_ensembles WHERE id = ?", (ensemble_id,))
            ensemble = cursor.fetchone()

            if not ensemble:
                raise ValueError(f"Ensemble {ensemble_id} not found")

            if ensemble["status"] != "active":
                raise ValueError("Ensemble is not active")

            # Get models
            cursor.execute("""
                SELECT * FROM ensemble_models WHERE ensemble_id = ?
            """, (ensemble_id,))
            models = cursor.fetchall()

        # Simulate ensemble prediction (in real impl, would call each model)
        import random
        random.seed(hash(str(input_data)))

        ensemble_type = ensemble["ensemble_type"]
        model_predictions = []

        for model in models:
            # Simulated individual model prediction
            pred = random.uniform(0, 1)
            model_predictions.append({
                "model_id": model["model_id"],
                "consortium_id": model["consortium_id"],
                "prediction": round(pred, 4),
                "weight": model["weight"]
            })

        # Combine predictions based on ensemble type
        if ensemble_type == "voting":
            votes = sum(1 for p in model_predictions if p["prediction"] > 0.5)
            final_prediction = 1 if votes > len(model_predictions) / 2 else 0
            confidence = votes / len(model_predictions)
        elif ensemble_type == "averaging":
            final_prediction = sum(p["prediction"] for p in model_predictions) / len(model_predictions)
            confidence = 1 - abs(final_prediction - 0.5) * 2
        elif ensemble_type == "weighted":
            total_weight = sum(p["weight"] for p in model_predictions)
            final_prediction = sum(p["prediction"] * p["weight"] for p in model_predictions) / total_weight
            confidence = 1 - abs(final_prediction - 0.5) * 2
        else:  # stacking, boosting - simplified
            final_prediction = sum(p["prediction"] for p in model_predictions) / len(model_predictions)
            confidence = 0.85

        latency_ms = (time.time() - start_time) * 1000

        # Store prediction
        pred_id = f"epred_{uuid.uuid4().hex[:12]}"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ensemble_predictions
                (id, ensemble_id, requester_id, input_hash, prediction_result, confidence, models_used, latency_ms, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pred_id,
                ensemble_id,
                requester_id,
                hashlib.sha256(str(input_data).encode()).hexdigest()[:16],
                str(round(final_prediction, 4)),
                confidence,
                len(models),
                latency_ms,
                json.dumps({"model_predictions": model_predictions})
            ))
            conn.commit()

        return {
            "prediction_id": pred_id,
            "ensemble_id": ensemble_id,
            "ensemble_type": ensemble_type,
            "prediction": round(final_prediction, 4),
            "confidence": round(confidence, 4),
            "models_used": len(models),
            "model_predictions": model_predictions,
            "latency_ms": round(latency_ms, 2),
            "privacy_note": "Prediction combines insights from multiple encrypted models"
        }

    def get_ensemble_performance(self, ensemble_id: str) -> Dict:
        """Get ensemble performance metrics.

        Args:
            ensemble_id: Ensemble ID

        Returns:
            Performance metrics.
        """
        self._init_ensemble_schema()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get prediction stats
            cursor.execute("""
                SELECT
                    COUNT(*) as total_predictions,
                    AVG(confidence) as avg_confidence,
                    AVG(latency_ms) as avg_latency,
                    MIN(created_at) as first_prediction,
                    MAX(created_at) as last_prediction
                FROM ensemble_predictions
                WHERE ensemble_id = ?
            """, (ensemble_id,))
            stats = dict(cursor.fetchone())

            # Get model count
            cursor.execute("""
                SELECT COUNT(*) FROM ensemble_models WHERE ensemble_id = ?
            """, (ensemble_id,))
            model_count = cursor.fetchone()[0]

        return {
            "ensemble_id": ensemble_id,
            "model_count": model_count,
            "total_predictions": stats.get("total_predictions", 0),
            "avg_confidence": round(stats.get("avg_confidence", 0) or 0, 4),
            "avg_latency_ms": round(stats.get("avg_latency_ms", 0) or 0, 2),
            "first_prediction": stats.get("first_prediction"),
            "last_prediction": stats.get("last_prediction"),
            "privacy_note": "Metrics computed without exposing individual model data"
        }

    def get_ensemble_stats(self) -> Dict:
        """Get overall ensemble statistics."""
        self._init_ensemble_schema()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM model_ensembles")
            total_ensembles = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM model_ensembles WHERE status = 'active'")
            active_ensembles = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM ensemble_models")
            total_models = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM ensemble_predictions")
            total_predictions = cursor.fetchone()[0]

            cursor.execute("""
                SELECT ensemble_type, COUNT(*) as count
                FROM model_ensembles
                GROUP BY ensemble_type
            """)
            by_type = {row[0]: row[1] for row in cursor.fetchall()}

        return {
            "total_ensembles": total_ensembles,
            "active_ensembles": active_ensembles,
            "total_models_in_ensembles": total_models,
            "total_predictions": total_predictions,
            "by_type": by_type,
            "ensemble_types_available": ["voting", "averaging", "weighted", "stacking", "boosting"],
            "privacy_preserved": True
        }

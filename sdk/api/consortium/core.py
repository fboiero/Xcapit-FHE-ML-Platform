"""Core consortium operations.

This module contains fundamental operations for managing companies,
consortiums, memberships, invitations, and data contributions.
"""

import hashlib
import json
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from .database import DatabaseManager
from .models import (
    Company,
    Consortium,
    ConsortiumStatus,
    DataContribution,
    Invitation,
    InviteStatus,
    MemberRole,
    Membership,
    MemberStatus,
)


class CoreManager:
    """Manager for core consortium operations."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize core manager.

        Args:
            db_path: Path to SQLite database.
        """
        self._db = DatabaseManager(db_path)
        self._db.init_core_schema()

    # ========== Company Operations ==========

    def create_company(
        self, name: str, email: str, api_key: Optional[str] = None, metadata: Optional[dict] = None
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

        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO companies (id, name, email, api_key_hash, metadata)
                VALUES (?, ?, ?, ?, ?)
            """,
                (company_id, name, email, api_key_hash, json.dumps(metadata or {})),
            )

        company = Company(
            id=company_id,
            name=name,
            email=email,
            api_key_hash=api_key_hash,
            created_at=datetime.utcnow(),
            metadata=metadata or {},
        )

        return company, api_key

    def get_company_by_api_key(self, api_key: str) -> Optional[Company]:
        """Get company by API key."""
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM companies WHERE api_key_hash = ?
            """,
                (api_key_hash,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        return Company(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            api_key_hash=row["api_key_hash"],
            created_at=row["created_at"],
            metadata=json.loads(row["metadata"]),
        )

    def get_company(self, company_id: str) -> Optional[Company]:
        """Get company by ID."""
        with self._db.get_connection() as conn:
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
            metadata=json.loads(row["metadata"]),
        )

    # ========== Consortium Operations ==========

    def create_consortium(
        self,
        name: str,
        description: Optional[str] = None,
        owner_id: Optional[str] = None,
        model_type: str = "linear_regression",
        model_config: Optional[dict] = None,
        metadata: Optional[dict] = None,
        created_by: Optional[str] = None,
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
        owner_id = owner_id or created_by
        if not owner_id:
            raise ValueError("Either owner_id or created_by must be provided")

        consortium_id = f"cons_{secrets.token_hex(8)}"
        now = datetime.utcnow()

        with self._db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO consortiums
                (id, name, description, owner_id, model_type, model_config, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    consortium_id,
                    name,
                    description,
                    owner_id,
                    model_type,
                    json.dumps(model_config or {}),
                    json.dumps(metadata or {}),
                ),
            )

            membership_id = f"memb_{secrets.token_hex(8)}"
            cursor.execute(
                """
                INSERT INTO memberships
                (id, consortium_id, company_id, role, status, joined_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    membership_id,
                    consortium_id,
                    owner_id,
                    MemberRole.OWNER.value,
                    MemberStatus.ACTIVE.value,
                    now,
                ),
            )

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
            metadata=metadata or {},
        )

    def get_consortium(self, consortium_id: str) -> Optional[Consortium]:
        """Get consortium by ID."""
        with self._db.get_connection() as conn:
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
            metadata=json.loads(row["metadata"]),
        )

    def list_consortiums(
        self, company_id: Optional[str] = None, status: Optional[ConsortiumStatus] = None
    ) -> list[Consortium]:
        """List consortiums, optionally filtered.

        Args:
            company_id: Filter by company membership.
            status: Filter by status.

        Returns:
            List of consortiums.
        """
        with self._db.get_connection() as conn:
            cursor = conn.cursor()

            if company_id:
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
        self, consortium_id: str, status: ConsortiumStatus
    ) -> Optional[Consortium]:
        """Update consortium status."""
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE consortiums
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (status.value, consortium_id),
            )

        return self.get_consortium(consortium_id)

    # ========== Membership Operations ==========

    def get_members(self, consortium_id: str) -> list[dict]:
        """Get all members of a consortium with company info."""
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT m.*, c.name as company_name, c.email as company_email
                FROM memberships m
                JOIN companies c ON m.company_id = c.id
                WHERE m.consortium_id = ?
            """,
                (consortium_id,),
            )
            rows = cursor.fetchall()

        return [
            {
                "membership_id": row["id"],
                "company_id": row["company_id"],
                "company_name": row["company_name"],
                "company_email": row["company_email"],
                "role": row["role"],
                "status": row["status"],
                "joined_at": row["joined_at"],
                "data_uploaded": bool(row["data_uploaded"]),
                "data_record_count": row["data_record_count"],
                "last_upload_at": row["last_upload_at"],
            }
            for row in rows
        ]

    def get_membership(self, consortium_id: str, company_id: str) -> Optional[Membership]:
        """Get membership for a company in a consortium."""
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM memberships
                WHERE consortium_id = ? AND company_id = ?
            """,
                (consortium_id, company_id),
            )
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
            metadata=json.loads(row["metadata"]),
        )

    # ========== Invitation Operations ==========

    def create_invitation(
        self,
        consortium_id: str,
        invited_by: str,
        invite_email: str,
        role: MemberRole = MemberRole.CONTRIBUTOR,
        expires_in_days: int = 7,
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
        invitation_id = f"inv_{secrets.token_hex(8)}"
        invite_code = secrets.token_urlsafe(32)
        now = datetime.utcnow()
        expires_at = now + timedelta(days=expires_in_days)

        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO invitations
                (id, consortium_id, invited_by, invite_email, invite_code, role, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    invitation_id,
                    consortium_id,
                    invited_by,
                    invite_email,
                    invite_code,
                    role.value,
                    expires_at,
                ),
            )

        return Invitation(
            id=invitation_id,
            consortium_id=consortium_id,
            invited_by=invited_by,
            invite_email=invite_email,
            invite_code=invite_code,
            role=role,
            status=InviteStatus.PENDING,
            created_at=now,
            expires_at=expires_at,
        )

    def get_invitation_by_code(self, invite_code: str) -> Optional[Invitation]:
        """Get invitation by code."""
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM invitations WHERE invite_code = ?
            """,
                (invite_code,),
            )
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
            accepted_by=row["accepted_by"],
        )

    def accept_invitation(self, invite_code: str, company_id: str) -> Optional[Membership]:
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
            with self._db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE invitations SET status = ? WHERE id = ?
                """,
                    (InviteStatus.EXPIRED.value, invitation.id),
                )
            return None

        now = datetime.utcnow()
        membership_id = f"memb_{secrets.token_hex(8)}"

        with self._db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE invitations
                SET status = ?, accepted_at = ?, accepted_by = ?
                WHERE id = ?
            """,
                (InviteStatus.ACCEPTED.value, now, company_id, invitation.id),
            )

            cursor.execute(
                """
                INSERT INTO memberships
                (id, consortium_id, company_id, role, status, joined_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    membership_id,
                    invitation.consortium_id,
                    company_id,
                    invitation.role.value,
                    MemberStatus.ACTIVE.value,
                    now,
                ),
            )

        return Membership(
            id=membership_id,
            consortium_id=invitation.consortium_id,
            company_id=company_id,
            role=invitation.role,
            status=MemberStatus.ACTIVE,
            joined_at=now,
        )

    def list_invitations(
        self, consortium_id: str, status: Optional[InviteStatus] = None
    ) -> list[Invitation]:
        """List invitations for a consortium."""
        with self._db.get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM invitations WHERE consortium_id = ?"
            params = [consortium_id]

            if status:
                query += " AND status = ?"
                params.append(status.value)

            cursor.execute(query, params)
            rows = cursor.fetchall()

        return [
            Invitation(
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
                accepted_by=row["accepted_by"],
            )
            for row in rows
        ]

    # ========== Data Contribution Operations ==========

    def record_data_contribution(
        self,
        consortium_id: str,
        company_id: str,
        encrypted_blob_path: str,
        record_count: int,
        feature_count: int,
        checksum: str,
        metadata: Optional[dict] = None,
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

        with self._db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO data_contributions
                (id, consortium_id, company_id, encrypted_blob_path,
                 record_count, feature_count, checksum, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    contribution_id,
                    consortium_id,
                    company_id,
                    encrypted_blob_path,
                    record_count,
                    feature_count,
                    checksum,
                    json.dumps(metadata or {}),
                ),
            )

            cursor.execute(
                """
                UPDATE memberships
                SET data_uploaded = 1,
                    data_record_count = data_record_count + ?,
                    last_upload_at = ?
                WHERE consortium_id = ? AND company_id = ?
            """,
                (record_count, now, consortium_id, company_id),
            )

        return DataContribution(
            id=contribution_id,
            consortium_id=consortium_id,
            company_id=company_id,
            encrypted_blob_path=encrypted_blob_path,
            record_count=record_count,
            feature_count=feature_count,
            uploaded_at=now,
            checksum=checksum,
            metadata=metadata or {},
        )

    def get_consortium_data_summary(self, consortium_id: str) -> dict:
        """Get summary of data contributions for a consortium."""
        with self._db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    COUNT(DISTINCT company_id) as companies_contributed,
                    SUM(record_count) as total_records,
                    MAX(feature_count) as feature_count,
                    COUNT(*) as total_uploads
                FROM data_contributions
                WHERE consortium_id = ?
            """,
                (consortium_id,),
            )
            row = cursor.fetchone()

        return {
            "companies_contributed": row["companies_contributed"] or 0,
            "total_records": row["total_records"] or 0,
            "feature_count": row["feature_count"] or 0,
            "total_uploads": row["total_uploads"] or 0,
        }

    def get_data_contributions(self, consortium_id: str) -> list[DataContribution]:
        """Get all data contributions for a consortium."""
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM data_contributions WHERE consortium_id = ?
            """,
                (consortium_id,),
            )
            rows = cursor.fetchall()

        return [
            DataContribution(
                id=row["id"],
                consortium_id=row["consortium_id"],
                company_id=row["company_id"],
                encrypted_blob_path=row["encrypted_blob_path"],
                record_count=row["record_count"],
                feature_count=row["feature_count"],
                uploaded_at=row["uploaded_at"],
                checksum=row["checksum"],
                metadata=json.loads(row["metadata"]),
            )
            for row in rows
        ]

    def add_data_contribution(
        self,
        consortium_id: str,
        company_id: str,
        contribution_id: str,
        record_count: int,
        file_path: str,
        feature_count: int = 0,
        metadata: dict = None,
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

        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO data_contributions
                (id, consortium_id, company_id, encrypted_blob_path, record_count,
                 feature_count, uploaded_at, checksum, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    contribution_id,
                    consortium_id,
                    company_id,
                    file_path,
                    record_count,
                    feature_count,
                    now,
                    checksum,
                    json.dumps(metadata or {}),
                ),
            )

        return DataContribution(
            id=contribution_id,
            consortium_id=consortium_id,
            company_id=company_id,
            encrypted_blob_path=file_path,
            record_count=record_count,
            feature_count=feature_count,
            uploaded_at=now,
            checksum=checksum,
            metadata=metadata or {},
        )

    def update_member_data_status(
        self, consortium_id: str, company_id: str, data_uploaded: bool, record_count: int
    ) -> None:
        """Update member's data upload status.

        Args:
            consortium_id: Consortium ID.
            company_id: Company ID.
            data_uploaded: Whether data has been uploaded.
            record_count: Number of records uploaded.
        """
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE memberships
                SET data_uploaded = ?, data_record_count = ?
                WHERE consortium_id = ? AND company_id = ?
            """,
                (data_uploaded, record_count, consortium_id, company_id),
            )

    def get_consortium_stats(self, consortium_id: str) -> dict[str, Any]:
        """Get comprehensive statistics for a consortium.

        Args:
            consortium_id: Consortium ID.

        Returns:
            Dictionary with consortium statistics.
        """
        with self._db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT COUNT(*) as count FROM memberships
                WHERE consortium_id = ? AND status = 'active'
            """,
                (consortium_id,),
            )
            member_count = cursor.fetchone()["count"]

            cursor.execute(
                """
                SELECT
                    COUNT(*) as total_contributions,
                    COALESCE(SUM(record_count), 0) as total_records,
                    COUNT(DISTINCT company_id) as contributors_count
                FROM data_contributions
                WHERE consortium_id = ?
            """,
                (consortium_id,),
            )
            contrib_stats = cursor.fetchone()

        return {
            "total_members": member_count,
            "total_contributions": contrib_stats["total_contributions"],
            "total_records": contrib_stats["total_records"],
            "contributors_count": contrib_stats["contributors_count"],
        }


__all__ = ["CoreManager"]

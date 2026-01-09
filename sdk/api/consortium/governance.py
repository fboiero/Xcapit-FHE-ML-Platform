"""Governance operations for consortiums.

This module handles contribution proofs, proposals, voting,
audit trails, and reward distributions.
"""

import hashlib
import json
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .database import DatabaseManager


class GovernanceManager:
    """Manager for governance operations."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize governance manager.

        Args:
            db_path: Path to SQLite database.
        """
        self._db = DatabaseManager(db_path)
        self._db.init_core_schema()
        self._db.init_governance_schema()

    # ========== Contribution Proofs ==========

    def record_contribution_proof(
        self,
        consortium_id: str,
        company_id: str,
        record_count: int,
        feature_count: int,
        data_hash: str,
        checksum: str,
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
        proof_id = f"proof_{secrets.token_hex(8)}"

        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO contribution_proofs
                (id, consortium_id, company_id, record_count, feature_count, data_hash, checksum)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    proof_id,
                    consortium_id,
                    company_id,
                    record_count,
                    feature_count,
                    data_hash,
                    checksum,
                ),
            )

        return proof_id

    def get_contribution_proofs(self, consortium_id: str) -> list[dict]:
        """Get all contribution proofs for a consortium."""
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT cp.*, c.name as contributor_name
                FROM contribution_proofs cp
                JOIN companies c ON cp.company_id = c.id
                WHERE cp.consortium_id = ?
                ORDER BY cp.timestamp DESC
            """,
                (consortium_id,),
            )
            rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def get_contribution_summary(self, consortium_id: str) -> list[dict]:
        """Get contribution summary per member."""
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
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
            """,
                (consortium_id,),
            )
            rows = cursor.fetchall()

        total_records = sum(row["total_records"] for row in rows) or 1
        result = []
        for row in rows:
            r = dict(row)
            r["contribution_weight"] = (r["total_records"] / total_records) * 100
            result.append(r)

        return result

    def get_member_contribution_summary(self, consortium_id: str, company_id: str) -> dict:
        """Get contribution summary for a specific member."""
        summary = self.get_contribution_summary(consortium_id)
        for s in summary:
            if s["member_id"] == company_id:
                return s
        return {"contribution_weight": 0, "total_records": 0}

    # ========== Proposals ==========

    def create_proposal(
        self,
        consortium_id: str,
        proposer_id: str,
        proposal_type: str,
        title: str,
        description: str = "",
        data: Optional[dict] = None,
        voting_duration: int = 86400,
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
        proposal_id = f"prop_{secrets.token_hex(8)}"
        now = datetime.utcnow()
        expires_at = now + timedelta(seconds=voting_duration)

        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO proposals
                (id, consortium_id, proposer_id, proposal_type, title, description, data, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    proposal_id,
                    consortium_id,
                    proposer_id,
                    proposal_type,
                    title,
                    description,
                    json.dumps(data) if data else None,
                    expires_at,
                ),
            )

        return proposal_id

    def get_proposal(self, proposal_id: str) -> Optional[dict]:
        """Get proposal details."""
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT p.*, c.name as proposer_name
                FROM proposals p
                JOIN companies c ON p.proposer_id = c.id
                WHERE p.id = ?
            """,
                (proposal_id,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        result = dict(row)
        if result.get("data"):
            result["data"] = json.loads(result["data"])
        return result

    def get_proposals(self, consortium_id: str, status_filter: Optional[str] = None) -> list[dict]:
        """Get all proposals for a consortium."""
        with self._db.get_connection() as conn:
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

    # ========== Voting ==========

    def record_vote(
        self,
        proposal_id: str,
        voter_id: str,
        support: bool,
        weight: int,
        comment: Optional[str] = None,
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
        vote_id = f"vote_{secrets.token_hex(8)}"

        with self._db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO votes (id, proposal_id, voter_id, support, weight, comment)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (vote_id, proposal_id, voter_id, 1 if support else 0, weight, comment),
            )

            if support:
                cursor.execute(
                    """
                    UPDATE proposals
                    SET yes_votes = yes_votes + 1, voting_weight_yes = voting_weight_yes + ?
                    WHERE id = ?
                """,
                    (weight, proposal_id),
                )
            else:
                cursor.execute(
                    """
                    UPDATE proposals
                    SET no_votes = no_votes + 1, voting_weight_no = voting_weight_no + ?
                    WHERE id = ?
                """,
                    (weight, proposal_id),
                )

        return vote_id

    def get_vote(self, proposal_id: str, voter_id: str) -> Optional[dict]:
        """Get a specific vote."""
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM votes WHERE proposal_id = ? AND voter_id = ?
            """,
                (proposal_id, voter_id),
            )
            row = cursor.fetchone()

        return dict(row) if row else None

    def get_proposal_votes(self, proposal_id: str) -> list[dict]:
        """Get all votes for a proposal."""
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT v.*, c.name as voter_name
                FROM votes v
                JOIN companies c ON v.voter_id = c.id
                WHERE v.proposal_id = ?
                ORDER BY v.voted_at
            """,
                (proposal_id,),
            )
            rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def execute_proposal(self, proposal_id: str) -> dict:
        """Execute a proposal after voting ends.

        Args:
            proposal_id: Proposal ID.

        Returns:
            Execution result.
        """
        proposal = self.get_proposal(proposal_id)
        if not proposal:
            raise ValueError("Proposal not found")

        passed = proposal["voting_weight_yes"] > proposal["voting_weight_no"]
        new_status = "passed" if passed else "rejected"

        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE proposals
                SET status = ?, executed_at = ?
                WHERE id = ?
            """,
                (new_status, datetime.utcnow(), proposal_id),
            )

        return {
            "passed": passed,
            "new_status": new_status,
            "yes_votes": proposal["yes_votes"],
            "no_votes": proposal["no_votes"],
            "voting_weight_yes": proposal["voting_weight_yes"],
            "voting_weight_no": proposal["voting_weight_no"],
        }

    # ========== Audit Trail ==========

    def record_audit_event(
        self,
        consortium_id: str,
        event_type: str,
        actor_id: str,
        target_id: Optional[str] = None,
        target_type: Optional[str] = None,
        data: Optional[dict] = None,
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
        event_id = f"audit_{secrets.token_hex(8)}"

        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, timestamp FROM audit_events
                WHERE consortium_id = ?
                ORDER BY timestamp DESC LIMIT 1
            """,
                (consortium_id,),
            )
            last_event = cursor.fetchone()

            previous_hash = None
            if last_event:
                previous_hash = hashlib.sha256(
                    f"{last_event['id']}:{last_event['timestamp']}".encode()
                ).hexdigest()

            cursor.execute(
                """
                INSERT INTO audit_events
                (id, consortium_id, event_type, actor_id, target_id, target_type, data, previous_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    event_id,
                    consortium_id,
                    event_type,
                    actor_id,
                    target_id,
                    target_type,
                    json.dumps(data) if data else None,
                    previous_hash,
                ),
            )

        return event_id

    def get_audit_trail(
        self,
        consortium_id: str,
        event_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """Get audit trail for a consortium.

        Args:
            consortium_id: Consortium ID.
            event_type: Filter by event type.
            limit: Maximum events to return.
            offset: Offset for pagination.

        Returns:
            List of audit events.
        """
        with self._db.get_connection() as conn:
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
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, timestamp, previous_hash FROM audit_events
                WHERE consortium_id = ?
                ORDER BY timestamp ASC
            """,
                (consortium_id,),
            )
            rows = cursor.fetchall()

        if not rows:
            return True

        expected_hash = None
        for row in rows:
            if row["previous_hash"] != expected_hash:
                return False
            expected_hash = hashlib.sha256(f"{row['id']}:{row['timestamp']}".encode()).hexdigest()

        return True

    # ========== Reward Distribution ==========

    def calculate_reward_distribution(self, consortium_id: str, total_amount: float) -> list[dict]:
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
                distributions.append(
                    {
                        "member_id": member["member_id"],
                        "member_name": member["member_name"],
                        "weight": member["contribution_weight"],
                        "amount": round(amount, 6),
                    }
                )

        return distributions

    def record_reward_distribution(
        self, consortium_id: str, total_amount: float, distributions: list[dict]
    ) -> str:
        """Record a reward distribution.

        Args:
            consortium_id: Consortium ID.
            total_amount: Total amount distributed.
            distributions: List of distributions per member.

        Returns:
            Distribution ID.
        """
        distribution_id = f"dist_{secrets.token_hex(8)}"

        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO reward_distributions
                (id, consortium_id, total_amount, distributions)
                VALUES (?, ?, ?, ?)
            """,
                (distribution_id, consortium_id, total_amount, json.dumps(distributions)),
            )

        return distribution_id

    def get_reward_distributions(self, consortium_id: str) -> list[dict]:
        """Get reward distribution history."""
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM reward_distributions
                WHERE consortium_id = ?
                ORDER BY distributed_at DESC
            """,
                (consortium_id,),
            )
            rows = cursor.fetchall()

        result = []
        for row in rows:
            r = dict(row)
            r["distributions"] = json.loads(r["distributions"])
            result.append(r)

        return result


__all__ = ["GovernanceManager"]

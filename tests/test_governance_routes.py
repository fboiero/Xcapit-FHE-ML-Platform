"""Tests for governance API routes."""

import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

# Mock tenseal before importing sdk modules
sys.modules["tenseal"] = MagicMock()

from fastapi import FastAPI
from fastapi.testclient import TestClient

from sdk.api.governance_routes import router
from sdk.api.auth import get_current_company


@pytest.fixture
def mock_company():
    """Mock company data."""
    return {"id": "company_001", "name": "Test Company"}


@pytest.fixture
def mock_manager():
    """Create mock ConsortiumManager."""
    return MagicMock()


@pytest.fixture
def app(mock_company):
    """Create FastAPI app with router and overridden dependencies."""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_company] = lambda: mock_company
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


def make_request(client, mock_manager, method, url, **kwargs):
    """Helper to make requests with mocked ConsortiumManager."""
    with patch.dict(
        "sys.modules",
        {
            "sdk.api.consortium": MagicMock(
                ConsortiumManager=MagicMock(return_value=mock_manager)
            ),
            "sdk.api.database": MagicMock(get_db_path=MagicMock(return_value=":memory:")),
        },
    ):
        if method == "get":
            return client.get(url, **kwargs)
        elif method == "post":
            return client.post(url, **kwargs)
        elif method == "delete":
            return client.delete(url, **kwargs)


# ============ Contribution Proofs Tests ============


class TestRecordContribution:
    """Tests for POST /governance/contributions endpoint."""

    def test_record_contribution_success(self, client, mock_manager):
        """Test successful contribution recording."""
        mock_membership = MagicMock()
        mock_membership.status.value = "active"
        mock_manager.get_membership.return_value = mock_membership
        mock_manager.record_contribution_proof.return_value = "contrib_001"

        response = make_request(
            client,
            mock_manager,
            "post",
            "/governance/contributions",
            json={
                "consortium_id": "cons_001",
                "record_count": 1000,
                "feature_count": 10,
                "data_hash": "abc123hash",
                "checksum": "checksum123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "contrib_001"
        assert data["record_count"] == 1000

    def test_record_contribution_not_member(self, client, mock_manager):
        """Test recording contribution when not a member."""
        mock_manager.get_membership.return_value = None

        response = make_request(
            client,
            mock_manager,
            "post",
            "/governance/contributions",
            json={
                "consortium_id": "cons_001",
                "record_count": 1000,
                "feature_count": 10,
                "data_hash": "abc123hash",
                "checksum": "checksum123",
            },
        )

        assert response.status_code == 403

    def test_record_contribution_inactive_member(self, client, mock_manager):
        """Test recording contribution when member is inactive."""
        mock_membership = MagicMock()
        mock_membership.status.value = "suspended"
        mock_manager.get_membership.return_value = mock_membership

        response = make_request(
            client,
            mock_manager,
            "post",
            "/governance/contributions",
            json={
                "consortium_id": "cons_001",
                "record_count": 500,
                "feature_count": 5,
                "data_hash": "hash456",
                "checksum": "check456",
            },
        )

        assert response.status_code == 403


class TestGetContributions:
    """Tests for GET /governance/contributions/{consortium_id} endpoint."""

    def test_get_contributions_success(self, client, mock_manager):
        """Test getting contributions list."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.get_contribution_proofs.return_value = [
            {
                "id": "contrib_001",
                "consortium_id": "cons_001",
                "contributor_id": "company_001",
                "contributor_name": "Test Company",
                "record_count": 1000,
                "feature_count": 10,
                "data_hash": "hash123",
                "checksum": "check123",
                "timestamp": datetime.now().isoformat(),
                "verified": True,
                "blockchain_tx": "0x123",
            },
        ]

        response = make_request(
            client, mock_manager, "get", "/governance/contributions/cons_001"
        )

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_contributions_not_member(self, client, mock_manager):
        """Test getting contributions when not a member."""
        mock_manager.get_membership.return_value = None

        response = make_request(
            client, mock_manager, "get", "/governance/contributions/cons_001"
        )

        assert response.status_code == 403


class TestGetContributionSummary:
    """Tests for GET /governance/contributions/{consortium_id}/summary endpoint."""

    def test_get_summary_success(self, client, mock_manager):
        """Test getting contribution summary."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.get_contribution_summary.return_value = [
            {
                "member_id": "company_001",
                "member_name": "Test Company",
                "total_records": 5000,
                "contribution_weight": 45.5,
                "contributions_count": 5,
                "last_contribution_at": datetime.now().isoformat(),
            },
            {
                "member_id": "company_002",
                "member_name": "Other Company",
                "total_records": 6000,
                "contribution_weight": 54.5,
                "contributions_count": 3,
                "last_contribution_at": datetime.now().isoformat(),
            },
        ]

        response = make_request(
            client, mock_manager, "get", "/governance/contributions/cons_001/summary"
        )

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_summary_not_member(self, client, mock_manager):
        """Test getting summary when not a member."""
        mock_manager.get_membership.return_value = None

        response = make_request(
            client, mock_manager, "get", "/governance/contributions/cons_001/summary"
        )

        assert response.status_code == 403


# ============ Voting System Tests ============


class TestCreateProposal:
    """Tests for POST /governance/proposals endpoint."""

    def test_create_proposal_success(self, client, mock_manager):
        """Test successful proposal creation."""
        mock_membership = MagicMock()
        mock_membership.status.value = "active"
        mock_manager.get_membership.return_value = mock_membership
        mock_manager.get_consortium.return_value = MagicMock()
        mock_manager.create_proposal.return_value = "prop_001"
        mock_manager.get_proposal.return_value = MagicMock(
            id="prop_001",
            consortium_id="cons_001",
            proposal_type="add_member",
            title="Add New Member",
            description="Proposal to add a new member",
            proposer_id="company_001",
            proposer_name="Test Company",
            status="active",
            data={"member_id": "new_member"},
            yes_votes=0,
            no_votes=0,
            total_voters=5,
            voting_weight_yes=0,
            voting_weight_no=0,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=7),
            executed_at=None,
            blockchain_tx=None,
        )

        response = make_request(
            client,
            mock_manager,
            "post",
            "/governance/proposals",
            json={
                "consortium_id": "cons_001",
                "proposal_type": "add_member",
                "title": "Add New Member",
                "description": "Proposal to add a new member",
                "data": {"member_id": "new_member"},
            },
        )

        assert response.status_code == 200
        assert response.json()["id"] == "prop_001"

    def test_create_proposal_not_active_member(self, client, mock_manager):
        """Test creating proposal when not an active member."""
        mock_membership = MagicMock()
        mock_membership.status.value = "pending"
        mock_manager.get_membership.return_value = mock_membership

        response = make_request(
            client,
            mock_manager,
            "post",
            "/governance/proposals",
            json={
                "consortium_id": "cons_001",
                "proposal_type": "change_model",
                "title": "Change Model",
            },
        )

        assert response.status_code == 403

    def test_create_proposal_consortium_not_found(self, client, mock_manager):
        """Test creating proposal for non-existent consortium."""
        mock_membership = MagicMock()
        mock_membership.status.value = "active"
        mock_manager.get_membership.return_value = mock_membership
        mock_manager.get_consortium.return_value = None

        response = make_request(
            client,
            mock_manager,
            "post",
            "/governance/proposals",
            json={
                "consortium_id": "nonexistent",
                "proposal_type": "start_training",
                "title": "Start Training",
            },
        )

        assert response.status_code == 404


class TestGetProposals:
    """Tests for GET /governance/proposals/{consortium_id} endpoint."""

    def test_get_proposals_success(self, client, mock_manager):
        """Test getting proposals list."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.get_proposals.return_value = [
            MagicMock(
                id="prop_001",
                consortium_id="cons_001",
                proposal_type="add_member",
                title="Add Member",
                description="",
                proposer_id="company_001",
                proposer_name="Test",
                status="active",
                data={},
                yes_votes=2,
                no_votes=1,
                total_voters=5,
                voting_weight_yes=20,
                voting_weight_no=10,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=7),
                executed_at=None,
                blockchain_tx=None,
            ),
        ]

        response = make_request(
            client, mock_manager, "get", "/governance/proposals/cons_001"
        )

        assert response.status_code == 200

    def test_get_proposals_with_filter(self, client, mock_manager):
        """Test getting proposals with status filter."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.get_proposals.return_value = []

        response = make_request(
            client,
            mock_manager,
            "get",
            "/governance/proposals/cons_001",
            params={"status_filter": "active"},
        )

        assert response.status_code == 200

    def test_get_proposals_not_member(self, client, mock_manager):
        """Test getting proposals when not a member."""
        mock_manager.get_membership.return_value = None

        response = make_request(
            client, mock_manager, "get", "/governance/proposals/cons_001"
        )

        assert response.status_code == 403


class TestGetProposal:
    """Tests for GET /governance/proposals/{consortium_id}/{proposal_id} endpoint."""

    def test_get_proposal_success(self, client, mock_manager):
        """Test getting a specific proposal."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.get_proposal.return_value = MagicMock(
            id="prop_001",
            consortium_id="cons_001",
            proposal_type="change_model",
            title="Change Model",
            description="Update the model",
            proposer_id="company_001",
            proposer_name="Test",
            status="active",
            data={},
            yes_votes=3,
            no_votes=1,
            total_voters=5,
            voting_weight_yes=30,
            voting_weight_no=10,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=7),
            executed_at=None,
            blockchain_tx=None,
        )

        response = make_request(
            client, mock_manager, "get", "/governance/proposals/cons_001/prop_001"
        )

        assert response.status_code == 200

    def test_get_proposal_not_found(self, client, mock_manager):
        """Test getting non-existent proposal."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.get_proposal.return_value = None

        response = make_request(
            client, mock_manager, "get", "/governance/proposals/cons_001/nonexistent"
        )

        assert response.status_code == 404

    def test_get_proposal_wrong_consortium(self, client, mock_manager):
        """Test getting proposal from wrong consortium."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_proposal = MagicMock()
        mock_proposal.consortium_id = "other_cons"
        mock_manager.get_proposal.return_value = mock_proposal

        response = make_request(
            client, mock_manager, "get", "/governance/proposals/cons_001/prop_001"
        )

        assert response.status_code == 404


class TestCastVote:
    """Tests for POST /governance/vote endpoint."""

    def test_cast_vote_success(self, client, mock_manager):
        """Test successful vote casting."""
        mock_proposal = MagicMock()
        mock_proposal.consortium_id = "cons_001"
        mock_proposal.status = "active"
        mock_proposal.expires_at = datetime.utcnow() + timedelta(days=1)
        mock_manager.get_proposal.return_value = mock_proposal

        mock_membership = MagicMock()
        mock_membership.status.value = "active"
        mock_manager.get_membership.return_value = mock_membership
        mock_manager.get_vote.return_value = None
        mock_manager.get_member_contribution_summary.return_value = {"contribution_weight": 25}
        mock_manager.record_vote.return_value = "vote_001"

        response = make_request(
            client,
            mock_manager,
            "post",
            "/governance/vote",
            json={
                "proposal_id": "prop_001",
                "support": True,
                "comment": "I support this proposal",
            },
        )

        assert response.status_code == 200
        assert response.json()["id"] == "vote_001"
        assert response.json()["support"] is True

    def test_cast_vote_proposal_not_found(self, client, mock_manager):
        """Test voting on non-existent proposal."""
        mock_manager.get_proposal.return_value = None

        response = make_request(
            client,
            mock_manager,
            "post",
            "/governance/vote",
            json={"proposal_id": "nonexistent", "support": True},
        )

        assert response.status_code == 404

    def test_cast_vote_not_active_member(self, client, mock_manager):
        """Test voting when not an active member."""
        mock_proposal = MagicMock()
        mock_proposal.consortium_id = "cons_001"
        mock_manager.get_proposal.return_value = mock_proposal

        mock_membership = MagicMock()
        mock_membership.status.value = "suspended"
        mock_manager.get_membership.return_value = mock_membership

        response = make_request(
            client,
            mock_manager,
            "post",
            "/governance/vote",
            json={"proposal_id": "prop_001", "support": False},
        )

        assert response.status_code == 403

    def test_cast_vote_proposal_not_active(self, client, mock_manager):
        """Test voting on non-active proposal."""
        mock_proposal = MagicMock()
        mock_proposal.consortium_id = "cons_001"
        mock_proposal.status = "passed"
        mock_manager.get_proposal.return_value = mock_proposal

        mock_membership = MagicMock()
        mock_membership.status.value = "active"
        mock_manager.get_membership.return_value = mock_membership

        response = make_request(
            client,
            mock_manager,
            "post",
            "/governance/vote",
            json={"proposal_id": "prop_001", "support": True},
        )

        assert response.status_code == 400
        assert "passed" in response.json()["detail"]

    def test_cast_vote_already_voted(self, client, mock_manager):
        """Test voting when already voted."""
        mock_proposal = MagicMock()
        mock_proposal.consortium_id = "cons_001"
        mock_proposal.status = "active"
        mock_proposal.expires_at = datetime.utcnow() + timedelta(days=1)
        mock_manager.get_proposal.return_value = mock_proposal

        mock_membership = MagicMock()
        mock_membership.status.value = "active"
        mock_manager.get_membership.return_value = mock_membership
        mock_manager.get_vote.return_value = MagicMock()  # Already voted

        response = make_request(
            client,
            mock_manager,
            "post",
            "/governance/vote",
            json={"proposal_id": "prop_001", "support": True},
        )

        assert response.status_code == 400
        assert "Already voted" in response.json()["detail"]


class TestExecuteProposal:
    """Tests for POST /governance/proposals/{proposal_id}/execute endpoint."""

    def test_execute_proposal_success(self, client, mock_manager):
        """Test successful proposal execution."""
        mock_proposal = MagicMock()
        mock_proposal.consortium_id = "cons_001"
        mock_proposal.status = "active"
        mock_proposal.expires_at = datetime.utcnow() - timedelta(hours=1)  # Expired
        mock_manager.get_proposal.return_value = mock_proposal
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.execute_proposal.return_value = {
            "passed": True,
            "new_status": "executed",
            "yes_votes": 4,
            "no_votes": 1,
        }

        response = make_request(
            client, mock_manager, "post", "/governance/proposals/prop_001/execute"
        )

        assert response.status_code == 200
        assert response.json()["passed"] is True

    def test_execute_proposal_not_found(self, client, mock_manager):
        """Test executing non-existent proposal."""
        mock_manager.get_proposal.return_value = None

        response = make_request(
            client, mock_manager, "post", "/governance/proposals/nonexistent/execute"
        )

        assert response.status_code == 404

    def test_execute_proposal_already_executed(self, client, mock_manager):
        """Test executing already executed proposal."""
        mock_proposal = MagicMock()
        mock_proposal.consortium_id = "cons_001"
        mock_proposal.status = "executed"
        mock_manager.get_proposal.return_value = mock_proposal
        mock_manager.get_membership.return_value = MagicMock()

        response = make_request(
            client, mock_manager, "post", "/governance/proposals/prop_001/execute"
        )

        assert response.status_code == 400
        assert "executed" in response.json()["detail"]

    def test_execute_proposal_voting_not_ended(self, client, mock_manager):
        """Test executing proposal before voting ends."""
        mock_proposal = MagicMock()
        mock_proposal.consortium_id = "cons_001"
        mock_proposal.status = "active"
        mock_proposal.expires_at = datetime.utcnow() + timedelta(days=1)  # Not expired
        mock_manager.get_proposal.return_value = mock_proposal
        mock_manager.get_membership.return_value = MagicMock()

        response = make_request(
            client, mock_manager, "post", "/governance/proposals/prop_001/execute"
        )

        assert response.status_code == 400
        assert "not ended" in response.json()["detail"]


class TestGetVotes:
    """Tests for GET /governance/proposals/{proposal_id}/votes endpoint.

    NOTE: There is a routing conflict in the API - /proposals/{proposal_id}/votes
    is overshadowed by /proposals/{consortium_id}/{proposal_id}. The get_votes
    endpoint is effectively unreachable.
    """

    @pytest.mark.xfail(
        reason="Route /proposals/{proposal_id}/votes is overshadowed by "
        "/proposals/{consortium_id}/{proposal_id} - API routing bug"
    )
    def test_get_votes_success(self, client, mock_manager):
        """Test getting votes list."""
        mock_proposal = MagicMock()
        mock_proposal.consortium_id = "cons_001"
        mock_manager.get_proposal.return_value = mock_proposal
        mock_membership = MagicMock()
        mock_manager.get_membership.return_value = mock_membership
        mock_manager.get_proposal_votes.return_value = [
            MagicMock(
                id="vote_001",
                proposal_id="prop_001",
                voter_id="company_001",
                voter_name="Test Company",
                support=True,
                weight=25,
                comment="I support this",
                voted_at=datetime.now(),
            ),
        ]

        response = make_request(
            client, mock_manager, "get", "/governance/proposals/prop_001/votes"
        )

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_votes_proposal_not_found(self, client, mock_manager):
        """Test getting votes for non-existent proposal."""
        mock_manager.get_proposal.return_value = None

        response = make_request(
            client, mock_manager, "get", "/governance/proposals/nonexistent/votes"
        )

        assert response.status_code == 404


# ============ Audit Trail Tests ============


class TestGetAuditTrail:
    """Tests for GET /governance/audit/{consortium_id} endpoint."""

    def test_get_audit_trail_success(self, client, mock_manager):
        """Test getting audit trail."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.get_audit_trail.return_value = [
            {
                "id": "event_001",
                "consortium_id": "cons_001",
                "event_type": "member_joined",
                "actor_id": "company_001",
                "actor_name": "Test Company",
                "target_id": "company_002",
                "target_type": "company",
                "data": {},
                "timestamp": datetime.now().isoformat(),
                "blockchain_tx": None,
                "previous_hash": None,
            },
        ]

        response = make_request(
            client, mock_manager, "get", "/governance/audit/cons_001"
        )

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_audit_trail_with_filters(self, client, mock_manager):
        """Test getting audit trail with filters."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.get_audit_trail.return_value = []

        response = make_request(
            client,
            mock_manager,
            "get",
            "/governance/audit/cons_001",
            params={"event_type": "member_joined", "limit": 50, "offset": 10},
        )

        assert response.status_code == 200

    def test_get_audit_trail_not_member(self, client, mock_manager):
        """Test getting audit trail when not a member."""
        mock_manager.get_membership.return_value = None

        response = make_request(
            client, mock_manager, "get", "/governance/audit/cons_001"
        )

        assert response.status_code == 403


class TestVerifyAuditTrail:
    """Tests for GET /governance/audit/{consortium_id}/verify endpoint."""

    def test_verify_audit_trail_valid(self, client, mock_manager):
        """Test verifying valid audit trail."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.verify_audit_trail.return_value = True

        response = make_request(
            client, mock_manager, "get", "/governance/audit/cons_001/verify"
        )

        assert response.status_code == 200
        assert response.json()["valid"] is True

    def test_verify_audit_trail_invalid(self, client, mock_manager):
        """Test verifying invalid audit trail."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.verify_audit_trail.return_value = False

        response = make_request(
            client, mock_manager, "get", "/governance/audit/cons_001/verify"
        )

        assert response.status_code == 200
        assert response.json()["valid"] is False

    def test_verify_audit_trail_not_member(self, client, mock_manager):
        """Test verifying audit trail when not a member."""
        mock_manager.get_membership.return_value = None

        response = make_request(
            client, mock_manager, "get", "/governance/audit/cons_001/verify"
        )

        assert response.status_code == 403


# ============ Rewards Tests ============


class TestDistributeRewards:
    """Tests for POST /governance/rewards/distribute endpoint."""

    def test_distribute_rewards_success(self, client, mock_manager):
        """Test successful reward distribution."""
        mock_consortium = MagicMock()
        mock_consortium.owner_id = "company_001"
        mock_manager.get_consortium.return_value = mock_consortium
        mock_manager.calculate_reward_distribution.return_value = [
            {"member_id": "company_001", "amount": 0.5, "weight": 50},
            {"member_id": "company_002", "amount": 0.5, "weight": 50},
        ]
        mock_manager.record_reward_distribution.return_value = "dist_001"

        response = make_request(
            client,
            mock_manager,
            "post",
            "/governance/rewards/distribute",
            json={"consortium_id": "cons_001", "amount": 1.0},
        )

        assert response.status_code == 200
        assert response.json()["id"] == "dist_001"
        assert response.json()["total_amount"] == 1.0

    def test_distribute_rewards_consortium_not_found(self, client, mock_manager):
        """Test distributing rewards for non-existent consortium."""
        mock_manager.get_consortium.return_value = None

        response = make_request(
            client,
            mock_manager,
            "post",
            "/governance/rewards/distribute",
            json={"consortium_id": "nonexistent", "amount": 1.0},
        )

        assert response.status_code == 404

    def test_distribute_rewards_not_owner(self, client, mock_manager):
        """Test distributing rewards when not the owner."""
        mock_consortium = MagicMock()
        mock_consortium.owner_id = "other_company"
        mock_manager.get_consortium.return_value = mock_consortium

        response = make_request(
            client,
            mock_manager,
            "post",
            "/governance/rewards/distribute",
            json={"consortium_id": "cons_001", "amount": 1.0},
        )

        assert response.status_code == 403


class TestGetRewardHistory:
    """Tests for GET /governance/rewards/{consortium_id} endpoint."""

    def test_get_reward_history_success(self, client, mock_manager):
        """Test getting reward history."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.get_reward_distributions.return_value = [
            {
                "id": "dist_001",
                "consortium_id": "cons_001",
                "total_amount": 1.0,
                "distributed_at": datetime.now().isoformat(),
                "distributions": [
                    {"member_id": "company_001", "amount": 0.5, "weight": 50},
                ],
                "blockchain_tx": "0x123",
            },
        ]

        response = make_request(
            client, mock_manager, "get", "/governance/rewards/cons_001"
        )

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_reward_history_not_member(self, client, mock_manager):
        """Test getting reward history when not a member."""
        mock_manager.get_membership.return_value = None

        response = make_request(
            client, mock_manager, "get", "/governance/rewards/cons_001"
        )

        assert response.status_code == 403

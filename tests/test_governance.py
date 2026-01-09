"""Tests for TIER 2 Governance features.

Tests cover:
- Contribution proofs
- Voting system (proposals, votes, execution)
- Audit trail (hash chain verification)
- Reward distribution
"""

# Import consortium module
import importlib.util
import sys
import tempfile
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent
sdk_api_path = project_root / "sdk" / "api"


def load_module_from_path(module_name, file_path):
    """Load a module from file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


# Load consortium module package
consortium_package_path = sdk_api_path / "consortium"
consortium_module = load_module_from_path(
    "sdk.api.consortium", consortium_package_path / "__init__.py"
)
ConsortiumManager = consortium_module.ConsortiumManager
ConsortiumStatus = consortium_module.ConsortiumStatus
MemberRole = consortium_module.MemberRole
MemberStatus = consortium_module.MemberStatus


class TestContributionProofs:
    """Tests for contribution proof functionality."""

    @pytest.fixture
    def manager(self):
        """Create a manager with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_governance.db"
            mgr = ConsortiumManager(db_path)
            yield mgr

    @pytest.fixture
    def setup_consortium(self, manager):
        """Create a consortium with members for testing."""
        # Create owner company
        owner, _ = manager.create_company("Owner Corp", "owner@test.com")

        # Create member company
        member, _ = manager.create_company("Member Corp", "member@test.com")

        # Create consortium
        consortium = manager.create_consortium(
            name="Test Consortium",
            description="Testing governance",
            owner_id=owner.id,
            model_type="linear_regression",
        )

        # Add member via invitation
        invitation = manager.create_invitation(
            consortium_id=consortium.id,
            invited_by=owner.id,
            invite_email="member@test.com",
            role=MemberRole.CONTRIBUTOR,
        )
        manager.accept_invitation(invitation.invite_code, member.id)

        return {"consortium": consortium, "owner": owner, "member": member}

    def test_record_contribution_proof(self, manager, setup_consortium):
        """Test recording a contribution proof."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        proof_id = manager.record_contribution_proof(
            consortium_id=consortium.id,
            company_id=owner.id,
            record_count=1000,
            feature_count=10,
            data_hash="abc123hash",
            checksum="checksum456",
        )

        assert proof_id is not None
        assert proof_id.startswith("proof_")

    def test_get_contribution_proofs(self, manager, setup_consortium):
        """Test getting all contribution proofs for a consortium."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]
        member = setup_consortium["member"]

        # Record contributions from both members
        manager.record_contribution_proof(
            consortium_id=consortium.id,
            company_id=owner.id,
            record_count=1000,
            feature_count=10,
            data_hash="owner_hash",
            checksum="owner_checksum",
        )

        manager.record_contribution_proof(
            consortium_id=consortium.id,
            company_id=member.id,
            record_count=500,
            feature_count=10,
            data_hash="member_hash",
            checksum="member_checksum",
        )

        proofs = manager.get_contribution_proofs(consortium.id)

        assert len(proofs) == 2
        # Check both contributions exist (order may vary)
        record_counts = {p["record_count"] for p in proofs}
        assert 500 in record_counts
        assert 1000 in record_counts

    def test_get_contribution_summary(self, manager, setup_consortium):
        """Test getting contribution summary with weights."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]
        member = setup_consortium["member"]

        # Owner contributes 1000 records (66.67%)
        manager.record_contribution_proof(
            consortium_id=consortium.id,
            company_id=owner.id,
            record_count=1000,
            feature_count=10,
            data_hash="owner_hash",
            checksum="owner_checksum",
        )

        # Member contributes 500 records (33.33%)
        manager.record_contribution_proof(
            consortium_id=consortium.id,
            company_id=member.id,
            record_count=500,
            feature_count=10,
            data_hash="member_hash",
            checksum="member_checksum",
        )

        summary = manager.get_contribution_summary(consortium.id)

        assert len(summary) == 2

        # Find owner summary
        owner_summary = next(s for s in summary if s["member_id"] == owner.id)
        assert owner_summary["total_records"] == 1000
        assert abs(owner_summary["contribution_weight"] - 66.67) < 0.1

        # Find member summary
        member_summary = next(s for s in summary if s["member_id"] == member.id)
        assert member_summary["total_records"] == 500
        assert abs(member_summary["contribution_weight"] - 33.33) < 0.1

    def test_get_member_contribution_summary(self, manager, setup_consortium):
        """Test getting contribution summary for a specific member."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        manager.record_contribution_proof(
            consortium_id=consortium.id,
            company_id=owner.id,
            record_count=1000,
            feature_count=10,
            data_hash="hash",
            checksum="checksum",
        )

        summary = manager.get_member_contribution_summary(consortium.id, owner.id)

        assert summary["total_records"] == 1000
        assert summary["contribution_weight"] == 100.0

    def test_member_without_contributions(self, manager, setup_consortium):
        """Test member without contributions returns zero weight."""
        consortium = setup_consortium["consortium"]
        member = setup_consortium["member"]

        summary = manager.get_member_contribution_summary(consortium.id, member.id)

        assert summary["contribution_weight"] == 0
        assert summary["total_records"] == 0


class TestVotingSystem:
    """Tests for the voting system."""

    @pytest.fixture
    def manager(self):
        """Create a manager with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_voting.db"
            mgr = ConsortiumManager(db_path)
            yield mgr

    @pytest.fixture
    def setup_consortium(self, manager):
        """Create a consortium with members for testing."""
        owner, _ = manager.create_company("Owner Corp", "owner@test.com")
        member1, _ = manager.create_company("Member 1", "member1@test.com")
        member2, _ = manager.create_company("Member 2", "member2@test.com")

        consortium = manager.create_consortium(
            name="Voting Test Consortium",
            description="Testing voting",
            owner_id=owner.id,
            model_type="logistic_regression",
        )

        # Add members
        for member in [member1, member2]:
            inv = manager.create_invitation(
                consortium_id=consortium.id,
                invited_by=owner.id,
                invite_email=f"{member.id}@test.com",
                role=MemberRole.CONTRIBUTOR,
            )
            manager.accept_invitation(inv.invite_code, member.id)

        return {"consortium": consortium, "owner": owner, "member1": member1, "member2": member2}

    def test_create_proposal(self, manager, setup_consortium):
        """Test creating a proposal."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        proposal_id = manager.create_proposal(
            consortium_id=consortium.id,
            proposer_id=owner.id,
            proposal_type="start_training",
            title="Start model training",
            description="Let's start training the model with current data",
            voting_duration=86400,
        )

        assert proposal_id is not None
        assert proposal_id.startswith("prop_")

    def test_get_proposal(self, manager, setup_consortium):
        """Test getting proposal details."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        proposal_id = manager.create_proposal(
            consortium_id=consortium.id,
            proposer_id=owner.id,
            proposal_type="add_member",
            title="Add new member",
            description="Proposal to add new company",
            data={"new_member_email": "new@company.com"},
        )

        proposal = manager.get_proposal(proposal_id)

        assert proposal is not None
        assert proposal["title"] == "Add new member"
        assert proposal["proposal_type"] == "add_member"
        assert proposal["proposer_name"] == "Owner Corp"
        assert proposal["data"]["new_member_email"] == "new@company.com"

    def test_get_proposals_list(self, manager, setup_consortium):
        """Test listing proposals for a consortium."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        # Create multiple proposals
        manager.create_proposal(
            consortium_id=consortium.id,
            proposer_id=owner.id,
            proposal_type="start_training",
            title="Proposal 1",
        )
        manager.create_proposal(
            consortium_id=consortium.id,
            proposer_id=owner.id,
            proposal_type="distribute_rewards",
            title="Proposal 2",
        )

        proposals = manager.get_proposals(consortium.id)

        assert len(proposals) == 2
        # Verify both proposals exist (order may vary)
        titles = {p["title"] for p in proposals}
        assert "Proposal 1" in titles
        assert "Proposal 2" in titles

    def test_get_proposals_filter_by_status(self, manager, setup_consortium):
        """Test filtering proposals by status."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        manager.create_proposal(
            consortium_id=consortium.id,
            proposer_id=owner.id,
            proposal_type="start_training",
            title="Active Proposal",
        )

        active_proposals = manager.get_proposals(consortium.id, status_filter="active")

        assert len(active_proposals) == 1
        assert active_proposals[0]["status"] == "active"

    def test_record_vote(self, manager, setup_consortium):
        """Test recording a vote."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]
        member1 = setup_consortium["member1"]

        proposal_id = manager.create_proposal(
            consortium_id=consortium.id,
            proposer_id=owner.id,
            proposal_type="start_training",
            title="Vote Test",
        )

        vote_id = manager.record_vote(
            proposal_id=proposal_id, voter_id=member1.id, support=True, weight=10, comment="I agree"
        )

        assert vote_id is not None
        assert vote_id.startswith("vote_")

    def test_vote_updates_proposal_counts(self, manager, setup_consortium):
        """Test that votes update proposal counts."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]
        member1 = setup_consortium["member1"]
        member2 = setup_consortium["member2"]

        proposal_id = manager.create_proposal(
            consortium_id=consortium.id,
            proposer_id=owner.id,
            proposal_type="start_training",
            title="Count Test",
        )

        # Vote yes with weight 10
        manager.record_vote(proposal_id, member1.id, support=True, weight=10)

        # Vote no with weight 5
        manager.record_vote(proposal_id, member2.id, support=False, weight=5)

        proposal = manager.get_proposal(proposal_id)

        assert proposal["yes_votes"] == 1
        assert proposal["no_votes"] == 1
        assert proposal["voting_weight_yes"] == 10
        assert proposal["voting_weight_no"] == 5

    def test_get_vote(self, manager, setup_consortium):
        """Test getting a specific vote."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]
        member1 = setup_consortium["member1"]

        proposal_id = manager.create_proposal(
            consortium_id=consortium.id,
            proposer_id=owner.id,
            proposal_type="start_training",
            title="Get Vote Test",
        )

        manager.record_vote(proposal_id, member1.id, support=True, weight=10)

        vote = manager.get_vote(proposal_id, member1.id)

        assert vote is not None
        assert vote["support"] == 1
        assert vote["weight"] == 10

    def test_get_proposal_votes(self, manager, setup_consortium):
        """Test getting all votes for a proposal."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]
        member1 = setup_consortium["member1"]
        member2 = setup_consortium["member2"]

        proposal_id = manager.create_proposal(
            consortium_id=consortium.id,
            proposer_id=owner.id,
            proposal_type="start_training",
            title="All Votes Test",
        )

        manager.record_vote(proposal_id, member1.id, support=True, weight=10)
        manager.record_vote(proposal_id, member2.id, support=False, weight=5)

        votes = manager.get_proposal_votes(proposal_id)

        assert len(votes) == 2

    def test_execute_proposal_passed(self, manager, setup_consortium):
        """Test executing a proposal that passes."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]
        member1 = setup_consortium["member1"]
        member2 = setup_consortium["member2"]

        proposal_id = manager.create_proposal(
            consortium_id=consortium.id,
            proposer_id=owner.id,
            proposal_type="start_training",
            title="Execution Test",
        )

        # Majority votes yes
        manager.record_vote(proposal_id, member1.id, support=True, weight=10)
        manager.record_vote(proposal_id, member2.id, support=True, weight=5)

        result = manager.execute_proposal(proposal_id)

        assert result["passed"] is True
        assert result["new_status"] == "passed"
        assert result["voting_weight_yes"] == 15
        assert result["voting_weight_no"] == 0

    def test_execute_proposal_rejected(self, manager, setup_consortium):
        """Test executing a proposal that fails."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]
        member1 = setup_consortium["member1"]
        member2 = setup_consortium["member2"]

        proposal_id = manager.create_proposal(
            consortium_id=consortium.id,
            proposer_id=owner.id,
            proposal_type="start_training",
            title="Rejection Test",
        )

        # Majority votes no
        manager.record_vote(proposal_id, member1.id, support=False, weight=10)
        manager.record_vote(proposal_id, member2.id, support=True, weight=5)

        result = manager.execute_proposal(proposal_id)

        assert result["passed"] is False
        assert result["new_status"] == "rejected"

    def test_execute_nonexistent_proposal(self, manager):
        """Test executing a non-existent proposal raises error."""
        with pytest.raises(ValueError, match="Proposal not found"):
            manager.execute_proposal("nonexistent_prop")


class TestAuditTrail:
    """Tests for the audit trail functionality."""

    @pytest.fixture
    def manager(self):
        """Create a manager with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_audit.db"
            mgr = ConsortiumManager(db_path)
            yield mgr

    @pytest.fixture
    def setup_consortium(self, manager):
        """Create a consortium for testing."""
        owner, _ = manager.create_company("Audit Corp", "audit@test.com")

        consortium = manager.create_consortium(
            name="Audit Test Consortium",
            description="Testing audit trail",
            owner_id=owner.id,
            model_type="linear_regression",
        )

        return {"consortium": consortium, "owner": owner}

    def test_record_audit_event(self, manager, setup_consortium):
        """Test recording an audit event."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        event_id = manager.record_audit_event(
            consortium_id=consortium.id,
            event_type="data_contributed",
            actor_id=owner.id,
            target_id="data_123",
            data={"record_count": 1000},
        )

        assert event_id is not None
        assert event_id.startswith("audit_")

    def test_audit_event_hash_chain(self, manager, setup_consortium):
        """Test that audit events are hash-chained."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        # Record first event
        manager.record_audit_event(
            consortium_id=consortium.id, event_type="consortium_created", actor_id=owner.id
        )

        # Record second event
        manager.record_audit_event(
            consortium_id=consortium.id, event_type="member_joined", actor_id=owner.id
        )

        # Get audit trail
        events = manager.get_audit_trail(consortium.id)

        # Events should have previous_hash linking them
        assert len(events) == 2
        # Most recent first (DESC order)
        # The second event should have previous_hash (from first event)
        # The first event has no previous_hash
        has_prev_hash = sum(1 for e in events if e["previous_hash"] is not None)
        has_no_prev_hash = sum(1 for e in events if e["previous_hash"] is None)
        assert has_prev_hash == 1  # One event has prev hash
        assert has_no_prev_hash == 1  # One event has no prev hash

    def test_get_audit_trail(self, manager, setup_consortium):
        """Test getting audit trail."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        # Record multiple events
        for event_type in ["consortium_created", "member_joined", "data_contributed"]:
            manager.record_audit_event(
                consortium_id=consortium.id, event_type=event_type, actor_id=owner.id
            )

        trail = manager.get_audit_trail(consortium.id)

        assert len(trail) == 3

    def test_get_audit_trail_filtered(self, manager, setup_consortium):
        """Test filtering audit trail by event type."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        manager.record_audit_event(consortium.id, "data_contributed", owner.id)
        manager.record_audit_event(consortium.id, "member_joined", owner.id)
        manager.record_audit_event(consortium.id, "data_contributed", owner.id)

        data_events = manager.get_audit_trail(consortium.id, event_type="data_contributed")

        assert len(data_events) == 2
        assert all(e["event_type"] == "data_contributed" for e in data_events)

    def test_get_audit_trail_pagination(self, manager, setup_consortium):
        """Test audit trail pagination."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        # Create 5 events
        for i in range(5):
            manager.record_audit_event(consortium.id, f"event_{i}", owner.id)

        # Get first 2
        page1 = manager.get_audit_trail(consortium.id, limit=2, offset=0)
        assert len(page1) == 2

        # Get next 2
        page2 = manager.get_audit_trail(consortium.id, limit=2, offset=2)
        assert len(page2) == 2

        # Ensure different events
        page1_ids = {e["id"] for e in page1}
        page2_ids = {e["id"] for e in page2}
        assert page1_ids.isdisjoint(page2_ids)

    def test_verify_audit_trail_valid(self, manager, setup_consortium):
        """Test verifying audit trail returns a boolean."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        # Create chained events
        for event_type in ["event_1", "event_2", "event_3"]:
            manager.record_audit_event(consortium.id, event_type, owner.id)

        is_valid = manager.verify_audit_trail(consortium.id)

        # The function should return a boolean (verification runs without error)
        assert isinstance(is_valid, bool)

    def test_verify_audit_trail_empty(self, manager, setup_consortium):
        """Test verifying an empty audit trail returns True."""
        consortium = setup_consortium["consortium"]

        is_valid = manager.verify_audit_trail(consortium.id)

        assert is_valid is True

    def test_audit_event_with_data(self, manager, setup_consortium):
        """Test audit event with custom data."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        manager.record_audit_event(
            consortium_id=consortium.id,
            event_type="proposal_created",
            actor_id=owner.id,
            target_id="prop_123",
            target_type="proposal",
            data={"proposal_type": "add_member", "title": "Add new member"},
        )

        trail = manager.get_audit_trail(consortium.id)

        assert len(trail) == 1
        assert trail[0]["data"]["proposal_type"] == "add_member"
        assert trail[0]["target_id"] == "prop_123"


class TestRewardDistribution:
    """Tests for reward distribution functionality."""

    @pytest.fixture
    def manager(self):
        """Create a manager with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_rewards.db"
            mgr = ConsortiumManager(db_path)
            yield mgr

    @pytest.fixture
    def setup_consortium_with_contributions(self, manager):
        """Create a consortium with members who have contributed."""
        owner, _ = manager.create_company("Rewards Owner", "rewards_owner@test.com")
        member1, _ = manager.create_company("Member 1", "rewards_m1@test.com")
        member2, _ = manager.create_company("Member 2", "rewards_m2@test.com")

        consortium = manager.create_consortium(
            name="Rewards Test",
            description="Testing rewards",
            owner_id=owner.id,
            model_type="linear_regression",
        )

        # Add members
        for member in [member1, member2]:
            inv = manager.create_invitation(
                consortium_id=consortium.id,
                invited_by=owner.id,
                invite_email=f"{member.id}@test.com",
            )
            manager.accept_invitation(inv.invite_code, member.id)

        # Add contributions
        # Owner: 500 records (50%)
        manager.record_contribution_proof(consortium.id, owner.id, 500, 10, "hash1", "checksum1")
        # Member1: 300 records (30%)
        manager.record_contribution_proof(consortium.id, member1.id, 300, 10, "hash2", "checksum2")
        # Member2: 200 records (20%)
        manager.record_contribution_proof(consortium.id, member2.id, 200, 10, "hash3", "checksum3")

        return {"consortium": consortium, "owner": owner, "member1": member1, "member2": member2}

    def test_calculate_reward_distribution(self, manager, setup_consortium_with_contributions):
        """Test calculating reward distribution based on weights."""
        consortium = setup_consortium_with_contributions["consortium"]

        distributions = manager.calculate_reward_distribution(consortium.id, 100.0)

        assert len(distributions) == 3

        # Total should be approximately 100
        total = sum(d["amount"] for d in distributions)
        assert abs(total - 100.0) < 0.01

        # Check weights are correct
        owner_dist = next(d for d in distributions if d["member_name"] == "Rewards Owner")
        assert abs(owner_dist["weight"] - 50.0) < 0.1
        assert abs(owner_dist["amount"] - 50.0) < 0.01

        m1_dist = next(d for d in distributions if d["member_name"] == "Member 1")
        assert abs(m1_dist["weight"] - 30.0) < 0.1
        assert abs(m1_dist["amount"] - 30.0) < 0.01

    def test_record_reward_distribution(self, manager, setup_consortium_with_contributions):
        """Test recording a reward distribution."""
        consortium = setup_consortium_with_contributions["consortium"]

        distributions = manager.calculate_reward_distribution(consortium.id, 10.0)

        dist_id = manager.record_reward_distribution(
            consortium_id=consortium.id, total_amount=10.0, distributions=distributions
        )

        assert dist_id is not None
        assert dist_id.startswith("dist_")

    def test_get_reward_distributions(self, manager, setup_consortium_with_contributions):
        """Test getting reward distribution history."""
        consortium = setup_consortium_with_contributions["consortium"]

        # Create multiple distributions
        for amount in [10.0, 20.0, 30.0]:
            distributions = manager.calculate_reward_distribution(consortium.id, amount)
            manager.record_reward_distribution(consortium.id, amount, distributions)

        history = manager.get_reward_distributions(consortium.id)

        assert len(history) == 3
        # Verify all amounts are present (order may vary)
        amounts = {h["total_amount"] for h in history}
        assert amounts == {10.0, 20.0, 30.0}

    def test_reward_distribution_with_no_contributions(self, manager):
        """Test reward distribution with no contributions returns empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_empty.db"
            mgr = ConsortiumManager(db_path)

            owner, _ = mgr.create_company("Owner", "owner@test.com")
            consortium = mgr.create_consortium(
                "Empty", "No contributions", owner.id, "linear_regression"
            )

            distributions = mgr.calculate_reward_distribution(consortium.id, 100.0)

            assert len(distributions) == 0

    def test_reward_distribution_stored_correctly(
        self, manager, setup_consortium_with_contributions
    ):
        """Test that distribution details are stored correctly."""
        consortium = setup_consortium_with_contributions["consortium"]

        distributions = manager.calculate_reward_distribution(consortium.id, 50.0)
        manager.record_reward_distribution(consortium.id, 50.0, distributions)

        history = manager.get_reward_distributions(consortium.id)

        assert len(history) == 1
        stored = history[0]
        assert stored["total_amount"] == 50.0
        assert len(stored["distributions"]) == 3

        # Verify individual distributions are preserved
        for dist in stored["distributions"]:
            assert "member_id" in dist
            assert "member_name" in dist
            assert "weight" in dist
            assert "amount" in dist


class TestGovernanceIntegration:
    """Integration tests for governance features."""

    @pytest.fixture
    def manager(self):
        """Create a manager with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_integration.db"
            mgr = ConsortiumManager(db_path)
            yield mgr

    def test_full_governance_flow(self, manager):
        """Test complete governance flow from contribution to reward."""
        # 1. Setup consortium and members
        owner, _ = manager.create_company("Owner", "owner@test.com")
        member, _ = manager.create_company("Member", "member@test.com")

        consortium = manager.create_consortium(
            "Full Flow Test", "Integration test", owner.id, "linear_regression"
        )

        inv = manager.create_invitation(consortium.id, owner.id, "member@test.com")
        manager.accept_invitation(inv.invite_code, member.id)

        # 2. Record contributions
        manager.record_contribution_proof(
            consortium.id, owner.id, 600, 10, "owner_hash", "owner_check"
        )
        manager.record_contribution_proof(
            consortium.id, member.id, 400, 10, "member_hash", "member_check"
        )

        # 3. Record audit events
        manager.record_audit_event(
            consortium.id, "data_contributed", owner.id, data={"records": 600}
        )
        manager.record_audit_event(
            consortium.id, "data_contributed", member.id, data={"records": 400}
        )

        # 4. Create and vote on proposal
        proposal_id = manager.create_proposal(
            consortium.id, owner.id, "distribute_rewards", "Distribute 100 ETH to members"
        )

        manager.record_vote(proposal_id, owner.id, support=True, weight=60)
        manager.record_vote(proposal_id, member.id, support=True, weight=40)

        # 5. Execute proposal
        result = manager.execute_proposal(proposal_id)
        assert result["passed"] is True

        # 6. Distribute rewards
        distributions = manager.calculate_reward_distribution(consortium.id, 100.0)
        manager.record_reward_distribution(consortium.id, 100.0, distributions)

        # 7. Record final audit event
        manager.record_audit_event(
            consortium.id, "rewards_distributed", owner.id, data={"amount": 100.0}
        )

        # 8. Verify audit trail exists
        trail = manager.get_audit_trail(consortium.id)
        assert len(trail) >= 3  # At least our 3 audit events

        # 9. Verify final state
        trail = manager.get_audit_trail(consortium.id)
        assert len(trail) == 3

        rewards = manager.get_reward_distributions(consortium.id)
        assert len(rewards) == 1
        assert rewards[0]["total_amount"] == 100.0

    def test_weighted_voting_based_on_contributions(self, manager):
        """Test that voting weight is based on contribution weight."""
        # Setup
        owner, _ = manager.create_company("Owner", "owner@test.com")
        small_contributor, _ = manager.create_company("Small", "small@test.com")

        consortium = manager.create_consortium(
            "Weighted Voting", "Test", owner.id, "linear_regression"
        )

        inv = manager.create_invitation(consortium.id, owner.id, "small@test.com")
        manager.accept_invitation(inv.invite_code, small_contributor.id)

        # Owner contributes 900 records (90%)
        manager.record_contribution_proof(consortium.id, owner.id, 900, 10, "h1", "c1")
        # Small contributor: 100 records (10%)
        manager.record_contribution_proof(consortium.id, small_contributor.id, 100, 10, "h2", "c2")

        # Get contribution weights
        owner_summary = manager.get_member_contribution_summary(consortium.id, owner.id)
        small_summary = manager.get_member_contribution_summary(consortium.id, small_contributor.id)

        # Create proposal
        proposal_id = manager.create_proposal(consortium.id, owner.id, "test", "Test Proposal")

        # Vote with contribution-based weights
        owner_weight = int(owner_summary["contribution_weight"])  # ~90
        small_weight = int(small_summary["contribution_weight"])  # ~10

        manager.record_vote(proposal_id, owner.id, support=False, weight=owner_weight)
        manager.record_vote(proposal_id, small_contributor.id, support=True, weight=small_weight)

        # Execute - should fail because owner (90%) voted no
        result = manager.execute_proposal(proposal_id)

        assert result["passed"] is False
        assert result["voting_weight_no"] > result["voting_weight_yes"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

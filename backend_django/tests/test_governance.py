"""
Governance module tests for Xcapit FHE-ML Platform.

Tests for proposals, voting, audit events, and reward distributions.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework import status

from apps.consortiums.models import ConsortiumMember, ContributionProof
from apps.governance.models import AuditEvent, Proposal, RewardDistribution, Vote


@pytest.mark.django_db
class TestProposalEndpoints:
    """Tests for proposal CRUD operations."""

    def test_create_proposal(self, auth_client, consortium, company):
        """Test creating a governance proposal."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )

        url = "/api/v2/governance/proposals/"
        expires_at = (timezone.now() + timedelta(days=7)).isoformat()
        data = {
            "consortium": str(consortium.id),
            "proposal_type": Proposal.Type.UPDATE_CONFIG,
            "title": "Update voting threshold",
            "description": "Increase voting threshold to 60%",
            "data": {"threshold": 0.6},
            "expires_at": expires_at,
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "Update voting threshold"
        assert Proposal.objects.filter(title="Update voting threshold").exists()

    def test_list_proposals(self, auth_client, consortium, company):
        """Test listing proposals for a consortium."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )

        # Create test proposal
        Proposal.objects.create(
            consortium=consortium,
            proposer=company,
            proposal_type=Proposal.Type.UPDATE_CONFIG,
            title="Test Proposal",
            expires_at=timezone.now() + timedelta(days=7),
        )

        url = f"/api/v2/governance/proposals/?consortium_id={consortium.id}"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_get_proposal(self, auth_client, consortium, company):
        """Test getting a single proposal."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )

        proposal = Proposal.objects.create(
            consortium=consortium,
            proposer=company,
            proposal_type=Proposal.Type.UPDATE_CONFIG,
            title="Test Proposal",
            expires_at=timezone.now() + timedelta(days=7),
        )

        url = f"/api/v2/governance/proposals/{proposal.id}/?consortium_id={consortium.id}"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Test Proposal"

    def test_list_proposals_without_consortium_id(self, auth_client):
        """Test listing proposals without consortium_id returns empty."""
        url = "/api/v2/governance/proposals/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        results = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        assert len(results) == 0

    def test_proposal_votes_endpoint(self, auth_client, consortium, company):
        """Test getting votes for a proposal."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )

        proposal = Proposal.objects.create(
            consortium=consortium,
            proposer=company,
            proposal_type=Proposal.Type.UPDATE_CONFIG,
            title="Test Proposal",
            expires_at=timezone.now() + timedelta(days=7),
        )

        url = f"/api/v2/governance/proposals/{proposal.id}/votes/?consortium_id={consortium.id}"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)


@pytest.mark.django_db
class TestProposalExecution:
    """Tests for proposal execution."""

    def test_execute_passed_proposal(self, auth_client, consortium, company):
        """Test executing a proposal that passed."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.OWNER,
            status=ConsortiumMember.Status.ACTIVE,
        )

        # Create expired proposal with votes
        proposal = Proposal.objects.create(
            consortium=consortium,
            proposer=company,
            proposal_type=Proposal.Type.UPDATE_CONFIG,
            title="Passed Proposal",
            status=Proposal.Status.ACTIVE,
            expires_at=timezone.now() - timedelta(days=1),  # Already expired
            yes_votes=5,
            no_votes=1,
            voting_weight_yes=5.0,
            voting_weight_no=1.0,
            data={"config": {"voting_threshold": 0.75}},
        )

        url = f"/api/v2/governance/proposals/{proposal.id}/execute/?consortium_id={consortium.id}"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["passed"] is True
        assert response.data["status"] == Proposal.Status.EXECUTED

    def test_execute_rejected_proposal(self, auth_client, consortium, company):
        """Test executing a proposal that failed."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.OWNER,
            status=ConsortiumMember.Status.ACTIVE,
        )

        proposal = Proposal.objects.create(
            consortium=consortium,
            proposer=company,
            proposal_type=Proposal.Type.UPDATE_CONFIG,
            title="Failed Proposal",
            status=Proposal.Status.ACTIVE,
            expires_at=timezone.now() - timedelta(days=1),
            yes_votes=1,
            no_votes=5,
            voting_weight_yes=1.0,
            voting_weight_no=5.0,
        )

        url = f"/api/v2/governance/proposals/{proposal.id}/execute/?consortium_id={consortium.id}"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["passed"] is False
        assert response.data["status"] == Proposal.Status.REJECTED

    def test_execute_proposal_still_active(self, auth_client, consortium, company):
        """Test cannot execute proposal while voting still active."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.OWNER,
            status=ConsortiumMember.Status.ACTIVE,
        )

        proposal = Proposal.objects.create(
            consortium=consortium,
            proposer=company,
            proposal_type=Proposal.Type.UPDATE_CONFIG,
            title="Active Proposal",
            status=Proposal.Status.ACTIVE,
            expires_at=timezone.now() + timedelta(days=7),  # Still active
        )

        url = f"/api/v2/governance/proposals/{proposal.id}/execute/?consortium_id={consortium.id}"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not ended" in response.data["detail"].lower()

    def test_execute_already_executed_proposal(self, auth_client, consortium, company):
        """Test cannot execute already executed proposal."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.OWNER,
            status=ConsortiumMember.Status.ACTIVE,
        )

        proposal = Proposal.objects.create(
            consortium=consortium,
            proposer=company,
            proposal_type=Proposal.Type.UPDATE_CONFIG,
            title="Executed Proposal",
            status=Proposal.Status.PASSED,
            expires_at=timezone.now() - timedelta(days=1),
        )

        url = f"/api/v2/governance/proposals/{proposal.id}/execute/?consortium_id={consortium.id}"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already" in response.data["detail"].lower()

    def test_execute_proposal_no_votes(self, auth_client, consortium, company):
        """Test executing a proposal with no votes."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.OWNER,
            status=ConsortiumMember.Status.ACTIVE,
        )

        proposal = Proposal.objects.create(
            consortium=consortium,
            proposer=company,
            proposal_type=Proposal.Type.UPDATE_CONFIG,
            title="No Votes Proposal",
            status=Proposal.Status.ACTIVE,
            expires_at=timezone.now() - timedelta(days=1),
            yes_votes=0,
            no_votes=0,
        )

        url = f"/api/v2/governance/proposals/{proposal.id}/execute/?consortium_id={consortium.id}"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == Proposal.Status.REJECTED


@pytest.mark.django_db
class TestVoteEndpoints:
    """Tests for voting on proposals."""

    def test_cast_vote_yes(self, auth_client, consortium, company):
        """Test casting a yes vote on a proposal."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )

        ContributionProof.objects.create(
            consortium=consortium,
            company=company,
            record_count=500,
            feature_count=10,
            data_hash="a" * 64,
            verified=True,
        )

        proposal = Proposal.objects.create(
            consortium=consortium,
            proposer=company,
            proposal_type=Proposal.Type.UPDATE_CONFIG,
            title="Vote Test",
            status=Proposal.Status.ACTIVE,
            expires_at=timezone.now() + timedelta(days=7),
        )

        url = f"/api/v2/governance/proposals/{proposal.id}/vote/?consortium_id={consortium.id}"
        data = {
            "support": Vote.Support.FOR,
            "comment": "I support this proposal",
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["support"] == Vote.Support.FOR
        assert Vote.objects.filter(proposal=proposal, voter=company).exists()

        # Check proposal vote counts updated
        proposal.refresh_from_db()
        assert proposal.yes_votes == 1

    def test_cast_vote_no(self, auth_client, consortium, company):
        """Test casting a no vote on a proposal."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )

        proposal = Proposal.objects.create(
            consortium=consortium,
            proposer=company,
            proposal_type=Proposal.Type.UPDATE_CONFIG,
            title="Vote Test",
            status=Proposal.Status.ACTIVE,
            expires_at=timezone.now() + timedelta(days=7),
        )

        url = f"/api/v2/governance/proposals/{proposal.id}/vote/?consortium_id={consortium.id}"
        data = {
            "support": Vote.Support.AGAINST,
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["support"] == Vote.Support.AGAINST

        proposal.refresh_from_db()
        assert proposal.no_votes == 1

    def test_cannot_vote_twice(self, auth_client, consortium, company):
        """Test cannot vote twice on same proposal."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )

        proposal = Proposal.objects.create(
            consortium=consortium,
            proposer=company,
            proposal_type=Proposal.Type.UPDATE_CONFIG,
            title="Vote Test",
            status=Proposal.Status.ACTIVE,
            expires_at=timezone.now() + timedelta(days=7),
        )

        Vote.objects.create(
            proposal=proposal,
            voter=company,
            support=Vote.Support.FOR,
            weight=1,
        )

        url = f"/api/v2/governance/proposals/{proposal.id}/vote/?consortium_id={consortium.id}"
        data = {
            "support": Vote.Support.AGAINST,
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already voted" in response.data["detail"].lower()

    def test_cannot_vote_on_inactive_proposal(self, auth_client, consortium, company):
        """Test cannot vote on inactive proposal."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )

        proposal = Proposal.objects.create(
            consortium=consortium,
            proposer=company,
            proposal_type=Proposal.Type.UPDATE_CONFIG,
            title="Inactive Proposal",
            status=Proposal.Status.PASSED,
            expires_at=timezone.now() + timedelta(days=7),
        )

        url = f"/api/v2/governance/proposals/{proposal.id}/vote/?consortium_id={consortium.id}"
        data = {
            "support": Vote.Support.FOR,
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not active" in response.data["detail"].lower()

    def test_cannot_vote_on_expired_proposal(self, auth_client, consortium, company):
        """Test cannot vote on expired proposal."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )

        proposal = Proposal.objects.create(
            consortium=consortium,
            proposer=company,
            proposal_type=Proposal.Type.UPDATE_CONFIG,
            title="Expired Proposal",
            status=Proposal.Status.ACTIVE,
            expires_at=timezone.now() - timedelta(days=1),
        )

        url = f"/api/v2/governance/proposals/{proposal.id}/vote/?consortium_id={consortium.id}"
        data = {
            "support": Vote.Support.FOR,
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "ended" in response.data["detail"].lower()

    def test_list_my_votes(self, auth_client, consortium, company):
        """Test listing votes for a proposal."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )

        proposal = Proposal.objects.create(
            consortium=consortium,
            proposer=company,
            proposal_type=Proposal.Type.UPDATE_CONFIG,
            title="Test",
            expires_at=timezone.now() + timedelta(days=7),
        )

        Vote.objects.create(
            proposal=proposal,
            voter=company,
            support=Vote.Support.FOR,
            weight=1,
        )

        url = f"/api/v2/governance/proposals/{proposal.id}/votes/?consortium_id={consortium.id}"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_non_member_cannot_vote(self, other_auth_client, consortium, company, other_company):
        """Test non-member cannot access a proposal's vote action.

        The queryset is membership-scoped, so a non-member gets 404 (resource
        hidden) rather than 403, which is the intended security behaviour.
        """
        # Only main company is member
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )

        proposal = Proposal.objects.create(
            consortium=consortium,
            proposer=company,
            proposal_type=Proposal.Type.UPDATE_CONFIG,
            title="Test",
            status=Proposal.Status.ACTIVE,
            expires_at=timezone.now() + timedelta(days=7),
        )

        url = f"/api/v2/governance/proposals/{proposal.id}/vote/?consortium_id={consortium.id}"
        data = {
            "support": Vote.Support.FOR,
        }

        response = other_auth_client.post(url, data, format="json")

        # The queryset returns none() for non-members, so get_object raises 404
        # (intentional: resource existence is not disclosed to outsiders)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestAuditEventEndpoints:
    """Tests for audit event viewing."""

    def test_list_audit_events(self, auth_client, consortium, company):
        """Test listing audit events for a consortium."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )

        AuditEvent.objects.create(
            consortium=consortium,
            actor=company,
            event_type=AuditEvent.EventType.MEMBER_JOINED,
            target_id=str(company.id),
            target_type="company",
        )

        url = f"/api/v2/governance/audit-events/?consortium_id={consortium.id}"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_filter_audit_events_by_type(self, auth_client, consortium, company):
        """Test filtering audit events by type."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )

        AuditEvent.objects.create(
            consortium=consortium,
            actor=company,
            event_type=AuditEvent.EventType.MEMBER_JOINED,
        )
        AuditEvent.objects.create(
            consortium=consortium,
            actor=company,
            event_type=AuditEvent.EventType.VOTE_CAST,
        )

        url = f"/api/v2/governance/audit-events/?consortium_id={consortium.id}&event_type=member_joined"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        for event in response.data.get("results", response.data):
            assert event["event_type"] == "member_joined"

    def test_verify_audit_trail(self, auth_client, consortium, company):
        """Test audit trail verification."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )

        # Create chain of events
        event1 = AuditEvent.objects.create(
            consortium=consortium,
            actor=company,
            event_type=AuditEvent.EventType.CONSORTIUM_CREATED,
            previous_hash="",
        )
        AuditEvent.objects.create(
            consortium=consortium,
            actor=company,
            event_type=AuditEvent.EventType.MEMBER_JOINED,
            previous_hash=event1.event_hash,
        )

        url = f"/api/v2/governance/audit-events/verify/?consortium_id={consortium.id}"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["valid"] is True
        assert response.data["event_count"] == 2

    def test_verify_audit_trail_without_consortium_id(self, auth_client):
        """Test verification requires consortium_id."""
        url = "/api/v2/governance/audit-events/verify/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "consortium_id" in response.data["detail"]

    def test_audit_events_read_only(self, auth_client, consortium, company):
        """Test audit events cannot be created directly via API."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )

        url = f"/api/v2/governance/audit-events/?consortium_id={consortium.id}"
        data = {
            "consortium": str(consortium.id),
            "event_type": "member_joined",
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestRewardDistributionEndpoints:
    """Tests for reward distribution."""

    def test_list_distributions(self, auth_client, consortium, company):
        """Test listing reward distributions."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )

        RewardDistribution.objects.create(
            consortium=consortium,
            total_amount=Decimal("100.00"),
            distributions=[{"company_id": str(company.id), "amount": 100.0}],
        )

        url = f"/api/v2/governance/rewards/?consortium_id={consortium.id}"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_distribute_rewards_as_owner(self, auth_client, consortium, company):
        """Test distributing rewards as consortium owner."""
        consortium.owner = company
        consortium.save()
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.OWNER,
            status=ConsortiumMember.Status.ACTIVE,
        )

        # Add verified contribution
        ContributionProof.objects.create(
            consortium=consortium,
            company=company,
            record_count=1000,
            feature_count=10,
            data_hash="a" * 64,
            verified=True,
        )

        url = "/api/v2/governance/rewards/distribute/"
        data = {
            "consortium_id": str(consortium.id),
            "amount": "1.0",
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert RewardDistribution.objects.filter(consortium=consortium).exists()

    def test_distribute_rewards_no_contributions(self, auth_client, consortium, company):
        """Test cannot distribute when no contributions."""
        consortium.owner = company
        consortium.save()
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.OWNER,
            status=ConsortiumMember.Status.ACTIVE,
        )

        url = "/api/v2/governance/rewards/distribute/"
        data = {
            "consortium_id": str(consortium.id),
            "amount": "1.0",
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "no contributions" in response.data["detail"].lower()


@pytest.mark.django_db
class TestProposalModel:
    """Tests for Proposal model methods."""

    def test_proposal_str(self, consortium, company):
        """Test proposal string representation."""
        proposal = Proposal.objects.create(
            consortium=consortium,
            proposer=company,
            proposal_type=Proposal.Type.UPDATE_CONFIG,
            title="Test Proposal",
            expires_at=timezone.now() + timedelta(days=7),
        )

        assert "Test Proposal" in str(proposal)

    def test_proposal_is_expired(self, consortium, company):
        """Test proposal expiration check."""
        proposal = Proposal.objects.create(
            consortium=consortium,
            proposer=company,
            proposal_type=Proposal.Type.UPDATE_CONFIG,
            title="Test",
            status=Proposal.Status.ACTIVE,
            expires_at=timezone.now() - timedelta(days=1),
        )

        assert proposal.is_expired is True

    def test_proposal_total_voters(self, consortium, company, other_company):
        """Test total voters count."""
        proposal = Proposal.objects.create(
            consortium=consortium,
            proposer=company,
            proposal_type=Proposal.Type.UPDATE_CONFIG,
            title="Test",
            expires_at=timezone.now() + timedelta(days=7),
        )

        Vote.objects.create(proposal=proposal, voter=company, support=True)
        Vote.objects.create(proposal=proposal, voter=other_company, support=False)

        assert proposal.total_voters == 2

    def test_check_result_passed(self, consortium, company):
        """Test proposal check_result when passed."""
        proposal = Proposal.objects.create(
            consortium=consortium,
            proposer=company,
            proposal_type=Proposal.Type.UPDATE_CONFIG,
            title="Test",
            expires_at=timezone.now() + timedelta(days=7),
            voting_weight_yes=7.0,
            voting_weight_no=3.0,
        )

        assert proposal.check_result(threshold=0.5) is True

    def test_check_result_failed(self, consortium, company):
        """Test proposal check_result when failed."""
        proposal = Proposal.objects.create(
            consortium=consortium,
            proposer=company,
            proposal_type=Proposal.Type.UPDATE_CONFIG,
            title="Test",
            expires_at=timezone.now() + timedelta(days=7),
            voting_weight_yes=3.0,
            voting_weight_no=7.0,
        )

        assert proposal.check_result(threshold=0.5) is False

    def test_check_result_no_votes(self, consortium, company):
        """Test proposal check_result with no votes."""
        proposal = Proposal.objects.create(
            consortium=consortium,
            proposer=company,
            proposal_type=Proposal.Type.UPDATE_CONFIG,
            title="Test",
            expires_at=timezone.now() + timedelta(days=7),
        )

        assert proposal.check_result() is None


@pytest.mark.django_db
class TestVoteModel:
    """Tests for Vote model."""

    def test_vote_str(self, consortium, company):
        """Test vote string representation."""
        proposal = Proposal.objects.create(
            consortium=consortium,
            proposer=company,
            proposal_type=Proposal.Type.UPDATE_CONFIG,
            title="Test Proposal",
            expires_at=timezone.now() + timedelta(days=7),
        )

        vote = Vote.objects.create(
            proposal=proposal,
            voter=company,
            support=Vote.Support.FOR,
        )

        assert Vote.Support.FOR in str(vote)
        assert company.name in str(vote)


@pytest.mark.django_db
class TestAuditEventModel:
    """Tests for AuditEvent model."""

    def test_audit_event_hash_generation(self, consortium, company):
        """Test audit event hash can be stored and retrieved."""
        test_hash = "a" * 64  # SHA-256 hex-length placeholder
        event = AuditEvent.objects.create(
            consortium=consortium,
            actor=company,
            event_type=AuditEvent.EventType.MEMBER_JOINED,
            event_hash=test_hash,
        )

        assert event.event_hash == test_hash
        assert len(event.event_hash) == 64  # SHA-256 hex length

    def test_audit_event_str(self, consortium, company):
        """Test audit event string representation."""
        event = AuditEvent.objects.create(
            consortium=consortium,
            actor=company,
            event_type=AuditEvent.EventType.MEMBER_JOINED,
        )

        assert "member_joined" in str(event)

    def test_get_previous_hash_empty(self, consortium):
        """Test get_previous_hash returns empty for first event."""
        hash_val = AuditEvent.get_previous_hash(consortium.id)
        assert hash_val == ""

    def test_get_previous_hash_chain(self, consortium, company):
        """Test get_previous_hash returns last event hash."""
        event = AuditEvent.objects.create(
            consortium=consortium,
            actor=company,
            event_type=AuditEvent.EventType.MEMBER_JOINED,
        )

        hash_val = AuditEvent.get_previous_hash(consortium.id)
        assert hash_val == event.event_hash


@pytest.mark.django_db
class TestRewardDistributionModel:
    """Tests for RewardDistribution model."""

    def test_distribution_str(self, consortium):
        """Test distribution string representation."""
        dist = RewardDistribution.objects.create(
            consortium=consortium,
            total_amount=Decimal("100.00"),
            distributions=[],
        )

        assert "100" in str(dist)
        assert consortium.name in str(dist)

"""
Tests for ProposalExecutionService.

Covers all 7 proposal type handlers, validation, audit trail, and error cases.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.consortiums.models import (
    Consortium,
    ConsortiumMember,
    ContributionProof,
)
from apps.core.models import Company
from apps.governance.models import AuditEvent, Proposal, RewardDistribution
from apps.governance.services import ExecutionResult, ProposalExecutionService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def gov_company(db):
    return Company.objects.create(name="Gov Corp", email="gov@corp.com", industry="tech")


@pytest.fixture
def target_company(db):
    return Company.objects.create(name="Target Co", email="target@co.com", industry="finance")


@pytest.fixture
def third_company(db):
    return Company.objects.create(name="Third Co", email="third@co.com", industry="health")


@pytest.fixture
def gov_consortium(db, gov_company):
    return Consortium.objects.create(
        name="Gov Consortium",
        owner=gov_company,
        status=Consortium.Status.ACTIVE,
        min_members=2,
    )


@pytest.fixture
def owner_member(db, gov_consortium, gov_company):
    return ConsortiumMember.objects.create(
        consortium=gov_consortium,
        company=gov_company,
        role=ConsortiumMember.Role.OWNER,
        status=ConsortiumMember.Status.ACTIVE,
    )


@pytest.fixture
def target_member(db, gov_consortium, target_company):
    return ConsortiumMember.objects.create(
        consortium=gov_consortium,
        company=target_company,
        role=ConsortiumMember.Role.CONTRIBUTOR,
        status=ConsortiumMember.Status.ACTIVE,
    )


def _make_proposal(consortium, proposer, proposal_type, data=None, status=Proposal.Status.PASSED):
    return Proposal.objects.create(
        consortium=consortium,
        proposer=proposer,
        proposal_type=proposal_type,
        title=f"Test {proposal_type}",
        data=data or {},
        status=status,
        expires_at=timezone.now() + timedelta(days=7),
    )


# ===========================================================================
# Core Execution Tests
# ===========================================================================


@pytest.mark.django_db
class TestProposalExecutionValidation:
    def test_execute_non_passed_proposal_fails(self, gov_consortium, gov_company):
        proposal = _make_proposal(
            gov_consortium,
            gov_company,
            Proposal.Type.ADD_MEMBER,
            status=Proposal.Status.ACTIVE,
        )

        service = ProposalExecutionService()
        result = service.execute(proposal)

        assert not result.success
        assert result.error_code == "invalid_status"

    def test_execute_rejected_proposal_fails(self, gov_consortium, gov_company):
        proposal = _make_proposal(
            gov_consortium,
            gov_company,
            Proposal.Type.ADD_MEMBER,
            status=Proposal.Status.REJECTED,
        )

        service = ProposalExecutionService()
        result = service.execute(proposal)

        assert not result.success

    def test_execute_unknown_handler_fails(self, gov_consortium, gov_company):
        proposal = _make_proposal(
            gov_consortium,
            gov_company,
            "unknown_type",
        )

        service = ProposalExecutionService()
        result = service.execute(proposal)

        assert not result.success
        assert result.error_code == "no_handler"


# ===========================================================================
# ADD_MEMBER Handler Tests
# ===========================================================================


@pytest.mark.django_db
class TestExecuteAddMember:
    def test_add_member_happy_path(self, gov_consortium, gov_company, target_company):
        proposal = _make_proposal(
            gov_consortium,
            gov_company,
            Proposal.Type.ADD_MEMBER,
            data={"company_id": str(target_company.id), "role": "contributor"},
        )

        service = ProposalExecutionService()
        result = service.execute(proposal)

        assert result.success
        exec_result = result.data
        assert exec_result.success
        assert "member_id" in exec_result.data

        member = ConsortiumMember.objects.get(
            consortium=gov_consortium,
            company=target_company,
        )
        assert member.status == ConsortiumMember.Status.ACTIVE

    def test_add_member_missing_company_id(self, gov_consortium, gov_company):
        proposal = _make_proposal(
            gov_consortium,
            gov_company,
            Proposal.Type.ADD_MEMBER,
            data={},
        )

        service = ProposalExecutionService()
        result = service.execute(proposal)

        assert result.success  # Execution succeeded but handler returned failure
        assert not result.data.success

    def test_add_member_already_active_fails(
        self, gov_consortium, gov_company, target_company, target_member
    ):
        proposal = _make_proposal(
            gov_consortium,
            gov_company,
            Proposal.Type.ADD_MEMBER,
            data={"company_id": str(target_company.id)},
        )

        service = ProposalExecutionService()
        result = service.execute(proposal)

        assert result.success
        assert not result.data.success
        assert "already" in result.data.message.lower()

    def test_add_member_reactivates_left_member(
        self, gov_consortium, gov_company, target_company
    ):
        ConsortiumMember.objects.create(
            consortium=gov_consortium,
            company=target_company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.LEFT,
        )

        proposal = _make_proposal(
            gov_consortium,
            gov_company,
            Proposal.Type.ADD_MEMBER,
            data={"company_id": str(target_company.id), "role": "admin"},
        )

        service = ProposalExecutionService()
        result = service.execute(proposal)

        assert result.success
        assert result.data.success

        member = ConsortiumMember.objects.get(
            consortium=gov_consortium,
            company=target_company,
        )
        assert member.status == ConsortiumMember.Status.ACTIVE
        assert member.role == "admin"


# ===========================================================================
# REMOVE_MEMBER Handler Tests
# ===========================================================================


@pytest.mark.django_db
class TestExecuteRemoveMember:
    def test_remove_member_happy_path(
        self, gov_consortium, gov_company, target_company, target_member
    ):
        proposal = _make_proposal(
            gov_consortium,
            gov_company,
            Proposal.Type.REMOVE_MEMBER,
            data={"company_id": str(target_company.id)},
        )

        service = ProposalExecutionService()
        result = service.execute(proposal)

        assert result.success
        assert result.data.success

        target_member.refresh_from_db()
        assert target_member.status == ConsortiumMember.Status.REMOVED

    def test_remove_member_missing_company_id(self, gov_consortium, gov_company):
        proposal = _make_proposal(
            gov_consortium,
            gov_company,
            Proposal.Type.REMOVE_MEMBER,
            data={},
        )

        service = ProposalExecutionService()
        result = service.execute(proposal)

        assert result.success
        assert not result.data.success

    def test_remove_owner_fails(self, gov_consortium, gov_company, owner_member):
        proposal = _make_proposal(
            gov_consortium,
            gov_company,
            Proposal.Type.REMOVE_MEMBER,
            data={"company_id": str(gov_company.id)},
        )

        service = ProposalExecutionService()
        result = service.execute(proposal)

        assert result.success
        assert not result.data.success
        assert "owner" in result.data.message.lower()

    def test_remove_nonexistent_member(self, gov_consortium, gov_company, third_company):
        proposal = _make_proposal(
            gov_consortium,
            gov_company,
            Proposal.Type.REMOVE_MEMBER,
            data={"company_id": str(third_company.id)},
        )

        service = ProposalExecutionService()
        result = service.execute(proposal)

        assert result.success
        assert not result.data.success


# ===========================================================================
# CHANGE_MODEL Handler Tests
# ===========================================================================


@pytest.mark.django_db
class TestExecuteChangeModel:
    def test_change_model_happy_path(self, gov_consortium, gov_company):
        proposal = _make_proposal(
            gov_consortium,
            gov_company,
            Proposal.Type.CHANGE_MODEL,
            data={"model_type": Consortium.ModelType.LINEAR_REGRESSION},
        )

        service = ProposalExecutionService()
        result = service.execute(proposal)

        assert result.success
        assert result.data.success

        gov_consortium.refresh_from_db()
        assert gov_consortium.model_type == Consortium.ModelType.LINEAR_REGRESSION

    def test_change_model_missing_type(self, gov_consortium, gov_company):
        proposal = _make_proposal(
            gov_consortium,
            gov_company,
            Proposal.Type.CHANGE_MODEL,
            data={},
        )

        service = ProposalExecutionService()
        result = service.execute(proposal)

        assert result.success
        assert not result.data.success

    def test_change_model_invalid_type(self, gov_consortium, gov_company):
        proposal = _make_proposal(
            gov_consortium,
            gov_company,
            Proposal.Type.CHANGE_MODEL,
            data={"model_type": "nonexistent_model"},
        )

        service = ProposalExecutionService()
        result = service.execute(proposal)

        assert result.success
        assert not result.data.success


# ===========================================================================
# START_TRAINING Handler Tests
# ===========================================================================


@pytest.mark.django_db
class TestExecuteStartTraining:
    def test_start_training_happy_path(
        self, gov_consortium, gov_company, owner_member, target_member
    ):
        proposal = _make_proposal(
            gov_consortium,
            gov_company,
            Proposal.Type.START_TRAINING,
        )

        service = ProposalExecutionService()
        result = service.execute(proposal)

        assert result.success
        assert result.data.success

        gov_consortium.refresh_from_db()
        assert gov_consortium.status == Consortium.Status.TRAINING

    def test_start_training_already_training(self, gov_consortium, gov_company):
        gov_consortium.status = Consortium.Status.TRAINING
        gov_consortium.save()

        proposal = _make_proposal(
            gov_consortium,
            gov_company,
            Proposal.Type.START_TRAINING,
        )

        service = ProposalExecutionService()
        result = service.execute(proposal)

        assert result.success
        assert not result.data.success

    def test_start_training_insufficient_members(self, gov_consortium, gov_company):
        # No members at all (member_count = 0 < min_members = 2)
        proposal = _make_proposal(
            gov_consortium,
            gov_company,
            Proposal.Type.START_TRAINING,
        )

        service = ProposalExecutionService()
        result = service.execute(proposal)

        assert result.success
        assert not result.data.success
        assert "members" in result.data.message.lower()


# ===========================================================================
# DISTRIBUTE_REWARDS Handler Tests
# ===========================================================================


@pytest.mark.django_db
class TestExecuteDistributeRewards:
    def test_distribute_rewards_happy_path(
        self, gov_consortium, gov_company, target_company, owner_member, target_member
    ):
        # Create verified contributions
        ContributionProof.objects.create(
            consortium=gov_consortium,
            company=gov_company,
            record_count=1000,
            feature_count=10,
            data_hash="abc123",
            checksum="xyz",
            verified=True,
        )
        ContributionProof.objects.create(
            consortium=gov_consortium,
            company=target_company,
            record_count=500,
            feature_count=10,
            data_hash="def456",
            checksum="xyz",
            verified=True,
        )

        proposal = _make_proposal(
            gov_consortium,
            gov_company,
            Proposal.Type.DISTRIBUTE_REWARDS,
            data={"amount": "1.5", "currency": "ETH"},
        )

        service = ProposalExecutionService()
        result = service.execute(proposal)

        assert result.success
        assert result.data.success
        assert "distribution_id" in result.data.data

        dist = RewardDistribution.objects.get(consortium=gov_consortium)
        assert dist.total_amount == Decimal("1.5")
        assert len(dist.distributions) == 2

    def test_distribute_rewards_invalid_amount(self, gov_consortium, gov_company):
        proposal = _make_proposal(
            gov_consortium,
            gov_company,
            Proposal.Type.DISTRIBUTE_REWARDS,
            data={"amount": "0"},
        )

        service = ProposalExecutionService()
        result = service.execute(proposal)

        assert result.success
        assert not result.data.success

    def test_distribute_rewards_no_contributions(self, gov_consortium, gov_company):
        proposal = _make_proposal(
            gov_consortium,
            gov_company,
            Proposal.Type.DISTRIBUTE_REWARDS,
            data={"amount": "1.0"},
        )

        service = ProposalExecutionService()
        result = service.execute(proposal)

        assert result.success
        assert not result.data.success
        assert "contributions" in result.data.message.lower()


# ===========================================================================
# UPDATE_CONFIG Handler Tests
# ===========================================================================


@pytest.mark.django_db
class TestExecuteUpdateConfig:
    def test_update_config_allowed_fields(self, gov_consortium, gov_company):
        proposal = _make_proposal(
            gov_consortium,
            gov_company,
            Proposal.Type.UPDATE_CONFIG,
            data={"config": {"voting_threshold": 0.75, "min_members": 3}},
        )

        service = ProposalExecutionService()
        result = service.execute(proposal)

        assert result.success
        assert result.data.success

        gov_consortium.refresh_from_db()
        assert gov_consortium.voting_threshold == 0.75
        assert gov_consortium.min_members == 3

    def test_update_config_ml_fields(self, gov_consortium, gov_company):
        proposal = _make_proposal(
            gov_consortium,
            gov_company,
            Proposal.Type.UPDATE_CONFIG,
            data={"config": {"ml_learning_rate": 0.01}},
        )

        service = ProposalExecutionService()
        result = service.execute(proposal)

        assert result.success
        assert result.data.success

        gov_consortium.refresh_from_db()
        assert gov_consortium.ml_config.get("ml_learning_rate") == 0.01

    def test_update_config_empty_fails(self, gov_consortium, gov_company):
        proposal = _make_proposal(
            gov_consortium,
            gov_company,
            Proposal.Type.UPDATE_CONFIG,
            data={"config": {}},
        )

        service = ProposalExecutionService()
        result = service.execute(proposal)

        assert result.success
        assert not result.data.success

    def test_update_config_no_config_key_fails(self, gov_consortium, gov_company):
        proposal = _make_proposal(
            gov_consortium,
            gov_company,
            Proposal.Type.UPDATE_CONFIG,
            data={},
        )

        service = ProposalExecutionService()
        result = service.execute(proposal)

        assert result.success
        assert not result.data.success

    def test_update_config_ignores_disallowed_fields(self, gov_consortium, gov_company):
        proposal = _make_proposal(
            gov_consortium,
            gov_company,
            Proposal.Type.UPDATE_CONFIG,
            data={"config": {"name": "hacked", "voting_threshold": 0.8}},
        )

        service = ProposalExecutionService()
        result = service.execute(proposal)

        assert result.success
        assert result.data.success

        gov_consortium.refresh_from_db()
        assert gov_consortium.name == "Gov Consortium"  # Unchanged
        assert gov_consortium.voting_threshold == 0.8


# ===========================================================================
# DISSOLVE Handler Tests
# ===========================================================================


@pytest.mark.django_db
class TestExecuteDissolve:
    def test_dissolve_happy_path(
        self, gov_consortium, gov_company, owner_member, target_member
    ):
        proposal = _make_proposal(
            gov_consortium,
            gov_company,
            Proposal.Type.DISSOLVE,
        )

        service = ProposalExecutionService()
        result = service.execute(proposal)

        assert result.success
        assert result.data.success

        gov_consortium.refresh_from_db()
        assert gov_consortium.status == Consortium.Status.ARCHIVED

        owner_member.refresh_from_db()
        target_member.refresh_from_db()
        assert owner_member.status == ConsortiumMember.Status.LEFT
        assert target_member.status == ConsortiumMember.Status.LEFT


# ===========================================================================
# Audit Trail Tests
# ===========================================================================


@pytest.mark.django_db
class TestProposalExecutionAudit:
    def test_successful_execution_creates_audit_event(
        self, gov_consortium, gov_company, owner_member, target_member
    ):
        proposal = _make_proposal(
            gov_consortium,
            gov_company,
            Proposal.Type.START_TRAINING,
        )

        service = ProposalExecutionService()
        result = service.execute(proposal)

        assert result.success
        assert result.data.success

        audit = AuditEvent.objects.filter(
            consortium=gov_consortium,
            event_type=AuditEvent.EventType.PROPOSAL_EXECUTED,
        ).first()
        assert audit is not None
        assert audit.target_id == str(proposal.id)

    def test_successful_execution_marks_proposal_executed(
        self, gov_consortium, gov_company, owner_member, target_member
    ):
        proposal = _make_proposal(
            gov_consortium,
            gov_company,
            Proposal.Type.START_TRAINING,
        )

        service = ProposalExecutionService()
        service.execute(proposal)

        proposal.refresh_from_db()
        assert proposal.status == Proposal.Status.EXECUTED
        assert proposal.executed_at is not None

    def test_failed_handler_does_not_create_audit(self, gov_consortium, gov_company):
        proposal = _make_proposal(
            gov_consortium,
            gov_company,
            Proposal.Type.REMOVE_MEMBER,
            data={},
        )

        service = ProposalExecutionService()
        result = service.execute(proposal)

        # Handler failed (missing company_id)
        assert not result.data.success

        audit_count = AuditEvent.objects.filter(
            consortium=gov_consortium,
            event_type=AuditEvent.EventType.PROPOSAL_EXECUTED,
        ).count()
        assert audit_count == 0

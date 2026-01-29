"""
Integration tests for complete consortium workflow.

Tests the full E2E flow:
1. Authentication
2. Consortium creation
3. Invitation management
4. Member activation
5. Automatic consortium activation
6. Data contribution with verification
7. Training initiation
"""

import hashlib
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.consortiums.models import (
    Consortium,
    ConsortiumInvitation,
    ConsortiumMember,
    ContributionProof,
    TrainingResult,
)
from apps.core.models import Company, User


@pytest.fixture
def api_client():
    """Create an API client for testing."""
    return APIClient()


@pytest.fixture
def create_hospital(db):
    """Factory for creating hospital companies with users."""
    counter = [0]

    def _create(name: str, email: str):
        counter[0] += 1
        company = Company.objects.create(
            name=name,
            email=email,
            tier="enterprise",
        )
        # Use unique email based on company email to avoid conflicts
        user_email = f"admin{counter[0]}_{email.replace('@', '_at_')}"
        user = User.objects.create_user(
            email=user_email,
            password="TestPassword123!",
            company=company,
        )
        return company, user
    return _create


@pytest.fixture
def hospital_a(create_hospital):
    """Create Hospital A (consortium owner)."""
    return create_hospital("Hospital A - Consortium Owner", "hospital_a@example.com")


@pytest.fixture
def hospital_b(create_hospital):
    """Create Hospital B (invited member)."""
    return create_hospital("Hospital B - Member", "hospital_b@example.com")


@pytest.fixture
def hospital_c(create_hospital):
    """Create Hospital C (invited member)."""
    return create_hospital("Hospital C - Member", "hospital_c@example.com")


def generate_data_hash(data: str) -> str:
    """Generate a valid SHA-256 hash."""
    return hashlib.sha256(data.encode()).hexdigest()


class TestCompleteConsortiumFlow:
    """
    Integration tests for the complete consortium workflow.

    This test class validates the full E2E flow documented in
    docs/evidence/consortium-test-report.html
    """

    @pytest.mark.django_db(transaction=True)
    def test_complete_consortium_flow(
        self,
        api_client,
        hospital_a,
        hospital_b,
        hospital_c,
    ):
        """
        Test the complete consortium workflow from creation to training.

        Steps:
        1. Hospital A authenticates and creates a consortium
        2. Hospital A invites Hospital B and Hospital C
        3. Hospitals B and C accept invitations
        4. Consortium auto-activates when min_members is reached
        5. All hospitals contribute data (auto-verified)
        6. Hospital A starts training
        7. Verify final state
        """
        company_a, user_a = hospital_a
        company_b, user_b = hospital_b
        company_c, user_c = hospital_c

        # =================================================================
        # STEP 1: Hospital A creates a consortium
        # =================================================================

        api_client.force_authenticate(user=user_a)

        consortium_data = {
            "name": "Healthcare Analytics Consortium",
            "description": "Collaborative cancer research using privacy-preserving ML",
            "model_type": "logistic_regression",
            "min_members": 3,
            "ml_config": {
                "learning_rate": 0.01,
                "epochs": 10,
                "security_level": 128,
            },
            "voting_threshold": 0.6,
            "voting_duration_days": 7,
        }

        response = api_client.post(
            "/api/v2/consortiums/",
            data=consortium_data,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert "id" in response.data, "Response should include consortium ID"

        consortium_id = response.data["id"]
        consortium = Consortium.objects.get(id=consortium_id)

        assert consortium.status == Consortium.Status.DRAFT
        assert consortium.owner == company_a

        # Verify owner membership was created
        owner_membership = ConsortiumMember.objects.get(
            consortium=consortium,
            company=company_a,
        )
        assert owner_membership.role == ConsortiumMember.Role.OWNER
        assert owner_membership.status == ConsortiumMember.Status.ACTIVE

        # =================================================================
        # STEP 2: Hospital A invites Hospital B and Hospital C
        # =================================================================

        expires_at = timezone.now() + timedelta(days=7)

        # Invite Hospital B
        invitation_b_data = {
            "consortium": str(consortium_id),
            "invitee_email": company_b.email,
            "role": "contributor",
            "message": "Join our cancer research consortium",
            "expires_at": expires_at.isoformat(),
        }

        response = api_client.post(
            "/api/v2/consortiums/invitations/",
            data=invitation_b_data,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert "id" in response.data, "Response should include invitation ID"
        invitation_b_id = response.data["id"]

        # Invite Hospital C
        invitation_c_data = {
            "consortium": str(consortium_id),
            "invitee_email": company_c.email,
            "role": "contributor",
            "message": "Join our cancer research consortium",
            "expires_at": expires_at.isoformat(),
        }

        response = api_client.post(
            "/api/v2/consortiums/invitations/",
            data=invitation_c_data,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        invitation_c_id = response.data["id"]

        # =================================================================
        # STEP 3: Hospitals B and C accept invitations
        # =================================================================

        # Hospital B accepts
        api_client.force_authenticate(user=user_b)

        response = api_client.post(
            f"/api/v2/consortiums/invitations/{invitation_b_id}/accept/",
        )

        assert response.status_code == status.HTTP_200_OK

        invitation_b = ConsortiumInvitation.objects.get(id=invitation_b_id)
        assert invitation_b.status == ConsortiumInvitation.Status.ACCEPTED

        # Verify membership created
        member_b = ConsortiumMember.objects.get(
            consortium=consortium,
            company=company_b,
        )
        assert member_b.status == ConsortiumMember.Status.ACTIVE

        # Consortium should still be in DRAFT (need 3 members, have 2)
        consortium.refresh_from_db()
        assert consortium.status == Consortium.Status.DRAFT

        # Hospital C accepts
        api_client.force_authenticate(user=user_c)

        response = api_client.post(
            f"/api/v2/consortiums/invitations/{invitation_c_id}/accept/",
        )

        assert response.status_code == status.HTTP_200_OK

        # =================================================================
        # STEP 4: Verify automatic consortium activation
        # =================================================================

        consortium.refresh_from_db()
        assert consortium.status == Consortium.Status.ACTIVE, (
            "Consortium should auto-activate when min_members is reached"
        )

        # Verify all 3 members are active
        active_members = ConsortiumMember.objects.filter(
            consortium=consortium,
            status=ConsortiumMember.Status.ACTIVE,
        ).count()
        assert active_members == 3

        # =================================================================
        # STEP 5: All hospitals contribute data with auto-verification
        # =================================================================

        contributions_data = [
            (user_a, company_a, 10000, "hospital_a_data_v1"),
            (user_b, company_b, 8000, "hospital_b_data_v1"),
            (user_c, company_c, 12000, "hospital_c_data_v1"),
        ]

        contribution_ids = []

        for user, company, record_count, data_seed in contributions_data:
            api_client.force_authenticate(user=user)

            contribution_data = {
                "consortium": str(consortium_id),
                "record_count": record_count,
                "feature_count": 25,
                "data_hash": generate_data_hash(data_seed),
                "checksum": generate_data_hash(f"{data_seed}_checksum"),
            }

            response = api_client.post(
                f"/api/v2/consortiums/{consortium_id}/contributions/",
                data=contribution_data,
                format="json",
            )

            assert response.status_code == status.HTTP_201_CREATED
            assert "id" in response.data, "Response should include contribution ID"
            contribution_ids.append(response.data["id"])

        # Verify all contributions were auto-verified
        for contribution_id in contribution_ids:
            contribution = ContributionProof.objects.get(id=contribution_id)
            assert contribution.verified is True, (
                f"Contribution {contribution_id} should be auto-verified"
            )
            assert contribution.verification_status == ContributionProof.VerificationStatus.VERIFIED

        # Verify total records
        total_records = ContributionProof.objects.filter(
            consortium=consortium,
            verified=True,
        ).values_list("record_count", flat=True)

        assert sum(total_records) == 30000, "Total records should be 30,000"

        # =================================================================
        # STEP 6: Hospital A starts training
        # =================================================================

        api_client.force_authenticate(user=user_a)

        # Mock Celery task to avoid actual async execution
        with patch("apps.consortiums.tasks.train_consortium_model.delay") as mock_task:
            mock_task.return_value.id = "test-task-id-12345"

            response = api_client.post(
                f"/api/v2/consortiums/{consortium_id}/start_training/",
            )

            assert response.status_code == status.HTTP_200_OK
            assert "task_id" in response.data, "Response should include task_id"
            assert "training_result_id" in response.data

        # Verify training result was created
        training_result = TrainingResult.objects.get(
            id=response.data["training_result_id"]
        )
        assert training_result.status == TrainingResult.Status.PENDING
        assert training_result.contributions_count == 3
        assert training_result.total_records == 30000

        # Verify consortium status
        consortium.refresh_from_db()
        assert consortium.status == "training"

        # =================================================================
        # STEP 7: Final state verification
        # =================================================================

        # Summary
        final_stats = {
            "consortium_id": str(consortium_id),
            "consortium_status": consortium.status,
            "active_members": ConsortiumMember.objects.filter(
                consortium=consortium,
                status=ConsortiumMember.Status.ACTIVE,
            ).count(),
            "verified_contributions": ContributionProof.objects.filter(
                consortium=consortium,
                verified=True,
            ).count(),
            "total_records": sum(
                ContributionProof.objects.filter(
                    consortium=consortium,
                    verified=True,
                ).values_list("record_count", flat=True)
            ),
            "training_started": TrainingResult.objects.filter(
                consortium=consortium,
            ).exists(),
        }

        assert final_stats["active_members"] == 3
        assert final_stats["verified_contributions"] == 3
        assert final_stats["total_records"] == 30000
        assert final_stats["training_started"] is True

    @pytest.mark.django_db
    def test_serializers_return_ids(self, api_client, hospital_a, hospital_b):
        """Test that create serializers return IDs in response."""
        company_a, user_a = hospital_a
        company_b, user_b = hospital_b

        api_client.force_authenticate(user=user_a)

        # Test consortium creation returns ID
        consortium_data = {
            "name": "Test Consortium",
            "description": "Test",
            "model_type": "linear_regression",
            "min_members": 2,
        }

        response = api_client.post(
            "/api/v2/consortiums/",
            data=consortium_data,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED, f"Response: {response.data}"
        assert "id" in response.data, "Response should include consortium ID"

        consortium_id = response.data["id"]

        # Test invitation creation returns ID
        invitation_data = {
            "consortium": str(consortium_id),
            "invitee_email": company_b.email,
            "role": "contributor",
            "expires_at": (timezone.now() + timedelta(days=7)).isoformat(),
        }

        response = api_client.post(
            "/api/v2/consortiums/invitations/",
            data=invitation_data,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED, f"Response: {response.data}"
        assert "id" in response.data, "Response should include invitation ID"

        # Test contribution creation returns ID
        contribution_data = {
            "consortium": str(consortium_id),
            "record_count": 1000,
            "feature_count": 10,
            "data_hash": generate_data_hash("test_data"),
            "checksum": generate_data_hash("test_checksum"),
        }

        response = api_client.post(
            f"/api/v2/consortiums/{consortium_id}/contributions/",
            data=contribution_data,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED, f"Response: {response.data}"
        assert "id" in response.data, "Response should include contribution ID"

    @pytest.mark.django_db
    def test_contribution_auto_verification(self, api_client, hospital_a):
        """Test that contributions are automatically verified."""
        company_a, user_a = hospital_a

        api_client.force_authenticate(user=user_a)

        # Create consortium
        consortium_data = {
            "name": "Verification Test Consortium",
            "model_type": "linear_regression",
            "min_members": 1,
        }

        response = api_client.post(
            "/api/v2/consortiums/",
            data=consortium_data,
            format="json",
        )
        consortium_id = response.data["id"]

        # Create contribution with valid data
        contribution_data = {
            "consortium": str(consortium_id),
            "record_count": 1000,
            "feature_count": 10,
            "data_hash": generate_data_hash("valid_data"),
            "checksum": generate_data_hash("valid_checksum"),
        }

        response = api_client.post(
            f"/api/v2/consortiums/{consortium_id}/contributions/",
            data=contribution_data,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        contribution = ContributionProof.objects.get(id=response.data["id"])
        assert contribution.verified is True
        assert contribution.verification_status == ContributionProof.VerificationStatus.VERIFIED
        assert contribution.verification_message == "All verification checks passed"

    @pytest.mark.django_db
    def test_consortium_auto_activation(self, api_client, hospital_a, hospital_b):
        """Test that consortium auto-activates when min_members is reached."""
        company_a, user_a = hospital_a
        company_b, user_b = hospital_b

        api_client.force_authenticate(user=user_a)

        # Create consortium with min_members=2
        consortium_data = {
            "name": "Auto-Activation Test",
            "model_type": "linear_regression",
            "min_members": 2,
        }

        response = api_client.post(
            "/api/v2/consortiums/",
            data=consortium_data,
            format="json",
        )
        consortium_id = response.data["id"]

        # Verify initial status is DRAFT
        consortium = Consortium.objects.get(id=consortium_id)
        assert consortium.status == Consortium.Status.DRAFT

        # Create invitation
        invitation_data = {
            "consortium": str(consortium_id),
            "invitee_email": company_b.email,
            "role": "contributor",
            "expires_at": (timezone.now() + timedelta(days=7)).isoformat(),
        }

        response = api_client.post(
            "/api/v2/consortiums/invitations/",
            data=invitation_data,
            format="json",
        )
        invitation_id = response.data["id"]

        # Hospital B accepts
        api_client.force_authenticate(user=user_b)
        response = api_client.post(f"/api/v2/consortiums/invitations/{invitation_id}/accept/")

        assert response.status_code == status.HTTP_200_OK

        # Verify consortium is now ACTIVE
        consortium.refresh_from_db()
        assert consortium.status == Consortium.Status.ACTIVE, (
            "Consortium should auto-activate when min_members is reached"
        )

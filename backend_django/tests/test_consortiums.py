"""
Consortium module tests for Xcapit FHE-ML Platform.
"""

import pytest
from rest_framework import status

from apps.consortiums.models import Consortium, ConsortiumMember, ContributionProof


@pytest.mark.django_db
class TestConsortiumEndpoints:
    """Tests for consortium endpoints."""

    def test_create_consortium(self, auth_client, company):
        """Test creating a consortium."""
        url = "/api/v2/consortiums/"
        data = {
            "name": "New Consortium",
            "description": "Test consortium",
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Consortium"

        # Consortium should be created
        consortium = Consortium.objects.get(name="New Consortium")

        # Owner should be added as OWNER member with ACTIVE status
        assert ConsortiumMember.objects.filter(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.OWNER,
            status=ConsortiumMember.Status.ACTIVE,
        ).exists()

    def test_list_consortiums(self, auth_client, consortium, company):
        """Test listing consortiums."""
        # User must be an ACTIVE member to see the consortium
        ConsortiumMember.objects.get_or_create(
            consortium=consortium,
            company=company,
            defaults={
                "role": ConsortiumMember.Role.CONTRIBUTOR,
                "status": ConsortiumMember.Status.ACTIVE,
            },
        )

        url = "/api/v2/consortiums/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_get_consortium(self, auth_client, consortium, company):
        """Test getting a single consortium."""
        # User must be an ACTIVE member to access
        ConsortiumMember.objects.get_or_create(
            consortium=consortium,
            company=company,
            defaults={
                "role": ConsortiumMember.Role.CONTRIBUTOR,
                "status": ConsortiumMember.Status.ACTIVE,
            },
        )

        url = f"/api/v2/consortiums/{consortium.id}/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == consortium.name

    def test_update_consortium_as_owner(self, auth_client, consortium, company):
        """Test updating consortium as owner."""
        # Ensure company is the owner
        consortium.owner = company
        consortium.save()
        ConsortiumMember.objects.get_or_create(
            consortium=consortium,
            company=company,
            defaults={
                "role": ConsortiumMember.Role.OWNER,
                "status": ConsortiumMember.Status.ACTIVE,
            },
        )

        url = f"/api/v2/consortiums/{consortium.id}/"
        data = {"description": "Updated description"}

        response = auth_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        consortium.refresh_from_db()
        assert consortium.description == "Updated description"


@pytest.mark.django_db
class TestConsortiumMemberEndpoints:
    """Tests for consortium member endpoints."""

    def test_list_members(self, auth_client, consortium, company):
        """Test listing consortium members."""
        ConsortiumMember.objects.get_or_create(
            consortium=consortium,
            company=company,
            defaults={
                "role": ConsortiumMember.Role.CONTRIBUTOR,
                "status": ConsortiumMember.Status.ACTIVE,
            },
        )

        url = f"/api/v2/consortiums/{consortium.id}/members/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestContributionEndpoints:
    """Tests for contribution endpoints."""

    def test_submit_contribution(self, auth_client, consortium, company):
        """Test submitting a contribution proof."""
        # Ensure user is a member
        ConsortiumMember.objects.get_or_create(
            consortium=consortium,
            company=company,
            defaults={
                "role": ConsortiumMember.Role.CONTRIBUTOR,
                "status": ConsortiumMember.Status.ACTIVE,
            },
        )

        url = f"/api/v2/consortiums/{consortium.id}/contributions/"
        # ContributionProofCreateSerializer requires: consortium, record_count, feature_count, data_hash (64 char SHA-256), checksum
        data = {
            "consortium": str(consortium.id),
            "record_count": 1000,
            "feature_count": 10,
            "data_hash": "abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234",
            "checksum": "efgh5678efgh5678efgh5678efgh5678efgh5678efgh5678efgh5678efgh5678",
        }

        response = auth_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["record_count"] == 1000

    def test_list_contributions(self, auth_client, consortium, company):
        """Test listing contributions."""
        ConsortiumMember.objects.get_or_create(
            consortium=consortium,
            company=company,
            defaults={
                "role": ConsortiumMember.Role.CONTRIBUTOR,
                "status": ConsortiumMember.Status.ACTIVE,
            },
        )

        ContributionProof.objects.create(
            consortium=consortium,
            company=company,
            record_count=500,
            feature_count=10,
            data_hash="abc123def456789012345678901234567890123456789012345678901234",
        )

        url = f"/api/v2/consortiums/{consortium.id}/contributions/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1


@pytest.mark.django_db
class TestConsortiumInvitations:
    """Tests for consortium invitations."""

    def test_create_invitation(self, auth_client, consortium, company, other_company):
        """Test creating an invitation."""
        # Make user an admin of the consortium first
        consortium.owner = company
        consortium.save()
        ConsortiumMember.objects.get_or_create(
            consortium=consortium,
            company=company,
            defaults={
                "role": ConsortiumMember.Role.ADMIN,
                "status": ConsortiumMember.Status.ACTIVE,
            },
        )

        # Invitations are at the top level, not nested under consortium
        url = "/api/v2/consortiums/invitations/"
        from django.utils import timezone
        from datetime import timedelta
        expires_at = (timezone.now() + timedelta(days=7)).isoformat()

        data = {
            "consortium": str(consortium.id),
            "invitee_email": other_company.email,
            "message": "Please join our consortium",
            "expires_at": expires_at,
        }

        response = auth_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_list_invitations(self, auth_client, consortium, company):
        """Test listing invitations."""
        consortium.owner = company
        consortium.save()
        ConsortiumMember.objects.get_or_create(
            consortium=consortium,
            company=company,
            defaults={
                "role": ConsortiumMember.Role.ADMIN,
                "status": ConsortiumMember.Status.ACTIVE,
            },
        )

        url = "/api/v2/consortiums/invitations/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestConsortiumStats:
    """Tests for consortium statistics."""

    def test_get_stats(self, auth_client, consortium, company):
        """Test getting consortium statistics."""
        ConsortiumMember.objects.get_or_create(
            consortium=consortium,
            company=company,
            defaults={
                "role": ConsortiumMember.Role.CONTRIBUTOR,
                "status": ConsortiumMember.Status.ACTIVE,
            },
        )

        url = f"/api/v2/consortiums/{consortium.id}/stats/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Check actual field names from ConsortiumStatsSerializer
        assert "total_members" in response.data
        assert "total_contributions" in response.data

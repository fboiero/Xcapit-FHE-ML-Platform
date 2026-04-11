"""
Core module tests for Xcapit FHE-ML Platform.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from apps.core.models import APIKey, AuditLog, Company

User = get_user_model()


@pytest.mark.django_db
class TestHealthCheck:
    """Tests for health check endpoint."""

    def test_health_check(self, api_client):
        """Test health check returns success."""
        url = "/api/v2/health/"

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "healthy"
        assert "version" in response.data
        assert "timestamp" in response.data


@pytest.mark.django_db
class TestCompanyEndpoints:
    """Tests for company endpoints."""

    def test_get_my_company(self, auth_client, company):
        """Test getting user's company."""
        url = "/api/v2/companies/me/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == company.name

    def test_list_companies_only_own(self, auth_client, company, other_company):
        """Test listing companies only returns own company."""
        url = "/api/v2/companies/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        results = response.data.get("results", response.data)
        company_ids = [c["id"] for c in results]
        assert str(company.id) in company_ids
        assert str(other_company.id) not in company_ids

    def test_update_company(self, auth_client, company):
        """Test updating company."""
        url = f"/api/v2/companies/{company.id}/"
        data = {"name": "Updated Company Name"}

        response = auth_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        company.refresh_from_db()
        assert company.name == "Updated Company Name"


@pytest.mark.django_db
class TestUserEndpoints:
    """Tests for user endpoints."""

    def test_get_my_profile(self, auth_client, user):
        """Test getting own profile."""
        url = "/api/v2/users/me/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == user.email

    def test_update_profile(self, auth_client, user):
        """Test updating own profile."""
        url = "/api/v2/users/me/"
        data = {"first_name": "Updated"}

        response = auth_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.first_name == "Updated"

    def test_list_users_same_company(self, auth_client, user, other_user):
        """Test listing users only returns same company users."""
        url = "/api/v2/users/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        results = response.data.get("results", response.data)
        emails = [u["email"] for u in results]
        assert user.email in emails
        assert other_user.email not in emails


@pytest.mark.django_db
class TestAPIKeyEndpoints:
    """Tests for API key endpoints."""

    def test_create_api_key(self, auth_client, company):
        """Test creating an API key."""
        url = "/api/v2/api-keys/"
        data = {"name": "Test Key"}

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert "raw_key" in response.data
        assert APIKey.objects.filter(name="Test Key").exists()

    def test_list_api_keys(self, auth_client, company, user):
        """Test listing API keys."""
        # Create a key first
        APIKey.objects.create(
            company=company,
            name="Existing Key",
            key_hash="abc123def456789012345678901234567890123456789012345678901234",
        )

        url = "/api/v2/api-keys/"
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_revoke_api_key(self, auth_client, company, user):
        """Test revoking an API key."""
        api_key = APIKey.objects.create(
            company=company,
            name="To Revoke",
            key_hash="def456789012345678901234567890123456789012345678901234567890",
        )

        url = f"/api/v2/api-keys/{api_key.id}/revoke/"
        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        api_key.refresh_from_db()
        assert not api_key.is_active


@pytest.mark.django_db
class TestAuditLogEndpoints:
    """Tests for audit log endpoints."""

    def test_list_audit_logs(self, auth_client, company, user):
        """Test listing audit logs."""
        # Create an audit log
        AuditLog.objects.create(
            company=company,
            user=user,
            action="test_action",
            resource_type="test",
            resource_id=user.id,
        )

        url = "/api/v2/audit-logs/"
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        results = response.data.get("results", response.data)
        assert len(results) >= 1

    def test_filter_audit_logs_by_action(self, auth_client, company, user):
        """Test filtering audit logs by action."""
        AuditLog.objects.create(
            company=company,
            user=user,
            action="specific_action",
            resource_type="test",
            resource_id=user.id,
        )
        AuditLog.objects.create(
            company=company,
            user=user,
            action="other_action",
            resource_type="test",
            resource_id=user.id,
        )

        url = "/api/v2/audit-logs/?action=specific_action"
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        results = response.data.get("results", response.data)
        for log in results:
            assert log["action"] == "specific_action"

    def test_audit_logs_read_only(self, auth_client, company, user):
        """Test that audit logs cannot be modified."""
        log = AuditLog.objects.create(
            company=company,
            user=user,
            action="test_action",
            resource_type="test",
            resource_id=user.id,
        )

        # Try to update
        url = f"/api/v2/audit-logs/{log.id}/"
        response = auth_client.patch(url, {"action": "modified"})

        assert response.status_code in [
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_403_FORBIDDEN,
        ]

        # Try to delete
        response = auth_client.delete(url)

        assert response.status_code in [
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_403_FORBIDDEN,
        ]


@pytest.mark.django_db
class TestIsolation:
    """Tests for data isolation between companies."""

    def test_cannot_access_other_company_data(self, auth_client, other_company):
        """Test user cannot access another company's data."""
        url = f"/api/v2/companies/{other_company.id}/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_see_other_company_audit_logs(self, auth_client, other_company, other_user):
        """Test user cannot see another company's audit logs."""
        AuditLog.objects.create(
            company=other_company,
            user=other_user,
            action="secret_action",
            resource_type="test",
            resource_id=other_user.id,
        )

        url = "/api/v2/audit-logs/"
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        results = response.data.get("results", response.data)
        for log in results:
            assert log.get("company") != str(other_company.id)

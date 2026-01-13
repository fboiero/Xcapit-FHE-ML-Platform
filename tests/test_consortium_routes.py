"""Tests for consortium_routes.py API endpoints."""

import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

# Mock tenseal before importing sdk modules
sys.modules["tenseal"] = MagicMock()

from fastapi import FastAPI
from fastapi.testclient import TestClient

from sdk.api.consortium_routes import router, get_company_from_api_key


# ============ Test Fixtures ============


@pytest.fixture
def app():
    """Create FastAPI test app."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def mock_company():
    """Mock authenticated company."""
    return {"id": "company-123", "name": "Test Corp", "email": "test@example.com"}


@pytest.fixture
def client(app, mock_company):
    """Create test client with mocked auth."""
    app.dependency_overrides[get_company_from_api_key] = lambda: mock_company
    return TestClient(app)


@pytest.fixture
def mock_manager():
    """Create mock ConsortiumManager."""
    return MagicMock()


def make_request(client, mock_manager, method, url, **kwargs):
    """Helper to make requests with mocked ConsortiumManager."""
    with patch.dict(
        "sys.modules",
        {
            "sdk.api.consortium": MagicMock(
                ConsortiumManager=MagicMock(return_value=mock_manager)
            ),
        },
    ):
        # Reset the global manager
        import sdk.api.consortium_routes as routes_module
        routes_module._manager = mock_manager

        if method == "get":
            return client.get(url, **kwargs)
        elif method == "post":
            return client.post(url, **kwargs)
        elif method == "delete":
            return client.delete(url, **kwargs)


# ============ Company Endpoints Tests ============


class TestCreateCompany:
    """Tests for POST /consortiums/companies."""

    def test_create_company_success(self, app):
        """Test successful company creation."""
        client = TestClient(app)
        mock_manager = MagicMock()

        mock_company = MagicMock()
        mock_company.id = "company-new"
        mock_company.name = "New Company"
        mock_company.email = "new@example.com"
        mock_company.created_at = datetime(2024, 1, 1, 12, 0, 0)

        mock_manager.create_company.return_value = (mock_company, "api-key-12345")

        with patch.dict(
            "sys.modules",
            {
                "sdk.api.consortium": MagicMock(
                    ConsortiumManager=MagicMock(return_value=mock_manager)
                ),
            },
        ):
            import sdk.api.consortium_routes as routes_module
            routes_module._manager = mock_manager

            response = client.post(
                "/consortiums/companies",
                json={"name": "New Company", "email": "new@example.com"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["company"]["id"] == "company-new"
        assert data["company"]["name"] == "New Company"
        assert data["api_key"] == "api-key-12345"

    def test_create_company_duplicate_email(self, app):
        """Test company creation with duplicate email."""
        client = TestClient(app)
        mock_manager = MagicMock()
        mock_manager.create_company.side_effect = Exception("UNIQUE constraint failed")

        with patch.dict(
            "sys.modules",
            {
                "sdk.api.consortium": MagicMock(
                    ConsortiumManager=MagicMock(return_value=mock_manager)
                ),
            },
        ):
            import sdk.api.consortium_routes as routes_module
            routes_module._manager = mock_manager

            response = client.post(
                "/consortiums/companies",
                json={"name": "Test Company", "email": "duplicate@example.com"}
            )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_create_company_validation_error(self, app):
        """Test company creation with invalid data."""
        client = TestClient(app)

        response = client.post(
            "/consortiums/companies",
            json={"name": "A", "email": "test@example.com"}  # Name too short
        )

        assert response.status_code == 422


class TestGetCurrentCompany:
    """Tests for GET /consortiums/companies/me."""

    def test_get_current_company_success(self, client, mock_manager, mock_company):
        """Test getting current company info."""
        company_obj = MagicMock()
        company_obj.id = mock_company["id"]
        company_obj.name = mock_company["name"]
        company_obj.email = mock_company["email"]
        company_obj.created_at = datetime(2024, 1, 1, 12, 0, 0)

        mock_manager.get_company.return_value = company_obj

        response = make_request(client, mock_manager, "get", "/consortiums/companies/me")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == mock_company["id"]
        assert data["name"] == mock_company["name"]


# ============ Consortium Endpoints Tests ============


class TestCreateConsortium:
    """Tests for POST /consortiums."""

    def test_create_consortium_success(self, client, mock_manager):
        """Test successful consortium creation."""
        mock_consortium = MagicMock()
        mock_consortium.id = "consortium-123"
        mock_consortium.name = "Test Consortium"
        mock_consortium.description = "A test consortium for collaboration"
        mock_consortium.owner_id = "company-123"
        mock_consortium.status.value = "pending"
        mock_consortium.model_type = "linear_regression"
        mock_consortium.model_config = {}
        mock_consortium.created_at = datetime(2024, 1, 1, 12, 0, 0)
        mock_consortium.updated_at = datetime(2024, 1, 1, 12, 0, 0)

        mock_manager.create_consortium.return_value = mock_consortium

        response = make_request(
            client, mock_manager, "post", "/consortiums",
            json={
                "name": "Test Consortium",
                "description": "A test consortium for collaboration",
                "model_type": "linear_regression"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "consortium-123"
        assert data["name"] == "Test Consortium"
        assert data["model_type"] == "linear_regression"

    def test_create_consortium_invalid_model_type(self, client, mock_manager):
        """Test consortium creation with invalid model type."""
        response = make_request(
            client, mock_manager, "post", "/consortiums",
            json={
                "name": "Test Consortium",
                "description": "A test consortium for collaboration",
                "model_type": "invalid_model"
            }
        )

        assert response.status_code == 400
        assert "Invalid model_type" in response.json()["detail"]

    def test_create_consortium_validation_error(self, client, mock_manager):
        """Test consortium creation with validation errors."""
        response = make_request(
            client, mock_manager, "post", "/consortiums",
            json={
                "name": "T",  # Too short
                "description": "Short",  # Too short
                "model_type": "linear_regression"
            }
        )

        assert response.status_code == 422


class TestListConsortiums:
    """Tests for GET /consortiums."""

    def test_list_consortiums_success(self, client, mock_manager):
        """Test listing consortiums."""
        mock_consortium = MagicMock()
        mock_consortium.id = "consortium-123"
        mock_consortium.name = "Test Consortium"
        mock_consortium.description = "A test consortium"
        mock_consortium.owner_id = "company-123"
        mock_consortium.status.value = "active"
        mock_consortium.model_type = "linear_regression"
        mock_consortium.model_config = {}
        mock_consortium.created_at = datetime(2024, 1, 1, 12, 0, 0)
        mock_consortium.updated_at = datetime(2024, 1, 1, 12, 0, 0)
        mock_consortium.training_started_at = None
        mock_consortium.training_completed_at = None
        mock_consortium.model_id = None

        mock_manager.list_consortiums.return_value = [mock_consortium]

        response = make_request(client, mock_manager, "get", "/consortiums")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "consortium-123"

    def test_list_consortiums_with_status_filter(self, client, mock_manager):
        """Test listing consortiums with status filter."""
        mock_manager.list_consortiums.return_value = []

        response = make_request(
            client, mock_manager, "get", "/consortiums",
            params={"status": "active"}
        )

        assert response.status_code == 200

    def test_list_consortiums_empty(self, client, mock_manager):
        """Test listing consortiums when none exist."""
        mock_manager.list_consortiums.return_value = []

        response = make_request(client, mock_manager, "get", "/consortiums")

        assert response.status_code == 200
        assert response.json() == []


class TestGetConsortium:
    """Tests for GET /consortiums/{consortium_id}."""

    def test_get_consortium_success(self, client, mock_manager):
        """Test getting consortium details."""
        from sdk.api.consortium import MemberStatus

        mock_membership = MagicMock()
        mock_membership.status = MemberStatus.ACTIVE
        mock_manager.get_membership.return_value = mock_membership

        mock_consortium = MagicMock()
        mock_consortium.id = "consortium-123"
        mock_consortium.name = "Test Consortium"
        mock_consortium.description = "A test consortium"
        mock_consortium.owner_id = "company-123"
        mock_consortium.status.value = "active"
        mock_consortium.model_type = "linear_regression"
        mock_consortium.model_config = {}
        mock_consortium.created_at = datetime(2024, 1, 1, 12, 0, 0)
        mock_consortium.updated_at = datetime(2024, 1, 1, 12, 0, 0)
        mock_consortium.training_started_at = None
        mock_consortium.training_completed_at = None
        mock_consortium.model_id = None

        mock_manager.get_consortium.return_value = mock_consortium
        mock_manager.get_members.return_value = []
        mock_manager.get_consortium_data_summary.return_value = {
            "companies_contributed": 1,
            "total_records": 100,
            "feature_count": 10
        }

        response = make_request(
            client, mock_manager, "get", "/consortiums/consortium-123"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "consortium-123"
        assert "members" in data
        assert "data_summary" in data

    def test_get_consortium_not_member(self, client, mock_manager):
        """Test getting consortium when not a member."""
        mock_manager.get_membership.return_value = None

        response = make_request(
            client, mock_manager, "get", "/consortiums/consortium-123"
        )

        assert response.status_code == 403
        assert "not a member" in response.json()["detail"]

    def test_get_consortium_not_found(self, client, mock_manager):
        """Test getting non-existent consortium."""
        from sdk.api.consortium import MemberStatus

        mock_membership = MagicMock()
        mock_membership.status = MemberStatus.ACTIVE
        mock_manager.get_membership.return_value = mock_membership
        mock_manager.get_consortium.return_value = None

        response = make_request(
            client, mock_manager, "get", "/consortiums/nonexistent"
        )

        assert response.status_code == 404


class TestGetConsortiumStats:
    """Tests for GET /consortiums/{consortium_id}/stats."""

    def test_get_consortium_stats_success(self, client, mock_manager):
        """Test getting consortium statistics."""
        from sdk.api.consortium import MemberStatus

        mock_membership = MagicMock()
        mock_membership.status = MemberStatus.ACTIVE
        mock_manager.get_membership.return_value = mock_membership

        mock_consortium = MagicMock()
        mock_consortium.id = "consortium-123"
        mock_consortium.name = "Test Consortium"
        mock_consortium.status.value = "active"
        mock_manager.get_consortium.return_value = mock_consortium

        mock_manager.get_members.return_value = [{"status": "active"}]
        mock_manager.get_consortium_data_summary.return_value = {
            "companies_contributed": 2,
            "total_records": 500,
            "feature_count": 20
        }

        response = make_request(
            client, mock_manager, "get", "/consortiums/consortium-123/stats"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["consortium_id"] == "consortium-123"
        assert data["ready_for_training"] is True  # 2 companies contributed

    def test_get_consortium_stats_not_ready(self, client, mock_manager):
        """Test consortium not ready for training."""
        from sdk.api.consortium import MemberStatus

        mock_membership = MagicMock()
        mock_membership.status = MemberStatus.ACTIVE
        mock_manager.get_membership.return_value = mock_membership

        mock_consortium = MagicMock()
        mock_consortium.id = "consortium-123"
        mock_consortium.name = "Test Consortium"
        mock_consortium.status.value = "active"
        mock_manager.get_consortium.return_value = mock_consortium

        mock_manager.get_members.return_value = [{"status": "active"}]
        mock_manager.get_consortium_data_summary.return_value = {
            "companies_contributed": 1,  # Only 1 company
            "total_records": 100,
            "feature_count": 10
        }

        response = make_request(
            client, mock_manager, "get", "/consortiums/consortium-123/stats"
        )

        assert response.status_code == 200
        assert response.json()["ready_for_training"] is False


# ============ Invitation Endpoints Tests ============


class TestInviteToConsortium:
    """Tests for POST /consortiums/{consortium_id}/invite."""

    def test_invite_success(self, client, mock_manager):
        """Test successful invitation."""
        from sdk.api.consortium import MemberRole, MemberStatus

        mock_membership = MagicMock()
        mock_membership.status = MemberStatus.ACTIVE
        mock_membership.role = MemberRole.OWNER
        mock_manager.get_membership.return_value = mock_membership

        mock_invitation = MagicMock()
        mock_invitation.id = "invite-123"
        mock_invitation.consortium_id = "consortium-123"
        mock_invitation.invite_email = "invitee@example.com"
        mock_invitation.invite_code = "ABC123"
        mock_invitation.role.value = "contributor"
        mock_invitation.status.value = "pending"
        mock_invitation.expires_at = datetime(2024, 1, 8, 12, 0, 0)

        mock_manager.create_invitation.return_value = mock_invitation

        response = make_request(
            client, mock_manager, "post", "/consortiums/consortium-123/invite",
            json={"email": "invitee@example.com", "role": "contributor"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["invite_code"] == "ABC123"
        assert "invite_url" in data

    def test_invite_not_authorized(self, client, mock_manager):
        """Test invitation by non-admin."""
        from sdk.api.consortium import MemberRole, MemberStatus

        mock_membership = MagicMock()
        mock_membership.status = MemberStatus.ACTIVE
        mock_membership.role = MemberRole.CONTRIBUTOR  # Not owner/admin
        mock_manager.get_membership.return_value = mock_membership

        response = make_request(
            client, mock_manager, "post", "/consortiums/consortium-123/invite",
            json={"email": "invitee@example.com", "role": "contributor"}
        )

        assert response.status_code == 403
        assert "Only owners and admins" in response.json()["detail"]

    def test_invite_invalid_role(self, client, mock_manager):
        """Test invitation with invalid role."""
        from sdk.api.consortium import MemberRole, MemberStatus

        mock_membership = MagicMock()
        mock_membership.status = MemberStatus.ACTIVE
        mock_membership.role = MemberRole.OWNER
        mock_manager.get_membership.return_value = mock_membership

        response = make_request(
            client, mock_manager, "post", "/consortiums/consortium-123/invite",
            json={"email": "invitee@example.com", "role": "invalid_role"}
        )

        assert response.status_code == 400
        assert "Invalid role" in response.json()["detail"]


class TestListInvitations:
    """Tests for GET /consortiums/{consortium_id}/invitations."""

    def test_list_invitations_success(self, client, mock_manager):
        """Test listing invitations."""
        from sdk.api.consortium import MemberRole, MemberStatus

        mock_membership = MagicMock()
        mock_membership.status = MemberStatus.ACTIVE
        mock_membership.role = MemberRole.ADMIN
        mock_manager.get_membership.return_value = mock_membership

        mock_invitation = MagicMock()
        mock_invitation.id = "invite-123"
        mock_invitation.consortium_id = "consortium-123"
        mock_invitation.invite_email = "invitee@example.com"
        mock_invitation.invite_code = "ABC123"
        mock_invitation.role.value = "contributor"
        mock_invitation.status.value = "pending"
        mock_invitation.expires_at = datetime(2024, 1, 8, 12, 0, 0)

        mock_manager.list_invitations.return_value = [mock_invitation]

        response = make_request(
            client, mock_manager, "get", "/consortiums/consortium-123/invitations"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["invite_code"] == "ABC123"

    def test_list_invitations_not_authorized(self, client, mock_manager):
        """Test listing invitations by non-admin."""
        from sdk.api.consortium import MemberRole, MemberStatus

        mock_membership = MagicMock()
        mock_membership.status = MemberStatus.ACTIVE
        mock_membership.role = MemberRole.VIEWER
        mock_manager.get_membership.return_value = mock_membership

        response = make_request(
            client, mock_manager, "get", "/consortiums/consortium-123/invitations"
        )

        assert response.status_code == 403


class TestAcceptInvitation:
    """Tests for POST /consortiums/join."""

    def test_accept_invitation_success(self, client, mock_manager, mock_company):
        """Test accepting an invitation."""
        mock_membership = MagicMock()
        mock_membership.id = "membership-123"
        mock_membership.company_id = mock_company["id"]
        mock_membership.role.value = "contributor"
        mock_membership.status.value = "active"
        mock_membership.joined_at = datetime(2024, 1, 1, 12, 0, 0)
        mock_membership.data_uploaded = False
        mock_membership.data_record_count = 0

        mock_manager.accept_invitation.return_value = mock_membership

        company_obj = MagicMock()
        company_obj.name = mock_company["name"]
        company_obj.email = mock_company["email"]
        mock_manager.get_company.return_value = company_obj

        response = make_request(
            client, mock_manager, "post", "/consortiums/join",
            json={"invite_code": "ABC123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["membership_id"] == "membership-123"

    def test_accept_invitation_invalid_code(self, client, mock_manager):
        """Test accepting invitation with invalid code."""
        mock_manager.accept_invitation.return_value = None

        response = make_request(
            client, mock_manager, "post", "/consortiums/join",
            json={"invite_code": "INVALID"}
        )

        assert response.status_code == 400
        assert "Invalid or expired" in response.json()["detail"]


# ============ Member Endpoints Tests ============


class TestListMembers:
    """Tests for GET /consortiums/{consortium_id}/members."""

    def test_list_members_success(self, client, mock_manager):
        """Test listing consortium members."""
        from sdk.api.consortium import MemberStatus

        mock_membership = MagicMock()
        mock_membership.status = MemberStatus.ACTIVE
        mock_manager.get_membership.return_value = mock_membership

        mock_manager.get_members.return_value = [
            {
                "membership_id": "mem-1",
                "company_id": "company-1",
                "company_name": "Company One",
                "company_email": "one@example.com",
                "role": "owner",
                "status": "active",
                "joined_at": datetime(2024, 1, 1, 12, 0, 0),
                "data_uploaded": True,
                "data_record_count": 100
            }
        ]

        response = make_request(
            client, mock_manager, "get", "/consortiums/consortium-123/members"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["company_name"] == "Company One"

    def test_list_members_not_member(self, client, mock_manager):
        """Test listing members when not a member."""
        mock_manager.get_membership.return_value = None

        response = make_request(
            client, mock_manager, "get", "/consortiums/consortium-123/members"
        )

        assert response.status_code == 403


# ============ Status Endpoints Tests ============


class TestActivateConsortium:
    """Tests for POST /consortiums/{consortium_id}/activate."""

    def test_activate_consortium_success(self, client, mock_manager):
        """Test activating a consortium."""
        from sdk.api.consortium import MemberRole

        mock_membership = MagicMock()
        mock_membership.role = MemberRole.OWNER
        mock_manager.get_membership.return_value = mock_membership

        mock_consortium = MagicMock()
        mock_consortium.id = "consortium-123"
        mock_consortium.name = "Test Consortium"
        mock_consortium.description = "A test consortium"
        mock_consortium.owner_id = "company-123"
        mock_consortium.status.value = "active"
        mock_consortium.model_type = "linear_regression"
        mock_consortium.model_config = {}
        mock_consortium.created_at = datetime(2024, 1, 1, 12, 0, 0)
        mock_consortium.updated_at = datetime(2024, 1, 1, 12, 0, 0)

        mock_manager.update_consortium_status.return_value = mock_consortium

        response = make_request(
            client, mock_manager, "post", "/consortiums/consortium-123/activate"
        )

        assert response.status_code == 200
        assert response.json()["status"] == "active"

    def test_activate_consortium_not_owner(self, client, mock_manager):
        """Test activating consortium by non-owner."""
        from sdk.api.consortium import MemberRole

        mock_membership = MagicMock()
        mock_membership.role = MemberRole.ADMIN  # Not owner
        mock_manager.get_membership.return_value = mock_membership

        response = make_request(
            client, mock_manager, "post", "/consortiums/consortium-123/activate"
        )

        assert response.status_code == 403
        assert "Only the owner" in response.json()["detail"]

    def test_activate_consortium_not_found(self, client, mock_manager):
        """Test activating non-existent consortium."""
        from sdk.api.consortium import MemberRole

        mock_membership = MagicMock()
        mock_membership.role = MemberRole.OWNER
        mock_manager.get_membership.return_value = mock_membership
        mock_manager.update_consortium_status.return_value = None

        response = make_request(
            client, mock_manager, "post", "/consortiums/consortium-123/activate"
        )

        assert response.status_code == 404


# ============ Data Upload Endpoints Tests ============


class TestUploadData:
    """Tests for POST /consortiums/{consortium_id}/data."""

    def test_upload_data_success(self, client, mock_manager):
        """Test uploading encrypted data."""
        from sdk.api.consortium import MemberRole, MemberStatus, ConsortiumStatus

        mock_membership = MagicMock()
        mock_membership.status = MemberStatus.ACTIVE
        mock_membership.role = MemberRole.CONTRIBUTOR
        mock_manager.get_membership.return_value = mock_membership

        mock_consortium = MagicMock()
        mock_consortium.status = ConsortiumStatus.ACTIVE
        mock_manager.get_consortium.return_value = mock_consortium

        with patch("os.makedirs"):
            response = make_request(
                client, mock_manager, "post", "/consortiums/consortium-123/data"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["encrypted"] is True
        assert "contribution_id" in data or "id" in data

    def test_upload_data_viewer_forbidden(self, client, mock_manager):
        """Test viewer cannot upload data."""
        from sdk.api.consortium import MemberRole, MemberStatus

        mock_membership = MagicMock()
        mock_membership.status = MemberStatus.ACTIVE
        mock_membership.role = MemberRole.VIEWER
        mock_manager.get_membership.return_value = mock_membership

        response = make_request(
            client, mock_manager, "post", "/consortiums/consortium-123/data"
        )

        assert response.status_code == 403
        assert "Viewers cannot upload" in response.json()["detail"]

    def test_upload_data_consortium_not_active(self, client, mock_manager):
        """Test upload when consortium is not active."""
        from sdk.api.consortium import MemberRole, MemberStatus, ConsortiumStatus

        mock_membership = MagicMock()
        mock_membership.status = MemberStatus.ACTIVE
        mock_membership.role = MemberRole.CONTRIBUTOR
        mock_manager.get_membership.return_value = mock_membership

        mock_consortium = MagicMock()
        mock_consortium.status = ConsortiumStatus.DRAFT  # Not active
        mock_manager.get_consortium.return_value = mock_consortium

        response = make_request(
            client, mock_manager, "post", "/consortiums/consortium-123/data"
        )

        assert response.status_code == 400
        assert "must be active" in response.json()["detail"]


class TestGetConsortiumSummary:
    """Tests for GET /consortiums/{consortium_id}/summary."""

    def test_get_summary_success(self, client, mock_manager):
        """Test getting consortium summary."""
        from sdk.api.consortium import MemberStatus, ConsortiumStatus

        mock_membership = MagicMock()
        mock_membership.status = MemberStatus.ACTIVE
        mock_manager.get_membership.return_value = mock_membership

        mock_consortium = MagicMock()
        mock_consortium.status = ConsortiumStatus.ACTIVE
        mock_manager.get_consortium.return_value = mock_consortium

        mock_manager.get_consortium_stats.return_value = {
            "total_members": 3,
            "total_contributions": 5,
            "total_records": 500,
            "contributors_count": 2
        }

        response = make_request(
            client, mock_manager, "get", "/consortiums/consortium-123/summary"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_members"] == 3
        assert data["total_records"] == 500


# ============ Training Endpoints Tests ============


class TestStartTraining:
    """Tests for POST /consortiums/{consortium_id}/train."""

    def test_start_training_success(self, client, mock_manager):
        """Test starting model training."""
        from sdk.api.consortium import MemberRole, ConsortiumStatus

        mock_membership = MagicMock()
        mock_membership.role = MemberRole.OWNER
        mock_manager.get_membership.return_value = mock_membership

        mock_consortium = MagicMock()
        mock_consortium.status = ConsortiumStatus.ACTIVE
        mock_manager.get_consortium.return_value = mock_consortium

        mock_manager.get_consortium_stats.return_value = {
            "total_contributions": 2
        }

        response = make_request(
            client, mock_manager, "post", "/consortiums/consortium-123/train"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["progress"] == 0

    def test_start_training_not_authorized(self, client, mock_manager):
        """Test training start by contributor."""
        from sdk.api.consortium import MemberRole

        mock_membership = MagicMock()
        mock_membership.role = MemberRole.CONTRIBUTOR
        mock_manager.get_membership.return_value = mock_membership

        response = make_request(
            client, mock_manager, "post", "/consortiums/consortium-123/train"
        )

        assert response.status_code == 403
        assert "Only owners and admins" in response.json()["detail"]

    def test_start_training_already_training(self, client, mock_manager):
        """Test starting training when already in progress."""
        from sdk.api.consortium import MemberRole, ConsortiumStatus

        mock_membership = MagicMock()
        mock_membership.role = MemberRole.OWNER
        mock_manager.get_membership.return_value = mock_membership

        mock_consortium = MagicMock()
        mock_consortium.status = ConsortiumStatus.TRAINING
        mock_manager.get_consortium.return_value = mock_consortium

        response = make_request(
            client, mock_manager, "post", "/consortiums/consortium-123/train"
        )

        assert response.status_code == 400
        assert "already in progress" in response.json()["detail"]

    def test_start_training_no_data(self, client, mock_manager):
        """Test starting training without data."""
        from sdk.api.consortium import MemberRole, ConsortiumStatus

        mock_membership = MagicMock()
        mock_membership.role = MemberRole.OWNER
        mock_manager.get_membership.return_value = mock_membership

        mock_consortium = MagicMock()
        mock_consortium.status = ConsortiumStatus.ACTIVE
        mock_manager.get_consortium.return_value = mock_consortium

        mock_manager.get_consortium_stats.return_value = {
            "total_contributions": 0
        }

        response = make_request(
            client, mock_manager, "post", "/consortiums/consortium-123/train"
        )

        assert response.status_code == 400
        assert "No data has been uploaded" in response.json()["detail"]


class TestGetTrainingStatus:
    """Tests for GET /consortiums/{consortium_id}/training-status."""

    def test_get_training_status_success(self, client, mock_manager):
        """Test getting training status."""
        from sdk.api.consortium import MemberStatus

        mock_membership = MagicMock()
        mock_membership.status = MemberStatus.ACTIVE
        mock_manager.get_membership.return_value = mock_membership

        response = make_request(
            client, mock_manager, "get", "/consortiums/consortium-123/training-status"
        )

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "progress" in data

    def test_get_training_status_not_started(self, client, mock_manager):
        """Test getting status when training not started."""
        from sdk.api.consortium import MemberStatus

        mock_membership = MagicMock()
        mock_membership.status = MemberStatus.ACTIVE
        mock_manager.get_membership.return_value = mock_membership

        response = make_request(
            client, mock_manager, "get", "/consortiums/new-consortium/training-status"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_started"


# ============ Results Endpoints Tests ============


class TestDownloadResults:
    """Tests for GET /consortiums/{consortium_id}/results."""

    def test_download_results_success(self, client, mock_manager):
        """Test downloading training results."""
        from sdk.api.consortium import MemberStatus, ConsortiumStatus

        mock_membership = MagicMock()
        mock_membership.status = MemberStatus.ACTIVE
        mock_manager.get_membership.return_value = mock_membership

        mock_consortium = MagicMock()
        mock_consortium.status = ConsortiumStatus.COMPLETED
        mock_consortium.model_type = "linear_regression"
        mock_manager.get_consortium.return_value = mock_consortium

        response = make_request(
            client, mock_manager, "get", "/consortiums/consortium-123/results"
        )

        assert response.status_code == 200
        data = response.json()
        assert "model_parameters" in data
        assert "metrics" in data
        assert "privacy_guarantees" in data

    def test_download_results_training_not_complete(self, client, mock_manager):
        """Test downloading results when training not complete."""
        from sdk.api.consortium import MemberStatus, ConsortiumStatus

        mock_membership = MagicMock()
        mock_membership.status = MemberStatus.ACTIVE
        mock_manager.get_membership.return_value = mock_membership

        mock_consortium = MagicMock()
        mock_consortium.status = ConsortiumStatus.TRAINING  # Still training
        mock_manager.get_consortium.return_value = mock_consortium

        response = make_request(
            client, mock_manager, "get", "/consortiums/consortium-123/results"
        )

        assert response.status_code == 400
        assert "must be completed" in response.json()["detail"]

    def test_download_results_not_member(self, client, mock_manager):
        """Test downloading results when not a member."""
        mock_manager.get_membership.return_value = None

        response = make_request(
            client, mock_manager, "get", "/consortiums/consortium-123/results"
        )

        assert response.status_code == 403


# ============ Validation Tests ============


class TestConsortiumValidation:
    """Tests for request validation."""

    def test_consortium_name_min_length(self, client, mock_manager):
        """Test consortium name minimum length validation."""
        response = make_request(
            client, mock_manager, "post", "/consortiums",
            json={
                "name": "A",
                "description": "Valid description for the test",
                "model_type": "linear_regression"
            }
        )

        assert response.status_code == 422

    def test_consortium_description_min_length(self, client, mock_manager):
        """Test consortium description minimum length validation."""
        response = make_request(
            client, mock_manager, "post", "/consortiums",
            json={
                "name": "Valid Name",
                "description": "Short",
                "model_type": "linear_regression"
            }
        )

        assert response.status_code == 422

    def test_company_name_max_length(self, app):
        """Test company name maximum length validation."""
        client = TestClient(app)

        response = client.post(
            "/consortiums/companies",
            json={
                "name": "A" * 101,  # Exceeds 100 char limit
                "email": "test@example.com"
            }
        )

        assert response.status_code == 422


class TestAuthenticationErrors:
    """Tests for authentication error handling."""

    def test_missing_api_key(self, app):
        """Test request without API key."""
        client = TestClient(app)

        response = client.get("/consortiums")

        assert response.status_code == 422  # Missing required header

    def test_invalid_api_key(self, app):
        """Test request with invalid API key."""
        client = TestClient(app)
        mock_manager = MagicMock()
        mock_manager.get_company_by_api_key.return_value = None

        with patch.dict(
            "sys.modules",
            {
                "sdk.api.consortium": MagicMock(
                    ConsortiumManager=MagicMock(return_value=mock_manager)
                ),
            },
        ):
            import sdk.api.consortium_routes as routes_module
            routes_module._manager = mock_manager

            response = client.get(
                "/consortiums",
                headers={"X-API-Key": "invalid-key"}
            )

        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]

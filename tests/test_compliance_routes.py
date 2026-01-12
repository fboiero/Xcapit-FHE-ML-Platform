"""Tests for compliance API routes."""

import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

# Mock tenseal before importing sdk modules
sys.modules["tenseal"] = MagicMock()

from fastapi import FastAPI
from fastapi.testclient import TestClient

from sdk.api.compliance_routes import router
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


# ============ Frameworks Tests ============


class TestListFrameworks:
    """Tests for GET /compliance/frameworks endpoint."""

    def test_list_frameworks_success(self, client, mock_manager):
        """Test listing all compliance frameworks."""
        mock_manager.get_compliance_frameworks.return_value = [
            {
                "id": "framework_gdpr",
                "name": "GDPR",
                "version": "2018",
                "description": "General Data Protection Regulation",
                "region": "EU",
                "industry": None,
                "controls_count": 50,
            },
            {
                "id": "framework_hipaa",
                "name": "HIPAA",
                "version": "1996",
                "description": "Health Insurance Portability and Accountability Act",
                "region": "US",
                "industry": "Healthcare",
                "controls_count": 45,
            },
        ]

        response = make_request(client, mock_manager, "get", "/compliance/frameworks")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == "framework_gdpr"
        assert data[1]["id"] == "framework_hipaa"

    def test_list_frameworks_empty(self, client, mock_manager):
        """Test listing frameworks when none exist."""
        mock_manager.get_compliance_frameworks.return_value = []

        response = make_request(client, mock_manager, "get", "/compliance/frameworks")

        assert response.status_code == 200
        assert response.json() == []


class TestGetFramework:
    """Tests for GET /compliance/frameworks/{framework_id} endpoint."""

    def test_get_framework_success(self, client, mock_manager):
        """Test getting a specific framework."""
        mock_manager.get_compliance_framework.return_value = {
            "id": "framework_gdpr",
            "name": "GDPR",
            "version": "2018",
            "description": "General Data Protection Regulation",
            "region": "EU",
            "industry": None,
            "controls_count": 50,
        }

        response = make_request(
            client, mock_manager, "get", "/compliance/frameworks/framework_gdpr"
        )

        assert response.status_code == 200
        assert response.json()["id"] == "framework_gdpr"

    def test_get_framework_not_found(self, client, mock_manager):
        """Test getting non-existent framework."""
        mock_manager.get_compliance_framework.return_value = None

        response = make_request(
            client, mock_manager, "get", "/compliance/frameworks/nonexistent"
        )

        assert response.status_code == 404


class TestEnableFramework:
    """Tests for POST /compliance/frameworks/enable endpoint."""

    def test_enable_framework_success(self, client, mock_manager):
        """Test enabling a framework for consortium."""
        mock_consortium = MagicMock()
        mock_consortium.owner_id = "company_001"
        mock_manager.get_consortium.return_value = mock_consortium
        mock_manager.enable_compliance_framework.return_value = {
            "status": "enabled",
            "framework_id": "framework_gdpr",
        }

        response = make_request(
            client,
            mock_manager,
            "post",
            "/compliance/frameworks/enable",
            json={"consortium_id": "cons_001", "framework_id": "framework_gdpr"},
        )

        assert response.status_code == 200
        mock_manager.enable_compliance_framework.assert_called_once()
        mock_manager.record_audit_event.assert_called_once()

    def test_enable_framework_consortium_not_found(self, client, mock_manager):
        """Test enabling framework for non-existent consortium."""
        mock_manager.get_consortium.return_value = None

        response = make_request(
            client,
            mock_manager,
            "post",
            "/compliance/frameworks/enable",
            json={"consortium_id": "nonexistent", "framework_id": "framework_gdpr"},
        )

        assert response.status_code == 404

    def test_enable_framework_not_owner(self, client, mock_manager):
        """Test enabling framework when not the owner."""
        mock_consortium = MagicMock()
        mock_consortium.owner_id = "other_company"
        mock_manager.get_consortium.return_value = mock_consortium

        response = make_request(
            client,
            mock_manager,
            "post",
            "/compliance/frameworks/enable",
            json={"consortium_id": "cons_001", "framework_id": "framework_hipaa"},
        )

        assert response.status_code == 403


# ============ Settings Tests ============


class TestGetComplianceSettings:
    """Tests for GET /compliance/settings/{consortium_id} endpoint."""

    def test_get_settings_success(self, client, mock_manager):
        """Test getting compliance settings."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.get_consortium_compliance_settings.return_value = {
            "consortium_id": "cons_001",
            "enabled_frameworks": ["framework_gdpr", "framework_hipaa"],
            "auto_check_interval": 24,
            "notification_emails": ["admin@test.com"],
            "last_check_at": datetime.now().isoformat(),
            "next_check_at": (datetime.now() + timedelta(hours=24)).isoformat(),
        }

        response = make_request(
            client, mock_manager, "get", "/compliance/settings/cons_001"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["consortium_id"] == "cons_001"
        assert len(data["enabled_frameworks"]) == 2

    def test_get_settings_not_member(self, client, mock_manager):
        """Test getting settings when not a member."""
        mock_manager.get_membership.return_value = None

        response = make_request(
            client, mock_manager, "get", "/compliance/settings/cons_001"
        )

        assert response.status_code == 403


# ============ Checks Tests ============


class TestRecordCheck:
    """Tests for POST /compliance/checks endpoint."""

    def test_record_check_success(self, client, mock_manager):
        """Test recording a compliance check."""
        mock_membership = MagicMock()
        mock_membership.status.value = "active"
        mock_manager.get_membership.return_value = mock_membership
        mock_manager.record_compliance_check.return_value = "check_001"

        response = make_request(
            client,
            mock_manager,
            "post",
            "/compliance/checks",
            json={
                "consortium_id": "cons_001",
                "framework_id": "framework_gdpr",
                "control_id": "gdpr_encryption",
                "status": "passed",
                "result": "All data is encrypted at rest and in transit",
                "evidence": {"test_date": "2024-01-15"},
                "notes": "Verified encryption settings",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "check_001"
        assert data["status"] == "passed"

    def test_record_check_not_member(self, client, mock_manager):
        """Test recording check when not a member."""
        mock_manager.get_membership.return_value = None

        response = make_request(
            client,
            mock_manager,
            "post",
            "/compliance/checks",
            json={
                "consortium_id": "cons_001",
                "framework_id": "framework_gdpr",
                "control_id": "gdpr_encryption",
                "status": "passed",
                "result": "Check passed",
            },
        )

        assert response.status_code == 403

    def test_record_check_inactive_member(self, client, mock_manager):
        """Test recording check when member is inactive."""
        mock_membership = MagicMock()
        mock_membership.status.value = "suspended"
        mock_manager.get_membership.return_value = mock_membership

        response = make_request(
            client,
            mock_manager,
            "post",
            "/compliance/checks",
            json={
                "consortium_id": "cons_001",
                "framework_id": "framework_hipaa",
                "control_id": "hipaa_access",
                "status": "pending",
                "result": "Pending review",
            },
        )

        assert response.status_code == 403


class TestGetChecks:
    """Tests for GET /compliance/checks/{consortium_id} endpoint."""

    def test_get_checks_success(self, client, mock_manager):
        """Test getting compliance checks."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.get_compliance_checks.return_value = [
            {
                "id": "check_001",
                "consortium_id": "cons_001",
                "framework_id": "framework_gdpr",
                "control_id": "gdpr_encryption",
                "status": "passed",
                "result": "Encryption verified",
                "evidence": {},
                "checked_at": datetime.now().isoformat(),
                "checked_by": "company_001",
                "notes": None,
            },
        ]

        response = make_request(
            client, mock_manager, "get", "/compliance/checks/cons_001"
        )

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_checks_with_filters(self, client, mock_manager):
        """Test getting checks with filters."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.get_compliance_checks.return_value = []

        response = make_request(
            client,
            mock_manager,
            "get",
            "/compliance/checks/cons_001",
            params={"framework_id": "framework_gdpr", "check_status": "passed"},
        )

        assert response.status_code == 200
        mock_manager.get_compliance_checks.assert_called_once()

    def test_get_checks_not_member(self, client, mock_manager):
        """Test getting checks when not a member."""
        mock_manager.get_membership.return_value = None

        response = make_request(
            client, mock_manager, "get", "/compliance/checks/cons_001"
        )

        assert response.status_code == 403


class TestRunAutomatedChecks:
    """Tests for POST /compliance/checks/run endpoint."""

    def test_run_checks_success(self, client, mock_manager):
        """Test running automated compliance checks."""
        mock_consortium = MagicMock()
        mock_manager.get_consortium.return_value = mock_consortium
        mock_membership = MagicMock()
        mock_membership.role.value = "admin"
        mock_manager.get_membership.return_value = mock_membership

        response = make_request(
            client,
            mock_manager,
            "post",
            "/compliance/checks/run",
            json={"consortium_id": "cons_001", "framework_id": "framework_gdpr"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["consortium_id"] == "cons_001"
        assert data["checks_run"] == 3
        assert data["checks_passed"] == 3

    def test_run_checks_as_owner(self, client, mock_manager):
        """Test running checks as owner."""
        mock_consortium = MagicMock()
        mock_manager.get_consortium.return_value = mock_consortium
        mock_membership = MagicMock()
        mock_membership.role.value = "owner"
        mock_manager.get_membership.return_value = mock_membership

        response = make_request(
            client,
            mock_manager,
            "post",
            "/compliance/checks/run",
            json={"consortium_id": "cons_001", "framework_id": "framework_hipaa"},
        )

        assert response.status_code == 200

    def test_run_checks_consortium_not_found(self, client, mock_manager):
        """Test running checks for non-existent consortium."""
        mock_manager.get_consortium.return_value = None

        response = make_request(
            client,
            mock_manager,
            "post",
            "/compliance/checks/run",
            json={"consortium_id": "nonexistent", "framework_id": "framework_gdpr"},
        )

        assert response.status_code == 404

    def test_run_checks_not_admin(self, client, mock_manager):
        """Test running checks when not admin or owner."""
        mock_consortium = MagicMock()
        mock_manager.get_consortium.return_value = mock_consortium
        mock_membership = MagicMock()
        mock_membership.role.value = "member"
        mock_manager.get_membership.return_value = mock_membership

        response = make_request(
            client,
            mock_manager,
            "post",
            "/compliance/checks/run",
            json={"consortium_id": "cons_001", "framework_id": "framework_gdpr"},
        )

        assert response.status_code == 403


# ============ Reports Tests ============


class TestGenerateReport:
    """Tests for POST /compliance/reports endpoint."""

    def test_generate_report_success(self, client, mock_manager):
        """Test generating a compliance report."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.generate_compliance_report.return_value = {
            "id": "report_001",
            "consortium_id": "cons_001",
            "framework_id": "framework_gdpr",
            "framework_name": "GDPR",
            "overall_score": 85.5,
            "passed_controls": 42,
            "failed_controls": 5,
            "pending_controls": 3,
            "total_controls": 50,
            "status": "partial",
            "generated_at": datetime.now().isoformat(),
            "valid_until": (datetime.now() + timedelta(days=30)).isoformat(),
        }

        response = make_request(
            client,
            mock_manager,
            "post",
            "/compliance/reports",
            json={"consortium_id": "cons_001", "framework_id": "framework_gdpr"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "report_001"
        assert data["overall_score"] == 85.5
        mock_manager.record_audit_event.assert_called_once()

    def test_generate_report_not_member(self, client, mock_manager):
        """Test generating report when not a member."""
        mock_manager.get_membership.return_value = None

        response = make_request(
            client,
            mock_manager,
            "post",
            "/compliance/reports",
            json={"consortium_id": "cons_001", "framework_id": "framework_gdpr"},
        )

        assert response.status_code == 403


class TestGetReports:
    """Tests for GET /compliance/reports/{consortium_id} endpoint."""

    def test_get_reports_success(self, client, mock_manager):
        """Test getting compliance reports."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.get_compliance_reports.return_value = [
            {
                "id": "report_001",
                "consortium_id": "cons_001",
                "framework_id": "framework_gdpr",
                "framework_name": "GDPR",
                "overall_score": 90.0,
                "passed_controls": 45,
                "failed_controls": 2,
                "pending_controls": 3,
                "total_controls": 50,
                "status": "compliant",
                "generated_at": datetime.now().isoformat(),
                "valid_until": None,
            },
        ]

        response = make_request(
            client, mock_manager, "get", "/compliance/reports/cons_001"
        )

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_reports_with_filter(self, client, mock_manager):
        """Test getting reports with framework filter."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.get_compliance_reports.return_value = []

        response = make_request(
            client,
            mock_manager,
            "get",
            "/compliance/reports/cons_001",
            params={"framework_id": "framework_hipaa"},
        )

        assert response.status_code == 200

    def test_get_reports_not_member(self, client, mock_manager):
        """Test getting reports when not a member."""
        mock_manager.get_membership.return_value = None

        response = make_request(
            client, mock_manager, "get", "/compliance/reports/cons_001"
        )

        assert response.status_code == 403


# ============ Attestations Tests ============


class TestCreateAttestation:
    """Tests for POST /compliance/attestations endpoint."""

    def test_create_attestation_success(self, client, mock_manager):
        """Test creating an attestation."""
        mock_membership = MagicMock()
        mock_membership.status.value = "active"
        mock_manager.get_membership.return_value = mock_membership
        mock_manager.create_attestation.return_value = "attest_001"

        response = make_request(
            client,
            mock_manager,
            "post",
            "/compliance/attestations",
            json={
                "consortium_id": "cons_001",
                "framework_id": "framework_gdpr",
                "statement": "I attest that all data processing complies with GDPR requirements",
                "control_id": "gdpr_consent",
                "attester_role": "Data Protection Officer",
                "attestation_type": "manual",
                "evidence_urls": ["https://example.com/evidence1"],
                "valid_days": 365,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "attest_001"
        assert data["attester_role"] == "Data Protection Officer"
        assert data["revoked"] is False

    def test_create_attestation_minimal(self, client, mock_manager):
        """Test creating attestation with minimal data."""
        mock_membership = MagicMock()
        mock_membership.status.value = "active"
        mock_manager.get_membership.return_value = mock_membership
        mock_manager.create_attestation.return_value = "attest_002"

        response = make_request(
            client,
            mock_manager,
            "post",
            "/compliance/attestations",
            json={
                "consortium_id": "cons_001",
                "framework_id": "framework_soc2",
                "statement": "I confirm compliance with SOC2 security requirements",
            },
        )

        assert response.status_code == 200

    def test_create_attestation_not_member(self, client, mock_manager):
        """Test creating attestation when not a member."""
        mock_manager.get_membership.return_value = None

        response = make_request(
            client,
            mock_manager,
            "post",
            "/compliance/attestations",
            json={
                "consortium_id": "cons_001",
                "framework_id": "framework_gdpr",
                "statement": "Attestation statement here",
            },
        )

        assert response.status_code == 403

    def test_create_attestation_inactive_member(self, client, mock_manager):
        """Test creating attestation when inactive."""
        mock_membership = MagicMock()
        mock_membership.status.value = "suspended"
        mock_manager.get_membership.return_value = mock_membership

        response = make_request(
            client,
            mock_manager,
            "post",
            "/compliance/attestations",
            json={
                "consortium_id": "cons_001",
                "framework_id": "framework_hipaa",
                "statement": "HIPAA compliance attestation",
            },
        )

        assert response.status_code == 403


class TestGetAttestations:
    """Tests for GET /compliance/attestations/{consortium_id} endpoint."""

    def test_get_attestations_success(self, client, mock_manager):
        """Test getting attestations."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.get_attestations.return_value = [
            {
                "id": "attest_001",
                "consortium_id": "cons_001",
                "framework_id": "framework_gdpr",
                "control_id": None,
                "attested_by": "company_001",
                "attester_name": "Test Company",
                "attester_role": "DPO",
                "attestation_type": "manual",
                "statement": "Compliance confirmed",
                "evidence_urls": [],
                "valid_from": datetime.now().isoformat(),
                "valid_until": (datetime.now() + timedelta(days=365)).isoformat(),
                "revoked": False,
            },
        ]

        response = make_request(
            client, mock_manager, "get", "/compliance/attestations/cons_001"
        )

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_attestations_with_filters(self, client, mock_manager):
        """Test getting attestations with filters."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.get_attestations.return_value = []

        response = make_request(
            client,
            mock_manager,
            "get",
            "/compliance/attestations/cons_001",
            params={"framework_id": "framework_gdpr", "include_revoked": True},
        )

        assert response.status_code == 200
        mock_manager.get_attestations.assert_called_with(
            "cons_001", framework_id="framework_gdpr", include_revoked=True
        )

    def test_get_attestations_not_member(self, client, mock_manager):
        """Test getting attestations when not a member."""
        mock_manager.get_membership.return_value = None

        response = make_request(
            client, mock_manager, "get", "/compliance/attestations/cons_001"
        )

        assert response.status_code == 403


# ============ Data Processing Records Tests ============


class TestRecordDataProcessing:
    """Tests for POST /compliance/data-processing endpoint."""

    def test_record_data_processing_success(self, client, mock_manager):
        """Test recording a data processing activity."""
        mock_membership = MagicMock()
        mock_membership.status.value = "active"
        mock_manager.get_membership.return_value = mock_membership
        mock_manager.record_data_processing.return_value = "dpr_001"

        response = make_request(
            client,
            mock_manager,
            "post",
            "/compliance/data-processing",
            json={
                "consortium_id": "cons_001",
                "processing_purpose": "Machine learning model training",
                "data_categories": ["personal_data", "financial_data"],
                "legal_basis": "Legitimate interest",
                "data_subjects": "EU customers",
                "recipients": ["Analytics Team"],
                "retention_period": "2 years",
                "security_measures": ["encryption", "access_control"],
                "cross_border_transfer": True,
                "transfer_safeguards": "Standard contractual clauses",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "dpr_001"
        assert data["processing_purpose"] == "Machine learning model training"
        assert data["cross_border_transfer"] is True

    def test_record_data_processing_minimal(self, client, mock_manager):
        """Test recording data processing with minimal fields."""
        mock_membership = MagicMock()
        mock_membership.status.value = "active"
        mock_manager.get_membership.return_value = mock_membership
        mock_manager.record_data_processing.return_value = "dpr_002"

        response = make_request(
            client,
            mock_manager,
            "post",
            "/compliance/data-processing",
            json={
                "consortium_id": "cons_001",
                "processing_purpose": "Data analysis",
                "data_categories": ["anonymized_data"],
                "legal_basis": "Consent",
            },
        )

        assert response.status_code == 200

    def test_record_data_processing_not_member(self, client, mock_manager):
        """Test recording when not a member."""
        mock_manager.get_membership.return_value = None

        response = make_request(
            client,
            mock_manager,
            "post",
            "/compliance/data-processing",
            json={
                "consortium_id": "cons_001",
                "processing_purpose": "Data processing",
                "data_categories": ["data"],
                "legal_basis": "Consent",
            },
        )

        assert response.status_code == 403

    def test_record_data_processing_inactive(self, client, mock_manager):
        """Test recording when member is inactive."""
        mock_membership = MagicMock()
        mock_membership.status.value = "pending"
        mock_manager.get_membership.return_value = mock_membership

        response = make_request(
            client,
            mock_manager,
            "post",
            "/compliance/data-processing",
            json={
                "consortium_id": "cons_001",
                "processing_purpose": "Data processing",
                "data_categories": ["data"],
                "legal_basis": "Consent",
            },
        )

        assert response.status_code == 403


class TestGetDataProcessingRecords:
    """Tests for GET /compliance/data-processing/{consortium_id} endpoint."""

    def test_get_records_success(self, client, mock_manager):
        """Test getting data processing records."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.get_data_processing_records.return_value = [
            {
                "id": "dpr_001",
                "consortium_id": "cons_001",
                "company_id": "company_001",
                "company_name": "Test Company",
                "processing_purpose": "ML training",
                "data_categories": ["personal_data"],
                "data_subjects": "Customers",
                "recipients": None,
                "retention_period": "1 year",
                "security_measures": ["encryption"],
                "legal_basis": "Consent",
                "cross_border_transfer": False,
                "transfer_safeguards": None,
                "created_at": datetime.now().isoformat(),
            },
        ]

        response = make_request(
            client, mock_manager, "get", "/compliance/data-processing/cons_001"
        )

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_records_with_company_filter(self, client, mock_manager):
        """Test getting records filtered by company."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.get_data_processing_records.return_value = []

        response = make_request(
            client,
            mock_manager,
            "get",
            "/compliance/data-processing/cons_001",
            params={"company_id": "company_002"},
        )

        assert response.status_code == 200
        mock_manager.get_data_processing_records.assert_called_with(
            "cons_001", company_id="company_002"
        )

    def test_get_records_not_member(self, client, mock_manager):
        """Test getting records when not a member."""
        mock_manager.get_membership.return_value = None

        response = make_request(
            client, mock_manager, "get", "/compliance/data-processing/cons_001"
        )

        assert response.status_code == 403


# ============ Dashboard Tests ============


class TestGetComplianceDashboard:
    """Tests for GET /compliance/dashboard/{consortium_id} endpoint."""

    def test_get_dashboard_success(self, client, mock_manager):
        """Test getting compliance dashboard."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.get_compliance_dashboard.return_value = {
            "consortium_id": "cons_001",
            "overall_score": 87.5,
            "overall_status": "partial",
            "enabled_frameworks_count": 2,
            "frameworks": [
                {
                    "framework_id": "framework_gdpr",
                    "framework_name": "GDPR",
                    "score": 90.0,
                    "status": "compliant",
                    "passed": 45,
                    "failed": 2,
                    "pending": 3,
                    "total": 50,
                },
                {
                    "framework_id": "framework_hipaa",
                    "framework_name": "HIPAA",
                    "score": 85.0,
                    "status": "partial",
                    "passed": 38,
                    "failed": 5,
                    "pending": 2,
                    "total": 45,
                },
            ],
            "last_check_at": datetime.now().isoformat(),
            "next_check_at": (datetime.now() + timedelta(hours=24)).isoformat(),
        }

        response = make_request(
            client, mock_manager, "get", "/compliance/dashboard/cons_001"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["overall_score"] == 87.5
        assert len(data["frameworks"]) == 2

    def test_get_dashboard_not_member(self, client, mock_manager):
        """Test getting dashboard when not a member."""
        mock_manager.get_membership.return_value = None

        response = make_request(
            client, mock_manager, "get", "/compliance/dashboard/cons_001"
        )

        assert response.status_code == 403


# ============ Edge Cases and Validation Tests ============


class TestComplianceValidation:
    """Tests for input validation in compliance routes."""

    def test_attestation_statement_too_short(self, client, mock_manager):
        """Test attestation with statement too short."""
        mock_membership = MagicMock()
        mock_membership.status.value = "active"
        mock_manager.get_membership.return_value = mock_membership

        response = make_request(
            client,
            mock_manager,
            "post",
            "/compliance/attestations",
            json={
                "consortium_id": "cons_001",
                "framework_id": "framework_gdpr",
                "statement": "Short",  # Less than 10 chars
            },
        )

        assert response.status_code == 422

    def test_data_processing_purpose_too_short(self, client, mock_manager):
        """Test data processing with purpose too short."""
        mock_membership = MagicMock()
        mock_membership.status.value = "active"
        mock_manager.get_membership.return_value = mock_membership

        response = make_request(
            client,
            mock_manager,
            "post",
            "/compliance/data-processing",
            json={
                "consortium_id": "cons_001",
                "processing_purpose": "abc",  # Less than 5 chars
                "data_categories": ["data"],
                "legal_basis": "Consent",
            },
        )

        assert response.status_code == 422

    def test_invalid_framework_id(self, client, mock_manager):
        """Test with invalid framework ID enum value."""
        mock_membership = MagicMock()
        mock_membership.status.value = "active"
        mock_manager.get_membership.return_value = mock_membership

        response = make_request(
            client,
            mock_manager,
            "post",
            "/compliance/checks",
            json={
                "consortium_id": "cons_001",
                "framework_id": "invalid_framework",
                "control_id": "test",
                "status": "passed",
                "result": "Test result",
            },
        )

        assert response.status_code == 422

    def test_invalid_check_status(self, client, mock_manager):
        """Test with invalid check status enum value."""
        mock_membership = MagicMock()
        mock_membership.status.value = "active"
        mock_manager.get_membership.return_value = mock_membership

        response = make_request(
            client,
            mock_manager,
            "post",
            "/compliance/checks",
            json={
                "consortium_id": "cons_001",
                "framework_id": "framework_gdpr",
                "control_id": "test",
                "status": "invalid_status",
                "result": "Test result",
            },
        )

        assert response.status_code == 422

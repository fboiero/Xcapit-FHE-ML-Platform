"""Tests for data quality API routes."""

import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

# Mock tenseal before importing sdk modules
sys.modules["tenseal"] = MagicMock()

from fastapi import FastAPI
from fastapi.testclient import TestClient

from sdk.api.data_quality_routes import router
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


# ============ Assessment Tests ============


class TestAssessDataQuality:
    """Tests for POST /quality/assess endpoint."""

    def test_assess_quality_success(self, client, mock_manager):
        """Test successful data quality assessment."""
        mock_membership = MagicMock()
        mock_membership.status.value = "active"
        mock_manager.get_membership.return_value = mock_membership
        mock_manager.assess_data_quality.return_value = {
            "id": "assessment_001",
            "consortium_id": "cons_001",
            "company_id": "company_001",
            "contribution_id": "contrib_001",
            "overall_score": 92.5,
            "completeness_score": 95.0,
            "consistency_score": 90.0,
            "uniqueness_score": 98.0,
            "validity_score": 88.0,
            "freshness_score": 91.5,
            "record_count": 10000,
            "feature_count": 25,
            "null_ratio": 0.05,
            "duplicate_ratio": 0.02,
            "outlier_ratio": 0.01,
            "assessed_at": datetime.now().isoformat(),
            "metadata": {"source": "api"},
        }

        response = make_request(
            client,
            mock_manager,
            "post",
            "/quality/assess",
            json={
                "consortium_id": "cons_001",
                "contribution_id": "contrib_001",
                "record_count": 10000,
                "feature_count": 25,
                "null_count": 500,
                "duplicate_count": 200,
                "outlier_count": 100,
                "schema_violations": 10,
                "format_violations": 5,
                "range_violations": 15,
                "metadata": {"source": "api"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "assessment_001"
        assert data["overall_score"] == 92.5
        mock_manager.record_audit_event.assert_called_once()

    def test_assess_quality_minimal_request(self, client, mock_manager):
        """Test assessment with minimal required fields."""
        mock_membership = MagicMock()
        mock_membership.status.value = "active"
        mock_manager.get_membership.return_value = mock_membership
        mock_manager.assess_data_quality.return_value = {
            "id": "assessment_002",
            "consortium_id": "cons_001",
            "company_id": "company_001",
            "contribution_id": None,
            "overall_score": 100.0,
            "completeness_score": 100.0,
            "consistency_score": 100.0,
            "uniqueness_score": 100.0,
            "validity_score": 100.0,
            "freshness_score": 100.0,
            "record_count": 1000,
            "feature_count": 10,
            "null_ratio": 0.0,
            "duplicate_ratio": 0.0,
            "outlier_ratio": 0.0,
            "assessed_at": datetime.now().isoformat(),
            "metadata": None,
        }

        response = make_request(
            client,
            mock_manager,
            "post",
            "/quality/assess",
            json={
                "consortium_id": "cons_001",
                "record_count": 1000,
                "feature_count": 10,
            },
        )

        assert response.status_code == 200

    def test_assess_quality_not_member(self, client, mock_manager):
        """Test assessment when not a member."""
        mock_manager.get_membership.return_value = None

        response = make_request(
            client,
            mock_manager,
            "post",
            "/quality/assess",
            json={
                "consortium_id": "cons_001",
                "record_count": 1000,
                "feature_count": 10,
            },
        )

        assert response.status_code == 403

    def test_assess_quality_inactive_member(self, client, mock_manager):
        """Test assessment when member is inactive."""
        mock_membership = MagicMock()
        mock_membership.status.value = "suspended"
        mock_manager.get_membership.return_value = mock_membership

        response = make_request(
            client,
            mock_manager,
            "post",
            "/quality/assess",
            json={
                "consortium_id": "cons_001",
                "record_count": 500,
                "feature_count": 5,
            },
        )

        assert response.status_code == 403


class TestGetQualityAssessments:
    """Tests for GET /quality/assessments/{consortium_id} endpoint."""

    def test_get_assessments_success(self, client, mock_manager):
        """Test getting quality assessments."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.get_quality_assessments.return_value = [
            {
                "id": "assessment_001",
                "consortium_id": "cons_001",
                "company_id": "company_001",
                "company_name": "Test Company",
                "contribution_id": None,
                "overall_score": 88.0,
                "completeness_score": 90.0,
                "consistency_score": 85.0,
                "uniqueness_score": 92.0,
                "validity_score": 86.0,
                "freshness_score": 87.0,
                "record_count": 5000,
                "feature_count": 15,
                "null_ratio": 0.1,
                "duplicate_ratio": 0.08,
                "outlier_ratio": 0.03,
                "assessed_at": datetime.now().isoformat(),
                "metadata": None,
            },
        ]

        response = make_request(
            client, mock_manager, "get", "/quality/assessments/cons_001"
        )

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_assessments_with_filters(self, client, mock_manager):
        """Test getting assessments with filters."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.get_quality_assessments.return_value = []

        response = make_request(
            client,
            mock_manager,
            "get",
            "/quality/assessments/cons_001",
            params={"company_id": "company_002", "limit": 25},
        )

        assert response.status_code == 200
        mock_manager.get_quality_assessments.assert_called_with(
            "cons_001", company_id="company_002", limit=25
        )

    def test_get_assessments_not_member(self, client, mock_manager):
        """Test getting assessments when not a member."""
        mock_manager.get_membership.return_value = None

        response = make_request(
            client, mock_manager, "get", "/quality/assessments/cons_001"
        )

        assert response.status_code == 403


class TestGetLatestAssessment:
    """Tests for GET /quality/assessments/{consortium_id}/latest endpoint."""

    def test_get_latest_success(self, client, mock_manager):
        """Test getting latest assessment."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.get_latest_quality_assessment.return_value = {
            "id": "assessment_001",
            "consortium_id": "cons_001",
            "company_id": "company_001",
            "company_name": "Test Company",
            "contribution_id": None,
            "overall_score": 95.0,
            "completeness_score": 96.0,
            "consistency_score": 94.0,
            "uniqueness_score": 97.0,
            "validity_score": 93.0,
            "freshness_score": 95.0,
            "record_count": 8000,
            "feature_count": 20,
            "null_ratio": 0.04,
            "duplicate_ratio": 0.03,
            "outlier_ratio": 0.02,
            "assessed_at": datetime.now().isoformat(),
            "metadata": None,
        }

        response = make_request(
            client, mock_manager, "get", "/quality/assessments/cons_001/latest"
        )

        assert response.status_code == 200
        assert response.json()["overall_score"] == 95.0

    def test_get_latest_for_other_company(self, client, mock_manager):
        """Test getting latest assessment for another company."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.get_latest_quality_assessment.return_value = {
            "id": "assessment_002",
            "consortium_id": "cons_001",
            "company_id": "company_002",
            "company_name": "Other Company",
            "contribution_id": None,
            "overall_score": 80.0,
            "completeness_score": 82.0,
            "consistency_score": 78.0,
            "uniqueness_score": 85.0,
            "validity_score": 76.0,
            "freshness_score": 79.0,
            "record_count": 3000,
            "feature_count": 12,
            "null_ratio": 0.18,
            "duplicate_ratio": 0.15,
            "outlier_ratio": 0.05,
            "assessed_at": datetime.now().isoformat(),
            "metadata": None,
        }

        response = make_request(
            client,
            mock_manager,
            "get",
            "/quality/assessments/cons_001/latest",
            params={"target_company_id": "company_002"},
        )

        assert response.status_code == 200
        mock_manager.get_latest_quality_assessment.assert_called_with(
            "cons_001", "company_002"
        )

    def test_get_latest_not_found(self, client, mock_manager):
        """Test getting latest when no assessments exist."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.get_latest_quality_assessment.return_value = None

        response = make_request(
            client, mock_manager, "get", "/quality/assessments/cons_001/latest"
        )

        assert response.status_code == 404

    def test_get_latest_not_member(self, client, mock_manager):
        """Test getting latest when not a member."""
        mock_manager.get_membership.return_value = None

        response = make_request(
            client, mock_manager, "get", "/quality/assessments/cons_001/latest"
        )

        assert response.status_code == 403


# ============ History Tests ============


class TestGetQualityHistory:
    """Tests for GET /quality/history/{consortium_id} endpoint."""

    def test_get_history_success(self, client, mock_manager):
        """Test getting quality history."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.get_quality_history.return_value = [
            {
                "id": "history_001",
                "consortium_id": "cons_001",
                "company_id": "company_001",
                "metric": "overall",
                "value": 90.0,
                "recorded_at": datetime.now().isoformat(),
            },
            {
                "id": "history_002",
                "consortium_id": "cons_001",
                "company_id": "company_001",
                "metric": "overall",
                "value": 88.0,
                "recorded_at": (datetime.now() - timedelta(days=1)).isoformat(),
            },
        ]

        response = make_request(
            client, mock_manager, "get", "/quality/history/cons_001"
        )

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_history_with_filters(self, client, mock_manager):
        """Test getting history with filters."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.get_quality_history.return_value = []

        response = make_request(
            client,
            mock_manager,
            "get",
            "/quality/history/cons_001",
            params={"metric": "completeness", "company_id": "company_001", "days": 7},
        )

        assert response.status_code == 200
        mock_manager.get_quality_history.assert_called_with(
            "cons_001", metric="completeness", company_id="company_001", days=7
        )

    def test_get_history_not_member(self, client, mock_manager):
        """Test getting history when not a member."""
        mock_manager.get_membership.return_value = None

        response = make_request(
            client, mock_manager, "get", "/quality/history/cons_001"
        )

        assert response.status_code == 403


# ============ Rules Tests ============


class TestSetQualityRule:
    """Tests for POST /quality/rules endpoint."""

    def test_set_rule_success(self, client, mock_manager):
        """Test setting a quality rule."""
        mock_consortium = MagicMock()
        mock_manager.get_consortium.return_value = mock_consortium
        mock_membership = MagicMock()
        mock_membership.role.value = "admin"
        mock_manager.get_membership.return_value = mock_membership
        mock_manager.set_quality_rule.return_value = {
            "id": "rule_001",
            "consortium_id": "cons_001",
            "metric": "completeness",
            "warning_threshold": 85.0,
            "critical_threshold": 70.0,
            "enabled": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": None,
        }

        response = make_request(
            client,
            mock_manager,
            "post",
            "/quality/rules",
            json={
                "consortium_id": "cons_001",
                "metric": "completeness",
                "warning_threshold": 85.0,
                "critical_threshold": 70.0,
                "enabled": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "rule_001"
        assert data["warning_threshold"] == 85.0
        mock_manager.record_audit_event.assert_called_once()

    def test_set_rule_as_owner(self, client, mock_manager):
        """Test setting rule as owner."""
        mock_consortium = MagicMock()
        mock_manager.get_consortium.return_value = mock_consortium
        mock_membership = MagicMock()
        mock_membership.role.value = "owner"
        mock_manager.get_membership.return_value = mock_membership
        mock_manager.set_quality_rule.return_value = {
            "id": "rule_002",
            "consortium_id": "cons_001",
            "metric": "consistency",
            "warning_threshold": 80.0,
            "critical_threshold": 60.0,
            "enabled": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": None,
        }

        response = make_request(
            client,
            mock_manager,
            "post",
            "/quality/rules",
            json={
                "consortium_id": "cons_001",
                "metric": "consistency",
                "warning_threshold": 80.0,
                "critical_threshold": 60.0,
            },
        )

        assert response.status_code == 200

    def test_set_rule_consortium_not_found(self, client, mock_manager):
        """Test setting rule for non-existent consortium."""
        mock_manager.get_consortium.return_value = None

        response = make_request(
            client,
            mock_manager,
            "post",
            "/quality/rules",
            json={
                "consortium_id": "nonexistent",
                "metric": "completeness",
                "warning_threshold": 85.0,
                "critical_threshold": 70.0,
            },
        )

        assert response.status_code == 404

    def test_set_rule_not_admin(self, client, mock_manager):
        """Test setting rule when not admin or owner."""
        mock_consortium = MagicMock()
        mock_manager.get_consortium.return_value = mock_consortium
        mock_membership = MagicMock()
        mock_membership.role.value = "member"
        mock_manager.get_membership.return_value = mock_membership

        response = make_request(
            client,
            mock_manager,
            "post",
            "/quality/rules",
            json={
                "consortium_id": "cons_001",
                "metric": "uniqueness",
                "warning_threshold": 90.0,
                "critical_threshold": 80.0,
            },
        )

        assert response.status_code == 403

    def test_set_rule_invalid_thresholds(self, client, mock_manager):
        """Test setting rule with invalid thresholds (critical > warning)."""
        mock_consortium = MagicMock()
        mock_manager.get_consortium.return_value = mock_consortium
        mock_membership = MagicMock()
        mock_membership.role.value = "admin"
        mock_manager.get_membership.return_value = mock_membership

        response = make_request(
            client,
            mock_manager,
            "post",
            "/quality/rules",
            json={
                "consortium_id": "cons_001",
                "metric": "completeness",
                "warning_threshold": 70.0,  # Lower than critical
                "critical_threshold": 85.0,  # Higher than warning
            },
        )

        assert response.status_code == 400
        assert "threshold" in response.json()["detail"].lower()


class TestGetQualityRules:
    """Tests for GET /quality/rules/{consortium_id} endpoint."""

    def test_get_rules_success(self, client, mock_manager):
        """Test getting quality rules."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.get_quality_rules.return_value = [
            {
                "id": "rule_001",
                "consortium_id": "cons_001",
                "metric": "completeness",
                "warning_threshold": 85.0,
                "critical_threshold": 70.0,
                "enabled": True,
                "created_at": datetime.now().isoformat(),
                "updated_at": None,
            },
            {
                "id": "rule_002",
                "consortium_id": "cons_001",
                "metric": "consistency",
                "warning_threshold": 80.0,
                "critical_threshold": 65.0,
                "enabled": True,
                "created_at": datetime.now().isoformat(),
                "updated_at": None,
            },
        ]

        response = make_request(
            client, mock_manager, "get", "/quality/rules/cons_001"
        )

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_rules_not_member(self, client, mock_manager):
        """Test getting rules when not a member."""
        mock_manager.get_membership.return_value = None

        response = make_request(
            client, mock_manager, "get", "/quality/rules/cons_001"
        )

        assert response.status_code == 403


# ============ Alerts Tests ============


class TestGetQualityAlerts:
    """Tests for GET /quality/alerts/{consortium_id} endpoint."""

    def test_get_alerts_success(self, client, mock_manager):
        """Test getting quality alerts."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.get_quality_alerts.return_value = [
            {
                "id": "alert_001",
                "consortium_id": "cons_001",
                "company_id": "company_001",
                "company_name": "Test Company",
                "assessment_id": "assessment_001",
                "metric": "completeness",
                "current_value": 65.0,
                "threshold": 70.0,
                "severity": "critical",
                "status": "active",
                "message": "Completeness score below critical threshold",
                "created_at": datetime.now().isoformat(),
                "acknowledged_at": None,
                "acknowledged_by": None,
            },
        ]

        response = make_request(
            client, mock_manager, "get", "/quality/alerts/cons_001"
        )

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["severity"] == "critical"

    def test_get_alerts_with_filters(self, client, mock_manager):
        """Test getting alerts with filters."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.get_quality_alerts.return_value = []

        response = make_request(
            client,
            mock_manager,
            "get",
            "/quality/alerts/cons_001",
            params={"severity": "warning", "alert_status": "active"},
        )

        assert response.status_code == 200
        mock_manager.get_quality_alerts.assert_called_with(
            "cons_001", severity="warning", status="active"
        )

    def test_get_alerts_not_member(self, client, mock_manager):
        """Test getting alerts when not a member."""
        mock_manager.get_membership.return_value = None

        response = make_request(
            client, mock_manager, "get", "/quality/alerts/cons_001"
        )

        assert response.status_code == 403


class TestAcknowledgeAlert:
    """Tests for POST /quality/alerts/{alert_id}/acknowledge endpoint."""

    def test_acknowledge_success(self, client, mock_manager):
        """Test acknowledging an alert."""
        mock_manager.acknowledge_alert.return_value = True

        response = make_request(
            client,
            mock_manager,
            "post",
            "/quality/alerts/alert_001/acknowledge",
            json={"notes": "Investigating the issue"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "acknowledged"
        mock_manager.acknowledge_alert.assert_called_with(
            alert_id="alert_001",
            acknowledged_by="company_001",
            notes="Investigating the issue",
        )

    def test_acknowledge_without_notes(self, client, mock_manager):
        """Test acknowledging without notes."""
        mock_manager.acknowledge_alert.return_value = True

        response = make_request(
            client,
            mock_manager,
            "post",
            "/quality/alerts/alert_001/acknowledge",
            json={},
        )

        assert response.status_code == 200

    def test_acknowledge_not_found(self, client, mock_manager):
        """Test acknowledging non-existent alert."""
        mock_manager.acknowledge_alert.return_value = False

        response = make_request(
            client,
            mock_manager,
            "post",
            "/quality/alerts/nonexistent/acknowledge",
            json={},
        )

        assert response.status_code == 404


# ============ Dashboard Tests ============


class TestGetQualityDashboard:
    """Tests for GET /quality/dashboard/{consortium_id} endpoint."""

    def test_get_dashboard_success(self, client, mock_manager):
        """Test getting quality dashboard."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.get_consortium_quality_dashboard.return_value = {
            "consortium_id": "cons_001",
            "overall_score": 87.5,
            "completeness_avg": 90.0,
            "consistency_avg": 85.0,
            "uniqueness_avg": 92.0,
            "validity_avg": 84.0,
            "freshness_avg": 86.5,
            "total_records": 50000,
            "total_companies": 5,
            "total_assessments": 25,
            "companies": [
                {
                    "company_id": "company_001",
                    "company_name": "Test Company",
                    "overall_score": 92.0,
                    "completeness_score": 95.0,
                    "consistency_score": 90.0,
                    "uniqueness_score": 94.0,
                    "validity_score": 88.0,
                    "freshness_score": 93.0,
                    "total_records": 10000,
                    "assessments_count": 5,
                    "last_assessment": datetime.now().isoformat(),
                },
                {
                    "company_id": "company_002",
                    "company_name": "Other Company",
                    "overall_score": 83.0,
                    "completeness_score": 85.0,
                    "consistency_score": 80.0,
                    "uniqueness_score": 90.0,
                    "validity_score": 78.0,
                    "freshness_score": 82.0,
                    "total_records": 8000,
                    "assessments_count": 4,
                    "last_assessment": datetime.now().isoformat(),
                },
            ],
            "active_alerts": 2,
            "last_assessment": datetime.now().isoformat(),
        }

        response = make_request(
            client, mock_manager, "get", "/quality/dashboard/cons_001"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["overall_score"] == 87.5
        assert len(data["companies"]) == 2
        assert data["active_alerts"] == 2

    def test_get_dashboard_not_member(self, client, mock_manager):
        """Test getting dashboard when not a member."""
        mock_manager.get_membership.return_value = None

        response = make_request(
            client, mock_manager, "get", "/quality/dashboard/cons_001"
        )

        assert response.status_code == 403


# ============ Validation Tests ============


class TestDataQualityValidation:
    """Tests for input validation in data quality routes."""

    def test_assess_negative_record_count(self, client, mock_manager):
        """Test assessment with negative record count."""
        mock_membership = MagicMock()
        mock_membership.status.value = "active"
        mock_manager.get_membership.return_value = mock_membership

        response = make_request(
            client,
            mock_manager,
            "post",
            "/quality/assess",
            json={
                "consortium_id": "cons_001",
                "record_count": -100,
                "feature_count": 10,
            },
        )

        assert response.status_code == 422

    def test_assess_negative_null_count(self, client, mock_manager):
        """Test assessment with negative null count."""
        mock_membership = MagicMock()
        mock_membership.status.value = "active"
        mock_manager.get_membership.return_value = mock_membership

        response = make_request(
            client,
            mock_manager,
            "post",
            "/quality/assess",
            json={
                "consortium_id": "cons_001",
                "record_count": 1000,
                "feature_count": 10,
                "null_count": -50,
            },
        )

        assert response.status_code == 422

    def test_rule_threshold_out_of_range(self, client, mock_manager):
        """Test rule with threshold > 100."""
        mock_consortium = MagicMock()
        mock_manager.get_consortium.return_value = mock_consortium
        mock_membership = MagicMock()
        mock_membership.role.value = "admin"
        mock_manager.get_membership.return_value = mock_membership

        response = make_request(
            client,
            mock_manager,
            "post",
            "/quality/rules",
            json={
                "consortium_id": "cons_001",
                "metric": "completeness",
                "warning_threshold": 150.0,  # > 100
                "critical_threshold": 70.0,
            },
        )

        assert response.status_code == 422

    def test_invalid_metric_enum(self, client, mock_manager):
        """Test with invalid metric enum value."""
        mock_consortium = MagicMock()
        mock_manager.get_consortium.return_value = mock_consortium
        mock_membership = MagicMock()
        mock_membership.role.value = "admin"
        mock_manager.get_membership.return_value = mock_membership

        response = make_request(
            client,
            mock_manager,
            "post",
            "/quality/rules",
            json={
                "consortium_id": "cons_001",
                "metric": "invalid_metric",
                "warning_threshold": 85.0,
                "critical_threshold": 70.0,
            },
        )

        assert response.status_code == 422

    def test_invalid_severity_filter(self, client, mock_manager):
        """Test with invalid severity filter."""
        mock_manager.get_membership.return_value = MagicMock()

        response = make_request(
            client,
            mock_manager,
            "get",
            "/quality/alerts/cons_001",
            params={"severity": "invalid_severity"},
        )

        assert response.status_code == 422

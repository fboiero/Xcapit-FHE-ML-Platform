"""Tests for explainability API routes."""

import sys
from unittest.mock import MagicMock

import pytest

# Mock tenseal before importing sdk modules
sys.modules["tenseal"] = MagicMock()

from fastapi import FastAPI
from fastapi.testclient import TestClient

from sdk.api.explainability_routes import router, get_manager
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
def app(mock_company, mock_manager):
    """Create FastAPI app with router and overridden dependencies."""
    app = FastAPI()
    app.include_router(router)

    # Override dependencies
    app.dependency_overrides[get_current_company] = lambda: mock_company
    app.dependency_overrides[get_manager] = lambda: mock_manager

    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestRequestExplanation:
    """Tests for POST /api/explainability/explain endpoint."""

    def test_request_explanation_success(self, client, mock_manager):
        """Test successful explanation request."""
        mock_manager.request_explanation.return_value = {
            "request_id": "exp_001",
            "consortium_id": "cons_001",
            "explanation_type": "feature_importance",
            "status": "pending",
        }

        response = client.post(
            "/api/explainability/explain",
            json={
                "consortium_id": "cons_001",
                "explanation_type": "feature_importance",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["request_id"] == "exp_001"
        assert data["status"] == "pending"

    def test_request_explanation_invalid_type(self, client, mock_manager):
        """Test explanation request with invalid type."""
        response = client.post(
            "/api/explainability/explain",
            json={
                "consortium_id": "cons_001",
                "explanation_type": "invalid_type",
            },
        )

        assert response.status_code == 400
        assert "Invalid explanation type" in response.json()["detail"]

    def test_request_explanation_shap(self, client, mock_manager):
        """Test SHAP explanation request."""
        mock_manager.request_explanation.return_value = {
            "request_id": "exp_002",
            "consortium_id": "cons_001",
            "explanation_type": "shap",
            "status": "pending",
        }

        response = client.post(
            "/api/explainability/explain",
            json={
                "consortium_id": "cons_001",
                "explanation_type": "shap",
                "input_data": {"feature1": 1.0, "feature2": 2.0},
            },
        )

        assert response.status_code == 200
        assert response.json()["explanation_type"] == "shap"

    def test_request_explanation_value_error(self, client, mock_manager):
        """Test explanation request with ValueError."""
        mock_manager.request_explanation.side_effect = ValueError("Invalid consortium")

        response = client.post(
            "/api/explainability/explain",
            json={
                "consortium_id": "invalid_cons",
                "explanation_type": "feature_importance",
            },
        )

        assert response.status_code == 400

    def test_request_explanation_server_error(self, client, mock_manager):
        """Test explanation request with server error."""
        mock_manager.request_explanation.side_effect = Exception("Database error")

        response = client.post(
            "/api/explainability/explain",
            json={
                "consortium_id": "cons_001",
                "explanation_type": "summary",
            },
        )

        assert response.status_code == 500


class TestGetExplanation:
    """Tests for GET /api/explainability/explanations/{request_id} endpoint."""

    def test_get_explanation_success(self, client, mock_company, mock_manager):
        """Test getting an explanation by ID."""
        mock_manager.get_explanation.return_value = {
            "request_id": "exp_001",
            "consortium_id": "cons_001",
            "requester_id": "company_001",
            "explanation_type": "feature_importance",
            "status": "completed",
            "result": {"features": [{"name": "f1", "importance": 0.8}]},
        }

        response = client.get("/api/explainability/explanations/exp_001")

        assert response.status_code == 200
        assert response.json()["request_id"] == "exp_001"

    def test_get_explanation_not_found(self, client, mock_manager):
        """Test getting non-existent explanation."""
        mock_manager.get_explanation.return_value = None

        response = client.get("/api/explainability/explanations/nonexistent")

        assert response.status_code == 404

    def test_get_explanation_access_denied_not_member(self, client, mock_manager):
        """Test access denied when not a consortium member."""
        mock_manager.get_explanation.return_value = {
            "request_id": "exp_001",
            "consortium_id": "cons_001",
            "requester_id": "other_company",
        }
        mock_manager.get_consortium.return_value = {"id": "cons_001"}
        mock_manager.get_consortium_members.return_value = [{"company_id": "other_company"}]

        response = client.get("/api/explainability/explanations/exp_001")

        assert response.status_code == 403

    def test_get_explanation_as_consortium_member(self, client, mock_manager):
        """Test access allowed for consortium member."""
        mock_manager.get_explanation.return_value = {
            "request_id": "exp_001",
            "consortium_id": "cons_001",
            "requester_id": "other_company",
            "status": "completed",
        }
        mock_manager.get_consortium.return_value = {"id": "cons_001"}
        mock_manager.get_consortium_members.return_value = [
            {"company_id": "company_001"},
            {"company_id": "other_company"},
        ]

        response = client.get("/api/explainability/explanations/exp_001")

        assert response.status_code == 200


class TestListExplanations:
    """Tests for GET /api/explainability/explanations endpoint."""

    def test_list_explanations_success(self, client, mock_manager):
        """Test listing explanations."""
        mock_manager.get_consortium.return_value = {"id": "cons_001"}
        mock_manager.list_explanations.return_value = [
            {"request_id": "exp_001", "explanation_type": "shap"},
            {"request_id": "exp_002", "explanation_type": "feature_importance"},
        ]

        response = client.get(
            "/api/explainability/explanations",
            params={"consortium_id": "cons_001"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["explanations"]) == 2

    def test_list_explanations_consortium_not_found(self, client, mock_manager):
        """Test listing explanations for non-existent consortium."""
        mock_manager.get_consortium.return_value = None

        response = client.get(
            "/api/explainability/explanations",
            params={"consortium_id": "nonexistent"},
        )

        assert response.status_code == 404

    def test_list_explanations_with_type_filter(self, client, mock_manager):
        """Test listing explanations with type filter."""
        mock_manager.get_consortium.return_value = {"id": "cons_001"}
        mock_manager.list_explanations.return_value = [
            {"request_id": "exp_001", "explanation_type": "shap"},
        ]

        response = client.get(
            "/api/explainability/explanations",
            params={"consortium_id": "cons_001", "explanation_type": "shap"},
        )

        assert response.status_code == 200
        mock_manager.list_explanations.assert_called_once()


class TestGetFeatureImportance:
    """Tests for GET /api/explainability/feature-importance endpoint."""

    def test_get_feature_importance_success(self, client, mock_manager):
        """Test getting feature importance."""
        mock_manager.get_consortium.return_value = {"id": "cons_001"}
        mock_manager.get_feature_importance.return_value = [
            {"name": "feature1", "importance": 0.45},
            {"name": "feature2", "importance": 0.35},
            {"name": "feature3", "importance": 0.20},
        ]

        response = client.get(
            "/api/explainability/feature-importance",
            params={"consortium_id": "cons_001"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["feature_count"] == 3
        assert "privacy_note" in data

    def test_get_feature_importance_consortium_not_found(self, client, mock_manager):
        """Test feature importance for non-existent consortium."""
        mock_manager.get_consortium.return_value = None

        response = client.get(
            "/api/explainability/feature-importance",
            params={"consortium_id": "nonexistent"},
        )

        assert response.status_code == 404


class TestComputeModelInsights:
    """Tests for POST /api/explainability/insights endpoint."""

    def test_compute_insights_success(self, client, mock_manager):
        """Test computing model insights."""
        mock_manager.get_consortium.return_value = {"id": "cons_001"}
        mock_manager.compute_model_insights.return_value = {
            "model_complexity": "medium",
            "feature_interactions": [],
            "decision_boundaries": {},
        }

        response = client.post(
            "/api/explainability/insights",
            json={"consortium_id": "cons_001"},
        )

        assert response.status_code == 200
        assert "model_complexity" in response.json()

    def test_compute_insights_consortium_not_found(self, client, mock_manager):
        """Test computing insights for non-existent consortium."""
        mock_manager.get_consortium.return_value = None

        response = client.post(
            "/api/explainability/insights",
            json={"consortium_id": "nonexistent"},
        )

        assert response.status_code == 404

    def test_compute_insights_error(self, client, mock_manager):
        """Test computing insights with error."""
        mock_manager.get_consortium.return_value = {"id": "cons_001"}
        mock_manager.compute_model_insights.side_effect = Exception("Computation failed")

        response = client.post(
            "/api/explainability/insights",
            json={"consortium_id": "cons_001"},
        )

        assert response.status_code == 500


class TestGetInsights:
    """Tests for GET /api/explainability/insights/{consortium_id} endpoint."""

    def test_get_insights_success(self, client, mock_manager):
        """Test getting model insights."""
        mock_manager.get_consortium.return_value = {"id": "cons_001"}
        mock_manager.compute_model_insights.return_value = {
            "model_summary": "Linear model with 5 features",
        }

        response = client.get("/api/explainability/insights/cons_001")

        assert response.status_code == 200

    def test_get_insights_not_found(self, client, mock_manager):
        """Test getting insights for non-existent consortium."""
        mock_manager.get_consortium.return_value = None

        response = client.get("/api/explainability/insights/nonexistent")

        assert response.status_code == 404


class TestGetStats:
    """Tests for GET /api/explainability/stats endpoint."""

    def test_get_stats_success(self, client, mock_manager):
        """Test getting explainability statistics."""
        mock_manager.get_explainability_stats.return_value = {
            "total_requests": 100,
            "completed_requests": 85,
            "by_type": {"shap": 40, "feature_importance": 60},
        }

        response = client.get("/api/explainability/stats")

        assert response.status_code == 200
        data = response.json()
        assert "stats" in data
        assert data["privacy_preserved"] is True


class TestDeleteExplanation:
    """Tests for DELETE /api/explainability/explanations/{request_id} endpoint."""

    def test_delete_explanation_success(self, client, mock_company, mock_manager):
        """Test deleting an explanation."""
        mock_manager.get_explanation.return_value = {
            "request_id": "exp_001",
            "requester_id": "company_001",
        }
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_manager._get_connection.return_value = mock_conn

        response = client.delete("/api/explainability/explanations/exp_001")

        assert response.status_code == 200
        assert response.json()["request_id"] == "exp_001"

    def test_delete_explanation_not_found(self, client, mock_manager):
        """Test deleting non-existent explanation."""
        mock_manager.get_explanation.return_value = None

        response = client.delete("/api/explainability/explanations/nonexistent")

        assert response.status_code == 404

    def test_delete_explanation_forbidden(self, client, mock_manager):
        """Test deleting explanation by non-owner."""
        mock_manager.get_explanation.return_value = {
            "request_id": "exp_001",
            "requester_id": "other_company",
        }

        response = client.delete("/api/explainability/explanations/exp_001")

        assert response.status_code == 403

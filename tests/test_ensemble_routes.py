"""Tests for multi-model ensemble API routes."""

import sys
from unittest.mock import MagicMock

import pytest

# Mock tenseal before importing sdk modules
sys.modules["tenseal"] = MagicMock()

from fastapi import FastAPI
from fastapi.testclient import TestClient

from sdk.api.ensemble_routes import router, get_manager
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


class TestCreateEnsemble:
    """Tests for POST /api/ensemble/create endpoint."""

    def test_create_ensemble_success(self, client, mock_manager):
        """Test successful ensemble creation."""
        mock_manager.create_ensemble.return_value = {
            "id": "ens_001",
            "name": "Test Ensemble",
            "ensemble_type": "voting",
            "status": "draft",
        }

        response = client.post(
            "/api/ensemble/create",
            json={
                "name": "Test Ensemble",
                "description": "Test ensemble description",
                "ensemble_type": "voting",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "ens_001"
        assert data["ensemble_type"] == "voting"

    def test_create_ensemble_averaging_type(self, client, mock_manager):
        """Test creating averaging ensemble."""
        mock_manager.create_ensemble.return_value = {
            "id": "ens_002",
            "name": "Averaging Ensemble",
            "ensemble_type": "averaging",
        }

        response = client.post(
            "/api/ensemble/create",
            json={
                "name": "Averaging Ensemble",
                "description": "Averaging type ensemble",
                "ensemble_type": "averaging",
            },
        )

        assert response.status_code == 200
        assert response.json()["ensemble_type"] == "averaging"

    def test_create_ensemble_weighted_type(self, client, mock_manager):
        """Test creating weighted ensemble."""
        mock_manager.create_ensemble.return_value = {
            "id": "ens_003",
            "ensemble_type": "weighted",
        }

        response = client.post(
            "/api/ensemble/create",
            json={
                "name": "Weighted Ensemble",
                "description": "Weighted type",
                "ensemble_type": "weighted",
            },
        )

        assert response.status_code == 200
        assert response.json()["ensemble_type"] == "weighted"

    def test_create_ensemble_stacking_type(self, client, mock_manager):
        """Test creating stacking ensemble."""
        mock_manager.create_ensemble.return_value = {
            "id": "ens_004",
            "ensemble_type": "stacking",
        }

        response = client.post(
            "/api/ensemble/create",
            json={
                "name": "Stacking Ensemble",
                "description": "Stacking type",
                "ensemble_type": "stacking",
            },
        )

        assert response.status_code == 200
        assert response.json()["ensemble_type"] == "stacking"

    def test_create_ensemble_boosting_type(self, client, mock_manager):
        """Test creating boosting ensemble."""
        mock_manager.create_ensemble.return_value = {
            "id": "ens_005",
            "ensemble_type": "boosting",
        }

        response = client.post(
            "/api/ensemble/create",
            json={
                "name": "Boosting Ensemble",
                "description": "Boosting type",
                "ensemble_type": "boosting",
            },
        )

        assert response.status_code == 200
        assert response.json()["ensemble_type"] == "boosting"

    def test_create_ensemble_invalid_type(self, client, mock_manager):
        """Test creating ensemble with invalid type."""
        response = client.post(
            "/api/ensemble/create",
            json={
                "name": "Invalid Ensemble",
                "description": "Invalid type",
                "ensemble_type": "invalid_type",
            },
        )

        assert response.status_code == 400
        assert "must be one of" in response.json()["detail"]

    def test_create_ensemble_value_error(self, client, mock_manager):
        """Test ensemble creation with value error."""
        mock_manager.create_ensemble.side_effect = ValueError("Invalid parameters")

        response = client.post(
            "/api/ensemble/create",
            json={
                "name": "Test Ensemble",
                "description": "Description",
                "ensemble_type": "voting",
            },
        )

        assert response.status_code == 400


class TestAddModelToEnsemble:
    """Tests for POST /api/ensemble/{ensemble_id}/models endpoint."""

    def test_add_model_success(self, client, mock_manager):
        """Test successfully adding model to ensemble."""
        mock_manager.add_model_to_ensemble.return_value = {
            "entry_id": "entry_001",
            "ensemble_id": "ens_001",
            "model_id": "model_001",
            "weight": 1.0,
        }

        response = client.post(
            "/api/ensemble/ens_001/models",
            json={
                "model_id": "model_001",
                "consortium_id": "cons_001",
                "model_type": "classifier",
                "weight": 1.0,
            },
        )

        assert response.status_code == 200
        assert response.json()["entry_id"] == "entry_001"

    def test_add_model_custom_weight(self, client, mock_manager):
        """Test adding model with custom weight."""
        mock_manager.add_model_to_ensemble.return_value = {
            "entry_id": "entry_002",
            "weight": 2.5,
        }

        response = client.post(
            "/api/ensemble/ens_001/models",
            json={
                "model_id": "model_002",
                "consortium_id": "cons_001",
                "model_type": "regressor",
                "weight": 2.5,
            },
        )

        assert response.status_code == 200
        assert response.json()["weight"] == 2.5

    def test_add_model_ensemble_not_found(self, client, mock_manager):
        """Test adding model to non-existent ensemble."""
        mock_manager.add_model_to_ensemble.side_effect = ValueError("Ensemble not found")

        response = client.post(
            "/api/ensemble/nonexistent/models",
            json={
                "model_id": "model_001",
                "consortium_id": "cons_001",
                "model_type": "classifier",
                "weight": 1.0,
            },
        )

        assert response.status_code == 404


class TestGetEnsemble:
    """Tests for GET /api/ensemble/{ensemble_id} endpoint."""

    def test_get_ensemble_success(self, client, mock_manager):
        """Test getting ensemble details."""
        mock_manager.get_ensemble.return_value = {
            "id": "ens_001",
            "name": "Test Ensemble",
            "ensemble_type": "voting",
            "models": [
                {"id": "m1", "model_id": "model_001"},
                {"id": "m2", "model_id": "model_002"},
            ],
        }

        response = client.get("/api/ensemble/ens_001")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "ens_001"
        assert len(data["models"]) == 2

    def test_get_ensemble_not_found(self, client, mock_manager):
        """Test getting non-existent ensemble."""
        mock_manager.get_ensemble.return_value = None

        response = client.get("/api/ensemble/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestListEnsembles:
    """Tests for GET /api/ensemble endpoint."""

    def test_list_ensembles_success(self, client, mock_manager):
        """Test listing ensembles."""
        mock_manager.list_ensembles.return_value = [
            {"id": "ens_001", "name": "Ensemble 1"},
            {"id": "ens_002", "name": "Ensemble 2"},
        ]

        response = client.get("/api/ensemble")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["ensembles"]) == 2

    def test_list_ensembles_with_status_filter(self, client, mock_manager):
        """Test listing ensembles with status filter."""
        mock_manager.list_ensembles.return_value = [
            {"id": "ens_001", "status": "active"},
        ]

        response = client.get("/api/ensemble", params={"status": "active"})

        assert response.status_code == 200
        mock_manager.list_ensembles.assert_called_once()

    def test_list_ensembles_with_limit(self, client, mock_manager):
        """Test listing ensembles with custom limit."""
        mock_manager.list_ensembles.return_value = []

        response = client.get("/api/ensemble", params={"limit": 10})

        assert response.status_code == 200
        mock_manager.list_ensembles.assert_called_with(
            owner_id="company_001", status=None, limit=10
        )

    def test_list_ensembles_empty(self, client, mock_manager):
        """Test listing when no ensembles exist."""
        mock_manager.list_ensembles.return_value = []

        response = client.get("/api/ensemble")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["ensembles"] == []


class TestActivateEnsemble:
    """Tests for POST /api/ensemble/{ensemble_id}/activate endpoint."""

    def test_activate_ensemble_success(self, client, mock_manager):
        """Test successfully activating an ensemble."""
        mock_manager.activate_ensemble.return_value = {
            "ensemble_id": "ens_001",
            "status": "active",
            "message": "Ensemble activated",
        }

        response = client.post("/api/ensemble/ens_001/activate")

        assert response.status_code == 200
        assert response.json()["status"] == "active"

    def test_activate_ensemble_not_enough_models(self, client, mock_manager):
        """Test activating ensemble without enough models."""
        mock_manager.activate_ensemble.side_effect = ValueError(
            "Ensemble needs at least 2 models"
        )

        response = client.post("/api/ensemble/ens_001/activate")

        assert response.status_code == 400
        assert "2 models" in response.json()["detail"]

    def test_activate_ensemble_not_found(self, client, mock_manager):
        """Test activating non-existent ensemble."""
        mock_manager.activate_ensemble.side_effect = ValueError("Ensemble not found")

        response = client.post("/api/ensemble/nonexistent/activate")

        assert response.status_code == 400


class TestPredictWithEnsemble:
    """Tests for POST /api/ensemble/{ensemble_id}/predict endpoint."""

    def test_predict_success(self, client, mock_manager):
        """Test successful ensemble prediction."""
        mock_manager.predict_with_ensemble.return_value = {
            "ensemble_id": "ens_001",
            "prediction": 0.85,
            "model_predictions": [
                {"model_id": "m1", "prediction": 0.80},
                {"model_id": "m2", "prediction": 0.90},
            ],
        }

        response = client.post(
            "/api/ensemble/ens_001/predict",
            json={"input_data": {"feature1": 1.0, "feature2": 2.0}},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["prediction"] == 0.85
        assert len(data["model_predictions"]) == 2

    def test_predict_ensemble_not_active(self, client, mock_manager):
        """Test prediction with inactive ensemble."""
        mock_manager.predict_with_ensemble.side_effect = ValueError(
            "Ensemble is not active"
        )

        response = client.post(
            "/api/ensemble/ens_001/predict",
            json={"input_data": {"feature1": 1.0}},
        )

        assert response.status_code == 400
        assert "not active" in response.json()["detail"]

    def test_predict_ensemble_not_found(self, client, mock_manager):
        """Test prediction with non-existent ensemble."""
        mock_manager.predict_with_ensemble.side_effect = ValueError("Ensemble not found")

        response = client.post(
            "/api/ensemble/nonexistent/predict",
            json={"input_data": {"feature1": 1.0}},
        )

        assert response.status_code == 400


class TestGetEnsemblePerformance:
    """Tests for GET /api/ensemble/{ensemble_id}/performance endpoint."""

    def test_get_performance_success(self, client, mock_manager):
        """Test getting ensemble performance metrics."""
        mock_manager.get_ensemble_performance.return_value = {
            "ensemble_id": "ens_001",
            "accuracy": 0.92,
            "prediction_count": 150,
            "avg_latency_ms": 45.2,
        }

        response = client.get("/api/ensemble/ens_001/performance")

        assert response.status_code == 200
        data = response.json()
        assert data["accuracy"] == 0.92
        assert data["prediction_count"] == 150

    def test_get_performance_no_data(self, client, mock_manager):
        """Test getting performance when no data exists."""
        mock_manager.get_ensemble_performance.return_value = {
            "ensemble_id": "ens_001",
            "accuracy": None,
            "prediction_count": 0,
        }

        response = client.get("/api/ensemble/ens_001/performance")

        assert response.status_code == 200
        assert response.json()["prediction_count"] == 0


class TestGetEnsembleStats:
    """Tests for GET /api/ensemble/stats/overview endpoint."""

    def test_get_stats_success(self, client, mock_manager):
        """Test getting ensemble statistics."""
        mock_manager.get_ensemble_stats.return_value = {
            "total_ensembles": 10,
            "active_ensembles": 5,
            "total_predictions": 1000,
            "models_in_ensembles": 25,
        }

        response = client.get("/api/ensemble/stats/overview")

        assert response.status_code == 200
        data = response.json()
        assert data["total_ensembles"] == 10
        assert data["active_ensembles"] == 5

    def test_get_stats_empty(self, client, mock_manager):
        """Test getting stats when no ensembles exist."""
        mock_manager.get_ensemble_stats.return_value = {
            "total_ensembles": 0,
            "active_ensembles": 0,
            "total_predictions": 0,
        }

        response = client.get("/api/ensemble/stats/overview")

        assert response.status_code == 200
        assert response.json()["total_ensembles"] == 0


class TestRemoveModelFromEnsemble:
    """Tests for DELETE /api/ensemble/{ensemble_id}/models/{model_entry_id} endpoint."""

    def test_remove_model_success(self, client, mock_company, mock_manager):
        """Test successfully removing model from ensemble."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"owner_id": "company_001"}
        mock_cursor.rowcount = 1
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_manager._get_connection.return_value = mock_conn

        response = client.delete("/api/ensemble/ens_001/models/entry_001")

        assert response.status_code == 200
        assert response.json()["entry_id"] == "entry_001"

    def test_remove_model_ensemble_not_found(self, client, mock_manager):
        """Test removing model from non-existent ensemble."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_manager._get_connection.return_value = mock_conn

        response = client.delete("/api/ensemble/nonexistent/models/entry_001")

        assert response.status_code == 404

    def test_remove_model_not_owner(self, client, mock_manager):
        """Test removing model when not owner."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"owner_id": "other_company"}
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_manager._get_connection.return_value = mock_conn

        response = client.delete("/api/ensemble/ens_001/models/entry_001")

        assert response.status_code == 403

    def test_remove_model_entry_not_found(self, client, mock_company, mock_manager):
        """Test removing non-existent model entry."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"owner_id": "company_001"}
        mock_cursor.rowcount = 0
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_manager._get_connection.return_value = mock_conn

        response = client.delete("/api/ensemble/ens_001/models/nonexistent")

        assert response.status_code == 404
        assert "Model entry not found" in response.json()["detail"]

    def test_remove_model_server_error(self, client, mock_manager):
        """Test removing model with server error."""
        mock_manager._get_connection.side_effect = Exception("Database error")

        response = client.delete("/api/ensemble/ens_001/models/entry_001")

        assert response.status_code == 500

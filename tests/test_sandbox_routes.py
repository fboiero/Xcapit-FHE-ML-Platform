"""Tests for sandbox API routes."""

import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

# Mock tenseal before importing sdk modules
sys.modules["tenseal"] = MagicMock()

from fastapi import FastAPI
from fastapi.testclient import TestClient

from sdk.api.sandbox_routes import router
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


# ============ Templates Tests ============


class TestListTemplates:
    """Tests for GET /sandbox/templates endpoint."""

    def test_list_templates_success(self, client, mock_manager):
        """Test listing all templates."""
        mock_manager.list_sandbox_templates.return_value = [
            {
                "id": "tpl_fraud",
                "name": "Fraud Detection",
                "description": "Template for fraud detection experiments",
                "industry": "finance",
                "template_type": "fraud_detection",
                "datasets": [{"name": "transactions", "record_count": 10000}],
                "experiments": [{"name": "baseline", "type": "training"}],
            },
            {
                "id": "tpl_credit",
                "name": "Credit Scoring",
                "description": "Template for credit risk assessment",
                "industry": "finance",
                "template_type": "credit_scoring",
                "datasets": [{"name": "applications", "record_count": 5000}],
                "experiments": [{"name": "model_eval", "type": "evaluation"}],
            },
        ]

        response = make_request(client, mock_manager, "get", "/sandbox/templates")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == "tpl_fraud"

    def test_list_templates_with_industry_filter(self, client, mock_manager):
        """Test listing templates filtered by industry."""
        mock_manager.list_sandbox_templates.return_value = []

        response = make_request(
            client,
            mock_manager,
            "get",
            "/sandbox/templates",
            params={"industry": "healthcare"},
        )

        assert response.status_code == 200
        mock_manager.list_sandbox_templates.assert_called_with(industry="healthcare")

    def test_list_templates_empty(self, client, mock_manager):
        """Test listing templates when none exist."""
        mock_manager.list_sandbox_templates.return_value = []

        response = make_request(client, mock_manager, "get", "/sandbox/templates")

        assert response.status_code == 200
        assert response.json() == []


# ============ Sandboxes Tests ============


class TestCreateSandbox:
    """Tests for POST /sandbox/environments endpoint."""

    def test_create_sandbox_success(self, client, mock_manager):
        """Test creating a sandbox."""
        mock_manager.create_sandbox.return_value = {
            "id": "sandbox_001",
            "name": "Test Sandbox",
            "description": "My test sandbox",
            "owner_id": "company_001",
            "owner_name": "Test Company",
            "template_type": "custom",
            "industry": "finance",
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=7)).isoformat(),
            "config": {},
            "dataset_count": 0,
            "experiment_count": 0,
        }

        response = make_request(
            client,
            mock_manager,
            "post",
            "/sandbox/environments",
            json={
                "name": "Test Sandbox",
                "description": "My test sandbox",
                "industry": "finance",
                "expires_days": 7,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "sandbox_001"
        assert data["name"] == "Test Sandbox"

    def test_create_sandbox_with_template(self, client, mock_manager):
        """Test creating sandbox from template."""
        mock_manager.create_sandbox.return_value = {
            "id": "sandbox_002",
            "name": "Fraud Sandbox",
            "description": None,
            "owner_id": "company_001",
            "owner_name": "Test Company",
            "template_type": "fraud_detection",
            "industry": "finance",
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=14)).isoformat(),
            "config": {},
            "dataset_count": 1,
            "experiment_count": 1,
        }

        response = make_request(
            client,
            mock_manager,
            "post",
            "/sandbox/environments",
            json={
                "name": "Fraud Sandbox",
                "template_id": "tpl_fraud",
                "expires_days": 14,
            },
        )

        assert response.status_code == 200
        mock_manager.create_sandbox.assert_called_once()

    def test_create_sandbox_minimal(self, client, mock_manager):
        """Test creating sandbox with minimal data."""
        mock_manager.create_sandbox.return_value = {
            "id": "sandbox_003",
            "name": "Minimal Sandbox",
            "description": None,
            "owner_id": "company_001",
            "owner_name": "Test Company",
            "template_type": "custom",
            "industry": None,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=7)).isoformat(),
            "config": {},
            "dataset_count": 0,
            "experiment_count": 0,
        }

        response = make_request(
            client,
            mock_manager,
            "post",
            "/sandbox/environments",
            json={"name": "Minimal Sandbox"},
        )

        assert response.status_code == 200


class TestListSandboxes:
    """Tests for GET /sandbox/environments endpoint."""

    def test_list_sandboxes_success(self, client, mock_manager):
        """Test listing sandboxes."""
        mock_manager.list_sandboxes.return_value = [
            {"id": "sandbox_001"},
            {"id": "sandbox_002"},
        ]
        mock_manager.get_sandbox.side_effect = [
            {
                "id": "sandbox_001",
                "name": "Sandbox 1",
                "description": None,
                "owner_id": "company_001",
                "owner_name": "Test Company",
                "template_type": "custom",
                "industry": None,
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(days=7)).isoformat(),
                "config": {},
                "dataset_count": 2,
                "experiment_count": 1,
            },
            {
                "id": "sandbox_002",
                "name": "Sandbox 2",
                "description": None,
                "owner_id": "company_001",
                "owner_name": "Test Company",
                "template_type": "fraud_detection",
                "industry": "finance",
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(days=14)).isoformat(),
                "config": {},
                "dataset_count": 1,
                "experiment_count": 3,
            },
        ]

        response = make_request(client, mock_manager, "get", "/sandbox/environments")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_sandboxes_with_status_filter(self, client, mock_manager):
        """Test listing sandboxes with status filter."""
        mock_manager.list_sandboxes.return_value = []

        response = make_request(
            client,
            mock_manager,
            "get",
            "/sandbox/environments",
            params={"status": "active"},
        )

        assert response.status_code == 200
        mock_manager.list_sandboxes.assert_called_with(
            owner_id="company_001", status="active"
        )


class TestGetSandbox:
    """Tests for GET /sandbox/environments/{sandbox_id} endpoint."""

    def test_get_sandbox_success(self, client, mock_manager):
        """Test getting a specific sandbox."""
        mock_manager.get_sandbox.return_value = {
            "id": "sandbox_001",
            "name": "Test Sandbox",
            "description": "My sandbox",
            "owner_id": "company_001",
            "owner_name": "Test Company",
            "template_type": "custom",
            "industry": "finance",
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=7)).isoformat(),
            "config": {"key": "value"},
            "dataset_count": 3,
            "experiment_count": 2,
        }

        response = make_request(
            client, mock_manager, "get", "/sandbox/environments/sandbox_001"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "sandbox_001"
        assert data["dataset_count"] == 3

    def test_get_sandbox_not_found(self, client, mock_manager):
        """Test getting non-existent sandbox."""
        mock_manager.get_sandbox.return_value = None

        response = make_request(
            client, mock_manager, "get", "/sandbox/environments/nonexistent"
        )

        assert response.status_code == 404

    def test_get_sandbox_not_owner(self, client, mock_manager):
        """Test getting sandbox owned by another company."""
        mock_manager.get_sandbox.return_value = {
            "id": "sandbox_001",
            "owner_id": "other_company",
        }

        response = make_request(
            client, mock_manager, "get", "/sandbox/environments/sandbox_001"
        )

        assert response.status_code == 403


class TestDeleteSandbox:
    """Tests for DELETE /sandbox/environments/{sandbox_id} endpoint."""

    def test_delete_sandbox_success(self, client, mock_manager):
        """Test deleting a sandbox."""
        mock_manager.delete_sandbox.return_value = True

        response = make_request(
            client, mock_manager, "delete", "/sandbox/environments/sandbox_001"
        )

        assert response.status_code == 200
        assert response.json()["status"] == "deleted"
        mock_manager.delete_sandbox.assert_called_with("sandbox_001", "company_001")

    def test_delete_sandbox_not_found(self, client, mock_manager):
        """Test deleting non-existent sandbox."""
        mock_manager.delete_sandbox.return_value = False

        response = make_request(
            client, mock_manager, "delete", "/sandbox/environments/nonexistent"
        )

        assert response.status_code == 404


# ============ Datasets Tests ============


class TestGenerateDataset:
    """Tests for POST /sandbox/environments/{sandbox_id}/datasets endpoint."""

    def test_generate_dataset_success(self, client, mock_manager):
        """Test generating a dataset."""
        mock_manager.get_sandbox.return_value = {
            "id": "sandbox_001",
            "owner_id": "company_001",
        }
        mock_manager.generate_synthetic_dataset.return_value = {
            "id": "dataset_001",
            "sandbox_id": "sandbox_001",
            "name": "Transaction Data",
            "description": "Synthetic transaction data",
            "dataset_type": "transactions",
            "industry": "finance",
            "record_count": 5000,
            "feature_count": 15,
            "features": [
                {"name": "amount", "type": "float"},
                {"name": "merchant", "type": "string"},
            ],
            "statistics": {"mean_amount": 150.0},
            "created_at": datetime.now().isoformat(),
            "data_preview": [{"amount": 100.0, "merchant": "Store A"}],
        }

        response = make_request(
            client,
            mock_manager,
            "post",
            "/sandbox/environments/sandbox_001/datasets",
            json={
                "name": "Transaction Data",
                "dataset_type": "transactions",
                "record_count": 5000,
                "description": "Synthetic transaction data",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "dataset_001"
        assert data["record_count"] == 5000

    def test_generate_dataset_sandbox_not_found(self, client, mock_manager):
        """Test generating dataset in non-existent sandbox."""
        mock_manager.get_sandbox.return_value = None

        response = make_request(
            client,
            mock_manager,
            "post",
            "/sandbox/environments/nonexistent/datasets",
            json={
                "name": "Test Data",
                "dataset_type": "generic",
                "record_count": 1000,
            },
        )

        assert response.status_code == 404

    def test_generate_dataset_not_owner(self, client, mock_manager):
        """Test generating dataset in sandbox owned by another."""
        mock_manager.get_sandbox.return_value = {
            "id": "sandbox_001",
            "owner_id": "other_company",
        }

        response = make_request(
            client,
            mock_manager,
            "post",
            "/sandbox/environments/sandbox_001/datasets",
            json={
                "name": "Test Data",
                "dataset_type": "generic",
                "record_count": 1000,
            },
        )

        assert response.status_code == 403


class TestListDatasets:
    """Tests for GET /sandbox/environments/{sandbox_id}/datasets endpoint."""

    def test_list_datasets_success(self, client, mock_manager):
        """Test listing datasets in a sandbox."""
        mock_manager.get_sandbox.return_value = {
            "id": "sandbox_001",
            "owner_id": "company_001",
        }
        mock_manager.list_datasets.return_value = [
            {
                "id": "dataset_001",
                "sandbox_id": "sandbox_001",
                "name": "Dataset 1",
                "description": None,
                "dataset_type": "transactions",
                "industry": "finance",
                "record_count": 5000,
                "feature_count": 10,
                "features": [],
                "statistics": {},
                "created_at": datetime.now().isoformat(),
            },
        ]

        response = make_request(
            client, mock_manager, "get", "/sandbox/environments/sandbox_001/datasets"
        )

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_list_datasets_sandbox_not_found(self, client, mock_manager):
        """Test listing datasets in non-existent sandbox."""
        mock_manager.get_sandbox.return_value = None

        response = make_request(
            client, mock_manager, "get", "/sandbox/environments/nonexistent/datasets"
        )

        assert response.status_code == 404

    def test_list_datasets_not_owner(self, client, mock_manager):
        """Test listing datasets in sandbox owned by another."""
        mock_manager.get_sandbox.return_value = {
            "id": "sandbox_001",
            "owner_id": "other_company",
        }

        response = make_request(
            client, mock_manager, "get", "/sandbox/environments/sandbox_001/datasets"
        )

        assert response.status_code == 403


class TestGetDataset:
    """Tests for GET /sandbox/datasets/{dataset_id} endpoint."""

    def test_get_dataset_success(self, client, mock_manager):
        """Test getting a specific dataset."""
        mock_manager.get_dataset.return_value = {
            "id": "dataset_001",
            "sandbox_id": "sandbox_001",
            "name": "Transaction Data",
            "description": "Test data",
            "dataset_type": "transactions",
            "industry": "finance",
            "record_count": 5000,
            "feature_count": 15,
            "features": [{"name": "amount", "type": "float"}],
            "statistics": {"mean": 100.0},
            "created_at": datetime.now().isoformat(),
            "data_preview": [{"amount": 50.0}],
        }
        mock_manager.get_sandbox.return_value = {
            "id": "sandbox_001",
            "owner_id": "company_001",
        }

        response = make_request(
            client, mock_manager, "get", "/sandbox/datasets/dataset_001"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "dataset_001"
        assert "data_preview" in data

    def test_get_dataset_not_found(self, client, mock_manager):
        """Test getting non-existent dataset."""
        mock_manager.get_dataset.return_value = None

        response = make_request(
            client, mock_manager, "get", "/sandbox/datasets/nonexistent"
        )

        assert response.status_code == 404

    def test_get_dataset_not_owner(self, client, mock_manager):
        """Test getting dataset from sandbox owned by another."""
        mock_manager.get_dataset.return_value = {
            "id": "dataset_001",
            "sandbox_id": "sandbox_001",
        }
        mock_manager.get_sandbox.return_value = {
            "id": "sandbox_001",
            "owner_id": "other_company",
        }

        response = make_request(
            client, mock_manager, "get", "/sandbox/datasets/dataset_001"
        )

        assert response.status_code == 403


class TestDeleteDataset:
    """Tests for DELETE /sandbox/datasets/{dataset_id} endpoint."""

    def test_delete_dataset_success(self, client, mock_manager):
        """Test deleting a dataset."""
        mock_manager.delete_dataset.return_value = True

        response = make_request(
            client, mock_manager, "delete", "/sandbox/datasets/dataset_001"
        )

        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

    def test_delete_dataset_not_found(self, client, mock_manager):
        """Test deleting non-existent dataset."""
        mock_manager.delete_dataset.return_value = False

        response = make_request(
            client, mock_manager, "delete", "/sandbox/datasets/nonexistent"
        )

        assert response.status_code == 404


# ============ Experiments Tests ============


class TestCreateExperiment:
    """Tests for POST /sandbox/environments/{sandbox_id}/experiments endpoint."""

    def test_create_experiment_success(self, client, mock_manager):
        """Test creating an experiment."""
        mock_manager.get_sandbox.return_value = {
            "id": "sandbox_001",
            "owner_id": "company_001",
        }
        mock_manager.create_experiment.return_value = {
            "id": "exp_001",
            "sandbox_id": "sandbox_001",
            "name": "Training Experiment",
            "description": "Test training",
            "experiment_type": "training",
            "model_type": "logistic_regression",
            "dataset_id": "dataset_001",
            "dataset_name": "Transaction Data",
            "status": "pending",
            "config": {"learning_rate": 0.01},
            "results": {},
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
        }

        response = make_request(
            client,
            mock_manager,
            "post",
            "/sandbox/environments/sandbox_001/experiments",
            json={
                "name": "Training Experiment",
                "experiment_type": "training",
                "model_type": "logistic_regression",
                "dataset_id": "dataset_001",
                "description": "Test training",
                "config": {"learning_rate": 0.01},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "exp_001"
        assert data["status"] == "pending"

    def test_create_experiment_sandbox_not_found(self, client, mock_manager):
        """Test creating experiment in non-existent sandbox."""
        mock_manager.get_sandbox.return_value = None

        response = make_request(
            client,
            mock_manager,
            "post",
            "/sandbox/environments/nonexistent/experiments",
            json={
                "name": "Test Experiment",
                "experiment_type": "evaluation",
            },
        )

        assert response.status_code == 404

    def test_create_experiment_not_owner(self, client, mock_manager):
        """Test creating experiment in sandbox owned by another."""
        mock_manager.get_sandbox.return_value = {
            "id": "sandbox_001",
            "owner_id": "other_company",
        }

        response = make_request(
            client,
            mock_manager,
            "post",
            "/sandbox/environments/sandbox_001/experiments",
            json={
                "name": "Test Experiment",
                "experiment_type": "evaluation",
            },
        )

        assert response.status_code == 403


class TestListExperiments:
    """Tests for GET /sandbox/environments/{sandbox_id}/experiments endpoint."""

    def test_list_experiments_success(self, client, mock_manager):
        """Test listing experiments in a sandbox."""
        mock_manager.get_sandbox.return_value = {
            "id": "sandbox_001",
            "owner_id": "company_001",
        }
        mock_manager.list_experiments.return_value = [
            {
                "id": "exp_001",
                "sandbox_id": "sandbox_001",
                "name": "Experiment 1",
                "description": None,
                "experiment_type": "training",
                "model_type": "logistic_regression",
                "dataset_id": None,
                "dataset_name": None,
                "status": "completed",
                "config": {},
                "results": {"accuracy": 0.92},
                "created_at": datetime.now().isoformat(),
                "started_at": datetime.now().isoformat(),
                "completed_at": datetime.now().isoformat(),
            },
        ]

        response = make_request(
            client, mock_manager, "get", "/sandbox/environments/sandbox_001/experiments"
        )

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_list_experiments_sandbox_not_found(self, client, mock_manager):
        """Test listing experiments in non-existent sandbox."""
        mock_manager.get_sandbox.return_value = None

        response = make_request(
            client, mock_manager, "get", "/sandbox/environments/nonexistent/experiments"
        )

        assert response.status_code == 404

    def test_list_experiments_not_owner(self, client, mock_manager):
        """Test listing experiments in sandbox owned by another."""
        mock_manager.get_sandbox.return_value = {
            "id": "sandbox_001",
            "owner_id": "other_company",
        }

        response = make_request(
            client, mock_manager, "get", "/sandbox/environments/sandbox_001/experiments"
        )

        assert response.status_code == 403


class TestGetExperiment:
    """Tests for GET /sandbox/experiments/{experiment_id} endpoint."""

    def test_get_experiment_success(self, client, mock_manager):
        """Test getting a specific experiment."""
        mock_manager.get_experiment.return_value = {
            "id": "exp_001",
            "sandbox_id": "sandbox_001",
            "name": "Training Experiment",
            "description": "Test",
            "experiment_type": "training",
            "model_type": "decision_tree",
            "dataset_id": "dataset_001",
            "dataset_name": "Test Data",
            "status": "completed",
            "config": {},
            "results": {"accuracy": 0.88, "f1_score": 0.85},
            "created_at": datetime.now().isoformat(),
            "started_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat(),
        }
        mock_manager.get_sandbox.return_value = {
            "id": "sandbox_001",
            "owner_id": "company_001",
        }

        response = make_request(
            client, mock_manager, "get", "/sandbox/experiments/exp_001"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "exp_001"
        assert data["results"]["accuracy"] == 0.88

    def test_get_experiment_not_found(self, client, mock_manager):
        """Test getting non-existent experiment."""
        mock_manager.get_experiment.return_value = None

        response = make_request(
            client, mock_manager, "get", "/sandbox/experiments/nonexistent"
        )

        assert response.status_code == 404

    def test_get_experiment_not_owner(self, client, mock_manager):
        """Test getting experiment from sandbox owned by another."""
        mock_manager.get_experiment.return_value = {
            "id": "exp_001",
            "sandbox_id": "sandbox_001",
        }
        mock_manager.get_sandbox.return_value = {
            "id": "sandbox_001",
            "owner_id": "other_company",
        }

        response = make_request(
            client, mock_manager, "get", "/sandbox/experiments/exp_001"
        )

        assert response.status_code == 403


class TestRunExperiment:
    """Tests for POST /sandbox/experiments/{experiment_id}/run endpoint."""

    def test_run_experiment_success(self, client, mock_manager):
        """Test running an experiment."""
        mock_manager.get_experiment.return_value = {
            "id": "exp_001",
            "sandbox_id": "sandbox_001",
            "status": "pending",
        }
        mock_manager.get_sandbox.return_value = {
            "id": "sandbox_001",
            "owner_id": "company_001",
        }
        mock_manager.run_experiment.return_value = {
            "id": "exp_001",
            "sandbox_id": "sandbox_001",
            "name": "Training Experiment",
            "description": None,
            "experiment_type": "training",
            "model_type": "logistic_regression",
            "dataset_id": "dataset_001",
            "dataset_name": "Test Data",
            "status": "completed",
            "config": {},
            "results": {"accuracy": 0.95, "training_time": 2.5},
            "created_at": datetime.now().isoformat(),
            "started_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat(),
        }

        response = make_request(
            client, mock_manager, "post", "/sandbox/experiments/exp_001/run"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["results"]["accuracy"] == 0.95

    def test_run_experiment_retry_failed(self, client, mock_manager):
        """Test retrying a failed experiment."""
        mock_manager.get_experiment.return_value = {
            "id": "exp_001",
            "sandbox_id": "sandbox_001",
            "status": "failed",
        }
        mock_manager.get_sandbox.return_value = {
            "id": "sandbox_001",
            "owner_id": "company_001",
        }
        mock_manager.run_experiment.return_value = {
            "id": "exp_001",
            "sandbox_id": "sandbox_001",
            "name": "Experiment",
            "description": None,
            "experiment_type": "training",
            "model_type": None,
            "dataset_id": None,
            "dataset_name": None,
            "status": "completed",
            "config": {},
            "results": {},
            "created_at": datetime.now().isoformat(),
            "started_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat(),
        }

        response = make_request(
            client, mock_manager, "post", "/sandbox/experiments/exp_001/run"
        )

        assert response.status_code == 200

    def test_run_experiment_not_found(self, client, mock_manager):
        """Test running non-existent experiment."""
        mock_manager.get_experiment.return_value = None

        response = make_request(
            client, mock_manager, "post", "/sandbox/experiments/nonexistent/run"
        )

        assert response.status_code == 404

    def test_run_experiment_not_owner(self, client, mock_manager):
        """Test running experiment from sandbox owned by another."""
        mock_manager.get_experiment.return_value = {
            "id": "exp_001",
            "sandbox_id": "sandbox_001",
            "status": "pending",
        }
        mock_manager.get_sandbox.return_value = {
            "id": "sandbox_001",
            "owner_id": "other_company",
        }

        response = make_request(
            client, mock_manager, "post", "/sandbox/experiments/exp_001/run"
        )

        assert response.status_code == 403

    def test_run_experiment_wrong_state(self, client, mock_manager):
        """Test running experiment in wrong state."""
        mock_manager.get_experiment.return_value = {
            "id": "exp_001",
            "sandbox_id": "sandbox_001",
            "status": "running",  # Not pending or failed
        }
        mock_manager.get_sandbox.return_value = {
            "id": "sandbox_001",
            "owner_id": "company_001",
        }

        response = make_request(
            client, mock_manager, "post", "/sandbox/experiments/exp_001/run"
        )

        assert response.status_code == 400
        assert "cannot be run" in response.json()["detail"].lower()


class TestDeleteExperiment:
    """Tests for DELETE /sandbox/experiments/{experiment_id} endpoint."""

    def test_delete_experiment_success(self, client, mock_manager):
        """Test deleting an experiment."""
        mock_manager.delete_experiment.return_value = True

        response = make_request(
            client, mock_manager, "delete", "/sandbox/experiments/exp_001"
        )

        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

    def test_delete_experiment_not_found(self, client, mock_manager):
        """Test deleting non-existent experiment."""
        mock_manager.delete_experiment.return_value = False

        response = make_request(
            client, mock_manager, "delete", "/sandbox/experiments/nonexistent"
        )

        assert response.status_code == 404


# ============ Statistics Tests ============


class TestGetSandboxStats:
    """Tests for GET /sandbox/stats endpoint."""

    def test_get_stats_success(self, client, mock_manager):
        """Test getting sandbox statistics."""
        mock_manager.get_sandbox_stats.return_value = {
            "total_sandboxes": 5,
            "active_sandboxes": 3,
            "total_datasets": 15,
            "total_experiments": 25,
            "completed_experiments": 20,
        }

        response = make_request(client, mock_manager, "get", "/sandbox/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_sandboxes"] == 5
        assert data["active_sandboxes"] == 3
        assert data["completed_experiments"] == 20


# ============ Validation Tests ============


class TestSandboxValidation:
    """Tests for input validation in sandbox routes."""

    def test_create_sandbox_name_too_long(self, client, mock_manager):
        """Test creating sandbox with name too long."""
        response = make_request(
            client,
            mock_manager,
            "post",
            "/sandbox/environments",
            json={"name": "x" * 101},  # Max is 100
        )

        assert response.status_code == 422

    def test_create_sandbox_expires_days_too_high(self, client, mock_manager):
        """Test creating sandbox with expires_days > 30."""
        response = make_request(
            client,
            mock_manager,
            "post",
            "/sandbox/environments",
            json={"name": "Test", "expires_days": 31},  # Max is 30
        )

        assert response.status_code == 422

    def test_create_sandbox_expires_days_too_low(self, client, mock_manager):
        """Test creating sandbox with expires_days < 1."""
        response = make_request(
            client,
            mock_manager,
            "post",
            "/sandbox/environments",
            json={"name": "Test", "expires_days": 0},  # Min is 1
        )

        assert response.status_code == 422

    def test_generate_dataset_record_count_too_low(self, client, mock_manager):
        """Test generating dataset with record_count < 100."""
        mock_manager.get_sandbox.return_value = {
            "id": "sandbox_001",
            "owner_id": "company_001",
        }

        response = make_request(
            client,
            mock_manager,
            "post",
            "/sandbox/environments/sandbox_001/datasets",
            json={
                "name": "Test",
                "dataset_type": "generic",
                "record_count": 50,  # Min is 100
            },
        )

        assert response.status_code == 422

    def test_generate_dataset_record_count_too_high(self, client, mock_manager):
        """Test generating dataset with record_count > 100000."""
        mock_manager.get_sandbox.return_value = {
            "id": "sandbox_001",
            "owner_id": "company_001",
        }

        response = make_request(
            client,
            mock_manager,
            "post",
            "/sandbox/environments/sandbox_001/datasets",
            json={
                "name": "Test",
                "dataset_type": "generic",
                "record_count": 150000,  # Max is 100000
            },
        )

        assert response.status_code == 422

    def test_create_experiment_name_empty(self, client, mock_manager):
        """Test creating experiment with empty name."""
        mock_manager.get_sandbox.return_value = {
            "id": "sandbox_001",
            "owner_id": "company_001",
        }

        response = make_request(
            client,
            mock_manager,
            "post",
            "/sandbox/environments/sandbox_001/experiments",
            json={
                "name": "",  # Empty
                "experiment_type": "training",
            },
        )

        assert response.status_code == 422

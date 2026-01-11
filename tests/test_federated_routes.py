"""Tests for federated inference API routes."""

import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

# Mock tenseal before importing sdk modules
sys.modules["tenseal"] = MagicMock()

from fastapi import FastAPI
from fastapi.testclient import TestClient

from sdk.api.federated_routes import router
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


# ============ Inference Endpoints Tests ============


class TestCreateEndpoint:
    """Tests for POST /federated/endpoints endpoint."""

    def test_create_endpoint_success(self, client, mock_manager):
        """Test successful endpoint creation."""
        mock_manager.create_inference_endpoint.return_value = {
            "id": "ep_001",
            "consortium_id": "cons_001",
            "company_id": "company_001",
            "company_name": "Test Company",
            "name": "Test Endpoint",
            "description": "Test description",
            "model_id": "model_001",
            "model_name": "Test Model",
            "endpoint_type": "realtime",
            "status": "active",
            "url": "https://api.example.com/ep_001",
            "config": {},
            "request_count": 0,
            "avg_latency_ms": 0.0,
            "created_at": datetime.now().isoformat(),
            "updated_at": None,
        }

        response = make_request(
            client,
            mock_manager,
            "post",
            "/federated/endpoints",
            json={
                "consortium_id": "cons_001",
                "name": "Test Endpoint",
                "description": "Test description",
                "model_id": "model_001",
                "endpoint_type": "realtime",
            },
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Test Endpoint"

    def test_create_endpoint_batch_type(self, client, mock_manager):
        """Test creating batch endpoint."""
        mock_manager.create_inference_endpoint.return_value = {
            "id": "ep_002",
            "consortium_id": "cons_001",
            "company_id": "company_001",
            "company_name": None,
            "name": "Batch Endpoint",
            "description": None,
            "model_id": None,
            "model_name": None,
            "endpoint_type": "batch",
            "status": "active",
            "url": None,
            "config": {},
            "request_count": 0,
            "avg_latency_ms": 0.0,
            "created_at": datetime.now().isoformat(),
            "updated_at": None,
        }

        response = make_request(
            client,
            mock_manager,
            "post",
            "/federated/endpoints",
            json={
                "consortium_id": "cons_001",
                "name": "Batch Endpoint",
                "endpoint_type": "batch",
            },
        )

        assert response.status_code == 200
        assert response.json()["endpoint_type"] == "batch"


class TestListEndpoints:
    """Tests for GET /federated/endpoints endpoint."""

    def test_list_endpoints_success(self, client, mock_manager):
        """Test listing endpoints."""
        mock_manager.list_inference_endpoints.return_value = [
            {
                "id": "ep_001",
                "consortium_id": "cons_001",
                "company_id": "company_001",
                "company_name": "Test Company",
                "name": "Endpoint 1",
                "description": None,
                "model_id": None,
                "model_name": None,
                "endpoint_type": "realtime",
                "status": "active",
                "url": None,
                "config": {},
                "request_count": 10,
                "avg_latency_ms": 50.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": None,
            },
        ]

        response = make_request(client, mock_manager, "get", "/federated/endpoints")

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_list_endpoints_with_filters(self, client, mock_manager):
        """Test listing endpoints with filters."""
        mock_manager.list_inference_endpoints.return_value = []

        response = make_request(
            client,
            mock_manager,
            "get",
            "/federated/endpoints",
            params={"consortium_id": "cons_001", "status": "active"},
        )

        assert response.status_code == 200


class TestGetEndpoint:
    """Tests for GET /federated/endpoints/{endpoint_id} endpoint."""

    def test_get_endpoint_success(self, client, mock_manager):
        """Test getting endpoint details."""
        mock_manager.get_inference_endpoint.return_value = {
            "id": "ep_001",
            "consortium_id": "cons_001",
            "company_id": "company_001",
            "company_name": "Test Company",
            "name": "Test Endpoint",
            "description": "Description",
            "model_id": "model_001",
            "model_name": "Test Model",
            "endpoint_type": "realtime",
            "status": "active",
            "url": "https://api.example.com/ep_001",
            "config": {},
            "request_count": 100,
            "avg_latency_ms": 45.5,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        response = make_request(
            client, mock_manager, "get", "/federated/endpoints/ep_001"
        )

        assert response.status_code == 200
        assert response.json()["id"] == "ep_001"

    def test_get_endpoint_not_found(self, client, mock_manager):
        """Test getting non-existent endpoint."""
        mock_manager.get_inference_endpoint.return_value = None

        response = make_request(
            client, mock_manager, "get", "/federated/endpoints/nonexistent"
        )

        assert response.status_code == 404

    def test_get_endpoint_not_authorized(self, client, mock_manager):
        """Test getting endpoint owned by another company."""
        mock_manager.get_inference_endpoint.return_value = {
            "id": "ep_001",
            "company_id": "other_company",
        }

        response = make_request(
            client, mock_manager, "get", "/federated/endpoints/ep_001"
        )

        assert response.status_code == 403


class TestDeleteEndpoint:
    """Tests for DELETE /federated/endpoints/{endpoint_id} endpoint."""

    def test_delete_endpoint_success(self, client, mock_manager):
        """Test deleting endpoint."""
        mock_manager.delete_inference_endpoint.return_value = True

        response = make_request(
            client, mock_manager, "delete", "/federated/endpoints/ep_001"
        )

        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

    def test_delete_endpoint_not_found(self, client, mock_manager):
        """Test deleting non-existent endpoint."""
        mock_manager.delete_inference_endpoint.return_value = False

        response = make_request(
            client, mock_manager, "delete", "/federated/endpoints/nonexistent"
        )

        assert response.status_code == 404


# ============ Inference Requests Tests ============


class TestSubmitInference:
    """Tests for POST /federated/endpoints/{endpoint_id}/infer endpoint."""

    def test_submit_inference_success(self, client, mock_manager):
        """Test successful inference submission."""
        mock_manager.get_inference_endpoint.return_value = {
            "id": "ep_001",
            "status": "active",
        }
        mock_manager.submit_inference_request.return_value = {
            "id": "req_001",
            "endpoint_id": "ep_001",
            "requester_id": "company_001",
            "requester_name": "Test Company",
            "status": "pending",
            "priority": "normal",
            "input_hash": "abc123",
            "encryption_key_id": None,
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "latency_ms": None,
        }

        response = make_request(
            client,
            mock_manager,
            "post",
            "/federated/endpoints/ep_001/infer",
            json={
                "input_data": {"feature1": 1.0, "feature2": 2.0},
                "priority": "normal",
            },
        )

        assert response.status_code == 200
        assert response.json()["id"] == "req_001"

    def test_submit_inference_high_priority(self, client, mock_manager):
        """Test submitting high priority inference."""
        mock_manager.get_inference_endpoint.return_value = {"id": "ep_001"}
        mock_manager.submit_inference_request.return_value = {
            "id": "req_002",
            "endpoint_id": "ep_001",
            "requester_id": "company_001",
            "requester_name": None,
            "status": "pending",
            "priority": "high",
            "input_hash": "def456",
            "encryption_key_id": "key_001",
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "latency_ms": None,
        }

        response = make_request(
            client,
            mock_manager,
            "post",
            "/federated/endpoints/ep_001/infer",
            json={
                "input_data": {"x": [1, 2, 3]},
                "priority": "high",
                "encryption_key_id": "key_001",
            },
        )

        assert response.status_code == 200
        assert response.json()["priority"] == "high"

    def test_submit_inference_endpoint_not_found(self, client, mock_manager):
        """Test submitting to non-existent endpoint."""
        mock_manager.get_inference_endpoint.return_value = None

        response = make_request(
            client,
            mock_manager,
            "post",
            "/federated/endpoints/nonexistent/infer",
            json={"input_data": {"x": 1}},
        )

        assert response.status_code == 404


class TestListInferenceRequests:
    """Tests for GET /federated/requests endpoint."""

    def test_list_requests_success(self, client, mock_manager):
        """Test listing inference requests."""
        mock_manager.list_inference_requests.return_value = [
            {
                "id": "req_001",
                "endpoint_id": "ep_001",
                "requester_id": "company_001",
                "requester_name": "Test Company",
                "status": "completed",
                "priority": "normal",
                "input_hash": "abc123",
                "encryption_key_id": None,
                "created_at": datetime.now().isoformat(),
                "started_at": datetime.now().isoformat(),
                "completed_at": datetime.now().isoformat(),
                "latency_ms": 50.0,
            },
        ]

        response = make_request(client, mock_manager, "get", "/federated/requests")

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_list_requests_with_filters(self, client, mock_manager):
        """Test listing requests with filters."""
        mock_manager.list_inference_requests.return_value = []

        response = make_request(
            client,
            mock_manager,
            "get",
            "/federated/requests",
            params={"endpoint_id": "ep_001", "status": "pending"},
        )

        assert response.status_code == 200


class TestGetInferenceRequest:
    """Tests for GET /federated/requests/{request_id} endpoint."""

    def test_get_request_success(self, client, mock_manager):
        """Test getting inference request details."""
        mock_manager.get_inference_request.return_value = {
            "id": "req_001",
            "endpoint_id": "ep_001",
            "requester_id": "company_001",
            "requester_name": "Test Company",
            "status": "completed",
            "priority": "normal",
            "input_hash": "abc123",
            "encryption_key_id": None,
            "created_at": datetime.now().isoformat(),
            "started_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat(),
            "latency_ms": 45.0,
        }

        response = make_request(
            client, mock_manager, "get", "/federated/requests/req_001"
        )

        assert response.status_code == 200
        assert response.json()["id"] == "req_001"

    def test_get_request_not_found(self, client, mock_manager):
        """Test getting non-existent request."""
        mock_manager.get_inference_request.return_value = None

        response = make_request(
            client, mock_manager, "get", "/federated/requests/nonexistent"
        )

        assert response.status_code == 404

    def test_get_request_not_authorized(self, client, mock_manager):
        """Test getting request owned by another company."""
        mock_manager.get_inference_request.return_value = {
            "id": "req_001",
            "requester_id": "other_company",
        }

        response = make_request(
            client, mock_manager, "get", "/federated/requests/req_001"
        )

        assert response.status_code == 403


class TestGetInferenceResult:
    """Tests for GET /federated/requests/{request_id}/result endpoint."""

    def test_get_result_success(self, client, mock_manager):
        """Test getting inference result."""
        mock_manager.get_inference_request.return_value = {
            "id": "req_001",
            "requester_id": "company_001",
            "status": "completed",
        }
        mock_manager.get_inference_result.return_value = {
            "request_id": "req_001",
            "encrypted_output": "encrypted_data_here",
            "output_metadata": {"model_version": "1.0"},
            "confidence_scores": [0.85, 0.10, 0.05],
            "created_at": datetime.now().isoformat(),
        }

        response = make_request(
            client, mock_manager, "get", "/federated/requests/req_001/result"
        )

        assert response.status_code == 200
        assert response.json()["request_id"] == "req_001"

    def test_get_result_request_not_found(self, client, mock_manager):
        """Test getting result for non-existent request."""
        mock_manager.get_inference_request.return_value = None

        response = make_request(
            client, mock_manager, "get", "/federated/requests/nonexistent/result"
        )

        assert response.status_code == 404

    def test_get_result_not_authorized(self, client, mock_manager):
        """Test getting result for request owned by another company."""
        mock_manager.get_inference_request.return_value = {
            "id": "req_001",
            "requester_id": "other_company",
        }

        response = make_request(
            client, mock_manager, "get", "/federated/requests/req_001/result"
        )

        assert response.status_code == 403

    def test_get_result_not_available(self, client, mock_manager):
        """Test getting result when not available yet."""
        mock_manager.get_inference_request.return_value = {
            "id": "req_001",
            "requester_id": "company_001",
            "status": "pending",
        }
        mock_manager.get_inference_result.return_value = None

        response = make_request(
            client, mock_manager, "get", "/federated/requests/req_001/result"
        )

        assert response.status_code == 404
        assert "not available" in response.json()["detail"]


# ============ Federated Models Tests ============


class TestCreateFederatedModel:
    """Tests for POST /federated/models endpoint."""

    def test_create_model_success(self, client, mock_manager):
        """Test successful model creation."""
        mock_manager.create_federated_model.return_value = {
            "id": "fm_001",
            "consortium_id": "cons_001",
            "name": "Test Model",
            "description": "A test model",
            "model_type": "logistic_regression",
            "version": "1.0.0",
            "status": "draft",
            "config": {},
            "metrics": {},
            "deployment_count": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": None,
        }

        response = make_request(
            client,
            mock_manager,
            "post",
            "/federated/models",
            json={
                "consortium_id": "cons_001",
                "name": "Test Model",
                "model_type": "logistic_regression",
                "description": "A test model",
            },
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Test Model"

    def test_create_model_neural_network(self, client, mock_manager):
        """Test creating neural network model."""
        mock_manager.create_federated_model.return_value = {
            "id": "fm_002",
            "consortium_id": "cons_001",
            "name": "NN Model",
            "description": None,
            "model_type": "neural_network",
            "version": "2.0.0",
            "status": "draft",
            "config": {"layers": [64, 32, 16]},
            "metrics": {},
            "deployment_count": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": None,
        }

        response = make_request(
            client,
            mock_manager,
            "post",
            "/federated/models",
            json={
                "consortium_id": "cons_001",
                "name": "NN Model",
                "model_type": "neural_network",
                "version": "2.0.0",
                "config": {"layers": [64, 32, 16]},
            },
        )

        assert response.status_code == 200
        assert response.json()["model_type"] == "neural_network"


class TestListFederatedModels:
    """Tests for GET /federated/models endpoint."""

    def test_list_models_success(self, client, mock_manager):
        """Test listing federated models."""
        mock_manager.list_federated_models.return_value = [
            {
                "id": "fm_001",
                "consortium_id": "cons_001",
                "name": "Model 1",
                "description": None,
                "model_type": "linear_regression",
                "version": "1.0.0",
                "status": "active",
                "config": {},
                "metrics": {"accuracy": 0.92},
                "deployment_count": 3,
                "created_at": datetime.now().isoformat(),
                "updated_at": None,
            },
        ]

        response = make_request(client, mock_manager, "get", "/federated/models")

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_list_models_with_filters(self, client, mock_manager):
        """Test listing models with filters."""
        mock_manager.list_federated_models.return_value = []

        response = make_request(
            client,
            mock_manager,
            "get",
            "/federated/models",
            params={"consortium_id": "cons_001", "status": "active"},
        )

        assert response.status_code == 200


class TestGetFederatedModel:
    """Tests for GET /federated/models/{model_id} endpoint."""

    def test_get_model_success(self, client, mock_manager):
        """Test getting model details."""
        mock_manager.get_federated_model.return_value = {
            "id": "fm_001",
            "consortium_id": "cons_001",
            "name": "Test Model",
            "description": "Description",
            "model_type": "xgboost",
            "version": "1.0.0",
            "status": "active",
            "config": {},
            "metrics": {"accuracy": 0.95, "f1": 0.93},
            "deployment_count": 5,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        response = make_request(
            client, mock_manager, "get", "/federated/models/fm_001"
        )

        assert response.status_code == 200
        assert response.json()["id"] == "fm_001"

    def test_get_model_not_found(self, client, mock_manager):
        """Test getting non-existent model."""
        mock_manager.get_federated_model.return_value = None

        response = make_request(
            client, mock_manager, "get", "/federated/models/nonexistent"
        )

        assert response.status_code == 404


# ============ Edge Nodes Tests ============


class TestRegisterEdgeNode:
    """Tests for POST /federated/nodes endpoint."""

    def test_register_node_success(self, client, mock_manager):
        """Test successful node registration."""
        mock_manager.register_edge_node.return_value = {
            "id": "node_001",
            "company_id": "company_001",
            "company_name": "Test Company",
            "name": "Edge Node 1",
            "node_type": "on_premise",
            "location": "US-East",
            "status": "online",
            "capabilities": {"gpu": True, "memory_gb": 32},
            "deployed_models": [],
            "last_heartbeat": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
        }

        response = make_request(
            client,
            mock_manager,
            "post",
            "/federated/nodes",
            json={
                "name": "Edge Node 1",
                "node_type": "on_premise",
                "location": "US-East",
                "capabilities": {"gpu": True, "memory_gb": 32},
            },
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Edge Node 1"

    def test_register_cloud_node(self, client, mock_manager):
        """Test registering cloud node."""
        mock_manager.register_edge_node.return_value = {
            "id": "node_002",
            "company_id": "company_001",
            "company_name": None,
            "name": "Cloud Node",
            "node_type": "cloud",
            "location": None,
            "status": "online",
            "capabilities": {},
            "deployed_models": [],
            "last_heartbeat": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
        }

        response = make_request(
            client,
            mock_manager,
            "post",
            "/federated/nodes",
            json={"name": "Cloud Node", "node_type": "cloud"},
        )

        assert response.status_code == 200
        assert response.json()["node_type"] == "cloud"


class TestListEdgeNodes:
    """Tests for GET /federated/nodes endpoint."""

    def test_list_nodes_success(self, client, mock_manager):
        """Test listing edge nodes."""
        mock_manager.list_edge_nodes.return_value = [
            {
                "id": "node_001",
                "company_id": "company_001",
                "company_name": "Test Company",
                "name": "Node 1",
                "node_type": "on_premise",
                "location": "US-East",
                "status": "online",
                "capabilities": {},
                "deployed_models": ["fm_001"],
                "last_heartbeat": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat(),
            },
        ]

        response = make_request(client, mock_manager, "get", "/federated/nodes")

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_list_nodes_with_status_filter(self, client, mock_manager):
        """Test listing nodes with status filter."""
        mock_manager.list_edge_nodes.return_value = []

        response = make_request(
            client,
            mock_manager,
            "get",
            "/federated/nodes",
            params={"status": "online"},
        )

        assert response.status_code == 200


class TestGetEdgeNode:
    """Tests for GET /federated/nodes/{node_id} endpoint."""

    def test_get_node_success(self, client, mock_manager):
        """Test getting node details."""
        mock_manager.get_edge_node.return_value = {
            "id": "node_001",
            "company_id": "company_001",
            "company_name": "Test Company",
            "name": "Edge Node 1",
            "node_type": "on_premise",
            "location": "US-East",
            "status": "online",
            "capabilities": {"gpu": True},
            "deployed_models": ["fm_001", "fm_002"],
            "last_heartbeat": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
        }

        response = make_request(
            client, mock_manager, "get", "/federated/nodes/node_001"
        )

        assert response.status_code == 200
        assert response.json()["id"] == "node_001"

    def test_get_node_not_found(self, client, mock_manager):
        """Test getting non-existent node."""
        mock_manager.get_edge_node.return_value = None

        response = make_request(
            client, mock_manager, "get", "/federated/nodes/nonexistent"
        )

        assert response.status_code == 404

    def test_get_node_not_authorized(self, client, mock_manager):
        """Test getting node owned by another company."""
        mock_manager.get_edge_node.return_value = {
            "id": "node_001",
            "company_id": "other_company",
        }

        response = make_request(
            client, mock_manager, "get", "/federated/nodes/node_001"
        )

        assert response.status_code == 403


class TestDeployModelToNode:
    """Tests for POST /federated/nodes/{node_id}/deploy endpoint."""

    def test_deploy_model_success(self, client, mock_manager):
        """Test successful model deployment."""
        mock_manager.deploy_model_to_edge.return_value = {
            "id": "node_001",
            "company_id": "company_001",
            "company_name": "Test Company",
            "name": "Edge Node 1",
            "node_type": "on_premise",
            "location": "US-East",
            "status": "online",
            "capabilities": {},
            "deployed_models": ["fm_001", "fm_002"],
            "last_heartbeat": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
        }

        response = make_request(
            client,
            mock_manager,
            "post",
            "/federated/nodes/node_001/deploy",
            json={"model_id": "fm_002"},
        )

        assert response.status_code == 200
        assert "fm_002" in response.json()["deployed_models"]

    def test_deploy_model_node_not_found(self, client, mock_manager):
        """Test deploying to non-existent node."""
        mock_manager.deploy_model_to_edge.return_value = None

        response = make_request(
            client,
            mock_manager,
            "post",
            "/federated/nodes/nonexistent/deploy",
            json={"model_id": "fm_001"},
        )

        assert response.status_code == 404


class TestUpdateNodeHeartbeat:
    """Tests for POST /federated/nodes/{node_id}/heartbeat endpoint."""

    def test_heartbeat_success(self, client, mock_manager):
        """Test successful heartbeat update."""
        mock_manager.get_edge_node.return_value = {
            "id": "node_001",
            "company_id": "company_001",
        }

        response = make_request(
            client, mock_manager, "post", "/federated/nodes/node_001/heartbeat"
        )

        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_heartbeat_node_not_found(self, client, mock_manager):
        """Test heartbeat for non-existent node."""
        mock_manager.get_edge_node.return_value = None

        response = make_request(
            client, mock_manager, "post", "/federated/nodes/nonexistent/heartbeat"
        )

        assert response.status_code == 404

    def test_heartbeat_not_authorized(self, client, mock_manager):
        """Test heartbeat for node owned by another company."""
        mock_manager.get_edge_node.return_value = {
            "id": "node_001",
            "company_id": "other_company",
        }

        response = make_request(
            client, mock_manager, "post", "/federated/nodes/node_001/heartbeat"
        )

        assert response.status_code == 403


class TestDeleteEdgeNode:
    """Tests for DELETE /federated/nodes/{node_id} endpoint."""

    def test_delete_node_success(self, client, mock_manager):
        """Test deleting edge node."""
        mock_manager.delete_edge_node.return_value = True

        response = make_request(
            client, mock_manager, "delete", "/federated/nodes/node_001"
        )

        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

    def test_delete_node_not_found(self, client, mock_manager):
        """Test deleting non-existent node."""
        mock_manager.delete_edge_node.return_value = False

        response = make_request(
            client, mock_manager, "delete", "/federated/nodes/nonexistent"
        )

        assert response.status_code == 404


# ============ Statistics Tests ============


class TestGetFederatedStats:
    """Tests for GET /federated/stats endpoint."""

    def test_get_stats_success(self, client, mock_manager):
        """Test getting federated statistics."""
        mock_manager.get_federated_stats.return_value = {
            "total_endpoints": 10,
            "active_endpoints": 8,
            "total_requests": 1000,
            "completed_requests": 950,
            "total_models": 5,
            "deployed_models": 4,
            "total_edge_nodes": 3,
            "online_edge_nodes": 2,
            "avg_latency_ms": 45.5,
        }

        response = make_request(client, mock_manager, "get", "/federated/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_endpoints"] == 10
        assert data["completed_requests"] == 950

    def test_get_stats_empty(self, client, mock_manager):
        """Test getting stats when no data exists."""
        mock_manager.get_federated_stats.return_value = {
            "total_endpoints": 0,
            "active_endpoints": 0,
            "total_requests": 0,
            "completed_requests": 0,
            "total_models": 0,
            "deployed_models": 0,
            "total_edge_nodes": 0,
            "online_edge_nodes": 0,
            "avg_latency_ms": 0.0,
        }

        response = make_request(client, mock_manager, "get", "/federated/stats")

        assert response.status_code == 200
        assert response.json()["total_endpoints"] == 0

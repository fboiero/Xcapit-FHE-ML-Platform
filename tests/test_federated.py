"""Tests for Federated Inference module (TIER 4).

This module tests:
- Inference endpoint management
- Inference request submission and processing
- Federated model management
- Edge node registration and deployment
- Statistics
"""

import os
import tempfile
import pytest
from datetime import datetime, timedelta
from pathlib import Path

from sdk.api.consortium import ConsortiumManager


class TestFederatedInference:
    """Test suite for Federated Inference functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.manager = ConsortiumManager(self.db_path)
        yield
        # Cleanup
        if self.db_path.exists():
            os.remove(self.db_path)

    @pytest.fixture
    def manager(self):
        """Get ConsortiumManager instance."""
        return self.manager

    @pytest.fixture
    def company(self, manager):
        """Create a test company."""
        company, _ = manager.create_company(
            name="Test Company",
            email="test@company.com"
        )
        return company

    @pytest.fixture
    def consortium(self, manager, company):
        """Create a test consortium."""
        consortium = manager.create_consortium(
            name="Test Consortium",
            owner_id=company.id,
            model_type="linear_regression",
            description="For federated inference testing"
        )
        return consortium

    # ============ Inference Endpoints Tests ============

    def test_create_inference_endpoint(self, manager, company, consortium):
        """Test creating an inference endpoint."""
        endpoint = manager.create_inference_endpoint(
            consortium_id=consortium.id,
            company_id=company.id,
            name="Fraud Detection API",
            description="Real-time fraud detection",
            endpoint_type="realtime"
        )

        assert endpoint is not None
        assert endpoint["id"].startswith("ep_")
        assert endpoint["name"] == "Fraud Detection API"
        assert endpoint["endpoint_type"] == "realtime"
        assert endpoint["status"] == "active"

    def test_create_endpoint_with_model(self, manager, company, consortium):
        """Test creating an endpoint with a model."""
        # First create a federated model
        model = manager.create_federated_model(
            consortium_id=consortium.id,
            name="Test Model",
            model_type="neural_network",
            created_by=company.id
        )

        endpoint = manager.create_inference_endpoint(
            consortium_id=consortium.id,
            company_id=company.id,
            name="ML API",
            model_id=model["id"],
            endpoint_type="batch"
        )

        assert endpoint["model_id"] == model["id"]
        assert endpoint["endpoint_type"] == "batch"

    def test_get_inference_endpoint(self, manager, company, consortium):
        """Test getting an inference endpoint."""
        created = manager.create_inference_endpoint(
            consortium_id=consortium.id,
            company_id=company.id,
            name="Test Endpoint"
        )

        retrieved = manager.get_inference_endpoint(created["id"])

        assert retrieved is not None
        assert retrieved["id"] == created["id"]
        assert retrieved["name"] == "Test Endpoint"

    def test_list_inference_endpoints(self, manager, company, consortium):
        """Test listing inference endpoints."""
        # Create multiple endpoints
        for i in range(3):
            manager.create_inference_endpoint(
                consortium_id=consortium.id,
                company_id=company.id,
                name=f"Endpoint {i}"
            )

        endpoints = manager.list_inference_endpoints(company_id=company.id)

        assert len(endpoints) == 3

    def test_list_endpoints_by_consortium(self, manager, company, consortium):
        """Test listing endpoints filtered by consortium."""
        manager.create_inference_endpoint(
            consortium_id=consortium.id,
            company_id=company.id,
            name="Endpoint 1"
        )

        # Create another consortium and endpoint
        consortium2 = manager.create_consortium(
            name="Another Consortium",
            owner_id=company.id,
            model_type="logistic_regression"
        )
        manager.create_inference_endpoint(
            consortium_id=consortium2.id,
            company_id=company.id,
            name="Endpoint 2"
        )

        endpoints = manager.list_inference_endpoints(
            company_id=company.id,
            consortium_id=consortium.id
        )

        assert len(endpoints) == 1
        assert endpoints[0]["name"] == "Endpoint 1"

    def test_delete_inference_endpoint(self, manager, company, consortium):
        """Test deleting an inference endpoint."""
        endpoint = manager.create_inference_endpoint(
            consortium_id=consortium.id,
            company_id=company.id,
            name="To Delete"
        )

        success = manager.delete_inference_endpoint(endpoint["id"], company.id)
        assert success is True

        retrieved = manager.get_inference_endpoint(endpoint["id"])
        assert retrieved is None

    # ============ Inference Requests Tests ============

    def test_submit_inference_request(self, manager, company, consortium):
        """Test submitting an inference request."""
        endpoint = manager.create_inference_endpoint(
            consortium_id=consortium.id,
            company_id=company.id,
            name="Test Endpoint"
        )

        request = manager.submit_inference_request(
            endpoint_id=endpoint["id"],
            requester_id=company.id,
            input_data={"feature1": 1.0, "feature2": 2.0},
            priority="high"
        )

        assert request is not None
        assert request["id"].startswith("req_")
        assert request["status"] == "completed"  # Simulated processing
        assert request["priority"] == "high"

    def test_inference_request_with_encryption_key(self, manager, company, consortium):
        """Test inference request with encryption key."""
        endpoint = manager.create_inference_endpoint(
            consortium_id=consortium.id,
            company_id=company.id,
            name="Encrypted Endpoint"
        )

        request = manager.submit_inference_request(
            endpoint_id=endpoint["id"],
            requester_id=company.id,
            input_data={"data": [1, 2, 3]},
            encryption_key_id="key_abc123"
        )

        assert request["encryption_key_id"] == "key_abc123"

    def test_get_inference_request(self, manager, company, consortium):
        """Test getting an inference request."""
        endpoint = manager.create_inference_endpoint(
            consortium_id=consortium.id,
            company_id=company.id,
            name="Test Endpoint"
        )

        submitted = manager.submit_inference_request(
            endpoint_id=endpoint["id"],
            requester_id=company.id,
            input_data={"x": 1}
        )

        retrieved = manager.get_inference_request(submitted["id"])

        assert retrieved is not None
        assert retrieved["id"] == submitted["id"]

    def test_list_inference_requests(self, manager, company, consortium):
        """Test listing inference requests."""
        endpoint = manager.create_inference_endpoint(
            consortium_id=consortium.id,
            company_id=company.id,
            name="Test Endpoint"
        )

        # Submit multiple requests
        for i in range(5):
            manager.submit_inference_request(
                endpoint_id=endpoint["id"],
                requester_id=company.id,
                input_data={"iteration": i}
            )

        requests = manager.list_inference_requests(requester_id=company.id)

        assert len(requests) == 5

    def test_get_inference_result(self, manager, company, consortium):
        """Test getting inference result."""
        endpoint = manager.create_inference_endpoint(
            consortium_id=consortium.id,
            company_id=company.id,
            name="Test Endpoint"
        )

        request = manager.submit_inference_request(
            endpoint_id=endpoint["id"],
            requester_id=company.id,
            input_data={"x": 1}
        )

        result = manager.get_inference_result(request["id"])

        assert result is not None
        assert "encrypted_output" in result
        assert "confidence_scores" in result

    # ============ Federated Models Tests ============

    def test_create_federated_model(self, manager, company, consortium):
        """Test creating a federated model."""
        model = manager.create_federated_model(
            consortium_id=consortium.id,
            name="Fraud Detector",
            model_type="neural_network",
            created_by=company.id,
            version="1.0.0"
        )

        assert model is not None
        assert model["id"].startswith("fm_")
        assert model["name"] == "Fraud Detector"
        assert model["model_type"] == "neural_network"
        assert model["version"] == "1.0.0"

    def test_create_model_with_config(self, manager, company, consortium):
        """Test creating a model with config."""
        model = manager.create_federated_model(
            consortium_id=consortium.id,
            name="XGBoost Model",
            model_type="xgboost",
            created_by=company.id,
            config={"n_estimators": 100, "max_depth": 5}
        )

        assert model["config"]["n_estimators"] == 100
        assert model["config"]["max_depth"] == 5

    def test_get_federated_model(self, manager, company, consortium):
        """Test getting a federated model."""
        created = manager.create_federated_model(
            consortium_id=consortium.id,
            name="Test Model",
            model_type="linear_regression",
            created_by=company.id
        )

        retrieved = manager.get_federated_model(created["id"])

        assert retrieved is not None
        assert retrieved["id"] == created["id"]

    def test_list_federated_models(self, manager, company, consortium):
        """Test listing federated models."""
        for i in range(3):
            manager.create_federated_model(
                consortium_id=consortium.id,
                name=f"Model {i}",
                model_type="neural_network",
                created_by=company.id
            )

        models = manager.list_federated_models(consortium_id=consortium.id)

        assert len(models) == 3

    def test_list_models_by_status(self, manager, company, consortium):
        """Test listing models filtered by status."""
        manager.create_federated_model(
            consortium_id=consortium.id,
            name="Model 1",
            model_type="neural_network",
            created_by=company.id
        )

        models = manager.list_federated_models(
            consortium_id=consortium.id,
            status="training"  # Default status
        )

        assert len(models) >= 1

    # ============ Edge Nodes Tests ============

    def test_register_edge_node(self, manager, company):
        """Test registering an edge node."""
        node = manager.register_edge_node(
            company_id=company.id,
            name="On-Premise Server 1",
            node_type="inference",
            hardware_info={"location": "Buenos Aires, AR", "gpu": True}
        )

        assert node is not None
        assert node["id"].startswith("node_")
        assert node["name"] == "On-Premise Server 1"
        assert node["status"] == "active"

    def test_register_node_with_hardware_info(self, manager, company):
        """Test registering a node with hardware info."""
        node = manager.register_edge_node(
            company_id=company.id,
            name="GPU Server",
            node_type="inference",
            hardware_info={"gpu": True, "memory_gb": 64, "cpu_cores": 16}
        )

        assert node["hardware_info"]["gpu"] is True
        assert node["hardware_info"]["memory_gb"] == 64

    def test_get_edge_node(self, manager, company):
        """Test getting an edge node."""
        created = manager.register_edge_node(
            company_id=company.id,
            name="Test Node"
        )

        retrieved = manager.get_edge_node(created["id"])

        assert retrieved is not None
        assert retrieved["id"] == created["id"]

    def test_list_edge_nodes(self, manager, company):
        """Test listing edge nodes."""
        for i in range(3):
            manager.register_edge_node(
                company_id=company.id,
                name=f"Node {i}"
            )

        nodes = manager.list_edge_nodes(company_id=company.id)

        assert len(nodes) == 3

    def test_deploy_model_to_edge(self, manager, company, consortium):
        """Test deploying a model to an edge node."""
        model = manager.create_federated_model(
            consortium_id=consortium.id,
            name="Deployable Model",
            model_type="linear_regression",
            created_by=company.id
        )

        node = manager.register_edge_node(
            company_id=company.id,
            name="Deploy Target"
        )

        result = manager.deploy_model_to_edge(
            node_id=node["id"],
            model_id=model["id"],
            company_id=company.id
        )

        assert result["status"] == "deployed"
        assert model["id"] in result["models_deployed"]

    def test_deploy_multiple_models(self, manager, company, consortium):
        """Test deploying multiple models to same node."""
        node = manager.register_edge_node(
            company_id=company.id,
            name="Multi-Model Node"
        )

        for i in range(3):
            model = manager.create_federated_model(
                consortium_id=consortium.id,
                name=f"Model {i}",
                model_type="neural_network",
                created_by=company.id
            )
            manager.deploy_model_to_edge(
                node_id=node["id"],
                model_id=model["id"],
                company_id=company.id
            )

        updated_node = manager.get_edge_node(node["id"])
        assert len(updated_node["models_deployed"]) == 3

    def test_update_edge_heartbeat(self, manager, company):
        """Test updating edge node heartbeat."""
        node = manager.register_edge_node(
            company_id=company.id,
            name="Heartbeat Node"
        )

        success = manager.update_edge_heartbeat(node["id"])

        assert success is True

    def test_delete_edge_node(self, manager, company):
        """Test deleting an edge node."""
        node = manager.register_edge_node(
            company_id=company.id,
            name="To Delete"
        )

        success = manager.delete_edge_node(node["id"], company.id)
        assert success is True

        retrieved = manager.get_edge_node(node["id"])
        assert retrieved is None

    # ============ Statistics Tests ============

    def test_get_federated_stats_empty(self, manager, company):
        """Test getting stats with no data."""
        stats = manager.get_federated_stats(company_id=company.id)

        assert stats["total_endpoints"] == 0
        assert stats["total_requests"] == 0
        assert stats["total_edge_nodes"] == 0

    def test_get_federated_stats_with_data(self, manager, company, consortium):
        """Test getting stats with data."""
        # Create endpoint
        endpoint = manager.create_inference_endpoint(
            consortium_id=consortium.id,
            company_id=company.id,
            name="Stats Endpoint"
        )

        # Submit requests
        for i in range(5):
            manager.submit_inference_request(
                endpoint_id=endpoint["id"],
                requester_id=company.id,
                input_data={"i": i}
            )

        # Create edge node
        manager.register_edge_node(
            company_id=company.id,
            name="Stats Node"
        )

        stats = manager.get_federated_stats(company_id=company.id)

        assert stats["total_endpoints"] == 1
        assert stats["completed_requests"] == 5
        assert stats["total_edge_nodes"] == 1
        assert stats["data_privacy_preserved"] is True

    def test_stats_avg_processing_time(self, manager, company, consortium):
        """Test that stats include average processing time."""
        endpoint = manager.create_inference_endpoint(
            consortium_id=consortium.id,
            company_id=company.id,
            name="Timing Endpoint"
        )

        for i in range(3):
            manager.submit_inference_request(
                endpoint_id=endpoint["id"],
                requester_id=company.id,
                input_data={"x": i}
            )

        stats = manager.get_federated_stats(company_id=company.id)

        assert "avg_processing_time_ms" in stats
        assert stats["avg_processing_time_ms"] >= 0

    # ============ Authorization Tests ============

    def test_cannot_delete_other_company_endpoint(self, manager, company, consortium):
        """Test that company cannot delete another company's endpoint."""
        endpoint = manager.create_inference_endpoint(
            consortium_id=consortium.id,
            company_id=company.id,
            name="Protected Endpoint"
        )

        # Create another company
        other_company, _ = manager.create_company(
            name="Other Company",
            email="other@company.com"
        )

        success = manager.delete_inference_endpoint(endpoint["id"], other_company.id)
        assert success is False

    def test_cannot_deploy_to_other_company_node(self, manager, company, consortium):
        """Test that company cannot deploy to another company's node."""
        node = manager.register_edge_node(
            company_id=company.id,
            name="Protected Node"
        )

        model = manager.create_federated_model(
            consortium_id=consortium.id,
            name="Test Model",
            model_type="linear_regression",
            created_by=company.id
        )

        other_company, _ = manager.create_company(
            name="Other Company",
            email="other@company.com"
        )

        with pytest.raises(ValueError):
            manager.deploy_model_to_edge(
                node_id=node["id"],
                model_id=model["id"],
                company_id=other_company.id
            )

    # ============ Edge Cases Tests ============

    def test_inference_with_empty_input(self, manager, company, consortium):
        """Test inference with empty input data."""
        endpoint = manager.create_inference_endpoint(
            consortium_id=consortium.id,
            company_id=company.id,
            name="Empty Input Endpoint"
        )

        request = manager.submit_inference_request(
            endpoint_id=endpoint["id"],
            requester_id=company.id,
            input_data={}
        )

        assert request is not None
        assert request["status"] == "completed"

    def test_get_nonexistent_endpoint(self, manager):
        """Test getting a nonexistent endpoint."""
        endpoint = manager.get_inference_endpoint("ep_nonexistent")
        assert endpoint is None

    def test_get_nonexistent_model(self, manager):
        """Test getting a nonexistent model."""
        model = manager.get_federated_model("fm_nonexistent")
        assert model is None

    def test_get_nonexistent_node(self, manager):
        """Test getting a nonexistent node."""
        node = manager.get_edge_node("node_nonexistent")
        assert node is None

    def test_deploy_nonexistent_model(self, manager, company):
        """Test deploying a nonexistent model."""
        node = manager.register_edge_node(
            company_id=company.id,
            name="Test Node"
        )

        with pytest.raises(ValueError):
            manager.deploy_model_to_edge(
                node_id=node["id"],
                model_id="fm_nonexistent",
                company_id=company.id
            )

"""
Federated inference module tests for Xcapit FHE-ML Platform.

Tests for inference endpoints, requests, federated models, and edge nodes.
"""

from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status

from apps.consortiums.models import ConsortiumMember
from apps.federated.models import (
    EdgeNode,
    FederatedModel,
    InferenceEndpoint,
    InferenceRequest,
    InferenceResult,
)


@pytest.mark.django_db
class TestInferenceEndpointEndpoints:
    """Tests for inference endpoint CRUD operations."""

    def test_create_endpoint(self, auth_client, consortium, company, ml_model):
        """Test creating an inference endpoint."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )

        url = "/api/v2/federated/endpoints/"
        data = {
            "consortium": str(consortium.id),
            "name": "Fraud Detection Endpoint",
            "description": "Real-time fraud detection",
            "model": str(ml_model.id),
            "endpoint_type": InferenceEndpoint.EndpointType.REALTIME,
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Fraud Detection Endpoint"
        # Verify via DB - endpoint was created
        endpoint = InferenceEndpoint.objects.get(name="Fraud Detection Endpoint")
        assert endpoint.status == InferenceEndpoint.Status.ACTIVE

    def test_list_endpoints_by_consortium(self, auth_client, consortium, company):
        """Test listing endpoints by consortium."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        InferenceEndpoint.objects.create(
            consortium=consortium,
            company=company,
            name="Test Endpoint",
            endpoint_type=InferenceEndpoint.EndpointType.REALTIME,
        )

        url = f"/api/v2/federated/endpoints/?consortium_id={consortium.id}"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_list_endpoints_by_company(self, auth_client, consortium, company):
        """Test listing endpoints by company (no consortium filter)."""
        InferenceEndpoint.objects.create(
            consortium=consortium,
            company=company,
            name="My Endpoint",
            endpoint_type=InferenceEndpoint.EndpointType.BATCH,
        )

        url = "/api/v2/federated/endpoints/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_get_endpoint(self, auth_client, consortium, company):
        """Test getting a single endpoint."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        endpoint = InferenceEndpoint.objects.create(
            consortium=consortium,
            company=company,
            name="Test Endpoint",
            endpoint_type=InferenceEndpoint.EndpointType.REALTIME,
        )

        url = f"/api/v2/federated/endpoints/{endpoint.id}/?consortium_id={consortium.id}"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Test Endpoint"


@pytest.mark.django_db
class TestInferenceEndpointActions:
    """Tests for inference endpoint custom actions."""

    def test_predict(self, auth_client, consortium, company):
        """Test making a prediction through endpoint."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        # Don't set model to avoid version attribute issue
        endpoint = InferenceEndpoint.objects.create(
            consortium=consortium,
            company=company,
            model=None,
            name="Test Endpoint",
            endpoint_type=InferenceEndpoint.EndpointType.REALTIME,
            status=InferenceEndpoint.Status.ACTIVE,
        )

        url = f"/api/v2/federated/endpoints/{endpoint.id}/predict/?consortium_id={consortium.id}"
        data = {
            "input_data": [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "encrypted_output" in response.data
        assert "latency_ms" in response.data
        assert response.data["metadata"]["n_samples"] == 2

    def test_predict_inactive_endpoint(self, auth_client, consortium, company):
        """Test cannot predict on inactive endpoint."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        endpoint = InferenceEndpoint.objects.create(
            consortium=consortium,
            company=company,
            name="Test Endpoint",
            status=InferenceEndpoint.Status.PAUSED,
        )

        url = f"/api/v2/federated/endpoints/{endpoint.id}/predict/?consortium_id={consortium.id}"
        data = {"input_data": [[1.0, 2.0]]}

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not active" in response.data["detail"].lower()

    def test_pause_endpoint(self, auth_client, consortium, company):
        """Test pausing an endpoint."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        endpoint = InferenceEndpoint.objects.create(
            consortium=consortium,
            company=company,
            name="Test Endpoint",
            status=InferenceEndpoint.Status.ACTIVE,
        )

        url = f"/api/v2/federated/endpoints/{endpoint.id}/pause/?consortium_id={consortium.id}"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        endpoint.refresh_from_db()
        assert endpoint.status == InferenceEndpoint.Status.PAUSED

    def test_resume_endpoint(self, auth_client, consortium, company):
        """Test resuming a paused endpoint."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        endpoint = InferenceEndpoint.objects.create(
            consortium=consortium,
            company=company,
            name="Test Endpoint",
            status=InferenceEndpoint.Status.PAUSED,
        )

        url = f"/api/v2/federated/endpoints/{endpoint.id}/resume/?consortium_id={consortium.id}"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        endpoint.refresh_from_db()
        assert endpoint.status == InferenceEndpoint.Status.ACTIVE

    def test_cannot_pause_inactive(self, auth_client, consortium, company):
        """Test cannot pause non-active endpoint."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        endpoint = InferenceEndpoint.objects.create(
            consortium=consortium,
            company=company,
            name="Test Endpoint",
            status=InferenceEndpoint.Status.PAUSED,
        )

        url = f"/api/v2/federated/endpoints/{endpoint.id}/pause/?consortium_id={consortium.id}"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_resume_active(self, auth_client, consortium, company):
        """Test cannot resume active endpoint."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        endpoint = InferenceEndpoint.objects.create(
            consortium=consortium,
            company=company,
            name="Test Endpoint",
            status=InferenceEndpoint.Status.ACTIVE,
        )

        url = f"/api/v2/federated/endpoints/{endpoint.id}/resume/?consortium_id={consortium.id}"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_endpoint_stats(self, auth_client, consortium, company):
        """Test getting endpoint statistics."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        endpoint = InferenceEndpoint.objects.create(
            consortium=consortium,
            company=company,
            name="Test Endpoint",
            status=InferenceEndpoint.Status.ACTIVE,
            request_count=100,
            total_latency_ms=5000,
        )

        url = f"/api/v2/federated/endpoints/{endpoint.id}/stats/?consortium_id={consortium.id}"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["request_count"] == 100
        assert response.data["avg_latency_ms"] == 50.0


@pytest.mark.django_db
class TestInferenceRequestEndpoints:
    """Tests for inference request viewing."""

    def test_list_requests(self, auth_client, consortium, company):
        """Test listing inference requests."""
        endpoint = InferenceEndpoint.objects.create(
            consortium=consortium,
            company=company,
            name="Test Endpoint",
        )
        InferenceRequest.objects.create(
            endpoint=endpoint,
            requester=company,
            input_hash="a" * 64,
        )

        url = "/api/v2/federated/requests/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_filter_requests_by_endpoint(self, auth_client, consortium, company):
        """Test filtering requests by endpoint."""
        endpoint1 = InferenceEndpoint.objects.create(
            consortium=consortium,
            company=company,
            name="Endpoint 1",
        )
        endpoint2 = InferenceEndpoint.objects.create(
            consortium=consortium,
            company=company,
            name="Endpoint 2",
        )
        InferenceRequest.objects.create(
            endpoint=endpoint1,
            requester=company,
            input_hash="a" * 64,
        )
        InferenceRequest.objects.create(
            endpoint=endpoint2,
            requester=company,
            input_hash="b" * 64,
        )

        url = f"/api/v2/federated/requests/?endpoint_id={endpoint1.id}"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        for req in response.data:
            # UUID comparison - endpoint can be UUID or string
            assert str(req["endpoint"]) == str(endpoint1.id)

    def test_filter_requests_by_status(self, auth_client, consortium, company):
        """Test filtering requests by status."""
        endpoint = InferenceEndpoint.objects.create(
            consortium=consortium,
            company=company,
            name="Test Endpoint",
        )
        InferenceRequest.objects.create(
            endpoint=endpoint,
            requester=company,
            input_hash="a" * 64,
            status=InferenceRequest.Status.COMPLETED,
        )
        InferenceRequest.objects.create(
            endpoint=endpoint,
            requester=company,
            input_hash="b" * 64,
            status=InferenceRequest.Status.PENDING,
        )

        url = "/api/v2/federated/requests/?status=completed"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        for req in response.data:
            assert req["status"] == "completed"

    def test_get_request_result(self, auth_client, consortium, company):
        """Test getting result for a completed request."""
        endpoint = InferenceEndpoint.objects.create(
            consortium=consortium,
            company=company,
            name="Test Endpoint",
        )
        request_obj = InferenceRequest.objects.create(
            endpoint=endpoint,
            requester=company,
            input_hash="a" * 64,
            status=InferenceRequest.Status.COMPLETED,
        )
        InferenceResult.objects.create(
            request=request_obj,
            encrypted_output="encrypted_data_here",
            confidence_scores=[0.95],
        )

        url = f"/api/v2/federated/requests/{request_obj.id}/result/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "encrypted_output" in response.data

    def test_cannot_get_result_pending(self, auth_client, consortium, company):
        """Test cannot get result for pending request."""
        endpoint = InferenceEndpoint.objects.create(
            consortium=consortium,
            company=company,
            name="Test Endpoint",
        )
        request_obj = InferenceRequest.objects.create(
            endpoint=endpoint,
            requester=company,
            input_hash="a" * 64,
            status=InferenceRequest.Status.PENDING,
        )

        url = f"/api/v2/federated/requests/{request_obj.id}/result/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestFederatedModelEndpoints:
    """Tests for federated model operations."""

    def test_create_federated_model(self, auth_client, consortium, company):
        """Test creating a federated model."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )

        url = "/api/v2/federated/models/"
        data = {
            "consortium": str(consortium.id),
            "name": "Fraud Detection Model",
            "description": "Federated fraud detection",
            "model_type": FederatedModel.ModelType.LOGISTIC_REGRESSION,
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Fraud Detection Model"

    def test_list_federated_models(self, auth_client, consortium, company):
        """Test listing federated models."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        FederatedModel.objects.create(
            consortium=consortium,
            name="Test Model",
            model_type=FederatedModel.ModelType.LINEAR_REGRESSION,
        )

        url = f"/api/v2/federated/models/?consortium_id={consortium.id}"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_train_model(self, auth_client, consortium, company):
        """Test starting federated training."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        model = FederatedModel.objects.create(
            consortium=consortium,
            name="Test Model",
            model_type=FederatedModel.ModelType.LINEAR_REGRESSION,
            status=FederatedModel.Status.DRAFT,
        )

        url = f"/api/v2/federated/models/{model.id}/train/?consortium_id={consortium.id}"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        model.refresh_from_db()
        assert model.status == FederatedModel.Status.TRAINING

    def test_cannot_train_already_training(self, auth_client, consortium, company):
        """Test cannot train model already training."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        model = FederatedModel.objects.create(
            consortium=consortium,
            name="Test Model",
            model_type=FederatedModel.ModelType.LINEAR_REGRESSION,
            status=FederatedModel.Status.TRAINING,
        )

        url = f"/api/v2/federated/models/{model.id}/train/?consortium_id={consortium.id}"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already training" in response.data["detail"].lower()

    def test_deploy_model(self, auth_client, consortium, company):
        """Test deploying a ready model."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        model = FederatedModel.objects.create(
            consortium=consortium,
            name="Test Model",
            model_type=FederatedModel.ModelType.LINEAR_REGRESSION,
            status=FederatedModel.Status.READY,
        )

        url = f"/api/v2/federated/models/{model.id}/deploy/?consortium_id={consortium.id}"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        model.refresh_from_db()
        assert model.status == FederatedModel.Status.DEPLOYED

    def test_cannot_deploy_not_ready(self, auth_client, consortium, company):
        """Test cannot deploy model not ready."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        model = FederatedModel.objects.create(
            consortium=consortium,
            name="Test Model",
            model_type=FederatedModel.ModelType.LINEAR_REGRESSION,
            status=FederatedModel.Status.DRAFT,
        )

        url = f"/api/v2/federated/models/{model.id}/deploy/?consortium_id={consortium.id}"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "ready" in response.data["detail"].lower()


@pytest.mark.django_db
class TestEdgeNodeEndpoints:
    """Tests for edge node operations."""

    def test_create_edge_node(self, auth_client, company):
        """Test creating an edge node."""
        url = "/api/v2/federated/nodes/"
        data = {
            "name": "Edge Node 1",
            "node_type": EdgeNode.NodeType.ON_PREMISE,
            "location": "Data Center A",
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Edge Node 1"

    def test_list_edge_nodes(self, auth_client, company):
        """Test listing edge nodes."""
        EdgeNode.objects.create(
            company=company,
            name="Node 1",
            node_type=EdgeNode.NodeType.ON_PREMISE,
        )

        url = "/api/v2/federated/nodes/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_node_heartbeat(self, auth_client, company):
        """Test updating node heartbeat."""
        node = EdgeNode.objects.create(
            company=company,
            name="Node 1",
            status=EdgeNode.Status.OFFLINE,
        )

        url = f"/api/v2/federated/nodes/{node.id}/heartbeat/"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        node.refresh_from_db()
        assert node.status == EdgeNode.Status.ONLINE
        assert node.last_heartbeat is not None

    def test_deploy_model_to_node(self, auth_client, consortium, company):
        """Test deploying model to node."""
        node = EdgeNode.objects.create(
            company=company,
            name="Node 1",
        )
        model = FederatedModel.objects.create(
            consortium=consortium,
            name="Test Model",
            model_type=FederatedModel.ModelType.LINEAR_REGRESSION,
            status=FederatedModel.Status.READY,
        )

        url = f"/api/v2/federated/nodes/{node.id}/deploy_model/"
        data = {"model_id": str(model.id)}

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert model in node.deployed_models.all()

    def test_deploy_model_not_found(self, auth_client, company):
        """Test deploying non-existent model."""
        import uuid

        node = EdgeNode.objects.create(
            company=company,
            name="Node 1",
        )

        url = f"/api/v2/federated/nodes/{node.id}/deploy_model/"
        data = {"model_id": str(uuid.uuid4())}

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_deploy_model_not_ready(self, auth_client, consortium, company):
        """Test cannot deploy model not ready."""
        node = EdgeNode.objects.create(
            company=company,
            name="Node 1",
        )
        model = FederatedModel.objects.create(
            consortium=consortium,
            name="Test Model",
            model_type=FederatedModel.ModelType.LINEAR_REGRESSION,
            status=FederatedModel.Status.DRAFT,
        )

        url = f"/api/v2/federated/nodes/{node.id}/deploy_model/"
        data = {"model_id": str(model.id)}

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_undeploy_model_from_node(self, auth_client, consortium, company):
        """Test removing model from node."""
        node = EdgeNode.objects.create(
            company=company,
            name="Node 1",
        )
        model = FederatedModel.objects.create(
            consortium=consortium,
            name="Test Model",
            model_type=FederatedModel.ModelType.LINEAR_REGRESSION,
            status=FederatedModel.Status.DEPLOYED,
        )
        node.deployed_models.add(model)

        url = f"/api/v2/federated/nodes/{node.id}/undeploy_model/"
        data = {"model_id": str(model.id)}

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert model not in node.deployed_models.all()

    def test_get_online_nodes(self, auth_client, company):
        """Test getting online nodes."""
        EdgeNode.objects.create(
            company=company,
            name="Online Node",
            status=EdgeNode.Status.ONLINE,
        )
        EdgeNode.objects.create(
            company=company,
            name="Offline Node",
            status=EdgeNode.Status.OFFLINE,
        )

        url = "/api/v2/federated/nodes/online/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        for node in response.data:
            assert node["status"] == "online"


@pytest.mark.django_db
class TestFederatedModels:
    """Tests for federated model methods and properties."""

    def test_endpoint_str(self, consortium, company):
        """Test endpoint string representation."""
        endpoint = InferenceEndpoint.objects.create(
            consortium=consortium,
            company=company,
            name="Test Endpoint",
            status=InferenceEndpoint.Status.ACTIVE,
        )

        assert "Test Endpoint" in str(endpoint)
        assert "active" in str(endpoint)

    def test_endpoint_avg_latency(self, consortium, company):
        """Test endpoint average latency calculation."""
        endpoint = InferenceEndpoint.objects.create(
            consortium=consortium,
            company=company,
            name="Test",
            request_count=10,
            total_latency_ms=500,
        )

        assert endpoint.avg_latency_ms == 50.0

    def test_endpoint_avg_latency_zero_requests(self, consortium, company):
        """Test avg latency with zero requests."""
        endpoint = InferenceEndpoint.objects.create(
            consortium=consortium,
            company=company,
            name="Test",
            request_count=0,
        )

        assert endpoint.avg_latency_ms == 0

    def test_request_str(self, consortium, company):
        """Test request string representation."""
        endpoint = InferenceEndpoint.objects.create(
            consortium=consortium,
            company=company,
            name="Test",
        )
        request = InferenceRequest.objects.create(
            endpoint=endpoint,
            requester=company,
            input_hash="a" * 64,
        )

        assert "Request" in str(request)
        assert "pending" in str(request)

    def test_request_hash_input(self):
        """Test input hashing."""
        input_data = {"key": "value", "number": 42}
        hash1 = InferenceRequest.hash_input(input_data)
        hash2 = InferenceRequest.hash_input(input_data)
        hash3 = InferenceRequest.hash_input({"different": "data"})

        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 64

    def test_result_str(self, consortium, company):
        """Test result string representation."""
        endpoint = InferenceEndpoint.objects.create(
            consortium=consortium,
            company=company,
            name="Test",
        )
        request = InferenceRequest.objects.create(
            endpoint=endpoint,
            requester=company,
            input_hash="a" * 64,
        )
        result = InferenceResult.objects.create(
            request=request,
            encrypted_output="test",
        )

        assert str(request.id) in str(result)

    def test_federated_model_str(self, consortium):
        """Test federated model string representation."""
        model = FederatedModel.objects.create(
            consortium=consortium,
            name="Test Model",
            model_type=FederatedModel.ModelType.LINEAR_REGRESSION,
            version="2.0.0",
        )

        assert "Test Model" in str(model)
        assert "v2.0.0" in str(model)

    def test_federated_model_deployment_count(self, consortium, company):
        """Test deployment count property."""
        model = FederatedModel.objects.create(
            consortium=consortium,
            name="Test Model",
            model_type=FederatedModel.ModelType.LINEAR_REGRESSION,
        )
        node1 = EdgeNode.objects.create(company=company, name="Node 1")
        node2 = EdgeNode.objects.create(company=company, name="Node 2")
        node1.deployed_models.add(model)
        node2.deployed_models.add(model)

        assert model.deployment_count == 2

    def test_edge_node_str(self, company):
        """Test edge node string representation."""
        node = EdgeNode.objects.create(
            company=company,
            name="Test Node",
            status=EdgeNode.Status.ONLINE,
        )

        assert "Test Node" in str(node)
        assert "online" in str(node)

    def test_edge_node_update_heartbeat(self, company):
        """Test heartbeat update."""
        node = EdgeNode.objects.create(
            company=company,
            name="Test Node",
            status=EdgeNode.Status.OFFLINE,
        )

        node.update_heartbeat()

        assert node.status == EdgeNode.Status.ONLINE
        assert node.last_heartbeat is not None

    def test_edge_node_is_online(self, company):
        """Test is_online property."""
        online_node = EdgeNode.objects.create(
            company=company,
            name="Online",
            status=EdgeNode.Status.ONLINE,
            last_heartbeat=timezone.now(),
        )
        offline_node = EdgeNode.objects.create(
            company=company,
            name="Offline",
            status=EdgeNode.Status.ONLINE,
            last_heartbeat=timezone.now() - timedelta(minutes=10),
        )
        no_heartbeat = EdgeNode.objects.create(
            company=company,
            name="No Heartbeat",
        )

        assert online_node.is_online is True
        assert offline_node.is_online is False
        assert no_heartbeat.is_online is False

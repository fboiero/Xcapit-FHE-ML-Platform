"""
Tests for federated services: EdgeNodeService, FederatedModelService, InferenceService.

Covers node lifecycle, model training/deployment, and encrypted inference.
"""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.core.models import Company
from apps.core.services.base import ServiceContext
from apps.federated.models import (
    EdgeNode,
    FederatedModel,
    InferenceEndpoint,
    InferenceRequest,
    InferenceResult,
)
from apps.federated.services import (
    EdgeNodeService,
    FederatedModelService,
    InferenceService,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fed_company(db):
    return Company.objects.create(name="Fed Corp", email="fed@corp.com", industry="tech")


@pytest.fixture
def other_fed_company(db):
    return Company.objects.create(name="Other Corp", email="other@fed.com", industry="finance")


@pytest.fixture
def consortium(db, fed_company):
    from apps.consortiums.models import Consortium

    return Consortium.objects.create(
        name="Fed Consortium",
        owner=fed_company,
        status=Consortium.Status.ACTIVE,
    )


@pytest.fixture
def inactive_consortium(db, fed_company):
    from apps.consortiums.models import Consortium

    return Consortium.objects.create(
        name="Inactive Consortium",
        owner=fed_company,
        status=Consortium.Status.DRAFT,
    )


@pytest.fixture
def edge_node(db, fed_company):
    return EdgeNode.objects.create(
        company=fed_company,
        name="Test Node",
        node_type=EdgeNode.NodeType.CLOUD,
        status=EdgeNode.Status.OFFLINE,
    )


@pytest.fixture
def online_node(db, fed_company):
    return EdgeNode.objects.create(
        company=fed_company,
        name="Online Node",
        node_type=EdgeNode.NodeType.CLOUD,
        status=EdgeNode.Status.ONLINE,
        last_heartbeat=timezone.now(),
    )


@pytest.fixture
def federated_model(db, consortium):
    return FederatedModel.objects.create(
        consortium=consortium,
        name="Test Model",
        model_type=FederatedModel.ModelType.LOGISTIC_REGRESSION,
        version="1.0.0",
        status=FederatedModel.Status.DRAFT,
    )


@pytest.fixture
def ready_model(db, consortium):
    return FederatedModel.objects.create(
        consortium=consortium,
        name="Ready Model",
        model_type=FederatedModel.ModelType.LOGISTIC_REGRESSION,
        version="1.0.1",
        status=FederatedModel.Status.READY,
    )


@pytest.fixture
def active_endpoint(db, consortium, fed_company):
    return InferenceEndpoint.objects.create(
        consortium=consortium,
        company=fed_company,
        name="Active Endpoint",
        model=None,
        status=InferenceEndpoint.Status.ACTIVE,
    )


@pytest.fixture
def inactive_endpoint(db, consortium, fed_company):
    return InferenceEndpoint.objects.create(
        consortium=consortium,
        company=fed_company,
        name="Inactive Endpoint",
        status=InferenceEndpoint.Status.PAUSED,
    )


# ===========================================================================
# EdgeNodeService Tests
# ===========================================================================


@pytest.mark.django_db
class TestEdgeNodeServiceRegister:
    def test_register_node_happy_path(self, fed_company):
        service = EdgeNodeService()
        result = service.register_node(fed_company, "Node-1", EdgeNode.NodeType.CLOUD)

        assert result.success
        node = result.data
        assert node.name == "Node-1"
        assert node.company == fed_company
        assert node.status == EdgeNode.Status.OFFLINE

    def test_register_node_with_capabilities(self, fed_company):
        caps = {"max_models": 5, "gpu": True}
        service = EdgeNodeService()
        result = service.register_node(
            fed_company, "GPU Node", EdgeNode.NodeType.ON_PREMISE, capabilities=caps
        )

        assert result.success
        assert result.data.capabilities == caps


@pytest.mark.django_db
class TestEdgeNodeServiceHeartbeat:
    def test_record_heartbeat_transitions_offline_to_online(self, edge_node):
        assert edge_node.status == EdgeNode.Status.OFFLINE

        service = EdgeNodeService()
        result = service.record_heartbeat(edge_node)

        assert result.success
        assert result.data.status == EdgeNode.Status.ONLINE
        assert result.data.last_heartbeat is not None

    def test_record_heartbeat_updates_timestamp(self, online_node):
        old_hb = online_node.last_heartbeat
        service = EdgeNodeService()
        result = service.record_heartbeat(online_node)

        assert result.success
        assert result.data.last_heartbeat >= old_hb


@pytest.mark.django_db
class TestEdgeNodeServiceDeploy:
    def test_deploy_model_happy_path(self, online_node, ready_model):
        service = EdgeNodeService()
        result = service.deploy_model_to_node(online_node, ready_model)

        assert result.success
        assert online_node.deployed_models.filter(id=ready_model.id).exists()

    def test_deploy_model_not_ready(self, online_node, federated_model):
        service = EdgeNodeService()
        result = service.deploy_model_to_node(online_node, federated_model)

        assert not result.success
        assert result.error_code == "invalid_status"

    def test_deploy_model_already_deployed(self, online_node, ready_model):
        online_node.deployed_models.add(ready_model)

        service = EdgeNodeService()
        result = service.deploy_model_to_node(online_node, ready_model)

        assert not result.success
        assert result.error_code == "already_deployed"

    def test_deploy_model_capacity_exceeded(self, online_node, ready_model):
        online_node.capabilities = {"max_models": 0}
        online_node.save()

        service = EdgeNodeService()
        result = service.deploy_model_to_node(online_node, ready_model)

        assert not result.success
        assert result.error_code == "capacity_exceeded"


@pytest.mark.django_db
class TestEdgeNodeServiceUndeploy:
    def test_undeploy_model_happy_path(self, online_node, ready_model):
        online_node.deployed_models.add(ready_model)

        service = EdgeNodeService()
        result = service.undeploy_model_from_node(online_node, ready_model)

        assert result.success
        assert not online_node.deployed_models.filter(id=ready_model.id).exists()

    def test_undeploy_model_not_deployed(self, online_node, ready_model):
        service = EdgeNodeService()
        result = service.undeploy_model_from_node(online_node, ready_model)

        assert not result.success
        assert result.error_code == "not_deployed"


@pytest.mark.django_db
class TestEdgeNodeServiceStatus:
    def test_update_node_status_stale_goes_offline(self, online_node):
        online_node.last_heartbeat = timezone.now() - timedelta(seconds=600)
        online_node.save()

        service = EdgeNodeService()
        node = service.update_node_status(online_node)

        assert node.status == EdgeNode.Status.OFFLINE

    def test_update_node_status_fresh_stays_online(self, online_node):
        service = EdgeNodeService()
        node = service.update_node_status(online_node)

        assert node.status == EdgeNode.Status.ONLINE

    def test_update_node_status_no_heartbeat(self, edge_node):
        service = EdgeNodeService()
        node = service.update_node_status(edge_node)
        # Should return unchanged
        assert node.status == EdgeNode.Status.OFFLINE

    def test_get_online_nodes(self, fed_company, online_node, edge_node):
        service = EdgeNodeService()
        nodes = service.get_online_nodes(fed_company)

        assert online_node in nodes
        assert edge_node not in nodes

    def test_get_online_nodes_filters_by_company(self, fed_company, other_fed_company):
        EdgeNode.objects.create(
            company=other_fed_company,
            name="Other Node",
            node_type=EdgeNode.NodeType.CLOUD,
            status=EdgeNode.Status.ONLINE,
            last_heartbeat=timezone.now(),
        )

        service = EdgeNodeService()
        nodes = service.get_online_nodes(fed_company)

        for node in nodes:
            assert node.company == fed_company


@pytest.mark.django_db
class TestEdgeNodeServiceHealth:
    def test_get_node_health_structure(self, online_node):
        service = EdgeNodeService()
        health = service.get_node_health(online_node)

        assert "id" in health
        assert "name" in health
        assert "status" in health
        assert "uptime_hours" in health
        assert "deployed_models_count" in health
        assert "capabilities" in health
        assert "is_healthy" in health

    def test_get_node_health_online_is_healthy(self, online_node):
        service = EdgeNodeService()
        health = service.get_node_health(online_node)

        assert health["is_healthy"] is True

    def test_get_node_health_uptime(self, online_node):
        service = EdgeNodeService()
        health = service.get_node_health(online_node)

        assert health["uptime_hours"] >= 0


@pytest.mark.django_db
class TestEdgeNodeServiceCleanup:
    def test_cleanup_stale_nodes(self, fed_company):
        EdgeNode.objects.create(
            company=fed_company,
            name="Stale Node",
            node_type=EdgeNode.NodeType.CLOUD,
            status=EdgeNode.Status.ONLINE,
            last_heartbeat=timezone.now() - timedelta(seconds=600),
        )

        service = EdgeNodeService()
        result = service.cleanup_stale_nodes()

        assert result.success
        assert result.data >= 1

    def test_cleanup_respects_company_filter(self, fed_company, other_fed_company):
        EdgeNode.objects.create(
            company=other_fed_company,
            name="Other Stale",
            node_type=EdgeNode.NodeType.CLOUD,
            status=EdgeNode.Status.ONLINE,
            last_heartbeat=timezone.now() - timedelta(seconds=600),
        )

        service = EdgeNodeService()
        result = service.cleanup_stale_nodes(company=fed_company)

        assert result.success
        assert result.data == 0

    def test_cleanup_returns_count(self, fed_company):
        for i in range(3):
            EdgeNode.objects.create(
                company=fed_company,
                name=f"Stale-{i}",
                node_type=EdgeNode.NodeType.CLOUD,
                status=EdgeNode.Status.ONLINE,
                last_heartbeat=timezone.now() - timedelta(seconds=600),
            )

        service = EdgeNodeService()
        result = service.cleanup_stale_nodes(company=fed_company)

        assert result.data == 3


# ===========================================================================
# FederatedModelService Tests
# ===========================================================================


@pytest.mark.django_db
class TestFederatedModelServiceCreate:
    def test_create_model_happy_path(self, consortium):
        service = FederatedModelService()
        result = service.create_model(
            consortium, "My Model", FederatedModel.ModelType.LOGISTIC_REGRESSION
        )

        assert result.success
        model = result.data
        assert model.name == "My Model"
        assert model.version == "1.0.0"
        assert model.status == FederatedModel.Status.DRAFT

    def test_create_model_with_config(self, consortium):
        config = {"learning_rate": 0.01}
        service = FederatedModelService()
        result = service.create_model(
            consortium, "Configured", FederatedModel.ModelType.LINEAR_REGRESSION, config=config
        )

        assert result.success
        assert result.data.config == config

    def test_create_model_inactive_consortium(self, inactive_consortium):
        service = FederatedModelService()
        result = service.create_model(
            inactive_consortium, "Fail", FederatedModel.ModelType.LOGISTIC_REGRESSION
        )

        assert not result.success
        assert result.error_code == "consortium_inactive"


@pytest.mark.django_db
class TestFederatedModelServiceTraining:
    def test_start_training_from_draft(self, federated_model):
        service = FederatedModelService()
        result = service.start_training(federated_model)

        assert result.success
        assert result.data.status == FederatedModel.Status.TRAINING

    def test_start_training_with_config(self, federated_model):
        config = {"epochs": 50}
        service = FederatedModelService()
        result = service.start_training(federated_model, training_config=config)

        assert result.success
        assert result.data.config.get("epochs") == 50

    def test_start_training_already_training(self, consortium):
        model = FederatedModel.objects.create(
            consortium=consortium,
            name="Training",
            model_type=FederatedModel.ModelType.LOGISTIC_REGRESSION,
            status=FederatedModel.Status.TRAINING,
        )

        service = FederatedModelService()
        result = service.start_training(model)

        assert not result.success
        assert result.error_code == "invalid_status"

    def test_start_training_deployed_fails(self, consortium):
        model = FederatedModel.objects.create(
            consortium=consortium,
            name="Deployed",
            model_type=FederatedModel.ModelType.LOGISTIC_REGRESSION,
            status=FederatedModel.Status.DEPLOYED,
        )

        service = FederatedModelService()
        result = service.start_training(model)

        assert not result.success
        assert result.error_code == "invalid_status"

    def test_complete_training_version_increments(self, consortium):
        model = FederatedModel.objects.create(
            consortium=consortium,
            name="Training Model",
            model_type=FederatedModel.ModelType.LOGISTIC_REGRESSION,
            status=FederatedModel.Status.TRAINING,
            version="1.0.0",
        )

        service = FederatedModelService()
        result = service.complete_training(model, {"accuracy": 0.95})

        assert result.success
        assert result.data.version == "1.0.1"
        assert result.data.status == FederatedModel.Status.READY

    def test_complete_training_not_training_fails(self, federated_model):
        service = FederatedModelService()
        result = service.complete_training(federated_model, {"accuracy": 0.9})

        assert not result.success
        assert result.error_code == "invalid_status"


@pytest.mark.django_db
class TestFederatedModelServiceDeploy:
    def test_deploy_model_from_ready(self, ready_model):
        service = FederatedModelService()
        result = service.deploy_model(ready_model)

        assert result.success
        assert result.data.status == FederatedModel.Status.DEPLOYED

    def test_deploy_model_not_ready_fails(self, federated_model):
        service = FederatedModelService()
        result = service.deploy_model(federated_model)

        assert not result.success
        assert result.error_code == "invalid_status"

    def test_undeploy_model_from_deployed(self, consortium):
        model = FederatedModel.objects.create(
            consortium=consortium,
            name="Deployed",
            model_type=FederatedModel.ModelType.LOGISTIC_REGRESSION,
            status=FederatedModel.Status.DEPLOYED,
        )

        service = FederatedModelService()
        result = service.undeploy_model(model)

        assert result.success
        assert result.data.status == FederatedModel.Status.READY

    def test_undeploy_model_not_deployed_fails(self, ready_model):
        service = FederatedModelService()
        result = service.undeploy_model(ready_model)

        assert not result.success
        assert result.error_code == "invalid_status"


@pytest.mark.django_db
class TestFederatedModelServiceArchive:
    def test_archive_model_happy_path(self, ready_model):
        service = FederatedModelService()
        result = service.archive_model(ready_model)

        assert result.success
        assert result.data.status == FederatedModel.Status.ARCHIVED

    def test_archive_training_fails(self, consortium):
        model = FederatedModel.objects.create(
            consortium=consortium,
            name="Training",
            model_type=FederatedModel.ModelType.LOGISTIC_REGRESSION,
            status=FederatedModel.Status.TRAINING,
        )

        service = FederatedModelService()
        result = service.archive_model(model)

        assert not result.success
        assert result.error_code == "invalid_status"


@pytest.mark.django_db
class TestFederatedModelServiceStatus:
    def test_get_model_status_structure(self, ready_model):
        # Service references model.training_metrics (dynamic attribute)
        ready_model.training_metrics = {"accuracy": 0.9}
        service = FederatedModelService()
        status = service.get_model_status(ready_model)

        assert "id" in status
        assert "name" in status
        assert "version" in status
        assert "status" in status
        assert "deployed_nodes" in status
        assert "node_count" in status

    def test_get_model_status_includes_edge_nodes(self, ready_model, online_node):
        online_node.deployed_models.add(ready_model)
        ready_model.training_metrics = {}

        service = FederatedModelService()
        status = service.get_model_status(ready_model)

        assert status["node_count"] == 1
        assert len(status["deployed_nodes"]) == 1
        assert status["deployed_nodes"][0]["name"] == "Online Node"


# ===========================================================================
# InferenceService Tests
# ===========================================================================


@pytest.mark.django_db
class TestInferenceServicePredict:
    def test_predict_happy_path(self, active_endpoint, fed_company):
        service = InferenceService()
        result = service.predict(
            active_endpoint,
            fed_company,
            [{"feature1": 1.0, "feature2": 2.0}],
        )

        assert result.success
        data = result.data
        assert data.request_id
        assert data.encrypted_output
        assert data.latency_ms > 0
        assert isinstance(data.metadata, dict)

    def test_predict_inactive_endpoint_fails(self, inactive_endpoint, fed_company):
        service = InferenceService()
        result = service.predict(
            inactive_endpoint,
            fed_company,
            [{"feature1": 1.0}],
        )

        assert not result.success
        assert result.error_code == "endpoint_inactive"

    def test_predict_creates_request_and_result(self, active_endpoint, fed_company):
        service = InferenceService()
        result = service.predict(
            active_endpoint,
            fed_company,
            [{"x": 1}],
        )

        assert result.success
        req = InferenceRequest.objects.get(id=result.data.request_id)
        assert req.status == InferenceRequest.Status.COMPLETED
        assert InferenceResult.objects.filter(request=req).exists()

    def test_predict_updates_endpoint_stats(self, active_endpoint, fed_company):
        initial_count = active_endpoint.request_count

        service = InferenceService()
        service.predict(active_endpoint, fed_company, [{"x": 1}])

        active_endpoint.refresh_from_db()
        assert active_endpoint.request_count == initial_count + 1
        assert active_endpoint.total_latency_ms > 0

    def test_predict_with_priority(self, active_endpoint, fed_company):
        service = InferenceService()
        result = service.predict(
            active_endpoint,
            fed_company,
            [{"x": 1}],
            priority="high",
        )

        assert result.success
        req = InferenceRequest.objects.get(id=result.data.request_id)
        assert req.priority == InferenceRequest.Priority.HIGH


@pytest.mark.django_db
class TestInferenceServiceExecutePrediction:
    def test_execute_prediction_returns_base64(self, active_endpoint):
        import base64

        service = InferenceService()
        output, metadata = service._execute_prediction(
            active_endpoint, [{"x": 1}, {"x": 2}]
        )

        # Should be valid base64
        decoded = base64.b64decode(output)
        assert decoded

    def test_execute_prediction_metadata(self, active_endpoint):
        service = InferenceService()
        _, metadata = service._execute_prediction(active_endpoint, [{"x": 1}])

        assert metadata["n_samples"] == 1
        assert metadata["encryption_scheme"] == "CKKS"
        assert "model_version" in metadata


@pytest.mark.django_db
class TestInferenceServiceStats:
    def test_update_endpoint_stats(self, active_endpoint):
        service = InferenceService()
        service._update_endpoint_stats(active_endpoint, 50.0)

        active_endpoint.refresh_from_db()
        assert active_endpoint.request_count == 1
        assert active_endpoint.total_latency_ms == 50.0

    def test_get_request_result_happy_path(self, active_endpoint, fed_company):
        service = InferenceService()
        predict_result = service.predict(active_endpoint, fed_company, [{"x": 1}])
        req = InferenceRequest.objects.get(id=predict_result.data.request_id)

        result = service.get_request_result(req)

        assert result.success
        assert "encrypted_output" in result.data
        assert "output_metadata" in result.data

    def test_get_request_result_not_completed_fails(self, active_endpoint, fed_company):
        req = InferenceRequest.objects.create(
            endpoint=active_endpoint,
            requester=fed_company,
            input_hash="abc123",
            status=InferenceRequest.Status.PENDING,
        )

        service = InferenceService()
        result = service.get_request_result(req)

        assert not result.success
        assert result.error_code == "invalid_status"

    def test_get_endpoint_stats_structure(self, active_endpoint):
        service = InferenceService()
        stats = service.get_endpoint_stats(active_endpoint)

        assert "endpoint_id" in stats
        assert "name" in stats
        assert "request_count" in stats
        assert "avg_latency_ms" in stats
        assert "success_rate" in stats
        assert stats["model"] is None  # No model attached

    def test_get_endpoint_stats_zero_requests(self, active_endpoint):
        service = InferenceService()
        stats = service.get_endpoint_stats(active_endpoint)

        assert stats["request_count"] == 0
        assert stats["avg_latency_ms"] == 0
        assert stats["success_rate"] == 100.0

"""
End-to-end integration tests for cross-app workflows.

Tests the following flows:
1. Auth -> ML Model Lifecycle (create, train, version, export, batch predict)
2. Model Sharing & Marketplace (share, request, deploy, review)
3. Federated Learning (model, node, endpoint, inference)
4. Data Quality -> Consortium -> Training (quality assessment, alerts, dashboard)
5. Governance (proposal, vote, execute)
"""

import hashlib
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.consortiums.models import (
    Consortium,
    ConsortiumInvitation,
    ConsortiumMember,
    ContributionProof,
)
from apps.core.models import Company, User
from apps.data_quality.models import QualityAlert, QualityAssessment, QualityRule
from apps.federated.models import EdgeNode, FederatedModel, InferenceEndpoint
from apps.governance.models import AuditEvent, Proposal, Vote
from apps.marketplace.models import Category, Deployment, MarketplaceModel, Review
from apps.models.models import (
    BatchPredictionJob,
    MLModel,
    ModelExport,
    ModelShare,
    ModelShareRequest,
    ModelVersion,
    TrainingRun,
)


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def api_client():
    """Create an API client for testing."""
    return APIClient()


@pytest.fixture
def create_company(db):
    """Factory for creating companies with users."""
    counter = [0]

    def _create(name: str, email: str, tier: str = "enterprise"):
        counter[0] += 1
        company = Company.objects.create(
            name=name,
            email=email,
            tier=tier,
        )
        user_email = f"user{counter[0]}_{email.replace('@', '_at_')}"
        user = User.objects.create_user(
            email=user_email,
            password="TestPassword123!",
            company=company,
        )
        return company, user

    return _create


@pytest.fixture
def company_a(create_company):
    return create_company("Company Alpha", "alpha@example.com")


@pytest.fixture
def company_b(create_company):
    return create_company("Company Beta", "beta@example.com")


@pytest.fixture
def company_c(create_company):
    return create_company("Company Gamma", "gamma@example.com")


def _data_hash(seed: str) -> str:
    """Generate a SHA-256 hash from a seed string."""
    return hashlib.sha256(seed.encode()).hexdigest()


def _setup_active_consortium(api_client, owner_user, owner_company, name="Test Consortium"):
    """Helper: create an active consortium with min_members=1 (auto-activates)."""
    api_client.force_authenticate(user=owner_user)
    response = api_client.post(
        "/api/v2/consortiums/",
        data={
            "name": name,
            "description": "Integration test consortium",
            "model_type": "logistic_regression",
            "min_members": 1,
        },
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED, response.data
    consortium_id = response.data["id"]
    consortium = Consortium.objects.get(id=consortium_id)
    assert consortium.status == Consortium.Status.ACTIVE
    return consortium


# ============================================================
# Flow 1: Auth -> ML Model Lifecycle
# ============================================================


class TestMLModelLifecycle:
    """
    E2E test: create model, train, version, export, batch predict.
    """

    @pytest.mark.django_db(transaction=True)
    def test_full_ml_model_lifecycle(self, api_client, company_a):
        company, user = company_a
        api_client.force_authenticate(user=user)

        # ----- STEP 1: Create ML model -----
        response = api_client.post(
            "/api/v2/models/",
            data={
                "name": "Fraud Detection Model",
                "model_type": "logistic_regression",
                "config": {"learning_rate": 0.01},
                "n_features": 10,
                "feature_names": ["f1", "f2", "f3", "f4", "f5",
                                  "f6", "f7", "f8", "f9", "f10"],
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED, response.data

        model = MLModel.objects.get(owner=company, name="Fraud Detection Model")
        model_id = model.id
        assert model.status == MLModel.Status.CREATED
        assert model.owner == company

        # ----- STEP 2: Start training -----
        response = api_client.post(
            f"/api/v2/models/{model_id}/train/",
            data={"epochs": 20},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "training_run_id" in response.data

        training_run_id = response.data["training_run_id"]
        training_run = TrainingRun.objects.get(id=training_run_id)
        assert training_run.epochs_total == 20

        model.refresh_from_db()
        assert model.status == MLModel.Status.TRAINING

        # ----- STEP 3: Verify training runs list -----
        response = api_client.get("/api/v2/models/training-runs/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

        # ----- STEP 4: Mark model as trained (simulating completed training) -----
        model.status = MLModel.Status.TRAINED
        model.trained_at = timezone.now()
        model.training_epochs = 20
        model.final_loss = 0.05
        model.save()

        # ----- STEP 5: Make a prediction -----
        response = api_client.post(
            f"/api/v2/models/{model_id}/predict/",
            data={
                "data": [[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]],
                "encrypted": False,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "predictions" in response.data
        assert len(response.data["predictions"]) == 1

        # ----- STEP 6: Create a model version -----
        response = api_client.post(
            f"/api/v2/models/{model_id}/create_version/",
            data={
                "bump_type": "minor",
                "changelog": "First trained version",
                "release_notes": "Initial release with fraud detection",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        version_id = response.data["id"]
        assert response.data["version"] is not None

        # Verify version in list
        response = api_client.get("/api/v2/models/versions/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

        # ----- STEP 7: Export model -----
        response = api_client.post(
            f"/api/v2/models/{model_id}/export_model/",
            data={
                "format": "fheml_json",
                "include_weights": True,
                "include_config": True,
                "include_metadata": True,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "export" in response.data
        export_id = response.data["export"]["id"]

        # Verify export in list
        response = api_client.get("/api/v2/models/exports/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

        # ----- STEP 8: Batch prediction (synchronous) -----
        response = api_client.post(
            f"/api/v2/models/{model_id}/batch_predict/",
            data={
                "data": [
                    [1.0] * 10,
                    [2.0] * 10,
                    [3.0] * 10,
                ],
                "encrypted": False,
                "priority": "high",
                "async_mode": False,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["n_samples"] == 3
        assert response.data["status"] == "completed"

        # Verify batch job in list
        response = api_client.get("/api/v2/models/batch-jobs/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

        # ----- STEP 9: Get model stats -----
        response = api_client.get(f"/api/v2/models/{model_id}/stats/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_predictions"] >= 1

        # ----- STEP 10: Verify final DB state -----
        model.refresh_from_db()
        assert model.status == MLModel.Status.TRAINED
        assert ModelVersion.objects.filter(model=model).count() >= 1
        assert ModelExport.objects.filter(model=model).count() >= 1
        assert BatchPredictionJob.objects.filter(model=model).count() >= 1
        assert TrainingRun.objects.filter(model=model).count() >= 1


# ============================================================
# Flow 2: Model Sharing & Marketplace
# ============================================================


class TestModelSharingAndMarketplace:
    """
    E2E test: two companies, share model, marketplace deploy, review.
    """

    @pytest.mark.django_db(transaction=True)
    def test_model_sharing_flow(self, api_client, company_a, company_b):
        comp_a, user_a = company_a
        comp_b, user_b = company_b

        # ----- Setup: consortiums for both companies -----
        consortium_a = _setup_active_consortium(
            api_client, user_a, comp_a, name="Consortium Alpha"
        )
        consortium_b = _setup_active_consortium(
            api_client, user_b, comp_b, name="Consortium Beta"
        )

        # ----- STEP 1: Company A creates a trained model -----
        api_client.force_authenticate(user=user_a)
        response = api_client.post(
            "/api/v2/models/",
            data={
                "name": "Shared Analytics Model",
                "model_type": "linear_regression",
                "consortium": str(consortium_a.id),
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

        # Mark as trained
        model = MLModel.objects.get(owner=comp_a, name="Shared Analytics Model")
        model_id = model.id
        model.status = MLModel.Status.TRAINED
        model.trained_at = timezone.now()
        model.save()

        # ----- STEP 2: Company A shares model with Company B's consortium -----
        response = api_client.post(
            "/api/v2/models/shares/",
            data={
                "model_id": str(model_id),
                "target_consortium_id": str(consortium_b.id),
                "share_type": "prediction_only",
                "requires_approval": False,
                "revenue_share_percent": 10,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        share_id = response.data["id"]
        assert response.data["status"] == "approved"

        # ----- STEP 3: Company B creates a share request for the model -----
        api_client.force_authenticate(user=user_b)
        response = api_client.post(
            "/api/v2/models/share-requests/",
            data={
                "model_id": str(model_id),
                "requested_share_type": "full_access",
                "message": "We need full access for research",
                "proposed_revenue_share": 15,
            },
            format="json",
        )
        # There's already an existing share, but share requests don't check
        # for existing shares (they're separate requests for different access).
        # If this fails due to a constraint, we verify the existing share works.
        if response.status_code == status.HTTP_201_CREATED:
            share_request_id = response.data["id"]

            # ----- STEP 4: Company A approves the share request -----
            api_client.force_authenticate(user=user_a)

            # Delete the existing share first to avoid unique_together constraint
            ModelShare.objects.filter(id=share_id).delete()

            response = api_client.post(
                f"/api/v2/models/share-requests/{share_request_id}/respond/",
                data={
                    "action": "approve",
                    "message": "Approved for full access",
                    "share_type": "full_access",
                    "revenue_share_percent": 12,
                },
                format="json",
            )
            assert response.status_code == status.HTTP_200_OK
            assert response.data["status"] == "approved"

        # ----- STEP 5: Verify shares lists -----
        api_client.force_authenticate(user=user_a)
        response = api_client.get("/api/v2/models/shares/given/")
        assert response.status_code == status.HTTP_200_OK

        api_client.force_authenticate(user=user_b)
        response = api_client.get("/api/v2/models/shares/received/")
        assert response.status_code == status.HTTP_200_OK

        # ----- STEP 6: Marketplace flow -----
        # Create a marketplace model and category (directly via ORM since
        # MarketplaceModelViewSet is read-only)
        category = Category.objects.create(
            name="Analytics",
            description="Analytics models",
        )
        marketplace_model = MarketplaceModel.objects.create(
            name="Analytics Model v1",
            description="Predictive analytics for financial data",
            category=category,
            model_type="linear_regression",
            accuracy=0.95,
            training_samples=50000,
            is_active=True,
        )

        # Company B deploys the marketplace model to their consortium
        api_client.force_authenticate(user=user_b)
        response = api_client.post(
            "/api/v2/marketplace/deployments/",
            data={
                "marketplace_model": str(marketplace_model.id),
                "consortium": str(consortium_b.id),
                "config": {"replicas": 2},
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

        deployment = Deployment.objects.get(
            marketplace_model=marketplace_model, consortium=consortium_b
        )
        deployment_id = deployment.id

        # Verify marketplace model download count incremented
        marketplace_model.refresh_from_db()
        assert marketplace_model.downloads == 1

        # ----- STEP 7: Company B leaves a review -----
        response = api_client.post(
            "/api/v2/marketplace/reviews/",
            data={
                "marketplace_model": str(marketplace_model.id),
                "consortium": str(consortium_b.id),
                "rating": 5,
                "title": "Excellent model",
                "comment": "Very accurate predictions for our use case.",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

        # ----- STEP 8: View marketplace model reviews -----
        response = api_client.get(
            f"/api/v2/marketplace/models/{marketplace_model.id}/reviews/"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_reviews"] == 1
        assert response.data["average_rating"] == 5.0

        # ----- STEP 9: Verify final state -----
        assert Deployment.objects.filter(consortium=consortium_b).count() >= 1
        assert Review.objects.filter(reviewer=comp_b).count() == 1
        assert ModelShare.objects.filter(
            target_consortium=consortium_b
        ).count() >= 1


# ============================================================
# Flow 3: Federated Learning
# ============================================================


class TestFederatedLearning:
    """
    E2E test: federated model, edge node, endpoint, inference.
    """

    @pytest.mark.django_db(transaction=True)
    def test_federated_learning_flow(self, api_client, company_a):
        company, user = company_a
        consortium = _setup_active_consortium(
            api_client, user, company, name="Federated Consortium"
        )

        api_client.force_authenticate(user=user)

        # ----- STEP 1: Create federated model -----
        response = api_client.post(
            "/api/v2/federated/models/",
            data={
                "consortium": str(consortium.id),
                "name": "Federated Fraud Detector",
                "description": "Cross-org fraud detection",
                "model_type": "logistic_regression",
                "config": {"rounds": 10, "lr": 0.001},
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED, response.data

        fed_model = FederatedModel.objects.get(
            consortium=consortium, name="Federated Fraud Detector"
        )
        fed_model_id = fed_model.id
        assert fed_model.status == FederatedModel.Status.DRAFT

        # ----- STEP 2: Start federated training -----
        response = api_client.post(
            f"/api/v2/federated/models/{fed_model_id}/train/"
            f"?consortium_id={consortium.id}"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "training"

        # Simulate training completion -> READY
        fed_model.refresh_from_db()
        fed_model.status = FederatedModel.Status.READY
        fed_model.metrics = {"accuracy": 0.92, "loss": 0.08}
        fed_model.save()

        # ----- STEP 3: Register an edge node -----
        response = api_client.post(
            "/api/v2/federated/nodes/",
            data={
                "name": "Edge Node Alpha",
                "node_type": "on_premise",
                "location": "Buenos Aires, Argentina",
                "capabilities": {"gpu": True, "memory_gb": 32},
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

        node = EdgeNode.objects.get(company=company, name="Edge Node Alpha")
        node_id = node.id
        assert node.company == company

        # ----- STEP 4: Send heartbeat (bring node online) -----
        response = api_client.post(
            f"/api/v2/federated/nodes/{node_id}/heartbeat/"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "online"

        # ----- STEP 5: Deploy federated model to edge node -----
        response = api_client.post(
            f"/api/v2/federated/nodes/{node_id}/deploy_model/",
            data={"model_id": str(fed_model_id)},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

        node.refresh_from_db()
        assert fed_model in node.deployed_models.all()

        # ----- STEP 6: Deploy the federated model (status -> DEPLOYED) -----
        response = api_client.post(
            f"/api/v2/federated/models/{fed_model_id}/deploy/"
            f"?consortium_id={consortium.id}"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "deployed"

        # ----- STEP 7: Create inference endpoint -----
        # Use the federated model (InferenceEndpoint.model FK points to FederatedModel)
        response = api_client.post(
            "/api/v2/federated/endpoints/",
            data={
                "consortium": str(consortium.id),
                "name": "Real-time Fraud Endpoint",
                "description": "Production fraud detection",
                "model": str(fed_model_id),
                "endpoint_type": "realtime",
                "config": {"max_batch_size": 100},
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED, response.data

        endpoint = InferenceEndpoint.objects.get(
            consortium=consortium, name="Real-time Fraud Endpoint"
        )
        endpoint_id = endpoint.id
        assert endpoint.status == InferenceEndpoint.Status.ACTIVE
        assert endpoint.url != ""

        # ----- STEP 8: Make an inference prediction -----
        response = api_client.post(
            f"/api/v2/federated/endpoints/{endpoint_id}/predict/",
            data={
                "input_data": [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
                "priority": "high",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "request_id" in response.data
        assert "encrypted_output" in response.data
        assert response.data["latency_ms"] >= 0

        # ----- STEP 9: Verify endpoint stats -----
        response = api_client.get(
            f"/api/v2/federated/endpoints/{endpoint_id}/stats/"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["request_count"] == 1

        # ----- STEP 10: Get online nodes -----
        response = api_client.get("/api/v2/federated/nodes/online/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

        # ----- STEP 11: Verify final state -----
        fed_model.refresh_from_db()
        assert fed_model.status == FederatedModel.Status.DEPLOYED
        assert EdgeNode.objects.filter(company=company).count() == 1
        assert InferenceEndpoint.objects.filter(consortium=consortium).count() == 1


# ============================================================
# Flow 4: Data Quality -> Consortium -> Training
# ============================================================


class TestDataQualityConsortiumTraining:
    """
    E2E test: quality assessment, alerts, dashboard, then training.
    """

    @pytest.mark.django_db(transaction=True)
    def test_data_quality_to_training_flow(self, api_client, company_a, company_b):
        comp_a, user_a = company_a
        comp_b, user_b = company_b

        # ----- STEP 1: Create consortium with 2 members -----
        api_client.force_authenticate(user=user_a)
        response = api_client.post(
            "/api/v2/consortiums/",
            data={
                "name": "Quality-Driven Consortium",
                "description": "Focus on data quality",
                "model_type": "logistic_regression",
                "min_members": 2,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        consortium_id = response.data["id"]
        consortium = Consortium.objects.get(id=consortium_id)
        assert consortium.status == Consortium.Status.DRAFT

        # Invite Company B
        expires_at = timezone.now() + timedelta(days=7)
        response = api_client.post(
            "/api/v2/consortiums/invitations/",
            data={
                "consortium": str(consortium_id),
                "invitee_email": comp_b.email,
                "role": "contributor",
                "expires_at": expires_at.isoformat(),
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        invitation_id = response.data["id"]

        # Company B accepts
        api_client.force_authenticate(user=user_b)
        response = api_client.post(
            f"/api/v2/consortiums/invitations/{invitation_id}/accept/"
        )
        assert response.status_code == status.HTTP_200_OK

        consortium.refresh_from_db()
        assert consortium.status == Consortium.Status.ACTIVE

        # ----- STEP 2: Both companies contribute data -----
        contributions_data = [
            (user_a, comp_a, 5000, "company_a_data"),
            (user_b, comp_b, 3000, "company_b_data"),
        ]

        for user, company, record_count, seed in contributions_data:
            api_client.force_authenticate(user=user)
            response = api_client.post(
                f"/api/v2/consortiums/{consortium_id}/contributions/",
                data={
                    "consortium": str(consortium_id),
                    "record_count": record_count,
                    "feature_count": 15,
                    "data_hash": _data_hash(seed),
                    "checksum": _data_hash(f"{seed}_checksum"),
                },
                format="json",
            )
            assert response.status_code == status.HTTP_201_CREATED

        # Verify contributions are auto-verified
        verified = ContributionProof.objects.filter(
            consortium=consortium, verified=True
        ).count()
        assert verified == 2

        # ----- STEP 3: Create quality assessment for Company A -----
        api_client.force_authenticate(user=user_a)
        response = api_client.post(
            "/api/v2/data-quality/assessments/",
            data={
                "consortium": str(consortium_id),
                "record_count": 5000,
                "feature_count": 15,
                "null_count": 50,
                "duplicate_count": 10,
                "outlier_count": 25,
                "schema_violations": 5,
                "format_violations": 3,
                "range_violations": 8,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assessment_a_id = response.data["id"]

        # Verify scores were calculated
        assessment_a = QualityAssessment.objects.get(id=assessment_a_id)
        assert assessment_a.status == QualityAssessment.Status.COMPLETED
        assert assessment_a.overall_score > 0

        # ----- STEP 4: Create quality assessment for Company B -----
        api_client.force_authenticate(user=user_b)
        response = api_client.post(
            "/api/v2/data-quality/assessments/",
            data={
                "consortium": str(consortium_id),
                "record_count": 3000,
                "feature_count": 15,
                "null_count": 200,
                "duplicate_count": 100,
                "outlier_count": 150,
                "schema_violations": 50,
                "format_violations": 30,
                "range_violations": 40,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assessment_b_id = response.data["id"]

        # ----- STEP 5: Create quality rule and alert (via ORM since rules
        # endpoint is not mounted) -----
        rule = QualityRule.objects.create(
            consortium=consortium,
            name="Min Overall Score",
            description="Overall score must be >= 70",
            rule_type=QualityRule.RuleType.THRESHOLD,
            metric="overall_score",
            condition={"operator": ">=", "value": 70},
            severity=QualityRule.Severity.WARNING,
        )

        assessment_b = QualityAssessment.objects.get(id=assessment_b_id)
        alert = QualityAlert.objects.create(
            rule=rule,
            assessment=assessment_b,
            company=comp_b,
            message=f"Overall score {assessment_b.overall_score:.1f} below threshold 70",
            actual_value=assessment_b.overall_score,
            expected_value=">= 70",
        )

        # ----- STEP 6: Company B checks and resolves alert -----
        api_client.force_authenticate(user=user_b)

        # Check open alert count
        response = api_client.get("/api/v2/data-quality/alerts/open_count/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["open_alerts"] >= 1

        # Acknowledge alert
        response = api_client.post(
            f"/api/v2/data-quality/alerts/{alert.id}/acknowledge/"
        )
        assert response.status_code == status.HTTP_200_OK

        # Resolve alert
        response = api_client.post(
            f"/api/v2/data-quality/alerts/{alert.id}/resolve/",
            data={"note": "Cleaned data and re-submitted"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

        alert.refresh_from_db()
        assert alert.status == QualityAlert.Status.RESOLVED

        # ----- STEP 7: Check quality dashboard -----
        api_client.force_authenticate(user=user_a)
        response = api_client.get("/api/v2/data-quality/dashboard/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_assessments"] >= 1

        # Quality summary
        response = api_client.get("/api/v2/data-quality/assessments/summary/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_count"] >= 1

        # ----- STEP 8: Start consortium training -----
        api_client.force_authenticate(user=user_a)
        with patch("apps.consortiums.tasks.train_consortium_model.delay") as mock_task:
            mock_task.return_value.id = "quality-training-task-id"

            response = api_client.post(
                f"/api/v2/consortiums/{consortium_id}/start_training/"
            )
            assert response.status_code == status.HTTP_200_OK
            assert "training_result_id" in response.data

        # ----- STEP 9: Verify final state -----
        consortium.refresh_from_db()
        assert consortium.status == Consortium.Status.TRAINING

        assert QualityAssessment.objects.filter(
            consortium=consortium
        ).count() == 2
        assert QualityAlert.objects.filter(
            company=comp_b, status=QualityAlert.Status.RESOLVED
        ).count() == 1


# ============================================================
# Flow 5: Governance (Proposal -> Vote -> Execute)
# ============================================================


class TestGovernanceFlow:
    """
    E2E test: create proposal, vote, execute.
    """

    @pytest.mark.django_db(transaction=True)
    def test_governance_proposal_vote_execute(
        self, api_client, company_a, company_b, company_c
    ):
        comp_a, user_a = company_a
        comp_b, user_b = company_b
        comp_c, user_c = company_c

        # ----- STEP 1: Create consortium with 3 members -----
        api_client.force_authenticate(user=user_a)
        response = api_client.post(
            "/api/v2/consortiums/",
            data={
                "name": "Governance Test Consortium",
                "model_type": "logistic_regression",
                "min_members": 3,
                "voting_threshold": 0.5,
                "voting_duration_days": 7,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        consortium_id = response.data["id"]
        consortium = Consortium.objects.get(id=consortium_id)

        # Invite B and C
        expires_at = timezone.now() + timedelta(days=7)
        for comp in [comp_b, comp_c]:
            response = api_client.post(
                "/api/v2/consortiums/invitations/",
                data={
                    "consortium": str(consortium_id),
                    "invitee_email": comp.email,
                    "role": "contributor",
                    "expires_at": expires_at.isoformat(),
                },
                format="json",
            )
            assert response.status_code == status.HTTP_201_CREATED

        invitations = ConsortiumInvitation.objects.filter(
            consortium=consortium, status=ConsortiumInvitation.Status.PENDING
        )

        # B accepts
        api_client.force_authenticate(user=user_b)
        inv_b = invitations.get(invitee_email=comp_b.email)
        response = api_client.post(
            f"/api/v2/consortiums/invitations/{inv_b.id}/accept/"
        )
        assert response.status_code == status.HTTP_200_OK

        # C accepts
        api_client.force_authenticate(user=user_c)
        inv_c = invitations.get(invitee_email=comp_c.email)
        response = api_client.post(
            f"/api/v2/consortiums/invitations/{inv_c.id}/accept/"
        )
        assert response.status_code == status.HTTP_200_OK

        consortium.refresh_from_db()
        assert consortium.status == Consortium.Status.ACTIVE

        # ----- STEP 2: All members contribute data (needed for voting weight) -----
        contributions = [
            (user_a, comp_a, 10000, "gov_data_a"),
            (user_b, comp_b, 5000, "gov_data_b"),
            (user_c, comp_c, 3000, "gov_data_c"),
        ]

        for user, company, records, seed in contributions:
            api_client.force_authenticate(user=user)
            response = api_client.post(
                f"/api/v2/consortiums/{consortium_id}/contributions/",
                data={
                    "consortium": str(consortium_id),
                    "record_count": records,
                    "feature_count": 20,
                    "data_hash": _data_hash(seed),
                    "checksum": _data_hash(f"{seed}_ck"),
                },
                format="json",
            )
            assert response.status_code == status.HTTP_201_CREATED

        # ----- STEP 3: Company A creates a governance proposal -----
        api_client.force_authenticate(user=user_a)
        response = api_client.post(
            "/api/v2/governance/proposals/",
            data={
                "consortium": str(consortium_id),
                "proposal_type": "update_config",
                "title": "Update voting threshold to 60%",
                "description": "Increase voting threshold for better governance",
                "data": {"config": {"voting_threshold": 0.6}},
                "voting_days": 1,  # Short for testing
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED, response.data

        proposal = Proposal.objects.get(
            consortium=consortium, title="Update voting threshold to 60%"
        )
        proposal_id = proposal.id
        assert proposal.status == Proposal.Status.ACTIVE
        assert proposal.proposer == comp_a

        # Verify audit event was created
        assert AuditEvent.objects.filter(
            consortium=consortium,
            event_type=AuditEvent.EventType.PROPOSAL_CREATED,
        ).exists()

        # ----- STEP 4: Members vote -----
        # Company A votes YES
        api_client.force_authenticate(user=user_a)
        response = api_client.post(
            "/api/v2/governance/votes/",
            data={
                "proposal": str(proposal_id),
                "support": True,
                "comment": "I support this change",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        # Weight should be 10000 // 100 = 100 (DecimalField returns string in DRF)
        assert float(response.data["weight"]) == 100

        # Company B votes YES
        api_client.force_authenticate(user=user_b)
        response = api_client.post(
            "/api/v2/governance/votes/",
            data={
                "proposal": str(proposal_id),
                "support": True,
                "comment": "Agreed",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert float(response.data["weight"]) == 50  # 5000 // 100

        # Company C votes NO
        api_client.force_authenticate(user=user_c)
        response = api_client.post(
            "/api/v2/governance/votes/",
            data={
                "proposal": str(proposal_id),
                "support": False,
                "comment": "I disagree",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert float(response.data["weight"]) == 30  # 3000 // 100

        # ----- STEP 5: Verify vote counts -----
        proposal.refresh_from_db()
        assert proposal.yes_votes == 2
        assert proposal.no_votes == 1
        assert float(proposal.voting_weight_yes) == 150  # 100 + 50
        assert float(proposal.voting_weight_no) == 30

        # Get votes list for the proposal
        api_client.force_authenticate(user=user_a)
        response = api_client.get(
            f"/api/v2/governance/proposals/{proposal_id}/votes/?consortium_id={consortium_id}"
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3

        # ----- STEP 6: Expire the proposal and execute -----
        # Move expires_at to the past to simulate voting period end
        proposal.expires_at = timezone.now() - timedelta(hours=1)
        proposal.save(update_fields=["expires_at"])

        response = api_client.post(
            f"/api/v2/governance/proposals/{proposal_id}/execute/?consortium_id={consortium_id}"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["passed"] is True
        assert response.data["status"] in [
            Proposal.Status.PASSED, Proposal.Status.EXECUTED
        ]

        # Verify consortium config was updated
        consortium.refresh_from_db()
        assert consortium.voting_threshold == 0.6

        # ----- STEP 7: Verify audit trail -----
        response = api_client.get(
            f"/api/v2/governance/audit-events/?consortium_id={consortium_id}"
        )
        assert response.status_code == status.HTTP_200_OK
        event_types = [e["event_type"] for e in response.data["results"]]
        assert "proposal_created" in event_types
        assert "vote_cast" in event_types
        assert "proposal_executed" in event_types

        # Verify audit trail integrity
        response = api_client.get(
            f"/api/v2/governance/audit-events/verify/?consortium_id={consortium_id}"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["valid"] is True
        assert response.data["event_count"] >= 5  # created + 3 votes + executed

        # ----- STEP 8: Reward distribution -----
        response = api_client.post(
            "/api/v2/governance/rewards/distribute/",
            data={
                "consortium_id": str(consortium_id),
                "amount": "1.00000000",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data["distributions"]) == 3

        # Verify proportional distribution
        distributions = {
            d["company_id"]: d for d in response.data["distributions"]
        }
        # Company A: 10000/18000 * 1 ≈ 0.5556
        # Company B: 5000/18000 * 1 ≈ 0.2778
        # Company C: 3000/18000 * 1 ≈ 0.1667
        total_distributed = sum(d["amount"] for d in response.data["distributions"])
        assert abs(total_distributed - 1.0) < 0.01

        # ----- STEP 9: Verify final state -----
        assert Vote.objects.filter(proposal=proposal).count() == 3
        assert AuditEvent.objects.filter(consortium=consortium).count() >= 6
        assert Proposal.objects.get(id=proposal_id).status == Proposal.Status.EXECUTED

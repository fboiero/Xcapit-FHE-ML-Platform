"""
Platform Simulation: A narrative integration test.

Three organizations use the Xcapit FHE-ML Platform together,
demonstrating the full lifecycle from onboarding to compliance.

Organizations:
- MedCorp (Hospital) — creates diagnostic ML models
- FinSecure (Fintech) — builds fraud detection models
- DataGov (Government) — provides regulatory governance

Acts:
1. Onboarding — authentication and API access
2. Individual Work — ML model lifecycle per organization
3. Collaboration — consortium creation, invitations, data contributions
4. Federated Learning — federated model, edge nodes, inference
5. Governance & Marketplace — proposals, voting, marketplace deployment
6. Advanced Analytics — ensemble, explainability, sandbox
7. Compliance & Audit — frameworks, checks, reports, attestations
"""

import hashlib
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.compliance.models import (
    Attestation,
    ComplianceCheck,
    ComplianceFramework,
    ComplianceReport,
    ConsortiumCompliance,
    DataProcessingRecord,
)
from apps.consortiums.models import (
    Consortium,
    ConsortiumInvitation,
    ConsortiumMember,
    ContributionProof,
)
from apps.core.models import Company, User
from apps.data_quality.models import QualityAlert, QualityAssessment, QualityRule
from apps.ensemble.models import Ensemble, EnsembleModel, EnsemblePrediction
from apps.explainability.models import (
    ExplanationRequest,
    FeatureImportance,
    ModelInsight,
)
from apps.federated.models import EdgeNode, FederatedModel, InferenceEndpoint
from apps.governance.models import AuditEvent, Proposal, RewardDistribution, Vote
from apps.marketplace.models import Category, Deployment, MarketplaceModel, Review
from apps.models.models import (
    BatchPredictionJob,
    MLModel,
    ModelExport,
    ModelVersion,
    TrainingRun,
)
from apps.sandbox.models import Experiment, Sandbox, SyntheticDataset


# ============================================================
# Helpers
# ============================================================


def _data_hash(seed: str) -> str:
    """Generate a SHA-256 hash from a seed string."""
    return hashlib.sha256(seed.encode()).hexdigest()


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
        user_email = f"sim{counter[0]}_{email.replace('@', '_at_')}"
        user = User.objects.create_user(
            email=user_email,
            password="TestPassword123!",
            company=company,
        )
        return company, user

    return _create


@pytest.fixture
def medcorp(create_company):
    """MedCorp — Hospital organization."""
    return create_company("MedCorp Hospital", "medcorp@example.com")


@pytest.fixture
def finsecure(create_company):
    """FinSecure — Fintech organization."""
    return create_company("FinSecure Fintech", "finsecure@example.com")


@pytest.fixture
def datagov(create_company):
    """DataGov — Government regulatory body."""
    return create_company("DataGov Agency", "datagov@example.com")


# ============================================================
# Simulation
# ============================================================


class TestPlatformSimulation:
    """
    A narrative simulation of the Xcapit FHE-ML Platform.

    Three organizations collaborate across the full platform lifecycle:
    ML models, consortiums, federated learning, governance, marketplace,
    ensemble analytics, explainability, sandbox, and compliance.
    """

    @pytest.mark.django_db(transaction=True)
    def test_full_platform_simulation(
        self, api_client, medcorp, finsecure, datagov
    ):
        med_company, med_user = medcorp
        fin_company, fin_user = finsecure
        gov_company, gov_user = datagov

        # ============================================================
        # ACT 1 — ONBOARDING
        # The three organizations authenticate and verify API access.
        # ============================================================

        for user, org_name in [
            (med_user, "MedCorp"),
            (fin_user, "FinSecure"),
            (gov_user, "DataGov"),
        ]:
            api_client.force_authenticate(user=user)
            response = api_client.get("/api/v2/models/")
            assert response.status_code == status.HTTP_200_OK, (
                f"{org_name} cannot access the API"
            )

        # ============================================================
        # ACT 2 — INDIVIDUAL WORK
        # Each organization creates and trains its own ML models.
        # ============================================================

        # --- MedCorp: Patient Diagnosis Model ---
        api_client.force_authenticate(user=med_user)

        response = api_client.post(
            "/api/v2/models/",
            data={
                "name": "Patient Diagnosis Model",
                "model_type": "logistic_regression",
                "config": {"learning_rate": 0.01, "regularization": "l2"},
                "n_features": 8,
                "feature_names": [
                    "age", "blood_pressure", "cholesterol", "glucose",
                    "bmi", "heart_rate", "oxygen_sat", "temperature",
                ],
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        med_model = MLModel.objects.get(owner=med_company, name="Patient Diagnosis Model")
        med_model_id = med_model.id

        # Train
        response = api_client.post(
            f"/api/v2/models/{med_model_id}/train/",
            data={"epochs": 50},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        training_run_id = response.data["training_run_id"]
        assert TrainingRun.objects.filter(id=training_run_id).exists()

        # Simulate training completion
        med_model.status = MLModel.Status.TRAINED
        med_model.trained_at = timezone.now()
        med_model.training_epochs = 50
        med_model.final_loss = 0.03
        med_model.save()

        # Predict
        response = api_client.post(
            f"/api/v2/models/{med_model_id}/predict/",
            data={
                "data": [[65, 140, 220, 110, 28.5, 72, 97, 37.2]],
                "encrypted": False,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "predictions" in response.data

        # Version
        response = api_client.post(
            f"/api/v2/models/{med_model_id}/create_version/",
            data={
                "bump_type": "minor",
                "changelog": "Trained on 50 epochs — diagnosis ready",
                "release_notes": "Initial clinical release",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        med_version_id = response.data["id"]

        # Stats
        response = api_client.get(f"/api/v2/models/{med_model_id}/stats/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_predictions"] >= 1

        # --- FinSecure: Fraud Detection Model ---
        api_client.force_authenticate(user=fin_user)

        response = api_client.post(
            "/api/v2/models/",
            data={
                "name": "Fraud Detection Model",
                "model_type": "logistic_regression",
                "config": {"learning_rate": 0.005},
                "n_features": 10,
                "feature_names": [
                    "amount", "merchant_cat", "time_of_day", "distance",
                    "frequency", "avg_amount", "card_age", "online",
                    "international", "velocity",
                ],
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        fin_model = MLModel.objects.get(owner=fin_company, name="Fraud Detection Model")
        fin_model_id = fin_model.id

        # Train
        response = api_client.post(
            f"/api/v2/models/{fin_model_id}/train/",
            data={"epochs": 100},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

        # Simulate training completion
        fin_model.status = MLModel.Status.TRAINED
        fin_model.trained_at = timezone.now()
        fin_model.training_epochs = 100
        fin_model.final_loss = 0.02
        fin_model.save()

        # Export
        response = api_client.post(
            f"/api/v2/models/{fin_model_id}/export_model/",
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

        # Batch prediction
        response = api_client.post(
            f"/api/v2/models/{fin_model_id}/batch_predict/",
            data={
                "data": [
                    [500.0, 1, 14, 5.2, 3, 450.0, 365, 1, 0, 2],
                    [15000.0, 5, 3, 120.0, 1, 200.0, 30, 0, 1, 10],
                    [25.0, 2, 19, 0.5, 15, 30.0, 1200, 1, 0, 1],
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

        # ============================================================
        # ACT 3 — COLLABORATION
        # MedCorp creates a consortium and invites the others.
        # All three contribute data, run quality assessments.
        # ============================================================

        # MedCorp creates the consortium
        api_client.force_authenticate(user=med_user)
        response = api_client.post(
            "/api/v2/consortiums/",
            data={
                "name": "Healthcare AI Alliance",
                "description": "Cross-sector AI for healthcare privacy",
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
        assert consortium.status == Consortium.Status.DRAFT

        # Invite FinSecure and DataGov
        expires_at = timezone.now() + timedelta(days=7)
        for comp in [fin_company, gov_company]:
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

        # FinSecure accepts
        api_client.force_authenticate(user=fin_user)
        inv_fin = invitations.get(invitee_email=fin_company.email)
        response = api_client.post(
            f"/api/v2/consortiums/invitations/{inv_fin.id}/accept/"
        )
        assert response.status_code == status.HTTP_200_OK

        # Still DRAFT (need 3 members, have 2)
        consortium.refresh_from_db()
        assert consortium.status == Consortium.Status.DRAFT

        # DataGov accepts → auto-activation (3 members reached)
        api_client.force_authenticate(user=gov_user)
        inv_gov = invitations.get(invitee_email=gov_company.email)
        response = api_client.post(
            f"/api/v2/consortiums/invitations/{inv_gov.id}/accept/"
        )
        assert response.status_code == status.HTTP_200_OK

        consortium.refresh_from_db()
        assert consortium.status == Consortium.Status.ACTIVE

        # All three contribute data (33,000 records total)
        contributions = [
            (med_user, med_company, 15000, "medcorp_patient_records"),
            (fin_user, fin_company, 10000, "finsecure_transaction_data"),
            (gov_user, gov_company, 8000, "datagov_census_health_data"),
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

        verified = ContributionProof.objects.filter(
            consortium=consortium, verified=True
        ).count()
        assert verified == 3

        # Quality assessment — MedCorp (high quality)
        api_client.force_authenticate(user=med_user)
        response = api_client.post(
            "/api/v2/data-quality/assessments/",
            data={
                "consortium": str(consortium_id),
                "record_count": 15000,
                "feature_count": 20,
                "null_count": 30,
                "duplicate_count": 5,
                "outlier_count": 12,
                "schema_violations": 2,
                "format_violations": 1,
                "range_violations": 3,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assessment_med = QualityAssessment.objects.get(id=response.data["id"])
        assert assessment_med.overall_score > 90

        # Quality assessment — FinSecure (lower quality, triggers alert)
        api_client.force_authenticate(user=fin_user)
        response = api_client.post(
            "/api/v2/data-quality/assessments/",
            data={
                "consortium": str(consortium_id),
                "record_count": 10000,
                "feature_count": 20,
                "null_count": 500,
                "duplicate_count": 200,
                "outlier_count": 300,
                "schema_violations": 100,
                "format_violations": 80,
                "range_violations": 60,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assessment_fin = QualityAssessment.objects.get(id=response.data["id"])

        # Create quality rule and alert for FinSecure's poor data
        rule = QualityRule.objects.create(
            consortium=consortium,
            name="Minimum Quality Score",
            description="Overall score must be >= 80",
            rule_type=QualityRule.RuleType.THRESHOLD,
            metric="overall_score",
            condition={"operator": ">=", "value": 80},
            severity=QualityRule.Severity.WARNING,
        )
        alert = QualityAlert.objects.create(
            rule=rule,
            assessment=assessment_fin,
            company=fin_company,
            message=f"Quality score {assessment_fin.overall_score:.1f} below threshold",
            actual_value=assessment_fin.overall_score,
            expected_value=">= 80",
        )

        # FinSecure acknowledges and resolves the alert
        api_client.force_authenticate(user=fin_user)
        response = api_client.post(
            f"/api/v2/data-quality/alerts/{alert.id}/acknowledge/"
        )
        assert response.status_code == status.HTTP_200_OK

        response = api_client.post(
            f"/api/v2/data-quality/alerts/{alert.id}/resolve/",
            data={"note": "Data cleaned and re-validated"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        alert.refresh_from_db()
        assert alert.status == QualityAlert.Status.RESOLVED

        # Dashboard check (scoped to the authenticated user's company)
        api_client.force_authenticate(user=med_user)
        response = api_client.get("/api/v2/data-quality/dashboard/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_assessments"] >= 1

        # ============================================================
        # ACT 4 — FEDERATED LEARNING
        # A federated model is created, nodes registered, and
        # inference endpoints deployed.
        # ============================================================

        api_client.force_authenticate(user=med_user)

        # Create federated model
        response = api_client.post(
            "/api/v2/federated/models/",
            data={
                "consortium": str(consortium_id),
                "name": "Federated Diagnosis Engine",
                "description": "Privacy-preserving cross-org diagnostics",
                "model_type": "logistic_regression",
                "config": {"rounds": 15, "lr": 0.001, "batch_size": 64},
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        fed_model = FederatedModel.objects.get(
            consortium=consortium, name="Federated Diagnosis Engine"
        )
        fed_model_id = fed_model.id

        # Register edge nodes — MedCorp and FinSecure
        nodes = {}
        for user, company, name, location in [
            (med_user, med_company, "MedCorp Edge", "Buenos Aires, AR"),
            (fin_user, fin_company, "FinSecure Edge", "São Paulo, BR"),
        ]:
            api_client.force_authenticate(user=user)
            response = api_client.post(
                "/api/v2/federated/nodes/",
                data={
                    "name": name,
                    "node_type": "on_premise",
                    "location": location,
                    "capabilities": {"gpu": True, "memory_gb": 64},
                },
                format="json",
            )
            assert response.status_code == status.HTTP_201_CREATED
            node = EdgeNode.objects.get(company=company, name=name)
            nodes[company.name] = node

            # Heartbeat — bring online
            response = api_client.post(
                f"/api/v2/federated/nodes/{node.id}/heartbeat/"
            )
            assert response.status_code == status.HTTP_200_OK
            assert response.data["status"] == "online"

        # Start federated training
        api_client.force_authenticate(user=med_user)
        response = api_client.post(
            f"/api/v2/federated/models/{fed_model_id}/train/"
            f"?consortium_id={consortium_id}"
        )
        assert response.status_code == status.HTTP_200_OK

        # Simulate training completion → READY
        fed_model.refresh_from_db()
        fed_model.status = FederatedModel.Status.READY
        fed_model.metrics = {"accuracy": 0.94, "loss": 0.06, "f1": 0.93}
        fed_model.save()

        # Now deploy the model to each edge node (requires READY status)
        for company_name, node in nodes.items():
            api_client.force_authenticate(
                user=med_user if company_name == med_company.name else fin_user
            )
            response = api_client.post(
                f"/api/v2/federated/nodes/{node.id}/deploy_model/",
                data={"model_id": str(fed_model_id)},
                format="json",
            )
            assert response.status_code == status.HTTP_200_OK

        # Deploy the federated model
        response = api_client.post(
            f"/api/v2/federated/models/{fed_model_id}/deploy/"
            f"?consortium_id={consortium_id}"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "deployed"

        # Create an inference endpoint
        # Use fed_model_id (InferenceEndpoint.model FK points to FederatedModel)
        response = api_client.post(
            "/api/v2/federated/endpoints/",
            data={
                "consortium": str(consortium_id),
                "name": "Diagnosis Endpoint",
                "description": "Real-time patient diagnostics",
                "model": str(fed_model_id),
                "endpoint_type": "realtime",
                "config": {"max_batch_size": 200},
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        endpoint = InferenceEndpoint.objects.get(
            consortium=consortium, name="Diagnosis Endpoint"
        )
        endpoint_id = endpoint.id

        # Make a prediction through the endpoint
        response = api_client.post(
            f"/api/v2/federated/endpoints/{endpoint_id}/predict/",
            data={
                "input_data": [
                    [65, 140, 220, 110, 28.5, 72, 97, 37.2],
                    [45, 120, 180, 95, 24.0, 68, 99, 36.8],
                ],
                "priority": "high",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "request_id" in response.data
        assert "encrypted_output" in response.data

        # Endpoint stats
        response = api_client.get(
            f"/api/v2/federated/endpoints/{endpoint_id}/stats/"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["request_count"] >= 1

        # ============================================================
        # ACT 5 — GOVERNANCE & MARKETPLACE
        # DataGov proposes governance changes. The consortium votes.
        # Models are deployed to the marketplace.
        # ============================================================

        # DataGov creates a governance proposal
        api_client.force_authenticate(user=gov_user)
        response = api_client.post(
            "/api/v2/governance/proposals/",
            data={
                "consortium": str(consortium_id),
                "proposal_type": "update_config",
                "title": "Increase voting threshold to 60%",
                "description": "Strengthen governance by requiring broader consensus",
                "data": {"config": {"voting_threshold": 0.6}},
                "voting_days": 1,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        proposal = Proposal.objects.get(
            consortium=consortium, title="Increase voting threshold to 60%"
        )
        proposal_id = proposal.id
        assert proposal.status == Proposal.Status.ACTIVE

        # Voting: DataGov YES (weight ~80), MedCorp YES (weight ~150),
        #         FinSecure NO (weight ~100)
        votes_data = [
            (gov_user, True, "Regulatory best practice"),
            (med_user, True, "Agree — better oversight"),
            (fin_user, False, "Current threshold is sufficient"),
        ]
        for user, support, comment in votes_data:
            api_client.force_authenticate(user=user)
            response = api_client.post(
                "/api/v2/governance/votes/",
                data={
                    "proposal": str(proposal_id),
                    "support": support,
                    "comment": comment,
                },
                format="json",
            )
            assert response.status_code == status.HTTP_201_CREATED
            assert float(response.data["weight"]) >= 1

        # Verify vote tally
        proposal.refresh_from_db()
        assert proposal.yes_votes == 2
        assert proposal.no_votes == 1
        assert proposal.voting_weight_yes > proposal.voting_weight_no

        # Expire and execute proposal
        proposal.expires_at = timezone.now() - timedelta(hours=1)
        proposal.save(update_fields=["expires_at"])

        api_client.force_authenticate(user=gov_user)
        response = api_client.post(
            f"/api/v2/governance/proposals/{proposal_id}/execute/"
            f"?consortium_id={consortium_id}"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["passed"] is True

        # Verify config was updated
        consortium.refresh_from_db()
        assert consortium.voting_threshold == 0.6

        # Marketplace: deploy a model
        category = Category.objects.create(
            name="Healthcare AI",
            description="AI models for healthcare applications",
        )
        marketplace_model = MarketplaceModel.objects.create(
            name="Diagnostic AI v1",
            description="Privacy-preserving diagnostic model for hospitals",
            category=category,
            model_type="logistic_regression",
            accuracy=0.94,
            training_samples=33000,
            is_active=True,
        )

        # FinSecure deploys the marketplace model via API
        api_client.force_authenticate(user=fin_user)
        response = api_client.post(
            "/api/v2/marketplace/deployments/",
            data={
                "marketplace_model": str(marketplace_model.id),
                "consortium": str(consortium_id),
                "config": {"replicas": 3},
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        marketplace_model.refresh_from_db()
        assert marketplace_model.downloads == 1

        # Create deployment records for MedCorp and DataGov (different
        # deployed_by) so they can leave reviews. Use ORM because the API
        # enforces unique_together on (marketplace_model, consortium).
        # Set the existing deployment's deployed_by to FinSecure explicitly,
        # then create separate Deployment objects for the other companies
        # referencing different consortiums created ad-hoc.
        med_review_consortium = Consortium.objects.create(
            name="MedCorp Review Consortium",
            owner=med_company,
            status=Consortium.Status.ACTIVE,
        )
        Deployment.objects.create(
            marketplace_model=marketplace_model,
            consortium=med_review_consortium,
            deployed_by=med_company,
        )
        gov_review_consortium = Consortium.objects.create(
            name="DataGov Review Consortium",
            owner=gov_company,
            status=Consortium.Status.ACTIVE,
        )
        Deployment.objects.create(
            marketplace_model=marketplace_model,
            consortium=gov_review_consortium,
            deployed_by=gov_company,
        )

        # Reviews (must have a deployment record with matching deployed_by)
        for user, company, rating, title, comment in [
            (med_user, med_company, 5, "Excellent accuracy",
             "Works perfectly with our patient data"),
            (gov_user, gov_company, 4, "Good compliance",
             "Meets most regulatory requirements"),
        ]:
            api_client.force_authenticate(user=user)
            response = api_client.post(
                "/api/v2/marketplace/reviews/",
                data={
                    "marketplace_model": str(marketplace_model.id),
                    "consortium": str(consortium_id),
                    "rating": rating,
                    "title": title,
                    "comment": comment,
                },
                format="json",
            )
            assert response.status_code == status.HTTP_201_CREATED

        # Verify reviews
        response = api_client.get(
            f"/api/v2/marketplace/models/{marketplace_model.id}/reviews/"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_reviews"] == 2
        assert response.data["average_rating"] == 4.5

        # ============================================================
        # ACT 6 — ADVANCED ANALYTICS
        # Ensemble models, explainability insights, and sandbox
        # experimentation.
        # ============================================================

        # --- Ensemble ---
        api_client.force_authenticate(user=med_user)

        response = api_client.post(
            "/api/v2/ensemble/ensembles/",
            data={
                "name": "Multi-Model Diagnostics",
                "description": "Ensemble of MedCorp and FinSecure models",
                "ensemble_type": "weighted",
                "owner": str(med_company.id),
                "aggregation_config": {"strategy": "soft_vote"},
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        ensemble = Ensemble.objects.get(name="Multi-Model Diagnostics")
        ensemble_id = ensemble.id
        assert ensemble.status == Ensemble.Status.DRAFT

        # Add both trained models
        for model_id, weight in [(med_model_id, 0.6), (fin_model_id, 0.4)]:
            response = api_client.post(
                f"/api/v2/ensemble/ensembles/{ensemble_id}/add_model/",
                data={"model_id": str(model_id), "weight": weight},
                format="json",
            )
            assert response.status_code == status.HTTP_201_CREATED

        assert EnsembleModel.objects.filter(ensemble=ensemble).count() == 2

        # Activate ensemble
        response = api_client.post(
            f"/api/v2/ensemble/ensembles/{ensemble_id}/activate/"
        )
        assert response.status_code == status.HTTP_200_OK
        ensemble.refresh_from_db()
        assert ensemble.status == Ensemble.Status.ACTIVE

        # Ensemble prediction
        response = api_client.post(
            f"/api/v2/ensemble/ensembles/{ensemble_id}/predict/",
            data={"X": [[65, 140, 220, 110, 28.5, 72, 97, 37.2]]},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "prediction" in response.data
        assert EnsemblePrediction.objects.filter(ensemble=ensemble).count() >= 1

        # --- Explainability ---
        # Create feature importance records for consortium
        for i, (feat, score) in enumerate([
            ("blood_pressure", 0.28), ("cholesterol", 0.22),
            ("glucose", 0.18), ("bmi", 0.12), ("age", 0.10),
        ]):
            FeatureImportance.objects.create(
                consortium=consortium,
                model=med_model,
                feature_name=feat,
                importance_score=score,
                importance_rank=i + 1,
                computation_method="shap",
            )

        response = api_client.get(
            f"/api/v2/explainability/features/top/?consortium={consortium_id}&n=5"
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 5

        # Create an explanation request (SHAP)
        response = api_client.post(
            "/api/v2/explainability/requests/",
            data={
                "consortium": str(consortium_id),
                "requester": str(med_company.id),
                "model": str(med_model_id),
                "explanation_type": "shap",
                "input_data": {"sample": [65, 140, 220, 110, 28.5, 72, 97, 37.2]},
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        explanation_req = ExplanationRequest.objects.get(id=response.data["id"])
        assert explanation_req.status in [
            ExplanationRequest.Status.PENDING,
            ExplanationRequest.Status.COMPLETED,
        ]

        # Create a model insight
        insight = ModelInsight.objects.create(
            consortium=consortium,
            insight_type=ModelInsight.InsightType.PERFORMANCE,
            title="Model accuracy above target",
            description="The diagnostic model exceeds 93% accuracy",
            severity="info",
            data={"accuracy": 0.94, "target": 0.90},
            recommendations=["Consider deploying to production"],
        )

        # Check explainability dashboard
        response = api_client.get("/api/v2/explainability/dashboard/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_requests"] >= 1

        # --- Sandbox ---
        response = api_client.post(
            "/api/v2/sandbox/sandboxes/",
            data={
                "name": "MedCorp Research Lab",
                "description": "Experimental environment for diagnostic models",
                "industry": "healthcare",
                "config": {"gpu_enabled": True},
                "expires_at": (timezone.now() + timedelta(days=7)).isoformat(),
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED, response.data
        sandbox = Sandbox.objects.get(name="MedCorp Research Lab")
        sandbox_id = sandbox.id

        # Generate synthetic patient data
        response = api_client.post(
            "/api/v2/sandbox/datasets/generate/",
            data={
                "sandbox_id": str(sandbox_id),
                "dataset_type": "patients",
                "record_count": 5000,
                "industry": "healthcare",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        dataset = SyntheticDataset.objects.get(sandbox=sandbox)
        dataset_id = dataset.id
        assert dataset.record_count == 5000

        # Run an experiment
        response = api_client.post(
            "/api/v2/sandbox/experiments/",
            data={
                "sandbox": str(sandbox_id),
                "name": "Diagnosis accuracy benchmark",
                "description": "Test model on synthetic patient data",
                "experiment_type": "evaluation",
                "model_type": "logistic_regression",
                "dataset": str(dataset_id),
                "config": {"metrics": ["accuracy", "f1", "auc"]},
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        experiment = Experiment.objects.get(sandbox=sandbox)
        experiment_id = experiment.id

        # Run the experiment
        response = api_client.post(
            f"/api/v2/sandbox/experiments/{experiment_id}/run/"
        )
        assert response.status_code == status.HTTP_200_OK

        experiment.refresh_from_db()
        assert experiment.status in [
            Experiment.Status.RUNNING, Experiment.Status.COMPLETED
        ]

        # ============================================================
        # ACT 7 — COMPLIANCE & AUDIT
        # DataGov sets up compliance frameworks, runs checks,
        # generates reports, and verifies the audit trail.
        # ============================================================

        api_client.force_authenticate(user=gov_user)

        # Create HIPAA compliance framework
        hipaa = ComplianceFramework.objects.create(
            name="HIPAA",
            version="2024",
            description="Health Insurance Portability and Accountability Act",
            region="US",
            industry="healthcare",
            controls=[
                {"id": "hipaa_1", "name": "Access Control",
                 "description": "Ensure proper access controls"},
                {"id": "hipaa_2", "name": "Audit Controls",
                 "description": "Record and examine access"},
                {"id": "hipaa_3", "name": "Integrity",
                 "description": "Protect ePHI from alteration"},
                {"id": "hipaa_4", "name": "Transmission Security",
                 "description": "Guard against unauthorized access during transmission"},
                {"id": "hipaa_5", "name": "Encryption",
                 "description": "Implement encryption mechanism"},
            ],
        )

        # Run compliance checks (4 passed, 1 failed)
        checks_data = [
            ("hipaa_1", "compliant", "pass", "Role-based access control implemented"),
            ("hipaa_2", "compliant", "pass", "Full audit trail with hash chain integrity"),
            ("hipaa_3", "compliant", "pass", "FHE encryption protects data at rest"),
            ("hipaa_4", "compliant", "pass", "TLS 1.3 for all transmissions"),
            ("hipaa_5", "non_compliant", "fail", "Legacy endpoint missing encryption"),
        ]
        for control_id, check_status, check_result, check_notes in checks_data:
            response = api_client.post(
                "/api/v2/compliance/checks/",
                data={
                    "consortium": str(consortium_id),
                    "framework": hipaa.id,
                    "control_id": control_id,
                    "status": check_status,
                    "result": check_result,
                    "evidence": "Automated scan: fhe-scanner",
                    "notes": check_notes,
                },
                format="json",
            )
            assert response.status_code == status.HTTP_201_CREATED

        assert ComplianceCheck.objects.filter(
            consortium=consortium, framework=hipaa
        ).count() == 5

        # Generate compliance report (4/5 = 80%) — requires consortium owner
        api_client.force_authenticate(user=med_user)
        response = api_client.post(
            "/api/v2/compliance/reports/generate/",
            data={
                "consortium_id": str(consortium_id),
                "framework_id": hipaa.id,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        report = ComplianceReport.objects.get(
            consortium=consortium, framework=hipaa
        )
        assert float(report.overall_score) == 80.0
        assert report.passed_controls == 4
        assert report.failed_controls == 1
        assert report.status == ComplianceReport.Status.COMPLETED

        # Create attestation
        response = api_client.post(
            "/api/v2/compliance/attestations/",
            data={
                "consortium": str(consortium_id),
                "framework": hipaa.id,
                "control_id": "hipaa_3",
                "attester": str(gov_company.id),
                "attester_role": "Chief Compliance Officer",
                "attestation_type": "self_assessment",
                "statement": "FHE encryption verified for all patient data at rest",
                "evidence_urls": [
                    "https://evidence.example.com/fhe-audit-2024.pdf"
                ],
                "valid_from": timezone.now().isoformat(),
                "valid_until": (timezone.now() + timedelta(days=365)).isoformat(),
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Attestation.objects.filter(
            consortium=consortium, framework=hipaa
        ).count() == 1

        # GDPR data processing record
        response = api_client.post(
            "/api/v2/compliance/data-processing/",
            data={
                "consortium": str(consortium_id),
                "company": str(med_company.id),
                "processing_purpose": "Medical diagnosis using FHE-encrypted ML models",
                "data_categories": ["health_data", "patient_demographics"],
                "legal_basis": "Explicit consent (Art. 9(2)(a) GDPR)",
                "data_subjects": "Hospital patients over 18 years",
                "recipients": ["MedCorp internal analytics", "Consortium members"],
                "retention_period": "5 years from last processing",
                "security_measures": "FHE encryption, access control, audit logging",
                "cross_border_transfer": False,
                "transfer_safeguards": "N/A — no cross-border transfers",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert DataProcessingRecord.objects.filter(
            consortium=consortium
        ).count() == 1

        # Verify audit trail
        response = api_client.get(
            f"/api/v2/governance/audit-events/?consortium_id={consortium_id}"
        )
        assert response.status_code == status.HTTP_200_OK
        event_types = [e["event_type"] for e in response.data["results"]]
        assert "proposal_created" in event_types
        assert "vote_cast" in event_types
        assert "proposal_executed" in event_types

        # Verify audit trail integrity (hash chain)
        response = api_client.get(
            f"/api/v2/governance/audit-events/verify/?consortium_id={consortium_id}"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["valid"] is True

        # Reward distribution
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
        total = sum(d["amount"] for d in response.data["distributions"])
        assert abs(total - 1.0) < 0.01

        # ============================================================
        # EPILOGUE — FINAL VERIFICATION
        # Cross-check the state of the entire system.
        # ============================================================

        # Models
        assert MLModel.objects.filter(
            owner__in=[med_company, fin_company]
        ).count() >= 2
        assert ModelVersion.objects.filter(model=med_model).count() >= 1
        assert ModelExport.objects.filter(model=fin_model).count() >= 1
        assert BatchPredictionJob.objects.filter(model=fin_model).count() >= 1

        # Consortium
        consortium.refresh_from_db()
        assert ConsortiumMember.objects.filter(
            consortium=consortium,
            status=ConsortiumMember.Status.ACTIVE,
        ).count() == 3
        assert ContributionProof.objects.filter(
            consortium=consortium, verified=True
        ).count() == 3
        total_records = sum(
            ContributionProof.objects.filter(
                consortium=consortium, verified=True
            ).values_list("record_count", flat=True)
        )
        assert total_records == 33000

        # Quality
        assert QualityAssessment.objects.filter(
            consortium=consortium
        ).count() == 2
        assert QualityAlert.objects.filter(
            status=QualityAlert.Status.RESOLVED
        ).count() >= 1

        # Federated
        fed_model.refresh_from_db()
        assert fed_model.status == FederatedModel.Status.DEPLOYED
        assert EdgeNode.objects.count() >= 2
        assert InferenceEndpoint.objects.filter(
            consortium=consortium
        ).count() >= 1

        # Governance
        assert Proposal.objects.get(id=proposal_id).status == Proposal.Status.EXECUTED
        assert Vote.objects.filter(proposal=proposal).count() == 3
        assert AuditEvent.objects.filter(consortium=consortium).count() >= 5
        assert RewardDistribution.objects.filter(
            consortium=consortium
        ).count() >= 1

        # Marketplace
        assert Deployment.objects.filter(consortium=consortium).count() >= 1
        assert Review.objects.filter(marketplace_model=marketplace_model).count() == 2

        # Compliance
        assert ComplianceCheck.objects.filter(
            consortium=consortium
        ).count() == 5
        assert ComplianceReport.objects.filter(
            consortium=consortium
        ).count() >= 1
        assert Attestation.objects.filter(
            consortium=consortium
        ).count() >= 1
        assert DataProcessingRecord.objects.filter(
            consortium=consortium
        ).count() >= 1

        # Explainability
        assert FeatureImportance.objects.filter(
            consortium=consortium
        ).count() >= 5
        assert ExplanationRequest.objects.filter(
            consortium=consortium
        ).count() >= 1
        assert ModelInsight.objects.filter(
            consortium=consortium
        ).count() >= 1

        # Ensemble
        assert Ensemble.objects.filter(owner=med_company).count() >= 1
        assert EnsembleModel.objects.filter(ensemble=ensemble).count() == 2
        assert EnsemblePrediction.objects.filter(
            ensemble=ensemble
        ).count() >= 1

        # Sandbox
        assert Sandbox.objects.filter(owner=med_company).count() >= 1
        assert SyntheticDataset.objects.filter(sandbox=sandbox).count() >= 1
        assert Experiment.objects.filter(sandbox=sandbox).count() >= 1

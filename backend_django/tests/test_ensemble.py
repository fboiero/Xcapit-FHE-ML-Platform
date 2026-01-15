"""
Ensemble module tests for Xcapit FHE-ML Platform.
"""

import pytest
from rest_framework import status

from apps.ensemble.models import (
    Ensemble,
    EnsembleEvaluation,
    EnsembleModel,
    EnsemblePrediction,
)


@pytest.fixture
def ensemble(db, company):
    """Create a test ensemble."""
    return Ensemble.objects.create(
        name="Fraud Detection Ensemble",
        description="Ensemble of fraud detection models",
        owner=company,
        ensemble_type=Ensemble.EnsembleType.WEIGHTED,
        status=Ensemble.Status.ACTIVE,
        aggregation_config={"weights": [0.4, 0.35, 0.25]},
    )


@pytest.fixture
def ensemble_model(db, ensemble, ml_model):
    """Create a test ensemble model membership."""
    return EnsembleModel.objects.create(
        ensemble=ensemble,
        model=ml_model,
        weight=0.4,
        individual_accuracy=0.85,
        contribution_score=0.35,
        is_active=True,
    )


@pytest.fixture
def ensemble_prediction(db, ensemble, company):
    """Create a test ensemble prediction."""
    return EnsemblePrediction.objects.create(
        ensemble=ensemble,
        requester=company,
        input_hash="abc123def456",
        n_samples=100,
        prediction={"labels": [0, 1, 0, 1], "probabilities": [0.1, 0.9, 0.2, 0.8]},
        confidence=0.87,
        model_predictions={"model1": [0, 1, 0, 1], "model2": [0, 1, 1, 1]},
        latency_ms=45.5,
    )


@pytest.fixture
def ensemble_evaluation(db, ensemble):
    """Create a test ensemble evaluation."""
    return EnsembleEvaluation.objects.create(
        ensemble=ensemble,
        accuracy=0.92,
        precision=0.90,
        recall=0.88,
        f1_score=0.89,
        auc_roc=0.95,
        best_individual_accuracy=0.87,
        improvement_over_best=5.75,
        test_samples=1000,
        test_data_hash="test123hash456",
    )


@pytest.mark.django_db
class TestEnsembleModel:
    """Tests for Ensemble model."""

    def test_create_ensemble(self, ensemble):
        """Test creating an ensemble."""
        assert ensemble.id is not None
        assert ensemble.name == "Fraud Detection Ensemble"
        assert ensemble.ensemble_type == Ensemble.EnsembleType.WEIGHTED

    def test_model_count_property(self, ensemble, ensemble_model):
        """Test model_count property."""
        assert ensemble.model_count == 1

    def test_ensemble_types(self, company):
        """Test all ensemble types can be created."""
        for etype in Ensemble.EnsembleType:
            ens = Ensemble.objects.create(
                name=f"Test {etype.label}",
                owner=company,
                ensemble_type=etype,
            )
            assert ens.ensemble_type == etype


@pytest.mark.django_db
class TestEnsembleModelMembership:
    """Tests for EnsembleModel model."""

    def test_create_membership(self, ensemble_model):
        """Test creating an ensemble model membership."""
        assert ensemble_model.id is not None
        assert ensemble_model.weight == 0.4
        assert ensemble_model.is_active is True

    def test_unique_constraint(self, ensemble, ml_model):
        """Test unique constraint on ensemble + model."""
        EnsembleModel.objects.create(ensemble=ensemble, model=ml_model)

        with pytest.raises(Exception):
            EnsembleModel.objects.create(ensemble=ensemble, model=ml_model)


@pytest.mark.django_db
class TestEnsemblePrediction:
    """Tests for EnsemblePrediction model."""

    def test_create_prediction(self, ensemble_prediction):
        """Test creating an ensemble prediction."""
        assert ensemble_prediction.id is not None
        assert ensemble_prediction.n_samples == 100
        assert ensemble_prediction.confidence == 0.87

    def test_prediction_json_storage(self, ensemble_prediction):
        """Test prediction data is properly stored as JSON."""
        assert "labels" in ensemble_prediction.prediction
        assert "model1" in ensemble_prediction.model_predictions


@pytest.mark.django_db
class TestEnsembleEvaluation:
    """Tests for EnsembleEvaluation model."""

    def test_create_evaluation(self, ensemble_evaluation):
        """Test creating an ensemble evaluation."""
        assert ensemble_evaluation.id is not None
        assert ensemble_evaluation.accuracy == 0.92
        assert ensemble_evaluation.improvement_over_best == 5.75

    def test_evaluation_str(self, ensemble_evaluation):
        """Test evaluation string representation."""
        result = str(ensemble_evaluation)
        assert "92" in result  # 0.92 as percentage


@pytest.mark.django_db
class TestEnsembleEndpoints:
    """Tests for ensemble API endpoints."""

    def test_list_ensembles(self, auth_client, ensemble):
        """Test listing ensembles."""
        url = "/api/v2/ensemble/ensembles/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_create_ensemble(self, auth_client):
        """Test creating an ensemble."""
        url = "/api/v2/ensemble/ensembles/"
        data = {
            "name": "New Ensemble",
            "description": "A new test ensemble",
            "ensemble_type": "voting",
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Ensemble"

    def test_get_ensemble_detail(self, auth_client, ensemble):
        """Test getting ensemble detail."""
        url = f"/api/v2/ensemble/ensembles/{ensemble.id}/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Fraud Detection Ensemble"

    def test_update_ensemble(self, auth_client, ensemble):
        """Test updating an ensemble."""
        url = f"/api/v2/ensemble/ensembles/{ensemble.id}/"
        data = {"name": "Updated Ensemble Name"}

        response = auth_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        ensemble.refresh_from_db()
        assert ensemble.name == "Updated Ensemble Name"


@pytest.mark.django_db
class TestEnsembleModelEndpoints:
    """Tests for ensemble model membership API endpoints."""

    def test_add_model_to_ensemble(self, auth_client, ensemble, ml_model):
        """Test adding a model to an ensemble."""
        url = f"/api/v2/ensemble/ensembles/{ensemble.id}/models/"
        data = {
            "model": str(ml_model.id),
            "weight": 0.5,
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED

    def test_list_ensemble_models(self, auth_client, ensemble, ensemble_model):
        """Test listing models in an ensemble."""
        url = f"/api/v2/ensemble/ensembles/{ensemble.id}/models/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1


@pytest.mark.django_db
class TestEnsemblePredictionEndpoints:
    """Tests for ensemble prediction API endpoints."""

    def test_list_predictions(self, auth_client, ensemble_prediction):
        """Test listing ensemble predictions."""
        url = "/api/v2/ensemble/predictions/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestDataIsolation:
    """Tests for data isolation between companies."""

    def test_cannot_see_other_company_ensembles(self, auth_client, other_company):
        """Test user cannot see another company's ensembles."""
        Ensemble.objects.create(
            name="Secret Ensemble",
            owner=other_company,
        )

        url = "/api/v2/ensemble/ensembles/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        for ens in response.data.get("results", response.data):
            assert ens.get("owner") != str(other_company.id)

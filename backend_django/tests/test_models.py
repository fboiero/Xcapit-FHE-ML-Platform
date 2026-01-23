"""
ML Models module tests for Xcapit FHE-ML Platform.
"""

import pytest
from rest_framework import status

from apps.consortiums.models import ConsortiumMember
from apps.models.models import MLModel, PredictionLog, TrainingRun


@pytest.mark.django_db
class TestMLModelEndpoints:
    """Tests for ML model endpoints."""

    def test_create_model(self, auth_client, company, consortium):
        """Test creating an ML model."""
        ConsortiumMember.objects.get_or_create(
            consortium=consortium,
            company=company,
            defaults={
                "role": ConsortiumMember.Role.CONTRIBUTOR,
                "status": ConsortiumMember.Status.ACTIVE,
            },
        )

        url = "/api/v2/models/"
        data = {
            "name": "New Model",
            "model_type": "logistic_regression",
            "n_features": 10,
            "consortium": str(consortium.id),
            "config": {"learning_rate": 0.01},
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Model"
        assert MLModel.objects.filter(name="New Model").exists()

    def test_list_models(self, auth_client, ml_model):
        """Test listing ML models."""
        url = "/api/v2/models/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_get_model(self, auth_client, ml_model):
        """Test getting a single model."""
        url = f"/api/v2/models/{ml_model.id}/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == ml_model.name

    def test_update_model(self, auth_client, ml_model):
        """Test updating a model."""
        url = f"/api/v2/models/{ml_model.id}/"
        data = {"name": "Updated Model Name"}

        response = auth_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        ml_model.refresh_from_db()
        assert ml_model.name == "Updated Model Name"


@pytest.mark.django_db
class TestTrainingEndpoints:
    """Tests for model training endpoints."""

    def test_start_training(self, auth_client, company, consortium):
        """Test starting model training."""
        ConsortiumMember.objects.get_or_create(
            consortium=consortium,
            company=company,
            defaults={
                "role": ConsortiumMember.Role.CONTRIBUTOR,
                "status": ConsortiumMember.Status.ACTIVE,
            },
        )

        model = MLModel.objects.create(
            name="Training Model",
            owner=company,
            consortium=consortium,
            model_type=MLModel.ModelType.LINEAR_REGRESSION,
            status=MLModel.Status.CREATED,
        )

        url = f"/api/v2/models/{model.id}/train/"
        data = {"epochs": 10}

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "training_run_id" in response.data

        model.refresh_from_db()
        assert model.status == MLModel.Status.TRAINING

    def test_cannot_train_while_training(self, auth_client, company, consortium):
        """Test that training cannot be started while already training."""
        ConsortiumMember.objects.get_or_create(
            consortium=consortium,
            company=company,
            defaults={
                "role": ConsortiumMember.Role.CONTRIBUTOR,
                "status": ConsortiumMember.Status.ACTIVE,
            },
        )

        model = MLModel.objects.create(
            name="Training Model",
            owner=company,
            consortium=consortium,
            model_type=MLModel.ModelType.LINEAR_REGRESSION,
            status=MLModel.Status.TRAINING,
        )

        url = f"/api/v2/models/{model.id}/train/"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestPredictionEndpoints:
    """Tests for prediction endpoints."""

    def test_make_prediction(self, auth_client, ml_model):
        """Test making a prediction."""
        url = f"/api/v2/models/{ml_model.id}/predict/"
        data = {
            "data": [[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]],
            "encrypted": False,
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "predictions" in response.data
        assert "latency_ms" in response.data

        # Check prediction was logged
        assert PredictionLog.objects.filter(model=ml_model).exists()

    def test_cannot_predict_untrained_model(self, auth_client, company, consortium):
        """Test that prediction fails for untrained models."""
        ConsortiumMember.objects.get_or_create(
            consortium=consortium,
            company=company,
            defaults={
                "role": ConsortiumMember.Role.CONTRIBUTOR,
                "status": ConsortiumMember.Status.ACTIVE,
            },
        )

        model = MLModel.objects.create(
            name="Untrained Model",
            owner=company,
            consortium=consortium,
            model_type=MLModel.ModelType.LINEAR_REGRESSION,
            status=MLModel.Status.CREATED,
        )

        url = f"/api/v2/models/{model.id}/predict/"
        data = {"data": [[1.0, 2.0, 3.0]]}

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestModelStatsEndpoints:
    """Tests for model statistics endpoints."""

    def test_get_stats(self, auth_client, ml_model, company):
        """Test getting model statistics."""
        # Create some prediction logs
        PredictionLog.objects.create(
            model=ml_model,
            requester=company,
            n_samples=100,
            encrypted=False,
            latency_ms=50.5,
        )
        PredictionLog.objects.create(
            model=ml_model,
            requester=company,
            n_samples=200,
            encrypted=True,
            latency_ms=75.3,
        )

        url = f"/api/v2/models/{ml_model.id}/stats/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_predictions"] == 2
        assert response.data["total_samples"] == 300


@pytest.mark.django_db
class TestTrainingRunEndpoints:
    """Tests for training run endpoints."""

    def test_list_training_runs(self, auth_client, ml_model):
        """Test listing training runs."""
        TrainingRun.objects.create(
            model=ml_model,
            epochs_total=10,
            status=TrainingRun.Status.COMPLETED,
        )

        url = "/api/v2/models/training-runs/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_cancel_training_run(self, auth_client, ml_model):
        """Test cancelling a training run."""
        training_run = TrainingRun.objects.create(
            model=ml_model,
            epochs_total=10,
            status=TrainingRun.Status.RUNNING,
        )

        url = f"/api/v2/models/training-runs/{training_run.id}/cancel/"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        training_run.refresh_from_db()
        assert training_run.status == TrainingRun.Status.CANCELLED


@pytest.mark.django_db
class TestPredictionLogEndpoints:
    """Tests for prediction log endpoints."""

    def test_list_prediction_logs(self, auth_client, ml_model, company):
        """Test listing prediction logs."""
        PredictionLog.objects.create(
            model=ml_model,
            requester=company,
            n_samples=50,
            encrypted=False,
            latency_ms=25.0,
        )

        url = "/api/v2/models/predictions/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_filter_by_model(self, auth_client, ml_model, company):
        """Test filtering prediction logs by model."""
        PredictionLog.objects.create(
            model=ml_model,
            requester=company,
            n_samples=50,
            encrypted=False,
            latency_ms=25.0,
        )

        url = f"/api/v2/models/predictions/?model_id={ml_model.id}"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        for log in response.data.get("results", response.data):
            # Model field might be a UUID or string representation
            assert str(log["model"]) == str(ml_model.id)

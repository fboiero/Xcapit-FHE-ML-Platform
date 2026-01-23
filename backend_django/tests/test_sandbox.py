"""
Sandbox module tests for Xcapit FHE-ML Platform.

Tests for sandbox environments, synthetic data generation, and experiments.
"""

from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status

from apps.sandbox.models import Experiment, Sandbox, SandboxTemplate, SyntheticDataset


@pytest.mark.django_db
class TestSandboxTemplateEndpoints:
    """Tests for sandbox templates (read-only)."""

    def test_list_templates(self, auth_client):
        """Test listing sandbox templates."""
        SandboxTemplate.objects.create(
            id="fintech-template",
            name="Fintech Sandbox",
            description="Template for financial services",
            industry="fintech",
        )

        url = "/api/v2/sandbox/templates/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_filter_templates_by_industry(self, auth_client):
        """Test filtering templates by industry."""
        SandboxTemplate.objects.create(
            id="fintech-template",
            name="Fintech Sandbox",
            industry="fintech",
        )
        SandboxTemplate.objects.create(
            id="healthcare-template",
            name="Healthcare Sandbox",
            industry="healthcare",
        )

        url = "/api/v2/sandbox/templates/?industry=fintech"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        for template in response.data.get("results", response.data):
            assert template["industry"] == "fintech"

    def test_get_template(self, auth_client):
        """Test getting a single template."""
        template = SandboxTemplate.objects.create(
            id="test-template",
            name="Test Template",
            description="A test template",
        )

        url = f"/api/v2/sandbox/templates/{template.id}/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Test Template"

    def test_templates_are_read_only(self, auth_client):
        """Test templates cannot be created via API."""
        url = "/api/v2/sandbox/templates/"
        data = {
            "id": "new-template",
            "name": "New Template",
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestSandboxEndpoints:
    """Tests for sandbox CRUD operations."""

    def test_create_sandbox(self, auth_client, company):
        """Test creating a sandbox."""
        url = "/api/v2/sandbox/sandboxes/"
        expires_at = (timezone.now() + timedelta(days=7)).isoformat()
        data = {
            "name": "Test Sandbox",
            "description": "A test sandbox",
            "industry": "fintech",
            "expires_at": expires_at,
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Test Sandbox"
        assert Sandbox.objects.filter(name="Test Sandbox").exists()

    def test_list_sandboxes(self, auth_client, company):
        """Test listing sandboxes owned by user."""
        Sandbox.objects.create(
            name="My Sandbox",
            owner=company,
            expires_at=timezone.now() + timedelta(days=7),
        )

        url = "/api/v2/sandbox/sandboxes/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_get_sandbox(self, auth_client, company):
        """Test getting a single sandbox."""
        sandbox = Sandbox.objects.create(
            name="My Sandbox",
            owner=company,
            expires_at=timezone.now() + timedelta(days=7),
        )

        url = f"/api/v2/sandbox/sandboxes/{sandbox.id}/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "My Sandbox"

    def test_update_sandbox(self, auth_client, company):
        """Test updating a sandbox."""
        sandbox = Sandbox.objects.create(
            name="My Sandbox",
            owner=company,
            expires_at=timezone.now() + timedelta(days=7),
        )

        url = f"/api/v2/sandbox/sandboxes/{sandbox.id}/"
        data = {"description": "Updated description"}

        response = auth_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        sandbox.refresh_from_db()
        assert sandbox.description == "Updated description"

    def test_delete_sandbox(self, auth_client, company):
        """Test deleting a sandbox."""
        sandbox = Sandbox.objects.create(
            name="To Delete",
            owner=company,
            expires_at=timezone.now() + timedelta(days=7),
        )

        url = f"/api/v2/sandbox/sandboxes/{sandbox.id}/"

        response = auth_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Sandbox.objects.filter(id=sandbox.id).exists()

    def test_cannot_access_other_company_sandbox(self, other_auth_client, company):
        """Test cannot access another company's sandbox."""
        sandbox = Sandbox.objects.create(
            name="Private Sandbox",
            owner=company,
            expires_at=timezone.now() + timedelta(days=7),
        )

        url = f"/api/v2/sandbox/sandboxes/{sandbox.id}/"

        response = other_auth_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestSandboxActions:
    """Tests for sandbox custom actions."""

    def test_extend_sandbox(self, auth_client, company):
        """Test extending sandbox expiration."""
        sandbox = Sandbox.objects.create(
            name="Test Sandbox",
            owner=company,
            expires_at=timezone.now() + timedelta(days=7),
        )
        original_expiry = sandbox.expires_at

        url = f"/api/v2/sandbox/sandboxes/{sandbox.id}/extend/"
        data = {"days": 7}

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        sandbox.refresh_from_db()
        assert sandbox.expires_at > original_expiry

    def test_extend_sandbox_max_limit(self, auth_client, company):
        """Test cannot extend sandbox beyond 30 days."""
        sandbox = Sandbox.objects.create(
            name="Test Sandbox",
            owner=company,
            expires_at=timezone.now() + timedelta(days=7),
        )

        url = f"/api/v2/sandbox/sandboxes/{sandbox.id}/extend/"
        data = {"days": 31}

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "30 days" in response.data["detail"].lower()

    def test_archive_sandbox(self, auth_client, company):
        """Test archiving a sandbox."""
        sandbox = Sandbox.objects.create(
            name="Test Sandbox",
            owner=company,
            status=Sandbox.Status.ACTIVE,
            expires_at=timezone.now() + timedelta(days=7),
        )

        url = f"/api/v2/sandbox/sandboxes/{sandbox.id}/archive/"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        sandbox.refresh_from_db()
        assert sandbox.status == Sandbox.Status.ARCHIVED

    def test_archive_already_archived(self, auth_client, company):
        """Test cannot archive already archived sandbox."""
        sandbox = Sandbox.objects.create(
            name="Test Sandbox",
            owner=company,
            status=Sandbox.Status.ARCHIVED,
            expires_at=timezone.now() + timedelta(days=7),
        )

        url = f"/api/v2/sandbox/sandboxes/{sandbox.id}/archive/"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already archived" in response.data["detail"].lower()

    def test_get_sandbox_datasets(self, auth_client, company):
        """Test getting datasets in a sandbox."""
        sandbox = Sandbox.objects.create(
            name="Test Sandbox",
            owner=company,
            expires_at=timezone.now() + timedelta(days=7),
        )
        SyntheticDataset.objects.create(
            sandbox=sandbox,
            name="Test Dataset",
            record_count=100,
            feature_count=5,
        )

        url = f"/api/v2/sandbox/sandboxes/{sandbox.id}/datasets/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_get_sandbox_experiments(self, auth_client, company):
        """Test getting experiments in a sandbox."""
        sandbox = Sandbox.objects.create(
            name="Test Sandbox",
            owner=company,
            expires_at=timezone.now() + timedelta(days=7),
        )
        Experiment.objects.create(
            sandbox=sandbox,
            name="Test Experiment",
            experiment_type=Experiment.ExperimentType.TRAINING,
        )

        url = f"/api/v2/sandbox/sandboxes/{sandbox.id}/experiments/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1


@pytest.mark.django_db
class TestSyntheticDatasetEndpoints:
    """Tests for synthetic dataset operations."""

    def test_create_dataset(self, auth_client, company):
        """Test creating a synthetic dataset."""
        sandbox = Sandbox.objects.create(
            name="Test Sandbox",
            owner=company,
            expires_at=timezone.now() + timedelta(days=7),
        )

        url = "/api/v2/sandbox/datasets/"
        data = {
            "sandbox": str(sandbox.id),
            "name": "Test Dataset",
            "dataset_type": SyntheticDataset.DatasetType.GENERIC,
            "record_count": 1000,
            "feature_count": 5,
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Test Dataset"

    def test_list_datasets(self, auth_client, company):
        """Test listing datasets owned by user."""
        sandbox = Sandbox.objects.create(
            name="Test Sandbox",
            owner=company,
            expires_at=timezone.now() + timedelta(days=7),
        )
        SyntheticDataset.objects.create(
            sandbox=sandbox,
            name="Test Dataset",
            record_count=100,
            feature_count=5,
        )

        url = "/api/v2/sandbox/datasets/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_get_dataset(self, auth_client, company):
        """Test getting a single dataset."""
        sandbox = Sandbox.objects.create(
            name="Test Sandbox",
            owner=company,
            expires_at=timezone.now() + timedelta(days=7),
        )
        dataset = SyntheticDataset.objects.create(
            sandbox=sandbox,
            name="Test Dataset",
            record_count=100,
            feature_count=5,
        )

        url = f"/api/v2/sandbox/datasets/{dataset.id}/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Test Dataset"

    def test_generate_synthetic_data(self, auth_client, company):
        """Test generating synthetic data."""
        sandbox = Sandbox.objects.create(
            name="Test Sandbox",
            owner=company,
            status=Sandbox.Status.ACTIVE,
            expires_at=timezone.now() + timedelta(days=7),
        )

        url = "/api/v2/sandbox/datasets/generate/"
        data = {
            "sandbox_id": str(sandbox.id),
            "dataset_type": SyntheticDataset.DatasetType.TRANSACTIONS,
            "record_count": 100,
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["record_count"] == 100
        assert "data_preview" in response.data

    def test_generate_data_with_custom_features(self, auth_client, company):
        """Test generating data with custom features."""
        sandbox = Sandbox.objects.create(
            name="Test Sandbox",
            owner=company,
            status=Sandbox.Status.ACTIVE,
            expires_at=timezone.now() + timedelta(days=7),
        )

        url = "/api/v2/sandbox/datasets/generate/"
        data = {
            "sandbox_id": str(sandbox.id),
            "dataset_type": SyntheticDataset.DatasetType.GENERIC,
            "record_count": 100,  # Minimum is 100
            "features": [
                {"name": "custom_value", "type": "float", "min": 0, "max": 1000},
                {"name": "category", "type": "category", "values": ["A", "B", "C"]},
            ],
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["feature_count"] == 2

    def test_generate_data_sandbox_not_found(self, auth_client, company):
        """Test generating data for non-existent sandbox."""
        import uuid

        url = "/api/v2/sandbox/datasets/generate/"
        data = {
            "sandbox_id": str(uuid.uuid4()),
            "dataset_type": SyntheticDataset.DatasetType.GENERIC,
            "record_count": 100,
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_generate_data_inactive_sandbox(self, auth_client, company):
        """Test cannot generate data in inactive sandbox."""
        sandbox = Sandbox.objects.create(
            name="Test Sandbox",
            owner=company,
            status=Sandbox.Status.ARCHIVED,
            expires_at=timezone.now() + timedelta(days=7),
        )

        url = "/api/v2/sandbox/datasets/generate/"
        data = {
            "sandbox_id": str(sandbox.id),
            "dataset_type": SyntheticDataset.DatasetType.GENERIC,
            "record_count": 100,
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not active" in response.data["detail"].lower()

    def test_generate_data_missing_sandbox_id(self, auth_client):
        """Test generating data without sandbox_id."""
        url = "/api/v2/sandbox/datasets/generate/"
        data = {
            "dataset_type": SyntheticDataset.DatasetType.GENERIC,
            "record_count": 100,
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestExperimentEndpoints:
    """Tests for experiment operations."""

    def test_create_experiment(self, auth_client, company):
        """Test creating an experiment."""
        sandbox = Sandbox.objects.create(
            name="Test Sandbox",
            owner=company,
            expires_at=timezone.now() + timedelta(days=7),
        )

        url = "/api/v2/sandbox/experiments/"
        data = {
            "sandbox": str(sandbox.id),
            "name": "Test Experiment",
            "experiment_type": Experiment.ExperimentType.TRAINING,
            "config": {"epochs": 10, "learning_rate": 0.01},
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Test Experiment"
        # Verify via DB
        experiment = Experiment.objects.get(name="Test Experiment")
        assert experiment.status == Experiment.Status.PENDING

    def test_list_experiments(self, auth_client, company):
        """Test listing experiments."""
        sandbox = Sandbox.objects.create(
            name="Test Sandbox",
            owner=company,
            expires_at=timezone.now() + timedelta(days=7),
        )
        Experiment.objects.create(
            sandbox=sandbox,
            name="Test Experiment",
            experiment_type=Experiment.ExperimentType.TRAINING,
        )

        url = "/api/v2/sandbox/experiments/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_filter_experiments_by_sandbox(self, auth_client, company):
        """Test filtering experiments by sandbox."""
        sandbox1 = Sandbox.objects.create(
            name="Sandbox 1",
            owner=company,
            expires_at=timezone.now() + timedelta(days=7),
        )
        sandbox2 = Sandbox.objects.create(
            name="Sandbox 2",
            owner=company,
            expires_at=timezone.now() + timedelta(days=7),
        )
        Experiment.objects.create(
            sandbox=sandbox1,
            name="Exp 1",
            experiment_type=Experiment.ExperimentType.TRAINING,
        )
        Experiment.objects.create(
            sandbox=sandbox2,
            name="Exp 2",
            experiment_type=Experiment.ExperimentType.TRAINING,
        )

        url = f"/api/v2/sandbox/experiments/?sandbox_id={sandbox1.id}"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        for exp in response.data.get("results", response.data):
            assert str(exp["sandbox"]) == str(sandbox1.id)

    def test_filter_experiments_by_status(self, auth_client, company):
        """Test filtering experiments by status."""
        sandbox = Sandbox.objects.create(
            name="Test Sandbox",
            owner=company,
            expires_at=timezone.now() + timedelta(days=7),
        )
        Experiment.objects.create(
            sandbox=sandbox,
            name="Pending",
            experiment_type=Experiment.ExperimentType.TRAINING,
            status=Experiment.Status.PENDING,
        )
        Experiment.objects.create(
            sandbox=sandbox,
            name="Completed",
            experiment_type=Experiment.ExperimentType.TRAINING,
            status=Experiment.Status.COMPLETED,
        )

        url = "/api/v2/sandbox/experiments/?status=pending"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        results = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        assert all(exp["status"] == "pending" for exp in results)

    def test_get_experiment(self, auth_client, company):
        """Test getting a single experiment."""
        sandbox = Sandbox.objects.create(
            name="Test Sandbox",
            owner=company,
            expires_at=timezone.now() + timedelta(days=7),
        )
        experiment = Experiment.objects.create(
            sandbox=sandbox,
            name="Test Experiment",
            experiment_type=Experiment.ExperimentType.TRAINING,
        )

        url = f"/api/v2/sandbox/experiments/{experiment.id}/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Test Experiment"


@pytest.mark.django_db
class TestExperimentActions:
    """Tests for experiment custom actions."""

    def test_run_training_experiment(self, auth_client, company):
        """Test running a training experiment."""
        sandbox = Sandbox.objects.create(
            name="Test Sandbox",
            owner=company,
            expires_at=timezone.now() + timedelta(days=7),
        )
        experiment = Experiment.objects.create(
            sandbox=sandbox,
            name="Training Experiment",
            experiment_type=Experiment.ExperimentType.TRAINING,
            config={"epochs": 5},
        )

        url = f"/api/v2/sandbox/experiments/{experiment.id}/run/"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == Experiment.Status.COMPLETED
        assert "accuracy" in response.data["results"]

    def test_run_evaluation_experiment(self, auth_client, company):
        """Test running an evaluation experiment."""
        sandbox = Sandbox.objects.create(
            name="Test Sandbox",
            owner=company,
            expires_at=timezone.now() + timedelta(days=7),
        )
        experiment = Experiment.objects.create(
            sandbox=sandbox,
            name="Evaluation Experiment",
            experiment_type=Experiment.ExperimentType.EVALUATION,
        )

        url = f"/api/v2/sandbox/experiments/{experiment.id}/run/"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert "precision" in response.data["results"]
        assert "recall" in response.data["results"]

    def test_run_clustering_experiment(self, auth_client, company):
        """Test running a clustering experiment."""
        sandbox = Sandbox.objects.create(
            name="Test Sandbox",
            owner=company,
            expires_at=timezone.now() + timedelta(days=7),
        )
        experiment = Experiment.objects.create(
            sandbox=sandbox,
            name="Clustering Experiment",
            experiment_type=Experiment.ExperimentType.CLUSTERING,
            config={"n_clusters": 5},
        )

        url = f"/api/v2/sandbox/experiments/{experiment.id}/run/"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert "silhouette_score" in response.data["results"]

    def test_run_benchmark_experiment(self, auth_client, company):
        """Test running an encryption benchmark experiment."""
        sandbox = Sandbox.objects.create(
            name="Test Sandbox",
            owner=company,
            expires_at=timezone.now() + timedelta(days=7),
        )
        experiment = Experiment.objects.create(
            sandbox=sandbox,
            name="Benchmark Experiment",
            experiment_type=Experiment.ExperimentType.ENCRYPTION_BENCHMARK,
        )

        url = f"/api/v2/sandbox/experiments/{experiment.id}/run/"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert "encryption_time_ms" in response.data["results"]

    def test_cannot_run_completed_experiment(self, auth_client, company):
        """Test cannot run already completed experiment."""
        sandbox = Sandbox.objects.create(
            name="Test Sandbox",
            owner=company,
            expires_at=timezone.now() + timedelta(days=7),
        )
        experiment = Experiment.objects.create(
            sandbox=sandbox,
            name="Completed Experiment",
            experiment_type=Experiment.ExperimentType.TRAINING,
            status=Experiment.Status.COMPLETED,
        )

        url = f"/api/v2/sandbox/experiments/{experiment.id}/run/"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already" in response.data["detail"].lower()

    def test_cancel_running_experiment(self, auth_client, company):
        """Test cancelling a running experiment."""
        sandbox = Sandbox.objects.create(
            name="Test Sandbox",
            owner=company,
            expires_at=timezone.now() + timedelta(days=7),
        )
        experiment = Experiment.objects.create(
            sandbox=sandbox,
            name="Running Experiment",
            experiment_type=Experiment.ExperimentType.TRAINING,
            status=Experiment.Status.RUNNING,
        )

        url = f"/api/v2/sandbox/experiments/{experiment.id}/cancel/"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        experiment.refresh_from_db()
        assert experiment.status == Experiment.Status.FAILED
        assert "cancelled" in experiment.error_message.lower()

    def test_cannot_cancel_non_running_experiment(self, auth_client, company):
        """Test cannot cancel non-running experiment."""
        sandbox = Sandbox.objects.create(
            name="Test Sandbox",
            owner=company,
            expires_at=timezone.now() + timedelta(days=7),
        )
        experiment = Experiment.objects.create(
            sandbox=sandbox,
            name="Pending Experiment",
            experiment_type=Experiment.ExperimentType.TRAINING,
            status=Experiment.Status.PENDING,
        )

        url = f"/api/v2/sandbox/experiments/{experiment.id}/cancel/"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not running" in response.data["detail"].lower()


@pytest.mark.django_db
class TestSandboxModels:
    """Tests for sandbox model methods."""

    def test_sandbox_str(self, company):
        """Test sandbox string representation."""
        sandbox = Sandbox.objects.create(
            name="Test Sandbox",
            owner=company,
            expires_at=timezone.now() + timedelta(days=7),
        )

        assert "Test Sandbox" in str(sandbox)
        assert company.name in str(sandbox)

    def test_sandbox_auto_expiry(self, company):
        """Test sandbox auto-sets expiry if not provided."""
        sandbox = Sandbox(name="Test", owner=company)
        sandbox.save()

        assert sandbox.expires_at is not None

    def test_sandbox_is_expired(self, company):
        """Test sandbox expiration check."""
        sandbox = Sandbox.objects.create(
            name="Expired",
            owner=company,
            expires_at=timezone.now() - timedelta(days=1),
        )

        assert sandbox.is_expired is True

    def test_sandbox_dataset_count(self, company):
        """Test sandbox dataset count property."""
        sandbox = Sandbox.objects.create(
            name="Test",
            owner=company,
            expires_at=timezone.now() + timedelta(days=7),
        )
        SyntheticDataset.objects.create(
            sandbox=sandbox,
            name="Dataset 1",
            record_count=100,
            feature_count=5,
        )
        SyntheticDataset.objects.create(
            sandbox=sandbox,
            name="Dataset 2",
            record_count=200,
            feature_count=5,
        )

        assert sandbox.dataset_count == 2

    def test_sandbox_experiment_count(self, company):
        """Test sandbox experiment count property."""
        sandbox = Sandbox.objects.create(
            name="Test",
            owner=company,
            expires_at=timezone.now() + timedelta(days=7),
        )
        Experiment.objects.create(
            sandbox=sandbox,
            name="Exp 1",
            experiment_type=Experiment.ExperimentType.TRAINING,
        )

        assert sandbox.experiment_count == 1

    def test_dataset_str(self, company):
        """Test dataset string representation."""
        sandbox = Sandbox.objects.create(
            name="Test",
            owner=company,
            expires_at=timezone.now() + timedelta(days=7),
        )
        dataset = SyntheticDataset.objects.create(
            sandbox=sandbox,
            name="Test Dataset",
            record_count=1000,
            feature_count=5,
        )

        assert "Test Dataset" in str(dataset)
        assert "1000" in str(dataset)

    def test_experiment_str(self, company):
        """Test experiment string representation."""
        sandbox = Sandbox.objects.create(
            name="Test",
            owner=company,
            expires_at=timezone.now() + timedelta(days=7),
        )
        experiment = Experiment.objects.create(
            sandbox=sandbox,
            name="Test Experiment",
            experiment_type=Experiment.ExperimentType.TRAINING,
        )

        assert "Test Experiment" in str(experiment)

    def test_experiment_start(self, company):
        """Test experiment start method."""
        sandbox = Sandbox.objects.create(
            name="Test",
            owner=company,
            expires_at=timezone.now() + timedelta(days=7),
        )
        experiment = Experiment.objects.create(
            sandbox=sandbox,
            name="Test",
            experiment_type=Experiment.ExperimentType.TRAINING,
        )

        experiment.start()

        assert experiment.status == Experiment.Status.RUNNING
        assert experiment.started_at is not None

    def test_experiment_complete(self, company):
        """Test experiment complete method."""
        sandbox = Sandbox.objects.create(
            name="Test",
            owner=company,
            expires_at=timezone.now() + timedelta(days=7),
        )
        experiment = Experiment.objects.create(
            sandbox=sandbox,
            name="Test",
            experiment_type=Experiment.ExperimentType.TRAINING,
        )

        experiment.complete({"accuracy": 0.95})

        assert experiment.status == Experiment.Status.COMPLETED
        assert experiment.completed_at is not None
        assert experiment.results["accuracy"] == 0.95

    def test_experiment_fail(self, company):
        """Test experiment fail method."""
        sandbox = Sandbox.objects.create(
            name="Test",
            owner=company,
            expires_at=timezone.now() + timedelta(days=7),
        )
        experiment = Experiment.objects.create(
            sandbox=sandbox,
            name="Test",
            experiment_type=Experiment.ExperimentType.TRAINING,
        )

        experiment.fail("Test error")

        assert experiment.status == Experiment.Status.FAILED
        assert experiment.error_message == "Test error"

    def test_template_str(self):
        """Test template string representation."""
        template = SandboxTemplate.objects.create(
            id="test-template",
            name="Test Template",
        )

        assert "Test Template" in str(template)

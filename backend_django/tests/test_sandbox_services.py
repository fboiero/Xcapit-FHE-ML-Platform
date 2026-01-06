"""
Tests for sandbox services: DataGenerationService, ExperimentService, SandboxService.

Covers data generation, experiment lifecycle, and sandbox management.
"""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.core.models import Company
from apps.sandbox.models import Experiment, Sandbox, SyntheticDataset
from apps.sandbox.services import DataGenerationService, ExperimentService, SandboxService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sandbox_company(db):
    return Company.objects.create(name="Sandbox Corp", email="sb@corp.com", industry="tech")


@pytest.fixture
def sandbox(db, sandbox_company):
    return Sandbox.objects.create(
        owner=sandbox_company,
        name="Test Sandbox",
        industry="fintech",
        status=Sandbox.Status.ACTIVE,
        expires_at=timezone.now() + timedelta(days=14),
    )


@pytest.fixture
def expired_sandbox(db, sandbox_company):
    return Sandbox.objects.create(
        owner=sandbox_company,
        name="Expired Sandbox",
        industry="fintech",
        status=Sandbox.Status.ACTIVE,
        expires_at=timezone.now() - timedelta(days=1),
    )


@pytest.fixture
def archived_sandbox(db, sandbox_company):
    return Sandbox.objects.create(
        owner=sandbox_company,
        name="Archived Sandbox",
        industry="fintech",
        status=Sandbox.Status.ARCHIVED,
        expires_at=timezone.now() + timedelta(days=7),
    )


@pytest.fixture
def dataset(db, sandbox):
    return SyntheticDataset.objects.create(
        sandbox=sandbox,
        name="Test Dataset",
        dataset_type=SyntheticDataset.DatasetType.TRANSACTIONS,
        record_count=1000,
        feature_count=4,
        features=[{"name": "amount", "type": "float", "min": 0, "max": 10000}],
        statistics={"record_count": 1000},
    )


@pytest.fixture
def pending_experiment(db, sandbox, dataset):
    return Experiment.objects.create(
        sandbox=sandbox,
        name="Training Exp",
        experiment_type=Experiment.ExperimentType.TRAINING,
        model_type="logistic_regression",
        dataset=dataset,
        config={"epochs": 10, "learning_rate": 0.01},
        status=Experiment.Status.PENDING,
    )


@pytest.fixture
def running_experiment(db, sandbox, dataset):
    return Experiment.objects.create(
        sandbox=sandbox,
        name="Running Exp",
        experiment_type=Experiment.ExperimentType.EVALUATION,
        model_type="logistic_regression",
        dataset=dataset,
        config={},
        status=Experiment.Status.RUNNING,
        started_at=timezone.now(),
    )


@pytest.fixture
def completed_experiment(db, sandbox, dataset):
    return Experiment.objects.create(
        sandbox=sandbox,
        name="Completed Exp",
        experiment_type=Experiment.ExperimentType.TRAINING,
        model_type="logistic_regression",
        dataset=dataset,
        config={},
        status=Experiment.Status.COMPLETED,
        results={"accuracy": 0.85},
    )


# ===========================================================================
# DataGenerationService Tests
# ===========================================================================


@pytest.mark.django_db
class TestDataGenerationServiceDefaults:
    def test_get_default_features_transactions(self):
        service = DataGenerationService()
        features = service.get_default_features("transactions")

        assert len(features) == 4
        names = [f["name"] for f in features]
        assert "amount" in names
        assert "is_fraud" in names

    def test_get_default_features_patients(self):
        service = DataGenerationService()
        features = service.get_default_features("patients")

        assert len(features) == 4
        names = [f["name"] for f in features]
        assert "age" in names

    def test_get_default_features_credit_scores(self):
        service = DataGenerationService()
        features = service.get_default_features("credit_scores")

        names = [f["name"] for f in features]
        assert "income" in names

    def test_get_default_features_unknown_type_falls_back(self):
        service = DataGenerationService()
        features = service.get_default_features("unknown_type")

        assert features == service.DEFAULT_FEATURES["default"]


@pytest.mark.django_db
class TestDataGenerationServicePreview:
    def test_generate_preview_row_count(self):
        service = DataGenerationService()
        features = service.get_default_features("transactions")
        rows = service.generate_preview(features, count=5)

        assert len(rows) == 5

    def test_generate_preview_seed_reproducible(self):
        service = DataGenerationService()
        features = service.get_default_features("transactions")
        rows1 = service.generate_preview(features, count=3, seed=42)
        rows2 = service.generate_preview(features, count=3, seed=42)

        assert rows1 == rows2

    def test_generate_row_float_type(self):
        service = DataGenerationService()
        features = [{"name": "val", "type": "float", "min": 0, "max": 100}]
        row = service._generate_row(features)

        assert isinstance(row["val"], float)
        assert 0 <= row["val"] <= 100

    def test_generate_row_int_type(self):
        service = DataGenerationService()
        features = [{"name": "val", "type": "int", "min": 0, "max": 23}]
        row = service._generate_row(features)

        assert isinstance(row["val"], int)
        assert 0 <= row["val"] <= 23

    def test_generate_row_category_type(self):
        service = DataGenerationService()
        features = [{"name": "cat", "type": "category", "values": ["a", "b", "c"]}]
        row = service._generate_row(features)

        assert row["cat"] in ["a", "b", "c"]

    def test_generate_row_bool_type(self):
        service = DataGenerationService()
        features = [{"name": "flag", "type": "bool", "true_ratio": 0.5}]
        row = service._generate_row(features)

        assert isinstance(row["flag"], bool)


@pytest.mark.django_db
class TestDataGenerationServiceStatistics:
    def test_calculate_statistics_structure(self):
        service = DataGenerationService()
        features = service.get_default_features("transactions")
        stats = service.calculate_statistics(features, 1000)

        assert stats["record_count"] == 1000
        assert stats["feature_count"] == 4
        assert "features" in stats

    def test_calculate_statistics_float_feature(self):
        service = DataGenerationService()
        features = [{"name": "val", "type": "float", "min": 0, "max": 100}]
        stats = service.calculate_statistics(features, 500)

        feature_stats = stats["features"]["val"]
        assert feature_stats["mean"] == 50
        assert feature_stats["std_estimate"] == 25

    def test_calculate_statistics_category_feature(self):
        service = DataGenerationService()
        features = [{"name": "cat", "type": "category", "values": ["a", "b", "c"]}]
        stats = service.calculate_statistics(features, 500)

        feature_stats = stats["features"]["cat"]
        assert feature_stats["unique_values"] == 3

    def test_calculate_statistics_bool_feature(self):
        service = DataGenerationService()
        features = [{"name": "flag", "type": "bool", "true_ratio": 0.3}]
        stats = service.calculate_statistics(features, 500)

        feature_stats = stats["features"]["flag"]
        assert feature_stats["true_ratio"] == 0.3
        assert feature_stats["false_ratio"] == pytest.approx(0.7)


@pytest.mark.django_db
class TestDataGenerationServiceDataset:
    def test_generate_dataset_happy_path(self):
        service = DataGenerationService()
        result = service.generate_dataset("transactions", 100)

        assert result.success
        data = result.data
        assert data["dataset_type"] == "transactions"
        assert data["record_count"] == 100
        assert len(data["preview"]) == 10
        assert "statistics" in data

    def test_generate_dataset_validation_zero_records(self):
        service = DataGenerationService()
        result = service.generate_dataset("transactions", 0)

        assert not result.success
        assert result.error_code == "validation_error"

    def test_generate_dataset_validation_too_many_records(self):
        service = DataGenerationService()
        result = service.generate_dataset("transactions", 2_000_000)

        assert not result.success
        assert result.error_code == "validation_error"


# ===========================================================================
# ExperimentService Tests
# ===========================================================================


@pytest.mark.django_db
class TestExperimentServiceRun:
    def test_run_experiment_training(self, pending_experiment):
        service = ExperimentService()
        result = service.run_experiment(pending_experiment)

        assert result.success
        assert "accuracy" in result.data
        assert "loss" in result.data
        pending_experiment.refresh_from_db()
        assert pending_experiment.status == Experiment.Status.COMPLETED

    def test_run_experiment_evaluation(self, sandbox, dataset):
        exp = Experiment.objects.create(
            sandbox=sandbox,
            name="Eval",
            experiment_type=Experiment.ExperimentType.EVALUATION,
            model_type="logistic_regression",
            dataset=dataset,
            config={},
        )

        service = ExperimentService()
        result = service.run_experiment(exp)

        assert result.success
        assert "precision" in result.data
        assert "recall" in result.data
        assert "f1_score" in result.data

    def test_run_experiment_clustering(self, sandbox, dataset):
        exp = Experiment.objects.create(
            sandbox=sandbox,
            name="Cluster",
            experiment_type=Experiment.ExperimentType.CLUSTERING,
            model_type="kmeans",
            dataset=dataset,
            config={"n_clusters": 5, "n_samples": 500},
        )

        service = ExperimentService()
        result = service.run_experiment(exp)

        assert result.success
        assert result.data["n_clusters"] == 5

    def test_run_experiment_encryption_benchmark(self, sandbox, dataset):
        exp = Experiment.objects.create(
            sandbox=sandbox,
            name="Bench",
            experiment_type=Experiment.ExperimentType.ENCRYPTION_BENCHMARK,
            model_type="ckks",
            dataset=dataset,
            config={"security_level": 256},
        )

        service = ExperimentService()
        result = service.run_experiment(exp)

        assert result.success
        assert result.data["security_level"] == 256
        assert "encryption_time_ms" in result.data

    def test_run_experiment_already_completed_fails(self, completed_experiment):
        service = ExperimentService()
        result = service.run_experiment(completed_experiment)

        assert not result.success
        assert result.error_code == "invalid_status"

    def test_run_experiment_expired_sandbox_fails(self, expired_sandbox, dataset):
        exp = Experiment.objects.create(
            sandbox=expired_sandbox,
            name="Exp",
            experiment_type=Experiment.ExperimentType.TRAINING,
            model_type="lr",
            dataset=dataset,
            config={},
        )

        service = ExperimentService()
        result = service.run_experiment(exp)

        assert not result.success
        assert result.error_code == "sandbox_expired"

    def test_run_experiment_transitions_status(self, pending_experiment):
        service = ExperimentService()
        service.run_experiment(pending_experiment)

        pending_experiment.refresh_from_db()
        assert pending_experiment.status == Experiment.Status.COMPLETED
        assert pending_experiment.started_at is not None
        assert pending_experiment.completed_at is not None

    def test_run_failed_experiment_can_retry(self, sandbox, dataset):
        exp = Experiment.objects.create(
            sandbox=sandbox,
            name="Failed Exp",
            experiment_type=Experiment.ExperimentType.TRAINING,
            model_type="lr",
            dataset=dataset,
            config={},
            status=Experiment.Status.FAILED,
            error_message="Previous error",
        )

        service = ExperimentService()
        result = service.run_experiment(exp)

        assert result.success


@pytest.mark.django_db
class TestExperimentServiceCancel:
    def test_cancel_running_experiment(self, running_experiment):
        service = ExperimentService()
        result = service.cancel_experiment(running_experiment)

        assert result.success
        running_experiment.refresh_from_db()
        assert running_experiment.status == Experiment.Status.FAILED
        assert "Cancelled" in running_experiment.error_message

    def test_cancel_non_running_fails(self, pending_experiment):
        service = ExperimentService()
        result = service.cancel_experiment(pending_experiment)

        assert not result.success
        assert result.error_code == "invalid_status"


@pytest.mark.django_db
class TestExperimentServiceStatus:
    def test_get_experiment_status_structure(self, pending_experiment):
        service = ExperimentService()
        status = service.get_experiment_status(pending_experiment)

        assert "id" in status
        assert "name" in status
        assert "status" in status
        assert "experiment_type" in status
        assert status["started_at"] is None  # PENDING experiment

    def test_get_experiment_status_completed(self, completed_experiment):
        service = ExperimentService()
        status = service.get_experiment_status(completed_experiment)

        assert status["status"] == Experiment.Status.COMPLETED
        assert status["results"] == {"accuracy": 0.85}


# ===========================================================================
# SandboxService Tests
# ===========================================================================


@pytest.mark.django_db
class TestSandboxServiceCreate:
    def test_create_sandbox_happy_path(self, sandbox_company):
        service = SandboxService()
        result = service.create_sandbox(sandbox_company, "New Sandbox", "fintech")

        assert result.success
        sb = result.data
        assert sb.name == "New Sandbox"
        assert sb.industry == "fintech"
        assert sb.status == Sandbox.Status.ACTIVE
        assert sb.expires_at is not None

    def test_create_sandbox_with_duration(self, sandbox_company):
        service = SandboxService()
        result = service.create_sandbox(sandbox_company, "Short", "tech", duration_days=3)

        assert result.success
        expected_expiry = timezone.now() + timedelta(days=3)
        assert abs((result.data.expires_at - expected_expiry).total_seconds()) < 5

    def test_create_sandbox_limit_exceeded(self, sandbox_company):
        for i in range(SandboxService.MAX_ACTIVE_SANDBOXES_PER_COMPANY):
            Sandbox.objects.create(
                owner=sandbox_company,
                name=f"Sandbox-{i}",
                industry="tech",
                status=Sandbox.Status.ACTIVE,
                expires_at=timezone.now() + timedelta(days=7),
            )

        service = SandboxService()
        result = service.create_sandbox(sandbox_company, "Overflow", "tech")

        assert not result.success
        assert result.error_code == "limit_exceeded"


@pytest.mark.django_db
class TestSandboxServiceExtend:
    def test_extend_sandbox_happy_path(self, sandbox):
        old_expiry = sandbox.expires_at

        service = SandboxService()
        result = service.extend_sandbox(sandbox, 7)

        assert result.success
        assert result.data.expires_at > old_expiry

    def test_extend_sandbox_exceeds_max_fails(self, sandbox):
        service = SandboxService()
        result = service.extend_sandbox(sandbox, SandboxService.MAX_EXTENSION_DAYS + 1)

        assert not result.success
        assert result.error_code == "limit_exceeded"

    def test_extend_archived_sandbox_fails(self, archived_sandbox):
        service = SandboxService()
        result = service.extend_sandbox(archived_sandbox, 7)

        assert not result.success
        assert result.error_code == "invalid_status"

    def test_extend_sandbox_negative_days_fails(self, sandbox):
        service = SandboxService()
        result = service.extend_sandbox(sandbox, -1)

        assert not result.success
        assert result.error_code == "validation_error"


@pytest.mark.django_db
class TestSandboxServiceArchive:
    def test_archive_sandbox_happy_path(self, sandbox):
        service = SandboxService()
        result = service.archive_sandbox(sandbox)

        assert result.success
        assert result.data.status == Sandbox.Status.ARCHIVED

    def test_archive_already_archived_fails(self, archived_sandbox):
        service = SandboxService()
        result = service.archive_sandbox(archived_sandbox)

        assert not result.success
        assert result.error_code == "invalid_status"


@pytest.mark.django_db
class TestSandboxServiceSummary:
    def test_get_sandbox_summary_structure(self, sandbox, dataset, pending_experiment):
        service = SandboxService()
        summary = service.get_sandbox_summary(sandbox)

        assert summary["name"] == "Test Sandbox"
        assert "datasets" in summary
        assert "experiments" in summary
        assert summary["datasets"]["total"] >= 1
        assert summary["experiments"]["total"] >= 1

    def test_get_sandbox_summary_experiment_counts(
        self, sandbox, dataset, pending_experiment, completed_experiment
    ):
        service = SandboxService()
        summary = service.get_sandbox_summary(sandbox)

        by_status = summary["experiments"]["by_status"]
        assert "pending" in by_status
        assert "completed" in by_status


@pytest.mark.django_db
class TestSandboxServiceCleanup:
    def test_cleanup_expired_sandboxes(self, sandbox_company):
        Sandbox.objects.create(
            owner=sandbox_company,
            name="Old",
            industry="tech",
            status=Sandbox.Status.ACTIVE,
            expires_at=timezone.now() - timedelta(days=1),
        )

        service = SandboxService()
        result = service.cleanup_expired_sandboxes()

        assert result.success
        assert result.data >= 1

    def test_cleanup_does_not_touch_non_expired(self, sandbox):
        service = SandboxService()
        result = service.cleanup_expired_sandboxes()

        sandbox.refresh_from_db()
        assert sandbox.status == Sandbox.Status.ACTIVE

    def test_cleanup_returns_correct_count(self, sandbox_company):
        for i in range(3):
            Sandbox.objects.create(
                owner=sandbox_company,
                name=f"Expired-{i}",
                industry="tech",
                status=Sandbox.Status.ACTIVE,
                expires_at=timezone.now() - timedelta(days=1),
            )

        service = SandboxService()
        result = service.cleanup_expired_sandboxes()

        assert result.data == 3

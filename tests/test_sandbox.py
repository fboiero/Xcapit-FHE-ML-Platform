"""Tests for TIER 3 Sandbox Mode feature.

Tests cover:
- Sandbox environments (create, get, list, delete)
- Sandbox templates
- Synthetic dataset generation
- Experiments (create, run, list, delete)
- Statistics
"""

import sys
from pathlib import Path
import pytest
import tempfile
from datetime import datetime
import importlib.util

project_root = Path(__file__).parent.parent
sdk_api_path = project_root / "sdk" / "api"


def load_module_from_path(module_name, file_path):
    """Load a module from file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


# Load consortium module
consortium_module = load_module_from_path(
    "sdk.api.consortium",
    sdk_api_path / "consortium.py"
)
ConsortiumManager = consortium_module.ConsortiumManager
ConsortiumStatus = consortium_module.ConsortiumStatus
MemberRole = consortium_module.MemberRole
MemberStatus = consortium_module.MemberStatus


class TestSandboxTemplates:
    """Tests for sandbox templates functionality."""

    @pytest.fixture
    def manager(self):
        """Create a manager with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_sandbox.db"
            mgr = ConsortiumManager(db_path)
            yield mgr

    def test_list_sandbox_templates(self, manager):
        """Test retrieving sandbox templates."""
        templates = manager.list_sandbox_templates()

        assert templates is not None
        assert len(templates) >= 5  # We seed 5 templates

        # Verify template structure
        for template in templates:
            assert "id" in template
            assert "name" in template
            assert "description" in template
            assert "template_type" in template
            assert "datasets" in template
            assert "experiments" in template

    def test_templates_include_fraud(self, manager):
        """Test that fraud detection template exists."""
        templates = manager.list_sandbox_templates()
        fraud_template = next((t for t in templates if t["id"] == "tpl_fraud_basic"), None)

        assert fraud_template is not None
        assert fraud_template["name"] == "Fraud Detection Starter"
        assert fraud_template["industry"] == "fraud"

    def test_templates_include_credit(self, manager):
        """Test that credit scoring template exists."""
        templates = manager.list_sandbox_templates()
        credit_template = next((t for t in templates if t["id"] == "tpl_credit_basic"), None)

        assert credit_template is not None
        assert credit_template["name"] == "Credit Scoring Starter"
        assert credit_template["industry"] == "credit"

    def test_templates_include_health(self, manager):
        """Test that healthcare template exists."""
        templates = manager.list_sandbox_templates()
        health_template = next((t for t in templates if t["id"] == "tpl_health_basic"), None)

        assert health_template is not None
        assert health_template["name"] == "Healthcare Analytics Starter"
        assert health_template["industry"] == "health"

    def test_filter_templates_by_industry(self, manager):
        """Test filtering templates by industry."""
        # Get all templates first to see what industries exist
        all_templates = manager.list_sandbox_templates()

        # Find a specific industry (not 'general')
        industries = [t["industry"] for t in all_templates if t.get("industry") and t["industry"] != "general"]
        if industries:
            target_industry = industries[0]
            filtered_templates = manager.list_sandbox_templates(industry=target_industry)

            # Verify filtering works - should include target industry and 'general'
            assert len(filtered_templates) >= 1
            for template in filtered_templates:
                # Templates should be either the target industry or 'general' (always included)
                assert template["industry"] in [target_industry, "general"]


class TestSandboxEnvironments:
    """Tests for sandbox environment functionality."""

    @pytest.fixture
    def manager(self):
        """Create a manager with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_sandbox.db"
            mgr = ConsortiumManager(db_path)
            yield mgr

    @pytest.fixture
    def company(self, manager):
        """Create a test company."""
        company, _ = manager.create_company(
            name="Test Corp",
            email="test@testcorp.com"
        )
        return company

    def test_create_sandbox(self, manager, company):
        """Test creating a sandbox environment."""
        sandbox = manager.create_sandbox(
            name="Test Sandbox",
            owner_id=company.id,
            description="A test sandbox environment"
        )

        assert sandbox is not None
        assert sandbox["id"].startswith("sandbox_")
        assert sandbox["name"] == "Test Sandbox"
        assert sandbox["owner_id"] == company.id
        assert sandbox["status"] == "active"

    def test_create_sandbox_with_template(self, manager, company):
        """Test creating a sandbox from a template."""
        sandbox = manager.create_sandbox(
            name="Fraud Test Sandbox",
            owner_id=company.id,
            template_id="tpl_fraud_basic",
            industry="fraud"
        )

        assert sandbox is not None
        assert "template_type" in sandbox
        assert sandbox["industry"] == "fraud"

    def test_get_sandbox(self, manager, company):
        """Test retrieving a sandbox by ID."""
        created = manager.create_sandbox(
            name="Get Test Sandbox",
            owner_id=company.id
        )

        sandbox = manager.get_sandbox(created["id"])

        assert sandbox is not None
        assert sandbox["id"] == created["id"]
        assert sandbox["name"] == "Get Test Sandbox"

    def test_list_sandboxes(self, manager, company):
        """Test listing sandboxes for a company."""
        manager.create_sandbox(name="Sandbox 1", owner_id=company.id)
        manager.create_sandbox(name="Sandbox 2", owner_id=company.id)
        manager.create_sandbox(name="Sandbox 3", owner_id=company.id)

        sandboxes = manager.list_sandboxes(owner_id=company.id)

        assert len(sandboxes) >= 3

    def test_list_sandboxes_by_status(self, manager, company):
        """Test filtering sandboxes by status."""
        manager.create_sandbox(name="Active Sandbox", owner_id=company.id)

        active_sandboxes = manager.list_sandboxes(
            owner_id=company.id,
            status="active"
        )

        assert len(active_sandboxes) >= 1
        for sandbox in active_sandboxes:
            assert sandbox["status"] == "active"

    def test_delete_sandbox(self, manager, company):
        """Test deleting a sandbox."""
        sandbox = manager.create_sandbox(
            name="To Delete",
            owner_id=company.id
        )

        result = manager.delete_sandbox(sandbox["id"], company.id)
        assert result is True

        deleted = manager.get_sandbox(sandbox["id"])
        assert deleted is None or deleted.get("status") == "deleted"

    def test_sandbox_expires_at(self, manager, company):
        """Test that sandbox has expiration date."""
        sandbox = manager.create_sandbox(
            name="Expiring Sandbox",
            owner_id=company.id,
            expires_days=7
        )

        assert sandbox["expires_at"] is not None


class TestSyntheticDatasets:
    """Tests for synthetic dataset generation."""

    @pytest.fixture
    def manager(self):
        """Create a manager with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_sandbox.db"
            mgr = ConsortiumManager(db_path)
            yield mgr

    @pytest.fixture
    def sandbox(self, manager):
        """Create a test sandbox."""
        company, _ = manager.create_company(
            name="Dataset Test Corp",
            email="dataset@testcorp.com"
        )
        sandbox = manager.create_sandbox(
            name="Dataset Test Sandbox",
            owner_id=company.id
        )
        sandbox["company"] = company
        return sandbox

    def test_generate_transactions_dataset(self, manager, sandbox):
        """Test generating a transactions dataset."""
        dataset = manager.generate_synthetic_dataset(
            sandbox_id=sandbox["id"],
            name="Test Transactions",
            dataset_type="transactions",
            record_count=500,
            created_by=sandbox["company"].id
        )

        assert dataset is not None
        assert dataset["id"].startswith("ds_")
        assert dataset["name"] == "Test Transactions"
        assert dataset["dataset_type"] == "transactions"
        assert dataset["record_count"] == 500
        assert "features" in dataset
        assert "data_preview" in dataset

    def test_generate_applications_dataset(self, manager, sandbox):
        """Test generating a credit applications dataset."""
        dataset = manager.generate_synthetic_dataset(
            sandbox_id=sandbox["id"],
            name="Test Applications",
            dataset_type="applications",
            record_count=300,
            created_by=sandbox["company"].id
        )

        assert dataset is not None
        assert dataset["dataset_type"] == "applications"
        assert len(dataset["features"]) > 0

    def test_generate_customers_dataset(self, manager, sandbox):
        """Test generating a customers dataset."""
        dataset = manager.generate_synthetic_dataset(
            sandbox_id=sandbox["id"],
            name="Test Customers",
            dataset_type="customers",
            record_count=200,
            created_by=sandbox["company"].id
        )

        assert dataset is not None
        assert dataset["dataset_type"] == "customers"

    def test_generate_patients_dataset(self, manager, sandbox):
        """Test generating a patients dataset."""
        dataset = manager.generate_synthetic_dataset(
            sandbox_id=sandbox["id"],
            name="Test Patients",
            dataset_type="patients",
            record_count=100,
            created_by=sandbox["company"].id
        )

        assert dataset is not None
        assert dataset["dataset_type"] == "patients"

    def test_generate_generic_dataset(self, manager, sandbox):
        """Test generating a generic dataset."""
        dataset = manager.generate_synthetic_dataset(
            sandbox_id=sandbox["id"],
            name="Test Generic",
            dataset_type="generic",
            record_count=150,
            created_by=sandbox["company"].id
        )

        assert dataset is not None
        assert dataset["dataset_type"] == "generic"

    def test_dataset_has_statistics(self, manager, sandbox):
        """Test that dataset includes statistics."""
        dataset = manager.generate_synthetic_dataset(
            sandbox_id=sandbox["id"],
            name="Stats Test",
            dataset_type="transactions",
            record_count=500,
            created_by=sandbox["company"].id
        )

        assert "statistics" in dataset
        stats = dataset["statistics"]
        # Verify we have some statistics (keys depend on dataset type)
        assert len(stats) > 0

    def test_dataset_has_preview(self, manager, sandbox):
        """Test that dataset includes data preview."""
        dataset = manager.generate_synthetic_dataset(
            sandbox_id=sandbox["id"],
            name="Preview Test",
            dataset_type="transactions",
            record_count=500,
            created_by=sandbox["company"].id
        )

        assert "data_preview" in dataset
        assert len(dataset["data_preview"]) > 0
        assert len(dataset["data_preview"]) <= 10  # Preview limited to 10 rows

    def test_list_datasets(self, manager, sandbox):
        """Test listing datasets in a sandbox."""
        manager.generate_synthetic_dataset(
            sandbox_id=sandbox["id"],
            name="Dataset 1",
            dataset_type="transactions",
            record_count=100,
            created_by=sandbox["company"].id
        )
        manager.generate_synthetic_dataset(
            sandbox_id=sandbox["id"],
            name="Dataset 2",
            dataset_type="customers",
            record_count=100,
            created_by=sandbox["company"].id
        )

        datasets = manager.list_datasets(sandbox["id"])

        assert len(datasets) >= 2

    def test_get_dataset(self, manager, sandbox):
        """Test retrieving a specific dataset."""
        created = manager.generate_synthetic_dataset(
            sandbox_id=sandbox["id"],
            name="Get Test Dataset",
            dataset_type="transactions",
            record_count=100,
            created_by=sandbox["company"].id
        )

        dataset = manager.get_dataset(created["id"])

        assert dataset is not None
        assert dataset["id"] == created["id"]
        assert dataset["name"] == "Get Test Dataset"

    def test_delete_dataset(self, manager, sandbox):
        """Test deleting a dataset."""
        dataset = manager.generate_synthetic_dataset(
            sandbox_id=sandbox["id"],
            name="To Delete",
            dataset_type="generic",
            record_count=100,
            created_by=sandbox["company"].id
        )

        result = manager.delete_dataset(dataset["id"], sandbox["company"].id)
        assert result is True


class TestSandboxExperiments:
    """Tests for sandbox experiments functionality."""

    @pytest.fixture
    def manager(self):
        """Create a manager with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_sandbox.db"
            mgr = ConsortiumManager(db_path)
            yield mgr

    @pytest.fixture
    def sandbox_with_dataset(self, manager):
        """Create a sandbox with a dataset."""
        company, _ = manager.create_company(
            name="Experiment Test Corp",
            email="exp@testcorp.com"
        )
        sandbox = manager.create_sandbox(
            name="Experiment Test Sandbox",
            owner_id=company.id
        )
        dataset = manager.generate_synthetic_dataset(
            sandbox_id=sandbox["id"],
            name="Experiment Dataset",
            dataset_type="transactions",
            record_count=500,
            created_by=company.id
        )
        return {
            "company": company,
            "sandbox": sandbox,
            "dataset": dataset
        }

    def test_create_experiment(self, manager, sandbox_with_dataset):
        """Test creating an experiment."""
        experiment = manager.create_experiment(
            sandbox_id=sandbox_with_dataset["sandbox"]["id"],
            name="Test Experiment",
            experiment_type="training",
            created_by=sandbox_with_dataset["company"].id,
            model_type="logistic_regression",
            dataset_id=sandbox_with_dataset["dataset"]["id"]
        )

        assert experiment is not None
        assert experiment["id"].startswith("exp_")
        assert experiment["name"] == "Test Experiment"
        assert experiment["experiment_type"] == "training"
        assert experiment["status"] == "pending"

    def test_create_evaluation_experiment(self, manager, sandbox_with_dataset):
        """Test creating an evaluation experiment."""
        experiment = manager.create_experiment(
            sandbox_id=sandbox_with_dataset["sandbox"]["id"],
            name="Evaluation Test",
            experiment_type="evaluation",
            created_by=sandbox_with_dataset["company"].id,
            dataset_id=sandbox_with_dataset["dataset"]["id"]
        )

        assert experiment["experiment_type"] == "evaluation"

    def test_create_clustering_experiment(self, manager, sandbox_with_dataset):
        """Test creating a clustering experiment."""
        experiment = manager.create_experiment(
            sandbox_id=sandbox_with_dataset["sandbox"]["id"],
            name="Clustering Test",
            experiment_type="clustering",
            created_by=sandbox_with_dataset["company"].id,
            model_type="kmeans",
            dataset_id=sandbox_with_dataset["dataset"]["id"]
        )

        assert experiment["experiment_type"] == "clustering"

    def test_create_encryption_benchmark(self, manager, sandbox_with_dataset):
        """Test creating an encryption benchmark experiment."""
        experiment = manager.create_experiment(
            sandbox_id=sandbox_with_dataset["sandbox"]["id"],
            name="Encryption Benchmark",
            experiment_type="encryption_benchmark",
            created_by=sandbox_with_dataset["company"].id
        )

        assert experiment["experiment_type"] == "encryption_benchmark"

    def test_run_experiment(self, manager, sandbox_with_dataset):
        """Test running an experiment."""
        experiment = manager.create_experiment(
            sandbox_id=sandbox_with_dataset["sandbox"]["id"],
            name="Run Test",
            experiment_type="training",
            created_by=sandbox_with_dataset["company"].id,
            model_type="linear_regression",
            dataset_id=sandbox_with_dataset["dataset"]["id"]
        )

        result = manager.run_experiment(experiment["id"])

        assert result is not None
        assert result["status"] == "completed"
        assert "results" in result
        assert result["started_at"] is not None
        assert result["completed_at"] is not None

    def test_run_experiment_generates_results(self, manager, sandbox_with_dataset):
        """Test that running an experiment generates results."""
        experiment = manager.create_experiment(
            sandbox_id=sandbox_with_dataset["sandbox"]["id"],
            name="Results Test",
            experiment_type="training",
            created_by=sandbox_with_dataset["company"].id,
            model_type="random_forest",
            dataset_id=sandbox_with_dataset["dataset"]["id"]
        )

        result = manager.run_experiment(experiment["id"])

        assert result["results"] is not None
        results = result["results"]
        # Training experiments should have model metrics
        assert "accuracy" in results or "mse" in results or "metrics" in results

    def test_list_experiments(self, manager, sandbox_with_dataset):
        """Test listing experiments in a sandbox."""
        manager.create_experiment(
            sandbox_id=sandbox_with_dataset["sandbox"]["id"],
            name="Experiment 1",
            experiment_type="training",
            created_by=sandbox_with_dataset["company"].id
        )
        manager.create_experiment(
            sandbox_id=sandbox_with_dataset["sandbox"]["id"],
            name="Experiment 2",
            experiment_type="evaluation",
            created_by=sandbox_with_dataset["company"].id
        )

        experiments = manager.list_experiments(sandbox_with_dataset["sandbox"]["id"])

        assert len(experiments) >= 2

    def test_get_experiment(self, manager, sandbox_with_dataset):
        """Test retrieving a specific experiment."""
        created = manager.create_experiment(
            sandbox_id=sandbox_with_dataset["sandbox"]["id"],
            name="Get Test Experiment",
            experiment_type="training",
            created_by=sandbox_with_dataset["company"].id
        )

        experiment = manager.get_experiment(created["id"])

        assert experiment is not None
        assert experiment["id"] == created["id"]
        assert experiment["name"] == "Get Test Experiment"

    def test_delete_experiment(self, manager, sandbox_with_dataset):
        """Test deleting an experiment."""
        experiment = manager.create_experiment(
            sandbox_id=sandbox_with_dataset["sandbox"]["id"],
            name="To Delete",
            experiment_type="training",
            created_by=sandbox_with_dataset["company"].id
        )

        result = manager.delete_experiment(
            experiment["id"],
            sandbox_with_dataset["company"].id
        )
        assert result is True


class TestSandboxStatistics:
    """Tests for sandbox statistics functionality."""

    @pytest.fixture
    def manager(self):
        """Create a manager with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_sandbox.db"
            mgr = ConsortiumManager(db_path)
            yield mgr

    @pytest.fixture
    def populated_sandbox(self, manager):
        """Create a sandbox with datasets and experiments."""
        company, _ = manager.create_company(
            name="Stats Test Corp",
            email="stats@testcorp.com"
        )
        sandbox = manager.create_sandbox(
            name="Stats Test Sandbox",
            owner_id=company.id
        )

        # Create datasets
        dataset = manager.generate_synthetic_dataset(
            sandbox_id=sandbox["id"],
            name="Stats Dataset",
            dataset_type="transactions",
            record_count=500,
            created_by=company.id
        )

        # Create experiments
        exp1 = manager.create_experiment(
            sandbox_id=sandbox["id"],
            name="Stats Exp 1",
            experiment_type="training",
            created_by=company.id,
            dataset_id=dataset["id"]
        )
        manager.run_experiment(exp1["id"])

        exp2 = manager.create_experiment(
            sandbox_id=sandbox["id"],
            name="Stats Exp 2",
            experiment_type="evaluation",
            created_by=company.id
        )
        manager.run_experiment(exp2["id"])

        return {
            "company": company,
            "sandbox": sandbox,
            "dataset": dataset
        }

    def test_get_sandbox_stats(self, manager, populated_sandbox):
        """Test retrieving sandbox statistics."""
        stats = manager.get_sandbox_stats(
            owner_id=populated_sandbox["company"].id
        )

        assert stats is not None
        assert "total_sandboxes" in stats
        assert "active_sandboxes" in stats
        assert "total_datasets" in stats
        assert "total_experiments" in stats
        assert "completed_experiments" in stats

    def test_stats_reflect_counts(self, manager, populated_sandbox):
        """Test that stats reflect actual counts."""
        stats = manager.get_sandbox_stats(
            owner_id=populated_sandbox["company"].id
        )

        assert stats["total_sandboxes"] >= 1
        assert stats["total_datasets"] >= 1
        assert stats["total_experiments"] >= 2
        assert stats["completed_experiments"] >= 2

    def test_sandbox_includes_counts(self, manager, populated_sandbox):
        """Test that sandbox response includes counts."""
        sandbox = manager.get_sandbox(populated_sandbox["sandbox"]["id"])

        assert "dataset_count" in sandbox
        assert "experiment_count" in sandbox
        assert sandbox["dataset_count"] >= 1
        assert sandbox["experiment_count"] >= 2

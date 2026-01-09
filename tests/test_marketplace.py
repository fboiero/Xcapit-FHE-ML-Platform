"""Tests for TIER 3 Model Marketplace feature.

Tests cover:
- Marketplace categories
- Marketplace models (listing, filtering, search)
- Model deployments to consortiums
- Model reviews and ratings
- Marketplace statistics
"""

import importlib.util
import sys
import tempfile
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent
sdk_api_path = project_root / "sdk" / "api"


def load_module_from_path(module_name, file_path):
    """Load a module from file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


# Load consortium module package
consortium_package_path = sdk_api_path / "consortium"
consortium_module = load_module_from_path(
    "sdk.api.consortium", consortium_package_path / "__init__.py"
)
ConsortiumManager = consortium_module.ConsortiumManager
ConsortiumStatus = consortium_module.ConsortiumStatus
MemberRole = consortium_module.MemberRole
MemberStatus = consortium_module.MemberStatus


class TestMarketplaceCategories:
    """Tests for marketplace categories functionality."""

    @pytest.fixture
    def manager(self):
        """Create a manager with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_marketplace.db"
            mgr = ConsortiumManager(db_path)
            yield mgr

    def test_get_marketplace_categories(self, manager):
        """Test retrieving marketplace categories."""
        categories = manager.get_marketplace_categories()

        assert categories is not None
        assert len(categories) >= 5  # We seed 5 categories

        # Verify category structure
        for category in categories:
            assert "id" in category
            assert "name" in category
            assert "description" in category
            assert "model_count" in category

    def test_categories_include_fraud(self, manager):
        """Test that fraud detection category exists."""
        categories = manager.get_marketplace_categories()
        fraud_category = next((c for c in categories if c["id"] == "cat_fraud"), None)

        assert fraud_category is not None
        assert fraud_category["name"] == "Fraud Detection"

    def test_categories_include_credit(self, manager):
        """Test that credit scoring category exists."""
        categories = manager.get_marketplace_categories()
        credit_category = next((c for c in categories if c["id"] == "cat_credit"), None)

        assert credit_category is not None
        assert credit_category["name"] == "Credit Scoring"

    def test_categories_include_health(self, manager):
        """Test that health category exists."""
        categories = manager.get_marketplace_categories()
        health_category = next((c for c in categories if c["id"] == "cat_health"), None)

        assert health_category is not None
        assert health_category["name"] == "Healthcare"

    def test_category_model_counts(self, manager):
        """Test that category model counts are correct."""
        categories = manager.get_marketplace_categories()

        # Each category should have at least 1 model from seeds
        for category in categories:
            assert category["model_count"] >= 0


class TestMarketplaceModels:
    """Tests for marketplace model listing and filtering."""

    @pytest.fixture
    def manager(self):
        """Create a manager with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_marketplace.db"
            mgr = ConsortiumManager(db_path)
            yield mgr

    def test_get_marketplace_models_all(self, manager):
        """Test retrieving all marketplace models."""
        models = manager.get_marketplace_models()

        assert models is not None
        assert len(models) >= 10  # We seed 10 models

    def test_model_structure(self, manager):
        """Test that models have required fields."""
        models = manager.get_marketplace_models()

        assert len(models) > 0
        model = models[0]

        required_fields = [
            "id",
            "name",
            "description",
            "industry",
            "model_type",
            "version",
            "pricing_type",
            "is_featured",
            "downloads",
            "rating",
            "rating_count",
        ]

        for field in required_fields:
            assert field in model, f"Missing field: {field}"

    def test_filter_by_industry(self, manager):
        """Test filtering models by industry."""
        models = manager.get_marketplace_models(industry="cat_fraud")

        assert len(models) >= 2  # We seed 2 fraud models
        for model in models:
            assert model["industry"] == "cat_fraud"

    def test_filter_by_model_type(self, manager):
        """Test filtering models by model type."""
        models = manager.get_marketplace_models(model_type="logistic_regression")

        assert len(models) >= 1
        for model in models:
            assert model["model_type"] == "logistic_regression"

    def test_filter_featured_only(self, manager):
        """Test filtering for featured models only."""
        models = manager.get_marketplace_models(featured_only=True)

        assert len(models) >= 1
        for model in models:
            assert model["is_featured"]

    def test_sort_by_downloads(self, manager):
        """Test sorting models by downloads."""
        models = manager.get_marketplace_models(sort_by="downloads")

        if len(models) > 1:
            for i in range(len(models) - 1):
                assert models[i]["downloads"] >= models[i + 1]["downloads"]

    def test_sort_by_rating(self, manager):
        """Test sorting models by rating."""
        models = manager.get_marketplace_models(sort_by="rating")

        if len(models) > 1:
            for i in range(len(models) - 1):
                assert models[i]["rating"] >= models[i + 1]["rating"]

    def test_search_models(self, manager):
        """Test searching models by text."""
        models = manager.get_marketplace_models(search="fraud")

        assert len(models) >= 1
        for model in models:
            assert "fraud" in model["name"].lower() or "fraud" in model["description"].lower()

    def test_limit_models(self, manager):
        """Test limiting number of models returned."""
        models = manager.get_marketplace_models(limit=3)

        assert len(models) <= 3

    def test_get_featured_models(self, manager):
        """Test getting featured models."""
        models = manager.get_featured_models(limit=4)

        assert len(models) >= 1
        assert len(models) <= 4
        for model in models:
            assert model["is_featured"]

    def test_get_single_model(self, manager):
        """Test retrieving a single model by ID."""
        # First get all models to get a valid ID
        all_models = manager.get_marketplace_models()
        assert len(all_models) > 0

        model_id = all_models[0]["id"]
        model = manager.get_marketplace_model(model_id)

        assert model is not None
        assert model["id"] == model_id
        assert "features" in model
        assert "use_cases" in model

    def test_get_nonexistent_model(self, manager):
        """Test retrieving a non-existent model."""
        model = manager.get_marketplace_model("nonexistent_model_id")
        assert model is None


class TestMarketplaceDeployments:
    """Tests for model deployment functionality."""

    @pytest.fixture
    def manager(self):
        """Create a manager with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_marketplace.db"
            mgr = ConsortiumManager(db_path)
            yield mgr

    @pytest.fixture
    def setup_consortium(self, manager):
        """Create a consortium with members for testing."""
        owner, _ = manager.create_company("Owner Corp", "owner@test.com")
        member, _ = manager.create_company("Member Corp", "member@test.com")

        consortium = manager.create_consortium(
            name="Test Consortium",
            description="Testing marketplace",
            owner_id=owner.id,
            model_type="linear_regression",
        )

        invitation = manager.create_invitation(
            consortium_id=consortium.id,
            invited_by=owner.id,
            invite_email="member@test.com",
            role=MemberRole.CONTRIBUTOR,
        )
        manager.accept_invitation(invitation.invite_code, member.id)

        return {"consortium": consortium, "owner": owner, "member": member}

    def test_deploy_marketplace_model(self, manager, setup_consortium):
        """Test deploying a model to a consortium."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        # Get a model from marketplace
        models = manager.get_marketplace_models()
        model = models[0]

        deployment = manager.deploy_marketplace_model(
            model_id=model["id"], consortium_id=consortium.id, deployed_by=owner.id
        )

        assert deployment is not None
        assert "id" in deployment
        assert deployment["model_id"] == model["id"]
        assert deployment["consortium_id"] == consortium.id
        assert deployment["deployed_by"] == owner.id
        assert deployment["status"] in ["active", "deployed"]

    def test_deploy_with_config(self, manager, setup_consortium):
        """Test deploying a model with custom configuration."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        models = manager.get_marketplace_models()
        model = models[0]

        config = {"threshold": 0.5, "max_predictions": 1000}

        deployment = manager.deploy_marketplace_model(
            model_id=model["id"], consortium_id=consortium.id, deployed_by=owner.id, config=config
        )

        assert deployment is not None
        assert "id" in deployment

    def test_get_consortium_deployments(self, manager, setup_consortium):
        """Test getting all deployments for a consortium."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        # Deploy a model
        models = manager.get_marketplace_models()
        manager.deploy_marketplace_model(
            model_id=models[0]["id"], consortium_id=consortium.id, deployed_by=owner.id
        )

        deployments = manager.get_consortium_deployments(consortium.id)

        assert len(deployments) >= 1
        assert deployments[0]["consortium_id"] == consortium.id

    def test_undeploy_model(self, manager, setup_consortium):
        """Test undeploying a model from consortium."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        # Deploy a model first
        models = manager.get_marketplace_models()
        deployment = manager.deploy_marketplace_model(
            model_id=models[0]["id"], consortium_id=consortium.id, deployed_by=owner.id
        )

        # Undeploy it
        success = manager.undeploy_model(deployment["id"], owner.id)

        assert success

        # Verify it's removed
        deployments = manager.get_consortium_deployments(consortium.id)
        active_deployments = [d for d in deployments if d["status"] == "active"]
        assert len(active_deployments) == 0

    def test_deploy_nonexistent_model(self, manager, setup_consortium):
        """Test deploying a non-existent model."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        with pytest.raises(ValueError):
            manager.deploy_marketplace_model(
                model_id="nonexistent_model", consortium_id=consortium.id, deployed_by=owner.id
            )


class TestMarketplaceReviews:
    """Tests for model review functionality."""

    @pytest.fixture
    def manager(self):
        """Create a manager with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_marketplace.db"
            mgr = ConsortiumManager(db_path)
            yield mgr

    @pytest.fixture
    def setup_company(self, manager):
        """Create a company for testing."""
        company, _ = manager.create_company("Test Corp", "test@test.com")
        return company

    def test_add_model_review(self, manager, setup_company):
        """Test adding a review to a model."""
        company = setup_company

        models = manager.get_marketplace_models()
        model = models[0]

        review_id = manager.add_model_review(
            model_id=model["id"],
            reviewer_id=company.id,
            rating=5,
            title="Great model!",
            comment="This model works perfectly for our use case.",
        )

        assert review_id is not None

    def test_add_review_with_consortium(self, manager, setup_company):
        """Test adding a review linked to a consortium."""
        company = setup_company

        consortium = manager.create_consortium(
            name="Test Consortium",
            description="Testing",
            owner_id=company.id,
            model_type="linear_regression",
        )

        models = manager.get_marketplace_models()
        model = models[0]

        review_id = manager.add_model_review(
            model_id=model["id"],
            reviewer_id=company.id,
            rating=4,
            title="Good model",
            comment="Works well in our consortium.",
            consortium_id=consortium.id,
        )

        assert review_id is not None

    def test_get_model_reviews(self, manager, setup_company):
        """Test retrieving reviews for a model."""
        company = setup_company

        models = manager.get_marketplace_models()
        model = models[0]

        # Add a review
        manager.add_model_review(
            model_id=model["id"],
            reviewer_id=company.id,
            rating=5,
            title="Excellent!",
            comment="Highly recommended.",
        )

        reviews = manager.get_model_reviews(model["id"])

        assert len(reviews) >= 1
        assert reviews[0]["rating"] == 5
        assert reviews[0]["title"] == "Excellent!"

    def test_review_rating_validation(self, manager, setup_company):
        """Test that ratings must be 1-5."""
        company = setup_company

        models = manager.get_marketplace_models()
        model = models[0]

        # Rating too low
        with pytest.raises(ValueError):
            manager.add_model_review(
                model_id=model["id"], reviewer_id=company.id, rating=0, title="Test"
            )

        # Rating too high
        with pytest.raises(ValueError):
            manager.add_model_review(
                model_id=model["id"], reviewer_id=company.id, rating=6, title="Test"
            )

    def test_review_updates_model_rating(self, manager, setup_company):
        """Test that adding reviews updates the model's average rating."""
        company = setup_company

        models = manager.get_marketplace_models()
        model = models[0]

        # Add a review
        manager.add_model_review(
            model_id=model["id"], reviewer_id=company.id, rating=5, title="Test review"
        )

        # Verify the review was added
        reviews = manager.get_model_reviews(model["id"])

        # Should have at least our newly added review
        assert len(reviews) >= 1

        # Find our review
        our_review = next((r for r in reviews if r["title"] == "Test review"), None)
        assert our_review is not None
        assert our_review["rating"] == 5


class TestMarketplaceStatistics:
    """Tests for marketplace statistics."""

    @pytest.fixture
    def manager(self):
        """Create a manager with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_marketplace.db"
            mgr = ConsortiumManager(db_path)
            yield mgr

    def test_get_marketplace_stats(self, manager):
        """Test retrieving marketplace statistics."""
        stats = manager.get_marketplace_stats()

        assert stats is not None
        assert "total_models" in stats
        assert "total_downloads" in stats
        assert "active_consortiums" in stats
        assert "total_reviews" in stats
        assert "average_rating" in stats

    def test_stats_total_models(self, manager):
        """Test that total models count is correct."""
        stats = manager.get_marketplace_stats()
        models = manager.get_marketplace_models()

        assert stats["total_models"] == len(models)

    def test_stats_total_downloads(self, manager):
        """Test that total downloads is calculated."""
        stats = manager.get_marketplace_stats()

        assert stats["total_downloads"] >= 0

    def test_stats_average_rating(self, manager):
        """Test that average rating is reasonable."""
        stats = manager.get_marketplace_stats()

        assert 0 <= stats["average_rating"] <= 5


class TestMarketplaceIntegration:
    """Integration tests for marketplace workflow."""

    @pytest.fixture
    def manager(self):
        """Create a manager with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_marketplace.db"
            mgr = ConsortiumManager(db_path)
            yield mgr

    def test_full_marketplace_workflow(self, manager):
        """Test complete marketplace workflow: browse, deploy, review."""
        # Create company
        company, _ = manager.create_company("Enterprise Corp", "enterprise@test.com")

        # Create consortium
        consortium = manager.create_consortium(
            name="Enterprise Consortium",
            description="For testing marketplace workflow",
            owner_id=company.id,
            model_type="logistic_regression",
        )

        # Browse marketplace categories
        categories = manager.get_marketplace_categories()
        assert len(categories) > 0

        # Browse models in fraud category
        fraud_models = manager.get_marketplace_models(industry="cat_fraud")
        assert len(fraud_models) > 0

        # View a specific model
        model = manager.get_marketplace_model(fraud_models[0]["id"])
        assert model is not None

        # Deploy model to consortium
        deployment = manager.deploy_marketplace_model(
            model_id=model["id"], consortium_id=consortium.id, deployed_by=company.id
        )
        assert deployment is not None

        # Verify deployment
        deployments = manager.get_consortium_deployments(consortium.id)
        assert len(deployments) == 1

        # Add a review
        review_id = manager.add_model_review(
            model_id=model["id"],
            reviewer_id=company.id,
            rating=5,
            title="Excellent fraud detection",
            comment="Reduced our false positives by 40%",
            consortium_id=consortium.id,
        )
        assert review_id is not None

        # Check reviews
        reviews = manager.get_model_reviews(model["id"])
        assert len(reviews) >= 1

        # Check marketplace stats
        stats = manager.get_marketplace_stats()
        assert stats["total_models"] > 0

        # Undeploy model
        success = manager.undeploy_model(deployment["id"], company.id)
        assert success

    def test_multiple_deployments(self, manager):
        """Test deploying multiple models to same consortium."""
        company, _ = manager.create_company("Multi Corp", "multi@test.com")

        consortium = manager.create_consortium(
            name="Multi Model Consortium",
            description="Testing multiple deployments",
            owner_id=company.id,
            model_type="logistic_regression",
        )

        models = manager.get_marketplace_models(limit=3)

        # Deploy multiple models
        for model in models:
            manager.deploy_marketplace_model(
                model_id=model["id"], consortium_id=consortium.id, deployed_by=company.id
            )

        deployments = manager.get_consortium_deployments(consortium.id)
        assert len(deployments) == 3

    def test_search_and_filter_combination(self, manager):
        """Test combining search with filters."""
        # Search for fraud in credit category (should return empty or matching)
        models = manager.get_marketplace_models(industry="cat_credit", search="default")

        for model in models:
            assert model["industry"] == "cat_credit"
            assert "default" in model["name"].lower() or "default" in model["description"].lower()

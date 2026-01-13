"""Tests for marketplace API routes."""

import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

# Mock tenseal before importing sdk modules
sys.modules["tenseal"] = MagicMock()

from fastapi import FastAPI
from fastapi.testclient import TestClient

from sdk.api.marketplace_routes import router
from sdk.api.auth import get_current_company


@pytest.fixture
def mock_company():
    """Mock company data."""
    return {"id": "company_001", "name": "Test Company"}


@pytest.fixture
def mock_manager():
    """Create mock ConsortiumManager."""
    return MagicMock()


@pytest.fixture
def app(mock_company):
    """Create FastAPI app with router and overridden dependencies."""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_company] = lambda: mock_company
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


def make_request(client, mock_manager, method, url, **kwargs):
    """Helper to make requests with mocked ConsortiumManager."""
    with patch.dict(
        "sys.modules",
        {
            "sdk.api.consortium": MagicMock(
                ConsortiumManager=MagicMock(return_value=mock_manager)
            ),
            "sdk.api.database": MagicMock(get_db_path=MagicMock(return_value=":memory:")),
        },
    ):
        if method == "get":
            return client.get(url, **kwargs)
        elif method == "post":
            return client.post(url, **kwargs)
        elif method == "delete":
            return client.delete(url, **kwargs)


# ============ Categories Tests ============


class TestListCategories:
    """Tests for GET /marketplace/categories endpoint."""

    def test_list_categories_success(self, client, mock_manager):
        """Test listing all categories."""
        mock_manager.get_marketplace_categories.return_value = [
            {
                "id": "cat_fraud",
                "name": "Fraud Detection",
                "description": "Models for fraud detection",
                "icon": "shield",
                "model_count": 15,
            },
            {
                "id": "cat_credit",
                "name": "Credit Scoring",
                "description": "Models for credit risk assessment",
                "icon": "credit-card",
                "model_count": 12,
            },
            {
                "id": "cat_health",
                "name": "Healthcare",
                "description": "Models for healthcare applications",
                "icon": "heart",
                "model_count": 8,
            },
        ]

        response = make_request(client, mock_manager, "get", "/marketplace/categories")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["id"] == "cat_fraud"
        assert data[0]["model_count"] == 15

    def test_list_categories_empty(self, client, mock_manager):
        """Test listing categories when none exist."""
        mock_manager.get_marketplace_categories.return_value = []

        response = make_request(client, mock_manager, "get", "/marketplace/categories")

        assert response.status_code == 200
        assert response.json() == []


# ============ Models Tests ============


class TestListModels:
    """Tests for GET /marketplace/models endpoint."""

    def test_list_models_success(self, client, mock_manager):
        """Test listing all models."""
        mock_manager.get_marketplace_models.return_value = [
            {
                "id": "model_001",
                "name": "Fraud Detector Pro",
                "description": "Advanced fraud detection model",
                "industry": "cat_fraud",
                "model_type": "logistic_regression",
                "version": "2.1.0",
                "accuracy": 0.95,
                "training_samples": 100000,
                "pricing_type": "free",
                "is_featured": True,
                "downloads": 5000,
                "rating": 4.5,
                "rating_count": 120,
            },
            {
                "id": "model_002",
                "name": "Credit Risk Analyzer",
                "description": "Credit scoring model",
                "industry": "cat_credit",
                "model_type": "decision_tree",
                "version": "1.5.0",
                "accuracy": 0.88,
                "training_samples": 50000,
                "pricing_type": "premium",
                "is_featured": False,
                "downloads": 2000,
                "rating": 4.2,
                "rating_count": 45,
            },
        ]

        response = make_request(client, mock_manager, "get", "/marketplace/models")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Fraud Detector Pro"

    def test_list_models_with_industry_filter(self, client, mock_manager):
        """Test listing models filtered by industry."""
        mock_manager.get_marketplace_models.return_value = []

        response = make_request(
            client,
            mock_manager,
            "get",
            "/marketplace/models",
            params={"industry": "cat_fraud"},
        )

        assert response.status_code == 200
        mock_manager.get_marketplace_models.assert_called_with(
            industry="cat_fraud",
            model_type=None,
            featured_only=False,
            search=None,
            sort_by="downloads",
            limit=50,
        )

    def test_list_models_with_model_type_filter(self, client, mock_manager):
        """Test listing models filtered by model type."""
        mock_manager.get_marketplace_models.return_value = []

        response = make_request(
            client,
            mock_manager,
            "get",
            "/marketplace/models",
            params={"model_type": "logistic_regression"},
        )

        assert response.status_code == 200
        mock_manager.get_marketplace_models.assert_called_with(
            industry=None,
            model_type="logistic_regression",
            featured_only=False,
            search=None,
            sort_by="downloads",
            limit=50,
        )

    def test_list_models_featured_only(self, client, mock_manager):
        """Test listing only featured models."""
        mock_manager.get_marketplace_models.return_value = []

        response = make_request(
            client,
            mock_manager,
            "get",
            "/marketplace/models",
            params={"featured": True},
        )

        assert response.status_code == 200
        mock_manager.get_marketplace_models.assert_called_with(
            industry=None,
            model_type=None,
            featured_only=True,
            search=None,
            sort_by="downloads",
            limit=50,
        )

    def test_list_models_with_search(self, client, mock_manager):
        """Test listing models with search query."""
        mock_manager.get_marketplace_models.return_value = []

        response = make_request(
            client,
            mock_manager,
            "get",
            "/marketplace/models",
            params={"search": "fraud"},
        )

        assert response.status_code == 200
        mock_manager.get_marketplace_models.assert_called_with(
            industry=None,
            model_type=None,
            featured_only=False,
            search="fraud",
            sort_by="downloads",
            limit=50,
        )

    def test_list_models_sort_by_rating(self, client, mock_manager):
        """Test listing models sorted by rating."""
        mock_manager.get_marketplace_models.return_value = []

        response = make_request(
            client,
            mock_manager,
            "get",
            "/marketplace/models",
            params={"sort_by": "rating"},
        )

        assert response.status_code == 200
        mock_manager.get_marketplace_models.assert_called_with(
            industry=None,
            model_type=None,
            featured_only=False,
            search=None,
            sort_by="rating",
            limit=50,
        )

    def test_list_models_with_limit(self, client, mock_manager):
        """Test listing models with custom limit."""
        mock_manager.get_marketplace_models.return_value = []

        response = make_request(
            client,
            mock_manager,
            "get",
            "/marketplace/models",
            params={"limit": 25},
        )

        assert response.status_code == 200
        mock_manager.get_marketplace_models.assert_called_with(
            industry=None,
            model_type=None,
            featured_only=False,
            search=None,
            sort_by="downloads",
            limit=25,
        )


class TestGetFeaturedModels:
    """Tests for GET /marketplace/models/featured endpoint."""

    def test_get_featured_success(self, client, mock_manager):
        """Test getting featured models."""
        mock_manager.get_featured_models.return_value = [
            {
                "id": "model_001",
                "name": "Featured Model 1",
                "description": "Top rated model",
                "industry": "cat_fraud",
                "model_type": "logistic_regression",
                "version": "3.0.0",
                "accuracy": 0.97,
                "training_samples": 200000,
                "pricing_type": "free",
                "is_featured": True,
                "downloads": 10000,
                "rating": 4.8,
                "rating_count": 250,
            },
        ]

        response = make_request(
            client, mock_manager, "get", "/marketplace/models/featured"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["is_featured"] is True

    def test_get_featured_with_limit(self, client, mock_manager):
        """Test getting featured models with custom limit."""
        mock_manager.get_featured_models.return_value = []

        response = make_request(
            client,
            mock_manager,
            "get",
            "/marketplace/models/featured",
            params={"limit": 3},
        )

        assert response.status_code == 200
        mock_manager.get_featured_models.assert_called_with(limit=3)


class TestGetModel:
    """Tests for GET /marketplace/models/{model_id} endpoint."""

    def test_get_model_success(self, client, mock_manager):
        """Test getting a specific model."""
        mock_manager.get_marketplace_model.return_value = {
            "id": "model_001",
            "name": "Fraud Detector Pro",
            "description": "Advanced fraud detection model",
            "industry": "cat_fraud",
            "model_type": "logistic_regression",
            "version": "2.1.0",
            "accuracy": 0.95,
            "training_samples": 100000,
            "features": ["transaction_amount", "merchant_category", "location"],
            "use_cases": ["Real-time fraud detection", "Transaction scoring"],
            "pricing_type": "free",
            "price": 0.0,
            "is_featured": True,
            "downloads": 5000,
            "rating": 4.5,
            "rating_count": 120,
            "created_at": datetime.now().isoformat(),
        }

        response = make_request(
            client, mock_manager, "get", "/marketplace/models/model_001"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "model_001"
        assert len(data["features"]) == 3

    def test_get_model_not_found(self, client, mock_manager):
        """Test getting non-existent model."""
        mock_manager.get_marketplace_model.return_value = None

        response = make_request(
            client, mock_manager, "get", "/marketplace/models/nonexistent"
        )

        assert response.status_code == 404


# ============ Deployments Tests ============


class TestDeployModel:
    """Tests for POST /marketplace/models/{model_id}/deploy endpoint."""

    def test_deploy_model_success(self, client, mock_manager):
        """Test successful model deployment."""
        mock_membership = MagicMock()
        mock_membership.role.value = "admin"
        mock_manager.get_membership.return_value = mock_membership
        mock_manager.deploy_marketplace_model.return_value = {
            "id": "deploy_001",
            "model_id": "model_001",
            "model_name": "Fraud Detector Pro",
            "consortium_id": "cons_001",
            "deployed_by": "company_001",
            "deployed_at": datetime.now().isoformat(),
            "status": "active",
        }

        response = make_request(
            client,
            mock_manager,
            "post",
            "/marketplace/models/model_001/deploy",
            json={"consortium_id": "cons_001", "config": {"threshold": 0.8}},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "deploy_001"
        assert data["status"] == "active"
        mock_manager.record_audit_event.assert_called_once()

    def test_deploy_model_as_owner(self, client, mock_manager):
        """Test deployment as owner."""
        mock_membership = MagicMock()
        mock_membership.role.value = "owner"
        mock_manager.get_membership.return_value = mock_membership
        mock_manager.deploy_marketplace_model.return_value = {
            "id": "deploy_002",
            "model_id": "model_002",
            "model_name": "Credit Analyzer",
            "consortium_id": "cons_001",
            "deployed_by": "company_001",
            "deployed_at": datetime.now().isoformat(),
            "status": "active",
        }

        response = make_request(
            client,
            mock_manager,
            "post",
            "/marketplace/models/model_002/deploy",
            json={"consortium_id": "cons_001"},
        )

        assert response.status_code == 200

    def test_deploy_model_not_admin(self, client, mock_manager):
        """Test deployment when not admin or owner."""
        mock_membership = MagicMock()
        mock_membership.role.value = "member"
        mock_manager.get_membership.return_value = mock_membership

        response = make_request(
            client,
            mock_manager,
            "post",
            "/marketplace/models/model_001/deploy",
            json={"consortium_id": "cons_001"},
        )

        assert response.status_code == 403

    def test_deploy_model_not_member(self, client, mock_manager):
        """Test deployment when not a member."""
        mock_manager.get_membership.return_value = None

        response = make_request(
            client,
            mock_manager,
            "post",
            "/marketplace/models/model_001/deploy",
            json={"consortium_id": "cons_001"},
        )

        assert response.status_code == 403

    def test_deploy_model_not_found(self, client, mock_manager):
        """Test deployment of non-existent model."""
        mock_membership = MagicMock()
        mock_membership.role.value = "admin"
        mock_manager.get_membership.return_value = mock_membership
        mock_manager.deploy_marketplace_model.side_effect = ValueError("Model not found")

        response = make_request(
            client,
            mock_manager,
            "post",
            "/marketplace/models/nonexistent/deploy",
            json={"consortium_id": "cons_001"},
        )

        assert response.status_code == 404


class TestGetConsortiumDeployments:
    """Tests for GET /marketplace/deployments/{consortium_id} endpoint."""

    def test_get_deployments_success(self, client, mock_manager):
        """Test getting consortium deployments."""
        mock_manager.get_membership.return_value = MagicMock()
        mock_manager.get_consortium_deployments.return_value = [
            {
                "id": "deploy_001",
                "model_id": "model_001",
                "model_name": "Fraud Detector Pro",
                "consortium_id": "cons_001",
                "deployed_by": "company_001",
                "deployed_at": datetime.now().isoformat(),
                "status": "active",
            },
            {
                "id": "deploy_002",
                "model_id": "model_002",
                "model_name": "Credit Analyzer",
                "consortium_id": "cons_001",
                "deployed_by": "company_001",
                "deployed_at": datetime.now().isoformat(),
                "status": "active",
            },
        ]

        response = make_request(
            client, mock_manager, "get", "/marketplace/deployments/cons_001"
        )

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_deployments_not_member(self, client, mock_manager):
        """Test getting deployments when not a member."""
        mock_manager.get_membership.return_value = None

        response = make_request(
            client, mock_manager, "get", "/marketplace/deployments/cons_001"
        )

        assert response.status_code == 403


class TestUndeployModel:
    """Tests for DELETE /marketplace/deployments/{deployment_id} endpoint."""

    def test_undeploy_success(self, client, mock_manager):
        """Test successful model undeployment."""
        mock_manager.undeploy_model.return_value = True

        response = make_request(
            client, mock_manager, "delete", "/marketplace/deployments/deploy_001"
        )

        assert response.status_code == 200
        assert response.json()["status"] == "undeployed"
        mock_manager.undeploy_model.assert_called_with("deploy_001", "company_001")

    def test_undeploy_not_found(self, client, mock_manager):
        """Test undeploying non-existent deployment."""
        mock_manager.undeploy_model.return_value = False

        response = make_request(
            client, mock_manager, "delete", "/marketplace/deployments/nonexistent"
        )

        assert response.status_code == 404


# ============ Reviews Tests ============


class TestAddReview:
    """Tests for POST /marketplace/models/{model_id}/reviews endpoint."""

    def test_add_review_success(self, client, mock_manager):
        """Test adding a review."""
        mock_manager.get_marketplace_model.return_value = {"id": "model_001"}
        mock_manager.add_model_review.return_value = "review_001"

        response = make_request(
            client,
            mock_manager,
            "post",
            "/marketplace/models/model_001/reviews",
            json={
                "rating": 5,
                "title": "Excellent model",
                "comment": "Works great for our use case",
                "consortium_id": "cons_001",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "review_001"
        assert data["rating"] == 5
        assert data["title"] == "Excellent model"

    def test_add_review_minimal(self, client, mock_manager):
        """Test adding a review with minimal data."""
        mock_manager.get_marketplace_model.return_value = {"id": "model_001"}
        mock_manager.add_model_review.return_value = "review_002"

        response = make_request(
            client,
            mock_manager,
            "post",
            "/marketplace/models/model_001/reviews",
            json={"rating": 4},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["rating"] == 4
        assert data["title"] is None

    def test_add_review_model_not_found(self, client, mock_manager):
        """Test adding review for non-existent model."""
        mock_manager.get_marketplace_model.return_value = None

        response = make_request(
            client,
            mock_manager,
            "post",
            "/marketplace/models/nonexistent/reviews",
            json={"rating": 4},
        )

        assert response.status_code == 404

    def test_add_review_duplicate(self, client, mock_manager):
        """Test adding duplicate review."""
        mock_manager.get_marketplace_model.return_value = {"id": "model_001"}
        mock_manager.add_model_review.side_effect = ValueError("Already reviewed")

        response = make_request(
            client,
            mock_manager,
            "post",
            "/marketplace/models/model_001/reviews",
            json={"rating": 3},
        )

        assert response.status_code == 400


class TestGetReviews:
    """Tests for GET /marketplace/models/{model_id}/reviews endpoint."""

    def test_get_reviews_success(self, client, mock_manager):
        """Test getting model reviews."""
        mock_manager.get_model_reviews.return_value = [
            {
                "id": "review_001",
                "model_id": "model_001",
                "reviewer_id": "company_001",
                "reviewer_name": "Test Company",
                "rating": 5,
                "title": "Great model",
                "comment": "Highly recommend",
                "created_at": datetime.now().isoformat(),
                "helpful_count": 10,
            },
            {
                "id": "review_002",
                "model_id": "model_001",
                "reviewer_id": "company_002",
                "reviewer_name": "Other Company",
                "rating": 4,
                "title": "Good model",
                "comment": "Works well",
                "created_at": datetime.now().isoformat(),
                "helpful_count": 5,
            },
        ]

        response = make_request(
            client, mock_manager, "get", "/marketplace/models/model_001/reviews"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["rating"] == 5

    def test_get_reviews_with_limit(self, client, mock_manager):
        """Test getting reviews with custom limit."""
        mock_manager.get_model_reviews.return_value = []

        response = make_request(
            client,
            mock_manager,
            "get",
            "/marketplace/models/model_001/reviews",
            params={"limit": 10},
        )

        assert response.status_code == 200
        mock_manager.get_model_reviews.assert_called_with("model_001", limit=10)


# ============ Statistics Tests ============


class TestGetMarketplaceStats:
    """Tests for GET /marketplace/stats endpoint."""

    def test_get_stats_success(self, client, mock_manager):
        """Test getting marketplace statistics."""
        mock_manager.get_marketplace_stats.return_value = {
            "total_models": 50,
            "total_downloads": 250000,
            "active_consortiums": 120,
            "total_reviews": 1500,
            "average_rating": 4.3,
        }

        response = make_request(client, mock_manager, "get", "/marketplace/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_models"] == 50
        assert data["total_downloads"] == 250000
        assert data["average_rating"] == 4.3


# ============ Validation Tests ============


class TestMarketplaceValidation:
    """Tests for input validation in marketplace routes."""

    def test_invalid_industry_filter(self, client, mock_manager):
        """Test with invalid industry filter."""
        response = make_request(
            client,
            mock_manager,
            "get",
            "/marketplace/models",
            params={"industry": "invalid_industry"},
        )

        assert response.status_code == 422

    def test_invalid_model_type_filter(self, client, mock_manager):
        """Test with invalid model type filter."""
        response = make_request(
            client,
            mock_manager,
            "get",
            "/marketplace/models",
            params={"model_type": "invalid_type"},
        )

        assert response.status_code == 422

    def test_invalid_sort_by(self, client, mock_manager):
        """Test with invalid sort_by value."""
        response = make_request(
            client,
            mock_manager,
            "get",
            "/marketplace/models",
            params={"sort_by": "invalid_sort"},
        )

        assert response.status_code == 422

    def test_limit_exceeds_maximum(self, client, mock_manager):
        """Test with limit exceeding maximum."""
        response = make_request(
            client,
            mock_manager,
            "get",
            "/marketplace/models",
            params={"limit": 200},  # Max is 100
        )

        assert response.status_code == 422

    def test_review_rating_below_minimum(self, client, mock_manager):
        """Test review with rating below minimum."""
        mock_manager.get_marketplace_model.return_value = {"id": "model_001"}

        response = make_request(
            client,
            mock_manager,
            "post",
            "/marketplace/models/model_001/reviews",
            json={"rating": 0},  # Min is 1
        )

        assert response.status_code == 422

    def test_review_rating_above_maximum(self, client, mock_manager):
        """Test review with rating above maximum."""
        mock_manager.get_marketplace_model.return_value = {"id": "model_001"}

        response = make_request(
            client,
            mock_manager,
            "post",
            "/marketplace/models/model_001/reviews",
            json={"rating": 6},  # Max is 5
        )

        assert response.status_code == 422

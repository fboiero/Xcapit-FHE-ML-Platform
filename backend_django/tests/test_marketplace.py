"""
Marketplace module tests for Xcapit FHE-ML Platform.

Tests for model marketplace, deployments, and reviews.
"""

from decimal import Decimal

import pytest
from rest_framework import status

from apps.consortiums.models import ConsortiumMember
from apps.marketplace.models import Category, Deployment, MarketplaceModel, Review


@pytest.mark.django_db
class TestCategoryEndpoints:
    """Tests for category (read-only) operations."""

    def test_list_categories(self, auth_client):
        """Test listing categories."""
        Category.objects.create(
            id="cat_fraud",
            name="Fraud Detection",
            description="Models for fraud detection",
        )

        url = "/api/v2/marketplace/categories/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_get_category(self, auth_client):
        """Test getting a single category."""
        category = Category.objects.create(
            id="cat_test",
            name="Test Category",
        )

        url = f"/api/v2/marketplace/categories/{category.id}/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Test Category"

    def test_get_category_models(self, auth_client):
        """Test getting models in a category."""
        category = Category.objects.create(
            id="cat_test",
            name="Test Category",
        )
        MarketplaceModel.objects.create(
            name="Test Model",
            category=category,
            model_type=MarketplaceModel.ModelType.LOGISTIC_REGRESSION,
            is_active=True,
        )

        url = f"/api/v2/marketplace/categories/{category.id}/models/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_categories_are_read_only(self, auth_client):
        """Test categories cannot be created via API."""
        url = "/api/v2/marketplace/categories/"
        data = {"id": "new_cat", "name": "New Category"}

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestMarketplaceModelEndpoints:
    """Tests for marketplace model viewing."""

    def test_list_models(self, auth_client):
        """Test listing marketplace models."""
        MarketplaceModel.objects.create(
            name="Test Model",
            model_type=MarketplaceModel.ModelType.LOGISTIC_REGRESSION,
            is_active=True,
        )

        url = "/api/v2/marketplace/models/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_list_only_active_models(self, auth_client):
        """Test only active models are listed."""
        active = MarketplaceModel.objects.create(
            name="Active Model",
            model_type=MarketplaceModel.ModelType.LOGISTIC_REGRESSION,
            is_active=True,
        )
        MarketplaceModel.objects.create(
            name="Inactive Model",
            model_type=MarketplaceModel.ModelType.LOGISTIC_REGRESSION,
            is_active=False,
        )

        url = "/api/v2/marketplace/models/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Inactive models are not returned
        model_names = [m["name"] for m in response.data]
        assert "Active Model" in model_names
        assert "Inactive Model" not in model_names

    def test_get_model(self, auth_client):
        """Test getting a single model."""
        model = MarketplaceModel.objects.create(
            name="Test Model",
            description="A test model",
            model_type=MarketplaceModel.ModelType.LINEAR_REGRESSION,
            accuracy=0.92,
            is_active=True,
        )

        url = f"/api/v2/marketplace/models/{model.id}/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Test Model"
        assert response.data["accuracy"] == 0.92

    def test_get_featured_models(self, auth_client):
        """Test getting featured models."""
        MarketplaceModel.objects.create(
            name="Featured Model",
            model_type=MarketplaceModel.ModelType.LOGISTIC_REGRESSION,
            is_active=True,
            is_featured=True,
        )
        MarketplaceModel.objects.create(
            name="Regular Model",
            model_type=MarketplaceModel.ModelType.LOGISTIC_REGRESSION,
            is_active=True,
            is_featured=False,
        )

        url = "/api/v2/marketplace/models/featured/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        for model in response.data:
            assert model["is_featured"] is True

    def test_get_popular_models(self, auth_client):
        """Test getting popular models."""
        MarketplaceModel.objects.create(
            name="Popular Model",
            model_type=MarketplaceModel.ModelType.LOGISTIC_REGRESSION,
            is_active=True,
            downloads=1000,
        )
        MarketplaceModel.objects.create(
            name="Less Popular",
            model_type=MarketplaceModel.ModelType.LOGISTIC_REGRESSION,
            is_active=True,
            downloads=10,
        )

        url = "/api/v2/marketplace/models/popular/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Sorted by downloads
        if len(response.data) >= 2:
            assert response.data[0]["downloads"] >= response.data[1]["downloads"]

    def test_get_top_rated_models(self, auth_client, company):
        """Test getting top rated models."""
        model = MarketplaceModel.objects.create(
            name="Top Rated",
            model_type=MarketplaceModel.ModelType.LOGISTIC_REGRESSION,
            is_active=True,
        )
        Review.objects.create(
            marketplace_model=model,
            reviewer=company,
            rating=5,
        )

        url = "/api/v2/marketplace/models/top_rated/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_search_models(self, auth_client):
        """Test searching marketplace models."""
        MarketplaceModel.objects.create(
            name="Fraud Detection Model",
            description="Detects fraud in transactions",
            model_type=MarketplaceModel.ModelType.LOGISTIC_REGRESSION,
            is_active=True,
        )
        MarketplaceModel.objects.create(
            name="Customer Segmentation",
            model_type=MarketplaceModel.ModelType.KMEANS,
            is_active=True,
        )

        url = "/api/v2/marketplace/models/search/"
        data = {"query": "fraud"}

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 1

    def test_search_with_filters(self, auth_client):
        """Test searching with filters."""
        category = Category.objects.create(id="cat_fraud", name="Fraud")
        MarketplaceModel.objects.create(
            name="Free Model",
            category=category,
            model_type=MarketplaceModel.ModelType.LOGISTIC_REGRESSION,
            pricing_type=MarketplaceModel.PricingType.FREE,
            is_active=True,
        )
        MarketplaceModel.objects.create(
            name="Paid Model",
            category=category,
            model_type=MarketplaceModel.ModelType.LOGISTIC_REGRESSION,
            pricing_type=MarketplaceModel.PricingType.ONE_TIME,
            is_active=True,
        )

        url = "/api/v2/marketplace/models/search/"
        data = {
            "category": "cat_fraud",
            "pricing_type": "free",
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        for result in response.data["results"]:
            assert result["pricing_type"] == "free"

    def test_search_by_min_accuracy(self, auth_client):
        """Test searching by minimum accuracy."""
        MarketplaceModel.objects.create(
            name="High Accuracy",
            model_type=MarketplaceModel.ModelType.LOGISTIC_REGRESSION,
            accuracy=0.95,
            is_active=True,
        )
        MarketplaceModel.objects.create(
            name="Low Accuracy",
            model_type=MarketplaceModel.ModelType.LOGISTIC_REGRESSION,
            accuracy=0.70,
            is_active=True,
        )

        url = "/api/v2/marketplace/models/search/"
        data = {"min_accuracy": 0.90}

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        for result in response.data["results"]:
            assert result["accuracy"] >= 0.90

    def test_get_model_reviews(self, auth_client, company):
        """Test getting reviews for a model."""
        model = MarketplaceModel.objects.create(
            name="Test Model",
            model_type=MarketplaceModel.ModelType.LOGISTIC_REGRESSION,
            is_active=True,
        )
        Review.objects.create(
            marketplace_model=model,
            reviewer=company,
            rating=4,
            title="Good model",
            comment="Works well",
        )

        url = f"/api/v2/marketplace/models/{model.id}/reviews/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_reviews"] >= 1
        assert "rating_distribution" in response.data

    def test_models_are_read_only(self, auth_client):
        """Test models cannot be created via API."""
        url = "/api/v2/marketplace/models/"
        data = {"name": "New Model", "model_type": "logistic_regression"}

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestDeploymentEndpoints:
    """Tests for deployment operations."""

    def test_create_deployment(self, auth_client, consortium, company):
        """Test deploying a marketplace model."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        model = MarketplaceModel.objects.create(
            name="Test Model",
            model_type=MarketplaceModel.ModelType.LOGISTIC_REGRESSION,
            is_active=True,
        )

        url = "/api/v2/marketplace/deployments/"
        data = {
            "marketplace_model": str(model.id),
            "consortium": str(consortium.id),
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert Deployment.objects.filter(
            marketplace_model=model,
            consortium=consortium,
        ).exists()

    def test_list_deployments_by_consortium(self, auth_client, consortium, company):
        """Test listing deployments by consortium."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        model = MarketplaceModel.objects.create(
            name="Test Model",
            model_type=MarketplaceModel.ModelType.LOGISTIC_REGRESSION,
        )
        Deployment.objects.create(
            marketplace_model=model,
            consortium=consortium,
            deployed_by=company,
        )

        url = f"/api/v2/marketplace/deployments/?consortium_id={consortium.id}"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_list_deployments_by_company(self, auth_client, consortium, company):
        """Test listing deployments by company."""
        model = MarketplaceModel.objects.create(
            name="Test Model",
            model_type=MarketplaceModel.ModelType.LOGISTIC_REGRESSION,
        )
        Deployment.objects.create(
            marketplace_model=model,
            consortium=consortium,
            deployed_by=company,
        )

        url = "/api/v2/marketplace/deployments/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_suspend_deployment(self, auth_client, consortium, company):
        """Test suspending a deployment."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        model = MarketplaceModel.objects.create(
            name="Test Model",
            model_type=MarketplaceModel.ModelType.LOGISTIC_REGRESSION,
        )
        deployment = Deployment.objects.create(
            marketplace_model=model,
            consortium=consortium,
            deployed_by=company,
            status=Deployment.Status.ACTIVE,
        )

        url = f"/api/v2/marketplace/deployments/{deployment.id}/suspend/?consortium_id={consortium.id}"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        deployment.refresh_from_db()
        assert deployment.status == Deployment.Status.SUSPENDED

    def test_activate_deployment(self, auth_client, consortium, company):
        """Test activating a suspended deployment."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        model = MarketplaceModel.objects.create(
            name="Test Model",
            model_type=MarketplaceModel.ModelType.LOGISTIC_REGRESSION,
        )
        deployment = Deployment.objects.create(
            marketplace_model=model,
            consortium=consortium,
            deployed_by=company,
            status=Deployment.Status.SUSPENDED,
        )

        url = f"/api/v2/marketplace/deployments/{deployment.id}/activate/?consortium_id={consortium.id}"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        deployment.refresh_from_db()
        assert deployment.status == Deployment.Status.ACTIVE

    def test_remove_deployment(self, auth_client, consortium, company):
        """Test removing a deployment."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        model = MarketplaceModel.objects.create(
            name="Test Model",
            model_type=MarketplaceModel.ModelType.LOGISTIC_REGRESSION,
        )
        deployment = Deployment.objects.create(
            marketplace_model=model,
            consortium=consortium,
            deployed_by=company,
            status=Deployment.Status.ACTIVE,
        )

        url = f"/api/v2/marketplace/deployments/{deployment.id}/remove/?consortium_id={consortium.id}"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        deployment.refresh_from_db()
        assert deployment.status == Deployment.Status.REMOVED
        assert deployment.removed_at is not None

    def test_cannot_suspend_inactive(self, auth_client, consortium, company):
        """Test cannot suspend non-active deployment."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        model = MarketplaceModel.objects.create(
            name="Test Model",
            model_type=MarketplaceModel.ModelType.LOGISTIC_REGRESSION,
        )
        deployment = Deployment.objects.create(
            marketplace_model=model,
            consortium=consortium,
            deployed_by=company,
            status=Deployment.Status.SUSPENDED,
        )

        url = f"/api/v2/marketplace/deployments/{deployment.id}/suspend/?consortium_id={consortium.id}"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_activate_active(self, auth_client, consortium, company):
        """Test cannot activate already active deployment."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        model = MarketplaceModel.objects.create(
            name="Test Model",
            model_type=MarketplaceModel.ModelType.LOGISTIC_REGRESSION,
        )
        deployment = Deployment.objects.create(
            marketplace_model=model,
            consortium=consortium,
            deployed_by=company,
            status=Deployment.Status.ACTIVE,
        )

        url = f"/api/v2/marketplace/deployments/{deployment.id}/activate/?consortium_id={consortium.id}"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_remove_already_removed(self, auth_client, consortium, company):
        """Test cannot remove already removed deployment."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        model = MarketplaceModel.objects.create(
            name="Test Model",
            model_type=MarketplaceModel.ModelType.LOGISTIC_REGRESSION,
        )
        deployment = Deployment.objects.create(
            marketplace_model=model,
            consortium=consortium,
            deployed_by=company,
            status=Deployment.Status.REMOVED,
        )

        url = f"/api/v2/marketplace/deployments/{deployment.id}/remove/?consortium_id={consortium.id}"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestReviewEndpoints:
    """Tests for review operations."""

    def test_create_review(self, auth_client, company, consortium):
        """Test creating a review."""
        model = MarketplaceModel.objects.create(
            name="Test Model",
            model_type=MarketplaceModel.ModelType.LOGISTIC_REGRESSION,
            is_active=True,
        )
        # Must deploy model before reviewing
        Deployment.objects.create(
            marketplace_model=model,
            consortium=consortium,
            deployed_by=company,
        )

        url = "/api/v2/marketplace/reviews/"
        data = {
            "marketplace_model": str(model.id),
            "rating": 5,
            "title": "Great model",
            "comment": "Works perfectly for our use case",
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["rating"] == 5

    def test_list_my_reviews(self, auth_client, company):
        """Test listing user's own reviews."""
        model = MarketplaceModel.objects.create(
            name="Test Model",
            model_type=MarketplaceModel.ModelType.LOGISTIC_REGRESSION,
        )
        Review.objects.create(
            marketplace_model=model,
            reviewer=company,
            rating=4,
        )

        url = "/api/v2/marketplace/reviews/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_update_review(self, auth_client, company):
        """Test updating a review."""
        model = MarketplaceModel.objects.create(
            name="Test Model",
            model_type=MarketplaceModel.ModelType.LOGISTIC_REGRESSION,
        )
        review = Review.objects.create(
            marketplace_model=model,
            reviewer=company,
            rating=3,
            comment="Okay",
        )

        url = f"/api/v2/marketplace/reviews/{review.id}/"
        data = {"rating": 4, "comment": "Better than expected"}

        response = auth_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        review.refresh_from_db()
        assert review.rating == 4

    def test_delete_review(self, auth_client, company):
        """Test deleting a review."""
        model = MarketplaceModel.objects.create(
            name="Test Model",
            model_type=MarketplaceModel.ModelType.LOGISTIC_REGRESSION,
        )
        review = Review.objects.create(
            marketplace_model=model,
            reviewer=company,
            rating=3,
        )

        url = f"/api/v2/marketplace/reviews/{review.id}/"

        response = auth_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Review.objects.filter(id=review.id).exists()

    def test_mark_review_helpful(self, auth_client, company):
        """Test marking a review as helpful."""
        model = MarketplaceModel.objects.create(
            name="Test Model",
            model_type=MarketplaceModel.ModelType.LOGISTIC_REGRESSION,
        )
        review = Review.objects.create(
            marketplace_model=model,
            reviewer=company,
            rating=5,
            helpful_count=0,
        )

        url = f"/api/v2/marketplace/reviews/{review.id}/helpful/"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["helpful_count"] == 1


@pytest.mark.django_db
class TestMarketplaceModels:
    """Tests for marketplace model methods and properties."""

    def test_category_str(self):
        """Test category string representation."""
        category = Category.objects.create(
            id="cat_test",
            name="Test Category",
        )

        assert "Test Category" in str(category)

    def test_category_model_count(self):
        """Test category model count property."""
        category = Category.objects.create(id="cat_test", name="Test")
        MarketplaceModel.objects.create(
            name="Model 1",
            category=category,
            model_type=MarketplaceModel.ModelType.LINEAR_REGRESSION,
            is_active=True,
        )
        MarketplaceModel.objects.create(
            name="Model 2",
            category=category,
            model_type=MarketplaceModel.ModelType.LINEAR_REGRESSION,
            is_active=True,
        )
        MarketplaceModel.objects.create(
            name="Inactive",
            category=category,
            model_type=MarketplaceModel.ModelType.LINEAR_REGRESSION,
            is_active=False,
        )

        assert category.model_count == 2  # Only active

    def test_model_str(self):
        """Test model string representation."""
        model = MarketplaceModel.objects.create(
            name="Test Model",
            model_type=MarketplaceModel.ModelType.LINEAR_REGRESSION,
            version="2.0.0",
        )

        assert "Test Model" in str(model)
        assert "v2.0.0" in str(model)

    def test_model_rating(self, company, other_company):
        """Test model rating property."""
        model = MarketplaceModel.objects.create(
            name="Test Model",
            model_type=MarketplaceModel.ModelType.LINEAR_REGRESSION,
        )
        Review.objects.create(marketplace_model=model, reviewer=company, rating=5)
        Review.objects.create(marketplace_model=model, reviewer=other_company, rating=3)

        assert model.rating == 4.0

    def test_model_rating_no_reviews(self):
        """Test model rating with no reviews."""
        model = MarketplaceModel.objects.create(
            name="Test Model",
            model_type=MarketplaceModel.ModelType.LINEAR_REGRESSION,
        )

        assert model.rating == 0

    def test_model_rating_count(self, company, other_company):
        """Test model rating count property."""
        model = MarketplaceModel.objects.create(
            name="Test Model",
            model_type=MarketplaceModel.ModelType.LINEAR_REGRESSION,
        )
        Review.objects.create(marketplace_model=model, reviewer=company, rating=5)
        Review.objects.create(marketplace_model=model, reviewer=other_company, rating=3)

        assert model.rating_count == 2

    def test_model_industry(self):
        """Test model industry property."""
        category = Category.objects.create(id="cat_fraud", name="Fraud")
        model = MarketplaceModel.objects.create(
            name="Test Model",
            category=category,
            model_type=MarketplaceModel.ModelType.LINEAR_REGRESSION,
        )

        assert model.industry == "cat_fraud"

    def test_deployment_str(self, consortium, company):
        """Test deployment string representation."""
        model = MarketplaceModel.objects.create(
            name="Test Model",
            model_type=MarketplaceModel.ModelType.LINEAR_REGRESSION,
        )
        deployment = Deployment.objects.create(
            marketplace_model=model,
            consortium=consortium,
            deployed_by=company,
        )

        assert "Test Model" in str(deployment)
        assert consortium.name in str(deployment)

    def test_review_str(self, company):
        """Test review string representation."""
        model = MarketplaceModel.objects.create(
            name="Test Model",
            model_type=MarketplaceModel.ModelType.LINEAR_REGRESSION,
        )
        review = Review.objects.create(
            marketplace_model=model,
            reviewer=company,
            rating=5,
        )

        assert company.name in str(review)
        assert "5/5" in str(review)
        assert "Test Model" in str(review)

"""
Explainability module tests for Xcapit FHE-ML Platform.
"""

import pytest
from rest_framework import status

from apps.explainability.models import (
    ExplanationRequest,
    FeatureImportance,
    ModelInsight,
)


@pytest.fixture
def explanation_request(db, company, consortium, ml_model):
    """Create a test explanation request."""
    return ExplanationRequest.objects.create(
        consortium=consortium,
        requester=company,
        model=ml_model,
        explanation_type=ExplanationRequest.ExplanationType.FEATURE_IMPORTANCE,
        input_data={"features": [1.0, 2.0, 3.0]},
        status=ExplanationRequest.Status.PENDING,
    )


@pytest.fixture
def feature_importance(db, consortium, ml_model):
    """Create a test feature importance."""
    return FeatureImportance.objects.create(
        consortium=consortium,
        model=ml_model,
        feature_name="transaction_amount",
        importance_score=0.35,
        importance_rank=1,
        computation_method="model_native",
        std_deviation=0.02,
    )


@pytest.fixture
def model_insight(db, consortium):
    """Create a test model insight."""
    return ModelInsight.objects.create(
        consortium=consortium,
        insight_type=ModelInsight.InsightType.PERFORMANCE,
        title="Model accuracy trending down",
        description="The model's accuracy has decreased by 3% over the last week.",
        severity="warning",
        data={"accuracy_trend": [0.92, 0.91, 0.90, 0.89]},
        recommendations=["Retrain with recent data", "Review feature drift"],
        is_active=True,
    )


@pytest.mark.django_db
class TestExplanationRequestModel:
    """Tests for ExplanationRequest model."""

    def test_create_request(self, explanation_request):
        """Test creating an explanation request."""
        assert explanation_request.id is not None
        assert explanation_request.status == ExplanationRequest.Status.PENDING

    def test_mark_completed(self, explanation_request):
        """Test marking request as completed."""
        explanation = {
            "feature_importance": {"amount": 0.35, "frequency": 0.25},
            "top_features": ["amount", "frequency"],
        }

        explanation_request.mark_completed(explanation)
        explanation_request.refresh_from_db()

        assert explanation_request.status == ExplanationRequest.Status.COMPLETED
        assert explanation_request.explanation == explanation
        assert explanation_request.completed_at is not None

    def test_mark_failed(self, explanation_request):
        """Test marking request as failed."""
        explanation_request.mark_failed("Insufficient data for SHAP analysis")
        explanation_request.refresh_from_db()

        assert explanation_request.status == ExplanationRequest.Status.FAILED
        assert "Insufficient data" in explanation_request.error_message
        assert explanation_request.completed_at is not None

    def test_all_explanation_types(self, company, consortium):
        """Test all explanation types can be created."""
        for etype in ExplanationRequest.ExplanationType:
            req = ExplanationRequest.objects.create(
                consortium=consortium,
                requester=company,
                explanation_type=etype,
            )
            assert req.explanation_type == etype


@pytest.mark.django_db
class TestFeatureImportanceModel:
    """Tests for FeatureImportance model."""

    def test_create_feature_importance(self, feature_importance):
        """Test creating a feature importance record."""
        assert feature_importance.id is not None
        assert feature_importance.feature_name == "transaction_amount"
        assert feature_importance.importance_rank == 1

    def test_ordering_by_rank(self, consortium, ml_model):
        """Test feature importances are ordered by rank."""
        FeatureImportance.objects.create(
            consortium=consortium,
            model=ml_model,
            feature_name="feature_a",
            importance_score=0.10,
            importance_rank=3,
        )
        FeatureImportance.objects.create(
            consortium=consortium,
            model=ml_model,
            feature_name="feature_b",
            importance_score=0.50,
            importance_rank=1,
        )
        FeatureImportance.objects.create(
            consortium=consortium,
            model=ml_model,
            feature_name="feature_c",
            importance_score=0.25,
            importance_rank=2,
        )

        features = list(FeatureImportance.objects.filter(consortium=consortium))
        assert features[0].importance_rank == 1
        assert features[1].importance_rank == 2
        assert features[2].importance_rank == 3


@pytest.mark.django_db
class TestModelInsightModel:
    """Tests for ModelInsight model."""

    def test_create_insight(self, model_insight):
        """Test creating a model insight."""
        assert model_insight.id is not None
        assert model_insight.severity == "warning"
        assert model_insight.is_active is True

    def test_acknowledge_insight(self, model_insight, user):
        """Test acknowledging an insight."""
        model_insight.acknowledge(user)
        model_insight.refresh_from_db()

        assert model_insight.acknowledged is True
        assert model_insight.acknowledged_by == user
        assert model_insight.acknowledged_at is not None

    def test_insight_types(self, consortium):
        """Test all insight types can be created."""
        for itype in ModelInsight.InsightType:
            insight = ModelInsight.objects.create(
                consortium=consortium,
                insight_type=itype,
                title=f"Test {itype.label}",
                description="Test description",
            )
            assert insight.insight_type == itype


@pytest.mark.django_db
class TestExplanationRequestEndpoints:
    """Tests for explanation request API endpoints."""

    def test_list_requests(self, auth_client, explanation_request):
        """Test listing explanation requests."""
        url = "/api/v2/explainability/requests/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_create_request(self, auth_client, consortium, ml_model):
        """Test creating an explanation request."""
        url = "/api/v2/explainability/requests/"
        data = {
            "consortium": str(consortium.id),
            "model": str(ml_model.id),
            "explanation_type": "shap",
            "input_data": {"sample": [1.0, 2.0, 3.0]},
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        # Request is processed synchronously, so status is completed
        assert response.data["status"] == "completed"

    def test_get_request_detail(self, auth_client, explanation_request):
        """Test getting request detail."""
        url = f"/api/v2/explainability/requests/{explanation_request.id}/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestFeatureImportanceEndpoints:
    """Tests for feature importance API endpoints."""

    def test_list_feature_importances(self, auth_client, feature_importance):
        """Test listing feature importances."""
        url = "/api/v2/explainability/features/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_filter_by_consortium(self, auth_client, feature_importance, consortium):
        """Test filtering feature importances by consortium."""
        url = f"/api/v2/explainability/features/?consortium={consortium.id}"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestModelInsightEndpoints:
    """Tests for model insight API endpoints."""

    def test_list_insights(self, auth_client, model_insight):
        """Test listing model insights."""
        url = "/api/v2/explainability/insights/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_acknowledge_insight(self, auth_client, model_insight):
        """Test acknowledging an insight."""
        url = f"/api/v2/explainability/insights/{model_insight.id}/acknowledge/"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        model_insight.refresh_from_db()
        assert model_insight.acknowledged is True


@pytest.mark.django_db
class TestDataIsolation:
    """Tests for data isolation between companies."""

    def test_cannot_see_other_company_requests(
        self, auth_client, other_company, consortium
    ):
        """Test user cannot see another company's explanation requests."""
        ExplanationRequest.objects.create(
            consortium=consortium,
            requester=other_company,
            explanation_type=ExplanationRequest.ExplanationType.SHAP,
        )

        url = "/api/v2/explainability/requests/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        for req in response.data:
            assert req.get("requester") != str(other_company.id)

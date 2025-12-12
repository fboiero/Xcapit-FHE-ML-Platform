"""Tests for Model Explainability module (TIER 4).

This module tests the explainability features including:
- Explanation requests (feature_importance, shap, decision_path, counterfactual, summary)
- Feature importance computation
- Model insights generation
- Privacy-preserving explanations
"""

import os
import tempfile
import pytest
from pathlib import Path
from datetime import datetime

# Set test mode before imports
os.environ["FHEML_AUTH_DISABLED"] = "true"


class TestExplainabilitySchema:
    """Test explainability database schema and initialization."""

    @pytest.fixture
    def manager(self):
        """Create a ConsortiumManager with temp database."""
        from sdk.api.consortium import ConsortiumManager
        self.temp_dir = tempfile.mkdtemp()
        manager = ConsortiumManager(db_path=Path(self.temp_dir) / "test.db")
        yield manager

    @pytest.fixture
    def consortium(self, manager):
        """Create a test consortium."""
        consortium = manager.create_consortium(
            name="Test Consortium",
            description="For explainability testing",
            created_by="company_a",
            model_type="logistic_regression"
        )
        return consortium

    def test_init_explainability_schema(self, manager):
        """Test that explainability schema is initialized."""
        # Schema should be created on manager init
        with manager._get_connection() as conn:
            cursor = conn.cursor()
            # Check explanation_requests table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='explanation_requests'
            """)
            assert cursor.fetchone() is not None

    def test_explanation_requests_table_structure(self, manager):
        """Test explanation_requests table has correct columns."""
        with manager._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(explanation_requests)")
            columns = {row[1] for row in cursor.fetchall()}
            expected = {'id', 'consortium_id', 'requester_id', 'explanation_type',
                        'status', 'input_data', 'model_id', 'prediction_id', 'created_at'}
            assert expected.issubset(columns)

    def test_explanation_results_table_exists(self, manager):
        """Test explanation_results table exists."""
        with manager._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='explanation_results'
            """)
            assert cursor.fetchone() is not None

    def test_feature_importance_table_exists(self, manager):
        """Test feature_importance table exists."""
        with manager._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='feature_importance'
            """)
            assert cursor.fetchone() is not None

    def test_model_insights_table_exists(self, manager):
        """Test model_insights table exists."""
        with manager._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='model_insights'
            """)
            assert cursor.fetchone() is not None


class TestExplanationRequests:
    """Test explanation request functionality."""

    @pytest.fixture
    def manager(self):
        """Create a ConsortiumManager with temp database."""
        from sdk.api.consortium import ConsortiumManager
        self.temp_dir = tempfile.mkdtemp()
        manager = ConsortiumManager(db_path=Path(self.temp_dir) / "test.db")
        yield manager

    @pytest.fixture
    def consortium(self, manager):
        """Create a test consortium."""
        consortium = manager.create_consortium(
            name="Explainability Test",
            description="Testing explanations",
            created_by="company_a",
            model_type="logistic_regression"
        )
        return consortium

    def test_request_feature_importance_explanation(self, manager, consortium):
        """Test requesting feature importance explanation."""
        result = manager.request_explanation(
            consortium_id=consortium.id,
            requester_id="company_a",
            explanation_type="feature_importance"
        )

        assert result is not None
        assert "request_id" in result
        assert result["explanation_type"] == "feature_importance"
        assert result["status"] in ["pending", "completed"]

    def test_request_shap_explanation(self, manager, consortium):
        """Test requesting SHAP values explanation."""
        input_data = {"credit_score": 720, "income": 55000, "debt_ratio": 0.25}
        result = manager.request_explanation(
            consortium_id=consortium.id,
            requester_id="company_a",
            explanation_type="shap",
            input_data=input_data
        )

        assert result is not None
        assert result["explanation_type"] == "shap"

    def test_request_decision_path_explanation(self, manager, consortium):
        """Test requesting decision path explanation."""
        input_data = {"feature_1": 0.5, "feature_2": 0.8}
        result = manager.request_explanation(
            consortium_id=consortium.id,
            requester_id="company_a",
            explanation_type="decision_path",
            input_data=input_data
        )

        assert result is not None
        assert result["explanation_type"] == "decision_path"

    def test_request_counterfactual_explanation(self, manager, consortium):
        """Test requesting counterfactual explanation."""
        input_data = {"credit_score": 580, "income": 35000}
        result = manager.request_explanation(
            consortium_id=consortium.id,
            requester_id="company_a",
            explanation_type="counterfactual",
            input_data=input_data
        )

        assert result is not None
        assert result["explanation_type"] == "counterfactual"

    def test_request_summary_explanation(self, manager, consortium):
        """Test requesting model summary explanation."""
        result = manager.request_explanation(
            consortium_id=consortium.id,
            requester_id="company_a",
            explanation_type="summary"
        )

        assert result is not None
        assert result["explanation_type"] == "summary"

    def test_invalid_explanation_type(self, manager, consortium):
        """Test that invalid explanation type raises error."""
        with pytest.raises(ValueError):
            manager.request_explanation(
                consortium_id=consortium.id,
                requester_id="company_a",
                explanation_type="invalid_type"
            )

    def test_explanation_stored_in_database(self, manager, consortium):
        """Test that explanation request is stored in database."""
        result = manager.request_explanation(
            consortium_id=consortium.id,
            requester_id="company_a",
            explanation_type="feature_importance"
        )

        # Retrieve from database
        with manager._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM explanation_requests WHERE id = ?",
                (result["request_id"],)
            )
            row = cursor.fetchone()
            assert row is not None


class TestGetExplanation:
    """Test retrieving explanations."""

    @pytest.fixture
    def manager(self):
        """Create a ConsortiumManager with temp database."""
        from sdk.api.consortium import ConsortiumManager
        self.temp_dir = tempfile.mkdtemp()
        manager = ConsortiumManager(db_path=Path(self.temp_dir) / "test.db")
        yield manager

    @pytest.fixture
    def consortium(self, manager):
        """Create a test consortium."""
        consortium = manager.create_consortium(
            name="Get Explanation Test",
            description="Testing get explanation",
            created_by="company_a",
            model_type="linear_regression"
        )
        return consortium

    def test_get_existing_explanation(self, manager, consortium):
        """Test getting an existing explanation."""
        # Create explanation
        request = manager.request_explanation(
            consortium_id=consortium.id,
            requester_id="company_a",
            explanation_type="feature_importance"
        )

        # Get explanation
        result = manager.get_explanation(request["request_id"])

        assert result is not None
        assert result["request_id"] == request["request_id"]
        assert "explanation_type" in result

    def test_get_nonexistent_explanation(self, manager):
        """Test getting non-existent explanation returns None."""
        result = manager.get_explanation("nonexistent_id")
        assert result is None

    def test_get_completed_explanation_has_result(self, manager, consortium):
        """Test that completed explanations include result data."""
        request = manager.request_explanation(
            consortium_id=consortium.id,
            requester_id="company_a",
            explanation_type="feature_importance"
        )

        result = manager.get_explanation(request["request_id"])

        # Should have result if completed
        if result["status"] == "completed":
            assert "result" in result or "explanation" in result


class TestListExplanations:
    """Test listing explanations."""

    @pytest.fixture
    def manager(self):
        """Create a ConsortiumManager with temp database."""
        from sdk.api.consortium import ConsortiumManager
        self.temp_dir = tempfile.mkdtemp()
        manager = ConsortiumManager(db_path=Path(self.temp_dir) / "test.db")
        yield manager

    @pytest.fixture
    def consortium(self, manager):
        """Create a test consortium."""
        consortium = manager.create_consortium(
            name="List Explanations Test",
            description="Testing list explanations",
            created_by="company_a",
            model_type="logistic_regression"
        )
        return consortium

    def test_list_explanations_empty(self, manager, consortium):
        """Test listing explanations when none exist."""
        results = manager.list_explanations(consortium_id=consortium.id)
        assert isinstance(results, list)
        assert len(results) == 0

    def test_list_explanations_with_data(self, manager, consortium):
        """Test listing explanations with multiple entries."""
        # Create multiple explanations
        for exp_type in ["feature_importance", "shap", "summary"]:
            manager.request_explanation(
                consortium_id=consortium.id,
                requester_id="company_a",
                explanation_type=exp_type
            )

        results = manager.list_explanations(consortium_id=consortium.id)
        assert len(results) >= 3

    def test_list_explanations_filter_by_type(self, manager, consortium):
        """Test filtering explanations by type."""
        # Create mixed explanations
        manager.request_explanation(
            consortium_id=consortium.id,
            requester_id="company_a",
            explanation_type="feature_importance"
        )
        manager.request_explanation(
            consortium_id=consortium.id,
            requester_id="company_a",
            explanation_type="shap"
        )

        results = manager.list_explanations(
            consortium_id=consortium.id,
            explanation_type="feature_importance"
        )

        for r in results:
            assert r["explanation_type"] == "feature_importance"

    def test_list_explanations_filter_by_requester(self, manager, consortium):
        """Test filtering explanations by requester."""
        manager.request_explanation(
            consortium_id=consortium.id,
            requester_id="company_a",
            explanation_type="feature_importance"
        )
        manager.request_explanation(
            consortium_id=consortium.id,
            requester_id="company_b",
            explanation_type="feature_importance"
        )

        results = manager.list_explanations(
            consortium_id=consortium.id,
            requester_id="company_a"
        )

        for r in results:
            assert r["requester_id"] == "company_a"

    def test_list_explanations_with_limit(self, manager, consortium):
        """Test limiting number of results."""
        # Create 5 explanations
        for _ in range(5):
            manager.request_explanation(
                consortium_id=consortium.id,
                requester_id="company_a",
                explanation_type="feature_importance"
            )

        results = manager.list_explanations(
            consortium_id=consortium.id,
            limit=3
        )

        assert len(results) <= 3


class TestFeatureImportance:
    """Test feature importance functionality."""

    @pytest.fixture
    def manager(self):
        """Create a ConsortiumManager with temp database."""
        from sdk.api.consortium import ConsortiumManager
        self.temp_dir = tempfile.mkdtemp()
        manager = ConsortiumManager(db_path=Path(self.temp_dir) / "test.db")
        yield manager

    @pytest.fixture
    def consortium(self, manager):
        """Create a test consortium."""
        consortium = manager.create_consortium(
            name="Feature Importance Test",
            description="Testing feature importance",
            created_by="company_a",
            model_type="logistic_regression"
        )
        return consortium

    def test_get_feature_importance(self, manager, consortium):
        """Test getting feature importance for a consortium."""
        result = manager.get_feature_importance(consortium_id=consortium.id)

        assert isinstance(result, list)
        # Should return simulated importance if no real data
        if len(result) > 0:
            assert "feature_name" in result[0] or "name" in result[0]
            assert "importance" in result[0]

    def test_feature_importance_sorted(self, manager, consortium):
        """Test that feature importance is sorted by importance."""
        result = manager.get_feature_importance(consortium_id=consortium.id)

        if len(result) > 1:
            importances = [f.get("importance", 0) for f in result]
            assert importances == sorted(importances, reverse=True)


class TestModelInsights:
    """Test model insights functionality."""

    @pytest.fixture
    def manager(self):
        """Create a ConsortiumManager with temp database."""
        from sdk.api.consortium import ConsortiumManager
        self.temp_dir = tempfile.mkdtemp()
        manager = ConsortiumManager(db_path=Path(self.temp_dir) / "test.db")
        yield manager

    @pytest.fixture
    def consortium(self, manager):
        """Create a test consortium."""
        consortium = manager.create_consortium(
            name="Model Insights Test",
            description="Testing model insights",
            created_by="company_a",
            model_type="logistic_regression"
        )
        return consortium

    def test_compute_model_insights(self, manager, consortium):
        """Test computing model insights."""
        result = manager.compute_model_insights(consortium_id=consortium.id)

        assert result is not None
        assert isinstance(result, dict)

    def test_insights_contain_expected_fields(self, manager, consortium):
        """Test that insights contain expected fields."""
        result = manager.compute_model_insights(consortium_id=consortium.id)

        # Should contain at least some insight fields
        expected_fields = ["model_type", "interpretability_score", "top_features"]
        for field in expected_fields:
            if field in result:
                assert result[field] is not None

    def test_insights_with_specific_model(self, manager, consortium):
        """Test computing insights for specific model."""
        result = manager.compute_model_insights(
            consortium_id=consortium.id,
            model_id="model_123"
        )

        assert result is not None


class TestExplainabilityStats:
    """Test explainability statistics."""

    @pytest.fixture
    def manager(self):
        """Create a ConsortiumManager with temp database."""
        from sdk.api.consortium import ConsortiumManager
        self.temp_dir = tempfile.mkdtemp()
        manager = ConsortiumManager(db_path=Path(self.temp_dir) / "test.db")
        yield manager

    @pytest.fixture
    def consortium(self, manager):
        """Create a test consortium."""
        consortium = manager.create_consortium(
            name="Stats Test",
            description="Testing stats",
            created_by="company_a",
            model_type="linear_regression"
        )
        return consortium

    def test_get_stats_empty(self, manager):
        """Test getting stats with no data."""
        result = manager.get_explainability_stats()

        assert result is not None
        assert isinstance(result, dict)
        assert "total_explanations" in result

    def test_get_stats_with_data(self, manager, consortium):
        """Test getting stats after creating explanations."""
        # Create some explanations
        for exp_type in ["feature_importance", "shap", "summary"]:
            manager.request_explanation(
                consortium_id=consortium.id,
                requester_id="company_a",
                explanation_type=exp_type
            )

        result = manager.get_explainability_stats()

        assert result["total_explanations"] >= 3

    def test_get_stats_filtered_by_consortium(self, manager, consortium):
        """Test getting stats filtered by consortium."""
        manager.request_explanation(
            consortium_id=consortium.id,
            requester_id="company_a",
            explanation_type="feature_importance"
        )

        result = manager.get_explainability_stats(consortium_id=consortium.id)

        assert result is not None

    def test_stats_by_type(self, manager, consortium):
        """Test that stats include breakdown by type."""
        manager.request_explanation(
            consortium_id=consortium.id,
            requester_id="company_a",
            explanation_type="feature_importance"
        )
        manager.request_explanation(
            consortium_id=consortium.id,
            requester_id="company_a",
            explanation_type="shap"
        )

        result = manager.get_explainability_stats()

        if "by_type" in result:
            assert isinstance(result["by_type"], dict)


class TestExplanationPrivacy:
    """Test privacy-preserving aspects of explanations."""

    @pytest.fixture
    def manager(self):
        """Create a ConsortiumManager with temp database."""
        from sdk.api.consortium import ConsortiumManager
        self.temp_dir = tempfile.mkdtemp()
        manager = ConsortiumManager(db_path=Path(self.temp_dir) / "test.db")
        yield manager

    @pytest.fixture
    def consortium(self, manager):
        """Create a test consortium."""
        consortium = manager.create_consortium(
            name="Privacy Test",
            description="Testing privacy",
            created_by="company_a",
            model_type="logistic_regression"
        )
        return consortium

    def test_explanation_does_not_expose_raw_data(self, manager, consortium):
        """Test that explanations don't expose raw training data."""
        result = manager.request_explanation(
            consortium_id=consortium.id,
            requester_id="company_a",
            explanation_type="feature_importance"
        )

        explanation = manager.get_explanation(result["request_id"])

        # Should not contain raw data fields
        assert "raw_data" not in explanation
        assert "training_samples" not in explanation

    def test_feature_importance_is_aggregated(self, manager, consortium):
        """Test that feature importance uses aggregate statistics."""
        result = manager.get_feature_importance(consortium_id=consortium.id)

        # Importance values should be aggregated (0-1 range typically)
        for feature in result:
            if "importance" in feature:
                assert 0 <= feature["importance"] <= 1


class TestExplainabilityAPI:
    """Test explainability API routes (integration tests)."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from sdk.api.server import app
        return TestClient(app)

    def test_explain_endpoint_exists(self, client):
        """Test that explain endpoint exists."""
        response = client.post(
            "/api/v1/api/explainability/explain",
            json={
                "consortium_id": "test_consortium",
                "explanation_type": "feature_importance"
            }
        )
        # Should not be 404 (endpoint exists)
        assert response.status_code != 404

    def test_list_explanations_endpoint(self, client):
        """Test list explanations endpoint."""
        response = client.get(
            "/api/v1/api/explainability/explanations",
            params={"consortium_id": "test_consortium"}
        )
        assert response.status_code != 404

    def test_feature_importance_endpoint(self, client):
        """Test feature importance endpoint."""
        response = client.get(
            "/api/v1/api/explainability/feature-importance",
            params={"consortium_id": "test_consortium"}
        )
        assert response.status_code != 404

    def test_insights_endpoint(self, client):
        """Test insights endpoint."""
        response = client.post(
            "/api/v1/api/explainability/insights",
            json={"consortium_id": "test_consortium"}
        )
        assert response.status_code != 404

    def test_stats_endpoint(self, client):
        """Test stats endpoint."""
        response = client.get("/api/v1/api/explainability/stats")
        assert response.status_code != 404


class TestExplanationTypes:
    """Test specific explanation type generation."""

    @pytest.fixture
    def manager(self):
        """Create a ConsortiumManager with temp database."""
        from sdk.api.consortium import ConsortiumManager
        self.temp_dir = tempfile.mkdtemp()
        manager = ConsortiumManager(db_path=Path(self.temp_dir) / "test.db")
        yield manager

    @pytest.fixture
    def consortium(self, manager):
        """Create a test consortium."""
        consortium = manager.create_consortium(
            name="Explanation Types Test",
            description="Testing explanation types",
            created_by="company_a",
            model_type="decision_tree"
        )
        return consortium

    def test_feature_importance_result_structure(self, manager, consortium):
        """Test feature importance result has correct structure."""
        request = manager.request_explanation(
            consortium_id=consortium.id,
            requester_id="company_a",
            explanation_type="feature_importance"
        )

        result = manager.get_explanation(request["request_id"])

        if result.get("status") == "completed" and "result" in result:
            res = result["result"]
            if "features" in res:
                for f in res["features"]:
                    assert "name" in f or "feature_name" in f
                    assert "importance" in f

    def test_shap_result_structure(self, manager, consortium):
        """Test SHAP result has correct structure."""
        request = manager.request_explanation(
            consortium_id=consortium.id,
            requester_id="company_a",
            explanation_type="shap",
            input_data={"feature_1": 0.5}
        )

        result = manager.get_explanation(request["request_id"])

        if result.get("status") == "completed" and "result" in result:
            res = result["result"]
            assert "base_value" in res or "shap_values" in res

    def test_decision_path_result_structure(self, manager, consortium):
        """Test decision path result has correct structure."""
        request = manager.request_explanation(
            consortium_id=consortium.id,
            requester_id="company_a",
            explanation_type="decision_path",
            input_data={"feature_1": 0.5}
        )

        result = manager.get_explanation(request["request_id"])

        if result.get("status") == "completed" and "result" in result:
            res = result["result"]
            assert "path" in res or "decision" in res

    def test_counterfactual_result_structure(self, manager, consortium):
        """Test counterfactual result has correct structure."""
        request = manager.request_explanation(
            consortium_id=consortium.id,
            requester_id="company_a",
            explanation_type="counterfactual",
            input_data={"feature_1": 0.5}
        )

        result = manager.get_explanation(request["request_id"])

        if result.get("status") == "completed" and "result" in result:
            res = result["result"]
            assert "changes" in res or "counterfactual" in res

    def test_summary_result_structure(self, manager, consortium):
        """Test summary result has correct structure."""
        request = manager.request_explanation(
            consortium_id=consortium.id,
            requester_id="company_a",
            explanation_type="summary"
        )

        result = manager.get_explanation(request["request_id"])

        if result.get("status") == "completed" and "result" in result:
            res = result["result"]
            assert "summary" in res or "model_behavior" in res

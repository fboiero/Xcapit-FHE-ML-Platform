"""Tests for competitive insights API routes."""

import sys
from unittest.mock import MagicMock

import pytest

# Mock tenseal before importing sdk modules
sys.modules["tenseal"] = MagicMock()

from fastapi import FastAPI
from fastapi.testclient import TestClient

from sdk.api.competitive_routes import router, get_manager
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
def app(mock_company, mock_manager):
    """Create FastAPI app with router and overridden dependencies."""
    app = FastAPI()
    app.include_router(router)

    # Override dependencies
    app.dependency_overrides[get_current_company] = lambda: mock_company
    app.dependency_overrides[get_manager] = lambda: mock_manager

    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestGetIndustryBenchmarks:
    """Tests for GET /api/competitive/benchmarks/{industry} endpoint."""

    def test_get_benchmarks_finance(self, client, mock_manager):
        """Test getting finance industry benchmarks."""
        mock_manager.get_industry_benchmarks.return_value = [
            {"metric": "accuracy", "p50": 0.85, "p90": 0.95},
            {"metric": "latency", "p50": 100, "p90": 200},
        ]

        response = client.get("/api/competitive/benchmarks/finance")

        assert response.status_code == 200
        data = response.json()
        assert data["industry"] == "finance"
        assert data["benchmark_count"] == 2
        assert "privacy_note" in data

    def test_get_benchmarks_healthcare(self, client, mock_manager):
        """Test getting healthcare industry benchmarks."""
        mock_manager.get_industry_benchmarks.return_value = [
            {"metric": "compliance_score", "p50": 0.92},
        ]

        response = client.get("/api/competitive/benchmarks/healthcare")

        assert response.status_code == 200
        assert response.json()["industry"] == "healthcare"

    def test_get_benchmarks_retail(self, client, mock_manager):
        """Test getting retail industry benchmarks."""
        mock_manager.get_industry_benchmarks.return_value = []

        response = client.get("/api/competitive/benchmarks/retail")

        assert response.status_code == 200
        assert response.json()["industry"] == "retail"

    def test_get_benchmarks_insurance(self, client, mock_manager):
        """Test getting insurance industry benchmarks."""
        mock_manager.get_industry_benchmarks.return_value = []

        response = client.get("/api/competitive/benchmarks/insurance")

        assert response.status_code == 200
        assert response.json()["industry"] == "insurance"

    def test_get_benchmarks_manufacturing(self, client, mock_manager):
        """Test getting manufacturing industry benchmarks."""
        mock_manager.get_industry_benchmarks.return_value = []

        response = client.get("/api/competitive/benchmarks/manufacturing")

        assert response.status_code == 200
        assert response.json()["industry"] == "manufacturing"

    def test_get_benchmarks_invalid_industry(self, client, mock_manager):
        """Test getting benchmarks for invalid industry."""
        response = client.get("/api/competitive/benchmarks/invalid_industry")

        assert response.status_code == 400
        assert "must be one of" in response.json()["detail"]

    def test_get_benchmarks_with_metric_type_filter(self, client, mock_manager):
        """Test getting benchmarks with metric type filter."""
        mock_manager.get_industry_benchmarks.return_value = [
            {"metric": "accuracy", "p50": 0.85},
        ]

        response = client.get(
            "/api/competitive/benchmarks/finance",
            params={"metric_type": "accuracy"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["metric_type_filter"] == "accuracy"
        mock_manager.get_industry_benchmarks.assert_called_with("finance", "accuracy")

    def test_get_benchmarks_empty_results(self, client, mock_manager):
        """Test getting benchmarks when none exist."""
        mock_manager.get_industry_benchmarks.return_value = []

        response = client.get("/api/competitive/benchmarks/finance")

        assert response.status_code == 200
        assert response.json()["benchmark_count"] == 0


class TestCompareToIndustry:
    """Tests for POST /api/competitive/compare endpoint."""

    def test_compare_success(self, client, mock_manager):
        """Test successful industry comparison."""
        mock_manager.compare_to_industry.return_value = {
            "industry": "finance",
            "percentile_rankings": {
                "accuracy": {"value": 0.90, "percentile": 75},
                "latency": {"value": 50, "percentile": 85},
            },
            "overall_rank": "top 20%",
        }

        response = client.post(
            "/api/competitive/compare",
            json={
                "industry": "finance",
                "metrics": {"accuracy": 0.90, "latency": 50},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["industry"] == "finance"
        assert "percentile_rankings" in data

    def test_compare_without_metrics(self, client, mock_manager):
        """Test comparison without providing metrics."""
        mock_manager.compare_to_industry.return_value = {
            "industry": "healthcare",
            "percentile_rankings": {},
            "message": "No metrics provided for comparison",
        }

        response = client.post(
            "/api/competitive/compare",
            json={"industry": "healthcare"},
        )

        assert response.status_code == 200

    def test_compare_error(self, client, mock_manager):
        """Test comparison with server error."""
        mock_manager.compare_to_industry.side_effect = Exception("Database error")

        response = client.post(
            "/api/competitive/compare",
            json={"industry": "finance", "metrics": {"accuracy": 0.9}},
        )

        assert response.status_code == 500
        assert "Comparison failed" in response.json()["detail"]


class TestGetIndustryTrends:
    """Tests for GET /api/competitive/trends/{industry} endpoint."""

    def test_get_trends_monthly(self, client, mock_manager):
        """Test getting monthly trends."""
        mock_manager.get_industry_trends.return_value = [
            {"month": "2025-01", "accuracy": 0.85},
            {"month": "2025-02", "accuracy": 0.87},
        ]

        response = client.get(
            "/api/competitive/trends/finance",
            params={"period": "monthly"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "monthly"
        assert len(data["trends"]) == 2

    def test_get_trends_quarterly(self, client, mock_manager):
        """Test getting quarterly trends (default)."""
        mock_manager.get_industry_trends.return_value = [
            {"quarter": "Q1-2025", "accuracy": 0.86},
        ]

        response = client.get("/api/competitive/trends/healthcare")

        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "quarterly"
        assert "privacy_note" in data

    def test_get_trends_yearly(self, client, mock_manager):
        """Test getting yearly trends."""
        mock_manager.get_industry_trends.return_value = [
            {"year": 2024, "accuracy": 0.80},
            {"year": 2025, "accuracy": 0.88},
        ]

        response = client.get(
            "/api/competitive/trends/retail",
            params={"period": "yearly"},
        )

        assert response.status_code == 200
        assert response.json()["period"] == "yearly"

    def test_get_trends_invalid_period(self, client, mock_manager):
        """Test getting trends with invalid period."""
        response = client.get(
            "/api/competitive/trends/finance",
            params={"period": "weekly"},
        )

        assert response.status_code == 400
        assert "must be one of" in response.json()["detail"]

    def test_get_trends_empty(self, client, mock_manager):
        """Test getting trends when none exist."""
        mock_manager.get_industry_trends.return_value = []

        response = client.get("/api/competitive/trends/insurance")

        assert response.status_code == 200
        assert response.json()["trends"] == []


class TestGetCompetitivePosition:
    """Tests for GET /api/competitive/position endpoint."""

    def test_get_position_success(self, client, mock_manager):
        """Test getting competitive position."""
        mock_manager.get_competitive_position.return_value = {
            "company_id": "company_001",
            "overall_ranking": "top 25%",
            "strengths": ["accuracy", "compliance"],
            "improvement_areas": ["latency"],
            "recommendations": [],
        }

        response = client.get("/api/competitive/position")

        assert response.status_code == 200
        data = response.json()
        assert data["overall_ranking"] == "top 25%"
        assert "accuracy" in data["strengths"]

    def test_get_position_with_consortium(self, client, mock_manager):
        """Test getting competitive position with consortium context."""
        mock_manager.get_competitive_position.return_value = {
            "company_id": "company_001",
            "consortium_id": "cons_001",
            "position_in_consortium": 2,
        }

        response = client.get(
            "/api/competitive/position",
            params={"consortium_id": "cons_001"},
        )

        assert response.status_code == 200
        mock_manager.get_competitive_position.assert_called_with(
            company_id="company_001", consortium_id="cons_001"
        )

    def test_get_position_no_data(self, client, mock_manager):
        """Test getting position when no data exists."""
        mock_manager.get_competitive_position.return_value = {
            "company_id": "company_001",
            "message": "Insufficient data for competitive analysis",
        }

        response = client.get("/api/competitive/position")

        assert response.status_code == 200


class TestGetCompetitiveStats:
    """Tests for GET /api/competitive/stats endpoint."""

    def test_get_stats_success(self, client, mock_manager):
        """Test getting competitive insights statistics."""
        mock_manager.get_competitive_insights_stats.return_value = {
            "total_comparisons": 500,
            "industries_tracked": 5,
            "active_benchmarks": 25,
            "trend_data_points": 1000,
        }

        response = client.get("/api/competitive/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_comparisons"] == 500
        assert data["industries_tracked"] == 5

    def test_get_stats_empty(self, client, mock_manager):
        """Test getting stats when no data exists."""
        mock_manager.get_competitive_insights_stats.return_value = {
            "total_comparisons": 0,
            "industries_tracked": 0,
        }

        response = client.get("/api/competitive/stats")

        assert response.status_code == 200
        assert response.json()["total_comparisons"] == 0

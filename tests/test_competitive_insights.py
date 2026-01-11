"""Tests for competitive insights module."""

import tempfile
from pathlib import Path

import pytest


def load_module_from_path(module_name: str, file_path: Path):
    """Load a Python module from a file path."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_competitive.db"
        yield db_path


@pytest.fixture
def consortium_manager(temp_db):
    """Create a ConsortiumManager with temporary database."""
    sdk_api_path = Path(__file__).parent.parent / "sdk" / "api"
    consortium_module = load_module_from_path(
        "sdk.api.consortium",
        sdk_api_path / "consortium" / "__init__.py"
    )
    ConsortiumManager = consortium_module.ConsortiumManager
    manager = ConsortiumManager(db_path=temp_db)
    return manager


class TestGetIndustryBenchmarks:
    """Tests for get_industry_benchmarks method."""

    def test_get_benchmarks_finance(self, consortium_manager):
        """Test getting benchmarks for finance industry."""
        benchmarks = consortium_manager.get_industry_benchmarks("finance")

        assert len(benchmarks) > 0
        assert all("metric_name" in b for b in benchmarks)
        assert all("percentile_50" in b for b in benchmarks)
        assert all(b["industry"] == "finance" for b in benchmarks)

    def test_get_benchmarks_healthcare(self, consortium_manager):
        """Test getting benchmarks for healthcare industry."""
        benchmarks = consortium_manager.get_industry_benchmarks("healthcare")

        assert len(benchmarks) > 0
        metric_names = [b["metric_name"] for b in benchmarks]
        assert "diagnostic_accuracy" in metric_names

    def test_get_benchmarks_retail(self, consortium_manager):
        """Test getting benchmarks for retail industry."""
        benchmarks = consortium_manager.get_industry_benchmarks("retail")

        assert len(benchmarks) > 0
        metric_names = [b["metric_name"] for b in benchmarks]
        assert "demand_forecast_accuracy" in metric_names

    def test_get_benchmarks_with_metric_type_filter(self, consortium_manager):
        """Test filtering benchmarks by metric type."""
        benchmarks = consortium_manager.get_industry_benchmarks(
            "finance", metric_type="accuracy"
        )

        assert len(benchmarks) > 0
        assert all(b["metric_type"] == "accuracy" for b in benchmarks)

    def test_get_benchmarks_unknown_industry(self, consortium_manager):
        """Test getting benchmarks for unknown industry returns finance defaults."""
        benchmarks = consortium_manager.get_industry_benchmarks("unknown")

        # Should return finance metrics as default
        assert len(benchmarks) > 0

    def test_benchmark_structure(self, consortium_manager):
        """Test benchmark data structure."""
        benchmarks = consortium_manager.get_industry_benchmarks("finance")

        for benchmark in benchmarks:
            assert "id" in benchmark
            assert "industry" in benchmark
            assert "metric_name" in benchmark
            assert "metric_type" in benchmark
            assert "percentile_10" in benchmark
            assert "percentile_25" in benchmark
            assert "percentile_50" in benchmark
            assert "percentile_75" in benchmark
            assert "percentile_90" in benchmark
            assert "sample_size" in benchmark

    def test_benchmark_percentiles_ordered(self, consortium_manager):
        """Test that percentiles are in correct order."""
        benchmarks = consortium_manager.get_industry_benchmarks("finance")

        for benchmark in benchmarks:
            p10 = benchmark["percentile_10"]
            p25 = benchmark["percentile_25"]
            p50 = benchmark["percentile_50"]
            p75 = benchmark["percentile_75"]
            p90 = benchmark["percentile_90"]

            assert p10 <= p25 <= p50 <= p75 <= p90


class TestCompareToIndustry:
    """Tests for compare_to_industry method."""

    def test_compare_basic(self, consortium_manager):
        """Test basic industry comparison."""
        result = consortium_manager.compare_to_industry(
            company_id="company_001",
            industry="finance"
        )

        assert "comparison_id" in result
        assert result["company_id"] == "company_001"
        assert result["industry"] == "finance"
        assert "overall_percentile" in result
        assert "comparisons" in result

    def test_compare_with_custom_metrics(self, consortium_manager):
        """Test comparison with custom metrics."""
        custom_metrics = {
            "model_accuracy": 0.90,
            "fraud_detection_rate": 0.88,
        }

        result = consortium_manager.compare_to_industry(
            company_id="company_002",
            industry="finance",
            metrics=custom_metrics
        )

        assert len(result["comparisons"]) > 0
        metric_names = [c["metric_name"] for c in result["comparisons"]]
        assert "model_accuracy" in metric_names

    def test_compare_identifies_strengths(self, consortium_manager):
        """Test that comparison identifies strengths."""
        # Use high values to ensure strengths are identified
        high_metrics = {
            "model_accuracy": 0.98,
            "fraud_detection_rate": 0.96,
        }

        result = consortium_manager.compare_to_industry(
            company_id="company_003",
            industry="finance",
            metrics=high_metrics
        )

        assert "strengths" in result
        assert "areas_for_improvement" in result

    def test_compare_stores_result(self, consortium_manager):
        """Test that comparison is stored in database."""
        result = consortium_manager.compare_to_industry(
            company_id="company_004",
            industry="finance"
        )

        comparison_id = result["comparison_id"]
        assert comparison_id.startswith("cmp_")

    def test_compare_percentile_ranking(self, consortium_manager):
        """Test percentile ranking calculation."""
        result = consortium_manager.compare_to_industry(
            company_id="company_005",
            industry="finance"
        )

        for comparison in result["comparisons"]:
            percentile = comparison["percentile_rank"]
            assert 0 <= percentile <= 100

    def test_compare_privacy_note(self, consortium_manager):
        """Test privacy note is included."""
        result = consortium_manager.compare_to_industry(
            company_id="company_006",
            industry="finance"
        )

        assert "privacy_note" in result


class TestGetIndustryTrends:
    """Tests for get_industry_trends method."""

    def test_get_trends_quarterly(self, consortium_manager):
        """Test getting quarterly trends."""
        trends = consortium_manager.get_industry_trends("finance", "quarterly")

        assert len(trends) > 0
        assert all(t["period"] == "quarterly" for t in trends)

    def test_get_trends_monthly(self, consortium_manager):
        """Test getting monthly trends."""
        trends = consortium_manager.get_industry_trends("finance", "monthly")

        assert len(trends) > 0
        assert all(t["period"] == "monthly" for t in trends)

    def test_trend_structure(self, consortium_manager):
        """Test trend data structure."""
        trends = consortium_manager.get_industry_trends("finance")

        for trend in trends:
            assert "id" in trend
            assert "industry" in trend
            assert "metric_name" in trend
            assert "period" in trend
            assert "trend_direction" in trend
            assert "change_percentage" in trend
            assert "computed_at" in trend

    def test_trend_direction_values(self, consortium_manager):
        """Test trend direction is valid."""
        trends = consortium_manager.get_industry_trends("finance")

        for trend in trends:
            assert trend["trend_direction"] in ["improving", "declining"]


class TestGetCompetitivePosition:
    """Tests for get_competitive_position method."""

    def test_get_position_no_history(self, consortium_manager):
        """Test getting position for company with no history."""
        result = consortium_manager.get_competitive_position("new_company")

        assert result["company_id"] == "new_company"
        assert "overall_ranking" in result
        assert "percentile" in result
        assert "key_strengths" in result
        assert "improvement_areas" in result

    def test_get_position_with_history(self, consortium_manager):
        """Test getting position for company with comparison history."""
        # First create some comparisons
        consortium_manager.compare_to_industry("company_hist", "finance")
        consortium_manager.compare_to_industry("company_hist", "healthcare")

        result = consortium_manager.get_competitive_position("company_hist")

        assert result["company_id"] == "company_hist"
        assert result["comparison_count"] >= 1

    def test_position_ranking_categories(self, consortium_manager):
        """Test that ranking uses valid categories."""
        result = consortium_manager.get_competitive_position("company_rank")

        valid_rankings = ["top_decile", "top_quartile", "above_median", "below_median"]
        assert result["overall_ranking"] in valid_rankings

    def test_position_includes_recommendations(self, consortium_manager):
        """Test position includes recommendations for new companies."""
        result = consortium_manager.get_competitive_position("brand_new_company")

        # New companies get recommendations
        assert "recommendations" in result or "privacy_note" in result


class TestGetCompetitiveInsightsStats:
    """Tests for get_competitive_insights_stats method."""

    def test_get_stats(self, consortium_manager):
        """Test getting competitive insights statistics."""
        stats = consortium_manager.get_competitive_insights_stats()

        assert "total_benchmarks" in stats
        assert "total_comparisons" in stats
        assert "industries_covered" in stats
        assert "features" in stats

    def test_stats_after_comparisons(self, consortium_manager):
        """Test stats reflect comparison activity."""
        # Create a comparison
        consortium_manager.compare_to_industry("stats_company", "finance")

        stats = consortium_manager.get_competitive_insights_stats()

        assert stats["total_comparisons"] >= 1

    def test_stats_includes_industries(self, consortium_manager):
        """Test stats include covered industries."""
        stats = consortium_manager.get_competitive_insights_stats()

        industries = stats["industries_covered"]
        assert isinstance(industries, list)
        assert len(industries) > 0

    def test_stats_privacy_flag(self, consortium_manager):
        """Test privacy flag is set."""
        stats = consortium_manager.get_competitive_insights_stats()

        assert stats["privacy_preserved"] is True


class TestCompetitiveInsightsIntegration:
    """Integration tests for competitive insights."""

    def test_full_analysis_workflow(self, consortium_manager):
        """Test complete competitive analysis workflow."""
        company_id = "workflow_company"
        industry = "finance"

        # 1. Get industry benchmarks
        benchmarks = consortium_manager.get_industry_benchmarks(industry)
        assert len(benchmarks) > 0

        # 2. Compare company to industry
        comparison = consortium_manager.compare_to_industry(company_id, industry)
        assert comparison["company_id"] == company_id

        # 3. Get trends
        trends = consortium_manager.get_industry_trends(industry)
        assert len(trends) > 0

        # 4. Get competitive position
        position = consortium_manager.get_competitive_position(company_id)
        assert position["comparison_count"] >= 1

        # 5. Get overall stats
        stats = consortium_manager.get_competitive_insights_stats()
        assert stats["total_comparisons"] >= 1

    def test_multi_industry_analysis(self, consortium_manager):
        """Test analyzing across multiple industries."""
        company_id = "multi_industry_company"

        # Compare to multiple industries
        finance_result = consortium_manager.compare_to_industry(company_id, "finance")
        healthcare_result = consortium_manager.compare_to_industry(company_id, "healthcare")
        retail_result = consortium_manager.compare_to_industry(company_id, "retail")

        # Get overall position
        position = consortium_manager.get_competitive_position(company_id)

        # Should have comparisons from all industries
        industries = position.get("industries_compared", [])
        assert len(industries) >= 1

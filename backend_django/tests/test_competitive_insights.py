"""
Competitive insights module tests for Xcapit FHE-ML Platform.
"""

import pytest
from datetime import date
from rest_framework import status

from apps.competitive_insights.models import (
    CompanyMetric,
    CompetitiveReport,
    IndustryBenchmark,
)


@pytest.fixture
def industry_benchmark(db):
    """Create a test industry benchmark."""
    return IndustryBenchmark.objects.create(
        industry="finance",
        sub_industry="banking",
        metric_name="fraud_detection_accuracy",
        metric_type=IndustryBenchmark.MetricType.ACCURACY,
        unit="%",
        p10_value=70.0,
        p25_value=78.0,
        p50_value=85.0,
        p75_value=92.0,
        p90_value=97.0,
        sample_size=50,
        period_start=date(2024, 1, 1),
        period_end=date(2024, 12, 31),
    )


@pytest.fixture
def company_metric(db, company, industry_benchmark):
    """Create a test company metric."""
    return CompanyMetric.objects.create(
        company=company,
        benchmark=industry_benchmark,
        metric_name="fraud_detection_accuracy",
        value=88.5,
        period_start=date(2024, 1, 1),
        period_end=date(2024, 12, 31),
    )


@pytest.fixture
def competitive_report(db, company):
    """Create a test competitive report."""
    return CompetitiveReport.objects.create(
        company=company,
        title="Q4 2024 Competitive Analysis",
        industry="finance",
        period_start=date(2024, 10, 1),
        period_end=date(2024, 12, 31),
        summary={"overall_rank": "top_quartile"},
        strengths=["High accuracy", "Low latency"],
        weaknesses=["Limited data volume"],
        opportunities=["Expand to new markets"],
        recommendations=["Increase training data"],
        status=CompetitiveReport.Status.COMPLETED,
    )


@pytest.mark.django_db
class TestIndustryBenchmarkModel:
    """Tests for IndustryBenchmark model."""

    def test_create_benchmark(self, industry_benchmark):
        """Test creating an industry benchmark."""
        assert industry_benchmark.id is not None
        assert industry_benchmark.industry == "finance"
        assert industry_benchmark.p50_value == 85.0

    def test_percentile_rank_below_p10(self, industry_benchmark):
        """Test percentile rank for value below p10."""
        rank = industry_benchmark.get_percentile_rank(65.0)
        assert rank == 10

    def test_percentile_rank_median(self, industry_benchmark):
        """Test percentile rank for value at median."""
        rank = industry_benchmark.get_percentile_rank(85.0)
        assert rank == 50

    def test_percentile_rank_above_p90(self, industry_benchmark):
        """Test percentile rank for value above p90."""
        rank = industry_benchmark.get_percentile_rank(99.0)
        assert rank == 95

    def test_unique_constraint(self, db, industry_benchmark):
        """Test unique constraint on industry, metric_name, period_start."""
        with pytest.raises(Exception):
            IndustryBenchmark.objects.create(
                industry="finance",
                metric_name="fraud_detection_accuracy",
                p10_value=70.0,
                p25_value=78.0,
                p50_value=85.0,
                p75_value=92.0,
                p90_value=97.0,
                sample_size=50,
                period_start=date(2024, 1, 1),
                period_end=date(2024, 12, 31),
            )


@pytest.mark.django_db
class TestCompanyMetricModel:
    """Tests for CompanyMetric model."""

    def test_create_metric(self, company_metric):
        """Test creating a company metric."""
        assert company_metric.id is not None
        assert company_metric.value == 88.5

    def test_calculate_percentile(self, company_metric):
        """Test calculating percentile rank."""
        company_metric.calculate_percentile()
        company_metric.refresh_from_db()

        # 88.5 >= p50 (85) but < p75 (92), so rank is 50 (last threshold exceeded)
        assert company_metric.percentile_rank == 50


@pytest.mark.django_db
class TestCompetitiveReportModel:
    """Tests for CompetitiveReport model."""

    def test_create_report(self, competitive_report):
        """Test creating a competitive report."""
        assert competitive_report.id is not None
        assert competitive_report.status == CompetitiveReport.Status.COMPLETED

    def test_json_fields(self, competitive_report):
        """Test JSON fields are properly stored."""
        assert competitive_report.strengths == ["High accuracy", "Low latency"]
        assert len(competitive_report.weaknesses) == 1
        assert "overall_rank" in competitive_report.summary


@pytest.mark.django_db
class TestBenchmarkEndpoints:
    """Tests for benchmark API endpoints."""

    def test_list_benchmarks(self, auth_client, industry_benchmark):
        """Test listing industry benchmarks."""
        url = "/api/v2/competitive/benchmarks/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_filter_benchmarks_by_industry(self, auth_client, industry_benchmark):
        """Test filtering benchmarks by industry."""
        url = "/api/v2/competitive/benchmarks/?industry=finance"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        for benchmark in response.data.get("results", response.data):
            assert benchmark["industry"] == "finance"


@pytest.mark.django_db
class TestCompanyMetricEndpoints:
    """Tests for company metric API endpoints."""

    def test_list_metrics(self, auth_client, company_metric):
        """Test listing company metrics."""
        url = "/api/v2/competitive/metrics/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_create_metric(self, auth_client, industry_benchmark):
        """Test creating a company metric."""
        url = "/api/v2/competitive/metrics/"
        data = {
            "benchmark": str(industry_benchmark.id),
            "metric_name": "fraud_detection_accuracy",
            "value": 91.5,
            "period_start": "2024-01-01",
            "period_end": "2024-12-31",
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
class TestCompetitiveReportEndpoints:
    """Tests for competitive report API endpoints."""

    def test_list_reports(self, auth_client, competitive_report):
        """Test listing competitive reports."""
        url = "/api/v2/competitive/reports/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_get_report_detail(self, auth_client, competitive_report):
        """Test getting report detail."""
        url = f"/api/v2/competitive/reports/{competitive_report.id}/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Q4 2024 Competitive Analysis"


@pytest.mark.django_db
class TestDataIsolation:
    """Tests for data isolation between companies."""

    def test_cannot_see_other_company_metrics(self, auth_client, other_company):
        """Test user cannot see another company's metrics."""
        CompanyMetric.objects.create(
            company=other_company,
            metric_name="secret_metric",
            value=99.9,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
        )

        url = "/api/v2/competitive/metrics/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        for metric in response.data.get("results", response.data):
            assert metric.get("company") != str(other_company.id)

"""
Competitive insights serializers for Xcapit FHE-ML Platform.
"""

from rest_framework import serializers

from .models import CompanyMetric, CompetitiveReport, IndustryBenchmark


class IndustryBenchmarkSerializer(serializers.ModelSerializer):
    """Serializer for IndustryBenchmark model."""

    class Meta:
        model = IndustryBenchmark
        fields = [
            "id",
            "industry",
            "sub_industry",
            "metric_name",
            "metric_type",
            "unit",
            "p10_value",
            "p25_value",
            "p50_value",
            "p75_value",
            "p90_value",
            "sample_size",
            "period_start",
            "period_end",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class CompanyMetricSerializer(serializers.ModelSerializer):
    """Serializer for CompanyMetric model."""

    company_name = serializers.CharField(source="company.name", read_only=True)
    benchmark_info = IndustryBenchmarkSerializer(source="benchmark", read_only=True)

    class Meta:
        model = CompanyMetric
        fields = [
            "id",
            "company",
            "company_name",
            "benchmark",
            "benchmark_info",
            "metric_name",
            "value",
            "percentile_rank",
            "period_start",
            "period_end",
            "created_at",
        ]
        read_only_fields = ["id", "percentile_rank", "created_at"]


class CompanyMetricCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating CompanyMetric."""

    class Meta:
        model = CompanyMetric
        fields = [
            "metric_name",
            "value",
            "period_start",
            "period_end",
        ]

    def create(self, validated_data):
        """Create metric and calculate percentile."""
        user = self.context["request"].user
        validated_data["company"] = user.company

        # Find matching benchmark
        industry = user.company.industry
        benchmark = IndustryBenchmark.objects.filter(
            industry=industry,
            metric_name=validated_data["metric_name"],
            period_start__lte=validated_data["period_start"],
            period_end__gte=validated_data["period_end"],
        ).first()

        if benchmark:
            validated_data["benchmark"] = benchmark

        metric = CompanyMetric.objects.create(**validated_data)

        if metric.benchmark:
            metric.calculate_percentile()

        return metric


class CompetitiveReportSerializer(serializers.ModelSerializer):
    """Serializer for CompetitiveReport model."""

    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = CompetitiveReport
        fields = [
            "id",
            "company",
            "company_name",
            "title",
            "industry",
            "period_start",
            "period_end",
            "summary",
            "strengths",
            "weaknesses",
            "opportunities",
            "recommendations",
            "status",
            "created_at",
            "completed_at",
        ]
        read_only_fields = [
            "id",
            "company",
            "summary",
            "strengths",
            "weaknesses",
            "opportunities",
            "recommendations",
            "status",
            "created_at",
            "completed_at",
        ]


class CompetitiveReportCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating CompetitiveReport."""

    class Meta:
        model = CompetitiveReport
        fields = ["title", "industry", "period_start", "period_end"]

    def create(self, validated_data):
        user = self.context["request"].user
        validated_data["company"] = user.company
        return CompetitiveReport.objects.create(**validated_data)


class IndustryComparisonSerializer(serializers.Serializer):
    """Serializer for industry comparison response."""

    industry = serializers.CharField()
    company_metrics = CompanyMetricSerializer(many=True)
    benchmarks = IndustryBenchmarkSerializer(many=True)
    company_position = serializers.DictField()

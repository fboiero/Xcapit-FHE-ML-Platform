"""
Competitive insights views for Xcapit FHE-ML Platform.
"""

from apps.core.models import AuditLog
from apps.core.permissions import IsCompanyMember
from django.db.models import Avg
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import CompanyMetric, CompetitiveReport, IndustryBenchmark
from .serializers import (
    CompanyMetricCreateSerializer,
    CompanyMetricSerializer,
    CompetitiveReportCreateSerializer,
    CompetitiveReportSerializer,
    IndustryBenchmarkSerializer,
)


class IndustryBenchmarkViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for industry benchmarks (read-only).
    """

    serializer_class = IndustryBenchmarkSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter benchmarks by industry and validity."""
        queryset = IndustryBenchmark.objects.filter(
            valid_until__isnull=True
        ) | IndustryBenchmark.objects.filter(
            valid_until__gt=timezone.now()
        )

        # Filter by industry if provided
        industry = self.request.query_params.get("industry")
        if industry:
            queryset = queryset.filter(industry=industry)

        # Filter by metric type if provided
        metric_type = self.request.query_params.get("metric_type")
        if metric_type:
            queryset = queryset.filter(metric_type=metric_type)

        return queryset

    @action(detail=False, methods=["get"])
    def industries(self, request):
        """Get list of available industries."""
        industries = (
            IndustryBenchmark.objects.values_list("industry", flat=True)
            .distinct()
            .order_by("industry")
        )
        return Response(list(industries))

    @action(detail=False, methods=["get"])
    def metrics(self, request):
        """Get list of available metrics for an industry."""
        industry = request.query_params.get("industry")
        if not industry:
            return Response(
                {"detail": "Industry parameter required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        metrics = (
            IndustryBenchmark.objects.filter(industry=industry)
            .values("metric_name", "metric_type", "unit")
            .distinct()
        )
        return Response(list(metrics))


class CompanyMetricViewSet(viewsets.ModelViewSet):
    """
    ViewSet for company metrics.
    """

    serializer_class = CompanyMetricSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self):
        """Filter metrics by user's company."""
        user = self.request.user
        if not user.company:
            return CompanyMetric.objects.none()

        return CompanyMetric.objects.filter(company=user.company).select_related(
            "benchmark"
        )

    def get_serializer_class(self):
        if self.action == "create":
            return CompanyMetricCreateSerializer
        return CompanyMetricSerializer

    def perform_create(self, serializer):
        """Create metric and log event."""
        metric = serializer.save()

        AuditLog.log(
            self.request,
            action="metric_recorded",
            resource_type="company_metric",
            resource_id=metric.id,
            extra_data={
                "metric_name": metric.metric_name,
                "percentile": metric.percentile_rank,
            },
        )

    @action(detail=False, methods=["get"])
    def comparison(self, request):
        """Get comparison of company metrics vs industry benchmarks."""
        user = request.user
        if not user.company:
            return Response({"detail": "No company associated."}, status=400)

        industry = user.company.industry
        if not industry:
            return Response(
                {"detail": "Company industry not set."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get company metrics
        company_metrics = CompanyMetric.objects.filter(
            company=user.company
        ).order_by("-period_start")[:20]

        # Get industry benchmarks
        benchmarks = IndustryBenchmark.objects.filter(industry=industry)

        # Calculate company position
        avg_percentile = company_metrics.aggregate(avg=Avg("percentile_rank"))["avg"]

        comparison_data = {
            "industry": industry,
            "company_metrics": CompanyMetricSerializer(company_metrics, many=True).data,
            "benchmarks": IndustryBenchmarkSerializer(benchmarks, many=True).data,
            "company_position": {
                "average_percentile": avg_percentile or 0,
                "total_metrics": company_metrics.count(),
            },
        }

        return Response(comparison_data)


class CompetitiveReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for competitive reports.
    """

    serializer_class = CompetitiveReportSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self):
        """Filter reports by user's company."""
        user = self.request.user
        if not user.company:
            return CompetitiveReport.objects.none()

        return CompetitiveReport.objects.filter(company=user.company)

    def get_serializer_class(self):
        if self.action == "create":
            return CompetitiveReportCreateSerializer
        return CompetitiveReportSerializer

    def perform_create(self, serializer):
        """Create report and start async generation."""
        report = serializer.save()

        # Log event
        AuditLog.log(
            self.request,
            action="report_requested",
            resource_type="competitive_report",
            resource_id=report.id,
        )

        # Trigger async report generation
        from .tasks import generate_competitive_report

        generate_competitive_report.delay(str(report.id))

    @action(detail=True, methods=["post"])
    def generate(self, request, pk=None):
        """Trigger report generation."""
        report = self.get_object()

        if report.status == CompetitiveReport.Status.GENERATING:
            return Response(
                {"detail": "Report is already being generated."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        report.status = CompetitiveReport.Status.GENERATING
        report.save(update_fields=["status"])

        # Generate report synchronously for now
        self._generate_report(report)

        return Response(CompetitiveReportSerializer(report).data)

    def _generate_report(self, report):
        """Generate competitive analysis report."""
        company = report.company

        # Get company metrics
        metrics = CompanyMetric.objects.filter(
            company=company,
            period_start__gte=report.period_start,
            period_end__lte=report.period_end,
        )

        # Calculate averages
        avg_percentile = metrics.aggregate(avg=Avg("percentile_rank"))["avg"] or 50

        # Generate summary
        report.summary = {
            "total_metrics_analyzed": metrics.count(),
            "average_percentile": round(avg_percentile, 1),
            "industry": report.industry,
            "period": f"{report.period_start} to {report.period_end}",
        }

        # Identify strengths (top percentile metrics)
        strengths = metrics.filter(percentile_rank__gte=75).values_list(
            "metric_name", flat=True
        )
        report.strengths = list(strengths)

        # Identify weaknesses (bottom percentile metrics)
        weaknesses = metrics.filter(percentile_rank__lte=25).values_list(
            "metric_name", flat=True
        )
        report.weaknesses = list(weaknesses)

        # Generate recommendations
        recommendations = []
        for weakness in weaknesses:
            recommendations.append(f"Focus on improving {weakness}")
        report.recommendations = recommendations

        report.status = CompetitiveReport.Status.COMPLETED
        report.completed_at = timezone.now()
        report.save()

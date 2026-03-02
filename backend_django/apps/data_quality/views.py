"""
Data quality views for Xcapit FHE-ML Platform.
"""

from apps.core.models import AuditLog
from apps.core.permissions import IsCompanyMember, IsConsortiumMember
from django.db.models import Avg, Count
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import QualityAlert, QualityAssessment, QualityRule
from .serializers import (
    QualityAlertSerializer,
    QualityAssessmentCreateSerializer,
    QualityAssessmentSerializer,
    QualityRuleSerializer,
)


class QualityAssessmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for quality assessments.
    """

    serializer_class = QualityAssessmentSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self):
        """Filter assessments by user's company."""
        user = self.request.user
        if not user.company:
            return QualityAssessment.objects.none()

        queryset = QualityAssessment.objects.filter(company=user.company)

        # Filter by consortium if provided
        consortium_id = self.request.query_params.get("consortium")
        if consortium_id:
            queryset = queryset.filter(consortium_id=consortium_id)

        return queryset.select_related("company", "consortium")

    def get_serializer_class(self):
        if self.action == "create":
            return QualityAssessmentCreateSerializer
        return QualityAssessmentSerializer

    def perform_create(self, serializer):
        """Create assessment and log event."""
        assessment = serializer.save()

        AuditLog.log(
            self.request,
            action="quality_assessed",
            resource_type="quality_assessment",
            resource_id=assessment.id,
            extra_data={"overall_score": assessment.overall_score},
        )

    @action(detail=True, methods=["post"])
    def recalculate(self, request, pk=None):
        """Recalculate quality scores."""
        assessment = self.get_object()
        assessment.calculate_scores()

        return Response(QualityAssessmentSerializer(assessment).data)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Get quality summary for user's company."""
        user = request.user
        assessments = QualityAssessment.objects.filter(
            company=user.company,
            status=QualityAssessment.Status.COMPLETED,
        )

        summary = assessments.aggregate(
            avg_completeness=Avg("completeness_score"),
            avg_consistency=Avg("consistency_score"),
            avg_accuracy=Avg("accuracy_score"),
            avg_timeliness=Avg("timeliness_score"),
            avg_overall=Avg("overall_score"),
            total_count=Count("id"),
        )

        return Response(summary)


class QualityRuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for quality rules.
    """

    serializer_class = QualityRuleSerializer
    permission_classes = [IsAuthenticated, IsConsortiumMember]

    def get_queryset(self):
        """Filter rules by consortium."""
        consortium_id = self.request.query_params.get("consortium")
        if consortium_id:
            return QualityRule.objects.filter(consortium_id=consortium_id)
        return QualityRule.objects.none()

    def perform_create(self, serializer):
        """Create rule and log event."""
        rule = serializer.save()

        AuditLog.log(
            self.request,
            action="quality_rule_created",
            resource_type="quality_rule",
            resource_id=rule.id,
            extra_data={"name": rule.name},
        )


class QualityAlertViewSet(viewsets.ModelViewSet):
    """
    ViewSet for quality alerts.
    """

    serializer_class = QualityAlertSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self):
        """Filter alerts by user's company."""
        user = self.request.user
        if not user.company:
            return QualityAlert.objects.none()

        queryset = QualityAlert.objects.filter(company=user.company)

        # Filter by consortium if provided
        consortium_id = self.request.query_params.get("consortium")
        if consortium_id:
            queryset = queryset.filter(rule__consortium_id=consortium_id)

        # Filter by severity if provided
        severity = self.request.query_params.get("severity")
        if severity:
            queryset = queryset.filter(rule__severity=severity)

        # Filter by status if provided
        alert_status = self.request.query_params.get("status")
        if alert_status:
            queryset = queryset.filter(status=alert_status)

        return queryset.select_related("rule", "company")

    @action(detail=True, methods=["post"])
    def acknowledge(self, request, pk=None):
        """Acknowledge an alert."""
        alert = self.get_object()

        if alert.status != QualityAlert.Status.OPEN:
            return Response(
                {"detail": "Alert is not open."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        alert.status = QualityAlert.Status.ACKNOWLEDGED
        alert.save(update_fields=["status"])

        return Response(QualityAlertSerializer(alert).data)

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        """Resolve an alert."""
        alert = self.get_object()
        note = request.data.get("note", "")

        alert.resolve(request.user, note)

        AuditLog.log(
            request,
            action="alert_resolved",
            resource_type="quality_alert",
            resource_id=alert.id,
        )

        return Response(QualityAlertSerializer(alert).data)

    @action(detail=False, methods=["get"])
    def open_count(self, request):
        """Get count of open alerts."""
        user = request.user
        count = QualityAlert.objects.filter(
            company=user.company,
            status=QualityAlert.Status.OPEN,
        ).count()

        return Response({"open_alerts": count})


class QualityDashboardView(viewsets.ViewSet):
    """
    ViewSet for quality dashboard.
    """

    permission_classes = [IsAuthenticated, IsCompanyMember]

    def list(self, request):
        """Get quality dashboard data."""
        user = request.user
        if not user.company:
            return Response({"detail": "No company associated."}, status=400)

        # Aggregate data
        assessments = QualityAssessment.objects.filter(company=user.company)
        alerts = QualityAlert.objects.filter(company=user.company)

        # Score distribution
        score_ranges = {
            "excellent": assessments.filter(overall_score__gte=90).count(),
            "good": assessments.filter(overall_score__gte=70, overall_score__lt=90).count(),
            "fair": assessments.filter(overall_score__gte=50, overall_score__lt=70).count(),
            "poor": assessments.filter(overall_score__lt=50).count(),
        }

        dashboard_data = {
            "total_assessments": assessments.count(),
            "average_score": assessments.aggregate(avg=Avg("overall_score"))["avg"] or 0,
            "open_alerts": alerts.filter(status=QualityAlert.Status.OPEN).count(),
            "active_rules": QualityRule.objects.filter(
                consortium__members__company=user.company,
                is_active=True,
            ).distinct().count(),
            "score_distribution": score_ranges,
            "recent_assessments": QualityAssessmentSerializer(
                assessments.order_by("-created_at")[:5],
                many=True,
            ).data,
        }

        return Response(dashboard_data)

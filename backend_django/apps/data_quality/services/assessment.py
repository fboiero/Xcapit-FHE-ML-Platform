"""
Quality assessment service for Xcapit FHE-ML Platform.

Encapsulates business logic for data quality assessment operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from django.db import transaction
from django.db.models import Avg, Count

from apps.core.services.base import BaseService, ServiceResult

if TYPE_CHECKING:
    from apps.data_quality.models import QualityAssessment


@dataclass
class QualityScores:
    """Quality scores for an assessment."""

    completeness: float
    consistency: float
    accuracy: float
    timeliness: float
    overall: float


@dataclass
class QualityDashboard:
    """Dashboard data for quality overview."""

    total_assessments: int
    average_score: float
    open_alerts: int
    active_rules: int
    score_distribution: dict[str, int]
    recent_assessments: list[dict[str, Any]]


class QualityAssessmentService(BaseService):
    """
    Service for data quality assessment business logic.

    Handles:
    - Score calculation with pluggable strategies
    - Quality metrics aggregation
    - Dashboard data generation
    - Alert triggering
    """

    # Scoring weights (could be made configurable per consortium)
    DEFAULT_WEIGHTS = {
        "completeness": 0.30,
        "consistency": 0.25,
        "accuracy": 0.25,
        "timeliness": 0.20,
    }

    def calculate_scores(
        self,
        assessment: QualityAssessment,
        weights: dict[str, float] | None = None,
    ) -> ServiceResult[QualityScores]:
        """
        Calculate quality scores for an assessment.

        Uses weighted scoring based on multiple quality dimensions.

        Args:
            assessment: The assessment to score
            weights: Optional custom weights (defaults to DEFAULT_WEIGHTS)

        Returns:
            ServiceResult with calculated scores
        """
        weights = weights or self.DEFAULT_WEIGHTS

        try:
            # Calculate individual scores
            completeness = self._calculate_completeness(assessment)
            consistency = self._calculate_consistency(assessment)
            accuracy = self._calculate_accuracy(assessment)
            timeliness = self._calculate_timeliness(assessment)

            # Calculate weighted overall score
            overall = (
                completeness * weights["completeness"]
                + consistency * weights["consistency"]
                + accuracy * weights["accuracy"]
                + timeliness * weights["timeliness"]
            )

            scores = QualityScores(
                completeness=round(completeness, 2),
                consistency=round(consistency, 2),
                accuracy=round(accuracy, 2),
                timeliness=round(timeliness, 2),
                overall=round(overall, 2),
            )

            return ServiceResult.ok(scores)

        except Exception as e:
            return ServiceResult.fail(
                f"Score calculation failed: {str(e)}",
                error_code="calculation_error",
            )

    def _calculate_completeness(self, assessment: QualityAssessment) -> float:
        """
        Calculate completeness score.

        Based on null count relative to total cells.
        """
        total_cells = assessment.record_count * assessment.feature_count
        if total_cells == 0:
            return 0.0

        null_ratio = assessment.null_count / total_cells
        return max(0, (1 - null_ratio)) * 100

    def _calculate_consistency(self, assessment: QualityAssessment) -> float:
        """
        Calculate consistency score.

        Based on duplicate and format violations.
        """
        if assessment.record_count == 0:
            return 0.0

        duplicate_ratio = assessment.duplicate_count / assessment.record_count
        format_ratio = assessment.format_violations / assessment.record_count

        consistency = 1 - (duplicate_ratio + format_ratio) / 2
        return max(0, consistency) * 100

    def _calculate_accuracy(self, assessment: QualityAssessment) -> float:
        """
        Calculate accuracy score.

        Based on outliers, schema, and range violations.
        """
        if assessment.record_count == 0:
            return 0.0

        violation_count = (
            assessment.outlier_count
            + assessment.schema_violations
            + assessment.range_violations
        )
        violation_ratio = violation_count / assessment.record_count

        accuracy = 1 - violation_ratio
        return max(0, accuracy) * 100

    def _calculate_timeliness(self, assessment: QualityAssessment) -> float:
        """
        Calculate timeliness score based on data freshness.

        Evaluates how recent the data contribution is relative to:
        1. The contribution's creation time vs assessment time
        2. The expected update frequency for the data type

        Scoring:
        - Data less than 1 day old: 100
        - Data 1-7 days old: 90-99 (linear decay)
        - Data 7-30 days old: 70-89 (linear decay)
        - Data 30-90 days old: 50-69 (linear decay)
        - Data older than 90 days: 0-49 (linear decay, min 0)
        """
        from django.utils import timezone
        from datetime import timedelta

        if not assessment.contribution:
            # No contribution linked - check assessment creation time
            contribution_time = assessment.created_at
        else:
            contribution_time = assessment.contribution.created_at

        now = timezone.now()
        age = now - contribution_time

        # Calculate days since data was contributed
        days_old = age.total_seconds() / (24 * 60 * 60)

        if days_old < 1:
            # Fresh data: 100
            return 100.0
        elif days_old < 7:
            # 1-7 days: 90-99 (linear decay)
            return 100.0 - (days_old - 1) * (10 / 6)
        elif days_old < 30:
            # 7-30 days: 70-89 (linear decay)
            return 90.0 - (days_old - 7) * (20 / 23)
        elif days_old < 90:
            # 30-90 days: 50-69 (linear decay)
            return 70.0 - (days_old - 30) * (20 / 60)
        else:
            # 90+ days: 0-49 (linear decay, min 0)
            score = 50.0 - (days_old - 90) * (50 / 90)
            return max(0.0, score)

    @transaction.atomic
    def run_assessment(
        self,
        assessment: QualityAssessment,
    ) -> ServiceResult[QualityAssessment]:
        """
        Run a complete quality assessment.

        Calculates scores and updates the assessment record.

        Args:
            assessment: The assessment to process

        Returns:
            ServiceResult with updated assessment
        """
        from django.utils import timezone

        from apps.core.services import AuditService
        from apps.data_quality.models import QualityAssessment as QAModel

        # Calculate scores
        result = self.calculate_scores(assessment)
        if not result.success:
            assessment.status = QAModel.Status.FAILED
            assessment.save(update_fields=["status"])
            return ServiceResult.fail(
                result.error or "Score calculation failed",
                error_code=result.error_code or "calculation_error",
            )

        scores = result.data

        # Update assessment
        assessment.completeness_score = scores.completeness
        assessment.consistency_score = scores.consistency
        assessment.accuracy_score = scores.accuracy
        assessment.timeliness_score = scores.timeliness
        assessment.overall_score = scores.overall
        assessment.status = QAModel.Status.COMPLETED
        assessment.last_assessed_at = timezone.now()
        assessment.save()

        # Check for alerts
        self._check_quality_rules(assessment)

        # Audit log
        if self.request:
            AuditService.log_from_request(
                self.request,
                action="quality_assessed",
                resource_type="quality_assessment",
                resource_id=assessment.id,
                extra_data={"overall_score": scores.overall},
            )

        return ServiceResult.ok(assessment)

    def _check_quality_rules(self, assessment: QualityAssessment) -> None:
        """
        Check quality rules and create alerts if needed.

        Args:
            assessment: The completed assessment
        """
        from apps.data_quality.models import QualityAlert, QualityRule

        rules = QualityRule.objects.filter(
            consortium=assessment.consortium,
            is_active=True,
        )

        for rule in rules:
            # Get the metric value
            metric_value = getattr(assessment, rule.metric, None)
            if metric_value is None:
                continue

            # Evaluate condition
            condition = rule.condition
            operator = condition.get("operator", ">=")
            threshold = condition.get("value", 0)

            violated = False
            if operator == ">=" and metric_value < threshold:
                violated = True
            elif operator == "<=" and metric_value > threshold:
                violated = True
            elif operator == ">" and metric_value <= threshold:
                violated = True
            elif operator == "<" and metric_value >= threshold:
                violated = True
            elif operator == "==" and metric_value != threshold:
                violated = True

            if violated:
                QualityAlert.objects.create(
                    rule=rule,
                    assessment=assessment,
                    company=assessment.company,
                    message=f"{rule.name}: {rule.metric} is {metric_value}, expected {operator}{threshold}",
                    actual_value=metric_value,
                    expected_value=f"{operator}{threshold}",
                    status=QualityAlert.Status.OPEN,
                )

    def get_dashboard(self) -> ServiceResult[QualityDashboard]:
        """
        Get quality dashboard data for the current company.

        Returns:
            ServiceResult with dashboard data
        """
        from apps.data_quality.models import QualityAlert, QualityAssessment, QualityRule

        company = self.require_company()

        assessments = QualityAssessment.objects.filter(company=company)
        alerts = QualityAlert.objects.filter(company=company)

        # Calculate score distribution
        completed = assessments.filter(status=QualityAssessment.Status.COMPLETED)
        score_distribution = {
            "excellent": completed.filter(overall_score__gte=90).count(),
            "good": completed.filter(overall_score__gte=70, overall_score__lt=90).count(),
            "fair": completed.filter(overall_score__gte=50, overall_score__lt=70).count(),
            "poor": completed.filter(overall_score__lt=50).count(),
        }

        # Get average score
        avg_score = completed.aggregate(avg=Avg("overall_score"))["avg"] or 0

        # Get recent assessments
        recent = assessments.order_by("-created_at")[:5]
        recent_data = [
            {
                "id": str(a.id),
                "overall_score": a.overall_score,
                "status": a.status,
                "created_at": a.created_at.isoformat(),
            }
            for a in recent
        ]

        dashboard = QualityDashboard(
            total_assessments=assessments.count(),
            average_score=round(avg_score, 2),
            open_alerts=alerts.filter(status=QualityAlert.Status.OPEN).count(),
            active_rules=QualityRule.objects.filter(
                consortium__members__company=company,
                is_active=True,
            ).distinct().count(),
            score_distribution=score_distribution,
            recent_assessments=recent_data,
        )

        return ServiceResult.ok(dashboard)

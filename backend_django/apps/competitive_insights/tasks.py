"""
Celery tasks for competitive insights.

Handles async report generation.
"""

import logging
from uuid import UUID

from celery import shared_task
from django.db.models import Avg
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
)
def generate_competitive_report(self, report_id: str) -> dict:
    """
    Generate competitive analysis report asynchronously.

    Args:
        report_id: UUID of the CompetitiveReport to generate

    Returns:
        Dict with report status and summary
    """
    from .models import CompanyMetric, CompetitiveReport

    try:
        report = CompetitiveReport.objects.get(id=UUID(report_id))
    except CompetitiveReport.DoesNotExist:
        logger.error(f"Report {report_id} not found")
        return {"error": "Report not found", "report_id": report_id}

    # Mark as generating
    report.status = CompetitiveReport.Status.GENERATING
    report.save(update_fields=["status"])

    try:
        company = report.company

        # Get company metrics for the period
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
            "generated_by": "celery_async",
        }

        # Identify strengths (top percentile metrics)
        strengths = list(
            metrics.filter(percentile_rank__gte=75).values_list("metric_name", flat=True)
        )
        report.strengths = strengths

        # Identify weaknesses (bottom percentile metrics)
        weaknesses = list(
            metrics.filter(percentile_rank__lte=25).values_list("metric_name", flat=True)
        )
        report.weaknesses = weaknesses

        # Identify opportunities (metrics with room for improvement)
        opportunities = list(
            metrics.filter(
                percentile_rank__gt=25,
                percentile_rank__lt=75,
            ).values_list("metric_name", flat=True)[:5]
        )
        report.opportunities = opportunities

        # Generate recommendations
        recommendations = []
        for weakness in weaknesses:
            recommendations.append(f"Focus on improving {weakness}")
        for opportunity in opportunities[:3]:
            recommendations.append(f"Opportunity to excel in {opportunity}")
        report.recommendations = recommendations

        # Mark as completed
        report.status = CompetitiveReport.Status.COMPLETED
        report.completed_at = timezone.now()
        report.save()

        logger.info(f"Report {report_id} generated successfully")
        return {
            "report_id": report_id,
            "status": "completed",
            "metrics_analyzed": metrics.count(),
            "average_percentile": avg_percentile,
        }

    except Exception as e:
        logger.exception(f"Error generating report {report_id}: {e}")
        report.status = CompetitiveReport.Status.FAILED
        report.save(update_fields=["status"])
        raise


@shared_task
def cleanup_old_reports(days: int = 90) -> dict:
    """
    Clean up old completed reports.

    Args:
        days: Delete reports older than this many days

    Returns:
        Dict with cleanup results
    """
    from django.utils import timezone
    from datetime import timedelta

    from .models import CompetitiveReport

    cutoff = timezone.now() - timedelta(days=days)
    old_reports = CompetitiveReport.objects.filter(
        status=CompetitiveReport.Status.COMPLETED,
        completed_at__lt=cutoff,
    )

    count = old_reports.count()
    old_reports.delete()

    logger.info(f"Cleaned up {count} old competitive reports")
    return {"deleted_count": count, "cutoff_date": str(cutoff)}

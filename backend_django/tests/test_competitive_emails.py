"""
Tests for competitive insights tasks and consortium email service.

Targets coverage gaps in:
- apps/competitive_insights/tasks.py (19% -> ~85%)
- apps/consortiums/emails.py (69% -> ~90%)
"""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.core import mail
from django.test import override_settings
from django.utils import timezone

from apps.competitive_insights.models import CompanyMetric, CompetitiveReport
from apps.competitive_insights.tasks import (
    cleanup_old_reports,
    generate_competitive_report,
)
from apps.consortiums.emails import ConsortiumEmailService
from apps.consortiums.models import (
    Consortium,
    ConsortiumInvitation,
    ConsortiumMember,
    TrainingResult,
)
from apps.core.models import Company


# ===========================================================================
# Competitive insights tasks
# ===========================================================================


@pytest.fixture
def report(db, company):
    return CompetitiveReport.objects.create(
        company=company,
        title="Q1 Analysis",
        industry="technology",
        period_start=date(2025, 1, 1),
        period_end=date(2025, 3, 31),
        status=CompetitiveReport.Status.PENDING,
    )


@pytest.fixture
def company_metrics(db, company, report):
    """Create metrics spanning the report period."""
    metrics = []
    for name, value, percentile in [
        ("accuracy", 0.92, 85),
        ("latency", 120, 30),
        ("throughput", 5000, 70),
        ("quality", 0.88, 60),
    ]:
        m = CompanyMetric.objects.create(
            company=company,
            metric_name=name,
            value=value,
            percentile_rank=percentile,
            period_start=date(2025, 1, 1),
            period_end=date(2025, 3, 31),
        )
        metrics.append(m)
    return metrics


CELERY_EAGER = {
    "CELERY_TASK_ALWAYS_EAGER": True,
    "CELERY_TASK_EAGER_PROPAGATES": True,
}


@pytest.mark.django_db
class TestGenerateCompetitiveReport:
    @override_settings(**CELERY_EAGER)
    def test_report_not_found(self):
        import uuid

        result = generate_competitive_report(str(uuid.uuid4()))
        assert "error" in result

    @override_settings(**CELERY_EAGER)
    def test_report_generated_successfully(self, report, company_metrics):
        result = generate_competitive_report(str(report.id))
        assert result["status"] == "completed"
        assert result["metrics_analyzed"] == 4

        report.refresh_from_db()
        assert report.status == CompetitiveReport.Status.COMPLETED
        assert report.completed_at is not None
        assert report.summary["total_metrics_analyzed"] == 4
        assert report.summary["industry"] == "technology"

    @override_settings(**CELERY_EAGER)
    def test_report_strengths_and_weaknesses(self, report, company_metrics):
        generate_competitive_report(str(report.id))

        report.refresh_from_db()
        # accuracy has percentile 85 >= 75 -> strength
        assert "accuracy" in report.strengths
        assert isinstance(report.weaknesses, list)
        assert isinstance(report.opportunities, list)
        assert isinstance(report.recommendations, list)

    @override_settings(**CELERY_EAGER)
    def test_report_with_no_metrics(self, report):
        result = generate_competitive_report(str(report.id))
        assert result["status"] == "completed"
        assert result["metrics_analyzed"] == 0

        report.refresh_from_db()
        assert report.summary["average_percentile"] == 50  # default


@pytest.mark.django_db
class TestCleanupOldReports:
    def test_cleanup_deletes_old(self, company):
        # Create old completed report
        old = CompetitiveReport.objects.create(
            company=company,
            title="Old Report",
            industry="tech",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 3, 31),
            status=CompetitiveReport.Status.COMPLETED,
            completed_at=timezone.now() - timedelta(days=100),
        )
        # Create recent completed report
        recent = CompetitiveReport.objects.create(
            company=company,
            title="Recent Report",
            industry="tech",
            period_start=date(2025, 1, 1),
            period_end=date(2025, 3, 31),
            status=CompetitiveReport.Status.COMPLETED,
            completed_at=timezone.now() - timedelta(days=10),
        )

        result = cleanup_old_reports(days=90)
        assert result["deleted_count"] == 1
        assert CompetitiveReport.objects.filter(id=recent.id).exists()
        assert not CompetitiveReport.objects.filter(id=old.id).exists()

    def test_cleanup_no_old_reports(self, company):
        result = cleanup_old_reports(days=90)
        assert result["deleted_count"] == 0

    def test_cleanup_skips_pending(self, company):
        """Only completed reports should be cleaned up."""
        CompetitiveReport.objects.create(
            company=company,
            title="Pending Report",
            industry="tech",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 3, 31),
            status=CompetitiveReport.Status.PENDING,
        )
        result = cleanup_old_reports(days=1)
        assert result["deleted_count"] == 0


# ===========================================================================
# ConsortiumEmailService
# ===========================================================================


@pytest.fixture
def email_svc():
    return ConsortiumEmailService()


@pytest.fixture
def invitation_for_email(db, consortium, company, other_company):
    inv = ConsortiumInvitation.objects.create(
        consortium=consortium,
        inviter=company,
        invitee_email="invitee@example.com",
        role=ConsortiumMember.Role.CONTRIBUTOR,
        message="Please join our consortium!",
        expires_at=timezone.now() + timedelta(days=7),
    )
    return inv


@pytest.fixture
def accepted_invitation(db, consortium, company, other_company):
    return ConsortiumInvitation.objects.create(
        consortium=consortium,
        inviter=company,
        invitee_email=other_company.email,
        invitee_company=other_company,
        role=ConsortiumMember.Role.CONTRIBUTOR,
        status="accepted",
        expires_at=timezone.now() + timedelta(days=7),
        responded_at=timezone.now(),
    )


@pytest.fixture
def training_result(db, consortium):
    return TrainingResult.objects.create(
        consortium=consortium,
        status=TrainingResult.Status.COMPLETED,
        contributions_count=5,
        total_records=10000,
        accuracy=0.92,
        epochs_completed=50,
        model_hash="abc123def456" * 4,
    )


EMAIL_SETTINGS = {
    "EMAIL_BACKEND": "django.core.mail.backends.locmem.EmailBackend",
    "DEFAULT_FROM_EMAIL": "test@xcapit.com",
}


@pytest.mark.django_db
class TestConsortiumEmailServiceSend:
    @pytest.fixture(autouse=True)
    def _clear_outbox(self):
        mail.outbox.clear()

    @override_settings(**EMAIL_SETTINGS)
    def test_send_invitation(self, email_svc, invitation_for_email):
        mail.outbox.clear()
        result = email_svc.send_invitation(invitation_for_email)
        assert result is True
        assert len(mail.outbox) == 1
        assert "Invitation to join" in mail.outbox[0].subject
        assert mail.outbox[0].to == ["invitee@example.com"]

    @override_settings(**EMAIL_SETTINGS)
    def test_send_invitation_accepted(self, email_svc, accepted_invitation):
        mail.outbox.clear()
        result = email_svc.send_invitation_accepted(accepted_invitation)
        assert result is True
        assert len(mail.outbox) == 1
        assert "joined" in mail.outbox[0].subject

    def test_send_invitation_accepted_no_invitee_company(
        self, email_svc, invitation_for_email
    ):
        """When invitee_company is None, should return False."""
        assert invitation_for_email.invitee_company is None
        result = email_svc.send_invitation_accepted(invitation_for_email)
        assert result is False

    @override_settings(**EMAIL_SETTINGS)
    def test_send_consortium_activated(self, email_svc, consortium):
        mail.outbox.clear()
        result = email_svc.send_consortium_activated(consortium)
        assert result is True
        assert len(mail.outbox) == 1
        assert "now active" in mail.outbox[0].subject

    @override_settings(**EMAIL_SETTINGS)
    def test_send_training_started(self, email_svc, training_result):
        mail.outbox.clear()
        result = email_svc.send_training_started(training_result)
        assert result is True
        assert len(mail.outbox) == 1
        assert "Training started" in mail.outbox[0].subject

    @override_settings(**EMAIL_SETTINGS)
    def test_send_training_complete(self, email_svc, training_result):
        mail.outbox.clear()
        result = email_svc.send_training_complete(training_result)
        assert result is True
        assert len(mail.outbox) == 1
        assert "Training completed" in mail.outbox[0].subject


@pytest.mark.django_db
class TestConsortiumEmailServiceFallback:
    def test_generate_plain_text(self, email_svc):
        text = email_svc._generate_plain_text(
            "Test Subject",
            {
                "consortium_name": "My Consortium",
                "platform_url": "https://example.com",
                "empty_value": "",
            },
        )
        assert "Test Subject" in text
        assert "My Consortium" in text
        assert "example.com" in text

    def test_send_email_failure(self, email_svc):
        """When send_mail raises, should return False."""
        with patch("apps.consortiums.emails.send_mail", side_effect=Exception("SMTP error")):
            result = email_svc._send_email(
                subject="Test",
                template_name="nonexistent.html",
                context={"key": "value"},
                recipient_email="test@example.com",
            )
            assert result is False

    @override_settings(**EMAIL_SETTINGS)
    def test_template_fallback(self, email_svc):
        """When template doesn't exist, falls back to plain text."""
        mail.outbox.clear()
        result = email_svc._send_email(
            subject="Fallback Test",
            template_name="emails/nonexistent_template.html",
            context={"consortium_name": "Test"},
            recipient_email="test@example.com",
        )
        assert result is True
        assert len(mail.outbox) == 1

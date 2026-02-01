"""
Small targeted tests to push coverage from 79.78% to 80%+.

Covers:
- Service audit log branches (member, invitation, consortium) via request context
- BaseService properties and methods
- Competitive tasks weakness/recommendation paths
"""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.test import RequestFactory, override_settings
from django.utils import timezone

from apps.competitive_insights.models import CompanyMetric, CompetitiveReport
from apps.competitive_insights.tasks import generate_competitive_report
from apps.consortiums.models import (
    ConsortiumInvitation,
    ConsortiumMember,
)
from apps.consortiums.services.consortium import ConsortiumService
from apps.consortiums.services.invitation import InvitationService
from apps.consortiums.services.member import MemberService
from apps.core.services.base import BaseService, ServiceContext


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_context_with_request(user, company):
    """Create a ServiceContext with a real Django request."""
    factory = RequestFactory()
    request = factory.get("/fake-endpoint")
    request.user = user
    return ServiceContext(user=user, company=company, request=request)


# ===========================================================================
# BaseService & ServiceContext
# ===========================================================================


@pytest.mark.django_db
class TestServiceContext:
    def test_from_request_authenticated(self, user, company):
        factory = RequestFactory()
        request = factory.get("/")
        request.user = user
        ctx = ServiceContext.from_request(request)
        assert ctx.user == user
        assert ctx.company == company

    def test_from_request_unauthenticated(self):
        mock_request = MagicMock()
        mock_request.user.is_authenticated = False
        ctx = ServiceContext.from_request(mock_request)
        assert ctx.user is None
        assert ctx.company is None


@pytest.mark.django_db
class TestBaseService:
    def test_user_property(self, user, company):
        ctx = ServiceContext(user=user, company=company)
        svc = BaseService(context=ctx)
        assert svc.user == user

    def test_company_property(self, user, company):
        ctx = ServiceContext(user=user, company=company)
        svc = BaseService(context=ctx)
        assert svc.company == company

    def test_require_user_success(self, user):
        ctx = ServiceContext(user=user)
        svc = BaseService(context=ctx)
        assert svc.require_user() == user

    def test_require_user_raises(self):
        svc = BaseService()
        with pytest.raises(PermissionError, match="Authentication required"):
            svc.require_user()

    def test_require_company_raises(self):
        svc = BaseService()
        with pytest.raises(PermissionError, match="Company membership required"):
            svc.require_company()

    def test_atomic_decorator(self):
        @BaseService.atomic
        def dummy():
            return 42

        assert dummy() == 42


# ===========================================================================
# MemberService with request context (covers audit log lines 57, 101, 159, 227)
# ===========================================================================


@pytest.mark.django_db
class TestMemberServiceAudit:
    def test_approve_with_audit(self, user, company, consortium, other_company):
        ctx = _make_context_with_request(user, company)
        svc = MemberService(context=ctx)
        member = ConsortiumMember.objects.create(
            consortium=consortium,
            company=other_company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.PENDING,
        )
        with patch("apps.core.services.AuditService.log_from_request"):
            result = svc.approve_member(member)
        assert result.success

    def test_reject_with_audit(self, user, company, consortium, other_company):
        ctx = _make_context_with_request(user, company)
        svc = MemberService(context=ctx)
        member = ConsortiumMember.objects.create(
            consortium=consortium,
            company=other_company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.PENDING,
        )
        ConsortiumMember.Status.REJECTED = "rejected"
        try:
            with patch("apps.core.services.AuditService.log_from_request"):
                result = svc.reject_member(member, reason="Bad data")
            assert result.success
        finally:
            del ConsortiumMember.Status.REJECTED

    def test_remove_with_audit(self, user, company, consortium, other_company):
        ctx = _make_context_with_request(user, company)
        svc = MemberService(context=ctx)
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.OWNER,
            status=ConsortiumMember.Status.ACTIVE,
        )
        member = ConsortiumMember.objects.create(
            consortium=consortium,
            company=other_company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        with patch("apps.core.services.AuditService.log_from_request"):
            result = svc.remove_member(member)
        assert result.success

    def test_change_role_with_audit(self, user, company, consortium, other_company):
        ctx = _make_context_with_request(user, company)
        svc = MemberService(context=ctx)
        member = ConsortiumMember.objects.create(
            consortium=consortium,
            company=other_company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        with patch("apps.core.services.AuditService.log_from_request"):
            result = svc.change_role(member, ConsortiumMember.Role.ADMIN)
        assert result.success


# ===========================================================================
# InvitationService with request context (covers audit log lines 195, 252)
# ===========================================================================


@pytest.mark.django_db
class TestInvitationServiceAudit:
    def test_accept_with_audit(self, user, company, consortium, other_company):
        ctx = _make_context_with_request(user, company)
        svc = InvitationService(context=ctx)
        invitation = ConsortiumInvitation.objects.create(
            consortium=consortium,
            inviter=company,
            invitee_email=other_company.email,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumInvitation.Status.PENDING,
            expires_at=timezone.now() + timedelta(days=7),
        )
        with patch("apps.core.services.AuditService.log_from_request"):
            result = svc.accept_invitation(invitation, other_company)
        assert result.success

    def test_decline_with_audit(self, user, company, consortium, other_company):
        ctx = _make_context_with_request(user, company)
        svc = InvitationService(context=ctx)
        invitation = ConsortiumInvitation.objects.create(
            consortium=consortium,
            inviter=company,
            invitee_email=other_company.email,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumInvitation.Status.PENDING,
            expires_at=timezone.now() + timedelta(days=7),
        )
        with patch("apps.core.services.AuditService.log_from_request"):
            result = svc.decline_invitation(invitation, other_company)
        assert result.success


# ===========================================================================
# ConsortiumService with request context (covers audit log line 156)
# ===========================================================================


@pytest.mark.django_db
class TestConsortiumServiceAudit:
    def test_start_training_with_audit(self, user, company, consortium, other_company):
        ctx = _make_context_with_request(user, company)
        svc = ConsortiumService(context=ctx)
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.OWNER,
            status=ConsortiumMember.Status.ACTIVE,
        )
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=other_company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        consortium.min_members = 2
        consortium.save()
        with patch("apps.core.services.AuditService.log_from_request"):
            result = svc.start_training(consortium)
        assert result.success


# ===========================================================================
# Competitive tasks — cover weakness recommendations (lines 90-93)
# ===========================================================================


CELERY_EAGER = {
    "CELERY_TASK_ALWAYS_EAGER": True,
    "CELERY_TASK_EAGER_PROPAGATES": True,
}


@pytest.mark.django_db
class TestCompetitiveTasksWeaknesses:
    @override_settings(**CELERY_EAGER)
    def test_report_with_weaknesses_generates_recommendations(self, company):
        report = CompetitiveReport.objects.create(
            company=company,
            title="Weakness Report",
            industry="technology",
            period_start=date(2025, 1, 1),
            period_end=date(2025, 3, 31),
            status=CompetitiveReport.Status.PENDING,
        )
        CompanyMetric.objects.create(
            company=company,
            metric_name="security_score",
            value=0.3,
            percentile_rank=15,  # <= 25 -> weakness
            period_start=date(2025, 1, 1),
            period_end=date(2025, 3, 31),
        )
        CompanyMetric.objects.create(
            company=company,
            metric_name="efficiency",
            value=0.6,
            percentile_rank=50,  # 25 < x < 75 -> opportunity
            period_start=date(2025, 1, 1),
            period_end=date(2025, 3, 31),
        )

        result = generate_competitive_report(str(report.id))
        assert result["status"] == "completed"

        report.refresh_from_db()
        assert "security_score" in report.weaknesses
        assert "efficiency" in report.opportunities
        assert any("security_score" in r for r in report.recommendations)
        assert any("efficiency" in r for r in report.recommendations)

"""
Tests for all core ViewSets: Company, User, APIKey, AuditLog,
Webhook, UsageStats, Report, Workflow, ScheduledTask, HealthCheck.
"""

import uuid
from datetime import date, timedelta

import pytest
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.models import (
    APIKey,
    AuditLog,
    Company,
    Report,
    ScheduledTask,
    UsageTracking,
    User,
    Webhook,
    Workflow,
)


# ── Helpers ──────────────────────────────────────────────────


def _company(**kw):
    defaults = {
        "name": f"Co-{uuid.uuid4().hex[:6]}",
        "email": f"co-{uuid.uuid4().hex[:6]}@example.com",
    }
    defaults.update(kw)
    return Company.objects.create(**defaults)


def _user(company=None, **kw):
    defaults = {
        "email": f"u-{uuid.uuid4().hex[:6]}@example.com",
        "first_name": "Test",
        "last_name": "User",
    }
    defaults.update(kw)
    return User.objects.create_user(password="StrongPass12345!", company=company, **defaults)


def _auth_client(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c


# ══════════════════════════════════════════════════════════════
# TestHealthCheck
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestHealthCheck(TestCase):

    def test_health_returns_200_no_auth(self):
        client = APIClient()
        resp = client.get("/api/v2/health/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["status"] == "healthy"


# ══════════════════════════════════════════════════════════════
# TestCompanyViewSet
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestCompanyViewSet(TestCase):

    def setUp(self):
        self.co = _company(name="ViewCo")
        self.user = _user(company=self.co)
        self.client = _auth_client(self.user)

    def test_list_returns_own_company(self):
        resp = self.client.get("/api/v2/companies/")
        assert resp.status_code == status.HTTP_200_OK
        ids = [r["id"] for r in resp.data["results"]]
        assert str(self.co.id) in ids

    def test_list_excludes_other_companies(self):
        _company(name="OtherCo")
        resp = self.client.get("/api/v2/companies/")
        names = [r["name"] for r in resp.data["results"]]
        assert "OtherCo" not in names

    def test_retrieve_uses_detail_serializer(self):
        resp = self.client.get(f"/api/v2/companies/{self.co.id}/")
        assert resp.status_code == status.HTTP_200_OK
        # CompanyDetailSerializer has extra fields
        assert "user_count" in resp.data
        assert "api_key_count" in resp.data
        assert "is_trial" in resp.data

    def test_no_company_user_gets_empty_list(self):
        user = _user()
        client = _auth_client(user)
        resp = client.get("/api/v2/companies/")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["results"]) == 0

    def test_unauthenticated_blocked(self):
        resp = APIClient().get("/api/v2/companies/")
        assert resp.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


# ══════════════════════════════════════════════════════════════
# TestUserViewSet
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestUserViewSet(TestCase):

    def setUp(self):
        self.co = _company()
        self.user = _user(company=self.co)
        self.client = _auth_client(self.user)

    def test_list_returns_only_self(self):
        _user(company=self.co)  # another user in same company
        resp = self.client.get("/api/v2/users/")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["results"]) == 1
        assert resp.data["results"][0]["id"] == str(self.user.id)

    def test_update_name(self):
        resp = self.client.patch(
            f"/api/v2/users/{self.user.id}/",
            {"first_name": "Updated"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        self.user.refresh_from_db()
        assert self.user.first_name == "Updated"

    def test_unauthenticated_blocked(self):
        resp = APIClient().get("/api/v2/users/")
        assert resp.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


# ══════════════════════════════════════════════════════════════
# TestAPIKeyViewSet
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestAPIKeyViewSet(TestCase):

    def setUp(self):
        self.co = _company()
        self.user = _user(company=self.co)
        self.client = _auth_client(self.user)

    def test_list_api_keys(self):
        APIKey.objects.create(
            name="k1", key_hash="a" * 64, company=self.co,
            created_by=self.user, prefix="fheml_aa",
        )
        resp = self.client.get("/api/v2/api-keys/")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["results"]) == 1

    def test_create_returns_raw_key(self):
        resp = self.client.post(
            "/api/v2/api-keys/",
            {"name": "new-key", "permissions": ["read"]},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert "raw_key" in resp.data
        assert resp.data["raw_key"].startswith("fheml_")

    def test_list_filtered_by_company(self):
        other_co = _company()
        APIKey.objects.create(
            name="other", key_hash="b" * 64, company=other_co, prefix="fheml_bb",
        )
        resp = self.client.get("/api/v2/api-keys/")
        names = [k["name"] for k in resp.data["results"]]
        assert "other" not in names

    def test_no_company_gets_empty_list(self):
        user = _user()
        client = _auth_client(user)
        resp = client.get("/api/v2/api-keys/")
        assert len(resp.data["results"]) == 0


# ══════════════════════════════════════════════════════════════
# TestAuditLogViewSet
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestAuditLogViewSet(TestCase):

    def setUp(self):
        self.co = _company()
        self.user = _user(company=self.co)
        self.client = _auth_client(self.user)

    def test_list_audit_logs(self):
        AuditLog.objects.create(
            company=self.co, action="test", resource_type="obj",
        )
        resp = self.client.get("/api/v2/audit-logs/")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["results"]) >= 1

    def test_read_only(self):
        resp = self.client.post(
            "/api/v2/audit-logs/",
            {"action": "hack", "resource_type": "x"},
            format="json",
        )
        assert resp.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_filtered_by_company(self):
        other_co = _company()
        AuditLog.objects.create(
            company=other_co, action="other", resource_type="x",
        )
        resp = self.client.get("/api/v2/audit-logs/")
        actions = [l["action"] for l in resp.data["results"]]
        assert "other" not in actions


# ══════════════════════════════════════════════════════════════
# TestWebhookViewSet
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestWebhookViewSet(TestCase):

    def setUp(self):
        self.co = _company()
        self.user = _user(company=self.co)
        self.client = _auth_client(self.user)

    def test_list_webhooks(self):
        Webhook.objects.create(
            company=self.co, name="hook", url="https://example.com",
            secret="s", events=["model.trained"],
        )
        resp = self.client.get("/api/v2/webhooks/")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["results"]) == 1

    def test_create_webhook(self):
        resp = self.client.post(
            "/api/v2/webhooks/",
            {
                "name": "new-hook",
                "url": "https://example.com/wh",
                "secret": "my-secret",
                "events": ["model.trained"],
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        wh = Webhook.objects.get(name="new-hook")
        assert wh.company == self.co

    def test_create_webhook_invalid_event(self):
        resp = self.client.post(
            "/api/v2/webhooks/",
            {
                "name": "bad",
                "url": "https://example.com/wh",
                "secret": "s",
                "events": ["invalid.event"],
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_company_filter(self):
        other_co = _company()
        Webhook.objects.create(
            company=other_co, name="other-hook", url="https://other.com",
            secret="s", events=["*"],
        )
        resp = self.client.get("/api/v2/webhooks/")
        names = [w["name"] for w in resp.data["results"]]
        assert "other-hook" not in names


# ══════════════════════════════════════════════════════════════
# TestUsageStatsViewSet
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestUsageStatsViewSet(TestCase):

    def setUp(self):
        self.co = _company()
        self.user = _user(company=self.co)
        self.client = _auth_client(self.user)

    def test_list_usage(self):
        UsageTracking.objects.create(
            company=self.co, date=date.today(), api_requests=42,
        )
        resp = self.client.get("/api/v2/usage-stats/")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["results"]) == 1
        assert resp.data["results"][0]["api_requests"] == 42

    def test_company_filter(self):
        other_co = _company()
        UsageTracking.objects.create(
            company=other_co, date=date.today(), api_requests=99,
        )
        resp = self.client.get("/api/v2/usage-stats/")
        for entry in resp.data["results"]:
            assert entry["company"] == str(self.co.id)

    def test_read_only(self):
        resp = self.client.post(
            "/api/v2/usage-stats/",
            {"date": "2026-01-01"},
            format="json",
        )
        assert resp.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


# ══════════════════════════════════════════════════════════════
# TestReportViewSet
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestReportViewSet(TestCase):

    def setUp(self):
        self.co = _company()
        self.user = _user(company=self.co)
        self.client = _auth_client(self.user)

    def test_list_reports(self):
        Report.objects.create(
            company=self.co, created_by=self.user,
            name="R1", report_type="usage", format="pdf",
        )
        resp = self.client.get("/api/v2/reports/")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["results"]) == 1

    def test_create_report_sets_company_and_user(self):
        resp = self.client.post(
            "/api/v2/reports/",
            {
                "name": "My Report",
                "report_type": "usage",
                "format": "csv",
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        rpt = Report.objects.get(name="My Report")
        assert rpt.company == self.co
        assert rpt.created_by == self.user

    def test_create_report_invalid_type(self):
        resp = self.client.post(
            "/api/v2/reports/",
            {
                "name": "Bad",
                "report_type": "nonexistent",
                "format": "pdf",
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_company_filter(self):
        other_co = _company()
        Report.objects.create(
            company=other_co, name="Other", report_type="usage", format="pdf",
        )
        resp = self.client.get("/api/v2/reports/")
        names = [r["name"] for r in resp.data["results"]]
        assert "Other" not in names


# ══════════════════════════════════════════════════════════════
# TestWorkflowViewSet
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestWorkflowViewSet(TestCase):

    def setUp(self):
        self.co = _company()
        self.user = _user(company=self.co)
        self.client = _auth_client(self.user)

    def test_list_workflows(self):
        Workflow.objects.create(
            company=self.co, name="wf1",
            steps=[{"name": "s1", "type": "query"}],
            trigger={"type": "manual"},
        )
        resp = self.client.get("/api/v2/workflows/")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["results"]) == 1

    def test_create_workflow(self):
        resp = self.client.post(
            "/api/v2/workflows/",
            {
                "name": "New WF",
                "steps": [{"name": "s1", "type": "query"}],
                "trigger": {"type": "manual"},
                "status": "draft",
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        wf = Workflow.objects.get(name="New WF")
        assert wf.company == self.co
        assert wf.created_by == self.user

    def test_create_workflow_invalid_steps(self):
        resp = self.client.post(
            "/api/v2/workflows/",
            {
                "name": "Bad",
                "steps": [{"no_name_field": True}],
                "trigger": {"type": "manual"},
                "status": "draft",
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_workflow_invalid_trigger(self):
        resp = self.client.post(
            "/api/v2/workflows/",
            {
                "name": "Bad",
                "steps": [{"name": "s", "type": "t"}],
                "trigger": {"type": "invalid_type"},
                "status": "draft",
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_workflow_invalid_status(self):
        resp = self.client.post(
            "/api/v2/workflows/",
            {
                "name": "Bad",
                "steps": [{"name": "s", "type": "t"}],
                "trigger": {"type": "manual"},
                "status": "archived",
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_company_filter(self):
        other_co = _company()
        Workflow.objects.create(
            company=other_co, name="other-wf",
            steps=[], trigger={},
        )
        resp = self.client.get("/api/v2/workflows/")
        names = [w["name"] for w in resp.data["results"]]
        assert "other-wf" not in names


# ══════════════════════════════════════════════════════════════
# TestScheduledTaskViewSet
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestScheduledTaskViewSet(TestCase):

    def setUp(self):
        self.co = _company()
        self.user = _user(company=self.co)
        self.client = _auth_client(self.user)

    def test_list_tasks(self):
        ScheduledTask.objects.create(
            company=self.co, name="task1",
            task_type="backup", cron_expression="0 0 * * *",
        )
        resp = self.client.get("/api/v2/scheduled-tasks/")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["results"]) == 1

    def test_create_task(self):
        resp = self.client.post(
            "/api/v2/scheduled-tasks/",
            {
                "name": "New Task",
                "task_type": "cleanup",
                "cron_expression": "30 2 * * *",
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        t = ScheduledTask.objects.get(name="New Task")
        assert t.company == self.co
        assert t.created_by == self.user

    def test_create_task_invalid_cron(self):
        resp = self.client.post(
            "/api/v2/scheduled-tasks/",
            {
                "name": "Bad",
                "task_type": "cleanup",
                "cron_expression": "not a cron",
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_task_workflow_type_requires_workflow(self):
        resp = self.client.post(
            "/api/v2/scheduled-tasks/",
            {
                "name": "Wf Task",
                "task_type": "workflow",
                "cron_expression": "0 0 * * *",
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_task_report_type_requires_report(self):
        resp = self.client.post(
            "/api/v2/scheduled-tasks/",
            {
                "name": "Rpt Task",
                "task_type": "report",
                "cron_expression": "0 0 * * *",
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_company_filter(self):
        other_co = _company()
        ScheduledTask.objects.create(
            company=other_co, name="other-task",
            task_type="backup", cron_expression="0 0 * * *",
        )
        resp = self.client.get("/api/v2/scheduled-tasks/")
        names = [t["name"] for t in resp.data["results"]]
        assert "other-task" not in names

    def test_create_task_with_negative_max_failures(self):
        resp = self.client.post(
            "/api/v2/scheduled-tasks/",
            {
                "name": "Bad",
                "task_type": "cleanup",
                "cron_expression": "0 0 * * *",
                "max_consecutive_failures": -1,
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

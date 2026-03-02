"""
Tests for core, ensemble, competitive_insights, explainability, and
consortiums views that have low coverage.

Target modules:
  - core/views.py (66% → ~85%)
  - ensemble/views.py (49% → ~80%)
  - competitive_insights/views.py (53% → ~85%)
  - explainability/views.py (69% → ~85%)
  - consortiums/views.py (67% → ~85%)
"""

import uuid
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.consortiums.models import (
    Consortium,
    ConsortiumInvitation,
    ConsortiumMember,
    ContributionProof,
)
from apps.core.models import (
    Company,
    Report,
    ScheduledTask,
    ScheduledTaskRun,
    UsageTracking,
    Webhook,
    WebhookDelivery,
    Workflow,
    WorkflowRun,
)

pytestmark = pytest.mark.django_db


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
def company(db):
    return Company.objects.create(name="TestCo", email="test@testco.com", industry="technology")


@pytest.fixture
def other_company(db):
    return Company.objects.create(name="OtherCo", email="other@otherco.com", industry="finance")


@pytest.fixture
def user(company):
    from django.contrib.auth import get_user_model

    return get_user_model().objects.create_user(
        email="u@testco.com", password="pass1234", company=company
    )


@pytest.fixture
def other_user(other_company):
    from django.contrib.auth import get_user_model

    return get_user_model().objects.create_user(
        email="u@otherco.com", password="pass1234", company=other_company
    )


@pytest.fixture
def auth(user):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return c


@pytest.fixture
def other_auth(other_user):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(other_user).access_token}")
    return c


@pytest.fixture
def consortium(company):
    return Consortium.objects.create(
        name="TestConsortium", owner=company, status=Consortium.Status.ACTIVE
    )


@pytest.fixture
def membership(company, consortium):
    return ConsortiumMember.objects.create(
        company=company,
        consortium=consortium,
        role=ConsortiumMember.Role.OWNER,
        status=ConsortiumMember.Status.ACTIVE,
    )


# ══════════════════════════════════════════════════════════════════════
# CORE VIEWS
# ══════════════════════════════════════════════════════════════════════


class TestWebhookViewSet:
    url = "/api/v2/webhooks/"

    @pytest.fixture
    def webhook(self, company, user):
        return Webhook.objects.create(
            company=company,
            name="Test Hook",
            url="https://example.com/hook",
            events=["model.trained"],
        )

    def test_create(self, auth, company):
        r = auth.post(
            self.url,
            {
                "name": "New Hook",
                "url": "https://example.com/new",
                "events": ["model.trained", "model.created"],
            },
            format="json",
        )
        assert r.status_code == status.HTTP_201_CREATED
        assert "secret" in r.data

    def test_update(self, auth, webhook):
        r = auth.put(
            f"{self.url}{webhook.id}/",
            {
                "name": "Updated",
                "url": "https://example.com/updated",
                "events": ["model.trained"],
            },
            format="json",
        )
        assert r.status_code == status.HTTP_200_OK

    def test_partial_update(self, auth, webhook):
        r = auth.patch(
            f"{self.url}{webhook.id}/",
            {"name": "Partial"},
            format="json",
        )
        assert r.status_code == status.HTTP_200_OK

    def test_destroy(self, auth, webhook):
        r = auth.delete(f"{self.url}{webhook.id}/")
        assert r.status_code == status.HTTP_204_NO_CONTENT

    def test_test_action_timeout(self, auth, webhook):
        import requests as req_lib

        with patch("requests.post", side_effect=req_lib.exceptions.Timeout):
            r = auth.post(f"{self.url}{webhook.id}/test/")
            assert r.status_code == status.HTTP_408_REQUEST_TIMEOUT

    def test_test_action_connection_error(self, auth, webhook):
        import requests as req_lib

        with patch(
            "requests.post",
            side_effect=req_lib.exceptions.ConnectionError("fail"),
        ):
            r = auth.post(f"{self.url}{webhook.id}/test/")
            assert r.status_code == status.HTTP_502_BAD_GATEWAY

    def test_test_action_success(self, auth, webhook):
        mock_resp = type("MockResp", (), {"status_code": 200, "text": "ok"})()
        with patch("requests.post", return_value=mock_resp):
            r = auth.post(f"{self.url}{webhook.id}/test/")
            assert r.status_code == status.HTTP_200_OK
            assert r.data["success"] is True

    def test_regenerate_secret(self, auth, webhook):
        old_secret = webhook.secret
        r = auth.post(f"{self.url}{webhook.id}/regenerate_secret/")
        assert r.status_code == status.HTTP_200_OK
        webhook.refresh_from_db()
        assert webhook.secret != old_secret


class TestWebhookDeliveryViewSet:
    url = "/api/v2/webhook-deliveries/"

    @pytest.fixture
    def delivery(self, company, user):
        wh = Webhook.objects.create(
            company=company, name="H", url="https://ex.com", events=["model.trained"]
        )
        return WebhookDelivery.objects.create(
            webhook=wh, event_type="e", payload={"data": 1}, status="failed"
        )

    def test_list(self, auth, delivery):
        r = auth.get(self.url)
        assert r.status_code == status.HTTP_200_OK

    def test_retry_failed(self, auth, delivery):
        r = auth.post(f"{self.url}{delivery.id}/retry/")
        assert r.status_code == status.HTTP_200_OK
        delivery.refresh_from_db()
        assert delivery.status == WebhookDelivery.Status.PENDING

    def test_retry_not_failed(self, auth, delivery):
        delivery.status = "pending"
        delivery.save(update_fields=["status"])
        r = auth.post(f"{self.url}{delivery.id}/retry/")
        assert r.status_code == status.HTTP_400_BAD_REQUEST


class TestUsageStatsViewSet:
    url = "/api/v2/usage-stats/"

    def test_list(self, auth, company):
        UsageTracking.objects.create(
            company=company,
            date=timezone.now().date(),
            api_requests=100,
            predictions=50,
        )
        r = auth.get(f"{self.url}")
        assert r.status_code == status.HTTP_200_OK
        assert "tier" in r.data

    def test_list_no_company(self, db):
        from django.contrib.auth import get_user_model

        u = get_user_model().objects.create_user(email="nc@t.com", password="p", company=None)
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(u).access_token}")
        r = c.get(f"{self.url}")
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_daily(self, auth, company):
        r = auth.get(f"{self.url}daily/")
        assert r.status_code == status.HTTP_200_OK

    def test_daily_no_company(self, db):
        from django.contrib.auth import get_user_model

        u = get_user_model().objects.create_user(email="nc2@t.com", password="p", company=None)
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(u).access_token}")
        r = c.get(f"{self.url}daily/")
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_monthly(self, auth, company):
        r = auth.get(f"{self.url}monthly/")
        assert r.status_code == status.HTTP_200_OK

    def test_monthly_no_company(self, db):
        from django.contrib.auth import get_user_model

        u = get_user_model().objects.create_user(email="nc3@t.com", password="p", company=None)
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(u).access_token}")
        r = c.get(f"{self.url}monthly/")
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_limits(self, auth, company):
        r = auth.get(f"{self.url}limits/")
        assert r.status_code == status.HTTP_200_OK
        assert "tier" in r.data

    def test_limits_no_company(self, db):
        from django.contrib.auth import get_user_model

        u = get_user_model().objects.create_user(email="nc4@t.com", password="p", company=None)
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(u).access_token}")
        r = c.get(f"{self.url}limits/")
        assert r.status_code == status.HTTP_403_FORBIDDEN


class TestReportViewSet:
    url = "/api/v2/reports/"

    @pytest.fixture
    def report(self, company, user):
        return Report.objects.create(
            company=company,
            created_by=user,
            name="Test Report",
            report_type=Report.ReportType.PERFORMANCE,
            format=Report.Format.PDF,
            status=Report.Status.PENDING,
        )

    def test_create(self, auth):
        r = auth.post(
            self.url,
            {"name": "New Report", "report_type": "performance", "format": "pdf"},
            format="json",
        )
        assert r.status_code == status.HTTP_201_CREATED

    def test_generate_pending(self, auth, report):
        r = auth.post(f"{self.url}{report.id}/generate/")
        assert r.status_code == status.HTTP_200_OK
        report.refresh_from_db()
        assert report.status == Report.Status.COMPLETED

    def test_generate_failed(self, auth, report):
        report.status = Report.Status.FAILED
        report.save(update_fields=["status"])
        r = auth.post(f"{self.url}{report.id}/generate/")
        assert r.status_code == status.HTTP_200_OK

    def test_generate_completed_rejects(self, auth, report):
        report.status = Report.Status.COMPLETED
        report.save(update_fields=["status"])
        r = auth.post(f"{self.url}{report.id}/generate/")
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_download_completed(self, auth, report):
        report.mark_generating()
        report.mark_completed("/tmp/report.pdf", 5000)
        r = auth.get(f"{self.url}{report.id}/download/")
        assert r.status_code == status.HTTP_200_OK
        assert "download_url" in r.data

    def test_download_not_ready(self, auth, report):
        r = auth.get(f"{self.url}{report.id}/download/")
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_download_expired(self, auth, report):
        report.status = Report.Status.COMPLETED
        report.download_expires_at = timezone.now() - timedelta(hours=1)
        report.save()
        r = auth.get(f"{self.url}{report.id}/download/")
        assert r.status_code == status.HTTP_410_GONE


class TestWorkflowViewSet:
    url = "/api/v2/workflows/"

    @pytest.fixture
    def workflow(self, company, user):
        return Workflow.objects.create(
            company=company,
            created_by=user,
            name="Test WF",
            steps=[{"name": "step1", "type": "action"}],
            status=Workflow.Status.ACTIVE,
        )

    def test_create(self, auth):
        r = auth.post(
            self.url,
            {"name": "New WF", "steps": [{"name": "s1", "type": "action"}], "trigger": {"type": "manual"}},
            format="json",
        )
        assert r.status_code == status.HTTP_201_CREATED

    def test_run_active(self, auth, workflow):
        r = auth.post(f"{self.url}{workflow.id}/run/", {"input_data": {}}, format="json")
        assert r.status_code == status.HTTP_201_CREATED

    def test_run_inactive(self, auth, workflow):
        workflow.status = Workflow.Status.DRAFT
        workflow.save(update_fields=["status"])
        r = auth.post(f"{self.url}{workflow.id}/run/", format="json")
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_activate_draft(self, auth, workflow):
        workflow.status = Workflow.Status.DRAFT
        workflow.save(update_fields=["status"])
        r = auth.post(f"{self.url}{workflow.id}/activate/")
        assert r.status_code == status.HTTP_200_OK
        workflow.refresh_from_db()
        assert workflow.status == Workflow.Status.ACTIVE

    def test_activate_paused(self, auth, workflow):
        workflow.status = Workflow.Status.PAUSED
        workflow.save(update_fields=["status"])
        r = auth.post(f"{self.url}{workflow.id}/activate/")
        assert r.status_code == status.HTTP_200_OK

    def test_activate_already_active(self, auth, workflow):
        r = auth.post(f"{self.url}{workflow.id}/activate/")
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_pause_active(self, auth, workflow):
        r = auth.post(f"{self.url}{workflow.id}/pause/")
        assert r.status_code == status.HTTP_200_OK
        workflow.refresh_from_db()
        assert workflow.status == Workflow.Status.PAUSED

    def test_pause_not_active(self, auth, workflow):
        workflow.status = Workflow.Status.DRAFT
        workflow.save(update_fields=["status"])
        r = auth.post(f"{self.url}{workflow.id}/pause/")
        assert r.status_code == status.HTTP_400_BAD_REQUEST


class TestWorkflowRunViewSet:
    url = "/api/v2/workflow-runs/"

    @pytest.fixture
    def wf_run(self, company, user):
        wf = Workflow.objects.create(
            company=company, created_by=user, name="WF", status=Workflow.Status.ACTIVE
        )
        run = WorkflowRun.objects.create(
            workflow=wf, triggered_by=user, trigger_type="manual", status=WorkflowRun.Status.RUNNING
        )
        run.started_at = timezone.now()
        run.save()
        return run

    def test_cancel_running(self, auth, wf_run):
        r = auth.post(f"{self.url}{wf_run.id}/cancel/")
        assert r.status_code == status.HTTP_200_OK
        wf_run.refresh_from_db()
        assert wf_run.status == WorkflowRun.Status.CANCELLED

    def test_cancel_not_running(self, auth, wf_run):
        wf_run.status = WorkflowRun.Status.COMPLETED
        wf_run.save(update_fields=["status"])
        r = auth.post(f"{self.url}{wf_run.id}/cancel/")
        assert r.status_code == status.HTTP_400_BAD_REQUEST


class TestScheduledTaskViewSet:
    url = "/api/v2/scheduled-tasks/"

    @pytest.fixture
    def task(self, company, user):
        return ScheduledTask.objects.create(
            company=company,
            created_by=user,
            name="Daily task",
            task_type=ScheduledTask.TaskType.CUSTOM,
            cron_expression="0 0 * * *",
            status=ScheduledTask.Status.ACTIVE,
        )

    def test_create(self, auth):
        r = auth.post(
            self.url,
            {
                "name": "New Task",
                "task_type": "custom",
                "cron_expression": "0 0 * * *",
            },
            format="json",
        )
        assert r.status_code == status.HTTP_201_CREATED

    def test_run_now(self, auth, task):
        r = auth.post(f"{self.url}{task.id}/run_now/")
        assert r.status_code == status.HTTP_201_CREATED

    def test_run_now_inactive(self, auth, task):
        task.status = ScheduledTask.Status.PAUSED
        task.save(update_fields=["status"])
        r = auth.post(f"{self.url}{task.id}/run_now/")
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_run_now_workflow_task(self, auth, company, user):
        wf = Workflow.objects.create(
            company=company, created_by=user, name="WF", status=Workflow.Status.ACTIVE
        )
        task = ScheduledTask.objects.create(
            company=company,
            created_by=user,
            name="WF task",
            task_type=ScheduledTask.TaskType.WORKFLOW,
            cron_expression="0 0 * * *",
            status=ScheduledTask.Status.ACTIVE,
            workflow=wf,
        )
        r = auth.post(f"{self.url}{task.id}/run_now/")
        assert r.status_code == status.HTTP_201_CREATED

    def test_run_now_report_task(self, auth, company, user):
        report = Report.objects.create(
            company=company,
            created_by=user,
            name="R",
            report_type="performance",
        )
        task = ScheduledTask.objects.create(
            company=company,
            created_by=user,
            name="Report task",
            task_type=ScheduledTask.TaskType.REPORT,
            cron_expression="0 0 * * *",
            status=ScheduledTask.Status.ACTIVE,
            report=report,
        )
        r = auth.post(f"{self.url}{task.id}/run_now/")
        assert r.status_code == status.HTTP_201_CREATED

    def test_pause(self, auth, task):
        r = auth.post(f"{self.url}{task.id}/pause/")
        assert r.status_code == status.HTTP_200_OK
        task.refresh_from_db()
        assert task.status == ScheduledTask.Status.PAUSED

    def test_pause_not_active(self, auth, task):
        task.status = ScheduledTask.Status.PAUSED
        task.save(update_fields=["status"])
        r = auth.post(f"{self.url}{task.id}/pause/")
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_resume(self, auth, task):
        task.status = ScheduledTask.Status.PAUSED
        task.save(update_fields=["status"])
        r = auth.post(f"{self.url}{task.id}/resume/")
        assert r.status_code == status.HTTP_200_OK
        task.refresh_from_db()
        assert task.status == ScheduledTask.Status.ACTIVE

    def test_resume_not_paused(self, auth, task):
        r = auth.post(f"{self.url}{task.id}/resume/")
        assert r.status_code == status.HTTP_400_BAD_REQUEST


# ══════════════════════════════════════════════════════════════════════
# ENSEMBLE VIEWS
# ══════════════════════════════════════════════════════════════════════


class TestEnsembleViewSet:
    url = "/api/v2/ensemble/ensembles/"

    @pytest.fixture
    def ml_models(self, company, consortium):
        from apps.models.models import MLModel

        m1 = MLModel.objects.create(
            name="M1", owner=company, consortium=consortium,
            model_type=MLModel.ModelType.LOGISTIC_REGRESSION,
            status=MLModel.Status.TRAINED,
        )
        m2 = MLModel.objects.create(
            name="M2", owner=company, consortium=consortium,
            model_type=MLModel.ModelType.LINEAR_REGRESSION,
            status=MLModel.Status.TRAINED,
        )
        return m1, m2

    @pytest.fixture
    def ensemble(self, company, user):
        from apps.ensemble.models import Ensemble

        return Ensemble.objects.create(
            name="Test Ensemble",
            owner=company,
            ensemble_type=Ensemble.EnsembleType.VOTING,
            status=Ensemble.Status.DRAFT,
        )

    def test_models_get(self, auth, ensemble):
        r = auth.get(f"{self.url}{ensemble.id}/models/")
        assert r.status_code == status.HTTP_200_OK

    def test_models_post(self, auth, ensemble, ml_models):
        m1, _ = ml_models
        r = auth.post(
            f"{self.url}{ensemble.id}/models/",
            {"model": str(m1.id), "weight": 1.0},
            format="json",
        )
        assert r.status_code == status.HTTP_201_CREATED

    def test_models_post_duplicate(self, auth, ensemble, ml_models):
        from apps.ensemble.models import EnsembleModel

        m1, _ = ml_models
        EnsembleModel.objects.create(ensemble=ensemble, model=m1, weight=1.0)
        r = auth.post(
            f"{self.url}{ensemble.id}/models/",
            {"model": str(m1.id)},
            format="json",
        )
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_add_model(self, auth, ensemble, ml_models):
        m1, _ = ml_models
        r = auth.post(
            f"{self.url}{ensemble.id}/add_model/",
            {"model_id": str(m1.id), "weight": 1.5},
            format="json",
        )
        assert r.status_code == status.HTTP_201_CREATED

    def test_add_model_duplicate(self, auth, ensemble, ml_models):
        from apps.ensemble.models import EnsembleModel

        m1, _ = ml_models
        EnsembleModel.objects.create(ensemble=ensemble, model=m1, weight=1.0)
        r = auth.post(
            f"{self.url}{ensemble.id}/add_model/",
            {"model_id": str(m1.id), "weight": 1.0},
            format="json",
        )
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_remove_model(self, auth, ensemble, ml_models):
        from apps.ensemble.models import EnsembleModel

        m1, _ = ml_models
        EnsembleModel.objects.create(ensemble=ensemble, model=m1, weight=1.0)
        r = auth.post(
            f"{self.url}{ensemble.id}/remove_model/",
            {"model_id": str(m1.id)},
            format="json",
        )
        assert r.status_code == status.HTTP_200_OK

    def test_remove_model_no_id(self, auth, ensemble):
        r = auth.post(f"{self.url}{ensemble.id}/remove_model/", {}, format="json")
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_remove_model_not_in(self, auth, ensemble):
        r = auth.post(
            f"{self.url}{ensemble.id}/remove_model/",
            {"model_id": str(uuid.uuid4())},
            format="json",
        )
        assert r.status_code == status.HTTP_404_NOT_FOUND

    def test_update_weights(self, auth, ensemble, ml_models):
        from apps.ensemble.models import EnsembleModel

        m1, m2 = ml_models
        EnsembleModel.objects.create(ensemble=ensemble, model=m1, weight=1.0)
        EnsembleModel.objects.create(ensemble=ensemble, model=m2, weight=1.0)
        r = auth.post(
            f"{self.url}{ensemble.id}/update_weights/",
            {"weights": {str(m1.id): 2.0, str(m2.id): 0.5}},
            format="json",
        )
        assert r.status_code == status.HTTP_200_OK

    def test_update_weights_empty(self, auth, ensemble):
        r = auth.post(
            f"{self.url}{ensemble.id}/update_weights/", {"weights": {}}, format="json"
        )
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_activate_enough_models(self, auth, ensemble, ml_models):
        from apps.ensemble.models import EnsembleModel

        m1, m2 = ml_models
        EnsembleModel.objects.create(ensemble=ensemble, model=m1, weight=1.0)
        EnsembleModel.objects.create(ensemble=ensemble, model=m2, weight=1.0)
        r = auth.post(f"{self.url}{ensemble.id}/activate/")
        assert r.status_code == status.HTTP_200_OK

    def test_activate_not_enough_models(self, auth, ensemble):
        r = auth.post(f"{self.url}{ensemble.id}/activate/")
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_predict_active(self, auth, ensemble, ml_models):
        from apps.ensemble.models import Ensemble, EnsembleModel

        m1, m2 = ml_models
        EnsembleModel.objects.create(ensemble=ensemble, model=m1, weight=1.0, is_active=True)
        EnsembleModel.objects.create(ensemble=ensemble, model=m2, weight=1.0, is_active=True)
        ensemble.status = Ensemble.Status.ACTIVE
        ensemble.save(update_fields=["status"])
        r = auth.post(
            f"{self.url}{ensemble.id}/predict/",
            {"X": [[1, 2], [3, 4]]},
            format="json",
        )
        assert r.status_code == status.HTTP_200_OK

    def test_predict_inactive(self, auth, ensemble):
        r = auth.post(
            f"{self.url}{ensemble.id}/predict/",
            {"X": [[1, 2]]},
            format="json",
        )
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_evaluations(self, auth, ensemble):
        r = auth.get(f"{self.url}{ensemble.id}/evaluations/")
        assert r.status_code == status.HTTP_200_OK


# ══════════════════════════════════════════════════════════════════════
# COMPETITIVE INSIGHTS VIEWS
# ══════════════════════════════════════════════════════════════════════


class TestIndustryBenchmarkViewSet:
    url = "/api/v2/competitive/benchmarks/"

    @pytest.fixture
    def benchmark(self, db):
        from apps.competitive_insights.models import IndustryBenchmark

        return IndustryBenchmark.objects.create(
            industry="technology",
            metric_name="accuracy",
            metric_type="percentage",
            unit="%",
            p10_value=60,
            p25_value=70,
            p50_value=80,
            p75_value=90,
            p90_value=95,
            sample_size=100,
            period_start=timezone.now().date() - timedelta(days=30),
            period_end=timezone.now().date(),
        )

    def test_list(self, auth, benchmark):
        r = auth.get(self.url)
        assert r.status_code == status.HTTP_200_OK

    def test_industries(self, auth, benchmark):
        r = auth.get(f"{self.url}industries/")
        assert r.status_code == status.HTTP_200_OK
        assert "technology" in r.data

    def test_metrics(self, auth, benchmark):
        r = auth.get(f"{self.url}metrics/?industry=technology")
        assert r.status_code == status.HTTP_200_OK

    def test_metrics_no_industry(self, auth):
        r = auth.get(f"{self.url}metrics/")
        assert r.status_code == status.HTTP_400_BAD_REQUEST


class TestCompanyMetricViewSet:
    url = "/api/v2/competitive/metrics/"

    @pytest.fixture
    def benchmark(self, db):
        from apps.competitive_insights.models import IndustryBenchmark

        return IndustryBenchmark.objects.create(
            industry="technology",
            metric_name="accuracy",
            metric_type="percentage",
            unit="%",
            p10_value=60,
            p25_value=70,
            p50_value=80,
            p75_value=90,
            p90_value=95,
            sample_size=100,
            period_start=timezone.now().date() - timedelta(days=30),
            period_end=timezone.now().date(),
        )

    def test_comparison(self, auth, company, benchmark):
        r = auth.get(f"{self.url}comparison/")
        assert r.status_code == status.HTTP_200_OK
        assert "industry" in r.data

    def test_comparison_no_company(self, db):
        from django.contrib.auth import get_user_model

        u = get_user_model().objects.create_user(email="nc5@t.com", password="p", company=None)
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(u).access_token}")
        r = c.get(f"{self.url}comparison/")
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_comparison_no_industry(self, db):
        from django.contrib.auth import get_user_model

        co = Company.objects.create(name="NoInd", email="noind@t.com", industry="")
        u = get_user_model().objects.create_user(email="ni@t.com", password="p", company=co)
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(u).access_token}")
        r = c.get(f"{self.url}comparison/")
        assert r.status_code == status.HTTP_400_BAD_REQUEST


class TestCompetitiveReportViewSet:
    url = "/api/v2/competitive/reports/"

    @pytest.fixture
    def report(self, company, user):
        from apps.competitive_insights.models import CompetitiveReport

        return CompetitiveReport.objects.create(
            company=company,
            title="Test Report",
            industry="technology",
            period_start=timezone.now().date() - timedelta(days=30),
            period_end=timezone.now().date(),
            status=CompetitiveReport.Status.PENDING,
        )

    def test_generate(self, auth, report):
        r = auth.post(f"{self.url}{report.id}/generate/")
        assert r.status_code == status.HTTP_200_OK
        report.refresh_from_db()
        from apps.competitive_insights.models import CompetitiveReport

        assert report.status == CompetitiveReport.Status.COMPLETED

    def test_generate_already_generating(self, auth, report):
        from apps.competitive_insights.models import CompetitiveReport

        report.status = CompetitiveReport.Status.GENERATING
        report.save(update_fields=["status"])
        r = auth.post(f"{self.url}{report.id}/generate/")
        assert r.status_code == status.HTTP_400_BAD_REQUEST


# ══════════════════════════════════════════════════════════════════════
# EXPLAINABILITY VIEWS
# ══════════════════════════════════════════════════════════════════════


class TestExplanationRequestViewSet:
    url = "/api/v2/explainability/requests/"

    @pytest.fixture
    def explanation(self, company, user, consortium, membership):
        from apps.explainability.models import ExplanationRequest

        return ExplanationRequest.objects.create(
            consortium=consortium,
            requester=company,
            explanation_type=ExplanationRequest.ExplanationType.FEATURE_IMPORTANCE,
            status=ExplanationRequest.Status.COMPLETED,
            explanation={"features": []},
        )

    def test_list(self, auth, explanation):
        r = auth.get(self.url)
        assert r.status_code == status.HTTP_200_OK


class TestModelInsightViewSet:
    url = "/api/v2/explainability/insights/"

    @pytest.fixture
    def insight(self, consortium, membership):
        from apps.explainability.models import ModelInsight

        return ModelInsight.objects.create(
            consortium=consortium,
            insight_type=ModelInsight.InsightType.PERFORMANCE,
            severity="info",
            title="Test Insight",
            description="Description",
        )

    def test_acknowledge(self, auth, insight):
        r = auth.post(f"{self.url}{insight.id}/acknowledge/")
        assert r.status_code == status.HTTP_200_OK
        insight.refresh_from_db()
        assert insight.acknowledged is True

    def test_acknowledge_already(self, auth, insight, user):
        insight.acknowledge(user)
        r = auth.post(f"{self.url}{insight.id}/acknowledge/")
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_summary(self, auth, insight):
        r = auth.get(f"{self.url}summary/")
        assert r.status_code == status.HTTP_200_OK
        assert "total" in r.data


class TestExplainabilityDashboard:
    url = "/api/v2/explainability/dashboard/"

    def test_dashboard(self, auth, company, consortium, membership):
        r = auth.get(self.url)
        assert r.status_code == status.HTTP_200_OK
        assert "total_requests" in r.data

    def test_dashboard_no_company(self, db):
        from django.contrib.auth import get_user_model

        u = get_user_model().objects.create_user(email="nc6@t.com", password="p", company=None)
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(u).access_token}")
        r = c.get(self.url)
        assert r.status_code == status.HTTP_403_FORBIDDEN


# ══════════════════════════════════════════════════════════════════════
# CONSORTIUM VIEWS
# ══════════════════════════════════════════════════════════════════════


class TestConsortiumViewSetActions:
    url = "/api/v2/consortiums/"

    def test_owned(self, auth, consortium, membership):
        r = auth.get(f"{self.url}owned/")
        assert r.status_code == status.HTTP_200_OK

    def test_owned_no_company(self, db):
        from django.contrib.auth import get_user_model

        u = get_user_model().objects.create_user(email="nc7@t.com", password="p", company=None)
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(u).access_token}")
        r = c.get(f"{self.url}owned/")
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_stats(self, auth, consortium, membership):
        r = auth.get(f"{self.url}{consortium.id}/stats/")
        assert r.status_code == status.HTTP_200_OK
        assert "total_members" in r.data

    def test_start_training_not_active(self, auth, consortium, membership):
        consortium.status = Consortium.Status.COMPLETED
        consortium.save(update_fields=["status"])
        r = auth.post(f"{self.url}{consortium.id}/start_training/")
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_start_training_not_enough_members(self, auth, consortium, membership):
        consortium.min_members = 5
        consortium.save(update_fields=["min_members"])
        r = auth.post(f"{self.url}{consortium.id}/start_training/")
        assert r.status_code == status.HTTP_400_BAD_REQUEST


class TestConsortiumMemberViewSetActions:

    @pytest.fixture
    def pending_member(self, consortium, other_company):
        return ConsortiumMember.objects.create(
            company=other_company,
            consortium=consortium,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.PENDING,
        )

    def _url(self, consortium_id, suffix=""):
        return f"/api/v2/consortiums/{consortium_id}/members/{suffix}"

    def test_approve(self, auth, consortium, membership, pending_member):
        r = auth.post(self._url(consortium.id, f"{pending_member.id}/approve/"))
        assert r.status_code == status.HTTP_200_OK
        pending_member.refresh_from_db()
        assert pending_member.status == ConsortiumMember.Status.ACTIVE

    def test_approve_not_pending(self, auth, consortium, membership, pending_member):
        pending_member.status = ConsortiumMember.Status.ACTIVE
        pending_member.save(update_fields=["status"])
        r = auth.post(self._url(consortium.id, f"{pending_member.id}/approve/"))
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_remove(self, auth, consortium, membership, pending_member):
        pending_member.status = ConsortiumMember.Status.ACTIVE
        pending_member.save(update_fields=["status"])
        r = auth.post(self._url(consortium.id, f"{pending_member.id}/remove/"))
        assert r.status_code == status.HTTP_200_OK
        pending_member.refresh_from_db()
        assert pending_member.status == ConsortiumMember.Status.REMOVED

    def test_remove_owner_fails(self, auth, consortium, membership):
        r = auth.post(self._url(consortium.id, f"{membership.id}/remove/"))
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_leave(self, other_auth, consortium, membership, other_company):
        m = ConsortiumMember.objects.create(
            company=other_company,
            consortium=consortium,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        r = other_auth.post(self._url(consortium.id, "leave/"))
        assert r.status_code == status.HTTP_200_OK
        m.refresh_from_db()
        assert m.status == ConsortiumMember.Status.LEFT

    def test_leave_not_member(self, other_auth, consortium, membership):
        r = other_auth.post(self._url(consortium.id, "leave/"))
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_leave_owner_fails(self, auth, consortium, membership):
        r = auth.post(self._url(consortium.id, "leave/"))
        assert r.status_code == status.HTTP_400_BAD_REQUEST


class TestContributionProofViewSetActions:

    @pytest.fixture
    def contribution(self, company, consortium):
        return ContributionProof.objects.create(
            company=company,
            consortium=consortium,
            data_hash="abc123def456",
            record_count=100,
            feature_count=10,
            checksum="abc123checksum",
            verified=True,
        )

    def _url(self, consortium_id, suffix=""):
        return f"/api/v2/consortiums/{consortium_id}/contributions/{suffix}"

    def test_my_contributions(self, auth, consortium, membership, contribution):
        r = auth.get(self._url(consortium.id, "my_contributions/"))
        assert r.status_code == status.HTTP_200_OK

    def test_summary(self, auth, consortium, membership, contribution):
        r = auth.get(self._url(consortium.id, "summary/"))
        assert r.status_code == status.HTTP_200_OK


class TestConsortiumInvitationViewSetActions:
    url = "/api/v2/consortiums/invitations/"

    @pytest.fixture
    def invitation(self, company, consortium):
        return ConsortiumInvitation.objects.create(
            consortium=consortium,
            inviter=company,
            invitee_email="other@otherco.com",
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumInvitation.Status.PENDING,
            expires_at=timezone.now() + timedelta(days=7),
        )

    def test_accept(self, other_auth, invitation, other_company):
        r = other_auth.post(f"{self.url}{invitation.id}/accept/")
        assert r.status_code == status.HTTP_200_OK
        invitation.refresh_from_db()
        assert invitation.status == ConsortiumInvitation.Status.ACCEPTED

    def test_accept_wrong_company(self, auth, invitation):
        r = auth.post(f"{self.url}{invitation.id}/accept/")
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_accept_not_pending(self, other_auth, invitation):
        invitation.status = ConsortiumInvitation.Status.ACCEPTED
        invitation.save(update_fields=["status"])
        r = other_auth.post(f"{self.url}{invitation.id}/accept/")
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_accept_expired(self, other_auth, invitation):
        invitation.expires_at = timezone.now() - timedelta(days=1)
        invitation.save(update_fields=["expires_at"])
        r = other_auth.post(f"{self.url}{invitation.id}/accept/")
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_decline(self, other_auth, invitation):
        r = other_auth.post(f"{self.url}{invitation.id}/decline/")
        assert r.status_code == status.HTTP_200_OK
        invitation.refresh_from_db()
        assert invitation.status == ConsortiumInvitation.Status.DECLINED

    def test_decline_wrong_company(self, auth, invitation):
        r = auth.post(f"{self.url}{invitation.id}/decline/")
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_decline_not_pending(self, other_auth, invitation):
        invitation.status = ConsortiumInvitation.Status.DECLINED
        invitation.save(update_fields=["status"])
        r = other_auth.post(f"{self.url}{invitation.id}/decline/")
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_received(self, other_auth, invitation, other_company):
        r = other_auth.get(f"{self.url}received/")
        assert r.status_code == status.HTTP_200_OK

    def test_sent(self, auth, invitation):
        r = auth.get(f"{self.url}sent/")
        assert r.status_code == status.HTTP_200_OK

"""
Tests for all core models: User, Company, APIKey, AuditLog,
UsageTracking, Webhook, Report, Workflow, ScheduledTask.
"""

import hashlib
import uuid
from datetime import timedelta

import pytest
from django.test import TestCase
from django.utils import timezone

from apps.core.models import (
    APIKey,
    AuditLog,
    Company,
    Report,
    ScheduledTask,
    ScheduledTaskRun,
    UsageTracking,
    User,
    Webhook,
    WebhookDelivery,
    Workflow,
    WorkflowRun,
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


# ══════════════════════════════════════════════════════════════
# TestUser
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestUser(TestCase):

    def test_create_user_basic(self):
        user = User.objects.create_user(
            email="alice@example.com", password="SecurePass123!"
        )
        assert user.email == "alice@example.com"
        assert user.check_password("SecurePass123!")
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False

    def test_create_user_normalizes_email(self):
        user = User.objects.create_user(
            email="Bob@Example.COM", password="SecurePass123!"
        )
        assert user.email == "Bob@example.com"

    def test_create_user_without_email_raises(self):
        with pytest.raises(ValueError, match="email"):
            User.objects.create_user(email="", password="SecurePass123!")

    def test_create_superuser(self):
        su = User.objects.create_superuser(
            email="admin@example.com", password="AdminPass123!"
        )
        assert su.is_staff is True
        assert su.is_superuser is True
        assert su.is_active is True

    def test_create_superuser_not_staff_raises(self):
        with pytest.raises(ValueError, match="is_staff"):
            User.objects.create_superuser(
                email="bad@example.com", password="Pass1234!", is_staff=False
            )

    def test_create_superuser_not_superuser_raises(self):
        with pytest.raises(ValueError, match="is_superuser"):
            User.objects.create_superuser(
                email="bad@example.com", password="Pass1234!", is_superuser=False
            )

    def test_str_returns_email(self):
        user = _user()
        assert str(user) == user.email

    def test_get_full_name(self):
        user = _user(first_name="Alice", last_name="Smith")
        assert user.get_full_name() == "Alice Smith"

    def test_get_full_name_empty_returns_email(self):
        user = _user(first_name="", last_name="")
        assert user.get_full_name() == user.email

    def test_get_short_name(self):
        user = _user(first_name="Alice")
        assert user.get_short_name() == "Alice"

    def test_get_short_name_no_first_name(self):
        user = _user(first_name="", email="bob@example.com")
        assert user.get_short_name() == "bob"

    def test_user_uuid_pk(self):
        user = _user()
        assert isinstance(user.id, uuid.UUID)

    def test_user_company_fk(self):
        co = _company()
        user = _user(company=co)
        assert user.company == co
        assert user in co.users.all()


# ══════════════════════════════════════════════════════════════
# TestCompany
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestCompany(TestCase):

    def test_create_company(self):
        co = _company(name="Acme")
        assert co.name == "Acme"
        assert co.tier == "free"
        assert co.is_active is True
        assert isinstance(co.id, uuid.UUID)

    def test_str_returns_name(self):
        co = _company(name="FooCorp")
        assert str(co) == "FooCorp"

    # ── Tier limits ──

    def test_rate_limit_per_tier(self):
        for tier, expected in Company.TIER_RATE_LIMITS.items():
            co = _company(tier=tier)
            assert co.rate_limit == expected

    def test_daily_limit_per_tier(self):
        for tier, expected in Company.TIER_DAILY_LIMITS.items():
            co = _company(tier=tier)
            assert co.daily_limit == expected

    def test_model_limit_per_tier(self):
        for tier, expected in Company.TIER_MODEL_LIMITS.items():
            co = _company(tier=tier)
            assert co.model_limit == expected

    def test_consortium_limit_per_tier(self):
        for tier, expected in Company.TIER_CONSORTIUM_LIMITS.items():
            co = _company(tier=tier)
            assert co.consortium_limit == expected

    def test_upload_limit_per_tier(self):
        for tier, expected in Company.TIER_UPLOAD_LIMITS.items():
            co = _company(tier=tier)
            assert co.upload_limit == expected

    def test_training_limit_per_tier(self):
        for tier, expected in Company.TIER_TRAINING_LIMITS.items():
            co = _company(tier=tier)
            assert co.training_limit == expected

    def test_sandbox_limit_per_tier(self):
        for tier, expected in Company.TIER_SANDBOX_LIMITS.items():
            co = _company(tier=tier)
            assert co.sandbox_limit == expected

    # ── Custom overrides ──

    def test_custom_rate_limit_overrides_tier(self):
        co = _company(tier="free", custom_rate_limit=999)
        assert co.rate_limit == 999

    def test_custom_daily_limit_overrides_tier(self):
        co = _company(tier="free", custom_daily_limit=7777)
        assert co.daily_limit == 7777

    # ── Trial fields ──

    def test_new_company_not_trial(self):
        co = _company()
        assert co.is_trial is False
        assert co.trial_expired is False
        assert co.trial_days_remaining == 0

    def test_start_trial(self):
        co = _company()
        co.start_trial()
        co.refresh_from_db()
        assert co.trial_started_at is not None
        assert co.trial_expires_at is not None
        assert co.is_trial is True
        assert co.trial_days_remaining >= 13

    def test_trial_expired(self):
        co = _company()
        co.trial_started_at = timezone.now() - timedelta(days=15)
        co.trial_expires_at = timezone.now() - timedelta(hours=1)
        co.save()
        assert co.trial_expired is True
        assert co.trial_days_remaining == 0

    def test_is_trial_false_for_paid_tier(self):
        co = _company(tier="starter")
        co.trial_expires_at = timezone.now() + timedelta(days=5)
        co.save()
        assert co.is_trial is False

    # ── Tier transition ──

    def test_tier_transition_updates_limits(self):
        co = _company(tier="free")
        assert co.daily_limit == 100
        co.tier = "professional"
        assert co.daily_limit == 50_000


# ══════════════════════════════════════════════════════════════
# TestAPIKey
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestAPIKey(TestCase):

    def test_generate_key_format(self):
        raw, hashed = APIKey.generate_key()
        assert raw.startswith("fheml_")
        assert len(hashed) == 64  # SHA-256 hex digest

    def test_generate_key_hash_matches(self):
        raw, hashed = APIKey.generate_key()
        assert hashlib.sha256(raw.encode()).hexdigest() == hashed

    def test_hash_key_classmethod(self):
        raw = "test_key_12345"
        expected = hashlib.sha256(raw.encode()).hexdigest()
        assert APIKey.hash_key(raw) == expected

    def test_create_api_key(self):
        co = _company()
        user = _user(company=co)
        raw, hashed = APIKey.generate_key()
        key = APIKey.objects.create(
            name="prod-key",
            key_hash=hashed,
            company=co,
            created_by=user,
            prefix=raw[:13],
            permissions=["read", "write"],
        )
        assert key.name == "prod-key"
        assert key.is_active is True
        assert key.company == co
        assert key.created_by == user

    def test_str_representation(self):
        co = _company(name="Acme")
        key = APIKey.objects.create(
            name="my-key",
            key_hash="a" * 64,
            company=co,
            prefix="fheml_ab",
        )
        assert "my-key" in str(key)
        assert "Acme" in str(key)

    def test_has_permission(self):
        co = _company()
        key = APIKey.objects.create(
            name="k", key_hash="b" * 64, company=co,
            permissions=["read"],
        )
        assert key.has_permission("read") is True
        assert key.has_permission("write") is False

    def test_admin_has_all_permissions(self):
        co = _company()
        key = APIKey.objects.create(
            name="k", key_hash="c" * 64, company=co,
            permissions=["admin"],
        )
        assert key.has_permission("read") is True
        assert key.has_permission("write") is True
        assert key.has_permission("admin") is True

    def test_update_last_used(self):
        co = _company()
        key = APIKey.objects.create(
            name="k", key_hash="d" * 64, company=co,
        )
        assert key.last_used_at is None
        key.update_last_used()
        key.refresh_from_db()
        assert key.last_used_at is not None

    def test_expiration_field(self):
        co = _company()
        expires = timezone.now() + timedelta(days=30)
        key = APIKey.objects.create(
            name="exp", key_hash="e" * 64, company=co,
            expires_at=expires,
        )
        assert key.expires_at == expires


# ══════════════════════════════════════════════════════════════
# TestAuditLog
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestAuditLog(TestCase):

    def test_create_audit_log(self):
        log = AuditLog.objects.create(
            action="test_action",
            resource_type="test",
            resource_id="123",
        )
        assert log.action == "test_action"
        assert str(log).startswith("test_action")

    def test_audit_log_with_user(self):
        co = _company()
        user = _user(company=co)
        log = AuditLog.objects.create(
            user=user,
            company=co,
            action="user_login",
            resource_type="user",
            resource_id=str(user.id),
        )
        assert log.user == user
        assert log.company == co

    def test_log_classmethod(self):
        """AuditLog.log() from a real request (simulated with RequestFactory)."""
        from rest_framework.test import APIRequestFactory

        co = _company()
        user = _user(company=co)
        factory = APIRequestFactory()
        request = factory.get("/api/v2/health/")
        request.user = user
        request.auth = None

        log = AuditLog.log(
            request,
            action="health_check",
            resource_type="system",
            resource_id="",
        )
        assert log.action == "health_check"
        assert log.user == user
        assert log.company == co
        assert log.request_method == "GET"

    def test_log_classmethod_with_extra_data(self):
        from rest_framework.test import APIRequestFactory

        user = _user()
        factory = APIRequestFactory()
        request = factory.post("/api/v2/test/")
        request.user = user
        request.auth = None

        log = AuditLog.log(
            request,
            action="data_created",
            resource_type="data",
            extra_data={"key": "value"},
        )
        assert log.extra_data == {"key": "value"}

    def test_str_contains_action_and_resource(self):
        log = AuditLog.objects.create(
            action="model_trained",
            resource_type="model",
        )
        s = str(log)
        assert "model_trained" in s
        assert "model" in s


# ══════════════════════════════════════════════════════════════
# TestUsageTracking
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestUsageTracking(TestCase):

    def test_create_usage(self):
        co = _company()
        ut = UsageTracking.objects.create(
            company=co, date=timezone.now().date(),
        )
        assert ut.api_requests == 0
        assert ut.predictions == 0

    def test_str_contains_company_and_date(self):
        co = _company(name="TrackCo")
        ut = UsageTracking.objects.create(
            company=co, date=timezone.now().date(),
        )
        s = str(ut)
        assert "TrackCo" in s

    def test_get_or_create_today(self):
        co = _company()
        t1 = UsageTracking.get_or_create_today(co)
        t2 = UsageTracking.get_or_create_today(co)
        assert t1.pk == t2.pk

    def test_increment_requests(self):
        co = _company()
        ut = UsageTracking.objects.create(
            company=co, date=timezone.now().date(),
        )
        ut.increment_requests(5)
        assert ut.api_requests == 5

    def test_increment_predictions(self):
        co = _company()
        ut = UsageTracking.objects.create(
            company=co, date=timezone.now().date(),
        )
        ut.increment_predictions(3)
        assert ut.predictions == 3

    def test_increment_rate_limit_hits(self):
        co = _company()
        ut = UsageTracking.objects.create(
            company=co, date=timezone.now().date(),
        )
        ut.increment_rate_limit_hits(2)
        assert ut.rate_limit_hits == 2

    def test_check_daily_limit_within(self):
        co = _company(tier="free")  # daily_limit = 100
        ut = UsageTracking.objects.create(
            company=co, date=timezone.now().date(), api_requests=50,
        )
        assert ut.check_daily_limit() is True

    def test_check_daily_limit_exceeded(self):
        co = _company(tier="free")  # daily_limit = 100
        ut = UsageTracking.objects.create(
            company=co, date=timezone.now().date(), api_requests=100,
        )
        assert ut.check_daily_limit() is False

    def test_check_daily_limit_unlimited(self):
        co = _company(tier="enterprise")  # daily_limit = -1
        ut = UsageTracking.objects.create(
            company=co, date=timezone.now().date(), api_requests=999_999,
        )
        assert ut.check_daily_limit() is True


# ══════════════════════════════════════════════════════════════
# TestWebhook
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestWebhook(TestCase):

    def _make_webhook(self, **kw):
        co = kw.pop("company", None) or _company()
        defaults = {
            "company": co,
            "name": "test-hook",
            "url": "https://example.com/hook",
            "secret": "s3cr3t",
            "events": ["model.trained"],
        }
        defaults.update(kw)
        return Webhook.objects.create(**defaults)

    def test_create_webhook(self):
        wh = self._make_webhook()
        assert wh.is_active is True
        assert wh.max_retries == 3

    def test_str_representation(self):
        co = _company(name="HookCo")
        wh = self._make_webhook(company=co, name="my-hook")
        assert "my-hook" in str(wh)
        assert "HookCo" in str(wh)

    def test_should_receive_event_matching(self):
        wh = self._make_webhook(events=["model.trained", "model.failed"])
        assert wh.should_receive_event("model.trained") is True

    def test_should_receive_event_not_matching(self):
        wh = self._make_webhook(events=["model.trained"])
        assert wh.should_receive_event("prediction.completed") is False

    def test_should_receive_event_wildcard(self):
        wh = self._make_webhook(events=["*"])
        assert wh.should_receive_event("anything") is True

    def test_should_receive_event_inactive(self):
        wh = self._make_webhook(is_active=False, events=["*"])
        assert wh.should_receive_event("anything") is False

    def test_update_stats_success(self):
        wh = self._make_webhook()
        wh.update_stats(success=True)
        assert wh.total_deliveries == 1
        assert wh.successful_deliveries == 1
        assert wh.failed_deliveries == 0

    def test_update_stats_failure(self):
        wh = self._make_webhook()
        wh.update_stats(success=False, error="timeout")
        assert wh.total_deliveries == 1
        assert wh.successful_deliveries == 0
        assert wh.failed_deliveries == 1
        assert wh.last_error == "timeout"

    def test_event_type_choices_exist(self):
        choices = Webhook.EventType.choices
        assert len(choices) > 10
        values = [c[0] for c in choices]
        assert "model.trained" in values
        assert "*" in values


# ══════════════════════════════════════════════════════════════
# TestReport
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestReport(TestCase):

    def _make_report(self, **kw):
        co = kw.pop("company", None) or _company()
        defaults = {
            "company": co,
            "name": "Monthly Report",
            "report_type": Report.ReportType.USAGE,
            "format": Report.Format.PDF,
        }
        defaults.update(kw)
        return Report.objects.create(**defaults)

    def test_create_report(self):
        r = self._make_report()
        assert r.status == Report.Status.PENDING
        assert r.name == "Monthly Report"

    def test_str_representation(self):
        r = self._make_report(name="Q1 Compliance")
        assert "Q1 Compliance" in str(r)
        assert "usage" in str(r)

    def test_mark_generating(self):
        r = self._make_report()
        r.mark_generating()
        r.refresh_from_db()
        assert r.status == Report.Status.GENERATING

    def test_mark_completed(self):
        r = self._make_report()
        r.mark_completed(
            file_path="/reports/q1.pdf",
            file_size=1024,
            download_url="https://cdn.example.com/q1.pdf",
        )
        r.refresh_from_db()
        assert r.status == Report.Status.COMPLETED
        assert r.file_path == "/reports/q1.pdf"
        assert r.file_size == 1024
        assert r.completed_at is not None
        assert r.download_expires_at is not None

    def test_mark_failed(self):
        r = self._make_report()
        r.mark_failed("Timeout generating report")
        r.refresh_from_db()
        assert r.status == Report.Status.FAILED
        assert "Timeout" in r.error_message

    def test_status_transitions(self):
        r = self._make_report()
        assert r.status == Report.Status.PENDING
        r.mark_generating()
        assert r.status == Report.Status.GENERATING
        r.mark_completed("/f", 10)
        r.refresh_from_db()
        assert r.status == Report.Status.COMPLETED


# ══════════════════════════════════════════════════════════════
# TestWorkflow
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestWorkflow(TestCase):

    def _make_workflow(self, **kw):
        co = kw.pop("company", None) or _company()
        defaults = {
            "company": co,
            "name": "ETL Pipeline",
            "steps": [{"name": "extract", "type": "query"}],
            "trigger": {"type": "manual"},
        }
        defaults.update(kw)
        return Workflow.objects.create(**defaults)

    def test_create_workflow(self):
        wf = self._make_workflow()
        assert wf.status == Workflow.Status.DRAFT
        assert wf.total_runs == 0

    def test_str_representation(self):
        wf = self._make_workflow(name="ML Train")
        assert "ML Train" in str(wf)
        assert "draft" in str(wf)

    def test_success_rate_no_runs(self):
        wf = self._make_workflow()
        assert wf.success_rate == 0.0

    def test_success_rate_with_runs(self):
        wf = self._make_workflow()
        wf.total_runs = 10
        wf.successful_runs = 7
        assert wf.success_rate == 70.0

    def test_update_stats_success(self):
        wf = self._make_workflow()
        wf.update_stats(success=True)
        assert wf.total_runs == 1
        assert wf.successful_runs == 1
        assert wf.last_run_at is not None
        assert wf.last_success_at is not None

    def test_update_stats_failure(self):
        wf = self._make_workflow()
        wf.update_stats(success=False)
        assert wf.total_runs == 1
        assert wf.failed_runs == 1
        assert wf.last_failure_at is not None


# ══════════════════════════════════════════════════════════════
# TestScheduledTask
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestScheduledTask(TestCase):

    def _make_task(self, **kw):
        co = kw.pop("company", None) or _company()
        defaults = {
            "company": co,
            "name": "Nightly Backup",
            "task_type": ScheduledTask.TaskType.BACKUP,
            "cron_expression": "0 2 * * *",
        }
        defaults.update(kw)
        return ScheduledTask.objects.create(**defaults)

    def test_create_task(self):
        t = self._make_task()
        assert t.status == ScheduledTask.Status.ACTIVE
        assert t.total_runs == 0

    def test_str_representation(self):
        t = self._make_task(name="Daily Sync")
        assert "Daily Sync" in str(t)
        assert "0 2 * * *" in str(t)

    def test_update_stats_success(self):
        t = self._make_task()
        t.update_stats(success=True)
        assert t.total_runs == 1
        assert t.successful_runs == 1
        assert t.consecutive_failures == 0

    def test_update_stats_failure(self):
        t = self._make_task()
        t.update_stats(success=False)
        assert t.total_runs == 1
        assert t.failed_runs == 1
        assert t.consecutive_failures == 1

    def test_auto_disable_after_consecutive_failures(self):
        t = self._make_task(max_consecutive_failures=3)
        for _ in range(3):
            t.update_stats(success=False)
        t.refresh_from_db()
        assert t.status == ScheduledTask.Status.DISABLED

    def test_consecutive_failures_reset_on_success(self):
        t = self._make_task()
        t.update_stats(success=False)
        t.update_stats(success=False)
        assert t.consecutive_failures == 2
        t.update_stats(success=True)
        assert t.consecutive_failures == 0

    def test_calculate_next_run_no_croniter(self):
        """calculate_next_run should not raise if croniter is unavailable."""
        t = self._make_task(cron_expression="0 0 * * *")
        t.calculate_next_run()
        # It either sets next_run_at or silently passes
        # depending on croniter availability


# ══════════════════════════════════════════════════════════════
# TestScheduledTaskRun
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestScheduledTaskRun(TestCase):

    def _make_run(self, **kw):
        task = kw.pop("task", None)
        if not task:
            co = _company()
            task = ScheduledTask.objects.create(
                company=co,
                name="task",
                task_type=ScheduledTask.TaskType.CLEANUP,
                cron_expression="0 0 * * *",
            )
        defaults = {
            "task": task,
            "scheduled_at": timezone.now(),
        }
        defaults.update(kw)
        return ScheduledTaskRun.objects.create(**defaults)

    def test_create_run(self):
        run = self._make_run()
        assert run.status == ScheduledTaskRun.Status.PENDING

    def test_start(self):
        run = self._make_run()
        run.start()
        run.refresh_from_db()
        assert run.status == ScheduledTaskRun.Status.RUNNING
        assert run.started_at is not None

    def test_complete(self):
        run = self._make_run()
        run.start()
        run.complete(output={"cleaned": 42})
        run.refresh_from_db()
        assert run.status == ScheduledTaskRun.Status.COMPLETED
        assert run.output == {"cleaned": 42}
        assert run.duration_seconds is not None

    def test_fail(self):
        run = self._make_run()
        run.start()
        run.fail("disk full")
        run.refresh_from_db()
        assert run.status == ScheduledTaskRun.Status.FAILED
        assert "disk full" in run.error_message

    def test_str_representation(self):
        run = self._make_run()
        assert "task" in str(run)


# ══════════════════════════════════════════════════════════════
# TestWebhookDelivery
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestWebhookDelivery(TestCase):

    def _make_delivery(self, **kw):
        co = _company()
        wh = kw.pop("webhook", None)
        if not wh:
            wh = Webhook.objects.create(
                company=co, name="hook", url="https://example.com",
                secret="s", events=["*"],
            )
        defaults = {
            "webhook": wh,
            "event_type": "model.trained",
            "payload": {"model_id": "abc"},
        }
        defaults.update(kw)
        return WebhookDelivery.objects.create(**defaults)

    def test_create_delivery(self):
        d = self._make_delivery()
        assert d.status == WebhookDelivery.Status.PENDING
        assert d.attempt_count == 0

    def test_mark_delivered(self):
        d = self._make_delivery()
        d.mark_delivered(status_code=200, body='{"ok": true}', latency_ms=42.5)
        d.refresh_from_db()
        assert d.status == WebhookDelivery.Status.DELIVERED
        assert d.response_status_code == 200
        assert d.latency_ms == 42.5
        assert d.delivered_at is not None

    def test_mark_failed_with_retry(self):
        d = self._make_delivery()
        d.mark_failed("Connection refused", retry=True)
        d.refresh_from_db()
        assert d.status == WebhookDelivery.Status.RETRYING
        assert d.attempt_count == 1
        assert d.next_retry_at is not None

    def test_mark_failed_no_retry(self):
        d = self._make_delivery()
        d.mark_failed("fatal error", retry=False)
        d.refresh_from_db()
        assert d.status == WebhookDelivery.Status.FAILED

    def test_mark_failed_exhausts_retries(self):
        d = self._make_delivery()
        d.max_attempts = 2
        d.save()
        d.mark_failed("err1", retry=True)  # attempt 1
        d.mark_failed("err2", retry=True)  # attempt 2 >= max
        d.refresh_from_db()
        assert d.status == WebhookDelivery.Status.FAILED


# ══════════════════════════════════════════════════════════════
# TestWorkflowRun
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestWorkflowRun(TestCase):

    def _make_workflow_run(self, **kw):
        co = _company()
        wf = kw.pop("workflow", None)
        if not wf:
            wf = Workflow.objects.create(
                company=co, name="wf",
                steps=[], trigger={"type": "manual"},
            )
        defaults = {
            "workflow": wf,
            "trigger_type": "manual",
        }
        defaults.update(kw)
        return WorkflowRun.objects.create(**defaults)

    def test_start(self):
        run = self._make_workflow_run()
        run.start()
        run.refresh_from_db()
        assert run.status == WorkflowRun.Status.RUNNING

    def test_complete(self):
        run = self._make_workflow_run()
        run.start()
        run.complete(output_data={"result": "ok"})
        run.refresh_from_db()
        assert run.status == WorkflowRun.Status.COMPLETED
        assert run.output_data == {"result": "ok"}
        assert run.duration_seconds is not None

    def test_fail(self):
        run = self._make_workflow_run()
        run.start()
        run.fail("Something broke")
        run.refresh_from_db()
        assert run.status == WorkflowRun.Status.FAILED
        assert "Something broke" in run.error_message

    def test_log_step(self):
        run = self._make_workflow_run()
        run.log_step("extract", "completed", output={"rows": 100})
        run.refresh_from_db()
        assert len(run.step_logs) == 1
        assert run.step_logs[0]["step_name"] == "extract"
        assert run.current_step == 1

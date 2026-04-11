"""
Tests for sandbox models: Subscription, DataUpload, SandboxLead,
SandboxTemplate, Sandbox, SyntheticDataset, Experiment.
"""

import secrets
import uuid
from datetime import timedelta

import pytest
from django.test import TestCase
from django.utils import timezone

from apps.core.models import Company, User
from apps.sandbox.models import (
    DataUpload,
    Experiment,
    Sandbox,
    SandboxLead,
    SandboxTemplate,
    Subscription,
    SyntheticDataset,
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


def _sandbox(owner=None, **kw):
    owner = owner or _company()
    defaults = {
        "name": f"Sandbox-{uuid.uuid4().hex[:6]}",
        "owner": owner,
        "expires_at": timezone.now() + timedelta(days=7),
    }
    defaults.update(kw)
    return Sandbox.objects.create(**defaults)


# ══════════════════════════════════════════════════════════════
# TestSubscription
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestSubscription(TestCase):

    def _make_sub(self, **kw):
        co = kw.pop("company", None) or _company()
        now = timezone.now()
        defaults = {
            "company": co,
            "plan": "free",
            "status": Subscription.Status.TRIALING,
            "trial_end": now + timedelta(days=14),
            "current_period_start": now,
            "current_period_end": now + timedelta(days=14),
        }
        defaults.update(kw)
        return Subscription.objects.create(**defaults)

    def test_create_subscription(self):
        sub = self._make_sub()
        assert sub.plan == "free"
        assert sub.status == Subscription.Status.TRIALING
        assert isinstance(sub.id, uuid.UUID)

    def test_str_contains_company_and_plan(self):
        co = _company(name="SubCo")
        sub = self._make_sub(company=co, plan="starter")
        s = str(sub)
        assert "SubCo" in s
        assert "starter" in s

    def test_is_active_or_trialing_trialing(self):
        sub = self._make_sub(status=Subscription.Status.TRIALING)
        assert sub.is_active_or_trialing is True

    def test_is_active_or_trialing_active(self):
        sub = self._make_sub(status=Subscription.Status.ACTIVE)
        assert sub.is_active_or_trialing is True

    def test_is_active_or_trialing_cancelled(self):
        sub = self._make_sub(status=Subscription.Status.CANCELLED)
        assert sub.is_active_or_trialing is False

    def test_is_active_or_trialing_expired(self):
        sub = self._make_sub(status=Subscription.Status.EXPIRED)
        assert sub.is_active_or_trialing is False

    def test_activate(self):
        sub = self._make_sub()
        sub.activate("professional", period_days=30)
        sub.refresh_from_db()
        assert sub.plan == "professional"
        assert sub.status == Subscription.Status.ACTIVE
        delta = sub.current_period_end - sub.current_period_start
        assert abs(delta.days - 30) <= 1

    def test_cancel(self):
        sub = self._make_sub(status=Subscription.Status.ACTIVE)
        sub.cancel()
        sub.refresh_from_db()
        assert sub.cancel_at_period_end is True
        # Status remains active until period end
        assert sub.status == Subscription.Status.ACTIVE

    def test_expire(self):
        sub = self._make_sub(status=Subscription.Status.ACTIVE)
        sub.expire()
        sub.refresh_from_db()
        assert sub.status == Subscription.Status.EXPIRED
        assert sub.is_active_or_trialing is False

    def test_full_lifecycle(self):
        """trialing -> active -> cancel -> expire"""
        sub = self._make_sub()
        assert sub.status == Subscription.Status.TRIALING

        sub.activate("starter", period_days=30)
        assert sub.status == Subscription.Status.ACTIVE

        sub.cancel()
        assert sub.cancel_at_period_end is True

        sub.expire()
        assert sub.status == Subscription.Status.EXPIRED


# ══════════════════════════════════════════════════════════════
# TestDataUpload
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestDataUpload(TestCase):

    def test_create_upload(self):
        co = _company()
        upload = DataUpload.objects.create(
            company=co,
            file_name="data.csv",
            file_size=2048,
            record_count=200,
            feature_count=10,
            status="completed",
        )
        assert upload.file_size == 2048
        assert upload.record_count == 200

    def test_str_contains_filename_and_size(self):
        co = _company()
        upload = DataUpload.objects.create(
            company=co, file_name="patients.csv", file_size=4096,
        )
        s = str(upload)
        assert "patients.csv" in s
        assert "4096" in s

    def test_default_status_pending(self):
        co = _company()
        upload = DataUpload.objects.create(
            company=co, file_name="f.csv", file_size=100,
        )
        assert upload.status == "pending"

    def test_error_message_stored(self):
        co = _company()
        upload = DataUpload.objects.create(
            company=co, file_name="bad.csv", file_size=100,
            status="failed", error_message="Parse error",
        )
        assert upload.error_message == "Parse error"

    def test_ordering_by_created_at(self):
        co = _company()
        u1 = DataUpload.objects.create(company=co, file_name="a.csv", file_size=1)
        u2 = DataUpload.objects.create(company=co, file_name="b.csv", file_size=2)
        uploads = list(DataUpload.objects.filter(company=co))
        assert uploads[0] == u2  # most recent first


# ══════════════════════════════════════════════════════════════
# TestSandboxLead
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestSandboxLead(TestCase):

    def test_create_lead(self):
        lead = SandboxLead.objects.create(
            email="lead@example.com",
        )
        assert lead.token.startswith("sbx_")
        assert lead.access_count == 0

    def test_auto_expires_at(self):
        lead = SandboxLead.objects.create(email="lead2@example.com")
        assert lead.expires_at is not None
        assert lead.expires_at > timezone.now()

    def test_is_expired_false(self):
        lead = SandboxLead.objects.create(
            email="valid@example.com",
            expires_at=timezone.now() + timedelta(days=3),
        )
        assert lead.is_expired is False
        assert lead.is_valid is True

    def test_is_expired_true(self):
        lead = SandboxLead.objects.create(
            email="old@example.com",
            token=f"sbx_{secrets.token_urlsafe(32)}",
            expires_at=timezone.now() - timedelta(hours=1),
        )
        assert lead.is_expired is True
        assert lead.is_valid is False

    def test_record_access(self):
        lead = SandboxLead.objects.create(email="counter@example.com")
        lead.record_access()
        lead.refresh_from_db()
        assert lead.access_count == 1
        assert lead.last_access_at is not None

    def test_record_access_increments(self):
        lead = SandboxLead.objects.create(email="multi@example.com")
        lead.record_access()
        lead.record_access()
        lead.refresh_from_db()
        assert lead.access_count == 2

    def test_mark_converted(self):
        co = _company()
        user = _user(company=co)
        lead = SandboxLead.objects.create(email="convert@example.com")
        lead.mark_converted(user)
        lead.refresh_from_db()
        assert lead.converted is True
        assert lead.converted_at is not None
        assert lead.converted_to_user == user

    def test_get_or_create_for_email_new(self):
        lead, created = SandboxLead.get_or_create_for_email("new@example.com")
        assert created is True
        assert lead.email == "new@example.com"

    def test_get_or_create_for_email_existing(self):
        SandboxLead.objects.create(
            email="existing@example.com",
            expires_at=timezone.now() + timedelta(days=5),
        )
        lead, created = SandboxLead.get_or_create_for_email("existing@example.com")
        assert created is False

    def test_get_or_create_expired_creates_new(self):
        SandboxLead.objects.create(
            email="expired@example.com",
            token=f"sbx_{secrets.token_urlsafe(32)}",
            expires_at=timezone.now() - timedelta(days=1),
        )
        lead, created = SandboxLead.get_or_create_for_email("expired@example.com")
        assert created is True

    def test_str_representation(self):
        lead = SandboxLead.objects.create(email="str@example.com")
        assert "str@example.com" in str(lead)

    def test_utm_fields(self):
        lead = SandboxLead.objects.create(
            email="utm@example.com",
            utm_campaign="launch",
            utm_source="twitter",
            utm_medium="social",
        )
        assert lead.utm_campaign == "launch"
        assert lead.utm_source == "twitter"


# ══════════════════════════════════════════════════════════════
# TestSandboxTemplate
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestSandboxTemplate(TestCase):

    def test_create_template(self):
        tmpl = SandboxTemplate.objects.create(
            id="healthcare-basic",
            name="Healthcare Basic",
            description="Basic healthcare demo",
            industry="healthcare",
        )
        assert tmpl.name == "Healthcare Basic"

    def test_str_representation(self):
        tmpl = SandboxTemplate.objects.create(
            id="fin-basic", name="Finance Basic",
        )
        assert str(tmpl) == "Finance Basic"

    def test_default_datasets_and_experiments(self):
        tmpl = SandboxTemplate.objects.create(
            id="generic", name="Generic",
        )
        assert tmpl.datasets == []
        assert tmpl.experiments == []


# ══════════════════════════════════════════════════════════════
# TestSandbox
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestSandbox(TestCase):

    def test_create_sandbox(self):
        co = _company()
        sb = _sandbox(owner=co, name="Test Sandbox")
        assert sb.name == "Test Sandbox"
        assert sb.status == Sandbox.Status.ACTIVE
        assert sb.owner == co

    def test_str_representation(self):
        co = _company(name="SbCo")
        sb = _sandbox(owner=co, name="Demo")
        assert "Demo" in str(sb)
        assert "SbCo" in str(sb)

    def test_auto_expires_at(self):
        co = _company()
        sb = Sandbox.objects.create(name="Auto", owner=co)
        assert sb.expires_at is not None

    def test_is_expired_false(self):
        sb = _sandbox()
        assert sb.is_expired is False

    def test_is_expired_true(self):
        co = _company()
        sb = Sandbox.objects.create(
            name="Old", owner=co,
            expires_at=timezone.now() - timedelta(hours=1),
        )
        assert sb.is_expired is True

    def test_status_transitions(self):
        sb = _sandbox()
        assert sb.status == Sandbox.Status.ACTIVE
        sb.status = Sandbox.Status.ARCHIVED
        sb.save()
        sb.refresh_from_db()
        assert sb.status == Sandbox.Status.ARCHIVED

    def test_dataset_count(self):
        sb = _sandbox()
        assert sb.dataset_count == 0

    def test_experiment_count(self):
        sb = _sandbox()
        assert sb.experiment_count == 0


# ══════════════════════════════════════════════════════════════
# TestSyntheticDataset
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestSyntheticDataset(TestCase):

    def test_create_dataset(self):
        sb = _sandbox()
        ds = SyntheticDataset.objects.create(
            sandbox=sb,
            name="Transactions",
            dataset_type=SyntheticDataset.DatasetType.TRANSACTIONS,
            record_count=1000,
            feature_count=4,
        )
        assert ds.record_count == 1000
        assert ds.dataset_type == "transactions"

    def test_str_representation(self):
        sb = _sandbox()
        ds = SyntheticDataset.objects.create(
            sandbox=sb, name="Patients", record_count=500, feature_count=3,
        )
        assert "Patients" in str(ds)
        assert "500" in str(ds)

    def test_default_fields(self):
        sb = _sandbox()
        ds = SyntheticDataset.objects.create(
            sandbox=sb, name="D", record_count=10, feature_count=1,
        )
        assert ds.features == []
        assert ds.statistics == {}
        assert ds.data_preview == []

    def test_dataset_belongs_to_sandbox(self):
        sb = _sandbox()
        ds = SyntheticDataset.objects.create(
            sandbox=sb, name="D", record_count=10, feature_count=1,
        )
        assert ds in sb.datasets.all()


# ══════════════════════════════════════════════════════════════
# TestExperiment
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestExperiment(TestCase):

    def _make_experiment(self, **kw):
        sb = kw.pop("sandbox", None) or _sandbox()
        defaults = {
            "sandbox": sb,
            "name": "Train Model",
            "experiment_type": Experiment.ExperimentType.TRAINING,
        }
        defaults.update(kw)
        return Experiment.objects.create(**defaults)

    def test_create_experiment(self):
        exp = self._make_experiment()
        assert exp.status == Experiment.Status.PENDING
        assert exp.experiment_type == "training"

    def test_str_representation(self):
        exp = self._make_experiment(name="Eval")
        assert "Eval" in str(exp)
        assert "pending" in str(exp)

    def test_start(self):
        exp = self._make_experiment()
        exp.start()
        exp.refresh_from_db()
        assert exp.status == Experiment.Status.RUNNING
        assert exp.started_at is not None

    def test_complete(self):
        exp = self._make_experiment()
        exp.start()
        results = {"accuracy": 0.92}
        exp.complete(results=results)
        exp.refresh_from_db()
        assert exp.status == Experiment.Status.COMPLETED
        assert exp.results == results
        assert exp.completed_at is not None

    def test_complete_without_results(self):
        exp = self._make_experiment()
        exp.start()
        exp.complete()
        exp.refresh_from_db()
        assert exp.status == Experiment.Status.COMPLETED
        assert exp.results == {}

    def test_fail(self):
        exp = self._make_experiment()
        exp.start()
        exp.fail("Out of memory")
        exp.refresh_from_db()
        assert exp.status == Experiment.Status.FAILED
        assert "Out of memory" in exp.error_message
        assert exp.completed_at is not None

    def test_full_lifecycle(self):
        exp = self._make_experiment()
        assert exp.status == Experiment.Status.PENDING
        exp.start()
        assert exp.status == Experiment.Status.RUNNING
        exp.complete(results={"loss": 0.01})
        assert exp.status == Experiment.Status.COMPLETED

    def test_experiment_types(self):
        for et_val, et_label in Experiment.ExperimentType.choices:
            exp = self._make_experiment(experiment_type=et_val)
            assert exp.experiment_type == et_val

    def test_default_config(self):
        exp = self._make_experiment()
        assert exp.config == {}

    def test_experiment_with_dataset(self):
        sb = _sandbox()
        ds = SyntheticDataset.objects.create(
            sandbox=sb, name="Data", record_count=100, feature_count=3,
        )
        exp = self._make_experiment(sandbox=sb, dataset=ds)
        assert exp.dataset == ds
        assert exp in ds.experiments.all()

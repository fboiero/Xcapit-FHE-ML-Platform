"""
Tests for the trial sandbox feature.

Covers: Company trial fields, TrialService, trial API endpoints,
Subscription model, DataUpload model, and permissions.
"""

import uuid
from datetime import timedelta
from io import BytesIO

import pytest
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.core.models import Company, User, UsageTracking
from apps.consortiums.models import Consortium, ConsortiumMember
from apps.sandbox.models import DataUpload, Subscription
from apps.sandbox.services import TrialService


# ── Fixtures ──────────────────────────────────────────────────


def make_company(**kwargs):
    defaults = {
        "name": f"TestCo-{uuid.uuid4().hex[:6]}",
        "email": f"test-{uuid.uuid4().hex[:6]}@example.com",
        "tier": "free",
    }
    defaults.update(kwargs)
    return Company.objects.create(**defaults)


def make_user(company=None, **kwargs):
    defaults = {
        "email": f"user-{uuid.uuid4().hex[:6]}@example.com",
        "first_name": "Test",
        "last_name": "User",
    }
    defaults.update(kwargs)
    user = User.objects.create_user(password="TestPass12345!", company=company, **defaults)
    return user


# ── Company Trial Fields ──────────────────────────────────────


@pytest.mark.django_db
class TestCompanyTrialFields(TestCase):

    def test_new_company_has_no_trial(self):
        co = make_company()
        assert co.trial_started_at is None
        assert co.trial_expires_at is None
        assert co.is_trial is False
        assert co.trial_expired is False
        assert co.trial_days_remaining == 0

    def test_start_trial_sets_dates(self):
        co = make_company()
        co.start_trial()
        co.refresh_from_db()
        assert co.trial_started_at is not None
        assert co.trial_expires_at is not None
        assert co.is_trial is True
        assert co.trial_expired is False
        assert co.trial_days_remaining >= 13  # 14 days minus a few seconds

    def test_trial_expired_after_expiry(self):
        co = make_company()
        co.trial_started_at = timezone.now() - timedelta(days=15)
        co.trial_expires_at = timezone.now() - timedelta(days=1)
        co.save()
        assert co.trial_expired is True
        assert co.trial_days_remaining == 0

    def test_is_trial_false_for_paid_tier(self):
        co = make_company(tier="starter")
        co.trial_expires_at = timezone.now() + timedelta(days=7)
        co.save()
        assert co.is_trial is False

    def test_upload_limit_per_tier(self):
        free_co = make_company(tier="free")
        assert free_co.upload_limit == 50 * 1024 * 1024
        starter_co = make_company(tier="starter")
        assert starter_co.upload_limit == 1 * 1024 ** 3
        enterprise_co = make_company(tier="enterprise")
        assert enterprise_co.upload_limit == -1

    def test_training_limit_per_tier(self):
        co = make_company(tier="free")
        assert co.training_limit == 5
        co.tier = "professional"
        assert co.training_limit == 500

    def test_sandbox_limit_per_tier(self):
        co = make_company(tier="free")
        assert co.sandbox_limit == 1
        co.tier = "enterprise"
        assert co.sandbox_limit == -1


# ── Subscription Model ────────────────────────────────────────


@pytest.mark.django_db
class TestSubscriptionModel(TestCase):

    def test_create_subscription(self):
        co = make_company()
        now = timezone.now()
        sub = Subscription.objects.create(
            company=co,
            plan="free",
            status=Subscription.Status.TRIALING,
            trial_end=now + timedelta(days=14),
            current_period_start=now,
            current_period_end=now + timedelta(days=14),
        )
        assert sub.is_active_or_trialing is True
        assert str(co.name) in str(sub)

    def test_activate_subscription(self):
        co = make_company()
        now = timezone.now()
        sub = Subscription.objects.create(
            company=co,
            plan="free",
            status=Subscription.Status.TRIALING,
            current_period_start=now,
            current_period_end=now + timedelta(days=14),
        )
        sub.activate("starter", period_days=30)
        sub.refresh_from_db()
        assert sub.plan == "starter"
        assert sub.status == Subscription.Status.ACTIVE
        assert sub.is_active_or_trialing is True

    def test_cancel_subscription(self):
        co = make_company()
        now = timezone.now()
        sub = Subscription.objects.create(
            company=co,
            plan="starter",
            status=Subscription.Status.ACTIVE,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
        )
        sub.cancel()
        sub.refresh_from_db()
        assert sub.cancel_at_period_end is True

    def test_expire_subscription(self):
        co = make_company()
        now = timezone.now()
        sub = Subscription.objects.create(
            company=co,
            plan="starter",
            status=Subscription.Status.ACTIVE,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
        )
        sub.expire()
        sub.refresh_from_db()
        assert sub.status == Subscription.Status.EXPIRED
        assert sub.is_active_or_trialing is False


# ── DataUpload Model ──────────────────────────────────────────


@pytest.mark.django_db
class TestDataUploadModel(TestCase):

    def test_create_upload(self):
        co = make_company()
        upload = DataUpload.objects.create(
            company=co,
            file_name="test.csv",
            file_size=1024,
            record_count=100,
            feature_count=5,
            status="completed",
        )
        assert upload.file_size == 1024
        assert "test.csv" in str(upload)


# ── TrialService ──────────────────────────────────────────────


@pytest.mark.django_db
class TestTrialService(TestCase):

    def setUp(self):
        self.service = TrialService()

    def test_start_trial_success(self):
        co = make_company(tier="free")
        result = self.service.start_trial(co)
        assert result.success is True
        assert "trial_started_at" in result.data
        assert "subscription_id" in result.data

        co.refresh_from_db()
        assert co.is_trial is True
        assert Subscription.objects.filter(company=co).exists()

    def test_start_trial_fails_for_paid_tier(self):
        co = make_company(tier="starter")
        result = self.service.start_trial(co)
        assert result.success is False
        assert result.error_code == "already_paid"

    def test_start_trial_fails_if_already_started(self):
        co = make_company(tier="free")
        self.service.start_trial(co)
        result = self.service.start_trial(co)
        assert result.success is False
        assert result.error_code == "trial_already_started"

    def test_get_usage_summary(self):
        co = make_company(tier="free")
        co.start_trial()
        result = self.service.get_usage_summary(co)
        assert result.success is True
        assert result.data["tier"] == "free"
        assert result.data["is_trial"] is True
        assert "usage" in result.data
        assert "limits" in result.data

    def test_check_upload_allowed_within_limit(self):
        co = make_company(tier="free")
        co.start_trial()
        result = self.service.check_upload_allowed(co, 1024)
        assert result.success is True
        assert result.data["allowed"] is True

    def test_check_upload_exceeds_limit(self):
        co = make_company(tier="free")
        co.start_trial()
        # Create uploads that fill the quota
        DataUpload.objects.create(
            company=co,
            file_name="big.csv",
            file_size=50 * 1024 * 1024,  # 50 MB = full quota
            status="completed",
        )
        result = self.service.check_upload_allowed(co, 1024)
        assert result.success is False
        assert result.error_code == "upload_limit_exceeded"

    def test_check_upload_blocked_when_trial_expired(self):
        co = make_company(tier="free")
        co.trial_started_at = timezone.now() - timedelta(days=15)
        co.trial_expires_at = timezone.now() - timedelta(days=1)
        co.save()
        result = self.service.check_upload_allowed(co, 1024)
        assert result.success is False
        assert result.error_code == "trial_expired"

    def test_check_training_allowed(self):
        co = make_company(tier="free")
        co.start_trial()
        result = self.service.check_training_allowed(co)
        assert result.success is True

    def test_check_training_blocked_at_limit(self):
        co = make_company(tier="free")
        co.start_trial()
        UsageTracking.objects.create(
            company=co,
            date=timezone.now().date(),
            training_runs=5,
        )
        result = self.service.check_training_allowed(co)
        assert result.success is False
        assert result.error_code == "training_limit_exceeded"

    def test_request_upgrade_success(self):
        co = make_company(tier="free")
        self.service.start_trial(co)
        result = self.service.request_upgrade(co, "starter")
        assert result.success is True
        assert result.data["requested_tier"] == "starter"
        assert result.data["status"] == "pending_payment"
        # Tier is NOT yet changed — requires payment confirmation
        co.refresh_from_db()
        assert co.tier == "free"

    def test_request_upgrade_invalid_tier(self):
        co = make_company(tier="free")
        result = self.service.request_upgrade(co, "invalid")
        assert result.success is False
        assert result.error_code == "invalid_tier"

    def test_request_upgrade_no_downgrade(self):
        co = make_company(tier="professional")
        result = self.service.request_upgrade(co, "starter")
        assert result.success is False
        assert result.error_code == "invalid_upgrade"

    def test_get_plans_comparison(self):
        plans = TrialService.get_plans_comparison()
        assert len(plans) == 4
        tiers = [p["tier"] for p in plans]
        assert "free" in tiers
        assert "enterprise" in tiers


# ── API Endpoints ─────────────────────────────────────────────


@pytest.mark.django_db
class TestTrialAPI(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.company = make_company(tier="free")
        self.user = make_user(company=self.company)
        self.client.force_authenticate(user=self.user)

    def test_start_trial(self):
        resp = self.client.post("/api/v2/sandbox/trial/start/")
        assert resp.status_code == 201
        assert "trial_started_at" in resp.data

    def test_start_trial_twice_fails(self):
        self.client.post("/api/v2/sandbox/trial/start/")
        resp = self.client.post("/api/v2/sandbox/trial/start/")
        assert resp.status_code == 400

    def test_trial_status(self):
        self.client.post("/api/v2/sandbox/trial/start/")
        resp = self.client.get("/api/v2/sandbox/trial/status/")
        assert resp.status_code == 200
        assert resp.data["tier"] == "free"
        assert resp.data["is_trial"] is True

    def test_trial_usage(self):
        self.client.post("/api/v2/sandbox/trial/start/")
        resp = self.client.get("/api/v2/sandbox/trial/usage/")
        assert resp.status_code == 200
        assert "usage" in resp.data
        assert "limits" in resp.data

    def test_upgrade(self):
        self.client.post("/api/v2/sandbox/trial/start/")
        resp = self.client.post(
            "/api/v2/sandbox/trial/upgrade/",
            {"target_tier": "starter"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["requested_tier"] == "starter"
        assert resp.data["status"] == "pending_payment"

    def test_upgrade_invalid_tier(self):
        resp = self.client.post(
            "/api/v2/sandbox/trial/upgrade/",
            {"target_tier": "invalid"},
            format="json",
        )
        assert resp.status_code == 400

    def test_plans_comparison_public(self):
        client = APIClient()  # unauthenticated
        resp = client.get("/api/v2/sandbox/plans/")
        assert resp.status_code == 200
        assert len(resp.data) == 4

    def test_upload_data(self):
        self.client.post("/api/v2/sandbox/trial/start/")

        # Create a consortium
        consortium = Consortium.objects.create(
            name="Test Consortium",
            owner=self.company,
        )

        # Upload a file
        f = BytesIO(b"col1,col2\n1,2\n3,4\n")
        f.name = "test.csv"
        resp = self.client.post(
            "/api/v2/sandbox/trial/upload-data/",
            {"consortium_id": str(consortium.id), "file": f},
            format="multipart",
        )
        assert resp.status_code == 201
        assert resp.data["file_name"] == "test.csv"

    def test_upload_blocked_when_trial_expired(self):
        self.company.trial_started_at = timezone.now() - timedelta(days=15)
        self.company.trial_expires_at = timezone.now() - timedelta(days=1)
        self.company.save()

        consortium = Consortium.objects.create(
            name="Test", owner=self.company,
        )
        f = BytesIO(b"data")
        f.name = "test.csv"
        resp = self.client.post(
            "/api/v2/sandbox/trial/upload-data/",
            {"consortium_id": str(consortium.id), "file": f},
            format="multipart",
        )
        assert resp.status_code == 403

    def test_unauthenticated_blocked(self):
        client = APIClient()
        resp = client.post("/api/v2/sandbox/trial/start/")
        assert resp.status_code in (401, 403)

    def test_no_company_blocked(self):
        user = make_user()  # no company
        self.client.force_authenticate(user=user)
        resp = self.client.post("/api/v2/sandbox/trial/start/")
        assert resp.status_code == 403


# ── Consortium Demo Endpoints ─────────────────────────────────


@pytest.mark.django_db
class TestConsortiumDemoAPI(TestCase):

    def test_demo_limits_public(self):
        client = APIClient()
        resp = client.get("/api/v2/sandbox/consortium-demo/limits/")
        assert resp.status_code == 200
        assert resp.data["tier"] == "free"
        assert "limits" in resp.data

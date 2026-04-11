"""
Tests for sandbox services: ConsortiumDemoService and TrialService.
"""

import uuid
from datetime import timedelta

import pytest
from django.test import TestCase
from django.utils import timezone

from apps.core.models import Company, UsageTracking, User
from apps.sandbox.models import DataUpload, Subscription
from apps.sandbox.services import (
    TIER_DEMO_LIMITS,
    ConsortiumDemoService,
    TrialService,
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
# TestConsortiumDemoService
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestConsortiumDemoService(TestCase):

    def setUp(self):
        self.service = ConsortiumDemoService()

    def _members(self, count=2, samples=10):
        return [
            {
                "name": f"Hospital-{i}",
                "samples": samples,
                "age_range": [20, 80],
                "bmi_bias": 0,
                "severity_bias": 0,
            }
            for i in range(count)
        ]

    def test_run_demo_simulated_mode(self):
        """When tenseal is unavailable, demo falls back to simulation."""
        members = self._members(2, 10)
        result = self.service.run_demo(members=members, tier="free")
        assert result.success is True
        data = result.data
        # Simulated mode should return structured results
        assert "local_results" in data
        assert "consortium_result" in data
        assert "improvement" in data
        assert len(data["local_results"]) == 2

    def test_run_demo_returns_improvement(self):
        members = self._members(3, 15)
        result = self.service.run_demo(members=members, tier="free")
        assert result.success is True
        imp = result.data["improvement"]
        assert "r2_local_avg" in imp
        assert "r2_consortium" in imp
        assert "r2_delta" in imp
        assert "mae_reduction_pct" in imp

    def test_run_demo_encryption_info(self):
        members = self._members(2, 10)
        result = self.service.run_demo(members=members, tier="free")
        assert result.success is True
        enc = result.data["encryption"]
        assert "scheme" in enc
        assert enc["security_bits"] == 128

    # ── Tier limit enforcement ──

    def test_free_tier_max_members_enforced(self):
        max_members = TIER_DEMO_LIMITS["free"]["max_members"]
        members = self._members(max_members + 1, 10)
        result = self.service.run_demo(members=members, tier="free")
        assert result.success is False
        assert result.error_code == "tier_limit_members"

    def test_free_tier_max_samples_enforced(self):
        max_samples = TIER_DEMO_LIMITS["free"]["max_samples_per_member"]
        members = self._members(1, max_samples + 1)
        result = self.service.run_demo(members=members, tier="free")
        assert result.success is False
        assert result.error_code == "tier_limit_samples"

    def test_starter_tier_allows_more_members(self):
        max_free = TIER_DEMO_LIMITS["free"]["max_members"]
        members = self._members(max_free + 1, 10)
        result = self.service.run_demo(members=members, tier="starter")
        assert result.success is True

    def test_starter_tier_allows_more_samples(self):
        members = self._members(1, 100)
        result = self.service.run_demo(members=members, tier="starter")
        assert result.success is True

    def test_enterprise_tier_unlimited_members(self):
        members = self._members(50, 10)
        result = self.service.run_demo(members=members, tier="enterprise")
        assert result.success is True

    def test_enterprise_tier_unlimited_samples(self):
        members = self._members(1, 10000)
        result = self.service.run_demo(members=members, tier="enterprise")
        assert result.success is True

    # ── Various member configs ──

    def test_single_member(self):
        members = self._members(1, 10)
        result = self.service.run_demo(members=members, tier="free")
        assert result.success is True
        assert len(result.data["local_results"]) == 1

    def test_max_free_members(self):
        max_m = TIER_DEMO_LIMITS["free"]["max_members"]
        members = self._members(max_m, 10)
        result = self.service.run_demo(members=members, tier="free")
        assert result.success is True
        assert len(result.data["local_results"]) == max_m

    def test_member_with_custom_biases(self):
        members = [
            {"name": "H1", "samples": 10, "age_range": [30, 50], "bmi_bias": 5, "severity_bias": 2},
            {"name": "H2", "samples": 10, "age_range": [60, 90], "bmi_bias": -3, "severity_bias": -1},
        ]
        result = self.service.run_demo(members=members, tier="free")
        assert result.success is True
        local = result.data["local_results"]
        assert local[0]["name"] == "H1"
        assert local[1]["name"] == "H2"

    def test_member_default_samples(self):
        """Members without explicit samples should default to 20."""
        members = [{"name": "H1", "age_range": [18, 90]}]
        result = self.service.run_demo(members=members, tier="free")
        assert result.success is True

    # ── get_tier_limits ──

    def test_get_tier_limits_free(self):
        limits = ConsortiumDemoService.get_tier_limits("free")
        assert limits == TIER_DEMO_LIMITS["free"]

    def test_get_tier_limits_unknown_tier(self):
        limits = ConsortiumDemoService.get_tier_limits("nonexistent")
        assert limits == TIER_DEMO_LIMITS["free"]

    def test_get_tier_limits_enterprise(self):
        limits = ConsortiumDemoService.get_tier_limits("enterprise")
        assert limits["max_members"] == -1
        assert limits["max_samples_per_member"] == -1

    def test_consortium_result_total_samples(self):
        members = self._members(2, 15)
        result = self.service.run_demo(members=members, tier="free")
        assert result.success is True
        assert result.data["consortium_result"]["total_samples"] == 30


# ══════════════════════════════════════════════════════════════
# TestTrialService
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestTrialService(TestCase):

    def setUp(self):
        self.service = TrialService()

    # ── start_trial ──

    def test_start_trial_success(self):
        co = _company(tier="free")
        result = self.service.start_trial(co)
        assert result.success is True
        assert "trial_started_at" in result.data
        assert "subscription_id" in result.data
        co.refresh_from_db()
        assert co.is_trial is True
        assert Subscription.objects.filter(company=co).exists()

    def test_start_trial_fails_for_paid_tier(self):
        co = _company(tier="starter")
        result = self.service.start_trial(co)
        assert result.success is False
        assert result.error_code == "already_paid"

    def test_start_trial_fails_if_already_started(self):
        co = _company(tier="free")
        self.service.start_trial(co)
        result = self.service.start_trial(co)
        assert result.success is False
        assert result.error_code == "trial_already_started"

    def test_start_trial_creates_subscription(self):
        co = _company(tier="free")
        result = self.service.start_trial(co)
        assert result.success is True
        sub = Subscription.objects.get(company=co)
        assert sub.status == Subscription.Status.TRIALING
        assert sub.plan == "free"

    def test_start_trial_sets_14_days(self):
        co = _company(tier="free")
        self.service.start_trial(co)
        co.refresh_from_db()
        remaining = co.trial_days_remaining
        assert 13 <= remaining <= 14

    # ── get_usage_summary ──

    def test_get_usage_summary_basic(self):
        co = _company(tier="free")
        co.start_trial()
        result = self.service.get_usage_summary(co)
        assert result.success is True
        assert result.data["tier"] == "free"
        assert result.data["is_trial"] is True
        assert "usage" in result.data
        assert "limits" in result.data

    def test_usage_summary_with_tracking(self):
        co = _company(tier="free")
        co.start_trial()
        UsageTracking.objects.create(
            company=co,
            date=timezone.now().date(),
            api_requests=42,
            training_runs=3,
        )
        result = self.service.get_usage_summary(co)
        assert result.data["usage"]["api_requests_today"] == 42
        assert result.data["usage"]["training_runs_today"] == 3

    def test_usage_summary_with_uploads(self):
        co = _company(tier="free")
        co.start_trial()
        DataUpload.objects.create(
            company=co, file_name="a.csv", file_size=1024,
        )
        DataUpload.objects.create(
            company=co, file_name="b.csv", file_size=2048,
        )
        result = self.service.get_usage_summary(co)
        assert result.data["usage"]["data_uploaded_bytes"] == 3072

    def test_usage_summary_limits_match_tier(self):
        co = _company(tier="free")
        co.start_trial()
        result = self.service.get_usage_summary(co)
        limits = result.data["limits"]
        assert limits["daily_requests"] == Company.TIER_DAILY_LIMITS["free"]
        assert limits["training_runs_per_day"] == Company.TIER_TRAINING_LIMITS["free"]
        assert limits["upload_bytes"] == Company.TIER_UPLOAD_LIMITS["free"]

    def test_usage_summary_no_tracking_today(self):
        co = _company(tier="free")
        co.start_trial()
        result = self.service.get_usage_summary(co)
        assert result.data["usage"]["api_requests_today"] == 0

    # ── check_upload_allowed ──

    def test_upload_allowed_within_limit(self):
        co = _company(tier="free")
        co.start_trial()
        result = self.service.check_upload_allowed(co, 1024)
        assert result.success is True
        assert result.data["allowed"] is True

    def test_upload_blocked_exceeds_limit(self):
        co = _company(tier="free")
        co.start_trial()
        DataUpload.objects.create(
            company=co, file_name="big.csv",
            file_size=50 * 1024 * 1024,
            status="completed",
        )
        result = self.service.check_upload_allowed(co, 1)
        assert result.success is False
        assert result.error_code == "upload_limit_exceeded"

    def test_upload_blocked_trial_expired(self):
        co = _company(tier="free")
        co.trial_started_at = timezone.now() - timedelta(days=15)
        co.trial_expires_at = timezone.now() - timedelta(days=1)
        co.save()
        result = self.service.check_upload_allowed(co, 1024)
        assert result.success is False
        assert result.error_code == "trial_expired"

    def test_upload_allowed_enterprise_unlimited(self):
        co = _company(tier="enterprise")
        result = self.service.check_upload_allowed(co, 999_999_999)
        assert result.success is True

    def test_upload_remaining_bytes(self):
        co = _company(tier="free")
        co.start_trial()
        DataUpload.objects.create(
            company=co, file_name="small.csv",
            file_size=1024,
            status="completed",
        )
        result = self.service.check_upload_allowed(co, 1024)
        assert result.success is True
        expected_remaining = co.upload_limit - 1024
        assert result.data["remaining_bytes"] == expected_remaining

    # ── check_training_allowed ──

    def test_training_allowed(self):
        co = _company(tier="free")
        co.start_trial()
        result = self.service.check_training_allowed(co)
        assert result.success is True
        assert result.data["runs_today"] == 0

    def test_training_blocked_at_limit(self):
        co = _company(tier="free")
        co.start_trial()
        UsageTracking.objects.create(
            company=co,
            date=timezone.now().date(),
            training_runs=5,
        )
        result = self.service.check_training_allowed(co)
        assert result.success is False
        assert result.error_code == "training_limit_exceeded"

    def test_training_blocked_trial_expired(self):
        co = _company(tier="free")
        co.trial_started_at = timezone.now() - timedelta(days=15)
        co.trial_expires_at = timezone.now() - timedelta(days=1)
        co.save()
        result = self.service.check_training_allowed(co)
        assert result.success is False
        assert result.error_code == "trial_expired"

    def test_training_allowed_enterprise_unlimited(self):
        co = _company(tier="enterprise")
        result = self.service.check_training_allowed(co)
        assert result.success is True

    def test_training_remaining_runs(self):
        co = _company(tier="free")
        co.start_trial()
        UsageTracking.objects.create(
            company=co,
            date=timezone.now().date(),
            training_runs=3,
        )
        result = self.service.check_training_allowed(co)
        assert result.success is True
        assert result.data["remaining"] == 2

    # ── request_upgrade ──

    def test_upgrade_free_to_starter(self):
        co = _company(tier="free")
        self.service.start_trial(co)
        result = self.service.request_upgrade(co, "starter")
        assert result.success is True
        assert result.data["current_tier"] == "free"
        assert result.data["requested_tier"] == "starter"
        assert result.data["status"] == "pending_payment"
        # Tier is NOT yet changed — requires payment confirmation
        co.refresh_from_db()
        assert co.tier == "free"

    def test_upgrade_starter_to_professional(self):
        co = _company(tier="starter")
        now = timezone.now()
        Subscription.objects.create(
            company=co, plan="starter", status=Subscription.Status.ACTIVE,
            current_period_start=now, current_period_end=now + timedelta(days=30),
        )
        result = self.service.request_upgrade(co, "professional")
        assert result.success is True
        assert result.data["requested_tier"] == "professional"

    def test_upgrade_invalid_tier(self):
        co = _company(tier="free")
        result = self.service.request_upgrade(co, "nonexistent")
        assert result.success is False
        assert result.error_code == "invalid_tier"

    def test_upgrade_downgrade_rejected(self):
        co = _company(tier="professional")
        result = self.service.request_upgrade(co, "starter")
        assert result.success is False
        assert result.error_code == "invalid_upgrade"

    def test_upgrade_same_tier_rejected(self):
        co = _company(tier="starter")
        result = self.service.request_upgrade(co, "starter")
        assert result.success is False
        assert result.error_code == "invalid_upgrade"

    def test_upgrade_creates_subscription_if_missing(self):
        co = _company(tier="free")
        result = self.service.request_upgrade(co, "starter")
        assert result.success is True
        sub = Subscription.objects.get(company=co)
        assert sub.plan == "starter"
        # request_upgrade creates a PENDING subscription (payment required)
        assert sub.status == Subscription.Status.PENDING

    def test_upgrade_updates_existing_subscription(self):
        co = _company(tier="free")
        self.service.start_trial(co)
        result = self.service.request_upgrade(co, "professional")
        assert result.success is True
        sub = Subscription.objects.get(company=co)
        assert sub.plan == "professional"
        # Existing subscription is updated to PENDING
        assert sub.status == Subscription.Status.PENDING

    # ── get_plans_comparison ──

    def test_get_plans_comparison(self):
        plans = TrialService.get_plans_comparison()
        assert len(plans) == 4
        tiers = [p["tier"] for p in plans]
        assert "free" in tiers
        assert "starter" in tiers
        assert "professional" in tiers
        assert "enterprise" in tiers

    def test_plans_have_all_fields(self):
        plans = TrialService.get_plans_comparison()
        required_fields = {
            "tier", "name", "rate_limit_rpm", "daily_requests",
            "max_models", "max_consortiums", "max_upload_mb",
            "training_runs_per_day", "max_sandboxes",
        }
        for plan in plans:
            assert required_fields.issubset(plan.keys())

    def test_enterprise_unlimited_values(self):
        plans = TrialService.get_plans_comparison()
        enterprise = next(p for p in plans if p["tier"] == "enterprise")
        assert enterprise["daily_requests"] == -1
        assert enterprise["max_models"] == -1
        assert enterprise["max_upload_mb"] == -1

    # ── Boundary / edge cases ──

    def test_upload_exactly_at_limit(self):
        """Upload that would reach exactly the limit should be allowed."""
        co = _company(tier="free")
        co.start_trial()
        limit = co.upload_limit
        DataUpload.objects.create(
            company=co, file_name="partial.csv",
            file_size=limit - 100,
            status="completed",
        )
        result = self.service.check_upload_allowed(co, 100)
        assert result.success is True

    def test_upload_one_byte_over_limit(self):
        co = _company(tier="free")
        co.start_trial()
        limit = co.upload_limit
        DataUpload.objects.create(
            company=co, file_name="full.csv",
            file_size=limit,
            status="completed",
        )
        result = self.service.check_upload_allowed(co, 1)
        assert result.success is False

    def test_training_at_exactly_limit(self):
        co = _company(tier="free")
        co.start_trial()
        UsageTracking.objects.create(
            company=co,
            date=timezone.now().date(),
            training_runs=co.training_limit,
        )
        result = self.service.check_training_allowed(co)
        assert result.success is False

    def test_training_one_below_limit(self):
        co = _company(tier="free")
        co.start_trial()
        UsageTracking.objects.create(
            company=co,
            date=timezone.now().date(),
            training_runs=co.training_limit - 1,
        )
        result = self.service.check_training_allowed(co)
        assert result.success is True
        assert result.data["remaining"] == 1

"""
Tests for RateLimitService and RateLimitMiddleware.

Covers rate limiting, daily quotas, usage tracking, and middleware behaviour.
"""

from unittest.mock import MagicMock, patch

import pytest
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory, override_settings

from apps.core.models import Company, UsageTracking
from apps.core.services.base import ServiceContext
from apps.core.services.rate_limiting import (
    RateLimitMiddleware,
    RateLimitResult,
    RateLimitService,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def rl_company(db):
    return Company.objects.create(
        name="Rate Ltd",
        email="rate@ltd.com",
        industry="tech",
        tier=Company.Tier.STARTER,
    )


@pytest.fixture
def enterprise_company(db):
    return Company.objects.create(
        name="Enterprise Inc",
        email="ent@inc.com",
        industry="finance",
        tier=Company.Tier.ENTERPRISE,
    )


@pytest.fixture
def factory():
    return RequestFactory()


# ===========================================================================
# RateLimitService Tests
# ===========================================================================


LOCMEM_CACHE = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "rate-limit-test",
    }
}


@pytest.mark.django_db
class TestRateLimitServiceCheck:
    def test_check_without_company_returns_default(self):
        service = RateLimitService()
        result = service.check_rate_limit(company=None)

        assert isinstance(result, RateLimitResult)
        assert result.allowed is True
        assert result.limit == 10

    @override_settings(CACHES=LOCMEM_CACHE)
    def test_check_with_company_allowed(self, rl_company):
        from django.core.cache import cache

        cache.clear()

        service = RateLimitService()
        result = service.check_rate_limit(company=rl_company)

        assert result.allowed is True
        assert result.limit == rl_company.rate_limit
        assert result.remaining >= 0

    @override_settings(CACHES=LOCMEM_CACHE)
    def test_check_rate_limit_exceeded(self, rl_company):
        from django.core.cache import cache

        cache.clear()
        # Pre-fill cache to exceed limit
        cache_key = f"rate_limit:{rl_company.id}"
        cache.set(cache_key, rl_company.rate_limit + 10, 60)

        service = RateLimitService()
        result = service.check_rate_limit(company=rl_company)

        assert result.allowed is False
        assert result.remaining == 0
        assert result.retry_after is not None

    def test_check_rate_limit_cache_fallback(self, rl_company):
        """When cache raises exception, request should still be allowed."""
        service = RateLimitService()

        with patch("apps.core.services.rate_limiting.cache") as mock_cache:
            mock_cache.get.side_effect = Exception("Cache down")
            result = service.check_rate_limit(company=rl_company)

        assert result.allowed is True

    def test_check_uses_context_company(self, rl_company):
        context = ServiceContext(company=rl_company)
        service = RateLimitService(context)

        with patch("apps.core.services.rate_limiting.cache") as mock_cache:
            mock_cache.get.return_value = 0
            mock_cache.incr.return_value = 1
            result = service.check_rate_limit()

        assert result.allowed is True
        assert result.limit == rl_company.rate_limit


@pytest.mark.django_db
class TestRateLimitServiceDailyQuota:
    def test_check_daily_quota_within_limit(self, rl_company):
        service = RateLimitService()
        result = service.check_daily_quota(company=rl_company)

        assert result.success is True

    def test_check_daily_quota_exceeded(self, rl_company):
        tracking = UsageTracking.get_or_create_today(rl_company)
        # Set requests way above daily limit
        tracking.api_requests = rl_company.daily_limit + 100
        tracking.save()

        service = RateLimitService()
        result = service.check_daily_quota(company=rl_company)

        assert result.success is False
        assert result.error_code == "daily_quota_exceeded"

    def test_check_daily_quota_unlimited(self, enterprise_company):
        """Enterprise tier with unlimited (-1) daily limit should always pass."""
        service = RateLimitService()
        result = service.check_daily_quota(company=enterprise_company)

        assert result.success is True

    def test_check_daily_quota_no_company(self):
        service = RateLimitService()
        result = service.check_daily_quota(company=None)

        assert result.success is True


@pytest.mark.django_db
class TestRateLimitServiceUsage:
    def test_increment_usage_requests(self, rl_company):
        service = RateLimitService()
        service.increment_usage(company=rl_company)

        tracking = UsageTracking.objects.filter(company=rl_company).first()
        assert tracking is not None
        assert tracking.api_requests >= 1

    def test_increment_usage_predictions(self, rl_company):
        service = RateLimitService()
        service.increment_usage(company=rl_company, predictions=5)

        tracking = UsageTracking.objects.filter(company=rl_company).first()
        assert tracking.predictions >= 5

    def test_increment_usage_no_company_noop(self):
        service = RateLimitService()
        service.increment_usage(company=None)
        # Should not raise


@pytest.mark.django_db
class TestRateLimitServiceStats:
    def test_get_usage_stats_structure(self, rl_company):
        service = RateLimitService()
        result = service.get_usage_stats(company=rl_company)

        assert result.success
        stats = result.data
        assert "tier" in stats
        assert "limits" in stats
        assert "today" in stats
        assert "month" in stats

    def test_get_usage_stats_today(self, rl_company):
        tracking = UsageTracking.get_or_create_today(rl_company)
        tracking.api_requests = 42
        tracking.save()

        service = RateLimitService()
        result = service.get_usage_stats(company=rl_company)

        assert result.data["today"]["requests"] == 42

    def test_get_usage_stats_monthly(self, rl_company):
        service = RateLimitService()
        service.increment_usage(company=rl_company)

        result = service.get_usage_stats(company=rl_company)

        assert result.data["month"]["requests"] >= 1

    def test_get_usage_stats_no_company_fails(self):
        service = RateLimitService()
        result = service.get_usage_stats(company=None)

        assert not result.success
        assert result.error_code == "no_company"


@pytest.mark.django_db
class TestRateLimitServiceRecordHit:
    @override_settings(CACHES=LOCMEM_CACHE)
    def test_record_rate_limit_hit(self, rl_company):
        service = RateLimitService()

        with patch("apps.core.services.webhook.trigger_webhook_event"):
            service._record_rate_limit_hit(rl_company)

        tracking = UsageTracking.objects.filter(company=rl_company).first()
        assert tracking.rate_limit_hits >= 1


# ===========================================================================
# RateLimitMiddleware Tests
# ===========================================================================


@pytest.mark.django_db
class TestRateLimitMiddleware:
    def _get_response(self, request):
        return HttpResponse("OK")

    def test_skip_non_api_requests(self, factory):
        middleware = RateLimitMiddleware(self._get_response)
        request = factory.get("/admin/")

        response = middleware(request)

        assert response.status_code == 200
        assert "X-RateLimit-Limit" not in response

    def test_skip_excluded_paths(self, factory):
        middleware = RateLimitMiddleware(self._get_response)
        request = factory.get("/api/v2/health/")

        response = middleware(request)

        assert response.status_code == 200
        assert "X-RateLimit-Limit" not in response

    def test_adds_rate_limit_headers(self, factory):
        middleware = RateLimitMiddleware(self._get_response)
        request = factory.get("/api/v2/models/")
        request.user = MagicMock(is_authenticated=False)

        response = middleware(request)

        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response

    @override_settings(CACHES=LOCMEM_CACHE)
    def test_blocks_when_rate_limited(self, factory, rl_company):
        from django.core.cache import cache

        cache.clear()
        cache_key = f"rate_limit:{rl_company.id}"
        cache.set(cache_key, rl_company.rate_limit + 100, 60)

        middleware = RateLimitMiddleware(self._get_response)
        request = factory.get("/api/v2/models/")
        mock_user = MagicMock(is_authenticated=True, company=rl_company)
        request.user = mock_user

        with patch("apps.core.services.webhook.trigger_webhook_event"):
            response = middleware(request)

        assert response.status_code == 429

    def test_get_company_from_authenticated_user(self, factory, rl_company):
        middleware = RateLimitMiddleware(self._get_response)
        request = factory.get("/api/v2/test/")
        request.user = MagicMock(is_authenticated=True, company=rl_company)

        company = middleware._get_company(request)
        assert company == rl_company

    def test_get_company_unauthenticated(self, factory):
        middleware = RateLimitMiddleware(self._get_response)
        request = factory.get("/api/v2/test/")
        request.user = MagicMock(is_authenticated=False)

        company = middleware._get_company(request)
        assert company is None

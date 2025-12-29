"""
Rate limiting service for tier-based API throttling.

Provides rate limiting based on company tier with Redis-backed tracking.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from .base import BaseService, ServiceContext, ServiceResult

if TYPE_CHECKING:
    from apps.core.models import Company

logger = logging.getLogger(__name__)


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""

    allowed: bool
    limit: int
    remaining: int
    reset_at: int  # Unix timestamp
    retry_after: int | None = None  # Seconds until allowed (if blocked)


class RateLimitService(BaseService):
    """
    Service for rate limiting API requests based on company tier.

    Features:
    - Per-minute rate limiting
    - Daily quota tracking
    - Tier-based limits (Free, Starter, Professional, Enterprise)
    - Redis-backed for distributed environments
    - Graceful fallback when cache unavailable
    """

    # Cache key prefixes
    RATE_KEY_PREFIX = "rate_limit:"
    DAILY_KEY_PREFIX = "daily_quota:"

    # Window size in seconds
    RATE_WINDOW = 60  # 1 minute

    def __init__(self, context: ServiceContext | None = None) -> None:
        super().__init__(context)

    def check_rate_limit(self, company: Company | None = None) -> RateLimitResult:
        """
        Check if a request should be rate limited.

        Args:
            company: Company to check (uses context if not provided)

        Returns:
            RateLimitResult indicating if request is allowed
        """
        target_company = company or self.company
        if not target_company:
            # No company = use default low limit
            return RateLimitResult(
                allowed=True,
                limit=10,
                remaining=10,
                reset_at=int(time.time()) + self.RATE_WINDOW,
            )

        limit = target_company.rate_limit
        cache_key = f"{self.RATE_KEY_PREFIX}{target_company.id}"

        try:
            # Atomic increment with expiry
            current = cache.get(cache_key, 0)
            current_time = int(time.time())
            window_start = current_time - (current_time % self.RATE_WINDOW)
            reset_at = window_start + self.RATE_WINDOW

            if current >= limit:
                # Rate limit exceeded
                retry_after = reset_at - current_time
                self._record_rate_limit_hit(target_company)
                return RateLimitResult(
                    allowed=False,
                    limit=limit,
                    remaining=0,
                    reset_at=reset_at,
                    retry_after=retry_after,
                )

            # Increment counter
            new_count = cache.incr(cache_key, 1)
            if new_count == 1:
                # First request in window, set expiry
                cache.expire(cache_key, self.RATE_WINDOW)

            remaining = max(0, limit - new_count)

            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=remaining,
                reset_at=reset_at,
            )

        except Exception as e:
            # Cache unavailable, allow request but log warning
            logger.warning(f"Rate limit check failed: {e}, allowing request")
            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=limit,
                reset_at=int(time.time()) + self.RATE_WINDOW,
            )

    def check_daily_quota(self, company: Company | None = None) -> ServiceResult[bool]:
        """
        Check if company is within daily quota.

        Args:
            company: Company to check (uses context if not provided)

        Returns:
            ServiceResult with True if within quota, False if exceeded
        """
        from apps.core.models import UsageTracking

        target_company = company or self.company
        if not target_company:
            return ServiceResult.ok(True)

        daily_limit = target_company.daily_limit
        if daily_limit == -1:  # Unlimited
            return ServiceResult.ok(True)

        tracking = UsageTracking.get_or_create_today(target_company)

        if tracking.api_requests >= daily_limit:
            return ServiceResult.fail(
                f"Daily quota exceeded ({daily_limit} requests)",
                error_code="daily_quota_exceeded",
                details={
                    "limit": daily_limit,
                    "used": tracking.api_requests,
                    "resets_at": (timezone.now().date() + timezone.timedelta(days=1)).isoformat(),
                },
            )

        return ServiceResult.ok(True)

    def increment_usage(self, company: Company | None = None, predictions: int = 0) -> None:
        """
        Increment usage counters for a company.

        Args:
            company: Company to track usage for
            predictions: Number of predictions made (optional)
        """
        from apps.core.models import UsageTracking

        target_company = company or self.company
        if not target_company:
            return

        tracking = UsageTracking.get_or_create_today(target_company)
        tracking.increment_requests()

        if predictions > 0:
            tracking.increment_predictions(predictions)

    def _record_rate_limit_hit(self, company: Company) -> None:
        """Record a rate limit violation for monitoring."""
        from apps.core.models import UsageTracking

        try:
            tracking = UsageTracking.get_or_create_today(company)
            tracking.increment_rate_limit_hits()

            # Trigger webhook for rate limit exceeded
            from apps.core.services.webhook import trigger_webhook_event

            trigger_webhook_event(
                "security.ratelimit.exceeded",
                {
                    "company_id": str(company.id),
                    "tier": company.tier,
                    "limit": company.rate_limit,
                },
                company,
            )
        except Exception as e:
            logger.error(f"Failed to record rate limit hit: {e}")

    def get_usage_stats(self, company: Company | None = None) -> ServiceResult[dict]:
        """
        Get usage statistics for a company.

        Args:
            company: Company to get stats for

        Returns:
            ServiceResult with usage statistics
        """
        from django.db.models import Sum

        from apps.core.models import UsageTracking

        target_company = company or self.company
        if not target_company:
            return ServiceResult.fail("No company specified", error_code="no_company")

        today = timezone.now().date()
        today_tracking = UsageTracking.objects.filter(
            company=target_company,
            date=today,
        ).first()

        # Get monthly totals
        month_start = today.replace(day=1)
        monthly_stats = UsageTracking.objects.filter(
            company=target_company,
            date__gte=month_start,
        ).aggregate(
            total_requests=Sum("api_requests"),
            total_predictions=Sum("predictions"),
            total_rate_limit_hits=Sum("rate_limit_hits"),
        )

        stats = {
            "tier": target_company.tier,
            "limits": {
                "rate_per_minute": target_company.rate_limit,
                "daily_requests": target_company.daily_limit,
                "max_models": target_company.model_limit,
                "max_consortiums": target_company.consortium_limit,
            },
            "today": {
                "requests": today_tracking.api_requests if today_tracking else 0,
                "predictions": today_tracking.predictions if today_tracking else 0,
                "rate_limit_hits": today_tracking.rate_limit_hits if today_tracking else 0,
            },
            "month": {
                "requests": monthly_stats["total_requests"] or 0,
                "predictions": monthly_stats["total_predictions"] or 0,
                "rate_limit_hits": monthly_stats["total_rate_limit_hits"] or 0,
            },
        }

        return ServiceResult.ok(stats)


class RateLimitMiddleware:
    """
    Django middleware for rate limiting API requests.

    Applies rate limiting to all API endpoints based on company tier.
    """

    EXCLUDED_PATHS = [
        "/api/v2/health/",
        "/api/v2/schema/",
        "/api/v2/docs/",
        "/api/v2/auth/token/",
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip non-API requests
        if not request.path.startswith("/api/"):
            return self.get_response(request)

        # Skip excluded paths
        for path in self.EXCLUDED_PATHS:
            if request.path.startswith(path):
                return self.get_response(request)

        # Get company from request
        company = self._get_company(request)

        # Check rate limit
        context = ServiceContext(company=company)
        service = RateLimitService(context)

        result = service.check_rate_limit(company)

        if not result.allowed:
            from django.http import JsonResponse

            return JsonResponse(
                {
                    "error": {
                        "code": "rate_limit_exceeded",
                        "message": "Rate limit exceeded. Please slow down.",
                        "status": 429,
                        "details": {
                            "limit": result.limit,
                            "retry_after": result.retry_after,
                            "reset_at": result.reset_at,
                        },
                    }
                },
                status=429,
                headers={
                    "X-RateLimit-Limit": str(result.limit),
                    "X-RateLimit-Remaining": str(result.remaining),
                    "X-RateLimit-Reset": str(result.reset_at),
                    "Retry-After": str(result.retry_after),
                },
            )

        # Check daily quota
        quota_result = service.check_daily_quota(company)
        if not quota_result.success:
            from django.http import JsonResponse

            return JsonResponse(
                {
                    "error": {
                        "code": quota_result.error_code,
                        "message": quota_result.error,
                        "status": 429,
                        "details": quota_result.details,
                    }
                },
                status=429,
            )

        # Process request
        response = self.get_response(request)

        # Add rate limit headers
        response["X-RateLimit-Limit"] = str(result.limit)
        response["X-RateLimit-Remaining"] = str(result.remaining)
        response["X-RateLimit-Reset"] = str(result.reset_at)

        # Track usage
        if response.status_code < 400:
            service.increment_usage(company)

        return response

    def _get_company(self, request):
        """Extract company from request authentication."""
        if hasattr(request, "user") and request.user.is_authenticated:
            return getattr(request.user, "company", None)
        return None

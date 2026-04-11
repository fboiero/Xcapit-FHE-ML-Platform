"""
Tier-based rate limiting service and middleware for Xcapit FHE-ML Platform.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from django.core.cache import cache
from django.db.models import Sum
from django.http import JsonResponse
from django.utils import timezone

from .base import BaseService, ServiceContext, ServiceResult

if TYPE_CHECKING:
    from apps.core.models import Company

logger = logging.getLogger(__name__)

# Default rate limit for unauthenticated / unknown requests
DEFAULT_RATE_LIMIT = 10


@dataclass
class RateLimitResult:
    """Result of a rate-limit check."""

    allowed: bool
    limit: int
    remaining: int
    retry_after: int | None = None


class RateLimitService(BaseService):
    """
    Service-layer rate limiting with sliding-window counters.

    Features:
    - Per-company rate limit checks via Django cache
    - Daily quota enforcement via UsageTracking
    - Usage statistics aggregation
    """

    def __init__(self, context: ServiceContext | None = None) -> None:
        super().__init__(context)

    # ------------------------------------------------------------------
    # Rate-limit check
    # ------------------------------------------------------------------

    def check_rate_limit(
        self, company: Company | None = None
    ) -> RateLimitResult:
        """Check whether *company* is within the per-minute rate limit.

        Falls back to ``self.context.company`` when *company* is not
        supplied.  If the cache is unavailable the request is allowed
        (fail-open).
        """
        company = company or self.company

        if company is None:
            return RateLimitResult(
                allowed=True,
                limit=DEFAULT_RATE_LIMIT,
                remaining=DEFAULT_RATE_LIMIT,
            )

        limit = company.rate_limit
        cache_key = f"rate_limit:{company.id}"

        try:
            current = cache.get(cache_key, 0)

            if limit != -1 and current >= limit:
                retry_after = 60 - (int(time.time()) % 60)
                return RateLimitResult(
                    allowed=False,
                    limit=limit,
                    remaining=0,
                    retry_after=retry_after,
                )

            # Increment
            if current == 0:
                cache.set(cache_key, 1, timeout=60)
            else:
                try:
                    cache.incr(cache_key)
                except ValueError:
                    cache.set(cache_key, current + 1, timeout=60)

            remaining = max(0, limit - current - 1) if limit != -1 else limit
            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=remaining,
            )
        except Exception:
            logger.warning("Rate limit cache unavailable — allowing request")
            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=limit,
            )

    # ------------------------------------------------------------------
    # Daily quota
    # ------------------------------------------------------------------

    def check_daily_quota(
        self, company: Company | None = None
    ) -> ServiceResult:
        """Check if *company* is within its daily API-request quota."""
        from apps.core.models import UsageTracking

        company = company or self.company

        if company is None:
            return ServiceResult.ok()

        daily_limit = company.daily_limit
        if daily_limit == -1:
            return ServiceResult.ok()

        tracking = UsageTracking.get_or_create_today(company)
        if tracking.api_requests >= daily_limit:
            return ServiceResult.fail(
                "Daily quota exceeded",
                error_code="daily_quota_exceeded",
            )
        return ServiceResult.ok()

    # ------------------------------------------------------------------
    # Usage tracking
    # ------------------------------------------------------------------

    def increment_usage(
        self,
        company: Company | None = None,
        predictions: int = 0,
    ) -> None:
        """Increment the daily usage counters for *company*."""
        from apps.core.models import UsageTracking

        company = company or self.company
        if company is None:
            return

        tracking = UsageTracking.get_or_create_today(company)
        tracking.increment_requests()
        if predictions:
            tracking.increment_predictions(predictions)

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_usage_stats(
        self, company: Company | None = None
    ) -> ServiceResult[dict[str, Any]]:
        """Return aggregated usage stats for *company*."""
        from apps.core.models import UsageTracking

        company = company or self.company
        if company is None:
            return ServiceResult.fail(
                "Company required for usage stats",
                error_code="no_company",
            )

        today = timezone.now().date()
        tracking = UsageTracking.get_or_create_today(company)

        # Monthly aggregation
        first_of_month = today.replace(day=1)
        monthly = (
            UsageTracking.objects.filter(
                company=company,
                date__gte=first_of_month,
            ).aggregate(
                requests=Sum("api_requests"),
                preds=Sum("predictions"),
            )
        )

        return ServiceResult.ok(
            {
                "tier": company.tier,
                "limits": {
                    "rate_limit": company.rate_limit,
                    "daily_limit": company.daily_limit,
                },
                "today": {
                    "requests": tracking.api_requests,
                    "predictions": tracking.predictions,
                },
                "month": {
                    "requests": monthly["requests"] or 0,
                    "predictions": monthly["preds"] or 0,
                },
            }
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _record_rate_limit_hit(self, company: Company) -> None:
        """Record a rate-limit violation for auditing purposes."""
        from apps.core.models import UsageTracking

        tracking = UsageTracking.get_or_create_today(company)
        tracking.increment_rate_limit_hits()

        # Fire webhook event (best-effort)
        try:
            from apps.core.services.webhook import trigger_webhook_event

            trigger_webhook_event(
                company=company,
                event="rate_limit.exceeded",
                data={"company_id": str(company.id)},
            )
        except Exception:
            logger.debug("Webhook trigger skipped for rate-limit hit")


# ======================================================================
# Middleware
# ======================================================================

# Paths excluded from rate limiting
EXCLUDED_PATHS = (
    "/api/v2/health/",
    "/api/v2/auth/",
)


class RateLimitMiddleware:
    """
    Per-company rate limiting based on tier.

    Uses Django cache (Redis) for sliding-window counters.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self._service = RateLimitService()

    def __call__(self, request):
        # Skip rate limiting for non-API paths
        if not request.path.startswith("/api/"):
            return self.get_response(request)

        # Skip excluded paths
        for excluded in EXCLUDED_PATHS:
            if request.path.startswith(excluded):
                return self.get_response(request)

        company = self._get_company(request)

        # Always add headers for API paths
        if company is None:
            response = self.get_response(request)
            response["X-RateLimit-Limit"] = str(DEFAULT_RATE_LIMIT)
            response["X-RateLimit-Remaining"] = str(DEFAULT_RATE_LIMIT)
            return response

        # Check rate limit
        result = self._service.check_rate_limit(company=company)

        if not result.allowed:
            self._service._record_rate_limit_hit(company)
            return JsonResponse(
                {
                    "detail": "Rate limit exceeded.",
                    "retry_after": result.retry_after or 60,
                },
                status=429,
            )

        response = self.get_response(request)
        response["X-RateLimit-Limit"] = str(result.limit)
        response["X-RateLimit-Remaining"] = str(result.remaining)
        return response

    @staticmethod
    def _get_company(request):
        """Extract Company from request user."""
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return None
        return getattr(user, "company", None)

"""
Contribution service for Xcapit FHE-ML Platform.

Encapsulates business logic for consortium contribution operations.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from django.db.models import Count, Sum

from apps.core.services.base import BaseService, ServiceResult

if TYPE_CHECKING:
    from apps.consortiums.models import Consortium, ContributionProof
    from apps.core.models import Company

logger = logging.getLogger(__name__)


class ContributionService(BaseService):
    """
    Service for consortium contribution business logic.

    Handles:
    - Contribution summary and analytics
    - Contribution weight calculation
    - Contribution validation
    """

    def get_contribution_summary(
        self,
        consortium: Consortium,
        verified_only: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Get contribution summary by company for a consortium.

        Args:
            consortium: The consortium to get summary for
            verified_only: Only include verified contributions

        Returns:
            List of contribution summaries per company
        """
        from apps.consortiums.models import ContributionProof

        queryset = ContributionProof.objects.filter(consortium=consortium)

        if verified_only:
            queryset = queryset.filter(verified=True)

        contributions = (
            queryset.values("company__id", "company__name")
            .annotate(
                total_records=Sum("record_count"),
                total_features=Sum("feature_count"),
                contribution_count=Count("id"),
            )
            .order_by("-total_records")
        )

        # Calculate weights
        total_records = sum(c["total_records"] or 0 for c in contributions)

        result = []
        for c in contributions:
            records = c["total_records"] or 0
            weight = records / total_records if total_records > 0 else 0

            result.append({
                "company_id": str(c["company__id"]),
                "company_name": c["company__name"],
                "total_records": records,
                "total_features": c["total_features"] or 0,
                "contribution_count": c["contribution_count"],
                "weight": round(weight, 4),
            })

        return result

    def get_company_contributions(
        self,
        consortium: Consortium,
        company: Company,
    ) -> list[ContributionProof]:
        """
        Get all contributions from a specific company.

        Args:
            consortium: The consortium
            company: The contributing company

        Returns:
            List of contribution proofs
        """
        from apps.consortiums.models import ContributionProof

        return list(
            ContributionProof.objects.filter(
                consortium=consortium,
                company=company,
            ).order_by("-created_at")
        )

    def get_contribution_stats(
        self,
        consortium: Consortium,
    ) -> dict[str, Any]:
        """
        Get overall contribution statistics for a consortium.

        Args:
            consortium: The consortium to analyze

        Returns:
            Dictionary with contribution statistics
        """
        from apps.consortiums.models import ContributionProof

        all_contributions = ContributionProof.objects.filter(consortium=consortium)
        verified = all_contributions.filter(verified=True)

        # Aggregate stats
        totals = verified.aggregate(
            total_records=Sum("record_count"),
            total_features=Sum("feature_count"),
        )

        # Get contributor count
        contributor_count = verified.values("company").distinct().count()

        # Recent activity (last 30 days)
        from django.utils import timezone
        from datetime import timedelta

        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent = verified.filter(created_at__gte=thirty_days_ago)
        recent_count = recent.count()
        recent_records = recent.aggregate(total=Sum("record_count"))["total"] or 0

        return {
            "consortium_id": str(consortium.id),
            "total_contributions": verified.count(),
            "total_records": totals["total_records"] or 0,
            "total_features": totals["total_features"] or 0,
            "contributor_count": contributor_count,
            "pending_verification": all_contributions.filter(verified=False).count(),
            "recent_activity": {
                "period_days": 30,
                "contributions": recent_count,
                "records": recent_records,
            },
        }

    def calculate_contribution_weights(
        self,
        consortium: Consortium,
    ) -> dict[str, float]:
        """
        Calculate contribution weights for all members.

        Weights are based on verified record count relative to total.

        Args:
            consortium: The consortium

        Returns:
            Dictionary mapping company_id to weight (0-1)
        """
        from apps.consortiums.models import ContributionProof

        contributions = (
            ContributionProof.objects.filter(
                consortium=consortium,
                verified=True,
            )
            .values("company_id")
            .annotate(total_records=Sum("record_count"))
        )

        total_records = sum(c["total_records"] or 0 for c in contributions)

        weights = {}
        for c in contributions:
            company_id = str(c["company_id"])
            records = c["total_records"] or 0
            weights[company_id] = records / total_records if total_records > 0 else 0

        return weights

    def verify_contribution(
        self,
        contribution: ContributionProof,
        verifier_notes: str = "",
    ) -> ServiceResult[ContributionProof]:
        """
        Mark a contribution as verified.

        Args:
            contribution: The contribution to verify
            verifier_notes: Optional notes from verifier

        Returns:
            ServiceResult with verified contribution
        """
        from django.utils import timezone

        if contribution.verified:
            return ServiceResult.fail(
                "Contribution is already verified",
                error_code="already_verified",
            )

        contribution.verified = True
        contribution.verified_at = timezone.now()
        contribution.save(update_fields=["verified", "verified_at", "updated_at"])

        logger.info(f"Contribution {contribution.id} verified")

        return ServiceResult.ok(contribution)

    def get_leaderboard(
        self,
        consortium: Consortium,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Get contribution leaderboard for a consortium.

        Args:
            consortium: The consortium
            limit: Maximum number of entries

        Returns:
            List of leaderboard entries
        """
        summary = self.get_contribution_summary(consortium)

        # Sort by records and limit
        sorted_summary = sorted(
            summary,
            key=lambda x: x["total_records"],
            reverse=True,
        )[:limit]

        # Add rank
        for i, entry in enumerate(sorted_summary, 1):
            entry["rank"] = i

        return sorted_summary

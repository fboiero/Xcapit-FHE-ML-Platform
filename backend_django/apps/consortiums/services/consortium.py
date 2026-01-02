"""
Consortium service for Xcapit FHE-ML Platform.

Encapsulates business logic for consortium operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from apps.core.services.base import BaseService, ServiceResult
from django.db import transaction
from django.db.models import Avg, Count, Sum

if TYPE_CHECKING:

    from apps.consortiums.models import Consortium


@dataclass
class ConsortiumStats:
    """Statistics for a consortium."""

    total_members: int
    active_members: int
    pending_members: int
    total_contributions: int
    total_records: int
    avg_quality_score: float | None
    training_runs: int


class ConsortiumService(BaseService):
    """
    Service for consortium business logic.

    Handles:
    - Consortium creation and updates
    - Statistics calculation
    - Training coordination
    - Member analytics
    """

    def get_stats(self, consortium: Consortium) -> ServiceResult[ConsortiumStats]:
        """
        Calculate comprehensive statistics for a consortium.

        Args:
            consortium: The consortium to analyze

        Returns:
            ServiceResult containing ConsortiumStats
        """
        from apps.consortiums.models import ConsortiumMember, ContributionProof
        from apps.data_quality.models import QualityAssessment

        members = ConsortiumMember.objects.filter(consortium=consortium)
        contributions = ContributionProof.objects.filter(
            consortium=consortium,
            verification_status=ContributionProof.VerificationStatus.VERIFIED,
        )

        # Aggregate contribution stats
        contribution_stats = contributions.aggregate(
            total_contributions=Count("id"),
            total_records=Sum("record_count"),
        )

        # Quality score
        quality_stats = QualityAssessment.objects.filter(
            consortium=consortium,
            status=QualityAssessment.Status.COMPLETED,
        ).aggregate(avg_score=Avg("overall_score"))

        # Training runs
        training_count = consortium.training_runs.count() if hasattr(consortium, "training_runs") else 0

        stats = ConsortiumStats(
            total_members=members.filter(status=ConsortiumMember.Status.ACTIVE).count(),
            active_members=members.filter(status=ConsortiumMember.Status.ACTIVE).count(),
            pending_members=members.filter(status=ConsortiumMember.Status.PENDING).count(),
            total_contributions=contribution_stats["total_contributions"] or 0,
            total_records=contribution_stats["total_records"] or 0,
            avg_quality_score=quality_stats["avg_score"],
            training_runs=training_count,
        )

        return ServiceResult.ok(stats)

    def can_start_training(self, consortium: Consortium) -> ServiceResult[bool]:
        """
        Check if consortium can start a training run.

        Args:
            consortium: The consortium to check

        Returns:
            ServiceResult with boolean indicating if training can start
        """
        from apps.consortiums.models import Consortium as ConsortiumModel
        from apps.consortiums.models import ConsortiumMember

        # Check consortium status
        if consortium.status != ConsortiumModel.Status.ACTIVE:
            return ServiceResult.fail(
                "Consortium must be active to start training",
                error_code="consortium_not_active",
            )

        # Check minimum members
        active_members = ConsortiumMember.objects.filter(
            consortium=consortium,
            status=ConsortiumMember.Status.ACTIVE,
        ).count()

        if active_members < consortium.min_members:
            return ServiceResult.fail(
                f"Minimum {consortium.min_members} active members required",
                error_code="insufficient_members",
                details={"current": active_members, "required": consortium.min_members},
            )

        return ServiceResult.ok(True)

    @transaction.atomic
    def start_training(self, consortium: Consortium) -> ServiceResult[dict[str, Any]]:
        """
        Start a federated training run for the consortium.

        Args:
            consortium: The consortium to start training for

        Returns:
            ServiceResult with training run details
        """
        from apps.core.services import AuditService

        # Validate
        can_start = self.can_start_training(consortium)
        if not can_start.success:
            return ServiceResult.fail(
                can_start.error or "Cannot start training",
                error_code=can_start.error_code or "training_error",
            )

        # Create training run (simplified - actual implementation would be more complex)
        training_data = {
            "consortium_id": str(consortium.id),
            "status": "started",
            "message": "Federated training initiated",
        }

        # Audit log
        if self.request:
            AuditService.log_from_request(
                self.request,
                action="training_started",
                resource_type="consortium",
                resource_id=consortium.id,
            )

        return ServiceResult.ok(training_data)

    def get_member_rankings(
        self,
        consortium: Consortium,
        limit: int = 10,
    ) -> ServiceResult[list[dict[str, Any]]]:
        """
        Get member rankings by contribution.

        Args:
            consortium: The consortium
            limit: Maximum number of members to return

        Returns:
            ServiceResult with ranked member list
        """
        from apps.consortiums.models import ConsortiumMember, ContributionProof

        members = ConsortiumMember.objects.filter(
            consortium=consortium,
            status=ConsortiumMember.Status.ACTIVE,
        ).select_related("company")

        rankings = []
        for member in members:
            contributions = ContributionProof.objects.filter(
                consortium=consortium,
                company=member.company,
                verification_status=ContributionProof.VerificationStatus.VERIFIED,
            ).aggregate(
                total_records=Sum("record_count"),
                contribution_count=Count("id"),
            )

            rankings.append({
                "company_id": str(member.company.id),
                "company_name": member.company.name,
                "role": member.role,
                "total_records": contributions["total_records"] or 0,
                "contributions": contributions["contribution_count"] or 0,
            })

        # Sort by total records descending
        rankings.sort(key=lambda x: x["total_records"], reverse=True)

        return ServiceResult.ok(rankings[:limit])

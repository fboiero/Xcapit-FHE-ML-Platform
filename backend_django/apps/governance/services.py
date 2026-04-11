"""
Governance services for Xcapit FHE-ML Platform.

Handles proposal execution logic.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from apps.core.services.base import BaseService, ServiceContext, ServiceResult
from django.db import transaction
from django.utils import timezone

if TYPE_CHECKING:
    from django.http import HttpRequest

    from .models import Proposal

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of proposal execution."""

    success: bool
    message: str
    data: dict[str, Any] | None = None


class ProposalExecutionService(BaseService):
    """
    Service for executing passed proposals.

    Dispatches to appropriate handler based on proposal type.
    """

    def __init__(
        self,
        context: ServiceContext | None = None,
        request: HttpRequest | None = None,
    ) -> None:
        """Initialize service with context or request."""
        if request and not context:
            context = ServiceContext.from_request(request)
        super().__init__(context)

    def execute(self, proposal: Proposal) -> ServiceResult[ExecutionResult]:
        """
        Execute a passed proposal.

        Args:
            proposal: The proposal to execute

        Returns:
            ServiceResult with execution outcome
        """
        from .models import AuditEvent, Proposal

        # Validate proposal state
        if proposal.status != Proposal.Status.PASSED:
            return ServiceResult.fail(
                f"Proposal must be PASSED to execute, current status: {proposal.status}",
                error_code="invalid_status",
            )

        # Get handler for proposal type
        handler = self._get_handler(proposal.proposal_type)
        if not handler:
            return ServiceResult.fail(
                f"No handler for proposal type: {proposal.proposal_type}",
                error_code="no_handler",
            )

        try:
            with transaction.atomic():
                # Execute the proposal
                result = handler(proposal)

                if result.success:
                    proposal.status = Proposal.Status.EXECUTED
                    proposal.executed_at = timezone.now()
                    proposal.save(update_fields=["status", "executed_at"])

                    # Create audit event
                    AuditEvent.objects.create(
                        consortium=proposal.consortium,
                        actor=proposal.proposer,
                        event_type=AuditEvent.EventType.PROPOSAL_EXECUTED,
                        target_id=str(proposal.id),
                        target_type="proposal",
                        data={
                            "proposal_type": proposal.proposal_type,
                            "result": result.message,
                            "data": result.data,
                        },
                        previous_hash=AuditEvent.get_previous_hash(proposal.consortium_id),
                    )

                    logger.info(
                        f"Proposal {proposal.id} executed: {result.message}"
                    )
                else:
                    logger.warning(
                        f"Proposal {proposal.id} execution failed: {result.message}"
                    )

                return ServiceResult.ok(result)

        except Exception as e:
            logger.exception(f"Error executing proposal {proposal.id}: {e}")
            return ServiceResult.fail(
                f"Execution error: {str(e)}",
                error_code="execution_error",
            )

    def _get_handler(self, proposal_type: str):
        """Get handler function for proposal type."""
        from .models import Proposal

        handlers = {
            Proposal.Type.ADD_MEMBER: self._execute_add_member,
            Proposal.Type.REMOVE_MEMBER: self._execute_remove_member,
            Proposal.Type.CHANGE_MODEL: self._execute_change_model,
            Proposal.Type.CHANGE_PARAMS: self._execute_change_params,
            Proposal.Type.START_TRAINING: self._execute_start_training,
            Proposal.Type.DISTRIBUTE_REWARDS: self._execute_distribute_rewards,
            Proposal.Type.UPDATE_CONFIG: self._execute_update_config,
            Proposal.Type.DISSOLVE: self._execute_dissolve,
            Proposal.Type.CUSTOM: self._execute_custom,
        }
        return handlers.get(proposal_type)

    def _execute_add_member(self, proposal: Proposal) -> ExecutionResult:
        """Execute ADD_MEMBER proposal."""
        from apps.consortiums.models import ConsortiumMember

        data = proposal.data
        company_id = data.get("company_id")
        role = data.get("role", ConsortiumMember.Role.CONTRIBUTOR)

        if not company_id:
            return ExecutionResult(
                success=False,
                message="Missing company_id in proposal data",
            )

        # Check if already a member
        existing = ConsortiumMember.objects.filter(
            consortium=proposal.consortium,
            company_id=company_id,
        ).first()

        if existing:
            if existing.status == ConsortiumMember.Status.ACTIVE:
                return ExecutionResult(
                    success=False,
                    message="Company is already an active member",
                )
            # Reactivate suspended/left member
            existing.status = ConsortiumMember.Status.ACTIVE
            existing.role = role
            existing.save(update_fields=["status", "role", "updated_at"])
            member = existing
        else:
            # Create new membership
            member = ConsortiumMember.objects.create(
                consortium=proposal.consortium,
                company_id=company_id,
                role=role,
                status=ConsortiumMember.Status.ACTIVE,
            )

        return ExecutionResult(
            success=True,
            message=f"Member added with role {role}",
            data={"member_id": str(member.id)},
        )

    def _execute_remove_member(self, proposal: Proposal) -> ExecutionResult:
        """Execute REMOVE_MEMBER proposal."""
        from apps.consortiums.models import ConsortiumMember

        data = proposal.data
        company_id = data.get("company_id")

        if not company_id:
            return ExecutionResult(
                success=False,
                message="Missing company_id in proposal data",
            )

        member = ConsortiumMember.objects.filter(
            consortium=proposal.consortium,
            company_id=company_id,
            status=ConsortiumMember.Status.ACTIVE,
        ).first()

        if not member:
            return ExecutionResult(
                success=False,
                message="Member not found or not active",
            )

        # Cannot remove the owner
        if member.role == ConsortiumMember.Role.OWNER:
            return ExecutionResult(
                success=False,
                message="Cannot remove the consortium owner",
            )

        member.status = ConsortiumMember.Status.REMOVED
        member.save(update_fields=["status", "updated_at"])

        return ExecutionResult(
            success=True,
            message="Member removed from consortium",
            data={"member_id": str(member.id)},
        )

    def _execute_change_model(self, proposal: Proposal) -> ExecutionResult:
        """Execute CHANGE_MODEL proposal."""
        from apps.consortiums.models import Consortium

        data = proposal.data
        new_model_type = data.get("model_type")

        if not new_model_type:
            return ExecutionResult(
                success=False,
                message="Missing model_type in proposal data",
            )

        if new_model_type not in [choice[0] for choice in Consortium.ModelType.choices]:
            return ExecutionResult(
                success=False,
                message=f"Invalid model type: {new_model_type}",
            )

        old_model = proposal.consortium.model_type
        proposal.consortium.model_type = new_model_type
        proposal.consortium.save(update_fields=["model_type", "updated_at"])

        return ExecutionResult(
            success=True,
            message=f"Model changed from {old_model} to {new_model_type}",
            data={"old_model": old_model, "new_model": new_model_type},
        )

    def _execute_start_training(self, proposal: Proposal) -> ExecutionResult:
        """Execute START_TRAINING proposal."""
        from apps.consortiums.models import Consortium

        consortium = proposal.consortium

        # Validate consortium can start training
        if consortium.status == Consortium.Status.TRAINING:
            return ExecutionResult(
                success=False,
                message="Training is already in progress",
            )

        if consortium.member_count < consortium.min_members:
            return ExecutionResult(
                success=False,
                message=f"Need at least {consortium.min_members} members to start training",
            )

        # Update consortium status
        consortium.status = Consortium.Status.TRAINING
        consortium.save(update_fields=["status", "updated_at"])

        # In production, this would trigger actual FHE training
        # For now, we just update the status
        return ExecutionResult(
            success=True,
            message="Training initiated",
            data={
                "model_type": consortium.model_type,
                "member_count": consortium.member_count,
                "total_records": consortium.total_records,
            },
        )

    def _execute_distribute_rewards(self, proposal: Proposal) -> ExecutionResult:
        """Execute DISTRIBUTE_REWARDS proposal."""
        from decimal import Decimal

        from apps.consortiums.models import ContributionProof
        from django.db.models import Sum

        from .models import RewardDistribution

        data = proposal.data
        total_amount = Decimal(str(data.get("amount", 0)))
        currency = data.get("currency", "ETH")

        if total_amount <= 0:
            return ExecutionResult(
                success=False,
                message="Invalid reward amount",
            )

        # Calculate contributions
        contributions = (
            ContributionProof.objects.filter(
                consortium=proposal.consortium,
                verified=True,
            )
            .values("company_id")
            .annotate(total_records=Sum("record_count"))
        )

        total_records = sum(c["total_records"] for c in contributions)

        if total_records == 0:
            return ExecutionResult(
                success=False,
                message="No verified contributions to distribute rewards",
            )

        # Calculate distribution
        distributions = []
        for contrib in contributions:
            weight = contrib["total_records"] / total_records
            share = float(total_amount) * weight
            distributions.append({
                "company_id": str(contrib["company_id"]),
                "amount": round(share, 8),
                "weight": round(weight * 100, 2),
            })

        # Create distribution record
        distribution = RewardDistribution.objects.create(
            consortium=proposal.consortium,
            total_amount=total_amount,
            currency=currency,
            distributions=distributions,
        )

        return ExecutionResult(
            success=True,
            message=f"Distributed {total_amount} {currency} to {len(distributions)} members",
            data={
                "distribution_id": str(distribution.id),
                "recipient_count": len(distributions),
            },
        )

    def _execute_update_config(self, proposal: Proposal) -> ExecutionResult:
        """Execute UPDATE_CONFIG proposal."""
        data = proposal.data
        config_updates = data.get("config", {})

        if not config_updates:
            return ExecutionResult(
                success=False,
                message="No configuration updates provided",
            )

        consortium = proposal.consortium
        old_config = consortium.ml_config.copy() if consortium.ml_config else {}

        # Allowed configuration fields
        allowed_fields = {
            "voting_threshold",
            "voting_duration_days",
            "min_members",
        }

        # Apply updates to allowed consortium fields
        updates_applied = {}
        for key, value in config_updates.items():
            if key in allowed_fields:
                setattr(consortium, key, value)
                updates_applied[key] = value
            elif key.startswith("ml_"):
                # ML-specific config goes to ml_config
                consortium.ml_config[key] = value
                updates_applied[key] = value

        if not updates_applied:
            return ExecutionResult(
                success=False,
                message="No valid configuration fields to update",
            )

        consortium.save()

        return ExecutionResult(
            success=True,
            message=f"Updated {len(updates_applied)} configuration fields",
            data={"updates": updates_applied, "previous_config": old_config},
        )

    def _execute_change_params(self, proposal: Proposal) -> ExecutionResult:
        """Execute CHANGE_PARAMS proposal."""
        data = proposal.data
        params = data.get("params", {})

        if not params:
            return ExecutionResult(
                success=False,
                message="No parameters provided",
            )

        consortium = proposal.consortium
        old_config = consortium.ml_config.copy() if consortium.ml_config else {}

        for key, value in params.items():
            consortium.ml_config[key] = value

        consortium.save(update_fields=["ml_config", "updated_at"])

        return ExecutionResult(
            success=True,
            message=f"Updated {len(params)} model parameters",
            data={"updates": params, "previous_config": old_config},
        )

    def _execute_custom(self, proposal: Proposal) -> ExecutionResult:
        """Execute CUSTOM proposal."""
        return ExecutionResult(
            success=True,
            message="Custom proposal executed",
            data={"proposal_id": str(proposal.id)},
        )

    def _execute_dissolve(self, proposal: Proposal) -> ExecutionResult:
        """Execute DISSOLVE proposal."""
        from apps.consortiums.models import Consortium, ConsortiumMember

        consortium = proposal.consortium

        # Mark all members as left
        ConsortiumMember.objects.filter(
            consortium=consortium,
            status=ConsortiumMember.Status.ACTIVE,
        ).update(status=ConsortiumMember.Status.LEFT)

        # Archive the consortium
        consortium.status = Consortium.Status.ARCHIVED
        consortium.save(update_fields=["status", "updated_at"])

        return ExecutionResult(
            success=True,
            message="Consortium dissolved and archived",
            data={"consortium_id": str(consortium.id)},
        )

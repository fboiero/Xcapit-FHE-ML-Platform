"""
Invitation service for Xcapit FHE-ML Platform.

Encapsulates business logic for consortium invitation operations.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from django.db import transaction
from django.utils import timezone

from apps.core.services.base import BaseService, ServiceResult

if TYPE_CHECKING:
    from apps.consortiums.models import Consortium, ConsortiumInvitation
    from apps.core.models import Company

logger = logging.getLogger(__name__)


class InvitationService(BaseService):
    """
    Service for consortium invitation business logic.

    Handles:
    - Invitation creation
    - Invitation acceptance/decline
    - Invitation expiration checks
    """

    @transaction.atomic
    def create_invitation(
        self,
        consortium: Consortium,
        inviter: Company,
        invitee_email: str,
        role: str = "contributor",
        message: str = "",
    ) -> ServiceResult[ConsortiumInvitation]:
        """
        Create a new invitation to join a consortium.

        Args:
            consortium: Target consortium
            inviter: Company sending the invitation
            invitee_email: Email of company to invite
            role: Role to assign on join
            message: Optional invitation message

        Returns:
            ServiceResult with created invitation
        """
        from apps.consortiums.models import (
            ConsortiumInvitation,
            ConsortiumMember,
        )
        from apps.core.services import AuditService

        # Check if inviter is a member with invite permissions
        inviter_membership = ConsortiumMember.objects.filter(
            consortium=consortium,
            company=inviter,
            status=ConsortiumMember.Status.ACTIVE,
            role__in=[ConsortiumMember.Role.OWNER, ConsortiumMember.Role.ADMIN],
        ).first()

        if not inviter_membership:
            return ServiceResult.fail(
                "You must be an admin or owner to send invitations",
                error_code="permission_denied",
            )

        # Check for existing pending invitation
        existing = ConsortiumInvitation.objects.filter(
            consortium=consortium,
            invitee_email__iexact=invitee_email,
            status=ConsortiumInvitation.Status.PENDING,
        ).first()

        if existing:
            return ServiceResult.fail(
                "A pending invitation already exists for this email",
                error_code="duplicate_invitation",
            )

        # Check if already a member
        existing_member = ConsortiumMember.objects.filter(
            consortium=consortium,
            company__email__iexact=invitee_email,
            status=ConsortiumMember.Status.ACTIVE,
        ).first()

        if existing_member:
            return ServiceResult.fail(
                "This company is already a member of the consortium",
                error_code="already_member",
            )

        # Create invitation
        invitation = ConsortiumInvitation.objects.create(
            consortium=consortium,
            inviter=inviter,
            invitee_email=invitee_email,
            role=role,
            message=message,
        )

        logger.info(
            f"Created invitation {invitation.id} for {invitee_email} "
            f"to consortium {consortium.id}"
        )

        # Audit log
        if self.request:
            AuditService.log_from_request(
                self.request,
                action="invitation_sent",
                resource_type="consortium_invitation",
                resource_id=invitation.id,
                extra_data={
                    "consortium_id": str(consortium.id),
                    "invitee_email": invitee_email,
                    "role": role,
                },
            )

        return ServiceResult.ok(invitation)

    @transaction.atomic
    def accept_invitation(
        self,
        invitation: ConsortiumInvitation,
        accepting_company: Company,
    ) -> ServiceResult[ConsortiumInvitation]:
        """
        Accept a consortium invitation.

        Args:
            invitation: The invitation to accept
            accepting_company: Company accepting the invitation

        Returns:
            ServiceResult with updated invitation
        """
        from apps.consortiums.models import ConsortiumInvitation, ConsortiumMember
        from apps.core.services import AuditService

        # Validate invitation is for this company
        if invitation.invitee_email.lower() != accepting_company.email.lower():
            return ServiceResult.fail(
                "This invitation is not for your company",
                error_code="permission_denied",
            )

        # Check invitation status
        if invitation.status != ConsortiumInvitation.Status.PENDING:
            return ServiceResult.fail(
                f"Invitation is no longer pending (status: {invitation.status})",
                error_code="invalid_status",
            )

        # Check expiration
        if invitation.is_expired:
            invitation.status = ConsortiumInvitation.Status.EXPIRED
            invitation.save(update_fields=["status"])
            return ServiceResult.fail(
                "Invitation has expired",
                error_code="invitation_expired",
            )

        # Create membership
        member = ConsortiumMember.objects.create(
            consortium=invitation.consortium,
            company=accepting_company,
            role=invitation.role,
            status=ConsortiumMember.Status.ACTIVE,
        )

        # Update invitation
        invitation.status = ConsortiumInvitation.Status.ACCEPTED
        invitation.invitee_company = accepting_company
        invitation.responded_at = timezone.now()
        invitation.save()

        logger.info(
            f"Invitation {invitation.id} accepted by {accepting_company.id}, "
            f"created membership {member.id}"
        )

        # Audit log
        if self.request:
            AuditService.log_from_request(
                self.request,
                action="invitation_accepted",
                resource_type="consortium_invitation",
                resource_id=invitation.id,
                extra_data={
                    "consortium_id": str(invitation.consortium_id),
                    "member_id": str(member.id),
                },
            )

        return ServiceResult.ok(invitation)

    @transaction.atomic
    def decline_invitation(
        self,
        invitation: ConsortiumInvitation,
        declining_company: Company,
        reason: str = "",
    ) -> ServiceResult[ConsortiumInvitation]:
        """
        Decline a consortium invitation.

        Args:
            invitation: The invitation to decline
            declining_company: Company declining the invitation
            reason: Optional reason for declining

        Returns:
            ServiceResult with updated invitation
        """
        from apps.consortiums.models import ConsortiumInvitation
        from apps.core.services import AuditService

        # Validate invitation is for this company
        if invitation.invitee_email.lower() != declining_company.email.lower():
            return ServiceResult.fail(
                "This invitation is not for your company",
                error_code="permission_denied",
            )

        # Check invitation status
        if invitation.status != ConsortiumInvitation.Status.PENDING:
            return ServiceResult.fail(
                f"Invitation is no longer pending (status: {invitation.status})",
                error_code="invalid_status",
            )

        # Update invitation
        invitation.status = ConsortiumInvitation.Status.DECLINED
        invitation.responded_at = timezone.now()
        invitation.save()

        logger.info(f"Invitation {invitation.id} declined by {declining_company.id}")

        # Audit log
        if self.request:
            AuditService.log_from_request(
                self.request,
                action="invitation_declined",
                resource_type="consortium_invitation",
                resource_id=invitation.id,
                extra_data={
                    "consortium_id": str(invitation.consortium_id),
                    "reason": reason,
                },
            )

        return ServiceResult.ok(invitation)

    @transaction.atomic
    def cancel_invitation(
        self,
        invitation: ConsortiumInvitation,
        cancelling_company: Company,
    ) -> ServiceResult[ConsortiumInvitation]:
        """
        Cancel a pending invitation.

        Args:
            invitation: The invitation to cancel
            cancelling_company: Company cancelling (must be inviter)

        Returns:
            ServiceResult with updated invitation
        """
        from apps.consortiums.models import ConsortiumInvitation

        # Validate canceller is the inviter
        if invitation.inviter_id != cancelling_company.id:
            return ServiceResult.fail(
                "Only the inviter can cancel an invitation",
                error_code="permission_denied",
            )

        # Check invitation status
        if invitation.status != ConsortiumInvitation.Status.PENDING:
            return ServiceResult.fail(
                "Only pending invitations can be cancelled",
                error_code="invalid_status",
            )

        # Update invitation
        invitation.status = ConsortiumInvitation.Status.CANCELLED
        invitation.save(update_fields=["status"])

        logger.info(f"Invitation {invitation.id} cancelled")

        return ServiceResult.ok(invitation)

    def get_pending_invitations(
        self,
        company: Company,
    ) -> list[ConsortiumInvitation]:
        """
        Get all pending invitations for a company.

        Args:
            company: The company to get invitations for

        Returns:
            List of pending invitations
        """
        from apps.consortiums.models import ConsortiumInvitation

        return list(
            ConsortiumInvitation.objects.filter(
                invitee_email__iexact=company.email,
                status=ConsortiumInvitation.Status.PENDING,
            ).select_related("consortium", "inviter")
        )

    def get_sent_invitations(
        self,
        company: Company,
        consortium: Consortium | None = None,
    ) -> list[ConsortiumInvitation]:
        """
        Get invitations sent by a company.

        Args:
            company: The sending company
            consortium: Optional filter by consortium

        Returns:
            List of sent invitations
        """
        from apps.consortiums.models import ConsortiumInvitation

        queryset = ConsortiumInvitation.objects.filter(inviter=company)

        if consortium:
            queryset = queryset.filter(consortium=consortium)

        return list(queryset.select_related("consortium").order_by("-created_at"))

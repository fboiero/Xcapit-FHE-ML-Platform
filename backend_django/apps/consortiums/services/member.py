"""
Member service for Xcapit FHE-ML Platform.

Encapsulates business logic for consortium member operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from apps.core.services.base import BaseService, ServiceResult
from django.db import transaction

if TYPE_CHECKING:
    from apps.consortiums.models import ConsortiumMember


class MemberService(BaseService):
    """
    Service for consortium member business logic.

    Handles:
    - Member approval/rejection
    - Role management
    - Member removal
    """

    @transaction.atomic
    def approve_member(
        self,
        member: ConsortiumMember,
    ) -> ServiceResult[ConsortiumMember]:
        """
        Approve a pending consortium member.

        Args:
            member: The member to approve

        Returns:
            ServiceResult with updated member
        """
        from apps.consortiums.models import ConsortiumMember
        from apps.core.services import AuditService

        if member.status != ConsortiumMember.Status.PENDING:
            return ServiceResult.fail(
                "Only pending members can be approved",
                error_code="invalid_status",
                details={"current_status": member.status},
            )

        member.status = ConsortiumMember.Status.ACTIVE
        member.save(update_fields=["status", "updated_at"])

        # Audit log
        if self.request:
            AuditService.log_from_request(
                self.request,
                action="member_approved",
                resource_type="consortium_member",
                resource_id=member.id,
                extra_data={
                    "consortium_id": str(member.consortium_id),
                    "company_id": str(member.company_id),
                },
            )

        return ServiceResult.ok(member)

    @transaction.atomic
    def reject_member(
        self,
        member: ConsortiumMember,
        reason: str | None = None,
    ) -> ServiceResult[ConsortiumMember]:
        """
        Reject a pending consortium member.

        Args:
            member: The member to reject
            reason: Optional rejection reason

        Returns:
            ServiceResult with updated member
        """
        from apps.consortiums.models import ConsortiumMember
        from apps.core.services import AuditService

        if member.status != ConsortiumMember.Status.PENDING:
            return ServiceResult.fail(
                "Only pending members can be rejected",
                error_code="invalid_status",
                details={"current_status": member.status},
            )

        member.status = ConsortiumMember.Status.REJECTED
        member.save(update_fields=["status", "updated_at"])

        # Audit log
        if self.request:
            AuditService.log_from_request(
                self.request,
                action="member_rejected",
                resource_type="consortium_member",
                resource_id=member.id,
                extra_data={
                    "consortium_id": str(member.consortium_id),
                    "company_id": str(member.company_id),
                    "reason": reason,
                },
            )

        return ServiceResult.ok(member)

    @transaction.atomic
    def remove_member(
        self,
        member: ConsortiumMember,
        reason: str | None = None,
    ) -> ServiceResult[bool]:
        """
        Remove an active member from consortium.

        Args:
            member: The member to remove
            reason: Optional removal reason

        Returns:
            ServiceResult indicating success
        """
        from apps.consortiums.models import ConsortiumMember
        from apps.core.services import AuditService

        if member.status not in [ConsortiumMember.Status.ACTIVE, ConsortiumMember.Status.SUSPENDED]:
            return ServiceResult.fail(
                "Member is not active or suspended",
                error_code="invalid_status",
            )

        # Check if this is the last admin/owner
        if member.role in [ConsortiumMember.Role.OWNER, ConsortiumMember.Role.ADMIN]:
            remaining_admins = ConsortiumMember.objects.filter(
                consortium=member.consortium,
                status=ConsortiumMember.Status.ACTIVE,
                role__in=[ConsortiumMember.Role.OWNER, ConsortiumMember.Role.ADMIN],
            ).exclude(id=member.id).count()

            if remaining_admins == 0:
                return ServiceResult.fail(
                    "Cannot remove the last admin/owner",
                    error_code="last_admin",
                )

        member.status = ConsortiumMember.Status.LEFT
        member.save(update_fields=["status", "updated_at"])

        # Audit log
        if self.request:
            AuditService.log_from_request(
                self.request,
                action="member_removed",
                resource_type="consortium_member",
                resource_id=member.id,
                extra_data={
                    "consortium_id": str(member.consortium_id),
                    "company_id": str(member.company_id),
                    "reason": reason,
                },
            )

        return ServiceResult.ok(True)

    @transaction.atomic
    def change_role(
        self,
        member: ConsortiumMember,
        new_role: str,
    ) -> ServiceResult[ConsortiumMember]:
        """
        Change a member's role in the consortium.

        Args:
            member: The member to update
            new_role: The new role to assign

        Returns:
            ServiceResult with updated member
        """
        from apps.consortiums.models import ConsortiumMember
        from apps.core.services import AuditService

        if member.status != ConsortiumMember.Status.ACTIVE:
            return ServiceResult.fail(
                "Only active members can have their role changed",
                error_code="invalid_status",
            )

        # Validate new role
        valid_roles = [choice.value for choice in ConsortiumMember.Role]
        if new_role not in valid_roles:
            return ServiceResult.fail(
                f"Invalid role: {new_role}",
                error_code="invalid_role",
                details={"valid_roles": valid_roles},
            )

        # Cannot demote the last owner
        if member.role == ConsortiumMember.Role.OWNER and new_role != ConsortiumMember.Role.OWNER:
            other_owners = ConsortiumMember.objects.filter(
                consortium=member.consortium,
                status=ConsortiumMember.Status.ACTIVE,
                role=ConsortiumMember.Role.OWNER,
            ).exclude(id=member.id).count()

            if other_owners == 0:
                return ServiceResult.fail(
                    "Cannot demote the last owner",
                    error_code="last_owner",
                )

        old_role = member.role
        member.role = new_role
        member.save(update_fields=["role", "updated_at"])

        # Audit log
        if self.request:
            AuditService.log_from_request(
                self.request,
                action="member_role_changed",
                resource_type="consortium_member",
                resource_id=member.id,
                extra_data={
                    "old_role": old_role,
                    "new_role": new_role,
                },
            )

        return ServiceResult.ok(member)

"""
Django signals for Xcapit FHE-ML Platform consortiums.

Handles automatic:
- Consortium activation when min_members is reached
- Contribution verification on creation
- Email notifications for key events
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Consortium, ConsortiumInvitation, ConsortiumMember, ContributionProof

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ConsortiumMember)
def auto_activate_consortium(sender, instance: ConsortiumMember, created: bool, **kwargs):
    """
    Automatically activate a consortium when minimum members is reached.

    Triggered when:
    - A new membership is created with ACTIVE status
    - An existing membership is updated to ACTIVE status
    """
    # Only process active memberships
    if instance.status != ConsortiumMember.Status.ACTIVE:
        return

    consortium = instance.consortium

    # Only process draft consortiums
    if consortium.status != Consortium.Status.DRAFT:
        return

    # Count active members
    active_members = ConsortiumMember.objects.filter(
        consortium=consortium,
        status=ConsortiumMember.Status.ACTIVE,
    ).count()

    # Check if minimum is reached
    if active_members >= consortium.min_members:
        consortium.status = Consortium.Status.ACTIVE
        consortium.save(update_fields=["status", "updated_at"])

        logger.info(
            "Consortium %s auto-activated with %d members (min: %d)",
            consortium.name,
            active_members,
            consortium.min_members,
            extra={
                "consortium_id": str(consortium.id),
                "active_members": active_members,
                "min_members": consortium.min_members,
            },
        )

        # Send notification email
        _send_consortium_activated_email(consortium)


@receiver(post_save, sender=ContributionProof)
def auto_verify_contribution(sender, instance: ContributionProof, created: bool, **kwargs):
    """
    Automatically verify contribution proofs on creation.

    Only processes newly created contributions that are still pending.
    """
    if not created:
        return

    # Only verify pending contributions
    if instance.verification_status != ContributionProof.VerificationStatus.PENDING:
        return

    # Avoid re-processing if already verified
    if instance.verified:
        return

    from .services.verification import ContributionVerificationService

    service = ContributionVerificationService()
    result = service.verify_contribution(instance)

    if result.success and result.data:
        logger.info(
            "Contribution %s auto-verified: %s",
            instance.id,
            result.data.message,
            extra={
                "contribution_id": str(instance.id),
                "valid": result.data.valid,
                "checks": result.data.checks,
            },
        )

        # Queue blockchain registration for verified contributions
        if result.data.valid:
            _queue_blockchain_registration(instance)


@receiver(post_save, sender=ConsortiumInvitation)
def handle_invitation_events(sender, instance: ConsortiumInvitation, created: bool, **kwargs):
    """
    Handle invitation-related events for notifications.

    Sends emails for:
    - New invitations
    - Accepted invitations
    """
    if created:
        # New invitation created
        _send_invitation_email(instance)
    elif instance.status == ConsortiumInvitation.Status.ACCEPTED:
        # Invitation was accepted
        _send_invitation_accepted_email(instance)


def _send_invitation_email(invitation: ConsortiumInvitation):
    """Send invitation notification email."""
    try:
        from .emails import ConsortiumEmailService

        email_service = ConsortiumEmailService()
        email_service.send_invitation(invitation)
    except ImportError:
        logger.debug("Email service not available, skipping invitation email")
    except Exception as e:
        logger.error(
            "Failed to send invitation email: %s",
            str(e),
            extra={"invitation_id": str(invitation.id)},
        )


def _send_invitation_accepted_email(invitation: ConsortiumInvitation):
    """Send notification when invitation is accepted."""
    try:
        from .emails import ConsortiumEmailService

        email_service = ConsortiumEmailService()
        email_service.send_invitation_accepted(invitation)
    except ImportError:
        logger.debug("Email service not available, skipping acceptance email")
    except Exception as e:
        logger.error(
            "Failed to send invitation accepted email: %s",
            str(e),
            extra={"invitation_id": str(invitation.id)},
        )


def _send_consortium_activated_email(consortium: Consortium):
    """Send notification when consortium is activated."""
    try:
        from .emails import ConsortiumEmailService

        email_service = ConsortiumEmailService()
        email_service.send_consortium_activated(consortium)
    except ImportError:
        logger.debug("Email service not available, skipping activation email")
    except Exception as e:
        logger.error(
            "Failed to send consortium activated email: %s",
            str(e),
            extra={"consortium_id": str(consortium.id)},
        )


def _queue_blockchain_registration(contribution: ContributionProof):
    """Queue blockchain registration for a verified contribution."""
    try:
        from .tasks import register_contribution_blockchain

        register_contribution_blockchain.delay(str(contribution.id))
        logger.info(
            "Queued blockchain registration for contribution %s",
            contribution.id,
            extra={"contribution_id": str(contribution.id)},
        )
    except ImportError:
        logger.debug("Celery tasks not available, skipping blockchain registration")
    except Exception as e:
        logger.error(
            "Failed to queue blockchain registration: %s",
            str(e),
            extra={"contribution_id": str(contribution.id)},
        )

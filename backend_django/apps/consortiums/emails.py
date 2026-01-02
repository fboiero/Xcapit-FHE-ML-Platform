"""
Email service for consortium notifications.

Handles sending emails for:
- Consortium invitations
- Invitation acceptances
- Training events
- Consortium activation
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

if TYPE_CHECKING:
    from .models import Consortium, ConsortiumInvitation, TrainingResult

logger = logging.getLogger(__name__)


class ConsortiumEmailService:
    """
    Service for sending consortium-related emails.

    Uses Django's email backend which can be configured for:
    - Console (development)
    - SMTP/SendGrid (production)
    """

    def __init__(self):
        self.from_email = settings.DEFAULT_FROM_EMAIL
        self.platform_url = getattr(settings, "PLATFORM_URL", "https://appfhe.xcapit.com")

    def send_invitation(self, invitation: ConsortiumInvitation) -> bool:
        """
        Send invitation email to a potential consortium member.

        Args:
            invitation: The invitation object

        Returns:
            True if email was sent successfully
        """
        context = {
            "consortium_name": invitation.consortium.name,
            "inviter_name": invitation.inviter.name,
            "role": invitation.get_role_display(),
            "message": invitation.message,
            "expires_at": invitation.expires_at,
            "invitation_url": f"{self.platform_url}/invitations/{invitation.id}",
            "platform_url": self.platform_url,
        }

        subject = f"Invitation to join {invitation.consortium.name} consortium"

        return self._send_email(
            subject=subject,
            template_name="emails/invitation.html",
            context=context,
            recipient_email=invitation.invitee_email,
        )

    def send_invitation_accepted(self, invitation: ConsortiumInvitation) -> bool:
        """
        Send notification to inviter when invitation is accepted.

        Args:
            invitation: The accepted invitation

        Returns:
            True if email was sent successfully
        """
        if not invitation.invitee_company:
            return False

        context = {
            "consortium_name": invitation.consortium.name,
            "inviter_name": invitation.inviter.name,
            "invitee_name": invitation.invitee_company.name,
            "role": invitation.get_role_display(),
            "consortium_url": f"{self.platform_url}/consortiums/{invitation.consortium.id}",
            "platform_url": self.platform_url,
        }

        subject = f"{invitation.invitee_company.name} joined {invitation.consortium.name}"

        return self._send_email(
            subject=subject,
            template_name="emails/invitation_accepted.html",
            context=context,
            recipient_email=invitation.inviter.email,
        )

    def send_consortium_activated(self, consortium: Consortium) -> bool:
        """
        Send notification when consortium is automatically activated.

        Args:
            consortium: The activated consortium

        Returns:
            True if email was sent successfully
        """
        context = {
            "consortium_name": consortium.name,
            "member_count": consortium.member_count,
            "min_members": consortium.min_members,
            "consortium_url": f"{self.platform_url}/consortiums/{consortium.id}",
            "platform_url": self.platform_url,
        }

        subject = f"Consortium {consortium.name} is now active!"

        return self._send_email(
            subject=subject,
            template_name="emails/consortium_activated.html",
            context=context,
            recipient_email=consortium.owner.email,
        )

    def send_training_started(self, training_result: TrainingResult) -> bool:
        """
        Send notification when training starts.

        Args:
            training_result: The training result object

        Returns:
            True if email was sent successfully
        """
        consortium = training_result.consortium

        context = {
            "consortium_name": consortium.name,
            "contributions_count": training_result.contributions_count,
            "total_records": training_result.total_records,
            "training_url": f"{self.platform_url}/consortiums/{consortium.id}/training/{training_result.id}",
            "platform_url": self.platform_url,
        }

        subject = f"Training started for {consortium.name}"

        return self._send_email(
            subject=subject,
            template_name="emails/training_started.html",
            context=context,
            recipient_email=consortium.owner.email,
        )

    def send_training_complete(self, training_result: TrainingResult) -> bool:
        """
        Send notification when training completes.

        Args:
            training_result: The completed training result

        Returns:
            True if email was sent successfully
        """
        consortium = training_result.consortium

        context = {
            "consortium_name": consortium.name,
            "accuracy": training_result.accuracy,
            "epochs_completed": training_result.epochs_completed,
            "model_hash": training_result.model_hash[:16] + "..." if training_result.model_hash else "N/A",
            "training_url": f"{self.platform_url}/consortiums/{consortium.id}/training/{training_result.id}",
            "platform_url": self.platform_url,
        }

        subject = f"Training completed for {consortium.name}"

        return self._send_email(
            subject=subject,
            template_name="emails/training_complete.html",
            context=context,
            recipient_email=consortium.owner.email,
        )

    def _send_email(
        self,
        subject: str,
        template_name: str,
        context: dict,
        recipient_email: str,
    ) -> bool:
        """
        Send an email using a template.

        Args:
            subject: Email subject
            template_name: Path to the HTML template
            context: Context for template rendering
            recipient_email: Recipient email address

        Returns:
            True if email was sent successfully
        """
        try:
            # Try to render template, fall back to plain text
            try:
                html_message = render_to_string(template_name, context)
                plain_message = strip_tags(html_message)
            except Exception:
                # Fallback to simple text if template not found
                html_message = None
                plain_message = self._generate_plain_text(subject, context)

            send_mail(
                subject=subject,
                message=plain_message,
                from_email=self.from_email,
                recipient_list=[recipient_email],
                html_message=html_message,
                fail_silently=False,
            )

            logger.info(
                "Email sent successfully: %s to %s",
                subject,
                recipient_email,
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to send email '%s' to %s: %s",
                subject,
                recipient_email,
                str(e),
            )
            return False

    def _generate_plain_text(self, subject: str, context: dict) -> str:
        """Generate plain text fallback when template is not available."""
        lines = [
            f"Subject: {subject}",
            "",
            "Xcapit FHE-ML Platform Notification",
            "=" * 40,
            "",
        ]

        for key, value in context.items():
            if key not in ("platform_url",) and value:
                formatted_key = key.replace("_", " ").title()
                lines.append(f"{formatted_key}: {value}")

        lines.extend([
            "",
            "---",
            f"Visit {context.get('platform_url', self.platform_url)} for more details.",
        ])

        return "\n".join(lines)

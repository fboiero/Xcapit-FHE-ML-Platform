"""
Governance models for Xcapit FHE-ML Platform.

Propuestas, votaciones, auditoría y distribución de recompensas
para la gobernanza descentralizada de consorcios.
"""

import uuid

from django.db import models
from django.utils import timezone


class Proposal(models.Model):
    """Propuesta de gobernanza dentro de un consorcio."""

    class Type(models.TextChoices):
        ADD_MEMBER = "add_member", "Add Member"
        REMOVE_MEMBER = "remove_member", "Remove Member"
        CHANGE_MODEL = "change_model", "Change Model"
        CHANGE_PARAMS = "change_params", "Change Parameters"
        START_TRAINING = "start_training", "Start Training"
        DISTRIBUTE_REWARDS = "distribute_rewards", "Distribute Rewards"
        UPDATE_CONFIG = "update_config", "Update Config"
        DISSOLVE = "dissolve", "Dissolve"
        CUSTOM = "custom", "Custom"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        PASSED = "passed", "Passed"
        REJECTED = "rejected", "Rejected"
        EXECUTED = "executed", "Executed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    consortium = models.ForeignKey(
        "consortiums.Consortium",
        on_delete=models.CASCADE,
        related_name="proposals",
    )
    proposer = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="proposals",
    )

    proposal_type = models.CharField(max_length=30, choices=Type.choices)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    data = models.JSONField(default=dict, blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )

    yes_votes = models.IntegerField(default=0)
    no_votes = models.IntegerField(default=0)
    voting_weight_yes = models.DecimalField(
        max_digits=10, decimal_places=4, default=0
    )
    voting_weight_no = models.DecimalField(
        max_digits=10, decimal_places=4, default=0
    )

    blockchain_tx = models.CharField(max_length=66, blank=True)

    expires_at = models.DateTimeField(null=True, blank=True)
    executed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "proposal"
        verbose_name_plural = "proposals"
        indexes = [
            models.Index(fields=["consortium", "status"]),
            models.Index(fields=["proposer"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.status})"

    @property
    def total_voters(self) -> int:
        """Número total de votantes."""
        return self.votes.count()

    @property
    def is_expired(self) -> bool:
        """Indica si la propuesta ha expirado."""
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at and self.status == self.Status.ACTIVE

    def check_result(self, threshold: float = 0.5) -> bool | None:
        """Check if proposal passes based on weighted votes.

        Returns:
            True if passed, False if failed, None if no votes cast.
        """
        total_weight = float(self.voting_weight_yes) + float(self.voting_weight_no)
        if total_weight == 0:
            return None
        return (float(self.voting_weight_yes) / total_weight) >= threshold


class Vote(models.Model):
    """Voto individual sobre una propuesta."""

    class Support(models.TextChoices):
        FOR = "for", "For"
        AGAINST = "against", "Against"
        ABSTAIN = "abstain", "Abstain"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        related_name="votes",
    )
    voter = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="votes",
    )

    support = models.CharField(max_length=10, choices=Support.choices)
    weight = models.DecimalField(max_digits=10, decimal_places=4, default=1)
    comment = models.TextField(blank=True)

    voted_at = models.DateTimeField(auto_now_add=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "vote"
        verbose_name_plural = "votes"
        unique_together = ["proposal", "voter"]
        indexes = [
            models.Index(fields=["proposal", "support"]),
        ]

    def __str__(self) -> str:
        return f"{self.voter} — {self.support} on {self.proposal.title}"


class AuditEvent(models.Model):
    """Evento de auditoría para trazabilidad de gobernanza."""

    class EventType(models.TextChoices):
        PROPOSAL_CREATED = "proposal_created", "Proposal Created"
        PROPOSAL_EXECUTED = "proposal_executed", "Proposal Executed"
        PROPOSAL_CANCELLED = "proposal_cancelled", "Proposal Cancelled"
        VOTE_CAST = "vote_cast", "Vote Cast"
        MEMBER_ADDED = "member_added", "Member Added"
        MEMBER_JOINED = "member_joined", "Member Joined"
        MEMBER_REMOVED = "member_removed", "Member Removed"
        REWARD_DISTRIBUTED = "reward_distributed", "Reward Distributed"
        CONFIG_CHANGED = "config_changed", "Config Changed"
        CONSORTIUM_CREATED = "consortium_created", "Consortium Created"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    consortium = models.ForeignKey(
        "consortiums.Consortium",
        on_delete=models.CASCADE,
        related_name="audit_events",
    )
    actor = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="audit_events",
    )

    event_type = models.CharField(max_length=30, choices=EventType.choices, db_index=True)
    target_id = models.CharField(max_length=255, blank=True)
    target_type = models.CharField(max_length=100, blank=True)
    data = models.JSONField(default=dict, blank=True)

    previous_hash = models.CharField(max_length=66, blank=True)
    event_hash = models.CharField(max_length=66, blank=True)
    blockchain_tx = models.CharField(max_length=66, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "audit event"
        verbose_name_plural = "audit events"
        indexes = [
            models.Index(fields=["consortium", "event_type"]),
            models.Index(fields=["actor"]),
        ]

    def __str__(self) -> str:
        return f"{self.event_type} by {self.actor} @ {self.created_at:%Y-%m-%d %H:%M}"

    @classmethod
    def get_previous_hash(cls, consortium_id) -> str:
        """Return the event_hash of the most recent audit event for a consortium.

        Returns an empty string when there are no prior events (genesis).
        """
        last = (
            cls.objects.filter(consortium_id=consortium_id)
            .order_by("-created_at")
            .values_list("event_hash", flat=True)
            .first()
        )
        return last or ""


class RewardDistribution(models.Model):
    """Registro de distribución de recompensas dentro de un consorcio."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    consortium = models.ForeignKey(
        "consortiums.Consortium",
        on_delete=models.CASCADE,
        related_name="reward_distributions",
    )

    total_amount = models.DecimalField(max_digits=20, decimal_places=8)
    currency = models.CharField(max_length=10, default="ETH")
    distributions = models.JSONField(default=list)
    blockchain_tx = models.CharField(max_length=66, blank=True)

    distributed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "reward distribution"
        verbose_name_plural = "reward distributions"
        indexes = [
            models.Index(fields=["consortium"]),
        ]

    def __str__(self) -> str:
        return f"{self.total_amount} {self.currency} — {self.consortium.name}"

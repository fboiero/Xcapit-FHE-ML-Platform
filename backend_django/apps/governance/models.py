"""
Governance models for Xcapit FHE-ML Platform.

Implements on-chain governance with proposals, voting,
and reward distribution for consortium participants.
"""

import hashlib
import uuid

from django.db import models
from django.utils import timezone


class Proposal(models.Model):
    """
    Governance proposal for consortium decisions.

    Proposals require voting from consortium members.
    """

    class Type(models.TextChoices):
        ADD_MEMBER = "add_member", "Add Member"
        REMOVE_MEMBER = "remove_member", "Remove Member"
        CHANGE_MODEL = "change_model", "Change Model"
        START_TRAINING = "start_training", "Start Training"
        DISTRIBUTE_REWARDS = "distribute_rewards", "Distribute Rewards"
        UPDATE_CONFIG = "update_config", "Update Configuration"
        DISSOLVE = "dissolve", "Dissolve Consortium"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PASSED = "passed", "Passed"
        REJECTED = "rejected", "Rejected"
        EXECUTED = "executed", "Executed"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"

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

    # Proposal details
    proposal_type = models.CharField(max_length=30, choices=Type.choices)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Type-specific data (validated by serializer, stored as JSON)
    data = models.JSONField(default=dict, blank=True)

    # Voting
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    yes_votes = models.IntegerField(default=0)
    no_votes = models.IntegerField(default=0)
    voting_weight_yes = models.FloatField(default=0)
    voting_weight_no = models.FloatField(default=0)

    # Blockchain
    blockchain_tx = models.CharField(max_length=66, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    executed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "proposal"
        verbose_name_plural = "proposals"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["consortium", "status"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.status})"

    @property
    def total_voters(self):
        return self.votes.count()

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at and self.status == self.Status.ACTIVE

    def check_result(self, threshold=0.5):
        """Check if proposal passed based on voting weight."""
        total_weight = self.voting_weight_yes + self.voting_weight_no
        if total_weight == 0:
            return None
        return (self.voting_weight_yes / total_weight) >= threshold


class Vote(models.Model):
    """
    Vote on a governance proposal.
    """

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

    support = models.BooleanField()  # True = yes, False = no
    weight = models.IntegerField(default=1)  # Based on contribution
    comment = models.TextField(blank=True, max_length=500)

    # Timestamps
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "vote"
        verbose_name_plural = "votes"
        unique_together = ["proposal", "voter"]
        indexes = [
            models.Index(fields=["proposal"]),
            models.Index(fields=["voter"]),
        ]

    def __str__(self):
        vote_type = "Yes" if self.support else "No"
        return f"{self.voter.name}: {vote_type} on {self.proposal.title}"


class AuditEvent(models.Model):
    """
    Immutable audit trail for consortium operations.

    Forms a hash chain for integrity verification.
    """

    class EventType(models.TextChoices):
        CONSORTIUM_CREATED = "consortium_created", "Consortium Created"
        MEMBER_JOINED = "member_joined", "Member Joined"
        MEMBER_LEFT = "member_left", "Member Left"
        MEMBER_REMOVED = "member_removed", "Member Removed"
        DATA_CONTRIBUTED = "data_contributed", "Data Contributed"
        TRAINING_STARTED = "training_started", "Training Started"
        TRAINING_COMPLETED = "training_completed", "Training Completed"
        PROPOSAL_CREATED = "proposal_created", "Proposal Created"
        PROPOSAL_VOTED = "proposal_voted", "Proposal Voted"
        PROPOSAL_EXECUTED = "proposal_executed", "Proposal Executed"
        REWARDS_DISTRIBUTED = "rewards_distributed", "Rewards Distributed"
        CONFIG_UPDATED = "config_updated", "Config Updated"
        MODEL_DEPLOYED = "model_deployed", "Model Deployed"
        COMPLIANCE_CHECK = "compliance_check", "Compliance Check"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    consortium = models.ForeignKey(
        "consortiums.Consortium",
        on_delete=models.CASCADE,
        related_name="audit_events",
    )
    actor = models.ForeignKey(
        "core.Company",
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_actions",
    )

    # Event details
    event_type = models.CharField(max_length=50, choices=EventType.choices, db_index=True)
    target_id = models.CharField(max_length=255, blank=True)
    target_type = models.CharField(max_length=50, blank=True)
    data = models.JSONField(default=dict, blank=True)

    # Hash chain for integrity
    previous_hash = models.CharField(max_length=64, blank=True)
    event_hash = models.CharField(max_length=64, blank=True, db_index=True)

    # Blockchain
    blockchain_tx = models.CharField(max_length=66, blank=True)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "audit event"
        verbose_name_plural = "audit events"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["consortium", "event_type"]),
            models.Index(fields=["consortium", "created_at"]),
            models.Index(fields=["event_hash"]),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.created_at}"

    def save(self, *args, **kwargs):
        """Generate event hash on save."""
        if not self.event_hash:
            self.event_hash = self._compute_hash()
        super().save(*args, **kwargs)

    def _compute_hash(self):
        """Compute SHA-256 hash of event data."""
        data_str = f"{self.consortium_id}:{self.event_type}:{self.actor_id}:{self.target_id}:{self.previous_hash}:{self.created_at}"
        return hashlib.sha256(data_str.encode()).hexdigest()

    @classmethod
    def get_previous_hash(cls, consortium_id):
        """Get hash of most recent event for chain continuity."""
        last_event = cls.objects.filter(
            consortium_id=consortium_id
        ).order_by("-created_at").first()
        return last_event.event_hash if last_event else ""


class RewardDistribution(models.Model):
    """
    Record of reward distribution to consortium members.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    consortium = models.ForeignKey(
        "consortiums.Consortium",
        on_delete=models.CASCADE,
        related_name="reward_distributions",
    )

    # Distribution details
    total_amount = models.DecimalField(max_digits=20, decimal_places=8)
    currency = models.CharField(max_length=10, default="ETH")

    # Individual distributions (member_id -> amount)
    distributions = models.JSONField(default=list)

    # Blockchain
    blockchain_tx = models.CharField(max_length=66, blank=True)

    # Timestamps
    distributed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "reward distribution"
        verbose_name_plural = "reward distributions"
        ordering = ["-distributed_at"]
        indexes = [
            models.Index(fields=["consortium"]),
            models.Index(fields=["distributed_at"]),
        ]

    def __str__(self):
        return f"{self.total_amount} {self.currency} to {self.consortium.name}"

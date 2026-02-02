"""
Consortium models for Xcapit FHE-ML Platform.

Consortiums enable multi-party collaborative ML training
while preserving data privacy through FHE.
"""

import uuid

from django.db import models
from django.utils import timezone


class Consortium(models.Model):
    """
    A consortium is a group of companies collaborating on ML training.

    Members contribute encrypted data and receive access to the
    trained model without exposing their raw data.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        TRAINING = "training", "Training"
        COMPLETED = "completed", "Completed"
        ARCHIVED = "archived", "Archived"

    class ModelType(models.TextChoices):
        LINEAR_REGRESSION = "linear_regression", "Linear Regression"
        LOGISTIC_REGRESSION = "logistic_regression", "Logistic Regression"
        DECISION_TREE = "decision_tree", "Decision Tree"
        KMEANS = "kmeans", "K-Means Clustering"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Ownership
    owner = models.ForeignKey(
        "core.Company",
        on_delete=models.PROTECT,
        related_name="owned_consortiums",
    )

    # Configuration
    model_type = models.CharField(
        max_length=50,
        choices=ModelType.choices,
        default=ModelType.LOGISTIC_REGRESSION,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )

    # ML Configuration (stored as JSON, no pickle!)
    ml_config = models.JSONField(default=dict, blank=True)

    # Governance settings
    min_members = models.IntegerField(default=2)
    voting_threshold = models.FloatField(default=0.5)  # 50% for proposals
    voting_duration_days = models.IntegerField(default=7)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "consortium"
        verbose_name_plural = "consortiums"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["owner"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.status})"

    @property
    def member_count(self):
        """Get active member count."""
        return self.members.filter(status=ConsortiumMember.Status.ACTIVE).count()

    @property
    def total_records(self):
        """Get total contributed records."""
        return sum(
            cp.record_count
            for cp in self.contribution_proofs.filter(verified=True)
        )


class ConsortiumMember(models.Model):
    """
    Membership record for a company in a consortium.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        REJECTED = "rejected", "Rejected"
        LEFT = "left", "Left"
        REMOVED = "removed", "Removed"

    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"
        CONTRIBUTOR = "contributor", "Contributor"
        OBSERVER = "observer", "Observer"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    consortium = models.ForeignKey(
        Consortium,
        on_delete=models.CASCADE,
        related_name="members",
    )
    company = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="consortium_memberships",
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CONTRIBUTOR,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    # Timestamps
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "consortium member"
        verbose_name_plural = "consortium members"
        ordering = ["-joined_at"]
        unique_together = ["consortium", "company"]
        indexes = [
            models.Index(fields=["consortium", "status"]),
            models.Index(fields=["company"]),
        ]

    def __str__(self):
        return f"{self.company.name} in {self.consortium.name} ({self.role})"


class ContributionProof(models.Model):
    """
    Proof of data contribution to a consortium.

    Records are hashed - actual data is never stored on server.
    """

    class VerificationStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        VERIFIED = "verified", "Verified"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    consortium = models.ForeignKey(
        Consortium,
        on_delete=models.CASCADE,
        related_name="contribution_proofs",
    )
    company = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="contributions",
    )

    # Contribution metadata
    record_count = models.IntegerField()
    feature_count = models.IntegerField()
    schema_version = models.CharField(max_length=20, default="1.0")

    # Cryptographic proofs (hashes only, never raw data)
    data_hash = models.CharField(max_length=64, db_index=True)
    checksum = models.CharField(max_length=64)

    # Verification (legacy field kept for backwards compatibility)
    verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)

    # New verification fields
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
        db_index=True,
    )
    verification_message = models.TextField(blank=True)

    # Blockchain record
    blockchain_tx = models.CharField(max_length=66, blank=True)  # 0x + 64 hex chars
    blockchain_registered_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "contribution proof"
        verbose_name_plural = "contribution proofs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["consortium", "company"]),
            models.Index(fields=["data_hash"]),
            models.Index(fields=["verified"]),
        ]

    def __str__(self):
        return f"{self.company.name}: {self.record_count} records"

    def verify(self, message: str = "Verification successful"):
        """Mark contribution as verified."""
        self.verified = True
        self.verified_at = timezone.now()
        self.verification_status = self.VerificationStatus.VERIFIED
        self.verification_message = message
        self.save(update_fields=[
            "verified", "verified_at", "verification_status", "verification_message"
        ])

    def fail_verification(self, message: str):
        """Mark contribution verification as failed."""
        self.verification_status = self.VerificationStatus.FAILED
        self.verification_message = message
        self.save(update_fields=["verification_status", "verification_message"])


class TrainingResult(models.Model):
    """
    Result of a consortium model training run.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    consortium = models.ForeignKey(
        Consortium,
        on_delete=models.CASCADE,
        related_name="training_results",
    )

    # Training metadata
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    task_id = models.CharField(max_length=255, blank=True, db_index=True)

    # Model information
    model_hash = models.CharField(max_length=64, blank=True)
    accuracy = models.FloatField(null=True, blank=True)
    loss = models.FloatField(null=True, blank=True)
    epochs_completed = models.IntegerField(default=0)

    # Configuration used
    config_snapshot = models.JSONField(default=dict, blank=True)

    # Contributions included
    contributions_count = models.IntegerField(default=0)
    total_records = models.IntegerField(default=0)

    # Error tracking
    error_message = models.TextField(blank=True)

    # Blockchain registration
    blockchain_tx = models.CharField(max_length=66, blank=True)
    blockchain_registered_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "training result"
        verbose_name_plural = "training results"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["consortium", "status"]),
            models.Index(fields=["task_id"]),
        ]

    def __str__(self):
        return f"{self.consortium.name} training ({self.status})"


class ConsortiumInvitation(models.Model):
    """
    Invitation to join a consortium.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        EXPIRED = "expired", "Expired"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    consortium = models.ForeignKey(
        Consortium,
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    inviter = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="sent_invitations",
    )
    invitee_email = models.EmailField()
    invitee_company = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="received_invitations",
        null=True,
        blank=True,
    )

    role = models.CharField(
        max_length=20,
        choices=ConsortiumMember.Role.choices,
        default=ConsortiumMember.Role.CONTRIBUTOR,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    message = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "consortium invitation"
        verbose_name_plural = "consortium invitations"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["invitee_email"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Invitation to {self.invitee_email} for {self.consortium.name}"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at and self.status == self.Status.PENDING

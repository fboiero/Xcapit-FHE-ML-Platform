"""
Sandbox models for Xcapit FHE-ML Platform.

Sandbox environments for testing and experimentation
with synthetic data generation.
"""

import secrets
import uuid
from datetime import timedelta

from django.db import models
from django.utils import timezone


class SandboxLead(models.Model):
    """
    Lead captured from sandbox access request.

    Stores email for marketing follow-up and provides
    a temporary token for sandbox access.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(db_index=True)

    # Access token
    token = models.CharField(max_length=64, unique=True, db_index=True)

    # Tracking
    source = models.CharField(max_length=50, blank=True, default="direct")
    utm_campaign = models.CharField(max_length=100, blank=True)
    utm_source = models.CharField(max_length=100, blank=True)
    utm_medium = models.CharField(max_length=100, blank=True)

    # Conversion tracking
    converted = models.BooleanField(default=False)
    converted_at = models.DateTimeField(null=True, blank=True)
    converted_to_user = models.ForeignKey(
        "core.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sandbox_lead",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    last_access_at = models.DateTimeField(null=True, blank=True)
    access_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = "sandbox lead"
        verbose_name_plural = "sandbox leads"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["token"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["converted"]),
        ]

    def __str__(self):
        return f"{self.email} ({self.created_at.date()})"

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = f"sbx_{secrets.token_urlsafe(32)}"
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return not self.is_expired

    def record_access(self):
        """Record a sandbox access."""
        self.last_access_at = timezone.now()
        self.access_count += 1
        self.save(update_fields=["last_access_at", "access_count"])

    def mark_converted(self, user):
        """Mark lead as converted to a real user."""
        self.converted = True
        self.converted_at = timezone.now()
        self.converted_to_user = user
        self.save(update_fields=["converted", "converted_at", "converted_to_user"])

    @classmethod
    def get_or_create_for_email(cls, email, **kwargs):
        """
        Get existing valid lead or create new one.

        If an unexpired lead exists for this email, return it.
        Otherwise, create a new one.
        """
        # Look for existing unexpired lead
        existing = cls.objects.filter(
            email=email,
            expires_at__gt=timezone.now(),
        ).first()

        if existing:
            return existing, False

        # Create new lead
        lead = cls.objects.create(email=email, **kwargs)
        return lead, True


class SandboxTemplate(models.Model):
    """
    Template for creating sandbox environments.
    """

    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    industry = models.CharField(max_length=50, blank=True)
    template_type = models.CharField(max_length=50, default="generic")

    # Template configuration
    datasets = models.JSONField(default=list)  # Pre-configured datasets
    experiments = models.JSONField(default=list)  # Pre-configured experiments

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "sandbox template"
        verbose_name_plural = "sandbox templates"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Sandbox(models.Model):
    """
    Sandbox environment for testing and experimentation.
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        EXPIRED = "expired", "Expired"
        ARCHIVED = "archived", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # Ownership
    owner = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="sandboxes",
    )

    # Configuration
    template = models.ForeignKey(
        SandboxTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sandboxes",
    )
    industry = models.CharField(max_length=50, blank=True)
    config = models.JSONField(default=dict, blank=True)

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "sandbox"
        verbose_name_plural = "sandboxes"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner"]),
            models.Index(fields=["status"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.owner.name})"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def dataset_count(self):
        return self.datasets.count()

    @property
    def experiment_count(self):
        return self.experiments.count()


class SyntheticDataset(models.Model):
    """
    Synthetically generated dataset for sandbox testing.
    """

    class DatasetType(models.TextChoices):
        TRANSACTIONS = "transactions", "Transactions"
        APPLICATIONS = "applications", "Applications"
        CUSTOMERS = "customers", "Customers"
        PATIENTS = "patients", "Patients"
        GENERIC = "generic", "Generic"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sandbox = models.ForeignKey(
        Sandbox,
        on_delete=models.CASCADE,
        related_name="datasets",
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # Dataset type
    dataset_type = models.CharField(
        max_length=30,
        choices=DatasetType.choices,
        default=DatasetType.GENERIC,
    )
    industry = models.CharField(max_length=50, blank=True)

    # Schema
    record_count = models.IntegerField()
    feature_count = models.IntegerField()
    features = models.JSONField(default=list)  # Feature definitions

    # Statistics
    statistics = models.JSONField(default=dict, blank=True)

    # Data (stored as JSON, not pickle!)
    # Note: For large datasets, consider using file storage
    data_preview = models.JSONField(default=list)  # First 10 rows

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "synthetic dataset"
        verbose_name_plural = "synthetic datasets"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["sandbox"]),
            models.Index(fields=["dataset_type"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.record_count} records)"


class Experiment(models.Model):
    """
    Experiment run in a sandbox environment.
    """

    class ExperimentType(models.TextChoices):
        TRAINING = "training", "Model Training"
        EVALUATION = "evaluation", "Model Evaluation"
        CLUSTERING = "clustering", "Clustering Analysis"
        ENCRYPTION_BENCHMARK = "encryption_benchmark", "Encryption Benchmark"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sandbox = models.ForeignKey(
        Sandbox,
        on_delete=models.CASCADE,
        related_name="experiments",
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # Type
    experiment_type = models.CharField(
        max_length=30,
        choices=ExperimentType.choices,
    )
    model_type = models.CharField(max_length=50, blank=True)

    # Dataset
    dataset = models.ForeignKey(
        SyntheticDataset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="experiments",
    )

    # Configuration
    config = models.JSONField(default=dict, blank=True)

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    # Results
    results = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "experiment"
        verbose_name_plural = "experiments"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["sandbox"]),
            models.Index(fields=["status"]),
            models.Index(fields=["experiment_type"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.status})"

    def start(self):
        """Mark experiment as started."""
        self.status = self.Status.RUNNING
        self.started_at = timezone.now()
        self.save(update_fields=["status", "started_at"])

    def complete(self, results=None):
        """Mark experiment as completed."""
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        if results:
            self.results = results
        self.save()

    def fail(self, error_message):
        """Mark experiment as failed."""
        self.status = self.Status.FAILED
        self.completed_at = timezone.now()
        self.error_message = error_message
        self.save()

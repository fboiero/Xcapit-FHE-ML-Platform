"""
Compliance models for Xcapit FHE-ML Platform.

Supports GDPR, HIPAA, SOC2, and PCI-DSS compliance tracking.
"""

import uuid
from datetime import timedelta

from django.db import models
from django.utils import timezone


class ComplianceFramework(models.Model):
    """
    Compliance framework definition (GDPR, HIPAA, etc.).
    """

    id = models.CharField(max_length=50, primary_key=True)  # e.g., "framework_gdpr"
    name = models.CharField(max_length=100)
    version = models.CharField(max_length=20)
    description = models.TextField(blank=True)

    # Applicability
    region = models.CharField(max_length=50, blank=True)  # e.g., "EU", "US"
    industry = models.CharField(max_length=50, blank=True)  # e.g., "healthcare", "finance"

    # Controls
    controls = models.JSONField(default=list)  # List of control definitions

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "compliance framework"
        verbose_name_plural = "compliance frameworks"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} v{self.version}"

    @property
    def controls_count(self):
        return len(self.controls)


class ConsortiumCompliance(models.Model):
    """
    Compliance settings for a consortium.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    consortium = models.OneToOneField(
        "consortiums.Consortium",
        on_delete=models.CASCADE,
        related_name="compliance_settings",
    )

    # Enabled frameworks
    enabled_frameworks = models.ManyToManyField(
        ComplianceFramework,
        related_name="consortiums",
        blank=True,
    )

    # Settings
    auto_check_interval = models.IntegerField(default=24)  # hours
    notification_emails = models.JSONField(default=list, blank=True)

    # Last check
    last_check_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "consortium compliance"
        verbose_name_plural = "consortium compliance settings"
        ordering = ["-last_check_at"]

    def __str__(self):
        return f"Compliance for {self.consortium.name}"

    @property
    def next_check_at(self):
        if self.last_check_at:
            return self.last_check_at + timedelta(hours=self.auto_check_interval)
        return None


class ComplianceCheck(models.Model):
    """
    Individual compliance check result.
    """

    class Status(models.TextChoices):
        PASSED = "passed", "Passed"
        FAILED = "failed", "Failed"
        PENDING = "pending", "Pending"
        NA = "na", "Not Applicable"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    consortium = models.ForeignKey(
        "consortiums.Consortium",
        on_delete=models.CASCADE,
        related_name="compliance_checks",
    )
    framework = models.ForeignKey(
        ComplianceFramework,
        on_delete=models.CASCADE,
        related_name="checks",
    )

    # Control info
    control_id = models.CharField(max_length=50)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    result = models.TextField()

    # Evidence
    evidence = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)

    # Who performed the check
    checked_by = models.ForeignKey(
        "core.Company",
        on_delete=models.SET_NULL,
        null=True,
        related_name="compliance_checks",
    )

    # Timestamps
    checked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "compliance check"
        verbose_name_plural = "compliance checks"
        ordering = ["-checked_at"]
        indexes = [
            models.Index(fields=["consortium", "framework"]),
            models.Index(fields=["control_id"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.framework.name} - {self.control_id}: {self.status}"


class ComplianceReport(models.Model):
    """
    Generated compliance report.
    """

    class Status(models.TextChoices):
        COMPLIANT = "compliant", "Compliant"
        NON_COMPLIANT = "non_compliant", "Non-Compliant"
        PARTIAL = "partial", "Partially Compliant"
        PENDING = "pending", "Pending"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    consortium = models.ForeignKey(
        "consortiums.Consortium",
        on_delete=models.CASCADE,
        related_name="compliance_reports",
    )
    framework = models.ForeignKey(
        ComplianceFramework,
        on_delete=models.CASCADE,
        related_name="reports",
    )

    # Results
    overall_score = models.FloatField()  # 0-100
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
    )

    # Control counts
    passed_controls = models.IntegerField(default=0)
    failed_controls = models.IntegerField(default=0)
    pending_controls = models.IntegerField(default=0)
    total_controls = models.IntegerField(default=0)

    # Timestamps
    generated_at = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "compliance report"
        verbose_name_plural = "compliance reports"
        ordering = ["-generated_at"]
        indexes = [
            models.Index(fields=["consortium", "framework"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.consortium.name} - {self.framework.name} Report"


class Attestation(models.Model):
    """
    Compliance attestation by authorized personnel.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    consortium = models.ForeignKey(
        "consortiums.Consortium",
        on_delete=models.CASCADE,
        related_name="attestations",
    )
    framework = models.ForeignKey(
        ComplianceFramework,
        on_delete=models.CASCADE,
        related_name="attestations",
    )
    control_id = models.CharField(max_length=50, blank=True)

    # Attester info
    attester = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="attestations",
    )
    attester_role = models.CharField(max_length=100, blank=True)
    attestation_type = models.CharField(max_length=50, default="manual")

    # Statement
    statement = models.TextField()
    evidence_urls = models.JSONField(default=list, blank=True)

    # Validity
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    revoked = models.BooleanField(default=False)
    revoked_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "attestation"
        verbose_name_plural = "attestations"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["consortium", "framework"]),
            models.Index(fields=["revoked"]),
        ]

    def __str__(self):
        return f"Attestation by {self.attester.name}"

    @property
    def is_valid(self):
        if self.revoked:
            return False
        now = timezone.now()
        if self.valid_until and now > self.valid_until:
            return False
        return now >= self.valid_from


class DataProcessingRecord(models.Model):
    """
    GDPR Article 30 - Records of processing activities.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    consortium = models.ForeignKey(
        "consortiums.Consortium",
        on_delete=models.CASCADE,
        related_name="data_processing_records",
    )
    company = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="data_processing_records",
    )

    # Processing details
    processing_purpose = models.TextField()
    data_categories = models.JSONField(default=list)
    legal_basis = models.CharField(max_length=200)

    # Data subjects
    data_subjects = models.CharField(max_length=500, blank=True)
    recipients = models.JSONField(default=list, blank=True)

    # Retention
    retention_period = models.CharField(max_length=100, blank=True)

    # Security
    security_measures = models.JSONField(default=list, blank=True)

    # Cross-border transfers
    cross_border_transfer = models.BooleanField(default=False)
    transfer_safeguards = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "data processing record"
        verbose_name_plural = "data processing records"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["consortium"]),
            models.Index(fields=["company"]),
        ]

    def __str__(self):
        return f"{self.processing_purpose[:50]}..."

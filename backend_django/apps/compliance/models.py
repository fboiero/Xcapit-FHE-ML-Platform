"""
Compliance models for Xcapit FHE-ML Platform.

Marcos regulatorios, evaluaciones de cumplimiento, verificaciones de controles,
atestaciones y registros de procesamiento de datos (GDPR Art. 30).
"""

import uuid

from django.db import models
from django.utils import timezone


class ComplianceFramework(models.Model):
    """Marco regulatorio de cumplimiento."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=100, unique=True)
    version = models.CharField(max_length=20, default="1.0")
    description = models.TextField(blank=True)
    region = models.CharField(max_length=100, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    controls = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "compliance framework"
        verbose_name_plural = "compliance frameworks"

    def __str__(self) -> str:
        return f"{self.name} v{self.version}"

    @property
    def controls_count(self) -> int:
        """Cantidad de controles definidos en el marco."""
        if isinstance(self.controls, list):
            return len(self.controls)
        return 0


class ConsortiumCompliance(models.Model):
    """Configuración de cumplimiento por consorcio."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    consortium = models.OneToOneField(
        "consortiums.Consortium",
        on_delete=models.CASCADE,
        related_name="compliance_config",
    )
    enabled_frameworks = models.ManyToManyField(
        ComplianceFramework,
        related_name="consortium_configs",
        blank=True,
    )

    auto_check_interval = models.IntegerField(
        default=24,
        help_text="Intervalo de verificación automática en horas.",
    )
    notification_emails = models.JSONField(default=list, blank=True)
    last_check_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "consortium compliance"
        verbose_name_plural = "consortium compliances"

    def __str__(self) -> str:
        return f"Compliance config — {self.consortium.name}"

    @property
    def next_check_at(self) -> "timezone.datetime | None":
        """Próxima verificación programada."""
        if self.last_check_at is None:
            return None
        from datetime import timedelta

        return self.last_check_at + timedelta(hours=self.auto_check_interval)


class ComplianceCheck(models.Model):
    """Verificación individual de un control de cumplimiento."""

    class Status(models.TextChoices):
        COMPLIANT = "compliant", "Compliant"
        NON_COMPLIANT = "non_compliant", "Non-Compliant"
        PARTIAL = "partial", "Partial"
        NOT_APPLICABLE = "not_applicable", "Not Applicable"

    class Result(models.TextChoices):
        PASS = "pass", "Pass"
        FAIL = "fail", "Fail"
        WARNING = "warning", "Warning"
        SKIPPED = "skipped", "Skipped"

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

    control_id = models.CharField(max_length=50)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NOT_APPLICABLE,
    )
    result = models.CharField(
        max_length=20,
        choices=Result.choices,
        default=Result.SKIPPED,
    )
    evidence = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    checked_by = models.ForeignKey(
        "core.Company",
        on_delete=models.SET_NULL,
        related_name="compliance_checks",
        null=True,
        blank=True,
    )
    checked_at = models.DateTimeField(auto_now_add=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "compliance check"
        verbose_name_plural = "compliance checks"
        indexes = [
            models.Index(fields=["consortium", "framework"]),
            models.Index(fields=["control_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.control_id} — {self.status} ({self.framework.name})"


class ComplianceReport(models.Model):
    """Reporte generado de cumplimiento para un consorcio y marco."""

    class Status(models.TextChoices):
        GENERATING = "generating", "Generating"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

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

    overall_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.GENERATING,
    )

    passed_controls = models.IntegerField(default=0)
    failed_controls = models.IntegerField(default=0)
    pending_controls = models.IntegerField(default=0)
    total_controls = models.IntegerField(default=0)

    generated_at = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "compliance report"
        verbose_name_plural = "compliance reports"
        indexes = [
            models.Index(fields=["consortium", "framework"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"Report — {self.consortium.name} / {self.framework.name} ({self.status})"


class Attestation(models.Model):
    """Atestación de cumplimiento por parte de una empresa."""

    class AttestationType(models.TextChoices):
        SELF_ASSESSMENT = "self_assessment", "Self Assessment"
        THIRD_PARTY = "third_party", "Third Party"
        AUTOMATED = "automated", "Automated"

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

    attester = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="attestations",
    )
    attester_role = models.CharField(max_length=100, blank=True)
    attestation_type = models.CharField(
        max_length=20,
        choices=AttestationType.choices,
        default=AttestationType.SELF_ASSESSMENT,
    )

    statement = models.TextField()
    evidence_urls = models.JSONField(default=list, blank=True)

    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)

    revoked = models.BooleanField(default=False)
    revoked_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "attestation"
        verbose_name_plural = "attestations"
        indexes = [
            models.Index(fields=["consortium", "framework"]),
            models.Index(fields=["attester"]),
        ]

    def __str__(self) -> str:
        return f"Attestation by {self.attester} — {self.framework.name}"

    @property
    def is_valid(self) -> bool:
        """Indica si la atestación está vigente."""
        if self.revoked:
            return False
        now = timezone.now()
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        return True


class DataProcessingRecord(models.Model):
    """Registro de procesamiento de datos (GDPR Artículo 30)."""

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

    processing_purpose = models.TextField()
    data_categories = models.JSONField(default=list)
    legal_basis = models.CharField(max_length=255)
    data_subjects = models.TextField(blank=True)
    recipients = models.JSONField(default=list, blank=True)
    retention_period = models.CharField(max_length=100, blank=True)
    security_measures = models.TextField(blank=True)
    cross_border_transfer = models.BooleanField(default=False)
    transfer_safeguards = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "data processing record"
        verbose_name_plural = "data processing records"
        indexes = [
            models.Index(fields=["consortium", "company"]),
        ]

    def __str__(self) -> str:
        purpose = self.processing_purpose
        if len(purpose) > 60:
            purpose = purpose[:57] + "..."
        return f"{self.company.name} — {purpose}"

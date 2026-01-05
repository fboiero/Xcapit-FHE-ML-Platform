# Generated manually for Xcapit FHE-ML Platform
# Django 5.2 LTS

import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("core", "0001_initial"),
        ("consortiums", "0001_initial"),
    ]

    operations = [
        # ComplianceFramework
        migrations.CreateModel(
            name="ComplianceFramework",
            fields=[
                ("id", models.CharField(max_length=50, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=100)),
                ("version", models.CharField(max_length=20)),
                ("description", models.TextField(blank=True)),
                ("region", models.CharField(blank=True, max_length=50)),
                ("industry", models.CharField(blank=True, max_length=50)),
                ("controls", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "compliance framework",
                "verbose_name_plural": "compliance frameworks",
            },
        ),
        # ConsortiumCompliance
        migrations.CreateModel(
            name="ConsortiumCompliance",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("auto_check_interval", models.IntegerField(default=24)),
                ("notification_emails", models.JSONField(blank=True, default=list)),
                ("last_check_at", models.DateTimeField(blank=True, null=True)),
                (
                    "consortium",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="compliance_settings",
                        to="consortiums.consortium",
                    ),
                ),
                (
                    "enabled_frameworks",
                    models.ManyToManyField(
                        blank=True,
                        related_name="consortiums",
                        to="compliance.complianceframework",
                    ),
                ),
            ],
            options={
                "verbose_name": "consortium compliance",
                "verbose_name_plural": "consortium compliance settings",
            },
        ),
        # ComplianceCheck
        migrations.CreateModel(
            name="ComplianceCheck",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("control_id", models.CharField(max_length=50)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("passed", "Passed"),
                            ("failed", "Failed"),
                            ("pending", "Pending"),
                            ("na", "Not Applicable"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("result", models.TextField()),
                ("evidence", models.JSONField(blank=True, default=dict)),
                ("notes", models.TextField(blank=True)),
                ("checked_at", models.DateTimeField(auto_now_add=True)),
                (
                    "checked_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="compliance_checks",
                        to="core.company",
                    ),
                ),
                (
                    "consortium",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="compliance_checks",
                        to="consortiums.consortium",
                    ),
                ),
                (
                    "framework",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="checks",
                        to="compliance.complianceframework",
                    ),
                ),
            ],
            options={
                "verbose_name": "compliance check",
                "verbose_name_plural": "compliance checks",
                "ordering": ["-checked_at"],
            },
        ),
        migrations.AddIndex(
            model_name="compliancecheck",
            index=models.Index(
                fields=["consortium", "framework"], name="comp_check_cons_fw_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="compliancecheck",
            index=models.Index(fields=["control_id"], name="comp_check_control_idx"),
        ),
        migrations.AddIndex(
            model_name="compliancecheck",
            index=models.Index(fields=["status"], name="comp_check_status_idx"),
        ),
        # ComplianceReport
        migrations.CreateModel(
            name="ComplianceReport",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("overall_score", models.FloatField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("compliant", "Compliant"),
                            ("non_compliant", "Non-Compliant"),
                            ("partial", "Partially Compliant"),
                            ("pending", "Pending"),
                        ],
                        max_length=20,
                    ),
                ),
                ("passed_controls", models.IntegerField(default=0)),
                ("failed_controls", models.IntegerField(default=0)),
                ("pending_controls", models.IntegerField(default=0)),
                ("total_controls", models.IntegerField(default=0)),
                ("generated_at", models.DateTimeField(auto_now_add=True)),
                ("valid_until", models.DateTimeField(blank=True, null=True)),
                (
                    "consortium",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="compliance_reports",
                        to="consortiums.consortium",
                    ),
                ),
                (
                    "framework",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reports",
                        to="compliance.complianceframework",
                    ),
                ),
            ],
            options={
                "verbose_name": "compliance report",
                "verbose_name_plural": "compliance reports",
                "ordering": ["-generated_at"],
            },
        ),
        migrations.AddIndex(
            model_name="compliancereport",
            index=models.Index(
                fields=["consortium", "framework"], name="comp_report_cons_fw_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="compliancereport",
            index=models.Index(fields=["status"], name="comp_report_status_idx"),
        ),
        # Attestation
        migrations.CreateModel(
            name="Attestation",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("control_id", models.CharField(blank=True, max_length=50)),
                ("attester_role", models.CharField(blank=True, max_length=100)),
                ("attestation_type", models.CharField(default="manual", max_length=50)),
                ("statement", models.TextField()),
                ("evidence_urls", models.JSONField(blank=True, default=list)),
                ("valid_from", models.DateTimeField(default=django.utils.timezone.now)),
                ("valid_until", models.DateTimeField(blank=True, null=True)),
                ("revoked", models.BooleanField(default=False)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "attester",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attestations",
                        to="core.company",
                    ),
                ),
                (
                    "consortium",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attestations",
                        to="consortiums.consortium",
                    ),
                ),
                (
                    "framework",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attestations",
                        to="compliance.complianceframework",
                    ),
                ),
            ],
            options={
                "verbose_name": "attestation",
                "verbose_name_plural": "attestations",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="attestation",
            index=models.Index(
                fields=["consortium", "framework"], name="attest_cons_fw_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="attestation",
            index=models.Index(fields=["revoked"], name="attest_revoked_idx"),
        ),
        # DataProcessingRecord
        migrations.CreateModel(
            name="DataProcessingRecord",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("processing_purpose", models.TextField()),
                ("data_categories", models.JSONField(default=list)),
                ("legal_basis", models.CharField(max_length=200)),
                ("data_subjects", models.CharField(blank=True, max_length=500)),
                ("recipients", models.JSONField(blank=True, default=list)),
                ("retention_period", models.CharField(blank=True, max_length=100)),
                ("security_measures", models.JSONField(blank=True, default=list)),
                ("cross_border_transfer", models.BooleanField(default=False)),
                ("transfer_safeguards", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="data_processing_records",
                        to="core.company",
                    ),
                ),
                (
                    "consortium",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="data_processing_records",
                        to="consortiums.consortium",
                    ),
                ),
            ],
            options={
                "verbose_name": "data processing record",
                "verbose_name_plural": "data processing records",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="dataprocessingrecord",
            index=models.Index(fields=["consortium"], name="dpr_consortium_idx"),
        ),
        migrations.AddIndex(
            model_name="dataprocessingrecord",
            index=models.Index(fields=["company"], name="dpr_company_idx"),
        ),
    ]

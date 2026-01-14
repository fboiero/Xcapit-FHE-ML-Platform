# Generated manually for Xcapit FHE-ML Platform
# Django 5.2 LTS

import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("core", "0001_initial"),
        ("consortiums", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # QualityAssessment
        migrations.CreateModel(
            name="QualityAssessment",
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
                ("record_count", models.IntegerField(default=0)),
                ("feature_count", models.IntegerField(default=0)),
                ("null_count", models.IntegerField(default=0)),
                ("duplicate_count", models.IntegerField(default=0)),
                ("outlier_count", models.IntegerField(default=0)),
                ("schema_violations", models.IntegerField(default=0)),
                ("format_violations", models.IntegerField(default=0)),
                ("range_violations", models.IntegerField(default=0)),
                ("completeness_score", models.FloatField(default=0)),
                ("consistency_score", models.FloatField(default=0)),
                ("accuracy_score", models.FloatField(default=0)),
                ("timeliness_score", models.FloatField(default=0)),
                ("overall_score", models.FloatField(default=0)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("last_assessed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="quality_assessments",
                        to="core.company",
                    ),
                ),
                (
                    "consortium",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="quality_assessments",
                        to="consortiums.consortium",
                    ),
                ),
                (
                    "contribution",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="quality_assessments",
                        to="consortiums.contributionproof",
                    ),
                ),
            ],
            options={
                "verbose_name": "quality assessment",
                "verbose_name_plural": "quality assessments",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="qualityassessment",
            index=models.Index(
                fields=["consortium", "company"], name="dq_assess_cons_comp_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="qualityassessment",
            index=models.Index(fields=["status"], name="dq_assess_status_idx"),
        ),
        migrations.AddIndex(
            model_name="qualityassessment",
            index=models.Index(fields=["overall_score"], name="dq_assess_score_idx"),
        ),
        # QualityRule
        migrations.CreateModel(
            name="QualityRule",
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
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                (
                    "rule_type",
                    models.CharField(
                        choices=[
                            ("threshold", "Threshold"),
                            ("range", "Range"),
                            ("pattern", "Pattern"),
                            ("custom", "Custom"),
                        ],
                        default="threshold",
                        max_length=20,
                    ),
                ),
                ("metric", models.CharField(max_length=100)),
                ("condition", models.JSONField(default=dict)),
                (
                    "severity",
                    models.CharField(
                        choices=[
                            ("info", "Info"),
                            ("warning", "Warning"),
                            ("error", "Error"),
                            ("critical", "Critical"),
                        ],
                        default="warning",
                        max_length=20,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "consortium",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="quality_rules",
                        to="consortiums.consortium",
                    ),
                ),
            ],
            options={
                "verbose_name": "quality rule",
                "verbose_name_plural": "quality rules",
            },
        ),
        migrations.AddIndex(
            model_name="qualityrule",
            index=models.Index(fields=["consortium"], name="dq_rule_consortium_idx"),
        ),
        migrations.AddIndex(
            model_name="qualityrule",
            index=models.Index(fields=["is_active"], name="dq_rule_active_idx"),
        ),
        # QualityAlert
        migrations.CreateModel(
            name="QualityAlert",
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
                ("message", models.TextField()),
                ("actual_value", models.FloatField(blank=True, null=True)),
                ("expected_value", models.CharField(blank=True, max_length=255)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("open", "Open"),
                            ("acknowledged", "Acknowledged"),
                            ("resolved", "Resolved"),
                            ("ignored", "Ignored"),
                        ],
                        db_index=True,
                        default="open",
                        max_length=20,
                    ),
                ),
                ("resolution_note", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                (
                    "assessment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="alerts",
                        to="data_quality.qualityassessment",
                    ),
                ),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="quality_alerts",
                        to="core.company",
                    ),
                ),
                (
                    "resolved_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="resolved_alerts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "rule",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="alerts",
                        to="data_quality.qualityrule",
                    ),
                ),
            ],
            options={
                "verbose_name": "quality alert",
                "verbose_name_plural": "quality alerts",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="qualityalert",
            index=models.Index(fields=["status"], name="dq_alert_status_idx"),
        ),
        migrations.AddIndex(
            model_name="qualityalert",
            index=models.Index(fields=["company"], name="dq_alert_company_idx"),
        ),
    ]

# Generated manually for Xcapit FHE-ML Platform
# Django 5.2 LTS

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        # SandboxTemplate
        migrations.CreateModel(
            name="SandboxTemplate",
            fields=[
                ("id", models.CharField(max_length=50, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
                ("industry", models.CharField(blank=True, max_length=50)),
                ("template_type", models.CharField(default="generic", max_length=50)),
                ("datasets", models.JSONField(default=list)),
                ("experiments", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "sandbox template",
                "verbose_name_plural": "sandbox templates",
            },
        ),
        # Sandbox
        migrations.CreateModel(
            name="Sandbox",
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
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
                ("industry", models.CharField(blank=True, max_length=50)),
                ("config", models.JSONField(blank=True, default=dict)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("expired", "Expired"),
                            ("archived", "Archived"),
                        ],
                        default="active",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sandboxes",
                        to="core.company",
                    ),
                ),
                (
                    "template",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="sandboxes",
                        to="sandbox.sandboxtemplate",
                    ),
                ),
            ],
            options={
                "verbose_name": "sandbox",
                "verbose_name_plural": "sandboxes",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="sandbox",
            index=models.Index(fields=["owner"], name="sb_owner_idx"),
        ),
        migrations.AddIndex(
            model_name="sandbox",
            index=models.Index(fields=["status"], name="sb_status_idx"),
        ),
        migrations.AddIndex(
            model_name="sandbox",
            index=models.Index(fields=["expires_at"], name="sb_expires_idx"),
        ),
        # SyntheticDataset
        migrations.CreateModel(
            name="SyntheticDataset",
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
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
                (
                    "dataset_type",
                    models.CharField(
                        choices=[
                            ("transactions", "Transactions"),
                            ("applications", "Applications"),
                            ("customers", "Customers"),
                            ("patients", "Patients"),
                            ("generic", "Generic"),
                        ],
                        default="generic",
                        max_length=30,
                    ),
                ),
                ("industry", models.CharField(blank=True, max_length=50)),
                ("record_count", models.IntegerField()),
                ("feature_count", models.IntegerField()),
                ("features", models.JSONField(default=list)),
                ("statistics", models.JSONField(blank=True, default=dict)),
                ("data_preview", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "sandbox",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="datasets",
                        to="sandbox.sandbox",
                    ),
                ),
            ],
            options={
                "verbose_name": "synthetic dataset",
                "verbose_name_plural": "synthetic datasets",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="syntheticdataset",
            index=models.Index(fields=["sandbox"], name="sd_sandbox_idx"),
        ),
        migrations.AddIndex(
            model_name="syntheticdataset",
            index=models.Index(fields=["dataset_type"], name="sd_type_idx"),
        ),
        # Experiment
        migrations.CreateModel(
            name="Experiment",
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
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
                (
                    "experiment_type",
                    models.CharField(
                        choices=[
                            ("training", "Model Training"),
                            ("evaluation", "Model Evaluation"),
                            ("clustering", "Clustering Analysis"),
                            ("encryption_benchmark", "Encryption Benchmark"),
                        ],
                        max_length=30,
                    ),
                ),
                ("model_type", models.CharField(blank=True, max_length=50)),
                ("config", models.JSONField(blank=True, default=dict)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("running", "Running"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("results", models.JSONField(blank=True, default=dict)),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "dataset",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="experiments",
                        to="sandbox.syntheticdataset",
                    ),
                ),
                (
                    "sandbox",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="experiments",
                        to="sandbox.sandbox",
                    ),
                ),
            ],
            options={
                "verbose_name": "experiment",
                "verbose_name_plural": "experiments",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="experiment",
            index=models.Index(fields=["sandbox"], name="exp_sandbox_idx"),
        ),
        migrations.AddIndex(
            model_name="experiment",
            index=models.Index(fields=["status"], name="exp_status_idx"),
        ),
        migrations.AddIndex(
            model_name="experiment",
            index=models.Index(fields=["experiment_type"], name="exp_type_idx"),
        ),
    ]

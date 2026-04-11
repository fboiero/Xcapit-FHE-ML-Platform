"""
Initial sandbox migration — SandboxLead, SandboxTemplate, Sandbox,
SyntheticDataset, Experiment, Subscription, DataUpload.
"""

import secrets
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("core", "0004_company_trial_fields"),
        ("consortiums", "0001_initial"),
    ]

    operations = [
        # ── SandboxLead ──────────────────────────────────────────
        migrations.CreateModel(
            name="SandboxLead",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("email", models.EmailField(db_index=True, max_length=254)),
                ("token", models.CharField(db_index=True, max_length=64, unique=True)),
                ("source", models.CharField(blank=True, default="direct", max_length=50)),
                ("utm_campaign", models.CharField(blank=True, max_length=100)),
                ("utm_source", models.CharField(blank=True, max_length=100)),
                ("utm_medium", models.CharField(blank=True, max_length=100)),
                ("converted", models.BooleanField(default=False)),
                ("converted_at", models.DateTimeField(blank=True, null=True)),
                ("converted_to_user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="sandbox_lead", to=settings.AUTH_USER_MODEL)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                ("last_access_at", models.DateTimeField(blank=True, null=True)),
                ("access_count", models.IntegerField(default=0)),
            ],
            options={
                "verbose_name": "sandbox lead",
                "verbose_name_plural": "sandbox leads",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="sandboxlead",
            index=models.Index(fields=["email"], name="sandbox_sbl_email_idx"),
        ),
        migrations.AddIndex(
            model_name="sandboxlead",
            index=models.Index(fields=["token"], name="sandbox_sbl_token_idx"),
        ),
        migrations.AddIndex(
            model_name="sandboxlead",
            index=models.Index(fields=["created_at"], name="sandbox_sbl_created_idx"),
        ),
        migrations.AddIndex(
            model_name="sandboxlead",
            index=models.Index(fields=["converted"], name="sandbox_sbl_conv_idx"),
        ),
        # ── SandboxTemplate ──────────────────────────────────────
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
                "ordering": ["name"],
            },
        ),
        # ── Sandbox ──────────────────────────────────────────────
        migrations.CreateModel(
            name="Sandbox",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sandboxes", to="core.company")),
                ("template", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="sandboxes", to="sandbox.sandboxtemplate")),
                ("industry", models.CharField(blank=True, max_length=50)),
                ("config", models.JSONField(blank=True, default=dict)),
                ("status", models.CharField(choices=[("active", "Active"), ("expired", "Expired"), ("archived", "Archived")], default="active", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "sandbox",
                "verbose_name_plural": "sandboxes",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="sandbox",
            index=models.Index(fields=["owner"], name="sandbox_sb_owner_idx"),
        ),
        migrations.AddIndex(
            model_name="sandbox",
            index=models.Index(fields=["status"], name="sandbox_sb_status_idx"),
        ),
        migrations.AddIndex(
            model_name="sandbox",
            index=models.Index(fields=["expires_at"], name="sandbox_sb_expires_idx"),
        ),
        # ── SyntheticDataset ─────────────────────────────────────
        migrations.CreateModel(
            name="SyntheticDataset",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("sandbox", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="datasets", to="sandbox.sandbox")),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
                ("dataset_type", models.CharField(choices=[("transactions", "Transactions"), ("applications", "Applications"), ("customers", "Customers"), ("patients", "Patients"), ("generic", "Generic")], default="generic", max_length=30)),
                ("industry", models.CharField(blank=True, max_length=50)),
                ("record_count", models.IntegerField()),
                ("feature_count", models.IntegerField()),
                ("features", models.JSONField(default=list)),
                ("statistics", models.JSONField(blank=True, default=dict)),
                ("data_preview", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "synthetic dataset",
                "verbose_name_plural": "synthetic datasets",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="syntheticdataset",
            index=models.Index(fields=["sandbox"], name="sandbox_sd_sandbox_idx"),
        ),
        migrations.AddIndex(
            model_name="syntheticdataset",
            index=models.Index(fields=["dataset_type"], name="sandbox_sd_dtype_idx"),
        ),
        # ── Experiment ───────────────────────────────────────────
        migrations.CreateModel(
            name="Experiment",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("sandbox", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="experiments", to="sandbox.sandbox")),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
                ("experiment_type", models.CharField(choices=[("training", "Model Training"), ("evaluation", "Model Evaluation"), ("clustering", "Clustering Analysis"), ("encryption_benchmark", "Encryption Benchmark")], max_length=30)),
                ("model_type", models.CharField(blank=True, max_length=50)),
                ("dataset", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="experiments", to="sandbox.syntheticdataset")),
                ("config", models.JSONField(blank=True, default=dict)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("running", "Running"), ("completed", "Completed"), ("failed", "Failed")], default="pending", max_length=20)),
                ("results", models.JSONField(blank=True, default=dict)),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "experiment",
                "verbose_name_plural": "experiments",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="experiment",
            index=models.Index(fields=["sandbox"], name="sandbox_exp_sandbox_idx"),
        ),
        migrations.AddIndex(
            model_name="experiment",
            index=models.Index(fields=["status"], name="sandbox_exp_status_idx"),
        ),
        migrations.AddIndex(
            model_name="experiment",
            index=models.Index(fields=["experiment_type"], name="sandbox_exp_type_idx"),
        ),
        # ── Subscription ─────────────────────────────────────────
        migrations.CreateModel(
            name="Subscription",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("company", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="subscription", to="core.company")),
                ("plan", models.CharField(choices=[("free", "Free"), ("starter", "Starter"), ("professional", "Professional"), ("enterprise", "Enterprise")], default="free", max_length=20)),
                ("status", models.CharField(choices=[("trialing", "Trialing"), ("active", "Active"), ("past_due", "Past Due"), ("cancelled", "Cancelled"), ("expired", "Expired")], db_index=True, default="trialing", max_length=20)),
                ("trial_end", models.DateTimeField(blank=True, null=True)),
                ("current_period_start", models.DateTimeField()),
                ("current_period_end", models.DateTimeField()),
                ("cancel_at_period_end", models.BooleanField(default=False)),
                ("external_id", models.CharField(blank=True, db_index=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "subscription",
                "verbose_name_plural": "subscriptions",
            },
        ),
        migrations.AddIndex(
            model_name="subscription",
            index=models.Index(fields=["status"], name="sandbox_sub_status_idx"),
        ),
        migrations.AddIndex(
            model_name="subscription",
            index=models.Index(fields=["plan"], name="sandbox_sub_plan_idx"),
        ),
        # ── DataUpload ───────────────────────────────────────────
        migrations.CreateModel(
            name="DataUpload",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="data_uploads", to="core.company")),
                ("consortium", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="data_uploads", to="consortiums.consortium")),
                ("file_name", models.CharField(max_length=255)),
                ("file_size", models.BigIntegerField()),
                ("record_count", models.IntegerField(default=0)),
                ("feature_count", models.IntegerField(default=0)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("processing", "Processing"), ("completed", "Completed"), ("failed", "Failed")], default="pending", max_length=20)),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "data upload",
                "verbose_name_plural": "data uploads",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="dataupload",
            index=models.Index(fields=["company"], name="sandbox_du_company_idx"),
        ),
        migrations.AddIndex(
            model_name="dataupload",
            index=models.Index(fields=["created_at"], name="sandbox_du_created_idx"),
        ),
    ]

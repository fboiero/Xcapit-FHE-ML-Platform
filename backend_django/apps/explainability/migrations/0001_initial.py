# Generated manually for Xcapit FHE-ML Platform
# Django 5.2 LTS

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("core", "0001_initial"),
        ("consortiums", "0001_initial"),
        ("models", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ExplanationRequest
        migrations.CreateModel(
            name="ExplanationRequest",
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
                (
                    "explanation_type",
                    models.CharField(
                        choices=[
                            ("feature_importance", "Feature Importance"),
                            ("shap", "SHAP Values"),
                            ("decision_path", "Decision Path"),
                            ("counterfactual", "Counterfactual"),
                            ("summary", "Model Summary"),
                        ],
                        default="feature_importance",
                        max_length=20,
                    ),
                ),
                (
                    "input_data",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Input data for instance-level explanations",
                    ),
                ),
                (
                    "prediction_id",
                    models.CharField(
                        blank=True,
                        help_text="Reference to specific prediction to explain",
                        max_length=100,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("processing", "Processing"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("error_message", models.TextField(blank=True)),
                ("explanation", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "consortium",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="explanation_requests",
                        to="consortiums.consortium",
                    ),
                ),
                (
                    "model",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="explanation_requests",
                        to="models.mlmodel",
                    ),
                ),
                (
                    "requester",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="explanation_requests",
                        to="core.company",
                    ),
                ),
            ],
            options={
                "verbose_name": "explanation request",
                "verbose_name_plural": "explanation requests",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="explanationrequest",
            index=models.Index(fields=["consortium"], name="expl_req_consortium_idx"),
        ),
        migrations.AddIndex(
            model_name="explanationrequest",
            index=models.Index(fields=["requester"], name="expl_req_requester_idx"),
        ),
        migrations.AddIndex(
            model_name="explanationrequest",
            index=models.Index(fields=["status"], name="expl_req_status_idx"),
        ),
        # FeatureImportance
        migrations.CreateModel(
            name="FeatureImportance",
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
                ("feature_name", models.CharField(max_length=255)),
                ("importance_score", models.FloatField()),
                ("importance_rank", models.IntegerField()),
                (
                    "computation_method",
                    models.CharField(
                        default="model_native",
                        help_text="Method used: model_native, permutation, shap",
                        max_length=50,
                    ),
                ),
                (
                    "std_deviation",
                    models.FloatField(
                        blank=True,
                        help_text="Standard deviation of importance across folds",
                        null=True,
                    ),
                ),
                ("computed_at", models.DateTimeField(auto_now_add=True)),
                (
                    "consortium",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="feature_importances",
                        to="consortiums.consortium",
                    ),
                ),
                (
                    "model",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="feature_importances",
                        to="models.mlmodel",
                    ),
                ),
            ],
            options={
                "verbose_name": "feature importance",
                "verbose_name_plural": "feature importances",
                "ordering": ["importance_rank"],
            },
        ),
        migrations.AddIndex(
            model_name="featureimportance",
            index=models.Index(fields=["consortium"], name="feat_imp_consortium_idx"),
        ),
        migrations.AddIndex(
            model_name="featureimportance",
            index=models.Index(fields=["importance_rank"], name="feat_imp_rank_idx"),
        ),
        # ModelInsight
        migrations.CreateModel(
            name="ModelInsight",
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
                (
                    "insight_type",
                    models.CharField(
                        choices=[
                            ("performance", "Performance Insight"),
                            ("feature", "Feature Insight"),
                            ("bias", "Bias Detection"),
                            ("drift", "Data Drift"),
                            ("anomaly", "Anomaly Detection"),
                        ],
                        max_length=20,
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField()),
                (
                    "severity",
                    models.CharField(
                        choices=[
                            ("info", "Info"),
                            ("warning", "Warning"),
                            ("critical", "Critical"),
                        ],
                        default="info",
                        max_length=20,
                    ),
                ),
                ("data", models.JSONField(default=dict)),
                ("recommendations", models.JSONField(default=list)),
                ("is_active", models.BooleanField(default=True)),
                ("acknowledged", models.BooleanField(default=False)),
                ("acknowledged_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                (
                    "acknowledged_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "consortium",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="model_insights",
                        to="consortiums.consortium",
                    ),
                ),
            ],
            options={
                "verbose_name": "model insight",
                "verbose_name_plural": "model insights",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="modelinsight",
            index=models.Index(fields=["consortium"], name="insight_consortium_idx"),
        ),
        migrations.AddIndex(
            model_name="modelinsight",
            index=models.Index(fields=["insight_type"], name="insight_type_idx"),
        ),
        migrations.AddIndex(
            model_name="modelinsight",
            index=models.Index(fields=["severity"], name="insight_severity_idx"),
        ),
    ]

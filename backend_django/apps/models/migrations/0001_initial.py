# Generated manually for Xcapit FHE-ML Platform
# Django 5.2 LTS

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("core", "0001_initial"),
        ("consortiums", "0001_initial"),
    ]

    operations = [
        # MLModel
        migrations.CreateModel(
            name="MLModel",
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
                (
                    "model_type",
                    models.CharField(
                        choices=[
                            ("linear_regression", "Linear Regression"),
                            ("logistic_regression", "Logistic Regression"),
                            ("decision_tree", "Decision Tree"),
                            ("kmeans", "K-Means Clustering"),
                        ],
                        db_index=True,
                        max_length=50,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("created", "Created"),
                            ("training", "Training"),
                            ("trained", "Trained"),
                            ("failed", "Failed"),
                            ("archived", "Archived"),
                        ],
                        db_index=True,
                        default="created",
                        max_length=20,
                    ),
                ),
                ("config", models.JSONField(blank=True, default=dict)),
                ("params", models.JSONField(blank=True, default=dict)),
                ("n_features", models.IntegerField(blank=True, null=True)),
                ("feature_names", models.JSONField(blank=True, default=list)),
                ("trained_at", models.DateTimeField(blank=True, null=True)),
                ("training_epochs", models.IntegerField(blank=True, null=True)),
                ("final_loss", models.FloatField(blank=True, null=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "consortium",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="models",
                        to="consortiums.consortium",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="models",
                        to="core.company",
                    ),
                ),
            ],
            options={
                "verbose_name": "ML model",
                "verbose_name_plural": "ML models",
                "ordering": ["-updated_at"],
            },
        ),
        migrations.AddIndex(
            model_name="mlmodel",
            index=models.Index(fields=["model_type"], name="models_model_type_idx"),
        ),
        migrations.AddIndex(
            model_name="mlmodel",
            index=models.Index(fields=["status"], name="models_status_idx"),
        ),
        migrations.AddIndex(
            model_name="mlmodel",
            index=models.Index(fields=["consortium"], name="models_consortium_idx"),
        ),
        migrations.AddIndex(
            model_name="mlmodel",
            index=models.Index(fields=["owner"], name="models_owner_idx"),
        ),
        # TrainingRun
        migrations.CreateModel(
            name="TrainingRun",
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
                    "status",
                    models.CharField(
                        choices=[
                            ("queued", "Queued"),
                            ("running", "Running"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                            ("cancelled", "Cancelled"),
                        ],
                        db_index=True,
                        default="queued",
                        max_length=20,
                    ),
                ),
                ("epochs_completed", models.IntegerField(default=0)),
                ("epochs_total", models.IntegerField(blank=True, null=True)),
                ("current_loss", models.FloatField(blank=True, null=True)),
                ("final_loss", models.FloatField(blank=True, null=True)),
                ("metrics", models.JSONField(blank=True, default=dict)),
                ("error_message", models.TextField(blank=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "model",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="training_runs",
                        to="models.mlmodel",
                    ),
                ),
            ],
            options={
                "verbose_name": "training run",
                "verbose_name_plural": "training runs",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="trainingrun",
            index=models.Index(fields=["model"], name="training_model_idx"),
        ),
        migrations.AddIndex(
            model_name="trainingrun",
            index=models.Index(fields=["status"], name="training_status_idx"),
        ),
        # PredictionLog
        migrations.CreateModel(
            name="PredictionLog",
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
                ("n_samples", models.IntegerField()),
                ("encrypted", models.BooleanField(default=False)),
                ("latency_ms", models.FloatField()),
                ("api_key_name", models.CharField(blank=True, max_length=255)),
                ("timestamp", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "model",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="prediction_logs",
                        to="models.mlmodel",
                    ),
                ),
                (
                    "requester",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="predictions",
                        to="core.company",
                    ),
                ),
            ],
            options={
                "verbose_name": "prediction log",
                "verbose_name_plural": "prediction logs",
                "ordering": ["-timestamp"],
            },
        ),
        migrations.AddIndex(
            model_name="predictionlog",
            index=models.Index(fields=["model"], name="prediction_model_idx"),
        ),
        migrations.AddIndex(
            model_name="predictionlog",
            index=models.Index(fields=["requester"], name="prediction_requester_idx"),
        ),
        migrations.AddIndex(
            model_name="predictionlog",
            index=models.Index(fields=["timestamp"], name="prediction_timestamp_idx"),
        ),
        migrations.AddIndex(
            model_name="predictionlog",
            index=models.Index(fields=["encrypted"], name="prediction_encrypted_idx"),
        ),
        # ModelCheckpoint
        migrations.CreateModel(
            name="ModelCheckpoint",
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
                ("epoch", models.IntegerField()),
                ("loss", models.FloatField(blank=True, null=True)),
                ("weights_encrypted", models.JSONField(default=dict)),
                ("weights_hash", models.CharField(max_length=64)),
                ("blockchain_tx", models.CharField(blank=True, max_length=66)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "model",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="checkpoints",
                        to="models.mlmodel",
                    ),
                ),
            ],
            options={
                "verbose_name": "model checkpoint",
                "verbose_name_plural": "model checkpoints",
                "ordering": ["-epoch"],
                "unique_together": {("model", "epoch")},
            },
        ),
        migrations.AddIndex(
            model_name="modelcheckpoint",
            index=models.Index(fields=["model", "epoch"], name="checkpoint_model_epoch_idx"),
        ),
        migrations.AddIndex(
            model_name="modelcheckpoint",
            index=models.Index(fields=["weights_hash"], name="checkpoint_hash_idx"),
        ),
    ]

# Generated manually for Xcapit FHE-ML Platform
# Django 5.2 LTS

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("core", "0001_initial"),
        ("models", "0001_initial"),
    ]

    operations = [
        # Ensemble
        migrations.CreateModel(
            name="Ensemble",
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
                    "ensemble_type",
                    models.CharField(
                        choices=[
                            ("voting", "Voting (Majority)"),
                            ("averaging", "Averaging"),
                            ("weighted", "Weighted Average"),
                            ("stacking", "Stacking"),
                            ("boosting", "Boosting"),
                        ],
                        default="voting",
                        max_length=20,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("active", "Active"),
                            ("training", "Training"),
                            ("deployed", "Deployed"),
                            ("archived", "Archived"),
                        ],
                        db_index=True,
                        default="draft",
                        max_length=20,
                    ),
                ),
                ("aggregation_config", models.JSONField(blank=True, default=dict)),
                ("accuracy", models.FloatField(blank=True, null=True)),
                ("f1_score", models.FloatField(blank=True, null=True)),
                (
                    "ensemble_improvement",
                    models.FloatField(
                        blank=True,
                        help_text="Improvement over best single model (%)",
                        null=True,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="owned_ensembles",
                        to="core.company",
                    ),
                ),
            ],
            options={
                "verbose_name": "ensemble",
                "verbose_name_plural": "ensembles",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="ensemble",
            index=models.Index(fields=["owner"], name="ens_owner_idx"),
        ),
        migrations.AddIndex(
            model_name="ensemble",
            index=models.Index(fields=["status"], name="ens_status_idx"),
        ),
        # EnsembleModel
        migrations.CreateModel(
            name="EnsembleModel",
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
                ("weight", models.FloatField(default=1.0)),
                ("individual_accuracy", models.FloatField(blank=True, null=True)),
                (
                    "contribution_score",
                    models.FloatField(
                        blank=True,
                        help_text="Model's contribution to ensemble performance",
                        null=True,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("added_at", models.DateTimeField(auto_now_add=True)),
                (
                    "ensemble",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ensemble_models",
                        to="ensemble.ensemble",
                    ),
                ),
                (
                    "model",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ensemble_memberships",
                        to="models.mlmodel",
                    ),
                ),
            ],
            options={
                "verbose_name": "ensemble model",
                "verbose_name_plural": "ensemble models",
                "unique_together": {("ensemble", "model")},
            },
        ),
        migrations.AddIndex(
            model_name="ensemblemodel",
            index=models.Index(fields=["ensemble"], name="ensmodel_ensemble_idx"),
        ),
        migrations.AddIndex(
            model_name="ensemblemodel",
            index=models.Index(fields=["model"], name="ensmodel_model_idx"),
        ),
        # EnsemblePrediction
        migrations.CreateModel(
            name="EnsemblePrediction",
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
                ("input_hash", models.CharField(max_length=64)),
                ("n_samples", models.IntegerField()),
                ("prediction", models.JSONField()),
                ("confidence", models.FloatField(blank=True, null=True)),
                ("model_predictions", models.JSONField(default=dict)),
                ("latency_ms", models.FloatField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "ensemble",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="predictions",
                        to="ensemble.ensemble",
                    ),
                ),
                (
                    "requester",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ensemble_predictions",
                        to="core.company",
                    ),
                ),
            ],
            options={
                "verbose_name": "ensemble prediction",
                "verbose_name_plural": "ensemble predictions",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="ensembleprediction",
            index=models.Index(fields=["ensemble"], name="enspred_ensemble_idx"),
        ),
        migrations.AddIndex(
            model_name="ensembleprediction",
            index=models.Index(fields=["requester"], name="enspred_requester_idx"),
        ),
        migrations.AddIndex(
            model_name="ensembleprediction",
            index=models.Index(fields=["created_at"], name="enspred_created_idx"),
        ),
        # EnsembleEvaluation
        migrations.CreateModel(
            name="EnsembleEvaluation",
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
                ("accuracy", models.FloatField()),
                ("precision", models.FloatField(blank=True, null=True)),
                ("recall", models.FloatField(blank=True, null=True)),
                ("f1_score", models.FloatField(blank=True, null=True)),
                ("auc_roc", models.FloatField(blank=True, null=True)),
                ("best_individual_accuracy", models.FloatField()),
                ("improvement_over_best", models.FloatField()),
                ("test_samples", models.IntegerField()),
                ("test_data_hash", models.CharField(max_length=64)),
                ("evaluated_at", models.DateTimeField(auto_now_add=True)),
                (
                    "ensemble",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="evaluations",
                        to="ensemble.ensemble",
                    ),
                ),
            ],
            options={
                "verbose_name": "ensemble evaluation",
                "verbose_name_plural": "ensemble evaluations",
                "ordering": ["-evaluated_at"],
            },
        ),
    ]

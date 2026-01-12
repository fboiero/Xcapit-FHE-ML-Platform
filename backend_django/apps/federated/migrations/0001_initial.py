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
        ("models", "0001_initial"),
    ]

    operations = [
        # FederatedModel
        migrations.CreateModel(
            name="FederatedModel",
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
                    "model_type",
                    models.CharField(
                        choices=[
                            ("linear_regression", "Linear Regression"),
                            ("logistic_regression", "Logistic Regression"),
                            ("neural_network", "Neural Network"),
                            ("xgboost", "XGBoost"),
                        ],
                        max_length=50,
                    ),
                ),
                ("version", models.CharField(default="1.0.0", max_length=20)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("training", "Training"),
                            ("ready", "Ready"),
                            ("deployed", "Deployed"),
                            ("archived", "Archived"),
                        ],
                        default="draft",
                        max_length=20,
                    ),
                ),
                ("config", models.JSONField(blank=True, default=dict)),
                ("metrics", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "consortium",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="federated_models",
                        to="consortiums.consortium",
                    ),
                ),
            ],
            options={
                "verbose_name": "federated model",
                "verbose_name_plural": "federated models",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="federatedmodel",
            index=models.Index(fields=["consortium"], name="fed_model_cons_idx"),
        ),
        migrations.AddIndex(
            model_name="federatedmodel",
            index=models.Index(fields=["status"], name="fed_model_status_idx"),
        ),
        # EdgeNode
        migrations.CreateModel(
            name="EdgeNode",
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
                (
                    "node_type",
                    models.CharField(
                        choices=[
                            ("on_premise", "On-Premise"),
                            ("cloud", "Cloud"),
                            ("hybrid", "Hybrid"),
                        ],
                        default="on_premise",
                        max_length=20,
                    ),
                ),
                ("location", models.CharField(blank=True, max_length=200)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("offline", "Offline"),
                            ("online", "Online"),
                            ("maintenance", "Maintenance"),
                        ],
                        default="offline",
                        max_length=20,
                    ),
                ),
                ("capabilities", models.JSONField(blank=True, default=dict)),
                ("last_heartbeat", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="edge_nodes",
                        to="core.company",
                    ),
                ),
                (
                    "deployed_models",
                    models.ManyToManyField(
                        blank=True,
                        related_name="edge_deployments",
                        to="federated.federatedmodel",
                    ),
                ),
            ],
            options={
                "verbose_name": "edge node",
                "verbose_name_plural": "edge nodes",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="edgenode",
            index=models.Index(fields=["company"], name="edge_company_idx"),
        ),
        migrations.AddIndex(
            model_name="edgenode",
            index=models.Index(fields=["status"], name="edge_status_idx"),
        ),
        # InferenceEndpoint
        migrations.CreateModel(
            name="InferenceEndpoint",
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
                    "endpoint_type",
                    models.CharField(
                        choices=[
                            ("realtime", "Real-time"),
                            ("batch", "Batch"),
                            ("streaming", "Streaming"),
                        ],
                        default="realtime",
                        max_length=20,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("active", "Active"),
                            ("paused", "Paused"),
                            ("failed", "Failed"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("config", models.JSONField(blank=True, default=dict)),
                ("url", models.URLField(blank=True)),
                ("request_count", models.IntegerField(default=0)),
                ("total_latency_ms", models.FloatField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="inference_endpoints",
                        to="core.company",
                    ),
                ),
                (
                    "consortium",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="inference_endpoints",
                        to="consortiums.consortium",
                    ),
                ),
                (
                    "model",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="endpoints",
                        to="models.mlmodel",
                    ),
                ),
            ],
            options={
                "verbose_name": "inference endpoint",
                "verbose_name_plural": "inference endpoints",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="inferenceendpoint",
            index=models.Index(fields=["consortium"], name="infer_ep_cons_idx"),
        ),
        migrations.AddIndex(
            model_name="inferenceendpoint",
            index=models.Index(fields=["company"], name="infer_ep_company_idx"),
        ),
        migrations.AddIndex(
            model_name="inferenceendpoint",
            index=models.Index(fields=["status"], name="infer_ep_status_idx"),
        ),
        # InferenceRequest
        migrations.CreateModel(
            name="InferenceRequest",
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
                            ("pending", "Pending"),
                            ("processing", "Processing"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                (
                    "priority",
                    models.CharField(
                        choices=[
                            ("low", "Low"),
                            ("normal", "Normal"),
                            ("high", "High"),
                        ],
                        default="normal",
                        max_length=10,
                    ),
                ),
                ("input_hash", models.CharField(max_length=64)),
                ("encryption_key_id", models.CharField(blank=True, max_length=100)),
                ("latency_ms", models.FloatField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "endpoint",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="requests",
                        to="federated.inferenceendpoint",
                    ),
                ),
                (
                    "requester",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="inference_requests",
                        to="core.company",
                    ),
                ),
            ],
            options={
                "verbose_name": "inference request",
                "verbose_name_plural": "inference requests",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="inferencerequest",
            index=models.Index(fields=["endpoint"], name="infer_req_ep_idx"),
        ),
        migrations.AddIndex(
            model_name="inferencerequest",
            index=models.Index(fields=["requester"], name="infer_req_req_idx"),
        ),
        migrations.AddIndex(
            model_name="inferencerequest",
            index=models.Index(fields=["status"], name="infer_req_status_idx"),
        ),
        # InferenceResult
        migrations.CreateModel(
            name="InferenceResult",
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
                ("encrypted_output", models.TextField()),
                ("output_metadata", models.JSONField(blank=True, default=dict)),
                ("confidence_scores", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "request",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="result",
                        to="federated.inferencerequest",
                    ),
                ),
            ],
            options={
                "verbose_name": "inference result",
                "verbose_name_plural": "inference results",
            },
        ),
    ]

# Generated manually for Xcapit FHE-ML Platform
# Django 5.2 LTS

import uuid

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("core", "0001_initial"),
        ("consortiums", "0001_initial"),
    ]

    operations = [
        # Category
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.CharField(max_length=50, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
                ("icon", models.CharField(blank=True, max_length=50)),
                ("order", models.IntegerField(default=0)),
            ],
            options={
                "verbose_name": "category",
                "verbose_name_plural": "categories",
                "ordering": ["order", "name"],
            },
        ),
        # MarketplaceModel
        migrations.CreateModel(
            name="MarketplaceModel",
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
                    "model_type",
                    models.CharField(
                        choices=[
                            ("linear_regression", "Linear Regression"),
                            ("logistic_regression", "Logistic Regression"),
                            ("decision_tree", "Decision Tree"),
                            ("kmeans", "K-Means Clustering"),
                        ],
                        max_length=50,
                    ),
                ),
                ("version", models.CharField(default="1.0.0", max_length=20)),
                (
                    "accuracy",
                    models.FloatField(
                        blank=True,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(1),
                        ],
                    ),
                ),
                ("training_samples", models.IntegerField(blank=True, null=True)),
                ("features", models.JSONField(default=list)),
                ("use_cases", models.JSONField(default=list)),
                (
                    "pricing_type",
                    models.CharField(
                        choices=[
                            ("free", "Free"),
                            ("one_time", "One-Time Purchase"),
                            ("subscription", "Subscription"),
                        ],
                        default="free",
                        max_length=20,
                    ),
                ),
                ("price", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("is_active", models.BooleanField(default=True)),
                ("is_featured", models.BooleanField(default=False)),
                ("downloads", models.IntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "category",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="marketplace_models",
                        to="marketplace.category",
                    ),
                ),
            ],
            options={
                "verbose_name": "marketplace model",
                "verbose_name_plural": "marketplace models",
                "ordering": ["-downloads", "-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="marketplacemodel",
            index=models.Index(fields=["category"], name="mkt_model_category_idx"),
        ),
        migrations.AddIndex(
            model_name="marketplacemodel",
            index=models.Index(fields=["model_type"], name="mkt_model_type_idx"),
        ),
        migrations.AddIndex(
            model_name="marketplacemodel",
            index=models.Index(fields=["is_active"], name="mkt_model_active_idx"),
        ),
        migrations.AddIndex(
            model_name="marketplacemodel",
            index=models.Index(fields=["is_featured"], name="mkt_model_featured_idx"),
        ),
        migrations.AddIndex(
            model_name="marketplacemodel",
            index=models.Index(fields=["-downloads"], name="mkt_model_downloads_idx"),
        ),
        # Deployment
        migrations.CreateModel(
            name="Deployment",
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
                            ("active", "Active"),
                            ("suspended", "Suspended"),
                            ("removed", "Removed"),
                        ],
                        default="active",
                        max_length=20,
                    ),
                ),
                ("config", models.JSONField(blank=True, default=dict)),
                ("deployed_at", models.DateTimeField(auto_now_add=True)),
                ("removed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "consortium",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="marketplace_deployments",
                        to="consortiums.consortium",
                    ),
                ),
                (
                    "deployed_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="deployments",
                        to="core.company",
                    ),
                ),
                (
                    "marketplace_model",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="deployments",
                        to="marketplace.marketplacemodel",
                    ),
                ),
            ],
            options={
                "verbose_name": "deployment",
                "verbose_name_plural": "deployments",
                "unique_together": {("marketplace_model", "consortium")},
            },
        ),
        migrations.AddIndex(
            model_name="deployment",
            index=models.Index(fields=["consortium"], name="mkt_deploy_cons_idx"),
        ),
        migrations.AddIndex(
            model_name="deployment",
            index=models.Index(fields=["status"], name="mkt_deploy_status_idx"),
        ),
        # Review
        migrations.CreateModel(
            name="Review",
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
                    "rating",
                    models.IntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(5),
                        ],
                    ),
                ),
                ("title", models.CharField(blank=True, max_length=100)),
                ("comment", models.TextField(blank=True, max_length=1000)),
                ("helpful_count", models.IntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "consortium",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="model_reviews",
                        to="consortiums.consortium",
                    ),
                ),
                (
                    "marketplace_model",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reviews",
                        to="marketplace.marketplacemodel",
                    ),
                ),
                (
                    "reviewer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reviews",
                        to="core.company",
                    ),
                ),
            ],
            options={
                "verbose_name": "review",
                "verbose_name_plural": "reviews",
                "ordering": ["-created_at"],
                "unique_together": {("marketplace_model", "reviewer")},
            },
        ),
        migrations.AddIndex(
            model_name="review",
            index=models.Index(fields=["marketplace_model"], name="mkt_review_model_idx"),
        ),
        migrations.AddIndex(
            model_name="review",
            index=models.Index(fields=["rating"], name="mkt_review_rating_idx"),
        ),
    ]

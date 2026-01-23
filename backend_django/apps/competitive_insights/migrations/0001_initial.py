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
        # IndustryBenchmark
        migrations.CreateModel(
            name="IndustryBenchmark",
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
                ("industry", models.CharField(db_index=True, max_length=100)),
                ("sub_industry", models.CharField(blank=True, max_length=100)),
                ("metric_name", models.CharField(max_length=100)),
                (
                    "metric_type",
                    models.CharField(
                        choices=[
                            ("accuracy", "Accuracy"),
                            ("performance", "Performance"),
                            ("efficiency", "Efficiency"),
                            ("quality", "Quality"),
                            ("growth", "Growth"),
                        ],
                        default="performance",
                        max_length=20,
                    ),
                ),
                ("unit", models.CharField(blank=True, max_length=50)),
                (
                    "p10_value",
                    models.FloatField(help_text="10th percentile"),
                ),
                (
                    "p25_value",
                    models.FloatField(help_text="25th percentile"),
                ),
                (
                    "p50_value",
                    models.FloatField(help_text="Median (50th percentile)"),
                ),
                (
                    "p75_value",
                    models.FloatField(help_text="75th percentile"),
                ),
                (
                    "p90_value",
                    models.FloatField(help_text="90th percentile"),
                ),
                (
                    "sample_size",
                    models.IntegerField(help_text="Number of companies in sample"),
                ),
                ("period_start", models.DateField()),
                ("period_end", models.DateField()),
                ("valid_until", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "industry benchmark",
                "verbose_name_plural": "industry benchmarks",
                "unique_together": {("industry", "metric_name", "period_start")},
            },
        ),
        migrations.AddIndex(
            model_name="industrybenchmark",
            index=models.Index(fields=["industry"], name="ci_bench_industry_idx"),
        ),
        migrations.AddIndex(
            model_name="industrybenchmark",
            index=models.Index(fields=["metric_name"], name="ci_bench_metric_idx"),
        ),
        migrations.AddIndex(
            model_name="industrybenchmark",
            index=models.Index(
                fields=["period_start", "period_end"], name="ci_bench_period_idx"
            ),
        ),
        # CompanyMetric
        migrations.CreateModel(
            name="CompanyMetric",
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
                ("metric_name", models.CharField(max_length=100)),
                ("value", models.FloatField()),
                ("percentile_rank", models.FloatField(blank=True, null=True)),
                ("period_start", models.DateField()),
                ("period_end", models.DateField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "benchmark",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="company_metrics",
                        to="competitive_insights.industrybenchmark",
                    ),
                ),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="competitive_metrics",
                        to="core.company",
                    ),
                ),
            ],
            options={
                "verbose_name": "company metric",
                "verbose_name_plural": "company metrics",
            },
        ),
        migrations.AddIndex(
            model_name="companymetric",
            index=models.Index(fields=["company"], name="ci_metric_company_idx"),
        ),
        migrations.AddIndex(
            model_name="companymetric",
            index=models.Index(fields=["metric_name"], name="ci_metric_name_idx"),
        ),
        migrations.AddIndex(
            model_name="companymetric",
            index=models.Index(fields=["period_start"], name="ci_metric_period_idx"),
        ),
        # CompetitiveReport
        migrations.CreateModel(
            name="CompetitiveReport",
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
                ("title", models.CharField(max_length=255)),
                ("industry", models.CharField(max_length=100)),
                ("period_start", models.DateField()),
                ("period_end", models.DateField()),
                ("summary", models.JSONField(default=dict)),
                ("strengths", models.JSONField(default=list)),
                ("weaknesses", models.JSONField(default=list)),
                ("opportunities", models.JSONField(default=list)),
                ("recommendations", models.JSONField(default=list)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("generating", "Generating"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="competitive_reports",
                        to="core.company",
                    ),
                ),
            ],
            options={
                "verbose_name": "competitive report",
                "verbose_name_plural": "competitive reports",
                "ordering": ["-created_at"],
            },
        ),
    ]

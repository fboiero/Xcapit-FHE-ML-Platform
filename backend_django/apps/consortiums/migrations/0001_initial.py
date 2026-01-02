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
        # Consortium model
        migrations.CreateModel(
            name="Consortium",
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
                        default="logistic_regression",
                        max_length=50,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("active", "Active"),
                            ("training", "Training"),
                            ("completed", "Completed"),
                            ("archived", "Archived"),
                        ],
                        db_index=True,
                        default="draft",
                        max_length=20,
                    ),
                ),
                ("ml_config", models.JSONField(blank=True, default=dict)),
                ("min_members", models.IntegerField(default=2)),
                ("voting_threshold", models.FloatField(default=0.5)),
                ("voting_duration_days", models.IntegerField(default=7)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="owned_consortiums",
                        to="core.company",
                    ),
                ),
            ],
            options={
                "verbose_name": "consortium",
                "verbose_name_plural": "consortiums",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="consortium",
            index=models.Index(fields=["status"], name="consort_status_a1b2c3_idx"),
        ),
        migrations.AddIndex(
            model_name="consortium",
            index=models.Index(fields=["owner"], name="consort_owner_d4e5f6_idx"),
        ),
        migrations.AddIndex(
            model_name="consortium",
            index=models.Index(fields=["created_at"], name="consort_created_g7h8i9_idx"),
        ),
        # ConsortiumMember model
        migrations.CreateModel(
            name="ConsortiumMember",
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
                    "role",
                    models.CharField(
                        choices=[
                            ("owner", "Owner"),
                            ("admin", "Admin"),
                            ("contributor", "Contributor"),
                            ("observer", "Observer"),
                        ],
                        default="contributor",
                        max_length=20,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("active", "Active"),
                            ("suspended", "Suspended"),
                            ("left", "Left"),
                            ("removed", "Removed"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("joined_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="consortium_memberships",
                        to="core.company",
                    ),
                ),
                (
                    "consortium",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="members",
                        to="consortiums.consortium",
                    ),
                ),
            ],
            options={
                "verbose_name": "consortium member",
                "verbose_name_plural": "consortium members",
                "unique_together": {("consortium", "company")},
            },
        ),
        migrations.AddIndex(
            model_name="consortiummember",
            index=models.Index(
                fields=["consortium", "status"], name="consort_mem_cons_stat_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="consortiummember",
            index=models.Index(fields=["company"], name="consort_mem_company_idx"),
        ),
        # ContributionProof model
        migrations.CreateModel(
            name="ContributionProof",
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
                ("record_count", models.IntegerField()),
                ("feature_count", models.IntegerField()),
                ("data_hash", models.CharField(db_index=True, max_length=64)),
                ("checksum", models.CharField(max_length=64)),
                ("verified", models.BooleanField(default=False)),
                ("verified_at", models.DateTimeField(blank=True, null=True)),
                ("blockchain_tx", models.CharField(blank=True, max_length=66)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="contributions",
                        to="core.company",
                    ),
                ),
                (
                    "consortium",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="contribution_proofs",
                        to="consortiums.consortium",
                    ),
                ),
            ],
            options={
                "verbose_name": "contribution proof",
                "verbose_name_plural": "contribution proofs",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="contributionproof",
            index=models.Index(
                fields=["consortium", "company"], name="contrib_cons_comp_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="contributionproof",
            index=models.Index(fields=["data_hash"], name="contrib_data_hash_idx"),
        ),
        migrations.AddIndex(
            model_name="contributionproof",
            index=models.Index(fields=["verified"], name="contrib_verified_idx"),
        ),
        # ConsortiumInvitation model
        migrations.CreateModel(
            name="ConsortiumInvitation",
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
                ("invitee_email", models.EmailField(max_length=254)),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("owner", "Owner"),
                            ("admin", "Admin"),
                            ("contributor", "Contributor"),
                            ("observer", "Observer"),
                        ],
                        default="contributor",
                        max_length=20,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("accepted", "Accepted"),
                            ("declined", "Declined"),
                            ("expired", "Expired"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                ("responded_at", models.DateTimeField(blank=True, null=True)),
                (
                    "consortium",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="invitations",
                        to="consortiums.consortium",
                    ),
                ),
                (
                    "inviter",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sent_invitations",
                        to="core.company",
                    ),
                ),
                (
                    "invitee_company",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="received_invitations",
                        to="core.company",
                    ),
                ),
            ],
            options={
                "verbose_name": "consortium invitation",
                "verbose_name_plural": "consortium invitations",
            },
        ),
        migrations.AddIndex(
            model_name="consortiuminvitation",
            index=models.Index(fields=["invitee_email"], name="invite_email_idx"),
        ),
        migrations.AddIndex(
            model_name="consortiuminvitation",
            index=models.Index(fields=["status"], name="invite_status_idx"),
        ),
    ]

"""
Initial consortium migration.
"""

import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("core", "0003_add_tiers_webhooks_sharing"),
    ]

    operations = [
        migrations.CreateModel(
            name="Consortium",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="owned_consortiums", to="core.company")),
                ("model_type", models.CharField(
                    choices=[
                        ("linear_regression", "Linear Regression"),
                        ("logistic_regression", "Logistic Regression"),
                        ("decision_tree", "Decision Tree"),
                        ("kmeans", "K-Means"),
                    ],
                    default="linear_regression",
                    max_length=30,
                )),
                ("status", models.CharField(
                    choices=[
                        ("draft", "Draft"),
                        ("active", "Active"),
                        ("training", "Training"),
                        ("completed", "Completed"),
                        ("archived", "Archived"),
                    ],
                    default="draft",
                    max_length=20,
                )),
                ("ml_config", models.JSONField(blank=True, default=dict)),
                ("min_members", models.IntegerField(default=2)),
                ("voting_threshold", models.FloatField(default=0.5)),
                ("voting_duration_days", models.IntegerField(default=7)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "consortium",
                "verbose_name_plural": "consortiums",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["status"], name="consort_status_a1b2c3_idx"),
                    models.Index(fields=["owner"], name="consort_owner_d4e5f6_idx"),
                    models.Index(fields=["created_at"], name="consort_created_g7h8i9_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="ConsortiumMember",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("consortium", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="members", to="consortiums.consortium")),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="consortium_memberships", to="core.company")),
                ("role", models.CharField(
                    choices=[
                        ("owner", "Owner"),
                        ("admin", "Admin"),
                        ("contributor", "Contributor"),
                        ("observer", "Observer"),
                    ],
                    default="contributor",
                    max_length=20,
                )),
                ("status", models.CharField(
                    choices=[
                        ("pending", "Pending"),
                        ("active", "Active"),
                        ("suspended", "Suspended"),
                        ("rejected", "Rejected"),
                        ("left", "Left"),
                        ("removed", "Removed"),
                    ],
                    default="pending",
                    max_length=20,
                )),
                ("joined_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "consortium member",
                "verbose_name_plural": "consortium members",
                "indexes": [
                    models.Index(fields=["consortium", "status"], name="consort_mem_cons_stat_idx"),
                    models.Index(fields=["company"], name="consort_mem_company_idx"),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="consortiummember",
            constraint=models.UniqueConstraint(
                fields=["consortium", "company"],
                name="unique_consortium_company",
            ),
        ),
        migrations.CreateModel(
            name="ContributionProof",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("consortium", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="contribution_proofs", to="consortiums.consortium")),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="contributions", to="core.company")),
                ("record_count", models.IntegerField()),
                ("feature_count", models.IntegerField()),
                ("data_hash", models.CharField(max_length=64, db_index=True)),
                ("checksum", models.CharField(max_length=64)),
                ("verified", models.BooleanField(default=False)),
                ("verified_at", models.DateTimeField(null=True, blank=True)),
                ("blockchain_tx", models.CharField(max_length=66, blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "contribution proof",
                "verbose_name_plural": "contribution proofs",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["consortium", "company"], name="contrib_cons_comp_idx"),
                    models.Index(fields=["data_hash"], name="contrib_data_hash_idx"),
                    models.Index(fields=["verified"], name="contrib_verified_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="ConsortiumInvitation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("consortium", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="invitations", to="consortiums.consortium")),
                ("inviter", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sent_invitations", to="core.company")),
                ("invitee_email", models.EmailField(max_length=254)),
                ("invitee_company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="received_invitations", to="core.company", null=True, blank=True)),
                ("role", models.CharField(
                    choices=[
                        ("owner", "Owner"),
                        ("admin", "Admin"),
                        ("contributor", "Contributor"),
                        ("observer", "Observer"),
                    ],
                    default="contributor",
                    max_length=20,
                )),
                ("status", models.CharField(
                    choices=[
                        ("pending", "Pending"),
                        ("accepted", "Accepted"),
                        ("declined", "Declined"),
                        ("expired", "Expired"),
                    ],
                    default="pending",
                    max_length=20,
                )),
                ("message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                ("responded_at", models.DateTimeField(null=True, blank=True)),
            ],
            options={
                "verbose_name": "consortium invitation",
                "verbose_name_plural": "consortium invitations",
                "indexes": [
                    models.Index(fields=["invitee_email"], name="invite_email_idx"),
                    models.Index(fields=["status"], name="invite_status_idx"),
                ],
            },
        ),
    ]

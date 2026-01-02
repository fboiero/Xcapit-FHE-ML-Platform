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
        # Proposal
        migrations.CreateModel(
            name="Proposal",
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
                    "proposal_type",
                    models.CharField(
                        choices=[
                            ("add_member", "Add Member"),
                            ("remove_member", "Remove Member"),
                            ("change_model", "Change Model"),
                            ("start_training", "Start Training"),
                            ("distribute_rewards", "Distribute Rewards"),
                            ("update_config", "Update Configuration"),
                            ("dissolve", "Dissolve Consortium"),
                        ],
                        max_length=30,
                    ),
                ),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                ("data", models.JSONField(blank=True, default=dict)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("passed", "Passed"),
                            ("rejected", "Rejected"),
                            ("executed", "Executed"),
                            ("cancelled", "Cancelled"),
                            ("expired", "Expired"),
                        ],
                        db_index=True,
                        default="active",
                        max_length=20,
                    ),
                ),
                ("yes_votes", models.IntegerField(default=0)),
                ("no_votes", models.IntegerField(default=0)),
                ("voting_weight_yes", models.FloatField(default=0)),
                ("voting_weight_no", models.FloatField(default=0)),
                ("blockchain_tx", models.CharField(blank=True, max_length=66)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                ("executed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "consortium",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="proposals",
                        to="consortiums.consortium",
                    ),
                ),
                (
                    "proposer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="proposals",
                        to="core.company",
                    ),
                ),
            ],
            options={
                "verbose_name": "proposal",
                "verbose_name_plural": "proposals",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="proposal",
            index=models.Index(
                fields=["consortium", "status"], name="gov_prop_cons_status_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="proposal",
            index=models.Index(fields=["expires_at"], name="gov_prop_expires_idx"),
        ),
        # Vote
        migrations.CreateModel(
            name="Vote",
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
                ("support", models.BooleanField()),
                ("weight", models.IntegerField(default=1)),
                ("comment", models.TextField(blank=True, max_length=500)),
                ("voted_at", models.DateTimeField(auto_now_add=True)),
                (
                    "proposal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="votes",
                        to="governance.proposal",
                    ),
                ),
                (
                    "voter",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="votes",
                        to="core.company",
                    ),
                ),
            ],
            options={
                "verbose_name": "vote",
                "verbose_name_plural": "votes",
                "unique_together": {("proposal", "voter")},
            },
        ),
        migrations.AddIndex(
            model_name="vote",
            index=models.Index(fields=["proposal"], name="gov_vote_proposal_idx"),
        ),
        migrations.AddIndex(
            model_name="vote",
            index=models.Index(fields=["voter"], name="gov_vote_voter_idx"),
        ),
        # AuditEvent
        migrations.CreateModel(
            name="AuditEvent",
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
                    "event_type",
                    models.CharField(
                        choices=[
                            ("consortium_created", "Consortium Created"),
                            ("member_joined", "Member Joined"),
                            ("member_left", "Member Left"),
                            ("member_removed", "Member Removed"),
                            ("data_contributed", "Data Contributed"),
                            ("training_started", "Training Started"),
                            ("training_completed", "Training Completed"),
                            ("proposal_created", "Proposal Created"),
                            ("proposal_voted", "Proposal Voted"),
                            ("proposal_executed", "Proposal Executed"),
                            ("rewards_distributed", "Rewards Distributed"),
                            ("config_updated", "Config Updated"),
                            ("model_deployed", "Model Deployed"),
                            ("compliance_check", "Compliance Check"),
                        ],
                        db_index=True,
                        max_length=50,
                    ),
                ),
                ("target_id", models.CharField(blank=True, max_length=255)),
                ("target_type", models.CharField(blank=True, max_length=50)),
                ("data", models.JSONField(blank=True, default=dict)),
                ("previous_hash", models.CharField(blank=True, max_length=64)),
                ("event_hash", models.CharField(blank=True, db_index=True, max_length=64)),
                ("blockchain_tx", models.CharField(blank=True, max_length=66)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "actor",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="audit_actions",
                        to="core.company",
                    ),
                ),
                (
                    "consortium",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="audit_events",
                        to="consortiums.consortium",
                    ),
                ),
            ],
            options={
                "verbose_name": "audit event",
                "verbose_name_plural": "audit events",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="auditevent",
            index=models.Index(
                fields=["consortium", "event_type"], name="gov_audit_cons_type_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="auditevent",
            index=models.Index(
                fields=["consortium", "created_at"], name="gov_audit_cons_created_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="auditevent",
            index=models.Index(fields=["event_hash"], name="gov_audit_hash_idx"),
        ),
        # RewardDistribution
        migrations.CreateModel(
            name="RewardDistribution",
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
                ("total_amount", models.DecimalField(decimal_places=8, max_digits=20)),
                ("currency", models.CharField(default="ETH", max_length=10)),
                ("distributions", models.JSONField(default=list)),
                ("blockchain_tx", models.CharField(blank=True, max_length=66)),
                ("distributed_at", models.DateTimeField(auto_now_add=True)),
                (
                    "consortium",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reward_distributions",
                        to="consortiums.consortium",
                    ),
                ),
            ],
            options={
                "verbose_name": "reward distribution",
                "verbose_name_plural": "reward distributions",
                "ordering": ["-distributed_at"],
            },
        ),
        migrations.AddIndex(
            model_name="rewarddistribution",
            index=models.Index(fields=["consortium"], name="gov_reward_cons_idx"),
        ),
        migrations.AddIndex(
            model_name="rewarddistribution",
            index=models.Index(fields=["distributed_at"], name="gov_reward_dist_idx"),
        ),
    ]

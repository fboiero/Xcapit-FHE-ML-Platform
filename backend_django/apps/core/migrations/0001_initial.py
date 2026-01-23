# Generated manually for Xcapit FHE-ML Platform
# Django 5.2 LTS

import uuid

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        # Company model (no dependencies)
        migrations.CreateModel(
            name="Company",
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
                ("email", models.EmailField(db_index=True, max_length=254, unique=True)),
                ("industry", models.CharField(blank=True, max_length=100)),
                ("website", models.URLField(blank=True)),
                ("description", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("is_verified", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "company",
                "verbose_name_plural": "companies",
            },
        ),
        migrations.AddIndex(
            model_name="company",
            index=models.Index(fields=["email"], name="core_compan_email_9b1c8a_idx"),
        ),
        migrations.AddIndex(
            model_name="company",
            index=models.Index(fields=["is_active"], name="core_compan_is_acti_5e0b7a_idx"),
        ),
        # User model
        migrations.CreateModel(
            name="User",
            fields=[
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("email", models.EmailField(db_index=True, max_length=254, unique=True)),
                ("first_name", models.CharField(blank=True, max_length=150)),
                ("last_name", models.CharField(blank=True, max_length=150)),
                ("is_active", models.BooleanField(default=True)),
                ("is_staff", models.BooleanField(default=False)),
                (
                    "date_joined",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "company",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="users",
                        to="core.company",
                    ),
                ),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "user",
                "verbose_name_plural": "users",
            },
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(fields=["email"], name="core_user_email_8d7e1a_idx"),
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(fields=["company"], name="core_user_company_3f4b2c_idx"),
        ),
        # APIKey model
        migrations.CreateModel(
            name="APIKey",
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
                    "key_hash",
                    models.CharField(db_index=True, max_length=64, unique=True),
                ),
                ("permissions", models.JSONField(default=list)),
                ("rate_limit", models.IntegerField(default=100)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("last_used_at", models.DateTimeField(blank=True, null=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="api_keys",
                        to="core.company",
                    ),
                ),
            ],
            options={
                "verbose_name": "API key",
                "verbose_name_plural": "API keys",
            },
        ),
        migrations.AddIndex(
            model_name="apikey",
            index=models.Index(fields=["key_hash"], name="core_apikey_key_has_a1b2c3_idx"),
        ),
        migrations.AddIndex(
            model_name="apikey",
            index=models.Index(fields=["company"], name="core_apikey_company_d4e5f6_idx"),
        ),
        migrations.AddIndex(
            model_name="apikey",
            index=models.Index(fields=["is_active"], name="core_apikey_is_acti_g7h8i9_idx"),
        ),
        # AuditLog model
        migrations.CreateModel(
            name="AuditLog",
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
                ("api_key_name", models.CharField(blank=True, max_length=255)),
                ("action", models.CharField(db_index=True, max_length=100)),
                ("resource_type", models.CharField(db_index=True, max_length=100)),
                ("resource_id", models.CharField(blank=True, max_length=255)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.CharField(blank=True, max_length=500)),
                ("request_path", models.CharField(blank=True, max_length=500)),
                ("request_method", models.CharField(blank=True, max_length=10)),
                ("response_status", models.IntegerField(blank=True, null=True)),
                ("extra_data", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "company",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="audit_logs",
                        to="core.company",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="audit_logs",
                        to="core.user",
                    ),
                ),
            ],
            options={
                "verbose_name": "audit log",
                "verbose_name_plural": "audit logs",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(fields=["action"], name="core_auditl_action_j1k2l3_idx"),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(fields=["resource_type"], name="core_auditl_resourc_m4n5o6_idx"),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(fields=["created_at"], name="core_auditl_created_p7q8r9_idx"),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(fields=["company"], name="core_auditl_company_s0t1u2_idx"),
        ),
    ]

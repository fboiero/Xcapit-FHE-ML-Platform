"""
Add trial tracking fields to Company model.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_add_tiers_webhooks_sharing"),
    ]

    operations = [
        migrations.AddField(
            model_name="company",
            name="trial_started_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="company",
            name="trial_expires_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

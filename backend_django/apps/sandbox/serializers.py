"""
Sandbox serializers for Xcapit FHE-ML Platform.
"""

from rest_framework import serializers

from .models import (
    DataUpload,
    Experiment,
    Sandbox,
    SandboxLead,
    SandboxTemplate,
    Subscription,
    SyntheticDataset,
)


# =============================================================================
# SANDBOX LEAD SERIALIZERS (for public sandbox access)
# =============================================================================


class SandboxLeadRequestSerializer(serializers.Serializer):
    """Serializer for requesting sandbox access."""

    email = serializers.EmailField()
    source = serializers.CharField(required=False, allow_blank=True, max_length=50)
    utm_campaign = serializers.CharField(required=False, allow_blank=True, max_length=100)
    utm_source = serializers.CharField(required=False, allow_blank=True, max_length=100)
    utm_medium = serializers.CharField(required=False, allow_blank=True, max_length=100)


class SandboxLeadResponseSerializer(serializers.ModelSerializer):
    """Serializer for sandbox access response."""

    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = SandboxLead
        fields = [
            "token",
            "email",
            "expires_at",
            "is_valid",
            "created_at",
        ]
        read_only_fields = fields


class SandboxLeadVerifySerializer(serializers.Serializer):
    """Serializer for verifying sandbox token."""

    token = serializers.CharField(max_length=64)


# =============================================================================
# SANDBOX TEMPLATE SERIALIZERS
# =============================================================================


class SandboxTemplateSerializer(serializers.ModelSerializer):
    """Serializer for SandboxTemplate."""

    class Meta:
        model = SandboxTemplate
        fields = [
            "id",
            "name",
            "description",
            "industry",
            "template_type",
            "datasets",
            "experiments",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class SandboxSerializer(serializers.ModelSerializer):
    """Serializer for Sandbox."""

    owner_name = serializers.CharField(source="owner.name", read_only=True)
    template_name = serializers.CharField(source="template.name", read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    dataset_count = serializers.IntegerField(read_only=True)
    experiment_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Sandbox
        fields = [
            "id",
            "name",
            "description",
            "owner",
            "owner_name",
            "template",
            "template_name",
            "industry",
            "config",
            "status",
            "is_expired",
            "dataset_count",
            "experiment_count",
            "created_at",
            "expires_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "owner",
            "status",
            "created_at",
            "updated_at",
        ]


class SandboxCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Sandbox."""

    class Meta:
        model = Sandbox
        fields = [
            "name",
            "description",
            "template",
            "industry",
            "config",
            "expires_at",
        ]

    def create(self, validated_data):
        """Create sandbox with owner."""
        owner = self.context["request"].user.company
        return Sandbox.objects.create(owner=owner, **validated_data)


class SyntheticDatasetSerializer(serializers.ModelSerializer):
    """Serializer for SyntheticDataset."""

    sandbox_name = serializers.CharField(source="sandbox.name", read_only=True)

    class Meta:
        model = SyntheticDataset
        fields = [
            "id",
            "sandbox",
            "sandbox_name",
            "name",
            "description",
            "dataset_type",
            "industry",
            "record_count",
            "feature_count",
            "features",
            "statistics",
            "data_preview",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "statistics",
            "data_preview",
            "created_at",
        ]


class SyntheticDatasetCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating SyntheticDataset."""

    class Meta:
        model = SyntheticDataset
        fields = [
            "sandbox",
            "name",
            "description",
            "dataset_type",
            "industry",
            "record_count",
            "feature_count",
            "features",
        ]

    def validate_record_count(self, value):
        """Limit record count."""
        if value > 100000:
            raise serializers.ValidationError("Maximum 100,000 records allowed.")
        return value


class ExperimentSerializer(serializers.ModelSerializer):
    """Serializer for Experiment."""

    sandbox_name = serializers.CharField(source="sandbox.name", read_only=True)
    dataset_name = serializers.CharField(source="dataset.name", read_only=True)

    class Meta:
        model = Experiment
        fields = [
            "id",
            "sandbox",
            "sandbox_name",
            "name",
            "description",
            "experiment_type",
            "model_type",
            "dataset",
            "dataset_name",
            "config",
            "status",
            "results",
            "error_message",
            "created_at",
            "started_at",
            "completed_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "results",
            "error_message",
            "created_at",
            "started_at",
            "completed_at",
        ]


class ExperimentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Experiment."""

    class Meta:
        model = Experiment
        fields = [
            "sandbox",
            "name",
            "description",
            "experiment_type",
            "model_type",
            "dataset",
            "config",
        ]

    def validate(self, attrs):
        """Validate experiment configuration."""
        sandbox = attrs["sandbox"]
        dataset = attrs.get("dataset")

        # Check sandbox is active
        if sandbox.is_expired or sandbox.status != Sandbox.Status.ACTIVE:
            raise serializers.ValidationError("Sandbox is not active.")

        # Check dataset belongs to sandbox
        if dataset and dataset.sandbox != sandbox:
            raise serializers.ValidationError("Dataset does not belong to this sandbox.")

        return attrs


class GenerateDataSerializer(serializers.Serializer):
    """Serializer for generating synthetic data."""

    dataset_type = serializers.ChoiceField(choices=SyntheticDataset.DatasetType.choices)
    record_count = serializers.IntegerField(min_value=100, max_value=100000)
    industry = serializers.CharField(required=False, allow_blank=True)
    features = serializers.ListField(
        child=serializers.DictField(),
        required=False,
    )


# =============================================================================
# TRIAL / SUBSCRIPTION SERIALIZERS
# =============================================================================


class SubscriptionSerializer(serializers.ModelSerializer):
    """Read-only subscription info."""

    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "id",
            "company",
            "company_name",
            "plan",
            "status",
            "trial_end",
            "current_period_start",
            "current_period_end",
            "cancel_at_period_end",
            "created_at",
        ]
        read_only_fields = fields


class TrialStartSerializer(serializers.Serializer):
    """Input for starting a trial (no fields needed — uses request.user.company)."""

    pass


class TrialUpgradeSerializer(serializers.Serializer):
    """Input for requesting an upgrade."""

    target_tier = serializers.ChoiceField(
        choices=["starter", "professional", "enterprise"],
    )


class DataUploadSerializer(serializers.ModelSerializer):
    """Read-only data upload record."""

    class Meta:
        model = DataUpload
        fields = [
            "id",
            "company",
            "consortium",
            "file_name",
            "file_size",
            "record_count",
            "feature_count",
            "status",
            "error_message",
            "created_at",
        ]
        read_only_fields = fields


class TrialDataUploadSerializer(serializers.Serializer):
    """Input for uploading data to a consortium within trial limits."""

    consortium_id = serializers.UUIDField()
    file = serializers.FileField()


class TrialUsageSerializer(serializers.Serializer):
    """Output for trial usage summary."""

    tier = serializers.CharField()
    is_trial = serializers.BooleanField()
    trial_days_remaining = serializers.IntegerField()
    trial_expired = serializers.BooleanField()
    usage = serializers.DictField()
    limits = serializers.DictField()


class PlanComparisonSerializer(serializers.Serializer):
    """Output for plan comparison."""

    tier = serializers.CharField()
    name = serializers.CharField()
    rate_limit_rpm = serializers.IntegerField()
    daily_requests = serializers.IntegerField()
    max_models = serializers.IntegerField()
    max_consortiums = serializers.IntegerField()
    max_upload_mb = serializers.FloatField()
    training_runs_per_day = serializers.IntegerField()
    max_sandboxes = serializers.IntegerField()

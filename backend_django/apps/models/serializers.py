"""
ML Model serializers for Xcapit FHE-ML Platform.
"""

from rest_framework import serializers

from .models import (
    BatchPredictionJob,
    MLModel,
    ModelCheckpoint,
    ModelExport,
    ModelShare,
    ModelShareRequest,
    ModelVersion,
    PredictionLog,
    TrainingRun,
)


class MLModelSerializer(serializers.ModelSerializer):
    """Serializer for MLModel."""

    owner_name = serializers.CharField(source="owner.name", read_only=True)
    consortium_name = serializers.CharField(source="consortium.name", read_only=True)

    class Meta:
        model = MLModel
        fields = [
            "id",
            "name",
            "model_type",
            "status",
            "config",
            "n_features",
            "feature_names",
            "trained_at",
            "training_epochs",
            "final_loss",
            "consortium",
            "consortium_name",
            "owner",
            "owner_name",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "trained_at",
            "training_epochs",
            "final_loss",
            "created_at",
            "updated_at",
        ]


class MLModelCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating MLModel."""

    class Meta:
        model = MLModel
        fields = [
            "name",
            "model_type",
            "config",
            "n_features",
            "feature_names",
            "consortium",
            "metadata",
        ]

    def validate_config(self, value):
        """Validate model configuration."""
        allowed_keys = {
            # General training
            "learning_rate",
            "epochs",
            "batch_size",
            "regularization",
            # Tree-based
            "max_depth",
            "n_estimators",
            "min_samples_split",
            "min_samples_leaf",
            # Clustering
            "n_clusters",
            # Neural networks
            "hidden_layers",
            "activation",
            "dropout",
            # SVM
            "kernel",
            "C",
            "gamma",
            "nu",
            # Naive Bayes
            "var_smoothing",
            # PCA
            "n_components",
            "whiten",
            # Anomaly detection
            "contamination",
            "n_neighbors",
            "max_samples",
            # Time series
            "order",  # ARIMA (p, d, q)
            "seasonal_order",  # ARIMA seasonal
            "alpha",  # Exponential smoothing
            "beta",  # Trend smoothing
            "gamma_seasonal",  # Seasonal smoothing
            "window_size",  # Moving average
            "yearly_seasonality",
            "weekly_seasonality",
            "daily_seasonality",
            # Regularization
            "alpha_reg",  # Ridge/Lasso alpha
            "l1_ratio",  # ElasticNet
            "fit_intercept",
            "max_iter",
            "tol",
            # Ensemble
            "voting",  # hard/soft
            "weights",
            "estimators",
            # Feature selection
            "k",  # SelectKBest
            "percentile",
            "threshold",
            "score_func",
        }
        for key in value.keys():
            if key not in allowed_keys:
                raise serializers.ValidationError(f"Invalid config key: {key}")
        return value

    def create(self, validated_data):
        """Create model with owner."""
        owner = self.context["request"].user.company
        return MLModel.objects.create(owner=owner, **validated_data)


class TrainingRunSerializer(serializers.ModelSerializer):
    """Serializer for TrainingRun."""

    duration_seconds = serializers.FloatField(read_only=True)

    class Meta:
        model = TrainingRun
        fields = [
            "id",
            "model",
            "status",
            "epochs_completed",
            "epochs_total",
            "current_loss",
            "final_loss",
            "metrics",
            "error_message",
            "started_at",
            "completed_at",
            "created_at",
            "duration_seconds",
        ]
        read_only_fields = fields


class TrainingRunCreateSerializer(serializers.ModelSerializer):
    """Serializer for starting a training run."""

    class Meta:
        model = TrainingRun
        fields = ["model", "epochs_total"]


class PredictionLogSerializer(serializers.ModelSerializer):
    """Serializer for PredictionLog."""

    model_name = serializers.CharField(source="model.name", read_only=True)
    requester_name = serializers.CharField(source="requester.name", read_only=True)

    class Meta:
        model = PredictionLog
        fields = [
            "id",
            "model",
            "model_name",
            "requester",
            "requester_name",
            "n_samples",
            "encrypted",
            "latency_ms",
            "api_key_name",
            "timestamp",
        ]
        read_only_fields = fields


class ModelCheckpointSerializer(serializers.ModelSerializer):
    """Serializer for ModelCheckpoint."""

    class Meta:
        model = ModelCheckpoint
        fields = [
            "id",
            "model",
            "epoch",
            "loss",
            "weights_hash",
            "blockchain_tx",
            "created_at",
        ]
        read_only_fields = fields


class PredictRequestSerializer(serializers.Serializer):
    """Serializer for prediction requests."""

    model_id = serializers.UUIDField()
    data = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField()),
        min_length=1,
        max_length=10000,
    )
    encrypted = serializers.BooleanField(default=False)


class PredictResponseSerializer(serializers.Serializer):
    """Serializer for prediction responses."""

    model_id = serializers.UUIDField()
    predictions = serializers.ListField(child=serializers.FloatField())
    encrypted = serializers.BooleanField()
    latency_ms = serializers.FloatField()


class ModelStatsSerializer(serializers.Serializer):
    """Serializer for model statistics."""

    total_predictions = serializers.IntegerField()
    total_samples = serializers.IntegerField()
    avg_latency_ms = serializers.FloatField()
    encrypted_predictions = serializers.IntegerField()


# Model Versioning Serializers


class ModelVersionSerializer(serializers.ModelSerializer):
    """Serializer for ModelVersion."""

    model_name = serializers.CharField(source="model.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.name", read_only=True)

    class Meta:
        model = ModelVersion
        fields = [
            "id",
            "model",
            "model_name",
            "version",
            "major",
            "minor",
            "patch",
            "status",
            "metrics",
            "training_metrics",
            "changelog",
            "release_notes",
            "created_by",
            "created_by_name",
            "created_at",
            "published_at",
        ]
        read_only_fields = [
            "id",
            "model",
            "version",
            "major",
            "minor",
            "patch",
            "created_at",
            "published_at",
        ]


class CreateVersionSerializer(serializers.Serializer):
    """Serializer for creating a new version."""

    bump_type = serializers.ChoiceField(
        choices=["major", "minor", "patch"],
        default="patch",
    )
    changelog = serializers.CharField(required=False, allow_blank=True, default="")
    release_notes = serializers.CharField(required=False, allow_blank=True, default="")


# Batch Prediction Serializers


class BatchPredictionJobSerializer(serializers.ModelSerializer):
    """Serializer for BatchPredictionJob."""

    model_name = serializers.CharField(source="model.name", read_only=True)
    requester_name = serializers.CharField(source="requester.name", read_only=True)

    class Meta:
        model = BatchPredictionJob
        fields = [
            "id",
            "model",
            "model_name",
            "requester",
            "requester_name",
            "status",
            "priority",
            "n_samples",
            "encrypted",
            "samples_processed",
            "progress_percent",
            "total_latency_ms",
            "avg_latency_per_sample_ms",
            "error_message",
            "created_at",
            "started_at",
            "completed_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "n_samples",
            "samples_processed",
            "progress_percent",
            "total_latency_ms",
            "avg_latency_per_sample_ms",
            "error_message",
            "created_at",
            "started_at",
            "completed_at",
        ]


class BatchPredictRequestSerializer(serializers.Serializer):
    """Serializer for batch prediction requests."""

    model_id = serializers.UUIDField()
    data = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField()),
        min_length=1,
        max_length=100000,  # Higher limit for batch
    )
    encrypted = serializers.BooleanField(default=False)
    priority = serializers.ChoiceField(
        choices=["low", "normal", "high"],
        default="normal",
    )
    async_mode = serializers.BooleanField(default=True)


class BatchPredictResponseSerializer(serializers.Serializer):
    """Serializer for batch prediction responses."""

    job_id = serializers.UUIDField()
    model_id = serializers.UUIDField()
    status = serializers.CharField()
    n_samples = serializers.IntegerField()
    predictions = serializers.ListField(
        child=serializers.FloatField(),
        required=False,
    )
    encrypted = serializers.BooleanField()
    total_latency_ms = serializers.FloatField(required=False)


# Model Export/Import Serializers


class ModelExportSerializer(serializers.ModelSerializer):
    """Serializer for ModelExport."""

    model_name = serializers.CharField(source="model.name", read_only=True)
    version_str = serializers.CharField(source="version.version", read_only=True)
    exported_by_name = serializers.CharField(source="exported_by.name", read_only=True)

    class Meta:
        model = ModelExport
        fields = [
            "id",
            "model",
            "model_name",
            "version",
            "version_str",
            "format",
            "file_size_bytes",
            "checksum_sha256",
            "include_weights",
            "include_config",
            "include_metadata",
            "exported_by",
            "exported_by_name",
            "created_at",
            "expires_at",
        ]
        read_only_fields = fields


class ExportRequestSerializer(serializers.Serializer):
    """Serializer for export requests."""

    format = serializers.ChoiceField(
        choices=["fheml_json", "fheml_binary", "onnx_compatible"],
        default="fheml_json",
    )
    include_weights = serializers.BooleanField(default=True)
    include_config = serializers.BooleanField(default=True)
    include_metadata = serializers.BooleanField(default=True)
    version_id = serializers.UUIDField(required=False, allow_null=True)


class ExportDataSerializer(serializers.Serializer):
    """Serializer for exported model data."""

    fheml_version = serializers.CharField()
    model = serializers.DictField()
    config = serializers.DictField()
    metadata = serializers.DictField()
    training = serializers.DictField()
    params = serializers.DictField(required=False)
    version = serializers.DictField(required=False)


class ImportRequestSerializer(serializers.Serializer):
    """Serializer for import requests."""

    export_data = serializers.DictField()
    new_name = serializers.CharField(required=False, allow_blank=True)
    consortium_id = serializers.UUIDField(required=False, allow_null=True)


class ImportResponseSerializer(serializers.Serializer):
    """Serializer for import responses."""

    model_id = serializers.UUIDField()
    name = serializers.CharField()
    model_type = serializers.CharField()
    status = serializers.CharField()
    imported_from_version = serializers.CharField(required=False)


# Model Sharing Serializers


class ModelShareSerializer(serializers.ModelSerializer):
    """Serializer for ModelShare."""

    model_name = serializers.CharField(source="model.name", read_only=True)
    source_consortium_name = serializers.CharField(source="source_consortium.name", read_only=True)
    target_consortium_name = serializers.CharField(source="target_consortium.name", read_only=True)
    shared_by_name = serializers.CharField(source="shared_by.name", read_only=True)
    approved_by_name = serializers.CharField(source="approved_by.name", read_only=True)
    version_str = serializers.CharField(source="version.version", read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    can_predict = serializers.BooleanField(read_only=True)
    can_retrain = serializers.BooleanField(read_only=True)

    class Meta:
        model = ModelShare
        fields = [
            "id",
            "model",
            "model_name",
            "source_consortium",
            "source_consortium_name",
            "target_consortium",
            "target_consortium_name",
            "shared_by",
            "shared_by_name",
            "approved_by",
            "approved_by_name",
            "share_type",
            "status",
            "version",
            "version_str",
            "revenue_share_percent",
            "max_predictions",
            "predictions_used",
            "terms",
            "requires_approval",
            "valid_from",
            "valid_until",
            "request_message",
            "approval_message",
            "blockchain_tx",
            "is_active",
            "can_predict",
            "can_retrain",
            "created_at",
            "approved_at",
            "revoked_at",
        ]
        read_only_fields = [
            "id",
            "source_consortium",
            "shared_by",
            "approved_by",
            "status",
            "predictions_used",
            "blockchain_tx",
            "created_at",
            "approved_at",
            "revoked_at",
        ]


class ModelShareCreateSerializer(serializers.Serializer):
    """Serializer for creating a model share."""

    model_id = serializers.UUIDField()
    target_consortium_id = serializers.UUIDField()
    share_type = serializers.ChoiceField(
        choices=["full_access", "prediction_only", "read_only"],
        default="prediction_only",
    )
    version_id = serializers.UUIDField(required=False, allow_null=True)
    revenue_share_percent = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        min_value=0,
        max_value=100,
    )
    max_predictions = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1,
    )
    terms = serializers.CharField(required=False, allow_blank=True, default="")
    requires_approval = serializers.BooleanField(default=True)
    valid_until = serializers.DateTimeField(required=False, allow_null=True)
    request_message = serializers.CharField(required=False, allow_blank=True, default="")


class ModelShareApprovalSerializer(serializers.Serializer):
    """Serializer for approving/rejecting a share."""

    action = serializers.ChoiceField(choices=["approve", "reject"])
    message = serializers.CharField(required=False, allow_blank=True, default="")


class ModelShareRevokeSerializer(serializers.Serializer):
    """Serializer for revoking a share."""

    message = serializers.CharField(required=False, allow_blank=True, default="")


class ModelShareRequestSerializer(serializers.ModelSerializer):
    """Serializer for ModelShareRequest."""

    model_name = serializers.CharField(source="model.name", read_only=True)
    model_type = serializers.CharField(source="model.model_type", read_only=True)
    model_owner_name = serializers.CharField(source="model.owner.name", read_only=True)
    requesting_consortium_name = serializers.CharField(
        source="requesting_consortium.name", read_only=True
    )
    requested_by_name = serializers.CharField(source="requested_by.name", read_only=True)

    class Meta:
        model = ModelShareRequest
        fields = [
            "id",
            "model",
            "model_name",
            "model_type",
            "model_owner_name",
            "requesting_consortium",
            "requesting_consortium_name",
            "requested_by",
            "requested_by_name",
            "requested_share_type",
            "message",
            "proposed_revenue_share",
            "status",
            "response_message",
            "resulting_share",
            "created_at",
            "responded_at",
        ]
        read_only_fields = [
            "id",
            "model",
            "requesting_consortium",
            "requested_by",
            "status",
            "response_message",
            "resulting_share",
            "created_at",
            "responded_at",
        ]


class ModelShareRequestCreateSerializer(serializers.Serializer):
    """Serializer for creating a share request."""

    model_id = serializers.UUIDField()
    requested_share_type = serializers.ChoiceField(
        choices=["full_access", "prediction_only", "read_only"],
        default="prediction_only",
    )
    message = serializers.CharField(required=False, allow_blank=True, default="")
    proposed_revenue_share = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        allow_null=True,
        min_value=0,
        max_value=100,
    )


class ModelShareRequestResponseSerializer(serializers.Serializer):
    """Serializer for responding to a share request."""

    action = serializers.ChoiceField(choices=["approve", "reject"])
    message = serializers.CharField(required=False, allow_blank=True, default="")
    share_type = serializers.ChoiceField(
        choices=["full_access", "prediction_only", "read_only"],
        required=False,
    )
    revenue_share_percent = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        min_value=0,
        max_value=100,
    )
    max_predictions = serializers.IntegerField(required=False, allow_null=True)
    valid_until = serializers.DateTimeField(required=False, allow_null=True)

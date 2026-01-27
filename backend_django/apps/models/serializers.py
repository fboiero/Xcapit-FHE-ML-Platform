"""
ML Model serializers for Xcapit FHE-ML Platform.
"""

from rest_framework import serializers

from .models import MLModel, ModelCheckpoint, PredictionLog, TrainingRun


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

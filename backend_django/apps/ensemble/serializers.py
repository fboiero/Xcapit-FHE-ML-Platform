"""
Ensemble serializers for Xcapit FHE-ML Platform.
"""

from rest_framework import serializers

from .models import Ensemble, EnsembleEvaluation, EnsembleModel, EnsemblePrediction


class EnsembleModelSerializer(serializers.ModelSerializer):
    """Serializer for EnsembleModel."""

    model_name = serializers.CharField(source="model.name", read_only=True)
    model_type = serializers.CharField(source="model.model_type", read_only=True)

    class Meta:
        model = EnsembleModel
        fields = [
            "id",
            "model",
            "model_name",
            "model_type",
            "weight",
            "individual_accuracy",
            "contribution_score",
            "is_active",
            "added_at",
        ]
        read_only_fields = ["id", "individual_accuracy", "contribution_score", "added_at"]


class EnsembleSerializer(serializers.ModelSerializer):
    """Serializer for Ensemble model."""

    owner_name = serializers.CharField(source="owner.name", read_only=True)
    models = EnsembleModelSerializer(source="ensemble_models", many=True, read_only=True)
    model_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Ensemble
        fields = [
            "id",
            "name",
            "description",
            "owner",
            "owner_name",
            "ensemble_type",
            "status",
            "aggregation_config",
            "accuracy",
            "f1_score",
            "ensemble_improvement",
            "model_count",
            "models",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "owner",
            "accuracy",
            "f1_score",
            "ensemble_improvement",
            "created_at",
            "updated_at",
        ]


class EnsembleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Ensemble."""

    class Meta:
        model = Ensemble
        fields = ["name", "description", "ensemble_type", "aggregation_config"]

    def create(self, validated_data):
        user = self.context["request"].user
        validated_data["owner"] = user.company
        return Ensemble.objects.create(**validated_data)


class AddModelSerializer(serializers.Serializer):
    """Serializer for adding a model to an ensemble."""

    model_id = serializers.UUIDField()
    weight = serializers.FloatField(default=1.0, min_value=0.0, max_value=10.0)


class EnsemblePredictionSerializer(serializers.ModelSerializer):
    """Serializer for EnsemblePrediction."""

    ensemble_name = serializers.CharField(source="ensemble.name", read_only=True)

    class Meta:
        model = EnsemblePrediction
        fields = [
            "id",
            "ensemble",
            "ensemble_name",
            "n_samples",
            "prediction",
            "confidence",
            "model_predictions",
            "latency_ms",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class PredictRequestSerializer(serializers.Serializer):
    """Serializer for ensemble prediction request."""

    X = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField()),
        help_text="Feature matrix for prediction",
    )


class EnsembleEvaluationSerializer(serializers.ModelSerializer):
    """Serializer for EnsembleEvaluation."""

    class Meta:
        model = EnsembleEvaluation
        fields = [
            "id",
            "ensemble",
            "accuracy",
            "precision",
            "recall",
            "f1_score",
            "auc_roc",
            "best_individual_accuracy",
            "improvement_over_best",
            "test_samples",
            "evaluated_at",
        ]
        read_only_fields = ["id", "evaluated_at"]

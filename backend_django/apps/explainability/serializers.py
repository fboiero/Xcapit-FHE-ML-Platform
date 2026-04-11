"""
Explainability serializers for Xcapit FHE-ML Platform.
"""

from rest_framework import serializers

from apps.consortiums.models import ConsortiumMember

from .models import ExplanationRequest, FeatureImportance, ModelInsight


class ExplanationRequestSerializer(serializers.ModelSerializer):
    """Serializer for ExplanationRequest model."""

    consortium_name = serializers.CharField(source="consortium.name", read_only=True)
    requester_name = serializers.CharField(source="requester.name", read_only=True)

    class Meta:
        model = ExplanationRequest
        fields = [
            "id",
            "consortium",
            "consortium_name",
            "requester",
            "requester_name",
            "model",
            "explanation_type",
            "input_data",
            "prediction_id",
            "status",
            "error_message",
            "explanation",
            "created_at",
            "completed_at",
        ]
        read_only_fields = [
            "id",
            "requester",
            "status",
            "error_message",
            "explanation",
            "created_at",
            "completed_at",
        ]


class ExplanationRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating ExplanationRequest."""

    class Meta:
        model = ExplanationRequest
        fields = [
            "id",
            "consortium",
            "model",
            "explanation_type",
            "input_data",
            "prediction_id",
            "status",
            "explanation",
        ]
        read_only_fields = [
            "id",
            "status",
            "explanation",
        ]

    def validate_consortium(self, value):
        """SECURITY: Verify user is a member of the target consortium."""
        user = self.context["request"].user
        company = user.company

        is_owner = value.owner_id == company.id
        is_member = ConsortiumMember.objects.filter(
            consortium=value,
            company=company,
            status="active",
        ).exists()
        if not is_owner and not is_member:
            raise serializers.ValidationError(
                "You are not a member of this consortium."
            )
        return value

    def create(self, validated_data):
        user = self.context["request"].user
        validated_data["requester"] = user.company
        return ExplanationRequest.objects.create(**validated_data)


class FeatureImportanceSerializer(serializers.ModelSerializer):
    """Serializer for FeatureImportance model."""

    class Meta:
        model = FeatureImportance
        fields = [
            "id",
            "consortium",
            "model",
            "feature_name",
            "importance_score",
            "importance_rank",
            "computation_method",
            "std_deviation",
            "computed_at",
        ]
        read_only_fields = ["id", "computed_at"]


class ModelInsightSerializer(serializers.ModelSerializer):
    """Serializer for ModelInsight model."""

    consortium_name = serializers.CharField(source="consortium.name", read_only=True)
    acknowledged_by_name = serializers.CharField(
        source="acknowledged_by.get_full_name",
        read_only=True,
    )

    class Meta:
        model = ModelInsight
        fields = [
            "id",
            "consortium",
            "consortium_name",
            "insight_type",
            "title",
            "description",
            "severity",
            "data",
            "recommendations",
            "is_active",
            "acknowledged",
            "acknowledged_by",
            "acknowledged_by_name",
            "acknowledged_at",
            "created_at",
            "expires_at",
        ]
        read_only_fields = [
            "id",
            "acknowledged_by",
            "acknowledged_at",
            "created_at",
        ]


class ExplainabilityDashboardSerializer(serializers.Serializer):
    """Serializer for explainability dashboard."""

    total_requests = serializers.IntegerField()
    pending_requests = serializers.IntegerField()
    top_features = FeatureImportanceSerializer(many=True)
    active_insights = ModelInsightSerializer(many=True)
    recent_explanations = ExplanationRequestSerializer(many=True)

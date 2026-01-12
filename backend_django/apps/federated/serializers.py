"""
Federated inference serializers for Xcapit FHE-ML Platform.
"""

from rest_framework import serializers

from .models import EdgeNode, FederatedModel, InferenceEndpoint, InferenceRequest, InferenceResult


class InferenceEndpointSerializer(serializers.ModelSerializer):
    """Serializer for InferenceEndpoint."""

    consortium_name = serializers.CharField(source="consortium.name", read_only=True)
    company_name = serializers.CharField(source="company.name", read_only=True)
    model_name = serializers.CharField(source="model.name", read_only=True)
    avg_latency_ms = serializers.FloatField(read_only=True)

    class Meta:
        model = InferenceEndpoint
        fields = [
            "id",
            "consortium",
            "consortium_name",
            "company",
            "company_name",
            "name",
            "description",
            "model",
            "model_name",
            "endpoint_type",
            "status",
            "config",
            "url",
            "request_count",
            "total_latency_ms",
            "avg_latency_ms",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "company",
            "status",
            "url",
            "request_count",
            "total_latency_ms",
            "created_at",
            "updated_at",
        ]


class InferenceEndpointCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating InferenceEndpoint."""

    class Meta:
        model = InferenceEndpoint
        fields = [
            "consortium",
            "name",
            "description",
            "model",
            "endpoint_type",
            "config",
        ]

    def create(self, validated_data):
        """Create endpoint with company."""
        company = self.context["request"].user.company
        return InferenceEndpoint.objects.create(company=company, **validated_data)


class InferenceRequestSerializer(serializers.ModelSerializer):
    """Serializer for InferenceRequest."""

    endpoint_name = serializers.CharField(source="endpoint.name", read_only=True)
    requester_name = serializers.CharField(source="requester.name", read_only=True)

    class Meta:
        model = InferenceRequest
        fields = [
            "id",
            "endpoint",
            "endpoint_name",
            "requester",
            "requester_name",
            "status",
            "priority",
            "input_hash",
            "encryption_key_id",
            "latency_ms",
            "created_at",
            "started_at",
            "completed_at",
        ]
        read_only_fields = fields


class InferenceRequestCreateSerializer(serializers.Serializer):
    """Serializer for creating inference request."""

    endpoint_id = serializers.UUIDField()
    input_data = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField()),
        min_length=1,
    )
    priority = serializers.ChoiceField(
        choices=InferenceRequest.Priority.choices,
        default=InferenceRequest.Priority.NORMAL,
    )
    encryption_key_id = serializers.CharField(required=False, allow_blank=True)


class InferenceResultSerializer(serializers.ModelSerializer):
    """Serializer for InferenceResult."""

    class Meta:
        model = InferenceResult
        fields = [
            "id",
            "request",
            "encrypted_output",
            "output_metadata",
            "confidence_scores",
            "created_at",
        ]
        read_only_fields = fields


class FederatedModelSerializer(serializers.ModelSerializer):
    """Serializer for FederatedModel."""

    consortium_name = serializers.CharField(source="consortium.name", read_only=True)
    deployment_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = FederatedModel
        fields = [
            "id",
            "consortium",
            "consortium_name",
            "name",
            "description",
            "model_type",
            "version",
            "status",
            "config",
            "metrics",
            "deployment_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "metrics",
            "created_at",
            "updated_at",
        ]


class FederatedModelCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating FederatedModel."""

    class Meta:
        model = FederatedModel
        fields = [
            "consortium",
            "name",
            "description",
            "model_type",
            "version",
            "config",
        ]


class EdgeNodeSerializer(serializers.ModelSerializer):
    """Serializer for EdgeNode."""

    company_name = serializers.CharField(source="company.name", read_only=True)
    is_online = serializers.BooleanField(read_only=True)
    deployed_model_ids = serializers.PrimaryKeyRelatedField(
        queryset=FederatedModel.objects.all(),
        many=True,
        source="deployed_models",
        write_only=True,
        required=False,
    )
    deployed_models_info = FederatedModelSerializer(
        source="deployed_models",
        many=True,
        read_only=True,
    )

    class Meta:
        model = EdgeNode
        fields = [
            "id",
            "company",
            "company_name",
            "name",
            "node_type",
            "location",
            "status",
            "capabilities",
            "deployed_model_ids",
            "deployed_models_info",
            "last_heartbeat",
            "is_online",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "company",
            "status",
            "last_heartbeat",
            "created_at",
            "updated_at",
        ]


class EdgeNodeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating EdgeNode."""

    class Meta:
        model = EdgeNode
        fields = [
            "name",
            "node_type",
            "location",
            "capabilities",
        ]

    def create(self, validated_data):
        """Create edge node with company."""
        company = self.context["request"].user.company
        return EdgeNode.objects.create(company=company, **validated_data)


class DeployModelSerializer(serializers.Serializer):
    """Serializer for deploying model to edge node."""

    model_id = serializers.UUIDField()


class InferencePredictSerializer(serializers.Serializer):
    """Serializer for prediction response."""

    request_id = serializers.UUIDField()
    encrypted_output = serializers.CharField()
    latency_ms = serializers.FloatField()
    metadata = serializers.DictField()

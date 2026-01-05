"""
Marketplace serializers for Xcapit FHE-ML Platform.
"""

from rest_framework import serializers

from .models import Category, Deployment, MarketplaceModel, Review


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category."""

    model_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "description",
            "icon",
            "order",
            "model_count",
        ]


class MarketplaceModelSerializer(serializers.ModelSerializer):
    """Serializer for MarketplaceModel."""

    category_name = serializers.CharField(source="category.name", read_only=True)
    rating = serializers.FloatField(read_only=True)
    rating_count = serializers.IntegerField(read_only=True)
    industry = serializers.CharField(read_only=True)

    class Meta:
        model = MarketplaceModel
        fields = [
            "id",
            "name",
            "description",
            "category",
            "category_name",
            "model_type",
            "version",
            "accuracy",
            "training_samples",
            "features",
            "use_cases",
            "pricing_type",
            "price",
            "is_active",
            "is_featured",
            "downloads",
            "rating",
            "rating_count",
            "industry",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "downloads",
            "created_at",
            "updated_at",
        ]


class MarketplaceModelListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing models."""

    category_name = serializers.CharField(source="category.name", read_only=True)
    rating = serializers.FloatField(read_only=True)
    rating_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = MarketplaceModel
        fields = [
            "id",
            "name",
            "category",
            "category_name",
            "model_type",
            "accuracy",
            "pricing_type",
            "price",
            "is_featured",
            "downloads",
            "rating",
            "rating_count",
        ]


class DeploymentSerializer(serializers.ModelSerializer):
    """Serializer for Deployment."""

    model_name = serializers.CharField(source="marketplace_model.name", read_only=True)
    consortium_name = serializers.CharField(source="consortium.name", read_only=True)
    deployed_by_name = serializers.CharField(source="deployed_by.name", read_only=True)

    class Meta:
        model = Deployment
        fields = [
            "id",
            "marketplace_model",
            "model_name",
            "consortium",
            "consortium_name",
            "deployed_by",
            "deployed_by_name",
            "status",
            "config",
            "deployed_at",
            "removed_at",
        ]
        read_only_fields = [
            "id",
            "deployed_by",
            "deployed_at",
            "removed_at",
        ]


class DeploymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Deployment."""

    class Meta:
        model = Deployment
        fields = [
            "marketplace_model",
            "consortium",
            "config",
        ]

    def validate(self, attrs):
        """Check if model is active and not already deployed."""
        model = attrs["marketplace_model"]
        consortium = attrs["consortium"]

        if not model.is_active:
            raise serializers.ValidationError("Model is not active.")

        if Deployment.objects.filter(
            marketplace_model=model,
            consortium=consortium,
            status__in=[Deployment.Status.PENDING, Deployment.Status.ACTIVE],
        ).exists():
            raise serializers.ValidationError("Model already deployed to this consortium.")

        return attrs

    def create(self, validated_data):
        """Create deployment and increment downloads."""
        deployed_by = self.context["request"].user.company
        deployment = Deployment.objects.create(deployed_by=deployed_by, **validated_data)

        # Increment downloads
        model = validated_data["marketplace_model"]
        model.downloads += 1
        model.save(update_fields=["downloads"])

        return deployment


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for Review."""

    model_name = serializers.CharField(source="marketplace_model.name", read_only=True)
    reviewer_name = serializers.CharField(source="reviewer.name", read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "marketplace_model",
            "model_name",
            "reviewer",
            "reviewer_name",
            "consortium",
            "rating",
            "title",
            "comment",
            "helpful_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "reviewer",
            "helpful_count",
            "created_at",
            "updated_at",
        ]


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Review."""

    class Meta:
        model = Review
        fields = [
            "marketplace_model",
            "consortium",
            "rating",
            "title",
            "comment",
        ]

    def validate(self, attrs):
        """Check if user has deployed the model."""
        model = attrs["marketplace_model"]
        reviewer = self.context["request"].user.company

        # Check if already reviewed
        if Review.objects.filter(marketplace_model=model, reviewer=reviewer).exists():
            raise serializers.ValidationError("You have already reviewed this model.")

        # Check if deployed (must use before review)
        has_deployed = Deployment.objects.filter(
            marketplace_model=model,
            deployed_by=reviewer,
        ).exists()

        if not has_deployed:
            raise serializers.ValidationError(
                "You must deploy the model before reviewing it."
            )

        return attrs

    def create(self, validated_data):
        """Create review with reviewer."""
        reviewer = self.context["request"].user.company
        return Review.objects.create(reviewer=reviewer, **validated_data)


class ModelSearchSerializer(serializers.Serializer):
    """Serializer for model search."""

    query = serializers.CharField(required=False, allow_blank=True)
    category = serializers.CharField(required=False)
    model_type = serializers.CharField(required=False)
    pricing_type = serializers.CharField(required=False)
    min_accuracy = serializers.FloatField(required=False)
    featured_only = serializers.BooleanField(required=False, default=False)

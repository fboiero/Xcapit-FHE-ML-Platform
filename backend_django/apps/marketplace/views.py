"""
Marketplace views for Xcapit FHE-ML Platform.

Provides endpoints for model marketplace, deployments, and reviews.
"""

from django.db.models import Avg, Count, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.models import AuditLog
from apps.core.permissions import IsCompanyMember, IsConsortiumAdmin, IsConsortiumMember

from .models import Category, Deployment, MarketplaceModel, Review
from .serializers import (
    CategorySerializer,
    DeploymentCreateSerializer,
    DeploymentSerializer,
    MarketplaceModelListSerializer,
    MarketplaceModelSerializer,
    ModelSearchSerializer,
    ReviewCreateSerializer,
    ReviewSerializer,
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for model categories (read-only).
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["get"])
    def models(self, request, pk=None):
        """Get models in this category."""
        category = self.get_object()
        models = MarketplaceModel.objects.filter(
            category=category,
            is_active=True,
        )
        serializer = MarketplaceModelListSerializer(models, many=True)
        return Response(serializer.data)


class MarketplaceModelViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for marketplace models (read-only for consumers).
    """

    serializer_class = MarketplaceModelSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by active models."""
        return MarketplaceModel.objects.filter(is_active=True)

    def get_serializer_class(self):
        if self.action == "list":
            return MarketplaceModelListSerializer
        return MarketplaceModelSerializer

    @action(detail=False, methods=["get"])
    def featured(self, request):
        """Get featured models."""
        models = MarketplaceModel.objects.filter(
            is_active=True,
            is_featured=True,
        ).order_by("-downloads")[:10]
        serializer = MarketplaceModelListSerializer(models, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def popular(self, request):
        """Get most popular models by downloads."""
        models = MarketplaceModel.objects.filter(
            is_active=True,
        ).order_by("-downloads")[:10]
        serializer = MarketplaceModelListSerializer(models, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def top_rated(self, request):
        """Get top rated models."""
        models = (
            MarketplaceModel.objects.filter(is_active=True)
            .annotate(avg_rating=Avg("reviews__rating"))
            .filter(avg_rating__isnull=False)
            .order_by("-avg_rating")[:10]
        )
        serializer = MarketplaceModelListSerializer(models, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def search(self, request):
        """Search marketplace models."""
        search_serializer = ModelSearchSerializer(data=request.data)
        search_serializer.is_valid(raise_exception=True)
        params = search_serializer.validated_data

        queryset = MarketplaceModel.objects.filter(is_active=True)

        # Text search
        query = params.get("query")
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query)
            )

        # Filters
        category = params.get("category")
        if category:
            queryset = queryset.filter(category_id=category)

        model_type = params.get("model_type")
        if model_type:
            queryset = queryset.filter(model_type=model_type)

        pricing_type = params.get("pricing_type")
        if pricing_type:
            queryset = queryset.filter(pricing_type=pricing_type)

        min_accuracy = params.get("min_accuracy")
        if min_accuracy:
            queryset = queryset.filter(accuracy__gte=min_accuracy)

        if params.get("featured_only"):
            queryset = queryset.filter(is_featured=True)

        serializer = MarketplaceModelListSerializer(queryset, many=True)
        return Response({
            "count": queryset.count(),
            "results": serializer.data,
        })

    @action(detail=True, methods=["get"])
    def reviews(self, request, pk=None):
        """Get reviews for a model."""
        model = self.get_object()
        reviews = Review.objects.filter(marketplace_model=model).order_by("-created_at")
        serializer = ReviewSerializer(reviews, many=True)

        # Calculate rating distribution
        distribution = (
            reviews.values("rating")
            .annotate(count=Count("id"))
            .order_by("rating")
        )
        rating_dist = {i: 0 for i in range(1, 6)}
        for item in distribution:
            rating_dist[item["rating"]] = item["count"]

        return Response({
            "model_id": model.id,
            "total_reviews": reviews.count(),
            "average_rating": model.rating,
            "rating_distribution": rating_dist,
            "reviews": serializer.data,
        })


class DeploymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for marketplace model deployments.
    """

    serializer_class = DeploymentSerializer
    permission_classes = [IsAuthenticated, IsConsortiumMember]

    def get_queryset(self):
        """Filter deployments by consortium."""
        consortium_id = self.request.query_params.get("consortium_id")
        if consortium_id:
            return Deployment.objects.filter(consortium_id=consortium_id)

        # Or by company
        user = self.request.user
        if user.company:
            return Deployment.objects.filter(deployed_by=user.company)
        return Deployment.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return DeploymentCreateSerializer
        return DeploymentSerializer

    def perform_create(self, serializer):
        """Create deployment and log event."""
        deployment = serializer.save()
        AuditLog.log(
            self.request,
            action="model_deployed",
            resource_type="deployment",
            resource_id=deployment.id,
            extra_data={
                "model_id": str(deployment.marketplace_model_id),
                "consortium_id": str(deployment.consortium_id),
            },
        )

    @action(detail=True, methods=["post"])
    def suspend(self, request, pk=None):
        """Suspend a deployment."""
        deployment = self.get_object()

        if deployment.status != Deployment.Status.ACTIVE:
            return Response(
                {"detail": "Deployment is not active."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        deployment.status = Deployment.Status.SUSPENDED
        deployment.save(update_fields=["status"])

        return Response({"detail": "Deployment suspended."})

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """Activate a suspended deployment."""
        deployment = self.get_object()

        if deployment.status != Deployment.Status.SUSPENDED:
            return Response(
                {"detail": "Deployment is not suspended."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        deployment.status = Deployment.Status.ACTIVE
        deployment.save(update_fields=["status"])

        return Response({"detail": "Deployment activated."})

    @action(detail=True, methods=["post"])
    def remove(self, request, pk=None):
        """Remove a deployment."""
        deployment = self.get_object()

        if deployment.status == Deployment.Status.REMOVED:
            return Response(
                {"detail": "Deployment already removed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        deployment.status = Deployment.Status.REMOVED
        deployment.removed_at = timezone.now()
        deployment.save()

        return Response({"detail": "Deployment removed."})


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for model reviews.
    """

    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        """Filter reviews."""
        user = self.request.user
        if user.company:
            # Own reviews
            return Review.objects.filter(reviewer=user.company)
        return Review.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return ReviewCreateSerializer
        return ReviewSerializer

    @action(detail=True, methods=["post"])
    def helpful(self, request, pk=None):
        """Mark a review as helpful."""
        review = self.get_object()
        review.helpful_count += 1
        review.save(update_fields=["helpful_count"])
        return Response({"helpful_count": review.helpful_count})

"""
Views para la app de Marketplace.

ViewSets para gestionar listados de modelos, categorias,
despliegues y resenas del marketplace.
"""

from __future__ import annotations

from django.db.models import Avg, Count, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.models import AuditLog
from apps.core.permissions import IsConsortiumMember

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


# =============================================================================
# ModelListing (replaces MarketplaceModel as a full ModelViewSet)
# =============================================================================


class ModelListingViewSet(viewsets.ModelViewSet):
    """
    CRUD para listados de modelos en el marketplace.

    - list:     modelos activos con filtros por model_type, pricing_type, tags.
    - retrieve: detalle de un modelo.
    - create:   publicar un modelo (admin).
    - purchase: comprar/desplegar un modelo (POST).
    - review:   escribir una resena para un modelo (POST).

    Soporta busqueda por nombre y descripcion via search query param.
    """

    serializer_class = MarketplaceModelSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retorna modelos activos con filtros opcionales."""
        queryset = MarketplaceModel.objects.filter(is_active=True)

        # Filtros opcionales
        model_type = self.request.query_params.get("model_type")
        if model_type:
            queryset = queryset.filter(model_type=model_type)

        pricing_type = self.request.query_params.get("pricing_type")
        if pricing_type:
            queryset = queryset.filter(pricing_type=pricing_type)

        tags = self.request.query_params.get("tags")
        if tags:
            tag_list = [t.strip() for t in tags.split(",")]
            for tag in tag_list:
                queryset = queryset.filter(
                    Q(features__contains=[tag]) | Q(use_cases__contains=[tag])
                )

        # Busqueda por texto
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )

        return queryset.select_related("category")

    def get_serializer_class(self):
        if self.action == "list":
            return MarketplaceModelListSerializer
        return MarketplaceModelSerializer

    def create(self, request, *args, **kwargs) -> Response:
        """Marketplace models are managed via admin, not via the public API."""
        return Response(
            {"detail": "Method not allowed."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def update(self, request, *args, **kwargs) -> Response:
        """Marketplace models are managed via admin, not via the public API."""
        return Response(
            {"detail": "Method not allowed."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def partial_update(self, request, *args, **kwargs) -> Response:
        """Marketplace models are managed via admin, not via the public API."""
        return Response(
            {"detail": "Method not allowed."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def destroy(self, request, *args, **kwargs) -> Response:
        """Marketplace models are managed via admin, not via the public API."""
        return Response(
            {"detail": "Method not allowed."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(detail=True, methods=["post"])
    def purchase(self, request, pk=None) -> Response:
        """
        Comprar/desplegar un modelo del marketplace.

        Requiere consortium_id en el body del request. Crea un Deployment
        y actualiza el contador de descargas.
        """
        marketplace_model = self.get_object()
        company = request.user.company

        if not company:
            return Response(
                {"detail": "Debes pertenecer a una empresa."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        consortium_id = request.data.get("consortium_id")
        if not consortium_id:
            return Response(
                {"detail": "consortium_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # SECURITY: Verify user is a member of the target consortium
        from apps.consortiums.models import Consortium, ConsortiumMember

        try:
            consortium = Consortium.objects.get(pk=consortium_id)
        except Consortium.DoesNotExist:
            return Response(
                {"detail": "Consortium not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        is_owner = consortium.owner_id == company.id
        is_member = ConsortiumMember.objects.filter(
            consortium=consortium,
            company=company,
            status="active",
        ).exists()
        if not is_owner and not is_member:
            return Response(
                {"detail": "No tienes acceso a este consorcio."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not marketplace_model.is_active:
            return Response(
                {"detail": "Model is not active."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if already deployed
        if Deployment.objects.filter(
            marketplace_model=marketplace_model,
            consortium_id=consortium_id,
            status__in=[Deployment.Status.PENDING, Deployment.Status.ACTIVE],
        ).exists():
            return Response(
                {"detail": "Model already deployed to this consortium."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create deployment
        config = request.data.get("config", {})
        deployment = Deployment.objects.create(
            marketplace_model=marketplace_model,
            consortium_id=consortium_id,
            deployed_by=company,
            config=config,
        )

        # Increment downloads
        marketplace_model.downloads += 1
        marketplace_model.save(update_fields=["downloads"])

        AuditLog.log(
            request,
            action="model_purchased",
            resource_type="deployment",
            resource_id=deployment.id,
            extra_data={
                "model_id": str(marketplace_model.id),
                "consortium_id": str(consortium_id),
            },
        )

        return Response(
            DeploymentSerializer(deployment).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def review(self, request, pk=None) -> Response:
        """
        Escribir una resena para un modelo del marketplace.

        Requiere rating (1-5) y opcionalmente title y comment.
        El usuario debe haber desplegado el modelo previamente.
        """
        marketplace_model = self.get_object()
        company = request.user.company

        if not company:
            return Response(
                {"detail": "Debes pertenecer a una empresa."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if already reviewed
        if Review.objects.filter(
            marketplace_model=marketplace_model,
            reviewer=company,
        ).exists():
            return Response(
                {"detail": "You have already reviewed this model."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if deployed (must use before review)
        has_deployed = Deployment.objects.filter(
            marketplace_model=marketplace_model,
            deployed_by=company,
        ).exists()

        if not has_deployed:
            return Response(
                {"detail": "You must deploy the model before reviewing it."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate review data
        rating = request.data.get("rating")
        if not rating or not isinstance(rating, int) or not (1 <= rating <= 5):
            return Response(
                {"detail": "rating (1-5) is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        review_obj = Review.objects.create(
            marketplace_model=marketplace_model,
            reviewer=company,
            consortium_id=request.data.get("consortium_id"),
            rating=rating,
            title=request.data.get("title", ""),
            comment=request.data.get("comment", ""),
        )

        return Response(
            ReviewSerializer(review_obj).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"])
    def featured(self, request) -> Response:
        """Modelos destacados."""
        models = MarketplaceModel.objects.filter(
            is_active=True,
            is_featured=True,
        ).order_by("-downloads")[:10]
        serializer = MarketplaceModelListSerializer(models, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def popular(self, request) -> Response:
        """Modelos mas populares por descargas."""
        models = MarketplaceModel.objects.filter(
            is_active=True,
        ).order_by("-downloads")[:10]
        serializer = MarketplaceModelListSerializer(models, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def top_rated(self, request) -> Response:
        """Modelos mejor calificados."""
        models = (
            MarketplaceModel.objects.filter(is_active=True)
            .annotate(avg_rating=Avg("reviews__rating"))
            .filter(avg_rating__isnull=False)
            .order_by("-avg_rating")[:10]
        )
        serializer = MarketplaceModelListSerializer(models, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def search(self, request) -> Response:
        """Buscar modelos en el marketplace."""
        search_serializer = ModelSearchSerializer(data=request.data)
        search_serializer.is_valid(raise_exception=True)
        params = search_serializer.validated_data

        queryset = MarketplaceModel.objects.filter(is_active=True)

        query = params.get("query")
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )

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
    def reviews(self, request, pk=None) -> Response:
        """Listar resenas de un modelo."""
        model_obj = self.get_object()
        model_reviews = Review.objects.filter(marketplace_model=model_obj).order_by("-created_at")
        serializer = ReviewSerializer(model_reviews, many=True)

        distribution = (
            model_reviews.values("rating")
            .annotate(count=Count("id"))
            .order_by("rating")
        )
        rating_dist = dict.fromkeys(range(1, 6), 0)
        for item in distribution:
            rating_dist[item["rating"]] = item["count"]

        return Response({
            "model_id": model_obj.id,
            "total_reviews": model_reviews.count(),
            "average_rating": model_obj.rating,
            "rating_distribution": rating_dist,
            "reviews": serializer.data,
        })


# =============================================================================
# Categories
# =============================================================================


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para categorias del marketplace.
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["get"])
    def models(self, request, pk=None) -> Response:
        """Listar modelos activos en esta categoria."""
        category = self.get_object()
        category_models = MarketplaceModel.objects.filter(
            category=category,
            is_active=True,
        )
        serializer = MarketplaceModelListSerializer(category_models, many=True)
        return Response(serializer.data)


# =============================================================================
# Deployments
# =============================================================================


class DeploymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet para despliegues de modelos del marketplace.

    Membership security is enforced inside get_queryset() and
    DeploymentCreateSerializer.validate_consortium() — not via the
    IsConsortiumMember class-level permission, which would incorrectly
    treat the deployment pk as a consortium pk on detail endpoints.
    """

    serializer_class = DeploymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter deployments by consortium or company (membership-scoped)."""
        from apps.consortiums.models import Consortium, ConsortiumMember

        user = self.request.user
        company = getattr(user, "company", None)
        if not company:
            return Deployment.objects.none()

        consortium_id = self.request.query_params.get("consortium_id")
        if consortium_id:
            # SECURITY: Verify membership before returning deployments
            is_owner = Consortium.objects.filter(
                pk=consortium_id, owner=company,
            ).exists()
            is_member = ConsortiumMember.objects.filter(
                consortium_id=consortium_id,
                company=company,
                status="active",
            ).exists()
            if not is_owner and not is_member:
                return Deployment.objects.none()
            return Deployment.objects.filter(consortium_id=consortium_id)

        return Deployment.objects.filter(deployed_by=company)

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
    def suspend(self, request, pk=None) -> Response:
        """Suspender un despliegue."""
        deployment = self.get_object()

        if deployment.status != Deployment.Status.ACTIVE:
            return Response(
                {"detail": "Deployment is not active."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        deployment.status = Deployment.Status.PAUSED
        deployment.save(update_fields=["status"])

        return Response({"detail": "Deployment suspended."})

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None) -> Response:
        """Activar un despliegue suspendido."""
        deployment = self.get_object()

        if deployment.status != Deployment.Status.PAUSED:
            return Response(
                {"detail": "Deployment is not paused."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        deployment.status = Deployment.Status.ACTIVE
        deployment.save(update_fields=["status"])

        return Response({"detail": "Deployment activated."})

    @action(detail=True, methods=["post"])
    def remove(self, request, pk=None) -> Response:
        """Remover un despliegue."""
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


# =============================================================================
# Reviews
# =============================================================================


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet para resenas de modelos.
    """

    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        """Filter reviews by company."""
        user = self.request.user
        if user.company:
            return Review.objects.filter(reviewer=user.company)
        return Review.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return ReviewCreateSerializer
        return ReviewSerializer

    @action(detail=True, methods=["post"])
    def helpful(self, request, pk=None) -> Response:
        """Marcar una resena como util."""
        review_obj = self.get_object()
        review_obj.helpful_count += 1
        review_obj.save(update_fields=["helpful_count"])
        return Response({"helpful_count": review_obj.helpful_count})

"""
Ensemble views for Xcapit FHE-ML Platform.
"""

import hashlib
import time

from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.models import AuditLog
from apps.core.permissions import IsCompanyMember
from apps.models.models import MLModel

from .models import Ensemble, EnsembleEvaluation, EnsembleModel, EnsemblePrediction
from .serializers import (
    AddModelSerializer,
    EnsembleCreateSerializer,
    EnsembleEvaluationSerializer,
    EnsembleModelSerializer,
    EnsemblePredictionSerializer,
    EnsembleSerializer,
    PredictRequestSerializer,
)


class EnsembleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ensemble management.
    """

    serializer_class = EnsembleSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self):
        """Filter ensembles by user's company."""
        user = self.request.user
        if not user.company:
            return Ensemble.objects.none()

        return Ensemble.objects.filter(owner=user.company).prefetch_related(
            "ensemble_models__model"
        )

    def get_serializer_class(self):
        if self.action == "create":
            return EnsembleCreateSerializer
        return EnsembleSerializer

    def perform_create(self, serializer):
        """Create ensemble and log event."""
        ensemble = serializer.save()

        AuditLog.log(
            self.request,
            action="ensemble_created",
            resource_type="ensemble",
            resource_id=ensemble.id,
            extra_data={"name": ensemble.name, "type": ensemble.ensemble_type},
        )

    @action(detail=True, methods=["post"])
    def add_model(self, request, pk=None):
        """Add a model to the ensemble."""
        ensemble = self.get_object()
        serializer = AddModelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        model_id = serializer.validated_data["model_id"]
        weight = serializer.validated_data["weight"]

        # Check if model exists and is accessible
        model = get_object_or_404(MLModel, id=model_id)

        # Check if model is already in ensemble
        if EnsembleModel.objects.filter(ensemble=ensemble, model=model).exists():
            return Response(
                {"detail": "Model already in ensemble."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ensemble_model = EnsembleModel.objects.create(
            ensemble=ensemble,
            model=model,
            weight=weight,
        )

        AuditLog.log(
            request,
            action="model_added_to_ensemble",
            resource_type="ensemble",
            resource_id=ensemble.id,
            extra_data={"model_id": str(model_id)},
        )

        return Response(
            EnsembleModelSerializer(ensemble_model).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def remove_model(self, request, pk=None):
        """Remove a model from the ensemble."""
        ensemble = self.get_object()
        model_id = request.data.get("model_id")

        if not model_id:
            return Response(
                {"detail": "model_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ensemble_model = EnsembleModel.objects.filter(
            ensemble=ensemble,
            model_id=model_id,
        ).first()

        if not ensemble_model:
            return Response(
                {"detail": "Model not in ensemble."},
                status=status.HTTP_404_NOT_FOUND,
            )

        ensemble_model.delete()

        return Response({"detail": "Model removed from ensemble."})

    @action(detail=True, methods=["post"])
    def update_weights(self, request, pk=None):
        """Update model weights in the ensemble."""
        ensemble = self.get_object()
        weights = request.data.get("weights", {})

        if not weights:
            return Response(
                {"detail": "weights is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated = 0
        for model_id, weight in weights.items():
            updated += EnsembleModel.objects.filter(
                ensemble=ensemble,
                model_id=model_id,
            ).update(weight=weight)

        return Response({"detail": f"Updated {updated} model weights."})

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """Activate the ensemble for predictions."""
        ensemble = self.get_object()

        if ensemble.ensemble_models.count() < 2:
            return Response(
                {"detail": "Ensemble needs at least 2 models."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ensemble.status = Ensemble.Status.ACTIVE
        ensemble.save(update_fields=["status"])

        return Response(EnsembleSerializer(ensemble).data)

    @action(detail=True, methods=["post"])
    def predict(self, request, pk=None):
        """Make predictions using the ensemble."""
        ensemble = self.get_object()

        if ensemble.status not in [Ensemble.Status.ACTIVE, Ensemble.Status.DEPLOYED]:
            return Response(
                {"detail": "Ensemble must be active to make predictions."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PredictRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        X = serializer.validated_data["X"]
        start_time = time.perf_counter()

        # Get predictions from each model (simulated)
        model_predictions = {}
        for em in ensemble.ensemble_models.filter(is_active=True):
            # In real implementation, would call actual model
            model_predictions[str(em.model.id)] = {
                "predictions": [0] * len(X),  # Placeholder
                "weight": em.weight,
            }

        # Aggregate predictions based on ensemble type
        aggregated = self._aggregate_predictions(
            ensemble.ensemble_type,
            model_predictions,
            len(X),
        )

        latency_ms = (time.perf_counter() - start_time) * 1000

        # Create prediction record
        prediction = EnsemblePrediction.objects.create(
            ensemble=ensemble,
            requester=request.user.company,
            input_hash=hashlib.sha256(str(X).encode()).hexdigest(),
            n_samples=len(X),
            prediction=aggregated,
            model_predictions=model_predictions,
            latency_ms=latency_ms,
        )

        return Response(EnsemblePredictionSerializer(prediction).data)

    def _aggregate_predictions(self, ensemble_type, model_predictions, n_samples):
        """Aggregate predictions based on ensemble type."""
        if ensemble_type == Ensemble.EnsembleType.VOTING:
            # Majority voting (simplified)
            return {"method": "voting", "predictions": [0] * n_samples}
        elif ensemble_type == Ensemble.EnsembleType.AVERAGING:
            # Simple average
            return {"method": "averaging", "predictions": [0.5] * n_samples}
        elif ensemble_type == Ensemble.EnsembleType.WEIGHTED:
            # Weighted average
            return {"method": "weighted", "predictions": [0.5] * n_samples}
        else:
            return {"method": ensemble_type, "predictions": [0] * n_samples}

    @action(detail=True, methods=["get"])
    def evaluations(self, request, pk=None):
        """Get evaluation history for the ensemble."""
        ensemble = self.get_object()
        evaluations = EnsembleEvaluation.objects.filter(ensemble=ensemble)
        return Response(EnsembleEvaluationSerializer(evaluations, many=True).data)


class EnsemblePredictionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for ensemble predictions (read-only).
    """

    serializer_class = EnsemblePredictionSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self):
        """Filter predictions by user's company."""
        user = self.request.user
        if not user.company:
            return EnsemblePrediction.objects.none()

        return EnsemblePrediction.objects.filter(requester=user.company)

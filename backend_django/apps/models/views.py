"""
ML Model views for Xcapit FHE-ML Platform.

Provides endpoints for model management, training, and prediction.
"""

import time
import uuid

from django.db.models import Avg, Count, Q, Sum
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.models import AuditLog
from apps.core.permissions import IsCompanyMember, IsResourceOwner

from .models import MLModel, ModelCheckpoint, PredictionLog, TrainingRun
from .serializers import (
    MLModelCreateSerializer,
    MLModelSerializer,
    ModelCheckpointSerializer,
    ModelStatsSerializer,
    PredictionLogSerializer,
    PredictRequestSerializer,
    PredictResponseSerializer,
    TrainingRunCreateSerializer,
    TrainingRunSerializer,
)


class MLModelViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ML model management.
    """

    serializer_class = MLModelSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self):
        """Filter models by owner."""
        user = self.request.user
        if user.company:
            return MLModel.objects.filter(owner=user.company)
        return MLModel.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return MLModelCreateSerializer
        return MLModelSerializer

    def perform_create(self, serializer):
        """Create model and log event."""
        model = serializer.save()
        AuditLog.log(
            self.request,
            action="model_created",
            resource_type="ml_model",
            resource_id=model.id,
            extra_data={"name": model.name, "type": model.model_type},
        )

    @action(detail=True, methods=["post"])
    def train(self, request, pk=None):
        """Start training for a model."""
        model = self.get_object()

        if model.status == MLModel.Status.TRAINING:
            return Response(
                {"detail": "Model is already training."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create training run
        epochs = request.data.get("epochs", 10)
        training_run = TrainingRun.objects.create(
            model=model,
            epochs_total=epochs,
        )

        # Update model status
        model.status = MLModel.Status.TRAINING
        model.save(update_fields=["status"])

        # Log event
        AuditLog.log(
            request,
            action="training_started",
            resource_type="ml_model",
            resource_id=model.id,
            extra_data={"training_run_id": str(training_run.id)},
        )

        return Response({
            "detail": "Training started.",
            "training_run_id": training_run.id,
            "model_status": model.status,
        })

    @action(detail=True, methods=["post"])
    def predict(self, request, pk=None):
        """Make predictions with a model."""
        model = self.get_object()

        if model.status != MLModel.Status.TRAINED:
            return Response(
                {"detail": "Model must be trained before making predictions."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PredictRequestSerializer(data={
            "model_id": pk,
            **request.data,
        })
        serializer.is_valid(raise_exception=True)

        start_time = time.time()

        # Simulated prediction (actual FHE prediction would go here)
        data = serializer.validated_data["data"]
        n_samples = len(data)
        encrypted = serializer.validated_data["encrypted"]

        # Mock predictions
        predictions = [0.5] * n_samples

        latency_ms = (time.time() - start_time) * 1000

        # Log prediction
        PredictionLog.objects.create(
            model=model,
            requester=request.user.company,
            n_samples=n_samples,
            encrypted=encrypted,
            latency_ms=latency_ms,
            api_key_name=getattr(request.auth, "name", ""),
        )

        return Response(PredictResponseSerializer({
            "model_id": model.id,
            "predictions": predictions,
            "encrypted": encrypted,
            "latency_ms": round(latency_ms, 2),
        }).data)

    @action(detail=True, methods=["get"])
    def stats(self, request, pk=None):
        """Get prediction statistics for a model."""
        model = self.get_object()

        stats = PredictionLog.objects.filter(model=model).aggregate(
            total_predictions=Count("id"),
            total_samples=Sum("n_samples"),
            avg_latency_ms=Avg("latency_ms"),
            encrypted_predictions=Count("id", filter=Q(encrypted=True)),
        )

        return Response(ModelStatsSerializer({
            "total_predictions": stats["total_predictions"] or 0,
            "total_samples": stats["total_samples"] or 0,
            "avg_latency_ms": round(stats["avg_latency_ms"] or 0, 2),
            "encrypted_predictions": stats["encrypted_predictions"] or 0,
        }).data)

    @action(detail=True, methods=["get"])
    def checkpoints(self, request, pk=None):
        """Get model checkpoints."""
        model = self.get_object()
        checkpoints = ModelCheckpoint.objects.filter(model=model)
        serializer = ModelCheckpointSerializer(checkpoints, many=True)
        return Response(serializer.data)


class TrainingRunViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for training runs (read-only).
    """

    serializer_class = TrainingRunSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self):
        """Filter training runs by model owner."""
        user = self.request.user
        if user.company:
            return TrainingRun.objects.filter(model__owner=user.company)
        return TrainingRun.objects.none()

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a running training."""
        run = self.get_object()

        if run.status != TrainingRun.Status.RUNNING:
            return Response(
                {"detail": "Training is not running."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        run.status = TrainingRun.Status.CANCELLED
        run.save(update_fields=["status"])

        # Update model status
        run.model.status = MLModel.Status.CREATED
        run.model.save(update_fields=["status"])

        return Response({"detail": "Training cancelled."})


class PredictionLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for prediction logs (read-only).
    """

    serializer_class = PredictionLogSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self):
        """Filter logs by requester."""
        user = self.request.user
        if user.company:
            queryset = PredictionLog.objects.filter(requester=user.company)

            # Optional model filter
            model_id = self.request.query_params.get("model_id")
            if model_id:
                queryset = queryset.filter(model_id=model_id)

            return queryset.order_by("-timestamp")
        return PredictionLog.objects.none()

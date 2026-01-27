"""
ML Model views for Xcapit FHE-ML Platform.

Provides endpoints for model management, training, and prediction.
"""

import time

from apps.core.models import AuditLog
from apps.core.permissions import IsCompanyMember
from django.db import transaction
from django.db.models import Avg, Count, Q, Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import MLModel, ModelCheckpoint, PredictionLog, TrainingRun
from .serializers import (
    MLModelCreateSerializer,
    MLModelSerializer,
    ModelCheckpointSerializer,
    ModelStatsSerializer,
    PredictionLogSerializer,
    PredictRequestSerializer,
    PredictResponseSerializer,
    TrainingRunSerializer,
)


class MLModelViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ML model management.
    """

    serializer_class = MLModelSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "model_type"]
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "name", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Filter models by owner."""
        user = self.request.user
        if user.company:
            return MLModel.objects.filter(owner=user.company).select_related(
                "owner", "consortium"
            ).prefetch_related("training_runs", "checkpoints")
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
    @transaction.atomic
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

    @action(detail=True, methods=["post"])
    def detect_anomalies(self, request, pk=None):
        """Detect anomalies using anomaly detection models."""
        model = self.get_object()

        anomaly_types = [
            MLModel.ModelType.ISOLATION_FOREST,
            MLModel.ModelType.ONE_CLASS_SVM,
            MLModel.ModelType.LOCAL_OUTLIER_FACTOR,
            MLModel.ModelType.ELLIPTIC_ENVELOPE,
        ]

        if model.model_type not in anomaly_types:
            return Response(
                {"detail": f"Model type {model.model_type} is not an anomaly detection model."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if model.status != MLModel.Status.TRAINED:
            return Response(
                {"detail": "Model must be trained before detecting anomalies."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = request.data.get("data", [])
        if not data:
            return Response(
                {"detail": "No data provided for anomaly detection."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        start_time = time.time()

        # Simulated anomaly detection (actual FHE detection would go here)
        n_samples = len(data)
        # Mock results: -1 for anomaly, 1 for normal
        predictions = [1] * n_samples
        anomaly_scores = [0.1] * n_samples

        latency_ms = (time.time() - start_time) * 1000

        # Log prediction
        PredictionLog.objects.create(
            model=model,
            requester=request.user.company,
            n_samples=n_samples,
            encrypted=request.data.get("encrypted", False),
            latency_ms=latency_ms,
            api_key_name=getattr(request.auth, "name", ""),
        )

        return Response({
            "model_id": str(model.id),
            "predictions": predictions,
            "anomaly_scores": anomaly_scores,
            "n_anomalies": sum(1 for p in predictions if p == -1),
            "latency_ms": round(latency_ms, 2),
        })

    @action(detail=True, methods=["post"])
    def forecast(self, request, pk=None):
        """Generate forecasts using time series models."""
        model = self.get_object()

        time_series_types = [
            MLModel.ModelType.ARIMA,
            MLModel.ModelType.EXPONENTIAL_SMOOTHING,
            MLModel.ModelType.SIMPLE_MOVING_AVERAGE,
            MLModel.ModelType.PROPHET_LIKE,
        ]

        if model.model_type not in time_series_types:
            return Response(
                {"detail": f"Model type {model.model_type} is not a time series model."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if model.status != MLModel.Status.TRAINED:
            return Response(
                {"detail": "Model must be trained before forecasting."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        steps = request.data.get("steps", 10)
        if steps < 1 or steps > 365:
            return Response(
                {"detail": "Steps must be between 1 and 365."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        start_time = time.time()

        # Simulated forecast (actual FHE forecast would go here)
        forecasts = [0.5] * steps
        confidence_lower = [0.3] * steps
        confidence_upper = [0.7] * steps

        latency_ms = (time.time() - start_time) * 1000

        # Log prediction
        PredictionLog.objects.create(
            model=model,
            requester=request.user.company,
            n_samples=steps,
            encrypted=request.data.get("encrypted", False),
            latency_ms=latency_ms,
            api_key_name=getattr(request.auth, "name", ""),
        )

        return Response({
            "model_id": str(model.id),
            "steps": steps,
            "forecasts": forecasts,
            "confidence_lower": confidence_lower,
            "confidence_upper": confidence_upper,
            "latency_ms": round(latency_ms, 2),
        })

    @action(detail=True, methods=["post"])
    def tune_hyperparameters(self, request, pk=None):
        """Start hyperparameter tuning for a model."""
        model = self.get_object()

        if model.status == MLModel.Status.TRAINING:
            return Response(
                {"detail": "Model is already training."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        param_grid = request.data.get("param_grid", {})
        n_iter = request.data.get("n_iter", 10)
        cv_folds = request.data.get("cv_folds", 5)
        method = request.data.get("method", "random")  # random, bayesian, halving

        if not param_grid:
            return Response(
                {"detail": "param_grid is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if method not in ["random", "bayesian", "halving"]:
            return Response(
                {"detail": "method must be 'random', 'bayesian', or 'halving'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Log event
        AuditLog.log(
            request,
            action="hyperparameter_tuning_started",
            resource_type="ml_model",
            resource_id=model.id,
            extra_data={
                "method": method,
                "n_iter": n_iter,
                "cv_folds": cv_folds,
            },
        )

        return Response({
            "detail": "Hyperparameter tuning started.",
            "model_id": str(model.id),
            "method": method,
            "n_iter": n_iter,
            "cv_folds": cv_folds,
            "param_grid": param_grid,
        })

    @action(detail=False, methods=["get"])
    def model_types(self, request):
        """Get available model types."""
        types = []
        for choice in MLModel.ModelType.choices:
            types.append({
                "value": choice[0],
                "label": choice[1],
            })
        return Response({"model_types": types})

    @action(detail=False, methods=["get"])
    def model_categories(self, request):
        """Get model types grouped by category."""
        categories = {
            "core": {
                "label": "Core Models",
                "types": ["linear_regression", "logistic_regression", "decision_tree", "kmeans"],
            },
            "ensemble": {
                "label": "Ensemble Models",
                "types": ["random_forest", "gradient_boosting", "ensemble_voting"],
            },
            "neural": {
                "label": "Neural Networks",
                "types": ["neural_network"],
            },
            "classification": {
                "label": "Classification",
                "types": ["svm", "naive_bayes"],
            },
            "dimensionality": {
                "label": "Dimensionality Reduction",
                "types": ["pca"],
            },
            "anomaly": {
                "label": "Anomaly Detection",
                "types": ["isolation_forest", "one_class_svm", "local_outlier_factor", "elliptic_envelope"],
            },
            "time_series": {
                "label": "Time Series",
                "types": ["arima", "exponential_smoothing", "simple_moving_average", "prophet_like"],
            },
            "regularized": {
                "label": "Regularized Models",
                "types": ["ridge", "lasso", "elastic_net", "ridge_classifier", "sgd_regressor"],
            },
        }
        return Response({"categories": categories})


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
    @transaction.atomic
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

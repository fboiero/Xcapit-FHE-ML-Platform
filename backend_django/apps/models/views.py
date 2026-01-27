"""
ML Model views for Xcapit FHE-ML Platform.

Provides endpoints for model management, training, and prediction.
"""

import time

from apps.core.models import AuditLog
from apps.core.permissions import IsCompanyMember
from django.db import transaction
from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    BatchPredictionJob,
    MLModel,
    ModelCheckpoint,
    ModelExport,
    ModelVersion,
    PredictionLog,
    TrainingRun,
)
from .serializers import (
    BatchPredictRequestSerializer,
    BatchPredictResponseSerializer,
    BatchPredictionJobSerializer,
    CreateVersionSerializer,
    ExportDataSerializer,
    ExportRequestSerializer,
    ImportRequestSerializer,
    ImportResponseSerializer,
    MLModelCreateSerializer,
    MLModelSerializer,
    ModelCheckpointSerializer,
    ModelExportSerializer,
    ModelStatsSerializer,
    ModelVersionSerializer,
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

    # ==================== Model Versioning ====================

    @action(detail=True, methods=["get"])
    def versions(self, request, pk=None):
        """Get all versions of a model."""
        model = self.get_object()
        versions = ModelVersion.objects.filter(model=model)
        serializer = ModelVersionSerializer(versions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def create_version(self, request, pk=None):
        """Create a new version of the model."""
        model = self.get_object()

        if model.status != MLModel.Status.TRAINED:
            return Response(
                {"detail": "Model must be trained before creating a version."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CreateVersionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        version = model.create_version(
            bump_type=serializer.validated_data["bump_type"],
            changelog=serializer.validated_data.get("changelog", ""),
            created_by=request.user.company,
        )

        if serializer.validated_data.get("release_notes"):
            version.release_notes = serializer.validated_data["release_notes"]
            version.save()

        # Log event
        AuditLog.log(
            request,
            action="version_created",
            resource_type="ml_model",
            resource_id=model.id,
            extra_data={"version": version.version},
        )

        return Response(ModelVersionSerializer(version).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="versions/(?P<version_id>[^/.]+)/publish")
    @transaction.atomic
    def publish_version(self, request, pk=None, version_id=None):
        """Publish a specific version."""
        model = self.get_object()

        try:
            version = ModelVersion.objects.get(id=version_id, model=model)
        except ModelVersion.DoesNotExist:
            return Response(
                {"detail": "Version not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        version.publish()

        # Log event
        AuditLog.log(
            request,
            action="version_published",
            resource_type="ml_model",
            resource_id=model.id,
            extra_data={"version": version.version},
        )

        return Response(ModelVersionSerializer(version).data)

    @action(detail=True, methods=["post"], url_path="versions/(?P<version_id>[^/.]+)/rollback")
    @transaction.atomic
    def rollback_version(self, request, pk=None, version_id=None):
        """Rollback to a specific version."""
        model = self.get_object()

        try:
            version = ModelVersion.objects.get(id=version_id, model=model)
        except ModelVersion.DoesNotExist:
            return Response(
                {"detail": "Version not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Restore model params and config from version snapshot
        model.params = version.params_snapshot
        model.config = version.config_snapshot
        model.current_version = version.version
        model.save()

        # Log event
        AuditLog.log(
            request,
            action="version_rollback",
            resource_type="ml_model",
            resource_id=model.id,
            extra_data={"version": version.version},
        )

        return Response({
            "detail": f"Rolled back to version {version.version}.",
            "model": MLModelSerializer(model).data,
        })

    # ==================== Batch Prediction ====================

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def batch_predict(self, request, pk=None):
        """Submit a batch prediction job."""
        model = self.get_object()

        if model.status != MLModel.Status.TRAINED:
            return Response(
                {"detail": "Model must be trained before making predictions."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = BatchPredictRequestSerializer(data={
            "model_id": pk,
            **request.data,
        })
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data["data"]
        n_samples = len(data)
        encrypted = serializer.validated_data["encrypted"]
        priority = serializer.validated_data["priority"]
        async_mode = serializer.validated_data["async_mode"]

        # Create batch job
        job = BatchPredictionJob.objects.create(
            model=model,
            requester=request.user.company,
            input_data=data,
            n_samples=n_samples,
            encrypted=encrypted,
            priority=priority,
        )

        # Log event
        AuditLog.log(
            request,
            action="batch_prediction_submitted",
            resource_type="ml_model",
            resource_id=model.id,
            extra_data={"job_id": str(job.id), "n_samples": n_samples},
        )

        if async_mode:
            # Return job ID for async processing
            return Response(BatchPredictResponseSerializer({
                "job_id": job.id,
                "model_id": model.id,
                "status": job.status,
                "n_samples": n_samples,
                "encrypted": encrypted,
            }).data, status=status.HTTP_202_ACCEPTED)
        else:
            # Synchronous processing
            start_time = time.time()
            job.start()

            # Simulated batch prediction (actual FHE would go here)
            predictions = [0.5] * n_samples

            total_latency_ms = (time.time() - start_time) * 1000
            job.complete(predictions, total_latency_ms)

            # Log prediction
            PredictionLog.objects.create(
                model=model,
                requester=request.user.company,
                n_samples=n_samples,
                encrypted=encrypted,
                latency_ms=total_latency_ms,
                api_key_name=getattr(request.auth, "name", ""),
            )

            return Response(BatchPredictResponseSerializer({
                "job_id": job.id,
                "model_id": model.id,
                "status": job.status,
                "n_samples": n_samples,
                "predictions": predictions,
                "encrypted": encrypted,
                "total_latency_ms": round(total_latency_ms, 2),
            }).data)

    @action(detail=True, methods=["get"])
    def batch_jobs(self, request, pk=None):
        """Get batch prediction jobs for a model."""
        model = self.get_object()
        jobs = BatchPredictionJob.objects.filter(model=model, requester=request.user.company)
        serializer = BatchPredictionJobSerializer(jobs, many=True)
        return Response(serializer.data)

    # ==================== Model Export/Import ====================

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def export_model(self, request, pk=None):
        """Export model to portable format."""
        model = self.get_object()

        if model.status != MLModel.Status.TRAINED:
            return Response(
                {"detail": "Model must be trained before exporting."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ExportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get version if specified
        version = None
        if serializer.validated_data.get("version_id"):
            try:
                version = ModelVersion.objects.get(
                    id=serializer.validated_data["version_id"],
                    model=model,
                )
            except ModelVersion.DoesNotExist:
                return Response(
                    {"detail": "Version not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        export = ModelExport.create_export(
            model=model,
            format_type=serializer.validated_data["format"],
            include_weights=serializer.validated_data["include_weights"],
            exported_by=request.user.company,
            version=version,
        )

        # Log event
        AuditLog.log(
            request,
            action="model_exported",
            resource_type="ml_model",
            resource_id=model.id,
            extra_data={
                "export_id": str(export.id),
                "format": export.format,
            },
        )

        return Response({
            "export": ModelExportSerializer(export).data,
            "data": ExportDataSerializer(export.export_data).data,
        })

    @action(detail=True, methods=["get"])
    def exports(self, request, pk=None):
        """Get export history for a model."""
        model = self.get_object()
        exports = ModelExport.objects.filter(model=model)
        serializer = ModelExportSerializer(exports, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="exports/(?P<export_id>[^/.]+)/download")
    def download_export(self, request, pk=None, export_id=None):
        """Download a specific export."""
        model = self.get_object()

        try:
            export = ModelExport.objects.get(id=export_id, model=model)
        except ModelExport.DoesNotExist:
            return Response(
                {"detail": "Export not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({
            "export": ModelExportSerializer(export).data,
            "data": export.export_data,
        })

    @action(detail=False, methods=["post"])
    @transaction.atomic
    def import_model(self, request):
        """Import a model from exported data."""
        serializer = ImportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        export_data = serializer.validated_data["export_data"]

        # Validate export data format
        if "fheml_version" not in export_data or "model" not in export_data:
            return Response(
                {"detail": "Invalid export data format."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        model_data = export_data["model"]
        config = export_data.get("config", {})
        metadata = export_data.get("metadata", {})
        params = export_data.get("params", {})
        training = export_data.get("training", {})
        version_info = export_data.get("version")

        # Create new model
        new_name = serializer.validated_data.get("new_name") or f"{model_data['name']} (imported)"

        model = MLModel.objects.create(
            name=new_name,
            model_type=model_data["type"],
            status=MLModel.Status.TRAINED if params else MLModel.Status.CREATED,
            config=config,
            params=params,
            n_features=model_data.get("n_features"),
            feature_names=model_data.get("feature_names", []),
            training_epochs=training.get("epochs"),
            final_loss=training.get("final_loss"),
            owner=request.user.company,
            metadata={
                **metadata,
                "imported_from": model_data.get("id"),
                "import_timestamp": str(timezone.now()),
            },
        )

        if serializer.validated_data.get("consortium_id"):
            from apps.consortiums.models import Consortium
            try:
                consortium = Consortium.objects.get(id=serializer.validated_data["consortium_id"])
                model.consortium = consortium
                model.save()
            except Consortium.DoesNotExist:
                pass

        # Log event
        AuditLog.log(
            request,
            action="model_imported",
            resource_type="ml_model",
            resource_id=model.id,
            extra_data={
                "original_model_id": model_data.get("id"),
                "original_name": model_data["name"],
            },
        )

        return Response(ImportResponseSerializer({
            "model_id": model.id,
            "name": model.name,
            "model_type": model.model_type,
            "status": model.status,
            "imported_from_version": version_info.get("version") if version_info else None,
        }).data, status=status.HTTP_201_CREATED)


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


class BatchPredictionJobViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for batch prediction jobs (read-only with cancel action).
    """

    serializer_class = BatchPredictionJobSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "priority", "model"]
    ordering_fields = ["created_at", "status", "priority"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Filter jobs by requester."""
        user = self.request.user
        if user.company:
            return BatchPredictionJob.objects.filter(requester=user.company)
        return BatchPredictionJob.objects.none()

    @action(detail=True, methods=["get"])
    def status(self, request, pk=None):
        """Get job status and progress."""
        job = self.get_object()
        return Response({
            "id": job.id,
            "status": job.status,
            "progress_percent": job.progress_percent,
            "samples_processed": job.samples_processed,
            "n_samples": job.n_samples,
            "error_message": job.error_message,
        })

    @action(detail=True, methods=["get"])
    def results(self, request, pk=None):
        """Get job results if completed."""
        job = self.get_object()

        if job.status != BatchPredictionJob.Status.COMPLETED:
            return Response(
                {"detail": f"Job is not completed. Current status: {job.status}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({
            "id": job.id,
            "status": job.status,
            "predictions": job.predictions,
            "n_samples": job.n_samples,
            "total_latency_ms": job.total_latency_ms,
            "avg_latency_per_sample_ms": job.avg_latency_per_sample_ms,
        })

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def cancel(self, request, pk=None):
        """Cancel a pending or processing job."""
        job = self.get_object()

        if job.status not in [BatchPredictionJob.Status.PENDING, BatchPredictionJob.Status.PROCESSING]:
            return Response(
                {"detail": f"Cannot cancel job with status: {job.status}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        job.status = BatchPredictionJob.Status.CANCELLED
        job.completed_at = timezone.now()
        job.save()

        return Response({"detail": "Job cancelled.", "status": job.status})


class ModelVersionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for model versions (read-only).
    """

    serializer_class = ModelVersionSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "model"]
    ordering_fields = ["created_at", "major", "minor", "patch"]
    ordering = ["-major", "-minor", "-patch"]

    def get_queryset(self):
        """Filter versions by model owner."""
        user = self.request.user
        if user.company:
            return ModelVersion.objects.filter(model__owner=user.company)
        return ModelVersion.objects.none()

    @action(detail=True, methods=["get"])
    def diff(self, request, pk=None):
        """Get diff between this version and the previous one."""
        version = self.get_object()

        # Get previous version
        previous = ModelVersion.objects.filter(
            model=version.model,
        ).filter(
            Q(major__lt=version.major) |
            Q(major=version.major, minor__lt=version.minor) |
            Q(major=version.major, minor=version.minor, patch__lt=version.patch)
        ).order_by("-major", "-minor", "-patch").first()

        if not previous:
            return Response({
                "version": version.version,
                "previous_version": None,
                "diff": "This is the first version.",
            })

        # Simple config diff
        config_changes = {}
        for key in set(list(version.config_snapshot.keys()) + list(previous.config_snapshot.keys())):
            old_val = previous.config_snapshot.get(key)
            new_val = version.config_snapshot.get(key)
            if old_val != new_val:
                config_changes[key] = {"old": old_val, "new": new_val}

        return Response({
            "version": version.version,
            "previous_version": previous.version,
            "config_changes": config_changes,
            "metrics_current": version.metrics,
            "metrics_previous": previous.metrics,
            "changelog": version.changelog,
        })


class ModelExportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for model exports (read-only).
    """

    serializer_class = ModelExportSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["format", "model"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Filter exports by owner."""
        user = self.request.user
        if user.company:
            return ModelExport.objects.filter(exported_by=user.company)
        return ModelExport.objects.none()

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        """Download export data."""
        export = self.get_object()
        return Response({
            "export": ModelExportSerializer(export).data,
            "data": export.export_data,
        })

"""
ML Models for Xcapit FHE-ML Platform.

Provides models for ML model management, training, prediction,
versioning, batch processing, export/import, and sharing.
"""

from __future__ import annotations

import hashlib
import json
import uuid

from django.db import models
from django.utils import timezone


# =============================================================================
# MLModel
# =============================================================================


class MLModel(models.Model):
    """Machine Learning model managed within the platform."""

    class ModelType(models.TextChoices):
        LINEAR_REGRESSION = "linear_regression", "Linear Regression"
        LOGISTIC_REGRESSION = "logistic_regression", "Logistic Regression"
        DECISION_TREE = "decision_tree", "Decision Tree"
        KMEANS = "kmeans", "K-Means Clustering"
        RANDOM_FOREST = "random_forest", "Random Forest"
        GRADIENT_BOOSTING = "gradient_boosting", "Gradient Boosting"
        ENSEMBLE_VOTING = "ensemble_voting", "Ensemble Voting"
        NEURAL_NETWORK = "neural_network", "Neural Network"
        SVM = "svm", "Support Vector Machine"
        NAIVE_BAYES = "naive_bayes", "Naive Bayes"
        PCA = "pca", "Principal Component Analysis"
        ISOLATION_FOREST = "isolation_forest", "Isolation Forest"
        ONE_CLASS_SVM = "one_class_svm", "One-Class SVM"
        LOCAL_OUTLIER_FACTOR = "local_outlier_factor", "Local Outlier Factor"
        ELLIPTIC_ENVELOPE = "elliptic_envelope", "Elliptic Envelope"
        ARIMA = "arima", "ARIMA"
        EXPONENTIAL_SMOOTHING = "exponential_smoothing", "Exponential Smoothing"
        SIMPLE_MOVING_AVERAGE = "simple_moving_average", "Simple Moving Average"
        PROPHET_LIKE = "prophet_like", "Prophet-like Forecasting"
        RIDGE = "ridge", "Ridge Regression"
        LASSO = "lasso", "Lasso Regression"
        ELASTIC_NET = "elastic_net", "Elastic Net"
        RIDGE_CLASSIFIER = "ridge_classifier", "Ridge Classifier"
        SGD_REGRESSOR = "sgd_regressor", "SGD Regressor"

    class Status(models.TextChoices):
        CREATED = "created", "Created"
        TRAINING = "training", "Training"
        TRAINED = "trained", "Trained"
        FAILED = "failed", "Failed"
        ARCHIVED = "archived", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    model_type = models.CharField(max_length=50, choices=ModelType.choices, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CREATED,
        db_index=True,
    )
    config = models.JSONField(default=dict, blank=True)
    params = models.JSONField(default=dict, blank=True)
    n_features = models.IntegerField(blank=True, null=True)
    feature_names = models.JSONField(default=list, blank=True)
    trained_at = models.DateTimeField(blank=True, null=True)
    training_epochs = models.IntegerField(blank=True, null=True)
    final_loss = models.FloatField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    current_version = models.CharField(max_length=50, default="1.0.0")

    consortium = models.ForeignKey(
        "consortiums.Consortium",
        on_delete=models.SET_NULL,
        related_name="models",
        blank=True,
        null=True,
    )
    owner = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="models",
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "ML model"
        verbose_name_plural = "ML models"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["consortium"], name="models_mlmo_consort_374b32_idx"),
            models.Index(fields=["owner"], name="models_mlmo_owner_i_baf0ab_idx"),
            models.Index(fields=["model_type"], name="models_mlmo_model_t_9d75ba_idx"),
            models.Index(fields=["status"], name="models_mlmo_status_de16a7_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.model_type} / {self.status})"

    def mark_trained(
        self,
        epochs: int | None = None,
        loss: float | None = None,
        params: dict | None = None,
    ) -> None:
        """Mark the model as trained with the given metrics."""
        self.status = self.Status.TRAINED
        self.trained_at = timezone.now()
        if epochs is not None:
            self.training_epochs = epochs
        if loss is not None:
            self.final_loss = loss
        if params is not None:
            self.params = params
        self.save()

    def get_latest_version(self) -> "ModelVersion | None":
        """Return the most recent ModelVersion or None."""
        return (
            self.versions.order_by("-major", "-minor", "-patch").first()
        )

    def export(self, exported_by: object | None = None, **kwargs) -> "ModelExport":
        """Convenience method to create a ModelExport for this model."""
        return ModelExport.create_export(model=self, exported_by=exported_by, **kwargs)

    def set_params(self, params: dict) -> None:
        """Update model parameters and persist."""
        self.params = params
        self.save(update_fields=["params", "updated_at"])

    def get_params(self) -> dict:
        """Return the current model parameters."""
        return self.params or {}

    def create_version(
        self,
        bump_type: str = "patch",
        changelog: str = "",
        created_by: object | None = None,
    ) -> "ModelVersion":
        """Create a new version snapshot of this model.

        Args:
            bump_type: One of 'major', 'minor', 'patch'.
            changelog: Human-readable changelog entry.
            created_by: Company that created the version.

        Returns:
            The newly created ModelVersion.
        """
        latest = (
            ModelVersion.objects.filter(model=self)
            .order_by("-major", "-minor", "-patch")
            .first()
        )

        if latest:
            major, minor, patch = latest.major, latest.minor, latest.patch
            if bump_type == "major":
                major += 1
                minor = 0
                patch = 0
            elif bump_type == "minor":
                minor += 1
                patch = 0
            else:
                patch += 1
        else:
            # First version is always 1.0.0
            major, minor, patch = 1, 0, 0

        version_str = f"{major}.{minor}.{patch}"

        version = ModelVersion.objects.create(
            model=self,
            version=version_str,
            major=major,
            minor=minor,
            patch=patch,
            params_snapshot=self.params,
            config_snapshot=self.config,
            metrics={
                "final_loss": self.final_loss,
                "training_epochs": self.training_epochs,
            },
            training_metrics={
                "trained_at": str(self.trained_at) if self.trained_at else None,
            },
            changelog=changelog,
            created_by=created_by,
        )

        self.current_version = version_str
        self.save(update_fields=["current_version"])

        return version


# =============================================================================
# TrainingRun
# =============================================================================


class TrainingRun(models.Model):
    """Record of a training run for an ML model."""

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model = models.ForeignKey(
        MLModel,
        on_delete=models.CASCADE,
        related_name="training_runs",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.QUEUED,
        db_index=True,
    )
    epochs_completed = models.IntegerField(default=0)
    epochs_total = models.IntegerField(blank=True, null=True)
    current_loss = models.FloatField(blank=True, null=True)
    final_loss = models.FloatField(blank=True, null=True)
    metrics = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)

    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "training run"
        verbose_name_plural = "training runs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["model"], name="models_trai_model_i_0f18a4_idx"),
            models.Index(fields=["status"], name="models_trai_status_60775c_idx"),
        ]

    def __str__(self) -> str:
        return f"TrainingRun {self.id!s:.8} ({self.status})"

    def start(self) -> None:
        """Mark the training run as running."""
        self.status = self.Status.RUNNING
        self.started_at = timezone.now()
        self.save(update_fields=["status", "started_at"])

    def complete(
        self,
        final_loss: float | None = None,
        metrics: dict | None = None,
    ) -> None:
        """Mark the training run as completed."""
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        if final_loss is not None:
            self.final_loss = final_loss
        if metrics:
            self.metrics = metrics
        self.save()

    def fail(self, error_message: str = "") -> None:
        """Mark the training run as failed."""
        self.status = self.Status.FAILED
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "error_message", "completed_at"])

    @property
    def duration_seconds(self) -> float | None:
        """Duration of the training run in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


# =============================================================================
# PredictionLog
# =============================================================================


class PredictionLog(models.Model):
    """Log of a prediction made with an ML model."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model = models.ForeignKey(
        MLModel,
        on_delete=models.CASCADE,
        related_name="prediction_logs",
    )
    requester = models.ForeignKey(
        "core.Company",
        on_delete=models.SET_NULL,
        null=True,
        related_name="predictions",
    )
    n_samples = models.IntegerField()
    encrypted = models.BooleanField(default=False)
    latency_ms = models.FloatField()
    api_key_name = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "prediction log"
        verbose_name_plural = "prediction logs"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["model"], name="models_pred_model_i_31f693_idx"),
            models.Index(fields=["requester"], name="models_pred_request_40dd90_idx"),
            models.Index(fields=["timestamp"], name="models_pred_timesta_8e44d1_idx"),
            models.Index(fields=["encrypted"], name="models_pred_encrypt_b63b4b_idx"),
        ]

    def __str__(self) -> str:
        return f"PredictionLog {self.id!s:.8} — {self.n_samples} samples"


# =============================================================================
# ModelCheckpoint
# =============================================================================


class ModelCheckpoint(models.Model):
    """Checkpoint saved during training."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model = models.ForeignKey(
        MLModel,
        on_delete=models.CASCADE,
        related_name="checkpoints",
    )
    epoch = models.IntegerField()
    loss = models.FloatField(blank=True, null=True)
    weights_encrypted = models.JSONField(default=dict)
    weights_hash = models.CharField(max_length=64)
    blockchain_tx = models.CharField(max_length=66, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "model checkpoint"
        verbose_name_plural = "model checkpoints"
        ordering = ["-epoch"]
        unique_together = [("model", "epoch")]
        indexes = [
            models.Index(fields=["model", "epoch"], name="models_mode_model_i_0530e9_idx"),
            models.Index(fields=["weights_hash"], name="models_mode_weights_71434d_idx"),
        ]

    def __str__(self) -> str:
        return f"Epoch {self.epoch} checkpoint — {self.model.name}"


# =============================================================================
# ModelVersion
# =============================================================================


class ModelVersion(models.Model):
    """Immutable snapshot of a model at a point in time."""

    class VersionStatus(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        DEPRECATED = "deprecated", "Deprecated"
        ARCHIVED = "archived", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model = models.ForeignKey(
        MLModel,
        on_delete=models.CASCADE,
        related_name="versions",
    )
    version = models.CharField(max_length=50)
    major = models.IntegerField(default=1)
    minor = models.IntegerField(default=0)
    patch = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=VersionStatus.choices,
        default=VersionStatus.DRAFT,
    )
    params_snapshot = models.JSONField(default=dict)
    config_snapshot = models.JSONField(default=dict)
    metrics = models.JSONField(default=dict)
    training_metrics = models.JSONField(default=dict)
    changelog = models.TextField(blank=True)
    release_notes = models.TextField(blank=True)

    created_by = models.ForeignKey(
        "core.Company",
        on_delete=models.SET_NULL,
        null=True,
        related_name="model_versions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "model version"
        verbose_name_plural = "model versions"
        ordering = ["-major", "-minor", "-patch"]
        unique_together = [("model", "version")]
        indexes = [
            models.Index(fields=["model", "version"], name="models_mode_model_i_c92ec5_idx"),
            models.Index(fields=["status"], name="models_mode_status_bae3ba_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.model.name} v{self.version} ({self.status})"

    def publish(self) -> None:
        """Mark this version as published."""
        self.status = self.VersionStatus.PUBLISHED
        self.published_at = timezone.now()
        self.save(update_fields=["status", "published_at"])

    def deprecate(self) -> None:
        """Mark this version as deprecated."""
        self.status = self.VersionStatus.DEPRECATED
        self.save(update_fields=["status"])


# =============================================================================
# ModelExport
# =============================================================================


class ModelExport(models.Model):
    """Export of a model to a portable format."""

    class ExportFormat(models.TextChoices):
        FHEML_JSON = "fheml_json", "FHE-ML JSON"
        FHEML_BINARY = "fheml_binary", "FHE-ML Binary"
        ONNX_COMPATIBLE = "onnx_compatible", "ONNX Compatible"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model = models.ForeignKey(
        MLModel,
        on_delete=models.CASCADE,
        related_name="exports",
    )
    version = models.ForeignKey(
        ModelVersion,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="exports",
    )
    format = models.CharField(
        max_length=20,
        choices=ExportFormat.choices,
        default=ExportFormat.FHEML_JSON,
    )
    file_size_bytes = models.IntegerField(blank=True, null=True)
    checksum_sha256 = models.CharField(max_length=64, blank=True)
    export_data = models.JSONField(default=dict)
    include_weights = models.BooleanField(default=True)
    include_config = models.BooleanField(default=True)
    include_metadata = models.BooleanField(default=True)
    encryption_key_hash = models.CharField(max_length=64, blank=True)

    exported_by = models.ForeignKey(
        "core.Company",
        on_delete=models.SET_NULL,
        null=True,
        related_name="model_exports",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "model export"
        verbose_name_plural = "model exports"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["model"], name="models_mode_model_i_fe6420_idx"),
            models.Index(fields=["format"], name="models_mode_format_8bbf4e_idx"),
            models.Index(fields=["checksum_sha256"], name="models_mode_checksu_60f18e_idx"),
        ]

    def __str__(self) -> str:
        return f"Export {self.id!s:.8} ({self.format}) — {self.model.name}"

    @classmethod
    def create_export(
        cls,
        model: MLModel,
        exported_by: object | None = None,
        format_type: str = "fheml_json",
        include_weights: bool = True,
        include_config: bool = True,
        include_metadata: bool = True,
        version: ModelVersion | None = None,
    ) -> "ModelExport":
        """Create a new export for the given model.

        Args:
            model: The ML model to export.
            exported_by: Company performing the export.
            format_type: Export format.
            include_weights: Include model weights.
            include_config: Include model config.
            include_metadata: Include model metadata.
            version: Specific version to export.

        Returns:
            The newly created ModelExport.
        """
        export_data = {
            "fheml_version": "1.0",
            "model": {
                "id": str(model.id),
                "name": model.name,
                "type": model.model_type,
                "n_features": model.n_features,
                "feature_names": model.feature_names,
            },
            "config": model.config if include_config else {},
            "metadata": model.metadata if include_metadata else {},
            "training": {
                "epochs": model.training_epochs,
                "final_loss": model.final_loss,
                "trained_at": str(model.trained_at) if model.trained_at else None,
            },
        }

        if include_weights:
            export_data["params"] = model.params

        if version:
            export_data["version"] = {
                "version": version.version,
                "major": version.major,
                "minor": version.minor,
                "patch": version.patch,
            }

        data_str = json.dumps(export_data, sort_keys=True, default=str)
        checksum = hashlib.sha256(data_str.encode()).hexdigest()

        return cls.objects.create(
            model=model,
            version=version,
            format=format_type,
            export_data=export_data,
            file_size_bytes=len(data_str.encode()),
            checksum_sha256=checksum,
            include_weights=include_weights,
            include_config=include_config,
            include_metadata=include_metadata,
            exported_by=exported_by,
        )


# =============================================================================
# BatchPredictionJob
# =============================================================================


class BatchPredictionJob(models.Model):
    """Batch prediction job for an ML model."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model = models.ForeignKey(
        MLModel,
        on_delete=models.CASCADE,
        related_name="batch_jobs",
    )
    requester = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="batch_jobs",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.NORMAL,
    )
    input_data = models.JSONField(default=list)
    n_samples = models.IntegerField(default=0)
    encrypted = models.BooleanField(default=False)
    predictions = models.JSONField(default=list)
    error_message = models.TextField(blank=True)

    samples_processed = models.IntegerField(default=0)
    progress_percent = models.FloatField(default=0.0)
    total_latency_ms = models.FloatField(blank=True, null=True)
    avg_latency_per_sample_ms = models.FloatField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "batch prediction job"
        verbose_name_plural = "batch prediction jobs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["model"], name="models_batc_model_i_1ce424_idx"),
            models.Index(fields=["requester"], name="models_batc_request_69df1b_idx"),
            models.Index(fields=["status"], name="models_batc_status_56b65d_idx"),
            models.Index(
                fields=["priority", "-created_at"],
                name="models_batc_priorit_daf1ae_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"BatchJob {self.id!s:.8} ({self.status}) — {self.n_samples} samples"

    def start(self) -> None:
        """Mark job as processing."""
        self.status = self.Status.PROCESSING
        self.started_at = timezone.now()
        self.save(update_fields=["status", "started_at"])

    def update_progress(self, samples_processed: int) -> None:
        """Update progress based on samples processed so far."""
        self.samples_processed = samples_processed
        if self.n_samples > 0:
            self.progress_percent = round(
                (samples_processed / self.n_samples) * 100, 2
            )
        self.save(update_fields=["samples_processed", "progress_percent"])

    def complete(self, predictions: list, total_latency_ms: float) -> None:
        """Mark job as completed with results.

        Args:
            predictions: List of prediction values.
            total_latency_ms: Total time taken in milliseconds.
        """
        self.status = self.Status.COMPLETED
        self.predictions = predictions
        self.samples_processed = len(predictions)
        self.progress_percent = 100.0
        self.total_latency_ms = total_latency_ms
        if self.n_samples:
            self.avg_latency_per_sample_ms = total_latency_ms / self.n_samples
        self.completed_at = timezone.now()
        self.save()

    def fail(self, error_message: str) -> None:
        """Mark job as failed.

        Args:
            error_message: Error description.
        """
        self.status = self.Status.FAILED
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "error_message", "completed_at"])


# =============================================================================
# ModelShare
# =============================================================================


class ModelShare(models.Model):
    """Record of a model shared between consortiums."""

    class ShareType(models.TextChoices):
        FULL_ACCESS = "full_access", "Full Access"
        PREDICTION_ONLY = "prediction_only", "Prediction Only"
        READ_ONLY = "read_only", "Read Only"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending Approval"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        REVOKED = "revoked", "Revoked"
        EXPIRED = "expired", "Expired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model = models.ForeignKey(
        MLModel,
        on_delete=models.CASCADE,
        related_name="shares",
    )
    source_consortium = models.ForeignKey(
        "consortiums.Consortium",
        on_delete=models.CASCADE,
        related_name="model_shares_given",
    )
    shared_by = models.ForeignKey(
        "core.Company",
        on_delete=models.SET_NULL,
        null=True,
        related_name="models_shared",
    )
    target_consortium = models.ForeignKey(
        "consortiums.Consortium",
        on_delete=models.CASCADE,
        related_name="model_shares_received",
    )
    approved_by = models.ForeignKey(
        "core.Company",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="shares_approved",
    )
    version = models.ForeignKey(
        ModelVersion,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="shares",
    )

    share_type = models.CharField(
        max_length=20,
        choices=ShareType.choices,
        default=ShareType.PREDICTION_ONLY,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    revenue_share_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    max_predictions = models.IntegerField(blank=True, null=True)
    predictions_used = models.IntegerField(default=0)
    terms = models.TextField(blank=True)
    requires_approval = models.BooleanField(default=True)
    valid_from = models.DateTimeField(blank=True, null=True)
    valid_until = models.DateTimeField(blank=True, null=True)
    request_message = models.TextField(blank=True)
    approval_message = models.TextField(blank=True)
    blockchain_tx = models.CharField(max_length=66, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    revoked_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "model share"
        verbose_name_plural = "model shares"
        ordering = ["-created_at"]
        unique_together = [("model", "target_consortium")]
        indexes = [
            models.Index(fields=["model"], name="models_mode_model_i_8a36c2_idx"),
            models.Index(fields=["source_consortium"], name="models_mode_source__ad6613_idx"),
            models.Index(fields=["target_consortium"], name="models_mode_target__8f454e_idx"),
            models.Index(fields=["status"], name="models_mode_status_353157_idx"),
        ]

    def __str__(self) -> str:
        return f"Share {self.model.name} -> {self.target_consortium} ({self.status})"

    @property
    def is_active(self) -> bool:
        """Whether this share is currently active."""
        if self.status != self.Status.APPROVED:
            return False
        now = timezone.now()
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        if self.max_predictions and self.predictions_used >= self.max_predictions:
            return False
        return True

    @property
    def can_predict(self) -> bool:
        """Whether this share allows predictions."""
        return self.is_active and self.share_type in [
            self.ShareType.FULL_ACCESS,
            self.ShareType.PREDICTION_ONLY,
        ]

    @property
    def can_retrain(self) -> bool:
        """Whether this share allows retraining."""
        return self.is_active and self.share_type == self.ShareType.FULL_ACCESS

    def approve(self, approved_by: object | None = None, message: str = "") -> None:
        """Approve this share.

        Args:
            approved_by: Company approving the share.
            message: Approval message.
        """
        self.status = self.Status.APPROVED
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        if not self.valid_from:
            self.valid_from = timezone.now()
        self.approval_message = message
        self.save()

    def reject(self, rejected_by: object | None = None, message: str = "") -> None:
        """Reject this share.

        Args:
            rejected_by: Company rejecting the share.
            message: Rejection message.
        """
        self.status = self.Status.REJECTED
        self.approval_message = message
        self.save()

    def revoke(self, message: str = "") -> None:
        """Revoke this share.

        Args:
            message: Revocation message.
        """
        self.status = self.Status.REVOKED
        self.revoked_at = timezone.now()
        self.approval_message = message
        self.save()

    def increment_predictions(self, count: int = 1) -> None:
        """Increment the predictions_used counter and expire if limit reached."""
        from django.db.models import F

        ModelShare.objects.filter(pk=self.pk).update(
            predictions_used=F("predictions_used") + count
        )
        self.refresh_from_db()
        if self.max_predictions and self.predictions_used >= self.max_predictions:
            self.status = self.Status.EXPIRED
            self.save(update_fields=["status"])


# =============================================================================
# ModelShareRequest
# =============================================================================


class ModelShareRequest(models.Model):
    """Request to share a model from another consortium."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model = models.ForeignKey(
        MLModel,
        on_delete=models.CASCADE,
        related_name="share_requests",
    )
    requesting_consortium = models.ForeignKey(
        "consortiums.Consortium",
        on_delete=models.CASCADE,
        related_name="model_share_requests",
    )
    requested_by = models.ForeignKey(
        "core.Company",
        on_delete=models.SET_NULL,
        null=True,
        related_name="model_requests",
    )
    resulting_share = models.OneToOneField(
        ModelShare,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="original_request",
    )

    requested_share_type = models.CharField(
        max_length=20,
        choices=ModelShare.ShareType.choices,
        default=ModelShare.ShareType.PREDICTION_ONLY,
    )
    message = models.TextField(blank=True)
    proposed_revenue_share = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    response_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "model share request"
        verbose_name_plural = "model share requests"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["model"], name="models_mode_model_i_8e3ea6_idx"),
            models.Index(
                fields=["requesting_consortium"],
                name="models_mode_request_df242e_idx",
            ),
            models.Index(fields=["status"], name="models_mode_status_a4336d_idx"),
        ]

    def __str__(self) -> str:
        return f"ShareRequest {self.id!s:.8} ({self.status})"

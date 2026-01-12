"""
ML Model management for Xcapit FHE-ML Platform.

Handles model storage, training runs, and prediction logging.
Note: Uses JSON instead of pickle for secure serialization.
"""

import uuid

from django.db import models
from django.utils import timezone


class ModelVersion(models.Model):
    """
    Tracks version history for ML models.

    Each version represents a snapshot of the model at a specific point in time.
    """

    class VersionStatus(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        DEPRECATED = "deprecated", "Deprecated"
        ARCHIVED = "archived", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model = models.ForeignKey(
        "MLModel",
        on_delete=models.CASCADE,
        related_name="versions",
    )

    # Version info
    version = models.CharField(max_length=50)  # Semantic versioning: 1.0.0
    major = models.IntegerField(default=1)
    minor = models.IntegerField(default=0)
    patch = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=VersionStatus.choices,
        default=VersionStatus.DRAFT,
    )

    # Model snapshot
    params_snapshot = models.JSONField(default=dict)
    config_snapshot = models.JSONField(default=dict)

    # Metrics at version time
    metrics = models.JSONField(default=dict)  # accuracy, f1, etc.
    training_metrics = models.JSONField(default=dict)  # loss, epochs, etc.

    # Changelog
    changelog = models.TextField(blank=True)
    release_notes = models.TextField(blank=True)

    # Author
    created_by = models.ForeignKey(
        "core.Company",
        on_delete=models.SET_NULL,
        null=True,
        related_name="model_versions",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "model version"
        verbose_name_plural = "model versions"
        unique_together = ["model", "version"]
        ordering = ["-major", "-minor", "-patch"]
        indexes = [
            models.Index(fields=["model", "version"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.model.name} v{self.version}"

    def publish(self):
        """Publish this version."""
        self.status = self.VersionStatus.PUBLISHED
        self.published_at = timezone.now()
        self.save()

    def deprecate(self):
        """Mark version as deprecated."""
        self.status = self.VersionStatus.DEPRECATED
        self.save()

    @classmethod
    def create_version(cls, model, bump_type="patch", changelog="", created_by=None):
        """Create a new version for a model."""
        # Get latest version
        latest = cls.objects.filter(model=model).order_by("-major", "-minor", "-patch").first()

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
            major, minor, patch = 1, 0, 0

        version_str = f"{major}.{minor}.{patch}"

        return cls.objects.create(
            model=model,
            version=version_str,
            major=major,
            minor=minor,
            patch=patch,
            params_snapshot=model.params,
            config_snapshot=model.config,
            training_metrics={
                "epochs": model.training_epochs,
                "final_loss": model.final_loss,
            },
            changelog=changelog,
            created_by=created_by,
        )


class BatchPredictionJob(models.Model):
    """
    Batch prediction job for processing large datasets asynchronously.
    """

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
        "MLModel",
        on_delete=models.CASCADE,
        related_name="batch_jobs",
    )
    requester = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="batch_jobs",
    )

    # Job configuration
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

    # Input data
    input_data = models.JSONField(default=list)  # List of feature vectors
    n_samples = models.IntegerField(default=0)
    encrypted = models.BooleanField(default=False)

    # Output
    predictions = models.JSONField(default=list)
    error_message = models.TextField(blank=True)

    # Progress
    samples_processed = models.IntegerField(default=0)
    progress_percent = models.FloatField(default=0.0)

    # Metrics
    total_latency_ms = models.FloatField(null=True, blank=True)
    avg_latency_per_sample_ms = models.FloatField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "batch prediction job"
        verbose_name_plural = "batch prediction jobs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["model"]),
            models.Index(fields=["requester"]),
            models.Index(fields=["status"]),
            models.Index(fields=["priority", "-created_at"]),
        ]

    def __str__(self):
        return f"Batch {self.id} - {self.n_samples} samples"

    def start(self):
        """Mark job as started."""
        self.status = self.Status.PROCESSING
        self.started_at = timezone.now()
        self.save()

    def update_progress(self, samples_done):
        """Update job progress."""
        self.samples_processed = samples_done
        self.progress_percent = (samples_done / self.n_samples) * 100 if self.n_samples > 0 else 0
        self.save()

    def complete(self, predictions, total_latency_ms):
        """Mark job as completed."""
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.predictions = predictions
        self.samples_processed = self.n_samples
        self.progress_percent = 100.0
        self.total_latency_ms = total_latency_ms
        self.avg_latency_per_sample_ms = total_latency_ms / self.n_samples if self.n_samples > 0 else 0
        self.save()

    def fail(self, error_message):
        """Mark job as failed."""
        self.status = self.Status.FAILED
        self.completed_at = timezone.now()
        self.error_message = error_message
        self.save()


class ModelExport(models.Model):
    """
    Model export record for portable model format (FHE-ML format).

    Similar to ONNX but designed for FHE-compatible models.
    """

    class ExportFormat(models.TextChoices):
        FHEML_JSON = "fheml_json", "FHE-ML JSON"
        FHEML_BINARY = "fheml_binary", "FHE-ML Binary"
        ONNX_COMPATIBLE = "onnx_compatible", "ONNX Compatible"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    model = models.ForeignKey(
        "MLModel",
        on_delete=models.CASCADE,
        related_name="exports",
    )
    version = models.ForeignKey(
        ModelVersion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="exports",
    )

    # Export info
    format = models.CharField(
        max_length=20,
        choices=ExportFormat.choices,
        default=ExportFormat.FHEML_JSON,
    )
    file_size_bytes = models.IntegerField(null=True, blank=True)
    checksum_sha256 = models.CharField(max_length=64, blank=True)

    # Exported content (JSON for portability)
    export_data = models.JSONField(default=dict)

    # Metadata
    include_weights = models.BooleanField(default=True)
    include_config = models.BooleanField(default=True)
    include_metadata = models.BooleanField(default=True)
    encryption_key_hash = models.CharField(max_length=64, blank=True)  # For encrypted exports

    # Who exported
    exported_by = models.ForeignKey(
        "core.Company",
        on_delete=models.SET_NULL,
        null=True,
        related_name="model_exports",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "model export"
        verbose_name_plural = "model exports"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["model"]),
            models.Index(fields=["format"]),
            models.Index(fields=["checksum_sha256"]),
        ]

    def __str__(self):
        return f"Export {self.model.name} ({self.format})"

    @classmethod
    def create_export(cls, model, format_type=None, include_weights=True, exported_by=None, version=None):
        """Create an export of a model."""
        import hashlib
        import json

        if format_type is None:
            format_type = cls.ExportFormat.FHEML_JSON

        # Build export data
        export_data = {
            "fheml_version": "1.0.0",
            "model": {
                "id": str(model.id),
                "name": model.name,
                "type": model.model_type,
                "status": model.status,
                "n_features": model.n_features,
                "feature_names": model.feature_names,
            },
            "config": model.config,
            "metadata": model.metadata,
            "training": {
                "epochs": model.training_epochs,
                "final_loss": model.final_loss,
                "trained_at": model.trained_at.isoformat() if model.trained_at else None,
            },
        }

        if include_weights:
            export_data["params"] = model.params

        if version:
            export_data["version"] = {
                "version": version.version,
                "changelog": version.changelog,
                "metrics": version.metrics,
            }

        # Calculate checksum
        export_json = json.dumps(export_data, sort_keys=True)
        checksum = hashlib.sha256(export_json.encode()).hexdigest()

        return cls.objects.create(
            model=model,
            version=version,
            format=format_type,
            export_data=export_data,
            file_size_bytes=len(export_json.encode()),
            checksum_sha256=checksum,
            include_weights=include_weights,
            exported_by=exported_by,
        )


class MLModel(models.Model):
    """
    Machine Learning model with FHE support.

    Parameters are serialized as JSON for security (no pickle).
    """

    class ModelType(models.TextChoices):
        # Core models
        LINEAR_REGRESSION = "linear_regression", "Linear Regression"
        LOGISTIC_REGRESSION = "logistic_regression", "Logistic Regression"
        DECISION_TREE = "decision_tree", "Decision Tree"
        KMEANS = "kmeans", "K-Means Clustering"

        # Ensemble models
        RANDOM_FOREST = "random_forest", "Random Forest"
        GRADIENT_BOOSTING = "gradient_boosting", "Gradient Boosting"
        ENSEMBLE_VOTING = "ensemble_voting", "Ensemble Voting"

        # Neural networks
        NEURAL_NETWORK = "neural_network", "Neural Network"

        # Classification
        SVM = "svm", "Support Vector Machine"
        NAIVE_BAYES = "naive_bayes", "Naive Bayes"

        # Dimensionality reduction
        PCA = "pca", "Principal Component Analysis"

        # Anomaly detection
        ISOLATION_FOREST = "isolation_forest", "Isolation Forest"
        ONE_CLASS_SVM = "one_class_svm", "One-Class SVM"
        LOCAL_OUTLIER_FACTOR = "local_outlier_factor", "Local Outlier Factor"
        ELLIPTIC_ENVELOPE = "elliptic_envelope", "Elliptic Envelope"

        # Time series
        ARIMA = "arima", "ARIMA"
        EXPONENTIAL_SMOOTHING = "exponential_smoothing", "Exponential Smoothing"
        SIMPLE_MOVING_AVERAGE = "simple_moving_average", "Simple Moving Average"
        PROPHET_LIKE = "prophet_like", "Prophet-like Forecasting"

        # Regularized models
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

    # Type and configuration
    model_type = models.CharField(
        max_length=50,
        choices=ModelType.choices,
        db_index=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CREATED,
        db_index=True,
    )

    # Configuration (JSON, validated by serializer)
    config = models.JSONField(default=dict, blank=True)

    # Model parameters (JSON serialization, NOT pickle)
    # For complex numpy arrays, store as lists
    params = models.JSONField(default=dict, blank=True)

    # Feature information
    n_features = models.IntegerField(null=True, blank=True)
    feature_names = models.JSONField(default=list, blank=True)

    # Training info
    trained_at = models.DateTimeField(null=True, blank=True)
    training_epochs = models.IntegerField(null=True, blank=True)
    final_loss = models.FloatField(null=True, blank=True)

    # Association (optional - for consortium models)
    consortium = models.ForeignKey(
        "consortiums.Consortium",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="models",
    )
    owner = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="models",
        null=True,
        blank=True,
    )

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)

    # Version tracking
    current_version = models.CharField(max_length=50, default="1.0.0")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "ML model"
        verbose_name_plural = "ML models"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["model_type"]),
            models.Index(fields=["status"]),
            models.Index(fields=["consortium"]),
            models.Index(fields=["owner"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.model_type})"

    def set_params(self, params_dict):
        """
        Safely set model parameters.

        Converts numpy arrays to lists for JSON serialization.
        """
        import numpy as np

        def convert_to_serializable(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, (np.float32, np.float64)):
                return float(obj)
            elif isinstance(obj, (np.int32, np.int64)):
                return int(obj)
            elif isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(v) for v in obj]
            return obj

        self.params = convert_to_serializable(params_dict)

    def get_params(self):
        """
        Get model parameters, converting lists back to numpy arrays.
        """
        import numpy as np

        def convert_to_numpy(obj, key=None):
            if isinstance(obj, list) and obj and isinstance(obj[0], (int, float, list)):
                return np.array(obj)
            elif isinstance(obj, dict):
                return {k: convert_to_numpy(v, k) for k, v in obj.items()}
            return obj

        return convert_to_numpy(self.params)

    def mark_trained(self, epochs=None, loss=None, params=None):
        """Mark model as trained with results."""
        self.status = self.Status.TRAINED
        self.trained_at = timezone.now()
        if epochs is not None:
            self.training_epochs = epochs
        if loss is not None:
            self.final_loss = loss
        if params is not None:
            self.set_params(params)
        self.save()

    def get_latest_version(self):
        """Get the latest version of this model."""
        return self.versions.order_by("-major", "-minor", "-patch").first()

    def create_version(self, bump_type="patch", changelog="", created_by=None):
        """Create a new version snapshot of this model."""
        version = ModelVersion.create_version(
            model=self,
            bump_type=bump_type,
            changelog=changelog,
            created_by=created_by,
        )
        self.current_version = version.version
        self.save(update_fields=["current_version"])
        return version

    def export(self, format_type=None, include_weights=True, exported_by=None):
        """Export this model to portable format."""
        version = self.get_latest_version()
        return ModelExport.create_export(
            model=self,
            format_type=format_type,
            include_weights=include_weights,
            exported_by=exported_by,
            version=version,
        )


class TrainingRun(models.Model):
    """
    Record of a model training run.
    """

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

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.QUEUED,
        db_index=True,
    )

    # Training progress
    epochs_completed = models.IntegerField(default=0)
    epochs_total = models.IntegerField(null=True, blank=True)
    current_loss = models.FloatField(null=True, blank=True)
    final_loss = models.FloatField(null=True, blank=True)

    # Metrics (JSON)
    metrics = models.JSONField(default=dict, blank=True)

    # Error handling
    error_message = models.TextField(blank=True)

    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "training run"
        verbose_name_plural = "training runs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["model"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Training {self.model.name} ({self.status})"

    @property
    def duration_seconds(self):
        """Get training duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def start(self):
        """Mark training as started."""
        self.status = self.Status.RUNNING
        self.started_at = timezone.now()
        self.save(update_fields=["status", "started_at"])

    def complete(self, final_loss=None, metrics=None):
        """Mark training as completed."""
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        if final_loss is not None:
            self.final_loss = final_loss
        if metrics:
            self.metrics = metrics
        self.save()

    def fail(self, error_message):
        """Mark training as failed."""
        self.status = self.Status.FAILED
        self.completed_at = timezone.now()
        self.error_message = error_message
        self.save()


class PredictionLog(models.Model):
    """
    Log of prediction requests for monitoring and billing.
    """

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

    # Request details
    n_samples = models.IntegerField()
    encrypted = models.BooleanField(default=False)
    latency_ms = models.FloatField()

    # API key used (name only, not the key itself)
    api_key_name = models.CharField(max_length=255, blank=True)

    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "prediction log"
        verbose_name_plural = "prediction logs"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["model"]),
            models.Index(fields=["requester"]),
            models.Index(fields=["timestamp"]),
            models.Index(fields=["encrypted"]),
        ]

    def __str__(self):
        return f"{self.n_samples} samples on {self.model.name}"


class ModelCheckpoint(models.Model):
    """
    Model checkpoint for federated learning rounds.

    Stores encrypted model weights after each training round.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    model = models.ForeignKey(
        MLModel,
        on_delete=models.CASCADE,
        related_name="checkpoints",
    )

    # Checkpoint info
    epoch = models.IntegerField()
    loss = models.FloatField(null=True, blank=True)

    # Encrypted weights (JSON, not pickle)
    weights_encrypted = models.JSONField(default=dict)

    # Hash for verification
    weights_hash = models.CharField(max_length=64)

    # Blockchain
    blockchain_tx = models.CharField(max_length=66, blank=True)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "model checkpoint"
        verbose_name_plural = "model checkpoints"
        unique_together = ["model", "epoch"]
        ordering = ["-epoch"]
        indexes = [
            models.Index(fields=["model", "epoch"]),
            models.Index(fields=["weights_hash"]),
        ]

    def __str__(self):
        return f"{self.model.name} - Epoch {self.epoch}"


class ModelShare(models.Model):
    """
    Model sharing between consortiums.

    Allows one consortium to share a trained model with another consortium,
    with configurable permissions and optional revenue sharing.
    """

    class ShareType(models.TextChoices):
        FULL_ACCESS = "full_access", "Full Access"  # Read + Predict + Re-train
        PREDICTION_ONLY = "prediction_only", "Prediction Only"  # Only run predictions
        READ_ONLY = "read_only", "Read Only"  # View model info only

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

    # Source (who is sharing)
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

    # Target (who receives the share)
    target_consortium = models.ForeignKey(
        "consortiums.Consortium",
        on_delete=models.CASCADE,
        related_name="model_shares_received",
    )
    approved_by = models.ForeignKey(
        "core.Company",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="shares_approved",
    )

    # Share configuration
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

    # Optional version lock (share specific version only)
    version = models.ForeignKey(
        ModelVersion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="shares",
    )

    # Revenue sharing (percentage of prediction revenue to source)
    revenue_share_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    # Usage limits
    max_predictions = models.IntegerField(null=True, blank=True)  # None = unlimited
    predictions_used = models.IntegerField(default=0)

    # Terms and conditions
    terms = models.TextField(blank=True)
    requires_approval = models.BooleanField(default=True)

    # Validity period
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)

    # Notes
    request_message = models.TextField(blank=True)  # Message when requesting
    approval_message = models.TextField(blank=True)  # Message when approving/rejecting

    # Blockchain
    blockchain_tx = models.CharField(max_length=66, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "model share"
        verbose_name_plural = "model shares"
        ordering = ["-created_at"]
        unique_together = ["model", "target_consortium"]  # One share per consortium per model
        indexes = [
            models.Index(fields=["model"]),
            models.Index(fields=["source_consortium"]),
            models.Index(fields=["target_consortium"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.model.name} -> {self.target_consortium.name}"

    @property
    def is_active(self) -> bool:
        """Check if share is currently active and valid."""
        if self.status != self.Status.APPROVED:
            return False

        now = timezone.now()

        # Check validity period
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False

        # Check usage limits
        if self.max_predictions and self.predictions_used >= self.max_predictions:
            return False

        return True

    def can_predict(self) -> bool:
        """Check if target consortium can make predictions."""
        if not self.is_active:
            return False
        return self.share_type in [self.ShareType.FULL_ACCESS, self.ShareType.PREDICTION_ONLY]

    def can_retrain(self) -> bool:
        """Check if target consortium can re-train the model."""
        if not self.is_active:
            return False
        return self.share_type == self.ShareType.FULL_ACCESS

    def approve(self, approved_by=None, message: str = ""):
        """Approve the share request."""
        self.status = self.Status.APPROVED
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        self.approval_message = message
        if not self.valid_from:
            self.valid_from = timezone.now()
        self.save()

    def reject(self, rejected_by=None, message: str = ""):
        """Reject the share request."""
        self.status = self.Status.REJECTED
        self.approved_by = rejected_by
        self.approval_message = message
        self.save()

    def revoke(self, revoked_by=None, message: str = ""):
        """Revoke an active share."""
        self.status = self.Status.REVOKED
        self.revoked_at = timezone.now()
        self.approval_message = message
        self.save()

    def increment_predictions(self, count: int = 1):
        """Increment prediction usage count."""
        from django.db.models import F

        ModelShare.objects.filter(pk=self.pk).update(
            predictions_used=F("predictions_used") + count
        )
        self.refresh_from_db()

        # Check if limit reached
        if self.max_predictions and self.predictions_used >= self.max_predictions:
            self.status = self.Status.EXPIRED
            self.save(update_fields=["status"])


class ModelShareRequest(models.Model):
    """
    Request to share a model from another consortium.

    Used when a consortium wants access to a model they don't own.
    """

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

    # Requester
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

    # Request details
    requested_share_type = models.CharField(
        max_length=20,
        choices=ModelShare.ShareType.choices,
        default=ModelShare.ShareType.PREDICTION_ONLY,
    )
    message = models.TextField(blank=True)
    proposed_revenue_share = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    response_message = models.TextField(blank=True)

    # Created share (if approved)
    resulting_share = models.OneToOneField(
        ModelShare,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="original_request",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "model share request"
        verbose_name_plural = "model share requests"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["model"]),
            models.Index(fields=["requesting_consortium"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Request: {self.requesting_consortium.name} -> {self.model.name}"

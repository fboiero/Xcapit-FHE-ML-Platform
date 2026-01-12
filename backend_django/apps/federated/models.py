"""
Federated inference models for Xcapit FHE-ML Platform.

Supports distributed inference across edge nodes
with encrypted data processing.
"""

import hashlib
import json
import uuid

from django.db import models
from django.utils import timezone


class InferenceEndpoint(models.Model):
    """
    Inference endpoint for encrypted predictions.
    """

    class EndpointType(models.TextChoices):
        REALTIME = "realtime", "Real-time"
        BATCH = "batch", "Batch"
        STREAMING = "streaming", "Streaming"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    consortium = models.ForeignKey(
        "consortiums.Consortium",
        on_delete=models.CASCADE,
        related_name="inference_endpoints",
    )
    company = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="inference_endpoints",
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # Associated model
    model = models.ForeignKey(
        "models.MLModel",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="endpoints",
    )

    # Type and status
    endpoint_type = models.CharField(
        max_length=20,
        choices=EndpointType.choices,
        default=EndpointType.REALTIME,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    # Configuration
    config = models.JSONField(default=dict, blank=True)

    # URL (generated after deployment)
    url = models.URLField(blank=True)

    # Stats
    request_count = models.IntegerField(default=0)
    total_latency_ms = models.FloatField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "inference endpoint"
        verbose_name_plural = "inference endpoints"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["consortium"]),
            models.Index(fields=["company"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.status})"

    @property
    def avg_latency_ms(self):
        if self.request_count > 0:
            return self.total_latency_ms / self.request_count
        return 0


class InferenceRequest(models.Model):
    """
    Individual inference request.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    endpoint = models.ForeignKey(
        InferenceEndpoint,
        on_delete=models.CASCADE,
        related_name="requests",
    )
    requester = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="inference_requests",
    )

    # Request details
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.NORMAL,
    )

    # Input hash (not the actual data)
    input_hash = models.CharField(max_length=64)

    # Encryption key reference
    encryption_key_id = models.CharField(max_length=100, blank=True)

    # Timing
    latency_ms = models.FloatField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "inference request"
        verbose_name_plural = "inference requests"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["endpoint"]),
            models.Index(fields=["requester"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Request {self.id} ({self.status})"

    @staticmethod
    def hash_input(input_data):
        """Hash input data for storage."""
        data_str = json.dumps(input_data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()


class InferenceResult(models.Model):
    """
    Result of an inference request.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    request = models.OneToOneField(
        InferenceRequest,
        on_delete=models.CASCADE,
        related_name="result",
    )

    # Encrypted output (JSON, never raw predictions)
    encrypted_output = models.TextField()

    # Metadata
    output_metadata = models.JSONField(default=dict, blank=True)
    confidence_scores = models.JSONField(default=list)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "inference result"
        verbose_name_plural = "inference results"

    def __str__(self):
        return f"Result for {self.request_id}"


class FederatedModel(models.Model):
    """
    Federated model for distributed training and inference.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        TRAINING = "training", "Training"
        READY = "ready", "Ready"
        DEPLOYED = "deployed", "Deployed"
        ARCHIVED = "archived", "Archived"

    class ModelType(models.TextChoices):
        LINEAR_REGRESSION = "linear_regression", "Linear Regression"
        LOGISTIC_REGRESSION = "logistic_regression", "Logistic Regression"
        NEURAL_NETWORK = "neural_network", "Neural Network"
        XGBOOST = "xgboost", "XGBoost"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    consortium = models.ForeignKey(
        "consortiums.Consortium",
        on_delete=models.CASCADE,
        related_name="federated_models",
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    model_type = models.CharField(
        max_length=50,
        choices=ModelType.choices,
    )
    version = models.CharField(max_length=20, default="1.0.0")

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    # Configuration
    config = models.JSONField(default=dict, blank=True)

    # Metrics
    metrics = models.JSONField(default=dict, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "federated model"
        verbose_name_plural = "federated models"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["consortium"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.name} v{self.version}"

    @property
    def deployment_count(self):
        return self.edge_deployments.count()


class EdgeNode(models.Model):
    """
    Edge node for federated inference.
    """

    class NodeType(models.TextChoices):
        ON_PREMISE = "on_premise", "On-Premise"
        CLOUD = "cloud", "Cloud"
        HYBRID = "hybrid", "Hybrid"

    class Status(models.TextChoices):
        OFFLINE = "offline", "Offline"
        ONLINE = "online", "Online"
        MAINTENANCE = "maintenance", "Maintenance"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    company = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="edge_nodes",
    )

    name = models.CharField(max_length=100)
    node_type = models.CharField(
        max_length=20,
        choices=NodeType.choices,
        default=NodeType.ON_PREMISE,
    )
    location = models.CharField(max_length=200, blank=True)

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OFFLINE,
    )

    # Capabilities
    capabilities = models.JSONField(default=dict, blank=True)

    # Deployed models
    deployed_models = models.ManyToManyField(
        FederatedModel,
        related_name="edge_deployments",
        blank=True,
    )

    # Health
    last_heartbeat = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "edge node"
        verbose_name_plural = "edge nodes"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["company"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.status})"

    def update_heartbeat(self):
        """Update last heartbeat timestamp."""
        self.last_heartbeat = timezone.now()
        self.status = self.Status.ONLINE
        self.save(update_fields=["last_heartbeat", "status"])

    @property
    def is_online(self):
        if not self.last_heartbeat:
            return False
        # Consider offline if no heartbeat in last 5 minutes
        return (timezone.now() - self.last_heartbeat).seconds < 300

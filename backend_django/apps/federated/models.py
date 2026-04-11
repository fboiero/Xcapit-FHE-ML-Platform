"""
Federated models for Xcapit FHE-ML Platform.

Modelos federados, endpoints de inferencia, nodos edge,
solicitudes y resultados de inferencia distribuida.
"""

import uuid

from django.db import models
from django.utils import timezone


class FederatedModel(models.Model):
    """Modelo federado entrenado dentro de un consorcio."""

    class ModelType(models.TextChoices):
        LINEAR_REGRESSION = "linear_regression", "Linear Regression"
        LOGISTIC_REGRESSION = "logistic_regression", "Logistic Regression"
        DECISION_TREE = "decision_tree", "Decision Tree"
        KMEANS = "kmeans", "K-Means"
        RANDOM_FOREST = "random_forest", "Random Forest"
        NEURAL_NETWORK = "neural_network", "Neural Network"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        TRAINING = "training", "Training"
        READY = "ready", "Ready"
        DEPLOYED = "deployed", "Deployed"
        DEPRECATED = "deprecated", "Deprecated"
        ARCHIVED = "archived", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    consortium = models.ForeignKey(
        "consortiums.Consortium",
        on_delete=models.CASCADE,
        related_name="federated_models",
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    model_type = models.CharField(max_length=50)
    version = models.CharField(max_length=20, default="1.0.0")

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    config = models.JSONField(default=dict, blank=True)
    metrics = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "federated model"
        verbose_name_plural = "federated models"
        indexes = [
            models.Index(fields=["consortium", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} v{self.version} ({self.status})"

    @property
    def deployment_count(self) -> int:
        """Cantidad de nodos edge donde este modelo está desplegado."""
        return self.edge_nodes.count()


class InferenceEndpoint(models.Model):
    """Endpoint de inferencia para un modelo federado."""

    class EndpointType(models.TextChoices):
        REST = "rest", "REST"
        GRPC = "grpc", "gRPC"
        WEBSOCKET = "websocket", "WebSocket"
        BATCH = "batch", "Batch"
        REALTIME = "realtime", "Realtime"

    class Status(models.TextChoices):
        PROVISIONING = "provisioning", "Provisioning"
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        ERROR = "error", "Error"
        DECOMMISSIONED = "decommissioned", "Decommissioned"

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
    model = models.ForeignKey(
        FederatedModel,
        on_delete=models.SET_NULL,
        related_name="inference_endpoints",
        null=True,
        blank=True,
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    endpoint_type = models.CharField(
        max_length=20,
        choices=EndpointType.choices,
        default=EndpointType.REST,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PROVISIONING,
        db_index=True,
    )
    config = models.JSONField(default=dict, blank=True)
    url = models.URLField(max_length=500, blank=True)

    request_count = models.IntegerField(default=0)
    total_latency_ms = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "inference endpoint"
        verbose_name_plural = "inference endpoints"
        indexes = [
            models.Index(fields=["consortium", "status"]),
            models.Index(fields=["company"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.endpoint_type} / {self.status})"

    @property
    def avg_latency_ms(self) -> float:
        """Latencia promedio por solicitud en milisegundos."""
        if self.request_count == 0:
            return 0
        return round(self.total_latency_ms / self.request_count, 2)


class InferenceRequest(models.Model):
    """Solicitud de inferencia sobre un endpoint."""

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
        CRITICAL = "critical", "Critical"

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

    input_hash = models.CharField(max_length=66, blank=True)
    encryption_key_id = models.CharField(max_length=255, blank=True)
    latency_ms = models.IntegerField(null=True, blank=True)

    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "inference request"
        verbose_name_plural = "inference requests"
        indexes = [
            models.Index(fields=["endpoint", "status"]),
            models.Index(fields=["requester"]),
        ]

    def __str__(self) -> str:
        return f"Request {self.id!s:.8} — {self.status}"

    @staticmethod
    def hash_input(data: dict) -> str:
        """Compute a deterministic SHA-256 hash of *data*."""
        import hashlib
        import json

        raw = json.dumps(data, sort_keys=True).encode()
        return hashlib.sha256(raw).hexdigest()


class InferenceResult(models.Model):
    """Resultado de una solicitud de inferencia."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    request = models.OneToOneField(
        InferenceRequest,
        on_delete=models.CASCADE,
        related_name="result",
    )

    encrypted_output = models.TextField(blank=True)
    output_metadata = models.JSONField(default=dict, blank=True)
    confidence_scores = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "inference result"
        verbose_name_plural = "inference results"

    def __str__(self) -> str:
        return f"Result for request {self.request_id!s:.8}"


class EdgeNode(models.Model):
    """Nodo edge para ejecución distribuida de inferencia."""

    class NodeType(models.TextChoices):
        GPU = "gpu", "GPU"
        CPU = "cpu", "CPU"
        TPU = "tpu", "TPU"
        FPGA = "fpga", "FPGA"
        CLOUD = "cloud", "Cloud"
        ON_PREMISE = "on_premise", "On Premise"

    class Status(models.TextChoices):
        ONLINE = "online", "Online"
        OFFLINE = "offline", "Offline"
        MAINTENANCE = "maintenance", "Maintenance"
        ERROR = "error", "Error"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    company = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="edge_nodes",
    )

    name = models.CharField(max_length=255)
    node_type = models.CharField(
        max_length=10,
        choices=NodeType.choices,
        default=NodeType.CPU,
    )
    location = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OFFLINE,
        db_index=True,
    )
    capabilities = models.JSONField(default=dict, blank=True)

    deployed_models = models.ManyToManyField(
        FederatedModel,
        related_name="edge_nodes",
        blank=True,
    )

    last_heartbeat = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "edge node"
        verbose_name_plural = "edge nodes"
        indexes = [
            models.Index(fields=["company", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.node_type} / {self.status})"

    def update_heartbeat(self) -> None:
        """Record a heartbeat and mark the node as online."""
        self.last_heartbeat = timezone.now()
        self.status = self.Status.ONLINE
        self.save(update_fields=["last_heartbeat", "status", "updated_at"])

    @property
    def is_online(self) -> bool:
        """Indica si el nodo se reportó en los últimos 5 minutos."""
        if self.last_heartbeat is None:
            return False
        from datetime import timedelta

        return timezone.now() - self.last_heartbeat < timedelta(minutes=5)

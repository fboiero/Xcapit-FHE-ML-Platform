"""
Marketplace models for Xcapit FHE-ML Platform.

Catálogo de modelos ML pre-entrenados para licenciamiento,
despliegue y revisión por parte de los consorcios.
"""

import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Category(models.Model):
    """Categoría de modelo en el marketplace."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    order = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "category"
        verbose_name_plural = "categories"

    def __str__(self) -> str:
        return self.name

    @property
    def model_count(self) -> int:
        """Cantidad de modelos activos en esta categoría."""
        return self.marketplace_models.filter(is_active=True).count()


class MarketplaceModel(models.Model):
    """Modelo ML publicado en el marketplace."""

    class ModelType(models.TextChoices):
        LINEAR_REGRESSION = "linear_regression", "Linear Regression"
        LOGISTIC_REGRESSION = "logistic_regression", "Logistic Regression"
        DECISION_TREE = "decision_tree", "Decision Tree"
        KMEANS = "kmeans", "K-Means"
        RANDOM_FOREST = "random_forest", "Random Forest"
        NEURAL_NETWORK = "neural_network", "Neural Network"

    class PricingType(models.TextChoices):
        ONE_TIME = "one_time", "One-Time"
        SUBSCRIPTION = "subscription", "Subscription"
        PER_INFERENCE = "per_inference", "Per Inference"
        FREE = "free", "Free"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="marketplace_models",
    )

    model_type = models.CharField(max_length=50)
    version = models.CharField(max_length=20, default="1.0.0")
    accuracy = models.DecimalField(
        max_digits=5, decimal_places=4, null=True, blank=True
    )
    training_samples = models.IntegerField(default=0)
    features = models.JSONField(default=list, blank=True)
    use_cases = models.JSONField(default=list, blank=True)

    pricing_type = models.CharField(
        max_length=20,
        choices=PricingType.choices,
        default=PricingType.FREE,
    )
    price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    is_active = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    downloads = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "marketplace model"
        verbose_name_plural = "marketplace models"
        indexes = [
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["pricing_type"]),
            models.Index(fields=["is_featured"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} v{self.version}"

    @property
    def rating(self) -> float:
        """Calificación promedio del modelo. Retorna 0 si no tiene reseñas."""
        avg = self.reviews.aggregate(avg=models.Avg("rating"))["avg"]
        return round(avg, 2) if avg is not None else 0

    @property
    def rating_count(self) -> int:
        """Cantidad de reseñas."""
        return self.reviews.count()

    @property
    def industry(self) -> str:
        """Industria derivada de la categoría."""
        return self.category.name if self.category else ""


class Deployment(models.Model):
    """Despliegue de un modelo del marketplace en un consorcio."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        REMOVED = "removed", "Removed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    marketplace_model = models.ForeignKey(
        MarketplaceModel,
        on_delete=models.CASCADE,
        related_name="deployments",
    )
    consortium = models.ForeignKey(
        "consortiums.Consortium",
        on_delete=models.CASCADE,
        related_name="marketplace_deployments",
    )
    deployed_by = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="marketplace_deployments",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    config = models.JSONField(default=dict, blank=True)

    deployed_at = models.DateTimeField(auto_now_add=True)
    removed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "deployment"
        verbose_name_plural = "deployments"
        indexes = [
            models.Index(fields=["marketplace_model", "consortium"]),
            models.Index(fields=["deployed_by"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"{self.marketplace_model.name} → {self.consortium.name} ({self.status})"


class Review(models.Model):
    """Reseña de un modelo del marketplace."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    marketplace_model = models.ForeignKey(
        MarketplaceModel,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    reviewer = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="marketplace_reviews",
    )
    consortium = models.ForeignKey(
        "consortiums.Consortium",
        on_delete=models.SET_NULL,
        related_name="marketplace_reviews",
        null=True,
        blank=True,
    )

    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=255, blank=True)
    comment = models.TextField(blank=True)
    helpful_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "review"
        verbose_name_plural = "reviews"
        unique_together = ["marketplace_model", "reviewer"]
        indexes = [
            models.Index(fields=["marketplace_model", "rating"]),
        ]

    def __str__(self) -> str:
        return f"{self.reviewer.name} — {self.rating}/5 on {self.marketplace_model.name}"

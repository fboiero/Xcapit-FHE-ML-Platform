"""
Marketplace models for Xcapit FHE-ML Platform.

Pre-trained model marketplace for consortium deployment.
"""

import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg


class Category(models.Model):
    """
    Model category for marketplace browsing.
    """

    id = models.CharField(max_length=50, primary_key=True)  # e.g., "cat_fraud"
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)  # Icon class name
    order = models.IntegerField(default=0)

    class Meta:
        verbose_name = "category"
        verbose_name_plural = "categories"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    @property
    def model_count(self):
        return self.marketplace_models.filter(is_active=True).count()


class MarketplaceModel(models.Model):
    """
    Pre-trained model available in the marketplace.
    """

    class PricingType(models.TextChoices):
        FREE = "free", "Free"
        ONE_TIME = "one_time", "One-Time Purchase"
        SUBSCRIPTION = "subscription", "Subscription"

    class ModelType(models.TextChoices):
        LINEAR_REGRESSION = "linear_regression", "Linear Regression"
        LOGISTIC_REGRESSION = "logistic_regression", "Logistic Regression"
        DECISION_TREE = "decision_tree", "Decision Tree"
        KMEANS = "kmeans", "K-Means Clustering"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Categorization
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name="marketplace_models",
    )
    model_type = models.CharField(
        max_length=50,
        choices=ModelType.choices,
    )

    # Version
    version = models.CharField(max_length=20, default="1.0.0")

    # Performance metrics
    accuracy = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
    )
    training_samples = models.IntegerField(null=True, blank=True)

    # Features
    features = models.JSONField(default=list)  # List of feature names
    use_cases = models.JSONField(default=list)  # List of use case descriptions

    # Pricing
    pricing_type = models.CharField(
        max_length=20,
        choices=PricingType.choices,
        default=PricingType.FREE,
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    # Stats
    downloads = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "marketplace model"
        verbose_name_plural = "marketplace models"
        ordering = ["-downloads", "-created_at"]
        indexes = [
            models.Index(fields=["category"]),
            models.Index(fields=["model_type"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["is_featured"]),
            models.Index(fields=["-downloads"]),
        ]

    def __str__(self):
        return f"{self.name} v{self.version}"

    @property
    def rating(self):
        avg = self.reviews.aggregate(avg=Avg("rating"))["avg"]
        return round(avg, 1) if avg else 0

    @property
    def rating_count(self):
        return self.reviews.count()

    @property
    def industry(self):
        return self.category.id if self.category else None


class Deployment(models.Model):
    """
    Deployment of marketplace model to consortium.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        REMOVED = "removed", "Removed"

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
        on_delete=models.SET_NULL,
        null=True,
        related_name="deployments",
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    # Configuration
    config = models.JSONField(default=dict, blank=True)

    # Timestamps
    deployed_at = models.DateTimeField(auto_now_add=True)
    removed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "deployment"
        verbose_name_plural = "deployments"
        ordering = ["-deployed_at"]
        unique_together = ["marketplace_model", "consortium"]
        indexes = [
            models.Index(fields=["consortium"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.marketplace_model.name} -> {self.consortium.name}"


class Review(models.Model):
    """
    User review of a marketplace model.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    marketplace_model = models.ForeignKey(
        MarketplaceModel,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    reviewer = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    consortium = models.ForeignKey(
        "consortiums.Consortium",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="model_reviews",
    )

    # Review content
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    title = models.CharField(max_length=100, blank=True)
    comment = models.TextField(blank=True, max_length=1000)

    # Engagement
    helpful_count = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "review"
        verbose_name_plural = "reviews"
        unique_together = ["marketplace_model", "reviewer"]
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["marketplace_model"]),
            models.Index(fields=["rating"]),
        ]

    def __str__(self):
        return f"{self.reviewer.name}: {self.rating}/5 for {self.marketplace_model.name}"

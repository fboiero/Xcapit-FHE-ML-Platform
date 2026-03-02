"""
Core models for Xcapit FHE-ML Platform.

Custom User model and Company model for multi-tenant API access.
"""

import secrets
import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from encrypted_model_fields.fields import EncryptedCharField


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""

    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user."""
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model using email as the unique identifier.

    Extends AbstractBaseUser for secure password handling and PermissionsMixin
    for Django's permission system integration.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)

    # Company association (multi-tenant)
    company = models.ForeignKey(
        "Company",
        on_delete=models.CASCADE,
        related_name="users",
        null=True,
        blank=True,
    )

    # Status
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"
        ordering = ["-date_joined"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["company"]),
        ]

    def __str__(self):
        return self.email

    def get_full_name(self):
        """Return the full name of the user."""
        return f"{self.first_name} {self.last_name}".strip() or self.email

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name or self.email.split("@")[0]


class Company(models.Model):
    """
    Company model for multi-tenant API access.

    Companies own API keys and participate in consortiums.
    """

    class Tier(models.TextChoices):
        FREE = "free", "Free"
        STARTER = "starter", "Starter"
        PROFESSIONAL = "professional", "Professional"
        ENTERPRISE = "enterprise", "Enterprise"

    # Rate limits per tier (requests per minute)
    TIER_RATE_LIMITS = {
        "free": 10,
        "starter": 100,
        "professional": 500,
        "enterprise": 2000,
    }

    # Daily request limits per tier
    TIER_DAILY_LIMITS = {
        "free": 100,
        "starter": 5000,
        "professional": 50000,
        "enterprise": -1,  # Unlimited
    }

    # Max models per tier
    TIER_MODEL_LIMITS = {
        "free": 2,
        "starter": 10,
        "professional": 50,
        "enterprise": -1,  # Unlimited
    }

    # Max consortiums per tier
    TIER_CONSORTIUM_LIMITS = {
        "free": 1,
        "starter": 5,
        "professional": 20,
        "enterprise": -1,  # Unlimited
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, db_index=True)

    # Subscription tier
    tier = models.CharField(
        max_length=20,
        choices=Tier.choices,
        default=Tier.FREE,
        db_index=True,
    )

    # Custom rate limits (override tier defaults)
    custom_rate_limit = models.IntegerField(null=True, blank=True)
    custom_daily_limit = models.IntegerField(null=True, blank=True)

    # Metadata
    industry = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "company"
        verbose_name_plural = "companies"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["tier"]),
        ]

    def __str__(self):
        return self.name

    @property
    def rate_limit(self) -> int:
        """Get rate limit (requests per minute) for this company."""
        if self.custom_rate_limit is not None:
            return self.custom_rate_limit
        return self.TIER_RATE_LIMITS.get(self.tier, 10)

    @property
    def daily_limit(self) -> int:
        """Get daily request limit for this company. -1 means unlimited."""
        if self.custom_daily_limit is not None:
            return self.custom_daily_limit
        return self.TIER_DAILY_LIMITS.get(self.tier, 100)

    @property
    def model_limit(self) -> int:
        """Get max models limit for this company. -1 means unlimited."""
        return self.TIER_MODEL_LIMITS.get(self.tier, 2)

    @property
    def consortium_limit(self) -> int:
        """Get max consortiums limit for this company. -1 means unlimited."""
        return self.TIER_CONSORTIUM_LIMITS.get(self.tier, 1)

    def can_create_model(self) -> bool:
        """Check if company can create more models."""
        if self.model_limit == -1:
            return True
        return self.models.count() < self.model_limit

    def can_join_consortium(self) -> bool:
        """Check if company can join more consortiums."""
        if self.consortium_limit == -1:
            return True
        # Count through memberships
        from apps.consortiums.models import ConsortiumMember

        current_count = ConsortiumMember.objects.filter(
            company=self, status="active"
        ).count()
        return current_count < self.consortium_limit


class APIKey(models.Model):
    """
    API Key model for programmatic access.

    Keys are hashed using SHA-256 before storage.
    """

    PREFIX = "fheml"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    key_hash = models.CharField(max_length=64, unique=True, db_index=True)

    # Association
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="api_keys",
    )
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_api_keys",
    )

    # Key prefix (first 8 chars, for identification without exposing the full key)
    prefix = models.CharField(max_length=20, blank=True, default="")

    # Permissions
    PERMISSION_CHOICES = [
        ("read", "Read"),
        ("write", "Write"),
        ("admin", "Admin"),
    ]
    permissions = models.JSONField(default=list)  # List of permissions

    # Rate limiting
    rate_limit = models.IntegerField(default=100)  # requests per minute

    # Status
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "API key"
        verbose_name_plural = "API keys"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["key_hash"]),
            models.Index(fields=["company"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.company.name})"

    @classmethod
    def generate_key(cls):
        """Generate a new API key.

        Returns:
            Tuple of (raw_key, key_hash)
        """
        import hashlib

        random_part = secrets.token_urlsafe(32)
        raw_key = f"{cls.PREFIX}_{random_part}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        return raw_key, key_hash

    @classmethod
    def hash_key(cls, raw_key):
        """Hash an API key using SHA-256."""
        import hashlib

        return hashlib.sha256(raw_key.encode()).hexdigest()

    def has_permission(self, permission):
        """Check if key has a specific permission."""
        return permission in self.permissions or "admin" in self.permissions

    def update_last_used(self):
        """Update last_used_at timestamp."""
        self.last_used_at = timezone.now()
        self.save(update_fields=["last_used_at"])


class AuditLog(models.Model):
    """
    Audit log for security-sensitive operations.

    All API operations are logged with actor, action, and context.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Actor
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_logs",
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_logs",
    )
    api_key_name = models.CharField(max_length=255, blank=True)

    # Action
    action = models.CharField(max_length=100, db_index=True)
    resource_type = models.CharField(max_length=100, db_index=True)
    resource_id = models.CharField(max_length=255, blank=True)

    # Context (sanitized - no PII)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    response_status = models.IntegerField(null=True, blank=True)

    # Additional data (JSON, sanitized)
    extra_data = models.JSONField(default=dict, blank=True)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "audit log"
        verbose_name_plural = "audit logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["action"]),
            models.Index(fields=["resource_type"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["company"]),
        ]

    def __str__(self):
        return f"{self.action} - {self.resource_type} - {self.created_at}"

    @classmethod
    def log(cls, request, action, resource_type, resource_id="", extra_data=None):
        """Create an audit log entry from a request."""
        user = request.user if request.user.is_authenticated else None
        company = getattr(user, "company", None)

        # Get API key name if used
        api_key_name = ""
        if hasattr(request, "auth") and hasattr(request.auth, "name"):
            api_key_name = request.auth.name

        # Sanitize user agent
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]

        return cls.objects.create(
            user=user,
            company=company,
            api_key_name=api_key_name,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id),
            ip_address=cls._get_client_ip(request),
            user_agent=user_agent,
            request_path=request.path[:500],
            request_method=request.method,
            extra_data=extra_data or {},
        )

    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request, handling proxies."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip


class UsageTracking(models.Model):
    """
    Daily usage tracking for rate limiting and billing.

    Aggregated counts reset daily.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="usage_tracking",
    )

    # Date for aggregation
    date = models.DateField(db_index=True)

    # Request counts
    api_requests = models.IntegerField(default=0)
    predictions = models.IntegerField(default=0)
    training_runs = models.IntegerField(default=0)
    data_uploads_bytes = models.BigIntegerField(default=0)

    # Rate limit violations
    rate_limit_hits = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "usage tracking"
        verbose_name_plural = "usage tracking"
        unique_together = ["company", "date"]
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["company", "date"]),
            models.Index(fields=["date"]),
        ]

    def __str__(self):
        return f"{self.company.name} - {self.date}"

    @classmethod
    def get_or_create_today(cls, company):
        """Get or create today's usage tracking record."""
        today = timezone.now().date()
        tracking, _ = cls.objects.get_or_create(
            company=company,
            date=today,
        )
        return tracking

    def increment_requests(self, count=1):
        """Increment API request count atomically."""
        from django.db.models import F

        cls = self.__class__
        cls.objects.filter(pk=self.pk).update(api_requests=F("api_requests") + count)
        self.refresh_from_db()

    def increment_predictions(self, count=1):
        """Increment prediction count atomically."""
        from django.db.models import F

        cls = self.__class__
        cls.objects.filter(pk=self.pk).update(predictions=F("predictions") + count)
        self.refresh_from_db()

    def increment_rate_limit_hits(self, count=1):
        """Increment rate limit hit count atomically."""
        from django.db.models import F

        cls = self.__class__
        cls.objects.filter(pk=self.pk).update(rate_limit_hits=F("rate_limit_hits") + count)
        self.refresh_from_db()

    def check_daily_limit(self) -> bool:
        """Check if company is within daily limit. Returns True if allowed."""
        limit = self.company.daily_limit
        if limit == -1:  # Unlimited
            return True
        return self.api_requests < limit


class Webhook(models.Model):
    """
    Webhook configuration for event notifications.

    Companies can register webhooks to receive notifications about
    platform events (model trained, prediction made, etc.).
    """

    class EventType(models.TextChoices):
        # Model events
        MODEL_CREATED = "model.created", "Model Created"
        MODEL_TRAINED = "model.trained", "Model Trained"
        MODEL_FAILED = "model.failed", "Model Training Failed"
        MODEL_DELETED = "model.deleted", "Model Deleted"
        MODEL_VERSION_CREATED = "model.version.created", "Model Version Created"

        # Prediction events
        PREDICTION_COMPLETED = "prediction.completed", "Prediction Completed"
        BATCH_COMPLETED = "batch.completed", "Batch Prediction Completed"
        BATCH_FAILED = "batch.failed", "Batch Prediction Failed"

        # Consortium events
        CONSORTIUM_JOINED = "consortium.joined", "Joined Consortium"
        CONSORTIUM_LEFT = "consortium.left", "Left Consortium"
        MEMBER_ADDED = "consortium.member.added", "Member Added"
        MEMBER_REMOVED = "consortium.member.removed", "Member Removed"

        # Governance events
        PROPOSAL_CREATED = "governance.proposal.created", "Proposal Created"
        PROPOSAL_VOTED = "governance.proposal.voted", "Proposal Voted"
        PROPOSAL_PASSED = "governance.proposal.passed", "Proposal Passed"
        PROPOSAL_REJECTED = "governance.proposal.rejected", "Proposal Rejected"

        # Data events
        DATA_UPLOADED = "data.uploaded", "Data Uploaded"
        DATA_VALIDATED = "data.validated", "Data Validated"

        # Security events
        API_KEY_CREATED = "security.apikey.created", "API Key Created"
        API_KEY_REVOKED = "security.apikey.revoked", "API Key Revoked"
        RATE_LIMIT_EXCEEDED = "security.ratelimit.exceeded", "Rate Limit Exceeded"

        # All events
        ALL = "*", "All Events"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="webhooks",
    )

    # Webhook configuration
    name = models.CharField(max_length=255)
    url = models.URLField(max_length=2000)
    secret = EncryptedCharField(max_length=255)  # For HMAC signature (encrypted at rest)

    # Event filtering
    events = models.JSONField(default=list)  # List of EventType values

    # Optional headers
    custom_headers = models.JSONField(default=dict, blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)

    # Retry configuration
    max_retries = models.IntegerField(default=3)
    timeout_seconds = models.IntegerField(default=30)

    # Statistics
    total_deliveries = models.IntegerField(default=0)
    successful_deliveries = models.IntegerField(default=0)
    failed_deliveries = models.IntegerField(default=0)
    last_delivery_at = models.DateTimeField(null=True, blank=True)
    last_success_at = models.DateTimeField(null=True, blank=True)
    last_failure_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "webhook"
        verbose_name_plural = "webhooks"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["company"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.company.name})"

    def should_receive_event(self, event_type: str) -> bool:
        """Check if webhook should receive a specific event type."""
        if not self.is_active:
            return False
        if "*" in self.events:
            return True
        return event_type in self.events

    def generate_signature(self, payload: str) -> str:
        """Generate HMAC-SHA256 signature for payload."""
        import hashlib
        import hmac

        return hmac.new(
            self.secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

    def update_stats(self, success: bool, error: str = ""):
        """Update webhook delivery statistics."""
        from django.db.models import F

        now = timezone.now()
        updates = {
            "total_deliveries": F("total_deliveries") + 1,
            "last_delivery_at": now,
        }

        if success:
            updates["successful_deliveries"] = F("successful_deliveries") + 1
            updates["last_success_at"] = now
            updates["last_error"] = ""
        else:
            updates["failed_deliveries"] = F("failed_deliveries") + 1
            updates["last_failure_at"] = now
            updates["last_error"] = error[:1000]

        Webhook.objects.filter(pk=self.pk).update(**updates)
        self.refresh_from_db()


class WebhookDelivery(models.Model):
    """
    Record of a webhook delivery attempt.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        DELIVERED = "delivered", "Delivered"
        FAILED = "failed", "Failed"
        RETRYING = "retrying", "Retrying"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    webhook = models.ForeignKey(
        Webhook,
        on_delete=models.CASCADE,
        related_name="deliveries",
    )

    # Event info
    event_type = models.CharField(max_length=100, db_index=True)
    event_id = models.CharField(max_length=255, blank=True)  # Reference ID
    payload = models.JSONField(default=dict)

    # Delivery status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    attempt_count = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)

    # Response details
    response_status_code = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    response_headers = models.JSONField(default=dict, blank=True)
    latency_ms = models.FloatField(null=True, blank=True)

    # Error tracking
    error_message = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    next_retry_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "webhook delivery"
        verbose_name_plural = "webhook deliveries"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["webhook"]),
            models.Index(fields=["event_type"]),
            models.Index(fields=["status"]),
            models.Index(fields=["next_retry_at"]),
        ]

    def __str__(self):
        return f"{self.event_type} to {self.webhook.name}"

    def mark_delivered(self, status_code: int, body: str, latency_ms: float):
        """Mark delivery as successful."""
        self.status = self.Status.DELIVERED
        self.response_status_code = status_code
        self.response_body = body[:10000]
        self.latency_ms = latency_ms
        self.delivered_at = timezone.now()
        self.attempt_count += 1
        self.save()
        self.webhook.update_stats(success=True)

    def mark_failed(self, error: str, status_code: int = None, retry: bool = True):
        """Mark delivery as failed, optionally scheduling retry."""
        import datetime

        self.attempt_count += 1
        self.error_message = error[:1000]
        if status_code:
            self.response_status_code = status_code

        if retry and self.attempt_count < self.max_attempts:
            self.status = self.Status.RETRYING
            # Exponential backoff: 1min, 5min, 15min
            backoff_minutes = [1, 5, 15]
            delay = backoff_minutes[min(self.attempt_count - 1, len(backoff_minutes) - 1)]
            self.next_retry_at = timezone.now() + datetime.timedelta(minutes=delay)
        else:
            self.status = self.Status.FAILED

        self.save()
        self.webhook.update_stats(success=False, error=error)


class Report(models.Model):
    """
    Generated report for analytics and compliance.

    Reports can be generated on-demand or scheduled.
    """

    class ReportType(models.TextChoices):
        PERFORMANCE = "performance", "Performance Report"
        COMPLIANCE = "compliance", "Compliance Report"
        CONSORTIUM = "consortium", "Consortium Report"
        USAGE = "usage", "Usage Report"
        AUDIT = "audit", "Audit Report"
        CUSTOM = "custom", "Custom Report"

    class Format(models.TextChoices):
        PDF = "pdf", "PDF"
        CSV = "csv", "CSV"
        JSON = "json", "JSON"
        EXCEL = "excel", "Excel"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        GENERATING = "generating", "Generating"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="reports",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_reports",
    )

    # Report configuration
    name = models.CharField(max_length=255)
    report_type = models.CharField(
        max_length=50,
        choices=ReportType.choices,
        db_index=True,
    )
    format = models.CharField(
        max_length=20,
        choices=Format.choices,
        default=Format.PDF,
    )

    # Date range
    date_from = models.DateField(null=True, blank=True)
    date_to = models.DateField(null=True, blank=True)

    # Sections to include
    sections = models.JSONField(default=list)  # List of section names

    # Filters and parameters
    parameters = models.JSONField(default=dict, blank=True)

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    # Output
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    download_url = models.URLField(max_length=2000, blank=True)
    download_expires_at = models.DateTimeField(null=True, blank=True)

    # Error tracking
    error_message = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "report"
        verbose_name_plural = "reports"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["company"]),
            models.Index(fields=["report_type"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.report_type})"

    def mark_generating(self):
        """Mark report as generating."""
        self.status = self.Status.GENERATING
        self.save(update_fields=["status", "updated_at"])

    def mark_completed(self, file_path: str, file_size: int, download_url: str = ""):
        """Mark report as completed."""
        import datetime

        self.status = self.Status.COMPLETED
        self.file_path = file_path
        self.file_size = file_size
        self.download_url = download_url
        self.completed_at = timezone.now()
        # Download URL expires in 24 hours
        self.download_expires_at = timezone.now() + datetime.timedelta(hours=24)
        self.save()

    def mark_failed(self, error: str):
        """Mark report as failed."""
        self.status = self.Status.FAILED
        self.error_message = error[:1000]
        self.save()


class Workflow(models.Model):
    """
    Workflow automation configuration.

    Workflows define a series of steps to execute in sequence or parallel.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        ARCHIVED = "archived", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="workflows",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_workflows",
    )

    # Workflow definition
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Steps configuration (JSON array of step definitions)
    # Each step: {type, name, config, on_success, on_failure}
    steps = models.JSONField(default=list)

    # Trigger configuration
    # {type: "manual"|"schedule"|"event", schedule: "0 0 * * *", event: "model.trained"}
    trigger = models.JSONField(default=dict)

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )

    # Statistics
    total_runs = models.IntegerField(default=0)
    successful_runs = models.IntegerField(default=0)
    failed_runs = models.IntegerField(default=0)
    last_run_at = models.DateTimeField(null=True, blank=True)
    last_success_at = models.DateTimeField(null=True, blank=True)
    last_failure_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "workflow"
        verbose_name_plural = "workflows"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["company"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.status})"

    @property
    def success_rate(self) -> float:
        """Calculate workflow success rate."""
        if self.total_runs == 0:
            return 0.0
        return (self.successful_runs / self.total_runs) * 100

    def update_stats(self, success: bool):
        """Update workflow run statistics."""
        from django.db.models import F

        now = timezone.now()
        updates = {
            "total_runs": F("total_runs") + 1,
            "last_run_at": now,
        }

        if success:
            updates["successful_runs"] = F("successful_runs") + 1
            updates["last_success_at"] = now
        else:
            updates["failed_runs"] = F("failed_runs") + 1
            updates["last_failure_at"] = now

        Workflow.objects.filter(pk=self.pk).update(**updates)
        self.refresh_from_db()


class WorkflowRun(models.Model):
    """
    Record of a workflow execution.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name="runs",
    )
    triggered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="triggered_workflow_runs",
    )

    # Trigger info
    trigger_type = models.CharField(max_length=50)  # manual, schedule, event
    trigger_event = models.CharField(max_length=255, blank=True)

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    # Step execution log
    # [{step_name, status, started_at, completed_at, output, error}]
    step_logs = models.JSONField(default=list)
    current_step = models.IntegerField(default=0)

    # Input/output
    input_data = models.JSONField(default=dict, blank=True)
    output_data = models.JSONField(default=dict, blank=True)

    # Error tracking
    error_message = models.TextField(blank=True)

    # Duration
    duration_seconds = models.FloatField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "workflow run"
        verbose_name_plural = "workflow runs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["workflow"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.workflow.name} run ({self.status})"

    def start(self):
        """Mark run as started."""
        self.status = self.Status.RUNNING
        self.started_at = timezone.now()
        self.save(update_fields=["status", "started_at"])

    def complete(self, output_data: dict = None):
        """Mark run as completed."""
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.output_data = output_data or {}
        if self.started_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
        self.save()
        self.workflow.update_stats(success=True)

    def fail(self, error: str):
        """Mark run as failed."""
        self.status = self.Status.FAILED
        self.completed_at = timezone.now()
        self.error_message = error[:1000]
        if self.started_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
        self.save()
        self.workflow.update_stats(success=False)

    def log_step(self, step_name: str, status: str, output: dict = None, error: str = ""):
        """Log a step execution."""
        step_log = {
            "step_name": step_name,
            "status": status,
            "timestamp": timezone.now().isoformat(),
            "output": output or {},
            "error": error,
        }
        self.step_logs.append(step_log)
        self.current_step = len(self.step_logs)
        self.save(update_fields=["step_logs", "current_step"])


class ScheduledTask(models.Model):
    """
    Scheduled task configuration for recurring jobs.

    Tasks can be scheduled using cron expressions.
    """

    class TaskType(models.TextChoices):
        REPORT = "report", "Generate Report"
        WORKFLOW = "workflow", "Run Workflow"
        DATA_SYNC = "data_sync", "Data Sync"
        CLEANUP = "cleanup", "Cleanup"
        BACKUP = "backup", "Backup"
        CUSTOM = "custom", "Custom Task"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        DISABLED = "disabled", "Disabled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="scheduled_tasks",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_scheduled_tasks",
    )

    # Task definition
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    task_type = models.CharField(
        max_length=50,
        choices=TaskType.choices,
        db_index=True,
    )

    # Schedule (cron expression)
    # Format: minute hour day month day_of_week
    cron_expression = models.CharField(max_length=100)

    # Timezone for scheduling
    timezone = models.CharField(max_length=100, default="UTC")

    # Task configuration
    # {report_id, workflow_id, or custom config}
    config = models.JSONField(default=dict)

    # Related objects (optional)
    report = models.ForeignKey(
        Report,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scheduled_tasks",
    )
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scheduled_tasks",
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )

    # Scheduling
    next_run_at = models.DateTimeField(null=True, blank=True)
    last_run_at = models.DateTimeField(null=True, blank=True)

    # Statistics
    total_runs = models.IntegerField(default=0)
    successful_runs = models.IntegerField(default=0)
    failed_runs = models.IntegerField(default=0)
    consecutive_failures = models.IntegerField(default=0)

    # Auto-disable after N consecutive failures (0 = never)
    max_consecutive_failures = models.IntegerField(default=5)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "scheduled task"
        verbose_name_plural = "scheduled tasks"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["company"]),
            models.Index(fields=["task_type"]),
            models.Index(fields=["status"]),
            models.Index(fields=["next_run_at"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.cron_expression})"

    def calculate_next_run(self):
        """Calculate the next run time based on cron expression."""
        try:
            from croniter import croniter
            import pytz

            tz = pytz.timezone(self.timezone)
            now = timezone.now().astimezone(tz)
            cron = croniter(self.cron_expression, now)
            self.next_run_at = cron.get_next(timezone.datetime)
            self.save(update_fields=["next_run_at"])
        except Exception:
            # If croniter is not available, skip calculation
            pass

    def update_stats(self, success: bool):
        """Update task run statistics."""
        from django.db.models import F

        now = timezone.now()
        updates = {
            "total_runs": F("total_runs") + 1,
            "last_run_at": now,
        }

        if success:
            updates["successful_runs"] = F("successful_runs") + 1
            updates["consecutive_failures"] = 0
        else:
            updates["failed_runs"] = F("failed_runs") + 1
            updates["consecutive_failures"] = F("consecutive_failures") + 1

        ScheduledTask.objects.filter(pk=self.pk).update(**updates)
        self.refresh_from_db()

        # Check for auto-disable
        if (
            not success
            and self.max_consecutive_failures > 0
            and self.consecutive_failures >= self.max_consecutive_failures
        ):
            self.status = self.Status.DISABLED
            self.save(update_fields=["status"])

        # Calculate next run time
        self.calculate_next_run()


class ScheduledTaskRun(models.Model):
    """
    Record of a scheduled task execution.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        SKIPPED = "skipped", "Skipped"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    task = models.ForeignKey(
        ScheduledTask,
        on_delete=models.CASCADE,
        related_name="runs",
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    # Scheduled vs actual
    scheduled_at = models.DateTimeField()
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Duration
    duration_seconds = models.FloatField(null=True, blank=True)

    # Output
    output = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)

    # Related run (if applicable)
    workflow_run = models.ForeignKey(
        WorkflowRun,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scheduled_task_runs",
    )
    report = models.ForeignKey(
        Report,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scheduled_task_runs",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "scheduled task run"
        verbose_name_plural = "scheduled task runs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["task"]),
            models.Index(fields=["status"]),
            models.Index(fields=["scheduled_at"]),
        ]

    def __str__(self):
        return f"{self.task.name} run ({self.status})"

    def start(self):
        """Mark run as started."""
        self.status = self.Status.RUNNING
        self.started_at = timezone.now()
        self.save(update_fields=["status", "started_at"])

    def complete(self, output: dict = None):
        """Mark run as completed."""
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.output = output or {}
        if self.started_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
        self.save()
        self.task.update_stats(success=True)

    def fail(self, error: str):
        """Mark run as failed."""
        self.status = self.Status.FAILED
        self.completed_at = timezone.now()
        self.error_message = error[:1000]
        if self.started_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
        self.save()
        self.task.update_stats(success=False)

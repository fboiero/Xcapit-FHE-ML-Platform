"""
Core models for Xcapit FHE-ML Platform.

Custom User model and Company model for multi-tenant API access.
"""

import secrets
import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, db_index=True)

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
        ]

    def __str__(self):
        return self.name


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

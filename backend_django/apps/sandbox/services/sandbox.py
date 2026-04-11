"""
Sandbox management service.

Handles:
- Sandbox lifecycle management
- Expiration and archival
- Resource limits
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from django.db import transaction
from django.utils import timezone

from apps.core.services.base import BaseService, ServiceResult

if TYPE_CHECKING:
    from apps.core.models import Company
    from apps.sandbox.models import Sandbox

logger = logging.getLogger(__name__)


class SandboxService(BaseService):
    """
    Service for managing sandbox environments.

    Provides operations for:
    - Creating and configuring sandboxes
    - Managing sandbox lifecycle (extend, archive)
    - Enforcing resource limits
    """

    # Default limits
    MAX_EXTENSION_DAYS = 30
    MAX_ACTIVE_SANDBOXES_PER_COMPANY = 10
    DEFAULT_SANDBOX_DURATION_DAYS = 14

    def create_sandbox(
        self,
        company: Company,
        name: str,
        industry: str,
        template_id: str | None = None,
        duration_days: int | None = None,
    ) -> ServiceResult[Sandbox]:
        """
        Create a new sandbox environment.

        Args:
            company: Owner company
            name: Sandbox name
            industry: Industry vertical
            template_id: Optional template to initialize from
            duration_days: Days until expiration

        Returns:
            ServiceResult with created sandbox
        """
        from apps.sandbox.models import Sandbox, SandboxTemplate

        # Check active sandbox limit
        active_count = Sandbox.objects.filter(
            owner=company,
            status=Sandbox.Status.ACTIVE,
        ).count()

        if active_count >= self.MAX_ACTIVE_SANDBOXES_PER_COMPANY:
            return ServiceResult.fail(
                f"Maximum active sandboxes ({self.MAX_ACTIVE_SANDBOXES_PER_COMPANY}) reached",
                error_code="limit_exceeded",
            )

        # Calculate expiration
        duration = duration_days or self.DEFAULT_SANDBOX_DURATION_DAYS
        expires_at = timezone.now() + timedelta(days=duration)

        # Get template configuration if provided
        config = {}
        if template_id:
            try:
                template = SandboxTemplate.objects.get(id=template_id)
                config = template.default_config or {}
                if not industry:
                    industry = template.industry
            except SandboxTemplate.DoesNotExist:
                return ServiceResult.fail(
                    "Template not found",
                    error_code="not_found",
                )

        # Create sandbox
        with transaction.atomic():
            sandbox = Sandbox.objects.create(
                owner=company,
                name=name,
                industry=industry,
                expires_at=expires_at,
                config=config,
            )

            logger.info(f"Created sandbox {sandbox.id} for company {company.id}")

            return ServiceResult.ok(sandbox)

    def extend_sandbox(
        self,
        sandbox: Sandbox,
        days: int,
    ) -> ServiceResult[Sandbox]:
        """
        Extend sandbox expiration.

        Args:
            sandbox: The sandbox to extend
            days: Number of days to extend

        Returns:
            ServiceResult with updated sandbox
        """
        from apps.sandbox.models import Sandbox

        if sandbox.status == Sandbox.Status.ARCHIVED:
            return ServiceResult.fail(
                "Cannot extend archived sandbox",
                error_code="invalid_status",
            )

        if days <= 0:
            return ServiceResult.fail(
                "Extension days must be positive",
                error_code="validation_error",
            )

        if days > self.MAX_EXTENSION_DAYS:
            return ServiceResult.fail(
                f"Maximum extension is {self.MAX_EXTENSION_DAYS} days",
                error_code="limit_exceeded",
            )

        sandbox.expires_at = sandbox.expires_at + timedelta(days=days)
        sandbox.save(update_fields=["expires_at", "updated_at"])

        logger.info(f"Extended sandbox {sandbox.id} by {days} days")

        return ServiceResult.ok(sandbox)

    def archive_sandbox(self, sandbox: Sandbox) -> ServiceResult[Sandbox]:
        """
        Archive a sandbox.

        Args:
            sandbox: The sandbox to archive

        Returns:
            ServiceResult with archived sandbox
        """
        from apps.sandbox.models import Sandbox

        if sandbox.status == Sandbox.Status.ARCHIVED:
            return ServiceResult.fail(
                "Sandbox is already archived",
                error_code="invalid_status",
            )

        sandbox.status = Sandbox.Status.ARCHIVED
        sandbox.save(update_fields=["status", "updated_at"])

        logger.info(f"Archived sandbox {sandbox.id}")

        return ServiceResult.ok(sandbox)

    def get_sandbox_summary(self, sandbox: Sandbox) -> dict[str, Any]:
        """
        Get summary information about a sandbox.

        Args:
            sandbox: The sandbox to summarize

        Returns:
            Dictionary with sandbox summary
        """
        from apps.sandbox.models import Experiment, SyntheticDataset

        datasets = SyntheticDataset.objects.filter(sandbox=sandbox)
        experiments = Experiment.objects.filter(sandbox=sandbox)

        return {
            "id": str(sandbox.id),
            "name": sandbox.name,
            "industry": sandbox.industry,
            "status": sandbox.status,
            "is_expired": sandbox.is_expired,
            "expires_at": sandbox.expires_at.isoformat(),
            "created_at": sandbox.created_at.isoformat(),
            "datasets": {
                "total": datasets.count(),
                "total_records": sum(d.record_count for d in datasets),
            },
            "experiments": {
                "total": experiments.count(),
                "by_status": {
                    "pending": experiments.filter(status=Experiment.Status.PENDING).count(),
                    "running": experiments.filter(status=Experiment.Status.RUNNING).count(),
                    "completed": experiments.filter(status=Experiment.Status.COMPLETED).count(),
                    "failed": experiments.filter(status=Experiment.Status.FAILED).count(),
                },
            },
        }

    def cleanup_expired_sandboxes(self) -> ServiceResult[int]:
        """
        Archive all expired sandboxes.

        This should be called periodically (e.g., via Celery task).

        Returns:
            ServiceResult with count of archived sandboxes
        """
        from apps.sandbox.models import Sandbox

        now = timezone.now()
        expired = Sandbox.objects.filter(
            status=Sandbox.Status.ACTIVE,
            expires_at__lt=now,
        )

        count = expired.count()
        expired.update(status=Sandbox.Status.ARCHIVED)

        if count > 0:
            logger.info(f"Archived {count} expired sandboxes")

        return ServiceResult.ok(count)

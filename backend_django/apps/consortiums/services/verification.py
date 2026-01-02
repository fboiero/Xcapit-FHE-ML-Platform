"""
Contribution verification service for Xcapit FHE-ML Platform.

Handles automatic verification of data contribution proofs.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from apps.core.services.base import BaseService, ServiceResult

if TYPE_CHECKING:
    from apps.consortiums.models import ContributionProof

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """Result of a verification check."""

    valid: bool
    message: str
    checks: dict[str, bool]


class ContributionVerificationService(BaseService):
    """
    Service for verifying contribution proofs.

    Performs automatic validation of:
    - SHA-256 hash format
    - Record count validity
    - Schema version presence
    - Checksum format
    """

    # SHA-256 hex pattern (64 lowercase hex characters)
    SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

    def verify_contribution(
        self, contribution: ContributionProof
    ) -> ServiceResult[VerificationResult]:
        """
        Verify a contribution proof automatically.

        Args:
            contribution: The contribution proof to verify

        Returns:
            ServiceResult containing VerificationResult
        """
        checks = {}
        errors = []

        # Check 1: Valid SHA-256 data hash
        checks["data_hash_valid"] = self._is_valid_sha256(contribution.data_hash)
        if not checks["data_hash_valid"]:
            errors.append("Invalid SHA-256 data hash format")

        # Check 2: Valid SHA-256 checksum
        checks["checksum_valid"] = self._is_valid_sha256(contribution.checksum)
        if not checks["checksum_valid"]:
            errors.append("Invalid SHA-256 checksum format")

        # Check 3: Record count is positive
        checks["record_count_valid"] = contribution.record_count > 0
        if not checks["record_count_valid"]:
            errors.append("Record count must be greater than 0")

        # Check 4: Feature count is positive
        checks["feature_count_valid"] = contribution.feature_count > 0
        if not checks["feature_count_valid"]:
            errors.append("Feature count must be greater than 0")

        # Check 5: Schema version is present
        checks["schema_version_present"] = bool(
            contribution.schema_version and contribution.schema_version.strip()
        )
        if not checks["schema_version_present"]:
            errors.append("Schema version is required")

        # Check 6: Company is an active member of the consortium
        checks["member_active"] = self._is_active_member(contribution)
        if not checks["member_active"]:
            errors.append("Company is not an active member of the consortium")

        # Determine overall result
        all_valid = all(checks.values())

        if all_valid:
            message = "All verification checks passed"
            # Update contribution status
            contribution.verify(message)
            logger.info(
                "Contribution %s verified successfully",
                contribution.id,
                extra={"contribution_id": str(contribution.id), "checks": checks},
            )
        else:
            message = "; ".join(errors)
            contribution.fail_verification(message)
            logger.warning(
                "Contribution %s verification failed: %s",
                contribution.id,
                message,
                extra={"contribution_id": str(contribution.id), "checks": checks},
            )

        result = VerificationResult(
            valid=all_valid,
            message=message,
            checks=checks,
        )

        return ServiceResult.ok(result)

    def _is_valid_sha256(self, hash_value: str) -> bool:
        """Check if a string is a valid SHA-256 hex hash."""
        if not hash_value:
            return False
        return bool(self.SHA256_PATTERN.match(hash_value.lower()))

    def _is_active_member(self, contribution: ContributionProof) -> bool:
        """Check if the contributing company is an active consortium member."""
        from apps.consortiums.models import ConsortiumMember

        return ConsortiumMember.objects.filter(
            consortium=contribution.consortium,
            company=contribution.company,
            status=ConsortiumMember.Status.ACTIVE,
        ).exists()

"""
Blockchain registration service for Xcapit FHE-ML Platform.

Handles registration of contributions and training results
on the Arbitrum blockchain for immutable audit trails.
"""

from __future__ import annotations

import hashlib
import logging
from typing import TYPE_CHECKING, Any

from apps.core.services.base import BaseService, ServiceResult
from django.conf import settings
from django.utils import timezone

if TYPE_CHECKING:
    from apps.consortiums.models import ContributionProof, TrainingResult

logger = logging.getLogger(__name__)


class BlockchainRegistrationService(BaseService):
    """
    Service for registering consortium data on the blockchain.

    Uses the SDK's blockchain module to interact with
    Arbitrum smart contracts for immutable audit trails.
    """

    def __init__(self, request=None):
        super().__init__(request)
        self.blockchain_config = getattr(settings, "BLOCKCHAIN_CONFIG", {})
        self.network = self.blockchain_config.get("network", "arbitrum-sepolia")
        self.chain_id = self.blockchain_config.get("chain_id", 421614)
        self.model_registry_address = self.blockchain_config.get("model_registry", "")

    def register_contribution(
        self, contribution: ContributionProof
    ) -> ServiceResult[dict[str, Any]]:
        """
        Register a contribution proof on the blockchain.

        Records:
        - Data hash
        - Record count
        - Consortium ID
        - Contributor company ID

        Args:
            contribution: The contribution proof to register

        Returns:
            ServiceResult with transaction hash
        """
        if contribution.blockchain_tx:
            return ServiceResult.fail(
                "Contribution already registered on blockchain",
                error_code="already_registered",
            )

        if contribution.verification_status != contribution.VerificationStatus.VERIFIED:
            return ServiceResult.fail(
                "Only verified contributions can be registered",
                error_code="not_verified",
            )

        try:
            # Prepare data for blockchain registration
            registration_data = {
                "contribution_id": str(contribution.id),
                "consortium_id": str(contribution.consortium_id),
                "company_id": str(contribution.company_id),
                "data_hash": contribution.data_hash,
                "checksum": contribution.checksum,
                "record_count": contribution.record_count,
                "feature_count": contribution.feature_count,
                "timestamp": contribution.created_at.isoformat(),
            }

            # Generate combined hash for on-chain storage
            combined_hash = self._generate_registration_hash(registration_data)

            # Register on blockchain
            tx_hash = self._submit_to_blockchain(
                data_type="contribution",
                data_hash=combined_hash,
                metadata=registration_data,
            )

            if tx_hash:
                # Update contribution record
                contribution.blockchain_tx = tx_hash
                contribution.blockchain_registered_at = timezone.now()
                contribution.save(update_fields=[
                    "blockchain_tx",
                    "blockchain_registered_at",
                ])

                logger.info(
                    "Contribution %s registered on blockchain: %s",
                    contribution.id,
                    tx_hash,
                    extra={
                        "contribution_id": str(contribution.id),
                        "tx_hash": tx_hash,
                        "network": self.network,
                    },
                )

                return ServiceResult.ok({
                    "tx_hash": tx_hash,
                    "network": self.network,
                    "chain_id": self.chain_id,
                    "combined_hash": combined_hash,
                    "explorer_url": self._get_explorer_url(tx_hash),
                })
            else:
                return ServiceResult.fail(
                    "Failed to submit to blockchain",
                    error_code="submission_failed",
                )

        except Exception as e:
            logger.exception(
                "Failed to register contribution %s: %s",
                contribution.id,
                str(e),
            )
            return ServiceResult.fail(
                f"Blockchain registration failed: {str(e)}",
                error_code="blockchain_error",
            )

    def register_training_result(
        self, training_result: TrainingResult
    ) -> ServiceResult[dict[str, Any]]:
        """
        Register a training result on the blockchain.

        Records:
        - Model hash
        - Training metrics
        - Consortium ID
        - Contribution count

        Args:
            training_result: The training result to register

        Returns:
            ServiceResult with transaction hash
        """
        if training_result.blockchain_tx:
            return ServiceResult.fail(
                "Training result already registered on blockchain",
                error_code="already_registered",
            )

        if training_result.status != training_result.Status.COMPLETED:
            return ServiceResult.fail(
                "Only completed training results can be registered",
                error_code="not_completed",
            )

        try:
            # Prepare data for blockchain registration
            registration_data = {
                "training_result_id": str(training_result.id),
                "consortium_id": str(training_result.consortium_id),
                "model_hash": training_result.model_hash,
                "accuracy": training_result.accuracy,
                "loss": training_result.loss,
                "epochs_completed": training_result.epochs_completed,
                "contributions_count": training_result.contributions_count,
                "total_records": training_result.total_records,
                "timestamp": training_result.completed_at.isoformat() if training_result.completed_at else None,
            }

            # Generate combined hash for on-chain storage
            combined_hash = self._generate_registration_hash(registration_data)

            # Register on blockchain
            tx_hash = self._submit_to_blockchain(
                data_type="training_result",
                data_hash=combined_hash,
                metadata=registration_data,
            )

            if tx_hash:
                # Update training result record
                training_result.blockchain_tx = tx_hash
                training_result.blockchain_registered_at = timezone.now()
                training_result.save(update_fields=[
                    "blockchain_tx",
                    "blockchain_registered_at",
                ])

                logger.info(
                    "Training result %s registered on blockchain: %s",
                    training_result.id,
                    tx_hash,
                    extra={
                        "training_result_id": str(training_result.id),
                        "tx_hash": tx_hash,
                        "network": self.network,
                    },
                )

                return ServiceResult.ok({
                    "tx_hash": tx_hash,
                    "network": self.network,
                    "chain_id": self.chain_id,
                    "combined_hash": combined_hash,
                    "explorer_url": self._get_explorer_url(tx_hash),
                })
            else:
                return ServiceResult.fail(
                    "Failed to submit to blockchain",
                    error_code="submission_failed",
                )

        except Exception as e:
            logger.exception(
                "Failed to register training result %s: %s",
                training_result.id,
                str(e),
            )
            return ServiceResult.fail(
                f"Blockchain registration failed: {str(e)}",
                error_code="blockchain_error",
            )

    def verify_registration(self, tx_hash: str) -> ServiceResult[dict[str, Any]]:
        """
        Verify a blockchain registration by transaction hash.

        Args:
            tx_hash: The transaction hash to verify

        Returns:
            ServiceResult with verification details
        """
        try:
            # Try to get transaction receipt
            receipt = self._get_transaction_receipt(tx_hash)

            if receipt:
                return ServiceResult.ok({
                    "verified": True,
                    "tx_hash": tx_hash,
                    "block_number": receipt.get("block_number"),
                    "status": receipt.get("status"),
                    "explorer_url": self._get_explorer_url(tx_hash),
                })
            else:
                return ServiceResult.ok({
                    "verified": False,
                    "tx_hash": tx_hash,
                    "message": "Transaction not found or pending",
                })

        except Exception as e:
            return ServiceResult.fail(
                f"Verification failed: {str(e)}",
                error_code="verification_error",
            )

    def _generate_registration_hash(self, data: dict) -> str:
        """
        Generate a deterministic hash from registration data.

        Args:
            data: Dictionary of data to hash

        Returns:
            SHA-256 hash string
        """
        # Sort keys for deterministic ordering
        sorted_data = {k: data[k] for k in sorted(data.keys())}
        data_string = str(sorted_data)
        return hashlib.sha256(data_string.encode()).hexdigest()

    def _submit_to_blockchain(
        self,
        data_type: str,
        data_hash: str,
        metadata: dict,
    ) -> str | None:
        """
        Submit data to the blockchain.

        In production, this uses the SDK's blockchain module.
        For testing/development, returns a mock transaction hash.

        Args:
            data_type: Type of data being registered
            data_hash: Hash of the data
            metadata: Additional metadata

        Returns:
            Transaction hash or None if failed
        """
        try:
            # Try to use SDK blockchain module
            from sdk.blockchain import BlockchainClient

            client = BlockchainClient(
                rpc_url=self.blockchain_config.get("rpc_url"),
                chain_id=self.chain_id,
            )

            tx_hash = client.register_data(
                contract_address=self.model_registry_address,
                data_type=data_type,
                data_hash=data_hash,
            )

            return tx_hash

        except ImportError:
            # SDK not available, generate mock hash for development
            logger.warning("SDK blockchain module not available, using mock transaction")
            mock_hash = "0x" + hashlib.sha256(
                f"{data_type}{data_hash}{timezone.now().isoformat()}".encode()
            ).hexdigest()
            return mock_hash

        except Exception as e:
            logger.error("Blockchain submission failed: %s", str(e))
            return None

    def _get_transaction_receipt(self, tx_hash: str) -> dict | None:
        """
        Get transaction receipt from the blockchain.

        Args:
            tx_hash: Transaction hash

        Returns:
            Receipt dictionary or None
        """
        try:
            from sdk.blockchain import BlockchainClient

            client = BlockchainClient(
                rpc_url=self.blockchain_config.get("rpc_url"),
                chain_id=self.chain_id,
            )

            return client.get_transaction_receipt(tx_hash)

        except ImportError:
            # SDK not available
            return None

        except Exception:
            return None

    def _get_explorer_url(self, tx_hash: str) -> str:
        """
        Get blockchain explorer URL for a transaction.

        Args:
            tx_hash: Transaction hash

        Returns:
            Explorer URL string
        """
        explorer_base = self.blockchain_config.get(
            "explorer",
            "https://sepolia.arbiscan.io",
        )
        return f"{explorer_base}/tx/{tx_hash}"

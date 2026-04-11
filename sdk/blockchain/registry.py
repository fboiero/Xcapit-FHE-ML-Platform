"""Model registry client for the FHE-ML platform.

Provides a high-level API on top of the ModelRegistryContract for
registering, querying, and verifying ML models on-chain.
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Optional

from .connector import BlockchainConnector


# Default ABI for the ModelRegistry contract.
# In production this would be loaded from a compiled artefact.
MODEL_REGISTRY_ABI: list[dict] = [
    {
        "inputs": [
            {"name": "modelHash", "type": "string"},
            {"name": "metadataUri", "type": "string"},
        ],
        "name": "registerModel",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"name": "modelId", "type": "uint256"}],
        "name": "getModel",
        "outputs": [
            {"name": "modelHash", "type": "string"},
            {"name": "metadataUri", "type": "string"},
            {"name": "owner", "type": "address"},
            {"name": "timestamp", "type": "uint256"},
            {"name": "isActive", "type": "bool"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "getModelCount",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"name": "modelId", "type": "uint256"},
            {"name": "newHash", "type": "string"},
        ],
        "name": "updateModel",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]


@dataclass
class ModelRecord:
    """Represents a model registered on-chain."""

    model_id: int
    model_hash: str
    metadata_uri: str
    owner: str
    timestamp: int
    is_active: bool


class ModelRegistryClient:
    """High-level client for the on-chain model registry.

    Example:
        >>> from sdk.blockchain import BlockchainConnector, ModelRegistryClient, Network
        >>> connector = BlockchainConnector(Network.ARBITRUM_SEPOLIA)
        >>> connector.set_account(private_key)
        >>> connector.connect()
        >>> registry = ModelRegistryClient(connector, contract_address)
        >>> tx = registry.register(model_hash, {"version": "1.0"})
    """

    def __init__(
        self,
        connector: BlockchainConnector,
        contract_address: Optional[str] = None,
        abi: Optional[list] = None,
    ):
        """Initialize the registry client.

        Args:
            connector: An active BlockchainConnector.
            contract_address: Address of the deployed ModelRegistry contract.
            abi: Contract ABI. Defaults to the built-in ABI.
        """
        self._connector = connector
        self._contract_address = contract_address
        self._abi = abi or MODEL_REGISTRY_ABI
        self._contract = None

        if contract_address:
            self._contract = connector.get_contract(
                contract_address, self._abi
            )

    def _ensure_contract(self):
        """Ensure contract is available."""
        if self._contract is None:
            raise ValueError(
                "No contract address set. "
                "Pass contract_address to the constructor."
            )

    def register(
        self,
        model_hash: str,
        metadata: Optional[dict] = None,
    ) -> str:
        """Register a model on-chain.

        Args:
            model_hash: SHA-256 hash of the model artefact.
            metadata: Optional metadata dict (serialised to JSON as the URI).

        Returns:
            Transaction hash.
        """
        self._ensure_contract()

        metadata_uri = ""
        if metadata is not None:
            metadata_uri = json.dumps(metadata, sort_keys=True)

        from .contracts import ModelRegistryContract

        registry = ModelRegistryContract(
            self._connector, self._contract_address, self._abi
        )
        return registry.register_model(model_hash, metadata_uri)

    def get(self, model_id: int) -> ModelRecord:
        """Get a model record by ID.

        Args:
            model_id: On-chain model identifier.

        Returns:
            ModelRecord with all on-chain fields.
        """
        self._ensure_contract()

        from .contracts import ModelRegistryContract

        registry = ModelRegistryContract(
            self._connector, self._contract_address, self._abi
        )
        data = registry.get_model(model_id)
        return ModelRecord(
            model_id=model_id,
            model_hash=data.get("model_hash", ""),
            metadata_uri=data.get("metadata_uri", ""),
            owner=data.get("owner", ""),
            timestamp=data.get("timestamp", 0),
            is_active=data.get("is_active", False),
        )

    def list_all(self) -> list[ModelRecord]:
        """List all registered models.

        Returns:
            List of ModelRecord objects.
        """
        self._ensure_contract()

        from .contracts import ModelRegistryContract

        registry = ModelRegistryContract(
            self._connector, self._contract_address, self._abi
        )
        raw_models = registry.list_models()
        records = []
        for m in raw_models:
            records.append(
                ModelRecord(
                    model_id=m.get("model_id", 0),
                    model_hash=m.get("model_hash", ""),
                    metadata_uri=m.get("metadata_uri", ""),
                    owner=m.get("owner", ""),
                    timestamp=m.get("timestamp", 0),
                    is_active=m.get("is_active", False),
                )
            )
        return records

    def verify(self, model_id: int, expected_hash: str) -> bool:
        """Verify that a model's on-chain hash matches an expected value.

        Args:
            model_id: On-chain model identifier.
            expected_hash: The hash to compare against.

        Returns:
            True if the hashes match.
        """
        record = self.get(model_id)
        return record.model_hash == expected_hash

    @staticmethod
    def compute_hash(data: bytes) -> str:
        """Compute a SHA-256 hash for model data.

        Args:
            data: Raw model bytes.

        Returns:
            Hex-encoded SHA-256 hash with 0x prefix.
        """
        digest = hashlib.sha256(data).hexdigest()
        return f"0x{digest}"

    def __repr__(self) -> str:
        addr = self._contract_address or "not set"
        return f"ModelRegistryClient(contract={addr})"

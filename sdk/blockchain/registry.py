"""Model registry on blockchain.

This module provides a Python client for interacting with the
ModelRegistry smart contract for model verification and audit trail.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
import hashlib
import json
import numpy as np

from .connector import BlockchainConnector, Network


# ModelRegistry contract ABI (subset of functions we use)
MODEL_REGISTRY_ABI = [
    {
        "inputs": [
            {"name": "modelType", "type": "string"},
            {"name": "version", "type": "string"}
        ],
        "name": "registerModel",
        "outputs": [{"name": "modelId", "type": "bytes32"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "modelId", "type": "bytes32"},
            {"name": "epoch", "type": "uint256"},
            {"name": "weightsHash", "type": "bytes32"},
            {"name": "metricsHash", "type": "bytes32"}
        ],
        "name": "saveCheckpoint",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "modelId", "type": "bytes32"},
            {"name": "datasetHash", "type": "bytes32"}
        ],
        "name": "startTraining",
        "outputs": [{"name": "runId", "type": "bytes32"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "modelId", "type": "bytes32"},
            {"name": "runIndex", "type": "uint256"},
            {"name": "totalEpochs", "type": "uint256"},
            {"name": "finalWeightsHash", "type": "bytes32"}
        ],
        "name": "completeTraining",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "modelId", "type": "bytes32"}],
        "name": "verifyModel",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "modelId", "type": "bytes32"}],
        "name": "getModel",
        "outputs": [
            {"name": "owner", "type": "address"},
            {"name": "modelType", "type": "string"},
            {"name": "version", "type": "string"},
            {"name": "weightsHash", "type": "bytes32"},
            {"name": "createdAt", "type": "uint256"},
            {"name": "updatedAt", "type": "uint256"},
            {"name": "verified", "type": "bool"},
            {"name": "active", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "modelId", "type": "bytes32"}],
        "name": "getCheckpointCount",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "modelId", "type": "bytes32"},
            {"name": "index", "type": "uint256"}
        ],
        "name": "getCheckpoint",
        "outputs": [
            {"name": "epoch", "type": "uint256"},
            {"name": "weightsHash", "type": "bytes32"},
            {"name": "metricsHash", "type": "bytes32"},
            {"name": "timestamp", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "modelId", "type": "bytes32"},
            {"name": "epoch", "type": "uint256"},
            {"name": "weightsHash", "type": "bytes32"}
        ],
        "name": "verifyCheckpoint",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "getOwnerModels",
        "outputs": [{"name": "", "type": "bytes32[]"}],
        "stateMutability": "view",
        "type": "function"
    },
]


@dataclass
class ModelInfo:
    """Information about a registered model."""

    model_id: str
    owner: str
    model_type: str
    version: str
    weights_hash: str
    created_at: datetime
    updated_at: datetime
    verified: bool
    active: bool


@dataclass
class CheckpointInfo:
    """Information about a training checkpoint."""

    epoch: int
    weights_hash: str
    metrics_hash: str
    timestamp: datetime


class ModelRegistryClient:
    """Python client for ModelRegistry smart contract.

    This class provides a high-level interface for:
    - Registering ML models on blockchain
    - Saving training checkpoints
    - Verifying model provenance
    - Managing model lifecycle

    Example:
        >>> connector = BlockchainConnector(Network.ARBITRUM_SEPOLIA)
        >>> connector.set_account(private_key)
        >>> connector.connect()
        >>> registry = ModelRegistryClient(connector, contract_address)
        >>> model_id = registry.register_model("LinearRegression", "1.0.0")
        >>> registry.save_checkpoint(model_id, epoch=100, weights=model.weights)
    """

    def __init__(
        self,
        connector: BlockchainConnector,
        contract_address: str,
    ):
        """Initialize ModelRegistry client.

        Args:
            connector: Connected BlockchainConnector instance.
            contract_address: Address of deployed ModelRegistry contract.
        """
        self._connector = connector
        self._contract_address = contract_address
        self._contract = connector.get_contract(contract_address, MODEL_REGISTRY_ABI)

    @property
    def contract_address(self) -> str:
        """Get contract address."""
        return self._contract_address

    @staticmethod
    def compute_weights_hash(weights: np.ndarray) -> bytes:
        """Compute SHA256 hash of model weights.

        Args:
            weights: Numpy array of weights.

        Returns:
            32-byte hash.
        """
        weights_bytes = weights.tobytes()
        return hashlib.sha256(weights_bytes).digest()

    @staticmethod
    def compute_metrics_hash(metrics: Dict[str, Any]) -> bytes:
        """Compute SHA256 hash of training metrics.

        Args:
            metrics: Dictionary of metrics.

        Returns:
            32-byte hash.
        """
        metrics_json = json.dumps(metrics, sort_keys=True)
        return hashlib.sha256(metrics_json.encode()).digest()

    def register_model(
        self,
        model_type: str,
        version: str,
        wait: bool = True,
    ) -> str:
        """Register a new model on blockchain.

        Args:
            model_type: Type of model (e.g., "LinearRegression").
            version: Version string (e.g., "1.0.0").
            wait: Whether to wait for transaction confirmation.

        Returns:
            Model ID (bytes32 as hex string).
        """
        tx = self._contract.functions.registerModel(
            model_type,
            version,
        ).build_transaction({
            "from": self._connector.address,
            "nonce": self._connector.get_nonce(),
            "gas": 200000,
            "gasPrice": self._connector.get_gas_price(),
            "chainId": self._connector.config.chain_id,
        })

        signed = self._connector.account.sign_transaction(tx)
        tx_hash = self._connector.web3.eth.send_raw_transaction(
            signed.raw_transaction
        )

        if wait:
            receipt = self._connector.web3.eth.wait_for_transaction_receipt(tx_hash)
            # Extract model_id from logs
            # For now, return tx hash as placeholder
            return tx_hash.hex()

        return tx_hash.hex()

    def save_checkpoint(
        self,
        model_id: str,
        epoch: int,
        weights: np.ndarray,
        metrics: Optional[Dict[str, Any]] = None,
        wait: bool = True,
    ) -> str:
        """Save a training checkpoint.

        Args:
            model_id: Model identifier (hex string).
            epoch: Current epoch number.
            weights: Model weights as numpy array.
            metrics: Optional training metrics.
            wait: Whether to wait for confirmation.

        Returns:
            Transaction hash.
        """
        weights_hash = self.compute_weights_hash(weights)
        metrics_hash = self.compute_metrics_hash(metrics or {})

        # Convert model_id to bytes32
        if model_id.startswith("0x"):
            model_id_bytes = bytes.fromhex(model_id[2:])
        else:
            model_id_bytes = bytes.fromhex(model_id)

        tx = self._contract.functions.saveCheckpoint(
            model_id_bytes,
            epoch,
            weights_hash,
            metrics_hash,
        ).build_transaction({
            "from": self._connector.address,
            "nonce": self._connector.get_nonce(),
            "gas": 150000,
            "gasPrice": self._connector.get_gas_price(),
            "chainId": self._connector.config.chain_id,
        })

        signed = self._connector.account.sign_transaction(tx)
        tx_hash = self._connector.web3.eth.send_raw_transaction(
            signed.raw_transaction
        )

        if wait:
            self._connector.web3.eth.wait_for_transaction_receipt(tx_hash)

        return tx_hash.hex()

    def start_training(
        self,
        model_id: str,
        dataset_hash: bytes,
        wait: bool = True,
    ) -> str:
        """Start a new training run.

        Args:
            model_id: Model identifier.
            dataset_hash: Hash of training dataset.
            wait: Whether to wait for confirmation.

        Returns:
            Transaction hash.
        """
        if model_id.startswith("0x"):
            model_id_bytes = bytes.fromhex(model_id[2:])
        else:
            model_id_bytes = bytes.fromhex(model_id)

        tx = self._contract.functions.startTraining(
            model_id_bytes,
            dataset_hash,
        ).build_transaction({
            "from": self._connector.address,
            "nonce": self._connector.get_nonce(),
            "gas": 150000,
            "gasPrice": self._connector.get_gas_price(),
            "chainId": self._connector.config.chain_id,
        })

        signed = self._connector.account.sign_transaction(tx)
        tx_hash = self._connector.web3.eth.send_raw_transaction(
            signed.raw_transaction
        )

        if wait:
            self._connector.web3.eth.wait_for_transaction_receipt(tx_hash)

        return tx_hash.hex()

    def complete_training(
        self,
        model_id: str,
        run_index: int,
        total_epochs: int,
        final_weights: np.ndarray,
        wait: bool = True,
    ) -> str:
        """Complete a training run.

        Args:
            model_id: Model identifier.
            run_index: Index of the training run.
            total_epochs: Total epochs completed.
            final_weights: Final model weights.
            wait: Whether to wait for confirmation.

        Returns:
            Transaction hash.
        """
        if model_id.startswith("0x"):
            model_id_bytes = bytes.fromhex(model_id[2:])
        else:
            model_id_bytes = bytes.fromhex(model_id)

        final_hash = self.compute_weights_hash(final_weights)

        tx = self._contract.functions.completeTraining(
            model_id_bytes,
            run_index,
            total_epochs,
            final_hash,
        ).build_transaction({
            "from": self._connector.address,
            "nonce": self._connector.get_nonce(),
            "gas": 150000,
            "gasPrice": self._connector.get_gas_price(),
            "chainId": self._connector.config.chain_id,
        })

        signed = self._connector.account.sign_transaction(tx)
        tx_hash = self._connector.web3.eth.send_raw_transaction(
            signed.raw_transaction
        )

        if wait:
            self._connector.web3.eth.wait_for_transaction_receipt(tx_hash)

        return tx_hash.hex()

    def get_model(self, model_id: str) -> ModelInfo:
        """Get model information from blockchain.

        Args:
            model_id: Model identifier.

        Returns:
            ModelInfo dataclass.
        """
        if model_id.startswith("0x"):
            model_id_bytes = bytes.fromhex(model_id[2:])
        else:
            model_id_bytes = bytes.fromhex(model_id)

        result = self._contract.functions.getModel(model_id_bytes).call()

        return ModelInfo(
            model_id=model_id,
            owner=result[0],
            model_type=result[1],
            version=result[2],
            weights_hash=result[3].hex(),
            created_at=datetime.fromtimestamp(result[4]),
            updated_at=datetime.fromtimestamp(result[5]),
            verified=result[6],
            active=result[7],
        )

    def get_checkpoint_count(self, model_id: str) -> int:
        """Get number of checkpoints for a model.

        Args:
            model_id: Model identifier.

        Returns:
            Number of checkpoints.
        """
        if model_id.startswith("0x"):
            model_id_bytes = bytes.fromhex(model_id[2:])
        else:
            model_id_bytes = bytes.fromhex(model_id)

        return self._contract.functions.getCheckpointCount(model_id_bytes).call()

    def get_checkpoint(self, model_id: str, index: int) -> CheckpointInfo:
        """Get a specific checkpoint.

        Args:
            model_id: Model identifier.
            index: Checkpoint index.

        Returns:
            CheckpointInfo dataclass.
        """
        if model_id.startswith("0x"):
            model_id_bytes = bytes.fromhex(model_id[2:])
        else:
            model_id_bytes = bytes.fromhex(model_id)

        result = self._contract.functions.getCheckpoint(
            model_id_bytes,
            index,
        ).call()

        return CheckpointInfo(
            epoch=result[0],
            weights_hash=result[1].hex(),
            metrics_hash=result[2].hex(),
            timestamp=datetime.fromtimestamp(result[3]),
        )

    def verify_checkpoint(
        self,
        model_id: str,
        epoch: int,
        weights: np.ndarray,
    ) -> bool:
        """Verify a checkpoint matches on-chain record.

        Args:
            model_id: Model identifier.
            epoch: Epoch to verify.
            weights: Weights to verify.

        Returns:
            True if checkpoint is valid.
        """
        if model_id.startswith("0x"):
            model_id_bytes = bytes.fromhex(model_id[2:])
        else:
            model_id_bytes = bytes.fromhex(model_id)

        weights_hash = self.compute_weights_hash(weights)

        return self._contract.functions.verifyCheckpoint(
            model_id_bytes,
            epoch,
            weights_hash,
        ).call()

    def get_my_models(self) -> List[str]:
        """Get all models owned by current account.

        Returns:
            List of model IDs.
        """
        result = self._contract.functions.getOwnerModels(
            self._connector.address
        ).call()

        return [m.hex() for m in result]

    def __repr__(self) -> str:
        return f"ModelRegistryClient(contract={self._contract_address[:10]}...)"

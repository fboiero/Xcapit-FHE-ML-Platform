"""Tests for model registry on blockchain."""

import hashlib
from datetime import datetime
from unittest.mock import MagicMock

import numpy as np

from sdk.blockchain.registry import (
    MODEL_REGISTRY_ABI,
    CheckpointInfo,
    ModelInfo,
    ModelRegistryClient,
)


class TestModelRegistryABI:
    """Tests for contract ABI definition."""

    def test_abi_has_register_model(self):
        """Test ABI includes registerModel function."""
        func_names = [f["name"] for f in MODEL_REGISTRY_ABI if f.get("type") == "function"]
        assert "registerModel" in func_names

    def test_abi_has_save_checkpoint(self):
        """Test ABI includes saveCheckpoint function."""
        func_names = [f["name"] for f in MODEL_REGISTRY_ABI if f.get("type") == "function"]
        assert "saveCheckpoint" in func_names

    def test_abi_has_get_model(self):
        """Test ABI includes getModel function."""
        func_names = [f["name"] for f in MODEL_REGISTRY_ABI if f.get("type") == "function"]
        assert "getModel" in func_names

    def test_abi_has_verify_checkpoint(self):
        """Test ABI includes verifyCheckpoint function."""
        func_names = [f["name"] for f in MODEL_REGISTRY_ABI if f.get("type") == "function"]
        assert "verifyCheckpoint" in func_names


class TestModelInfo:
    """Tests for ModelInfo dataclass."""

    def test_model_info_fields(self):
        """Test ModelInfo has all expected fields."""
        info = ModelInfo(
            model_id="0x" + "a" * 64,
            owner="0x" + "1" * 40,
            model_type="LinearRegression",
            version="1.0.0",
            weights_hash="0x" + "b" * 64,
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 2),
            verified=True,
            active=True,
        )

        assert info.model_id == "0x" + "a" * 64
        assert info.model_type == "LinearRegression"
        assert info.verified is True


class TestCheckpointInfo:
    """Tests for CheckpointInfo dataclass."""

    def test_checkpoint_info_fields(self):
        """Test CheckpointInfo has all expected fields."""
        info = CheckpointInfo(
            epoch=100,
            weights_hash="0x" + "c" * 64,
            metrics_hash="0x" + "d" * 64,
            timestamp=datetime(2024, 1, 15),
        )

        assert info.epoch == 100
        assert len(info.weights_hash) > 0


class TestModelRegistryClientInit:
    """Tests for ModelRegistryClient initialization."""

    def test_init_stores_connector_and_address(self):
        """Test initialization stores connector and contract address."""
        mock_connector = MagicMock()
        mock_contract = MagicMock()
        mock_connector.get_contract.return_value = mock_contract

        client = ModelRegistryClient(mock_connector, "0x" + "1" * 40)

        assert client._connector == mock_connector
        assert client._contract_address == "0x" + "1" * 40
        assert client._contract == mock_contract

    def test_contract_address_property(self):
        """Test contract_address property returns address."""
        mock_connector = MagicMock()
        mock_connector.get_contract.return_value = MagicMock()

        client = ModelRegistryClient(mock_connector, "0x" + "2" * 40)

        assert client.contract_address == "0x" + "2" * 40


class TestModelRegistryClientHashing:
    """Tests for hash computation methods."""

    def test_compute_weights_hash(self):
        """Test compute_weights_hash returns correct hash."""
        weights = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32)

        hash_result = ModelRegistryClient.compute_weights_hash(weights)

        assert isinstance(hash_result, bytes)
        assert len(hash_result) == 32  # SHA256 produces 32 bytes

    def test_compute_weights_hash_deterministic(self):
        """Test hash computation is deterministic."""
        weights = np.array([1.0, 2.0, 3.0], dtype=np.float32)

        hash1 = ModelRegistryClient.compute_weights_hash(weights)
        hash2 = ModelRegistryClient.compute_weights_hash(weights)

        assert hash1 == hash2

    def test_compute_weights_hash_different_for_different_weights(self):
        """Test different weights produce different hashes."""
        weights1 = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        weights2 = np.array([1.0, 2.0, 4.0], dtype=np.float32)

        hash1 = ModelRegistryClient.compute_weights_hash(weights1)
        hash2 = ModelRegistryClient.compute_weights_hash(weights2)

        assert hash1 != hash2

    def test_compute_metrics_hash(self):
        """Test compute_metrics_hash returns correct hash."""
        metrics = {"accuracy": 0.95, "loss": 0.05}

        hash_result = ModelRegistryClient.compute_metrics_hash(metrics)

        assert isinstance(hash_result, bytes)
        assert len(hash_result) == 32

    def test_compute_metrics_hash_deterministic(self):
        """Test metrics hash is deterministic for same input."""
        metrics = {"accuracy": 0.95, "f1_score": 0.92}

        hash1 = ModelRegistryClient.compute_metrics_hash(metrics)
        hash2 = ModelRegistryClient.compute_metrics_hash(metrics)

        assert hash1 == hash2

    def test_compute_metrics_hash_order_independent(self):
        """Test metrics hash is independent of key order."""
        metrics1 = {"accuracy": 0.95, "loss": 0.05}
        metrics2 = {"loss": 0.05, "accuracy": 0.95}

        hash1 = ModelRegistryClient.compute_metrics_hash(metrics1)
        hash2 = ModelRegistryClient.compute_metrics_hash(metrics2)

        assert hash1 == hash2


class TestModelRegistryClientRegister:
    """Tests for model registration."""

    def test_register_model_builds_transaction(self):
        """Test register_model builds correct transaction."""
        mock_connector = MagicMock()
        mock_connector.address = "0x" + "1" * 40
        mock_connector.get_nonce.return_value = 5
        mock_connector.get_gas_price.return_value = 20000000000
        mock_connector.config.chain_id = 421614

        mock_contract = MagicMock()
        mock_tx_builder = MagicMock()
        mock_tx_builder.build_transaction.return_value = {}
        mock_contract.functions.registerModel.return_value = mock_tx_builder
        mock_connector.get_contract.return_value = mock_contract

        mock_account = MagicMock()
        mock_account.sign_transaction.return_value = MagicMock(raw_transaction=b"signed")
        mock_connector.account = mock_account
        mock_connector.web3.eth.send_raw_transaction.return_value = b"0x" + b"a" * 64
        mock_connector.web3.eth.wait_for_transaction_receipt.return_value = {}

        client = ModelRegistryClient(mock_connector, "0x" + "2" * 40)
        result = client.register_model("LinearRegression", "1.0.0")

        mock_contract.functions.registerModel.assert_called_once_with("LinearRegression", "1.0.0")
        assert result is not None

    def test_register_model_without_wait(self):
        """Test register_model without waiting for confirmation."""
        mock_connector = MagicMock()
        mock_connector.address = "0x" + "1" * 40
        mock_connector.get_nonce.return_value = 5
        mock_connector.get_gas_price.return_value = 20000000000
        mock_connector.config.chain_id = 421614

        mock_contract = MagicMock()
        mock_tx_builder = MagicMock()
        mock_tx_builder.build_transaction.return_value = {}
        mock_contract.functions.registerModel.return_value = mock_tx_builder
        mock_connector.get_contract.return_value = mock_contract

        mock_account = MagicMock()
        mock_account.sign_transaction.return_value = MagicMock(raw_transaction=b"signed")
        mock_connector.account = mock_account
        mock_connector.web3.eth.send_raw_transaction.return_value = b"0x" + b"a" * 64

        client = ModelRegistryClient(mock_connector, "0x" + "2" * 40)
        result = client.register_model("LogisticRegression", "2.0.0", wait=False)

        mock_connector.web3.eth.wait_for_transaction_receipt.assert_not_called()
        assert result is not None


class TestModelRegistryClientCheckpoint:
    """Tests for checkpoint operations."""

    def test_save_checkpoint_with_0x_prefix(self):
        """Test save_checkpoint handles 0x prefix."""
        mock_connector = MagicMock()
        mock_connector.address = "0x" + "1" * 40
        mock_connector.get_nonce.return_value = 10
        mock_connector.get_gas_price.return_value = 20000000000
        mock_connector.config.chain_id = 421614

        mock_contract = MagicMock()
        mock_tx_builder = MagicMock()
        mock_tx_builder.build_transaction.return_value = {}
        mock_contract.functions.saveCheckpoint.return_value = mock_tx_builder
        mock_connector.get_contract.return_value = mock_contract

        mock_account = MagicMock()
        mock_account.sign_transaction.return_value = MagicMock(raw_transaction=b"signed")
        mock_connector.account = mock_account
        mock_connector.web3.eth.send_raw_transaction.return_value = b"0x" + b"b" * 64
        mock_connector.web3.eth.wait_for_transaction_receipt.return_value = {}

        client = ModelRegistryClient(mock_connector, "0x" + "2" * 40)
        weights = np.array([1.0, 2.0, 3.0])

        result = client.save_checkpoint("0x" + "a" * 64, epoch=100, weights=weights)

        mock_contract.functions.saveCheckpoint.assert_called_once()
        assert result is not None

    def test_save_checkpoint_without_0x_prefix(self):
        """Test save_checkpoint handles model_id without 0x prefix."""
        mock_connector = MagicMock()
        mock_connector.address = "0x" + "1" * 40
        mock_connector.get_nonce.return_value = 10
        mock_connector.get_gas_price.return_value = 20000000000
        mock_connector.config.chain_id = 421614

        mock_contract = MagicMock()
        mock_tx_builder = MagicMock()
        mock_tx_builder.build_transaction.return_value = {}
        mock_contract.functions.saveCheckpoint.return_value = mock_tx_builder
        mock_connector.get_contract.return_value = mock_contract

        mock_account = MagicMock()
        mock_account.sign_transaction.return_value = MagicMock(raw_transaction=b"signed")
        mock_connector.account = mock_account
        mock_connector.web3.eth.send_raw_transaction.return_value = b"0x" + b"b" * 64
        mock_connector.web3.eth.wait_for_transaction_receipt.return_value = {}

        client = ModelRegistryClient(mock_connector, "0x" + "2" * 40)
        weights = np.array([1.0, 2.0, 3.0])

        result = client.save_checkpoint("a" * 64, epoch=50, weights=weights)

        assert result is not None

    def test_save_checkpoint_with_metrics(self):
        """Test save_checkpoint includes metrics hash."""
        mock_connector = MagicMock()
        mock_connector.address = "0x" + "1" * 40
        mock_connector.get_nonce.return_value = 10
        mock_connector.get_gas_price.return_value = 20000000000
        mock_connector.config.chain_id = 421614

        mock_contract = MagicMock()
        mock_tx_builder = MagicMock()
        mock_tx_builder.build_transaction.return_value = {}
        mock_contract.functions.saveCheckpoint.return_value = mock_tx_builder
        mock_connector.get_contract.return_value = mock_contract

        mock_account = MagicMock()
        mock_account.sign_transaction.return_value = MagicMock(raw_transaction=b"signed")
        mock_connector.account = mock_account
        mock_connector.web3.eth.send_raw_transaction.return_value = b"0x" + b"b" * 64
        mock_connector.web3.eth.wait_for_transaction_receipt.return_value = {}

        client = ModelRegistryClient(mock_connector, "0x" + "2" * 40)
        weights = np.array([1.0, 2.0, 3.0])
        metrics = {"accuracy": 0.95, "loss": 0.05}

        result = client.save_checkpoint("a" * 64, epoch=100, weights=weights, metrics=metrics)

        assert result is not None


class TestModelRegistryClientTraining:
    """Tests for training operations."""

    def test_start_training(self):
        """Test start_training sends transaction."""
        mock_connector = MagicMock()
        mock_connector.address = "0x" + "1" * 40
        mock_connector.get_nonce.return_value = 15
        mock_connector.get_gas_price.return_value = 20000000000
        mock_connector.config.chain_id = 421614

        mock_contract = MagicMock()
        mock_tx_builder = MagicMock()
        mock_tx_builder.build_transaction.return_value = {}
        mock_contract.functions.startTraining.return_value = mock_tx_builder
        mock_connector.get_contract.return_value = mock_contract

        mock_account = MagicMock()
        mock_account.sign_transaction.return_value = MagicMock(raw_transaction=b"signed")
        mock_connector.account = mock_account
        mock_connector.web3.eth.send_raw_transaction.return_value = b"0x" + b"c" * 64
        mock_connector.web3.eth.wait_for_transaction_receipt.return_value = {}

        client = ModelRegistryClient(mock_connector, "0x" + "2" * 40)
        dataset_hash = hashlib.sha256(b"test_dataset").digest()

        result = client.start_training("0x" + "a" * 64, dataset_hash)

        mock_contract.functions.startTraining.assert_called_once()
        assert result is not None

    def test_complete_training(self):
        """Test complete_training sends transaction."""
        mock_connector = MagicMock()
        mock_connector.address = "0x" + "1" * 40
        mock_connector.get_nonce.return_value = 20
        mock_connector.get_gas_price.return_value = 20000000000
        mock_connector.config.chain_id = 421614

        mock_contract = MagicMock()
        mock_tx_builder = MagicMock()
        mock_tx_builder.build_transaction.return_value = {}
        mock_contract.functions.completeTraining.return_value = mock_tx_builder
        mock_connector.get_contract.return_value = mock_contract

        mock_account = MagicMock()
        mock_account.sign_transaction.return_value = MagicMock(raw_transaction=b"signed")
        mock_connector.account = mock_account
        mock_connector.web3.eth.send_raw_transaction.return_value = b"0x" + b"d" * 64
        mock_connector.web3.eth.wait_for_transaction_receipt.return_value = {}

        client = ModelRegistryClient(mock_connector, "0x" + "2" * 40)
        final_weights = np.array([1.0, 2.0, 3.0, 4.0])

        result = client.complete_training(
            "0x" + "a" * 64,
            run_index=0,
            total_epochs=100,
            final_weights=final_weights,
        )

        mock_contract.functions.completeTraining.assert_called_once()
        assert result is not None


class TestModelRegistryClientQuery:
    """Tests for query operations."""

    def test_get_model_returns_model_info(self):
        """Test get_model returns ModelInfo object."""
        mock_connector = MagicMock()
        mock_contract = MagicMock()

        # Mock the contract call return value
        mock_contract.functions.getModel.return_value.call.return_value = (
            "0x" + "1" * 40,  # owner
            "LinearRegression",  # model_type
            "1.0.0",  # version
            bytes.fromhex("a" * 64),  # weights_hash
            1704067200,  # created_at timestamp
            1704153600,  # updated_at timestamp
            True,  # verified
            True,  # active
        )
        mock_connector.get_contract.return_value = mock_contract

        client = ModelRegistryClient(mock_connector, "0x" + "2" * 40)
        result = client.get_model("0x" + "b" * 64)

        assert isinstance(result, ModelInfo)
        assert result.model_type == "LinearRegression"
        assert result.version == "1.0.0"
        assert result.verified is True

    def test_get_checkpoint_count(self):
        """Test get_checkpoint_count returns count."""
        mock_connector = MagicMock()
        mock_contract = MagicMock()
        mock_contract.functions.getCheckpointCount.return_value.call.return_value = 5
        mock_connector.get_contract.return_value = mock_contract

        client = ModelRegistryClient(mock_connector, "0x" + "2" * 40)
        result = client.get_checkpoint_count("0x" + "a" * 64)

        assert result == 5

    def test_get_checkpoint_returns_checkpoint_info(self):
        """Test get_checkpoint returns CheckpointInfo object."""
        mock_connector = MagicMock()
        mock_contract = MagicMock()
        mock_contract.functions.getCheckpoint.return_value.call.return_value = (
            100,  # epoch
            bytes.fromhex("c" * 64),  # weights_hash
            bytes.fromhex("d" * 64),  # metrics_hash
            1704240000,  # timestamp
        )
        mock_connector.get_contract.return_value = mock_contract

        client = ModelRegistryClient(mock_connector, "0x" + "2" * 40)
        result = client.get_checkpoint("0x" + "a" * 64, 0)

        assert isinstance(result, CheckpointInfo)
        assert result.epoch == 100

    def test_verify_checkpoint_returns_bool(self):
        """Test verify_checkpoint returns boolean."""
        mock_connector = MagicMock()
        mock_contract = MagicMock()
        mock_contract.functions.verifyCheckpoint.return_value.call.return_value = True
        mock_connector.get_contract.return_value = mock_contract

        client = ModelRegistryClient(mock_connector, "0x" + "2" * 40)
        weights = np.array([1.0, 2.0, 3.0])

        result = client.verify_checkpoint("0x" + "a" * 64, epoch=100, weights=weights)

        assert result is True

    def test_get_my_models_returns_list(self):
        """Test get_my_models returns list of model IDs."""
        mock_connector = MagicMock()
        mock_connector.address = "0x" + "1" * 40
        mock_contract = MagicMock()
        mock_contract.functions.getOwnerModels.return_value.call.return_value = [
            bytes.fromhex("a" * 64),
            bytes.fromhex("b" * 64),
        ]
        mock_connector.get_contract.return_value = mock_contract

        client = ModelRegistryClient(mock_connector, "0x" + "2" * 40)
        result = client.get_my_models()

        assert len(result) == 2
        assert result[0] == "a" * 64
        assert result[1] == "b" * 64


class TestModelRegistryClientRepr:
    """Tests for string representation."""

    def test_repr_shows_truncated_address(self):
        """Test repr shows truncated contract address."""
        mock_connector = MagicMock()
        mock_connector.get_contract.return_value = MagicMock()

        client = ModelRegistryClient(mock_connector, "0x" + "1" * 40)

        repr_str = repr(client)

        assert "ModelRegistryClient" in repr_str
        assert "contract=" in repr_str
        assert "..." in repr_str


class TestModelRegistryClientIntegration:
    """Integration-style tests for ModelRegistryClient."""

    def test_full_training_workflow(self):
        """Test complete training workflow."""
        mock_connector = MagicMock()
        mock_connector.address = "0x" + "1" * 40
        mock_connector.get_nonce.return_value = 0
        mock_connector.get_gas_price.return_value = 20000000000
        mock_connector.config.chain_id = 421614

        mock_contract = MagicMock()
        mock_tx_builder = MagicMock()
        mock_tx_builder.build_transaction.return_value = {}

        # Setup all function mocks
        mock_contract.functions.registerModel.return_value = mock_tx_builder
        mock_contract.functions.startTraining.return_value = mock_tx_builder
        mock_contract.functions.saveCheckpoint.return_value = mock_tx_builder
        mock_contract.functions.completeTraining.return_value = mock_tx_builder

        mock_connector.get_contract.return_value = mock_contract

        mock_account = MagicMock()
        mock_account.sign_transaction.return_value = MagicMock(raw_transaction=b"signed")
        mock_connector.account = mock_account
        mock_connector.web3.eth.send_raw_transaction.return_value = b"0x" + b"a" * 64
        mock_connector.web3.eth.wait_for_transaction_receipt.return_value = {}

        client = ModelRegistryClient(mock_connector, "0x" + "2" * 40)

        # 1. Register model
        model_id = client.register_model("NeuralNetwork", "1.0.0")
        assert model_id is not None

        # 2. Start training
        dataset_hash = hashlib.sha256(b"training_data").digest()
        tx_hash = client.start_training(model_id, dataset_hash)
        assert tx_hash is not None

        # 3. Save checkpoints
        for epoch in [10, 20, 30]:
            weights = np.random.randn(100)
            metrics = {"loss": 1.0 / epoch, "accuracy": epoch / 100.0}
            cp_hash = client.save_checkpoint(model_id, epoch, weights, metrics)
            assert cp_hash is not None

        # 4. Complete training
        final_weights = np.random.randn(100)
        complete_hash = client.complete_training(model_id, 0, 30, final_weights)
        assert complete_hash is not None

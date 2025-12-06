"""Tests for blockchain integration module."""

import sys
from pathlib import Path

# Add paths for importing blockchain modules without triggering sdk/__init__.py
project_root = Path(__file__).parent.parent
sdk_blockchain_path = project_root / "sdk" / "blockchain"

# Temporarily modify sys.modules to prevent sdk package import
if "sdk" not in sys.modules:
    # Create a dummy sdk module to prevent full import
    import types
    sdk_module = types.ModuleType("sdk")
    sdk_module.blockchain = types.ModuleType("sdk.blockchain")
    sys.modules["sdk"] = sdk_module
    sys.modules["sdk.blockchain"] = sdk_module.blockchain

sys.path.insert(0, str(project_root))

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

# Import using importlib to bypass sdk/__init__.py
import importlib.util

def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Load connector first (registry depends on it)
connector_module = load_module_from_path(
    "sdk.blockchain.connector",
    sdk_blockchain_path / "connector.py"
)
BlockchainConnector = connector_module.BlockchainConnector
Network = connector_module.Network
NetworkConfig = connector_module.NetworkConfig
NETWORK_CONFIGS = connector_module.NETWORK_CONFIGS

# Load registry
registry_module = load_module_from_path(
    "sdk.blockchain.registry",
    sdk_blockchain_path / "registry.py"
)
ModelRegistryClient = registry_module.ModelRegistryClient
ModelInfo = registry_module.ModelInfo
CheckpointInfo = registry_module.CheckpointInfo


class TestNetworkConfig:
    """Tests for network configuration."""

    def test_network_enum_values(self):
        """Test that all expected networks exist."""
        assert Network.ARBITRUM_ONE.value == "arbitrum-one"
        assert Network.ARBITRUM_SEPOLIA.value == "arbitrum-sepolia"
        assert Network.ETHEREUM_MAINNET.value == "ethereum-mainnet"
        assert Network.ETHEREUM_SEPOLIA.value == "ethereum-sepolia"
        assert Network.LOCAL.value == "local"

    def test_all_networks_have_config(self):
        """Test that all networks have configurations."""
        for network in Network:
            assert network in NETWORK_CONFIGS
            config = NETWORK_CONFIGS[network]
            assert isinstance(config, NetworkConfig)

    def test_arbitrum_one_config(self):
        """Test Arbitrum One configuration."""
        config = NETWORK_CONFIGS[Network.ARBITRUM_ONE]
        assert config.name == "Arbitrum One"
        assert config.chain_id == 42161
        assert "arbitrum" in config.rpc_url.lower()
        assert config.is_testnet is False

    def test_arbitrum_sepolia_config(self):
        """Test Arbitrum Sepolia testnet configuration."""
        config = NETWORK_CONFIGS[Network.ARBITRUM_SEPOLIA]
        assert config.name == "Arbitrum Sepolia"
        assert config.chain_id == 421614
        assert "sepolia" in config.rpc_url.lower()
        assert config.is_testnet is True

    def test_local_config(self):
        """Test local development configuration."""
        config = NETWORK_CONFIGS[Network.LOCAL]
        assert config.chain_id == 31337
        assert "127.0.0.1" in config.rpc_url or "localhost" in config.rpc_url
        assert config.is_testnet is True


class TestBlockchainConnector:
    """Tests for BlockchainConnector class."""

    def test_init_default_network(self):
        """Test connector initialization with default network."""
        connector = BlockchainConnector()
        assert connector.network == Network.ARBITRUM_SEPOLIA
        assert connector.is_connected is False
        assert connector.account is None

    def test_init_custom_network(self):
        """Test connector initialization with custom network."""
        connector = BlockchainConnector(Network.ARBITRUM_ONE)
        assert connector.network == Network.ARBITRUM_ONE
        assert connector.config.chain_id == 42161

    def test_init_custom_rpc_url(self):
        """Test connector with custom RPC URL."""
        custom_url = "https://custom-rpc.example.com"
        connector = BlockchainConnector(
            Network.ARBITRUM_SEPOLIA,
            rpc_url=custom_url
        )
        assert connector._rpc_url == custom_url

    def test_properties_before_connect(self):
        """Test properties before connection."""
        connector = BlockchainConnector()
        assert connector.is_connected is False
        assert connector.address is None

    def test_web3_property_raises_before_connect(self):
        """Test that web3 property raises if not connected."""
        connector = BlockchainConnector()
        with pytest.raises(RuntimeError, match="Not connected"):
            _ = connector.web3

    def test_connect_success(self):
        """Test successful connection."""
        with patch.object(connector_module, 'Web3') as mock_web3_class:
            mock_web3 = MagicMock()
            mock_web3.is_connected.return_value = True
            mock_web3.eth.chain_id = 421614
            mock_web3.middleware_onion = MagicMock()
            mock_web3_class.return_value = mock_web3

            connector = BlockchainConnector(Network.ARBITRUM_SEPOLIA)
            result = connector.connect()

            assert result is True
            assert connector.is_connected is True

    def test_connect_chain_id_mismatch(self):
        """Test connection fails with wrong chain ID."""
        with patch.object(connector_module, 'Web3') as mock_web3_class:
            mock_web3 = MagicMock()
            mock_web3.is_connected.return_value = True
            mock_web3.eth.chain_id = 1  # Wrong chain ID
            mock_web3.middleware_onion = MagicMock()
            mock_web3_class.return_value = mock_web3

            connector = BlockchainConnector(Network.ARBITRUM_SEPOLIA)

            with pytest.raises(ConnectionError, match="Chain ID mismatch"):
                connector.connect()

    def test_set_account(self):
        """Test setting account from private key."""
        with patch.object(connector_module, 'Account') as mock_account_class:
            mock_account = MagicMock()
            mock_account.address = "0x1234567890abcdef1234567890abcdef12345678"
            mock_account_class.from_key.return_value = mock_account

            connector = BlockchainConnector()
            address = connector.set_account("0x" + "a" * 64)

            assert address == mock_account.address
            assert connector.account == mock_account

    def test_set_account_without_0x_prefix(self):
        """Test setting account without 0x prefix."""
        with patch.object(connector_module, 'Account') as mock_account_class:
            mock_account = MagicMock()
            mock_account.address = "0x1234567890abcdef1234567890abcdef12345678"
            mock_account_class.from_key.return_value = mock_account

            connector = BlockchainConnector()
            connector.set_account("a" * 64)

            # Should add 0x prefix
            mock_account_class.from_key.assert_called_with("0x" + "a" * 64)

    def test_disconnect(self):
        """Test disconnection."""
        connector = BlockchainConnector()
        connector._connected = True
        connector._web3 = MagicMock()

        connector.disconnect()

        assert connector.is_connected is False
        assert connector._web3 is None

    def test_get_explorer_url(self):
        """Test explorer URL generation."""
        connector = BlockchainConnector(Network.ARBITRUM_SEPOLIA)
        tx_hash = "0x" + "a" * 64

        url = connector.get_explorer_url(tx_hash)

        assert "sepolia.arbiscan.io" in url
        assert tx_hash in url

    def test_get_explorer_url_local(self):
        """Test explorer URL for local network (empty)."""
        connector = BlockchainConnector(Network.LOCAL)
        url = connector.get_explorer_url("0x" + "a" * 64)
        assert url == ""

    def test_repr(self):
        """Test string representation."""
        connector = BlockchainConnector(Network.ARBITRUM_SEPOLIA)
        repr_str = repr(connector)
        assert "Arbitrum Sepolia" in repr_str
        assert "disconnected" in repr_str


class TestModelRegistryClient:
    """Tests for ModelRegistryClient class."""

    @pytest.fixture
    def mock_connector(self):
        """Create a mock blockchain connector."""
        connector = MagicMock()
        connector.address = "0x1234567890abcdef1234567890abcdef12345678"
        connector.web3 = MagicMock()
        connector.config = MagicMock()
        connector.config.chain_id = 421614
        connector.get_nonce.return_value = 0
        connector.get_gas_price.return_value = 1000000000
        connector.get_contract.return_value = MagicMock()
        return connector

    @pytest.fixture
    def registry_client(self, mock_connector):
        """Create a ModelRegistryClient instance."""
        contract_address = "0xabcdef1234567890abcdef1234567890abcdef12"
        return ModelRegistryClient(mock_connector, contract_address)

    def test_init(self, mock_connector):
        """Test client initialization."""
        contract_address = "0xabcdef1234567890abcdef1234567890abcdef12"
        client = ModelRegistryClient(mock_connector, contract_address)

        assert client.contract_address == contract_address
        mock_connector.get_contract.assert_called_once()

    def test_compute_weights_hash(self):
        """Test weights hash computation."""
        weights = np.array([1.0, 2.0, 3.0, 4.0])
        hash1 = ModelRegistryClient.compute_weights_hash(weights)

        assert isinstance(hash1, bytes)
        assert len(hash1) == 32  # SHA256 produces 32 bytes

        # Same weights should produce same hash
        hash2 = ModelRegistryClient.compute_weights_hash(weights)
        assert hash1 == hash2

        # Different weights should produce different hash
        different_weights = np.array([1.0, 2.0, 3.0, 5.0])
        hash3 = ModelRegistryClient.compute_weights_hash(different_weights)
        assert hash1 != hash3

    def test_compute_weights_hash_deterministic(self):
        """Test that hash is deterministic across calls."""
        np.random.seed(42)
        weights = np.random.randn(100)

        hashes = [ModelRegistryClient.compute_weights_hash(weights) for _ in range(5)]
        assert all(h == hashes[0] for h in hashes)

    def test_compute_metrics_hash(self):
        """Test metrics hash computation."""
        metrics = {"loss": 0.1, "accuracy": 0.95}
        hash1 = ModelRegistryClient.compute_metrics_hash(metrics)

        assert isinstance(hash1, bytes)
        assert len(hash1) == 32

        # Same metrics should produce same hash
        hash2 = ModelRegistryClient.compute_metrics_hash(metrics)
        assert hash1 == hash2

        # Different metrics should produce different hash
        different_metrics = {"loss": 0.2, "accuracy": 0.90}
        hash3 = ModelRegistryClient.compute_metrics_hash(different_metrics)
        assert hash1 != hash3

    def test_compute_metrics_hash_order_independent(self):
        """Test that metrics hash is independent of key order."""
        metrics1 = {"loss": 0.1, "accuracy": 0.95}
        metrics2 = {"accuracy": 0.95, "loss": 0.1}

        hash1 = ModelRegistryClient.compute_metrics_hash(metrics1)
        hash2 = ModelRegistryClient.compute_metrics_hash(metrics2)

        # Should be same due to sort_keys=True in json.dumps
        assert hash1 == hash2

    def test_repr(self, registry_client):
        """Test string representation."""
        repr_str = repr(registry_client)
        assert "ModelRegistryClient" in repr_str


class TestModelInfo:
    """Tests for ModelInfo dataclass."""

    def test_model_info_creation(self):
        """Test ModelInfo creation."""
        info = ModelInfo(
            model_id="0x" + "a" * 64,
            owner="0x1234567890abcdef1234567890abcdef12345678",
            model_type="LinearRegression",
            version="1.0.0",
            weights_hash="0x" + "b" * 64,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            verified=False,
            active=True,
        )

        assert info.model_type == "LinearRegression"
        assert info.version == "1.0.0"
        assert info.verified is False
        assert info.active is True


class TestCheckpointInfo:
    """Tests for CheckpointInfo dataclass."""

    def test_checkpoint_info_creation(self):
        """Test CheckpointInfo creation."""
        info = CheckpointInfo(
            epoch=100,
            weights_hash="0x" + "a" * 64,
            metrics_hash="0x" + "b" * 64,
            timestamp=datetime.now(),
        )

        assert info.epoch == 100
        assert len(info.weights_hash) == 66  # 0x + 64 hex chars


class TestHashConsistency:
    """Tests for hash consistency between Python and Solidity."""

    def test_weights_hash_format(self):
        """Test that weights hash format is compatible with bytes32."""
        weights = np.random.randn(100)
        hash_bytes = ModelRegistryClient.compute_weights_hash(weights)

        # Should be exactly 32 bytes for Solidity bytes32
        assert len(hash_bytes) == 32

        # Should be convertible to hex
        hex_str = hash_bytes.hex()
        assert len(hex_str) == 64

    def test_metrics_hash_format(self):
        """Test that metrics hash format is compatible with bytes32."""
        metrics = {
            "loss": 0.123456789,
            "accuracy": 0.987654321,
            "epoch": 100,
        }
        hash_bytes = ModelRegistryClient.compute_metrics_hash(metrics)

        assert len(hash_bytes) == 32
        assert len(hash_bytes.hex()) == 64

    def test_empty_metrics_hash(self):
        """Test hash of empty metrics dict."""
        hash_bytes = ModelRegistryClient.compute_metrics_hash({})
        assert len(hash_bytes) == 32

    def test_large_weights_hash(self):
        """Test hash of large weight arrays."""
        # Simulate a model with many parameters
        large_weights = np.random.randn(10000)
        hash_bytes = ModelRegistryClient.compute_weights_hash(large_weights)

        assert len(hash_bytes) == 32


class TestIntegrationScenarios:
    """Integration-style tests for common usage patterns."""

    def test_connector_workflow(self):
        """Test typical connector workflow."""
        with patch.object(connector_module, 'Web3') as mock_web3_class, \
             patch.object(connector_module, 'Account') as mock_account_class:

            mock_web3 = MagicMock()
            mock_web3.is_connected.return_value = True
            mock_web3.eth.chain_id = 421614
            mock_web3.eth.get_balance.return_value = 1000000000000000000
            mock_web3.eth.get_transaction_count.return_value = 0
            mock_web3.eth.gas_price = 1000000000
            mock_web3.middleware_onion = MagicMock()
            mock_web3_class.return_value = mock_web3

            mock_account = MagicMock()
            mock_account.address = "0x1234567890abcdef1234567890abcdef12345678"
            mock_account_class.from_key.return_value = mock_account

            connector = BlockchainConnector(Network.ARBITRUM_SEPOLIA)

            # Set account
            address = connector.set_account("0x" + "a" * 64)
            assert address is not None

            # Connect
            connected = connector.connect()
            assert connected is True
            assert connector.is_connected is True

            # Disconnect
            connector.disconnect()
            assert connector.is_connected is False

    def test_model_registration_workflow(self):
        """Test model registration workflow with mocked contract."""
        # Setup mocks
        mock_connector = MagicMock()
        mock_connector.address = "0x1234567890abcdef1234567890abcdef12345678"
        mock_connector.config.chain_id = 421614
        mock_connector.get_nonce.return_value = 0
        mock_connector.get_gas_price.return_value = 1000000000

        mock_contract = MagicMock()
        mock_tx_hash = bytes.fromhex("a" * 64)

        # Mock transaction flow
        mock_contract.functions.registerModel.return_value.build_transaction.return_value = {}
        mock_connector.account.sign_transaction.return_value.raw_transaction = b"signed"
        mock_connector.web3.eth.send_raw_transaction.return_value = mock_tx_hash
        mock_connector.web3.eth.wait_for_transaction_receipt.return_value = {}
        mock_connector.get_contract.return_value = mock_contract

        # Create client and register model
        client = ModelRegistryClient(
            mock_connector,
            "0xabcdef1234567890abcdef1234567890abcdef12"
        )

        # Model registration would return tx hash
        assert client.contract_address == "0xabcdef1234567890abcdef1234567890abcdef12"

    def test_checkpoint_hash_workflow(self):
        """Test checkpoint saving workflow."""
        # Simulate training
        weights_epoch_1 = np.array([0.1, 0.2, 0.3])
        metrics_epoch_1 = {"loss": 1.0, "accuracy": 0.6}

        weights_epoch_2 = np.array([0.15, 0.25, 0.35])
        metrics_epoch_2 = {"loss": 0.5, "accuracy": 0.8}

        # Compute hashes
        w_hash_1 = ModelRegistryClient.compute_weights_hash(weights_epoch_1)
        m_hash_1 = ModelRegistryClient.compute_metrics_hash(metrics_epoch_1)

        w_hash_2 = ModelRegistryClient.compute_weights_hash(weights_epoch_2)
        m_hash_2 = ModelRegistryClient.compute_metrics_hash(metrics_epoch_2)

        # Hashes should be different between epochs
        assert w_hash_1 != w_hash_2
        assert m_hash_1 != m_hash_2

        # Same data should produce same hash
        assert w_hash_1 == ModelRegistryClient.compute_weights_hash(weights_epoch_1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

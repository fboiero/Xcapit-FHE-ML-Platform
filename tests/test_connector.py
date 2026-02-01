"""Tests for blockchain connector module."""

import json
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from sdk.blockchain.connector import (
    NETWORK_CONFIGS,
    BlockchainConnector,
    Network,
    NetworkConfig,
)


class TestNetwork:
    """Tests for Network enum."""

    def test_arbitrum_one_value(self):
        """Test Arbitrum One network value."""
        assert Network.ARBITRUM_ONE.value == "arbitrum-one"

    def test_arbitrum_sepolia_value(self):
        """Test Arbitrum Sepolia network value."""
        assert Network.ARBITRUM_SEPOLIA.value == "arbitrum-sepolia"

    def test_ethereum_mainnet_value(self):
        """Test Ethereum mainnet value."""
        assert Network.ETHEREUM_MAINNET.value == "ethereum-mainnet"

    def test_ethereum_sepolia_value(self):
        """Test Ethereum Sepolia value."""
        assert Network.ETHEREUM_SEPOLIA.value == "ethereum-sepolia"

    def test_local_value(self):
        """Test local network value."""
        assert Network.LOCAL.value == "local"


class TestNetworkConfigs:
    """Tests for network configurations."""

    def test_arbitrum_one_config(self):
        """Test Arbitrum One configuration."""
        config = NETWORK_CONFIGS[Network.ARBITRUM_ONE]
        assert config.name == "Arbitrum One"
        assert config.chain_id == 42161
        assert config.is_testnet is False
        assert "arb1.arbitrum.io" in config.rpc_url

    def test_arbitrum_sepolia_config(self):
        """Test Arbitrum Sepolia configuration."""
        config = NETWORK_CONFIGS[Network.ARBITRUM_SEPOLIA]
        assert config.name == "Arbitrum Sepolia"
        assert config.chain_id == 421614
        assert config.is_testnet is True

    def test_ethereum_mainnet_config(self):
        """Test Ethereum mainnet configuration."""
        config = NETWORK_CONFIGS[Network.ETHEREUM_MAINNET]
        assert config.chain_id == 1
        assert config.is_testnet is False

    def test_local_config(self):
        """Test local network configuration."""
        config = NETWORK_CONFIGS[Network.LOCAL]
        assert config.chain_id == 31337
        assert config.rpc_url == "http://127.0.0.1:8545"
        assert config.explorer_url == ""


class TestBlockchainConnectorInit:
    """Tests for BlockchainConnector initialization."""

    def test_init_default_network(self):
        """Test initialization with default network."""
        connector = BlockchainConnector()
        assert connector.network == Network.ARBITRUM_SEPOLIA

    def test_init_custom_network(self):
        """Test initialization with custom network."""
        connector = BlockchainConnector(Network.ETHEREUM_MAINNET)
        assert connector.network == Network.ETHEREUM_MAINNET
        assert connector.config.chain_id == 1

    def test_init_custom_rpc_url(self):
        """Test initialization with custom RPC URL."""
        custom_url = "https://custom.rpc.example.com"
        connector = BlockchainConnector(rpc_url=custom_url)
        assert connector._rpc_url == custom_url

    def test_init_properties(self):
        """Test initial property values."""
        connector = BlockchainConnector()
        assert connector._web3 is None
        assert connector._account is None
        assert connector._connected is False
        assert connector.is_connected is False


class TestBlockchainConnectorProperties:
    """Tests for BlockchainConnector properties."""

    def test_network_property(self):
        """Test network property returns correct network."""
        connector = BlockchainConnector(Network.LOCAL)
        assert connector.network == Network.LOCAL

    def test_config_property(self):
        """Test config property returns NetworkConfig."""
        connector = BlockchainConnector(Network.ARBITRUM_ONE)
        config = connector.config
        assert isinstance(config, NetworkConfig)
        assert config.chain_id == 42161

    def test_web3_property_raises_when_not_connected(self):
        """Test web3 property raises RuntimeError when not connected."""
        connector = BlockchainConnector()
        with pytest.raises(RuntimeError) as exc_info:
            _ = connector.web3
        assert "Not connected" in str(exc_info.value)

    def test_account_property_returns_none(self):
        """Test account property returns None when not set."""
        connector = BlockchainConnector()
        assert connector.account is None

    def test_address_property_returns_none(self):
        """Test address property returns None when account not set."""
        connector = BlockchainConnector()
        assert connector.address is None


class TestBlockchainConnectorConnect:
    """Tests for connect functionality."""

    @patch("sdk.blockchain.connector.Web3")
    def test_connect_success(self, mock_web3_class):
        """Test successful connection."""
        mock_web3 = MagicMock()
        mock_web3.is_connected.return_value = True
        mock_web3.eth.chain_id = 421614  # Arbitrum Sepolia
        mock_web3_class.return_value = mock_web3
        mock_web3_class.HTTPProvider = MagicMock()

        connector = BlockchainConnector(Network.ARBITRUM_SEPOLIA)
        result = connector.connect()

        assert result is True
        assert connector.is_connected is True

    @patch("sdk.blockchain.connector.Web3")
    def test_connect_fails_when_not_connected(self, mock_web3_class):
        """Test connection failure when RPC not reachable."""
        mock_web3 = MagicMock()
        mock_web3.is_connected.return_value = False
        mock_web3_class.return_value = mock_web3
        mock_web3_class.HTTPProvider = MagicMock()

        connector = BlockchainConnector(Network.ARBITRUM_SEPOLIA)

        with pytest.raises(ConnectionError) as exc_info:
            connector.connect()

        assert "Failed to connect" in str(exc_info.value)
        assert connector.is_connected is False

    @patch("sdk.blockchain.connector.Web3")
    def test_connect_fails_on_chain_id_mismatch(self, mock_web3_class):
        """Test connection failure on chain ID mismatch."""
        mock_web3 = MagicMock()
        mock_web3.is_connected.return_value = True
        mock_web3.eth.chain_id = 1  # Wrong chain ID for Arbitrum Sepolia
        mock_web3_class.return_value = mock_web3
        mock_web3_class.HTTPProvider = MagicMock()

        connector = BlockchainConnector(Network.ARBITRUM_SEPOLIA)

        with pytest.raises(ConnectionError) as exc_info:
            connector.connect()

        assert "Chain ID mismatch" in str(exc_info.value)

    def test_disconnect(self):
        """Test disconnect resets connection state."""
        connector = BlockchainConnector()
        connector._web3 = MagicMock()
        connector._connected = True

        connector.disconnect()

        assert connector._web3 is None
        assert connector._connected is False


class TestBlockchainConnectorAccount:
    """Tests for account management."""

    def test_set_account_with_0x_prefix(self):
        """Test set_account with 0x prefixed key."""
        connector = BlockchainConnector()
        # Use a valid test private key
        test_key = "0x" + "a" * 64
        address = connector.set_account(test_key)

        assert connector.account is not None
        assert address.startswith("0x")
        assert len(address) == 42

    def test_set_account_without_0x_prefix(self):
        """Test set_account without 0x prefix."""
        connector = BlockchainConnector()
        test_key = "b" * 64
        address = connector.set_account(test_key)

        assert connector.account is not None
        assert connector.address == address

    def test_set_account_from_keyfile(self):
        """Test set_account_from_keyfile."""
        connector = BlockchainConnector()

        # Create a mock keyfile
        keyfile = {
            "version": 3,
            "crypto": {
                "cipher": "aes-128-ctr",
                "ciphertext": "a" * 64,
                "cipherparams": {"iv": "b" * 32},
                "kdf": "scrypt",
                "kdfparams": {
                    "dklen": 32,
                    "n": 2,
                    "p": 1,
                    "r": 8,
                    "salt": "c" * 64,
                },
                "mac": "d" * 64,
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(keyfile, f)
            keyfile_path = f.name

        # Mock the Account.decrypt call
        with patch("sdk.blockchain.connector.Account") as mock_account:
            mock_account.decrypt.return_value = bytes.fromhex("e" * 64)
            mock_account.from_key.return_value = MagicMock(address="0x" + "1" * 40)

            address = connector.set_account_from_keyfile(keyfile_path, "password")

            assert address.startswith("0x")
            mock_account.decrypt.assert_called_once()


class TestBlockchainConnectorBalance:
    """Tests for balance operations."""

    @patch("sdk.blockchain.connector.Web3")
    def test_get_balance_with_address(self, mock_web3_class):
        """Test get_balance with specific address."""
        mock_web3 = MagicMock()
        mock_web3.is_connected.return_value = True
        mock_web3.eth.chain_id = 421614
        mock_web3.eth.get_balance.return_value = 1000000000000000000  # 1 ETH in wei
        mock_web3_class.return_value = mock_web3
        mock_web3_class.HTTPProvider = MagicMock()

        connector = BlockchainConnector(Network.ARBITRUM_SEPOLIA)
        connector.connect()

        balance = connector.get_balance("0x" + "1" * 40)

        assert balance == 1000000000000000000

    @patch("sdk.blockchain.connector.Web3")
    def test_get_balance_uses_current_account(self, mock_web3_class):
        """Test get_balance uses current account when no address specified."""
        mock_web3 = MagicMock()
        mock_web3.is_connected.return_value = True
        mock_web3.eth.chain_id = 421614
        mock_web3.eth.get_balance.return_value = 500000000000000000
        mock_web3_class.return_value = mock_web3
        mock_web3_class.HTTPProvider = MagicMock()

        connector = BlockchainConnector(Network.ARBITRUM_SEPOLIA)
        connector.connect()
        connector.set_account("a" * 64)

        balance = connector.get_balance()

        assert balance == 500000000000000000

    def test_get_balance_raises_without_account(self):
        """Test get_balance raises when no address and no account."""
        connector = BlockchainConnector()
        connector._web3 = MagicMock()

        with pytest.raises(ValueError) as exc_info:
            connector.get_balance()

        assert "No address specified" in str(exc_info.value)

    @patch("sdk.blockchain.connector.Web3")
    def test_get_balance_eth(self, mock_web3_class):
        """Test get_balance_eth returns ETH value."""
        mock_web3 = MagicMock()
        mock_web3.is_connected.return_value = True
        mock_web3.eth.chain_id = 421614
        mock_web3.eth.get_balance.return_value = 2500000000000000000  # 2.5 ETH
        mock_web3_class.return_value = mock_web3
        mock_web3_class.HTTPProvider = MagicMock()
        mock_web3_class.from_wei.return_value = 2.5

        connector = BlockchainConnector(Network.ARBITRUM_SEPOLIA)
        connector.connect()
        connector.set_account("a" * 64)

        balance_eth = connector.get_balance_eth()

        assert balance_eth == 2.5


class TestBlockchainConnectorNonce:
    """Tests for nonce operations."""

    @patch("sdk.blockchain.connector.Web3")
    def test_get_nonce_with_address(self, mock_web3_class):
        """Test get_nonce with specific address."""
        mock_web3 = MagicMock()
        mock_web3.is_connected.return_value = True
        mock_web3.eth.chain_id = 421614
        mock_web3.eth.get_transaction_count.return_value = 42
        mock_web3_class.return_value = mock_web3
        mock_web3_class.HTTPProvider = MagicMock()

        connector = BlockchainConnector(Network.ARBITRUM_SEPOLIA)
        connector.connect()

        nonce = connector.get_nonce("0x" + "1" * 40)

        assert nonce == 42

    def test_get_nonce_raises_without_account(self):
        """Test get_nonce raises when no address and no account."""
        connector = BlockchainConnector()
        connector._web3 = MagicMock()

        with pytest.raises(ValueError) as exc_info:
            connector.get_nonce()

        assert "No address specified" in str(exc_info.value)


class TestBlockchainConnectorGas:
    """Tests for gas operations."""

    @patch("sdk.blockchain.connector.Web3")
    def test_estimate_gas(self, mock_web3_class):
        """Test estimate_gas returns gas estimate."""
        mock_web3 = MagicMock()
        mock_web3.is_connected.return_value = True
        mock_web3.eth.chain_id = 421614
        mock_web3.eth.estimate_gas.return_value = 21000
        mock_web3_class.return_value = mock_web3
        mock_web3_class.HTTPProvider = MagicMock()

        connector = BlockchainConnector(Network.ARBITRUM_SEPOLIA)
        connector.connect()

        tx = {"from": "0x" + "1" * 40, "to": "0x" + "2" * 40, "value": 1000}
        gas = connector.estimate_gas(tx)

        assert gas == 21000

    @patch("sdk.blockchain.connector.Web3")
    def test_get_gas_price(self, mock_web3_class):
        """Test get_gas_price returns current gas price."""
        mock_web3 = MagicMock()
        mock_web3.is_connected.return_value = True
        mock_web3.eth.chain_id = 421614
        mock_web3.eth.gas_price = 20000000000  # 20 Gwei
        mock_web3_class.return_value = mock_web3
        mock_web3_class.HTTPProvider = MagicMock()

        connector = BlockchainConnector(Network.ARBITRUM_SEPOLIA)
        connector.connect()

        gas_price = connector.get_gas_price()

        assert gas_price == 20000000000


class TestBlockchainConnectorTransaction:
    """Tests for transaction operations."""

    def test_send_transaction_raises_without_account(self):
        """Test send_transaction raises when no account set."""
        connector = BlockchainConnector()
        connector._web3 = MagicMock()

        with pytest.raises(ValueError) as exc_info:
            connector.send_transaction("0x" + "1" * 40)

        assert "No account set" in str(exc_info.value)

    @patch("sdk.blockchain.connector.Web3")
    def test_send_transaction_success(self, mock_web3_class):
        """Test successful transaction sending."""
        mock_web3 = MagicMock()
        mock_web3.is_connected.return_value = True
        mock_web3.eth.chain_id = 421614
        mock_web3.eth.get_transaction_count.return_value = 5
        mock_web3.eth.estimate_gas.return_value = 21000
        mock_web3.eth.gas_price = 20000000000
        mock_web3.eth.send_raw_transaction.return_value = b"tx_hash_123"
        mock_web3_class.return_value = mock_web3
        mock_web3_class.HTTPProvider = MagicMock()

        connector = BlockchainConnector(Network.ARBITRUM_SEPOLIA)
        connector.connect()
        connector.set_account("a" * 64)

        # Mock sign_transaction
        connector._account.sign_transaction = MagicMock(
            return_value=MagicMock(raw_transaction=b"signed_tx")
        )

        tx_hash = connector.send_transaction("0x" + "2" * 40, value=1000)

        assert tx_hash is not None

    @patch("sdk.blockchain.connector.Web3")
    def test_wait_for_transaction(self, mock_web3_class):
        """Test wait_for_transaction returns receipt."""
        mock_web3 = MagicMock()
        mock_web3.is_connected.return_value = True
        mock_web3.eth.chain_id = 421614
        mock_receipt = {
            "transactionHash": b"tx_hash",
            "blockNumber": 12345,
            "status": 1,
        }
        mock_web3.eth.wait_for_transaction_receipt.return_value = mock_receipt
        mock_web3_class.return_value = mock_web3
        mock_web3_class.HTTPProvider = MagicMock()

        connector = BlockchainConnector(Network.ARBITRUM_SEPOLIA)
        connector.connect()

        receipt = connector.wait_for_transaction("0x" + "1" * 64)

        assert receipt["blockNumber"] == 12345
        assert receipt["status"] == 1


class TestBlockchainConnectorContract:
    """Tests for contract operations."""

    def test_deploy_contract_raises_without_account(self):
        """Test deploy_contract raises when no account set."""
        connector = BlockchainConnector()
        connector._web3 = MagicMock()

        with pytest.raises(ValueError) as exc_info:
            connector.deploy_contract([], "0x")

        assert "No account set" in str(exc_info.value)

    @patch("sdk.blockchain.connector.Web3")
    def test_get_contract_returns_instance(self, mock_web3_class):
        """Test get_contract returns contract instance."""
        mock_web3 = MagicMock()
        mock_web3.is_connected.return_value = True
        mock_web3.eth.chain_id = 421614
        mock_contract = MagicMock()
        mock_web3.eth.contract.return_value = mock_contract
        mock_web3_class.return_value = mock_web3
        mock_web3_class.HTTPProvider = MagicMock()
        mock_web3_class.to_checksum_address = lambda x: x

        connector = BlockchainConnector(Network.ARBITRUM_SEPOLIA)
        connector.connect()

        abi = [{"name": "test", "type": "function"}]
        contract = connector.get_contract("0x" + "1" * 40, abi)

        assert contract == mock_contract


class TestBlockchainConnectorExplorer:
    """Tests for explorer URL generation."""

    def test_get_explorer_url_arbitrum(self):
        """Test explorer URL for Arbitrum."""
        connector = BlockchainConnector(Network.ARBITRUM_ONE)
        tx_hash = "0x" + "a" * 64

        url = connector.get_explorer_url(tx_hash)

        assert "arbiscan.io" in url
        assert tx_hash in url

    def test_get_explorer_url_local_returns_empty(self):
        """Test explorer URL returns empty for local network."""
        connector = BlockchainConnector(Network.LOCAL)
        tx_hash = "0x" + "a" * 64

        url = connector.get_explorer_url(tx_hash)

        assert url == ""


class TestBlockchainConnectorRepr:
    """Tests for string representation."""

    def test_repr_disconnected(self):
        """Test repr when disconnected."""
        connector = BlockchainConnector(Network.ARBITRUM_SEPOLIA)

        repr_str = repr(connector)

        assert "Arbitrum Sepolia" in repr_str
        assert "disconnected" in repr_str
        assert "no account" in repr_str

    def test_repr_connected_with_account(self):
        """Test repr when connected with account."""
        connector = BlockchainConnector(Network.ARBITRUM_ONE)
        connector._connected = True
        connector._web3 = MagicMock()
        connector.set_account("a" * 64)

        repr_str = repr(connector)

        assert "Arbitrum One" in repr_str
        assert "connected" in repr_str
        assert "0x" in repr_str

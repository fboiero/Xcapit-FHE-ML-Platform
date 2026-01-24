"""
Tests for blockchain secrets management.
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest


class TestBlockchainSecretsManager:
    """Tests for BlockchainSecretsManager."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        # Clear any cached imports
        if "apps.blockchain.secrets" in sys.modules:
            del sys.modules["apps.blockchain.secrets"]

    @pytest.fixture
    def mock_core_secrets(self):
        """Mock the core secrets module."""
        mock_secrets = MagicMock()
        mock_secrets.get.return_value = None
        mock_secrets.get_all.return_value = {}
        return mock_secrets

    def test_get_wallet_from_vault(self, mock_core_secrets):
        """Test getting wallet from Vault."""
        mock_core_secrets.get.side_effect = lambda path, key: {
            ("blockchain/deployer", "private_key"): "abc123",
            ("blockchain/deployer", "address"): "0x1234567890abcdef",
        }.get((path, key))

        with patch.dict(sys.modules, {"apps.core.secrets": MagicMock(secrets=mock_core_secrets)}):
            from apps.blockchain.secrets import BlockchainSecretsManager

            manager = BlockchainSecretsManager()
            wallet = manager.get_wallet("deployer")

            assert wallet is not None
            assert wallet.private_key == "abc123"
            assert wallet.address == "0x1234567890abcdef"
            assert wallet.name == "deployer"

    def test_get_wallet_from_env_fallback(self, mock_core_secrets):
        """Test falling back to environment variables."""
        mock_core_secrets.get.return_value = None

        with patch.dict(sys.modules, {"apps.core.secrets": MagicMock(secrets=mock_core_secrets)}):
            with patch.dict(os.environ, {
                "DEPLOYER_PRIVATE_KEY": "env_key_123",
                "DEPLOYER_ADDRESS": "0xenv_address",
            }):
                from apps.blockchain.secrets import BlockchainSecretsManager

                manager = BlockchainSecretsManager()
                wallet = manager.get_wallet("deployer")

                assert wallet is not None
                assert wallet.private_key == "env_key_123"
                assert wallet.address == "0xenv_address"

    def test_get_wallet_not_configured(self, mock_core_secrets):
        """Test when wallet is not configured."""
        mock_core_secrets.get.return_value = None

        with patch.dict(sys.modules, {"apps.core.secrets": MagicMock(secrets=mock_core_secrets)}):
            # Clear environment
            env_backup = {k: v for k, v in os.environ.items() if "DEPLOYER" in k}
            for k in env_backup:
                del os.environ[k]

            try:
                from apps.blockchain.secrets import BlockchainSecretsManager

                manager = BlockchainSecretsManager()
                wallet = manager.get_wallet("deployer")

                assert wallet is None
            finally:
                os.environ.update(env_backup)

    def test_get_deployer(self, mock_core_secrets):
        """Test get_deployer convenience method."""
        mock_core_secrets.get.side_effect = lambda path, key: {
            ("blockchain/deployer", "private_key"): "deployer_key",
            ("blockchain/deployer", "address"): "0xdeployer",
        }.get((path, key))

        with patch.dict(sys.modules, {"apps.core.secrets": MagicMock(secrets=mock_core_secrets)}):
            from apps.blockchain.secrets import BlockchainSecretsManager

            manager = BlockchainSecretsManager()
            wallet = manager.get_deployer()

            assert wallet is not None
            assert wallet.name == "deployer"

    def test_get_consortium_signer(self, mock_core_secrets):
        """Test get_consortium_signer convenience method."""
        mock_core_secrets.get.side_effect = lambda path, key: {
            ("blockchain/consortium-signer", "private_key"): "signer_key",
            ("blockchain/consortium-signer", "address"): "0xsigner",
        }.get((path, key))

        with patch.dict(sys.modules, {"apps.core.secrets": MagicMock(secrets=mock_core_secrets)}):
            from apps.blockchain.secrets import BlockchainSecretsManager

            manager = BlockchainSecretsManager()
            wallet = manager.get_consortium_signer()

            assert wallet is not None
            assert wallet.name == "consortium-signer"

    def test_get_rpc_config(self, mock_core_secrets):
        """Test getting RPC configuration."""
        mock_core_secrets.get_all.return_value = {
            "arbitrum_url": "https://custom.arbitrum.rpc",
            "arbitrum_sepolia_url": "https://custom.sepolia.rpc",
        }

        with patch.dict(sys.modules, {"apps.core.secrets": MagicMock(secrets=mock_core_secrets)}):
            from apps.blockchain.secrets import BlockchainSecretsManager

            manager = BlockchainSecretsManager()
            config = manager.get_rpc_config()

            assert config.arbitrum_url == "https://custom.arbitrum.rpc"
            assert config.arbitrum_sepolia_url == "https://custom.sepolia.rpc"

    def test_get_rpc_url_defaults(self, mock_core_secrets):
        """Test RPC URL defaults when not configured."""
        mock_core_secrets.get_all.return_value = {}

        with patch.dict(sys.modules, {"apps.core.secrets": MagicMock(secrets=mock_core_secrets)}):
            from apps.blockchain.secrets import BlockchainSecretsManager

            manager = BlockchainSecretsManager()

            sepolia_url = manager.get_rpc_url("arbitrum_sepolia")
            assert "sepolia" in sepolia_url.lower()

            mainnet_url = manager.get_rpc_url("arbitrum")
            assert "arb1" in mainnet_url.lower()

    def test_get_contracts(self, mock_core_secrets):
        """Test getting contract addresses."""
        mock_core_secrets.get_all.return_value = {
            "governance": "0xgov",
            "model_registry": "0xmodel",
            "computation_verifier": "0xverifier",
        }

        with patch.dict(sys.modules, {"apps.core.secrets": MagicMock(secrets=mock_core_secrets)}):
            from apps.blockchain.secrets import BlockchainSecretsManager

            manager = BlockchainSecretsManager()
            contracts = manager.get_contracts("arbitrum_sepolia")

            assert contracts.governance == "0xgov"
            assert contracts.model_registry == "0xmodel"
            assert contracts.computation_verifier == "0xverifier"
            assert contracts.network == "arbitrum_sepolia"

    def test_get_contracts_from_env(self, mock_core_secrets):
        """Test getting contract addresses from environment."""
        mock_core_secrets.get_all.return_value = None

        with patch.dict(sys.modules, {"apps.core.secrets": MagicMock(secrets=mock_core_secrets)}):
            with patch.dict(os.environ, {
                "GOVERNANCE_CONTRACT_ADDRESS": "0xenv_gov",
                "MODEL_REGISTRY_CONTRACT_ADDRESS": "0xenv_model",
                "COMPUTATION_VERIFIER_CONTRACT_ADDRESS": "0xenv_verifier",
            }):
                from apps.blockchain.secrets import BlockchainSecretsManager

                manager = BlockchainSecretsManager()
                contracts = manager.get_contracts()

                assert contracts.governance == "0xenv_gov"
                assert contracts.model_registry == "0xenv_model"
                assert contracts.computation_verifier == "0xenv_verifier"

    def test_cache_clearing(self, mock_core_secrets):
        """Test cache clearing after key rotation."""
        call_count = 0

        def get_side_effect(path, key):
            nonlocal call_count
            call_count += 1
            if (path, key) == ("blockchain/deployer", "private_key"):
                return f"key_{call_count}"
            if (path, key) == ("blockchain/deployer", "address"):
                return "0xaddr"
            return None

        mock_core_secrets.get.side_effect = get_side_effect

        with patch.dict(sys.modules, {"apps.core.secrets": MagicMock(secrets=mock_core_secrets)}):
            from apps.blockchain.secrets import BlockchainSecretsManager

            manager = BlockchainSecretsManager()

            # First call - should cache
            wallet1 = manager.get_wallet("deployer")
            key1 = wallet1.private_key

            # Second call - should use cache
            wallet2 = manager.get_wallet("deployer")
            assert wallet2.private_key == key1

            # Clear cache
            manager.clear_cache()

            # Third call - should get fresh value
            wallet3 = manager.get_wallet("deployer")
            assert wallet3.private_key != key1

    def test_wallet_repr_hides_private_key(self, mock_core_secrets):
        """Test that wallet repr doesn't expose private key."""
        mock_core_secrets.get.side_effect = lambda path, key: {
            ("blockchain/deployer", "private_key"): "super_secret_key",
            ("blockchain/deployer", "address"): "0x1234567890abcdef1234567890abcdef12345678",
        }.get((path, key))

        with patch.dict(sys.modules, {"apps.core.secrets": MagicMock(secrets=mock_core_secrets)}):
            from apps.blockchain.secrets import BlockchainSecretsManager

            manager = BlockchainSecretsManager()
            wallet = manager.get_wallet("deployer")

            wallet_str = repr(wallet)
            assert "super_secret_key" not in wallet_str
            assert "deployer" in wallet_str


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    @pytest.fixture
    def mock_core_secrets(self):
        """Mock the core secrets module."""
        mock_secrets = MagicMock()
        mock_secrets.get.side_effect = lambda path, key: {
            ("blockchain/deployer", "private_key"): "key1",
            ("blockchain/deployer", "address"): "0xaddr1",
            ("blockchain/consortium-signer", "private_key"): "key2",
            ("blockchain/consortium-signer", "address"): "0xaddr2",
            ("blockchain/verifier", "private_key"): "key3",
            ("blockchain/verifier", "address"): "0xaddr3",
        }.get((path, key))
        mock_secrets.get_all.return_value = {}
        return mock_secrets

    def test_get_deployer_wallet(self, mock_core_secrets):
        """Test get_deployer_wallet function."""
        # Clear cached module
        if "apps.blockchain.secrets" in sys.modules:
            del sys.modules["apps.blockchain.secrets"]

        with patch.dict(sys.modules, {"apps.core.secrets": MagicMock(secrets=mock_core_secrets)}):
            from apps.blockchain.secrets import get_deployer_wallet

            wallet = get_deployer_wallet()
            assert wallet is not None
            assert wallet.name == "deployer"

    def test_get_rpc_url(self, mock_core_secrets):
        """Test get_rpc_url function."""
        if "apps.blockchain.secrets" in sys.modules:
            del sys.modules["apps.blockchain.secrets"]

        with patch.dict(sys.modules, {"apps.core.secrets": MagicMock(secrets=mock_core_secrets)}):
            from apps.blockchain.secrets import get_rpc_url

            url = get_rpc_url("arbitrum_sepolia")
            assert "sepolia" in url.lower()

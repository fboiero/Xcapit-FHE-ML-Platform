"""
Tests to boost blockchain module coverage to 90%+.

Covers uncovered lines in:
- apps/blockchain/services.py (67% -> 90%+)
- apps/blockchain/resilience.py (87% -> 90%+)
- apps/blockchain/secrets.py (93% -> 95%+)

Each test documents which uncovered lines it targets.
"""

import json
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from threading import Thread
from unittest.mock import MagicMock, Mock, PropertyMock, patch, call

import pytest

from apps.blockchain.resilience import (
    CircuitBreaker,
    CircuitBreakerOpen,
    CircuitBreakerState,
    CircuitState,
    with_retry,
    with_timeout,
)
from apps.blockchain.secrets import BlockchainWallet
from apps.blockchain.services import (
    BlockchainService,
    ComputationVerifierService,
    ConsortiumService,
    ModelRegistryService,
    TransactionResult,
)


# =============================================================================
# Helper: create a BlockchainService with a mocked Web3 instance
# =============================================================================

def _make_service_with_web3() -> tuple[BlockchainService, MagicMock]:
    """Create a BlockchainService with a fully mocked Web3 and circuit reset."""
    svc = BlockchainService()
    mock_web3 = MagicMock()
    mock_web3.is_connected.return_value = True
    mock_web3.eth.chain_id = 421614
    mock_web3.eth.get_transaction_count.return_value = 0
    mock_web3.eth.estimate_gas.return_value = 21000
    mock_web3.eth.get_block.return_value = {"baseFeePerGas": 1000}
    mock_web3.to_checksum_address.side_effect = lambda x: x
    mock_web3.to_wei.return_value = 100000
    mock_web3.from_wei.return_value = 1.0
    svc._web3 = mock_web3
    svc._chain_id = 421614
    svc._circuit.reset()
    return svc, mock_web3


def _make_wallet(prefix: str = "0x") -> BlockchainWallet:
    """Create a test BlockchainWallet."""
    return BlockchainWallet(
        address="0x1234567890abcdef1234567890abcdef12345678",
        private_key=f"{prefix}abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890ab",
        name="test-wallet",
    )


# =============================================================================
# services.py — BlockchainService._connect() (lines 81, 93, 97-114, 118-120)
# =============================================================================


class TestBlockchainServiceConnect:
    """Tests covering the _connect() method and web3 property lazy init."""

    def test_web3_property_triggers_connect(self):
        """Line 81: self._connect() is called when _web3 is None."""
        svc = BlockchainService()
        svc._web3 = None
        with patch.object(svc, "_connect") as mock_connect:
            # After _connect, _web3 should be set
            def side_effect():
                svc._web3 = MagicMock()
            mock_connect.side_effect = side_effect
            _ = svc.web3
            mock_connect.assert_called_once()

    def test_connect_circuit_open_raises(self):
        """Line 93: raise CircuitBreakerOpen when circuit is open."""
        svc = BlockchainService()
        svc._circuit._state.state = CircuitState.OPEN
        svc._circuit._state.last_failure_time = datetime.utcnow()
        try:
            with pytest.raises(CircuitBreakerOpen):
                svc._connect()
        finally:
            svc._circuit.reset()

    def test_connect_success(self):
        """Lines 97-114: Full successful Web3 connection path."""
        svc = BlockchainService()
        svc._circuit.reset()

        mock_web3_cls = MagicMock()
        mock_web3_instance = MagicMock()
        mock_web3_instance.is_connected.return_value = True
        mock_web3_instance.eth.chain_id = 421614
        mock_web3_cls.return_value = mock_web3_instance
        mock_web3_cls.HTTPProvider.return_value = MagicMock()

        mock_poa_middleware = MagicMock()

        mock_web3_module = MagicMock()
        mock_web3_module.Web3 = mock_web3_cls
        mock_middleware_module = MagicMock()
        mock_middleware_module.ExtraDataToPOAMiddleware = mock_poa_middleware

        with patch.dict(sys.modules, {
            "web3": mock_web3_module,
            "web3.middleware": mock_middleware_module,
        }):
            with patch("apps.blockchain.services.get_rpc_url", return_value="https://test-rpc.example.com"):
                svc._connect()

        assert svc._web3 is mock_web3_instance
        assert svc._chain_id == 421614

    def test_connect_not_connected_records_failure(self):
        """Lines 108-110: Records circuit failure when is_connected() is False."""
        svc = BlockchainService()
        svc._circuit.reset()

        mock_web3_cls = MagicMock()
        mock_web3_instance = MagicMock()
        mock_web3_instance.is_connected.return_value = False
        mock_web3_cls.return_value = mock_web3_instance
        mock_web3_cls.HTTPProvider.return_value = MagicMock()

        mock_web3_module = MagicMock()
        mock_web3_module.Web3 = mock_web3_cls
        mock_middleware_module = MagicMock()

        with patch.dict(sys.modules, {
            "web3": mock_web3_module,
            "web3.middleware": mock_middleware_module,
        }):
            with patch("apps.blockchain.services.get_rpc_url", return_value="https://test-rpc.example.com"):
                with pytest.raises(ConnectionError, match="Failed to connect"):
                    svc._connect()

    def test_connect_import_error(self):
        """Lines 116-117: ImportError when web3 is not installed."""
        svc = BlockchainService()
        svc._circuit.reset()

        with patch.dict(sys.modules, {"web3": None}):
            with pytest.raises(ImportError, match="web3 package required"):
                svc._connect()

    def test_connect_rpc_exception(self):
        """Lines 118-120: RPC exceptions record circuit failure and re-raise."""
        svc = BlockchainService()
        svc._circuit.reset()

        mock_web3_module = MagicMock()
        mock_middleware_module = MagicMock()

        with patch.dict(sys.modules, {
            "web3": mock_web3_module,
            "web3.middleware": mock_middleware_module,
        }):
            with patch("apps.blockchain.services.get_rpc_url", side_effect=ConnectionError("RPC down")):
                with pytest.raises(ConnectionError):
                    svc._connect()


# =============================================================================
# services.py — chain_id property (line 139)
# =============================================================================


class TestBlockchainServiceChainId:
    """Tests covering chain_id property lazy init."""

    def test_chain_id_initializes_connection_when_none(self):
        """Line 139: _ = self.web3 initializes connection when _chain_id is None."""
        svc = BlockchainService()
        svc._chain_id = None
        svc._web3 = None

        def fake_connect():
            svc._web3 = MagicMock()
            svc._chain_id = 421614

        with patch.object(svc, "_connect", side_effect=fake_connect):
            result = svc.chain_id
            assert result == 421614


# =============================================================================
# services.py — _load_contract_abi v2 path + _get_contract (lines 148-155, 159-160)
# =============================================================================


class TestBlockchainServiceContractLoading:
    """Tests covering ABI loading and contract instantiation."""

    def test_load_abi_v2_path(self):
        """Lines 148, 153-155: Loads from v2 path when primary path missing."""
        svc = BlockchainService()

        abi_data = {"abi": [{"type": "function", "name": "test"}]}

        with patch.object(Path, "exists") as mock_exists:
            # First path doesn't exist, second (v2) does
            mock_exists.side_effect = [False, True]
            with patch("builtins.open", create=True) as mock_open:
                mock_open.return_value.__enter__ = lambda s: s
                mock_open.return_value.__exit__ = Mock(return_value=False)
                mock_open.return_value.read = Mock(return_value=json.dumps(abi_data))
                with patch("json.load", return_value=abi_data):
                    result = svc._load_contract_abi("TestContract")

        assert result == abi_data["abi"]

    def test_load_abi_not_found(self):
        """Line 151: FileNotFoundError when both paths missing."""
        svc = BlockchainService()

        with patch.object(Path, "exists", return_value=False):
            with pytest.raises(FileNotFoundError, match="Contract ABI not found"):
                svc._load_contract_abi("NonExistent")

    def test_load_abi_no_abi_key(self):
        """Line 155: Falls back to full artifact when 'abi' key is missing."""
        svc = BlockchainService()
        # artifact is a dict without an "abi" key — .get("abi", artifact) returns artifact
        raw_artifact = {"bytecode": "0x...", "metadata": {}}

        with patch.object(Path, "exists", return_value=True):
            with patch("builtins.open", create=True) as mock_open:
                mock_open.return_value.__enter__ = lambda s: s
                mock_open.return_value.__exit__ = Mock(return_value=False)
                with patch("json.load", return_value=raw_artifact):
                    result = svc._load_contract_abi("SimpleContract")

        assert result == raw_artifact

    def test_get_contract(self):
        """Lines 159-160: Creates contract instance from ABI and address."""
        svc, mock_web3 = _make_service_with_web3()
        mock_contract = MagicMock()
        mock_web3.eth.contract.return_value = mock_contract

        with patch.object(svc, "_load_contract_abi", return_value=[{"type": "function"}]):
            result = svc._get_contract("0xContractAddr", "TestContract")

        assert result is mock_contract
        mock_web3.eth.contract.assert_called_once()


# =============================================================================
# services.py — _sign_and_send + _sign_and_send_with_retry
# (lines 205, 228-253, 260-262)
# =============================================================================


class TestBlockchainServiceSignAndSend:
    """Tests covering transaction signing, sending, and receipt handling."""

    def test_sign_and_send_delegates_to_retry(self):
        """Line 205: _sign_and_send delegates to _sign_and_send_with_retry."""
        svc, _ = _make_service_with_web3()
        wallet = _make_wallet()
        expected = TransactionResult(success=True, tx_hash="0xabc")

        with patch.object(svc, "_sign_and_send_with_retry", return_value=expected) as mock_retry:
            result = svc._sign_and_send(wallet, {"data": "test"})

        assert result is expected
        mock_retry.assert_called_once_with(wallet, {"data": "test"})

    def test_sign_and_send_success_with_0x_prefix(self):
        """Lines 228-250: Full success path with key already having 0x prefix."""
        svc, mock_web3 = _make_service_with_web3()
        wallet = _make_wallet(prefix="0x")

        mock_account = MagicMock()
        mock_signed = MagicMock()
        mock_signed.raw_transaction = b"\x00" * 32
        mock_account.sign_transaction.return_value = mock_signed

        mock_tx_hash = MagicMock()
        mock_tx_hash.hex.return_value = "abcd1234"
        mock_web3.eth.send_raw_transaction.return_value = mock_tx_hash
        mock_web3.eth.wait_for_transaction_receipt.return_value = {
            "status": 1,
            "blockNumber": 100,
            "gasUsed": 21000,
        }

        with patch.dict(sys.modules, {"eth_account": MagicMock(Account=mock_account)}):
            with patch("eth_account.Account", mock_account):
                result = svc._sign_and_send_with_retry(wallet, {})

        assert result.success is True
        assert result.block_number == 100
        assert result.gas_used == 21000

    def test_sign_and_send_success_without_0x_prefix(self):
        """Line 229: Private key without 0x prefix gets prefixed."""
        svc, mock_web3 = _make_service_with_web3()
        wallet = _make_wallet(prefix="")

        mock_account = MagicMock()
        mock_signed = MagicMock()
        mock_signed.raw_transaction = b"\x00" * 32
        mock_account.sign_transaction.return_value = mock_signed

        mock_tx_hash = MagicMock()
        mock_tx_hash.hex.return_value = "ef567890"
        mock_web3.eth.send_raw_transaction.return_value = mock_tx_hash
        mock_web3.eth.wait_for_transaction_receipt.return_value = {
            "status": 1,
            "blockNumber": 200,
            "gasUsed": 42000,
        }

        with patch.dict(sys.modules, {"eth_account": MagicMock(Account=mock_account)}):
            with patch("eth_account.Account", mock_account):
                result = svc._sign_and_send_with_retry(wallet, {})

        assert result.success is True
        # Verify the key was prefixed with 0x
        sign_call = mock_account.sign_transaction.call_args
        assert sign_call[0][1].startswith("0x")

    def test_sign_and_send_transaction_reverted(self):
        """Lines 251-257: Transaction reverted (status != 1)."""
        svc, mock_web3 = _make_service_with_web3()
        wallet = _make_wallet()

        mock_account = MagicMock()
        mock_signed = MagicMock()
        mock_signed.raw_transaction = b"\x00" * 32
        mock_account.sign_transaction.return_value = mock_signed

        mock_tx_hash = MagicMock()
        mock_tx_hash.hex.return_value = "deadbeef"
        mock_web3.eth.send_raw_transaction.return_value = mock_tx_hash
        mock_web3.eth.wait_for_transaction_receipt.return_value = {
            "status": 0,
            "blockNumber": 300,
            "gasUsed": 50000,
        }

        with patch.dict(sys.modules, {"eth_account": MagicMock(Account=mock_account)}):
            with patch("eth_account.Account", mock_account):
                result = svc._sign_and_send_with_retry(wallet, {})

        assert result.success is False
        assert result.error == "Transaction reverted"
        assert result.tx_hash == "deadbeef"

    def test_sign_and_send_rpc_exception(self):
        """Lines 259-262: RPC exception records circuit failure and re-raises."""
        svc, mock_web3 = _make_service_with_web3()
        wallet = _make_wallet()

        mock_account = MagicMock()
        mock_account.sign_transaction.side_effect = ConnectionError("RPC down")

        with patch.dict(sys.modules, {"eth_account": MagicMock(Account=mock_account)}):
            with patch("eth_account.Account", mock_account):
                with pytest.raises(ConnectionError):
                    svc._sign_and_send_with_retry(wallet, {})

    def test_sign_and_send_generic_exception(self):
        """Lines 264-266: Generic exception returns failed TransactionResult."""
        svc, mock_web3 = _make_service_with_web3()
        wallet = _make_wallet()

        mock_account = MagicMock()
        mock_account.sign_transaction.side_effect = RuntimeError("unexpected")

        with patch.dict(sys.modules, {"eth_account": MagicMock(Account=mock_account)}):
            with patch("eth_account.Account", mock_account):
                result = svc._sign_and_send_with_retry(wallet, {})

        assert result.success is False
        assert "unexpected" in result.error


# =============================================================================
# services.py — ConsortiumService with wallet (lines 294-296, 323-329,
# 342-348, 364-370, 374-375, 387-390)
# =============================================================================


class TestConsortiumServiceWithWallet:
    """Tests for ConsortiumService methods when wallet IS available."""

    @pytest.fixture
    def consortium_svc(self):
        """Set up ConsortiumService with mocked web3 and contract."""
        svc = ConsortiumService("0xGovernanceContract")
        mock_web3 = MagicMock()
        mock_web3.is_connected.return_value = True
        mock_web3.eth.chain_id = 421614
        mock_web3.eth.get_transaction_count.return_value = 0
        mock_web3.eth.estimate_gas.return_value = 21000
        mock_web3.eth.get_block.return_value = {"baseFeePerGas": 1000}
        mock_web3.to_checksum_address.side_effect = lambda x: x
        mock_web3.to_wei.return_value = 100000
        svc._web3 = mock_web3
        svc._chain_id = 421614
        svc._circuit.reset()

        mock_contract = MagicMock()
        mock_contract.encodeABI.return_value = b"\x00" * 32
        svc._contract = mock_contract
        return svc

    def test_contract_property_lazy_init(self):
        """Lines 294-296: Contract property calls _get_contract when None."""
        svc = ConsortiumService("0xGovernanceContract")
        svc._contract = None
        mock_contract = MagicMock()

        with patch.object(svc, "_get_contract", return_value=mock_contract):
            result = svc.contract
            assert result is mock_contract

    def test_create_consortium_with_wallet(self, consortium_svc):
        """Lines 323-329: create_consortium builds tx and signs."""
        wallet = _make_wallet()
        expected = TransactionResult(success=True, tx_hash="0x111")

        with patch.object(consortium_svc, "_sign_and_send", return_value=expected):
            result = consortium_svc.create_consortium(
                name="Test",
                min_voting_quorum=50,
                voting_duration=3600,
                model_config_hash=b"\x00" * 32,
                wallet=wallet,
            )

        assert result.success is True

    def test_create_consortium_default_wallet(self, consortium_svc):
        """Lines 319-321: Falls back to get_consortium_signer_wallet."""
        wallet = _make_wallet()
        expected = TransactionResult(success=True, tx_hash="0x222")

        with patch("apps.blockchain.services.get_consortium_signer_wallet", return_value=wallet):
            with patch.object(consortium_svc, "_sign_and_send", return_value=expected):
                result = consortium_svc.create_consortium(
                    name="Test", min_voting_quorum=50,
                    voting_duration=3600, model_config_hash=b"\x00" * 32,
                )

        assert result.success is True

    def test_create_consortium_str_data(self, consortium_svc):
        """Line 328: Handles encodeABI returning str (calls .encode())."""
        consortium_svc._contract.encodeABI.return_value = "0xabcdef"
        wallet = _make_wallet()
        expected = TransactionResult(success=True, tx_hash="0x333")

        with patch.object(consortium_svc, "_sign_and_send", return_value=expected):
            with patch.object(consortium_svc, "_build_transaction", return_value={"data": "test"}) as mock_build:
                result = consortium_svc.create_consortium(
                    name="Test", min_voting_quorum=50,
                    voting_duration=3600, model_config_hash=b"\x00" * 32,
                    wallet=wallet,
                )
        assert result.success is True

    def test_add_member_with_wallet(self, consortium_svc):
        """Lines 342-348: add_member builds tx and signs."""
        wallet = _make_wallet()
        expected = TransactionResult(success=True, tx_hash="0x444")

        with patch.object(consortium_svc, "_sign_and_send", return_value=expected):
            result = consortium_svc.add_member(
                consortium_id=b"\x01" * 32,
                new_member="0xMember",
                wallet=wallet,
            )

        assert result.success is True

    def test_record_contribution_with_wallet(self, consortium_svc):
        """Lines 364-370: record_contribution builds tx and signs."""
        wallet = _make_wallet()
        expected = TransactionResult(success=True, tx_hash="0x555")

        with patch.object(consortium_svc, "_sign_and_send", return_value=expected):
            result = consortium_svc.record_contribution(
                consortium_id=b"\x01" * 32,
                record_count=100,
                feature_count=10,
                data_hash=b"\x02" * 32,
                checksum_hash=b"\x03" * 32,
                wallet=wallet,
            )

        assert result.success is True

    def test_get_consortium(self, consortium_svc):
        """Lines 374-383: get_consortium returns dict from contract call."""
        consortium_svc._contract.functions.getConsortium.return_value.call.return_value = (
            "Test Consortium",  # name
            "0xOwner",          # owner
            1,                  # status
            5,                  # member_count
            100,                # total_contributions
            50,                 # min_voting_quorum
            3600,               # voting_duration
        )

        result = consortium_svc.get_consortium(b"\x01" * 32)

        assert result["name"] == "Test Consortium"
        assert result["owner"] == "0xOwner"
        assert result["status"] == 1
        assert result["member_count"] == 5
        assert result["total_contributions"] == 100
        assert result["min_voting_quorum"] == 50
        assert result["voting_duration"] == 3600

    def test_get_member(self, consortium_svc):
        """Lines 387-396: get_member returns dict from contract call."""
        consortium_svc._contract.functions.getMember.return_value.call.return_value = (
            1,     # status
            1000,  # joined_at
            5,     # contribution_count
            100,   # contribution_weight
            2000,  # last_contribution_at
        )

        result = consortium_svc.get_member(b"\x01" * 32, "0xMember")

        assert result["status"] == 1
        assert result["joined_at"] == 1000
        assert result["contribution_count"] == 5
        assert result["contribution_weight"] == 100
        assert result["last_contribution_at"] == 2000


# =============================================================================
# services.py — ModelRegistryService (lines 414-416, 429-435, 450-456, 460-461, 474)
# =============================================================================


class TestModelRegistryServiceWithWallet:
    """Tests for ModelRegistryService methods when wallet IS available."""

    @pytest.fixture
    def registry_svc(self):
        """Set up ModelRegistryService with mocked web3 and contract."""
        svc = ModelRegistryService("0xModelRegistryContract")
        mock_web3 = MagicMock()
        mock_web3.is_connected.return_value = True
        mock_web3.eth.chain_id = 421614
        mock_web3.eth.get_transaction_count.return_value = 0
        mock_web3.eth.estimate_gas.return_value = 21000
        mock_web3.eth.get_block.return_value = {"baseFeePerGas": 1000}
        mock_web3.to_checksum_address.side_effect = lambda x: x
        mock_web3.to_wei.return_value = 100000
        svc._web3 = mock_web3
        svc._chain_id = 421614
        svc._circuit.reset()

        mock_contract = MagicMock()
        mock_contract.encodeABI.return_value = b"\x00" * 32
        svc._contract = mock_contract
        return svc

    def test_contract_property_lazy_init(self):
        """Lines 414-416: Contract property calls _get_contract when None."""
        svc = ModelRegistryService("0xModelRegistry")
        svc._contract = None
        mock_contract = MagicMock()

        with patch.object(svc, "_get_contract", return_value=mock_contract):
            result = svc.contract
            assert result is mock_contract

    def test_register_model_with_wallet(self, registry_svc):
        """Lines 429-435: register_model builds tx and signs."""
        wallet = _make_wallet()
        expected = TransactionResult(success=True, tx_hash="0x666")

        with patch.object(registry_svc, "_sign_and_send", return_value=expected):
            result = registry_svc.register_model(
                model_type="linear_regression",
                version="1.0",
                wallet=wallet,
            )

        assert result.success is True

    def test_register_model_default_wallet(self, registry_svc):
        """register_model falls back to get_consortium_signer_wallet."""
        wallet = _make_wallet()
        expected = TransactionResult(success=True, tx_hash="0x777")

        with patch("apps.blockchain.services.get_consortium_signer_wallet", return_value=wallet):
            with patch.object(registry_svc, "_sign_and_send", return_value=expected):
                result = registry_svc.register_model(
                    model_type="logistic_regression", version="2.0",
                )

        assert result.success is True

    def test_save_checkpoint_with_wallet(self, registry_svc):
        """Lines 450-456: save_checkpoint builds tx and signs."""
        wallet = _make_wallet()
        expected = TransactionResult(success=True, tx_hash="0x888")

        with patch.object(registry_svc, "_sign_and_send", return_value=expected):
            result = registry_svc.save_checkpoint(
                model_id=b"\x01" * 32,
                epoch=5,
                weights_hash=b"\x02" * 32,
                metrics_hash=b"\x03" * 32,
                wallet=wallet,
            )

        assert result.success is True

    def test_get_model(self, registry_svc):
        """Lines 460-470: get_model returns dict from contract call."""
        registry_svc._contract.functions.getModel.return_value.call.return_value = (
            "0xOwner",          # owner
            "linear_regression",  # model_type
            "1.0",              # version
            b"\xab" * 32,      # weights_hash
            1000,               # created_at
            2000,               # updated_at
            True,               # verified
            True,               # active
        )

        result = registry_svc.get_model(b"\x01" * 32)

        assert result["owner"] == "0xOwner"
        assert result["model_type"] == "linear_regression"
        assert result["version"] == "1.0"
        assert result["verified"] is True
        assert result["active"] is True
        assert len(result["weights_hash"]) == 64  # hex string

    def test_verify_checkpoint(self, registry_svc):
        """Line 474: verify_checkpoint calls contract function."""
        registry_svc._contract.functions.verifyCheckpoint.return_value.call.return_value = True

        result = registry_svc.verify_checkpoint(
            model_id=b"\x01" * 32,
            epoch=5,
            weights_hash=b"\x02" * 32,
        )

        assert result is True


# =============================================================================
# services.py — ComputationVerifierService (lines 492-494, 509-515, 529-535, 539, 543)
# =============================================================================


class TestComputationVerifierServiceWithWallet:
    """Tests for ComputationVerifierService methods when wallet IS available."""

    @pytest.fixture
    def verifier_svc(self):
        """Set up ComputationVerifierService with mocked web3 and contract."""
        svc = ComputationVerifierService("0xVerifierContract")
        mock_web3 = MagicMock()
        mock_web3.is_connected.return_value = True
        mock_web3.eth.chain_id = 421614
        mock_web3.eth.get_transaction_count.return_value = 0
        mock_web3.eth.estimate_gas.return_value = 21000
        mock_web3.eth.get_block.return_value = {"baseFeePerGas": 1000}
        mock_web3.to_checksum_address.side_effect = lambda x: x
        mock_web3.to_wei.return_value = 100000
        svc._web3 = mock_web3
        svc._chain_id = 421614
        svc._circuit.reset()

        mock_contract = MagicMock()
        mock_contract.encodeABI.return_value = b"\x00" * 32
        svc._contract = mock_contract
        return svc

    def test_contract_property_lazy_init(self):
        """Lines 492-494: Contract property calls _get_contract when None."""
        svc = ComputationVerifierService("0xVerifier")
        svc._contract = None
        mock_contract = MagicMock()

        with patch.object(svc, "_get_contract", return_value=mock_contract):
            result = svc.contract
            assert result is mock_contract

    def test_register_computation_with_wallet(self, verifier_svc):
        """Lines 509-515: register_computation builds tx and signs."""
        wallet = _make_wallet()
        expected = TransactionResult(success=True, tx_hash="0x999")

        with patch.object(verifier_svc, "_sign_and_send", return_value=expected):
            result = verifier_svc.register_computation(
                model_id=b"\x01" * 32,
                input_hash=b"\x02" * 32,
                output_hash=b"\x03" * 32,
                proof_hash=b"\x04" * 32,
                wallet=wallet,
            )

        assert result.success is True

    def test_register_computation_default_wallet(self, verifier_svc):
        """register_computation falls back to get_consortium_signer_wallet."""
        wallet = _make_wallet()
        expected = TransactionResult(success=True, tx_hash="0xaaa")

        with patch("apps.blockchain.services.get_consortium_signer_wallet", return_value=wallet):
            with patch.object(verifier_svc, "_sign_and_send", return_value=expected):
                result = verifier_svc.register_computation(
                    model_id=b"\x01" * 32,
                    input_hash=b"\x02" * 32,
                    output_hash=b"\x03" * 32,
                )

        assert result.success is True

    def test_register_batch_with_wallet(self, verifier_svc):
        """Lines 529-535: register_batch builds tx and signs."""
        wallet = _make_wallet()
        expected = TransactionResult(success=True, tx_hash="0xbbb")

        with patch.object(verifier_svc, "_sign_and_send", return_value=expected):
            result = verifier_svc.register_batch(
                model_id=b"\x01" * 32,
                input_hashes=[b"\x02" * 32, b"\x03" * 32],
                output_hashes=[b"\x04" * 32, b"\x05" * 32],
                wallet=wallet,
            )

        assert result.success is True

    def test_verify_output(self, verifier_svc):
        """Line 539: verify_output calls contract function."""
        verifier_svc._contract.functions.verifyOutput.return_value.call.return_value = (
            True,
            b"\x06" * 32,
        )

        result = verifier_svc.verify_output(
            model_id=b"\x01" * 32,
            input_hash=b"\x02" * 32,
            output_hash=b"\x03" * 32,
        )

        assert result == (True, b"\x06" * 32)

    def test_get_expected_output(self, verifier_svc):
        """Line 543: get_expected_output calls contract function."""
        verifier_svc._contract.functions.getExpectedOutput.return_value.call.return_value = b"\x07" * 32

        result = verifier_svc.get_expected_output(
            model_id=b"\x01" * 32,
            input_hash=b"\x02" * 32,
        )

        assert result == b"\x07" * 32


# =============================================================================
# resilience.py — CircuitBreaker singleton re-init (line 102)
# =============================================================================


class TestCircuitBreakerSingleton:
    """Tests covering the singleton __init__ guard."""

    def test_second_init_returns_early(self):
        """Line 102: Second __init__ returns early because _initialized is set."""
        # Use a unique name to get a fresh singleton
        circuit = CircuitBreaker("test_singleton_reinit_unique", failure_threshold=5)
        circuit.reset()

        original_config = circuit.config.failure_threshold

        # Re-initialize with different params — should be ignored
        circuit2 = CircuitBreaker("test_singleton_reinit_unique", failure_threshold=99)

        # Same instance
        assert circuit is circuit2
        # Config unchanged
        assert circuit.config.failure_threshold == original_config

        # Clean up singleton
        with CircuitBreaker._lock:
            CircuitBreaker._instances.pop("test_singleton_reinit_unique", None)


# =============================================================================
# resilience.py — _check_recovery_timeout with last_failure_time=None (line 138)
# =============================================================================


class TestCircuitBreakerRecoveryTimeout:
    """Tests covering _check_recovery_timeout edge cases."""

    def test_check_recovery_timeout_no_failure_time(self):
        """Line 138: Returns when state is OPEN but last_failure_time is None."""
        circuit = CircuitBreaker("test_recovery_none_time", failure_threshold=1)
        circuit.reset()

        # Force OPEN state but with no failure time
        circuit._state.state = CircuitState.OPEN
        circuit._state.last_failure_time = None

        circuit._check_recovery_timeout()

        # Should remain OPEN (not transition to HALF_OPEN)
        assert circuit._state.state == CircuitState.OPEN

        circuit.reset()
        with CircuitBreaker._lock:
            CircuitBreaker._instances.pop("test_recovery_none_time", None)


# =============================================================================
# resilience.py — with_retry: last_exception fallback (line 352)
# =============================================================================


class TestRetryLastExceptionFallback:
    """Tests covering the final raise last_exception fallback in with_retry."""

    def test_retry_raises_last_exception_on_max_attempts(self):
        """Line 352: Although normally unreachable, test the retry exhaustion path.
        The last exception is raised when max attempts are exhausted."""
        call_count = 0

        @with_retry(max_attempts=2, backoff_base=0.01, retryable_exceptions=(ValueError,))
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise ValueError(f"Attempt {call_count}")

        with pytest.raises(ValueError, match="Attempt 2"):
            always_fail()

        assert call_count == 2


# =============================================================================
# resilience.py — with_timeout decorator (lines 372-402)
# =============================================================================


class TestWithTimeout:
    """Tests covering the with_timeout decorator."""

    def test_timeout_function_completes_in_time(self):
        """Lines 372-390: Function completes before timeout."""
        @with_timeout(5.0)
        def fast_function():
            return "done"

        result = fast_function()
        assert result == "done"

    def test_timeout_function_exceeds_timeout(self):
        """Lines 381-382: Function exceeds timeout and raises TimeoutError."""
        @with_timeout(0.1)
        def slow_function():
            time.sleep(2.0)
            return "should not reach"

        with pytest.raises(TimeoutError, match="timed out"):
            slow_function()

    def test_timeout_restores_old_handler(self):
        """Lines 384, 390-391: Old SIGALRM handler is restored after function."""
        original_handler = signal.getsignal(signal.SIGALRM)

        @with_timeout(5.0)
        def normal_function():
            return "ok"

        normal_function()

        restored_handler = signal.getsignal(signal.SIGALRM)
        assert restored_handler == original_handler

    def test_timeout_fallback_in_non_main_thread(self):
        """Lines 393-398: Falls through to no-timeout execution in non-main thread."""
        result_container = [None]

        @with_timeout(0.001)
        def function_in_thread():
            # In a non-main thread, signal.signal raises ValueError
            # so it should fall through to the no-timeout path
            time.sleep(0.01)
            return "completed"

        def run_in_thread():
            result_container[0] = function_in_thread()

        thread = Thread(target=run_in_thread)
        thread.start()
        thread.join(timeout=5.0)

        assert result_container[0] == "completed"


# =============================================================================
# secrets.py — _derive_address success path (lines 193-196)
# =============================================================================


class TestBlockchainSecretsDeriveAddress:
    """Tests covering _derive_address success and exception paths."""

    def test_derive_address_success_with_prefix(self):
        """Lines 193-196: Successfully derives address with 0x prefix."""
        from apps.blockchain.secrets import BlockchainSecretsManager

        mgr = BlockchainSecretsManager()

        mock_account_cls = MagicMock()
        mock_account = MagicMock()
        mock_account.address = "0xDerivedAddress"
        mock_account_cls.from_key.return_value = mock_account

        mock_module = MagicMock()
        mock_module.Account = mock_account_cls

        with patch.dict(sys.modules, {"eth_account": mock_module}):
            result = mgr._derive_address("0xprivatekey123")

        assert result == "0xDerivedAddress"
        mock_account_cls.from_key.assert_called_once_with("0xprivatekey123")

    def test_derive_address_success_without_prefix(self):
        """Line 194: Auto-prefixes key without 0x."""
        from apps.blockchain.secrets import BlockchainSecretsManager

        mgr = BlockchainSecretsManager()

        mock_account_cls = MagicMock()
        mock_account = MagicMock()
        mock_account.address = "0xDerivedNoPrefix"
        mock_account_cls.from_key.return_value = mock_account

        mock_module = MagicMock()
        mock_module.Account = mock_account_cls

        with patch.dict(sys.modules, {"eth_account": mock_module}):
            result = mgr._derive_address("privatekey_no_prefix")

        assert result == "0xDerivedNoPrefix"
        mock_account_cls.from_key.assert_called_once_with("0xprivatekey_no_prefix")

    def test_derive_address_generic_exception(self):
        """Lines 200-202: Returns empty string on generic exception."""
        from apps.blockchain.secrets import BlockchainSecretsManager

        mgr = BlockchainSecretsManager()

        mock_account_cls = MagicMock()
        mock_account_cls.from_key.side_effect = RuntimeError("bad key format")

        mock_module = MagicMock()
        mock_module.Account = mock_account_cls

        with patch.dict(sys.modules, {"eth_account": mock_module}):
            result = mgr._derive_address("0xbadkey")

        assert result == ""


# =============================================================================
# secrets.py — get_verifier (line 153), derive address for env wallet (line 135)
# =============================================================================


class TestBlockchainSecretsAdditional:
    """Tests for remaining uncovered secrets.py lines."""

    def test_get_verifier_wallet(self):
        """Line 153: get_verifier convenience method."""
        from apps.blockchain.secrets import BlockchainSecretsManager

        mgr = BlockchainSecretsManager()
        with patch.object(mgr, "get_wallet", return_value=_make_wallet()) as mock_get:
            wallet = mgr.get_verifier()
            assert wallet is not None
            mock_get.assert_called_once_with("verifier")

    def test_get_wallet_derives_address_from_env_key(self):
        """Line 135: When env provides key but no address, derives address."""
        import os
        from apps.blockchain.secrets import BlockchainSecretsManager

        mgr = BlockchainSecretsManager()

        with patch.object(mgr, "_get_secret", return_value=None):
            with patch.dict(os.environ, {
                "DEPLOYER_PRIVATE_KEY": "0xenvkey123",
                # No DEPLOYER_ADDRESS
            }, clear=True):
                with patch.object(mgr, "_derive_address", return_value="0xDerivedFromEnv"):
                    wallet = mgr.get_wallet("deployer")

        assert wallet is not None
        assert wallet.address == "0xDerivedFromEnv"
        assert wallet.private_key == "0xenvkey123"


# =============================================================================
# Extra edge cases for full coverage
# =============================================================================


class TestBuildTransactionEdgeCases:
    """Extra edge cases for _build_transaction."""

    def test_build_transaction_no_base_fee(self):
        """Line 195: Falls back to gas_price when baseFeePerGas missing."""
        svc, mock_web3 = _make_service_with_web3()
        mock_web3.eth.get_block.return_value = {}  # No baseFeePerGas
        mock_web3.eth.gas_price = 5000

        wallet = _make_wallet()
        tx = svc._build_transaction(wallet, "0xContract", b"\x00")

        assert "maxFeePerGas" in tx
        assert "maxPriorityFeePerGas" in tx


class TestCircuitBreakerContextManager:
    """Additional context manager coverage."""

    def test_context_manager_records_failure_on_exception(self):
        """Lines 204-210: __exit__ records failure when exception occurs."""
        circuit = CircuitBreaker("test_ctx_failure_unique", failure_threshold=5)
        circuit.reset()

        try:
            with circuit:
                raise ValueError("boom")
        except ValueError:
            pass

        assert circuit._state.failure_count == 1

        circuit.reset()
        with CircuitBreaker._lock:
            CircuitBreaker._instances.pop("test_ctx_failure_unique", None)


class TestCircuitBreakerCall:
    """Tests for CircuitBreaker.call() method."""

    def test_call_success(self):
        """Lines 217-220: call executes function and records success."""
        circuit = CircuitBreaker("test_call_success_unique", failure_threshold=5)
        circuit.reset()

        result = circuit.call(lambda: "ok")
        assert result == "ok"

        circuit.reset()
        with CircuitBreaker._lock:
            CircuitBreaker._instances.pop("test_call_success_unique", None)

    def test_call_failure(self):
        """Lines 221-223: call records failure and re-raises."""
        circuit = CircuitBreaker("test_call_failure_unique", failure_threshold=5)
        circuit.reset()

        with pytest.raises(RuntimeError):
            circuit.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))

        circuit.reset()
        with CircuitBreaker._lock:
            CircuitBreaker._instances.pop("test_call_failure_unique", None)

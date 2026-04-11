"""
Tests for blockchain services and views.

Targets coverage gaps in:
- apps/blockchain/services.py (30% -> ~75%)
- apps/blockchain/views.py (27% -> ~75%)
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APIClient

from apps.blockchain.resilience import CircuitState
from apps.blockchain.secrets import BlockchainWallet, ContractAddresses
from apps.blockchain.services import (
    BlockchainService,
    ComputationVerifierService,
    ConsortiumService,
    ModelRegistryService,
    TransactionResult,
)


# ---------------------------------------------------------------------------
# TransactionResult Tests
# ---------------------------------------------------------------------------


class TestTransactionResult:
    def test_successful_result(self):
        r = TransactionResult(success=True, tx_hash="0xabc", block_number=100, gas_used=21000)
        assert bool(r) is True
        assert r.tx_hash == "0xabc"

    def test_failed_result(self):
        r = TransactionResult(success=False, error="reverted")
        assert bool(r) is False
        assert r.error == "reverted"

    def test_default_fields(self):
        r = TransactionResult(success=True)
        assert r.tx_hash is None
        assert r.block_number is None
        assert r.gas_used is None
        assert r.error is None


# ---------------------------------------------------------------------------
# BlockchainService Tests
# ---------------------------------------------------------------------------


class TestBlockchainServiceInit:
    def test_default_network(self):
        svc = BlockchainService()
        assert svc.network == "arbitrum_sepolia"
        assert svc._web3 is None

    def test_custom_network(self):
        svc = BlockchainService(network="arbitrum")
        assert svc.network == "arbitrum"

    def test_is_connected_no_web3(self):
        svc = BlockchainService()
        svc._web3 = None
        assert svc.is_connected() is False

    def test_is_connected_circuit_open(self):
        svc = BlockchainService()
        # Directly set the circuit breaker to open state
        svc._circuit._state.state = CircuitState.OPEN
        svc._circuit._state.last_failure_time = datetime.now(UTC)
        try:
            assert svc.is_connected() is False
        finally:
            svc._circuit.reset()

    def test_is_connected_with_mock_web3(self):
        svc = BlockchainService()
        mock_web3 = MagicMock()
        mock_web3.is_connected.return_value = True
        svc._web3 = mock_web3
        svc._circuit.reset()
        assert svc.is_connected() is True

    def test_is_connected_exception(self):
        svc = BlockchainService()
        mock_web3 = MagicMock()
        mock_web3.is_connected.side_effect = Exception("fail")
        svc._web3 = mock_web3
        assert svc.is_connected() is False

    def test_get_circuit_status(self):
        svc = BlockchainService()
        stats = svc.get_circuit_status()
        assert "name" in stats
        assert "state" in stats
        assert "config" in stats


class TestBlockchainServiceConnect:
    def test_connect_no_web3_package(self):
        svc = BlockchainService()
        with patch.dict("sys.modules", {"web3": None}):
            with pytest.raises(ImportError):
                svc._connect()

    def test_chain_id_triggers_connect(self):
        svc = BlockchainService()
        svc._chain_id = None
        with patch.object(svc, "_connect") as mock_connect:
            svc._web3 = MagicMock()
            svc._chain_id = 421614
            assert svc.chain_id == 421614


class TestBlockchainServiceLoadABI:
    def test_load_missing_abi(self):
        svc = BlockchainService()
        with pytest.raises(FileNotFoundError):
            svc._load_contract_abi("NonExistentContract")

    def test_estimate_gas(self):
        svc = BlockchainService()
        mock_web3 = MagicMock()
        mock_web3.eth.estimate_gas.return_value = 21000
        svc._web3 = mock_web3
        estimated = svc._estimate_gas({"from": "0x123"})
        assert estimated == 25200  # 21000 * 1.2

    def test_get_balance(self):
        svc = BlockchainService()
        mock_web3 = MagicMock()
        mock_web3.eth.get_balance.return_value = 1000000
        mock_web3.to_checksum_address.return_value = "0xChecksum"
        svc._web3 = mock_web3
        balance = svc.get_balance("0xaddr")
        assert balance == 1000000

    def test_get_balance_eth(self):
        svc = BlockchainService()
        mock_web3 = MagicMock()
        mock_web3.eth.get_balance.return_value = 10**18
        mock_web3.to_checksum_address.return_value = "0xChecksum"
        mock_web3.from_wei.return_value = 1.0
        svc._web3 = mock_web3
        balance_eth = svc.get_balance_eth("0xaddr")
        assert balance_eth == 1.0


class TestBlockchainServiceBuildTransaction:
    def test_build_transaction(self):
        svc = BlockchainService()
        mock_web3 = MagicMock()
        mock_web3.eth.get_transaction_count.return_value = 5
        mock_web3.eth.estimate_gas.return_value = 21000
        mock_web3.eth.get_block.return_value = {"baseFeePerGas": 1000}
        mock_web3.to_checksum_address.return_value = "0xChecksumAddr"
        mock_web3.to_wei.return_value = 100000
        svc._web3 = mock_web3
        svc._chain_id = 421614

        wallet = BlockchainWallet(address="0x123", private_key="0xkey", name="test")
        tx = svc._build_transaction(wallet, "0xContract", b"\x00")
        assert tx["from"] == "0x123"
        assert tx["nonce"] == 5
        assert tx["chainId"] == 421614
        assert "gas" in tx
        assert "maxFeePerGas" in tx


class TestBlockchainServiceSignAndSend:
    def test_sign_and_send_circuit_open(self):
        svc = BlockchainService()
        svc._circuit._state.state = CircuitState.OPEN
        svc._circuit._state.last_failure_time = datetime.now(UTC)
        try:
            wallet = BlockchainWallet(address="0x1", private_key="0xkey", name="t")
            result = svc._sign_and_send_with_retry(wallet, {})
            assert not result.success
            assert "Circuit breaker" in result.error
        finally:
            svc._circuit.reset()

    def test_sign_and_send_generic_exception(self):
        svc = BlockchainService()
        svc._circuit.reset()
        mock_web3 = MagicMock()
        svc._web3 = mock_web3

        with patch.dict("sys.modules", {"eth_account": MagicMock()}):
            with patch("eth_account.Account.sign_transaction", side_effect=ValueError("bad tx")):
                wallet = BlockchainWallet(address="0x1", private_key="0xkey", name="t")
                result = svc._sign_and_send_with_retry(wallet, {})
        assert not result.success


# ---------------------------------------------------------------------------
# ConsortiumService Tests
# ---------------------------------------------------------------------------


class TestConsortiumServiceNoWallet:
    def test_create_consortium_no_wallet(self):
        with patch("apps.blockchain.services.get_consortium_signer_wallet", return_value=None):
            svc = ConsortiumService("0xContract")
            result = svc.create_consortium("Test", 50, 3600, b"\x00" * 32)
        assert not result.success
        assert result.error == "No wallet configured"

    def test_add_member_no_wallet(self):
        with patch("apps.blockchain.services.get_consortium_signer_wallet", return_value=None):
            svc = ConsortiumService("0xContract")
            result = svc.add_member(b"\x01" * 32, "0xMember")
        assert not result.success

    def test_record_contribution_no_wallet(self):
        with patch("apps.blockchain.services.get_consortium_signer_wallet", return_value=None):
            svc = ConsortiumService("0xContract")
            result = svc.record_contribution(b"\x01" * 32, 100, 10, b"\x02" * 32, b"\x03" * 32)
        assert not result.success


# ---------------------------------------------------------------------------
# ModelRegistryService Tests
# ---------------------------------------------------------------------------


class TestModelRegistryServiceNoWallet:
    def test_register_model_no_wallet(self):
        with patch("apps.blockchain.services.get_consortium_signer_wallet", return_value=None):
            svc = ModelRegistryService("0xContract")
            result = svc.register_model("linear_regression", "1.0")
        assert not result.success

    def test_save_checkpoint_no_wallet(self):
        with patch("apps.blockchain.services.get_consortium_signer_wallet", return_value=None):
            svc = ModelRegistryService("0xContract")
            result = svc.save_checkpoint(b"\x01" * 32, 5, b"\x02" * 32, b"\x03" * 32)
        assert not result.success


# ---------------------------------------------------------------------------
# ComputationVerifierService Tests
# ---------------------------------------------------------------------------


class TestComputationVerifierServiceNoWallet:
    def test_register_computation_no_wallet(self):
        with patch("apps.blockchain.services.get_consortium_signer_wallet", return_value=None):
            svc = ComputationVerifierService("0xContract")
            result = svc.register_computation(b"\x01" * 32, b"\x02" * 32, b"\x03" * 32)
        assert not result.success

    def test_register_batch_no_wallet(self):
        with patch("apps.blockchain.services.get_consortium_signer_wallet", return_value=None):
            svc = ComputationVerifierService("0xContract")
            result = svc.register_batch(b"\x01" * 32, [b"\x02" * 32], [b"\x03" * 32])
        assert not result.success


# ---------------------------------------------------------------------------
# Blockchain Views Tests
# ---------------------------------------------------------------------------


def _mock_contract_addresses(
    governance="0xGov", model_registry="0xModel", computation_verifier="0xComp"
):
    return ContractAddresses(
        governance=governance,
        model_registry=model_registry,
        computation_verifier=computation_verifier,
        network="arbitrum_sepolia",
    )


@pytest.mark.django_db
class TestBlockchainStatusView:
    def test_status_unauthenticated(self, api_client):
        response = api_client.get("/api/v2/blockchain/status/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_status_authenticated(self, auth_client):
        with patch("apps.blockchain.views.BlockchainService") as MockSvc:
            mock_svc = MockSvc.return_value
            mock_svc.is_connected.return_value = False
            mock_svc.get_circuit_status.return_value = {
                "name": "test",
                "state": "closed",
                "failure_count": 0,
                "success_count": 0,
                "last_failure": None,
                "last_success": None,
                "config": {},
            }
            response = auth_client.get("/api/v2/blockchain/status/")
        assert response.status_code == status.HTTP_200_OK
        assert "connected" in response.data

    def test_status_connection_exception(self, auth_client):
        with patch("apps.blockchain.views.BlockchainService") as MockSvc:
            mock_svc = MockSvc.return_value
            mock_svc.is_connected.side_effect = Exception("Connection failed")
            mock_svc.get_circuit_status.return_value = {
                "name": "test",
                "state": "open",
                "failure_count": 5,
                "success_count": 0,
                "last_failure": None,
                "last_success": None,
                "config": {},
            }
            response = auth_client.get("/api/v2/blockchain/status/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["connected"] is False


@pytest.mark.django_db
class TestContractAddressesView:
    def test_get_contracts(self, auth_client):
        with patch("apps.blockchain.views.get_contract_addresses") as mock_get:
            mock_get.return_value = _mock_contract_addresses()
            response = auth_client.get("/api/v2/blockchain/contract-addresses/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["governance"] == "0xGov"

    def test_get_contracts_unauthenticated(self, api_client):
        response = api_client.get("/api/v2/blockchain/contract-addresses/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestConsortiumCreateView:
    def test_create_no_governance_contract(self, auth_client):
        with patch("apps.blockchain.views.get_contract_addresses") as mock_get:
            mock_get.return_value = _mock_contract_addresses(governance=None)
            response = auth_client.post(
                "/api/v2/blockchain/consortium/create/",
                {
                    "name": "Test",
                    "min_voting_quorum": 50,
                    "voting_duration": 3600,
                    "model_config_hash": "0x" + "a" * 64,
                },
                format="json",
            )
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_create_success(self, auth_client):
        with patch("apps.blockchain.views.get_contract_addresses") as mock_get:
            mock_get.return_value = _mock_contract_addresses()
            with patch("apps.blockchain.views.ConsortiumService") as MockSvc:
                mock_svc = MockSvc.return_value
                mock_svc.create_consortium.return_value = TransactionResult(
                    success=True, tx_hash="0x" + "f" * 64, block_number=100, gas_used=50000
                )
                response = auth_client.post(
                    "/api/v2/blockchain/consortium/create/",
                    {
                        "name": "Test Consortium",
                        "min_voting_quorum": 50,
                        "voting_duration": 3600,
                        "model_config_hash": "0x" + "a" * 64,
                    },
                    format="json",
                )
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_failure(self, auth_client):
        with patch("apps.blockchain.views.get_contract_addresses") as mock_get:
            mock_get.return_value = _mock_contract_addresses()
            with patch("apps.blockchain.views.ConsortiumService") as MockSvc:
                mock_svc = MockSvc.return_value
                mock_svc.create_consortium.return_value = TransactionResult(
                    success=False, error="No wallet"
                )
                response = auth_client.post(
                    "/api/v2/blockchain/consortium/create/",
                    {
                        "name": "Test",
                        "min_voting_quorum": 50,
                        "voting_duration": 3600,
                        "model_config_hash": "0x" + "a" * 64,
                    },
                    format="json",
                )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestConsortiumDetailView:
    def test_get_detail_no_governance(self, auth_client):
        with patch("apps.blockchain.views.get_contract_addresses") as mock_get:
            mock_get.return_value = _mock_contract_addresses(governance=None)
            response = auth_client.get(
                "/api/v2/blockchain/consortium/" + "a" * 64 + "/"
            )
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_get_detail_success(self, auth_client):
        with patch("apps.blockchain.views.get_contract_addresses") as mock_get:
            mock_get.return_value = _mock_contract_addresses()
            with patch("apps.blockchain.views.ConsortiumService") as MockSvc:
                mock_svc = MockSvc.return_value
                mock_svc.get_consortium.return_value = {
                    "name": "Test",
                    "owner": "0x123",
                    "status": 1,
                    "member_count": 5,
                    "total_contributions": 100,
                    "min_voting_quorum": 50,
                    "voting_duration": 3600,
                }
                response = auth_client.get(
                    "/api/v2/blockchain/consortium/" + "a" * 64 + "/"
                )
        assert response.status_code == status.HTTP_200_OK

    def test_get_detail_exception(self, auth_client):
        with patch("apps.blockchain.views.get_contract_addresses") as mock_get:
            mock_get.return_value = _mock_contract_addresses()
            with patch("apps.blockchain.views.ConsortiumService") as MockSvc:
                mock_svc = MockSvc.return_value
                mock_svc.get_consortium.side_effect = Exception("Not found")
                response = auth_client.get(
                    "/api/v2/blockchain/consortium/" + "a" * 64 + "/"
                )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestConsortiumAddMemberView:
    def test_add_member_no_governance(self, auth_client):
        with patch("apps.blockchain.views.get_contract_addresses") as mock_get:
            mock_get.return_value = _mock_contract_addresses(governance=None)
            response = auth_client.post(
                "/api/v2/blockchain/consortium/add-member/",
                {"consortium_id": "0x" + "a" * 64, "member_address": "0x" + "b" * 40},
                format="json",
            )
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_add_member_success(self, auth_client):
        with patch("apps.blockchain.views.get_contract_addresses") as mock_get:
            mock_get.return_value = _mock_contract_addresses()
            with patch("apps.blockchain.views.ConsortiumService") as MockSvc:
                mock_svc = MockSvc.return_value
                mock_svc.add_member.return_value = TransactionResult(
                    success=True, tx_hash="0x" + "c" * 64
                )
                response = auth_client.post(
                    "/api/v2/blockchain/consortium/add-member/",
                    {
                        "consortium_id": "0x" + "a" * 64,
                        "member_address": "0x" + "b" * 40,
                    },
                    format="json",
                )
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestModelRegisterView:
    def test_register_no_contract(self, auth_client):
        with patch("apps.blockchain.views.get_contract_addresses") as mock_get:
            mock_get.return_value = _mock_contract_addresses(model_registry=None)
            response = auth_client.post(
                "/api/v2/blockchain/model/register/",
                {"model_type": "linear_regression", "version": "1.0"},
                format="json",
            )
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_register_success(self, auth_client):
        with patch("apps.blockchain.views.get_contract_addresses") as mock_get:
            mock_get.return_value = _mock_contract_addresses()
            with patch("apps.blockchain.views.ModelRegistryService") as MockSvc:
                mock_svc = MockSvc.return_value
                mock_svc.register_model.return_value = TransactionResult(
                    success=True, tx_hash="0x" + "d" * 64
                )
                response = auth_client.post(
                    "/api/v2/blockchain/model/register/",
                    {"model_type": "linear_regression", "version": "1.0"},
                    format="json",
                )
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
class TestModelDetailView:
    def test_get_model_no_contract(self, auth_client):
        with patch("apps.blockchain.views.get_contract_addresses") as mock_get:
            mock_get.return_value = _mock_contract_addresses(model_registry=None)
            response = auth_client.get(
                "/api/v2/blockchain/model/" + "a" * 64 + "/"
            )
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_get_model_success(self, auth_client):
        with patch("apps.blockchain.views.get_contract_addresses") as mock_get:
            mock_get.return_value = _mock_contract_addresses()
            with patch("apps.blockchain.views.ModelRegistryService") as MockSvc:
                mock_svc = MockSvc.return_value
                mock_svc.get_model.return_value = {
                    "owner": "0x123",
                    "model_type": "linear_regression",
                    "version": "1.0",
                    "weights_hash": "a" * 64,
                    "created_at": 1000,
                    "updated_at": 2000,
                    "verified": True,
                    "active": True,
                }
                response = auth_client.get(
                    "/api/v2/blockchain/model/" + "a" * 64 + "/"
                )
        assert response.status_code == status.HTTP_200_OK

    def test_get_model_exception(self, auth_client):
        with patch("apps.blockchain.views.get_contract_addresses") as mock_get:
            mock_get.return_value = _mock_contract_addresses()
            with patch("apps.blockchain.views.ModelRegistryService") as MockSvc:
                mock_svc = MockSvc.return_value
                mock_svc.get_model.side_effect = Exception("fail")
                response = auth_client.get(
                    "/api/v2/blockchain/model/" + "a" * 64 + "/"
                )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestCheckpointViews:
    def test_save_checkpoint_no_contract(self, auth_client):
        with patch("apps.blockchain.views.get_contract_addresses") as mock_get:
            mock_get.return_value = _mock_contract_addresses(model_registry=None)
            response = auth_client.post(
                "/api/v2/blockchain/model/checkpoint/",
                {
                    "model_id": "0x" + "a" * 64,
                    "epoch": 5,
                    "weights_hash": "0x" + "b" * 64,
                    "metrics_hash": "0x" + "c" * 64,
                },
                format="json",
            )
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_save_checkpoint_success(self, auth_client):
        with patch("apps.blockchain.views.get_contract_addresses") as mock_get:
            mock_get.return_value = _mock_contract_addresses()
            with patch("apps.blockchain.views.ModelRegistryService") as MockSvc:
                mock_svc = MockSvc.return_value
                mock_svc.save_checkpoint.return_value = TransactionResult(
                    success=True, tx_hash="0x" + "e" * 64
                )
                response = auth_client.post(
                    "/api/v2/blockchain/model/checkpoint/",
                    {
                        "model_id": "0x" + "a" * 64,
                        "epoch": 5,
                        "weights_hash": "0x" + "b" * 64,
                        "metrics_hash": "0x" + "c" * 64,
                    },
                    format="json",
                )
        assert response.status_code == status.HTTP_201_CREATED

    def test_verify_checkpoint_no_contract(self, auth_client):
        with patch("apps.blockchain.views.get_contract_addresses") as mock_get:
            mock_get.return_value = _mock_contract_addresses(model_registry=None)
            response = auth_client.post(
                "/api/v2/blockchain/model/checkpoint/verify/",
                {
                    "model_id": "0x" + "a" * 64,
                    "epoch": 5,
                    "weights_hash": "0x" + "b" * 64,
                },
                format="json",
            )
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_verify_checkpoint_success(self, auth_client):
        with patch("apps.blockchain.views.get_contract_addresses") as mock_get:
            mock_get.return_value = _mock_contract_addresses()
            with patch("apps.blockchain.views.ModelRegistryService") as MockSvc:
                mock_svc = MockSvc.return_value
                mock_svc.verify_checkpoint.return_value = True
                response = auth_client.post(
                    "/api/v2/blockchain/model/checkpoint/verify/",
                    {
                        "model_id": "0x" + "a" * 64,
                        "epoch": 5,
                        "weights_hash": "0x" + "b" * 64,
                    },
                    format="json",
                )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["valid"] is True

    def test_verify_checkpoint_exception(self, auth_client):
        with patch("apps.blockchain.views.get_contract_addresses") as mock_get:
            mock_get.return_value = _mock_contract_addresses()
            with patch("apps.blockchain.views.ModelRegistryService") as MockSvc:
                mock_svc = MockSvc.return_value
                mock_svc.verify_checkpoint.side_effect = Exception("fail")
                response = auth_client.post(
                    "/api/v2/blockchain/model/checkpoint/verify/",
                    {
                        "model_id": "0x" + "a" * 64,
                        "epoch": 5,
                        "weights_hash": "0x" + "b" * 64,
                    },
                    format="json",
                )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestComputationViews:
    def test_register_computation_no_contract(self, auth_client):
        with patch("apps.blockchain.views.get_contract_addresses") as mock_get:
            mock_get.return_value = _mock_contract_addresses(computation_verifier=None)
            response = auth_client.post(
                "/api/v2/blockchain/computation/register/",
                {
                    "model_id": "0x" + "a" * 64,
                    "input_hash": "0x" + "b" * 64,
                    "output_hash": "0x" + "c" * 64,
                },
                format="json",
            )
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_register_computation_success(self, auth_client):
        with patch("apps.blockchain.views.get_contract_addresses") as mock_get:
            mock_get.return_value = _mock_contract_addresses()
            with patch("apps.blockchain.views.ComputationVerifierService") as MockSvc:
                mock_svc = MockSvc.return_value
                mock_svc.register_computation.return_value = TransactionResult(
                    success=True, tx_hash="0x" + "d" * 64
                )
                response = auth_client.post(
                    "/api/v2/blockchain/computation/register/",
                    {
                        "model_id": "0x" + "a" * 64,
                        "input_hash": "0x" + "b" * 64,
                        "output_hash": "0x" + "c" * 64,
                    },
                    format="json",
                )
        assert response.status_code == status.HTTP_201_CREATED

    def test_register_computation_with_proof_hash(self, auth_client):
        with patch("apps.blockchain.views.get_contract_addresses") as mock_get:
            mock_get.return_value = _mock_contract_addresses()
            with patch("apps.blockchain.views.ComputationVerifierService") as MockSvc:
                mock_svc = MockSvc.return_value
                mock_svc.register_computation.return_value = TransactionResult(
                    success=True, tx_hash="0x" + "d" * 64
                )
                response = auth_client.post(
                    "/api/v2/blockchain/computation/register/",
                    {
                        "model_id": "0x" + "a" * 64,
                        "input_hash": "0x" + "b" * 64,
                        "output_hash": "0x" + "c" * 64,
                        "proof_hash": "0x" + "e" * 64,
                    },
                    format="json",
                )
        assert response.status_code == status.HTTP_201_CREATED

    def test_register_batch_no_contract(self, auth_client):
        with patch("apps.blockchain.views.get_contract_addresses") as mock_get:
            mock_get.return_value = _mock_contract_addresses(computation_verifier=None)
            response = auth_client.post(
                "/api/v2/blockchain/computation/batch/",
                {
                    "model_id": "0x" + "a" * 64,
                    "input_hashes": ["0x" + "b" * 64],
                    "output_hashes": ["0x" + "c" * 64],
                },
                format="json",
            )
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_register_batch_success(self, auth_client):
        with patch("apps.blockchain.views.get_contract_addresses") as mock_get:
            mock_get.return_value = _mock_contract_addresses()
            with patch("apps.blockchain.views.ComputationVerifierService") as MockSvc:
                mock_svc = MockSvc.return_value
                mock_svc.register_batch.return_value = TransactionResult(
                    success=True, tx_hash="0x" + "d" * 64
                )
                response = auth_client.post(
                    "/api/v2/blockchain/computation/batch/",
                    {
                        "model_id": "0x" + "a" * 64,
                        "input_hashes": ["0x" + "b" * 64],
                        "output_hashes": ["0x" + "c" * 64],
                    },
                    format="json",
                )
        assert response.status_code == status.HTTP_201_CREATED

    def test_verify_output_no_contract(self, auth_client):
        with patch("apps.blockchain.views.get_contract_addresses") as mock_get:
            mock_get.return_value = _mock_contract_addresses(computation_verifier=None)
            response = auth_client.post(
                "/api/v2/blockchain/computation/verify/",
                {
                    "model_id": "0x" + "a" * 64,
                    "input_hash": "0x" + "b" * 64,
                    "output_hash": "0x" + "c" * 64,
                },
                format="json",
            )
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_verify_output_success(self, auth_client):
        with patch("apps.blockchain.views.get_contract_addresses") as mock_get:
            mock_get.return_value = _mock_contract_addresses()
            with patch("apps.blockchain.views.ComputationVerifierService") as MockSvc:
                mock_svc = MockSvc.return_value
                mock_svc.verify_output.return_value = (True, b"\x01" * 32)
                response = auth_client.post(
                    "/api/v2/blockchain/computation/verify/",
                    {
                        "model_id": "0x" + "a" * 64,
                        "input_hash": "0x" + "b" * 64,
                        "output_hash": "0x" + "c" * 64,
                    },
                    format="json",
                )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["valid"] is True

    def test_verify_output_exception(self, auth_client):
        with patch("apps.blockchain.views.get_contract_addresses") as mock_get:
            mock_get.return_value = _mock_contract_addresses()
            with patch("apps.blockchain.views.ComputationVerifierService") as MockSvc:
                mock_svc = MockSvc.return_value
                mock_svc.verify_output.side_effect = Exception("fail")
                response = auth_client.post(
                    "/api/v2/blockchain/computation/verify/",
                    {
                        "model_id": "0x" + "a" * 64,
                        "input_hash": "0x" + "b" * 64,
                        "output_hash": "0x" + "c" * 64,
                    },
                    format="json",
                )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestWalletBalanceView:
    def test_get_balance_unauthenticated(self, api_client):
        response = api_client.get("/api/v2/blockchain/balance/0x123/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_balance_success(self, auth_client):
        with patch("apps.blockchain.views.BlockchainService") as MockSvc:
            mock_svc = MockSvc.return_value
            mock_svc.get_balance.return_value = 1000000
            mock_svc.get_balance_eth.return_value = 0.001
            response = auth_client.get("/api/v2/blockchain/balance/0x" + "a" * 40 + "/")
        assert response.status_code == status.HTTP_200_OK

    def test_get_balance_exception(self, auth_client):
        with patch("apps.blockchain.views.BlockchainService") as MockSvc:
            mock_svc = MockSvc.return_value
            mock_svc.get_balance.side_effect = Exception("RPC down")
            response = auth_client.get("/api/v2/blockchain/balance/0x" + "a" * 40 + "/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestConsortiumMemberView:
    def test_get_member_no_governance(self, auth_client):
        with patch("apps.blockchain.views.get_contract_addresses") as mock_get:
            mock_get.return_value = _mock_contract_addresses(governance=None)
            response = auth_client.get(
                "/api/v2/blockchain/consortium/" + "a" * 64 + "/member/0x" + "b" * 40 + "/"
            )
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_get_member_success(self, auth_client):
        with patch("apps.blockchain.views.get_contract_addresses") as mock_get:
            mock_get.return_value = _mock_contract_addresses()
            with patch("apps.blockchain.views.ConsortiumService") as MockSvc:
                mock_svc = MockSvc.return_value
                mock_svc.get_member.return_value = {
                    "status": 1,
                    "joined_at": 1000,
                    "contribution_count": 5,
                    "contribution_weight": 100,
                    "last_contribution_at": 2000,
                }
                response = auth_client.get(
                    "/api/v2/blockchain/consortium/" + "a" * 64 + "/member/0x" + "b" * 40 + "/"
                )
        assert response.status_code == status.HTTP_200_OK

    def test_get_member_exception(self, auth_client):
        with patch("apps.blockchain.views.get_contract_addresses") as mock_get:
            mock_get.return_value = _mock_contract_addresses()
            with patch("apps.blockchain.views.ConsortiumService") as MockSvc:
                mock_svc = MockSvc.return_value
                mock_svc.get_member.side_effect = Exception("fail")
                response = auth_client.get(
                    "/api/v2/blockchain/consortium/" + "a" * 64 + "/member/0x" + "b" * 40 + "/"
                )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestContributionRecordView:
    def test_record_no_governance(self, auth_client):
        with patch("apps.blockchain.views.get_contract_addresses") as mock_get:
            mock_get.return_value = _mock_contract_addresses(governance=None)
            response = auth_client.post(
                "/api/v2/blockchain/consortium/contribution/",
                {
                    "consortium_id": "0x" + "a" * 64,
                    "record_count": 100,
                    "feature_count": 10,
                    "data_hash": "0x" + "b" * 64,
                    "checksum_hash": "0x" + "c" * 64,
                },
                format="json",
            )
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_record_success(self, auth_client):
        with patch("apps.blockchain.views.get_contract_addresses") as mock_get:
            mock_get.return_value = _mock_contract_addresses()
            with patch("apps.blockchain.views.ConsortiumService") as MockSvc:
                mock_svc = MockSvc.return_value
                mock_svc.record_contribution.return_value = TransactionResult(
                    success=True, tx_hash="0x" + "d" * 64
                )
                response = auth_client.post(
                    "/api/v2/blockchain/consortium/contribution/",
                    {
                        "consortium_id": "0x" + "a" * 64,
                        "record_count": 100,
                        "feature_count": 10,
                        "data_hash": "0x" + "b" * 64,
                        "checksum_hash": "0x" + "c" * 64,
                    },
                    format="json",
                )
        assert response.status_code == status.HTTP_201_CREATED


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------


class TestHexToBytes:
    def test_with_0x_prefix(self):
        from apps.blockchain.views import _hex_to_bytes

        result = _hex_to_bytes("0xabcd")
        assert result == bytes.fromhex("abcd")

    def test_without_prefix(self):
        from apps.blockchain.views import _hex_to_bytes

        result = _hex_to_bytes("abcd")
        assert result == bytes.fromhex("abcd")

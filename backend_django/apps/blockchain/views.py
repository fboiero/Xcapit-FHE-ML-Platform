"""
Views para la app de Blockchain.

ViewSets para gestionar transacciones y contratos inteligentes desplegados,
junto con las APIViews existentes para operaciones on-chain.
"""

from __future__ import annotations

import logging
from typing import Optional

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsCompanyMember

from .models import SmartContractDeployment, Transaction
from .secrets import blockchain_secrets, get_contract_addresses
from .serializers import (
    AddMemberSerializer,
    BatchComputationSerializer,
    BlockchainStatusSerializer,
    CheckpointSerializer,
    ComputationSerializer,
    ConsortiumCreateSerializer,
    ConsortiumIdSerializer,
    ConsortiumResponseSerializer,
    ContributionSerializer,
    MemberResponseSerializer,
    ModelRegisterSerializer,
    ModelResponseSerializer,
    TransactionResultSerializer,
    VerifyCheckpointSerializer,
    VerifyOutputResponseSerializer,
    VerifyOutputSerializer,
    WalletBalanceSerializer,
)
from .services import (
    BlockchainService,
    ComputationVerifierService,
    ConsortiumService,
    ModelRegistryService,
)

logger = logging.getLogger(__name__)


def _hex_to_bytes(hex_str: str) -> bytes:
    """Convert hex string to bytes."""
    if hex_str.startswith("0x"):
        hex_str = hex_str[2:]
    return bytes.fromhex(hex_str)


# =============================================================================
# Model-backed ViewSets (Transaction / SmartContractDeployment)
# =============================================================================

from rest_framework import serializers as drf_serializers


class TransactionSerializer(drf_serializers.ModelSerializer):
    """Serializer for Transaction model."""

    company_name: str = drf_serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "company",
            "company_name",
            "consortium",
            "tx_hash",
            "block_number",
            "network",
            "tx_type",
            "status",
            "gas_used",
            "gas_price",
            "value_wei",
            "from_address",
            "to_address",
            "contract_address",
            "input_data",
            "error_message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class SmartContractDeploymentSerializer(drf_serializers.ModelSerializer):
    """Serializer for SmartContractDeployment model."""

    company_name: str = drf_serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = SmartContractDeployment
        fields = [
            "id",
            "company",
            "company_name",
            "consortium",
            "contract_type",
            "address",
            "network",
            "transaction",
            "abi",
            "bytecode_hash",
            "version",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para transacciones blockchain.

    - list:     transacciones de la empresa del usuario.
    - retrieve: detalle de una transaccion.
    - recent:   ultimas 20 transacciones.

    Soporta filtros por query params: network, status, tx_type.
    """

    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self):
        """Retorna transacciones filtradas por la empresa del usuario."""
        user = self.request.user
        if not user.company:
            return Transaction.objects.none()

        queryset = Transaction.objects.filter(
            company=user.company,
        ).select_related("company", "consortium")

        # Filtros opcionales
        network = self.request.query_params.get("network")
        if network:
            queryset = queryset.filter(network=network)

        tx_status = self.request.query_params.get("status")
        if tx_status:
            queryset = queryset.filter(status=tx_status)

        tx_type = self.request.query_params.get("tx_type")
        if tx_type:
            queryset = queryset.filter(tx_type=tx_type)

        return queryset

    @action(detail=False, methods=["get"])
    def recent(self, request) -> Response:
        """Retorna las ultimas 20 transacciones de la empresa."""
        queryset = self.get_queryset()[:20]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class SmartContractViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para contratos inteligentes desplegados.

    - list:     contratos de la empresa del usuario.
    - retrieve: detalle de un contrato.
    """

    serializer_class = SmartContractDeploymentSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get_queryset(self):
        """Retorna contratos filtrados por la empresa del usuario."""
        user = self.request.user
        if not user.company:
            return SmartContractDeployment.objects.none()

        return SmartContractDeployment.objects.filter(
            company=user.company,
        ).select_related("company", "consortium", "transaction")


# =============================================================================
# On-chain APIViews (existing)
# =============================================================================


class BlockchainStatusView(APIView):
    """
    Get blockchain connection status.

    GET /api/v2/blockchain/status/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get connection status and circuit breaker info."""
        network = request.query_params.get("network", "arbitrum_sepolia")
        service = BlockchainService(network=network)

        try:
            connected = service.is_connected()
            chain_id = service.chain_id if connected else None
        except Exception as e:
            logger.warning(f"Blockchain connection check failed: {e}")
            connected = False
            chain_id = None

        data = {
            "connected": connected,
            "network": network,
            "chain_id": chain_id,
            "circuit_breaker": service.get_circuit_status(),
        }

        return Response(BlockchainStatusSerializer(data).data)


class WalletBalanceView(APIView):
    """
    Get wallet balance.

    GET /api/v2/blockchain/balance/{address}/
    """

    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get(self, request, address: str):
        """Get ETH balance for an address."""
        network = request.query_params.get("network", "arbitrum_sepolia")
        service = BlockchainService(network=network)

        try:
            balance_wei = service.get_balance(address)
            balance_eth = service.get_balance_eth(address)

            data = {
                "address": address,
                "balance_wei": str(balance_wei),
                "balance_eth": balance_eth,
            }
            return Response(WalletBalanceSerializer(data).data)
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ContractAddressesView(APIView):
    """
    Get deployed contract addresses.

    GET /api/v2/blockchain/contracts/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get contract addresses for the network."""
        network = request.query_params.get("network", "arbitrum_sepolia")
        contracts = get_contract_addresses(network)

        return Response({
            "network": contracts.network,
            "governance": contracts.governance,
            "model_registry": contracts.model_registry,
            "computation_verifier": contracts.computation_verifier,
        })


# =============================================================================
# CONSORTIUM ENDPOINTS
# =============================================================================


class ConsortiumCreateView(APIView):
    """
    Create a consortium on-chain.

    POST /api/v2/blockchain/consortium/create/
    """

    permission_classes = [IsAuthenticated, IsCompanyMember]

    def post(self, request):
        """Create a new consortium."""
        serializer = ConsortiumCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        network = request.query_params.get("network", "arbitrum_sepolia")
        contracts = get_contract_addresses(network)

        if not contracts.governance:
            return Response(
                {"detail": "Governance contract not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        service = ConsortiumService(contracts.governance, network)

        result = service.create_consortium(
            name=serializer.validated_data["name"],
            min_voting_quorum=serializer.validated_data["min_voting_quorum"],
            voting_duration=serializer.validated_data["voting_duration"],
            model_config_hash=_hex_to_bytes(serializer.validated_data["model_config_hash"]),
        )

        return Response(
            TransactionResultSerializer(result.__dict__).data,
            status=status.HTTP_201_CREATED if result.success else status.HTTP_400_BAD_REQUEST,
        )


class ConsortiumDetailView(APIView):
    """
    Get consortium details from chain.

    GET /api/v2/blockchain/consortium/{consortium_id}/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, consortium_id: str):
        """Get consortium details."""
        network = request.query_params.get("network", "arbitrum_sepolia")
        contracts = get_contract_addresses(network)

        if not contracts.governance:
            return Response(
                {"detail": "Governance contract not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        service = ConsortiumService(contracts.governance, network)

        try:
            data = service.get_consortium(_hex_to_bytes(consortium_id))
            return Response(ConsortiumResponseSerializer(data).data)
        except Exception as e:
            logger.error(f"Failed to get consortium: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ConsortiumAddMemberView(APIView):
    """
    Add a member to consortium.

    POST /api/v2/blockchain/consortium/add-member/
    """

    permission_classes = [IsAuthenticated, IsCompanyMember]

    def post(self, request):
        """Add a member to a consortium."""
        serializer = AddMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        network = request.query_params.get("network", "arbitrum_sepolia")
        contracts = get_contract_addresses(network)

        if not contracts.governance:
            return Response(
                {"detail": "Governance contract not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        service = ConsortiumService(contracts.governance, network)

        result = service.add_member(
            consortium_id=_hex_to_bytes(serializer.validated_data["consortium_id"]),
            new_member=serializer.validated_data["member_address"],
        )

        return Response(
            TransactionResultSerializer(result.__dict__).data,
            status=status.HTTP_200_OK if result.success else status.HTTP_400_BAD_REQUEST,
        )


class ConsortiumMemberView(APIView):
    """
    Get member details from consortium.

    GET /api/v2/blockchain/consortium/{consortium_id}/member/{address}/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, consortium_id: str, address: str):
        """Get member details."""
        network = request.query_params.get("network", "arbitrum_sepolia")
        contracts = get_contract_addresses(network)

        if not contracts.governance:
            return Response(
                {"detail": "Governance contract not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        service = ConsortiumService(contracts.governance, network)

        try:
            data = service.get_member(_hex_to_bytes(consortium_id), address)
            return Response(MemberResponseSerializer(data).data)
        except Exception as e:
            logger.error(f"Failed to get member: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ContributionRecordView(APIView):
    """
    Record a contribution on-chain.

    POST /api/v2/blockchain/consortium/contribution/
    """

    permission_classes = [IsAuthenticated, IsCompanyMember]

    def post(self, request):
        """Record a data contribution."""
        serializer = ContributionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        network = request.query_params.get("network", "arbitrum_sepolia")
        contracts = get_contract_addresses(network)

        if not contracts.governance:
            return Response(
                {"detail": "Governance contract not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        service = ConsortiumService(contracts.governance, network)

        result = service.record_contribution(
            consortium_id=_hex_to_bytes(serializer.validated_data["consortium_id"]),
            record_count=serializer.validated_data["record_count"],
            feature_count=serializer.validated_data["feature_count"],
            data_hash=_hex_to_bytes(serializer.validated_data["data_hash"]),
            checksum_hash=_hex_to_bytes(serializer.validated_data["checksum_hash"]),
        )

        return Response(
            TransactionResultSerializer(result.__dict__).data,
            status=status.HTTP_201_CREATED if result.success else status.HTTP_400_BAD_REQUEST,
        )


# =============================================================================
# MODEL REGISTRY ENDPOINTS
# =============================================================================


class ModelRegisterView(APIView):
    """
    Register a model on-chain.

    POST /api/v2/blockchain/model/register/
    """

    permission_classes = [IsAuthenticated, IsCompanyMember]

    def post(self, request):
        """Register a new ML model."""
        serializer = ModelRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        network = request.query_params.get("network", "arbitrum_sepolia")
        contracts = get_contract_addresses(network)

        if not contracts.model_registry:
            return Response(
                {"detail": "Model registry contract not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        service = ModelRegistryService(contracts.model_registry, network)

        result = service.register_model(
            model_type=serializer.validated_data["model_type"],
            version=serializer.validated_data["version"],
        )

        return Response(
            TransactionResultSerializer(result.__dict__).data,
            status=status.HTTP_201_CREATED if result.success else status.HTTP_400_BAD_REQUEST,
        )


class ModelDetailView(APIView):
    """
    Get model details from chain.

    GET /api/v2/blockchain/model/{model_id}/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, model_id: str):
        """Get model details."""
        network = request.query_params.get("network", "arbitrum_sepolia")
        contracts = get_contract_addresses(network)

        if not contracts.model_registry:
            return Response(
                {"detail": "Model registry contract not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        service = ModelRegistryService(contracts.model_registry, network)

        try:
            data = service.get_model(_hex_to_bytes(model_id))
            return Response(ModelResponseSerializer(data).data)
        except Exception as e:
            logger.error(f"Failed to get model: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CheckpointSaveView(APIView):
    """
    Save a model checkpoint on-chain.

    POST /api/v2/blockchain/model/checkpoint/
    """

    permission_classes = [IsAuthenticated, IsCompanyMember]

    def post(self, request):
        """Save a training checkpoint."""
        serializer = CheckpointSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        network = request.query_params.get("network", "arbitrum_sepolia")
        contracts = get_contract_addresses(network)

        if not contracts.model_registry:
            return Response(
                {"detail": "Model registry contract not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        service = ModelRegistryService(contracts.model_registry, network)

        result = service.save_checkpoint(
            model_id=_hex_to_bytes(serializer.validated_data["model_id"]),
            epoch=serializer.validated_data["epoch"],
            weights_hash=_hex_to_bytes(serializer.validated_data["weights_hash"]),
            metrics_hash=_hex_to_bytes(serializer.validated_data["metrics_hash"]),
        )

        return Response(
            TransactionResultSerializer(result.__dict__).data,
            status=status.HTTP_201_CREATED if result.success else status.HTTP_400_BAD_REQUEST,
        )


class CheckpointVerifyView(APIView):
    """
    Verify a model checkpoint.

    POST /api/v2/blockchain/model/checkpoint/verify/
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Verify a checkpoint (O(1) operation)."""
        serializer = VerifyCheckpointSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        network = request.query_params.get("network", "arbitrum_sepolia")
        contracts = get_contract_addresses(network)

        if not contracts.model_registry:
            return Response(
                {"detail": "Model registry contract not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        service = ModelRegistryService(contracts.model_registry, network)

        try:
            valid = service.verify_checkpoint(
                model_id=_hex_to_bytes(serializer.validated_data["model_id"]),
                epoch=serializer.validated_data["epoch"],
                weights_hash=_hex_to_bytes(serializer.validated_data["weights_hash"]),
            )
            return Response({"valid": valid})
        except Exception as e:
            logger.error(f"Failed to verify checkpoint: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


# =============================================================================
# COMPUTATION VERIFIER ENDPOINTS
# =============================================================================


class ComputationRegisterView(APIView):
    """
    Register a computation on-chain.

    POST /api/v2/blockchain/computation/register/
    """

    permission_classes = [IsAuthenticated, IsCompanyMember]

    def post(self, request):
        """Register a computation result."""
        serializer = ComputationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        network = request.query_params.get("network", "arbitrum_sepolia")
        contracts = get_contract_addresses(network)

        if not contracts.computation_verifier:
            return Response(
                {"detail": "Computation verifier contract not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        service = ComputationVerifierService(contracts.computation_verifier, network)

        proof_hash = serializer.validated_data.get("proof_hash")
        proof_bytes = _hex_to_bytes(proof_hash) if proof_hash else b"\x00" * 32

        result = service.register_computation(
            model_id=_hex_to_bytes(serializer.validated_data["model_id"]),
            input_hash=_hex_to_bytes(serializer.validated_data["input_hash"]),
            output_hash=_hex_to_bytes(serializer.validated_data["output_hash"]),
            proof_hash=proof_bytes,
        )

        return Response(
            TransactionResultSerializer(result.__dict__).data,
            status=status.HTTP_201_CREATED if result.success else status.HTTP_400_BAD_REQUEST,
        )


class ComputationBatchView(APIView):
    """
    Register a batch of computations on-chain.

    POST /api/v2/blockchain/computation/batch/
    """

    permission_classes = [IsAuthenticated, IsCompanyMember]

    def post(self, request):
        """Register a batch of computation results."""
        serializer = BatchComputationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        network = request.query_params.get("network", "arbitrum_sepolia")
        contracts = get_contract_addresses(network)

        if not contracts.computation_verifier:
            return Response(
                {"detail": "Computation verifier contract not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        service = ComputationVerifierService(contracts.computation_verifier, network)

        result = service.register_batch(
            model_id=_hex_to_bytes(serializer.validated_data["model_id"]),
            input_hashes=[_hex_to_bytes(h) for h in serializer.validated_data["input_hashes"]],
            output_hashes=[_hex_to_bytes(h) for h in serializer.validated_data["output_hashes"]],
        )

        return Response(
            TransactionResultSerializer(result.__dict__).data,
            status=status.HTTP_201_CREATED if result.success else status.HTTP_400_BAD_REQUEST,
        )


class ComputationVerifyView(APIView):
    """
    Verify a computation output.

    POST /api/v2/blockchain/computation/verify/
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Verify a computation output (O(1) operation)."""
        serializer = VerifyOutputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        network = request.query_params.get("network", "arbitrum_sepolia")
        contracts = get_contract_addresses(network)

        if not contracts.computation_verifier:
            return Response(
                {"detail": "Computation verifier contract not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        service = ComputationVerifierService(contracts.computation_verifier, network)

        try:
            valid, proof_hash = service.verify_output(
                model_id=_hex_to_bytes(serializer.validated_data["model_id"]),
                input_hash=_hex_to_bytes(serializer.validated_data["input_hash"]),
                output_hash=_hex_to_bytes(serializer.validated_data["output_hash"]),
            )
            data = {
                "valid": valid,
                "proof_hash": proof_hash.hex() if isinstance(proof_hash, bytes) else proof_hash,
            }
            return Response(VerifyOutputResponseSerializer(data).data)
        except Exception as e:
            logger.error(f"Failed to verify output: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

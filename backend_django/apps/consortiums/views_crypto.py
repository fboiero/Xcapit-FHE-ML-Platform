"""
API views para servicios criptográficos (ZKP, MPC, DP) de consorcios.

Expone endpoints REST para verificación de contribuciones con Zero-Knowledge
Proofs, agregación segura con Computación Multipartita, y privatización de
datos con Privacidad Diferencial.
"""

from __future__ import annotations

import base64
from typing import Any

import numpy as np
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsCompanyMember, IsConsortiumMember

from .services.crypto_service import CryptoService
from .services.mpc_service import MPCService
from .services.privacy_service import PrivacyService


# =============================================================================
# Serializers — Input validation
# =============================================================================


class ZKPVerifyContributionSerializer(serializers.Serializer):
    """Validates input for ZKP contribution verification."""

    data = serializers.CharField(
        help_text="Base64-encoded contribution data.",
    )

    def validate_data(self, value: str) -> str:
        try:
            base64.b64decode(value, validate=True)
        except Exception:
            raise serializers.ValidationError(
                "Invalid base64 encoding."
            )
        return value


class ZKPVerifyModelAccuracySerializer(serializers.Serializer):
    """Validates input for ZKP model accuracy verification."""

    metrics = serializers.DictField(
        child=serializers.FloatField(min_value=0.0, max_value=1.0),
        help_text="Model metrics dictionary with values in [0, 1].",
    )

    def validate_metrics(self, value: dict[str, float]) -> dict[str, float]:
        if not value:
            raise serializers.ValidationError(
                "Metrics dictionary cannot be empty."
            )
        return value


class MPCSetupKeysSerializer(serializers.Serializer):
    """Validates input for MPC threshold key generation."""

    threshold = serializers.IntegerField(
        min_value=2,
        help_text="Minimum number of shares required for reconstruction (K).",
    )
    n_parties = serializers.IntegerField(
        min_value=2,
        help_text="Total number of parties (N).",
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs["threshold"] > attrs["n_parties"]:
            raise serializers.ValidationError(
                {"threshold": "Threshold cannot exceed n_parties."}
            )
        return attrs


class MPCAggregateSerializer(serializers.Serializer):
    """Validates input for MPC secure aggregation."""

    updates = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField()),
        min_length=2,
        help_text="List of update vectors, one per participant.",
    )
    seed = serializers.IntegerField(
        required=False,
        default=None,
        allow_null=True,
        help_text="Shared seed for deterministic mask generation.",
    )

    def validate_updates(
        self, value: list[list[float]]
    ) -> list[list[float]]:
        if not value:
            raise serializers.ValidationError(
                "Updates list cannot be empty."
            )
        vector_size = len(value[0])
        if vector_size == 0:
            raise serializers.ValidationError(
                "Update vectors cannot be empty."
            )
        for idx, vec in enumerate(value):
            if len(vec) != vector_size:
                raise serializers.ValidationError(
                    f"All update vectors must have the same size. "
                    f"Vector at index {idx} has size {len(vec)}, "
                    f"expected {vector_size}."
                )
        return value


class DPPrivatizeSerializer(serializers.Serializer):
    """Validates input for differential privacy data privatization."""

    data = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField()),
        min_length=1,
        help_text="2D array of data to privatize.",
    )
    epsilon = serializers.FloatField(
        min_value=1e-10,
        help_text="Privacy parameter (larger = less noise).",
    )
    delta = serializers.FloatField(
        min_value=0.0,
        max_value=1.0,
        default=1e-5,
        help_text="Failure probability (for Gaussian mechanism).",
    )
    mechanism = serializers.ChoiceField(
        choices=["laplace", "gaussian"],
        default="gaussian",
        help_text="Noise mechanism: 'laplace' or 'gaussian'.",
    )


class DPBudgetCheckSerializer(serializers.Serializer):
    """Validates input for differential privacy budget check."""

    total_epsilon = serializers.FloatField(
        min_value=1e-10,
        help_text="Total epsilon budget.",
    )
    total_delta = serializers.FloatField(
        min_value=0.0,
        max_value=1.0,
        help_text="Total delta budget.",
    )
    steps_used = serializers.IntegerField(
        min_value=0,
        help_text="Number of operations already performed.",
    )
    mechanism_epsilon = serializers.FloatField(
        min_value=1e-10,
        help_text="Epsilon cost of the next proposed operation.",
    )
    mechanism_delta = serializers.FloatField(
        min_value=0.0,
        max_value=1.0,
        default=0.0,
        help_text="Delta cost of the next proposed operation.",
    )


# =============================================================================
# Helpers
# =============================================================================


def _service_error_response(
    result: Any,
    http_status: int = status.HTTP_400_BAD_REQUEST,
) -> Response:
    """Build an error response from a failed ``ServiceResult``."""
    return Response(
        {
            "error": result.error,
            "error_code": result.error_code,
        },
        status=http_status,
    )


# =============================================================================
# ZKP Views
# =============================================================================


class ZKPVerifyContributionView(APIView):
    """
    POST /consortiums/<consortium_pk>/zkp/verify-contribution/

    Genera y verifica una prueba de conocimiento cero (ZKP) para una
    contribución de datos. Los datos se envían codificados en base64.
    """

    permission_classes = [IsAuthenticated, IsCompanyMember, IsConsortiumMember]

    def post(self, request: Request, consortium_pk: str) -> Response:
        serializer = ZKPVerifyContributionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data_bytes: bytes = base64.b64decode(serializer.validated_data["data"])
        company_id = request.user.company_id

        service = CryptoService()
        result = service.verify_contribution_zkp(
            company_id=company_id,
            consortium_id=consortium_pk,
            data_bytes=data_bytes,
        )

        if not result.success:
            return _service_error_response(result)

        return Response(
            {
                "verified": result.data["verified"],
                "proof": result.data["proof"],
                "timing_seconds": result.metadata.get("elapsed_seconds", 0.0),
            },
            status=status.HTTP_200_OK,
        )


class ZKPVerifyModelAccuracyView(APIView):
    """
    POST /consortiums/<consortium_pk>/zkp/verify-accuracy/

    Genera y verifica una prueba ZKP para métricas de precisión de un modelo.
    """

    permission_classes = [IsAuthenticated, IsCompanyMember, IsConsortiumMember]

    def post(self, request: Request, consortium_pk: str) -> Response:
        serializer = ZKPVerifyModelAccuracySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        metrics: dict[str, float] = serializer.validated_data["metrics"]

        service = CryptoService()
        result = service.verify_model_accuracy_zkp(metrics=metrics)

        if not result.success:
            return _service_error_response(result)

        return Response(
            {
                "verified": result.data["verified"],
                "proof": result.data["proof"],
            },
            status=status.HTTP_200_OK,
        )


# =============================================================================
# MPC Views
# =============================================================================


class MPCSetupKeysView(APIView):
    """
    POST /consortiums/<consortium_pk>/mpc/setup-keys/

    Genera shares de clave Shamir para el consorcio, distribuyendo
    la clave entre N partes con un umbral K.
    """

    permission_classes = [IsAuthenticated, IsCompanyMember, IsConsortiumMember]

    def post(self, request: Request, consortium_pk: str) -> Response:
        serializer = MPCSetupKeysSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        threshold: int = serializer.validated_data["threshold"]
        n_parties: int = serializer.validated_data["n_parties"]

        service = MPCService()
        result = service.setup_threshold_keys(
            consortium_id=consortium_pk,
            threshold=threshold,
            n_parties=n_parties,
        )

        if not result.success:
            return _service_error_response(result)

        return Response(
            {
                "shares_count": len(result.data["shares"]),
                "commitment": result.data["verification_commitment_hex"],
                "timing_seconds": result.metadata.get("elapsed_seconds", 0.0),
            },
            status=status.HTTP_200_OK,
        )


class MPCAggregateView(APIView):
    """
    POST /consortiums/<consortium_pk>/mpc/aggregate/

    Realiza agregación segura de actualizaciones de modelo enmascaradas
    mediante el protocolo de enmascaramiento por pares.
    """

    permission_classes = [IsAuthenticated, IsCompanyMember, IsConsortiumMember]

    def post(self, request: Request, consortium_pk: str) -> Response:
        serializer = MPCAggregateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        raw_updates: list[list[float]] = serializer.validated_data["updates"]
        seed: int | None = serializer.validated_data.get("seed")

        np_updates: list[np.ndarray] = [
            np.array(vec, dtype=np.float64) for vec in raw_updates
        ]
        n_participants: int = len(np_updates)
        vector_size: int = len(raw_updates[0])

        service = MPCService()
        result = service.aggregate_updates(
            updates=np_updates,
            n_participants=n_participants,
            vector_size=vector_size,
            seed=seed,
        )

        if not result.success:
            return _service_error_response(result)

        aggregate = result.data["aggregate"]
        return Response(
            {
                "result": aggregate.tolist()
                if isinstance(aggregate, np.ndarray)
                else list(aggregate),
                "n_participants": result.data["n_participants"],
            },
            status=status.HTTP_200_OK,
        )


# =============================================================================
# Differential Privacy Views
# =============================================================================


class DPPrivatizeView(APIView):
    """
    POST /consortiums/<consortium_pk>/dp/privatize/

    Aplica ruido de privacidad diferencial a los datos proporcionados
    usando el mecanismo indicado (Laplace o Gaussiano).
    """

    permission_classes = [IsAuthenticated, IsCompanyMember, IsConsortiumMember]

    def post(self, request: Request, consortium_pk: str) -> Response:
        serializer = DPPrivatizeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        raw_data: list[list[float]] = serializer.validated_data["data"]
        epsilon: float = serializer.validated_data["epsilon"]
        delta: float = serializer.validated_data["delta"]
        mechanism: str = serializer.validated_data["mechanism"]

        np_data: np.ndarray = np.array(raw_data, dtype=np.float64)

        service = PrivacyService()
        result = service.privatize_data(
            data=np_data,
            epsilon=epsilon,
            delta=delta,
            mechanism=mechanism,
        )

        if not result.success:
            return _service_error_response(result)

        noisy = result.data["noisy_data"]
        return Response(
            {
                "privatized_data": noisy.tolist()
                if isinstance(noisy, np.ndarray)
                else list(noisy),
                "noise_params": result.data["noise_info"],
            },
            status=status.HTTP_200_OK,
        )


class DPBudgetCheckView(APIView):
    """
    POST /consortiums/<consortium_pk>/dp/budget-check/

    Verifica si el presupuesto de privacidad diferencial permite
    realizar una operación adicional con los costos indicados.
    """

    permission_classes = [IsAuthenticated, IsCompanyMember, IsConsortiumMember]

    def post(self, request: Request, consortium_pk: str) -> Response:
        serializer = DPBudgetCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = PrivacyService()
        result = service.check_privacy_budget(
            total_epsilon=serializer.validated_data["total_epsilon"],
            total_delta=serializer.validated_data["total_delta"],
            steps_used=serializer.validated_data["steps_used"],
            mechanism_epsilon=serializer.validated_data["mechanism_epsilon"],
            mechanism_delta=serializer.validated_data["mechanism_delta"],
        )

        if not result.success:
            return _service_error_response(result)

        return Response(
            {
                "budget_ok": result.data["can_proceed"],
                "remaining_epsilon": result.data["epsilon_remaining"],
                "remaining_delta": result.data["delta_remaining"],
            },
            status=status.HTTP_200_OK,
        )


# =============================================================================
# Crypto Status View
# =============================================================================


class CryptoStatusView(APIView):
    """
    GET /consortiums/<consortium_pk>/crypto/status/

    Retorna la disponibilidad de los módulos criptográficos del SDK
    (ZKP, MPC, DP, FHE).
    """

    permission_classes = [IsAuthenticated, IsCompanyMember, IsConsortiumMember]

    def get(self, request: Request, consortium_pk: str) -> Response:
        # Check ZKP availability
        try:
            from sdk.zkp import ZKProver, ZKVerifier
            zkp_available = ZKProver is not None and ZKVerifier is not None
        except ImportError:
            zkp_available = False

        # Check MPC availability
        try:
            from sdk.mpc import SecureAggregator, ThresholdDecryptor
            mpc_available = (
                SecureAggregator is not None and ThresholdDecryptor is not None
            )
        except ImportError:
            mpc_available = False

        # Check DP availability
        try:
            from sdk.privacy import (
                GaussianMechanism,
                LaplaceMechanism,
                PrivacyAccountant,
            )
            dp_available = (
                LaplaceMechanism is not None
                and GaussianMechanism is not None
                and PrivacyAccountant is not None
            )
        except ImportError:
            dp_available = False

        # Check FHE availability
        try:
            import tenseal  # noqa: F401
            fhe_available = True
        except ImportError:
            fhe_available = False

        return Response(
            {
                "zkp_available": zkp_available,
                "mpc_available": mpc_available,
                "dp_available": dp_available,
                "fhe_available": fhe_available,
            },
            status=status.HTTP_200_OK,
        )

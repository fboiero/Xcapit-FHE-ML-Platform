"""Servicio de pruebas de conocimiento cero (ZKP) para verificación de contribuciones.

Integra el módulo ``sdk.zkp`` en el backend Django, permitiendo crear y
verificar pruebas criptográficas de que un miembro contribuyó datos válidos
sin revelar los datos en sí.
"""

from __future__ import annotations

import hashlib
import time
from typing import Any

from apps.core.services.base import BaseService, ServiceResult

try:
    from sdk.zkp import ContributionProof, ZKProver, ZKVerifier
except ImportError:  # pragma: no cover – SDK may not be on PYTHONPATH
    ZKProver = None  # type: ignore[assignment,misc]
    ZKVerifier = None  # type: ignore[assignment,misc]
    ContributionProof = None  # type: ignore[assignment,misc]

_SDK_UNAVAILABLE = (
    "SDK ZKP module is not available. "
    "Ensure the project root is on PYTHONPATH so that `sdk.zkp` is importable."
)


class CryptoService(BaseService):
    """Operaciones de prueba de conocimiento cero para el flujo de contribuciones.

    Utiliza ``ZKProver`` / ``ZKVerifier`` del SDK para generar y validar
    pruebas criptográficas sin exponer los datos subyacentes.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def verify_contribution_zkp(
        self,
        company_id: int | str,
        consortium_id: int | str,
        data_bytes: bytes,
    ) -> ServiceResult[dict[str, Any]]:
        """Crear y verificar una prueba ZKP para una contribución de datos.

        Args:
            company_id: Identificador de la empresa que contribuye.
            consortium_id: Identificador del consorcio destino.
            data_bytes: Datos crudos de la contribución (bytes).

        Returns:
            ``ServiceResult`` con la prueba verificada o un mensaje de error.
        """
        if ZKProver is None or ZKVerifier is None:
            return ServiceResult.fail(_SDK_UNAVAILABLE, error_code="SDK_UNAVAILABLE")

        start = time.monotonic()
        try:
            prover_id = str(company_id)
            prover = ZKProver(prover_id=prover_id)
            proof = prover.prove_contribution(data=data_bytes, contributor_id=prover_id)

            verifier = ZKVerifier()
            is_valid = verifier.verify_contribution(proof)

            elapsed = time.monotonic() - start

            if not is_valid:
                self.logger.warning(
                    "ZKP contribution proof failed verification for "
                    "company=%s consortium=%s",
                    company_id,
                    consortium_id,
                )
                return ServiceResult.fail(
                    "La prueba ZKP de contribución no pasó la verificación.",
                    error_code="ZKP_VERIFICATION_FAILED",
                    elapsed_seconds=elapsed,
                )

            self.logger.info(
                "ZKP contribution proof created and verified for "
                "company=%s consortium=%s (%.3fs)",
                company_id,
                consortium_id,
                elapsed,
            )
            return ServiceResult.ok(
                data={
                    "proof": proof,
                    "verified": True,
                    "company_id": str(company_id),
                    "consortium_id": str(consortium_id),
                    "data_hash": hashlib.sha256(data_bytes).hexdigest(),
                    "data_size": len(data_bytes),
                },
                elapsed_seconds=elapsed,
            )

        except (ValueError, TypeError, OverflowError) as exc:
            elapsed = time.monotonic() - start
            self.logger.exception(
                "Error creating ZKP contribution proof for company=%s consortium=%s",
                company_id,
                consortium_id,
            )
            return ServiceResult.fail(
                f"Error al generar la prueba ZKP de contribución: {exc}",
                error_code="ZKP_PROOF_ERROR",
                elapsed_seconds=elapsed,
            )

    def verify_model_accuracy_zkp(
        self,
        metrics: dict[str, float],
    ) -> ServiceResult[dict[str, Any]]:
        """Crear y verificar una prueba ZKP para métricas de entrenamiento.

        Args:
            metrics: Diccionario con métricas del modelo (valores en [0, 1]).
                     Ejemplo: ``{"accuracy": 0.95, "f1": 0.92}``.

        Returns:
            ``ServiceResult`` con la prueba verificada o un mensaje de error.
        """
        if ZKProver is None or ZKVerifier is None:
            return ServiceResult.fail(_SDK_UNAVAILABLE, error_code="SDK_UNAVAILABLE")

        start = time.monotonic()
        try:
            prover = ZKProver(prover_id="model-accuracy-verifier")
            proof = prover.prove_model_accuracy(metrics=metrics)

            verifier = ZKVerifier()
            is_valid = verifier.verify_model_accuracy(proof)

            elapsed = time.monotonic() - start

            if not is_valid:
                self.logger.warning(
                    "ZKP model accuracy proof failed verification for metrics=%s",
                    list(metrics.keys()),
                )
                return ServiceResult.fail(
                    "La prueba ZKP de precisión del modelo no pasó la verificación.",
                    error_code="ZKP_VERIFICATION_FAILED",
                    elapsed_seconds=elapsed,
                )

            self.logger.info(
                "ZKP model accuracy proof created and verified for metrics=%s (%.3fs)",
                list(metrics.keys()),
                elapsed,
            )
            return ServiceResult.ok(
                data={
                    "proof": proof,
                    "verified": True,
                    "metrics": metrics,
                },
                elapsed_seconds=elapsed,
            )

        except (ValueError, TypeError, OverflowError) as exc:
            elapsed = time.monotonic() - start
            self.logger.exception(
                "Error creating ZKP model accuracy proof for metrics=%s",
                list(metrics.keys()),
            )
            return ServiceResult.fail(
                f"Error al generar la prueba ZKP de precisión: {exc}",
                error_code="ZKP_PROOF_ERROR",
                elapsed_seconds=elapsed,
            )

    def validate_stored_proof(
        self,
        proof_dict: dict[str, Any],
    ) -> ServiceResult[dict[str, Any]]:
        """Re-verificar una prueba ZKP previamente almacenada.

        Args:
            proof_dict: Diccionario de prueba generado previamente por
                ``verify_contribution_zkp`` o ``verify_model_accuracy_zkp``.

        Returns:
            ``ServiceResult`` indicando si la prueba sigue siendo válida.
        """
        if ZKVerifier is None or ContributionProof is None:
            return ServiceResult.fail(_SDK_UNAVAILABLE, error_code="SDK_UNAVAILABLE")

        start = time.monotonic()
        try:
            proof_type = proof_dict.get("proof_type", "")
            verifier = ZKVerifier()

            if proof_type == "contribution":
                is_valid = verifier.verify_contribution(proof_dict)
            elif proof_type == "model_accuracy":
                is_valid = verifier.verify_model_accuracy(proof_dict)
            else:
                elapsed = time.monotonic() - start
                return ServiceResult.fail(
                    f"Tipo de prueba desconocido: '{proof_type}'. "
                    "Se esperaba 'contribution' o 'model_accuracy'.",
                    error_code="UNKNOWN_PROOF_TYPE",
                    elapsed_seconds=elapsed,
                )

            elapsed = time.monotonic() - start

            if not is_valid:
                self.logger.warning(
                    "Stored ZKP proof re-verification failed (type=%s)",
                    proof_type,
                )
                return ServiceResult.fail(
                    "La prueba ZKP almacenada no pasó la re-verificación.",
                    error_code="ZKP_VERIFICATION_FAILED",
                    elapsed_seconds=elapsed,
                )

            self.logger.info(
                "Stored ZKP proof re-verified successfully (type=%s, %.3fs)",
                proof_type,
                elapsed,
            )
            return ServiceResult.ok(
                data={
                    "proof_type": proof_type,
                    "verified": True,
                },
                elapsed_seconds=elapsed,
            )

        except (KeyError, ValueError, TypeError, OverflowError) as exc:
            elapsed = time.monotonic() - start
            self.logger.exception("Error re-verifying stored ZKP proof")
            return ServiceResult.fail(
                f"Error al re-verificar la prueba ZKP: {exc}",
                error_code="ZKP_VALIDATION_ERROR",
                elapsed_seconds=elapsed,
            )

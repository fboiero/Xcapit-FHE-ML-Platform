"""Servicio de Computación Multipartita Segura (MPC) para entrenamiento en consorcios.

Integra el módulo ``sdk.mpc`` en el backend Django, proporcionando
distribución de claves mediante Shamir, agregación segura de actualizaciones
de modelos y orquestación del protocolo MPC para federated learning.
"""

from __future__ import annotations

import secrets
import time
from typing import Any

import numpy as np

from apps.core.services.base import BaseService, ServiceResult

try:
    from sdk.mpc import SecretSharer, SecureAggregator, ThresholdDecryptor
except ImportError:  # pragma: no cover – SDK may not be on PYTHONPATH
    SecretSharer = None  # type: ignore[assignment,misc]
    SecureAggregator = None  # type: ignore[assignment,misc]
    ThresholdDecryptor = None  # type: ignore[assignment,misc]

_SDK_UNAVAILABLE = (
    "SDK MPC module is not available. "
    "Ensure the project root is on PYTHONPATH so that `sdk.mpc` is importable."
)


class MPCService(BaseService):
    """Operaciones de Computación Multipartita Segura para consorcios.

    Proporciona distribución de claves Shamir, configuración de
    agregación segura y agregación de actualizaciones de modelos
    enmascaradas para federated learning.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def setup_threshold_keys(
        self,
        consortium_id: int | str,
        threshold: int,
        n_parties: int,
    ) -> ServiceResult[dict[str, Any]]:
        """Generar shares de clave Shamir para un consorcio.

        Crea una clave simétrica y la divide en ``n_parties`` shares con
        un umbral de ``threshold`` shares necesarios para reconstruirla.

        Args:
            consortium_id: Identificador del consorcio.
            threshold: Número mínimo de shares para reconstrucción (K).
            n_parties: Número total de partes (N).

        Returns:
            ``ServiceResult`` con los shares y commitment de verificación.
        """
        if ThresholdDecryptor is None:
            return ServiceResult.fail(_SDK_UNAVAILABLE, error_code="SDK_UNAVAILABLE")

        start = time.monotonic()
        try:
            decryptor = ThresholdDecryptor(
                threshold=threshold,
                total_parties=n_parties,
            )
            key_shares, verification_commitment = decryptor.setup()

            # Serializar shares para almacenamiento/transporte
            serialized_shares: list[dict[str, Any]] = [
                {
                    "party_index": idx,
                    "share_hex": share_bytes.hex(),
                    "share_length": len(share_bytes),
                }
                for idx, share_bytes in key_shares
            ]

            elapsed = time.monotonic() - start

            self.logger.info(
                "Threshold key shares generated for consortium=%s "
                "(threshold=%d, n_parties=%d, %.3fs)",
                consortium_id,
                threshold,
                n_parties,
                elapsed,
            )
            return ServiceResult.ok(
                data={
                    "consortium_id": str(consortium_id),
                    "threshold": threshold,
                    "n_parties": n_parties,
                    "shares": serialized_shares,
                    "verification_commitment_hex": verification_commitment.hex(),
                },
                elapsed_seconds=elapsed,
            )

        except (ValueError, TypeError, OverflowError) as exc:
            elapsed = time.monotonic() - start
            self.logger.exception(
                "Error generating threshold keys for consortium=%s",
                consortium_id,
            )
            return ServiceResult.fail(
                f"Error al generar claves de umbral: {exc}",
                error_code="MPC_KEY_SETUP_ERROR",
                elapsed_seconds=elapsed,
            )

    def create_secure_aggregation(
        self,
        consortium_id: int | str,
        n_participants: int,
        vector_size: int,
    ) -> ServiceResult[dict[str, Any]]:
        """Configurar un SecureAggregator para federated learning.

        Inicializa el protocolo de agregación segura basado en enmascaramiento
        por pares, donde cada participante enmascara su vector de actualización
        de forma que la suma de todas las actualizaciones enmascaradas sea
        igual a la suma real.

        Args:
            consortium_id: Identificador del consorcio.
            n_participants: Número de participantes en la ronda de agregación.
            vector_size: Dimensionalidad de los vectores de actualización del modelo.

        Returns:
            ``ServiceResult`` con la configuración del agregador.
        """
        if SecureAggregator is None:
            return ServiceResult.fail(_SDK_UNAVAILABLE, error_code="SDK_UNAVAILABLE")

        start = time.monotonic()
        try:
            aggregator = SecureAggregator(
                n_parties=n_participants,
                vector_size=vector_size,
            )

            # Generar una semilla compartida para la ronda
            shared_seed = secrets.randbits(128)

            elapsed = time.monotonic() - start

            self.logger.info(
                "Secure aggregation configured for consortium=%s "
                "(n_participants=%d, vector_size=%d, %.3fs)",
                consortium_id,
                n_participants,
                vector_size,
                elapsed,
            )
            return ServiceResult.ok(
                data={
                    "consortium_id": str(consortium_id),
                    "n_participants": n_participants,
                    "vector_size": vector_size,
                    "shared_seed": shared_seed,
                    "aggregator_ready": True,
                },
                elapsed_seconds=elapsed,
            )

        except (ValueError, TypeError) as exc:
            elapsed = time.monotonic() - start
            self.logger.exception(
                "Error creating secure aggregation for consortium=%s",
                consortium_id,
            )
            return ServiceResult.fail(
                f"Error al configurar agregación segura: {exc}",
                error_code="MPC_AGGREGATION_SETUP_ERROR",
                elapsed_seconds=elapsed,
            )

    def aggregate_updates(
        self,
        updates: list[np.ndarray],
        n_participants: int,
        vector_size: int,
        seed: int | None = None,
    ) -> ServiceResult[dict[str, Any]]:
        """Realizar agregación segura de actualizaciones de modelo enmascaradas.

        Ejecuta el protocolo completo de agregación por enmascaramiento
        por pares: genera máscaras, aplica el enmascaramiento a cada
        actualización y luego agrega los vectores enmascarados.

        Args:
            updates: Lista de vectores de actualización, uno por participante.
            n_participants: Número de participantes.
            vector_size: Dimensionalidad de cada vector de actualización.
            seed: Semilla compartida para generación determinista de máscaras.
                  Si es ``None``, se genera una aleatoriamente.

        Returns:
            ``ServiceResult`` con el vector agregado y metadatos.
        """
        if SecureAggregator is None:
            return ServiceResult.fail(_SDK_UNAVAILABLE, error_code="SDK_UNAVAILABLE")

        start = time.monotonic()
        try:
            if len(updates) != n_participants:
                return ServiceResult.fail(
                    f"Se esperaban {n_participants} actualizaciones, "
                    f"se recibieron {len(updates)}.",
                    error_code="MPC_UPDATE_COUNT_MISMATCH",
                    elapsed_seconds=time.monotonic() - start,
                )

            aggregator = SecureAggregator(
                n_parties=n_participants,
                vector_size=vector_size,
            )

            if seed is None:
                seed = secrets.randbits(128)

            # Generar máscaras y enmascarar cada actualización
            masked_updates: list[np.ndarray] = []
            for party_id, update in enumerate(updates):
                update_flat = np.asarray(update, dtype=np.float64).flatten()
                if update_flat.shape[0] != vector_size:
                    return ServiceResult.fail(
                        f"La actualización del participante {party_id} tiene "
                        f"tamaño {update_flat.shape[0]}, se esperaba {vector_size}.",
                        error_code="MPC_VECTOR_SIZE_MISMATCH",
                        elapsed_seconds=time.monotonic() - start,
                    )
                masks = aggregator.generate_masks(party_id, seed=seed)
                masked = aggregator.mask_update(update_flat, party_id, masks)
                masked_updates.append(masked)

            # Agregar las actualizaciones enmascaradas
            aggregate = aggregator.aggregate(masked_updates)

            elapsed = time.monotonic() - start

            self.logger.info(
                "Secure aggregation completed (n_participants=%d, "
                "vector_size=%d, %.3fs)",
                n_participants,
                vector_size,
                elapsed,
            )
            return ServiceResult.ok(
                data={
                    "aggregate": aggregate,
                    "aggregate_shape": list(aggregate.shape),
                    "n_participants": n_participants,
                    "vector_size": vector_size,
                    "aggregate_norm": float(np.linalg.norm(aggregate)),
                },
                elapsed_seconds=elapsed,
            )

        except (ValueError, TypeError, OverflowError) as exc:
            elapsed = time.monotonic() - start
            self.logger.exception("Error during secure aggregation")
            return ServiceResult.fail(
                f"Error al realizar la agregación segura: {exc}",
                error_code="MPC_AGGREGATION_ERROR",
                elapsed_seconds=elapsed,
            )

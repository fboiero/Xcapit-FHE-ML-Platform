"""Servicio de Privacidad Diferencial (DP) para el pipeline de datos.

Integra el módulo ``sdk.privacy`` en el backend Django, proporcionando
mecanismos de ruido para privatización de datos, contabilidad de presupuesto
de privacidad y recorte de gradientes para DP-SGD.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from apps.core.services.base import BaseService, ServiceResult

try:
    from sdk.privacy import (
        GaussianMechanism,
        GradientClipper,
        LaplaceMechanism,
        PrivacyAccountant,
    )
except ImportError:  # pragma: no cover – SDK may not be on PYTHONPATH
    LaplaceMechanism = None  # type: ignore[assignment,misc]
    GaussianMechanism = None  # type: ignore[assignment,misc]
    PrivacyAccountant = None  # type: ignore[assignment,misc]
    GradientClipper = None  # type: ignore[assignment,misc]

_SDK_UNAVAILABLE = (
    "SDK privacy module is not available. "
    "Ensure the project root is on PYTHONPATH so that `sdk.privacy` is importable."
)

_VALID_MECHANISMS = ("laplace", "gaussian")


class PrivacyService(BaseService):
    """Operaciones de privacidad diferencial para el pipeline de datos.

    Aplica ruido calibrado a datos, verifica presupuesto de privacidad,
    recorta gradientes y genera reportes de consumo de presupuesto.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def privatize_data(
        self,
        data: np.ndarray,
        epsilon: float,
        delta: float,
        mechanism: str = "laplace",
    ) -> ServiceResult[dict[str, Any]]:
        """Aplicar ruido de privacidad diferencial a datos.

        Args:
            data: Array de datos a privatizar (numpy).
            epsilon: Parámetro de privacidad (mayor = menos ruido).
            delta: Probabilidad de fallo (solo para mecanismo Gaussiano).
            mechanism: Mecanismo de ruido — ``"laplace"`` o ``"gaussian"``.

        Returns:
            ``ServiceResult`` con los datos privatizados y metadatos.
        """
        if LaplaceMechanism is None or GaussianMechanism is None:
            return ServiceResult.fail(_SDK_UNAVAILABLE, error_code="SDK_UNAVAILABLE")

        start = time.monotonic()
        try:
            mechanism_lower = mechanism.lower()
            if mechanism_lower not in _VALID_MECHANISMS:
                return ServiceResult.fail(
                    f"Mecanismo '{mechanism}' no soportado. "
                    f"Use uno de: {_VALID_MECHANISMS}.",
                    error_code="DP_INVALID_MECHANISM",
                    elapsed_seconds=time.monotonic() - start,
                )

            arr = np.asarray(data, dtype=np.float64)
            if arr.size == 0:
                return ServiceResult.fail(
                    "Los datos no pueden estar vacíos.",
                    error_code="DP_EMPTY_DATA",
                    elapsed_seconds=time.monotonic() - start,
                )

            # Sensibilidad L1/L2 basada en el rango de los datos
            sensitivity = float(np.max(np.abs(arr))) if arr.size > 0 else 1.0
            sensitivity = max(sensitivity, 1e-10)  # evitar sensitivity == 0

            if mechanism_lower == "laplace":
                dp_mechanism = LaplaceMechanism(epsilon=epsilon)
                noisy_data = dp_mechanism.add_noise(arr, sensitivity=sensitivity)
                noise_info = {
                    "mechanism": "laplace",
                    "scale": sensitivity / epsilon,
                    "variance": dp_mechanism.variance(sensitivity),
                }
            else:
                dp_mechanism = GaussianMechanism(epsilon=epsilon, delta=delta)
                noisy_data = dp_mechanism.add_noise(arr, sensitivity=sensitivity)
                sigma = dp_mechanism.compute_sigma(sensitivity)
                noise_info = {
                    "mechanism": "gaussian",
                    "sigma": sigma,
                    "variance": dp_mechanism.variance(sensitivity),
                }

            elapsed = time.monotonic() - start

            self.logger.info(
                "Data privatized with %s mechanism (epsilon=%.4f, "
                "delta=%.2e, sensitivity=%.4f, %.3fs)",
                mechanism_lower,
                epsilon,
                delta,
                sensitivity,
                elapsed,
            )
            return ServiceResult.ok(
                data={
                    "noisy_data": noisy_data,
                    "original_shape": list(arr.shape),
                    "epsilon": epsilon,
                    "delta": delta,
                    "sensitivity": sensitivity,
                    "noise_info": noise_info,
                },
                elapsed_seconds=elapsed,
            )

        except (ValueError, TypeError, OverflowError) as exc:
            elapsed = time.monotonic() - start
            self.logger.exception("Error privatizing data")
            return ServiceResult.fail(
                f"Error al privatizar datos: {exc}",
                error_code="DP_NOISE_ERROR",
                elapsed_seconds=elapsed,
            )

    def check_privacy_budget(
        self,
        total_epsilon: float,
        total_delta: float,
        steps_used: int,
        mechanism_epsilon: float,
        mechanism_delta: float = 0.0,
    ) -> ServiceResult[dict[str, Any]]:
        """Verificar si el presupuesto de privacidad permite otra operación.

        Simula el consumo de ``steps_used`` operaciones previas y luego
        verifica si queda presupuesto para una operación adicional con
        los costos indicados.

        Args:
            total_epsilon: Presupuesto total de epsilon.
            total_delta: Presupuesto total de delta.
            steps_used: Número de operaciones ya realizadas.
            mechanism_epsilon: Epsilon de la próxima operación propuesta.
            mechanism_delta: Delta de la próxima operación propuesta.

        Returns:
            ``ServiceResult`` con el estado del presupuesto.
        """
        if PrivacyAccountant is None:
            return ServiceResult.fail(_SDK_UNAVAILABLE, error_code="SDK_UNAVAILABLE")

        start = time.monotonic()
        try:
            accountant = PrivacyAccountant(
                total_epsilon=total_epsilon,
                total_delta=total_delta,
            )

            # Simular operaciones previas
            for step in range(steps_used):
                accountant.consume(
                    epsilon=mechanism_epsilon,
                    delta=mechanism_delta,
                    operation=f"previous_step_{step + 1}",
                )

            # Verificar si hay presupuesto para una operación más
            can_proceed = accountant.budget.can_afford(
                epsilon_cost=mechanism_epsilon,
                delta_cost=mechanism_delta,
            )
            eps_remaining, delta_remaining = accountant.remaining_budget()
            estimated_remaining = accountant.estimate_remaining_queries(
                per_query_epsilon=mechanism_epsilon,
                per_query_delta=mechanism_delta,
            )

            elapsed = time.monotonic() - start

            self.logger.info(
                "Privacy budget check: can_proceed=%s, "
                "eps_remaining=%.4f, delta_remaining=%.2e (%.3fs)",
                can_proceed,
                eps_remaining,
                delta_remaining,
                elapsed,
            )
            return ServiceResult.ok(
                data={
                    "can_proceed": can_proceed,
                    "is_exhausted": accountant.budget.is_exhausted,
                    "epsilon_remaining": eps_remaining,
                    "delta_remaining": delta_remaining,
                    "epsilon_used": accountant.budget.epsilon_used,
                    "delta_used": accountant.budget.delta_used,
                    "steps_used": steps_used,
                    "estimated_remaining_queries": estimated_remaining,
                },
                elapsed_seconds=elapsed,
            )

        except (ValueError, TypeError) as exc:
            elapsed = time.monotonic() - start
            self.logger.exception("Error checking privacy budget")
            return ServiceResult.fail(
                f"Error al verificar presupuesto de privacidad: {exc}",
                error_code="DP_BUDGET_ERROR",
                elapsed_seconds=elapsed,
            )

    def clip_gradients(
        self,
        gradients: np.ndarray,
        max_norm: float,
    ) -> ServiceResult[dict[str, Any]]:
        """Recortar gradientes por-muestra para DP-SGD.

        Limita la norma L2 de cada gradiente individual al valor
        ``max_norm``, lo cual acota la sensibilidad de la agregación
        de gradientes.

        Args:
            gradients: Array de gradientes (1D para un solo gradiente,
                       2D con shape ``(batch_size, param_dim)`` para un lote).
            max_norm: Norma L2 máxima permitida por gradiente.

        Returns:
            ``ServiceResult`` con los gradientes recortados y metadatos.
        """
        if GradientClipper is None:
            return ServiceResult.fail(_SDK_UNAVAILABLE, error_code="SDK_UNAVAILABLE")

        start = time.monotonic()
        try:
            arr = np.asarray(gradients, dtype=np.float64)
            if arr.size == 0:
                return ServiceResult.fail(
                    "Los gradientes no pueden estar vacíos.",
                    error_code="DP_EMPTY_GRADIENTS",
                    elapsed_seconds=time.monotonic() - start,
                )

            # Normas originales para informe
            if arr.ndim == 1:
                original_norms = [float(np.linalg.norm(arr))]
            else:
                original_norms = [
                    float(np.linalg.norm(arr[i])) for i in range(arr.shape[0])
                ]

            clipper = GradientClipper(max_norm=max_norm)
            clipped = clipper.clip(arr)

            # Normas recortadas
            if clipped.ndim == 1:
                clipped_norms = [float(np.linalg.norm(clipped))]
            else:
                clipped_norms = [
                    float(np.linalg.norm(clipped[i])) for i in range(clipped.shape[0])
                ]

            n_clipped = sum(
                1 for orig, clip in zip(original_norms, clipped_norms)
                if orig > max_norm
            )

            elapsed = time.monotonic() - start

            self.logger.info(
                "Gradients clipped (max_norm=%.4f, %d/%d clipped, %.3fs)",
                max_norm,
                n_clipped,
                len(original_norms),
                elapsed,
            )
            return ServiceResult.ok(
                data={
                    "clipped_gradients": clipped,
                    "original_shape": list(arr.shape),
                    "max_norm": max_norm,
                    "n_gradients": len(original_norms),
                    "n_clipped": n_clipped,
                    "original_norms": original_norms,
                    "clipped_norms": clipped_norms,
                },
                elapsed_seconds=elapsed,
            )

        except (ValueError, TypeError) as exc:
            elapsed = time.monotonic() - start
            self.logger.exception("Error clipping gradients")
            return ServiceResult.fail(
                f"Error al recortar gradientes: {exc}",
                error_code="DP_CLIP_ERROR",
                elapsed_seconds=elapsed,
            )

    def get_privacy_report(
        self,
        total_epsilon: float,
        total_delta: float,
        steps: list[dict[str, Any]],
    ) -> ServiceResult[dict[str, Any]]:
        """Generar un reporte de consumo de presupuesto de privacidad.

        Reproduce el historial de operaciones en un ``PrivacyAccountant``
        y genera un reporte completo incluyendo composición básica,
        avanzada y (si aplica) RDP.

        Args:
            total_epsilon: Presupuesto total de epsilon.
            total_delta: Presupuesto total de delta.
            steps: Lista de operaciones previas. Cada paso es un dict con:
                   ``{"epsilon": float, "delta": float, "operation": str}``.

        Returns:
            ``ServiceResult`` con el reporte detallado de privacidad.
        """
        if PrivacyAccountant is None:
            return ServiceResult.fail(_SDK_UNAVAILABLE, error_code="SDK_UNAVAILABLE")

        start = time.monotonic()
        try:
            accountant = PrivacyAccountant(
                total_epsilon=total_epsilon,
                total_delta=total_delta,
            )

            for step_data in steps:
                step_epsilon = step_data.get("epsilon", 0.0)
                step_delta = step_data.get("delta", 0.0)
                operation = step_data.get("operation", "unknown")
                accountant.consume(
                    epsilon=step_epsilon,
                    delta=step_delta,
                    operation=operation,
                )

            report = accountant.report()

            elapsed = time.monotonic() - start

            self.logger.info(
                "Privacy report generated (total_eps=%.4f, used_eps=%.4f, "
                "%d steps, %.3fs)",
                total_epsilon,
                accountant.budget.epsilon_used,
                len(steps),
                elapsed,
            )
            return ServiceResult.ok(
                data={
                    "report": report,
                    "summary": {
                        "total_epsilon": total_epsilon,
                        "total_delta": total_delta,
                        "epsilon_used": accountant.budget.epsilon_used,
                        "delta_used": accountant.budget.delta_used,
                        "epsilon_remaining": accountant.budget.epsilon_remaining,
                        "delta_remaining": accountant.budget.delta_remaining,
                        "is_exhausted": accountant.budget.is_exhausted,
                        "total_steps": len(steps),
                    },
                },
                elapsed_seconds=elapsed,
            )

        except (ValueError, TypeError) as exc:
            elapsed = time.monotonic() - start
            self.logger.exception("Error generating privacy report")
            return ServiceResult.fail(
                f"Error al generar reporte de privacidad: {exc}",
                error_code="DP_REPORT_ERROR",
                elapsed_seconds=elapsed,
            )

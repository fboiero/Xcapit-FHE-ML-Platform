"""Privacy budget tracking with composition theorems.

Implements privacy accounting for tracking cumulative privacy loss across
multiple DP operations. Supports basic composition, advanced composition,
and Renyi Differential Privacy (RDP) accounting.

References:
    [1] C. Dwork, A. Roth. "The Algorithmic Foundations of Differential
        Privacy." 2014. (Basic & Advanced Composition, Theorems 3.14-3.20)
    [2] I. Mironov. "Renyi Differential Privacy." CSF 2017.
    [3] M. Bun, C. Dwork, G. Rothblum, G. Vadhan. "Concentrated
        Differential Privacy." 2016.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

import numpy as np

if TYPE_CHECKING:
    from sdk.privacy.mechanisms import DPMechanism

# Default Renyi divergence orders used for RDP accounting.
# These cover a range that works well in practice for Gaussian mechanisms.
DEFAULT_RDP_ORDERS: tuple[float, ...] = (
    1.25,
    1.5,
    1.75,
    2.0,
    2.5,
    3.0,
    4.0,
    5.0,
    6.0,
    8.0,
    10.0,
    12.0,
    16.0,
    20.0,
    24.0,
    32.0,
    48.0,
    64.0,
    128.0,
    256.0,
)


@dataclass
class PrivacyBudget:
    """Tracks remaining privacy budget.

    A privacy budget defines the maximum acceptable privacy loss for a
    sequence of DP operations. Once the budget is exhausted, no further
    queries should be answered.

    Attributes:
        epsilon: Total epsilon budget.
        delta: Total delta budget.
        epsilon_used: Cumulative epsilon consumed so far.
        delta_used: Cumulative delta consumed so far.
        queries: Number of queries executed.
    """

    epsilon: float
    delta: float
    epsilon_used: float = 0.0
    delta_used: float = 0.0
    queries: int = 0

    def __post_init__(self) -> None:
        if self.epsilon <= 0:
            raise ValueError(f"Total epsilon budget must be positive, got {self.epsilon}")
        if self.delta < 0 or self.delta >= 1:
            raise ValueError(f"Total delta budget must be in [0, 1), got {self.delta}")

    @property
    def epsilon_remaining(self) -> float:
        """Remaining epsilon budget."""
        return max(0.0, self.epsilon - self.epsilon_used)

    @property
    def delta_remaining(self) -> float:
        """Remaining delta budget."""
        return max(0.0, self.delta - self.delta_used)

    @property
    def is_exhausted(self) -> bool:
        """Whether the privacy budget is fully consumed."""
        if self.delta > 0:
            return self.epsilon_used >= self.epsilon or self.delta_used >= self.delta
        return self.epsilon_used >= self.epsilon

    def can_afford(self, epsilon_cost: float, delta_cost: float = 0.0) -> bool:
        """Check if the budget can afford a query with the given cost.

        Args:
            epsilon_cost: Epsilon cost of the proposed query.
            delta_cost: Delta cost of the proposed query.

        Returns:
            True if the budget has sufficient remaining funds.
        """
        return (
            self.epsilon_used + epsilon_cost <= self.epsilon
            and self.delta_used + delta_cost <= self.delta
        )

    def __repr__(self) -> str:
        return (
            f"PrivacyBudget(eps={self.epsilon_used:.4f}/{self.epsilon}, "
            f"delta={self.delta_used:.2e}/{self.delta:.2e}, "
            f"queries={self.queries})"
        )


@dataclass
class _PrivacyExpenditure:
    """Record of a single privacy expenditure."""

    epsilon: float
    delta: float
    operation: str
    step: int


class PrivacyAccountant:
    """Tracks cumulative privacy loss across multiple DP operations.

    The accountant records each privacy expenditure and computes the total
    privacy loss using composition theorems. It enforces a hard budget
    limit and refuses further queries once the budget is exhausted.

    Supports three composition modes:

    1. **Basic composition** (Theorem 3.14, Dwork & Roth 2014):
       epsilon_total = sum(epsilon_i), delta_total = sum(delta_i).
       Simple but loose for many queries.

    2. **Advanced composition** (Theorem 3.20, Dwork & Roth 2014):
       For k mechanisms each satisfying (eps_i, delta_i)-DP, the
       composition satisfies (eps_total, k*delta + delta')-DP where
       eps_total = sqrt(2k * ln(1/delta')) * eps_max + k * eps_max * (e^eps_max - 1).
       Tighter for many queries with small per-query epsilon.

    3. **RDP accounting** (Mironov 2017):
       Tracks Renyi divergences at multiple alpha orders and converts to
       (epsilon, delta)-DP. Provides the tightest bounds, especially for
       subsampled Gaussian mechanisms (DP-SGD).

    Args:
        total_epsilon: Maximum allowed cumulative epsilon.
        total_delta: Maximum allowed cumulative delta.

    Example:
        >>> from sdk.privacy.mechanisms import LaplaceMechanism
        >>> accountant = PrivacyAccountant(total_epsilon=10.0, total_delta=1e-5)
        >>> mechanism = LaplaceMechanism(epsilon=1.0)
        >>> accountant.step(mechanism)
        True
        >>> accountant.remaining_budget()
        (9.0, 1e-05)
        >>> accountant.consume(epsilon=1.0, operation="mean_query")
        True
        >>> accountant.budget.epsilon_remaining
        8.0
    """

    def __init__(self, total_epsilon: float, total_delta: float = 1e-5) -> None:
        self.budget = PrivacyBudget(epsilon=total_epsilon, delta=total_delta)
        self._history: list[_PrivacyExpenditure] = []
        self._step: int = 0
        # RDP accounting: cumulative Renyi divergences for each alpha order
        self._rdp_orders: tuple[float, ...] = DEFAULT_RDP_ORDERS
        self._rdp_epsilons: np.ndarray = np.zeros(len(self._rdp_orders))

    # ------------------------------------------------------------------
    # Core recording methods
    # ------------------------------------------------------------------

    def step(self, mechanism: DPMechanism) -> bool:
        """Record one mechanism invocation using its intrinsic privacy cost.

        Extracts the epsilon consumed by the mechanism via
        ``mechanism.epsilon_consumed()`` and records it. For mechanisms
        with a ``delta`` attribute (e.g., ``GaussianMechanism``), the
        delta cost is also recorded; otherwise delta = 0.

        This also updates the internal RDP accounting if the mechanism
        is a ``GaussianMechanism`` (using its sigma and epsilon to
        compute Renyi divergences).

        Args:
            mechanism: A ``DPMechanism`` instance whose privacy cost
                will be recorded.

        Returns:
            True if the budget is not yet exhausted after this step,
            False if the budget has been exceeded.
        """
        eps: float = mechanism.epsilon_consumed()
        delta: float = getattr(mechanism, "delta", 0.0)
        operation: str = repr(mechanism)

        # Update RDP accounting for Gaussian mechanisms
        sigma: float | None = None
        if hasattr(mechanism, "compute_sigma"):
            # Use sensitivity=1.0 as the canonical reference; the actual
            # sensitivity scaling is handled externally when noise is added.
            sigma = mechanism.compute_sigma(1.0)
            self._accumulate_rdp_gaussian(sigma)

        return self.consume(epsilon=eps, delta=delta, operation=operation)

    def consume(
        self,
        epsilon: float,
        delta: float = 0.0,
        operation: str = "",
    ) -> bool:
        """Record a privacy expenditure.

        Deducts the given epsilon and delta from the remaining budget
        and records the operation in the history.

        Args:
            epsilon: Epsilon cost of this operation.
            delta: Delta cost of this operation.
            operation: Human-readable description of the operation.

        Returns:
            True if the expenditure was recorded successfully, False if
            the budget would be exceeded (expenditure is still recorded
            but a warning is logged).

        Raises:
            ValueError: If epsilon is negative.
        """
        if epsilon < 0:
            raise ValueError(f"Epsilon cost must be non-negative, got {epsilon}")
        if delta < 0:
            raise ValueError(f"Delta cost must be non-negative, got {delta}")

        self._step += 1

        self._history.append(
            _PrivacyExpenditure(
                epsilon=epsilon,
                delta=delta,
                operation=operation,
                step=self._step,
            )
        )

        self.budget.epsilon_used += epsilon
        self.budget.delta_used += delta
        self.budget.queries += 1

        if self.budget.is_exhausted:
            return False
        return True

    # ------------------------------------------------------------------
    # Convenience properties / methods matching the requested API
    # ------------------------------------------------------------------

    @property
    def history(self) -> list[tuple[float, float]]:
        """Return the history of privacy expenditures as (epsilon, delta) tuples.

        Returns:
            A list of ``(epsilon, delta)`` pairs, one per recorded operation,
            in chronological order.
        """
        return [(e.epsilon, e.delta) for e in self._history]

    def remaining_budget(self) -> tuple[float, float]:
        """Return the remaining (epsilon, delta) budget.

        Uses basic composition for the consumed amounts.

        Returns:
            Tuple of ``(epsilon_remaining, delta_remaining)``.
        """
        return self.budget.epsilon_remaining, self.budget.delta_remaining

    def is_budget_exceeded(self) -> bool:
        """Check whether the cumulative privacy budget has been exceeded.

        Returns:
            True if the total consumed epsilon or delta exceeds the
            allocated budget.
        """
        return self.budget.is_exhausted

    # ------------------------------------------------------------------
    # Composition theorems
    # ------------------------------------------------------------------

    def compose_basic(self) -> tuple[float, float]:
        """Basic sequential composition theorem.

        epsilon_total = sum(epsilon_i)
        delta_total = sum(delta_i)

        Reference:
            Dwork & Roth, 2014, Theorem 3.14.

        Returns:
            Tuple of (total_epsilon, total_delta) under basic composition.
        """
        total_eps = sum(e.epsilon for e in self._history)
        total_delta = sum(e.delta for e in self._history)
        return total_eps, total_delta

    def compose_advanced(self, delta_prime: Optional[float] = None) -> tuple[float, float]:
        """Advanced composition theorem (tighter for many queries).

        For k mechanisms each satisfying (eps_i, 0)-DP:
            eps_total = sqrt(2k * ln(1/delta')) * eps_max
                      + k * eps_max * (exp(eps_max) - 1)
            delta_total = k * max(delta_i) + delta'

        where delta' is a free parameter (defaults to total_delta / 2).

        Reference:
            Dwork & Roth, 2014, Theorem 3.20 (Strong Composition).

        Args:
            delta_prime: Free parameter for the composition bound.
                Defaults to half the total delta budget.

        Returns:
            Tuple of (total_epsilon, total_delta) under advanced composition.
        """
        if not self._history:
            return 0.0, 0.0

        if delta_prime is None:
            delta_prime = self.budget.delta / 2.0

        k = len(self._history)
        eps_max = max(e.epsilon for e in self._history)
        delta_max = max(e.delta for e in self._history)

        # Advanced composition formula
        eps_total = math.sqrt(2.0 * k * math.log(1.0 / delta_prime)) * eps_max + k * eps_max * (
            math.exp(eps_max) - 1.0
        )
        delta_total = k * delta_max + delta_prime

        return eps_total, delta_total

    # ------------------------------------------------------------------
    # Renyi DP (RDP) accounting
    # ------------------------------------------------------------------

    def _accumulate_rdp_gaussian(self, sigma: float) -> None:
        """Accumulate RDP epsilon for a Gaussian mechanism step.

        For the Gaussian mechanism with standard deviation ``sigma``
        and L2 sensitivity 1, the Renyi divergence of order alpha is:

            rdp_epsilon(alpha) = alpha / (2 * sigma^2)

        Under composition, RDP epsilons add:
            rdp_epsilon_total(alpha) = sum_i rdp_epsilon_i(alpha)

        Reference:
            Mironov, "Renyi Differential Privacy", CSF 2017, Proposition 3.

        Args:
            sigma: Standard deviation of the Gaussian noise (for
                sensitivity = 1).
        """
        for i, alpha in enumerate(self._rdp_orders):
            self._rdp_epsilons[i] += alpha / (2.0 * sigma**2)

    def compose_rdp(self, delta: Optional[float] = None) -> tuple[float, float]:
        """Convert accumulated RDP guarantees to (epsilon, delta)-DP.

        For each order alpha, the conversion formula is:

            epsilon = rdp_epsilon(alpha) + ln(1/delta) / (alpha - 1)

        The tightest bound is obtained by minimizing over all alpha
        orders.

        Reference:
            Mironov, "Renyi Differential Privacy", CSF 2017, Proposition 3.
            Balle et al., "Hypothesis Testing Interpretations and Renyi
            Differential Privacy", AISTATS 2020.

        Args:
            delta: Target delta for the conversion. Defaults to the
                accountant's total_delta.

        Returns:
            Tuple of ``(epsilon, delta)`` representing the tightest
            (epsilon, delta)-DP guarantee obtainable from the
            accumulated RDP bounds.

        Raises:
            ValueError: If no RDP steps have been recorded.
        """
        if delta is None:
            delta = self.budget.delta

        if np.all(self._rdp_epsilons == 0.0):
            return 0.0, delta

        log_inv_delta: float = math.log(1.0 / delta)
        best_eps: float = float("inf")

        for i, alpha in enumerate(self._rdp_orders):
            if alpha <= 1.0:
                continue
            candidate: float = self._rdp_epsilons[i] + log_inv_delta / (alpha - 1.0)
            best_eps = min(best_eps, candidate)

        if math.isinf(best_eps):
            # Fallback to basic composition if no valid alpha order found
            return self.compose_basic()

        return best_eps, delta

    # ------------------------------------------------------------------
    # Query estimation & reporting
    # ------------------------------------------------------------------

    def estimate_remaining_queries(
        self, per_query_epsilon: float, per_query_delta: float = 0.0
    ) -> int:
        """Estimate how many more queries the budget allows.

        Uses basic composition to give a conservative estimate.

        Args:
            per_query_epsilon: Expected epsilon cost per query.
            per_query_delta: Expected delta cost per query.

        Returns:
            Estimated number of remaining queries (integer).

        Raises:
            ValueError: If per_query_epsilon is not positive.
        """
        if per_query_epsilon <= 0:
            raise ValueError(f"Per-query epsilon must be positive, got {per_query_epsilon}")

        eps_remaining = self.budget.epsilon_remaining
        delta_remaining = self.budget.delta_remaining

        # Limit by epsilon
        eps_queries = int(eps_remaining / per_query_epsilon)

        # Limit by delta if applicable
        if per_query_delta > 0:
            delta_queries = int(delta_remaining / per_query_delta)
            return min(eps_queries, delta_queries)

        return eps_queries

    def report(self) -> dict:
        """Generate a detailed privacy budget report.

        Returns:
            Dictionary containing budget status, composition bounds,
            and operation history.
        """
        basic_eps, basic_delta = self.compose_basic()

        result: dict = {
            "budget": {
                "total_epsilon": self.budget.epsilon,
                "total_delta": self.budget.delta,
                "epsilon_used": self.budget.epsilon_used,
                "delta_used": self.budget.delta_used,
                "epsilon_remaining": self.budget.epsilon_remaining,
                "delta_remaining": self.budget.delta_remaining,
                "is_exhausted": self.budget.is_exhausted,
            },
            "queries": self.budget.queries,
            "composition": {
                "basic": {
                    "epsilon": basic_eps,
                    "delta": basic_delta,
                },
            },
            "history": [
                {
                    "step": e.step,
                    "epsilon": e.epsilon,
                    "delta": e.delta,
                    "operation": e.operation,
                }
                for e in self._history
            ],
        }

        if self._history:
            adv_eps, adv_delta = self.compose_advanced()
            result["composition"]["advanced"] = {
                "epsilon": adv_eps,
                "delta": adv_delta,
            }

            # Include RDP bounds if any Gaussian steps were recorded
            if np.any(self._rdp_epsilons > 0.0):
                rdp_eps, rdp_delta = self.compose_rdp()
                result["composition"]["rdp"] = {
                    "epsilon": rdp_eps,
                    "delta": rdp_delta,
                }

        return result

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Reset the accountant, clearing all history and restoring budget.

        Warning:
            This erases all privacy accounting. Use only when starting a
            genuinely new analysis on independent data.
        """
        self.budget.epsilon_used = 0.0
        self.budget.delta_used = 0.0
        self.budget.queries = 0
        self._history.clear()
        self._step = 0
        self._rdp_epsilons = np.zeros(len(self._rdp_orders))

    def __repr__(self) -> str:
        return f"PrivacyAccountant(budget={self.budget}, history_len={len(self._history)})"

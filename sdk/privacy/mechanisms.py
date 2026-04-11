"""Core differential privacy mechanisms.

Implements the fundamental DP mechanisms from the literature:
- Laplace mechanism (Dwork, McSherry, Nissim, Smith, 2006)
- Gaussian mechanism (Dwork & Roth, "The Algorithmic Foundations of DP", 2014)
- Exponential mechanism (McSherry & Talwar, 2007)

References:
    [1] C. Dwork, F. McSherry, K. Nissim, A. Smith. "Calibrating Noise to
        Sensitivity in Private Data Analysis." TCC 2006.
    [2] C. Dwork, A. Roth. "The Algorithmic Foundations of Differential
        Privacy." Foundations and Trends in Theoretical Computer Science, 2014.
    [3] F. McSherry, K. Talwar. "Mechanism Design via Differential Privacy."
        FOCS 2007.
"""

import secrets
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

import numpy as np


def _crypto_rng() -> np.random.Generator:
    """Return a numpy Generator seeded from the OS CSPRNG."""
    return np.random.Generator(np.random.PCG64(secrets.randbits(128)))


class DPMechanism(ABC):
    """Abstract base for differential privacy mechanisms.

    A DP mechanism takes a true answer (or data) and returns a noisy version
    that satisfies a formal privacy guarantee. The noise is calibrated to the
    *sensitivity* of the computation -- the maximum change in output when a
    single individual's data is added or removed.

    Subclasses must implement:
        - ``add_noise``: inject calibrated noise into a numpy array.
        - ``epsilon_consumed``: report the privacy cost of one invocation.
    """

    @abstractmethod
    def add_noise(self, value: np.ndarray, sensitivity: float) -> np.ndarray:
        """Add calibrated noise to ``value``.

        Args:
            value: The true (non-private) result as a numpy array.
            sensitivity: The L1 or L2 sensitivity of the computation,
                depending on the mechanism.

        Returns:
            A noisy array with the same shape as ``value``.
        """
        ...

    @abstractmethod
    def epsilon_consumed(self) -> float:
        """Return the epsilon privacy cost of a single invocation.

        Returns:
            The epsilon consumed by one call to ``add_noise``.
        """
        ...

    def _validate_inputs(
        self, value: np.ndarray, sensitivity: float
    ) -> np.ndarray:
        """Validate and coerce inputs.

        Args:
            value: Input array (will be coerced to float64 if needed).
            sensitivity: Must be positive.

        Returns:
            The validated array as float64.

        Raises:
            ValueError: If sensitivity is non-positive or value is empty.
        """
        if sensitivity <= 0:
            raise ValueError(
                f"Sensitivity must be positive, got {sensitivity}"
            )
        arr = np.asarray(value, dtype=np.float64)
        if arr.size == 0:
            raise ValueError("Input array must not be empty")
        return arr


class LaplaceMechanism(DPMechanism):
    """Laplace mechanism for pure epsilon-differential privacy.

    Adds independent Lap(sensitivity / epsilon) noise to each element.

    This mechanism provides *pure* epsilon-DP (delta = 0) and is calibrated
    to the L1 sensitivity of the computation.

    Reference:
        Dwork et al., "Calibrating Noise to Sensitivity in Private Data
        Analysis", TCC 2006, Theorem 1.

    Args:
        epsilon: Privacy parameter (must be positive). Smaller values give
            stronger privacy but more noise.

    Raises:
        ValueError: If epsilon is not positive.

    Example:
        >>> mechanism = LaplaceMechanism(epsilon=1.0)
        >>> data = np.array([10.0, 20.0, 30.0])
        >>> noisy = mechanism.add_noise(data, sensitivity=1.0)
    """

    def __init__(self, epsilon: float) -> None:
        if epsilon <= 0:
            raise ValueError(f"Epsilon must be positive, got {epsilon}")
        self.epsilon: float = epsilon

    def add_noise(self, value: np.ndarray, sensitivity: float) -> np.ndarray:
        """Add Laplace noise calibrated to L1 sensitivity.

        The scale parameter b = sensitivity / epsilon. Each element receives
        independent Lap(0, b) noise.

        Args:
            value: True result array.
            sensitivity: L1 sensitivity of the computation.

        Returns:
            Noisy array of the same shape.
        """
        arr = self._validate_inputs(value, sensitivity)
        scale: float = sensitivity / self.epsilon
        noise = _crypto_rng().laplace(loc=0.0, scale=scale, size=arr.shape)
        return arr + noise

    def epsilon_consumed(self) -> float:
        """Return epsilon cost per invocation."""
        return self.epsilon

    def variance(self, sensitivity: float) -> float:
        """Compute the variance of the Laplace noise.

        Var(Lap(b)) = 2 * b^2 where b = sensitivity / epsilon.

        Args:
            sensitivity: L1 sensitivity.

        Returns:
            Noise variance.
        """
        b: float = sensitivity / self.epsilon
        return 2.0 * b ** 2

    def __repr__(self) -> str:
        return f"LaplaceMechanism(epsilon={self.epsilon})"


class GaussianMechanism(DPMechanism):
    """Gaussian mechanism for (epsilon, delta)-differential privacy.

    Adds N(0, sigma^2) noise where:
        sigma = sensitivity * sqrt(2 * ln(1.25 / delta)) / epsilon

    This mechanism provides *approximate* (epsilon, delta)-DP and is
    calibrated to the L2 sensitivity of the computation. It is generally
    preferred over Laplace for high-dimensional queries because Gaussian
    noise concentrates better in high dimensions.

    Requires epsilon < 1 for the standard calibration formula to hold
    (Theorem 3.22 in Dwork & Roth). For epsilon >= 1, the mechanism
    remains valid but the privacy guarantee is weaker.

    Reference:
        Dwork & Roth, "The Algorithmic Foundations of Differential Privacy",
        2014, Theorem 3.22 (Analytic Gaussian Mechanism).

    Args:
        epsilon: Privacy parameter (must be positive).
        delta: Failure probability (must be in (0, 1)).

    Raises:
        ValueError: If epsilon or delta are out of range.

    Example:
        >>> mechanism = GaussianMechanism(epsilon=1.0, delta=1e-5)
        >>> data = np.array([10.0, 20.0, 30.0])
        >>> noisy = mechanism.add_noise(data, sensitivity=1.0)
    """

    def __init__(self, epsilon: float, delta: float = 1e-5) -> None:
        if epsilon <= 0:
            raise ValueError(f"Epsilon must be positive, got {epsilon}")
        if not (0 < delta < 1):
            raise ValueError(f"Delta must be in (0, 1), got {delta}")
        self.epsilon: float = epsilon
        self.delta: float = delta

    def compute_sigma(self, sensitivity: float) -> float:
        """Compute the standard deviation of the Gaussian noise.

        sigma = sensitivity * sqrt(2 * ln(1.25 / delta)) / epsilon

        This is the standard calibration from Theorem 3.22 in Dwork & Roth
        (2014). It guarantees (epsilon, delta)-DP for the given sensitivity.

        Args:
            sensitivity: L2 sensitivity of the computation.

        Returns:
            Standard deviation sigma for the Gaussian noise.
        """
        return (
            sensitivity
            * np.sqrt(2.0 * np.log(1.25 / self.delta))
            / self.epsilon
        )

    def add_noise(self, value: np.ndarray, sensitivity: float) -> np.ndarray:
        """Add Gaussian noise calibrated to L2 sensitivity.

        Args:
            value: True result array.
            sensitivity: L2 sensitivity of the computation.

        Returns:
            Noisy array of the same shape.
        """
        arr = self._validate_inputs(value, sensitivity)
        sigma: float = self.compute_sigma(sensitivity)
        noise = _crypto_rng().normal(loc=0.0, scale=sigma, size=arr.shape)
        return arr + noise

    def epsilon_consumed(self) -> float:
        """Return epsilon cost per invocation."""
        return self.epsilon

    def variance(self, sensitivity: float) -> float:
        """Compute the variance of the Gaussian noise.

        Args:
            sensitivity: L2 sensitivity.

        Returns:
            Noise variance (sigma^2).
        """
        sigma: float = self.compute_sigma(sensitivity)
        return sigma ** 2

    def __repr__(self) -> str:
        return (
            f"GaussianMechanism(epsilon={self.epsilon}, delta={self.delta})"
        )


class ExponentialMechanism(DPMechanism):
    """Exponential mechanism for selecting from discrete options.

    Selects an option with probability proportional to:
        exp(epsilon * utility(option) / (2 * sensitivity))

    This is the canonical mechanism for non-numeric queries (e.g., selecting
    a category, choosing a model architecture). It satisfies pure
    epsilon-DP.

    Reference:
        McSherry & Talwar, "Mechanism Design via Differential Privacy",
        FOCS 2007, Theorem 6.

    Args:
        epsilon: Privacy parameter (must be positive).

    Raises:
        ValueError: If epsilon is not positive.

    Example:
        >>> mechanism = ExponentialMechanism(epsilon=1.0)
        >>> utilities = np.array([3.0, 1.0, 2.0])
        >>> selected = mechanism.select(utilities, sensitivity=1.0)
    """

    def __init__(self, epsilon: float) -> None:
        if epsilon <= 0:
            raise ValueError(f"Epsilon must be positive, got {epsilon}")
        self.epsilon: float = epsilon

    def select(self, utilities: np.ndarray, sensitivity: float) -> int:
        """Select an index with probability proportional to exp(eps*u / 2s).

        Args:
            utilities: Utility score for each option (higher is better).
            sensitivity: Maximum change in any utility when one individual's
                data changes.

        Returns:
            The selected index (integer).

        Raises:
            ValueError: If utilities is empty or sensitivity is non-positive.
        """
        utilities = np.asarray(utilities, dtype=np.float64)
        if utilities.size == 0:
            raise ValueError("Utilities array must not be empty")
        if sensitivity <= 0:
            raise ValueError(
                f"Sensitivity must be positive, got {sensitivity}"
            )

        # Compute log-probabilities with numerical stability
        scores = self.epsilon * utilities / (2.0 * sensitivity)
        scores = scores - scores.max()  # shift for numerical stability
        probs = np.exp(scores)
        probs = probs / probs.sum()

        return int(np.random.choice(len(utilities), p=probs))

    def add_noise(self, value: np.ndarray, sensitivity: float) -> np.ndarray:
        """Not applicable for the exponential mechanism.

        The exponential mechanism operates on discrete selections, not
        continuous values. Use ``select()`` instead.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError(
            "ExponentialMechanism uses select(), not add_noise(). "
            "Use select(utilities, sensitivity) for discrete selection."
        )

    def epsilon_consumed(self) -> float:
        """Return epsilon cost per invocation."""
        return self.epsilon

    def __repr__(self) -> str:
        return f"ExponentialMechanism(epsilon={self.epsilon})"


@dataclass
class NoiseCalibrator:
    """Utility class for computing optimal noise parameters.

    Provides static methods for calibrating noise to achieve desired
    privacy guarantees given data characteristics.
    """

    @staticmethod
    def laplace_scale(epsilon: float, sensitivity: float) -> float:
        """Compute Laplace scale parameter b = sensitivity / epsilon.

        Args:
            epsilon: Privacy parameter.
            sensitivity: L1 sensitivity.

        Returns:
            Scale parameter for Laplace distribution.
        """
        if epsilon <= 0:
            raise ValueError(f"Epsilon must be positive, got {epsilon}")
        if sensitivity <= 0:
            raise ValueError(
                f"Sensitivity must be positive, got {sensitivity}"
            )
        return sensitivity / epsilon

    @staticmethod
    def gaussian_sigma(
        epsilon: float, delta: float, sensitivity: float
    ) -> float:
        """Compute Gaussian sigma = sensitivity * sqrt(2*ln(1.25/delta)) / eps.

        Args:
            epsilon: Privacy parameter.
            delta: Failure probability.
            sensitivity: L2 sensitivity.

        Returns:
            Standard deviation for Gaussian noise.
        """
        if epsilon <= 0:
            raise ValueError(f"Epsilon must be positive, got {epsilon}")
        if not (0 < delta < 1):
            raise ValueError(f"Delta must be in (0, 1), got {delta}")
        if sensitivity <= 0:
            raise ValueError(
                f"Sensitivity must be positive, got {sensitivity}"
            )
        return sensitivity * np.sqrt(2.0 * np.log(1.25 / delta)) / epsilon

    @staticmethod
    def epsilon_from_sigma(
        sigma: float, delta: float, sensitivity: float
    ) -> float:
        """Compute epsilon given sigma, delta, and sensitivity.

        Inverse of the Gaussian calibration formula:
            epsilon = sensitivity * sqrt(2*ln(1.25/delta)) / sigma

        Args:
            sigma: Standard deviation of Gaussian noise.
            delta: Failure probability.
            sensitivity: L2 sensitivity.

        Returns:
            The epsilon achieved by the given noise level.
        """
        if sigma <= 0:
            raise ValueError(f"Sigma must be positive, got {sigma}")
        if not (0 < delta < 1):
            raise ValueError(f"Delta must be in (0, 1), got {delta}")
        if sensitivity <= 0:
            raise ValueError(
                f"Sensitivity must be positive, got {sensitivity}"
            )
        return sensitivity * np.sqrt(2.0 * np.log(1.25 / delta)) / sigma

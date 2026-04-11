"""Privacy-preserving data loader with differential privacy.

Applies calibrated DP noise to data *before* CKKS encryption, providing
defense in depth:

1. **DP layer**: Mathematical privacy guarantees (epsilon, delta bounds).
2. **FHE layer**: Data remains encrypted during computation (CKKS).
3. **Combined**: Even if the encryption is compromised, DP still protects
   individual records.

This module bridges the gap between the DP mechanisms in
``sdk.privacy.mechanisms`` and the FHE encryption in
``sdk.encryption.ckks_wrapper``.

Reference:
    C. Dwork, A. Roth. "The Algorithmic Foundations of Differential
    Privacy." Foundations and Trends in Theoretical Computer Science, 2014.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Union

import numpy as np
import pandas as pd

from .accountant import PrivacyAccountant
from .mechanisms import GaussianMechanism, LaplaceMechanism, DPMechanism

# Optional FHE dependencies -- the DP module works standalone with numpy,
# but gains CKKS encryption when the TenSEAL-backed modules are available.
try:
    from ..encryption.context_manager import CKKSParameters
    from ..encryption.ckks_wrapper import CKKSEncryptor
    from ..utils.data_loader import EncryptedDataset, SecureDataLoader

    _HAS_FHE = True
except (ImportError, ModuleNotFoundError):
    _HAS_FHE = False
    CKKSParameters = None  # type: ignore[assignment,misc]


@dataclass
class PrivateDataset:
    """Dataset with DP noise applied (plaintext, pre-encryption).

    Attributes:
        X: Feature matrix with DP noise applied.
        y: Target vector (optionally noised).
        n_features: Number of features.
        n_samples: Number of samples.
        feature_names: Column names from the original DataFrame.
        privacy_report: Summary of privacy budget consumption.
    """

    X: np.ndarray
    y: Optional[np.ndarray]
    n_features: int
    n_samples: int
    feature_names: list[str]
    privacy_report: dict = field(default_factory=dict)


class DPDataLoader:
    """Data loader that applies differential privacy before FHE encryption.

    Combines DP noise injection with optional CKKS encryption for defense
    in depth:

    1. **Clip** values to bound sensitivity (L2 norm clipping per row).
    2. **Add calibrated noise** per column using the chosen mechanism.
    3. **Track** privacy budget consumption via ``PrivacyAccountant``.
    4. **Encrypt** with CKKS (optional, requires TenSEAL).

    Together, DP + FHE ensure that:
    - DP guarantees mathematical privacy bounds per individual.
    - FHE ensures data stays encrypted during computation.
    - Even if FHE is broken, DP still protects individuals.

    Args:
        epsilon: Total privacy budget (epsilon).
        delta: Total privacy budget (delta). Only used with Gaussian
            mechanism.
        mechanism: Noise mechanism to use: ``"gaussian"`` or ``"laplace"``.
        clip_norm: Maximum L2 norm for row clipping (bounds sensitivity).
        ckks_params: Optional CKKS parameters for FHE encryption.

    Example:
        >>> loader = DPDataLoader(epsilon=1.0, delta=1e-5)
        >>> private_ds = loader.load_private(df, target_column="label")
        >>> print(loader.get_privacy_report())
    """

    def __init__(
        self,
        epsilon: float = 1.0,
        delta: float = 1e-5,
        mechanism: str = "gaussian",
        clip_norm: float = 1.0,
        ckks_params: Any = None,
    ) -> None:
        if epsilon <= 0:
            raise ValueError(f"Epsilon must be positive, got {epsilon}")
        if mechanism not in ("gaussian", "laplace"):
            raise ValueError(
                f"Mechanism must be 'gaussian' or 'laplace', got '{mechanism}'"
            )

        self.epsilon: float = epsilon
        self.delta: float = delta
        self.clip_norm: float = clip_norm
        self.mechanism_name: str = mechanism
        self.ckks_params = ckks_params

        self.accountant = PrivacyAccountant(
            total_epsilon=epsilon, total_delta=delta
        )

        if mechanism == "gaussian":
            self._mechanism: DPMechanism = GaussianMechanism(
                epsilon=epsilon, delta=delta
            )
        else:
            self._mechanism = LaplaceMechanism(epsilon=epsilon)

    def load_private(
        self,
        df: pd.DataFrame,
        target_column: Optional[str] = None,
        per_column_epsilon: Optional[float] = None,
        noise_target: bool = False,
    ) -> PrivateDataset:
        """Load data with DP noise applied.

        Steps:
            1. Separate features and target.
            2. Clip feature rows to bound sensitivity.
            3. Add calibrated noise per column.
            4. Track privacy budget consumption.

        Args:
            df: Input DataFrame.
            target_column: Name of the target column (excluded from
                features for noising unless ``noise_target=True``).
            per_column_epsilon: If provided, allocate this epsilon per
                column (total cost = per_column_epsilon * n_columns).
                If None, the total epsilon is split evenly across columns.
            noise_target: Whether to add noise to the target column too.

        Returns:
            PrivateDataset with noised features.

        Raises:
            ValueError: If the DataFrame is empty or budget is exhausted.
            RuntimeError: If the privacy budget would be exceeded.
        """
        if df.empty:
            raise ValueError("Input DataFrame must not be empty")

        # Separate features and target
        if target_column and target_column in df.columns:
            feature_cols = [c for c in df.columns if c != target_column]
            X = df[feature_cols].values.astype(np.float64)
            y = df[target_column].values.astype(np.float64)
        else:
            feature_cols = list(df.columns)
            X = df.values.astype(np.float64)
            y = None

        n_features = X.shape[1]

        # Compute per-column epsilon
        if per_column_epsilon is not None:
            col_epsilon = per_column_epsilon
        else:
            # Split total epsilon evenly across columns
            col_epsilon = self.epsilon / n_features

        # Check budget feasibility
        total_eps_needed = col_epsilon * n_features
        if noise_target and y is not None:
            total_eps_needed += col_epsilon

        if not self.accountant.budget.can_afford(total_eps_needed):
            raise RuntimeError(
                f"Privacy budget would be exceeded: need {total_eps_needed:.4f} "
                f"epsilon but only {self.accountant.budget.epsilon_remaining:.4f} "
                f"remaining."
            )

        # Clip rows to bound sensitivity
        X_clipped = self._clip_rows(X)

        # Compute sensitivity after clipping
        sensitivity = self.compute_sensitivity(X_clipped)

        # Add noise per column
        X_noised = np.empty_like(X_clipped)
        for col_idx in range(n_features):
            col_data = X_clipped[:, col_idx : col_idx + 1].flatten()

            # Create per-column mechanism with allocated epsilon
            if self.mechanism_name == "gaussian":
                col_mechanism = GaussianMechanism(
                    epsilon=col_epsilon, delta=self.delta / n_features
                )
            else:
                col_mechanism = LaplaceMechanism(epsilon=col_epsilon)

            X_noised[:, col_idx] = col_mechanism.add_noise(
                col_data, sensitivity=sensitivity
            )

            self.accountant.consume(
                epsilon=col_epsilon,
                delta=self.delta / n_features if self.mechanism_name == "gaussian" else 0.0,
                operation=f"noise_column_{feature_cols[col_idx]}",
            )

        # Optionally noise target
        y_result = y
        if noise_target and y is not None:
            if self.mechanism_name == "gaussian":
                target_mechanism = GaussianMechanism(
                    epsilon=col_epsilon, delta=self.delta / n_features
                )
            else:
                target_mechanism = LaplaceMechanism(epsilon=col_epsilon)

            y_sensitivity = self.clip_norm
            y_result = target_mechanism.add_noise(y, sensitivity=y_sensitivity)
            self.accountant.consume(
                epsilon=col_epsilon,
                delta=self.delta / n_features if self.mechanism_name == "gaussian" else 0.0,
                operation=f"noise_target_{target_column}",
            )

        return PrivateDataset(
            X=X_noised,
            y=y_result,
            n_features=n_features,
            n_samples=X_noised.shape[0],
            feature_names=feature_cols,
            privacy_report=self.accountant.report(),
        )

    def load_private_encrypted(
        self,
        df: pd.DataFrame,
        target_column: Optional[str] = None,
        per_column_epsilon: Optional[float] = None,
    ) -> Any:
        """Load data with DP noise, then encrypt with CKKS.

        This is the full defense-in-depth pipeline: DP noise first,
        then homomorphic encryption.

        Args:
            df: Input DataFrame.
            target_column: Target column name.
            per_column_epsilon: Optional per-column epsilon allocation.

        Returns:
            EncryptedDataset with DP noise and CKKS encryption.

        Raises:
            ImportError: If TenSEAL is not available.
        """
        if not _HAS_FHE:
            raise ImportError(
                "FHE encryption requires TenSEAL. "
                "Install with: pip install tenseal"
            )

        # Step 1: Apply DP noise
        private_ds = self.load_private(
            df,
            target_column=target_column,
            per_column_epsilon=per_column_epsilon,
        )

        # Step 2: Encrypt with CKKS
        params = self.ckks_params if self.ckks_params is not None else CKKSParameters()
        noised_df = pd.DataFrame(
            private_ds.X, columns=private_ds.feature_names
        )
        if private_ds.y is not None and target_column:
            noised_df[target_column] = private_ds.y

        loader = SecureDataLoader(params=params, normalize=True)
        return loader.encrypt(noised_df, target_column=target_column)

    def clip_and_noise(
        self, data: np.ndarray, sensitivity: float
    ) -> np.ndarray:
        """Clip values to bound sensitivity and add calibrated noise.

        Args:
            data: Input array.
            sensitivity: L2 sensitivity for noise calibration.

        Returns:
            Clipped and noised array.
        """
        clipped = self._clip_values(data)
        noised = self._mechanism.add_noise(clipped, sensitivity)
        self.accountant.consume(
            epsilon=self._mechanism.epsilon_consumed(),
            delta=self.delta if self.mechanism_name == "gaussian" else 0.0,
            operation="clip_and_noise",
        )
        return noised

    def compute_sensitivity(self, data: np.ndarray) -> float:
        """Compute L2 sensitivity of the data after clipping.

        For a dataset with rows clipped to L2 norm <= clip_norm, the
        sensitivity of the mean is clip_norm / n_samples.

        For raw data (non-aggregated), the sensitivity equals the
        clip_norm itself.

        Args:
            data: Input array (already clipped).

        Returns:
            L2 sensitivity as a float.
        """
        if data.ndim == 1:
            return self.clip_norm
        # Sensitivity of mean query on clipped data
        return self.clip_norm / data.shape[0]

    def private_mean(self, data: np.ndarray) -> np.ndarray:
        """Compute differentially private mean.

        Computes the mean of clipped data and adds calibrated noise.
        The sensitivity of the mean on n rows clipped to norm C is C/n.

        Args:
            data: Input array of shape (n_samples,) or (n_samples, n_features).

        Returns:
            DP mean as a numpy array.
        """
        data = np.asarray(data, dtype=np.float64)

        if data.ndim == 1:
            data = data.reshape(-1, 1)

        clipped = self._clip_rows(data)
        n_samples = clipped.shape[0]
        true_mean = clipped.mean(axis=0)

        # Sensitivity of mean with clipped rows
        sensitivity = self.clip_norm / n_samples

        noisy_mean = self._mechanism.add_noise(true_mean, sensitivity)
        self.accountant.consume(
            epsilon=self._mechanism.epsilon_consumed(),
            delta=self.delta if self.mechanism_name == "gaussian" else 0.0,
            operation="private_mean",
        )
        return noisy_mean

    def private_histogram(
        self,
        data: np.ndarray,
        bins: int = 10,
        data_range: Optional[tuple[float, float]] = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Compute differentially private histogram.

        Each individual contributes to at most one bin, so the
        sensitivity is 1. We add noise to each bin count.

        Args:
            data: 1-D input array.
            bins: Number of histogram bins.
            data_range: Optional (min, max) range for binning. If None,
                derived from data (which leaks information -- consider
                setting this explicitly for strong privacy).

        Returns:
            Tuple of (noisy_counts, bin_edges).
        """
        data = np.asarray(data, dtype=np.float64).ravel()

        if data_range is not None:
            counts, bin_edges = np.histogram(
                data, bins=bins, range=data_range
            )
        else:
            counts, bin_edges = np.histogram(data, bins=bins)

        counts = counts.astype(np.float64)

        # Sensitivity of a histogram is 1 (each person in one bin)
        sensitivity = 1.0
        noisy_counts = self._mechanism.add_noise(counts, sensitivity)

        # Clamp to non-negative
        noisy_counts = np.maximum(noisy_counts, 0.0)

        self.accountant.consume(
            epsilon=self._mechanism.epsilon_consumed(),
            delta=self.delta if self.mechanism_name == "gaussian" else 0.0,
            operation="private_histogram",
        )

        return noisy_counts, bin_edges

    def get_privacy_report(self) -> dict:
        """Get report of privacy budget usage.

        Returns:
            Dictionary with budget status, composition bounds, and
            operation history.
        """
        return self.accountant.report()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _clip_rows(self, data: np.ndarray) -> np.ndarray:
        """Clip each row to have L2 norm <= clip_norm.

        Args:
            data: Input matrix of shape (n_samples, n_features).

        Returns:
            Clipped matrix with same shape.
        """
        norms = np.linalg.norm(data, axis=1, keepdims=True)
        # Avoid division by zero
        norms = np.maximum(norms, 1e-12)
        scale = np.minimum(1.0, self.clip_norm / norms)
        return data * scale

    def _clip_values(self, data: np.ndarray) -> np.ndarray:
        """Clip individual values to [-clip_norm, clip_norm].

        Args:
            data: Input array.

        Returns:
            Clipped array.
        """
        return np.clip(data, -self.clip_norm, self.clip_norm)

    # ------------------------------------------------------------------
    # Convenience methods matching the canonical API
    # ------------------------------------------------------------------

    def privatize_features(
        self,
        X: np.ndarray,
        clip_norm: float | None = None,
    ) -> np.ndarray:
        """Clip features then add calibrated DP noise.

        Each row of ``X`` is first clipped to the given L2 norm bound so
        that the sensitivity of the aggregation is bounded.  Calibrated
        noise is then added element-wise.

        Args:
            X: Feature matrix of shape ``(n_samples, n_features)``.
            clip_norm: Per-row L2 clipping bound.  Defaults to
                ``self.clip_norm``.

        Returns:
            Noisy feature matrix of the same shape.
        """
        X = np.asarray(X, dtype=np.float64)
        effective_clip: float = clip_norm if clip_norm is not None else self.clip_norm

        # Save / restore clip_norm so the internal helper sees the right value
        original_clip = self.clip_norm
        self.clip_norm = effective_clip
        try:
            X_clipped = self._clip_rows(X)
            sensitivity = self.compute_sensitivity(X_clipped)
            X_noised = self._mechanism.add_noise(X_clipped, sensitivity)
            self.accountant.consume(
                epsilon=self._mechanism.epsilon_consumed(),
                delta=self.delta if self.mechanism_name == "gaussian" else 0.0,
                operation="privatize_features",
            )
            return X_noised
        finally:
            self.clip_norm = original_clip

    def privatize_labels(
        self,
        y: np.ndarray,
        sensitivity: float = 1.0,
    ) -> np.ndarray:
        """Add calibrated DP noise to labels / targets.

        Args:
            y: Target array of shape ``(n_samples,)`` or ``(n_samples, 1)``.
            sensitivity: Sensitivity of the label query.

        Returns:
            Noisy target array of the same shape.
        """
        y = np.asarray(y, dtype=np.float64)
        y_noised = self._mechanism.add_noise(y, sensitivity)
        self.accountant.consume(
            epsilon=self._mechanism.epsilon_consumed(),
            delta=self.delta if self.mechanism_name == "gaussian" else 0.0,
            operation="privatize_labels",
        )
        return y_noised

    def privatize_dataset(
        self,
        X: np.ndarray,
        y: np.ndarray,
        clip_norm: float | None = None,
        label_sensitivity: float = 1.0,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Privatize both features and labels in one call.

        Equivalent to calling :meth:`privatize_features` followed by
        :meth:`privatize_labels`.

        Args:
            X: Feature matrix.
            y: Target array.
            clip_norm: Per-row L2 clipping bound for features.
            label_sensitivity: Sensitivity for the label noise.

        Returns:
            Tuple of ``(X_noised, y_noised)``.
        """
        X_noised = self.privatize_features(X, clip_norm=clip_norm)
        y_noised = self.privatize_labels(y, sensitivity=label_sensitivity)
        return X_noised, y_noised

    def __repr__(self) -> str:
        return (
            f"DPDataLoader(epsilon={self.epsilon}, delta={self.delta}, "
            f"mechanism={self.mechanism_name!r}, clip_norm={self.clip_norm})"
        )


class SubsampledMechanism:
    """Privacy amplification by subsampling.

    When a DP mechanism is applied to a random subsample of the dataset
    rather than the full dataset, the effective privacy cost is reduced.
    This is the *privacy amplification lemma* (Balle et al., 2018;
    Kasiviswanathan et al., 2011).

    For a mechanism satisfying (epsilon, delta)-DP and a Poisson
    subsampling rate ``q``, the composed mechanism satisfies approximately
    (epsilon', delta')-DP where:

        epsilon' = ln(1 + q * (exp(epsilon) - 1))

    This is tighter than simply scaling epsilon by q, especially for
    small epsilon.

    Reference:
        B. Balle, G. Barthe, M. Gaboardi. "Privacy Amplification by
        Subsampling: Tight Analyses via Couplings." NeurIPS 2018.

    Args:
        mechanism: The base DP mechanism to subsample.
        sampling_rate: Probability that each record is included in the
            subsample.  Must be in (0, 1].

    Raises:
        ValueError: If sampling_rate is out of range.

    Example:
        >>> from sdk.privacy.mechanisms import GaussianMechanism
        >>> base = GaussianMechanism(epsilon=1.0, delta=1e-5)
        >>> subsampled = SubsampledMechanism(base, sampling_rate=0.01)
        >>> subsampled.effective_epsilon()  # Much smaller than 1.0
    """

    def __init__(
        self,
        mechanism: DPMechanism,
        sampling_rate: float,
    ) -> None:
        if not (0.0 < sampling_rate <= 1.0):
            raise ValueError(
                f"sampling_rate must be in (0, 1], got {sampling_rate}"
            )
        self.mechanism: DPMechanism = mechanism
        self.sampling_rate: float = sampling_rate

    def effective_epsilon(self) -> float:
        """Compute the amplified epsilon under Poisson subsampling.

        Uses the tight bound from Balle et al. (2018):

            epsilon' = ln(1 + q * (exp(eps) - 1))

        where ``q`` is the sampling rate and ``eps`` is the base
        mechanism's epsilon.

        Returns:
            The amplified (reduced) epsilon.
        """
        eps: float = self.mechanism.epsilon_consumed()
        q: float = self.sampling_rate
        return float(np.log(1.0 + q * (np.exp(eps) - 1.0)))

    def add_noise(
        self,
        value: np.ndarray,
        sensitivity: float,
    ) -> np.ndarray:
        """Add noise using the base mechanism with amplified privacy.

        The noise injection itself is identical to the base mechanism;
        the privacy *guarantee* is tighter because only a subsample of
        the data is used.

        Args:
            value: True result array.
            sensitivity: Sensitivity of the computation.

        Returns:
            Noisy array of the same shape as ``value``.
        """
        return self.mechanism.add_noise(value, sensitivity)

    def __repr__(self) -> str:
        return (
            f"SubsampledMechanism("
            f"mechanism={self.mechanism!r}, "
            f"sampling_rate={self.sampling_rate})"
        )

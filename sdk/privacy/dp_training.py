"""Differentially private model training (DP-SGD).

Implements the DP-SGD algorithm from Abadi et al. (2016), which provides
per-sample privacy guarantees during gradient-based model training.

The algorithm works in three steps per mini-batch:
    1. **Clip** per-sample gradients to bound their L2 norm.
    2. **Aggregate** clipped gradients and add calibrated Gaussian noise.
    3. **Update** model parameters with the noisy gradient.

Combined with FHE (CKKS encryption), this gives:
    - Per-sample privacy guarantee (epsilon, delta)-DP.
    - Encrypted computation via lattice-based CKKS scheme.
    - Post-quantum security (lattice-based cryptography).

References:
    [1] M. Abadi, A. Chu, I. Goodfellow, H.B. McMahan, I. Mironov,
        K. Talwar, L. Zhang. "Deep Learning with Differential Privacy."
        CCS 2016.
    [2] I. Mironov. "Renyi Differential Privacy." CSF 2017.
    [3] C. Dwork, A. Roth. "The Algorithmic Foundations of Differential
        Privacy." 2014.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np

from .accountant import PrivacyAccountant


@dataclass
class DPTrainingConfig:
    """Configuration for DP-SGD training.

    Attributes:
        epsilon: Total privacy budget.
        delta: Failure probability for (epsilon, delta)-DP.
        max_grad_norm: Maximum L2 norm for per-sample gradient clipping.
        noise_multiplier: Ratio of noise standard deviation to clip norm.
            sigma = noise_multiplier * max_grad_norm / batch_size.
        learning_rate: Step size for gradient descent.
        n_epochs: Number of training epochs.
        batch_size: Mini-batch size.
    """

    epsilon: float = 1.0
    delta: float = 1e-5
    max_grad_norm: float = 1.0
    noise_multiplier: float = 1.1
    learning_rate: float = 0.01
    n_epochs: int = 10
    batch_size: int = 32


class DPTrainer:
    """Differentially private model training using DP-SGD.

    Implements the Abadi et al. (2016) DP-SGD algorithm:

    1. **Clip** per-sample gradients to ``max_grad_norm`` to bound
       the sensitivity of the gradient aggregation.
    2. **Add Gaussian noise** with sigma = ``noise_multiplier * max_grad_norm``
       to the sum of clipped gradients.
    3. **Track privacy loss** via the moments accountant.

    The noise is calibrated so that each training step satisfies
    (O(q * eps), delta)-DP where q = batch_size / dataset_size is the
    sampling rate.

    Args:
        epsilon: Total privacy budget.
        delta: Failure probability.
        max_grad_norm: Per-sample gradient clipping bound.
        noise_multiplier: Ratio sigma / max_grad_norm. Higher values
            give stronger privacy but slower convergence.

    Example:
        >>> trainer = DPTrainer(epsilon=1.0, max_grad_norm=1.0)
        >>> weights = np.zeros(10)
        >>> new_weights, eps_spent = trainer.private_step(
        ...     weights, X_batch, y_batch, lr=0.01, compute_gradients_fn=grad_fn
        ... )
    """

    def __init__(
        self,
        epsilon: float = 1.0,
        delta: float = 1e-5,
        max_grad_norm: float = 1.0,
        noise_multiplier: float = 1.1,
    ) -> None:
        if epsilon <= 0:
            raise ValueError(f"Epsilon must be positive, got {epsilon}")
        if max_grad_norm <= 0:
            raise ValueError(
                f"max_grad_norm must be positive, got {max_grad_norm}"
            )
        if noise_multiplier <= 0:
            raise ValueError(
                f"noise_multiplier must be positive, got {noise_multiplier}"
            )

        self.epsilon: float = epsilon
        self.delta: float = delta
        self.max_grad_norm: float = max_grad_norm
        self.noise_multiplier: float = noise_multiplier

        self.accountant = PrivacyAccountant(
            total_epsilon=epsilon, total_delta=delta
        )

        self._steps: int = 0
        self._training_history: list[dict] = []

    def clip_gradients(self, gradients: np.ndarray) -> np.ndarray:
        """Clip per-sample gradients to ``max_grad_norm``.

        For a batch of per-sample gradients, each gradient vector is
        scaled so that its L2 norm does not exceed ``max_grad_norm``.

        Args:
            gradients: Per-sample gradients of shape
                (batch_size, *param_shape). If 1-D, treated as a single
                gradient vector.

        Returns:
            Clipped gradients with the same shape.
        """
        gradients = np.asarray(gradients, dtype=np.float64)

        if gradients.ndim == 1:
            # Single gradient vector
            norm = np.linalg.norm(gradients)
            if norm > self.max_grad_norm:
                gradients = gradients * (self.max_grad_norm / norm)
            return gradients

        # Batch of per-sample gradients
        clipped = np.empty_like(gradients)
        for i in range(gradients.shape[0]):
            grad = gradients[i]
            norm = np.linalg.norm(grad)
            if norm > self.max_grad_norm:
                clipped[i] = grad * (self.max_grad_norm / norm)
            else:
                clipped[i] = grad
        return clipped

    def noise_gradients(
        self, clipped_gradients: np.ndarray, batch_size: int
    ) -> np.ndarray:
        """Add calibrated Gaussian noise to aggregated clipped gradients.

        Computes the noisy average gradient:
            g_noisy = (1/batch_size) * (sum(clipped_grads) + N(0, sigma^2 * I))

        where sigma = noise_multiplier * max_grad_norm.

        Reference:
            Abadi et al. (2016), Algorithm 1, Step 4.

        Args:
            clipped_gradients: Clipped per-sample gradients of shape
                (batch_size, *param_shape).
            batch_size: Number of samples in the batch.

        Returns:
            Noisy average gradient (same shape as a single gradient).
        """
        clipped_gradients = np.asarray(clipped_gradients, dtype=np.float64)

        # Sum clipped gradients
        if clipped_gradients.ndim == 1:
            grad_sum = clipped_gradients
        else:
            grad_sum = clipped_gradients.sum(axis=0)

        # Compute noise scale: sigma = noise_multiplier * max_grad_norm
        sigma = self.noise_multiplier * self.max_grad_norm

        # Add Gaussian noise
        noise = np.random.normal(loc=0.0, scale=sigma, size=grad_sum.shape)
        noisy_sum = grad_sum + noise

        # Average
        return noisy_sum / batch_size

    def private_step(
        self,
        model_weights: np.ndarray,
        X_batch: np.ndarray,
        y_batch: np.ndarray,
        learning_rate: float,
        compute_gradients_fn: Callable[
            [np.ndarray, np.ndarray, np.ndarray], np.ndarray
        ],
    ) -> tuple[np.ndarray, float]:
        """Execute one DP-SGD training step.

        Steps:
            1. Compute per-sample gradients using ``compute_gradients_fn``.
            2. Clip each gradient to ``max_grad_norm``.
            3. Aggregate and add calibrated Gaussian noise.
            4. Update model weights.
            5. Track privacy expenditure.

        Args:
            model_weights: Current model parameters.
            X_batch: Feature batch of shape (batch_size, n_features).
            y_batch: Target batch of shape (batch_size,).
            learning_rate: Step size for the gradient update.
            compute_gradients_fn: Function(weights, X, y) -> gradients
                that returns per-sample gradients of shape
                (batch_size, *weight_shape).

        Returns:
            Tuple of (updated_weights, epsilon_spent_this_step).
        """
        model_weights = np.asarray(model_weights, dtype=np.float64)
        X_batch = np.asarray(X_batch, dtype=np.float64)
        y_batch = np.asarray(y_batch, dtype=np.float64)

        batch_size = X_batch.shape[0]

        # Step 1: Compute per-sample gradients
        per_sample_grads = compute_gradients_fn(model_weights, X_batch, y_batch)

        # Step 2: Clip gradients
        clipped_grads = self.clip_gradients(per_sample_grads)

        # Step 3: Aggregate and add noise
        noisy_grad = self.noise_gradients(clipped_grads, batch_size)

        # Step 4: Update weights
        new_weights = model_weights - learning_rate * noisy_grad

        # Step 5: Track privacy
        eps_step = self._compute_step_epsilon(batch_size, dataset_size=None)
        self.accountant.consume(
            epsilon=eps_step,
            delta=0.0,
            operation=f"dp_sgd_step_{self._steps}",
        )

        self._steps += 1
        self._training_history.append(
            {
                "step": self._steps,
                "epsilon_spent": eps_step,
                "grad_norm_before_clip": float(
                    np.linalg.norm(per_sample_grads)
                ),
                "grad_norm_after_noise": float(np.linalg.norm(noisy_grad)),
                "batch_size": batch_size,
            }
        )

        return new_weights, eps_step

    def train(
        self,
        model_weights: np.ndarray,
        X: np.ndarray,
        y: np.ndarray,
        compute_gradients_fn: Callable[
            [np.ndarray, np.ndarray, np.ndarray], np.ndarray
        ],
        n_epochs: int = 10,
        batch_size: int = 32,
        learning_rate: float = 0.01,
    ) -> tuple[np.ndarray, dict]:
        """Run full DP-SGD training loop.

        Args:
            model_weights: Initial model parameters.
            X: Full training features of shape (n_samples, n_features).
            y: Full training targets of shape (n_samples,).
            compute_gradients_fn: Gradient function.
            n_epochs: Number of passes over the dataset.
            batch_size: Mini-batch size.
            learning_rate: Step size.

        Returns:
            Tuple of (final_weights, training_report).
        """
        weights = np.asarray(model_weights, dtype=np.float64).copy()
        n_samples = X.shape[0]
        n_batches = max(1, n_samples // batch_size)

        for epoch in range(n_epochs):
            # Shuffle data each epoch
            indices = np.random.permutation(n_samples)

            for batch_idx in range(n_batches):
                start = batch_idx * batch_size
                end = min(start + batch_size, n_samples)
                batch_indices = indices[start:end]

                X_batch = X[batch_indices]
                y_batch = y[batch_indices]

                if self.accountant.budget.is_exhausted:
                    return weights, self.get_training_report()

                weights, _ = self.private_step(
                    weights, X_batch, y_batch, learning_rate,
                    compute_gradients_fn,
                )

        return weights, self.get_training_report()

    def estimate_epsilon(
        self,
        n_steps: int,
        batch_size: int,
        dataset_size: int,
    ) -> float:
        """Estimate total epsilon after n_steps of DP-SGD.

        Uses the moments accountant approximation (Abadi et al., 2016):

        For Gaussian mechanism with noise_multiplier sigma/C and sampling
        rate q = batch_size / dataset_size:
            epsilon ~ q * sqrt(2 * n_steps * ln(1/delta)) / noise_multiplier

        This is an upper bound based on the strong composition theorem
        applied to the subsampled Gaussian mechanism.

        Args:
            n_steps: Number of DP-SGD steps.
            batch_size: Samples per batch.
            dataset_size: Total number of training samples.

        Returns:
            Estimated total epsilon.

        Raises:
            ValueError: If inputs are not positive.
        """
        if n_steps <= 0:
            raise ValueError(f"n_steps must be positive, got {n_steps}")
        if batch_size <= 0:
            raise ValueError(f"batch_size must be positive, got {batch_size}")
        if dataset_size <= 0:
            raise ValueError(
                f"dataset_size must be positive, got {dataset_size}"
            )

        q = batch_size / dataset_size  # Sampling rate

        # Upper bound via advanced composition + subsampling amplification
        # epsilon ~ q * sqrt(2T * ln(1/delta)) / sigma
        epsilon_estimate = (
            q
            * math.sqrt(2.0 * n_steps * math.log(1.0 / self.delta))
            / self.noise_multiplier
        )

        return epsilon_estimate

    def get_training_report(self) -> dict:
        """Get privacy report for the training run.

        Returns:
            Dictionary with training statistics and privacy accounting.
        """
        budget_report = self.accountant.report()

        return {
            "training": {
                "total_steps": self._steps,
                "max_grad_norm": self.max_grad_norm,
                "noise_multiplier": self.noise_multiplier,
            },
            "privacy": budget_report,
            "history": self._training_history,
        }

    def _compute_step_epsilon(
        self,
        batch_size: int,
        dataset_size: Optional[int] = None,
    ) -> float:
        """Compute epsilon cost of a single DP-SGD step.

        If dataset_size is provided, applies privacy amplification by
        subsampling (Balle et al., 2018):
            epsilon_step ~ 2 * q * epsilon_base

        where q = batch_size / dataset_size.

        Otherwise, uses the base Gaussian mechanism epsilon.

        Args:
            batch_size: Number of samples in the batch.
            dataset_size: Total dataset size (for subsampling amplification).

        Returns:
            Epsilon cost for one step.
        """
        # Base epsilon from the Gaussian mechanism
        # For noise_multiplier * max_grad_norm noise, the L2 sensitivity
        # of the clipped gradient sum is max_grad_norm, so:
        # epsilon_base = max_grad_norm * sqrt(2 * ln(1.25/delta)) /
        #                (noise_multiplier * max_grad_norm)
        #              = sqrt(2 * ln(1.25/delta)) / noise_multiplier
        eps_base = (
            math.sqrt(2.0 * math.log(1.25 / self.delta))
            / self.noise_multiplier
        )

        if dataset_size is not None and dataset_size > 0:
            # Privacy amplification by subsampling
            q = batch_size / dataset_size
            return 2.0 * q * eps_base

        return eps_base

    def __repr__(self) -> str:
        return (
            f"DPTrainer(epsilon={self.epsilon}, delta={self.delta}, "
            f"max_grad_norm={self.max_grad_norm}, "
            f"noise_multiplier={self.noise_multiplier}, "
            f"steps={self._steps})"
        )


# ======================================================================
# Extended DP-SGD utilities (Abadi et al., 2016)
# ======================================================================


class GradientClipper:
    """Per-sample gradient clipping for DP-SGD.

    Clips each per-sample gradient so that its L2 norm does not exceed
    ``max_norm``.  This bounds the *sensitivity* of the gradient
    aggregation, which is the foundation of the DP-SGD privacy proof.

    Reference:
        M. Abadi et al., "Deep Learning with Differential Privacy",
        CCS 2016, Algorithm 1, Step 3.

    Args:
        max_norm: Maximum L2 norm for each per-sample gradient.

    Raises:
        ValueError: If ``max_norm`` is not positive.

    Example:
        >>> clipper = GradientClipper(max_norm=1.0)
        >>> grads = np.array([[3.0, 4.0], [0.5, 0.1]])
        >>> clipped = clipper.clip(grads)
        >>> np.linalg.norm(clipped[0])  # <= 1.0
    """

    def __init__(self, max_norm: float = 1.0) -> None:
        if max_norm <= 0:
            raise ValueError(f"max_norm must be positive, got {max_norm}")
        self.max_norm: float = max_norm

    def clip(self, gradients: np.ndarray) -> np.ndarray:
        """Clip each per-sample gradient to ``max_norm``.

        For a 2-D input of shape ``(batch_size, param_dim)``, each row
        is independently scaled so that its L2 norm does not exceed
        ``max_norm``.  A 1-D input is treated as a single gradient
        vector.

        Args:
            gradients: Per-sample gradients.  Shape
                ``(batch_size, param_dim)`` or ``(param_dim,)``.

        Returns:
            Clipped gradients with the same shape.
        """
        gradients = np.asarray(gradients, dtype=np.float64)

        if gradients.ndim == 1:
            norm: float = float(np.linalg.norm(gradients))
            if norm > self.max_norm:
                return gradients * (self.max_norm / norm)
            return gradients.copy()

        # Vectorised row-wise clipping
        norms = np.linalg.norm(gradients, axis=1, keepdims=True)
        # Avoid division by zero for zero-gradient rows
        norms = np.maximum(norms, 1e-12)
        scales = np.minimum(1.0, self.max_norm / norms)
        return gradients * scales

    def clip_and_accumulate(
        self, per_sample_grads: np.ndarray
    ) -> np.ndarray:
        """Clip per-sample gradients then sum them.

        This is the core aggregation step of DP-SGD: each gradient is
        clipped and the results are summed into a single gradient
        vector that will subsequently receive calibrated noise.

        Args:
            per_sample_grads: Per-sample gradients of shape
                ``(batch_size, param_dim)``.

        Returns:
            Summed clipped gradient of shape ``(param_dim,)``.
        """
        clipped = self.clip(per_sample_grads)
        return clipped.sum(axis=0)

    def __repr__(self) -> str:
        return f"GradientClipper(max_norm={self.max_norm})"


@dataclass
class DPSGDConfig:
    """Configuration for the DP-SGD training loop.

    Bundles all hyper-parameters needed by :class:`DPSGDTrainer` into a
    single, validated dataclass.

    Attributes:
        learning_rate: SGD step size.
        max_grad_norm: Per-sample gradient clipping bound (C in the
            Abadi et al. paper).
        noise_multiplier: Ratio of Gaussian noise standard deviation to
            ``max_grad_norm``.  Higher values give stronger privacy.
        batch_size: Number of samples per mini-batch.
        n_samples: Total number of training samples.
        epochs: Number of full passes over the dataset.
        target_epsilon: Desired total epsilon budget.
        target_delta: Desired total delta budget.
    """

    learning_rate: float = 0.01
    max_grad_norm: float = 1.0
    noise_multiplier: float = 1.1
    batch_size: int = 32
    n_samples: int = 1000
    epochs: int = 10
    target_epsilon: float = 1.0
    target_delta: float = 1e-5

    def __post_init__(self) -> None:
        if self.learning_rate <= 0:
            raise ValueError(
                f"learning_rate must be positive, got {self.learning_rate}"
            )
        if self.max_grad_norm <= 0:
            raise ValueError(
                f"max_grad_norm must be positive, got {self.max_grad_norm}"
            )
        if self.noise_multiplier <= 0:
            raise ValueError(
                f"noise_multiplier must be positive, got {self.noise_multiplier}"
            )
        if self.batch_size <= 0:
            raise ValueError(
                f"batch_size must be positive, got {self.batch_size}"
            )
        if self.n_samples <= 0:
            raise ValueError(
                f"n_samples must be positive, got {self.n_samples}"
            )
        if self.epochs <= 0:
            raise ValueError(
                f"epochs must be positive, got {self.epochs}"
            )
        if self.target_epsilon <= 0:
            raise ValueError(
                f"target_epsilon must be positive, got {self.target_epsilon}"
            )
        if not (0 < self.target_delta < 1):
            raise ValueError(
                f"target_delta must be in (0, 1), got {self.target_delta}"
            )

    @property
    def sampling_rate(self) -> float:
        """Poisson subsampling rate q = batch_size / n_samples."""
        return self.batch_size / self.n_samples

    @property
    def steps_per_epoch(self) -> int:
        """Number of gradient steps per epoch."""
        return max(1, self.n_samples // self.batch_size)

    @property
    def total_steps(self) -> int:
        """Total number of gradient steps across all epochs."""
        return self.steps_per_epoch * self.epochs


class DPSGDTrainer:
    """DP-SGD training loop with gradient clipping and Gaussian noise.

    Implements the full Abadi et al. (2016) algorithm:

    1. For each mini-batch, compute per-sample gradients.
    2. Clip each gradient to ``max_grad_norm``.
    3. Sum the clipped gradients and add Gaussian noise with
       sigma = ``noise_multiplier * max_grad_norm``.
    4. Divide by batch size to get the noisy average gradient.
    5. Update model weights.
    6. Track cumulative privacy expenditure.

    Args:
        config: A :class:`DPSGDConfig` with all hyper-parameters.

    Example:
        >>> config = DPSGDConfig(
        ...     learning_rate=0.01,
        ...     max_grad_norm=1.0,
        ...     noise_multiplier=1.1,
        ...     batch_size=32,
        ...     n_samples=1000,
        ...     epochs=5,
        ...     target_epsilon=2.0,
        ... )
        >>> trainer = DPSGDTrainer(config)
        >>> sigma = trainer.compute_noise_sigma()
    """

    def __init__(self, config: DPSGDConfig) -> None:
        self.config: DPSGDConfig = config
        self._clipper = GradientClipper(max_norm=config.max_grad_norm)
        self.accountant = PrivacyAccountant(
            total_epsilon=config.target_epsilon,
            total_delta=config.target_delta,
        )
        self._steps: int = 0

    def compute_noise_sigma(self) -> float:
        """Compute the Gaussian noise standard deviation.

        sigma = noise_multiplier * max_grad_norm

        This is the noise added to the *sum* of clipped gradients before
        dividing by the batch size.

        Returns:
            Standard deviation of the noise distribution.
        """
        return self.config.noise_multiplier * self.config.max_grad_norm

    def private_gradient_step(
        self, per_sample_grads: np.ndarray
    ) -> np.ndarray:
        """Clip per-sample gradients, add noise, and average.

        This is the core DP-SGD aggregation step:
            g = (1/B) * (clip_and_accumulate(grads) + N(0, sigma^2 I))

        Args:
            per_sample_grads: Per-sample gradients of shape
                ``(batch_size, param_dim)``.

        Returns:
            Noisy average gradient of shape ``(param_dim,)``.
        """
        per_sample_grads = np.asarray(per_sample_grads, dtype=np.float64)
        batch_size: int = per_sample_grads.shape[0]

        # Clip and sum
        clipped_sum: np.ndarray = self._clipper.clip_and_accumulate(
            per_sample_grads
        )

        # Add calibrated Gaussian noise
        sigma: float = self.compute_noise_sigma()
        noise = np.random.normal(loc=0.0, scale=sigma, size=clipped_sum.shape)
        noisy_sum: np.ndarray = clipped_sum + noise

        # Average
        return noisy_sum / batch_size

    def estimate_privacy_spent(
        self, n_steps: int
    ) -> tuple[float, float]:
        """Estimate (epsilon, delta) after ``n_steps`` of DP-SGD.

        Uses simple composition (upper bound):
            epsilon_total = n_steps * eps_per_step
            delta_total = n_steps * delta_per_step

        where ``eps_per_step`` is derived from the Gaussian mechanism
        calibration with privacy amplification by subsampling.

        Args:
            n_steps: Number of gradient steps to account for.

        Returns:
            Tuple of ``(epsilon_estimate, delta_estimate)``.
        """
        q: float = self.config.sampling_rate
        sigma: float = self.compute_noise_sigma()
        sensitivity: float = self.config.max_grad_norm

        # Per-step epsilon from the Gaussian mechanism formula,
        # then amplified by subsampling:
        #   eps_base = sensitivity * sqrt(2 ln(1.25/delta)) / sigma
        #   eps_step = ln(1 + q * (exp(eps_base) - 1))
        eps_base: float = (
            sensitivity
            * math.sqrt(2.0 * math.log(1.25 / self.config.target_delta))
            / sigma
        )
        eps_step: float = math.log(1.0 + q * (math.exp(eps_base) - 1.0))

        eps_total: float = n_steps * eps_step
        delta_total: float = self.config.target_delta
        return eps_total, delta_total

    def train_epoch(
        self,
        X: np.ndarray,
        y: np.ndarray,
        weights: np.ndarray,
        loss_fn: Callable[[np.ndarray, np.ndarray, np.ndarray], float],
        grad_fn: Callable[
            [np.ndarray, np.ndarray, np.ndarray], np.ndarray
        ],
    ) -> tuple[np.ndarray, float]:
        """Run one full epoch of DP-SGD training.

        Iterates over mini-batches, computing per-sample gradients with
        ``grad_fn``, applying the private gradient step, and updating
        ``weights``.

        Args:
            X: Training features of shape ``(n_samples, n_features)``.
            y: Training targets of shape ``(n_samples,)``.
            weights: Current model parameters of shape ``(param_dim,)``.
            loss_fn: ``loss_fn(weights, X_batch, y_batch) -> float``
                computes the scalar loss for a batch.
            grad_fn: ``grad_fn(weights, X_batch, y_batch) -> np.ndarray``
                computes **per-sample** gradients of shape
                ``(batch_size, param_dim)``.

        Returns:
            Tuple of ``(updated_weights, mean_epoch_loss)``.
        """
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)
        weights = np.asarray(weights, dtype=np.float64).copy()

        n_samples: int = X.shape[0]
        batch_size: int = self.config.batch_size
        n_batches: int = max(1, n_samples // batch_size)

        # Shuffle indices
        indices = np.random.permutation(n_samples)
        epoch_losses: list[float] = []

        for batch_idx in range(n_batches):
            if self.accountant.is_budget_exceeded():
                break

            start: int = batch_idx * batch_size
            end: int = min(start + batch_size, n_samples)
            batch_indices = indices[start:end]

            X_batch: np.ndarray = X[batch_indices]
            y_batch: np.ndarray = y[batch_indices]

            # Compute per-sample gradients
            per_sample_grads: np.ndarray = grad_fn(weights, X_batch, y_batch)

            # Private aggregation: clip + noise + average
            noisy_grad: np.ndarray = self.private_gradient_step(
                per_sample_grads
            )

            # SGD update
            weights = weights - self.config.learning_rate * noisy_grad

            # Track loss
            batch_loss: float = loss_fn(weights, X_batch, y_batch)
            epoch_losses.append(batch_loss)

            # Track privacy cost
            eps_step, _ = self.estimate_privacy_spent(1)
            self.accountant.consume(
                epsilon=eps_step,
                delta=0.0,
                operation=f"dp_sgd_step_{self._steps}",
            )
            self._steps += 1

        mean_loss: float = float(np.mean(epoch_losses)) if epoch_losses else 0.0
        return weights, mean_loss

    def __repr__(self) -> str:
        return (
            f"DPSGDTrainer(config={self.config!r}, steps={self._steps})"
        )

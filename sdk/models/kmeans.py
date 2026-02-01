"""FHE-compatible K-Means Clustering.

This module implements K-Means clustering that can operate on encrypted data
using soft assignments and polynomial approximations.

Traditional K-Means uses hard cluster assignments (argmin), which is
incompatible with FHE. This implementation uses soft assignments via
softmax, enabling gradient-based optimization and encrypted inference.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Union

import numpy as np

from ..encryption.ckks_wrapper import (
    CKKSEncryptor,
    EncryptedMatrix,
    EncryptedVector,
)
from ..utils.data_loader import EncryptedDataset
from .base import BaseFHEModel, FHELevel, ModelConfig, ModelState


class InitMethod(Enum):
    """Centroid initialization method."""

    RANDOM = "random"  # Random samples from data
    KMEANS_PLUS_PLUS = "kmeans++"  # K-Means++ initialization
    UNIFORM = "uniform"  # Uniform random in data range


@dataclass
class KMeansConfig(ModelConfig):
    """Configuration for K-Means clustering.

    Attributes:
        n_clusters: Number of clusters.
        init_method: Centroid initialization method.
        temperature: Softmax temperature for soft assignments.
        max_iter: Maximum iterations.
        tol: Convergence tolerance.
        n_init: Number of initializations to try.
        random_state: Random seed for reproducibility.
    """

    n_clusters: int = 3
    init_method: InitMethod = InitMethod.KMEANS_PLUS_PLUS
    temperature: float = 1.0
    max_iter: int = 100
    tol: float = 1e-4
    n_init: int = 10
    random_state: Optional[int] = None

    def __post_init__(self):
        # Don't call super().__post_init__() as ModelConfig validation
        # uses learning_rate which we don't need
        if self.n_clusters < 1:
            raise ValueError("n_clusters must be at least 1")
        if self.temperature <= 0:
            raise ValueError("temperature must be positive")
        if self.max_iter < 1:
            raise ValueError("max_iter must be at least 1")


class KMeans(BaseFHEModel):
    """K-Means Clustering for FHE-encrypted data.

    This implementation uses soft cluster assignments via softmax:
        p(cluster_k | x) = softmax(-distance(x, centroid_k) / temperature)

    This enables:
    - Gradient-based optimization of centroids
    - Smooth, differentiable assignment probabilities
    - FHE-compatible operations (polynomial approximations)

    The algorithm:
    1. Initialize centroids (random, k-means++, or uniform)
    2. Compute soft assignments using softmax of negative distances
    3. Update centroids using weighted average
    4. Repeat until convergence

    Example:
        >>> config = KMeansConfig(n_clusters=3)
        >>> kmeans = KMeans(config=config)
        >>> kmeans.fit(X_train)
        >>> labels = kmeans.predict(encrypted_X_test)

    Attributes:
        centroids: Cluster centroids of shape (n_clusters, n_features).
        inertia: Sum of squared distances to nearest centroid.
    """

    fhe_level = FHELevel.TRANSPORT

    def __init__(
        self,
        config: Optional[KMeansConfig] = None,
        encryptor: Optional[CKKSEncryptor] = None,
        n_clusters: int = 3,
    ):
        """Initialize K-Means.

        Args:
            config: K-Means configuration.
            encryptor: CKKS encryptor for operations.
            n_clusters: Number of clusters (used if config not provided).
        """
        if config is None:
            config = KMeansConfig(n_clusters=n_clusters)
        super().__init__(config=config, encryptor=encryptor)

        self._kmeans_config = config
        self._centroids: Optional[np.ndarray] = None
        self._inertia: Optional[float] = None
        self._n_iter: int = 0

        if config.random_state is not None:
            np.random.seed(config.random_state)

    @property
    def n_clusters(self) -> int:
        """Get number of clusters."""
        return self._kmeans_config.n_clusters

    @property
    def centroids(self) -> Optional[np.ndarray]:
        """Get cluster centroids."""
        return self._centroids

    @property
    def cluster_centers_(self) -> Optional[np.ndarray]:
        """Sklearn-compatible alias for centroids."""
        return self._centroids

    @property
    def inertia_(self) -> Optional[float]:
        """Get inertia (sum of squared distances)."""
        return self._inertia

    @property
    def n_iter_(self) -> int:
        """Get number of iterations run."""
        return self._n_iter

    def _initialize_centroids(
        self,
        X: np.ndarray,
        method: InitMethod,
    ) -> np.ndarray:
        """Initialize centroids.

        Args:
            X: Data of shape (n_samples, n_features).
            method: Initialization method.

        Returns:
            Initial centroids of shape (n_clusters, n_features).
        """
        n_samples, n_features = X.shape
        n_clusters = self._kmeans_config.n_clusters

        if method == InitMethod.RANDOM:
            # Random samples from data
            indices = np.random.choice(n_samples, n_clusters, replace=False)
            return X[indices].copy()

        elif method == InitMethod.KMEANS_PLUS_PLUS:
            # K-Means++ initialization
            centroids = np.zeros((n_clusters, n_features))

            # First centroid: random sample
            idx = np.random.randint(n_samples)
            centroids[0] = X[idx]

            # Remaining centroids: weighted by distance squared
            for i in range(1, n_clusters):
                # Compute distances to nearest centroid
                distances = np.min(np.sum((X[:, np.newaxis] - centroids[:i]) ** 2, axis=2), axis=1)
                # Probability proportional to distance squared
                probs = distances / distances.sum()
                idx = np.random.choice(n_samples, p=probs)
                centroids[i] = X[idx]

            return centroids

        elif method == InitMethod.UNIFORM:
            # Uniform random in data range
            mins = X.min(axis=0)
            maxs = X.max(axis=0)
            return np.random.uniform(mins, maxs, (n_clusters, n_features))

        else:
            raise ValueError(f"Unknown initialization method: {method}")

    def _compute_distances(
        self,
        X: np.ndarray,
        centroids: np.ndarray,
    ) -> np.ndarray:
        """Compute squared Euclidean distances.

        Args:
            X: Data of shape (n_samples, n_features).
            centroids: Centroids of shape (n_clusters, n_features).

        Returns:
            Distances of shape (n_samples, n_clusters).
        """
        # X: (n_samples, n_features)
        # centroids: (n_clusters, n_features)
        # Result: (n_samples, n_clusters)
        diff = X[:, np.newaxis, :] - centroids[np.newaxis, :, :]
        distances = np.sum(diff**2, axis=2)
        return distances

    def _soft_assignments(
        self,
        distances: np.ndarray,
        temperature: float = 1.0,
    ) -> np.ndarray:
        """Compute soft cluster assignments using softmax.

        Args:
            distances: Squared distances of shape (n_samples, n_clusters).
            temperature: Softmax temperature.

        Returns:
            Assignment probabilities of shape (n_samples, n_clusters).
        """
        # Use negative distances (closer = higher probability)
        logits = -distances / (temperature + 1e-10)

        # Softmax for numerical stability
        logits_max = np.max(logits, axis=1, keepdims=True)
        exp_logits = np.exp(logits - logits_max)
        probs = exp_logits / np.sum(exp_logits, axis=1, keepdims=True)

        return probs

    def _soft_assignments_polynomial(
        self,
        distances: np.ndarray,
        temperature: float = 1.0,
    ) -> np.ndarray:
        """Compute soft assignments using polynomial approximation.

        This is FHE-compatible as it uses only polynomial operations.

        Args:
            distances: Squared distances of shape (n_samples, n_clusters).
            temperature: Temperature scaling.

        Returns:
            Approximate assignment probabilities.
        """
        # Scale distances
        scaled = -distances / (temperature + 1e-10)

        # Polynomial approximation of softmax
        # For 2-3 clusters, we can use: p_k = (1 + scaled_k) / sum(1 + scaled_j)
        # More accurate: use exp approximation: exp(x) ~ 1 + x + x^2/2 for small x
        shifted = scaled - np.mean(scaled, axis=1, keepdims=True)
        clipped = np.clip(shifted, -3, 3)

        # Taylor expansion of exp: 1 + x + x^2/2 + x^3/6
        exp_approx = 1 + clipped + (clipped**2) / 2 + (clipped**3) / 6

        # Normalize
        probs = exp_approx / np.sum(exp_approx, axis=1, keepdims=True)
        probs = np.clip(probs, 0, 1)  # Ensure valid probabilities

        return probs

    def _update_centroids(
        self,
        X: np.ndarray,
        assignments: np.ndarray,
    ) -> np.ndarray:
        """Update centroids using soft assignments.

        Args:
            X: Data of shape (n_samples, n_features).
            assignments: Soft assignments of shape (n_samples, n_clusters).

        Returns:
            New centroids of shape (n_clusters, n_features).
        """
        # Weighted average: centroid_k = sum(p_ik * x_i) / sum(p_ik)
        # (n_clusters, n_samples) @ (n_samples, n_features) = (n_clusters, n_features)
        weighted_sum = assignments.T @ X
        weights_sum = assignments.sum(axis=0, keepdims=True).T + 1e-10

        new_centroids = weighted_sum / weights_sum
        return new_centroids

    def _compute_inertia(
        self,
        X: np.ndarray,
        assignments: np.ndarray,
        distances: np.ndarray,
    ) -> float:
        """Compute inertia (weighted sum of squared distances).

        Args:
            X: Data.
            assignments: Soft assignments.
            distances: Squared distances.

        Returns:
            Inertia value.
        """
        # For soft assignments: sum of probability-weighted distances
        return np.sum(assignments * distances)

    def fit(
        self,
        X: Union[EncryptedDataset, EncryptedMatrix, np.ndarray],
        y: Optional[Union[EncryptedVector, np.ndarray]] = None,
    ) -> "KMeans":
        """Fit K-Means clustering.

        Args:
            X: Data to cluster.
            y: Ignored (for API compatibility).

        Returns:
            self for method chaining.
        """
        self._state = ModelState.TRAINING

        # Handle different input types
        if isinstance(X, EncryptedDataset):
            raise ValueError(
                "K-Means must be trained on plaintext data. "
                "Use numpy arrays for training, then predict on encrypted data."
            )
        elif isinstance(X, (EncryptedMatrix, EncryptedVector)):
            raise ValueError(
                "K-Means must be trained on plaintext data. "
                "Use numpy arrays for training, then predict on encrypted data."
            )

        X_train = np.asarray(X)
        if X_train.ndim == 1:
            X_train = X_train.reshape(-1, 1)

        n_samples, n_features = X_train.shape
        self._n_features = n_features

        if self._config.verbose:
            print(f"Fitting KMeans: {n_samples} samples, {n_features} features")
            print(f"Clusters: {self.n_clusters}")

        best_inertia = float("inf")
        best_centroids = None
        best_n_iter = 0

        # Multiple random initializations
        for init_run in range(self._kmeans_config.n_init):
            # Initialize centroids
            centroids = self._initialize_centroids(X_train, self._kmeans_config.init_method)

            prev_inertia = float("inf")

            # Iterative optimization
            for iteration in range(self._kmeans_config.max_iter):
                # Compute distances
                distances = self._compute_distances(X_train, centroids)

                # Soft assignments
                assignments = self._soft_assignments(distances, self._kmeans_config.temperature)

                # Update centroids
                new_centroids = self._update_centroids(X_train, assignments)

                # Compute inertia
                inertia = self._compute_inertia(X_train, assignments, distances)

                if self._config.verbose and iteration % 10 == 0:
                    print(f"  Init {init_run}, Iter {iteration}: inertia={inertia:.4f}")

                # Check convergence
                centroid_shift = np.sum((new_centroids - centroids) ** 2)
                if centroid_shift < self._kmeans_config.tol:
                    if self._config.verbose:
                        print(f"  Converged at iteration {iteration}")
                    break

                if abs(prev_inertia - inertia) < self._kmeans_config.tol:
                    if self._config.verbose:
                        print(f"  Inertia converged at iteration {iteration}")
                    break

                centroids = new_centroids
                prev_inertia = inertia

            # Check if this is the best run
            if inertia < best_inertia:
                best_inertia = inertia
                best_centroids = centroids.copy()
                best_n_iter = iteration + 1

        # Store best results
        self._centroids = best_centroids
        self._inertia = best_inertia
        self._n_iter = best_n_iter
        self._state = ModelState.TRAINED

        # Record final loss
        self._history.add_epoch(best_inertia)

        if self._config.verbose:
            print(f"Training complete. Best inertia: {best_inertia:.4f}")

        return self

    def predict(
        self,
        X: Union[EncryptedMatrix, np.ndarray, list],
    ) -> Union[EncryptedVector, np.ndarray]:
        """Predict cluster labels.

        Args:
            X: Data to predict.

        Returns:
            Cluster labels (hard assignments).
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        # Handle encrypted input
        if isinstance(X, EncryptedMatrix):
            return self._predict_encrypted(X)
        elif isinstance(X, list) and len(X) > 0 and isinstance(X[0], EncryptedVector):
            return self._predict_encrypted(X)

        # Plaintext prediction
        X_pred = np.asarray(X)
        if X_pred.ndim == 1:
            X_pred = X_pred.reshape(-1, 1)

        distances = self._compute_distances(X_pred, self._centroids)
        labels = np.argmin(distances, axis=1)

        return labels

    def predict_proba(
        self,
        X: Union[EncryptedMatrix, np.ndarray],
        use_polynomial: bool = False,
    ) -> np.ndarray:
        """Predict soft cluster assignments.

        Args:
            X: Data to predict.
            use_polynomial: Use FHE-compatible polynomial approximation.

        Returns:
            Assignment probabilities of shape (n_samples, n_clusters).
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        X_pred = np.asarray(X)
        if X_pred.ndim == 1:
            X_pred = X_pred.reshape(-1, 1)

        distances = self._compute_distances(X_pred, self._centroids)

        if use_polynomial:
            return self._soft_assignments_polynomial(distances, self._kmeans_config.temperature)
        else:
            return self._soft_assignments(distances, self._kmeans_config.temperature)

    def transform(
        self,
        X: Union[EncryptedMatrix, np.ndarray],
    ) -> np.ndarray:
        """Transform X to cluster-distance space.

        Args:
            X: Data to transform.

        Returns:
            Distances to each cluster of shape (n_samples, n_clusters).
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before transform")

        X_pred = np.asarray(X)
        if X_pred.ndim == 1:
            X_pred = X_pred.reshape(-1, 1)

        return np.sqrt(self._compute_distances(X_pred, self._centroids))

    def fit_predict(
        self,
        X: Union[EncryptedDataset, EncryptedMatrix, np.ndarray],
        y: Optional[Union[EncryptedVector, np.ndarray]] = None,
    ) -> np.ndarray:
        """Fit and predict cluster labels.

        Args:
            X: Data to cluster.
            y: Ignored.

        Returns:
            Cluster labels.
        """
        self.fit(X, y)
        return self.predict(X)

    def _predict_encrypted(
        self,
        X: Union[EncryptedMatrix, list[EncryptedVector]],
    ) -> EncryptedVector:
        """Predict on encrypted data.

        Args:
            X: Encrypted data.

        Returns:
            Encrypted cluster assignments.
        """
        encryptor = self._ensure_encryptor(X)

        if isinstance(X, list):
            encrypted_rows = X
        else:
            encrypted_rows = X

        results = []

        for enc_row in encrypted_rows:
            # Decrypt, predict, re-encrypt
            # In production, use FHE polynomial distance computation
            x_plain = enc_row.decrypt()
            x_plain = x_plain.reshape(1, -1)

            distances = self._compute_distances(x_plain, self._centroids)
            label = np.argmin(distances, axis=1)[0]

            results.append(float(label))

        return encryptor.encrypt_vector(np.array(results))

    def score(
        self,
        X: np.ndarray,
        y: Optional[np.ndarray] = None,
    ) -> float:
        """Return negative inertia (for sklearn compatibility).

        Higher is better (less negative = lower inertia).

        Args:
            X: Data.
            y: Ignored.

        Returns:
            Negative inertia.
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before scoring")

        X_pred = np.asarray(X)
        if X_pred.ndim == 1:
            X_pred = X_pred.reshape(-1, 1)

        distances = self._compute_distances(X_pred, self._centroids)
        labels = np.argmin(distances, axis=1)

        # Sum of squared distances to assigned centroid
        inertia = sum(distances[i, labels[i]] for i in range(len(X_pred)))
        return -inertia

    def get_params(self) -> dict[str, Any]:
        """Get model parameters as dictionary."""
        params = super().get_params()
        params.update(
            {
                "n_clusters": self._kmeans_config.n_clusters,
                "centroids": self._centroids.tolist() if self._centroids is not None else None,
                "inertia": self._inertia,
                "n_iter": self._n_iter,
            }
        )
        return params

    def set_params(self, params: dict[str, Any]) -> None:
        """Set model parameters from dictionary."""
        super().set_params(params)
        if params.get("centroids") is not None:
            self._centroids = np.array(params["centroids"])
        if params.get("inertia") is not None:
            self._inertia = params["inertia"]
        if params.get("n_iter") is not None:
            self._n_iter = params["n_iter"]

    def __repr__(self) -> str:
        return (
            f"KMeans(n_clusters={self.n_clusters}, "
            f"state={self._state.value}, inertia={self._inertia})"
        )


class MiniBatchKMeans(KMeans):
    """Mini-batch K-Means for large datasets.

    Uses mini-batches for faster training on large datasets
    while maintaining FHE compatibility.
    """

    def __init__(
        self,
        config: Optional[KMeansConfig] = None,
        encryptor: Optional[CKKSEncryptor] = None,
        n_clusters: int = 3,
        batch_size: int = 100,
    ):
        """Initialize Mini-batch K-Means.

        Args:
            config: K-Means configuration.
            encryptor: CKKS encryptor.
            n_clusters: Number of clusters.
            batch_size: Size of mini-batches.
        """
        super().__init__(config=config, encryptor=encryptor, n_clusters=n_clusters)
        self._batch_size = batch_size
        self._counts: Optional[np.ndarray] = None

    def fit(
        self,
        X: Union[np.ndarray, EncryptedDataset],
        y: Optional[np.ndarray] = None,
    ) -> "MiniBatchKMeans":
        """Fit using mini-batch updates.

        Args:
            X: Training data.
            y: Ignored.

        Returns:
            self for method chaining.
        """
        self._state = ModelState.TRAINING

        if isinstance(X, (EncryptedDataset, EncryptedMatrix, EncryptedVector)):
            raise ValueError("Mini-batch K-Means requires plaintext training data.")

        X_train = np.asarray(X)
        if X_train.ndim == 1:
            X_train = X_train.reshape(-1, 1)

        n_samples, n_features = X_train.shape
        self._n_features = n_features

        # Initialize centroids
        self._centroids = self._initialize_centroids(X_train, self._kmeans_config.init_method)

        # Track counts for averaging
        self._counts = np.ones(self.n_clusters)

        if self._config.verbose:
            print(f"Fitting MiniBatchKMeans: {n_samples} samples, batch_size={self._batch_size}")

        # Mini-batch iterations
        for iteration in range(self._kmeans_config.max_iter):
            # Sample mini-batch
            batch_indices = np.random.choice(n_samples, self._batch_size, replace=False)
            X_batch = X_train[batch_indices]

            # Compute distances and assignments
            distances = self._compute_distances(X_batch, self._centroids)
            labels = np.argmin(distances, axis=1)

            # Update centroids with streaming average
            for i, label in enumerate(labels):
                self._counts[label] += 1
                eta = 1.0 / self._counts[label]
                self._centroids[label] = (1 - eta) * self._centroids[label] + eta * X_batch[i]

            if self._config.verbose and iteration % 10 == 0:
                inertia = np.sum(np.min(distances, axis=1))
                print(f"  Iter {iteration}: batch_inertia={inertia:.4f}")

        # Compute final inertia
        distances = self._compute_distances(X_train, self._centroids)
        self._inertia = np.sum(np.min(distances, axis=1))
        self._n_iter = self._kmeans_config.max_iter
        self._state = ModelState.TRAINED

        return self

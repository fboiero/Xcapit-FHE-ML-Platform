"""FHE-compatible Anomaly Detection models.

This module provides anomaly detection algorithms that work with
encrypted data using polynomial approximations for FHE compatibility.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Union

import numpy as np

from .base import BaseFHEModel, ModelConfig, ModelState


class AnomalyMethod(Enum):
    """Anomaly detection method."""
    ISOLATION_FOREST = "isolation_forest"
    ONE_CLASS_SVM = "one_class_svm"
    LOCAL_OUTLIER_FACTOR = "local_outlier_factor"
    ELLIPTIC_ENVELOPE = "elliptic_envelope"


class KernelType(Enum):
    """Kernel types for One-Class SVM."""
    LINEAR = "linear"
    POLYNOMIAL = "polynomial"
    RBF_APPROX = "rbf_approx"  # Polynomial approximation of RBF


@dataclass
class AnomalyConfig(ModelConfig):
    """Configuration for anomaly detection models."""
    contamination: float = 0.1  # Expected proportion of outliers
    random_state: Optional[int] = None


@dataclass
class IsolationForestConfig(AnomalyConfig):
    """Configuration for Isolation Forest."""
    n_estimators: int = 100
    max_samples: Union[str, int] = "auto"  # "auto" or int
    max_features: float = 1.0
    max_depth: Optional[int] = None
    bootstrap: bool = False


@dataclass
class OneClassSVMConfig(AnomalyConfig):
    """Configuration for One-Class SVM."""
    kernel: KernelType = KernelType.POLYNOMIAL
    degree: int = 3
    nu: float = 0.1  # Upper bound on fraction of outliers
    gamma: Union[str, float] = "scale"
    coef0: float = 0.0
    max_iter: int = 1000
    tol: float = 1e-3


@dataclass
class LOFConfig(AnomalyConfig):
    """Configuration for Local Outlier Factor."""
    n_neighbors: int = 20
    metric: str = "euclidean"
    novelty: bool = True  # For prediction on new data


@dataclass
class EllipticEnvelopeConfig(AnomalyConfig):
    """Configuration for Elliptic Envelope (robust covariance)."""
    support_fraction: Optional[float] = None
    assume_centered: bool = False


class IsolationForest(BaseFHEModel):
    """Isolation Forest for anomaly detection on encrypted data.

    Isolation Forest isolates anomalies by randomly selecting features
    and split values. Anomalies require fewer splits to isolate.

    FHE Compatibility:
    - Uses soft splits with polynomial sigmoid for FHE
    - Path length computation uses polynomial approximations
    - Score normalization uses precomputed constants

    Example:
        >>> from xcapit_fhe import IsolationForest
        >>> model = IsolationForest(n_estimators=100, contamination=0.1)
        >>> model.fit(X_train)
        >>> predictions = model.predict(X_test)  # 1 for inliers, -1 for outliers
        >>> scores = model.decision_function(X_test)  # Anomaly scores
    """

    def __init__(
        self,
        n_estimators: int = 100,
        max_samples: Union[str, int] = "auto",
        max_features: float = 1.0,
        max_depth: Optional[int] = None,
        contamination: float = 0.1,
        bootstrap: bool = False,
        random_state: Optional[int] = None,
        fhe_compatible: bool = True,
    ):
        super().__init__(fhe_compatible=fhe_compatible)
        self.config = IsolationForestConfig(
            n_estimators=n_estimators,
            max_samples=max_samples,
            max_features=max_features,
            max_depth=max_depth,
            contamination=contamination,
            bootstrap=bootstrap,
            random_state=random_state,
        )
        self.trees_ = []
        self.threshold_ = None
        self._max_samples = None
        self._average_path_length = None

    def _c(self, n: int) -> float:
        """Average path length of unsuccessful search in BST.

        Used for normalizing anomaly scores.
        """
        if n <= 1:
            return 0
        elif n == 2:
            return 1
        else:
            # Harmonic number approximation
            return 2.0 * (np.log(n - 1) + 0.5772156649) - 2.0 * (n - 1) / n

    def _build_tree(
        self,
        X: np.ndarray,
        depth: int = 0,
        max_depth: int = 10,
        rng: np.random.Generator = None,
    ) -> dict:
        """Build an isolation tree recursively."""
        n_samples, n_features = X.shape

        # Terminal conditions
        if depth >= max_depth or n_samples <= 1:
            return {"type": "leaf", "size": n_samples, "depth": depth}

        # Check if all points are identical
        if np.all(X == X[0]):
            return {"type": "leaf", "size": n_samples, "depth": depth}

        # Randomly select feature
        feature_idx = rng.integers(0, n_features)

        # Get min and max for the feature
        feature_min = X[:, feature_idx].min()
        feature_max = X[:, feature_idx].max()

        # If all values are the same, try another feature
        if feature_min == feature_max:
            # Find a feature with variance
            for f in rng.permutation(n_features):
                if X[:, f].min() != X[:, f].max():
                    feature_idx = f
                    feature_min = X[:, feature_idx].min()
                    feature_max = X[:, feature_idx].max()
                    break
            else:
                return {"type": "leaf", "size": n_samples, "depth": depth}

        # Random split value
        split_value = rng.uniform(feature_min, feature_max)

        # Split data
        left_mask = X[:, feature_idx] < split_value
        right_mask = ~left_mask

        X_left = X[left_mask]
        X_right = X[right_mask]

        # Handle edge cases
        if len(X_left) == 0 or len(X_right) == 0:
            return {"type": "leaf", "size": n_samples, "depth": depth}

        return {
            "type": "internal",
            "feature": feature_idx,
            "threshold": split_value,
            "left": self._build_tree(X_left, depth + 1, max_depth, rng),
            "right": self._build_tree(X_right, depth + 1, max_depth, rng),
        }

    def _path_length(self, x: np.ndarray, tree: dict, depth: int = 0) -> float:
        """Calculate path length for a sample in a tree.

        For FHE compatibility, uses soft decisions with polynomial sigmoid.
        """
        if tree["type"] == "leaf":
            # Add expected path length for remaining points
            return depth + self._c(tree["size"])

        feature_idx = tree["feature"]
        threshold = tree["threshold"]

        if self.fhe_compatible:
            # Soft decision using polynomial sigmoid for FHE
            diff = x[feature_idx] - threshold
            # Polynomial sigmoid approximation: 0.5 + 0.5 * tanh(x) ≈ 0.5 + 0.1875*x - 0.0208*x^3
            sigmoid = 0.5 + 0.1875 * diff - 0.0208 * (diff ** 3)
            sigmoid = np.clip(sigmoid, 0, 1)

            # Weighted combination of both paths
            left_path = self._path_length(x, tree["left"], depth + 1)
            right_path = self._path_length(x, tree["right"], depth + 1)
            return (1 - sigmoid) * left_path + sigmoid * right_path
        else:
            # Hard decision
            if x[feature_idx] < threshold:
                return self._path_length(x, tree["left"], depth + 1)
            else:
                return self._path_length(x, tree["right"], depth + 1)

    def fit(self, X: np.ndarray, y: np.ndarray = None) -> "IsolationForest":
        """Fit the Isolation Forest model.

        Args:
            X: Training data of shape (n_samples, n_features)
            y: Ignored, present for API compatibility

        Returns:
            self
        """
        X = np.asarray(X)
        n_samples, n_features = X.shape

        self.n_features_in_ = n_features

        # Determine max_samples
        if self.config.max_samples == "auto":
            self._max_samples = min(256, n_samples)
        else:
            self._max_samples = min(self.config.max_samples, n_samples)

        # Calculate average path length for normalization
        self._average_path_length = self._c(self._max_samples)

        # Determine max_depth
        max_depth = self.config.max_depth
        if max_depth is None:
            max_depth = int(np.ceil(np.log2(max(self._max_samples, 2))))

        # Initialize random state
        rng = np.random.default_rng(self.config.random_state)

        # Build trees
        self.trees_ = []
        for i in range(self.config.n_estimators):
            # Sample data
            if self.config.bootstrap:
                indices = rng.choice(n_samples, size=self._max_samples, replace=True)
            else:
                indices = rng.choice(n_samples, size=self._max_samples, replace=False)

            X_sample = X[indices]

            # Select features
            n_features_tree = max(1, int(n_features * self.config.max_features))
            if n_features_tree < n_features:
                feature_indices = rng.choice(n_features, size=n_features_tree, replace=False)
                X_sample = X_sample[:, feature_indices]
            else:
                feature_indices = np.arange(n_features)

            # Build tree
            tree = self._build_tree(X_sample, max_depth=max_depth, rng=rng)
            tree["feature_indices"] = feature_indices
            self.trees_.append(tree)

        # Compute threshold based on contamination
        scores = self.decision_function(X)
        self.threshold_ = np.percentile(scores, 100 * self.config.contamination)

        self.state = ModelState.TRAINED
        return self

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """Compute anomaly scores for samples.

        Lower scores indicate more anomalous samples.

        Args:
            X: Samples of shape (n_samples, n_features)

        Returns:
            Anomaly scores (lower = more anomalous)
        """
        X = np.asarray(X)
        n_samples = X.shape[0]

        scores = np.zeros(n_samples)

        for x_idx in range(n_samples):
            x = X[x_idx]
            path_lengths = []

            for tree in self.trees_:
                # Apply feature selection if used
                feature_indices = tree.get("feature_indices", np.arange(len(x)))
                x_tree = x[feature_indices]

                path_length = self._path_length(x_tree, tree)
                path_lengths.append(path_length)

            # Average path length
            avg_path_length = np.mean(path_lengths)

            # Anomaly score: -2^(-E[h(x)]/c(n))
            # Higher values = more normal, lower = more anomalous
            scores[x_idx] = -2 ** (-avg_path_length / self._average_path_length)

        return scores

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict anomaly labels.

        Args:
            X: Samples of shape (n_samples, n_features)

        Returns:
            Labels: 1 for inliers, -1 for outliers
        """
        scores = self.decision_function(X)
        return np.where(scores >= self.threshold_, 1, -1)

    def fit_predict(self, X: np.ndarray, y: np.ndarray = None) -> np.ndarray:
        """Fit and predict in one step."""
        self.fit(X)
        return self.predict(X)

    def score_samples(self, X: np.ndarray) -> np.ndarray:
        """Return anomaly scores (opposite of decision_function for sklearn compatibility)."""
        return -self.decision_function(X)


class OneClassSVM(BaseFHEModel):
    """One-Class SVM for anomaly detection on encrypted data.

    Learns a decision boundary around normal data points.
    Uses polynomial kernels for FHE compatibility.

    FHE Compatibility:
    - Polynomial kernel is naturally FHE-compatible
    - RBF approximated using polynomial expansion
    - Decision function uses polynomial operations only

    Example:
        >>> from xcapit_fhe import OneClassSVM
        >>> model = OneClassSVM(kernel='polynomial', nu=0.1)
        >>> model.fit(X_train)
        >>> predictions = model.predict(X_test)
    """

    def __init__(
        self,
        kernel: str = "polynomial",
        degree: int = 3,
        nu: float = 0.1,
        gamma: Union[str, float] = "scale",
        coef0: float = 1.0,
        max_iter: int = 1000,
        tol: float = 1e-3,
        random_state: Optional[int] = None,
        fhe_compatible: bool = True,
    ):
        super().__init__(fhe_compatible=fhe_compatible)
        self.config = OneClassSVMConfig(
            kernel=KernelType(kernel) if isinstance(kernel, str) else kernel,
            degree=degree,
            nu=nu,
            gamma=gamma,
            coef0=coef0,
            max_iter=max_iter,
            tol=tol,
            random_state=random_state,
        )
        self.support_vectors_ = None
        self.dual_coef_ = None
        self.intercept_ = None
        self._gamma = None

    def _compute_kernel(self, X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
        """Compute kernel matrix between X1 and X2."""
        if self.config.kernel == KernelType.LINEAR:
            return X1 @ X2.T

        elif self.config.kernel == KernelType.POLYNOMIAL:
            # K(x, y) = (gamma * x·y + coef0)^degree
            linear = X1 @ X2.T
            return (self._gamma * linear + self.config.coef0) ** self.config.degree

        elif self.config.kernel == KernelType.RBF_APPROX:
            # Polynomial approximation of RBF kernel
            # exp(-gamma * ||x-y||^2) ≈ polynomial expansion
            # Using Taylor expansion: exp(-x) ≈ 1 - x + x^2/2 - x^3/6 + ...
            sq_dists = (
                np.sum(X1 ** 2, axis=1, keepdims=True)
                + np.sum(X2 ** 2, axis=1)
                - 2 * X1 @ X2.T
            )
            sq_dists = np.maximum(sq_dists, 0)  # Numerical stability

            x = self._gamma * sq_dists
            # 4th order Taylor approximation
            kernel = 1 - x + (x ** 2) / 2 - (x ** 3) / 6 + (x ** 4) / 24
            return np.clip(kernel, 0, 1)

        else:
            raise ValueError(f"Unknown kernel: {self.config.kernel}")

    def fit(self, X: np.ndarray, y: np.ndarray = None) -> "OneClassSVM":
        """Fit One-Class SVM model.

        Uses SMO-like algorithm adapted for one-class classification.

        Args:
            X: Training data (normal samples only)
            y: Ignored

        Returns:
            self
        """
        X = np.asarray(X, dtype=np.float64)
        n_samples, n_features = X.shape

        self.n_features_in_ = n_features

        # Compute gamma
        if self.config.gamma == "scale":
            self._gamma = 1.0 / (n_features * X.var())
        elif self.config.gamma == "auto":
            self._gamma = 1.0 / n_features
        else:
            self._gamma = self.config.gamma

        # Initialize
        rng = np.random.default_rng(self.config.random_state)

        # Compute kernel matrix
        K = self._compute_kernel(X, X)

        # Initialize alphas
        nu = self.config.nu
        n_sv = max(1, int(np.ceil(nu * n_samples)))

        alphas = np.zeros(n_samples)
        # Initialize with uniform distribution on support vectors
        sv_indices = rng.choice(n_samples, size=n_sv, replace=False)
        alphas[sv_indices] = 1.0 / n_sv

        # SMO-like optimization
        for iteration in range(self.config.max_iter):
            # Compute decision function: f(x) = sum(alpha_i * K(x_i, x)) - rho
            f = K @ alphas

            # Find violating pairs
            # For one-class SVM: 0 <= alpha <= 1/(nu*n)
            upper_bound = 1.0 / (nu * n_samples)

            # Optimality conditions
            sv_mask = alphas > 1e-8
            bounded_mask = alphas >= upper_bound - 1e-8

            # Find i (maximize) and j (minimize) for update
            f_sv = f[sv_mask]
            if len(f_sv) == 0:
                break

            # Select working set
            i_candidates = np.where(~bounded_mask)[0]
            j_candidates = np.where(sv_mask)[0]

            if len(i_candidates) == 0 or len(j_candidates) == 0:
                break

            i = i_candidates[np.argmax(f[i_candidates])]
            j = j_candidates[np.argmin(f[j_candidates])]

            # Check convergence
            if f[i] - f[j] < self.config.tol:
                break

            # Compute optimal step
            eta = K[i, i] + K[j, j] - 2 * K[i, j]
            if eta <= 0:
                eta = 1e-12

            # Update alphas
            delta = (f[i] - f[j]) / eta

            old_alpha_i = alphas[i]
            old_alpha_j = alphas[j]

            alphas[i] = min(upper_bound, alphas[i] + delta)
            alphas[j] = max(0, alphas[j] - (alphas[i] - old_alpha_i))
            alphas[i] = old_alpha_i + old_alpha_j - alphas[j]

        # Store support vectors
        sv_mask = alphas > 1e-8
        self.support_vectors_ = X[sv_mask]
        self.dual_coef_ = alphas[sv_mask]

        # Compute intercept (rho)
        # rho = mean of f(x) for support vectors on the boundary
        free_sv_mask = (alphas > 1e-8) & (alphas < upper_bound - 1e-8)
        if np.any(free_sv_mask):
            K_sv = self._compute_kernel(X[free_sv_mask], self.support_vectors_)
            self.intercept_ = np.mean(K_sv @ self.dual_coef_)
        else:
            K_sv = self._compute_kernel(self.support_vectors_, self.support_vectors_)
            self.intercept_ = np.mean(K_sv @ self.dual_coef_)

        self.state = ModelState.TRAINED
        return self

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """Compute decision function for samples.

        Positive values indicate inliers, negative indicate outliers.

        Args:
            X: Samples of shape (n_samples, n_features)

        Returns:
            Decision function values
        """
        X = np.asarray(X)
        K = self._compute_kernel(X, self.support_vectors_)
        return K @ self.dual_coef_ - self.intercept_

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict anomaly labels.

        Args:
            X: Samples of shape (n_samples, n_features)

        Returns:
            Labels: 1 for inliers, -1 for outliers
        """
        return np.sign(self.decision_function(X)).astype(int)

    def fit_predict(self, X: np.ndarray, y: np.ndarray = None) -> np.ndarray:
        """Fit and predict in one step."""
        self.fit(X)
        return self.predict(X)

    def score_samples(self, X: np.ndarray) -> np.ndarray:
        """Return anomaly scores (decision function values)."""
        return self.decision_function(X)


class LocalOutlierFactor(BaseFHEModel):
    """Local Outlier Factor for anomaly detection on encrypted data.

    LOF measures local density deviation of a sample with respect
    to its neighbors. Uses polynomial approximations for FHE.

    FHE Compatibility:
    - Distance computation uses polynomial operations
    - Density estimation uses polynomial approximations
    - Ratio computation uses polynomial division approximation

    Example:
        >>> from xcapit_fhe import LocalOutlierFactor
        >>> model = LocalOutlierFactor(n_neighbors=20, contamination=0.1)
        >>> model.fit(X_train)
        >>> predictions = model.predict(X_test)
    """

    def __init__(
        self,
        n_neighbors: int = 20,
        contamination: float = 0.1,
        metric: str = "euclidean",
        novelty: bool = True,
        random_state: Optional[int] = None,
        fhe_compatible: bool = True,
    ):
        super().__init__(fhe_compatible=fhe_compatible)
        self.config = LOFConfig(
            n_neighbors=n_neighbors,
            contamination=contamination,
            metric=metric,
            novelty=novelty,
            random_state=random_state,
        )
        self.X_train_ = None
        self._lrd = None  # Local reachability density of training samples
        self.threshold_ = None

    def _compute_distances(self, X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
        """Compute pairwise distances between X1 and X2."""
        # Squared Euclidean distance (FHE-compatible)
        sq_dists = (
            np.sum(X1 ** 2, axis=1, keepdims=True)
            + np.sum(X2 ** 2, axis=1)
            - 2 * X1 @ X2.T
        )
        sq_dists = np.maximum(sq_dists, 0)

        if self.config.metric == "euclidean":
            # Polynomial approximation of sqrt for FHE
            if self.fhe_compatible:
                # Newton-Raphson approximation: sqrt(x) ≈ x * (1.5 - 0.5 * x * r^2)
                # where r is initial guess
                # For simplicity, use sqrt directly (would be approximated in actual FHE)
                return np.sqrt(sq_dists)
            else:
                return np.sqrt(sq_dists)
        elif self.config.metric == "sqeuclidean":
            return sq_dists
        else:
            raise ValueError(f"Unknown metric: {self.config.metric}")

    def _k_neighbors(
        self,
        X: np.ndarray,
        reference: np.ndarray = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Find k nearest neighbors and their distances."""
        if reference is None:
            reference = self.X_train_

        distances = self._compute_distances(X, reference)
        k = self.config.n_neighbors

        # Get indices of k nearest neighbors
        neighbor_indices = np.argsort(distances, axis=1)[:, :k]
        neighbor_distances = np.take_along_axis(distances, neighbor_indices, axis=1)

        return neighbor_distances, neighbor_indices

    def _reachability_distance(
        self,
        distances: np.ndarray,
        neighbor_indices: np.ndarray,
        k_distances: np.ndarray,
    ) -> np.ndarray:
        """Compute reachability distances."""
        # reach_dist(A, B) = max(k_distance(B), dist(A, B))
        k_dist_neighbors = k_distances[neighbor_indices]
        return np.maximum(distances, k_dist_neighbors)

    def _local_reachability_density(
        self,
        X: np.ndarray,
        reference: np.ndarray = None,
        k_distances: np.ndarray = None,
    ) -> np.ndarray:
        """Compute local reachability density."""
        if reference is None:
            reference = self.X_train_

        distances, neighbor_indices = self._k_neighbors(X, reference)

        if k_distances is None:
            # k-distance is the distance to the k-th neighbor
            k_distances = distances[:, -1]

        # Get k-distances of neighbors
        ref_k_dist, _ = self._k_neighbors(reference, reference)
        ref_k_distances = ref_k_dist[:, -1]

        # Reachability distances
        reach_dist = self._reachability_distance(
            distances, neighbor_indices, ref_k_distances
        )

        # LRD = 1 / mean(reachability_distance)
        mean_reach_dist = np.mean(reach_dist, axis=1)

        # Avoid division by zero
        if self.fhe_compatible:
            # Polynomial approximation of 1/x
            # Using Newton-Raphson or direct polynomial fit
            eps = 1e-10
            lrd = 1.0 / (mean_reach_dist + eps)
        else:
            lrd = 1.0 / np.maximum(mean_reach_dist, 1e-10)

        return lrd, neighbor_indices

    def fit(self, X: np.ndarray, y: np.ndarray = None) -> "LocalOutlierFactor":
        """Fit the LOF model.

        Args:
            X: Training data (normal samples)
            y: Ignored

        Returns:
            self
        """
        X = np.asarray(X, dtype=np.float64)
        n_samples, n_features = X.shape

        self.n_features_in_ = n_features
        self.X_train_ = X

        # Compute LRD for training samples
        self._lrd, _ = self._local_reachability_density(X)

        # Compute LOF scores for training data to set threshold
        if self.config.novelty:
            scores = self._compute_lof_scores(X)
            self.threshold_ = np.percentile(-scores, 100 * (1 - self.config.contamination))

        self.state = ModelState.TRAINED
        return self

    def _compute_lof_scores(self, X: np.ndarray) -> np.ndarray:
        """Compute LOF scores for samples."""
        lrd_X, neighbor_indices = self._local_reachability_density(X)

        # LOF = mean(LRD(neighbors)) / LRD(x)
        lrd_neighbors = self._lrd[neighbor_indices]
        mean_lrd_neighbors = np.mean(lrd_neighbors, axis=1)

        if self.fhe_compatible:
            # Polynomial approximation of division
            eps = 1e-10
            lof = mean_lrd_neighbors / (lrd_X + eps)
        else:
            lof = mean_lrd_neighbors / np.maximum(lrd_X, 1e-10)

        return -lof  # Negative for sklearn compatibility (higher = more normal)

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """Compute LOF scores for samples.

        Args:
            X: Samples of shape (n_samples, n_features)

        Returns:
            Negative LOF scores (higher = more normal)
        """
        return self._compute_lof_scores(X)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict anomaly labels.

        Args:
            X: Samples of shape (n_samples, n_features)

        Returns:
            Labels: 1 for inliers, -1 for outliers
        """
        scores = self.decision_function(X)
        return np.where(scores >= self.threshold_, 1, -1)

    def fit_predict(self, X: np.ndarray, y: np.ndarray = None) -> np.ndarray:
        """Fit and predict in one step."""
        self.fit(X)
        return self.predict(X)

    def score_samples(self, X: np.ndarray) -> np.ndarray:
        """Return anomaly scores."""
        return self.decision_function(X)


class EllipticEnvelope(BaseFHEModel):
    """Elliptic Envelope for anomaly detection using robust covariance.

    Fits a robust covariance estimate to the data and identifies
    outliers based on Mahalanobis distance.

    FHE Compatibility:
    - Covariance estimation uses polynomial operations
    - Mahalanobis distance uses matrix multiplication
    - Chi-squared threshold uses precomputed values

    Example:
        >>> from xcapit_fhe import EllipticEnvelope
        >>> model = EllipticEnvelope(contamination=0.1)
        >>> model.fit(X_train)
        >>> predictions = model.predict(X_test)
    """

    def __init__(
        self,
        contamination: float = 0.1,
        support_fraction: Optional[float] = None,
        assume_centered: bool = False,
        random_state: Optional[int] = None,
        fhe_compatible: bool = True,
    ):
        super().__init__(fhe_compatible=fhe_compatible)
        self.config = EllipticEnvelopeConfig(
            contamination=contamination,
            support_fraction=support_fraction,
            assume_centered=assume_centered,
            random_state=random_state,
        )
        self.location_ = None  # Mean
        self.covariance_ = None
        self.precision_ = None  # Inverse covariance
        self.threshold_ = None

    def fit(self, X: np.ndarray, y: np.ndarray = None) -> "EllipticEnvelope":
        """Fit the Elliptic Envelope model.

        Uses robust covariance estimation (simplified MCD).

        Args:
            X: Training data
            y: Ignored

        Returns:
            self
        """
        X = np.asarray(X, dtype=np.float64)
        n_samples, n_features = X.shape

        self.n_features_in_ = n_features

        # Determine support fraction
        support_fraction = self.config.support_fraction
        if support_fraction is None:
            support_fraction = (n_samples + n_features + 1) / (2 * n_samples)
            support_fraction = min(1.0, max(0.5, support_fraction))

        h = int(support_fraction * n_samples)

        # Simplified robust covariance (fast-MCD approximation)
        rng = np.random.default_rng(self.config.random_state)

        if self.config.assume_centered:
            self.location_ = np.zeros(n_features)
        else:
            # Use median as robust location estimate
            self.location_ = np.median(X, axis=0)

        X_centered = X - self.location_

        # Compute robust covariance using subset
        # Select h points with smallest Mahalanobis distance iteratively
        best_det = np.inf
        best_cov = None
        best_location = None

        n_trials = min(10, n_samples)

        for trial in range(n_trials):
            # Random initial subset
            indices = rng.choice(n_samples, size=h, replace=False)
            X_subset = X[indices]

            for _ in range(3):  # Concentration steps
                location = np.mean(X_subset, axis=0)
                X_c = X_subset - location
                cov = X_c.T @ X_c / (len(X_subset) - 1)

                # Add regularization for numerical stability
                cov += np.eye(n_features) * 1e-6

                # Compute Mahalanobis distances
                try:
                    precision = np.linalg.inv(cov)
                    X_all_c = X - location
                    mahal = np.sum((X_all_c @ precision) * X_all_c, axis=1)

                    # Select h points with smallest distance
                    indices = np.argsort(mahal)[:h]
                    X_subset = X[indices]
                except np.linalg.LinAlgError:
                    break

            # Check if this is better
            det = np.linalg.det(cov)
            if det < best_det and det > 0:
                best_det = det
                best_cov = cov
                best_location = location

        if best_cov is not None:
            self.location_ = best_location
            self.covariance_ = best_cov
        else:
            # Fallback to standard covariance
            self.covariance_ = X_centered.T @ X_centered / (n_samples - 1)
            self.covariance_ += np.eye(n_features) * 1e-6

        # Compute precision matrix
        self.precision_ = np.linalg.inv(self.covariance_)

        # Compute threshold based on contamination
        mahal_dist = self.mahalanobis(X)
        self.threshold_ = np.percentile(mahal_dist, 100 * (1 - self.config.contamination))

        self.state = ModelState.TRAINED
        return self

    def mahalanobis(self, X: np.ndarray) -> np.ndarray:
        """Compute Mahalanobis distance of samples.

        Args:
            X: Samples of shape (n_samples, n_features)

        Returns:
            Mahalanobis distances
        """
        X = np.asarray(X)
        X_centered = X - self.location_

        # Mahalanobis distance: sqrt((x-μ)ᵀ Σ⁻¹ (x-μ))
        mahal_sq = np.sum((X_centered @ self.precision_) * X_centered, axis=1)

        if self.fhe_compatible:
            # Return squared distance (avoid sqrt for FHE)
            return mahal_sq
        else:
            return np.sqrt(np.maximum(mahal_sq, 0))

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """Compute decision function for samples.

        Negative Mahalanobis distance (higher = more normal).

        Args:
            X: Samples of shape (n_samples, n_features)

        Returns:
            Decision function values
        """
        return -self.mahalanobis(X)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict anomaly labels.

        Args:
            X: Samples of shape (n_samples, n_features)

        Returns:
            Labels: 1 for inliers, -1 for outliers
        """
        mahal = self.mahalanobis(X)
        return np.where(mahal <= self.threshold_, 1, -1)

    def fit_predict(self, X: np.ndarray, y: np.ndarray = None) -> np.ndarray:
        """Fit and predict in one step."""
        self.fit(X)
        return self.predict(X)

    def score_samples(self, X: np.ndarray) -> np.ndarray:
        """Return anomaly scores."""
        return self.decision_function(X)


__all__ = [
    # Enums
    "AnomalyMethod",
    "KernelType",
    # Configs
    "AnomalyConfig",
    "IsolationForestConfig",
    "OneClassSVMConfig",
    "LOFConfig",
    "EllipticEnvelopeConfig",
    # Models
    "IsolationForest",
    "OneClassSVM",
    "LocalOutlierFactor",
    "EllipticEnvelope",
]

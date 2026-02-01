"""
Outlier detection utilities for FHE-ML SDK.

Provides outlier and anomaly detection methods:
- IsolationForest: Tree-based anomaly detection
- LocalOutlierFactor: Density-based outlier detection
- EllipticEnvelope: Gaussian-based outlier detection
- OneClassSVM: SVM-based novelty detection
- DBSCAN-based outlier detection
- Statistical outlier detection utilities
"""

from __future__ import annotations

from typing import List, Optional, Tuple, Union

import numpy as np


class BaseOutlierDetector:
    """Base class for outlier detectors."""

    def __init__(self):
        self.is_fitted_: bool = False

    def _check_is_fitted(self) -> None:
        """Check if estimator is fitted."""
        if not self.is_fitted_:
            raise ValueError("Estimator not fitted. Call fit() first.")

    def fit_predict(self, X: np.ndarray) -> np.ndarray:
        """Fit and return outlier labels."""
        self.fit(X)
        return self.predict(X)


class IsolationForest(BaseOutlierDetector):
    """
    Isolation Forest for anomaly detection.

    Isolates observations by randomly selecting features and split values.
    Anomalies require fewer splits to isolate.

    Parameters
    ----------
    n_estimators : int, default=100
        Number of isolation trees.
    max_samples : int or float, default='auto'
        Number of samples to draw. 'auto' uses min(256, n_samples).
    contamination : float, default=0.1
        Expected proportion of outliers.
    max_features : float, default=1.0
        Fraction of features to draw.
    random_state : int, default=None
        Random seed.

    Attributes
    ----------
    threshold_ : float
        Score threshold for outlier classification.

    Examples
    --------
    >>> from sdk.outlier import IsolationForest
    >>> iso = IsolationForest(contamination=0.1)
    >>> iso.fit(X_train)
    >>> predictions = iso.predict(X_test)  # -1 for outliers, 1 for inliers
    """

    def __init__(
        self,
        n_estimators: int = 100,
        max_samples: Union[str, int, float] = "auto",
        contamination: float = 0.1,
        max_features: float = 1.0,
        random_state: Optional[int] = None,
    ):
        super().__init__()
        self.n_estimators = n_estimators
        self.max_samples = max_samples
        self.contamination = contamination
        self.max_features = max_features
        self.random_state = random_state
        self.trees_: List[IsolationTree] = []
        self.threshold_: float = 0.0
        self._max_samples: int = 0

    def fit(self, X: np.ndarray, y: np.ndarray = None) -> IsolationForest:
        """
        Fit the isolation forest.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : Ignored
            Not used, present for API compatibility.

        Returns
        -------
        self : IsolationForest
            Fitted estimator.
        """
        X = np.asarray(X)
        n_samples, n_features = X.shape

        if self.random_state is not None:
            np.random.seed(self.random_state)

        # Determine max_samples
        if self.max_samples == "auto":
            self._max_samples = min(256, n_samples)
        elif isinstance(self.max_samples, float):
            self._max_samples = int(self.max_samples * n_samples)
        else:
            self._max_samples = self.max_samples

        # Determine features per tree
        n_features_tree = max(1, int(self.max_features * n_features))

        # Build isolation trees
        self.trees_ = []
        for _ in range(self.n_estimators):
            # Sample data
            sample_idx = np.random.choice(n_samples, self._max_samples, replace=False)
            feature_idx = np.random.choice(n_features, n_features_tree, replace=False)

            X_sample = X[np.ix_(sample_idx, feature_idx)]

            # Build tree
            tree = IsolationTree(max_depth=int(np.ceil(np.log2(self._max_samples))))
            tree.fit(X_sample)
            tree.feature_idx_ = feature_idx
            self.trees_.append(tree)

        # Calculate threshold from training data
        scores = self.score_samples(X)
        self.threshold_ = np.percentile(scores, 100 * self.contamination)

        self.is_fitted_ = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict outlier labels.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        y_pred : array of shape (n_samples,)
            -1 for outliers, 1 for inliers.
        """
        self._check_is_fitted()
        scores = self.score_samples(X)
        return np.where(scores < self.threshold_, -1, 1)

    def score_samples(self, X: np.ndarray) -> np.ndarray:
        """
        Return anomaly scores.

        Lower scores indicate more anomalous samples.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        scores : array of shape (n_samples,)
            Anomaly scores.
        """
        self._check_is_fitted()
        X = np.asarray(X)
        n_samples = X.shape[0]

        # Average path length across all trees
        path_lengths = np.zeros(n_samples)
        for tree in self.trees_:
            X_tree = X[:, tree.feature_idx_]
            path_lengths += tree.path_length(X_tree)

        path_lengths /= self.n_estimators

        # Convert to anomaly score
        # Score = 2^(-E(h(x)) / c(n))
        # where c(n) is average path length of unsuccessful search in BST
        c_n = self._average_path_length(self._max_samples)
        scores = 2 ** (-path_lengths / c_n)

        # Invert so lower = more anomalous
        return -scores

    def _average_path_length(self, n: int) -> float:
        """Calculate average path length for n samples."""
        if n <= 1:
            return 0
        elif n == 2:
            return 1
        else:
            # H(n-1) approximation
            euler_gamma = 0.5772156649
            h = np.log(n - 1) + euler_gamma
            return 2 * h - (2 * (n - 1) / n)

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """Return decision scores (positive = inlier, negative = outlier)."""
        return -self.score_samples(X) - (-self.threshold_)


class IsolationTree:
    """Single isolation tree."""

    def __init__(self, max_depth: int = 10):
        self.max_depth = max_depth
        self.root: Optional[IsolationNode] = None
        self.feature_idx_: np.ndarray = np.array([])

    def fit(self, X: np.ndarray) -> IsolationTree:
        """Build the isolation tree."""
        self.root = self._build_tree(X, depth=0)
        return self

    def _build_tree(self, X: np.ndarray, depth: int) -> IsolationNode:
        """Recursively build tree."""
        n_samples, n_features = X.shape

        # External node
        if depth >= self.max_depth or n_samples <= 1:
            return IsolationNode(size=n_samples)

        # Random split
        feature = np.random.randint(n_features)
        min_val, max_val = X[:, feature].min(), X[:, feature].max()

        if min_val == max_val:
            return IsolationNode(size=n_samples)

        split_value = np.random.uniform(min_val, max_val)

        # Split data
        left_mask = X[:, feature] < split_value
        right_mask = ~left_mask

        node = IsolationNode(
            feature=feature,
            split_value=split_value,
            left=self._build_tree(X[left_mask], depth + 1),
            right=self._build_tree(X[right_mask], depth + 1),
        )
        return node

    def path_length(self, X: np.ndarray) -> np.ndarray:
        """Calculate path length for each sample."""
        return np.array([self._path_length_single(x, self.root, 0) for x in X])

    def _path_length_single(self, x: np.ndarray, node: IsolationNode, current_depth: int) -> float:
        """Calculate path length for a single sample."""
        if node.is_external:
            # Add correction for unbuilt subtree
            return current_depth + self._c(node.size)

        if x[node.feature] < node.split_value:
            return self._path_length_single(x, node.left, current_depth + 1)
        else:
            return self._path_length_single(x, node.right, current_depth + 1)

    def _c(self, n: int) -> float:
        """Average path length adjustment."""
        if n <= 1:
            return 0
        elif n == 2:
            return 1
        else:
            h = np.log(n - 1) + 0.5772156649
            return 2 * h - (2 * (n - 1) / n)


class IsolationNode:
    """Node in an isolation tree."""

    def __init__(
        self,
        feature: Optional[int] = None,
        split_value: Optional[float] = None,
        left: Optional[IsolationNode] = None,
        right: Optional[IsolationNode] = None,
        size: int = 0,
    ):
        self.feature = feature
        self.split_value = split_value
        self.left = left
        self.right = right
        self.size = size

    @property
    def is_external(self) -> bool:
        """Check if this is an external (leaf) node."""
        return self.left is None and self.right is None


class LocalOutlierFactor(BaseOutlierDetector):
    """
    Local Outlier Factor for density-based anomaly detection.

    Measures local deviation of density of a sample with respect to neighbors.

    Parameters
    ----------
    n_neighbors : int, default=20
        Number of neighbors to use.
    contamination : float, default=0.1
        Expected proportion of outliers.
    metric : str, default='euclidean'
        Distance metric.
    novelty : bool, default=False
        If True, use for novelty detection (predict on new data).

    Examples
    --------
    >>> from sdk.outlier import LocalOutlierFactor
    >>> lof = LocalOutlierFactor(n_neighbors=20)
    >>> predictions = lof.fit_predict(X)
    """

    def __init__(
        self,
        n_neighbors: int = 20,
        contamination: float = 0.1,
        metric: str = "euclidean",
        novelty: bool = False,
    ):
        super().__init__()
        self.n_neighbors = n_neighbors
        self.contamination = contamination
        self.metric = metric
        self.novelty = novelty
        self.X_fit_: Optional[np.ndarray] = None
        self.threshold_: float = 0.0
        self._lrd_: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray, y: np.ndarray = None) -> LocalOutlierFactor:
        """Fit the LOF model."""
        X = np.asarray(X)
        self.X_fit_ = X
        n_samples = X.shape[0]

        # Calculate k-distances and neighbors for all points
        k = min(self.n_neighbors, n_samples - 1)

        # Distance matrix
        distances = self._compute_distances(X, X)

        # For each point, find k nearest neighbors
        self._k_distances_ = np.zeros(n_samples)
        self._neighbors_ = []

        for i in range(n_samples):
            # Sort distances (excluding self)
            dist_i = distances[i].copy()
            dist_i[i] = np.inf
            sorted_idx = np.argsort(dist_i)[:k]
            self._neighbors_.append(sorted_idx)
            self._k_distances_[i] = dist_i[sorted_idx[-1]]

        # Calculate local reachability density
        self._lrd_ = self._compute_lrd(X, distances)

        # Calculate LOF scores for training data
        if not self.novelty:
            lof_scores = self._compute_lof(X, distances)
            self.threshold_ = np.percentile(-lof_scores, 100 * (1 - self.contamination))

        self.is_fitted_ = True
        return self

    def _compute_distances(self, X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
        """Compute pairwise distances."""
        if self.metric == "euclidean":
            # Efficient computation
            X1_sq = np.sum(X1**2, axis=1, keepdims=True)
            X2_sq = np.sum(X2**2, axis=1, keepdims=True)
            cross = np.dot(X1, X2.T)
            distances = np.sqrt(np.maximum(X1_sq + X2_sq.T - 2 * cross, 0))
        elif self.metric == "manhattan":
            distances = np.sum(np.abs(X1[:, np.newaxis] - X2), axis=2)
        else:
            # Default to euclidean
            distances = np.sqrt(np.sum((X1[:, np.newaxis] - X2) ** 2, axis=2))
        return distances

    def _compute_lrd(self, X: np.ndarray, distances: np.ndarray) -> np.ndarray:
        """Compute local reachability density."""
        n_samples = X.shape[0]
        min(self.n_neighbors, n_samples - 1)
        lrd = np.zeros(n_samples)

        for i in range(n_samples):
            reach_distances = []
            for j in self._neighbors_[i]:
                # Reachability distance = max(k-distance(j), d(i,j))
                reach_dist = max(self._k_distances_[j], distances[i, j])
                reach_distances.append(reach_dist)

            avg_reach = np.mean(reach_distances)
            lrd[i] = 1.0 / avg_reach if avg_reach > 0 else np.inf

        return lrd

    def _compute_lof(self, X: np.ndarray, distances: np.ndarray) -> np.ndarray:
        """Compute LOF scores."""
        n_samples = X.shape[0]
        lof = np.zeros(n_samples)

        for i in range(n_samples):
            neighbor_lrd = self._lrd_[self._neighbors_[i]]
            lof[i] = np.mean(neighbor_lrd) / self._lrd_[i] if self._lrd_[i] > 0 else np.inf

        return lof

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict outlier labels."""
        self._check_is_fitted()

        if not self.novelty:
            # Use fit data
            scores = self.score_samples(self.X_fit_)
        else:
            scores = self.score_samples(X)

        return np.where(scores < self.threshold_, -1, 1)

    def fit_predict(self, X: np.ndarray) -> np.ndarray:
        """Fit and predict outlier labels."""
        self.fit(X)
        distances = self._compute_distances(X, X)
        lof_scores = self._compute_lof(X, distances)
        threshold = np.percentile(lof_scores, 100 * (1 - self.contamination))
        return np.where(lof_scores > threshold, -1, 1)

    def score_samples(self, X: np.ndarray) -> np.ndarray:
        """Return negative LOF scores (higher = more normal)."""
        self._check_is_fitted()
        X = np.asarray(X)

        if np.array_equal(X, self.X_fit_):
            distances = self._compute_distances(X, X)
            lof_scores = self._compute_lof(X, distances)
        else:
            # New data - compute against training data
            distances = self._compute_distances(X, self.X_fit_)
            n_samples = X.shape[0]
            k = min(self.n_neighbors, self.X_fit_.shape[0])

            lof_scores = np.zeros(n_samples)
            for i in range(n_samples):
                sorted_idx = np.argsort(distances[i])[:k]
                distances[i, sorted_idx[-1]]

                reach_distances = []
                for j in sorted_idx:
                    reach_dist = max(self._k_distances_[j], distances[i, j])
                    reach_distances.append(reach_dist)

                avg_reach = np.mean(reach_distances)
                lrd_i = 1.0 / avg_reach if avg_reach > 0 else np.inf

                neighbor_lrd = self._lrd_[sorted_idx]
                lof_scores[i] = np.mean(neighbor_lrd) / lrd_i if lrd_i > 0 else np.inf

        return -lof_scores


class EllipticEnvelope(BaseOutlierDetector):
    """
    Outlier detection using Gaussian distribution.

    Fits a robust covariance estimate and classifies outliers based on
    Mahalanobis distance.

    Parameters
    ----------
    contamination : float, default=0.1
        Expected proportion of outliers.
    support_fraction : float, default=None
        Proportion of points used for robust estimate.
    random_state : int, default=None
        Random seed.

    Examples
    --------
    >>> from sdk.outlier import EllipticEnvelope
    >>> ee = EllipticEnvelope(contamination=0.1)
    >>> ee.fit(X_train)
    >>> predictions = ee.predict(X_test)
    """

    def __init__(
        self,
        contamination: float = 0.1,
        support_fraction: Optional[float] = None,
        random_state: Optional[int] = None,
    ):
        super().__init__()
        self.contamination = contamination
        self.support_fraction = support_fraction
        self.random_state = random_state
        self.location_: Optional[np.ndarray] = None
        self.covariance_: Optional[np.ndarray] = None
        self.precision_: Optional[np.ndarray] = None
        self.threshold_: float = 0.0

    def fit(self, X: np.ndarray, y: np.ndarray = None) -> EllipticEnvelope:
        """Fit the elliptic envelope."""
        X = np.asarray(X)
        n_samples, n_features = X.shape

        if self.random_state is not None:
            np.random.seed(self.random_state)

        # Use robust covariance estimation (simplified MCD)
        if self.support_fraction is not None:
            h = int(self.support_fraction * n_samples)
        else:
            h = int((n_samples + n_features + 1) / 2)

        # Simple approach: use trimmed mean and covariance
        self.location_, self.covariance_ = self._robust_estimate(X, h)

        # Compute precision matrix (inverse of covariance)
        try:
            self.precision_ = np.linalg.inv(self.covariance_)
        except np.linalg.LinAlgError:
            # Add small regularization if singular
            self.precision_ = np.linalg.inv(self.covariance_ + 1e-6 * np.eye(n_features))

        # Calculate threshold
        distances = self.mahalanobis(X)
        self.threshold_ = np.percentile(distances, 100 * (1 - self.contamination))

        self.is_fitted_ = True
        return self

    def _robust_estimate(self, X: np.ndarray, h: int) -> Tuple[np.ndarray, np.ndarray]:
        """Compute robust location and covariance estimates."""
        X.shape[0]

        # Initial estimate using all data
        mean = np.mean(X, axis=0)
        cov = np.cov(X, rowvar=False)

        if cov.ndim == 0:
            cov = np.array([[cov]])

        # Iteratively refine
        for _ in range(10):
            try:
                precision = np.linalg.inv(cov + 1e-10 * np.eye(cov.shape[0]))
            except np.linalg.LinAlgError:
                break

            # Calculate Mahalanobis distances
            diff = X - mean
            distances = np.sum(diff @ precision * diff, axis=1)

            # Select h points with smallest distances
            idx = np.argsort(distances)[:h]

            # Update estimates
            mean = np.mean(X[idx], axis=0)
            cov = np.cov(X[idx], rowvar=False)

            if cov.ndim == 0:
                cov = np.array([[cov]])

        return mean, cov

    def mahalanobis(self, X: np.ndarray) -> np.ndarray:
        """Calculate Mahalanobis distances."""
        self._check_is_fitted()
        X = np.asarray(X)

        diff = X - self.location_
        left = diff @ self.precision_
        distances = np.sum(left * diff, axis=1)
        return np.sqrt(np.maximum(distances, 0))

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict outlier labels."""
        distances = self.mahalanobis(X)
        return np.where(distances > self.threshold_, -1, 1)

    def score_samples(self, X: np.ndarray) -> np.ndarray:
        """Return negative Mahalanobis distances."""
        return -self.mahalanobis(X)

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """Return decision scores."""
        return self.threshold_ - self.mahalanobis(X)


class OneClassSVM(BaseOutlierDetector):
    """
    One-Class SVM for novelty detection.

    Learns a decision boundary around normal data.

    Parameters
    ----------
    kernel : str, default='rbf'
        Kernel type ('rbf', 'linear', 'poly', 'sigmoid').
    nu : float, default=0.1
        Upper bound on fraction of outliers.
    gamma : float or str, default='scale'
        Kernel coefficient.
    degree : int, default=3
        Degree for polynomial kernel.

    Examples
    --------
    >>> from sdk.outlier import OneClassSVM
    >>> ocsvm = OneClassSVM(nu=0.1)
    >>> ocsvm.fit(X_train)
    >>> predictions = ocsvm.predict(X_test)
    """

    def __init__(
        self,
        kernel: str = "rbf",
        nu: float = 0.1,
        gamma: Union[str, float] = "scale",
        degree: int = 3,
    ):
        super().__init__()
        self.kernel = kernel
        self.nu = nu
        self.gamma = gamma
        self.degree = degree
        self.support_vectors_: Optional[np.ndarray] = None
        self.dual_coef_: Optional[np.ndarray] = None
        self.intercept_: float = 0.0
        self._gamma_value: float = 1.0

    def fit(self, X: np.ndarray, y: np.ndarray = None) -> OneClassSVM:
        """Fit the one-class SVM."""
        X = np.asarray(X)
        n_samples, n_features = X.shape

        # Set gamma
        if self.gamma == "scale":
            self._gamma_value = 1.0 / (n_features * X.var())
        elif self.gamma == "auto":
            self._gamma_value = 1.0 / n_features
        else:
            self._gamma_value = self.gamma

        # Compute kernel matrix
        K = self._compute_kernel(X, X)

        # Simplified one-class SVM using kernel PCA-like approach
        # Find support vectors based on distance from center in feature space
        center_scores = np.mean(K, axis=1)
        threshold_idx = int(n_samples * (1 - self.nu))
        sorted_idx = np.argsort(center_scores)

        # Use top samples as support vectors
        sv_idx = sorted_idx[-threshold_idx:]
        self.support_vectors_ = X[sv_idx]
        self.dual_coef_ = np.ones(len(sv_idx)) / len(sv_idx)

        # Calculate intercept
        decision_values = self._decision_function_raw(X)
        self.intercept_ = np.percentile(decision_values, 100 * self.nu)

        self.is_fitted_ = True
        return self

    def _compute_kernel(self, X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
        """Compute kernel matrix."""
        if self.kernel == "linear":
            return np.dot(X1, X2.T)
        elif self.kernel == "rbf":
            # RBF kernel: exp(-gamma * ||x - y||^2)
            X1_sq = np.sum(X1**2, axis=1, keepdims=True)
            X2_sq = np.sum(X2**2, axis=1, keepdims=True)
            cross = np.dot(X1, X2.T)
            distances_sq = X1_sq + X2_sq.T - 2 * cross
            return np.exp(-self._gamma_value * distances_sq)
        elif self.kernel == "poly":
            return (self._gamma_value * np.dot(X1, X2.T) + 1) ** self.degree
        elif self.kernel == "sigmoid":
            return np.tanh(self._gamma_value * np.dot(X1, X2.T))
        else:
            return np.dot(X1, X2.T)

    def _decision_function_raw(self, X: np.ndarray) -> np.ndarray:
        """Raw decision function without intercept."""
        K = self._compute_kernel(X, self.support_vectors_)
        return np.dot(K, self.dual_coef_)

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """Return signed distance to separating hyperplane."""
        self._check_is_fitted()
        return self._decision_function_raw(X) - self.intercept_

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict outlier labels."""
        decision = self.decision_function(X)
        return np.where(decision < 0, -1, 1)

    def score_samples(self, X: np.ndarray) -> np.ndarray:
        """Return raw decision scores."""
        return self.decision_function(X)


# Statistical outlier detection utilities


def detect_outliers_zscore(
    X: np.ndarray,
    threshold: float = 3.0,
) -> np.ndarray:
    """
    Detect outliers using Z-score method.

    Parameters
    ----------
    X : array-like of shape (n_samples, n_features)
        Data.
    threshold : float, default=3.0
        Z-score threshold.

    Returns
    -------
    outliers : array of shape (n_samples,)
        Boolean mask (True for outliers).
    """
    X = np.asarray(X)
    mean = np.mean(X, axis=0)
    std = np.std(X, axis=0)

    # Avoid division by zero
    std = np.where(std == 0, 1, std)

    z_scores = np.abs((X - mean) / std)
    return np.any(z_scores > threshold, axis=1)


def detect_outliers_iqr(
    X: np.ndarray,
    k: float = 1.5,
) -> np.ndarray:
    """
    Detect outliers using IQR (Interquartile Range) method.

    Parameters
    ----------
    X : array-like of shape (n_samples, n_features)
        Data.
    k : float, default=1.5
        IQR multiplier.

    Returns
    -------
    outliers : array of shape (n_samples,)
        Boolean mask (True for outliers).
    """
    X = np.asarray(X)
    q1 = np.percentile(X, 25, axis=0)
    q3 = np.percentile(X, 75, axis=0)
    iqr = q3 - q1

    lower = q1 - k * iqr
    upper = q3 + k * iqr

    return np.any((X < lower) | (X > upper), axis=1)


def detect_outliers_mad(
    X: np.ndarray,
    threshold: float = 3.5,
) -> np.ndarray:
    """
    Detect outliers using MAD (Median Absolute Deviation) method.

    More robust than Z-score for non-normal distributions.

    Parameters
    ----------
    X : array-like of shape (n_samples, n_features)
        Data.
    threshold : float, default=3.5
        Modified Z-score threshold.

    Returns
    -------
    outliers : array of shape (n_samples,)
        Boolean mask (True for outliers).
    """
    X = np.asarray(X)
    median = np.median(X, axis=0)
    mad = np.median(np.abs(X - median), axis=0)

    # Avoid division by zero
    mad = np.where(mad == 0, 1, mad)

    # Modified Z-score
    modified_z = 0.6745 * (X - median) / mad
    return np.any(np.abs(modified_z) > threshold, axis=1)


def detect_outliers_dbscan(
    X: np.ndarray,
    eps: float = 0.5,
    min_samples: int = 5,
) -> np.ndarray:
    """
    Detect outliers using DBSCAN clustering.

    Points not belonging to any cluster are outliers.

    Parameters
    ----------
    X : array-like of shape (n_samples, n_features)
        Data.
    eps : float, default=0.5
        Maximum distance between samples.
    min_samples : int, default=5
        Minimum samples in a neighborhood.

    Returns
    -------
    outliers : array of shape (n_samples,)
        Boolean mask (True for outliers).
    """
    X = np.asarray(X)
    n_samples = X.shape[0]

    # Calculate distance matrix
    distances = np.sqrt(np.sum((X[:, np.newaxis] - X) ** 2, axis=2))

    # Find neighbors within eps
    neighbors = [np.where(distances[i] <= eps)[0] for i in range(n_samples)]

    # Find core points
    core_points = np.array([len(n) >= min_samples for n in neighbors])

    # Cluster assignment
    labels = np.full(n_samples, -1)
    cluster_id = 0

    for i in range(n_samples):
        if labels[i] != -1 or not core_points[i]:
            continue

        # Start new cluster
        stack = [i]
        while stack:
            point = stack.pop()
            if labels[point] == -1:
                labels[point] = cluster_id
                if core_points[point]:
                    for neighbor in neighbors[point]:
                        if labels[neighbor] == -1:
                            stack.append(neighbor)

        cluster_id += 1

    # Outliers have label -1
    return labels == -1


def get_outlier_scores(
    X: np.ndarray,
    method: str = "isolation_forest",
    **kwargs,
) -> np.ndarray:
    """
    Get outlier scores using specified method.

    Parameters
    ----------
    X : array-like of shape (n_samples, n_features)
        Data.
    method : str, default='isolation_forest'
        Method ('isolation_forest', 'lof', 'elliptic', 'ocsvm').
    **kwargs : dict
        Parameters for the detector.

    Returns
    -------
    scores : array of shape (n_samples,)
        Outlier scores (lower = more anomalous).
    """
    detectors = {
        "isolation_forest": IsolationForest,
        "lof": LocalOutlierFactor,
        "elliptic": EllipticEnvelope,
        "ocsvm": OneClassSVM,
    }

    if method not in detectors:
        raise ValueError(f"Unknown method: {method}. Use one of {list(detectors.keys())}")

    detector = detectors[method](**kwargs)
    detector.fit(X)
    return detector.score_samples(X)

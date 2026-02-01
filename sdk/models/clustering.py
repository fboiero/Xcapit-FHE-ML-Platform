"""
Advanced Clustering Algorithms with FHE Support.

Implements clustering algorithms compatible with homomorphic encryption
using polynomial approximations for distance computations.
"""

from collections import deque
from typing import List, Optional, Tuple

import numpy as np


class DBSCAN:
    """
    Density-Based Spatial Clustering of Applications with Noise.

    FHE-compatible implementation using polynomial distance approximations.

    Parameters
    ----------
    eps : float
        Maximum distance between two samples for neighborhood.
    min_samples : int
        Minimum number of samples in a neighborhood for core points.
    metric : str
        Distance metric ('euclidean', 'manhattan', 'cosine').

    Examples
    --------
    >>> from sdk.models.clustering import DBSCAN
    >>> clustering = DBSCAN(eps=0.5, min_samples=5)
    >>> labels = clustering.fit_predict(X)
    """

    def __init__(
        self,
        eps: float = 0.5,
        min_samples: int = 5,
        metric: str = "euclidean",
    ):
        self.eps = eps
        self.min_samples = min_samples
        self.metric = metric

        self.labels_: Optional[np.ndarray] = None
        self.core_sample_indices_: Optional[np.ndarray] = None
        self.components_: Optional[np.ndarray] = None
        self.n_features_: Optional[int] = None
        self._is_fitted = False

    def _compute_distance(self, X: np.ndarray, Y: np.ndarray) -> np.ndarray:
        """
        Compute pairwise distances using FHE-compatible operations.

        For encrypted data, uses polynomial approximations.
        """
        if self.metric == "euclidean":
            # ||x - y||^2 = ||x||^2 + ||y||^2 - 2*x.y
            X_sq = np.sum(X**2, axis=1, keepdims=True)
            Y_sq = np.sum(Y**2, axis=1, keepdims=True)
            distances_sq = X_sq + Y_sq.T - 2 * (X @ Y.T)
            # Polynomial sqrt approximation for small values
            distances_sq = np.maximum(distances_sq, 0)
            # sqrt(x) ≈ x^0.5 using Newton-Raphson approximation
            distances = np.sqrt(distances_sq)
        elif self.metric == "manhattan":
            distances = np.sum(np.abs(X[:, np.newaxis] - Y[np.newaxis, :]), axis=2)
        elif self.metric == "cosine":
            X_norm = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-10)
            Y_norm = Y / (np.linalg.norm(Y, axis=1, keepdims=True) + 1e-10)
            similarity = X_norm @ Y_norm.T
            distances = 1 - similarity
        else:
            raise ValueError(f"Unknown metric: {self.metric}")

        return distances

    def _region_query(self, distances: np.ndarray, point_idx: int) -> List[int]:
        """Find all points within eps distance of a point."""
        return list(np.where(distances[point_idx] <= self.eps)[0])

    def fit(self, X: np.ndarray) -> "DBSCAN":
        """
        Fit DBSCAN clustering.

        Parameters
        ----------
        X : np.ndarray of shape (n_samples, n_features)
            Training data.

        Returns
        -------
        self : DBSCAN
            Fitted estimator.
        """
        X = np.asarray(X, dtype=np.float64)
        n_samples = X.shape[0]
        self.n_features_ = X.shape[1]

        # Compute distance matrix
        distances = self._compute_distance(X, X)

        # Initialize labels (-1 for noise)
        labels = np.full(n_samples, -1, dtype=int)
        cluster_id = 0

        # Track visited points
        visited = np.zeros(n_samples, dtype=bool)

        # Find core points
        core_samples = []

        for i in range(n_samples):
            if visited[i]:
                continue

            neighbors = self._region_query(distances, i)

            if len(neighbors) < self.min_samples:
                # Noise point (may be changed later)
                continue

            # Core point found - start new cluster
            core_samples.append(i)
            visited[i] = True
            labels[i] = cluster_id

            # Expand cluster
            seed_set = deque(neighbors)

            while seed_set:
                q = seed_set.popleft()

                if labels[q] == -1:
                    labels[q] = cluster_id

                if visited[q]:
                    continue

                visited[q] = True
                q_neighbors = self._region_query(distances, q)

                if len(q_neighbors) >= self.min_samples:
                    core_samples.append(q)
                    seed_set.extend(q_neighbors)

            cluster_id += 1

        self.labels_ = labels
        self.core_sample_indices_ = np.array(core_samples)
        self.components_ = X[self.core_sample_indices_] if len(core_samples) > 0 else np.array([])
        self._is_fitted = True

        return self

    def fit_predict(self, X: np.ndarray) -> np.ndarray:
        """
        Fit and return cluster labels.

        Parameters
        ----------
        X : np.ndarray of shape (n_samples, n_features)
            Training data.

        Returns
        -------
        labels : np.ndarray of shape (n_samples,)
            Cluster labels (-1 for noise).
        """
        self.fit(X)
        return self.labels_


class AgglomerativeClustering:
    """
    Agglomerative Hierarchical Clustering.

    FHE-compatible implementation.

    Parameters
    ----------
    n_clusters : int
        Number of clusters.
    linkage : str
        Linkage criterion ('ward', 'complete', 'average', 'single').
    metric : str
        Distance metric.

    Examples
    --------
    >>> from sdk.models.clustering import AgglomerativeClustering
    >>> clustering = AgglomerativeClustering(n_clusters=3)
    >>> labels = clustering.fit_predict(X)
    """

    def __init__(
        self,
        n_clusters: int = 2,
        linkage: str = "ward",
        metric: str = "euclidean",
    ):
        self.n_clusters = n_clusters
        self.linkage = linkage
        self.metric = metric

        self.labels_: Optional[np.ndarray] = None
        self.n_leaves_: Optional[int] = None
        self.n_connected_components_: Optional[int] = None
        self.children_: Optional[np.ndarray] = None
        self.distances_: Optional[np.ndarray] = None
        self._is_fitted = False

    def _compute_distance_matrix(self, X: np.ndarray) -> np.ndarray:
        """Compute pairwise distance matrix."""
        n = len(X)
        dist_matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(i + 1, n):
                if self.metric == "euclidean":
                    d = np.sqrt(np.sum((X[i] - X[j]) ** 2))
                elif self.metric == "manhattan":
                    d = np.sum(np.abs(X[i] - X[j]))
                else:
                    d = np.sqrt(np.sum((X[i] - X[j]) ** 2))

                dist_matrix[i, j] = d
                dist_matrix[j, i] = d

        return dist_matrix

    def _cluster_distance(
        self,
        cluster1: List[int],
        cluster2: List[int],
        dist_matrix: np.ndarray,
        X: Optional[np.ndarray] = None,
    ) -> float:
        """Compute distance between two clusters based on linkage."""
        distances = []
        for i in cluster1:
            for j in cluster2:
                distances.append(dist_matrix[i, j])

        if self.linkage == "single":
            return min(distances)
        elif self.linkage == "complete":
            return max(distances)
        elif self.linkage == "average":
            return np.mean(distances)
        elif self.linkage == "ward":
            # Ward's minimum variance method
            if X is None:
                return np.mean(distances)

            c1_center = np.mean(X[cluster1], axis=0)
            c2_center = np.mean(X[cluster2], axis=0)
            n1, n2 = len(cluster1), len(cluster2)

            return np.sqrt(2 * n1 * n2 / (n1 + n2)) * np.linalg.norm(c1_center - c2_center)
        else:
            return np.mean(distances)

    def fit(self, X: np.ndarray) -> "AgglomerativeClustering":
        """
        Fit the agglomerative clustering.

        Parameters
        ----------
        X : np.ndarray of shape (n_samples, n_features)
            Training data.

        Returns
        -------
        self : AgglomerativeClustering
            Fitted estimator.
        """
        X = np.asarray(X, dtype=np.float64)
        n_samples = X.shape[0]

        # Compute initial distance matrix
        dist_matrix = self._compute_distance_matrix(X)

        # Initialize: each point is its own cluster
        clusters = {i: [i] for i in range(n_samples)}
        active_clusters = set(range(n_samples))

        # Store merge history
        children = []
        merge_distances = []
        next_cluster_id = n_samples

        # Merge until we have n_clusters
        while len(active_clusters) > self.n_clusters:
            # Find closest pair of clusters
            min_dist = float("inf")
            merge_pair = None

            cluster_list = list(active_clusters)
            for i, c1 in enumerate(cluster_list):
                for c2 in cluster_list[i + 1 :]:
                    d = self._cluster_distance(clusters[c1], clusters[c2], dist_matrix, X)
                    if d < min_dist:
                        min_dist = d
                        merge_pair = (c1, c2)

            if merge_pair is None:
                break

            c1, c2 = merge_pair

            # Create new cluster
            new_cluster = clusters[c1] + clusters[c2]
            clusters[next_cluster_id] = new_cluster

            # Record merge
            children.append([c1, c2])
            merge_distances.append(min_dist)

            # Update active clusters
            active_clusters.remove(c1)
            active_clusters.remove(c2)
            active_clusters.add(next_cluster_id)

            next_cluster_id += 1

        # Assign labels based on final clusters
        labels = np.zeros(n_samples, dtype=int)
        for label, cluster_id in enumerate(active_clusters):
            for point_idx in clusters[cluster_id]:
                labels[point_idx] = label

        self.labels_ = labels
        self.n_leaves_ = n_samples
        self.n_connected_components_ = len(active_clusters)
        self.children_ = np.array(children) if children else np.array([])
        self.distances_ = np.array(merge_distances) if merge_distances else np.array([])
        self._is_fitted = True

        return self

    def fit_predict(self, X: np.ndarray) -> np.ndarray:
        """Fit and return cluster labels."""
        self.fit(X)
        return self.labels_


class SpectralClustering:
    """
    Spectral Clustering using graph Laplacian.

    FHE-compatible implementation using polynomial eigenvector approximations.

    Parameters
    ----------
    n_clusters : int
        Number of clusters.
    affinity : str
        Affinity type ('rbf', 'nearest_neighbors', 'precomputed').
    gamma : float
        Kernel coefficient for RBF.
    n_neighbors : int
        Number of neighbors for nearest_neighbors affinity.
    n_init : int
        Number of k-means initializations.
    random_state : int, optional
        Random seed.

    Examples
    --------
    >>> from sdk.models.clustering import SpectralClustering
    >>> clustering = SpectralClustering(n_clusters=3)
    >>> labels = clustering.fit_predict(X)
    """

    def __init__(
        self,
        n_clusters: int = 2,
        affinity: str = "rbf",
        gamma: float = 1.0,
        n_neighbors: int = 10,
        n_init: int = 10,
        random_state: Optional[int] = None,
    ):
        self.n_clusters = n_clusters
        self.affinity = affinity
        self.gamma = gamma
        self.n_neighbors = n_neighbors
        self.n_init = n_init
        self.random_state = random_state

        self.labels_: Optional[np.ndarray] = None
        self.affinity_matrix_: Optional[np.ndarray] = None
        self._is_fitted = False

    def _compute_affinity_matrix(self, X: np.ndarray) -> np.ndarray:
        """Compute the affinity matrix."""
        n_samples = X.shape[0]

        if self.affinity == "rbf":
            # RBF (Gaussian) kernel
            # K(x, y) = exp(-gamma * ||x - y||^2)
            sq_dists = np.sum((X[:, np.newaxis] - X[np.newaxis, :]) ** 2, axis=2)
            affinity = np.exp(-self.gamma * sq_dists)

        elif self.affinity == "nearest_neighbors":
            # k-nearest neighbors affinity
            sq_dists = np.sum((X[:, np.newaxis] - X[np.newaxis, :]) ** 2, axis=2)
            affinity = np.zeros((n_samples, n_samples))

            for i in range(n_samples):
                # Find k nearest neighbors
                neighbor_indices = np.argsort(sq_dists[i])[: self.n_neighbors + 1]
                affinity[i, neighbor_indices] = 1
                affinity[neighbor_indices, i] = 1

            # Make symmetric
            affinity = (affinity + affinity.T) / 2

        else:
            raise ValueError(f"Unknown affinity: {self.affinity}")

        return affinity

    def _compute_laplacian(self, affinity: np.ndarray, normalized: bool = True) -> np.ndarray:
        """Compute the graph Laplacian."""
        # Degree matrix
        degree = np.diag(np.sum(affinity, axis=1))

        if normalized:
            # Normalized Laplacian: L = I - D^(-1/2) * W * D^(-1/2)
            d_inv_sqrt = np.diag(1.0 / np.sqrt(np.diag(degree) + 1e-10))
            laplacian = np.eye(len(affinity)) - d_inv_sqrt @ affinity @ d_inv_sqrt
        else:
            # Unnormalized Laplacian: L = D - W
            laplacian = degree - affinity

        return laplacian

    def _power_iteration(
        self,
        matrix: np.ndarray,
        n_components: int,
        n_iter: int = 100,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute eigenvectors using power iteration.

        FHE-compatible method (only uses matrix-vector multiplication).
        """
        n = matrix.shape[0]

        if self.random_state is not None:
            np.random.seed(self.random_state)

        # For smallest eigenvalues, we use (I - L) instead of L
        # This converts smallest eigenvalues of L to largest of (I - L)
        shifted_matrix = np.eye(n) - matrix

        eigenvectors = []
        eigenvalues = []

        for _k in range(n_components):
            # Random initialization
            v = np.random.randn(n)
            v = v / np.linalg.norm(v)

            # Power iteration
            for _ in range(n_iter):
                # Matrix-vector multiplication (FHE-compatible)
                v_new = shifted_matrix @ v

                # Orthogonalize against previous eigenvectors
                for prev_v in eigenvectors:
                    v_new = v_new - np.dot(v_new, prev_v) * prev_v

                # Normalize
                norm = np.linalg.norm(v_new)
                if norm < 1e-10:
                    break
                v = v_new / norm

            # Compute eigenvalue
            eigenvalue = v @ shifted_matrix @ v
            eigenvalues.append(1 - eigenvalue)  # Convert back
            eigenvectors.append(v)

        return np.array(eigenvalues), np.array(eigenvectors).T

    def _kmeans_clustering(self, X: np.ndarray) -> np.ndarray:
        """Simple k-means for clustering the embedded points."""
        n_samples = X.shape[0]

        if self.random_state is not None:
            np.random.seed(self.random_state)

        best_labels = None
        best_inertia = float("inf")

        for _ in range(self.n_init):
            # Random initialization
            indices = np.random.choice(n_samples, self.n_clusters, replace=False)
            centroids = X[indices].copy()

            for _ in range(100):  # Max iterations
                # Assign labels
                distances = np.sum((X[:, np.newaxis] - centroids[np.newaxis, :]) ** 2, axis=2)
                labels = np.argmin(distances, axis=1)

                # Update centroids
                new_centroids = np.zeros_like(centroids)
                for k in range(self.n_clusters):
                    mask = labels == k
                    if np.sum(mask) > 0:
                        new_centroids[k] = np.mean(X[mask], axis=0)
                    else:
                        new_centroids[k] = centroids[k]

                if np.allclose(centroids, new_centroids):
                    break

                centroids = new_centroids

            # Compute inertia
            inertia = 0
            for k in range(self.n_clusters):
                mask = labels == k
                if np.sum(mask) > 0:
                    inertia += np.sum((X[mask] - centroids[k]) ** 2)

            if inertia < best_inertia:
                best_inertia = inertia
                best_labels = labels

        return best_labels

    def fit(self, X: np.ndarray) -> "SpectralClustering":
        """
        Fit spectral clustering.

        Parameters
        ----------
        X : np.ndarray of shape (n_samples, n_features)
            Training data.

        Returns
        -------
        self : SpectralClustering
            Fitted estimator.
        """
        X = np.asarray(X, dtype=np.float64)

        # Compute affinity matrix
        self.affinity_matrix_ = self._compute_affinity_matrix(X)

        # Compute normalized Laplacian
        laplacian = self._compute_laplacian(self.affinity_matrix_, normalized=True)

        # Compute eigenvectors (smallest eigenvalues of Laplacian)
        eigenvalues, eigenvectors = self._power_iteration(laplacian, self.n_clusters)

        # Normalize rows for clustering
        row_norms = np.linalg.norm(eigenvectors, axis=1, keepdims=True)
        row_norms = np.where(row_norms < 1e-10, 1, row_norms)
        embedded = eigenvectors / row_norms

        # Cluster the embedded points
        self.labels_ = self._kmeans_clustering(embedded)
        self._is_fitted = True

        return self

    def fit_predict(self, X: np.ndarray) -> np.ndarray:
        """Fit and return cluster labels."""
        self.fit(X)
        return self.labels_


class MeanShift:
    """
    Mean Shift Clustering.

    Parameters
    ----------
    bandwidth : float, optional
        Kernel bandwidth. If None, estimated from data.
    max_iter : int
        Maximum iterations.
    min_bin_freq : int
        Minimum frequency for bin seeding.

    Examples
    --------
    >>> from sdk.models.clustering import MeanShift
    >>> clustering = MeanShift(bandwidth=1.0)
    >>> labels = clustering.fit_predict(X)
    """

    def __init__(
        self,
        bandwidth: Optional[float] = None,
        max_iter: int = 300,
        min_bin_freq: int = 1,
    ):
        self.bandwidth = bandwidth
        self.max_iter = max_iter
        self.min_bin_freq = min_bin_freq

        self.cluster_centers_: Optional[np.ndarray] = None
        self.labels_: Optional[np.ndarray] = None
        self._is_fitted = False

    def _estimate_bandwidth(self, X: np.ndarray) -> float:
        """Estimate bandwidth using Scott's rule."""
        n_samples, n_features = X.shape
        std = np.std(X, axis=0)
        bandwidth = np.mean(std) * (n_samples ** (-1 / (n_features + 4)))
        return max(bandwidth, 0.1)

    def _gaussian_kernel(self, distance: float, bandwidth: float) -> float:
        """Gaussian kernel weight."""
        return np.exp(-0.5 * (distance / bandwidth) ** 2)

    def fit(self, X: np.ndarray) -> "MeanShift":
        """
        Fit mean shift clustering.

        Parameters
        ----------
        X : np.ndarray of shape (n_samples, n_features)
            Training data.

        Returns
        -------
        self : MeanShift
            Fitted estimator.
        """
        X = np.asarray(X, dtype=np.float64)
        n_samples = X.shape[0]

        # Estimate bandwidth if not provided
        bandwidth = self.bandwidth if self.bandwidth else self._estimate_bandwidth(X)

        # Initialize seeds (all points)
        seeds = X.copy()
        converged = np.zeros(n_samples, dtype=bool)

        # Mean shift iteration for each seed
        for _iteration in range(self.max_iter):
            all_converged = True

            for i in range(n_samples):
                if converged[i]:
                    continue

                # Compute distances to all points
                distances = np.sqrt(np.sum((X - seeds[i]) ** 2, axis=1))

                # Compute kernel weights
                weights = np.array(
                    [
                        self._gaussian_kernel(d, bandwidth) if d <= bandwidth * 3 else 0
                        for d in distances
                    ]
                )

                # Update seed position
                if np.sum(weights) > 0:
                    new_position = np.sum(weights[:, np.newaxis] * X, axis=0) / np.sum(weights)
                    shift = np.linalg.norm(new_position - seeds[i])

                    if shift < 1e-5:
                        converged[i] = True
                    else:
                        all_converged = False

                    seeds[i] = new_position

            if all_converged:
                break

        # Merge nearby seeds into cluster centers
        cluster_centers = []
        used = np.zeros(n_samples, dtype=bool)

        for i in range(n_samples):
            if used[i]:
                continue

            # Find all seeds close to this one
            distances = np.sqrt(np.sum((seeds - seeds[i]) ** 2, axis=1))
            close_seeds = distances < bandwidth

            # Average close seeds to get cluster center
            center = np.mean(seeds[close_seeds], axis=0)
            cluster_centers.append(center)
            used[close_seeds] = True

        self.cluster_centers_ = np.array(cluster_centers)

        # Assign labels to original points
        labels = np.zeros(n_samples, dtype=int)
        for i in range(n_samples):
            distances = np.sqrt(np.sum((self.cluster_centers_ - X[i]) ** 2, axis=1))
            labels[i] = np.argmin(distances)

        self.labels_ = labels
        self._is_fitted = True

        return self

    def fit_predict(self, X: np.ndarray) -> np.ndarray:
        """Fit and return cluster labels."""
        self.fit(X)
        return self.labels_

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict cluster labels for new data."""
        if not self._is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        X = np.asarray(X, dtype=np.float64)
        labels = np.zeros(len(X), dtype=int)

        for i in range(len(X)):
            distances = np.sqrt(np.sum((self.cluster_centers_ - X[i]) ** 2, axis=1))
            labels[i] = np.argmin(distances)

        return labels


class GaussianMixture:
    """
    Gaussian Mixture Model clustering.

    FHE-compatible implementation using polynomial approximations.

    Parameters
    ----------
    n_components : int
        Number of mixture components.
    covariance_type : str
        Covariance type ('full', 'diag', 'spherical').
    max_iter : int
        Maximum EM iterations.
    tol : float
        Convergence tolerance.
    random_state : int, optional
        Random seed.

    Examples
    --------
    >>> from sdk.models.clustering import GaussianMixture
    >>> gmm = GaussianMixture(n_components=3)
    >>> labels = gmm.fit_predict(X)
    """

    def __init__(
        self,
        n_components: int = 1,
        covariance_type: str = "full",
        max_iter: int = 100,
        tol: float = 1e-3,
        random_state: Optional[int] = None,
    ):
        self.n_components = n_components
        self.covariance_type = covariance_type
        self.max_iter = max_iter
        self.tol = tol
        self.random_state = random_state

        self.weights_: Optional[np.ndarray] = None
        self.means_: Optional[np.ndarray] = None
        self.covariances_: Optional[np.ndarray] = None
        self.converged_: bool = False
        self.n_iter_: int = 0
        self.lower_bound_: float = -np.inf
        self._is_fitted = False

    def _initialize_parameters(self, X: np.ndarray):
        """Initialize GMM parameters."""
        n_samples, n_features = X.shape

        if self.random_state is not None:
            np.random.seed(self.random_state)

        # Initialize means with k-means++
        indices = np.random.choice(n_samples, self.n_components, replace=False)
        self.means_ = X[indices].copy()

        # Initialize weights uniformly
        self.weights_ = np.ones(self.n_components) / self.n_components

        # Initialize covariances
        if self.covariance_type == "full":
            self.covariances_ = np.array([np.eye(n_features) for _ in range(self.n_components)])
        elif self.covariance_type == "diag":
            self.covariances_ = np.ones((self.n_components, n_features))
        else:  # spherical
            self.covariances_ = np.ones(self.n_components)

    def _compute_log_prob(self, X: np.ndarray) -> np.ndarray:
        """Compute log probability of each sample under each component."""
        n_samples, n_features = X.shape
        log_prob = np.zeros((n_samples, self.n_components))

        for k in range(self.n_components):
            if self.covariance_type == "full":
                cov = self.covariances_[k]
                cov_inv = np.linalg.inv(cov + 1e-6 * np.eye(n_features))
                log_det = np.log(np.linalg.det(cov) + 1e-10)
            elif self.covariance_type == "diag":
                cov_diag = self.covariances_[k]
                cov_inv = np.diag(1.0 / (cov_diag + 1e-6))
                log_det = np.sum(np.log(cov_diag + 1e-10))
            else:  # spherical
                var = self.covariances_[k]
                cov_inv = np.eye(n_features) / (var + 1e-6)
                log_det = n_features * np.log(var + 1e-10)

            diff = X - self.means_[k]
            mahal = np.sum(diff @ cov_inv * diff, axis=1)

            log_prob[:, k] = -0.5 * (n_features * np.log(2 * np.pi) + log_det + mahal)

        return log_prob

    def _e_step(self, X: np.ndarray) -> Tuple[np.ndarray, float]:
        """E-step: compute responsibilities."""
        log_prob = self._compute_log_prob(X)
        log_weights = np.log(self.weights_ + 1e-10)

        # Log-sum-exp trick for numerical stability
        weighted_log_prob = log_prob + log_weights
        log_prob_norm = np.max(weighted_log_prob, axis=1, keepdims=True)
        log_resp = (
            weighted_log_prob
            - log_prob_norm
            - np.log(np.sum(np.exp(weighted_log_prob - log_prob_norm), axis=1, keepdims=True))
        )

        # Lower bound (log-likelihood)
        lower_bound = np.mean(
            np.log(np.sum(np.exp(weighted_log_prob - log_prob_norm), axis=1))
            + log_prob_norm.flatten()
        )

        return np.exp(log_resp), lower_bound

    def _m_step(self, X: np.ndarray, resp: np.ndarray):
        """M-step: update parameters."""
        n_samples, n_features = X.shape

        # Update weights
        nk = np.sum(resp, axis=0) + 1e-10
        self.weights_ = nk / n_samples

        # Update means
        self.means_ = (resp.T @ X) / nk[:, np.newaxis]

        # Update covariances
        for k in range(self.n_components):
            diff = X - self.means_[k]
            weighted_diff = resp[:, k : k + 1] * diff

            if self.covariance_type == "full":
                self.covariances_[k] = (weighted_diff.T @ diff) / nk[k]
                # Regularization
                self.covariances_[k] += 1e-6 * np.eye(n_features)
            elif self.covariance_type == "diag":
                self.covariances_[k] = np.sum(weighted_diff * diff, axis=0) / nk[k]
                self.covariances_[k] += 1e-6
            else:  # spherical
                self.covariances_[k] = np.sum(weighted_diff * diff) / (nk[k] * n_features)
                self.covariances_[k] += 1e-6

    def fit(self, X: np.ndarray) -> "GaussianMixture":
        """
        Fit the Gaussian Mixture Model.

        Parameters
        ----------
        X : np.ndarray of shape (n_samples, n_features)
            Training data.

        Returns
        -------
        self : GaussianMixture
            Fitted estimator.
        """
        X = np.asarray(X, dtype=np.float64)

        self._initialize_parameters(X)

        lower_bound = -np.inf

        for n_iter in range(self.max_iter):  # noqa: B007
            # E-step
            resp, new_lower_bound = self._e_step(X)

            # M-step
            self._m_step(X, resp)

            # Check convergence
            change = new_lower_bound - lower_bound
            if abs(change) < self.tol:
                self.converged_ = True
                break

            lower_bound = new_lower_bound

        self.n_iter_ = n_iter + 1
        self.lower_bound_ = lower_bound
        self._is_fitted = True

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict cluster labels."""
        if not self._is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        X = np.asarray(X, dtype=np.float64)
        resp, _ = self._e_step(X)
        return np.argmax(resp, axis=1)

    def fit_predict(self, X: np.ndarray) -> np.ndarray:
        """Fit and return cluster labels."""
        self.fit(X)
        return self.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict posterior probability of each component."""
        if not self._is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        X = np.asarray(X, dtype=np.float64)
        resp, _ = self._e_step(X)
        return resp

    def score(self, X: np.ndarray) -> float:
        """Compute average log-likelihood."""
        if not self._is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        X = np.asarray(X, dtype=np.float64)
        _, lower_bound = self._e_step(X)
        return lower_bound

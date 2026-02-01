"""
Advanced evaluation metrics for FHE-ML models.

Provides additional metrics beyond standard accuracy/F1:
- Matthews correlation coefficient
- Cohen's kappa
- Silhouette score for clustering
- Calinski-Harabasz index
- Davies-Bouldin index
- Log loss / cross-entropy
- Brier score
- Explained variance
"""

from typing import List, Optional

import numpy as np

# ==================== Classification Metrics ====================


def matthews_corrcoef(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Compute Matthews correlation coefficient (MCC).

    MCC is a balanced measure that can be used even with imbalanced classes.
    Returns a value between -1 and +1 (+1 is perfect prediction).

    Args:
        y_true: Ground truth labels
        y_pred: Predicted labels

    Returns:
        Matthews correlation coefficient
    """
    y_true = np.asarray(y_true).ravel()
    y_pred = np.asarray(y_pred).ravel()

    # Binary case
    tp = np.sum((y_true == 1) & (y_pred == 1))
    tn = np.sum((y_true == 0) & (y_pred == 0))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    fn = np.sum((y_true == 1) & (y_pred == 0))

    numerator = (tp * tn) - (fp * fn)
    denominator = np.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))

    if denominator == 0:
        return 0.0

    return numerator / denominator


def cohen_kappa_score(
    y1: np.ndarray,
    y2: np.ndarray,
    labels: Optional[List] = None,
    weights: Optional[str] = None,
) -> float:
    """
    Compute Cohen's kappa coefficient for inter-rater agreement.

    Args:
        y1: First set of labels
        y2: Second set of labels
        labels: Optional list of labels
        weights: None, 'linear', or 'quadratic'

    Returns:
        Cohen's kappa coefficient (-1 to 1)
    """
    y1 = np.asarray(y1).ravel()
    y2 = np.asarray(y2).ravel()

    if labels is None:
        labels = np.unique(np.concatenate([y1, y2]))

    n_labels = len(labels)
    label_to_idx = {label: i for i, label in enumerate(labels)}

    # Build confusion matrix
    conf_mat = np.zeros((n_labels, n_labels), dtype=float)
    for true_label, pred_label in zip(y1, y2):
        if true_label in label_to_idx and pred_label in label_to_idx:
            conf_mat[label_to_idx[true_label], label_to_idx[pred_label]] += 1

    n_samples = conf_mat.sum()

    # Marginal sums
    sum0 = conf_mat.sum(axis=0)
    sum1 = conf_mat.sum(axis=1)

    # Expected agreement (by chance)
    expected = np.outer(sum1, sum0) / n_samples

    # Weight matrix
    if weights is None:
        w_mat = np.ones((n_labels, n_labels)) - np.eye(n_labels)
    elif weights == "linear":
        w_mat = np.zeros((n_labels, n_labels))
        for i in range(n_labels):
            for j in range(n_labels):
                w_mat[i, j] = abs(i - j)
        w_mat = w_mat / (n_labels - 1)
    elif weights == "quadratic":
        w_mat = np.zeros((n_labels, n_labels))
        for i in range(n_labels):
            for j in range(n_labels):
                w_mat[i, j] = (i - j) ** 2
        w_mat = w_mat / ((n_labels - 1) ** 2)
    else:
        raise ValueError(f"Unknown weights: {weights}")

    # Calculate kappa
    observed = 1 - np.sum(w_mat * conf_mat) / n_samples
    expected_agreement = 1 - np.sum(w_mat * expected) / n_samples

    if expected_agreement == 0:
        return 1.0

    return (observed - expected_agreement) / (1 - expected_agreement)


def log_loss(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    eps: float = 1e-15,
    normalize: bool = True,
) -> float:
    """
    Compute log loss (cross-entropy loss).

    Args:
        y_true: True labels (0 or 1 for binary)
        y_pred_proba: Predicted probabilities
        eps: Small value to avoid log(0)
        normalize: Average over samples if True

    Returns:
        Log loss value
    """
    y_true = np.asarray(y_true).ravel()
    y_pred_proba = np.asarray(y_pred_proba)

    # Clip probabilities
    y_pred_proba = np.clip(y_pred_proba, eps, 1 - eps)

    # Binary classification
    if y_pred_proba.ndim == 1 or y_pred_proba.shape[1] == 1:
        y_pred_proba = y_pred_proba.ravel()
        loss = -(y_true * np.log(y_pred_proba) + (1 - y_true) * np.log(1 - y_pred_proba))
    else:
        # Multi-class
        n_classes = y_pred_proba.shape[1]
        y_true_onehot = np.zeros((len(y_true), n_classes))
        y_true_onehot[np.arange(len(y_true)), y_true.astype(int)] = 1
        loss = -np.sum(y_true_onehot * np.log(y_pred_proba), axis=1)

    if normalize:
        return np.mean(loss)
    return np.sum(loss)


def brier_score_loss(y_true: np.ndarray, y_pred_proba: np.ndarray) -> float:
    """
    Compute Brier score for probability predictions.

    Lower is better (0 is perfect).

    Args:
        y_true: True binary labels
        y_pred_proba: Predicted probabilities for positive class

    Returns:
        Brier score
    """
    y_true = np.asarray(y_true).ravel()
    y_pred_proba = np.asarray(y_pred_proba).ravel()

    return np.mean((y_pred_proba - y_true) ** 2)


def balanced_accuracy_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Compute balanced accuracy (average recall across classes).

    Args:
        y_true: True labels
        y_pred: Predicted labels

    Returns:
        Balanced accuracy score
    """
    y_true = np.asarray(y_true).ravel()
    y_pred = np.asarray(y_pred).ravel()

    classes = np.unique(y_true)
    recalls = []

    for cls in classes:
        mask = y_true == cls
        if mask.sum() > 0:
            recall = (y_pred[mask] == cls).mean()
            recalls.append(recall)

    return np.mean(recalls) if recalls else 0.0


def hamming_loss(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Compute Hamming loss (fraction of wrong labels).

    Args:
        y_true: True labels (can be multi-label)
        y_pred: Predicted labels

    Returns:
        Hamming loss
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    return (y_true != y_pred).mean()


def zero_one_loss(y_true: np.ndarray, y_pred: np.ndarray, normalize: bool = True) -> float:
    """
    Compute zero-one loss (misclassification count/rate).

    Args:
        y_true: True labels
        y_pred: Predicted labels
        normalize: Return fraction if True, count if False

    Returns:
        Zero-one loss
    """
    y_true = np.asarray(y_true).ravel()
    y_pred = np.asarray(y_pred).ravel()

    errors = (y_true != y_pred).sum()

    if normalize:
        return errors / len(y_true)
    return float(errors)


def hinge_loss(y_true: np.ndarray, y_pred_decision: np.ndarray) -> float:
    """
    Compute hinge loss for SVM-style classifiers.

    Args:
        y_true: True labels (-1 or 1)
        y_pred_decision: Decision function values

    Returns:
        Average hinge loss
    """
    y_true = np.asarray(y_true).ravel()
    y_pred_decision = np.asarray(y_pred_decision).ravel()

    # Convert 0/1 to -1/1 if needed
    if set(np.unique(y_true)).issubset({0, 1}):
        y_true = 2 * y_true - 1

    losses = np.maximum(0, 1 - y_true * y_pred_decision)
    return np.mean(losses)


# ==================== Regression Metrics ====================


def explained_variance_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Compute explained variance regression score.

    Args:
        y_true: True values
        y_pred: Predicted values

    Returns:
        Explained variance score (best is 1.0)
    """
    y_true = np.asarray(y_true).ravel()
    y_pred = np.asarray(y_pred).ravel()

    variance_residual = np.var(y_true - y_pred)
    variance_total = np.var(y_true)

    if variance_total == 0:
        return 0.0 if variance_residual > 0 else 1.0

    return 1 - variance_residual / variance_total


def max_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Compute maximum residual error.

    Args:
        y_true: True values
        y_pred: Predicted values

    Returns:
        Maximum error
    """
    y_true = np.asarray(y_true).ravel()
    y_pred = np.asarray(y_pred).ravel()

    return np.max(np.abs(y_true - y_pred))


def mean_absolute_percentage_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Compute mean absolute percentage error (MAPE).

    Args:
        y_true: True values
        y_pred: Predicted values

    Returns:
        MAPE (0 to inf, lower is better)
    """
    y_true = np.asarray(y_true).ravel()
    y_pred = np.asarray(y_pred).ravel()

    # Avoid division by zero
    mask = y_true != 0
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100


def median_absolute_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Compute median absolute error.

    Args:
        y_true: True values
        y_pred: Predicted values

    Returns:
        Median absolute error
    """
    y_true = np.asarray(y_true).ravel()
    y_pred = np.asarray(y_pred).ravel()

    return np.median(np.abs(y_true - y_pred))


def mean_squared_log_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Compute mean squared log error.

    Only valid for non-negative values.

    Args:
        y_true: True values (non-negative)
        y_pred: Predicted values (non-negative)

    Returns:
        MSLE
    """
    y_true = np.asarray(y_true).ravel()
    y_pred = np.asarray(y_pred).ravel()

    return np.mean((np.log1p(y_true) - np.log1p(y_pred)) ** 2)


# ==================== Clustering Metrics ====================


def silhouette_score(
    X: np.ndarray,
    labels: np.ndarray,
    metric: str = "euclidean",
    sample_size: Optional[int] = None,
    random_state: Optional[int] = None,
) -> float:
    """
    Compute mean silhouette coefficient for clustering.

    Args:
        X: Feature matrix
        labels: Cluster labels
        metric: Distance metric ('euclidean' or 'manhattan')
        sample_size: Optional sample size for large datasets
        random_state: Random seed for sampling

    Returns:
        Mean silhouette coefficient (-1 to 1, higher is better)
    """
    X = np.asarray(X)
    labels = np.asarray(labels).ravel()

    n_samples = X.shape[0]
    unique_labels = np.unique(labels)
    n_clusters = len(unique_labels)

    if n_clusters <= 1 or n_clusters >= n_samples:
        return 0.0

    # Sample if needed
    if sample_size is not None and sample_size < n_samples:
        rng = np.random.default_rng(random_state)
        indices = rng.choice(n_samples, sample_size, replace=False)
        X = X[indices]
        labels = labels[indices]
        n_samples = sample_size

    # Calculate pairwise distances
    if metric == "euclidean":
        distances = _euclidean_distances(X)
    elif metric == "manhattan":
        distances = _manhattan_distances(X)
    else:
        raise ValueError(f"Unknown metric: {metric}")

    silhouette_values = np.zeros(n_samples)

    for i in range(n_samples):
        own_cluster = labels[i]

        # Mean distance to points in same cluster (a)
        same_cluster_mask = labels == own_cluster
        same_cluster_mask[i] = False  # Exclude self

        if same_cluster_mask.sum() > 0:
            a = distances[i, same_cluster_mask].mean()
        else:
            a = 0.0

        # Mean distance to points in nearest other cluster (b)
        b = np.inf
        for other_label in unique_labels:
            if other_label == own_cluster:
                continue

            other_cluster_mask = labels == other_label
            if other_cluster_mask.sum() > 0:
                mean_dist = distances[i, other_cluster_mask].mean()
                b = min(b, mean_dist)

        if b == np.inf:
            b = 0.0

        # Silhouette coefficient for this sample
        silhouette_values[i] = (b - a) / max(a, b) if max(a, b) > 0 else 0.0

    return silhouette_values.mean()


def _euclidean_distances(X: np.ndarray) -> np.ndarray:
    """Compute pairwise Euclidean distances."""
    n = X.shape[0]
    distances = np.zeros((n, n))

    for i in range(n):
        for j in range(i + 1, n):
            d = np.sqrt(np.sum((X[i] - X[j]) ** 2))
            distances[i, j] = d
            distances[j, i] = d

    return distances


def _manhattan_distances(X: np.ndarray) -> np.ndarray:
    """Compute pairwise Manhattan distances."""
    n = X.shape[0]
    distances = np.zeros((n, n))

    for i in range(n):
        for j in range(i + 1, n):
            d = np.sum(np.abs(X[i] - X[j]))
            distances[i, j] = d
            distances[j, i] = d

    return distances


def calinski_harabasz_score(X: np.ndarray, labels: np.ndarray) -> float:
    """
    Compute Calinski-Harabasz index (variance ratio criterion).

    Higher is better.

    Args:
        X: Feature matrix
        labels: Cluster labels

    Returns:
        Calinski-Harabasz index
    """
    X = np.asarray(X)
    labels = np.asarray(labels).ravel()

    n_samples, n_features = X.shape
    unique_labels = np.unique(labels)
    n_clusters = len(unique_labels)

    if n_clusters <= 1:
        return 0.0

    # Overall mean
    overall_mean = X.mean(axis=0)

    # Between-cluster dispersion
    between = 0.0
    # Within-cluster dispersion
    within = 0.0

    for label in unique_labels:
        cluster_mask = labels == label
        cluster_points = X[cluster_mask]
        n_cluster = cluster_points.shape[0]

        if n_cluster == 0:
            continue

        cluster_mean = cluster_points.mean(axis=0)

        # Between: sum of squared distances from cluster mean to overall mean
        between += n_cluster * np.sum((cluster_mean - overall_mean) ** 2)

        # Within: sum of squared distances from points to cluster mean
        within += np.sum((cluster_points - cluster_mean) ** 2)

    if within == 0:
        return 0.0

    return (between / (n_clusters - 1)) / (within / (n_samples - n_clusters))


def davies_bouldin_score(X: np.ndarray, labels: np.ndarray) -> float:
    """
    Compute Davies-Bouldin index.

    Lower is better (tighter, more separated clusters).

    Args:
        X: Feature matrix
        labels: Cluster labels

    Returns:
        Davies-Bouldin index
    """
    X = np.asarray(X)
    labels = np.asarray(labels).ravel()

    unique_labels = np.unique(labels)
    n_clusters = len(unique_labels)

    if n_clusters <= 1:
        return 0.0

    # Compute cluster centroids and dispersions
    centroids = []
    dispersions = []

    for label in unique_labels:
        cluster_mask = labels == label
        cluster_points = X[cluster_mask]

        if len(cluster_points) == 0:
            centroids.append(np.zeros(X.shape[1]))
            dispersions.append(0.0)
            continue

        centroid = cluster_points.mean(axis=0)
        centroids.append(centroid)

        # Dispersion: average distance to centroid
        dispersion = np.mean(np.sqrt(np.sum((cluster_points - centroid) ** 2, axis=1)))
        dispersions.append(dispersion)

    centroids = np.array(centroids)
    dispersions = np.array(dispersions)

    # Compute DB index
    db_scores = []

    for i in range(n_clusters):
        max_ratio = 0.0
        for j in range(n_clusters):
            if i == j:
                continue

            # Distance between centroids
            centroid_dist = np.sqrt(np.sum((centroids[i] - centroids[j]) ** 2))

            if centroid_dist > 0:
                ratio = (dispersions[i] + dispersions[j]) / centroid_dist
                max_ratio = max(max_ratio, ratio)

        db_scores.append(max_ratio)

    return np.mean(db_scores)


def adjusted_rand_score(labels_true: np.ndarray, labels_pred: np.ndarray) -> float:
    """
    Compute adjusted Rand index (ARI) for clustering.

    Args:
        labels_true: Ground truth cluster labels
        labels_pred: Predicted cluster labels

    Returns:
        Adjusted Rand index (-1 to 1, 1 is perfect)
    """
    labels_true = np.asarray(labels_true).ravel()
    labels_pred = np.asarray(labels_pred).ravel()

    # Build contingency table
    classes = np.unique(labels_true)
    clusters = np.unique(labels_pred)

    contingency = np.zeros((len(classes), len(clusters)), dtype=np.int64)
    class_to_idx = {c: i for i, c in enumerate(classes)}
    cluster_to_idx = {c: i for i, c in enumerate(clusters)}

    for true_label, pred_label in zip(labels_true, labels_pred):
        contingency[class_to_idx[true_label], cluster_to_idx[pred_label]] += 1

    # Sum of combinations
    sum_comb_c = sum(
        contingency[:, j].sum() * (contingency[:, j].sum() - 1) / 2 for j in range(len(clusters))
    )
    sum_comb_k = sum(
        contingency[i, :].sum() * (contingency[i, :].sum() - 1) / 2 for i in range(len(classes))
    )

    sum_comb = sum(
        contingency[i, j] * (contingency[i, j] - 1) / 2
        for i in range(len(classes))
        for j in range(len(clusters))
    )

    n = len(labels_true)
    n_comb = n * (n - 1) / 2

    expected = sum_comb_c * sum_comb_k / n_comb if n_comb > 0 else 0
    max_index = (sum_comb_c + sum_comb_k) / 2

    if max_index - expected == 0:
        return 1.0 if sum_comb == expected else 0.0

    return (sum_comb - expected) / (max_index - expected)


def normalized_mutual_info_score(
    labels_true: np.ndarray,
    labels_pred: np.ndarray,
    average_method: str = "arithmetic",
) -> float:
    """
    Compute normalized mutual information (NMI).

    Args:
        labels_true: Ground truth labels
        labels_pred: Predicted labels
        average_method: 'arithmetic', 'geometric', 'min', or 'max'

    Returns:
        NMI score (0 to 1)
    """
    labels_true = np.asarray(labels_true).ravel()
    labels_pred = np.asarray(labels_pred).ravel()

    n = len(labels_true)

    # Compute entropies
    classes = np.unique(labels_true)
    clusters = np.unique(labels_pred)

    # Entropy of true labels
    h_true = 0.0
    for c in classes:
        p = (labels_true == c).sum() / n
        if p > 0:
            h_true -= p * np.log(p)

    # Entropy of predicted labels
    h_pred = 0.0
    for c in clusters:
        p = (labels_pred == c).sum() / n
        if p > 0:
            h_pred -= p * np.log(p)

    # Mutual information
    mi = 0.0
    for c_true in classes:
        for c_pred in clusters:
            p_joint = ((labels_true == c_true) & (labels_pred == c_pred)).sum() / n
            p_true = (labels_true == c_true).sum() / n
            p_pred = (labels_pred == c_pred).sum() / n

            if p_joint > 0 and p_true > 0 and p_pred > 0:
                mi += p_joint * np.log(p_joint / (p_true * p_pred))

    # Normalize
    if average_method == "arithmetic":
        normalizer = (h_true + h_pred) / 2
    elif average_method == "geometric":
        normalizer = np.sqrt(h_true * h_pred)
    elif average_method == "min":
        normalizer = min(h_true, h_pred)
    elif average_method == "max":
        normalizer = max(h_true, h_pred)
    else:
        raise ValueError(f"Unknown average_method: {average_method}")

    if normalizer == 0:
        return 0.0

    return mi / normalizer


__all__ = [
    # Classification
    "matthews_corrcoef",
    "cohen_kappa_score",
    "log_loss",
    "brier_score_loss",
    "balanced_accuracy_score",
    "hamming_loss",
    "zero_one_loss",
    "hinge_loss",
    # Regression
    "explained_variance_score",
    "max_error",
    "mean_absolute_percentage_error",
    "median_absolute_error",
    "mean_squared_log_error",
    # Clustering
    "silhouette_score",
    "calinski_harabasz_score",
    "davies_bouldin_score",
    "adjusted_rand_score",
    "normalized_mutual_info_score",
]

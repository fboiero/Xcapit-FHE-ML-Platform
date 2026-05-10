"""Evaluation metrics for regression, classification, and clustering tasks.

All calculations use numpy for performance and to avoid heavy sklearn
dependencies in the core SDK.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np


class MetricType(Enum):
    """Type of ML task for metric selection."""

    REGRESSION = "regression"
    CLASSIFICATION = "classification"
    CLUSTERING = "clustering"


@dataclass
class RegressionMetrics:
    """Container for regression evaluation metrics.

    Attributes:
        r2_score: Coefficient of determination.
        mse: Mean squared error.
        rmse: Root mean squared error.
        mae: Mean absolute error.
        mape: Mean absolute percentage error.
        explained_variance: Explained variance score.
    """

    r2_score: float
    mse: float
    rmse: float
    mae: float
    mape: float
    explained_variance: float


@dataclass
class ClassificationMetrics:
    """Container for classification evaluation metrics.

    Attributes:
        accuracy: Fraction of correct predictions.
        precision: Weighted precision.
        recall: Weighted recall.
        f1_score: Weighted F1 score.
        confusion_matrix: Confusion matrix as 2-D numpy array.
        roc_auc: Area under the ROC curve (None if probabilities not given).
        log_loss: Logarithmic loss (None if probabilities not given).
    """

    accuracy: float
    precision: float
    recall: float
    f1_score: float
    confusion_matrix: np.ndarray
    roc_auc: Optional[float] = None
    log_loss: Optional[float] = None


@dataclass
class ClusteringMetrics:
    """Container for clustering evaluation metrics.

    Attributes:
        silhouette_score: Mean silhouette coefficient.
        calinski_harabasz: Calinski-Harabasz index.
        davies_bouldin: Davies-Bouldin index.
    """

    silhouette_score: float
    calinski_harabasz: float
    davies_bouldin: float


class MetricCalculator:
    """Calculate evaluation metrics for various ML tasks.

    Example:
        >>> calc = MetricCalculator()
        >>> reg = calc.regression(y_true, y_pred)
        >>> print(reg.r2_score, reg.rmse)

        >>> clf = calc.classification(y_true, y_pred)
        >>> print(clf.accuracy, clf.f1_score)
    """

    def __init__(self):
        pass

    # ------------------------------------------------------------------
    # Regression
    # ------------------------------------------------------------------

    def regression(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
    ) -> RegressionMetrics:
        """Compute regression metrics.

        Args:
            y_true: Ground-truth target values.
            y_pred: Predicted values.

        Returns:
            RegressionMetrics dataclass.
        """
        y_true = np.asarray(y_true, dtype=np.float64).ravel()
        y_pred = np.asarray(y_pred, dtype=np.float64).ravel()

        mse = float(np.mean((y_true - y_pred) ** 2))
        rmse = float(np.sqrt(mse))
        mae = float(np.mean(np.abs(y_true - y_pred)))

        # MAPE — guard against division by zero
        mask = y_true != 0
        if mask.any():
            mape = float(
                np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask]))
            )
        else:
            mape = float("inf")

        # R^2
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        r2 = float(1.0 - ss_res / ss_tot) if ss_tot != 0 else 0.0

        # Explained variance
        y_diff = y_true - y_pred
        ev = float(
            1.0 - np.var(y_diff) / np.var(y_true)
        ) if np.var(y_true) != 0 else 0.0

        return RegressionMetrics(
            r2_score=r2,
            mse=mse,
            rmse=rmse,
            mae=mae,
            mape=mape,
            explained_variance=ev,
        )

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------

    def classification(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_prob: Optional[np.ndarray] = None,
    ) -> ClassificationMetrics:
        """Compute classification metrics.

        Args:
            y_true: Ground-truth labels.
            y_pred: Predicted labels.
            y_prob: Predicted probabilities (for ROC-AUC and log-loss).

        Returns:
            ClassificationMetrics dataclass.
        """
        y_true = np.asarray(y_true).ravel()
        y_pred = np.asarray(y_pred).ravel()

        classes = np.unique(np.concatenate([y_true, y_pred]))
        n_classes = len(classes)

        # Confusion matrix
        cm = self._confusion_matrix(y_true, y_pred, classes)

        # Accuracy
        accuracy = float(np.sum(y_true == y_pred) / len(y_true))

        # Per-class precision, recall, F1
        precisions = []
        recalls = []
        f1s = []
        supports = []

        for i, _cls in enumerate(classes):
            tp = cm[i, i]
            fp = cm[:, i].sum() - tp
            fn = cm[i, :].sum() - tp
            support = cm[i, :].sum()

            p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (2 * p * r / (p + r)) if (p + r) > 0 else 0.0

            precisions.append(p)
            recalls.append(r)
            f1s.append(f1)
            supports.append(support)

        supports = np.array(supports, dtype=np.float64)
        total = supports.sum()

        # Weighted averages
        precision = float(
            np.sum(np.array(precisions) * supports) / total
        ) if total > 0 else 0.0
        recall = float(
            np.sum(np.array(recalls) * supports) / total
        ) if total > 0 else 0.0
        f1_score = float(
            np.sum(np.array(f1s) * supports) / total
        ) if total > 0 else 0.0

        # ROC-AUC (binary only)
        roc_auc = None
        log_loss_val = None

        if y_prob is not None:
            y_prob = np.asarray(y_prob, dtype=np.float64)

            if n_classes == 2:
                # Use probability of positive class
                if y_prob.ndim == 2:
                    prob_pos = y_prob[:, 1]
                else:
                    prob_pos = y_prob

                roc_auc = self._roc_auc(y_true, prob_pos, classes)
                log_loss_val = self._log_loss_binary(y_true, prob_pos, classes)
            else:
                # Multi-class log loss
                if y_prob.ndim == 2:
                    log_loss_val = self._log_loss_multiclass(
                        y_true, y_prob, classes
                    )

        return ClassificationMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            confusion_matrix=cm,
            roc_auc=roc_auc,
            log_loss=log_loss_val,
        )

    # ------------------------------------------------------------------
    # Clustering
    # ------------------------------------------------------------------

    def clustering(
        self,
        X: np.ndarray,
        labels: np.ndarray,
    ) -> ClusteringMetrics:
        """Compute clustering metrics.

        Args:
            X: Feature matrix (n_samples, n_features).
            labels: Cluster assignments.

        Returns:
            ClusteringMetrics dataclass.
        """
        X = np.asarray(X, dtype=np.float64)
        labels = np.asarray(labels).ravel()

        sil = self._silhouette_score(X, labels)
        ch = self._calinski_harabasz(X, labels)
        db = self._davies_bouldin(X, labels)

        return ClusteringMetrics(
            silhouette_score=sil,
            calinski_harabasz=ch,
            davies_bouldin=db,
        )

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def summary(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        task_type: Optional[str] = None,
    ) -> dict:
        """Auto-detect task type and return a summary dict of metrics.

        Args:
            y_true: Ground-truth values.
            y_pred: Predicted values.
            task_type: Force "regression" or "classification". If None,
                auto-detects based on target dtype and cardinality.

        Returns:
            Dict of metric name -> value.
        """
        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)

        if task_type is None:
            # Heuristic: if floating point with many unique values -> regression
            unique_vals = np.unique(y_true)
            if np.issubdtype(y_true.dtype, np.floating) and len(unique_vals) > 20:
                task_type = "regression"
            else:
                task_type = "classification"

        if task_type == "regression":
            metrics = self.regression(y_true, y_pred)
            return {
                "task_type": "regression",
                "r2_score": metrics.r2_score,
                "mse": metrics.mse,
                "rmse": metrics.rmse,
                "mae": metrics.mae,
                "mape": metrics.mape,
                "explained_variance": metrics.explained_variance,
            }
        else:
            metrics = self.classification(y_true, y_pred)
            return {
                "task_type": "classification",
                "accuracy": metrics.accuracy,
                "precision": metrics.precision,
                "recall": metrics.recall,
                "f1_score": metrics.f1_score,
            }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _confusion_matrix(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        classes: np.ndarray,
    ) -> np.ndarray:
        """Build a confusion matrix."""
        n = len(classes)
        cm = np.zeros((n, n), dtype=np.int64)
        class_to_idx = {c: i for i, c in enumerate(classes)}
        for t, p in zip(y_true, y_pred):
            cm[class_to_idx[t], class_to_idx[p]] += 1
        return cm

    @staticmethod
    def _roc_auc(
        y_true: np.ndarray,
        prob_pos: np.ndarray,
        classes: np.ndarray,
    ) -> float:
        """Compute ROC-AUC for binary classification using the trapezoidal rule."""
        # Map labels to 0/1
        pos_label = classes[1]
        y_bin = (y_true == pos_label).astype(np.float64)

        # Sort by decreasing probability
        desc = np.argsort(-prob_pos)
        y_sorted = y_bin[desc]

        # Compute TPR and FPR at each threshold
        tps = np.cumsum(y_sorted)
        fps = np.cumsum(1 - y_sorted)

        total_pos = y_bin.sum()
        total_neg = len(y_bin) - total_pos

        if total_pos == 0 or total_neg == 0:
            return 0.0

        tpr = tps / total_pos
        fpr = fps / total_neg

        # Prepend origin
        tpr = np.concatenate([[0], tpr])
        fpr = np.concatenate([[0], fpr])

        # Trapezoidal AUC
        auc = float(np.trapz(tpr, fpr))
        return auc

    @staticmethod
    def _log_loss_binary(
        y_true: np.ndarray,
        prob_pos: np.ndarray,
        classes: np.ndarray,
        eps: float = 1e-15,
    ) -> float:
        """Compute binary log loss."""
        pos_label = classes[1]
        y_bin = (y_true == pos_label).astype(np.float64)
        prob_pos = np.clip(prob_pos, eps, 1 - eps)
        loss = -(
            y_bin * np.log(prob_pos) + (1 - y_bin) * np.log(1 - prob_pos)
        )
        return float(np.mean(loss))

    @staticmethod
    def _log_loss_multiclass(
        y_true: np.ndarray,
        y_prob: np.ndarray,
        classes: np.ndarray,
        eps: float = 1e-15,
    ) -> float:
        """Compute multi-class log loss."""
        class_to_idx = {c: i for i, c in enumerate(classes)}
        y_prob = np.clip(y_prob, eps, 1 - eps)
        n = len(y_true)
        loss = 0.0
        for i in range(n):
            idx = class_to_idx.get(y_true[i], 0)
            loss -= np.log(y_prob[i, idx])
        return float(loss / n)

    @staticmethod
    def _silhouette_score(X: np.ndarray, labels: np.ndarray) -> float:
        """Compute mean silhouette coefficient."""
        unique_labels = np.unique(labels)
        n_clusters = len(unique_labels)

        if n_clusters < 2 or n_clusters >= len(X):
            return 0.0

        n = len(X)
        silhouettes = np.zeros(n)

        for i in range(n):
            own_label = labels[i]
            own_mask = labels == own_label
            other_labels = unique_labels[unique_labels != own_label]

            # a(i): mean distance to own cluster
            own_points = X[own_mask]
            if len(own_points) > 1:
                dists = np.sqrt(np.sum((own_points - X[i]) ** 2, axis=1))
                a_i = np.sum(dists) / (len(own_points) - 1)
            else:
                a_i = 0.0

            # b(i): min mean distance to other clusters
            b_i = float("inf")
            for lbl in other_labels:
                cluster_points = X[labels == lbl]
                dists = np.sqrt(np.sum((cluster_points - X[i]) ** 2, axis=1))
                mean_dist = np.mean(dists)
                if mean_dist < b_i:
                    b_i = mean_dist

            denom = max(a_i, b_i)
            silhouettes[i] = (b_i - a_i) / denom if denom > 0 else 0.0

        return float(np.mean(silhouettes))

    @staticmethod
    def _calinski_harabasz(X: np.ndarray, labels: np.ndarray) -> float:
        """Compute Calinski-Harabasz index."""
        unique_labels = np.unique(labels)
        n_clusters = len(unique_labels)
        n_samples = len(X)

        if n_clusters < 2:
            return 0.0

        overall_mean = np.mean(X, axis=0)

        # Between-cluster dispersion
        bgss = 0.0
        # Within-cluster dispersion
        wgss = 0.0

        for lbl in unique_labels:
            cluster_points = X[labels == lbl]
            n_k = len(cluster_points)
            cluster_mean = np.mean(cluster_points, axis=0)

            bgss += n_k * np.sum((cluster_mean - overall_mean) ** 2)
            wgss += np.sum((cluster_points - cluster_mean) ** 2)

        if wgss == 0:
            return 0.0

        return float(
            (bgss / (n_clusters - 1)) / (wgss / (n_samples - n_clusters))
        )

    @staticmethod
    def _davies_bouldin(X: np.ndarray, labels: np.ndarray) -> float:
        """Compute Davies-Bouldin index."""
        unique_labels = np.unique(labels)
        n_clusters = len(unique_labels)

        if n_clusters < 2:
            return 0.0

        # Compute cluster centroids and average intra-cluster distances
        centroids = []
        avg_dists = []

        for lbl in unique_labels:
            cluster_points = X[labels == lbl]
            centroid = np.mean(cluster_points, axis=0)
            centroids.append(centroid)
            avg_dist = np.mean(
                np.sqrt(np.sum((cluster_points - centroid) ** 2, axis=1))
            )
            avg_dists.append(avg_dist)

        centroids = np.array(centroids)
        avg_dists = np.array(avg_dists)

        # Compute DB index
        db = 0.0
        for i in range(n_clusters):
            max_ratio = 0.0
            for j in range(n_clusters):
                if i == j:
                    continue
                inter_dist = np.sqrt(
                    np.sum((centroids[i] - centroids[j]) ** 2)
                )
                if inter_dist == 0:
                    continue
                ratio = (avg_dists[i] + avg_dists[j]) / inter_dist
                if ratio > max_ratio:
                    max_ratio = ratio
            db += max_ratio

        return float(db / n_clusters)

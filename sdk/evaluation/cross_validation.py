"""Cross-validation utilities for FHE-ML models.

Provides K-Fold splitting and model evaluation with
configurable metrics.
"""

from copy import deepcopy
from typing import Any, Optional

import numpy as np

from .metrics import MetricCalculator


class CrossValidator:
    """K-Fold cross-validation with metric evaluation.

    Example:
        >>> cv = CrossValidator(n_folds=5, shuffle=True, random_state=42)
        >>> results = cv.evaluate(model, X, y, metrics=["r2_score", "mse"])
    """

    def __init__(
        self,
        n_folds: int = 5,
        shuffle: bool = True,
        random_state: Optional[int] = 42,
    ):
        """Initialize the cross-validator.

        Args:
            n_folds: Number of folds.
            shuffle: Whether to shuffle before splitting.
            random_state: Random seed for reproducibility.
        """
        if n_folds < 2:
            raise ValueError("n_folds must be >= 2.")
        self.n_folds = n_folds
        self.shuffle = shuffle
        self.random_state = random_state

    def split(
        self,
        X: np.ndarray,
        y: Optional[np.ndarray] = None,
    ) -> list[tuple[np.ndarray, np.ndarray]]:
        """Generate train/test index splits.

        Args:
            X: Feature matrix (n_samples, n_features).
            y: Target vector (unused, accepted for API compatibility).

        Returns:
            List of (train_indices, test_indices) tuples.
        """
        n_samples = len(X)
        indices = np.arange(n_samples)

        if self.shuffle:
            rng = np.random.RandomState(self.random_state)
            rng.shuffle(indices)

        fold_sizes = np.full(self.n_folds, n_samples // self.n_folds, dtype=int)
        fold_sizes[: n_samples % self.n_folds] += 1

        splits = []
        current = 0
        for fold_size in fold_sizes:
            test_idx = indices[current : current + fold_size]
            train_idx = np.concatenate([indices[:current], indices[current + fold_size :]])
            splits.append((train_idx, test_idx))
            current += fold_size

        return splits

    def evaluate(
        self,
        model: Any,
        X: np.ndarray,
        y: np.ndarray,
        metrics: Optional[list[str]] = None,
    ) -> dict[str, list[float]]:
        """Evaluate a model using cross-validation.

        The model must implement fit(X, y) and predict(X). A deep copy
        is created for each fold so the original model is not modified.

        Args:
            model: Model with fit/predict interface.
            X: Feature matrix.
            y: Target vector.
            metrics: List of metric names to compute (e.g. ["r2_score", "mse"]).
                Defaults to ["r2_score", "mse"] for regression.

        Returns:
            Dict mapping metric name to list of per-fold values.
        """
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y).ravel()

        if metrics is None:
            metrics = ["r2_score", "mse"]

        calc = MetricCalculator()
        splits = self.split(X, y)

        results: dict[str, list[float]] = {m: [] for m in metrics}

        for train_idx, test_idx in splits:
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]

            fold_model = deepcopy(model)
            fold_model.fit(X_train, y_train)
            y_pred = fold_model.predict(X_test)

            # Auto-detect task type
            unique_vals = np.unique(y)
            is_regression = np.issubdtype(y.dtype, np.floating) and len(unique_vals) > 20

            if is_regression:
                reg = calc.regression(y_test, y_pred)
                metric_values = {
                    "r2_score": reg.r2_score,
                    "mse": reg.mse,
                    "rmse": reg.rmse,
                    "mae": reg.mae,
                    "mape": reg.mape,
                    "explained_variance": reg.explained_variance,
                }
            else:
                clf = calc.classification(y_test, y_pred)
                metric_values = {
                    "accuracy": clf.accuracy,
                    "precision": clf.precision,
                    "recall": clf.recall,
                    "f1_score": clf.f1_score,
                }

            for m in metrics:
                value = metric_values.get(m)
                if value is not None:
                    results[m].append(value)

        return results

    def k_fold(
        self,
        model: Any,
        X: np.ndarray,
        y: np.ndarray,
        k: int = 5,
    ) -> dict[str, Any]:
        """Run k-fold cross-validation and return summary statistics.

        Args:
            model: Model with fit/predict interface.
            X: Feature matrix.
            y: Target vector.
            k: Number of folds.

        Returns:
            Dict with per-fold scores and mean/std summaries.
        """
        original_folds = self.n_folds
        self.n_folds = k

        try:
            raw = self.evaluate(model, X, y)
        finally:
            self.n_folds = original_folds

        summary: dict[str, Any] = {}
        for metric_name, values in raw.items():
            arr = np.array(values)
            summary[metric_name] = {
                "scores": values,
                "mean": float(np.mean(arr)),
                "std": float(np.std(arr)),
                "min": float(np.min(arr)),
                "max": float(np.max(arr)),
            }

        return summary

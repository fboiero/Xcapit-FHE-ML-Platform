"""Model interpretation utilities.

Provides feature importance, partial dependence, and
permutation importance for any model with a predict interface.
"""

from typing import Any, Optional

import numpy as np

from .metrics import MetricCalculator


class ModelInterpreter:
    """Interpret model predictions through feature analysis.

    Example:
        >>> interpreter = ModelInterpreter(trained_model)
        >>> importance = interpreter.feature_importance(X, y)
        >>> pdp = interpreter.partial_dependence(X, feature_idx=0)
    """

    def __init__(self, model: Any):
        """Initialize the interpreter.

        Args:
            model: A trained model with a predict(X) method.
        """
        self.model = model

    def feature_importance(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> np.ndarray:
        """Compute feature importance via permutation.

        Measures how much the model's score degrades when each feature
        is randomly shuffled.

        Args:
            X: Feature matrix (n_samples, n_features).
            y: True target values.

        Returns:
            Array of importance scores (n_features,), normalised to sum to 1.
        """
        return self.permutation_importance(X, y, n_repeats=5)

    def partial_dependence(
        self,
        X: np.ndarray,
        feature_idx: int,
        grid_resolution: int = 50,
    ) -> dict[str, np.ndarray]:
        """Compute partial dependence for a single feature.

        Varies one feature across its range while averaging predictions
        over the other features.

        Args:
            X: Feature matrix (n_samples, n_features).
            feature_idx: Index of the feature to analyse.
            grid_resolution: Number of grid points.

        Returns:
            Dict with 'values' (grid points) and 'predictions' (averaged predictions).
        """
        X = np.asarray(X, dtype=np.float64)

        feature_values = X[:, feature_idx]
        grid = np.linspace(
            feature_values.min(), feature_values.max(), grid_resolution
        )

        avg_predictions = np.zeros(grid_resolution)

        for i, val in enumerate(grid):
            X_modified = X.copy()
            X_modified[:, feature_idx] = val
            preds = np.asarray(self.model.predict(X_modified)).ravel()
            avg_predictions[i] = np.mean(preds)

        return {
            "values": grid,
            "predictions": avg_predictions,
        }

    def permutation_importance(
        self,
        X: np.ndarray,
        y: np.ndarray,
        n_repeats: int = 10,
        random_state: Optional[int] = 42,
    ) -> np.ndarray:
        """Compute permutation importance for all features.

        For each feature, shuffles its values n_repeats times and measures
        the mean decrease in R^2 (regression) or accuracy (classification).

        Args:
            X: Feature matrix (n_samples, n_features).
            y: True target values.
            n_repeats: Number of shuffle repetitions.
            random_state: Random seed.

        Returns:
            Array of importance scores (n_features,), normalised to sum to 1.
        """
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y).ravel()
        rng = np.random.RandomState(random_state)

        n_features = X.shape[1]
        calc = MetricCalculator()

        # Baseline score
        y_pred_base = np.asarray(self.model.predict(X)).ravel()

        # Detect task type
        unique_vals = np.unique(y)
        is_regression = (
            np.issubdtype(y.dtype, np.floating) and len(unique_vals) > 20
        )

        if is_regression:
            base_score = calc.regression(y, y_pred_base).r2_score
        else:
            base_score = calc.classification(y, y_pred_base).accuracy

        importances = np.zeros(n_features)

        for f in range(n_features):
            scores = []
            for _ in range(n_repeats):
                X_perm = X.copy()
                rng.shuffle(X_perm[:, f])
                y_pred_perm = np.asarray(self.model.predict(X_perm)).ravel()

                if is_regression:
                    score = calc.regression(y, y_pred_perm).r2_score
                else:
                    score = calc.classification(y, y_pred_perm).accuracy

                scores.append(base_score - score)

            importances[f] = np.mean(scores)

        # Normalise to sum to 1 (clamp negatives to 0)
        importances = np.maximum(importances, 0)
        total = importances.sum()
        if total > 0:
            importances = importances / total

        return importances

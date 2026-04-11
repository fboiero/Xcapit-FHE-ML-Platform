"""Hyperparameter tuning via grid search and random search.

Provides GridSearchCV and RandomSearchCV that work with any
model implementing the fit/predict/score interface.
"""

import itertools
from copy import deepcopy
from typing import Any, Optional, Union

import numpy as np

from .cross_validation import CrossValidator
from .metrics import MetricCalculator


class GridSearchCV:
    """Exhaustive grid search over a parameter space with cross-validation.

    Example:
        >>> gs = GridSearchCV(
        ...     model_class=LinearRegression,
        ...     param_grid={"learning_rate": [0.01, 0.1], "n_epochs": [50, 100]},
        ...     cv=5,
        ...     scoring="r2",
        ... )
        >>> gs.fit(X, y)
        >>> print(gs.best_params, gs.best_score)
    """

    def __init__(
        self,
        model_class: type,
        param_grid: dict[str, list],
        cv: int = 5,
        scoring: str = "r2",
    ):
        """Initialize grid search.

        Args:
            model_class: The model class to instantiate.
            param_grid: Dict mapping parameter names to lists of values.
            cv: Number of cross-validation folds.
            scoring: Metric name to optimise (e.g. "r2", "accuracy", "mse").
        """
        self.model_class = model_class
        self.param_grid = param_grid
        self.cv = cv
        self.scoring = scoring

        self.best_params: Optional[dict] = None
        self.best_score: Optional[float] = None
        self.results: list[dict] = []

    def _metric_key(self) -> str:
        """Map scoring shorthand to metric calculator key."""
        mapping = {
            "r2": "r2_score",
            "r2_score": "r2_score",
            "mse": "mse",
            "rmse": "rmse",
            "mae": "mae",
            "accuracy": "accuracy",
            "precision": "precision",
            "recall": "recall",
            "f1": "f1_score",
            "f1_score": "f1_score",
        }
        return mapping.get(self.scoring, self.scoring)

    def _is_higher_better(self) -> bool:
        """Whether a higher metric value is better."""
        lower_is_better = {"mse", "rmse", "mae", "mape", "log_loss", "davies_bouldin"}
        return self._metric_key() not in lower_is_better

    def fit(self, X: np.ndarray, y: np.ndarray) -> "GridSearchCV":
        """Run the grid search.

        Args:
            X: Feature matrix.
            y: Target vector.

        Returns:
            self, for method chaining.
        """
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y).ravel()

        param_names = list(self.param_grid.keys())
        param_values = list(self.param_grid.values())
        combinations = list(itertools.product(*param_values))

        cv = CrossValidator(n_folds=self.cv, shuffle=True, random_state=42)
        metric_key = self._metric_key()
        higher_better = self._is_higher_better()

        best_score = -np.inf if higher_better else np.inf
        best_params = None

        self.results = []

        for combo in combinations:
            params = dict(zip(param_names, combo))

            try:
                model = self.model_class(**params)
            except TypeError:
                # Fall back to setting attributes
                model = self.model_class()
                for k, v in params.items():
                    setattr(model, k, v)

            scores_dict = cv.evaluate(model, X, y, metrics=[metric_key])
            scores = scores_dict.get(metric_key, [])

            if scores:
                mean_score = float(np.mean(scores))
                std_score = float(np.std(scores))
            else:
                mean_score = float("nan")
                std_score = float("nan")

            result = {
                "params": params,
                "mean_score": mean_score,
                "std_score": std_score,
                "scores": scores,
            }
            self.results.append(result)

            if not np.isnan(mean_score):
                if higher_better and mean_score > best_score:
                    best_score = mean_score
                    best_params = params
                elif not higher_better and mean_score < best_score:
                    best_score = mean_score
                    best_params = params

        self.best_score = best_score
        self.best_params = best_params

        return self


class RandomSearchCV:
    """Random search over a parameter distribution with cross-validation.

    Example:
        >>> rs = RandomSearchCV(
        ...     model_class=LinearRegression,
        ...     param_distributions={"learning_rate": [0.001, 0.01, 0.1, 1.0]},
        ...     n_iter=10,
        ...     cv=5,
        ... )
        >>> rs.fit(X, y)
        >>> print(rs.best_params, rs.best_score)
    """

    def __init__(
        self,
        model_class: type,
        param_distributions: dict[str, Any],
        n_iter: int = 10,
        cv: int = 5,
        scoring: str = "r2",
        random_state: Optional[int] = 42,
    ):
        """Initialize random search.

        Args:
            model_class: The model class to instantiate.
            param_distributions: Dict mapping parameter names to lists or
                distributions (anything that supports random sampling).
            n_iter: Number of random parameter combinations to try.
            cv: Number of cross-validation folds.
            scoring: Metric name to optimise.
            random_state: Random seed for reproducibility.
        """
        self.model_class = model_class
        self.param_distributions = param_distributions
        self.n_iter = n_iter
        self.cv = cv
        self.scoring = scoring
        self.random_state = random_state

        self.best_params: Optional[dict] = None
        self.best_score: Optional[float] = None
        self.results: list[dict] = []

    def _sample_params(self, rng: np.random.RandomState) -> dict:
        """Sample a random parameter combination."""
        params = {}
        for name, dist in self.param_distributions.items():
            if isinstance(dist, (list, tuple, np.ndarray)):
                params[name] = dist[rng.randint(0, len(dist))]
            elif hasattr(dist, "rvs"):
                # scipy distribution
                params[name] = dist.rvs(random_state=rng)
            else:
                params[name] = dist
        return params

    def _metric_key(self) -> str:
        """Map scoring shorthand to metric calculator key."""
        mapping = {
            "r2": "r2_score",
            "r2_score": "r2_score",
            "mse": "mse",
            "rmse": "rmse",
            "mae": "mae",
            "accuracy": "accuracy",
            "precision": "precision",
            "recall": "recall",
            "f1": "f1_score",
            "f1_score": "f1_score",
        }
        return mapping.get(self.scoring, self.scoring)

    def _is_higher_better(self) -> bool:
        """Whether a higher metric value is better."""
        lower_is_better = {"mse", "rmse", "mae", "mape", "log_loss", "davies_bouldin"}
        return self._metric_key() not in lower_is_better

    def fit(self, X: np.ndarray, y: np.ndarray) -> "RandomSearchCV":
        """Run the random search.

        Args:
            X: Feature matrix.
            y: Target vector.

        Returns:
            self, for method chaining.
        """
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y).ravel()

        rng = np.random.RandomState(self.random_state)
        cv = CrossValidator(n_folds=self.cv, shuffle=True, random_state=42)
        metric_key = self._metric_key()
        higher_better = self._is_higher_better()

        best_score = -np.inf if higher_better else np.inf
        best_params = None

        self.results = []

        for _ in range(self.n_iter):
            params = self._sample_params(rng)

            try:
                model = self.model_class(**params)
            except TypeError:
                model = self.model_class()
                for k, v in params.items():
                    setattr(model, k, v)

            scores_dict = cv.evaluate(model, X, y, metrics=[metric_key])
            scores = scores_dict.get(metric_key, [])

            if scores:
                mean_score = float(np.mean(scores))
                std_score = float(np.std(scores))
            else:
                mean_score = float("nan")
                std_score = float("nan")

            result = {
                "params": params,
                "mean_score": mean_score,
                "std_score": std_score,
                "scores": scores,
            }
            self.results.append(result)

            if not np.isnan(mean_score):
                if higher_better and mean_score > best_score:
                    best_score = mean_score
                    best_params = params
                elif not higher_better and mean_score < best_score:
                    best_score = mean_score
                    best_params = params

        self.best_score = best_score
        self.best_params = best_params

        return self

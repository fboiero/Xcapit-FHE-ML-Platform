"""
Imputation module for FHE-ML Platform.

Provides missing value imputation strategies compatible with encrypted data.
"""

from __future__ import annotations

from typing import Any, Callable, List, Literal, Optional, Union

import numpy as np


class SimpleImputer:
    """
    Univariate imputer for completing missing values.

    Args:
        missing_values: The placeholder for missing values. Default is np.nan.
        strategy: The imputation strategy:
            - "mean": Replace with mean of each column
            - "median": Replace with median of each column
            - "most_frequent": Replace with mode of each column
            - "constant": Replace with fill_value
        fill_value: Value to use for constant strategy
        copy: If True, create a copy of X

    Example:
        >>> imputer = SimpleImputer(strategy='mean')
        >>> imputer.fit(X)
        >>> X_imputed = imputer.transform(X)
    """

    def __init__(
        self,
        missing_values: Any = np.nan,
        strategy: Literal["mean", "median", "most_frequent", "constant"] = "mean",
        fill_value: Optional[Any] = None,
        copy: bool = True,
    ):
        self.missing_values = missing_values
        self.strategy = strategy
        self.fill_value = fill_value
        self.copy = copy

        # Fitted attributes
        self.statistics_: Optional[np.ndarray] = None
        self.n_features_in_: Optional[int] = None

    def _get_mask(self, X: np.ndarray) -> np.ndarray:
        """Get boolean mask for missing values."""
        if np.isnan(self.missing_values):
            return np.isnan(X)
        else:
            return X == self.missing_values

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> "SimpleImputer":
        """
        Fit the imputer on X.

        Args:
            X: Training data of shape (n_samples, n_features)
            y: Ignored

        Returns:
            self
        """
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        self.n_features_in_ = X.shape[1]
        mask = self._get_mask(X)

        if self.strategy == "mean":
            # Calculate mean ignoring missing values
            self.statistics_ = np.nanmean(
                np.where(mask, np.nan, X), axis=0
            )
        elif self.strategy == "median":
            self.statistics_ = np.nanmedian(
                np.where(mask, np.nan, X), axis=0
            )
        elif self.strategy == "most_frequent":
            self.statistics_ = np.zeros(self.n_features_in_)
            for i in range(self.n_features_in_):
                col = X[:, i][~mask[:, i]]
                if len(col) > 0:
                    values, counts = np.unique(col, return_counts=True)
                    self.statistics_[i] = values[np.argmax(counts)]
        elif self.strategy == "constant":
            if self.fill_value is None:
                raise ValueError("fill_value must be specified for strategy='constant'")
            self.statistics_ = np.full(self.n_features_in_, self.fill_value)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")

        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Impute missing values in X.

        Args:
            X: Data to impute of shape (n_samples, n_features)

        Returns:
            Imputed data
        """
        if self.statistics_ is None:
            raise ValueError("Imputer has not been fitted")

        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        if self.copy:
            X = X.copy()

        if X.shape[1] != self.n_features_in_:
            raise ValueError(
                f"X has {X.shape[1]} features, but imputer was fitted with {self.n_features_in_}"
            )

        mask = self._get_mask(X)

        for i in range(self.n_features_in_):
            X[mask[:, i], i] = self.statistics_[i]

        return X

    def fit_transform(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> np.ndarray:
        """Fit and transform in one step."""
        return self.fit(X, y).transform(X)

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """
        Return X as-is (inverse is not well-defined for imputation).
        """
        return X


class KNNImputer:
    """
    Imputer that uses k-Nearest Neighbors to complete missing values.

    Each sample's missing values are imputed using the mean value from
    n_neighbors nearest neighbors found in the training set.

    Args:
        n_neighbors: Number of neighboring samples to use for imputation
        weights: Weight function used in prediction:
            - "uniform": Uniform weights (all neighbors weighted equally)
            - "distance": Weight by inverse of distance
        metric: Distance metric ("euclidean" or "manhattan")
        copy: If True, create a copy of X

    Example:
        >>> imputer = KNNImputer(n_neighbors=5)
        >>> X_imputed = imputer.fit_transform(X)
    """

    def __init__(
        self,
        n_neighbors: int = 5,
        weights: Literal["uniform", "distance"] = "uniform",
        metric: Literal["euclidean", "manhattan"] = "euclidean",
        copy: bool = True,
    ):
        self.n_neighbors = n_neighbors
        self.weights = weights
        self.metric = metric
        self.copy = copy

        # Fitted attributes
        self._fit_X: Optional[np.ndarray] = None
        self.n_features_in_: Optional[int] = None

    def _compute_distances(self, X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
        """Compute pairwise distances between X1 and X2."""
        # Handle missing values by using only valid features
        n1, n2 = len(X1), len(X2)
        distances = np.zeros((n1, n2))

        for i in range(n1):
            for j in range(n2):
                # Find valid features (both not NaN)
                valid = ~(np.isnan(X1[i]) | np.isnan(X2[j]))
                if not valid.any():
                    distances[i, j] = np.inf
                    continue

                diff = X1[i, valid] - X2[j, valid]
                if self.metric == "euclidean":
                    distances[i, j] = np.sqrt(np.sum(diff ** 2))
                else:  # manhattan
                    distances[i, j] = np.sum(np.abs(diff))

        return distances

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> "KNNImputer":
        """
        Fit the imputer on X.

        Args:
            X: Training data of shape (n_samples, n_features)
            y: Ignored

        Returns:
            self
        """
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        self.n_features_in_ = X.shape[1]
        self._fit_X = X.copy()

        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Impute missing values in X.

        Args:
            X: Data to impute of shape (n_samples, n_features)

        Returns:
            Imputed data
        """
        if self._fit_X is None:
            raise ValueError("Imputer has not been fitted")

        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        if self.copy:
            X = X.copy()

        n_samples = X.shape[0]

        for i in range(n_samples):
            missing_mask = np.isnan(X[i])
            if not missing_mask.any():
                continue

            # Compute distances to all training samples
            distances = self._compute_distances(X[i:i+1], self._fit_X)[0]

            # Get k nearest neighbors
            neighbor_indices = np.argsort(distances)[: self.n_neighbors]

            # Get neighbor values for missing features
            for j in np.where(missing_mask)[0]:
                neighbor_values = self._fit_X[neighbor_indices, j]
                valid_values = neighbor_values[~np.isnan(neighbor_values)]

                if len(valid_values) == 0:
                    # Fall back to column mean
                    col = self._fit_X[:, j]
                    X[i, j] = np.nanmean(col)
                elif self.weights == "uniform":
                    X[i, j] = np.mean(valid_values)
                else:  # distance weights
                    valid_distances = distances[neighbor_indices][~np.isnan(neighbor_values)]
                    if np.all(valid_distances == 0):
                        X[i, j] = np.mean(valid_values)
                    else:
                        weights = 1 / (valid_distances + 1e-10)
                        X[i, j] = np.average(valid_values, weights=weights)

        return X

    def fit_transform(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> np.ndarray:
        """Fit and transform in one step."""
        return self.fit(X, y).transform(X)


class IterativeImputer:
    """
    Multivariate imputer using iterative modeling.

    A strategy for imputing missing values by modeling each feature with
    missing values as a function of other features in a round-robin fashion.

    Args:
        estimator: Estimator to use for imputation. Must have fit and predict.
            Default is a simple mean predictor.
        max_iter: Maximum number of imputation rounds
        tol: Tolerance for convergence
        initial_strategy: Strategy for initial imputation
        imputation_order: Order in which features are imputed:
            - "ascending": From features with fewest to most missing values
            - "descending": From features with most to fewest missing values
            - "roman": Left to right
            - "arabic": Right to left
            - "random": Random order
        random_state: Random seed

    Example:
        >>> from sdk.models import LinearRegression
        >>> imputer = IterativeImputer(estimator=LinearRegression(), max_iter=10)
        >>> X_imputed = imputer.fit_transform(X)
    """

    def __init__(
        self,
        estimator: Optional[Any] = None,
        max_iter: int = 10,
        tol: float = 1e-3,
        initial_strategy: Literal["mean", "median", "most_frequent"] = "mean",
        imputation_order: Literal["ascending", "descending", "roman", "arabic", "random"] = "ascending",
        random_state: Optional[int] = None,
    ):
        self.estimator = estimator
        self.max_iter = max_iter
        self.tol = tol
        self.initial_strategy = initial_strategy
        self.imputation_order = imputation_order
        self.random_state = random_state

        # Fitted attributes
        self.initial_imputer_: Optional[SimpleImputer] = None
        self.n_features_in_: Optional[int] = None
        self._fit_X: Optional[np.ndarray] = None

    def _get_estimator(self):
        """Get estimator for imputation."""
        if self.estimator is not None:
            import copy
            return copy.deepcopy(self.estimator)

        # Default: simple mean predictor
        class MeanPredictor:
            def __init__(self):
                self.mean_ = None

            def fit(self, X, y):
                self.mean_ = np.mean(y)
                return self

            def predict(self, X):
                return np.full(len(X), self.mean_)

        return MeanPredictor()

    def _get_imputation_order(self, mask: np.ndarray) -> np.ndarray:
        """Get the order in which to impute features."""
        n_features = mask.shape[1]
        missing_counts = np.sum(mask, axis=0)

        if self.imputation_order == "ascending":
            return np.argsort(missing_counts)
        elif self.imputation_order == "descending":
            return np.argsort(missing_counts)[::-1]
        elif self.imputation_order == "roman":
            return np.arange(n_features)
        elif self.imputation_order == "arabic":
            return np.arange(n_features)[::-1]
        else:  # random
            rng = np.random.RandomState(self.random_state)
            return rng.permutation(n_features)

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> "IterativeImputer":
        """
        Fit the imputer on X.

        Args:
            X: Training data
            y: Ignored

        Returns:
            self
        """
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        self.n_features_in_ = X.shape[1]

        # Initial imputation
        self.initial_imputer_ = SimpleImputer(strategy=self.initial_strategy)
        self._fit_X = self.initial_imputer_.fit_transform(X)

        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Impute missing values in X using iterative imputation.

        Args:
            X: Data to impute

        Returns:
            Imputed data
        """
        if self.initial_imputer_ is None:
            raise ValueError("Imputer has not been fitted")

        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        # Mask of missing values
        missing_mask = np.isnan(X)

        if not missing_mask.any():
            return X

        # Initial imputation
        X_imputed = self.initial_imputer_.transform(X)

        # Get imputation order
        order = self._get_imputation_order(missing_mask)

        # Iterative imputation
        for iteration in range(self.max_iter):
            X_prev = X_imputed.copy()

            for feat_idx in order:
                # Skip if no missing values for this feature
                if not missing_mask[:, feat_idx].any():
                    continue

                # Get samples with missing values
                missing_rows = missing_mask[:, feat_idx]

                # Create predictor variables (all other features)
                predictor_cols = [i for i in range(self.n_features_in_) if i != feat_idx]

                # Fit model on complete cases
                complete_rows = ~missing_mask[:, feat_idx]
                X_train = X_imputed[complete_rows][:, predictor_cols]
                y_train = X_imputed[complete_rows, feat_idx]

                if len(X_train) < 2:
                    continue

                estimator = self._get_estimator()
                estimator.fit(X_train, y_train)

                # Predict missing values
                X_pred = X_imputed[missing_rows][:, predictor_cols]
                X_imputed[missing_rows, feat_idx] = estimator.predict(X_pred)

            # Check convergence
            diff = np.abs(X_imputed - X_prev)
            diff[~missing_mask] = 0
            if np.max(diff) < self.tol:
                break

        return X_imputed

    def fit_transform(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> np.ndarray:
        """Fit and transform in one step."""
        return self.fit(X, y).transform(X)


class MissingIndicator:
    """
    Binary indicators for missing values.

    Useful as a preprocessing step to add binary indicators of missing values
    before imputation.

    Args:
        missing_values: The placeholder for missing values
        features: Which features to create indicators for:
            - "missing-only": Only features with missing values
            - "all": All features

    Example:
        >>> indicator = MissingIndicator()
        >>> indicator.fit(X)
        >>> X_indicator = indicator.transform(X)
    """

    def __init__(
        self,
        missing_values: Any = np.nan,
        features: Literal["missing-only", "all"] = "missing-only",
    ):
        self.missing_values = missing_values
        self.features = features

        # Fitted attributes
        self.features_: Optional[np.ndarray] = None
        self.n_features_in_: Optional[int] = None

    def _get_mask(self, X: np.ndarray) -> np.ndarray:
        """Get boolean mask for missing values."""
        if np.isnan(self.missing_values):
            return np.isnan(X)
        else:
            return X == self.missing_values

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> "MissingIndicator":
        """
        Fit the indicator.

        Args:
            X: Training data
            y: Ignored

        Returns:
            self
        """
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        self.n_features_in_ = X.shape[1]
        mask = self._get_mask(X)

        if self.features == "missing-only":
            # Only features that have at least one missing value
            self.features_ = np.where(mask.any(axis=0))[0]
        else:
            self.features_ = np.arange(self.n_features_in_)

        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Generate missing indicator features.

        Args:
            X: Data to generate indicators for

        Returns:
            Binary indicator array
        """
        if self.features_ is None:
            raise ValueError("Indicator has not been fitted")

        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        mask = self._get_mask(X)
        return mask[:, self.features_].astype(int)

    def fit_transform(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> np.ndarray:
        """Fit and transform in one step."""
        return self.fit(X, y).transform(X)


__all__ = [
    "SimpleImputer",
    "KNNImputer",
    "IterativeImputer",
    "MissingIndicator",
]

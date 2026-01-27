"""
Missing Value Imputers for FHE-ML Platform.

Implements imputation strategies for handling missing data.
"""

import numpy as np
from typing import Optional, Union, List


class SimpleImputer:
    """
    Imputation for missing values using simple strategies.

    Parameters
    ----------
    missing_values : float or np.nan
        Value to treat as missing.
    strategy : str
        Imputation strategy ('mean', 'median', 'most_frequent', 'constant').
    fill_value : any
        Value to use for 'constant' strategy.

    Examples
    --------
    >>> from sdk.preprocessing import SimpleImputer
    >>> imp = SimpleImputer(strategy='mean')
    >>> imp.fit_transform([[1, 2], [np.nan, 3], [7, 6]])
    """

    def __init__(
        self,
        missing_values: float = np.nan,
        strategy: str = "mean",
        fill_value: Optional[float] = None,
    ):
        self.missing_values = missing_values
        self.strategy = strategy
        self.fill_value = fill_value

        self.statistics_: Optional[np.ndarray] = None
        self.n_features_in_: Optional[int] = None
        self._is_fitted = False

    def _get_mask(self, X: np.ndarray) -> np.ndarray:
        """Get mask for missing values."""
        if np.isnan(self.missing_values):
            return np.isnan(X)
        else:
            return X == self.missing_values

    def fit(self, X: np.ndarray, y=None) -> "SimpleImputer":
        """
        Fit the imputer.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.

        Returns
        -------
        self : SimpleImputer
            Fitted imputer.
        """
        X = np.asarray(X, dtype=np.float64)
        self.n_features_in_ = X.shape[1]

        mask = self._get_mask(X)
        self.statistics_ = np.zeros(self.n_features_in_)

        for i in range(self.n_features_in_):
            col = X[:, i]
            valid = col[~mask[:, i]]

            if len(valid) == 0:
                self.statistics_[i] = 0
                continue

            if self.strategy == "mean":
                self.statistics_[i] = np.mean(valid)
            elif self.strategy == "median":
                self.statistics_[i] = np.median(valid)
            elif self.strategy == "most_frequent":
                values, counts = np.unique(valid, return_counts=True)
                self.statistics_[i] = values[np.argmax(counts)]
            elif self.strategy == "constant":
                self.statistics_[i] = self.fill_value if self.fill_value is not None else 0
            else:
                raise ValueError(f"Unknown strategy: {self.strategy}")

        self._is_fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Impute missing values.

        Parameters
        ----------
        X : array-like
            Data with missing values.

        Returns
        -------
        X_imputed : np.ndarray
            Data with imputed values.
        """
        if not self._is_fitted:
            raise ValueError("Imputer not fitted. Call fit() first.")

        X = np.asarray(X, dtype=np.float64).copy()
        mask = self._get_mask(X)

        for i in range(self.n_features_in_):
            X[mask[:, i], i] = self.statistics_[i]

        return X

    def fit_transform(self, X: np.ndarray, y=None) -> np.ndarray:
        """Fit and transform in one step."""
        return self.fit(X, y).transform(X)


class KNNImputer:
    """
    Imputation using k-Nearest Neighbors.

    Parameters
    ----------
    n_neighbors : int
        Number of neighbors to use.
    weights : str
        Weight function ('uniform', 'distance').
    metric : str
        Distance metric.

    Examples
    --------
    >>> from sdk.preprocessing import KNNImputer
    >>> imp = KNNImputer(n_neighbors=3)
    >>> imp.fit_transform(X)
    """

    def __init__(
        self,
        n_neighbors: int = 5,
        weights: str = "uniform",
        metric: str = "euclidean",
    ):
        self.n_neighbors = n_neighbors
        self.weights = weights
        self.metric = metric

        self._fit_X: Optional[np.ndarray] = None
        self.n_features_in_: Optional[int] = None
        self._is_fitted = False

    def fit(self, X: np.ndarray, y=None) -> "KNNImputer":
        """
        Fit the KNN imputer.

        Parameters
        ----------
        X : array-like
            Training data (may contain missing values).

        Returns
        -------
        self : KNNImputer
            Fitted imputer.
        """
        X = np.asarray(X, dtype=np.float64)
        self.n_features_in_ = X.shape[1]
        self._fit_X = X.copy()
        self._is_fitted = True
        return self

    def _compute_distances(self, x1: np.ndarray, x2: np.ndarray, mask1: np.ndarray, mask2: np.ndarray) -> float:
        """Compute distance ignoring missing values."""
        valid = ~mask1 & ~mask2
        if not np.any(valid):
            return np.inf

        diff = x1[valid] - x2[valid]

        if self.metric == "euclidean":
            return np.sqrt(np.sum(diff**2))
        elif self.metric == "manhattan":
            return np.sum(np.abs(diff))
        else:
            return np.sqrt(np.sum(diff**2))

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Impute missing values using KNN.

        Parameters
        ----------
        X : array-like
            Data with missing values.

        Returns
        -------
        X_imputed : np.ndarray
            Imputed data.
        """
        if not self._is_fitted:
            raise ValueError("Imputer not fitted. Call fit() first.")

        X = np.asarray(X, dtype=np.float64).copy()
        n_samples = X.shape[0]

        for i in range(n_samples):
            mask_i = np.isnan(X[i])
            if not np.any(mask_i):
                continue

            # Find k nearest neighbors in fit data
            distances = []
            for j in range(len(self._fit_X)):
                mask_j = np.isnan(self._fit_X[j])
                d = self._compute_distances(X[i], self._fit_X[j], mask_i, mask_j)
                distances.append((d, j))

            distances.sort(key=lambda x: x[0])
            neighbors = [idx for _, idx in distances[:self.n_neighbors] if _ != np.inf]

            if not neighbors:
                # No valid neighbors, use column mean
                for feat in np.where(mask_i)[0]:
                    valid_values = self._fit_X[:, feat][~np.isnan(self._fit_X[:, feat])]
                    X[i, feat] = np.mean(valid_values) if len(valid_values) > 0 else 0
                continue

            # Impute missing features
            for feat in np.where(mask_i)[0]:
                neighbor_values = []
                neighbor_weights = []

                for d, idx in distances[:self.n_neighbors]:
                    if d == np.inf:
                        continue
                    val = self._fit_X[idx, feat]
                    if not np.isnan(val):
                        neighbor_values.append(val)
                        if self.weights == "distance":
                            neighbor_weights.append(1.0 / (d + 1e-10))
                        else:
                            neighbor_weights.append(1.0)

                if neighbor_values:
                    if self.weights == "distance":
                        X[i, feat] = np.average(neighbor_values, weights=neighbor_weights)
                    else:
                        X[i, feat] = np.mean(neighbor_values)
                else:
                    # No valid neighbors for this feature
                    valid = self._fit_X[:, feat][~np.isnan(self._fit_X[:, feat])]
                    X[i, feat] = np.mean(valid) if len(valid) > 0 else 0

        return X

    def fit_transform(self, X: np.ndarray, y=None) -> np.ndarray:
        """Fit and transform in one step."""
        return self.fit(X, y).transform(X)


class IterativeImputer:
    """
    Multivariate imputer using iterative regression.

    Imputes each feature using values from other features.

    Parameters
    ----------
    max_iter : int
        Maximum number of imputation rounds.
    tol : float
        Tolerance for convergence.
    initial_strategy : str
        Initial imputation strategy.
    random_state : int, optional
        Random seed.

    Examples
    --------
    >>> from sdk.preprocessing import IterativeImputer
    >>> imp = IterativeImputer(max_iter=10)
    >>> imp.fit_transform(X)
    """

    def __init__(
        self,
        max_iter: int = 10,
        tol: float = 1e-3,
        initial_strategy: str = "mean",
        random_state: Optional[int] = None,
    ):
        self.max_iter = max_iter
        self.tol = tol
        self.initial_strategy = initial_strategy
        self.random_state = random_state

        self.initial_imputer_: Optional[SimpleImputer] = None
        self.n_features_in_: Optional[int] = None
        self._is_fitted = False

    def fit(self, X: np.ndarray, y=None) -> "IterativeImputer":
        """
        Fit the iterative imputer.

        Parameters
        ----------
        X : array-like
            Training data.

        Returns
        -------
        self : IterativeImputer
            Fitted imputer.
        """
        X = np.asarray(X, dtype=np.float64)
        self.n_features_in_ = X.shape[1]

        # Fit initial imputer for mean/median values
        self.initial_imputer_ = SimpleImputer(strategy=self.initial_strategy)
        self.initial_imputer_.fit(X)

        self._is_fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Impute missing values iteratively.

        Parameters
        ----------
        X : array-like
            Data with missing values.

        Returns
        -------
        X_imputed : np.ndarray
            Imputed data.
        """
        if not self._is_fitted:
            raise ValueError("Imputer not fitted. Call fit() first.")

        if self.random_state is not None:
            np.random.seed(self.random_state)

        X = np.asarray(X, dtype=np.float64).copy()
        mask = np.isnan(X)

        # Initial imputation
        X_filled = self.initial_imputer_.transform(X)

        # Iterative imputation
        for iteration in range(self.max_iter):
            X_old = X_filled.copy()

            # Impute each feature using others as predictors
            for feat in range(self.n_features_in_):
                feat_missing = mask[:, feat]
                if not np.any(feat_missing):
                    continue

                # Get samples with observed values for this feature
                feat_observed = ~feat_missing

                if np.sum(feat_observed) < 2:
                    continue

                # Simple linear regression using other features
                other_feats = [f for f in range(self.n_features_in_) if f != feat]
                X_train = X_filled[feat_observed][:, other_feats]
                y_train = X[feat_observed, feat]

                # Fit simple linear model
                # y = X @ w + b
                X_train_bias = np.column_stack([np.ones(len(X_train)), X_train])
                try:
                    w = np.linalg.lstsq(X_train_bias, y_train, rcond=None)[0]

                    # Predict missing values
                    X_test = X_filled[feat_missing][:, other_feats]
                    X_test_bias = np.column_stack([np.ones(len(X_test)), X_test])
                    predictions = X_test_bias @ w

                    X_filled[feat_missing, feat] = predictions
                except np.linalg.LinAlgError:
                    # If regression fails, keep current values
                    pass

            # Check convergence
            change = np.mean(np.abs(X_filled[mask] - X_old[mask])) if np.any(mask) else 0
            if change < self.tol:
                break

        return X_filled

    def fit_transform(self, X: np.ndarray, y=None) -> np.ndarray:
        """Fit and transform in one step."""
        return self.fit(X, y).transform(X)

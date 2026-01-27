"""
Data Scalers for FHE-ML Platform.

Implements scaling transformations compatible with encrypted data.
"""

import numpy as np
from typing import Optional, Union


class StandardScaler:
    """
    Standardize features by removing mean and scaling to unit variance.

    FHE-compatible: uses polynomial operations for scaling.

    Parameters
    ----------
    with_mean : bool
        Center data before scaling.
    with_std : bool
        Scale data to unit variance.

    Examples
    --------
    >>> from sdk.preprocessing import StandardScaler
    >>> scaler = StandardScaler()
    >>> X_scaled = scaler.fit_transform(X)
    """

    def __init__(self, with_mean: bool = True, with_std: bool = True):
        self.with_mean = with_mean
        self.with_std = with_std

        self.mean_: Optional[np.ndarray] = None
        self.var_: Optional[np.ndarray] = None
        self.scale_: Optional[np.ndarray] = None
        self.n_features_in_: Optional[int] = None
        self._is_fitted = False

    def fit(self, X: np.ndarray, y=None) -> "StandardScaler":
        """
        Compute mean and std for scaling.

        Parameters
        ----------
        X : np.ndarray of shape (n_samples, n_features)
            Training data.
        y : Ignored
            Not used.

        Returns
        -------
        self : StandardScaler
            Fitted scaler.
        """
        X = np.asarray(X, dtype=np.float64)
        self.n_features_in_ = X.shape[1]

        if self.with_mean:
            self.mean_ = np.mean(X, axis=0)
        else:
            self.mean_ = np.zeros(self.n_features_in_)

        if self.with_std:
            self.var_ = np.var(X, axis=0)
            self.scale_ = np.sqrt(self.var_)
            # Avoid division by zero
            self.scale_ = np.where(self.scale_ == 0, 1, self.scale_)
        else:
            self.var_ = np.ones(self.n_features_in_)
            self.scale_ = np.ones(self.n_features_in_)

        self._is_fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Standardize data.

        Parameters
        ----------
        X : np.ndarray of shape (n_samples, n_features)
            Data to transform.

        Returns
        -------
        X_scaled : np.ndarray
            Transformed data.
        """
        if not self._is_fitted:
            raise ValueError("Scaler not fitted. Call fit() first.")

        X = np.asarray(X, dtype=np.float64)
        return (X - self.mean_) / self.scale_

    def fit_transform(self, X: np.ndarray, y=None) -> np.ndarray:
        """Fit and transform in one step."""
        return self.fit(X, y).transform(X)

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """
        Reverse the scaling transformation.

        Parameters
        ----------
        X : np.ndarray
            Scaled data.

        Returns
        -------
        X_original : np.ndarray
            Original scale data.
        """
        if not self._is_fitted:
            raise ValueError("Scaler not fitted. Call fit() first.")

        X = np.asarray(X, dtype=np.float64)
        return X * self.scale_ + self.mean_


class MinMaxScaler:
    """
    Scale features to a given range (default [0, 1]).

    Parameters
    ----------
    feature_range : tuple
        Desired range of transformed data.

    Examples
    --------
    >>> from sdk.preprocessing import MinMaxScaler
    >>> scaler = MinMaxScaler(feature_range=(0, 1))
    >>> X_scaled = scaler.fit_transform(X)
    """

    def __init__(self, feature_range: tuple = (0, 1)):
        self.feature_range = feature_range

        self.min_: Optional[np.ndarray] = None
        self.max_: Optional[np.ndarray] = None
        self.scale_: Optional[np.ndarray] = None
        self.data_min_: Optional[np.ndarray] = None
        self.data_max_: Optional[np.ndarray] = None
        self.data_range_: Optional[np.ndarray] = None
        self.n_features_in_: Optional[int] = None
        self._is_fitted = False

    def fit(self, X: np.ndarray, y=None) -> "MinMaxScaler":
        """Compute min and max for scaling."""
        X = np.asarray(X, dtype=np.float64)
        self.n_features_in_ = X.shape[1]

        self.data_min_ = np.min(X, axis=0)
        self.data_max_ = np.max(X, axis=0)
        self.data_range_ = self.data_max_ - self.data_min_

        # Avoid division by zero
        self.data_range_ = np.where(self.data_range_ == 0, 1, self.data_range_)

        feature_min, feature_max = self.feature_range
        self.scale_ = (feature_max - feature_min) / self.data_range_
        self.min_ = feature_min - self.data_min_ * self.scale_

        self._is_fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Scale data to feature range."""
        if not self._is_fitted:
            raise ValueError("Scaler not fitted. Call fit() first.")

        X = np.asarray(X, dtype=np.float64)
        return X * self.scale_ + self.min_

    def fit_transform(self, X: np.ndarray, y=None) -> np.ndarray:
        """Fit and transform in one step."""
        return self.fit(X, y).transform(X)

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """Reverse the scaling transformation."""
        if not self._is_fitted:
            raise ValueError("Scaler not fitted. Call fit() first.")

        X = np.asarray(X, dtype=np.float64)
        return (X - self.min_) / self.scale_


class MaxAbsScaler:
    """
    Scale features by their maximum absolute value.

    Scales to [-1, 1] range without shifting/centering.
    Preserves sparsity.

    Examples
    --------
    >>> from sdk.preprocessing import MaxAbsScaler
    >>> scaler = MaxAbsScaler()
    >>> X_scaled = scaler.fit_transform(X)
    """

    def __init__(self):
        self.max_abs_: Optional[np.ndarray] = None
        self.scale_: Optional[np.ndarray] = None
        self.n_features_in_: Optional[int] = None
        self._is_fitted = False

    def fit(self, X: np.ndarray, y=None) -> "MaxAbsScaler":
        """Compute max absolute value for scaling."""
        X = np.asarray(X, dtype=np.float64)
        self.n_features_in_ = X.shape[1]

        self.max_abs_ = np.max(np.abs(X), axis=0)
        self.scale_ = np.where(self.max_abs_ == 0, 1, self.max_abs_)

        self._is_fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Scale data by max absolute value."""
        if not self._is_fitted:
            raise ValueError("Scaler not fitted. Call fit() first.")

        X = np.asarray(X, dtype=np.float64)
        return X / self.scale_

    def fit_transform(self, X: np.ndarray, y=None) -> np.ndarray:
        """Fit and transform in one step."""
        return self.fit(X, y).transform(X)

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """Reverse the scaling transformation."""
        if not self._is_fitted:
            raise ValueError("Scaler not fitted. Call fit() first.")

        X = np.asarray(X, dtype=np.float64)
        return X * self.scale_


class RobustScaler:
    """
    Scale features using statistics robust to outliers.

    Uses median and interquartile range (IQR).

    Parameters
    ----------
    with_centering : bool
        Center data using median.
    with_scaling : bool
        Scale data using IQR.
    quantile_range : tuple
        Quantile range for IQR (default 25th-75th percentile).

    Examples
    --------
    >>> from sdk.preprocessing import RobustScaler
    >>> scaler = RobustScaler()
    >>> X_scaled = scaler.fit_transform(X)
    """

    def __init__(
        self,
        with_centering: bool = True,
        with_scaling: bool = True,
        quantile_range: tuple = (25.0, 75.0),
    ):
        self.with_centering = with_centering
        self.with_scaling = with_scaling
        self.quantile_range = quantile_range

        self.center_: Optional[np.ndarray] = None
        self.scale_: Optional[np.ndarray] = None
        self.n_features_in_: Optional[int] = None
        self._is_fitted = False

    def fit(self, X: np.ndarray, y=None) -> "RobustScaler":
        """Compute median and IQR for scaling."""
        X = np.asarray(X, dtype=np.float64)
        self.n_features_in_ = X.shape[1]

        if self.with_centering:
            self.center_ = np.median(X, axis=0)
        else:
            self.center_ = np.zeros(self.n_features_in_)

        if self.with_scaling:
            q_min, q_max = self.quantile_range
            q_lower = np.percentile(X, q_min, axis=0)
            q_upper = np.percentile(X, q_max, axis=0)
            self.scale_ = q_upper - q_lower
            self.scale_ = np.where(self.scale_ == 0, 1, self.scale_)
        else:
            self.scale_ = np.ones(self.n_features_in_)

        self._is_fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Scale data using robust statistics."""
        if not self._is_fitted:
            raise ValueError("Scaler not fitted. Call fit() first.")

        X = np.asarray(X, dtype=np.float64)
        return (X - self.center_) / self.scale_

    def fit_transform(self, X: np.ndarray, y=None) -> np.ndarray:
        """Fit and transform in one step."""
        return self.fit(X, y).transform(X)

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """Reverse the scaling transformation."""
        if not self._is_fitted:
            raise ValueError("Scaler not fitted. Call fit() first.")

        X = np.asarray(X, dtype=np.float64)
        return X * self.scale_ + self.center_


class Normalizer:
    """
    Normalize samples individually to unit norm.

    Parameters
    ----------
    norm : str
        Norm to use ('l1', 'l2', 'max').

    Examples
    --------
    >>> from sdk.preprocessing import Normalizer
    >>> normalizer = Normalizer(norm='l2')
    >>> X_normalized = normalizer.fit_transform(X)
    """

    def __init__(self, norm: str = "l2"):
        self.norm = norm
        self._is_fitted = False

    def fit(self, X: np.ndarray, y=None) -> "Normalizer":
        """Fit the normalizer (no-op, just validates)."""
        X = np.asarray(X, dtype=np.float64)
        self._is_fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Normalize samples to unit norm."""
        X = np.asarray(X, dtype=np.float64)

        if self.norm == "l1":
            norms = np.sum(np.abs(X), axis=1, keepdims=True)
        elif self.norm == "l2":
            norms = np.sqrt(np.sum(X**2, axis=1, keepdims=True))
        elif self.norm == "max":
            norms = np.max(np.abs(X), axis=1, keepdims=True)
        else:
            raise ValueError(f"Unknown norm: {self.norm}")

        norms = np.where(norms == 0, 1, norms)
        return X / norms

    def fit_transform(self, X: np.ndarray, y=None) -> np.ndarray:
        """Fit and transform in one step."""
        return self.fit(X, y).transform(X)

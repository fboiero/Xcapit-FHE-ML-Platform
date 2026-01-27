"""
FHE-Compatible Data Transformers

Individual transformer classes for preprocessing data before FHE encryption.
All transformers follow scikit-learn's fit/transform API pattern.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Union, Any
import numpy as np


class TransformerState(Enum):
    """State of a transformer in its lifecycle."""
    INITIALIZED = "initialized"
    FITTED = "fitted"


@dataclass
class TransformerParams:
    """Base class for transformer parameters."""
    pass


class BaseTransformer(ABC):
    """
    Abstract base class for all transformers.

    All transformers must implement:
    - fit(): Learn parameters from data
    - transform(): Apply transformation
    - inverse_transform(): Reverse transformation (if applicable)
    - get_params(): Return learned parameters for serialization
    """

    def __init__(self, name: Optional[str] = None):
        self.name = name or self.__class__.__name__
        self.state = TransformerState.INITIALIZED
        self._params: dict = {}

    @abstractmethod
    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> 'BaseTransformer':
        """Fit transformer to data. Returns self for chaining."""
        pass

    @abstractmethod
    def transform(self, X: np.ndarray) -> np.ndarray:
        """Apply transformation to data."""
        pass

    def fit_transform(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> np.ndarray:
        """Fit and transform in one step."""
        return self.fit(X, y).transform(X)

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """Reverse transformation. Override in subclasses that support it."""
        raise NotImplementedError(f"{self.name} does not support inverse_transform")

    def get_params(self) -> dict:
        """Return learned parameters for serialization."""
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "state": self.state.value,
            "params": self._params.copy()
        }

    def _check_fitted(self):
        """Raise error if transformer is not fitted."""
        if self.state != TransformerState.FITTED:
            raise RuntimeError(f"{self.name} must be fitted before transform")

    def _validate_input(self, X: np.ndarray) -> np.ndarray:
        """Validate and convert input to numpy array."""
        if not isinstance(X, np.ndarray):
            X = np.array(X)
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        return X.astype(np.float64)


class StandardScaler(BaseTransformer):
    """
    Standardize features by removing mean and scaling to unit variance.

    z = (x - mean) / std

    This is often preferred for FHE as it centers data around 0.

    Parameters
    ----------
    with_mean : bool, default=True
        Center data by subtracting mean.
    with_std : bool, default=True
        Scale data by dividing by standard deviation.
    """

    def __init__(self, with_mean: bool = True, with_std: bool = True, name: Optional[str] = None):
        super().__init__(name)
        self.with_mean = with_mean
        self.with_std = with_std
        self._mean: Optional[np.ndarray] = None
        self._std: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> 'StandardScaler':
        X = self._validate_input(X)

        if self.with_mean:
            self._mean = np.mean(X, axis=0)
        else:
            self._mean = np.zeros(X.shape[1])

        if self.with_std:
            self._std = np.std(X, axis=0)
            # Avoid division by zero
            self._std[self._std == 0] = 1.0
        else:
            self._std = np.ones(X.shape[1])

        self._params = {
            "mean": self._mean.tolist(),
            "std": self._std.tolist(),
            "n_features": X.shape[1]
        }
        self.state = TransformerState.FITTED
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        self._check_fitted()
        X = self._validate_input(X)
        return (X - self._mean) / self._std

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        self._check_fitted()
        X = self._validate_input(X)
        return X * self._std + self._mean


class MinMaxScaler(BaseTransformer):
    """
    Scale features to a given range (default [-1, 1] for FHE compatibility).

    X_scaled = (X - min) / (max - min) * (feature_range[1] - feature_range[0]) + feature_range[0]

    Parameters
    ----------
    feature_range : tuple, default=(-1, 1)
        Desired range of transformed data. Default is [-1, 1] which is
        optimal for CKKS encryption precision.
    """

    def __init__(self, feature_range: tuple = (-1, 1), name: Optional[str] = None):
        super().__init__(name)
        self.feature_range = feature_range
        self._min: Optional[np.ndarray] = None
        self._max: Optional[np.ndarray] = None
        self._data_range: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> 'MinMaxScaler':
        X = self._validate_input(X)

        self._min = np.min(X, axis=0)
        self._max = np.max(X, axis=0)
        self._data_range = self._max - self._min
        # Avoid division by zero
        self._data_range[self._data_range == 0] = 1.0

        self._params = {
            "min": self._min.tolist(),
            "max": self._max.tolist(),
            "data_range": self._data_range.tolist(),
            "feature_range": list(self.feature_range),
            "n_features": X.shape[1]
        }
        self.state = TransformerState.FITTED
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        self._check_fitted()
        X = self._validate_input(X)

        # Scale to [0, 1]
        X_scaled = (X - self._min) / self._data_range
        # Scale to feature_range
        range_min, range_max = self.feature_range
        return X_scaled * (range_max - range_min) + range_min

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        self._check_fitted()
        X = self._validate_input(X)

        range_min, range_max = self.feature_range
        # Reverse scale from feature_range to [0, 1]
        X_unscaled = (X - range_min) / (range_max - range_min)
        # Reverse scale to original range
        return X_unscaled * self._data_range + self._min


class RobustScaler(BaseTransformer):
    """
    Scale features using statistics that are robust to outliers.

    Uses median and interquartile range (IQR) instead of mean and std.

    X_scaled = (X - median) / IQR

    Parameters
    ----------
    with_centering : bool, default=True
        Center data by subtracting median.
    with_scaling : bool, default=True
        Scale data by dividing by IQR.
    quantile_range : tuple, default=(25.0, 75.0)
        Quantile range used to calculate scale.
    """

    def __init__(
        self,
        with_centering: bool = True,
        with_scaling: bool = True,
        quantile_range: tuple = (25.0, 75.0),
        name: Optional[str] = None
    ):
        super().__init__(name)
        self.with_centering = with_centering
        self.with_scaling = with_scaling
        self.quantile_range = quantile_range
        self._center: Optional[np.ndarray] = None
        self._scale: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> 'RobustScaler':
        X = self._validate_input(X)

        if self.with_centering:
            self._center = np.median(X, axis=0)
        else:
            self._center = np.zeros(X.shape[1])

        if self.with_scaling:
            q_min, q_max = self.quantile_range
            q_low = np.percentile(X, q_min, axis=0)
            q_high = np.percentile(X, q_max, axis=0)
            self._scale = q_high - q_low
            self._scale[self._scale == 0] = 1.0
        else:
            self._scale = np.ones(X.shape[1])

        self._params = {
            "center": self._center.tolist(),
            "scale": self._scale.tolist(),
            "quantile_range": list(self.quantile_range),
            "n_features": X.shape[1]
        }
        self.state = TransformerState.FITTED
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        self._check_fitted()
        X = self._validate_input(X)
        return (X - self._center) / self._scale

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        self._check_fitted()
        X = self._validate_input(X)
        return X * self._scale + self._center


class OneHotEncoder(BaseTransformer):
    """
    Encode categorical features as one-hot numeric array.

    Each category becomes a binary column.

    Parameters
    ----------
    columns : list[int], optional
        Indices of columns to encode. If None, auto-detect categorical columns.
    drop_first : bool, default=False
        Drop first category to avoid multicollinearity.
    handle_unknown : str, default='error'
        How to handle unknown categories: 'error' or 'ignore'.
    """

    def __init__(
        self,
        columns: Optional[list] = None,
        drop_first: bool = False,
        handle_unknown: str = 'error',
        name: Optional[str] = None
    ):
        super().__init__(name)
        self.columns = columns
        self.drop_first = drop_first
        self.handle_unknown = handle_unknown
        self._categories: dict = {}
        self._n_features_in: int = 0
        self._feature_indices: list = []

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> 'OneHotEncoder':
        X = self._validate_input(X)
        self._n_features_in = X.shape[1]

        # Determine which columns to encode
        if self.columns is None:
            # Auto-detect: columns with few unique values (< 20) or non-float looking
            self._feature_indices = []
            for i in range(X.shape[1]):
                unique_vals = np.unique(X[:, i])
                if len(unique_vals) < 20:
                    self._feature_indices.append(i)
        else:
            self._feature_indices = list(self.columns)

        # Learn categories for each column
        self._categories = {}
        for col_idx in self._feature_indices:
            categories = np.unique(X[:, col_idx])
            if self.drop_first:
                categories = categories[1:]  # Drop first category
            self._categories[col_idx] = categories.tolist()

        self._params = {
            "categories": self._categories,
            "feature_indices": self._feature_indices,
            "drop_first": self.drop_first,
            "n_features_in": self._n_features_in
        }
        self.state = TransformerState.FITTED
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        self._check_fitted()
        X = self._validate_input(X)

        if X.shape[1] != self._n_features_in:
            raise ValueError(f"Expected {self._n_features_in} features, got {X.shape[1]}")

        result_parts = []

        for col_idx in range(X.shape[1]):
            if col_idx in self._feature_indices:
                # One-hot encode this column
                categories = self._categories[col_idx]
                encoded = np.zeros((X.shape[0], len(categories)))

                for i, cat in enumerate(categories):
                    encoded[:, i] = (X[:, col_idx] == cat).astype(float)

                # Handle unknown categories
                known_mask = np.isin(X[:, col_idx], categories)
                if not np.all(known_mask):
                    if self.handle_unknown == 'error':
                        unknown = X[~known_mask, col_idx]
                        raise ValueError(f"Unknown categories in column {col_idx}: {np.unique(unknown)}")
                    # 'ignore' - leave as all zeros

                result_parts.append(encoded)
            else:
                # Keep original column
                result_parts.append(X[:, col_idx:col_idx+1])

        return np.hstack(result_parts)

    def get_feature_names_out(self, input_features: Optional[list] = None) -> list:
        """Get output feature names after transformation."""
        self._check_fitted()

        if input_features is None:
            input_features = [f"x{i}" for i in range(self._n_features_in)]

        output_names = []
        for col_idx in range(self._n_features_in):
            if col_idx in self._feature_indices:
                for cat in self._categories[col_idx]:
                    output_names.append(f"{input_features[col_idx]}_{cat}")
            else:
                output_names.append(input_features[col_idx])

        return output_names


class OrdinalEncoder(BaseTransformer):
    """
    Encode categorical features as integer values.

    Each unique category is mapped to an integer starting from 0.

    Parameters
    ----------
    columns : list[int], optional
        Indices of columns to encode. If None, auto-detect.
    handle_unknown : str, default='error'
        How to handle unknown categories: 'error' or 'use_encoded_value'.
    unknown_value : float, default=-1
        Value to use for unknown categories if handle_unknown='use_encoded_value'.
    """

    def __init__(
        self,
        columns: Optional[list] = None,
        handle_unknown: str = 'error',
        unknown_value: float = -1,
        name: Optional[str] = None
    ):
        super().__init__(name)
        self.columns = columns
        self.handle_unknown = handle_unknown
        self.unknown_value = unknown_value
        self._mappings: dict = {}
        self._inverse_mappings: dict = {}
        self._n_features_in: int = 0
        self._feature_indices: list = []

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> 'OrdinalEncoder':
        X = self._validate_input(X)
        self._n_features_in = X.shape[1]

        if self.columns is None:
            self._feature_indices = list(range(X.shape[1]))
        else:
            self._feature_indices = list(self.columns)

        self._mappings = {}
        self._inverse_mappings = {}

        for col_idx in self._feature_indices:
            unique_vals = np.unique(X[:, col_idx])
            mapping = {val: idx for idx, val in enumerate(unique_vals)}
            self._mappings[col_idx] = mapping
            self._inverse_mappings[col_idx] = {v: k for k, v in mapping.items()}

        self._params = {
            "mappings": {k: {str(kk): vv for kk, vv in v.items()}
                        for k, v in self._mappings.items()},
            "feature_indices": self._feature_indices,
            "n_features_in": self._n_features_in
        }
        self.state = TransformerState.FITTED
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        self._check_fitted()
        X = self._validate_input(X)
        X_encoded = X.copy()

        for col_idx in self._feature_indices:
            mapping = self._mappings[col_idx]
            for i in range(X.shape[0]):
                val = X[i, col_idx]
                if val in mapping:
                    X_encoded[i, col_idx] = mapping[val]
                elif self.handle_unknown == 'error':
                    raise ValueError(f"Unknown value {val} in column {col_idx}")
                else:
                    X_encoded[i, col_idx] = self.unknown_value

        return X_encoded

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        self._check_fitted()
        X = self._validate_input(X)
        X_decoded = X.copy()

        for col_idx in self._feature_indices:
            inv_mapping = self._inverse_mappings[col_idx]
            for i in range(X.shape[0]):
                val = int(X[i, col_idx])
                if val in inv_mapping:
                    X_decoded[i, col_idx] = inv_mapping[val]

        return X_decoded


class MissingValueHandler(BaseTransformer):
    """
    Handle missing values in data.

    Parameters
    ----------
    strategy : str, default='mean'
        Strategy to use: 'mean', 'median', 'most_frequent', 'constant'.
    fill_value : float, optional
        Value to use when strategy='constant'.
    """

    def __init__(
        self,
        strategy: str = 'mean',
        fill_value: Optional[float] = None,
        name: Optional[str] = None
    ):
        super().__init__(name)
        if strategy not in ('mean', 'median', 'most_frequent', 'constant'):
            raise ValueError(f"Invalid strategy: {strategy}")
        self.strategy = strategy
        self.fill_value = fill_value
        self._fill_values: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> 'MissingValueHandler':
        X = self._validate_input(X)

        self._fill_values = np.zeros(X.shape[1])

        for col_idx in range(X.shape[1]):
            col = X[:, col_idx]
            valid_mask = ~np.isnan(col)
            valid_values = col[valid_mask]

            if len(valid_values) == 0:
                self._fill_values[col_idx] = 0.0
            elif self.strategy == 'mean':
                self._fill_values[col_idx] = np.mean(valid_values)
            elif self.strategy == 'median':
                self._fill_values[col_idx] = np.median(valid_values)
            elif self.strategy == 'most_frequent':
                values, counts = np.unique(valid_values, return_counts=True)
                self._fill_values[col_idx] = values[np.argmax(counts)]
            elif self.strategy == 'constant':
                self._fill_values[col_idx] = self.fill_value or 0.0

        self._params = {
            "strategy": self.strategy,
            "fill_values": self._fill_values.tolist(),
            "n_features": X.shape[1]
        }
        self.state = TransformerState.FITTED
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        self._check_fitted()
        X = self._validate_input(X)
        X_filled = X.copy()

        for col_idx in range(X.shape[1]):
            mask = np.isnan(X_filled[:, col_idx])
            X_filled[mask, col_idx] = self._fill_values[col_idx]

        return X_filled


class OutlierHandler(BaseTransformer):
    """
    Handle outliers in data using IQR or Z-score method.

    Parameters
    ----------
    method : str, default='iqr'
        Method to detect outliers: 'iqr' or 'zscore'.
    threshold : float, default=1.5
        For IQR: multiplier for IQR range (1.5 is standard).
        For Z-score: number of standard deviations (3 is common).
    strategy : str, default='clip'
        How to handle outliers: 'clip' (cap at bounds) or 'nan' (set to NaN).
    """

    def __init__(
        self,
        method: str = 'iqr',
        threshold: float = 1.5,
        strategy: str = 'clip',
        name: Optional[str] = None
    ):
        super().__init__(name)
        if method not in ('iqr', 'zscore'):
            raise ValueError(f"Invalid method: {method}")
        if strategy not in ('clip', 'nan'):
            raise ValueError(f"Invalid strategy: {strategy}")

        self.method = method
        self.threshold = threshold
        self.strategy = strategy
        self._lower_bounds: Optional[np.ndarray] = None
        self._upper_bounds: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> 'OutlierHandler':
        X = self._validate_input(X)

        self._lower_bounds = np.zeros(X.shape[1])
        self._upper_bounds = np.zeros(X.shape[1])

        for col_idx in range(X.shape[1]):
            col = X[:, col_idx]

            if self.method == 'iqr':
                q1 = np.percentile(col, 25)
                q3 = np.percentile(col, 75)
                iqr = q3 - q1
                self._lower_bounds[col_idx] = q1 - self.threshold * iqr
                self._upper_bounds[col_idx] = q3 + self.threshold * iqr
            else:  # zscore
                mean = np.mean(col)
                std = np.std(col)
                self._lower_bounds[col_idx] = mean - self.threshold * std
                self._upper_bounds[col_idx] = mean + self.threshold * std

        self._params = {
            "method": self.method,
            "threshold": self.threshold,
            "strategy": self.strategy,
            "lower_bounds": self._lower_bounds.tolist(),
            "upper_bounds": self._upper_bounds.tolist(),
            "n_features": X.shape[1]
        }
        self.state = TransformerState.FITTED
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        self._check_fitted()
        X = self._validate_input(X)
        X_handled = X.copy()

        for col_idx in range(X.shape[1]):
            lower = self._lower_bounds[col_idx]
            upper = self._upper_bounds[col_idx]

            if self.strategy == 'clip':
                X_handled[:, col_idx] = np.clip(X_handled[:, col_idx], lower, upper)
            else:  # nan
                mask = (X_handled[:, col_idx] < lower) | (X_handled[:, col_idx] > upper)
                X_handled[mask, col_idx] = np.nan

        return X_handled


class FeatureSelector(BaseTransformer):
    """
    Select features based on variance or correlation threshold.

    Parameters
    ----------
    method : str, default='variance'
        Selection method: 'variance' or 'correlation'.
    threshold : float, default=0.0
        For variance: minimum variance to keep feature.
        For correlation: maximum correlation to keep feature.
    """

    def __init__(
        self,
        method: str = 'variance',
        threshold: float = 0.0,
        name: Optional[str] = None
    ):
        super().__init__(name)
        if method not in ('variance', 'correlation'):
            raise ValueError(f"Invalid method: {method}")

        self.method = method
        self.threshold = threshold
        self._selected_indices: Optional[list] = None
        self._n_features_in: int = 0

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> 'FeatureSelector':
        X = self._validate_input(X)
        self._n_features_in = X.shape[1]

        if self.method == 'variance':
            variances = np.var(X, axis=0)
            self._selected_indices = np.where(variances > self.threshold)[0].tolist()
        else:  # correlation - remove highly correlated features
            self._selected_indices = list(range(X.shape[1]))
            corr_matrix = np.corrcoef(X.T)

            to_remove = set()
            for i in range(len(corr_matrix)):
                for j in range(i + 1, len(corr_matrix)):
                    if abs(corr_matrix[i, j]) > self.threshold:
                        # Remove the one with lower variance
                        var_i = np.var(X[:, i])
                        var_j = np.var(X[:, j])
                        to_remove.add(j if var_i > var_j else i)

            self._selected_indices = [i for i in range(X.shape[1]) if i not in to_remove]

        self._params = {
            "method": self.method,
            "threshold": self.threshold,
            "selected_indices": self._selected_indices,
            "n_features_in": self._n_features_in,
            "n_features_out": len(self._selected_indices)
        }
        self.state = TransformerState.FITTED
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        self._check_fitted()
        X = self._validate_input(X)

        if X.shape[1] != self._n_features_in:
            raise ValueError(f"Expected {self._n_features_in} features, got {X.shape[1]}")

        return X[:, self._selected_indices]

    def get_support(self) -> list:
        """Return indices of selected features."""
        self._check_fitted()
        return self._selected_indices.copy()

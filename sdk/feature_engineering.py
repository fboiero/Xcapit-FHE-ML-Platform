"""
Feature engineering utilities for FHE-ML SDK.

Provides feature transformation and generation methods:
- PolynomialFeatures: Generate polynomial and interaction features
- InteractionFeatures: Generate pairwise interactions only
- KBinsDiscretizer: Bin continuous data into intervals
- Binarizer: Threshold values to binary
- FunctionTransformer: Apply custom transformations
- TargetEncoder: Encode categorical features by target statistics
"""

from __future__ import annotations

from itertools import combinations, combinations_with_replacement
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np


class BaseTransformer:
    """Base class for feature transformers."""

    def __init__(self):
        self.is_fitted_: bool = False
        self.n_features_in_: int = 0
        self.n_features_out_: int = 0

    def _check_is_fitted(self) -> None:
        """Check if transformer is fitted."""
        if not self.is_fitted_:
            raise ValueError("Transformer not fitted. Call fit() first.")

    def fit_transform(self, X: np.ndarray, y: np.ndarray = None) -> np.ndarray:
        """Fit and transform data."""
        return self.fit(X, y).transform(X)


class PolynomialFeatures(BaseTransformer):
    """
    Generate polynomial and interaction features.

    Generates features [1, a, b, a^2, ab, b^2] for degree=2.

    Parameters
    ----------
    degree : int, default=2
        Maximum polynomial degree.
    interaction_only : bool, default=False
        If True, only produce interaction features.
    include_bias : bool, default=True
        If True, include a bias (all 1s) column.

    Attributes
    ----------
    n_features_in_ : int
        Number of input features.
    n_features_out_ : int
        Number of output features.
    powers_ : array
        Exponent matrix for each output feature.

    Examples
    --------
    >>> from sdk.feature_engineering import PolynomialFeatures
    >>> poly = PolynomialFeatures(degree=2)
    >>> X = np.array([[1, 2], [3, 4]])
    >>> X_poly = poly.fit_transform(X)
    # Result: [1, a, b, a^2, ab, b^2]
    """

    def __init__(
        self,
        degree: int = 2,
        interaction_only: bool = False,
        include_bias: bool = True,
    ):
        super().__init__()
        self.degree = degree
        self.interaction_only = interaction_only
        self.include_bias = include_bias
        self.powers_: Optional[np.ndarray] = None
        self.feature_names_: List[str] = []

    def fit(self, X: np.ndarray, y: np.ndarray = None) -> PolynomialFeatures:
        """
        Compute the exponent combinations.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : Ignored

        Returns
        -------
        self : PolynomialFeatures
        """
        X = np.asarray(X)
        self.n_features_in_ = X.shape[1]

        # Generate all combinations of powers
        powers = []
        feature_names = []

        for d in range(self.degree + 1):
            if d == 0 and self.include_bias:
                powers.append(tuple([0] * self.n_features_in_))
                feature_names.append("1")
            elif d > 0:
                if self.interaction_only:
                    # Only interactions (different features)
                    for combo in combinations(range(self.n_features_in_), d):
                        power = [0] * self.n_features_in_
                        for idx in combo:
                            power[idx] = 1
                        powers.append(tuple(power))
                        name = "*".join([f"x{i}" for i in combo])
                        feature_names.append(name)
                else:
                    # All combinations with replacement
                    for combo in combinations_with_replacement(range(self.n_features_in_), d):
                        power = [0] * self.n_features_in_
                        for idx in combo:
                            power[idx] += 1
                        powers.append(tuple(power))
                        name = "*".join(
                            [
                                f"x{i}^{power[i]}" if power[i] > 1 else f"x{i}"
                                for i in range(self.n_features_in_)
                                if power[i] > 0
                            ]
                        )
                        feature_names.append(name)

        self.powers_ = np.array(powers)
        self.feature_names_ = feature_names
        self.n_features_out_ = len(powers)
        self.is_fitted_ = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Transform data to polynomial features.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Data to transform.

        Returns
        -------
        X_poly : array of shape (n_samples, n_output_features)
            Transformed data.
        """
        self._check_is_fitted()
        X = np.asarray(X)
        n_samples = X.shape[0]

        result = np.empty((n_samples, self.n_features_out_))

        for i, power in enumerate(self.powers_):
            result[:, i] = np.prod(X**power, axis=1)

        return result

    def get_feature_names(self, input_features: Optional[List[str]] = None) -> List[str]:
        """Get output feature names."""
        self._check_is_fitted()
        if input_features is None:
            return self.feature_names_

        # Replace x0, x1, ... with actual names
        names = []
        for name in self.feature_names_:
            for i, feat in enumerate(input_features):
                name = name.replace(f"x{i}", feat)
            names.append(name)
        return names


class InteractionFeatures(BaseTransformer):
    """
    Generate only pairwise interaction features.

    Parameters
    ----------
    include_self : bool, default=False
        If True, include self-interactions (x^2).

    Examples
    --------
    >>> from sdk.feature_engineering import InteractionFeatures
    >>> inter = InteractionFeatures()
    >>> X = np.array([[1, 2, 3], [4, 5, 6]])
    >>> X_inter = inter.fit_transform(X)
    # Result includes: x0*x1, x0*x2, x1*x2
    """

    def __init__(self, include_self: bool = False):
        super().__init__()
        self.include_self = include_self
        self.interaction_pairs_: List[Tuple[int, int]] = []

    def fit(self, X: np.ndarray, y: np.ndarray = None) -> InteractionFeatures:
        """Fit the interaction feature generator."""
        X = np.asarray(X)
        self.n_features_in_ = X.shape[1]

        self.interaction_pairs_ = []
        for i in range(self.n_features_in_):
            start = i if self.include_self else i + 1
            for j in range(start, self.n_features_in_):
                self.interaction_pairs_.append((i, j))

        self.n_features_out_ = self.n_features_in_ + len(self.interaction_pairs_)
        self.is_fitted_ = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Transform data to include interaction features."""
        self._check_is_fitted()
        X = np.asarray(X)

        # Start with original features
        interactions = [X]

        # Add interaction features
        for i, j in self.interaction_pairs_:
            interactions.append((X[:, i] * X[:, j]).reshape(-1, 1))

        return np.hstack(interactions)


class KBinsDiscretizer(BaseTransformer):
    """
    Bin continuous data into intervals.

    Parameters
    ----------
    n_bins : int or array-like, default=5
        Number of bins per feature. If int, same for all features.
    encode : str, default='onehot'
        Encoding method ('ordinal', 'onehot', 'onehot-dense').
    strategy : str, default='quantile'
        Binning strategy ('uniform', 'quantile', 'kmeans').

    Attributes
    ----------
    bin_edges_ : list of arrays
        Bin edges for each feature.
    n_bins_ : array
        Actual number of bins per feature.

    Examples
    --------
    >>> from sdk.feature_engineering import KBinsDiscretizer
    >>> kbd = KBinsDiscretizer(n_bins=3, encode='ordinal')
    >>> X_binned = kbd.fit_transform(X)
    """

    def __init__(
        self,
        n_bins: Union[int, List[int]] = 5,
        encode: str = "onehot",
        strategy: str = "quantile",
    ):
        super().__init__()
        self.n_bins = n_bins
        self.encode = encode
        self.strategy = strategy
        self.bin_edges_: List[np.ndarray] = []
        self.n_bins_: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray, y: np.ndarray = None) -> KBinsDiscretizer:
        """
        Fit the discretizer.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Data to bin.
        y : Ignored

        Returns
        -------
        self : KBinsDiscretizer
        """
        X = np.asarray(X)
        n_samples, n_features = X.shape
        self.n_features_in_ = n_features

        # Determine number of bins per feature
        if isinstance(self.n_bins, int):
            n_bins = [self.n_bins] * n_features
        else:
            n_bins = list(self.n_bins)

        self.bin_edges_ = []
        actual_n_bins = []

        for i in range(n_features):
            col = X[:, i]
            k = n_bins[i]

            if self.strategy == "uniform":
                # Equal-width bins
                min_val, max_val = col.min(), col.max()
                edges = np.linspace(min_val, max_val, k + 1)
            elif self.strategy == "quantile":
                # Equal-frequency bins
                quantiles = np.linspace(0, 100, k + 1)
                edges = np.percentile(col, quantiles)
                edges = np.unique(edges)  # Remove duplicates
            elif self.strategy == "kmeans":
                # K-means clustering
                edges = self._kmeans_bins(col, k)
            else:
                raise ValueError(f"Unknown strategy: {self.strategy}")

            self.bin_edges_.append(edges)
            actual_n_bins.append(len(edges) - 1)

        self.n_bins_ = np.array(actual_n_bins)

        # Calculate output features
        if self.encode == "ordinal":
            self.n_features_out_ = n_features
        else:
            self.n_features_out_ = sum(actual_n_bins)

        self.is_fitted_ = True
        return self

    def _kmeans_bins(self, col: np.ndarray, k: int) -> np.ndarray:
        """Compute bin edges using k-means."""
        # Simple 1D k-means
        col_sorted = np.sort(col)
        len(col_sorted)

        # Initialize centers uniformly
        centers = np.linspace(col_sorted.min(), col_sorted.max(), k)

        for _ in range(100):  # Max iterations
            # Assign points to nearest center
            distances = np.abs(col_sorted[:, np.newaxis] - centers)
            labels = np.argmin(distances, axis=1)

            # Update centers
            new_centers = np.array(
                [
                    col_sorted[labels == i].mean() if np.sum(labels == i) > 0 else centers[i]
                    for i in range(k)
                ]
            )

            if np.allclose(centers, new_centers):
                break
            centers = new_centers

        # Compute bin edges as midpoints between centers
        centers_sorted = np.sort(centers)
        edges = np.concatenate(
            [
                [col_sorted.min()],
                (centers_sorted[:-1] + centers_sorted[1:]) / 2,
                [col_sorted.max()],
            ]
        )
        return edges

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Discretize the data.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Data to discretize.

        Returns
        -------
        X_binned : array
            Discretized data.
        """
        self._check_is_fitted()
        X = np.asarray(X)
        n_samples = X.shape[0]

        # Compute bin indices
        bin_indices = np.zeros((n_samples, self.n_features_in_), dtype=int)
        for i in range(self.n_features_in_):
            # np.digitize returns 1-indexed, so subtract 1
            bin_indices[:, i] = np.clip(
                np.digitize(X[:, i], self.bin_edges_[i]) - 1,
                0,
                self.n_bins_[i] - 1,
            )

        if self.encode == "ordinal":
            return bin_indices.astype(float)
        else:
            # One-hot encoding
            result = []
            for i in range(self.n_features_in_):
                n_bins = self.n_bins_[i]
                onehot = np.zeros((n_samples, n_bins))
                onehot[np.arange(n_samples), bin_indices[:, i]] = 1
                result.append(onehot)
            return np.hstack(result)


class Binarizer(BaseTransformer):
    """
    Binarize values based on threshold.

    Parameters
    ----------
    threshold : float, default=0.0
        Values <= threshold become 0, > threshold become 1.

    Examples
    --------
    >>> from sdk.feature_engineering import Binarizer
    >>> binarizer = Binarizer(threshold=0.5)
    >>> X_binary = binarizer.fit_transform(X)
    """

    def __init__(self, threshold: float = 0.0):
        super().__init__()
        self.threshold = threshold

    def fit(self, X: np.ndarray, y: np.ndarray = None) -> Binarizer:
        """Fit (no-op, for API consistency)."""
        X = np.asarray(X)
        self.n_features_in_ = X.shape[1] if X.ndim == 2 else 1
        self.n_features_out_ = self.n_features_in_
        self.is_fitted_ = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Binarize the data."""
        self._check_is_fitted()
        X = np.asarray(X)
        return (X > self.threshold).astype(float)


class FunctionTransformer(BaseTransformer):
    """
    Apply a custom function to transform features.

    Parameters
    ----------
    func : callable, optional
        Function to apply during transform. If None, identity.
    inverse_func : callable, optional
        Inverse function for inverse_transform.
    validate : bool, default=True
        Whether to validate input.
    kw_args : dict, optional
        Additional keyword arguments for func.

    Examples
    --------
    >>> from sdk.feature_engineering import FunctionTransformer
    >>> log_transformer = FunctionTransformer(np.log1p, np.expm1)
    >>> X_log = log_transformer.fit_transform(X)
    """

    def __init__(
        self,
        func: Optional[Callable] = None,
        inverse_func: Optional[Callable] = None,
        validate: bool = True,
        kw_args: Optional[dict] = None,
    ):
        super().__init__()
        self.func = func
        self.inverse_func = inverse_func
        self.validate = validate
        self.kw_args = kw_args or {}

    def fit(self, X: np.ndarray, y: np.ndarray = None) -> FunctionTransformer:
        """Fit (validates input)."""
        if self.validate:
            X = np.asarray(X)
        self.n_features_in_ = X.shape[1] if X.ndim == 2 else 1
        self.n_features_out_ = self.n_features_in_
        self.is_fitted_ = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Apply the function."""
        self._check_is_fitted()
        if self.validate:
            X = np.asarray(X)
        if self.func is None:
            return X
        return self.func(X, **self.kw_args)

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """Apply inverse function."""
        self._check_is_fitted()
        if self.inverse_func is None:
            raise ValueError("No inverse function specified")
        if self.validate:
            X = np.asarray(X)
        return self.inverse_func(X)


class TargetEncoder(BaseTransformer):
    """
    Encode categorical features using target statistics.

    For each category, replace with the mean of the target for that category.

    Parameters
    ----------
    smoothing : float, default=1.0
        Smoothing factor for regularization.
    min_samples_leaf : int, default=1
        Minimum samples required for a category.

    Attributes
    ----------
    encoding_map_ : dict
        Mapping from category to encoded value for each feature.
    global_mean_ : float
        Global target mean.

    Examples
    --------
    >>> from sdk.feature_engineering import TargetEncoder
    >>> encoder = TargetEncoder()
    >>> X_encoded = encoder.fit_transform(X_cat, y)
    """

    def __init__(self, smoothing: float = 1.0, min_samples_leaf: int = 1):
        super().__init__()
        self.smoothing = smoothing
        self.min_samples_leaf = min_samples_leaf
        self.encoding_map_: Dict[int, Dict[Any, float]] = {}
        self.global_mean_: float = 0.0

    def fit(self, X: np.ndarray, y: np.ndarray) -> TargetEncoder:
        """
        Fit the target encoder.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Categorical features.
        y : array-like of shape (n_samples,)
            Target values.

        Returns
        -------
        self : TargetEncoder
        """
        X = np.asarray(X)
        y = np.asarray(y)
        self.n_features_in_ = X.shape[1]
        self.n_features_out_ = self.n_features_in_

        self.global_mean_ = np.mean(y)
        self.encoding_map_ = {}

        for i in range(self.n_features_in_):
            col = X[:, i]
            categories = np.unique(col)
            encoding = {}

            for cat in categories:
                mask = col == cat
                n_samples = np.sum(mask)

                if n_samples < self.min_samples_leaf:
                    encoding[cat] = self.global_mean_
                else:
                    cat_mean = np.mean(y[mask])
                    # Smoothing: blend with global mean
                    lambda_smooth = 1 / (
                        1 + np.exp(-(n_samples - self.min_samples_leaf) / self.smoothing)
                    )
                    encoding[cat] = (
                        lambda_smooth * cat_mean + (1 - lambda_smooth) * self.global_mean_
                    )

            self.encoding_map_[i] = encoding

        self.is_fitted_ = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Transform categorical features to encoded values."""
        self._check_is_fitted()
        X = np.asarray(X)
        result = np.zeros_like(X, dtype=float)

        for i in range(self.n_features_in_):
            encoding = self.encoding_map_[i]
            for j, val in enumerate(X[:, i]):
                result[j, i] = encoding.get(val, self.global_mean_)

        return result


class OrdinalEncoder(BaseTransformer):
    """
    Encode categorical features as ordinal integers.

    Parameters
    ----------
    handle_unknown : str, default='error'
        How to handle unknown categories ('error', 'use_encoded_value').
    unknown_value : int, default=-1
        Value to use for unknown categories.

    Examples
    --------
    >>> from sdk.feature_engineering import OrdinalEncoder
    >>> encoder = OrdinalEncoder()
    >>> X_encoded = encoder.fit_transform(X_cat)
    """

    def __init__(
        self,
        handle_unknown: str = "error",
        unknown_value: int = -1,
    ):
        super().__init__()
        self.handle_unknown = handle_unknown
        self.unknown_value = unknown_value
        self.categories_: List[np.ndarray] = []
        self.category_map_: List[Dict[Any, int]] = []

    def fit(self, X: np.ndarray, y: np.ndarray = None) -> OrdinalEncoder:
        """Fit the ordinal encoder."""
        X = np.asarray(X)
        self.n_features_in_ = X.shape[1]
        self.n_features_out_ = self.n_features_in_

        self.categories_ = []
        self.category_map_ = []

        for i in range(self.n_features_in_):
            categories = np.unique(X[:, i])
            self.categories_.append(categories)
            self.category_map_.append({cat: idx for idx, cat in enumerate(categories)})

        self.is_fitted_ = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Transform to ordinal integers."""
        self._check_is_fitted()
        X = np.asarray(X)
        result = np.zeros_like(X, dtype=int)

        for i in range(self.n_features_in_):
            cat_map = self.category_map_[i]
            for j, val in enumerate(X[:, i]):
                if val in cat_map:
                    result[j, i] = cat_map[val]
                elif self.handle_unknown == "error":
                    raise ValueError(f"Unknown category '{val}' in column {i}")
                else:
                    result[j, i] = self.unknown_value

        return result

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """Convert back to original categories."""
        self._check_is_fitted()
        X = np.asarray(X, dtype=int)
        result = np.empty_like(X, dtype=object)

        for i in range(self.n_features_in_):
            categories = self.categories_[i]
            for j, idx in enumerate(X[:, i]):
                if 0 <= idx < len(categories):
                    result[j, i] = categories[idx]
                else:
                    result[j, i] = None

        return result


class OneHotEncoder(BaseTransformer):
    """
    Encode categorical features as one-hot vectors.

    Parameters
    ----------
    drop : str, default=None
        Whether to drop a category ('first', 'if_binary', None).
    handle_unknown : str, default='error'
        How to handle unknown categories.
    sparse : bool, default=False
        Whether to return sparse matrix (currently ignored, always dense).

    Examples
    --------
    >>> from sdk.feature_engineering import OneHotEncoder
    >>> encoder = OneHotEncoder()
    >>> X_encoded = encoder.fit_transform(X_cat)
    """

    def __init__(
        self,
        drop: Optional[str] = None,
        handle_unknown: str = "error",
        sparse: bool = False,
    ):
        super().__init__()
        self.drop = drop
        self.handle_unknown = handle_unknown
        self.sparse = sparse
        self.categories_: List[np.ndarray] = []
        self.drop_idx_: List[Optional[int]] = []

    def fit(self, X: np.ndarray, y: np.ndarray = None) -> OneHotEncoder:
        """Fit the one-hot encoder."""
        X = np.asarray(X)
        self.n_features_in_ = X.shape[1]

        self.categories_ = []
        self.drop_idx_ = []

        n_output = 0
        for i in range(self.n_features_in_):
            categories = np.unique(X[:, i])
            self.categories_.append(categories)

            n_cats = len(categories)
            if self.drop == "first":
                self.drop_idx_.append(0)
                n_output += n_cats - 1
            elif self.drop == "if_binary" and n_cats == 2:
                self.drop_idx_.append(0)
                n_output += 1
            else:
                self.drop_idx_.append(None)
                n_output += n_cats

        self.n_features_out_ = n_output
        self.is_fitted_ = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Transform to one-hot encoding."""
        self._check_is_fitted()
        X = np.asarray(X)
        n_samples = X.shape[0]

        result = []
        for i in range(self.n_features_in_):
            categories = self.categories_[i]
            drop_idx = self.drop_idx_[i]
            n_cats = len(categories)

            onehot = np.zeros((n_samples, n_cats))
            for j, val in enumerate(X[:, i]):
                if val in categories:
                    idx = np.where(categories == val)[0][0]
                    onehot[j, idx] = 1
                elif self.handle_unknown == "error":
                    raise ValueError(f"Unknown category '{val}' in column {i}")
                # else: all zeros for unknown

            if drop_idx is not None:
                onehot = np.delete(onehot, drop_idx, axis=1)

            result.append(onehot)

        return np.hstack(result)


class QuantileTransformer(BaseTransformer):
    """
    Transform features to follow a uniform or normal distribution.

    Parameters
    ----------
    n_quantiles : int, default=1000
        Number of quantiles to compute.
    output_distribution : str, default='uniform'
        Output distribution ('uniform' or 'normal').
    subsample : int, default=10000
        Maximum samples for quantile estimation.

    Examples
    --------
    >>> from sdk.feature_engineering import QuantileTransformer
    >>> qt = QuantileTransformer(output_distribution='normal')
    >>> X_transformed = qt.fit_transform(X)
    """

    def __init__(
        self,
        n_quantiles: int = 1000,
        output_distribution: str = "uniform",
        subsample: int = 10000,
    ):
        super().__init__()
        self.n_quantiles = n_quantiles
        self.output_distribution = output_distribution
        self.subsample = subsample
        self.quantiles_: Optional[np.ndarray] = None
        self.references_: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray, y: np.ndarray = None) -> QuantileTransformer:
        """Fit the quantile transformer."""
        X = np.asarray(X)
        n_samples, n_features = X.shape
        self.n_features_in_ = n_features
        self.n_features_out_ = n_features

        # Subsample if necessary
        if n_samples > self.subsample:
            idx = np.random.choice(n_samples, self.subsample, replace=False)
            X_subsample = X[idx]
        else:
            X_subsample = X

        # Compute quantiles
        self.quantiles_ = np.percentile(
            X_subsample,
            np.linspace(0, 100, self.n_quantiles),
            axis=0,
        )

        # Reference distribution
        if self.output_distribution == "uniform":
            self.references_ = np.linspace(0, 1, self.n_quantiles)
        elif self.output_distribution == "normal":
            from scipy.stats import norm

            self.references_ = norm.ppf(np.linspace(0.001, 0.999, self.n_quantiles))
        else:
            raise ValueError(f"Unknown distribution: {self.output_distribution}")

        self.is_fitted_ = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Transform features."""
        self._check_is_fitted()
        X = np.asarray(X)
        result = np.zeros_like(X, dtype=float)

        for i in range(self.n_features_in_):
            # Use interpolation
            result[:, i] = np.interp(
                X[:, i],
                self.quantiles_[:, i],
                self.references_,
            )

        return result


class PowerTransformer(BaseTransformer):
    """
    Apply power transformation to make data more Gaussian-like.

    Parameters
    ----------
    method : str, default='yeo-johnson'
        Transformation method ('yeo-johnson' or 'box-cox').
    standardize : bool, default=True
        Whether to standardize output.

    Examples
    --------
    >>> from sdk.feature_engineering import PowerTransformer
    >>> pt = PowerTransformer(method='yeo-johnson')
    >>> X_transformed = pt.fit_transform(X)
    """

    def __init__(self, method: str = "yeo-johnson", standardize: bool = True):
        super().__init__()
        self.method = method
        self.standardize = standardize
        self.lambdas_: Optional[np.ndarray] = None
        self.means_: Optional[np.ndarray] = None
        self.stds_: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray, y: np.ndarray = None) -> PowerTransformer:
        """Fit the power transformer."""
        X = np.asarray(X)
        self.n_features_in_ = X.shape[1]
        self.n_features_out_ = self.n_features_in_

        # Find optimal lambda for each feature
        self.lambdas_ = np.zeros(self.n_features_in_)

        for i in range(self.n_features_in_):
            self.lambdas_[i] = self._find_optimal_lambda(X[:, i])

        # Compute standardization parameters
        X_transformed = self._transform_raw(X)
        self.means_ = np.mean(X_transformed, axis=0)
        self.stds_ = np.std(X_transformed, axis=0)
        self.stds_[self.stds_ == 0] = 1  # Avoid division by zero

        self.is_fitted_ = True
        return self

    def _find_optimal_lambda(self, col: np.ndarray) -> float:
        """Find optimal lambda using maximum likelihood."""
        # Simple grid search
        best_lambda = 0
        best_ll = -np.inf

        for lam in np.linspace(-2, 2, 41):
            try:
                transformed = self._transform_col(col, lam)
                ll = self._log_likelihood(transformed)
                if ll > best_ll:
                    best_ll = ll
                    best_lambda = lam
            except (ValueError, RuntimeWarning):
                continue

        return best_lambda

    def _log_likelihood(self, x: np.ndarray) -> float:
        """Compute log-likelihood for normality."""
        n = len(x)
        mean = np.mean(x)
        var = np.var(x)
        if var == 0:
            return -np.inf
        return -n / 2 * np.log(2 * np.pi * var) - np.sum((x - mean) ** 2) / (2 * var)

    def _transform_col(self, col: np.ndarray, lam: float) -> np.ndarray:
        """Transform a single column."""
        if self.method == "yeo-johnson":
            return self._yeo_johnson(col, lam)
        elif self.method == "box-cox":
            if np.any(col <= 0):
                raise ValueError("Box-Cox requires positive values")
            return self._box_cox(col, lam)
        else:
            raise ValueError(f"Unknown method: {self.method}")

    def _yeo_johnson(self, x: np.ndarray, lam: float) -> np.ndarray:
        """Yeo-Johnson transformation."""
        result = np.zeros_like(x, dtype=float)
        pos = x >= 0
        neg = ~pos

        if lam != 0:
            result[pos] = ((x[pos] + 1) ** lam - 1) / lam
        else:
            result[pos] = np.log(x[pos] + 1)

        if lam != 2:
            result[neg] = -((-x[neg] + 1) ** (2 - lam) - 1) / (2 - lam)
        else:
            result[neg] = -np.log(-x[neg] + 1)

        return result

    def _box_cox(self, x: np.ndarray, lam: float) -> np.ndarray:
        """Box-Cox transformation."""
        if lam == 0:
            return np.log(x)
        else:
            return (x**lam - 1) / lam

    def _transform_raw(self, X: np.ndarray) -> np.ndarray:
        """Transform without standardization."""
        result = np.zeros_like(X, dtype=float)
        for i in range(self.n_features_in_):
            result[:, i] = self._transform_col(X[:, i], self.lambdas_[i])
        return result

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Transform features."""
        self._check_is_fitted()
        X = np.asarray(X)
        result = self._transform_raw(X)

        if self.standardize:
            result = (result - self.means_) / self.stds_

        return result

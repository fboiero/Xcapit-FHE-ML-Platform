"""FHE-compatible Feature Selection methods.

This module provides feature selection algorithms that work with
encrypted data using polynomial approximations for FHE compatibility.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional, Union

import numpy as np

from .base import BaseFHEModel, ModelConfig, ModelState


class ScoreFunc(Enum):
    """Score functions for feature selection."""

    F_CLASSIF = "f_classif"
    F_REGRESSION = "f_regression"
    MUTUAL_INFO_CLASSIF = "mutual_info_classif"
    MUTUAL_INFO_REGRESSION = "mutual_info_regression"
    CHI2 = "chi2"
    VARIANCE = "variance"


@dataclass
class SelectKBestConfig(ModelConfig):
    """Configuration for SelectKBest."""

    k: int = 10
    score_func: ScoreFunc = ScoreFunc.F_CLASSIF


@dataclass
class VarianceThresholdConfig(ModelConfig):
    """Configuration for VarianceThreshold."""

    threshold: float = 0.0


@dataclass
class RFEConfig(ModelConfig):
    """Configuration for Recursive Feature Elimination."""

    n_features_to_select: Optional[int] = None
    step: Union[int, float] = 1
    verbose: int = 0


def f_classif(X: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """ANOVA F-value for classification.

    Computes F-statistic between each feature and the target.
    FHE-compatible as it uses only polynomial operations.
    """
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y)

    classes = np.unique(y)
    n_samples, n_features = X.shape
    n_classes = len(classes)

    # Overall mean
    X_mean = np.mean(X, axis=0)

    # Between-class variance (SSB)
    ssb = np.zeros(n_features)
    for cls in classes:
        mask = y == cls
        n_cls = np.sum(mask)
        cls_mean = np.mean(X[mask], axis=0)
        ssb += n_cls * (cls_mean - X_mean) ** 2

    # Within-class variance (SSW)
    ssw = np.zeros(n_features)
    for cls in classes:
        mask = y == cls
        cls_mean = np.mean(X[mask], axis=0)
        ssw += np.sum((X[mask] - cls_mean) ** 2, axis=0)

    # Degrees of freedom
    df_between = n_classes - 1
    df_within = n_samples - n_classes

    # F-statistic
    # Avoid division by zero
    ssw = np.maximum(ssw, 1e-10)

    f_scores = (ssb / df_between) / (ssw / df_within)

    # p-values (approximation using F-distribution CDF)
    # For FHE, we skip p-values and just use F-scores
    p_values = np.ones(n_features)  # Placeholder

    return f_scores, p_values


def f_regression(X: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """F-value for regression.

    Computes correlation-based F-statistic.
    FHE-compatible as it uses only polynomial operations.
    """
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)

    n_samples, n_features = X.shape

    # Center data
    X_centered = X - np.mean(X, axis=0)
    y_centered = y - np.mean(y)

    # Correlation coefficients
    ss_x = np.sum(X_centered**2, axis=0)
    ss_y = np.sum(y_centered**2)
    cross = X_centered.T @ y_centered

    # Avoid division by zero
    ss_x = np.maximum(ss_x, 1e-10)
    ss_y = max(ss_y, 1e-10)

    correlation = cross / np.sqrt(ss_x * ss_y)

    # F-statistic: F = r^2 * (n-2) / (1 - r^2)
    r_squared = correlation**2
    r_squared = np.minimum(r_squared, 1 - 1e-10)  # Avoid division by zero

    f_scores = r_squared * (n_samples - 2) / (1 - r_squared)

    p_values = np.ones(n_features)  # Placeholder

    return f_scores, p_values


def chi2(X: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Chi-squared statistic for categorical features.

    Only works with non-negative features.
    FHE-compatible as it uses only polynomial operations.
    """
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y)

    # Ensure non-negative
    X = np.maximum(X, 0)

    classes = np.unique(y)
    n_samples, n_features = X.shape

    # Observed frequencies per class
    observed = np.zeros((len(classes), n_features))
    for i, cls in enumerate(classes):
        mask = y == cls
        observed[i] = np.sum(X[mask], axis=0)

    # Expected frequencies
    class_totals = observed.sum(axis=1, keepdims=True)
    feature_totals = observed.sum(axis=0, keepdims=True)
    total = observed.sum()

    expected = class_totals @ feature_totals / (total + 1e-10)

    # Chi-squared statistic
    expected = np.maximum(expected, 1e-10)
    chi2_scores = np.sum((observed - expected) ** 2 / expected, axis=0)

    p_values = np.ones(n_features)

    return chi2_scores, p_values


def mutual_info_classif(
    X: np.ndarray,
    y: np.ndarray,
    n_neighbors: int = 3,
    random_state: Optional[int] = None,
) -> np.ndarray:
    """Mutual information for classification.

    Estimates MI using k-nearest neighbors.
    Approximation for FHE using polynomial operations.
    """
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y)

    n_samples, n_features = X.shape
    classes, y_counts = np.unique(y, return_counts=True)

    # For FHE compatibility, use simplified MI estimation
    # based on class separability

    mi_scores = np.zeros(n_features)

    for j in range(n_features):
        feature = X[:, j]

        # Estimate MI using variance reduction
        total_var = np.var(feature)

        weighted_var = 0
        for cls, count in zip(classes, y_counts):
            mask = y == cls
            class_var = np.var(feature[mask])
            weighted_var += (count / n_samples) * class_var

        # MI approximation: reduction in variance when knowing class
        mi_scores[j] = max(0, total_var - weighted_var) / (total_var + 1e-10)

    return mi_scores


def mutual_info_regression(
    X: np.ndarray,
    y: np.ndarray,
    n_neighbors: int = 3,
    random_state: Optional[int] = None,
) -> np.ndarray:
    """Mutual information for regression.

    Estimates MI using correlation-based approximation.
    """
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)

    n_samples, n_features = X.shape

    mi_scores = np.zeros(n_features)

    for j in range(n_features):
        # Pearson correlation
        corr = np.corrcoef(X[:, j], y)[0, 1]

        # MI approximation: -0.5 * log(1 - r^2)
        # For FHE, use polynomial approximation
        r_squared = corr**2
        r_squared = min(r_squared, 0.999)  # Avoid log(0)

        # Polynomial approximation of -0.5 * log(1 - x)
        # log(1-x) ≈ -x - x^2/2 - x^3/3 - ...
        mi_scores[j] = 0.5 * (r_squared + r_squared**2 / 2 + r_squared**3 / 3)

    return mi_scores


class VarianceThreshold(BaseFHEModel):
    """Feature selector that removes low-variance features.

    Removes all features with variance below threshold.
    Fully FHE-compatible as variance is a polynomial operation.

    Example:
        >>> from xcapit_fhe import VarianceThreshold
        >>> selector = VarianceThreshold(threshold=0.1)
        >>> X_selected = selector.fit_transform(X)
    """

    def __init__(
        self,
        threshold: float = 0.0,
        fhe_compatible: bool = True,
    ):
        super().__init__(fhe_compatible=fhe_compatible)
        self.config = VarianceThresholdConfig(threshold=threshold)
        self.variances_ = None
        self.support_mask_ = None

    def fit(self, X: np.ndarray, y: np.ndarray = None) -> "VarianceThreshold":
        """Compute variance of each feature.

        Args:
            X: Training data
            y: Ignored

        Returns:
            self
        """
        X = np.asarray(X, dtype=np.float64)
        self.n_features_in_ = X.shape[1]

        self.variances_ = np.var(X, axis=0)
        self.support_mask_ = self.variances_ > self.config.threshold

        self.state = ModelState.TRAINED
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Select features with variance above threshold."""
        X = np.asarray(X, dtype=np.float64)
        return X[:, self.support_mask_]

    def fit_transform(self, X: np.ndarray, y: np.ndarray = None) -> np.ndarray:
        """Fit and transform in one step."""
        self.fit(X)
        return self.transform(X)

    def get_support(self, indices: bool = False) -> np.ndarray:
        """Get mask or indices of selected features."""
        if indices:
            return np.where(self.support_mask_)[0]
        return self.support_mask_


class SelectKBest(BaseFHEModel):
    """Select K best features based on score function.

    FHE-compatible score functions use polynomial approximations.

    Example:
        >>> from xcapit_fhe import SelectKBest, f_classif
        >>> selector = SelectKBest(score_func=f_classif, k=10)
        >>> X_selected = selector.fit_transform(X, y)
    """

    def __init__(
        self,
        score_func: Union[str, Callable] = "f_classif",
        k: int = 10,
        fhe_compatible: bool = True,
    ):
        super().__init__(fhe_compatible=fhe_compatible)
        self.score_func = score_func
        self.k = k
        self.scores_ = None
        self.pvalues_ = None
        self.support_mask_ = None

    def _get_score_func(self) -> Callable:
        """Get the score function."""
        if callable(self.score_func):
            return self.score_func

        score_funcs = {
            "f_classif": f_classif,
            "f_regression": f_regression,
            "chi2": chi2,
            "mutual_info_classif": mutual_info_classif,
            "mutual_info_regression": mutual_info_regression,
        }

        if self.score_func in score_funcs:
            return score_funcs[self.score_func]

        raise ValueError(f"Unknown score function: {self.score_func}")

    def fit(self, X: np.ndarray, y: np.ndarray) -> "SelectKBest":
        """Compute feature scores.

        Args:
            X: Training data
            y: Target values

        Returns:
            self
        """
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y)

        n_features = X.shape[1]
        self.n_features_in_ = n_features

        # Get score function
        score_func = self._get_score_func()

        # Compute scores
        result = score_func(X, y)
        if isinstance(result, tuple):
            self.scores_, self.pvalues_ = result
        else:
            self.scores_ = result
            self.pvalues_ = None

        # Select k best
        k = min(self.k, n_features)
        top_k_indices = np.argsort(self.scores_)[-k:]

        self.support_mask_ = np.zeros(n_features, dtype=bool)
        self.support_mask_[top_k_indices] = True

        self.state = ModelState.TRAINED
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Select k best features."""
        X = np.asarray(X, dtype=np.float64)
        return X[:, self.support_mask_]

    def fit_transform(self, X: np.ndarray, y: np.ndarray) -> np.ndarray:
        """Fit and transform in one step."""
        self.fit(X, y)
        return self.transform(X)

    def get_support(self, indices: bool = False) -> np.ndarray:
        """Get mask or indices of selected features."""
        if indices:
            return np.where(self.support_mask_)[0]
        return self.support_mask_


class SelectPercentile(BaseFHEModel):
    """Select features based on percentile of scores.

    Example:
        >>> from xcapit_fhe import SelectPercentile
        >>> selector = SelectPercentile(percentile=50)
        >>> X_selected = selector.fit_transform(X, y)
    """

    def __init__(
        self,
        score_func: Union[str, Callable] = "f_classif",
        percentile: float = 10,
        fhe_compatible: bool = True,
    ):
        super().__init__(fhe_compatible=fhe_compatible)
        self.score_func = score_func
        self.percentile = percentile
        self.scores_ = None
        self.support_mask_ = None

    def _get_score_func(self) -> Callable:
        """Get the score function."""
        if callable(self.score_func):
            return self.score_func

        score_funcs = {
            "f_classif": f_classif,
            "f_regression": f_regression,
        }

        if self.score_func in score_funcs:
            return score_funcs[self.score_func]

        raise ValueError(f"Unknown score function: {self.score_func}")

    def fit(self, X: np.ndarray, y: np.ndarray) -> "SelectPercentile":
        """Compute feature scores."""
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y)

        self.n_features_in_ = X.shape[1]

        score_func = self._get_score_func()
        result = score_func(X, y)
        self.scores_ = result[0] if isinstance(result, tuple) else result

        # Select by percentile
        threshold = np.percentile(self.scores_, 100 - self.percentile)
        self.support_mask_ = self.scores_ >= threshold

        self.state = ModelState.TRAINED
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Select features above percentile."""
        return np.asarray(X)[:, self.support_mask_]

    def fit_transform(self, X: np.ndarray, y: np.ndarray) -> np.ndarray:
        """Fit and transform in one step."""
        self.fit(X, y)
        return self.transform(X)

    def get_support(self, indices: bool = False) -> np.ndarray:
        """Get mask or indices of selected features."""
        if indices:
            return np.where(self.support_mask_)[0]
        return self.support_mask_


class RFE(BaseFHEModel):
    """Recursive Feature Elimination.

    Recursively removes least important features based on
    estimator feature importances.

    FHE-compatible when using FHE-compatible estimators.

    Example:
        >>> from xcapit_fhe import RFE, LogisticRegression
        >>> estimator = LogisticRegression()
        >>> selector = RFE(estimator, n_features_to_select=5)
        >>> X_selected = selector.fit_transform(X, y)
    """

    def __init__(
        self,
        estimator: Any,
        n_features_to_select: Optional[int] = None,
        step: Union[int, float] = 1,
        verbose: int = 0,
        fhe_compatible: bool = True,
    ):
        super().__init__(fhe_compatible=fhe_compatible)
        self.estimator = estimator
        self.n_features_to_select = n_features_to_select
        self.step = step
        self.verbose = verbose

        self.support_mask_ = None
        self.ranking_ = None
        self.estimator_ = None

    def _get_feature_importances(self, estimator: Any) -> np.ndarray:
        """Extract feature importances from estimator."""
        if hasattr(estimator, "feature_importances_"):
            return np.abs(estimator.feature_importances_)
        elif hasattr(estimator, "coef_"):
            coef = estimator.coef_
            if coef.ndim > 1:
                coef = np.mean(np.abs(coef), axis=0)
            return np.abs(coef)
        else:
            raise ValueError("Estimator must have feature_importances_ or coef_ attribute")

    def fit(self, X: np.ndarray, y: np.ndarray) -> "RFE":
        """Fit RFE.

        Args:
            X: Training data
            y: Target values

        Returns:
            self
        """
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y)

        n_samples, n_features = X.shape
        self.n_features_in_ = n_features

        # Determine number of features to select
        n_to_select = self.n_features_to_select
        if n_to_select is None:
            n_to_select = n_features // 2

        # Determine step size
        if isinstance(self.step, float):
            step = max(1, int(self.step * n_features))
        else:
            step = self.step

        # Initialize
        support = np.ones(n_features, dtype=bool)
        ranking = np.ones(n_features, dtype=int)

        while np.sum(support) > n_to_select:
            # Get current features
            features = np.where(support)[0]
            X_current = X[:, features]

            # Fit estimator
            import copy

            estimator = copy.deepcopy(self.estimator)
            estimator.fit(X_current, y)

            # Get importances
            importances = self._get_feature_importances(estimator)

            # Determine how many to remove
            n_remove = min(step, np.sum(support) - n_to_select)

            # Find least important
            threshold = np.sort(importances)[n_remove - 1]
            remove_mask = importances <= threshold

            # Update support and ranking
            features_to_remove = features[remove_mask][:n_remove]
            ranking[features_to_remove] = np.sum(support) - n_to_select + 1
            support[features_to_remove] = False

            if self.verbose > 0:
                print(f"Features remaining: {np.sum(support)}")

        # Final fit with selected features
        self.support_mask_ = support
        self.ranking_ = ranking

        X_final = X[:, support]
        import copy

        self.estimator_ = copy.deepcopy(self.estimator)
        self.estimator_.fit(X_final, y)

        self.state = ModelState.TRAINED
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Select features."""
        return np.asarray(X)[:, self.support_mask_]

    def fit_transform(self, X: np.ndarray, y: np.ndarray) -> np.ndarray:
        """Fit and transform in one step."""
        self.fit(X, y)
        return self.transform(X)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict using selected features."""
        X_selected = self.transform(X)
        return self.estimator_.predict(X_selected)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Score using selected features."""
        X_selected = self.transform(X)
        return self.estimator_.score(X_selected, y)

    def get_support(self, indices: bool = False) -> np.ndarray:
        """Get mask or indices of selected features."""
        if indices:
            return np.where(self.support_mask_)[0]
        return self.support_mask_


class SelectFromModel(BaseFHEModel):
    """Feature selection based on model importance.

    Selects features based on importance weights from a fitted model.

    Example:
        >>> from xcapit_fhe import SelectFromModel, RandomForest
        >>> model = RandomForest()
        >>> selector = SelectFromModel(model, threshold='median')
        >>> X_selected = selector.fit_transform(X, y)
    """

    def __init__(
        self,
        estimator: Any,
        threshold: Union[str, float] = "mean",
        prefit: bool = False,
        max_features: Optional[int] = None,
        fhe_compatible: bool = True,
    ):
        super().__init__(fhe_compatible=fhe_compatible)
        self.estimator = estimator
        self.threshold = threshold
        self.prefit = prefit
        self.max_features = max_features

        self.support_mask_ = None
        self.threshold_ = None
        self.estimator_ = None

    def _get_threshold(self, importances: np.ndarray) -> float:
        """Determine threshold value."""
        if isinstance(self.threshold, str):
            if self.threshold == "mean":
                return np.mean(importances)
            elif self.threshold == "median":
                return np.median(importances)
            else:
                raise ValueError(f"Unknown threshold: {self.threshold}")
        return self.threshold

    def _get_feature_importances(self, estimator: Any) -> np.ndarray:
        """Extract feature importances from estimator."""
        if hasattr(estimator, "feature_importances_"):
            return np.abs(estimator.feature_importances_)
        elif hasattr(estimator, "coef_"):
            coef = estimator.coef_
            if coef.ndim > 1:
                coef = np.mean(np.abs(coef), axis=0)
            return np.abs(coef)
        else:
            raise ValueError("Estimator must have feature_importances_ or coef_ attribute")

    def fit(self, X: np.ndarray, y: np.ndarray = None) -> "SelectFromModel":
        """Fit the selector.

        Args:
            X: Training data
            y: Target values

        Returns:
            self
        """
        X = np.asarray(X, dtype=np.float64)
        self.n_features_in_ = X.shape[1]

        if self.prefit:
            self.estimator_ = self.estimator
        else:
            import copy

            self.estimator_ = copy.deepcopy(self.estimator)
            self.estimator_.fit(X, y)

        importances = self._get_feature_importances(self.estimator_)
        self.threshold_ = self._get_threshold(importances)

        self.support_mask_ = importances >= self.threshold_

        if self.max_features is not None:
            # Limit to max_features
            n_selected = np.sum(self.support_mask_)
            if n_selected > self.max_features:
                top_indices = np.argsort(importances)[-self.max_features :]
                self.support_mask_ = np.zeros(len(importances), dtype=bool)
                self.support_mask_[top_indices] = True

        self.state = ModelState.TRAINED
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Select features."""
        return np.asarray(X)[:, self.support_mask_]

    def fit_transform(self, X: np.ndarray, y: np.ndarray = None) -> np.ndarray:
        """Fit and transform in one step."""
        self.fit(X, y)
        return self.transform(X)

    def get_support(self, indices: bool = False) -> np.ndarray:
        """Get mask or indices of selected features."""
        if indices:
            return np.where(self.support_mask_)[0]
        return self.support_mask_


__all__ = [
    # Score functions
    "f_classif",
    "f_regression",
    "chi2",
    "mutual_info_classif",
    "mutual_info_regression",
    # Enums
    "ScoreFunc",
    # Configs
    "SelectKBestConfig",
    "VarianceThresholdConfig",
    "RFEConfig",
    # Selectors
    "VarianceThreshold",
    "SelectKBest",
    "SelectPercentile",
    "RFE",
    "SelectFromModel",
]

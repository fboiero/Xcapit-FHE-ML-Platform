"""
Feature Selection module for FHE-ML Platform.

Provides feature selection algorithms compatible with encrypted data,
following scikit-learn's API patterns.
"""

from __future__ import annotations

from typing import Any, Callable, List, Optional, Tuple, Union

import numpy as np


class SelectorMixin:
    """Mixin class for feature selectors."""

    def get_support(self, indices: bool = False) -> np.ndarray:
        """
        Get a mask, or integer index, of the features selected.

        Args:
            indices: If True, return indices instead of boolean mask

        Returns:
            Support mask or indices
        """
        mask = self._get_support_mask()
        if indices:
            return np.where(mask)[0]
        return mask

    def _get_support_mask(self) -> np.ndarray:
        """Get the boolean mask for selected features."""
        raise NotImplementedError

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Reduce X to the selected features.

        Args:
            X: Input data of shape (n_samples, n_features)

        Returns:
            Reduced data of shape (n_samples, n_selected_features)
        """
        X = np.asarray(X)
        mask = self.get_support()
        if not mask.any():
            raise ValueError("No features were selected.")
        return X[:, mask]

    def fit_transform(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> np.ndarray:
        """Fit and transform in one step."""
        return self.fit(X, y).transform(X)

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """
        Reverse the transformation operation.

        Args:
            X: Transformed data of shape (n_samples, n_selected_features)

        Returns:
            Data with original feature dimensions (missing features as zeros)
        """
        X = np.asarray(X)
        support = self.get_support()
        n_features = support.shape[0]

        if X.ndim == 1:
            X = X.reshape(1, -1)

        X_inv = np.zeros((X.shape[0], n_features), dtype=X.dtype)
        X_inv[:, support] = X
        return X_inv


class VarianceThreshold(SelectorMixin):
    """
    Feature selector that removes low-variance features.

    Features with variance below threshold are removed. This is useful
    for removing constant or near-constant features.

    Args:
        threshold: Minimum variance required for a feature to be kept.
            Default is 0 (remove only constant features).

    Example:
        >>> selector = VarianceThreshold(threshold=0.1)
        >>> X = np.array([[0, 0, 1], [0, 1, 0], [1, 0, 0], [0, 1, 1]])
        >>> selector.fit_transform(X)
    """

    def __init__(self, threshold: float = 0.0):
        self.threshold = threshold
        self.variances_: Optional[np.ndarray] = None
        self._support_mask: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> "VarianceThreshold":
        """
        Learn empirical variances from X.

        Args:
            X: Training data of shape (n_samples, n_features)
            y: Ignored, present for API compatibility

        Returns:
            self
        """
        X = np.asarray(X)
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        self.variances_ = np.var(X, axis=0)
        self._support_mask = self.variances_ > self.threshold
        return self

    def _get_support_mask(self) -> np.ndarray:
        return self._support_mask


def _f_classif(X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute F-statistic and p-values for classification.

    ANOVA F-value between label/feature for classification tasks.
    """
    classes = np.unique(y)
    n_classes = len(classes)
    n_samples, n_features = X.shape

    # Calculate class means
    class_means = np.zeros((n_classes, n_features))
    class_counts = np.zeros(n_classes)
    for i, c in enumerate(classes):
        mask = y == c
        class_means[i] = X[mask].mean(axis=0)
        class_counts[i] = mask.sum()

    # Overall mean
    overall_mean = X.mean(axis=0)

    # Between-class sum of squares
    ss_between = np.sum(
        class_counts[:, np.newaxis] * (class_means - overall_mean) ** 2,
        axis=0
    )

    # Within-class sum of squares
    ss_within = np.zeros(n_features)
    for i, c in enumerate(classes):
        mask = y == c
        ss_within += np.sum((X[mask] - class_means[i]) ** 2, axis=0)

    # Degrees of freedom
    df_between = n_classes - 1
    df_within = n_samples - n_classes

    # F-statistic
    ms_between = ss_between / df_between
    ms_within = ss_within / df_within

    # Avoid division by zero
    ms_within = np.where(ms_within == 0, 1e-10, ms_within)
    f_statistic = ms_between / ms_within

    # Approximate p-values (simplified)
    # In practice, use scipy.stats.f.sf for exact p-values
    p_values = 1.0 / (1.0 + f_statistic)

    return f_statistic, p_values


def _f_regression(X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute F-statistic and p-values for regression.

    Univariate linear regression tests for each feature.
    """
    n_samples, n_features = X.shape

    # Center X and y
    X_centered = X - X.mean(axis=0)
    y_centered = y - y.mean()

    # Correlation coefficient
    ss_xy = np.sum(X_centered * y_centered[:, np.newaxis], axis=0)
    ss_xx = np.sum(X_centered ** 2, axis=0)
    ss_yy = np.sum(y_centered ** 2)

    # Avoid division by zero
    ss_xx = np.where(ss_xx == 0, 1e-10, ss_xx)

    # Correlation
    correlation = ss_xy / np.sqrt(ss_xx * ss_yy)

    # F-statistic from correlation
    df = n_samples - 2
    f_statistic = (correlation ** 2 * df) / (1 - correlation ** 2 + 1e-10)

    # Approximate p-values
    p_values = 1.0 / (1.0 + f_statistic)

    return f_statistic, p_values


def _mutual_info_classif(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """
    Estimate mutual information for classification.

    Simplified implementation using histogram-based estimation.
    """
    n_samples, n_features = X.shape
    mi = np.zeros(n_features)

    classes, class_counts = np.unique(y, return_counts=True)
    class_probs = class_counts / n_samples

    for i in range(n_features):
        feature = X[:, i]

        # Discretize continuous feature
        n_bins = min(10, len(np.unique(feature)))
        bins = np.linspace(feature.min(), feature.max() + 1e-10, n_bins + 1)
        digitized = np.digitize(feature, bins) - 1

        # Joint and marginal probabilities
        for c_idx, c in enumerate(classes):
            mask = y == c
            feature_class = digitized[mask]

            for b in range(n_bins):
                # P(feature=b, class=c)
                p_joint = np.sum((digitized == b) & (y == c)) / n_samples
                # P(feature=b)
                p_feature = np.sum(digitized == b) / n_samples
                # P(class=c)
                p_class = class_probs[c_idx]

                if p_joint > 0 and p_feature > 0 and p_class > 0:
                    mi[i] += p_joint * np.log(p_joint / (p_feature * p_class) + 1e-10)

    return np.maximum(mi, 0)


# Score functions mapping
SCORE_FUNCTIONS = {
    "f_classif": _f_classif,
    "f_regression": _f_regression,
    "mutual_info_classif": _mutual_info_classif,
}


class SelectKBest(SelectorMixin):
    """
    Select features according to the k highest scores.

    Args:
        score_func: Function taking (X, y) and returning (scores, pvalues)
            or just scores. Can be string name or callable.
        k: Number of top features to select. Use "all" for all features.

    Example:
        >>> selector = SelectKBest(score_func="f_classif", k=2)
        >>> X = np.random.randn(100, 10)
        >>> y = np.random.randint(0, 2, 100)
        >>> X_new = selector.fit_transform(X, y)
    """

    def __init__(
        self,
        score_func: Union[str, Callable] = "f_classif",
        k: Union[int, str] = 10,
    ):
        if isinstance(score_func, str):
            if score_func not in SCORE_FUNCTIONS:
                raise ValueError(f"Unknown score function: {score_func}")
            score_func = SCORE_FUNCTIONS[score_func]
        self.score_func = score_func
        self.k = k
        self.scores_: Optional[np.ndarray] = None
        self.pvalues_: Optional[np.ndarray] = None
        self._support_mask: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> "SelectKBest":
        """
        Run the score function on (X, y) and get appropriate features.

        Args:
            X: Training data of shape (n_samples, n_features)
            y: Target values

        Returns:
            self
        """
        X = np.asarray(X)
        y = np.asarray(y)

        if X.ndim == 1:
            X = X.reshape(-1, 1)

        n_features = X.shape[1]

        # Calculate scores
        result = self.score_func(X, y)
        if isinstance(result, tuple):
            self.scores_, self.pvalues_ = result
        else:
            self.scores_ = result
            self.pvalues_ = None

        # Determine k
        if self.k == "all":
            k = n_features
        else:
            k = min(self.k, n_features)

        # Select top k
        if k == n_features:
            self._support_mask = np.ones(n_features, dtype=bool)
        else:
            top_indices = np.argsort(self.scores_)[-k:]
            self._support_mask = np.zeros(n_features, dtype=bool)
            self._support_mask[top_indices] = True

        return self

    def _get_support_mask(self) -> np.ndarray:
        return self._support_mask


class SelectPercentile(SelectorMixin):
    """
    Select features according to a percentile of the highest scores.

    Args:
        score_func: Function taking (X, y) and returning scores
        percentile: Percent of features to keep (0-100)

    Example:
        >>> selector = SelectPercentile(score_func="f_classif", percentile=50)
        >>> X_new = selector.fit_transform(X, y)
    """

    def __init__(
        self,
        score_func: Union[str, Callable] = "f_classif",
        percentile: float = 10,
    ):
        if isinstance(score_func, str):
            if score_func not in SCORE_FUNCTIONS:
                raise ValueError(f"Unknown score function: {score_func}")
            score_func = SCORE_FUNCTIONS[score_func]
        self.score_func = score_func
        self.percentile = percentile
        self.scores_: Optional[np.ndarray] = None
        self.pvalues_: Optional[np.ndarray] = None
        self._support_mask: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> "SelectPercentile":
        """
        Run the score function on (X, y) and get features above percentile.

        Args:
            X: Training data
            y: Target values

        Returns:
            self
        """
        X = np.asarray(X)
        y = np.asarray(y)

        if X.ndim == 1:
            X = X.reshape(-1, 1)

        n_features = X.shape[1]

        # Calculate scores
        result = self.score_func(X, y)
        if isinstance(result, tuple):
            self.scores_, self.pvalues_ = result
        else:
            self.scores_ = result
            self.pvalues_ = None

        # Calculate threshold
        threshold = np.percentile(self.scores_, 100 - self.percentile)
        self._support_mask = self.scores_ >= threshold

        return self

    def _get_support_mask(self) -> np.ndarray:
        return self._support_mask


class SelectFromModel(SelectorMixin):
    """
    Feature selector based on importance weights from an estimator.

    Args:
        estimator: An estimator with feature_importances_ or coef_ attribute
        threshold: Threshold for feature selection. Features with importance
            greater than threshold are selected. Can be "mean", "median",
            or a numeric value.
        prefit: If True, use a prefit model (don't call fit)
        max_features: Maximum number of features to select

    Example:
        >>> from sdk.models import RandomForestClassifier
        >>> clf = RandomForestClassifier()
        >>> selector = SelectFromModel(clf, threshold="mean")
        >>> X_new = selector.fit_transform(X, y)
    """

    def __init__(
        self,
        estimator: Any,
        threshold: Union[str, float] = "mean",
        prefit: bool = False,
        max_features: Optional[int] = None,
    ):
        self.estimator = estimator
        self.threshold = threshold
        self.prefit = prefit
        self.max_features = max_features
        self.estimator_: Optional[Any] = None
        self._support_mask: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> "SelectFromModel":
        """
        Fit the model and determine feature importances.

        Args:
            X: Training data
            y: Target values

        Returns:
            self
        """
        X = np.asarray(X)
        y = np.asarray(y)

        if self.prefit:
            self.estimator_ = self.estimator
        else:
            self.estimator_ = self.estimator
            self.estimator_.fit(X, y)

        # Get feature importances
        importances = self._get_feature_importances()
        n_features = len(importances)

        # Determine threshold
        if self.threshold == "mean":
            threshold = np.mean(importances)
        elif self.threshold == "median":
            threshold = np.median(importances)
        else:
            threshold = self.threshold

        # Create mask
        mask = importances >= threshold

        # Apply max_features constraint
        if self.max_features is not None and mask.sum() > self.max_features:
            top_indices = np.argsort(importances)[-self.max_features:]
            mask = np.zeros(n_features, dtype=bool)
            mask[top_indices] = True

        self._support_mask = mask
        return self

    def _get_feature_importances(self) -> np.ndarray:
        """Get feature importances from the estimator."""
        if hasattr(self.estimator_, "feature_importances_"):
            return np.asarray(self.estimator_.feature_importances_)
        elif hasattr(self.estimator_, "coef_"):
            coef = np.asarray(self.estimator_.coef_)
            if coef.ndim > 1:
                coef = np.mean(np.abs(coef), axis=0)
            return np.abs(coef)
        else:
            raise ValueError(
                "Estimator must have feature_importances_ or coef_ attribute"
            )

    def _get_support_mask(self) -> np.ndarray:
        return self._support_mask


class RFE(SelectorMixin):
    """
    Recursive Feature Elimination.

    Selects features by recursively considering smaller and smaller
    sets of features. First, the estimator is trained on the initial
    set of features and the importance of each feature is obtained.
    Then, the least important features are pruned from current set
    of features. This is repeated until the desired number of features
    to select is eventually reached.

    Args:
        estimator: A supervised learning estimator with a fit method that
            provides feature_importances_ or coef_ attribute.
        n_features_to_select: Number of features to select. If None,
            half of the features are selected.
        step: If greater than or equal to 1, the number of features to
            remove at each iteration. If between 0 and 1, the percentage
            of features to remove.

    Example:
        >>> from sdk.models import LinearRegression
        >>> rfe = RFE(LinearRegression(), n_features_to_select=5)
        >>> X_new = rfe.fit_transform(X, y)
    """

    def __init__(
        self,
        estimator: Any,
        n_features_to_select: Optional[int] = None,
        step: Union[int, float] = 1,
    ):
        self.estimator = estimator
        self.n_features_to_select = n_features_to_select
        self.step = step
        self.estimator_: Optional[Any] = None
        self.n_features_: Optional[int] = None
        self.support_: Optional[np.ndarray] = None
        self.ranking_: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> "RFE":
        """
        Fit the RFE model and determine the optimal number of features.

        Args:
            X: Training data of shape (n_samples, n_features)
            y: Target values

        Returns:
            self
        """
        X = np.asarray(X)
        y = np.asarray(y)

        n_features = X.shape[1]

        # Determine n_features_to_select
        if self.n_features_to_select is None:
            n_features_to_select = n_features // 2
        else:
            n_features_to_select = self.n_features_to_select

        # Determine step
        if 0.0 < self.step < 1.0:
            step = max(1, int(n_features * self.step))
        else:
            step = int(self.step)

        # Initialize support and ranking
        support = np.ones(n_features, dtype=bool)
        ranking = np.ones(n_features, dtype=int)

        # Iterate until we have the desired number of features
        while np.sum(support) > n_features_to_select:
            # Remaining features
            features = np.where(support)[0]

            # Fit estimator on selected features
            self.estimator.fit(X[:, features], y)

            # Get feature importances
            if hasattr(self.estimator, "feature_importances_"):
                importances = np.asarray(self.estimator.feature_importances_)
            elif hasattr(self.estimator, "coef_"):
                coef = np.asarray(self.estimator.coef_)
                if coef.ndim > 1:
                    coef = np.mean(np.abs(coef), axis=0)
                importances = np.abs(coef)
            else:
                raise ValueError(
                    "Estimator must have feature_importances_ or coef_"
                )

            # Determine features to remove
            n_to_remove = min(step, np.sum(support) - n_features_to_select)
            remove_indices = np.argsort(importances)[:n_to_remove]

            # Update support and ranking
            support[features[remove_indices]] = False
            ranking[features[remove_indices]] = np.sum(~support)

        # Final fit on selected features
        features = np.where(support)[0]
        self.estimator.fit(X[:, features], y)
        self.estimator_ = self.estimator

        self.n_features_ = n_features_to_select
        self.support_ = support
        self.ranking_ = ranking

        return self

    def _get_support_mask(self) -> np.ndarray:
        return self.support_

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict using the selected features."""
        return self.estimator_.predict(self.transform(X))

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Score using the selected features."""
        return self.estimator_.score(self.transform(X), y)


class RFECV(RFE):
    """
    Recursive Feature Elimination with Cross-Validation.

    Selects the best number of features by cross-validation.

    Args:
        estimator: Estimator with fit and feature_importances_/coef_
        step: Features to remove at each iteration
        min_features_to_select: Minimum number of features
        cv: Number of cross-validation folds
        scoring: Scoring function (callable or None for estimator's score)

    Example:
        >>> rfecv = RFECV(estimator, step=1, cv=5)
        >>> X_new = rfecv.fit_transform(X, y)
    """

    def __init__(
        self,
        estimator: Any,
        step: Union[int, float] = 1,
        min_features_to_select: int = 1,
        cv: int = 5,
        scoring: Optional[Callable] = None,
    ):
        super().__init__(estimator, n_features_to_select=None, step=step)
        self.min_features_to_select = min_features_to_select
        self.cv = cv
        self.scoring = scoring
        self.cv_results_: Optional[dict] = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> "RFECV":
        """
        Fit the RFECV model with cross-validation.

        Args:
            X: Training data
            y: Target values

        Returns:
            self
        """
        from .model_selection import cross_val_score

        X = np.asarray(X)
        y = np.asarray(y)

        n_features = X.shape[1]

        # Determine step
        if 0.0 < self.step < 1.0:
            step = max(1, int(n_features * self.step))
        else:
            step = int(self.step)

        # Track scores for each number of features
        n_features_list = list(range(self.min_features_to_select, n_features + 1, step))
        if n_features not in n_features_list:
            n_features_list.append(n_features)
        n_features_list = sorted(n_features_list, reverse=True)

        scores = []
        support = np.ones(n_features, dtype=bool)
        ranking = np.ones(n_features, dtype=int)

        for n_feat in n_features_list:
            # Set target number and run RFE
            self.n_features_to_select = n_feat
            super().fit(X, y)

            # Cross-validate
            features = self.get_support(indices=True)
            X_selected = X[:, features]
            cv_scores = cross_val_score(
                self.estimator, X_selected, y,
                cv=self.cv, scoring=self.scoring
            )
            scores.append(cv_scores.mean())

            support = self.support_.copy()
            ranking = self.ranking_.copy()

        # Find best number of features
        best_idx = np.argmax(scores)
        best_n_features = n_features_list[best_idx]

        # Final fit with best number
        self.n_features_to_select = best_n_features
        super().fit(X, y)

        self.cv_results_ = {
            "n_features": n_features_list,
            "mean_test_score": scores,
        }

        return self


# Convenience functions
def f_classif(X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """ANOVA F-value for classification."""
    return _f_classif(X, y)


def f_regression(X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """F-value for regression."""
    return _f_regression(X, y)


def mutual_info_classif(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Mutual information for classification."""
    return _mutual_info_classif(X, y)


__all__ = [
    "VarianceThreshold",
    "SelectKBest",
    "SelectPercentile",
    "SelectFromModel",
    "RFE",
    "RFECV",
    "f_classif",
    "f_regression",
    "mutual_info_classif",
]

"""
Ensemble methods for FHE-ML SDK.

Provides ensemble learning methods compatible with FHE operations:
- VotingClassifier: Soft/hard voting for classification
- VotingRegressor: Averaging for regression
- StackingClassifier: Stacked generalization for classification
- StackingRegressor: Stacked generalization for regression
- BaggingClassifier: Bootstrap aggregating for classification
- BaggingRegressor: Bootstrap aggregating for regression
"""

from __future__ import annotations

from typing import Any, List, Optional, Tuple, Union

import numpy as np


class BaseEnsemble:
    """Base class for ensemble methods."""

    def __init__(self):
        self.estimators_: List[Any] = []
        self.is_fitted_: bool = False

    def _check_is_fitted(self) -> None:
        """Check if estimator is fitted."""
        if not self.is_fitted_:
            raise ValueError("Estimator not fitted. Call fit() first.")

    def _validate_estimators(self, estimators: List[Tuple[str, Any]]) -> List[Tuple[str, Any]]:
        """Validate estimators list."""
        if not estimators:
            raise ValueError("estimators list cannot be empty")

        validated = []
        names = set()
        for item in estimators:
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                raise ValueError("Each estimator must be a tuple of (name, estimator)")
            name, est = item
            if name in names:
                raise ValueError(f"Duplicate estimator name: {name}")
            names.add(name)
            validated.append((name, est))

        return validated


class VotingClassifier(BaseEnsemble):
    """
    Soft/hard voting classifier for ensemble classification.

    Parameters
    ----------
    estimators : list of (str, estimator) tuples
        List of (name, estimator) tuples.
    voting : {'hard', 'soft'}, default='hard'
        If 'hard', uses predicted class labels for majority vote.
        If 'soft', uses predicted probabilities for weighted vote.
    weights : array-like of shape (n_estimators,), default=None
        Weights for each estimator. If None, uniform weights.

    Attributes
    ----------
    estimators_ : list
        Fitted estimators.
    classes_ : array
        Class labels.

    Examples
    --------
    >>> from sdk.ensemble import VotingClassifier
    >>> from sdk.linear_model import LogisticRegression
    >>> from sdk.tree import DecisionTreeClassifier
    >>> clf1 = LogisticRegression()
    >>> clf2 = DecisionTreeClassifier(max_depth=3)
    >>> voting = VotingClassifier([('lr', clf1), ('dt', clf2)], voting='soft')
    >>> voting.fit(X_train, y_train)
    >>> predictions = voting.predict(X_test)
    """

    def __init__(
        self,
        estimators: List[Tuple[str, Any]],
        voting: str = "hard",
        weights: Optional[np.ndarray] = None,
    ):
        super().__init__()
        self.estimators = self._validate_estimators(estimators)
        self.voting = voting
        self.weights = weights
        self.classes_: Optional[np.ndarray] = None
        self.le_: Optional[Any] = None  # Label encoder if needed

    def fit(self, X: np.ndarray, y: np.ndarray) -> VotingClassifier:
        """
        Fit the estimators.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : array-like of shape (n_samples,)
            Target values.

        Returns
        -------
        self : VotingClassifier
            Fitted estimator.
        """
        X = np.asarray(X)
        y = np.asarray(y)

        self.classes_ = np.unique(y)
        self.estimators_ = []

        for name, est in self.estimators:
            # Clone and fit each estimator
            fitted_est = self._clone_and_fit(est, X, y)
            self.estimators_.append((name, fitted_est))

        self.is_fitted_ = True
        return self

    def _clone_and_fit(self, estimator: Any, X: np.ndarray, y: np.ndarray) -> Any:
        """Clone an estimator and fit it."""
        # Simple fit without cloning (assumes estimators are fresh)
        estimator.fit(X, y)
        return estimator

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class labels.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        y_pred : array of shape (n_samples,)
            Predicted class labels.
        """
        self._check_is_fitted()
        X = np.asarray(X)

        if self.voting == "soft":
            return self._predict_soft(X)
        else:
            return self._predict_hard(X)

    def _predict_hard(self, X: np.ndarray) -> np.ndarray:
        """Hard voting: majority vote of predictions."""
        predictions = np.array(
            [est.predict(X) for _, est in self.estimators_]
        )  # shape: (n_estimators, n_samples)

        # Weighted voting
        weights = self.weights if self.weights is not None else np.ones(len(self.estimators_))

        # For each sample, find the class with most votes
        n_samples = X.shape[0]
        result = np.empty(n_samples, dtype=self.classes_.dtype)

        for i in range(n_samples):
            votes = {}
            for j, pred in enumerate(predictions[:, i]):
                votes[pred] = votes.get(pred, 0) + weights[j]
            result[i] = max(votes, key=votes.get)

        return result

    def _predict_soft(self, X: np.ndarray) -> np.ndarray:
        """Soft voting: weighted average of probabilities."""
        probas = self.predict_proba(X)
        return self.classes_[np.argmax(probas, axis=1)]

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class probabilities.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        proba : array of shape (n_samples, n_classes)
            Class probabilities.
        """
        self._check_is_fitted()
        X = np.asarray(X)

        weights = self.weights if self.weights is not None else np.ones(len(self.estimators_))
        weights = np.array(weights) / np.sum(weights)

        # Collect probabilities from all estimators
        all_probas = []
        for _, est in self.estimators_:
            if hasattr(est, "predict_proba"):
                proba = est.predict_proba(X)
            else:
                # Use one-hot encoding of predictions
                preds = est.predict(X)
                proba = np.zeros((len(X), len(self.classes_)))
                for i, p in enumerate(preds):
                    idx = np.where(self.classes_ == p)[0][0]
                    proba[i, idx] = 1.0
            all_probas.append(proba)

        # Weighted average
        avg_proba = np.zeros_like(all_probas[0])
        for i, proba in enumerate(all_probas):
            avg_proba += weights[i] * proba

        return avg_proba

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Return accuracy score."""
        return np.mean(self.predict(X) == y)


class VotingRegressor(BaseEnsemble):
    """
    Voting regressor for ensemble regression.

    Predicts by averaging predictions of base estimators.

    Parameters
    ----------
    estimators : list of (str, estimator) tuples
        List of (name, estimator) tuples.
    weights : array-like of shape (n_estimators,), default=None
        Weights for each estimator. If None, uniform weights.

    Examples
    --------
    >>> from sdk.ensemble import VotingRegressor
    >>> from sdk.linear_model import LinearRegression, Ridge
    >>> reg1 = LinearRegression()
    >>> reg2 = Ridge(alpha=1.0)
    >>> voting = VotingRegressor([('lr', reg1), ('ridge', reg2)])
    >>> voting.fit(X_train, y_train)
    >>> predictions = voting.predict(X_test)
    """

    def __init__(
        self,
        estimators: List[Tuple[str, Any]],
        weights: Optional[np.ndarray] = None,
    ):
        super().__init__()
        self.estimators = self._validate_estimators(estimators)
        self.weights = weights

    def fit(self, X: np.ndarray, y: np.ndarray) -> VotingRegressor:
        """
        Fit the estimators.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : array-like of shape (n_samples,)
            Target values.

        Returns
        -------
        self : VotingRegressor
            Fitted estimator.
        """
        X = np.asarray(X)
        y = np.asarray(y)

        self.estimators_ = []
        for name, est in self.estimators:
            est.fit(X, y)
            self.estimators_.append((name, est))

        self.is_fitted_ = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict by averaging.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        y_pred : array of shape (n_samples,)
            Predicted values.
        """
        self._check_is_fitted()
        X = np.asarray(X)

        predictions = np.array([est.predict(X) for _, est in self.estimators_])

        weights = self.weights if self.weights is not None else np.ones(len(self.estimators_))
        weights = np.array(weights) / np.sum(weights)

        return np.average(predictions, axis=0, weights=weights)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Return R^2 score."""
        y_pred = self.predict(X)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        return 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0


class StackingClassifier(BaseEnsemble):
    """
    Stacked generalization classifier.

    Uses a meta-learner to combine base estimator predictions.

    Parameters
    ----------
    estimators : list of (str, estimator) tuples
        Base estimators.
    final_estimator : estimator
        Meta-learner that combines base predictions.
    cv : int, default=5
        Number of cross-validation folds for generating meta-features.
    stack_method : {'auto', 'predict_proba', 'predict'}, default='auto'
        Method to generate meta-features.
    passthrough : bool, default=False
        If True, include original features in meta-features.

    Examples
    --------
    >>> from sdk.ensemble import StackingClassifier
    >>> from sdk.linear_model import LogisticRegression
    >>> from sdk.tree import DecisionTreeClassifier
    >>> estimators = [
    ...     ('dt', DecisionTreeClassifier(max_depth=3)),
    ...     ('lr', LogisticRegression())
    ... ]
    >>> stacking = StackingClassifier(estimators, LogisticRegression())
    >>> stacking.fit(X_train, y_train)
    """

    def __init__(
        self,
        estimators: List[Tuple[str, Any]],
        final_estimator: Any,
        cv: int = 5,
        stack_method: str = "auto",
        passthrough: bool = False,
    ):
        super().__init__()
        self.estimators = self._validate_estimators(estimators)
        self.final_estimator = final_estimator
        self.cv = cv
        self.stack_method = stack_method
        self.passthrough = passthrough
        self.classes_: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> StackingClassifier:
        """
        Fit the stacking classifier.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : array-like of shape (n_samples,)
            Target values.

        Returns
        -------
        self : StackingClassifier
            Fitted estimator.
        """
        X = np.asarray(X)
        y = np.asarray(y)
        n_samples = X.shape[0]

        self.classes_ = np.unique(y)
        n_classes = len(self.classes_)

        # Generate meta-features using cross-validation
        meta_features = np.zeros((n_samples, len(self.estimators) * n_classes))

        # Simple k-fold split
        fold_size = n_samples // self.cv
        indices = np.arange(n_samples)
        np.random.shuffle(indices)

        self.estimators_ = []

        for est_idx, (name, est) in enumerate(self.estimators):
            est_meta = np.zeros((n_samples, n_classes))

            for fold in range(self.cv):
                start = fold * fold_size
                end = start + fold_size if fold < self.cv - 1 else n_samples

                val_idx = indices[start:end]
                train_idx = np.concatenate([indices[:start], indices[end:]])

                X_train, X_val = X[train_idx], X[val_idx]
                y_train = y[train_idx]

                # Fit on training fold
                est.fit(X_train, y_train)

                # Predict on validation fold
                if hasattr(est, "predict_proba") and self.stack_method != "predict":
                    est_meta[val_idx] = est.predict_proba(X_val)
                else:
                    preds = est.predict(X_val)
                    for i, p in enumerate(preds):
                        idx = np.where(self.classes_ == p)[0][0]
                        est_meta[val_idx[i], idx] = 1.0

            # Store meta-features
            meta_features[:, est_idx * n_classes : (est_idx + 1) * n_classes] = est_meta

            # Refit on full data
            est.fit(X, y)
            self.estimators_.append((name, est))

        # Add original features if passthrough
        if self.passthrough:
            meta_features = np.hstack([meta_features, X])

        # Fit final estimator
        self.final_estimator.fit(meta_features, y)
        self.is_fitted_ = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict class labels."""
        self._check_is_fitted()
        meta_features = self._get_meta_features(X)
        return self.final_estimator.predict(meta_features)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict class probabilities."""
        self._check_is_fitted()
        meta_features = self._get_meta_features(X)
        if hasattr(self.final_estimator, "predict_proba"):
            return self.final_estimator.predict_proba(meta_features)
        else:
            preds = self.final_estimator.predict(meta_features)
            proba = np.zeros((len(X), len(self.classes_)))
            for i, p in enumerate(preds):
                idx = np.where(self.classes_ == p)[0][0]
                proba[i, idx] = 1.0
            return proba

    def _get_meta_features(self, X: np.ndarray) -> np.ndarray:
        """Generate meta-features from base estimators."""
        X = np.asarray(X)
        n_classes = len(self.classes_)
        meta_features = np.zeros((X.shape[0], len(self.estimators_) * n_classes))

        for est_idx, (_, est) in enumerate(self.estimators_):
            if hasattr(est, "predict_proba") and self.stack_method != "predict":
                est_meta = est.predict_proba(X)
            else:
                preds = est.predict(X)
                est_meta = np.zeros((len(X), n_classes))
                for i, p in enumerate(preds):
                    idx = np.where(self.classes_ == p)[0][0]
                    est_meta[i, idx] = 1.0

            meta_features[:, est_idx * n_classes : (est_idx + 1) * n_classes] = est_meta

        if self.passthrough:
            meta_features = np.hstack([meta_features, X])

        return meta_features

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Return accuracy score."""
        return np.mean(self.predict(X) == y)


class StackingRegressor(BaseEnsemble):
    """
    Stacked generalization regressor.

    Parameters
    ----------
    estimators : list of (str, estimator) tuples
        Base estimators.
    final_estimator : estimator
        Meta-learner that combines base predictions.
    cv : int, default=5
        Number of cross-validation folds.
    passthrough : bool, default=False
        If True, include original features.

    Examples
    --------
    >>> from sdk.ensemble import StackingRegressor
    >>> from sdk.linear_model import LinearRegression, Ridge
    >>> estimators = [('lr', LinearRegression()), ('ridge', Ridge())]
    >>> stacking = StackingRegressor(estimators, LinearRegression())
    >>> stacking.fit(X_train, y_train)
    """

    def __init__(
        self,
        estimators: List[Tuple[str, Any]],
        final_estimator: Any,
        cv: int = 5,
        passthrough: bool = False,
    ):
        super().__init__()
        self.estimators = self._validate_estimators(estimators)
        self.final_estimator = final_estimator
        self.cv = cv
        self.passthrough = passthrough

    def fit(self, X: np.ndarray, y: np.ndarray) -> StackingRegressor:
        """Fit the stacking regressor."""
        X = np.asarray(X)
        y = np.asarray(y)
        n_samples = X.shape[0]

        # Generate meta-features
        meta_features = np.zeros((n_samples, len(self.estimators)))

        fold_size = n_samples // self.cv
        indices = np.arange(n_samples)
        np.random.shuffle(indices)

        self.estimators_ = []

        for est_idx, (name, est) in enumerate(self.estimators):
            for fold in range(self.cv):
                start = fold * fold_size
                end = start + fold_size if fold < self.cv - 1 else n_samples

                val_idx = indices[start:end]
                train_idx = np.concatenate([indices[:start], indices[end:]])

                X_train, X_val = X[train_idx], X[val_idx]
                y_train = y[train_idx]

                est.fit(X_train, y_train)
                meta_features[val_idx, est_idx] = est.predict(X_val)

            # Refit on full data
            est.fit(X, y)
            self.estimators_.append((name, est))

        if self.passthrough:
            meta_features = np.hstack([meta_features, X])

        self.final_estimator.fit(meta_features, y)
        self.is_fitted_ = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict using the stacking regressor."""
        self._check_is_fitted()
        X = np.asarray(X)

        meta_features = np.column_stack([est.predict(X) for _, est in self.estimators_])

        if self.passthrough:
            meta_features = np.hstack([meta_features, X])

        return self.final_estimator.predict(meta_features)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Return R^2 score."""
        y_pred = self.predict(X)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        return 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0


class BaggingClassifier(BaseEnsemble):
    """
    Bootstrap aggregating classifier.

    Fits base estimators on random subsets of the data.

    Parameters
    ----------
    estimator : estimator
        Base estimator to fit on subsets.
    n_estimators : int, default=10
        Number of estimators in the ensemble.
    max_samples : float or int, default=1.0
        Number of samples to draw. If float, fraction of total.
    max_features : float or int, default=1.0
        Number of features to draw. If float, fraction of total.
    bootstrap : bool, default=True
        Whether to use bootstrap sampling.
    bootstrap_features : bool, default=False
        Whether to bootstrap features.
    random_state : int, default=None
        Random seed.

    Examples
    --------
    >>> from sdk.ensemble import BaggingClassifier
    >>> from sdk.tree import DecisionTreeClassifier
    >>> bagging = BaggingClassifier(DecisionTreeClassifier(), n_estimators=10)
    >>> bagging.fit(X_train, y_train)
    >>> predictions = bagging.predict(X_test)
    """

    def __init__(
        self,
        estimator: Any,
        n_estimators: int = 10,
        max_samples: Union[int, float] = 1.0,
        max_features: Union[int, float] = 1.0,
        bootstrap: bool = True,
        bootstrap_features: bool = False,
        random_state: Optional[int] = None,
    ):
        super().__init__()
        self.base_estimator = estimator
        self.n_estimators = n_estimators
        self.max_samples = max_samples
        self.max_features = max_features
        self.bootstrap = bootstrap
        self.bootstrap_features = bootstrap_features
        self.random_state = random_state
        self.classes_: Optional[np.ndarray] = None
        self.estimators_features_: List[np.ndarray] = []

    def fit(self, X: np.ndarray, y: np.ndarray) -> BaggingClassifier:
        """Fit the bagging classifier."""
        X = np.asarray(X)
        y = np.asarray(y)
        n_samples, n_features = X.shape

        self.classes_ = np.unique(y)

        if self.random_state is not None:
            np.random.seed(self.random_state)

        # Determine sample and feature counts
        if isinstance(self.max_samples, float):
            n_samples_bootstrap = int(self.max_samples * n_samples)
        else:
            n_samples_bootstrap = self.max_samples

        if isinstance(self.max_features, float):
            n_features_bootstrap = int(self.max_features * n_features)
        else:
            n_features_bootstrap = self.max_features

        self.estimators_ = []
        self.estimators_features_ = []

        for _ in range(self.n_estimators):
            # Sample indices
            if self.bootstrap:
                sample_idx = np.random.choice(n_samples, n_samples_bootstrap, replace=True)
            else:
                sample_idx = np.random.choice(n_samples, n_samples_bootstrap, replace=False)

            # Feature indices
            if self.bootstrap_features:
                feature_idx = np.random.choice(n_features, n_features_bootstrap, replace=True)
            else:
                feature_idx = np.random.choice(n_features, n_features_bootstrap, replace=False)

            # Subset data
            X_subset = X[np.ix_(sample_idx, feature_idx)]
            y_subset = y[sample_idx]

            # Create and fit estimator
            est = self._clone_estimator(self.base_estimator)
            est.fit(X_subset, y_subset)

            self.estimators_.append(est)
            self.estimators_features_.append(feature_idx)

        self.is_fitted_ = True
        return self

    def _clone_estimator(self, estimator: Any) -> Any:
        """Create a fresh copy of the base estimator."""
        # Simple approach: create new instance with same parameters
        return estimator.__class__(**estimator.__dict__.copy())

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict class labels."""
        self._check_is_fitted()
        X = np.asarray(X)

        # Collect predictions
        predictions = np.array(
            [
                est.predict(X[:, self.estimators_features_[i]])
                for i, est in enumerate(self.estimators_)
            ]
        )

        # Majority vote
        n_samples = X.shape[0]
        result = np.empty(n_samples, dtype=self.classes_.dtype)

        for i in range(n_samples):
            votes = {}
            for pred in predictions[:, i]:
                votes[pred] = votes.get(pred, 0) + 1
            result[i] = max(votes, key=votes.get)

        return result

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict class probabilities."""
        self._check_is_fitted()
        X = np.asarray(X)
        n_samples = X.shape[0]
        n_classes = len(self.classes_)

        # Average probabilities
        proba = np.zeros((n_samples, n_classes))

        for i, est in enumerate(self.estimators_):
            X_subset = X[:, self.estimators_features_[i]]
            if hasattr(est, "predict_proba"):
                proba += est.predict_proba(X_subset)
            else:
                preds = est.predict(X_subset)
                for j, p in enumerate(preds):
                    idx = np.where(self.classes_ == p)[0][0]
                    proba[j, idx] += 1.0

        proba /= self.n_estimators
        return proba

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Return accuracy score."""
        return np.mean(self.predict(X) == y)


class BaggingRegressor(BaseEnsemble):
    """
    Bootstrap aggregating regressor.

    Parameters
    ----------
    estimator : estimator
        Base estimator to fit on subsets.
    n_estimators : int, default=10
        Number of estimators.
    max_samples : float or int, default=1.0
        Number of samples to draw.
    max_features : float or int, default=1.0
        Number of features to draw.
    bootstrap : bool, default=True
        Whether to use bootstrap sampling.
    bootstrap_features : bool, default=False
        Whether to bootstrap features.
    random_state : int, default=None
        Random seed.

    Examples
    --------
    >>> from sdk.ensemble import BaggingRegressor
    >>> from sdk.tree import DecisionTreeRegressor
    >>> bagging = BaggingRegressor(DecisionTreeRegressor(), n_estimators=10)
    >>> bagging.fit(X_train, y_train)
    """

    def __init__(
        self,
        estimator: Any,
        n_estimators: int = 10,
        max_samples: Union[int, float] = 1.0,
        max_features: Union[int, float] = 1.0,
        bootstrap: bool = True,
        bootstrap_features: bool = False,
        random_state: Optional[int] = None,
    ):
        super().__init__()
        self.base_estimator = estimator
        self.n_estimators = n_estimators
        self.max_samples = max_samples
        self.max_features = max_features
        self.bootstrap = bootstrap
        self.bootstrap_features = bootstrap_features
        self.random_state = random_state
        self.estimators_features_: List[np.ndarray] = []

    def fit(self, X: np.ndarray, y: np.ndarray) -> BaggingRegressor:
        """Fit the bagging regressor."""
        X = np.asarray(X)
        y = np.asarray(y)
        n_samples, n_features = X.shape

        if self.random_state is not None:
            np.random.seed(self.random_state)

        if isinstance(self.max_samples, float):
            n_samples_bootstrap = int(self.max_samples * n_samples)
        else:
            n_samples_bootstrap = self.max_samples

        if isinstance(self.max_features, float):
            n_features_bootstrap = int(self.max_features * n_features)
        else:
            n_features_bootstrap = self.max_features

        self.estimators_ = []
        self.estimators_features_ = []

        for _ in range(self.n_estimators):
            if self.bootstrap:
                sample_idx = np.random.choice(n_samples, n_samples_bootstrap, replace=True)
            else:
                sample_idx = np.random.choice(n_samples, n_samples_bootstrap, replace=False)

            if self.bootstrap_features:
                feature_idx = np.random.choice(n_features, n_features_bootstrap, replace=True)
            else:
                feature_idx = np.random.choice(n_features, n_features_bootstrap, replace=False)

            X_subset = X[np.ix_(sample_idx, feature_idx)]
            y_subset = y[sample_idx]

            est = self._clone_estimator(self.base_estimator)
            est.fit(X_subset, y_subset)

            self.estimators_.append(est)
            self.estimators_features_.append(feature_idx)

        self.is_fitted_ = True
        return self

    def _clone_estimator(self, estimator: Any) -> Any:
        """Create a fresh copy of the base estimator."""
        return estimator.__class__(**estimator.__dict__.copy())

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict by averaging."""
        self._check_is_fitted()
        X = np.asarray(X)

        predictions = np.array(
            [
                est.predict(X[:, self.estimators_features_[i]])
                for i, est in enumerate(self.estimators_)
            ]
        )

        return np.mean(predictions, axis=0)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Return R^2 score."""
        y_pred = self.predict(X)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        return 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0


class AdaBoostClassifier(BaseEnsemble):
    """
    AdaBoost classifier.

    Adaptively boosts weak classifiers by focusing on misclassified samples.

    Parameters
    ----------
    estimator : estimator, default=None
        Base estimator. If None, uses decision stump.
    n_estimators : int, default=50
        Number of estimators.
    learning_rate : float, default=1.0
        Weight applied to each classifier.
    random_state : int, default=None
        Random seed.

    Examples
    --------
    >>> from sdk.ensemble import AdaBoostClassifier
    >>> ada = AdaBoostClassifier(n_estimators=50)
    >>> ada.fit(X_train, y_train)
    """

    def __init__(
        self,
        estimator: Optional[Any] = None,
        n_estimators: int = 50,
        learning_rate: float = 1.0,
        random_state: Optional[int] = None,
    ):
        super().__init__()
        self.base_estimator = estimator
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.random_state = random_state
        self.estimator_weights_: List[float] = []
        self.classes_: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> AdaBoostClassifier:
        """Fit the AdaBoost classifier."""
        X = np.asarray(X)
        y = np.asarray(y)
        n_samples = X.shape[0]

        self.classes_ = np.unique(y)

        if self.random_state is not None:
            np.random.seed(self.random_state)

        # Initialize sample weights
        sample_weight = np.ones(n_samples) / n_samples

        self.estimators_ = []
        self.estimator_weights_ = []

        for _ in range(self.n_estimators):
            # Create base estimator (simple decision stump if none)
            if self.base_estimator is not None:
                est = self._clone_estimator(self.base_estimator)
            else:
                est = DecisionStump()

            # Fit with sample weights
            est.fit(X, y, sample_weight=sample_weight)

            # Predictions
            y_pred = est.predict(X)

            # Calculate error
            incorrect = y_pred != y
            error = np.sum(sample_weight * incorrect) / np.sum(sample_weight)

            # Stop if error is too high
            if error >= 0.5:
                break

            # Calculate estimator weight
            if error > 0:
                alpha = self.learning_rate * 0.5 * np.log((1 - error) / error)
            else:
                alpha = self.learning_rate

            # Update sample weights
            sample_weight *= np.exp(alpha * (2 * incorrect - 1))
            sample_weight /= np.sum(sample_weight)

            self.estimators_.append(est)
            self.estimator_weights_.append(alpha)

        self.is_fitted_ = True
        return self

    def _clone_estimator(self, estimator: Any) -> Any:
        """Create a fresh copy of the base estimator."""
        return estimator.__class__(**estimator.__dict__.copy())

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict class labels."""
        self._check_is_fitted()
        X = np.asarray(X)
        n_samples = X.shape[0]

        # Weighted vote
        class_votes = np.zeros((n_samples, len(self.classes_)))

        for est, alpha in zip(self.estimators_, self.estimator_weights_):
            preds = est.predict(X)
            for i, p in enumerate(preds):
                idx = np.where(self.classes_ == p)[0][0]
                class_votes[i, idx] += alpha

        return self.classes_[np.argmax(class_votes, axis=1)]

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Return accuracy score."""
        return np.mean(self.predict(X) == y)


class DecisionStump:
    """Simple decision stump (1-level decision tree) for AdaBoost."""

    def __init__(self):
        self.feature_idx: int = 0
        self.threshold: float = 0.0
        self.polarity: int = 1
        self.classes_: Optional[np.ndarray] = None

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None,
    ) -> DecisionStump:
        """Fit the decision stump."""
        n_samples, n_features = X.shape
        self.classes_ = np.unique(y)

        if sample_weight is None:
            sample_weight = np.ones(n_samples) / n_samples

        best_error = float("inf")

        for feature_idx in range(n_features):
            thresholds = np.unique(X[:, feature_idx])

            for threshold in thresholds:
                for polarity in [1, -1]:
                    predictions = np.where(
                        polarity * X[:, feature_idx] < polarity * threshold,
                        self.classes_[0],
                        self.classes_[-1],
                    )
                    error = np.sum(sample_weight * (predictions != y))

                    if error < best_error:
                        best_error = error
                        self.feature_idx = feature_idx
                        self.threshold = threshold
                        self.polarity = polarity

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict class labels."""
        X = np.asarray(X)
        return np.where(
            self.polarity * X[:, self.feature_idx] < self.polarity * self.threshold,
            self.classes_[0],
            self.classes_[-1],
        )


# Utility functions


def get_ensemble_feature_importances(
    ensemble: BaseEnsemble,
    X: np.ndarray,
    y: np.ndarray,
    n_repeats: int = 10,
) -> np.ndarray:
    """
    Calculate permutation feature importances for an ensemble.

    Parameters
    ----------
    ensemble : fitted ensemble
        Fitted ensemble estimator.
    X : array-like of shape (n_samples, n_features)
        Test data.
    y : array-like of shape (n_samples,)
        True labels.
    n_repeats : int, default=10
        Number of permutation repeats.

    Returns
    -------
    importances : array of shape (n_features,)
        Feature importances.
    """
    X = np.asarray(X)
    y = np.asarray(y)
    n_features = X.shape[1]

    baseline_score = ensemble.score(X, y)
    importances = np.zeros(n_features)

    for feat_idx in range(n_features):
        scores = []
        for _ in range(n_repeats):
            X_permuted = X.copy()
            np.random.shuffle(X_permuted[:, feat_idx])
            scores.append(ensemble.score(X_permuted, y))

        importances[feat_idx] = baseline_score - np.mean(scores)

    return importances

"""
FHE-compatible multi-output models.

Provides wrappers for handling multi-target regression and
multi-label classification with FHE-compatible base estimators.
"""

from enum import Enum
from typing import Any, List, Optional

import numpy as np


class MultiOutputStrategy(Enum):
    """Strategy for handling multiple outputs."""

    INDEPENDENT = "independent"  # Train separate model per output
    CHAIN = "chain"  # Use previous outputs as features
    REGRESSOR_CHAIN = "regressor_chain"  # Chain for regression


class MultiOutputClassifier:
    """
    Multi-target classification wrapper.

    Fits one classifier per target (column) in y.
    Each classifier is trained independently.

    Example:
        >>> from xcapit_fhe import MultiOutputClassifier, LogisticRegression
        >>> clf = MultiOutputClassifier(LogisticRegression())
        >>> clf.fit(X, y_multi)  # y_multi has shape (n_samples, n_targets)
        >>> predictions = clf.predict(X_test)
    """

    def __init__(self, estimator: Any, n_jobs: Optional[int] = None):
        """
        Initialize multi-output classifier.

        Args:
            estimator: Base classifier (will be cloned for each target)
            n_jobs: Number of parallel jobs (not used in FHE mode)
        """
        self.estimator = estimator
        self.n_jobs = n_jobs
        self._fitted = False
        self._estimators = []
        self._n_outputs = None
        self._classes = []

    def fit(self, X: np.ndarray, y: np.ndarray, **fit_params) -> "MultiOutputClassifier":
        """
        Fit one classifier per target.

        Args:
            X: Feature matrix (n_samples, n_features)
            y: Target matrix (n_samples, n_outputs)
            **fit_params: Parameters passed to fit

        Returns:
            self
        """
        import copy

        X = np.asarray(X)
        y = np.asarray(y)

        if y.ndim == 1:
            y = y.reshape(-1, 1)

        self._n_outputs = y.shape[1]
        self._estimators = []
        self._classes = []

        for i in range(self._n_outputs):
            # Clone estimator
            estimator = copy.deepcopy(self.estimator)

            # Fit on i-th target
            y_i = y[:, i]
            estimator.fit(X, y_i, **fit_params)

            self._estimators.append(estimator)
            self._classes.append(np.unique(y_i))

        self._fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict targets for X.

        Args:
            X: Feature matrix

        Returns:
            Predicted targets (n_samples, n_outputs)
        """
        if not self._fitted:
            raise RuntimeError("Must fit before predict")

        X = np.asarray(X)
        n_samples = X.shape[0]

        predictions = np.zeros((n_samples, self._n_outputs))

        for i, estimator in enumerate(self._estimators):
            predictions[:, i] = estimator.predict(X)

        return predictions

    def predict_proba(self, X: np.ndarray) -> List[np.ndarray]:
        """
        Predict class probabilities for each target.

        Args:
            X: Feature matrix

        Returns:
            List of probability arrays, one per target
        """
        if not self._fitted:
            raise RuntimeError("Must fit before predict_proba")

        X = np.asarray(X)
        probas = []

        for estimator in self._estimators:
            if hasattr(estimator, "predict_proba"):
                probas.append(estimator.predict_proba(X))
            else:
                raise AttributeError("Base estimator does not have predict_proba")

        return probas

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        Return mean accuracy across all targets.

        Args:
            X: Feature matrix
            y: True targets

        Returns:
            Mean accuracy
        """
        y = np.asarray(y)
        if y.ndim == 1:
            y = y.reshape(-1, 1)

        predictions = self.predict(X)
        return (predictions == y).mean()

    def partial_fit(
        self, X: np.ndarray, y: np.ndarray, classes: Optional[List] = None
    ) -> "MultiOutputClassifier":
        """
        Incrementally fit estimators (for streaming data).

        Args:
            X: Feature matrix
            y: Target matrix
            classes: List of classes per target

        Returns:
            self
        """
        import copy

        X = np.asarray(X)
        y = np.asarray(y)

        if y.ndim == 1:
            y = y.reshape(-1, 1)

        # Initialize on first call
        if not self._fitted:
            self._n_outputs = y.shape[1]
            self._estimators = [copy.deepcopy(self.estimator) for _ in range(self._n_outputs)]
            self._classes = classes or [None] * self._n_outputs
            self._fitted = True

        for i, estimator in enumerate(self._estimators):
            if hasattr(estimator, "partial_fit"):
                estimator.partial_fit(X, y[:, i], classes=self._classes[i])
            else:
                estimator.fit(X, y[:, i])

        return self


class MultiOutputRegressor:
    """
    Multi-target regression wrapper.

    Fits one regressor per target (column) in y.

    Example:
        >>> from xcapit_fhe import MultiOutputRegressor, LinearRegression
        >>> reg = MultiOutputRegressor(LinearRegression())
        >>> reg.fit(X, y_multi)
        >>> predictions = reg.predict(X_test)
    """

    def __init__(self, estimator: Any, n_jobs: Optional[int] = None):
        """
        Initialize multi-output regressor.

        Args:
            estimator: Base regressor
            n_jobs: Number of parallel jobs (not used)
        """
        self.estimator = estimator
        self.n_jobs = n_jobs
        self._fitted = False
        self._estimators = []
        self._n_outputs = None

    def fit(self, X: np.ndarray, y: np.ndarray, **fit_params) -> "MultiOutputRegressor":
        """
        Fit one regressor per target.

        Args:
            X: Feature matrix
            y: Target matrix
            **fit_params: Parameters passed to fit

        Returns:
            self
        """
        import copy

        X = np.asarray(X)
        y = np.asarray(y)

        if y.ndim == 1:
            y = y.reshape(-1, 1)

        self._n_outputs = y.shape[1]
        self._estimators = []

        for i in range(self._n_outputs):
            estimator = copy.deepcopy(self.estimator)
            estimator.fit(X, y[:, i], **fit_params)
            self._estimators.append(estimator)

        self._fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict targets for X.

        Args:
            X: Feature matrix

        Returns:
            Predicted targets
        """
        if not self._fitted:
            raise RuntimeError("Must fit before predict")

        X = np.asarray(X)
        n_samples = X.shape[0]

        predictions = np.zeros((n_samples, self._n_outputs))

        for i, estimator in enumerate(self._estimators):
            predictions[:, i] = estimator.predict(X)

        return predictions

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        Return mean R² score across all targets.

        Args:
            X: Feature matrix
            y: True targets

        Returns:
            Mean R² score
        """
        y = np.asarray(y)
        if y.ndim == 1:
            y = y.reshape(-1, 1)

        predictions = self.predict(X)

        scores = []
        for i in range(self._n_outputs):
            ss_res = np.sum((y[:, i] - predictions[:, i]) ** 2)
            ss_tot = np.sum((y[:, i] - y[:, i].mean()) ** 2)
            r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
            scores.append(r2)

        return np.mean(scores)

    def partial_fit(self, X: np.ndarray, y: np.ndarray) -> "MultiOutputRegressor":
        """
        Incrementally fit estimators.

        Args:
            X: Feature matrix
            y: Target matrix

        Returns:
            self
        """
        import copy

        X = np.asarray(X)
        y = np.asarray(y)

        if y.ndim == 1:
            y = y.reshape(-1, 1)

        if not self._fitted:
            self._n_outputs = y.shape[1]
            self._estimators = [copy.deepcopy(self.estimator) for _ in range(self._n_outputs)]
            self._fitted = True

        for i, estimator in enumerate(self._estimators):
            if hasattr(estimator, "partial_fit"):
                estimator.partial_fit(X, y[:, i])
            else:
                estimator.fit(X, y[:, i])

        return self


class ClassifierChain:
    """
    Classifier chain for multi-label classification.

    Chains classifiers so each predicts using original features
    plus predictions of previous classifiers in the chain.

    Example:
        >>> from xcapit_fhe import ClassifierChain, LogisticRegression
        >>> chain = ClassifierChain(LogisticRegression())
        >>> chain.fit(X, y_multilabel)
        >>> predictions = chain.predict(X_test)
    """

    def __init__(
        self,
        estimator: Any,
        order: Optional[List[int]] = None,
        cv: Optional[int] = None,
        random_state: Optional[int] = None,
    ):
        """
        Initialize classifier chain.

        Args:
            estimator: Base classifier
            order: Order of labels in chain (default: order in y)
            cv: Number of folds for cross-validation (for training set predictions)
            random_state: Random seed for order shuffling
        """
        self.estimator = estimator
        self.order = order
        self.cv = cv
        self.random_state = random_state
        self._fitted = False
        self._estimators = []
        self._order = None
        self._n_outputs = None
        self._classes = []

    def fit(self, X: np.ndarray, y: np.ndarray) -> "ClassifierChain":
        """
        Fit the classifier chain.

        Args:
            X: Feature matrix
            y: Multi-label target matrix

        Returns:
            self
        """
        import copy

        X = np.asarray(X)
        y = np.asarray(y)

        if y.ndim == 1:
            y = y.reshape(-1, 1)

        self._n_outputs = y.shape[1]

        # Determine order
        if self.order is not None:
            self._order = list(self.order)
        else:
            self._order = list(range(self._n_outputs))
            if self.random_state is not None:
                rng = np.random.default_rng(self.random_state)
                rng.shuffle(self._order)

        self._estimators = []
        self._classes = []

        # Build chain
        X_chain = X.copy()

        for i, target_idx in enumerate(self._order):
            estimator = copy.deepcopy(self.estimator)

            # Fit on augmented features
            y_target = y[:, target_idx]
            estimator.fit(X_chain, y_target)

            self._estimators.append(estimator)
            self._classes.append(np.unique(y_target))

            # Augment features with predictions for next estimator
            if i < self._n_outputs - 1:
                predictions = estimator.predict(X_chain).reshape(-1, 1)
                X_chain = np.hstack([X_chain, predictions])

        self._fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict using the chain.

        Args:
            X: Feature matrix

        Returns:
            Predicted labels
        """
        if not self._fitted:
            raise RuntimeError("Must fit before predict")

        X = np.asarray(X)
        n_samples = X.shape[0]

        predictions = np.zeros((n_samples, self._n_outputs))
        X_chain = X.copy()

        for i, (target_idx, estimator) in enumerate(zip(self._order, self._estimators)):
            y_pred = estimator.predict(X_chain)
            predictions[:, target_idx] = y_pred

            # Augment for next
            if i < self._n_outputs - 1:
                X_chain = np.hstack([X_chain, y_pred.reshape(-1, 1)])

        return predictions

    def predict_proba(self, X: np.ndarray) -> List[np.ndarray]:
        """
        Predict class probabilities.

        Args:
            X: Feature matrix

        Returns:
            List of probability arrays per target (in original order)
        """
        if not self._fitted:
            raise RuntimeError("Must fit before predict_proba")

        X = np.asarray(X)
        probas = [None] * self._n_outputs
        X_chain = X.copy()

        for i, (target_idx, estimator) in enumerate(zip(self._order, self._estimators)):
            if hasattr(estimator, "predict_proba"):
                proba = estimator.predict_proba(X_chain)
                probas[target_idx] = proba
            else:
                raise AttributeError("Base estimator has no predict_proba")

            # Augment with predictions
            if i < self._n_outputs - 1:
                y_pred = estimator.predict(X_chain)
                X_chain = np.hstack([X_chain, y_pred.reshape(-1, 1)])

        return probas

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Compute accuracy."""
        predictions = self.predict(X)
        return (predictions == y).mean()


class RegressorChain:
    """
    Regressor chain for multi-target regression.

    Similar to ClassifierChain but for regression problems.
    """

    def __init__(
        self,
        estimator: Any,
        order: Optional[List[int]] = None,
        random_state: Optional[int] = None,
    ):
        """
        Initialize regressor chain.

        Args:
            estimator: Base regressor
            order: Order of targets in chain
            random_state: Random seed
        """
        self.estimator = estimator
        self.order = order
        self.random_state = random_state
        self._fitted = False
        self._estimators = []
        self._order = None
        self._n_outputs = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> "RegressorChain":
        """Fit the regressor chain."""
        import copy

        X = np.asarray(X)
        y = np.asarray(y)

        if y.ndim == 1:
            y = y.reshape(-1, 1)

        self._n_outputs = y.shape[1]

        if self.order is not None:
            self._order = list(self.order)
        else:
            self._order = list(range(self._n_outputs))
            if self.random_state is not None:
                rng = np.random.default_rng(self.random_state)
                rng.shuffle(self._order)

        self._estimators = []
        X_chain = X.copy()

        for i, target_idx in enumerate(self._order):
            estimator = copy.deepcopy(self.estimator)
            y_target = y[:, target_idx]
            estimator.fit(X_chain, y_target)
            self._estimators.append(estimator)

            if i < self._n_outputs - 1:
                predictions = estimator.predict(X_chain).reshape(-1, 1)
                X_chain = np.hstack([X_chain, predictions])

        self._fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict using the chain."""
        if not self._fitted:
            raise RuntimeError("Must fit before predict")

        X = np.asarray(X)
        n_samples = X.shape[0]

        predictions = np.zeros((n_samples, self._n_outputs))
        X_chain = X.copy()

        for i, (target_idx, estimator) in enumerate(zip(self._order, self._estimators)):
            y_pred = estimator.predict(X_chain)
            predictions[:, target_idx] = y_pred

            if i < self._n_outputs - 1:
                X_chain = np.hstack([X_chain, y_pred.reshape(-1, 1)])

        return predictions

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Compute R² score."""
        y = np.asarray(y)
        if y.ndim == 1:
            y = y.reshape(-1, 1)

        predictions = self.predict(X)
        ss_res = np.sum((y - predictions) ** 2)
        ss_tot = np.sum((y - y.mean(axis=0)) ** 2)
        return 1 - ss_res / ss_tot if ss_tot > 0 else 0.0


class MultiLabelBinarizer:
    """
    Transform between multi-label format and indicator matrix.

    Example:
        >>> mlb = MultiLabelBinarizer()
        >>> y_ind = mlb.fit_transform([['cat', 'dog'], ['dog'], ['cat', 'bird']])
        >>> mlb.classes_  # ['bird', 'cat', 'dog']
        >>> mlb.inverse_transform(y_ind)
    """

    def __init__(self, classes: Optional[List] = None, sparse_output: bool = False):
        """
        Initialize multi-label binarizer.

        Args:
            classes: Fixed set of classes
            sparse_output: Not used in FHE mode
        """
        self.classes = classes
        self.sparse_output = sparse_output
        self.classes_ = None
        self._fitted = False

    def fit(self, y: List[List]) -> "MultiLabelBinarizer":
        """
        Fit the binarizer.

        Args:
            y: List of label lists

        Returns:
            self
        """
        if self.classes is not None:
            self.classes_ = sorted(self.classes)
        else:
            all_labels = set()
            for labels in y:
                all_labels.update(labels)
            self.classes_ = sorted(all_labels)

        self._fitted = True
        return self

    def transform(self, y: List[List]) -> np.ndarray:
        """
        Transform labels to indicator matrix.

        Args:
            y: List of label lists

        Returns:
            Binary indicator matrix
        """
        if not self._fitted:
            raise RuntimeError("Must fit before transform")

        n_samples = len(y)
        n_classes = len(self.classes_)
        class_to_idx = {c: i for i, c in enumerate(self.classes_)}

        indicator = np.zeros((n_samples, n_classes), dtype=int)

        for i, labels in enumerate(y):
            for label in labels:
                if label in class_to_idx:
                    indicator[i, class_to_idx[label]] = 1

        return indicator

    def fit_transform(self, y: List[List]) -> np.ndarray:
        """Fit and transform."""
        return self.fit(y).transform(y)

    def inverse_transform(self, y_indicator: np.ndarray) -> List[List]:
        """
        Transform indicator matrix back to labels.

        Args:
            y_indicator: Binary indicator matrix

        Returns:
            List of label lists
        """
        if not self._fitted:
            raise RuntimeError("Must fit before inverse_transform")

        y_indicator = np.asarray(y_indicator)
        result = []

        for row in y_indicator:
            labels = [self.classes_[i] for i, val in enumerate(row) if val]
            result.append(labels)

        return result


__all__ = [
    "MultiOutputClassifier",
    "MultiOutputRegressor",
    "ClassifierChain",
    "RegressorChain",
    "MultiLabelBinarizer",
    "MultiOutputStrategy",
]

"""Cross-validation utilities for FHE machine learning models.

This module provides cross-validation and model selection utilities.
"""

from dataclasses import dataclass
from typing import Any, Callable, Iterator, Optional, Union
import numpy as np


def train_test_split(
    *arrays,
    test_size: Optional[float] = None,
    train_size: Optional[float] = None,
    random_state: Optional[int] = None,
    shuffle: bool = True,
    stratify: Optional[np.ndarray] = None,
) -> list:
    """Split arrays into random train and test subsets.

    Args:
        *arrays: Sequence of arrays to split.
        test_size: Proportion for test set (default 0.25).
        train_size: Proportion for train set.
        random_state: Random seed.
        shuffle: Whether to shuffle before splitting.
        stratify: Array for stratified splitting.

    Returns:
        List of train/test splits for each input array.

    Example:
        >>> X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    """
    if len(arrays) == 0:
        raise ValueError("At least one array required")

    n_samples = len(arrays[0])

    if test_size is None and train_size is None:
        test_size = 0.25
    elif test_size is None:
        test_size = 1 - train_size
    elif train_size is None:
        train_size = 1 - test_size

    n_test = int(n_samples * test_size)
    n_train = n_samples - n_test

    rng = np.random.RandomState(random_state)

    if stratify is not None:
        # Stratified split
        classes, y_indices = np.unique(stratify, return_inverse=True)
        train_indices = []
        test_indices = []

        for cls in range(len(classes)):
            cls_indices = np.where(y_indices == cls)[0]
            if shuffle:
                rng.shuffle(cls_indices)

            n_cls_test = max(1, int(len(cls_indices) * test_size))
            test_indices.extend(cls_indices[:n_cls_test])
            train_indices.extend(cls_indices[n_cls_test:])

        train_indices = np.array(train_indices)
        test_indices = np.array(test_indices)

        if shuffle:
            rng.shuffle(train_indices)
            rng.shuffle(test_indices)
    else:
        indices = np.arange(n_samples)
        if shuffle:
            rng.shuffle(indices)

        train_indices = indices[:n_train]
        test_indices = indices[n_train:]

    result = []
    for arr in arrays:
        arr = np.asarray(arr)
        result.append(arr[train_indices])
        result.append(arr[test_indices])

    return result


class KFold:
    """K-Fold cross-validator.

    Provides train/test indices to split data into train/test sets.

    Example:
        >>> kf = KFold(n_splits=5)
        >>> for train_idx, test_idx in kf.split(X):
        ...     X_train, X_test = X[train_idx], X[test_idx]
    """

    def __init__(
        self,
        n_splits: int = 5,
        shuffle: bool = False,
        random_state: Optional[int] = None,
    ):
        """Initialize K-Fold.

        Args:
            n_splits: Number of folds.
            shuffle: Whether to shuffle data before splitting.
            random_state: Random seed for shuffling.
        """
        if n_splits < 2:
            raise ValueError("n_splits must be at least 2")

        self.n_splits = n_splits
        self.shuffle = shuffle
        self.random_state = random_state

    def split(
        self,
        X: np.ndarray,
        y: Optional[np.ndarray] = None,
    ) -> Iterator[tuple[np.ndarray, np.ndarray]]:
        """Generate indices to split data into train and test sets.

        Args:
            X: Training data.
            y: Target variable (ignored).

        Yields:
            Tuple of (train_indices, test_indices).
        """
        n_samples = len(X)
        indices = np.arange(n_samples)

        if self.shuffle:
            rng = np.random.RandomState(self.random_state)
            rng.shuffle(indices)

        fold_sizes = np.full(self.n_splits, n_samples // self.n_splits, dtype=int)
        fold_sizes[:n_samples % self.n_splits] += 1

        current = 0
        for fold_size in fold_sizes:
            start, stop = current, current + fold_size
            test_indices = indices[start:stop]
            train_indices = np.concatenate([indices[:start], indices[stop:]])
            yield train_indices, test_indices
            current = stop

    def get_n_splits(self) -> int:
        """Get number of splits."""
        return self.n_splits


class StratifiedKFold:
    """Stratified K-Fold cross-validator.

    Preserves the percentage of samples for each class in each fold.

    Example:
        >>> skf = StratifiedKFold(n_splits=5)
        >>> for train_idx, test_idx in skf.split(X, y):
        ...     X_train, X_test = X[train_idx], X[test_idx]
    """

    def __init__(
        self,
        n_splits: int = 5,
        shuffle: bool = False,
        random_state: Optional[int] = None,
    ):
        """Initialize Stratified K-Fold.

        Args:
            n_splits: Number of folds.
            shuffle: Whether to shuffle data before splitting.
            random_state: Random seed for shuffling.
        """
        if n_splits < 2:
            raise ValueError("n_splits must be at least 2")

        self.n_splits = n_splits
        self.shuffle = shuffle
        self.random_state = random_state

    def split(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> Iterator[tuple[np.ndarray, np.ndarray]]:
        """Generate indices to split data into train and test sets.

        Args:
            X: Training data.
            y: Target variable for stratification.

        Yields:
            Tuple of (train_indices, test_indices).
        """
        y = np.asarray(y).ravel()
        classes, y_indices = np.unique(y, return_inverse=True)
        n_classes = len(classes)

        # Create indices per class
        class_indices = [np.where(y_indices == i)[0] for i in range(n_classes)]

        rng = np.random.RandomState(self.random_state)
        if self.shuffle:
            for idx in class_indices:
                rng.shuffle(idx)

        # Initialize test fold indices for each sample
        test_folds = np.zeros(len(y), dtype=int)

        for cls_idx in class_indices:
            n_cls = len(cls_idx)
            fold_sizes = np.full(self.n_splits, n_cls // self.n_splits, dtype=int)
            fold_sizes[:n_cls % self.n_splits] += 1

            current = 0
            for fold, fold_size in enumerate(fold_sizes):
                test_folds[cls_idx[current:current + fold_size]] = fold
                current += fold_size

        # Yield each fold
        for fold in range(self.n_splits):
            test_indices = np.where(test_folds == fold)[0]
            train_indices = np.where(test_folds != fold)[0]
            yield train_indices, test_indices

    def get_n_splits(self) -> int:
        """Get number of splits."""
        return self.n_splits


def cross_val_score(
    estimator,
    X: np.ndarray,
    y: np.ndarray,
    cv: Union[int, KFold, StratifiedKFold] = 5,
    scoring: Optional[Union[str, Callable]] = None,
) -> np.ndarray:
    """Evaluate estimator by cross-validation.

    Args:
        estimator: Model to evaluate (must have fit and score methods).
        X: Training data.
        y: Target variable.
        cv: Cross-validation splitter or number of folds.
        scoring: Scoring function ('accuracy', 'r2', or callable).

    Returns:
        Array of scores for each fold.

    Example:
        >>> from sdk.models import LogisticRegression
        >>> from sdk.evaluation import cross_val_score
        >>> model = LogisticRegression()
        >>> scores = cross_val_score(model, X, y, cv=5)
        >>> print(f"Accuracy: {scores.mean():.3f} (+/- {scores.std():.3f})")
    """
    X = np.asarray(X)
    y = np.asarray(y)

    # Get CV splitter
    if isinstance(cv, int):
        cv_splitter = KFold(n_splits=cv)
    else:
        cv_splitter = cv

    # Get scoring function
    if scoring is None or scoring == "accuracy":
        def score_func(model, X, y):
            return model.score(X, y)
    elif scoring == "r2":
        def score_func(model, X, y):
            return model.score(X, y)
    elif callable(scoring):
        score_func = scoring
    else:
        def score_func(model, X, y):
            return model.score(X, y)

    scores = []

    for train_idx, test_idx in cv_splitter.split(X, y):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # Clone the estimator (simple approach: create new instance)
        import copy
        model = copy.deepcopy(estimator)

        # Fit and score
        model.fit(X_train, y_train)
        score = score_func(model, X_test, y_test)
        scores.append(score)

    return np.array(scores)


def cross_val_predict(
    estimator,
    X: np.ndarray,
    y: np.ndarray,
    cv: Union[int, KFold, StratifiedKFold] = 5,
    method: str = "predict",
) -> np.ndarray:
    """Generate cross-validated predictions.

    Args:
        estimator: Model to use.
        X: Training data.
        y: Target variable.
        cv: Cross-validation splitter or number of folds.
        method: 'predict' or 'predict_proba'.

    Returns:
        Cross-validated predictions.

    Example:
        >>> from sdk.evaluation import cross_val_predict
        >>> predictions = cross_val_predict(model, X, y, cv=5)
    """
    X = np.asarray(X)
    y = np.asarray(y)

    if isinstance(cv, int):
        cv_splitter = KFold(n_splits=cv)
    else:
        cv_splitter = cv

    # Initialize predictions array
    if method == "predict_proba":
        # Need to determine n_classes first
        n_classes = len(np.unique(y))
        predictions = np.zeros((len(y), n_classes))
    else:
        predictions = np.zeros(len(y))

    for train_idx, test_idx in cv_splitter.split(X, y):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        import copy
        model = copy.deepcopy(estimator)
        model.fit(X_train, y_train)

        if method == "predict_proba":
            pred = model.predict_proba(X_test)
        else:
            pred = model.predict(X_test)

        predictions[test_idx] = pred

    return predictions


@dataclass
class GridSearchResult:
    """Result of grid search."""

    best_params: dict
    best_score: float
    cv_results: list[dict]


class GridSearchCV:
    """Exhaustive search over specified parameter values.

    Example:
        >>> from sdk.models import LogisticRegression
        >>> from sdk.evaluation import GridSearchCV
        >>> param_grid = {'learning_rate': [0.01, 0.1], 'n_epochs': [50, 100]}
        >>> gs = GridSearchCV(LogisticRegression(), param_grid, cv=3)
        >>> gs.fit(X, y)
        >>> print(gs.best_params_)
    """

    def __init__(
        self,
        estimator,
        param_grid: dict,
        cv: Union[int, KFold, StratifiedKFold] = 5,
        scoring: Optional[Union[str, Callable]] = None,
        refit: bool = True,
        verbose: int = 0,
    ):
        """Initialize Grid Search.

        Args:
            estimator: Model to tune.
            param_grid: Dictionary with parameter names and values.
            cv: Cross-validation splitter.
            scoring: Scoring function.
            refit: Whether to refit on full data with best params.
            verbose: Verbosity level.
        """
        self.estimator = estimator
        self.param_grid = param_grid
        self.cv = cv
        self.scoring = scoring
        self.refit = refit
        self.verbose = verbose

        self.best_params_: Optional[dict] = None
        self.best_score_: Optional[float] = None
        self.best_estimator_: Optional[Any] = None
        self.cv_results_: Optional[list] = None

    def _generate_param_combinations(self) -> list[dict]:
        """Generate all parameter combinations."""
        import itertools

        keys = list(self.param_grid.keys())
        values = list(self.param_grid.values())

        combinations = []
        for combo in itertools.product(*values):
            combinations.append(dict(zip(keys, combo)))

        return combinations

    def fit(self, X: np.ndarray, y: np.ndarray) -> "GridSearchCV":
        """Run grid search.

        Args:
            X: Training data.
            y: Target variable.

        Returns:
            self for method chaining.
        """
        X = np.asarray(X)
        y = np.asarray(y)

        param_combinations = self._generate_param_combinations()

        if self.verbose > 0:
            print(f"Fitting {len(param_combinations)} parameter combinations")

        self.cv_results_ = []
        best_score = -np.inf
        best_params = None

        for i, params in enumerate(param_combinations):
            if self.verbose > 0:
                print(f"  [{i+1}/{len(param_combinations)}] {params}")

            # Create estimator with these params
            import copy
            estimator = copy.deepcopy(self.estimator)

            # Set parameters
            if hasattr(estimator, "_config"):
                for key, value in params.items():
                    if hasattr(estimator._config, key):
                        setattr(estimator._config, key, value)

            # Cross-validate
            scores = cross_val_score(estimator, X, y, cv=self.cv, scoring=self.scoring)
            mean_score = scores.mean()
            std_score = scores.std()

            self.cv_results_.append({
                "params": params,
                "mean_score": mean_score,
                "std_score": std_score,
                "scores": scores,
            })

            if self.verbose > 0:
                print(f"      Score: {mean_score:.4f} (+/- {std_score:.4f})")

            if mean_score > best_score:
                best_score = mean_score
                best_params = params

        self.best_params_ = best_params
        self.best_score_ = best_score

        if self.refit:
            import copy
            self.best_estimator_ = copy.deepcopy(self.estimator)
            if hasattr(self.best_estimator_, "_config"):
                for key, value in best_params.items():
                    if hasattr(self.best_estimator_._config, key):
                        setattr(self.best_estimator_._config, key, value)
            self.best_estimator_.fit(X, y)

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict using best estimator."""
        if self.best_estimator_ is None:
            raise RuntimeError("Must fit before predicting")
        return self.best_estimator_.predict(X)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Score using best estimator."""
        if self.best_estimator_ is None:
            raise RuntimeError("Must fit before scoring")
        return self.best_estimator_.score(X, y)

"""
Model Selection module for FHE-ML Platform.

Provides hyperparameter tuning and cross-validation utilities
compatible with FHE-enabled models.
"""

from __future__ import annotations

import copy
import itertools
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple, Union

import numpy as np


@dataclass
class CVResult:
    """Result of cross-validation."""

    scores: np.ndarray
    mean: float
    std: float
    fit_times: np.ndarray
    score_times: np.ndarray


def _check_cv(cv: Union[int, Any]) -> int:
    """Validate and return number of folds."""
    if isinstance(cv, int):
        if cv < 2:
            raise ValueError("cv must be at least 2")
        return cv
    # Could be a CV splitter object
    return 5


def _default_scorer(estimator: Any, X: np.ndarray, y: np.ndarray) -> float:
    """Default scoring using estimator's score method."""
    if hasattr(estimator, "score"):
        return estimator.score(X, y)
    else:
        # For classifiers without score, compute accuracy
        predictions = estimator.predict(X)
        return np.mean(predictions == y)


class KFold:
    """
    K-Fold cross-validator.

    Provides train/test indices to split data in train/test sets.

    Args:
        n_splits: Number of folds. Must be at least 2.
        shuffle: Whether to shuffle the data before splitting.
        random_state: Random seed for shuffling.

    Example:
        >>> kf = KFold(n_splits=5, shuffle=True, random_state=42)
        >>> for train_idx, test_idx in kf.split(X):
        ...     X_train, X_test = X[train_idx], X[test_idx]
    """

    def __init__(
        self,
        n_splits: int = 5,
        shuffle: bool = False,
        random_state: Optional[int] = None,
    ):
        if n_splits < 2:
            raise ValueError("n_splits must be at least 2")
        self.n_splits = n_splits
        self.shuffle = shuffle
        self.random_state = random_state

    def split(
        self, X: np.ndarray, y: Optional[np.ndarray] = None
    ) -> Iterator[Tuple[np.ndarray, np.ndarray]]:
        """
        Generate indices to split data into training and test set.

        Args:
            X: Training data
            y: Target variable (ignored for basic KFold)

        Yields:
            Tuples of (train_indices, test_indices)
        """
        n_samples = len(X)
        indices = np.arange(n_samples)

        if self.shuffle:
            rng = np.random.RandomState(self.random_state)
            rng.shuffle(indices)

        fold_sizes = np.full(self.n_splits, n_samples // self.n_splits, dtype=int)
        fold_sizes[: n_samples % self.n_splits] += 1

        current = 0
        for fold_size in fold_sizes:
            test_indices = indices[current : current + fold_size]
            train_indices = np.concatenate([
                indices[:current],
                indices[current + fold_size:]
            ])
            yield train_indices, test_indices
            current += fold_size

    def get_n_splits(self) -> int:
        """Return the number of splits."""
        return self.n_splits


class StratifiedKFold:
    """
    Stratified K-Fold cross-validator.

    Preserves the percentage of samples for each class in each fold.

    Args:
        n_splits: Number of folds. Must be at least 2.
        shuffle: Whether to shuffle each class's samples before splitting.
        random_state: Random seed for shuffling.

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
        if n_splits < 2:
            raise ValueError("n_splits must be at least 2")
        self.n_splits = n_splits
        self.shuffle = shuffle
        self.random_state = random_state

    def split(
        self, X: np.ndarray, y: np.ndarray
    ) -> Iterator[Tuple[np.ndarray, np.ndarray]]:
        """
        Generate stratified indices to split data.

        Args:
            X: Training data
            y: Target variable (required for stratification)

        Yields:
            Tuples of (train_indices, test_indices)
        """
        y = np.asarray(y)
        classes, y_indices = np.unique(y, return_inverse=True)
        n_classes = len(classes)

        # Get indices for each class
        class_indices = [np.where(y_indices == i)[0] for i in range(n_classes)]

        if self.shuffle:
            rng = np.random.RandomState(self.random_state)
            for idx in class_indices:
                rng.shuffle(idx)

        # Initialize fold indices
        test_folds = [[] for _ in range(self.n_splits)]

        for class_idx in class_indices:
            n_class = len(class_idx)
            fold_sizes = np.full(self.n_splits, n_class // self.n_splits, dtype=int)
            fold_sizes[: n_class % self.n_splits] += 1

            current = 0
            for fold, fold_size in enumerate(fold_sizes):
                test_folds[fold].extend(class_idx[current : current + fold_size])
                current += fold_size

        for test_indices in test_folds:
            test_indices = np.array(test_indices)
            train_indices = np.setdiff1d(np.arange(len(X)), test_indices)
            yield train_indices, test_indices

    def get_n_splits(self) -> int:
        """Return the number of splits."""
        return self.n_splits


class LeaveOneOut:
    """
    Leave-One-Out cross-validator.

    Each sample is used once as a test set while the remaining
    samples form the training set.

    Example:
        >>> loo = LeaveOneOut()
        >>> for train_idx, test_idx in loo.split(X):
        ...     X_train, X_test = X[train_idx], X[test_idx]
    """

    def split(
        self, X: np.ndarray, y: Optional[np.ndarray] = None
    ) -> Iterator[Tuple[np.ndarray, np.ndarray]]:
        """Generate leave-one-out splits."""
        n_samples = len(X)
        indices = np.arange(n_samples)

        for i in range(n_samples):
            test_indices = np.array([i])
            train_indices = np.delete(indices, i)
            yield train_indices, test_indices

    def get_n_splits(self, X: np.ndarray = None) -> int:
        """Return the number of splits."""
        if X is None:
            raise ValueError("X is required to determine n_splits")
        return len(X)


class ShuffleSplit:
    """
    Random permutation cross-validator.

    Yields indices to split data into training and test sets.

    Args:
        n_splits: Number of re-shuffling & splitting iterations.
        test_size: Fraction or absolute number of test samples.
        train_size: Fraction or absolute number of training samples.
        random_state: Random seed.

    Example:
        >>> ss = ShuffleSplit(n_splits=5, test_size=0.2)
        >>> for train_idx, test_idx in ss.split(X):
        ...     X_train, X_test = X[train_idx], X[test_idx]
    """

    def __init__(
        self,
        n_splits: int = 10,
        test_size: Union[float, int] = 0.1,
        train_size: Optional[Union[float, int]] = None,
        random_state: Optional[int] = None,
    ):
        self.n_splits = n_splits
        self.test_size = test_size
        self.train_size = train_size
        self.random_state = random_state

    def split(
        self, X: np.ndarray, y: Optional[np.ndarray] = None
    ) -> Iterator[Tuple[np.ndarray, np.ndarray]]:
        """Generate random train/test splits."""
        n_samples = len(X)
        rng = np.random.RandomState(self.random_state)

        # Determine test size
        if isinstance(self.test_size, float):
            n_test = int(n_samples * self.test_size)
        else:
            n_test = self.test_size

        # Determine train size
        if self.train_size is None:
            n_train = n_samples - n_test
        elif isinstance(self.train_size, float):
            n_train = int(n_samples * self.train_size)
        else:
            n_train = self.train_size

        for _ in range(self.n_splits):
            indices = rng.permutation(n_samples)
            yield indices[:n_train], indices[n_train : n_train + n_test]

    def get_n_splits(self) -> int:
        """Return the number of splits."""
        return self.n_splits


def train_test_split(
    *arrays,
    test_size: Union[float, int] = 0.25,
    train_size: Optional[Union[float, int]] = None,
    random_state: Optional[int] = None,
    shuffle: bool = True,
    stratify: Optional[np.ndarray] = None,
) -> List[np.ndarray]:
    """
    Split arrays into train and test subsets.

    Args:
        *arrays: Sequence of indexables with same length
        test_size: Fraction or number of test samples
        train_size: Fraction or number of train samples
        random_state: Random seed
        shuffle: Whether to shuffle before splitting
        stratify: Array for stratified splitting

    Returns:
        List containing train-test split of inputs

    Example:
        >>> X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    """
    n_samples = len(arrays[0])

    # Validate arrays have same length
    for arr in arrays:
        if len(arr) != n_samples:
            raise ValueError("All arrays must have the same length")

    # Determine sizes
    if isinstance(test_size, float):
        n_test = int(n_samples * test_size)
    else:
        n_test = test_size

    if train_size is None:
        n_train = n_samples - n_test
    elif isinstance(train_size, float):
        n_train = int(n_samples * train_size)
    else:
        n_train = train_size

    # Create indices
    rng = np.random.RandomState(random_state)

    if stratify is not None:
        # Stratified split
        classes, y_indices = np.unique(stratify, return_inverse=True)
        train_indices = []
        test_indices = []

        for class_idx in range(len(classes)):
            class_samples = np.where(y_indices == class_idx)[0]
            if shuffle:
                rng.shuffle(class_samples)

            n_class_test = int(len(class_samples) * n_test / n_samples)
            test_indices.extend(class_samples[:n_class_test])
            train_indices.extend(class_samples[n_class_test:])

        train_indices = np.array(train_indices)
        test_indices = np.array(test_indices)
    else:
        indices = np.arange(n_samples)
        if shuffle:
            rng.shuffle(indices)
        train_indices = indices[:n_train]
        test_indices = indices[n_train : n_train + n_test]

    # Split arrays
    result = []
    for arr in arrays:
        arr = np.asarray(arr)
        result.append(arr[train_indices])
        result.append(arr[test_indices])

    return result


def cross_val_score(
    estimator: Any,
    X: np.ndarray,
    y: np.ndarray,
    cv: Union[int, Any] = 5,
    scoring: Optional[Callable] = None,
    fit_params: Optional[Dict[str, Any]] = None,
) -> np.ndarray:
    """
    Evaluate a score by cross-validation.

    Args:
        estimator: The object to use to fit the data
        X: Training data
        y: Target values
        cv: Number of folds or cross-validator object
        scoring: Scoring function (callable) or None for default
        fit_params: Parameters to pass to fit method

    Returns:
        Array of scores, one per fold

    Example:
        >>> scores = cross_val_score(clf, X, y, cv=5)
        >>> print(f"Accuracy: {scores.mean():.2f} (+/- {scores.std():.2f})")
    """
    X = np.asarray(X)
    y = np.asarray(y)
    fit_params = fit_params or {}

    if scoring is None:
        scoring = _default_scorer

    # Get CV splitter
    if isinstance(cv, int):
        cv_splitter = KFold(n_splits=cv)
    else:
        cv_splitter = cv

    scores = []
    for train_idx, test_idx in cv_splitter.split(X, y):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # Clone estimator
        est = copy.deepcopy(estimator)
        est.fit(X_train, y_train, **fit_params)

        score = scoring(est, X_test, y_test)
        scores.append(score)

    return np.array(scores)


def cross_validate(
    estimator: Any,
    X: np.ndarray,
    y: np.ndarray,
    cv: Union[int, Any] = 5,
    scoring: Optional[Callable] = None,
    fit_params: Optional[Dict[str, Any]] = None,
    return_train_score: bool = False,
    return_estimator: bool = False,
) -> Dict[str, Any]:
    """
    Evaluate metric(s) by cross-validation with more detailed results.

    Args:
        estimator: The object to use to fit the data
        X: Training data
        y: Target values
        cv: Number of folds or cross-validator object
        scoring: Scoring function
        fit_params: Parameters to pass to fit method
        return_train_score: Whether to include training scores
        return_estimator: Whether to return fitted estimators

    Returns:
        Dictionary with test_score, fit_time, score_time, etc.

    Example:
        >>> results = cross_validate(clf, X, y, cv=5, return_train_score=True)
        >>> print(results['test_score'])
    """
    X = np.asarray(X)
    y = np.asarray(y)
    fit_params = fit_params or {}

    if scoring is None:
        scoring = _default_scorer

    # Get CV splitter
    if isinstance(cv, int):
        cv_splitter = KFold(n_splits=cv)
    else:
        cv_splitter = cv

    results = {
        "test_score": [],
        "fit_time": [],
        "score_time": [],
    }
    if return_train_score:
        results["train_score"] = []
    if return_estimator:
        results["estimator"] = []

    for train_idx, test_idx in cv_splitter.split(X, y):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # Clone and fit
        est = copy.deepcopy(estimator)

        start_time = time.time()
        est.fit(X_train, y_train, **fit_params)
        fit_time = time.time() - start_time

        # Score
        start_time = time.time()
        test_score = scoring(est, X_test, y_test)
        score_time = time.time() - start_time

        results["test_score"].append(test_score)
        results["fit_time"].append(fit_time)
        results["score_time"].append(score_time)

        if return_train_score:
            train_score = scoring(est, X_train, y_train)
            results["train_score"].append(train_score)

        if return_estimator:
            results["estimator"].append(est)

    # Convert to arrays
    for key in results:
        if key != "estimator":
            results[key] = np.array(results[key])

    return results


class ParameterGrid:
    """
    Grid of parameters with a discrete number of values for each.

    Args:
        param_grid: Dictionary mapping parameter names to sequences of values

    Example:
        >>> grid = ParameterGrid({'C': [1, 10], 'kernel': ['rbf', 'linear']})
        >>> list(grid)
        [{'C': 1, 'kernel': 'rbf'}, {'C': 1, 'kernel': 'linear'}, ...]
    """

    def __init__(self, param_grid: Dict[str, List[Any]]):
        self.param_grid = param_grid

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        keys = list(self.param_grid.keys())
        values = list(self.param_grid.values())

        for combo in itertools.product(*values):
            yield dict(zip(keys, combo))

    def __len__(self) -> int:
        product = 1
        for values in self.param_grid.values():
            product *= len(values)
        return product


class ParameterSampler:
    """
    Generator on parameters sampled from given distributions.

    Args:
        param_distributions: Dictionary mapping parameter names to
            distributions or lists of values
        n_iter: Number of parameter settings to sample
        random_state: Random seed

    Example:
        >>> from scipy.stats import uniform
        >>> sampler = ParameterSampler({'C': uniform(1, 10)}, n_iter=10)
    """

    def __init__(
        self,
        param_distributions: Dict[str, Any],
        n_iter: int,
        random_state: Optional[int] = None,
    ):
        self.param_distributions = param_distributions
        self.n_iter = n_iter
        self.random_state = random_state

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        rng = np.random.RandomState(self.random_state)

        for _ in range(self.n_iter):
            params = {}
            for key, dist in self.param_distributions.items():
                if hasattr(dist, "rvs"):
                    # Scipy distribution
                    params[key] = dist.rvs(random_state=rng)
                elif isinstance(dist, (list, tuple, np.ndarray)):
                    # List of values
                    params[key] = dist[rng.randint(len(dist))]
                else:
                    params[key] = dist
            yield params

    def __len__(self) -> int:
        return self.n_iter


class GridSearchCV:
    """
    Exhaustive search over specified parameter values for an estimator.

    Args:
        estimator: Estimator object
        param_grid: Dictionary or list of dictionaries with parameter names
            as keys and lists of parameter settings to try as values
        scoring: Scoring function
        cv: Number of folds or cross-validator
        refit: Whether to refit with best parameters on whole dataset
        verbose: Verbosity level
        n_jobs: Not used (for sklearn compatibility)

    Example:
        >>> param_grid = {'C': [0.1, 1, 10], 'kernel': ['rbf', 'linear']}
        >>> grid = GridSearchCV(SVC(), param_grid, cv=5)
        >>> grid.fit(X, y)
        >>> print(grid.best_params_)
    """

    def __init__(
        self,
        estimator: Any,
        param_grid: Union[Dict[str, List[Any]], List[Dict[str, List[Any]]]],
        scoring: Optional[Callable] = None,
        cv: Union[int, Any] = 5,
        refit: bool = True,
        verbose: int = 0,
        n_jobs: Optional[int] = None,
    ):
        self.estimator = estimator
        self.param_grid = param_grid
        self.scoring = scoring or _default_scorer
        self.cv = cv
        self.refit = refit
        self.verbose = verbose
        self.n_jobs = n_jobs

        # Results
        self.best_params_: Optional[Dict[str, Any]] = None
        self.best_score_: Optional[float] = None
        self.best_estimator_: Optional[Any] = None
        self.cv_results_: Optional[Dict[str, Any]] = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> "GridSearchCV":
        """
        Run fit with all sets of parameters.

        Args:
            X: Training data
            y: Target values

        Returns:
            self
        """
        X = np.asarray(X)
        y = np.asarray(y)

        # Create parameter grid
        if isinstance(self.param_grid, list):
            all_params = []
            for grid in self.param_grid:
                all_params.extend(list(ParameterGrid(grid)))
        else:
            all_params = list(ParameterGrid(self.param_grid))

        # Initialize results
        results = {
            "params": [],
            "mean_test_score": [],
            "std_test_score": [],
            "rank_test_score": [],
        }

        best_score = float("-inf")
        best_params = None

        for i, params in enumerate(all_params):
            if self.verbose:
                print(f"Testing params {i + 1}/{len(all_params)}: {params}")

            # Clone estimator and set params
            est = copy.deepcopy(self.estimator)
            for key, value in params.items():
                setattr(est, key, value)

            # Cross-validate
            scores = cross_val_score(est, X, y, cv=self.cv, scoring=self.scoring)
            mean_score = scores.mean()
            std_score = scores.std()

            results["params"].append(params)
            results["mean_test_score"].append(mean_score)
            results["std_test_score"].append(std_score)

            if mean_score > best_score:
                best_score = mean_score
                best_params = params

        # Compute ranks
        scores = np.array(results["mean_test_score"])
        results["rank_test_score"] = (scores.max() - scores).argsort().argsort() + 1

        self.cv_results_ = results
        self.best_params_ = best_params
        self.best_score_ = best_score

        # Refit on full data
        if self.refit:
            self.best_estimator_ = copy.deepcopy(self.estimator)
            for key, value in best_params.items():
                setattr(self.best_estimator_, key, value)
            self.best_estimator_.fit(X, y)

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict using the best estimator."""
        if self.best_estimator_ is None:
            raise ValueError("Call fit before predict")
        return self.best_estimator_.predict(X)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Score using the best estimator."""
        if self.best_estimator_ is None:
            raise ValueError("Call fit before score")
        return self.scoring(self.best_estimator_, X, y)


class RandomizedSearchCV:
    """
    Randomized search on hyperparameters.

    Args:
        estimator: Estimator object
        param_distributions: Dictionary with parameter names as keys and
            distributions or lists to sample from
        n_iter: Number of parameter settings that are sampled
        scoring: Scoring function
        cv: Number of folds or cross-validator
        refit: Whether to refit with best parameters
        verbose: Verbosity level
        random_state: Random seed

    Example:
        >>> param_dist = {'C': uniform(0.1, 10), 'kernel': ['rbf', 'linear']}
        >>> search = RandomizedSearchCV(SVC(), param_dist, n_iter=20, cv=5)
        >>> search.fit(X, y)
    """

    def __init__(
        self,
        estimator: Any,
        param_distributions: Dict[str, Any],
        n_iter: int = 10,
        scoring: Optional[Callable] = None,
        cv: Union[int, Any] = 5,
        refit: bool = True,
        verbose: int = 0,
        random_state: Optional[int] = None,
        n_jobs: Optional[int] = None,
    ):
        self.estimator = estimator
        self.param_distributions = param_distributions
        self.n_iter = n_iter
        self.scoring = scoring or _default_scorer
        self.cv = cv
        self.refit = refit
        self.verbose = verbose
        self.random_state = random_state
        self.n_jobs = n_jobs

        # Results
        self.best_params_: Optional[Dict[str, Any]] = None
        self.best_score_: Optional[float] = None
        self.best_estimator_: Optional[Any] = None
        self.cv_results_: Optional[Dict[str, Any]] = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> "RandomizedSearchCV":
        """
        Run randomized search.

        Args:
            X: Training data
            y: Target values

        Returns:
            self
        """
        X = np.asarray(X)
        y = np.asarray(y)

        # Sample parameters
        sampler = ParameterSampler(
            self.param_distributions,
            n_iter=self.n_iter,
            random_state=self.random_state,
        )
        all_params = list(sampler)

        # Initialize results
        results = {
            "params": [],
            "mean_test_score": [],
            "std_test_score": [],
            "rank_test_score": [],
        }

        best_score = float("-inf")
        best_params = None

        for i, params in enumerate(all_params):
            if self.verbose:
                print(f"Testing params {i + 1}/{len(all_params)}: {params}")

            # Clone estimator and set params
            est = copy.deepcopy(self.estimator)
            for key, value in params.items():
                setattr(est, key, value)

            # Cross-validate
            scores = cross_val_score(est, X, y, cv=self.cv, scoring=self.scoring)
            mean_score = scores.mean()
            std_score = scores.std()

            results["params"].append(params)
            results["mean_test_score"].append(mean_score)
            results["std_test_score"].append(std_score)

            if mean_score > best_score:
                best_score = mean_score
                best_params = params

        # Compute ranks
        scores = np.array(results["mean_test_score"])
        results["rank_test_score"] = (scores.max() - scores).argsort().argsort() + 1

        self.cv_results_ = results
        self.best_params_ = best_params
        self.best_score_ = best_score

        # Refit on full data
        if self.refit:
            self.best_estimator_ = copy.deepcopy(self.estimator)
            for key, value in best_params.items():
                setattr(self.best_estimator_, key, value)
            self.best_estimator_.fit(X, y)

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict using the best estimator."""
        if self.best_estimator_ is None:
            raise ValueError("Call fit before predict")
        return self.best_estimator_.predict(X)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Score using the best estimator."""
        if self.best_estimator_ is None:
            raise ValueError("Call fit before score")
        return self.scoring(self.best_estimator_, X, y)


__all__ = [
    # Splitters
    "KFold",
    "StratifiedKFold",
    "LeaveOneOut",
    "ShuffleSplit",
    # Functions
    "train_test_split",
    "cross_val_score",
    "cross_validate",
    # Parameter iteration
    "ParameterGrid",
    "ParameterSampler",
    # Search
    "GridSearchCV",
    "RandomizedSearchCV",
]

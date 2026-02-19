"""
Cross-Validation Utilities for FHE-ML Platform.
"""

import copy
import time
from typing import Any, Callable, Generator, Optional, Tuple

import numpy as np


class KFold:
    """K-Fold cross-validator."""

    def __init__(
        self, n_splits: int = 5, shuffle: bool = False, random_state: Optional[int] = None
    ):
        self.n_splits = n_splits
        self.shuffle = shuffle
        self.random_state = random_state

    def split(
        self, X: np.ndarray, y=None, groups=None
    ) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
        n_samples = len(X)
        indices = np.arange(n_samples)
        if self.shuffle:
            if self.random_state is not None:
                np.random.seed(self.random_state)
            np.random.shuffle(indices)
        fold_sizes = np.full(self.n_splits, n_samples // self.n_splits, dtype=int)
        fold_sizes[: n_samples % self.n_splits] += 1
        current = 0
        for fold_size in fold_sizes:
            test_idx = indices[current : current + fold_size]
            train_idx = np.concatenate([indices[:current], indices[current + fold_size :]])
            yield train_idx, test_idx
            current += fold_size

    def get_n_splits(self, X=None, y=None, groups=None) -> int:
        return self.n_splits


class StratifiedKFold:
    """Stratified K-Fold preserving class proportions."""

    def __init__(
        self, n_splits: int = 5, shuffle: bool = False, random_state: Optional[int] = None
    ):
        self.n_splits = n_splits
        self.shuffle = shuffle
        self.random_state = random_state

    def split(
        self, X: np.ndarray, y: np.ndarray, groups=None
    ) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
        classes = np.unique(y)
        if self.shuffle and self.random_state is not None:
            np.random.seed(self.random_state)
        class_indices = {}
        for c in classes:
            idx = np.where(y == c)[0]
            if self.shuffle:
                np.random.shuffle(idx)
            class_indices[c] = idx
        test_folds = [[] for _ in range(self.n_splits)]
        for c in classes:
            idx = class_indices[c]
            fold_sizes = np.full(self.n_splits, len(idx) // self.n_splits)
            fold_sizes[: len(idx) % self.n_splits] += 1
            current = 0
            for fold_id, size in enumerate(fold_sizes):
                test_folds[fold_id].extend(idx[current : current + size])
                current += size
        all_indices = np.arange(len(y))
        for test_idx in test_folds:
            test_idx = np.array(test_idx)
            train_idx = np.setdiff1d(all_indices, test_idx)
            yield train_idx, test_idx

    def get_n_splits(self, X=None, y=None, groups=None) -> int:
        return self.n_splits


class LeaveOneOut:
    """Leave-One-Out cross-validator."""

    def split(
        self, X: np.ndarray, y=None, groups=None
    ) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
        n_samples = len(X)
        indices = np.arange(n_samples)
        for i in range(n_samples):
            yield np.delete(indices, i), np.array([i])

    def get_n_splits(self, X=None, y=None, groups=None) -> int:
        return len(X) if X is not None else 0


class TimeSeriesSplit:
    """Time Series cross-validator respecting temporal order."""

    def __init__(
        self,
        n_splits: int = 5,
        max_train_size: Optional[int] = None,
        test_size: Optional[int] = None,
        gap: int = 0,
    ):
        self.n_splits = n_splits
        self.max_train_size = max_train_size
        self.test_size = test_size
        self.gap = gap

    def split(
        self, X: np.ndarray, y=None, groups=None
    ) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
        n_samples = len(X)
        indices = np.arange(n_samples)
        test_size = self.test_size if self.test_size else n_samples // (self.n_splits + 1)
        test_starts = range(
            test_size + self.gap,
            n_samples - test_size + 1,
            (n_samples - test_size - self.gap) // self.n_splits,
        )
        for test_start in list(test_starts)[-self.n_splits :]:
            train_end = test_start - self.gap
            train_start = max(0, train_end - self.max_train_size) if self.max_train_size else 0
            yield indices[train_start:train_end], indices[test_start : test_start + test_size]

    def get_n_splits(self, X=None, y=None, groups=None) -> int:
        return self.n_splits


class GroupKFold:
    """K-Fold with non-overlapping groups."""

    def __init__(self, n_splits: int = 5):
        self.n_splits = n_splits

    def split(
        self, X: np.ndarray, y=None, groups: np.ndarray = None
    ) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
        if groups is None:
            raise ValueError("Groups must be provided")
        unique_groups = np.unique(groups)
        n_groups = len(unique_groups)
        fold_sizes = np.full(self.n_splits, n_groups // self.n_splits)
        fold_sizes[: n_groups % self.n_splits] += 1
        group_to_fold = {}
        current = 0
        for fold_id, size in enumerate(fold_sizes):
            for g in unique_groups[current : current + size]:
                group_to_fold[g] = fold_id
            current += size
        for fold_id in range(self.n_splits):
            test_mask = np.array([group_to_fold[g] == fold_id for g in groups])
            yield np.where(~test_mask)[0], np.where(test_mask)[0]

    def get_n_splits(self, X=None, y=None, groups=None) -> int:
        return self.n_splits


class RepeatedKFold:
    """Repeated K-Fold cross-validator."""

    def __init__(self, n_splits: int = 5, n_repeats: int = 10, random_state: Optional[int] = None):
        self.n_splits = n_splits
        self.n_repeats = n_repeats
        self.random_state = random_state

    def split(
        self, X: np.ndarray, y=None, groups=None
    ) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
        for repeat in range(self.n_repeats):
            seed = self.random_state + repeat if self.random_state else None
            kfold = KFold(n_splits=self.n_splits, shuffle=True, random_state=seed)
            yield from kfold.split(X, y, groups)

    def get_n_splits(self, X=None, y=None, groups=None) -> int:
        return self.n_splits * self.n_repeats


def cross_val_score(
    estimator: Any, X: np.ndarray, y: np.ndarray, cv: int = 5, scoring: Callable = None, groups=None
) -> np.ndarray:
    """Evaluate estimator using cross-validation."""
    X, y = np.asarray(X), np.asarray(y)
    if scoring is None:

        def scoring(y_true, y_pred):
            return np.mean(y_true == y_pred)

    cv_obj = KFold(n_splits=cv, shuffle=True, random_state=42) if isinstance(cv, int) else cv
    scores = []
    for train_idx, test_idx in cv_obj.split(X, y, groups):
        model = copy.deepcopy(estimator)
        model.fit(X[train_idx], y[train_idx])
        scores.append(scoring(y[test_idx], model.predict(X[test_idx])))
    return np.array(scores)


def cross_validate(
    estimator: Any,
    X: np.ndarray,
    y: np.ndarray,
    cv: int = 5,
    scoring: Callable = None,
    groups=None,
    return_train_score: bool = False,
    return_estimator: bool = False,
) -> dict:
    """Evaluate estimator and return detailed results."""
    X, y = np.asarray(X), np.asarray(y)
    if scoring is None:

        def scoring(y_true, y_pred):
            return np.mean(y_true == y_pred)

    cv_obj = KFold(n_splits=cv, shuffle=True, random_state=42) if isinstance(cv, int) else cv
    results = {"test_score": [], "fit_time": [], "score_time": []}
    if return_train_score:
        results["train_score"] = []
    if return_estimator:
        results["estimator"] = []
    for train_idx, test_idx in cv_obj.split(X, y, groups):
        model = copy.deepcopy(estimator)
        start = time.time()
        model.fit(X[train_idx], y[train_idx])
        results["fit_time"].append(time.time() - start)
        start = time.time()
        y_pred = model.predict(X[test_idx])
        results["score_time"].append(time.time() - start)
        results["test_score"].append(scoring(y[test_idx], y_pred))
        if return_train_score:
            results["train_score"].append(scoring(y[train_idx], model.predict(X[train_idx])))
        if return_estimator:
            results["estimator"].append(model)
    for key in ["test_score", "fit_time", "score_time"]:
        results[key] = np.array(results[key])
    if return_train_score:
        results["train_score"] = np.array(results["train_score"])
    return results


def learning_curve(
    estimator: Any,
    X: np.ndarray,
    y: np.ndarray,
    train_sizes: np.ndarray = None,
    cv: int = 5,
    scoring: Callable = None,
    random_state: int = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Generate learning curve data."""
    X, y = np.asarray(X), np.asarray(y)
    if train_sizes is None:
        train_sizes = np.linspace(0.1, 1.0, 5)
    if scoring is None:

        def scoring(y_true, y_pred):
            return np.mean(y_true == y_pred)

    if random_state:
        np.random.seed(random_state)
    n_samples = len(X)
    train_sizes_abs = (
        (train_sizes * n_samples).astype(int)
        if np.all(train_sizes <= 1.0)
        else train_sizes.astype(int)
    )
    cv_obj = KFold(n_splits=cv, shuffle=True, random_state=random_state)
    train_scores = np.zeros((len(train_sizes_abs), cv))
    test_scores = np.zeros((len(train_sizes_abs), cv))
    for size_idx, size in enumerate(train_sizes_abs):
        for fold_idx, (train_idx, test_idx) in enumerate(cv_obj.split(X, y)):
            train_idx = train_idx[:size] if len(train_idx) > size else train_idx
            model = copy.deepcopy(estimator)
            model.fit(X[train_idx], y[train_idx])
            train_scores[size_idx, fold_idx] = scoring(y[train_idx], model.predict(X[train_idx]))
            test_scores[size_idx, fold_idx] = scoring(y[test_idx], model.predict(X[test_idx]))
    return train_sizes_abs, train_scores, test_scores


def cross_val_predict(
    estimator: Any,
    X: np.ndarray,
    y: np.ndarray,
    cv: int = 5,
    groups=None,
) -> np.ndarray:
    """Generate cross-validated predictions for each input data point."""
    X, y = np.asarray(X), np.asarray(y)
    predictions = np.zeros_like(y, dtype=float)
    cv_obj = KFold(n_splits=cv, shuffle=False)
    for train_idx, test_idx in cv_obj.split(X, y, groups):
        model = copy.deepcopy(estimator)
        model.fit(X[train_idx], y[train_idx])
        predictions[test_idx] = model.predict(X[test_idx])
    return predictions


def train_test_split(
    *arrays,
    test_size: float = 0.25,
    train_size: float = None,
    random_state: int = None,
    shuffle: bool = True,
    stratify=None,
):
    """Split arrays into random train and test subsets."""
    if len(arrays) == 0:
        raise ValueError("At least one array required")

    n_samples = len(arrays[0])
    if random_state is not None:
        np.random.seed(random_state)

    indices = np.arange(n_samples)
    if shuffle:
        np.random.shuffle(indices)

    if train_size is None:
        train_size = 1.0 - test_size

    n_train = int(n_samples * train_size)
    train_idx = indices[:n_train]
    test_idx = indices[n_train:]

    result = []
    for arr in arrays:
        arr = np.asarray(arr)
        result.append(arr[train_idx])
        result.append(arr[test_idx])

    return tuple(result)


class GridSearchCV:
    """Exhaustive search over specified parameter values for an estimator."""

    def __init__(
        self,
        estimator: Any,
        param_grid: dict,
        scoring: Callable = None,
        cv: int = 5,
        refit: bool = True,
        verbose: int = 0,
    ):
        self.estimator = estimator
        self.param_grid = param_grid
        self.scoring = scoring or (lambda y_true, y_pred: np.mean(y_true == y_pred))
        self.cv = cv
        self.refit = refit
        self.verbose = verbose
        self.best_params_ = None
        self.best_score_ = None
        self.best_estimator_ = None
        self.cv_results_ = None

    def fit(self, X: np.ndarray, y: np.ndarray):
        """Run fit with all sets of parameters."""
        X, y = np.asarray(X), np.asarray(y)

        # Generate all parameter combinations
        import itertools

        keys = list(self.param_grid.keys())
        values = list(self.param_grid.values())
        param_combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]

        best_score = -np.inf
        results = {"params": [], "mean_test_score": [], "std_test_score": []}

        for params in param_combinations:
            model = copy.deepcopy(self.estimator)
            for key, val in params.items():
                setattr(model, key, val)

            scores = cross_val_score(model, X, y, cv=self.cv, scoring=self.scoring)
            mean_score = np.mean(scores)

            results["params"].append(params)
            results["mean_test_score"].append(mean_score)
            results["std_test_score"].append(np.std(scores))

            if mean_score > best_score:
                best_score = mean_score
                self.best_params_ = params
                self.best_score_ = best_score

        self.cv_results_ = results

        if self.refit:
            self.best_estimator_ = copy.deepcopy(self.estimator)
            for key, val in self.best_params_.items():
                setattr(self.best_estimator_, key, val)
            self.best_estimator_.fit(X, y)

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict using the best estimator."""
        if self.best_estimator_ is None:
            raise ValueError("GridSearchCV not fitted yet")
        return self.best_estimator_.predict(X)

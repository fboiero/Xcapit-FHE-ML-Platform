"""FHE-compatible Hyperparameter Tuning.

This module provides hyperparameter optimization methods that work with
FHE-compatible models. Includes RandomizedSearchCV and Bayesian optimization.
"""

import copy
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Union

import numpy as np

from .cross_validation import cross_val_score


@dataclass
class SearchResult:
    """Result of hyperparameter search."""

    best_params: Dict[str, Any]
    best_score: float
    best_estimator: Any
    cv_results: Dict[str, Any]
    n_iterations: int


class ParameterSampler:
    """Sample parameters from distributions.

    Supports various distribution types for random search.
    """

    def __init__(
        self,
        param_distributions: Dict[str, Any],
        n_iter: int,
        random_state: Optional[int] = None,
    ):
        self.param_distributions = param_distributions
        self.n_iter = n_iter
        self.rng = np.random.default_rng(random_state)

    def __iter__(self):
        for _ in range(self.n_iter):
            params = {}
            for name, dist in self.param_distributions.items():
                params[name] = self._sample(dist)
            yield params

    def _sample(self, dist: Any) -> Any:
        """Sample a single value from a distribution."""
        if isinstance(dist, list):
            # List of choices
            return self.rng.choice(dist)
        elif hasattr(dist, "rvs"):
            # scipy-like distribution
            return dist.rvs(random_state=self.rng)
        elif isinstance(dist, dict):
            # Dict specifying distribution
            dist_type = dist.get("type", "uniform")
            if dist_type == "uniform":
                low = dist.get("low", 0)
                high = dist.get("high", 1)
                return self.rng.uniform(low, high)
            elif dist_type == "log_uniform":
                low = np.log(dist.get("low", 1e-4))
                high = np.log(dist.get("high", 1))
                return np.exp(self.rng.uniform(low, high))
            elif dist_type == "int_uniform":
                low = dist.get("low", 0)
                high = dist.get("high", 10)
                return self.rng.integers(low, high + 1)
            elif dist_type == "choice":
                choices = dist.get("choices", [])
                return self.rng.choice(choices)
            elif dist_type == "normal":
                mean = dist.get("mean", 0)
                std = dist.get("std", 1)
                return self.rng.normal(mean, std)
        elif callable(dist):
            # Callable that returns a value
            return dist()
        else:
            # Single value
            return dist


class RandomizedSearchCV:
    """Randomized search over hyperparameters.

    Samples from parameter distributions and evaluates using cross-validation.
    More efficient than grid search for large parameter spaces.

    Example:
        >>> from xcapit_fhe import RandomizedSearchCV, LogisticRegression
        >>> param_dist = {
        ...     'learning_rate': {'type': 'log_uniform', 'low': 1e-4, 'high': 1e-1},
        ...     'max_iter': {'type': 'int_uniform', 'low': 100, 'high': 1000},
        ... }
        >>> search = RandomizedSearchCV(LogisticRegression(), param_dist, n_iter=20)
        >>> search.fit(X, y)
        >>> print(search.best_params_)
    """

    def __init__(
        self,
        estimator: Any,
        param_distributions: Dict[str, Any],
        n_iter: int = 10,
        scoring: Optional[Union[str, Callable]] = None,
        cv: int = 5,
        refit: bool = True,
        random_state: Optional[int] = None,
        verbose: int = 0,
        n_jobs: int = 1,
        return_train_score: bool = False,
    ):
        self.estimator = estimator
        self.param_distributions = param_distributions
        self.n_iter = n_iter
        self.scoring = scoring
        self.cv = cv
        self.refit = refit
        self.random_state = random_state
        self.verbose = verbose
        self.n_jobs = n_jobs
        self.return_train_score = return_train_score

        # Results
        self.best_params_ = None
        self.best_score_ = None
        self.best_estimator_ = None
        self.cv_results_ = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> "RandomizedSearchCV":
        """Run randomized search.

        Args:
            X: Training data
            y: Target values

        Returns:
            self
        """
        X = np.asarray(X)
        y = np.asarray(y)

        # Initialize results
        results = {
            "params": [],
            "mean_test_score": [],
            "std_test_score": [],
            "rank_test_score": [],
        }

        if self.return_train_score:
            results["mean_train_score"] = []
            results["std_train_score"] = []

        # Sample parameters
        sampler = ParameterSampler(
            self.param_distributions,
            self.n_iter,
            self.random_state,
        )

        best_score = -np.inf
        best_params = None

        for i, params in enumerate(sampler):
            if self.verbose > 0:
                print(f"Iteration {i + 1}/{self.n_iter}: {params}")

            # Create estimator with these parameters
            estimator = copy.deepcopy(self.estimator)
            for param, value in params.items():
                setattr(estimator, param, value)

            # Cross-validation
            try:
                scores = cross_val_score(
                    estimator,
                    X,
                    y,
                    cv=self.cv,
                    scoring=self.scoring,
                )

                mean_score = np.mean(scores)
                std_score = np.std(scores)

                results["params"].append(params)
                results["mean_test_score"].append(mean_score)
                results["std_test_score"].append(std_score)

                if mean_score > best_score:
                    best_score = mean_score
                    best_params = params

                if self.verbose > 0:
                    print(f"  Score: {mean_score:.4f} (+/- {std_score:.4f})")

            except Exception as e:
                if self.verbose > 0:
                    print(f"  Failed: {e}")
                results["params"].append(params)
                results["mean_test_score"].append(np.nan)
                results["std_test_score"].append(np.nan)

        # Compute rankings
        scores = np.array(results["mean_test_score"])
        valid_mask = ~np.isnan(scores)
        ranks = np.zeros_like(scores, dtype=int)
        ranks[valid_mask] = (len(scores) - np.argsort(np.argsort(scores[valid_mask])))[
            : np.sum(valid_mask)
        ]
        ranks[~valid_mask] = len(scores)
        results["rank_test_score"] = ranks.tolist()

        self.cv_results_ = results
        self.best_params_ = best_params
        self.best_score_ = best_score

        # Refit with best parameters
        if self.refit and best_params is not None:
            self.best_estimator_ = copy.deepcopy(self.estimator)
            for param, value in best_params.items():
                setattr(self.best_estimator_, param, value)
            self.best_estimator_.fit(X, y)

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict using best estimator."""
        if self.best_estimator_ is None:
            raise ValueError("Must call fit with refit=True before predict")
        return self.best_estimator_.predict(X)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Score using best estimator."""
        if self.best_estimator_ is None:
            raise ValueError("Must call fit with refit=True before score")
        return self.best_estimator_.score(X, y)


class BayesianOptimization:
    """Bayesian optimization for hyperparameter tuning.

    Uses Gaussian Process surrogate model to guide search.
    More sample-efficient than random search for expensive evaluations.

    FHE Compatibility:
    - The optimization itself doesn't need FHE
    - The estimator being tuned should be FHE-compatible

    Example:
        >>> from xcapit_fhe import BayesianOptimization, LogisticRegression
        >>> param_bounds = {
        ...     'learning_rate': (1e-4, 1e-1, 'log'),
        ...     'max_iter': (100, 1000, 'int'),
        ... }
        >>> opt = BayesianOptimization(LogisticRegression(), param_bounds, n_iter=20)
        >>> opt.fit(X, y)
    """

    def __init__(
        self,
        estimator: Any,
        param_bounds: Dict[str, tuple],
        n_iter: int = 25,
        n_initial_points: int = 5,
        scoring: Optional[Union[str, Callable]] = None,
        cv: int = 5,
        acquisition: str = "ei",  # "ei", "ucb", "poi"
        kappa: float = 2.576,  # For UCB
        xi: float = 0.01,  # For EI/POI
        random_state: Optional[int] = None,
        verbose: int = 0,
    ):
        self.estimator = estimator
        self.param_bounds = param_bounds
        self.n_iter = n_iter
        self.n_initial_points = n_initial_points
        self.scoring = scoring
        self.cv = cv
        self.acquisition = acquisition
        self.kappa = kappa
        self.xi = xi
        self.random_state = random_state
        self.verbose = verbose

        self.rng = np.random.default_rng(random_state)

        # Results
        self.best_params_ = None
        self.best_score_ = None
        self.best_estimator_ = None
        self.history_ = []

        # GP surrogate
        self._X_observed = []
        self._y_observed = []

    def _transform_params(self, params: Dict[str, float]) -> Dict[str, Any]:
        """Transform normalized params to actual values."""
        actual = {}
        for name, (low, high, *scale) in self.param_bounds.items():
            x = params[name]
            scale_type = scale[0] if scale else "linear"

            if scale_type == "log":
                value = np.exp(np.log(low) + x * (np.log(high) - np.log(low)))
            else:
                value = low + x * (high - low)

            if scale_type == "int" or (len(scale) > 0 and scale[0] == "int"):
                value = int(round(value))

            actual[name] = value

        return actual

    def _inverse_transform(self, params: Dict[str, Any]) -> np.ndarray:
        """Transform actual params to normalized [0, 1] space."""
        x = []
        for name, (low, high, *scale) in self.param_bounds.items():
            value = params[name]
            scale_type = scale[0] if scale else "linear"

            if scale_type == "log":
                x_norm = (np.log(value) - np.log(low)) / (np.log(high) - np.log(low))
            else:
                x_norm = (value - low) / (high - low)

            x.append(x_norm)

        return np.array(x)

    def _rbf_kernel(self, X1: np.ndarray, X2: np.ndarray, length_scale: float = 1.0) -> np.ndarray:
        """RBF kernel for Gaussian Process."""
        sq_dists = np.sum(X1**2, axis=1, keepdims=True) + np.sum(X2**2, axis=1) - 2 * X1 @ X2.T
        return np.exp(-0.5 * sq_dists / length_scale**2)

    def _gp_predict(self, X_new: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Predict mean and std using Gaussian Process."""
        if len(self._X_observed) == 0:
            return np.zeros(len(X_new)), np.ones(len(X_new))

        X_obs = np.array(self._X_observed)
        y_obs = np.array(self._y_observed)

        # Normalize y
        y_mean = np.mean(y_obs)
        y_std = np.std(y_obs) + 1e-8
        y_norm = (y_obs - y_mean) / y_std

        # Kernel matrices
        length_scale = 0.5
        noise = 0.1

        K = self._rbf_kernel(X_obs, X_obs, length_scale) + noise * np.eye(len(X_obs))
        K_star = self._rbf_kernel(X_new, X_obs, length_scale)
        K_star_star = self._rbf_kernel(X_new, X_new, length_scale)

        # GP prediction
        try:
            K_inv = np.linalg.inv(K)
        except np.linalg.LinAlgError:
            K_inv = np.linalg.pinv(K)

        mean = K_star @ K_inv @ y_norm
        var = np.diag(K_star_star - K_star @ K_inv @ K_star.T)
        var = np.maximum(var, 1e-8)

        # Unnormalize
        mean = mean * y_std + y_mean
        std = np.sqrt(var) * y_std

        return mean, std

    def _acquisition_function(self, X: np.ndarray, best_y: float) -> np.ndarray:
        """Compute acquisition function values."""
        mean, std = self._gp_predict(X)

        if self.acquisition == "ucb":
            # Upper Confidence Bound
            return mean + self.kappa * std

        elif self.acquisition == "ei":
            # Expected Improvement
            z = (mean - best_y - self.xi) / (std + 1e-8)
            # Polynomial approximation of normal CDF and PDF
            # CDF(z) ≈ sigmoid(1.7 * z)
            cdf = 1 / (1 + np.exp(-1.7 * z))
            # PDF(z) ≈ 0.4 * exp(-0.5 * z^2)
            pdf = 0.4 * np.exp(-0.5 * z**2)
            ei = (mean - best_y - self.xi) * cdf + std * pdf
            return ei

        elif self.acquisition == "poi":
            # Probability of Improvement
            z = (mean - best_y - self.xi) / (std + 1e-8)
            poi = 1 / (1 + np.exp(-1.7 * z))
            return poi

        else:
            return mean

    def _optimize_acquisition(self, best_y: float) -> np.ndarray:
        """Find point that maximizes acquisition function."""
        n_params = len(self.param_bounds)

        # Random candidates
        n_candidates = 1000
        candidates = self.rng.random((n_candidates, n_params))

        # Evaluate acquisition
        acq_values = self._acquisition_function(candidates, best_y)

        # Return best
        best_idx = np.argmax(acq_values)
        return candidates[best_idx]

    def _evaluate(self, params: Dict[str, Any], X: np.ndarray, y: np.ndarray) -> float:
        """Evaluate estimator with given parameters."""
        estimator = copy.deepcopy(self.estimator)

        for param, value in params.items():
            setattr(estimator, param, value)

        scores = cross_val_score(
            estimator,
            X,
            y,
            cv=self.cv,
            scoring=self.scoring,
        )

        return np.mean(scores)

    def fit(self, X: np.ndarray, y: np.ndarray) -> "BayesianOptimization":
        """Run Bayesian optimization.

        Args:
            X: Training data
            y: Target values

        Returns:
            self
        """
        X_data = np.asarray(X)
        y_data = np.asarray(y)

        n_params = len(self.param_bounds)
        param_names = list(self.param_bounds.keys())

        best_score = -np.inf
        best_params = None

        # Initial random points
        for i in range(self.n_initial_points):
            if self.verbose > 0:
                print(f"Initial point {i + 1}/{self.n_initial_points}")

            # Random sample
            x_norm = self.rng.random(n_params)
            params_dict = {name: x_norm[j] for j, name in enumerate(param_names)}
            params = self._transform_params(params_dict)

            try:
                score = self._evaluate(params, X_data, y_data)

                self._X_observed.append(x_norm)
                self._y_observed.append(score)
                self.history_.append({"params": params, "score": score})

                if score > best_score:
                    best_score = score
                    best_params = params

                if self.verbose > 0:
                    print(f"  Params: {params}")
                    print(f"  Score: {score:.4f}")

            except Exception as e:
                if self.verbose > 0:
                    print(f"  Failed: {e}")

        # Bayesian optimization iterations
        for i in range(self.n_iter - self.n_initial_points):
            if self.verbose > 0:
                print(f"BO iteration {i + 1}/{self.n_iter - self.n_initial_points}")

            # Find next point using acquisition function
            x_next = self._optimize_acquisition(best_score)
            params_dict = {name: x_next[j] for j, name in enumerate(param_names)}
            params = self._transform_params(params_dict)

            try:
                score = self._evaluate(params, X_data, y_data)

                self._X_observed.append(x_next)
                self._y_observed.append(score)
                self.history_.append({"params": params, "score": score})

                if score > best_score:
                    best_score = score
                    best_params = params

                if self.verbose > 0:
                    print(f"  Params: {params}")
                    print(f"  Score: {score:.4f}")

            except Exception as e:
                if self.verbose > 0:
                    print(f"  Failed: {e}")

        self.best_params_ = best_params
        self.best_score_ = best_score

        # Refit with best parameters
        if best_params is not None:
            self.best_estimator_ = copy.deepcopy(self.estimator)
            for param, value in best_params.items():
                setattr(self.best_estimator_, param, value)
            self.best_estimator_.fit(X_data, y_data)

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict using best estimator."""
        if self.best_estimator_ is None:
            raise ValueError("Must call fit before predict")
        return self.best_estimator_.predict(X)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Score using best estimator."""
        if self.best_estimator_ is None:
            raise ValueError("Must call fit before score")
        return self.best_estimator_.score(X, y)


class HalvingRandomSearchCV:
    """Successive Halving for efficient hyperparameter search.

    Starts with many candidates and few resources, then iteratively
    eliminates poor performers while increasing resources.

    Example:
        >>> from xcapit_fhe import HalvingRandomSearchCV, LogisticRegression
        >>> search = HalvingRandomSearchCV(
        ...     LogisticRegression(),
        ...     param_distributions,
        ...     n_candidates=50,
        ...     factor=3,
        ... )
        >>> search.fit(X, y)
    """

    def __init__(
        self,
        estimator: Any,
        param_distributions: Dict[str, Any],
        n_candidates: int = 50,
        factor: int = 3,
        min_resources: int = 100,
        max_resources: Optional[int] = None,
        scoring: Optional[Union[str, Callable]] = None,
        cv: int = 5,
        random_state: Optional[int] = None,
        verbose: int = 0,
    ):
        self.estimator = estimator
        self.param_distributions = param_distributions
        self.n_candidates = n_candidates
        self.factor = factor
        self.min_resources = min_resources
        self.max_resources = max_resources
        self.scoring = scoring
        self.cv = cv
        self.random_state = random_state
        self.verbose = verbose

        self.best_params_ = None
        self.best_score_ = None
        self.best_estimator_ = None
        self.cv_results_ = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> "HalvingRandomSearchCV":
        """Run successive halving search.

        Args:
            X: Training data
            y: Target values

        Returns:
            self
        """
        X = np.asarray(X)
        y = np.asarray(y)

        n_samples = len(X)
        max_resources = self.max_resources or n_samples

        # Sample initial candidates
        sampler = ParameterSampler(
            self.param_distributions,
            self.n_candidates,
            self.random_state,
        )
        candidates = list(sampler)

        # Successive halving
        n_resources = self.min_resources
        iteration = 0

        results = []

        while len(candidates) > 1 and n_resources <= max_resources:
            if self.verbose > 0:
                print(
                    f"Iteration {iteration}: {len(candidates)} candidates, {n_resources} resources"
                )

            # Evaluate candidates
            scores = []
            for params in candidates:
                # Subsample data
                idx = np.random.choice(n_samples, size=min(n_resources, n_samples), replace=False)
                X_sub = X[idx]
                y_sub = y[idx]

                estimator = copy.deepcopy(self.estimator)
                for param, value in params.items():
                    setattr(estimator, param, value)

                try:
                    cv_scores = cross_val_score(
                        estimator,
                        X_sub,
                        y_sub,
                        cv=min(self.cv, len(X_sub) // 2),
                        scoring=self.scoring,
                    )
                    score = np.mean(cv_scores)
                except Exception:
                    score = -np.inf

                scores.append(score)
                results.append(
                    {
                        "iteration": iteration,
                        "params": params,
                        "score": score,
                        "n_resources": n_resources,
                    }
                )

            # Select top 1/factor candidates
            n_select = max(1, len(candidates) // self.factor)
            top_indices = np.argsort(scores)[-n_select:]
            candidates = [candidates[i] for i in top_indices]

            # Increase resources
            n_resources = min(n_resources * self.factor, max_resources)
            iteration += 1

        # Best candidate
        if candidates:
            best_params = candidates[0]
            self.best_params_ = best_params

            # Final evaluation
            self.best_estimator_ = copy.deepcopy(self.estimator)
            for param, value in best_params.items():
                setattr(self.best_estimator_, param, value)
            self.best_estimator_.fit(X, y)

            cv_scores = cross_val_score(
                self.best_estimator_,
                X,
                y,
                cv=self.cv,
                scoring=self.scoring,
            )
            self.best_score_ = np.mean(cv_scores)

        self.cv_results_ = results

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict using best estimator."""
        if self.best_estimator_ is None:
            raise ValueError("Must call fit before predict")
        return self.best_estimator_.predict(X)


__all__ = [
    "ParameterSampler",
    "RandomizedSearchCV",
    "BayesianOptimization",
    "HalvingRandomSearchCV",
    "SearchResult",
]

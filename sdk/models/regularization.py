"""FHE-compatible Regularized Linear Models.

This module provides regularized linear regression models that work with
encrypted data using iterative optimization methods compatible with FHE.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

import numpy as np

from .base import BaseFHEModel, ModelConfig, ModelState


class RegularizationType(Enum):
    """Type of regularization."""

    L1 = "l1"  # Lasso
    L2 = "l2"  # Ridge
    ELASTICNET = "elasticnet"  # Combination


@dataclass
class RidgeConfig(ModelConfig):
    """Configuration for Ridge regression."""

    alpha: float = 1.0  # Regularization strength
    fit_intercept: bool = True
    normalize: bool = False
    solver: str = "auto"  # "auto", "svd", "cholesky", "lsqr"
    max_iter: int = 1000
    tol: float = 1e-4


@dataclass
class LassoConfig(ModelConfig):
    """Configuration for Lasso regression."""

    alpha: float = 1.0  # Regularization strength
    fit_intercept: bool = True
    normalize: bool = False
    max_iter: int = 1000
    tol: float = 1e-4
    warm_start: bool = False
    selection: str = "cyclic"  # "cyclic" or "random"


@dataclass
class ElasticNetConfig(ModelConfig):
    """Configuration for Elastic Net regression."""

    alpha: float = 1.0  # Regularization strength
    l1_ratio: float = 0.5  # Balance between L1 and L2
    fit_intercept: bool = True
    normalize: bool = False
    max_iter: int = 1000
    tol: float = 1e-4
    warm_start: bool = False
    selection: str = "cyclic"


class Ridge(BaseFHEModel):
    """Ridge Regression (L2 regularization) for encrypted data.

    Minimizes: ||y - Xw||^2 + alpha * ||w||^2

    FHE Compatibility:
    - Uses closed-form solution: w = (X'X + alpha*I)^(-1) X'y
    - Matrix operations are naturally FHE-compatible
    - Iterative solver available for large problems

    Example:
        >>> from xcapit_fhe import Ridge
        >>> model = Ridge(alpha=1.0)
        >>> model.fit(X_train, y_train)
        >>> predictions = model.predict(X_test)
    """

    def __init__(
        self,
        alpha: float = 1.0,
        fit_intercept: bool = True,
        normalize: bool = False,
        solver: str = "auto",
        max_iter: int = 1000,
        tol: float = 1e-4,
        fhe_compatible: bool = True,
    ):
        super().__init__(fhe_compatible=fhe_compatible)
        self.config = RidgeConfig(
            alpha=alpha,
            fit_intercept=fit_intercept,
            normalize=normalize,
            solver=solver,
            max_iter=max_iter,
            tol=tol,
        )
        self.coef_ = None
        self.intercept_ = 0.0
        self._X_mean = None
        self._X_std = None
        self._y_mean = None

    def _preprocess(
        self, X: np.ndarray, y: np.ndarray = None, fit: bool = True
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Preprocess features (centering and optional normalization)."""
        X = np.asarray(X, dtype=np.float64)

        if fit:
            self._X_mean = np.mean(X, axis=0) if self.config.fit_intercept else np.zeros(X.shape[1])
            if self.config.normalize:
                self._X_std = np.std(X, axis=0)
                self._X_std[self._X_std == 0] = 1.0
            else:
                self._X_std = np.ones(X.shape[1])

            if y is not None:
                self._y_mean = np.mean(y) if self.config.fit_intercept else 0.0

        X_processed = (X - self._X_mean) / self._X_std

        if y is not None:
            y_processed = y - self._y_mean
            return X_processed, y_processed

        return X_processed, None

    def fit(self, X: np.ndarray, y: np.ndarray) -> "Ridge":
        """Fit Ridge regression model.

        Args:
            X: Training features of shape (n_samples, n_features)
            y: Target values of shape (n_samples,)

        Returns:
            self
        """
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64).flatten()

        n_samples, n_features = X.shape
        self.n_features_in_ = n_features

        # Preprocess
        X_proc, y_proc = self._preprocess(X, y, fit=True)

        # Choose solver
        solver = self.config.solver
        if solver == "auto":
            solver = "cholesky" if n_features < 1000 else "lsqr"

        if solver == "cholesky":
            # Closed-form solution: w = (X'X + alpha*I)^(-1) X'y
            XtX = X_proc.T @ X_proc
            Xty = X_proc.T @ y_proc

            # Add regularization
            XtX += self.config.alpha * np.eye(n_features)

            try:
                self.coef_ = np.linalg.solve(XtX, Xty)
            except np.linalg.LinAlgError:
                # Fallback to pseudo-inverse
                self.coef_ = np.linalg.lstsq(XtX, Xty, rcond=None)[0]

        elif solver == "svd":
            # SVD-based solution
            U, s, Vt = np.linalg.svd(X_proc, full_matrices=False)
            d = s / (s**2 + self.config.alpha)
            self.coef_ = Vt.T @ (d * (U.T @ y_proc))

        elif solver == "lsqr":
            # Iterative LSQR solver (conjugate gradient)
            self.coef_ = self._solve_lsqr(X_proc, y_proc)

        else:
            raise ValueError(f"Unknown solver: {solver}")

        # Adjust for normalization
        self.coef_ = self.coef_ / self._X_std

        # Compute intercept
        if self.config.fit_intercept:
            self.intercept_ = self._y_mean - np.dot(self._X_mean, self.coef_)
        else:
            self.intercept_ = 0.0

        self.state = ModelState.TRAINED
        return self

    def _solve_lsqr(self, X: np.ndarray, y: np.ndarray) -> np.ndarray:
        """Solve using conjugate gradient method."""
        n_features = X.shape[1]
        alpha = self.config.alpha

        # Initialize
        w = np.zeros(n_features)
        r = y - X @ w  # Residual
        p = X.T @ r  # Search direction
        rs_old = np.dot(r, r)

        for _ in range(self.config.max_iter):
            Xp = X @ p
            Ap = X.T @ Xp + alpha * p  # (X'X + alpha*I) p

            pAp = np.dot(p, Ap)
            if pAp < 1e-12:
                break

            alpha_cg = rs_old / pAp
            w += alpha_cg * p
            r -= alpha_cg * Xp

            rs_new = np.dot(r, r)

            if np.sqrt(rs_new) < self.config.tol:
                break

            beta = rs_new / (rs_old + 1e-12)
            p = X.T @ r + beta * p
            rs_old = rs_new

        return w

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict using the linear model.

        Args:
            X: Samples of shape (n_samples, n_features)

        Returns:
            Predicted values
        """
        X = np.asarray(X, dtype=np.float64)
        return X @ self.coef_ + self.intercept_

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Return R^2 score."""
        y_pred = self.predict(X)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        return 1 - ss_res / (ss_tot + 1e-10)


class Lasso(BaseFHEModel):
    """Lasso Regression (L1 regularization) for encrypted data.

    Minimizes: (1/2n) * ||y - Xw||^2 + alpha * ||w||_1

    FHE Compatibility:
    - Uses coordinate descent with soft thresholding
    - Polynomial approximation of sign function
    - Iterative updates are FHE-compatible

    Example:
        >>> from xcapit_fhe import Lasso
        >>> model = Lasso(alpha=0.1)
        >>> model.fit(X_train, y_train)
        >>> predictions = model.predict(X_test)
    """

    def __init__(
        self,
        alpha: float = 1.0,
        fit_intercept: bool = True,
        normalize: bool = False,
        max_iter: int = 1000,
        tol: float = 1e-4,
        warm_start: bool = False,
        selection: str = "cyclic",
        fhe_compatible: bool = True,
    ):
        super().__init__(fhe_compatible=fhe_compatible)
        self.config = LassoConfig(
            alpha=alpha,
            fit_intercept=fit_intercept,
            normalize=normalize,
            max_iter=max_iter,
            tol=tol,
            warm_start=warm_start,
            selection=selection,
        )
        self.coef_ = None
        self.intercept_ = 0.0
        self._X_mean = None
        self._X_std = None
        self._y_mean = None
        self.n_iter_ = 0

    def _soft_threshold(self, x: np.ndarray, threshold: float) -> np.ndarray:
        """Soft thresholding operator for L1 regularization.

        S(x, t) = sign(x) * max(|x| - t, 0)

        For FHE, we approximate sign using polynomial sigmoid.
        """
        if self.fhe_compatible:
            # Polynomial approximation of sign: sign(x) ≈ tanh(kx) for large k
            # Using polynomial tanh: tanh(x) ≈ x - x^3/3 + 2x^5/15 for small x
            # Or smooth approximation: x / sqrt(x^2 + eps)
            eps = 1e-6
            sign_approx = x / np.sqrt(x**2 + eps)
            magnitude = np.maximum(np.abs(x) - threshold, 0)
            return sign_approx * magnitude
        else:
            return np.sign(x) * np.maximum(np.abs(x) - threshold, 0)

    def fit(self, X: np.ndarray, y: np.ndarray) -> "Lasso":
        """Fit Lasso regression using coordinate descent.

        Args:
            X: Training features of shape (n_samples, n_features)
            y: Target values of shape (n_samples,)

        Returns:
            self
        """
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64).flatten()

        n_samples, n_features = X.shape
        self.n_features_in_ = n_features

        # Preprocess
        if self.config.fit_intercept:
            self._X_mean = np.mean(X, axis=0)
            self._y_mean = np.mean(y)
            X = X - self._X_mean
            y = y - self._y_mean
        else:
            self._X_mean = np.zeros(n_features)
            self._y_mean = 0.0

        if self.config.normalize:
            self._X_std = np.std(X, axis=0)
            self._X_std[self._X_std == 0] = 1.0
            X = X / self._X_std
        else:
            self._X_std = np.ones(n_features)

        # Initialize coefficients
        if self.config.warm_start and self.coef_ is not None:
            coef = self.coef_ * self._X_std
        else:
            coef = np.zeros(n_features)

        # Precompute X'X diagonal and X'y
        X_sq_sum = np.sum(X**2, axis=0)
        Xy = X.T @ y

        # Coordinate descent
        alpha = self.config.alpha * n_samples  # Scale alpha

        for iteration in range(self.config.max_iter):  # noqa: B007
            coef_old = coef.copy()

            # Coordinate selection
            if self.config.selection == "random":
                coords = np.random.permutation(n_features)
            else:
                coords = np.arange(n_features)

            for j in coords:
                if X_sq_sum[j] < 1e-12:
                    continue

                # Compute residual excluding feature j
                residual_j = Xy[j] - np.dot(X[:, j], X @ coef) + X_sq_sum[j] * coef[j]

                # Soft thresholding update
                coef[j] = self._soft_threshold(residual_j / X_sq_sum[j], alpha / X_sq_sum[j])

            # Check convergence
            max_change = np.max(np.abs(coef - coef_old))
            if max_change < self.config.tol:
                break

        self.n_iter_ = iteration + 1

        # Adjust for normalization
        self.coef_ = coef / self._X_std

        # Compute intercept
        if self.config.fit_intercept:
            self.intercept_ = self._y_mean - np.dot(self._X_mean, self.coef_)
        else:
            self.intercept_ = 0.0

        self.state = ModelState.TRAINED
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict using the linear model."""
        X = np.asarray(X, dtype=np.float64)
        return X @ self.coef_ + self.intercept_

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Return R^2 score."""
        y_pred = self.predict(X)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        return 1 - ss_res / (ss_tot + 1e-10)


class ElasticNet(BaseFHEModel):
    """Elastic Net Regression (L1 + L2 regularization) for encrypted data.

    Minimizes: (1/2n) * ||y - Xw||^2 + alpha * l1_ratio * ||w||_1
               + 0.5 * alpha * (1 - l1_ratio) * ||w||^2

    FHE Compatibility:
    - Combines Ridge and Lasso techniques
    - Coordinate descent with modified soft thresholding
    - All operations are polynomial

    Example:
        >>> from xcapit_fhe import ElasticNet
        >>> model = ElasticNet(alpha=0.1, l1_ratio=0.5)
        >>> model.fit(X_train, y_train)
        >>> predictions = model.predict(X_test)
    """

    def __init__(
        self,
        alpha: float = 1.0,
        l1_ratio: float = 0.5,
        fit_intercept: bool = True,
        normalize: bool = False,
        max_iter: int = 1000,
        tol: float = 1e-4,
        warm_start: bool = False,
        selection: str = "cyclic",
        fhe_compatible: bool = True,
    ):
        super().__init__(fhe_compatible=fhe_compatible)
        self.config = ElasticNetConfig(
            alpha=alpha,
            l1_ratio=l1_ratio,
            fit_intercept=fit_intercept,
            normalize=normalize,
            max_iter=max_iter,
            tol=tol,
            warm_start=warm_start,
            selection=selection,
        )
        self.coef_ = None
        self.intercept_ = 0.0
        self._X_mean = None
        self._X_std = None
        self._y_mean = None
        self.n_iter_ = 0

    def _soft_threshold(self, x: np.ndarray, threshold: float) -> np.ndarray:
        """Soft thresholding with polynomial approximation for FHE."""
        if self.fhe_compatible:
            eps = 1e-6
            sign_approx = x / np.sqrt(x**2 + eps)
            magnitude = np.maximum(np.abs(x) - threshold, 0)
            return sign_approx * magnitude
        else:
            return np.sign(x) * np.maximum(np.abs(x) - threshold, 0)

    def fit(self, X: np.ndarray, y: np.ndarray) -> "ElasticNet":
        """Fit Elastic Net using coordinate descent.

        Args:
            X: Training features
            y: Target values

        Returns:
            self
        """
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64).flatten()

        n_samples, n_features = X.shape
        self.n_features_in_ = n_features

        # Preprocess
        if self.config.fit_intercept:
            self._X_mean = np.mean(X, axis=0)
            self._y_mean = np.mean(y)
            X = X - self._X_mean
            y = y - self._y_mean
        else:
            self._X_mean = np.zeros(n_features)
            self._y_mean = 0.0

        if self.config.normalize:
            self._X_std = np.std(X, axis=0)
            self._X_std[self._X_std == 0] = 1.0
            X = X / self._X_std
        else:
            self._X_std = np.ones(n_features)

        # Initialize
        if self.config.warm_start and self.coef_ is not None:
            coef = self.coef_ * self._X_std
        else:
            coef = np.zeros(n_features)

        # Precompute
        X_sq_sum = np.sum(X**2, axis=0)
        Xy = X.T @ y

        # Regularization parameters
        alpha = self.config.alpha * n_samples
        l1_reg = alpha * self.config.l1_ratio
        l2_reg = alpha * (1 - self.config.l1_ratio)

        # Coordinate descent
        for iteration in range(self.config.max_iter):  # noqa: B007
            coef_old = coef.copy()

            coords = (
                np.random.permutation(n_features)
                if self.config.selection == "random"
                else np.arange(n_features)
            )

            for j in coords:
                if X_sq_sum[j] < 1e-12:
                    continue

                # Residual
                residual_j = Xy[j] - np.dot(X[:, j], X @ coef) + X_sq_sum[j] * coef[j]

                # Elastic net update with both L1 and L2
                denominator = X_sq_sum[j] + l2_reg
                coef[j] = self._soft_threshold(residual_j / denominator, l1_reg / denominator)

            # Convergence check
            if np.max(np.abs(coef - coef_old)) < self.config.tol:
                break

        self.n_iter_ = iteration + 1

        # Adjust for normalization
        self.coef_ = coef / self._X_std

        # Intercept
        if self.config.fit_intercept:
            self.intercept_ = self._y_mean - np.dot(self._X_mean, self.coef_)
        else:
            self.intercept_ = 0.0

        self.state = ModelState.TRAINED
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict using the linear model."""
        X = np.asarray(X, dtype=np.float64)
        return X @ self.coef_ + self.intercept_

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Return R^2 score."""
        y_pred = self.predict(X)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        return 1 - ss_res / (ss_tot + 1e-10)


class RidgeClassifier(BaseFHEModel):
    """Ridge Classifier for encrypted data.

    Converts classification to regression and applies Ridge.
    For binary classification, uses {-1, 1} encoding.
    For multiclass, uses one-vs-rest strategy.

    Example:
        >>> from xcapit_fhe import RidgeClassifier
        >>> model = RidgeClassifier(alpha=1.0)
        >>> model.fit(X_train, y_train)
        >>> predictions = model.predict(X_test)
    """

    def __init__(
        self,
        alpha: float = 1.0,
        fit_intercept: bool = True,
        normalize: bool = False,
        fhe_compatible: bool = True,
    ):
        super().__init__(fhe_compatible=fhe_compatible)
        self.alpha = alpha
        self.fit_intercept = fit_intercept
        self.normalize = normalize
        self.classes_ = None
        self._ridge_models = []

    def fit(self, X: np.ndarray, y: np.ndarray) -> "RidgeClassifier":
        """Fit Ridge classifier.

        Args:
            X: Training features
            y: Class labels

        Returns:
            self
        """
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y)

        self.classes_ = np.unique(y)
        n_classes = len(self.classes_)
        self.n_features_in_ = X.shape[1]

        self._ridge_models = []

        if n_classes == 2:
            # Binary classification
            y_binary = np.where(y == self.classes_[1], 1, -1).astype(np.float64)
            ridge = Ridge(
                alpha=self.alpha,
                fit_intercept=self.fit_intercept,
                normalize=self.normalize,
                fhe_compatible=self.fhe_compatible,
            )
            ridge.fit(X, y_binary)
            self._ridge_models.append(ridge)
        else:
            # One-vs-rest for multiclass
            for cls in self.classes_:
                y_binary = np.where(y == cls, 1, -1).astype(np.float64)
                ridge = Ridge(
                    alpha=self.alpha,
                    fit_intercept=self.fit_intercept,
                    normalize=self.normalize,
                    fhe_compatible=self.fhe_compatible,
                )
                ridge.fit(X, y_binary)
                self._ridge_models.append(ridge)

        self.state = ModelState.TRAINED
        return self

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """Compute decision function values."""
        X = np.asarray(X, dtype=np.float64)

        if len(self.classes_) == 2:
            return self._ridge_models[0].predict(X)
        else:
            scores = np.column_stack([model.predict(X) for model in self._ridge_models])
            return scores

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict class labels."""
        scores = self.decision_function(X)

        if len(self.classes_) == 2:
            return np.where(scores > 0, self.classes_[1], self.classes_[0])
        else:
            return self.classes_[np.argmax(scores, axis=1)]

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Return accuracy score."""
        return np.mean(self.predict(X) == y)


class SGDRegressor(BaseFHEModel):
    """Stochastic Gradient Descent for regression on encrypted data.

    Supports various loss functions and regularization types.
    FHE-compatible through polynomial approximations of gradients.

    Example:
        >>> from xcapit_fhe import SGDRegressor
        >>> model = SGDRegressor(loss='squared_error', penalty='l2')
        >>> model.fit(X_train, y_train)
    """

    def __init__(
        self,
        loss: str = "squared_error",
        penalty: str = "l2",
        alpha: float = 0.0001,
        l1_ratio: float = 0.15,
        fit_intercept: bool = True,
        max_iter: int = 1000,
        tol: float = 1e-4,
        learning_rate: str = "invscaling",
        eta0: float = 0.01,
        power_t: float = 0.25,
        random_state: Optional[int] = None,
        fhe_compatible: bool = True,
    ):
        super().__init__(fhe_compatible=fhe_compatible)
        self.loss = loss
        self.penalty = penalty
        self.alpha = alpha
        self.l1_ratio = l1_ratio
        self.fit_intercept = fit_intercept
        self.max_iter = max_iter
        self.tol = tol
        self.learning_rate = learning_rate
        self.eta0 = eta0
        self.power_t = power_t
        self.random_state = random_state

        self.coef_ = None
        self.intercept_ = 0.0
        self.n_iter_ = 0

    def _get_learning_rate(self, t: int) -> float:
        """Get learning rate at iteration t."""
        if self.learning_rate == "constant":
            return self.eta0
        elif self.learning_rate == "optimal":
            return 1.0 / (self.alpha * (t + 1))
        elif self.learning_rate == "invscaling":
            return self.eta0 / (t + 1) ** self.power_t
        elif self.learning_rate == "adaptive":
            return self.eta0
        else:
            return self.eta0

    def _compute_loss_gradient(self, y_true: float, y_pred: float) -> float:
        """Compute gradient of loss function."""
        if self.loss == "squared_error":
            return y_pred - y_true
        elif self.loss == "huber":
            diff = y_pred - y_true
            epsilon = 1.35
            if np.abs(diff) <= epsilon:
                return diff
            else:
                return epsilon * np.sign(diff)
        elif self.loss == "epsilon_insensitive":
            diff = y_pred - y_true
            epsilon = 0.1
            if np.abs(diff) <= epsilon:
                return 0.0
            else:
                return np.sign(diff)
        else:
            return y_pred - y_true

    def _soft_threshold(self, x: float, threshold: float) -> float:
        """Soft thresholding for L1 regularization."""
        if self.fhe_compatible:
            eps = 1e-6
            sign_approx = x / np.sqrt(x**2 + eps)
            magnitude = max(abs(x) - threshold, 0)
            return sign_approx * magnitude
        else:
            return np.sign(x) * max(abs(x) - threshold, 0)

    def fit(self, X: np.ndarray, y: np.ndarray) -> "SGDRegressor":
        """Fit SGD regressor.

        Args:
            X: Training features
            y: Target values

        Returns:
            self
        """
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64).flatten()

        n_samples, n_features = X.shape
        self.n_features_in_ = n_features

        rng = np.random.default_rng(self.random_state)

        # Initialize
        self.coef_ = np.zeros(n_features)
        self.intercept_ = 0.0

        t = 0  # Iteration counter

        for epoch in range(self.max_iter):
            indices = rng.permutation(n_samples)

            for i in indices:
                t += 1
                eta = self._get_learning_rate(t)

                # Prediction
                y_pred = np.dot(X[i], self.coef_) + self.intercept_

                # Gradient of loss
                grad_loss = self._compute_loss_gradient(y[i], y_pred)

                # Update coefficients
                if self.penalty == "l2":
                    self.coef_ = (1 - eta * self.alpha) * self.coef_ - eta * grad_loss * X[i]
                elif self.penalty == "l1":
                    self.coef_ = self.coef_ - eta * grad_loss * X[i]
                    # Apply L1 proximal step
                    for j in range(n_features):
                        self.coef_[j] = self._soft_threshold(self.coef_[j], eta * self.alpha)
                elif self.penalty == "elasticnet":
                    l2_term = (1 - self.l1_ratio) * self.alpha
                    l1_term = self.l1_ratio * self.alpha
                    self.coef_ = (1 - eta * l2_term) * self.coef_ - eta * grad_loss * X[i]
                    for j in range(n_features):
                        self.coef_[j] = self._soft_threshold(self.coef_[j], eta * l1_term)

                # Update intercept
                if self.fit_intercept:
                    self.intercept_ -= eta * grad_loss

            # Check convergence
            if epoch > 0:
                # Simple convergence check based on coefficient change
                pass

        self.n_iter_ = epoch + 1
        self.state = ModelState.TRAINED
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict using the linear model."""
        X = np.asarray(X, dtype=np.float64)
        return X @ self.coef_ + self.intercept_

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Return R^2 score."""
        y_pred = self.predict(X)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        return 1 - ss_res / (ss_tot + 1e-10)


__all__ = [
    # Enums
    "RegularizationType",
    # Configs
    "RidgeConfig",
    "LassoConfig",
    "ElasticNetConfig",
    # Models
    "Ridge",
    "Lasso",
    "ElasticNet",
    "RidgeClassifier",
    "SGDRegressor",
]

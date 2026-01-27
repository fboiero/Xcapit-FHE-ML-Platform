"""
FHE-compatible model calibration.

Provides probability calibration for classifiers to improve
the reliability of predicted probabilities.

Methods:
- Platt scaling (sigmoid calibration)
- Isotonic regression calibration
- Temperature scaling
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np


class CalibrationMethod(Enum):
    """Calibration methods."""
    SIGMOID = "sigmoid"  # Platt scaling
    ISOTONIC = "isotonic"  # Isotonic regression
    TEMPERATURE = "temperature"  # Temperature scaling


@dataclass
class CalibrationConfig:
    """Configuration for model calibration."""
    method: CalibrationMethod = CalibrationMethod.SIGMOID
    cv: int = 5  # Cross-validation folds for calibration
    ensemble: bool = True  # Use ensemble of calibrators


class IsotonicRegression:
    """
    Isotonic regression for probability calibration.

    Fits a non-decreasing step function to map predicted probabilities
    to calibrated probabilities.
    """

    def __init__(self, out_of_bounds: str = 'clip'):
        """
        Initialize isotonic regression.

        Args:
            out_of_bounds: 'clip', 'nan', or 'raise' for values outside training range
        """
        self.out_of_bounds = out_of_bounds
        self._fitted = False
        self._x_thresholds = None
        self._y_thresholds = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> "IsotonicRegression":
        """
        Fit isotonic regression.

        Args:
            X: Input values (predicted probabilities)
            y: Target values (true labels or calibrated probabilities)

        Returns:
            self
        """
        X = np.asarray(X).ravel()
        y = np.asarray(y).ravel()

        # Sort by X
        order = np.argsort(X)
        X_sorted = X[order]
        y_sorted = y[order]

        # Pool Adjacent Violators Algorithm (PAVA)
        n = len(y_sorted)
        y_isotonic = np.zeros(n)
        blocks = [[i] for i in range(n)]

        i = 0
        while i < len(blocks) - 1:
            # Get means of adjacent blocks
            mean_i = np.mean(y_sorted[blocks[i]])
            mean_next = np.mean(y_sorted[blocks[i + 1]])

            if mean_i > mean_next:
                # Merge blocks
                blocks[i] = blocks[i] + blocks[i + 1]
                blocks.pop(i + 1)
                # Go back to check previous
                i = max(0, i - 1)
            else:
                i += 1

        # Assign isotonic values
        for block in blocks:
            mean_val = np.mean(y_sorted[block])
            for idx in block:
                y_isotonic[idx] = mean_val

        # Store unique thresholds
        self._x_thresholds = []
        self._y_thresholds = []

        prev_y = None
        for x_val, y_val in zip(X_sorted, y_isotonic):
            if prev_y is None or y_val != prev_y:
                self._x_thresholds.append(x_val)
                self._y_thresholds.append(y_val)
                prev_y = y_val

        self._x_thresholds = np.array(self._x_thresholds)
        self._y_thresholds = np.array(self._y_thresholds)

        self._fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Apply isotonic regression to new data.

        Args:
            X: Input values

        Returns:
            Calibrated values
        """
        if not self._fitted:
            raise RuntimeError("Must fit before predict")

        X = np.asarray(X).ravel()
        result = np.zeros_like(X, dtype=float)

        for i, x in enumerate(X):
            if x <= self._x_thresholds[0]:
                if self.out_of_bounds == 'clip':
                    result[i] = self._y_thresholds[0]
                elif self.out_of_bounds == 'nan':
                    result[i] = np.nan
                else:
                    raise ValueError(f"Value {x} out of bounds")
            elif x >= self._x_thresholds[-1]:
                if self.out_of_bounds == 'clip':
                    result[i] = self._y_thresholds[-1]
                elif self.out_of_bounds == 'nan':
                    result[i] = np.nan
                else:
                    raise ValueError(f"Value {x} out of bounds")
            else:
                # Find appropriate threshold
                idx = np.searchsorted(self._x_thresholds, x, side='right') - 1
                result[i] = self._y_thresholds[idx]

        return result

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Alias for predict."""
        return self.predict(X)


class SigmoidCalibration:
    """
    Sigmoid (Platt) calibration for probability calibration.

    Fits a sigmoid function: P(y=1|f) = 1 / (1 + exp(A*f + B))
    """

    def __init__(self, max_iter: int = 100, tol: float = 1e-5):
        """
        Initialize sigmoid calibration.

        Args:
            max_iter: Maximum iterations for optimization
            tol: Convergence tolerance
        """
        self.max_iter = max_iter
        self.tol = tol
        self._fitted = False
        self.a_ = None
        self.b_ = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> "SigmoidCalibration":
        """
        Fit sigmoid calibration using Platt scaling.

        Args:
            X: Decision function values or probabilities
            y: True binary labels

        Returns:
            self
        """
        X = np.asarray(X).ravel()
        y = np.asarray(y).ravel()

        # Target probabilities (Platt's method)
        n_pos = y.sum()
        n_neg = len(y) - n_pos

        # Target transformation
        t_pos = (n_pos + 1) / (n_pos + 2)
        t_neg = 1 / (n_neg + 2)
        t = np.where(y > 0.5, t_pos, t_neg)

        # Initialize parameters
        a = 0.0
        b = np.log((n_neg + 1) / (n_pos + 1))

        # Newton-Raphson optimization
        for _ in range(self.max_iter):
            # Compute probabilities
            fval = a * X + b
            p = 1 / (1 + np.exp(-np.clip(fval, -500, 500)))
            p = np.clip(p, 1e-15, 1 - 1e-15)

            # Gradient
            grad_a = np.sum((p - t) * X)
            grad_b = np.sum(p - t)

            # Hessian
            w = p * (1 - p)
            hess_aa = np.sum(w * X * X)
            hess_ab = np.sum(w * X)
            hess_bb = np.sum(w)

            # Add regularization for numerical stability
            hess_aa += 1e-8
            hess_bb += 1e-8

            # Update (simplified - ignore off-diagonal for stability)
            delta_a = grad_a / (hess_aa + 1e-10)
            delta_b = grad_b / (hess_bb + 1e-10)

            a -= delta_a
            b -= delta_b

            if abs(delta_a) < self.tol and abs(delta_b) < self.tol:
                break

        self.a_ = a
        self.b_ = b
        self._fitted = True

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Apply sigmoid calibration.

        Args:
            X: Input values

        Returns:
            Calibrated probabilities
        """
        if not self._fitted:
            raise RuntimeError("Must fit before predict")

        X = np.asarray(X).ravel()
        fval = self.a_ * X + self.b_
        return 1 / (1 + np.exp(-np.clip(fval, -500, 500)))

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Alias for predict."""
        return self.predict(X)


class TemperatureScaling:
    """
    Temperature scaling for neural network calibration.

    Learns a single temperature parameter T such that
    calibrated probabilities = softmax(logits / T).
    """

    def __init__(self, max_iter: int = 100, lr: float = 0.01):
        """
        Initialize temperature scaling.

        Args:
            max_iter: Maximum iterations
            lr: Learning rate
        """
        self.max_iter = max_iter
        self.lr = lr
        self._fitted = False
        self.temperature_ = 1.0

    def fit(self, logits: np.ndarray, y: np.ndarray) -> "TemperatureScaling":
        """
        Fit temperature scaling.

        Args:
            logits: Pre-softmax logits (n_samples, n_classes)
            y: True class labels

        Returns:
            self
        """
        logits = np.asarray(logits)
        y = np.asarray(y).ravel().astype(int)

        if logits.ndim == 1:
            logits = logits.reshape(-1, 1)

        temperature = 1.0

        for _ in range(self.max_iter):
            # Compute calibrated probabilities
            scaled_logits = logits / temperature
            max_logits = np.max(scaled_logits, axis=1, keepdims=True)
            exp_logits = np.exp(scaled_logits - max_logits)
            probs = exp_logits / exp_logits.sum(axis=1, keepdims=True)

            # Cross-entropy loss
            n_samples = len(y)
            correct_probs = probs[np.arange(n_samples), y]

            # Gradient of NLL w.r.t. temperature
            # Simplified gradient computation
            grad = 0.0
            for i in range(n_samples):
                grad += np.dot(probs[i], logits[i]) - logits[i, y[i]]
            grad /= (temperature ** 2 * n_samples)

            # Update temperature
            temperature -= self.lr * grad
            temperature = max(0.01, temperature)  # Prevent negative/zero

        self.temperature_ = temperature
        self._fitted = True

        return self

    def predict(self, logits: np.ndarray) -> np.ndarray:
        """
        Apply temperature scaling.

        Args:
            logits: Pre-softmax logits

        Returns:
            Calibrated probabilities
        """
        if not self._fitted:
            raise RuntimeError("Must fit before predict")

        logits = np.asarray(logits)
        if logits.ndim == 1:
            logits = logits.reshape(-1, 1)

        scaled_logits = logits / self.temperature_
        max_logits = np.max(scaled_logits, axis=1, keepdims=True)
        exp_logits = np.exp(scaled_logits - max_logits)
        return exp_logits / exp_logits.sum(axis=1, keepdims=True)

    def transform(self, logits: np.ndarray) -> np.ndarray:
        """Alias for predict."""
        return self.predict(logits)


class CalibratedClassifierCV:
    """
    Probability calibration with cross-validation.

    Wraps a classifier and calibrates its probability estimates.

    Example:
        >>> from xcapit_fhe import CalibratedClassifierCV, LogisticRegression
        >>> clf = CalibratedClassifierCV(
        ...     estimator=LogisticRegression(),
        ...     method='sigmoid',
        ...     cv=5
        ... )
        >>> clf.fit(X_train, y_train)
        >>> probs = clf.predict_proba(X_test)
    """

    def __init__(
        self,
        estimator: Any,
        method: str = 'sigmoid',
        cv: int = 5,
        ensemble: bool = True,
    ):
        """
        Initialize calibrated classifier.

        Args:
            estimator: Base classifier
            method: 'sigmoid', 'isotonic', or 'temperature'
            cv: Number of cross-validation folds
            ensemble: If True, use ensemble of calibrators
        """
        self.estimator = estimator
        self.method = method
        self.cv = cv
        self.ensemble = ensemble
        self._fitted = False
        self._calibrators = []
        self._estimators = []
        self._classes = None

    def _get_calibrator(self):
        """Get calibrator instance based on method."""
        if self.method == 'sigmoid':
            return SigmoidCalibration()
        elif self.method == 'isotonic':
            return IsotonicRegression()
        elif self.method == 'temperature':
            return TemperatureScaling()
        else:
            raise ValueError(f"Unknown method: {self.method}")

    def fit(self, X: np.ndarray, y: np.ndarray) -> "CalibratedClassifierCV":
        """
        Fit calibrated classifier using cross-validation.

        Args:
            X: Training features
            y: Training labels

        Returns:
            self
        """
        X = np.asarray(X)
        y = np.asarray(y).ravel()

        self._classes = np.unique(y)
        n_samples = X.shape[0]

        # Create CV folds
        fold_size = n_samples // self.cv
        indices = np.arange(n_samples)
        np.random.shuffle(indices)

        self._calibrators = []
        self._estimators = []

        for fold in range(self.cv):
            # Split indices
            start = fold * fold_size
            end = start + fold_size if fold < self.cv - 1 else n_samples
            val_indices = indices[start:end]
            train_indices = np.concatenate([indices[:start], indices[end:]])

            X_train, y_train = X[train_indices], y[train_indices]
            X_val, y_val = X[val_indices], y[val_indices]

            # Clone and fit estimator
            import copy
            estimator = copy.deepcopy(self.estimator)
            estimator.fit(X_train, y_train)
            self._estimators.append(estimator)

            # Get predictions on validation set
            if hasattr(estimator, 'decision_function'):
                scores = estimator.decision_function(X_val)
            elif hasattr(estimator, 'predict_proba'):
                probs = estimator.predict_proba(X_val)
                scores = probs[:, 1] if len(self._classes) == 2 else probs
            else:
                raise ValueError("Estimator must have decision_function or predict_proba")

            # Fit calibrator
            calibrator = self._get_calibrator()

            if self.method == 'temperature' and scores.ndim > 1:
                calibrator.fit(scores, y_val)
            else:
                if scores.ndim > 1:
                    scores = scores[:, 1] if scores.shape[1] == 2 else scores
                calibrator.fit(scores, y_val)

            self._calibrators.append(calibrator)

        # If not ensemble, fit final estimator on all data
        if not self.ensemble:
            self.estimator.fit(X, y)
            self._estimators = [self.estimator]

            # Use last fold's calibrator (simplified)
            # In practice, might want to recalibrate

        self._fitted = True
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict calibrated probabilities.

        Args:
            X: Features to predict

        Returns:
            Calibrated probability estimates
        """
        if not self._fitted:
            raise RuntimeError("Must fit before predict_proba")

        X = np.asarray(X)
        n_samples = X.shape[0]

        if self.ensemble:
            # Average predictions from all estimators
            all_probs = []

            for estimator, calibrator in zip(self._estimators, self._calibrators):
                if hasattr(estimator, 'decision_function'):
                    scores = estimator.decision_function(X)
                else:
                    probs = estimator.predict_proba(X)
                    scores = probs[:, 1] if len(self._classes) == 2 else probs

                if self.method == 'temperature' and scores.ndim > 1:
                    calibrated = calibrator.predict(scores)
                else:
                    if scores.ndim > 1:
                        scores = scores[:, 1] if scores.shape[1] == 2 else scores
                    calibrated = calibrator.predict(scores)

                all_probs.append(calibrated)

            mean_probs = np.mean(all_probs, axis=0)

            # Convert to 2D for binary case
            if mean_probs.ndim == 1:
                return np.column_stack([1 - mean_probs, mean_probs])
            return mean_probs
        else:
            # Single estimator
            estimator = self._estimators[0]
            calibrator = self._calibrators[0]

            if hasattr(estimator, 'decision_function'):
                scores = estimator.decision_function(X)
            else:
                probs = estimator.predict_proba(X)
                scores = probs[:, 1] if len(self._classes) == 2 else probs

            calibrated = calibrator.predict(scores)

            if calibrated.ndim == 1:
                return np.column_stack([1 - calibrated, calibrated])
            return calibrated

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class labels.

        Args:
            X: Features

        Returns:
            Predicted class labels
        """
        proba = self.predict_proba(X)
        return self._classes[np.argmax(proba, axis=1)]

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Compute accuracy."""
        return (self.predict(X) == y).mean()


def calibration_curve(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 10,
    strategy: str = 'uniform',
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute calibration curve (reliability diagram data).

    Args:
        y_true: True binary labels
        y_prob: Predicted probabilities
        n_bins: Number of bins
        strategy: 'uniform' or 'quantile'

    Returns:
        Tuple of (mean_predicted_value, fraction_of_positives) per bin
    """
    y_true = np.asarray(y_true).ravel()
    y_prob = np.asarray(y_prob).ravel()

    if strategy == 'uniform':
        bins = np.linspace(0, 1, n_bins + 1)
    elif strategy == 'quantile':
        bins = np.percentile(y_prob, np.linspace(0, 100, n_bins + 1))
        bins = np.unique(bins)  # Remove duplicates
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    bin_ids = np.searchsorted(bins[1:-1], y_prob)

    bin_probs = []
    bin_true = []

    for i in range(len(bins) - 1):
        mask = bin_ids == i
        if mask.sum() > 0:
            bin_probs.append(y_prob[mask].mean())
            bin_true.append(y_true[mask].mean())

    return np.array(bin_true), np.array(bin_probs)


__all__ = [
    "CalibrationConfig",
    "CalibrationMethod",
    "IsotonicRegression",
    "SigmoidCalibration",
    "TemperatureScaling",
    "CalibratedClassifierCV",
    "calibration_curve",
]

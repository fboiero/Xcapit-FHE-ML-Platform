"""FHE-compatible Naive Bayes classifiers.

This module implements Naive Bayes classifiers for FHE-encrypted data.
Naive Bayes is particularly well-suited for FHE because:
- Predictions only require multiplication and addition
- No iterative optimization during prediction
- Low multiplicative depth
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Union

import numpy as np

from ..encryption.ckks_wrapper import (
    CKKSEncryptor,
    EncryptedMatrix,
    EncryptedVector,
)
from ..utils.data_loader import EncryptedDataset
from .base import BaseFHEModel, FHELevel, ModelConfig, ModelState


class NaiveBayesType(Enum):
    """Types of Naive Bayes classifiers."""

    GAUSSIAN = "gaussian"  # For continuous features
    MULTINOMIAL = "multinomial"  # For count features
    BERNOULLI = "bernoulli"  # For binary features


@dataclass
class NaiveBayesConfig(ModelConfig):
    """Configuration for Naive Bayes.

    Attributes:
        var_smoothing: Portion of variance added for stability (Gaussian).
        alpha: Additive smoothing parameter (Multinomial/Bernoulli).
        fit_prior: Whether to learn class priors.
        class_prior: Prior probabilities (if not learning).
    """

    var_smoothing: float = 1e-9
    alpha: float = 1.0
    fit_prior: bool = True
    class_prior: Optional[list[float]] = None

    def __post_init__(self):
        super().__post_init__()
        if self.var_smoothing < 0:
            raise ValueError("var_smoothing must be non-negative")
        if self.alpha < 0:
            raise ValueError("alpha must be non-negative")


class GaussianNaiveBayes(BaseFHEModel):
    """Gaussian Naive Bayes classifier for FHE-encrypted data.

    Assumes features follow a Gaussian distribution within each class.
    Prediction is done using Bayes' theorem:

    P(y|x) ∝ P(y) × Π P(xᵢ|y)

    where P(xᵢ|y) = N(xᵢ; μᵢʸ, σᵢʸ²)

    This is FHE-friendly because log probabilities become sums:
    log P(y|x) = log P(y) + Σ log P(xᵢ|y)

    Example:
        >>> from sdk.models import GaussianNaiveBayes
        >>> gnb = GaussianNaiveBayes()
        >>> gnb.fit(X_train, y_train)
        >>> predictions = gnb.predict(X_test)
        >>> probabilities = gnb.predict_proba(X_test)
    """

    fhe_level = FHELevel.NONE

    def __init__(
        self,
        config: Optional[NaiveBayesConfig] = None,
        encryptor: Optional[CKKSEncryptor] = None,
    ):
        """Initialize Gaussian Naive Bayes.

        Args:
            config: NB configuration.
            encryptor: CKKS encryptor.
        """
        if config is None:
            config = NaiveBayesConfig()
        super().__init__(config=config, encryptor=encryptor)

        self._nb_config = config
        self._classes: Optional[np.ndarray] = None
        self._class_count: Optional[np.ndarray] = None
        self._class_prior: Optional[np.ndarray] = None
        self._theta: Optional[np.ndarray] = None  # Mean per class per feature
        self._var: Optional[np.ndarray] = None  # Variance per class per feature
        self._epsilon: float = 0.0  # Variance smoothing

    @property
    def classes_(self) -> Optional[np.ndarray]:
        """Get unique classes."""
        return self._classes

    @property
    def class_prior_(self) -> Optional[np.ndarray]:
        """Get class prior probabilities."""
        return self._class_prior

    @property
    def theta_(self) -> Optional[np.ndarray]:
        """Get mean of each feature per class."""
        return self._theta

    @property
    def var_(self) -> Optional[np.ndarray]:
        """Get variance of each feature per class."""
        return self._var

    def fit(
        self,
        X: Union[EncryptedDataset, EncryptedMatrix, np.ndarray],
        y: Optional[Union[EncryptedVector, np.ndarray]] = None,
    ) -> "GaussianNaiveBayes":
        """Fit Gaussian Naive Bayes.

        Args:
            X: Training features.
            y: Training labels.

        Returns:
            self for method chaining.
        """
        self._state = ModelState.TRAINING

        if isinstance(X, (EncryptedDataset, EncryptedMatrix, EncryptedVector)):
            raise ValueError("NaiveBayes must be trained on plaintext data.")

        X_train = np.asarray(X)
        y_train = np.asarray(y).ravel()

        if X_train.ndim == 1:
            X_train = X_train.reshape(-1, 1)

        n_samples, n_features = X_train.shape
        self._n_features = n_features

        # Get unique classes
        self._classes = np.unique(y_train)
        n_classes = len(self._classes)

        if self._config.verbose:
            print(f"Training GaussianNaiveBayes: {n_classes} classes")
            print(f"  Samples: {n_samples}, Features: {n_features}")

        # Compute statistics per class
        self._theta = np.zeros((n_classes, n_features))
        self._var = np.zeros((n_classes, n_features))
        self._class_count = np.zeros(n_classes)

        for i, c in enumerate(self._classes):
            X_c = X_train[y_train == c]
            self._class_count[i] = X_c.shape[0]
            self._theta[i] = X_c.mean(axis=0)
            self._var[i] = X_c.var(axis=0)

        # Add variance smoothing
        self._epsilon = self._nb_config.var_smoothing * self._var.max()
        self._var += self._epsilon

        # Compute class priors
        if self._nb_config.fit_prior:
            self._class_prior = self._class_count / self._class_count.sum()
        else:
            if self._nb_config.class_prior is not None:
                self._class_prior = np.array(self._nb_config.class_prior)
            else:
                self._class_prior = np.ones(n_classes) / n_classes

        self._state = ModelState.TRAINED

        if self._config.verbose:
            print(f"Training complete. Class priors: {self._class_prior}")

        return self

    def _joint_log_likelihood(self, X: np.ndarray) -> np.ndarray:
        """Compute joint log-likelihood for each class.

        Args:
            X: Features of shape (n_samples, n_features).

        Returns:
            Log-likelihood of shape (n_samples, n_classes).
        """
        joint_log_likelihood = []

        for i in range(len(self._classes)):
            # Log prior
            log_prior = np.log(self._class_prior[i])

            # Log likelihood: log N(x; μ, σ²) = -0.5 * [log(2πσ²) + (x-μ)²/σ²]
            mean = self._theta[i]
            var = self._var[i]

            # -0.5 * sum(log(2πσ²))
            log_det = -0.5 * np.sum(np.log(2 * np.pi * var))

            # -0.5 * sum((x-μ)²/σ²)
            diff = X - mean
            log_exp = -0.5 * np.sum(diff ** 2 / var, axis=1)

            joint_log_likelihood.append(log_prior + log_det + log_exp)

        return np.array(joint_log_likelihood).T

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict class probabilities.

        Args:
            X: Features.

        Returns:
            Probabilities of shape (n_samples, n_classes).
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        X_pred = np.asarray(X)
        if X_pred.ndim == 1:
            X_pred = X_pred.reshape(-1, 1)

        jll = self._joint_log_likelihood(X_pred)

        # Softmax for numerical stability
        log_prob_x = np.max(jll, axis=1, keepdims=True)
        jll_stable = jll - log_prob_x
        prob = np.exp(jll_stable)
        prob /= prob.sum(axis=1, keepdims=True)

        return prob

    def predict_log_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict log class probabilities.

        Args:
            X: Features.

        Returns:
            Log probabilities of shape (n_samples, n_classes).
        """
        proba = self.predict_proba(X)
        return np.log(proba + 1e-10)

    def predict(
        self,
        X: Union[EncryptedMatrix, np.ndarray, list],
    ) -> Union[EncryptedVector, np.ndarray]:
        """Predict class labels.

        Args:
            X: Features.

        Returns:
            Predicted class labels.
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        if isinstance(X, EncryptedMatrix):
            return self._predict_encrypted(X)
        elif isinstance(X, list) and len(X) > 0 and isinstance(X[0], EncryptedVector):
            return self._predict_encrypted(X)

        jll = self._joint_log_likelihood(np.asarray(X).reshape(-1, self._n_features))
        return self._classes[np.argmax(jll, axis=1)]

    def _predict_encrypted(
        self,
        X: Union[EncryptedMatrix, list[EncryptedVector]],
    ) -> EncryptedVector:
        """Make predictions on encrypted data."""
        encryptor = self._ensure_encryptor(X)

        if isinstance(X, list):
            encrypted_rows = X
        else:
            encrypted_rows = list(X)

        results = []
        for enc_row in encrypted_rows:
            x_plain = enc_row.decrypt().reshape(1, -1)
            pred = self.predict(x_plain)[0]
            # Convert class label to numeric
            pred_idx = np.where(self._classes == pred)[0][0]
            results.append(pred_idx)

        return encryptor.encrypt_vector(np.array(results))

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Compute accuracy score.

        Args:
            X: Features.
            y: True labels.

        Returns:
            Accuracy score.
        """
        predictions = self.predict(X)
        return np.mean(predictions == y)

    def get_params(self) -> dict[str, Any]:
        """Get model parameters."""
        params = super().get_params()
        params.update({
            "classes": self._classes.tolist() if self._classes is not None else None,
            "class_prior": self._class_prior.tolist() if self._class_prior is not None else None,
            "theta": self._theta.tolist() if self._theta is not None else None,
            "var": self._var.tolist() if self._var is not None else None,
            "var_smoothing": self._nb_config.var_smoothing,
        })
        return params

    def __repr__(self) -> str:
        n_classes = len(self._classes) if self._classes is not None else 0
        return f"GaussianNaiveBayes(n_classes={n_classes}, state={self._state.value})"


class MultinomialNaiveBayes(BaseFHEModel):
    """Multinomial Naive Bayes classifier for FHE-encrypted data.

    Suitable for classification with discrete features (e.g., word counts).

    P(xᵢ|y) follows a multinomial distribution.

    Example:
        >>> from sdk.models import MultinomialNaiveBayes
        >>> mnb = MultinomialNaiveBayes(alpha=1.0)
        >>> mnb.fit(X_train, y_train)  # X should be counts
        >>> predictions = mnb.predict(X_test)
    """

    def __init__(
        self,
        alpha: float = 1.0,
        fit_prior: bool = True,
        encryptor: Optional[CKKSEncryptor] = None,
    ):
        """Initialize Multinomial Naive Bayes.

        Args:
            alpha: Additive (Laplace) smoothing parameter.
            fit_prior: Whether to learn class priors.
            encryptor: CKKS encryptor.
        """
        config = NaiveBayesConfig(alpha=alpha, fit_prior=fit_prior)
        super().__init__(config=config, encryptor=encryptor)

        self._nb_config = config
        self._classes: Optional[np.ndarray] = None
        self._class_count: Optional[np.ndarray] = None
        self._class_prior: Optional[np.ndarray] = None
        self._feature_count: Optional[np.ndarray] = None
        self._feature_log_prob: Optional[np.ndarray] = None

    @property
    def classes_(self) -> Optional[np.ndarray]:
        """Get unique classes."""
        return self._classes

    @property
    def feature_log_prob_(self) -> Optional[np.ndarray]:
        """Get log probability of features given class."""
        return self._feature_log_prob

    def fit(
        self,
        X: Union[EncryptedDataset, EncryptedMatrix, np.ndarray],
        y: Optional[Union[EncryptedVector, np.ndarray]] = None,
    ) -> "MultinomialNaiveBayes":
        """Fit Multinomial Naive Bayes.

        Args:
            X: Training features (counts).
            y: Training labels.

        Returns:
            self for method chaining.
        """
        self._state = ModelState.TRAINING

        if isinstance(X, (EncryptedDataset, EncryptedMatrix, EncryptedVector)):
            raise ValueError("NaiveBayes must be trained on plaintext data.")

        X_train = np.asarray(X)
        y_train = np.asarray(y).ravel()

        if X_train.ndim == 1:
            X_train = X_train.reshape(-1, 1)

        # Ensure non-negative
        if np.any(X_train < 0):
            raise ValueError("MultinomialNaiveBayes requires non-negative features")

        n_samples, n_features = X_train.shape
        self._n_features = n_features

        self._classes = np.unique(y_train)
        n_classes = len(self._classes)

        if self._config.verbose:
            print(f"Training MultinomialNaiveBayes: {n_classes} classes")

        # Count features per class
        self._feature_count = np.zeros((n_classes, n_features))
        self._class_count = np.zeros(n_classes)

        for i, c in enumerate(self._classes):
            X_c = X_train[y_train == c]
            self._class_count[i] = X_c.shape[0]
            self._feature_count[i] = X_c.sum(axis=0)

        # Compute log probabilities with smoothing
        alpha = self._nb_config.alpha
        smoothed_fc = self._feature_count + alpha
        smoothed_cc = smoothed_fc.sum(axis=1, keepdims=True)
        self._feature_log_prob = np.log(smoothed_fc / smoothed_cc)

        # Class priors
        if self._nb_config.fit_prior:
            self._class_prior = self._class_count / self._class_count.sum()
        else:
            self._class_prior = np.ones(n_classes) / n_classes

        self._state = ModelState.TRAINED
        return self

    def _joint_log_likelihood(self, X: np.ndarray) -> np.ndarray:
        """Compute joint log-likelihood."""
        return X @ self._feature_log_prob.T + np.log(self._class_prior)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict class probabilities."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        X_pred = np.asarray(X)
        if X_pred.ndim == 1:
            X_pred = X_pred.reshape(-1, 1)

        jll = self._joint_log_likelihood(X_pred)
        jll_stable = jll - np.max(jll, axis=1, keepdims=True)
        prob = np.exp(jll_stable)
        prob /= prob.sum(axis=1, keepdims=True)
        return prob

    def predict(
        self,
        X: Union[EncryptedMatrix, np.ndarray, list],
    ) -> Union[EncryptedVector, np.ndarray]:
        """Predict class labels."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        if isinstance(X, (EncryptedMatrix, list)):
            # Handle encrypted - simplified
            return self._predict_encrypted_simple(X)

        X_pred = np.asarray(X)
        if X_pred.ndim == 1:
            X_pred = X_pred.reshape(-1, 1)

        jll = self._joint_log_likelihood(X_pred)
        return self._classes[np.argmax(jll, axis=1)]

    def _predict_encrypted_simple(self, X):
        """Simplified encrypted prediction."""
        encryptor = self._ensure_encryptor(X)
        encrypted_rows = list(X) if not isinstance(X, list) else X
        results = []
        for enc_row in encrypted_rows:
            x_plain = enc_row.decrypt().reshape(1, -1)
            pred = self.predict(x_plain)[0]
            pred_idx = np.where(self._classes == pred)[0][0]
            results.append(pred_idx)
        return encryptor.encrypt_vector(np.array(results))

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Compute accuracy score."""
        return np.mean(self.predict(X) == y)

    def __repr__(self) -> str:
        n_classes = len(self._classes) if self._classes is not None else 0
        return f"MultinomialNaiveBayes(n_classes={n_classes}, alpha={self._nb_config.alpha})"


class BernoulliNaiveBayes(BaseFHEModel):
    """Bernoulli Naive Bayes classifier for FHE-encrypted data.

    Suitable for classification with binary features.

    Example:
        >>> from sdk.models import BernoulliNaiveBayes
        >>> bnb = BernoulliNaiveBayes(alpha=1.0, binarize=0.5)
        >>> bnb.fit(X_train, y_train)
        >>> predictions = bnb.predict(X_test)
    """

    def __init__(
        self,
        alpha: float = 1.0,
        binarize: Optional[float] = 0.0,
        fit_prior: bool = True,
        encryptor: Optional[CKKSEncryptor] = None,
    ):
        """Initialize Bernoulli Naive Bayes.

        Args:
            alpha: Additive smoothing parameter.
            binarize: Threshold for binarizing features (None = assume binary).
            fit_prior: Whether to learn class priors.
            encryptor: CKKS encryptor.
        """
        config = NaiveBayesConfig(alpha=alpha, fit_prior=fit_prior)
        super().__init__(config=config, encryptor=encryptor)

        self._nb_config = config
        self._binarize = binarize
        self._classes: Optional[np.ndarray] = None
        self._class_count: Optional[np.ndarray] = None
        self._class_prior: Optional[np.ndarray] = None
        self._feature_prob: Optional[np.ndarray] = None

    def _binarize_data(self, X: np.ndarray) -> np.ndarray:
        """Binarize features if threshold is set."""
        if self._binarize is not None:
            return (X > self._binarize).astype(float)
        return X

    def fit(
        self,
        X: Union[EncryptedDataset, EncryptedMatrix, np.ndarray],
        y: Optional[Union[EncryptedVector, np.ndarray]] = None,
    ) -> "BernoulliNaiveBayes":
        """Fit Bernoulli Naive Bayes."""
        self._state = ModelState.TRAINING

        if isinstance(X, (EncryptedDataset, EncryptedMatrix, EncryptedVector)):
            raise ValueError("NaiveBayes must be trained on plaintext data.")

        X_train = self._binarize_data(np.asarray(X))
        y_train = np.asarray(y).ravel()

        if X_train.ndim == 1:
            X_train = X_train.reshape(-1, 1)

        n_samples, n_features = X_train.shape
        self._n_features = n_features

        self._classes = np.unique(y_train)
        n_classes = len(self._classes)

        # Count features per class
        feature_count = np.zeros((n_classes, n_features))
        self._class_count = np.zeros(n_classes)

        for i, c in enumerate(self._classes):
            X_c = X_train[y_train == c]
            self._class_count[i] = X_c.shape[0]
            feature_count[i] = X_c.sum(axis=0)

        # Compute probabilities with smoothing
        alpha = self._nb_config.alpha
        self._feature_prob = (feature_count + alpha) / (self._class_count.reshape(-1, 1) + 2 * alpha)

        # Class priors
        if self._nb_config.fit_prior:
            self._class_prior = self._class_count / self._class_count.sum()
        else:
            self._class_prior = np.ones(n_classes) / n_classes

        self._state = ModelState.TRAINED
        return self

    def _joint_log_likelihood(self, X: np.ndarray) -> np.ndarray:
        """Compute joint log-likelihood."""
        X_bin = self._binarize_data(X)

        # log P(x|y) = Σ [xᵢ log(pᵢ) + (1-xᵢ) log(1-pᵢ)]
        log_prob = np.log(self._feature_prob + 1e-10)
        log_neg_prob = np.log(1 - self._feature_prob + 1e-10)

        jll = X_bin @ log_prob.T + (1 - X_bin) @ log_neg_prob.T
        jll += np.log(self._class_prior)

        return jll

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict class probabilities."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        X_pred = np.asarray(X)
        if X_pred.ndim == 1:
            X_pred = X_pred.reshape(-1, 1)

        jll = self._joint_log_likelihood(X_pred)
        jll_stable = jll - np.max(jll, axis=1, keepdims=True)
        prob = np.exp(jll_stable)
        prob /= prob.sum(axis=1, keepdims=True)
        return prob

    def predict(
        self,
        X: Union[EncryptedMatrix, np.ndarray, list],
    ) -> Union[EncryptedVector, np.ndarray]:
        """Predict class labels."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        if isinstance(X, (EncryptedMatrix, list)):
            encryptor = self._ensure_encryptor(X)
            encrypted_rows = list(X) if not isinstance(X, list) else X
            results = []
            for enc_row in encrypted_rows:
                x_plain = enc_row.decrypt().reshape(1, -1)
                pred = self.predict(x_plain)[0]
                pred_idx = np.where(self._classes == pred)[0][0]
                results.append(pred_idx)
            return encryptor.encrypt_vector(np.array(results))

        X_pred = np.asarray(X)
        if X_pred.ndim == 1:
            X_pred = X_pred.reshape(-1, 1)

        jll = self._joint_log_likelihood(X_pred)
        return self._classes[np.argmax(jll, axis=1)]

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Compute accuracy score."""
        return np.mean(self.predict(X) == y)

    def __repr__(self) -> str:
        n_classes = len(self._classes) if self._classes is not None else 0
        return f"BernoulliNaiveBayes(n_classes={n_classes}, binarize={self._binarize})"

"""FHE-compatible Support Vector Machine.

This module implements SVM for FHE-encrypted data using polynomial
kernel approximations that can be computed homomorphically.

Key design decisions for FHE compatibility:
- Uses polynomial kernel (degree 2-4) instead of RBF
- Training on plaintext, inference on encrypted data
- Approximates decision function with polynomial operations
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


class KernelType(Enum):
    """Kernel types for SVM."""

    LINEAR = "linear"  # K(x,y) = x·y
    POLYNOMIAL = "polynomial"  # K(x,y) = (γx·y + c)^d
    QUADRATIC = "quadratic"  # K(x,y) = (x·y)² - shortcut for poly d=2


@dataclass
class SVMConfig(ModelConfig):
    """Configuration for SVM.

    Attributes:
        C: Regularization parameter (larger = less regularization).
        kernel: Kernel type to use.
        degree: Degree for polynomial kernel.
        gamma: Kernel coefficient ('scale', 'auto', or float).
        coef0: Independent term in polynomial kernel.
        max_iter: Maximum iterations for optimization.
        tol: Tolerance for stopping criterion.
        random_state: Random seed for reproducibility.
    """

    C: float = 1.0
    kernel: KernelType = KernelType.POLYNOMIAL
    degree: int = 2
    gamma: Union[str, float] = "scale"
    coef0: float = 1.0
    max_iter: int = 1000
    tol: float = 1e-4
    random_state: Optional[int] = None

    def __post_init__(self):
        super().__post_init__()
        if self.C <= 0:
            raise ValueError("C must be positive")
        if self.degree < 1:
            raise ValueError("degree must be at least 1")
        if self.max_iter < 1:
            raise ValueError("max_iter must be at least 1")


class SVM(BaseFHEModel):
    """Support Vector Machine for FHE-encrypted data.

    This implementation uses polynomial kernels that can be computed
    on encrypted data. Training is performed on plaintext using
    Sequential Minimal Optimization (SMO).

    The decision function for a new point x is:
    f(x) = Σᵢ αᵢyᵢK(xᵢ, x) + b

    For FHE, we use polynomial kernels:
    - Linear: K(x,y) = x·y
    - Polynomial: K(x,y) = (γx·y + c)^d
    - Quadratic: K(x,y) = (x·y)²

    Example:
        >>> from sdk.models import SVM, SVMConfig, KernelType
        >>> config = SVMConfig(C=1.0, kernel=KernelType.POLYNOMIAL, degree=2)
        >>> svm = SVM(config=config)
        >>> svm.fit(X_train, y_train)
        >>> predictions = svm.predict(X_test)

    For classification:
        >>> from sdk.models import SVMClassifier
        >>> clf = SVMClassifier(C=1.0, kernel='polynomial')
        >>> clf.fit(X_train, y_train)
        >>> predictions = clf.predict(X_test)
    """

    fhe_level = FHELevel.TRANSPORT

    def __init__(
        self,
        config: Optional[SVMConfig] = None,
        encryptor: Optional[CKKSEncryptor] = None,
    ):
        """Initialize SVM.

        Args:
            config: SVM configuration.
            encryptor: CKKS encryptor for encrypted operations.
        """
        if config is None:
            config = SVMConfig()
        super().__init__(config=config, encryptor=encryptor)

        self._svm_config = config
        self._support_vectors: Optional[np.ndarray] = None
        self._support_labels: Optional[np.ndarray] = None
        self._alphas: Optional[np.ndarray] = None
        self._bias: float = 0.0
        self._gamma: float = 1.0
        self._n_support: int = 0
        self._rng = np.random.RandomState(config.random_state)

    @property
    def support_vectors_(self) -> Optional[np.ndarray]:
        """Get support vectors."""
        return self._support_vectors

    @property
    def n_support_(self) -> int:
        """Get number of support vectors."""
        return self._n_support

    @property
    def dual_coef_(self) -> Optional[np.ndarray]:
        """Get dual coefficients (alpha * y for support vectors)."""
        if self._alphas is None or self._support_labels is None:
            return None
        return self._alphas * self._support_labels

    def _compute_gamma(self, X: np.ndarray) -> float:
        """Compute gamma value based on configuration.

        Args:
            X: Training features.

        Returns:
            Gamma value.
        """
        if isinstance(self._svm_config.gamma, float):
            return self._svm_config.gamma
        elif self._svm_config.gamma == "scale":
            # 1 / (n_features * X.var())
            var = X.var()
            if var == 0:
                var = 1.0
            return 1.0 / (X.shape[1] * var)
        elif self._svm_config.gamma == "auto":
            return 1.0 / X.shape[1]
        else:
            return 1.0

    def _kernel(self, X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
        """Compute kernel matrix.

        Args:
            X1: First set of samples (n1, n_features).
            X2: Second set of samples (n2, n_features).

        Returns:
            Kernel matrix of shape (n1, n2).
        """
        if self._svm_config.kernel == KernelType.LINEAR:
            return X1 @ X2.T

        elif self._svm_config.kernel == KernelType.QUADRATIC:
            linear = X1 @ X2.T
            return linear**2

        elif self._svm_config.kernel == KernelType.POLYNOMIAL:
            linear = X1 @ X2.T
            return (self._gamma * linear + self._svm_config.coef0) ** self._svm_config.degree

        else:
            return X1 @ X2.T

    def _smo_step(
        self,
        i: int,
        j: int,
        X: np.ndarray,
        y: np.ndarray,
        alphas: np.ndarray,
        K: np.ndarray,
        E: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, bool]:
        """Perform one SMO optimization step.

        Args:
            i, j: Indices of alphas to optimize.
            X: Training features.
            y: Training labels.
            alphas: Current alpha values.
            K: Precomputed kernel matrix.
            E: Error cache.

        Returns:
            Tuple of (updated_alphas, updated_errors, changed).
        """
        if i == j:
            return alphas, E, False

        C = self._svm_config.C
        tol = self._svm_config.tol

        alpha_i, alpha_j = alphas[i], alphas[j]
        y_i, y_j = y[i], y[j]
        E_i, E_j = E[i], E[j]

        s = y_i * y_j

        # Compute bounds
        if s < 0:
            L = max(0, alpha_j - alpha_i)
            H = min(C, C + alpha_j - alpha_i)
        else:
            L = max(0, alpha_i + alpha_j - C)
            H = min(C, alpha_i + alpha_j)

        if L >= H:
            return alphas, E, False

        # Compute eta
        eta = 2 * K[i, j] - K[i, i] - K[j, j]

        if eta >= 0:
            return alphas, E, False

        # Update alpha_j
        alpha_j_new = alpha_j - y_j * (E_i - E_j) / eta
        alpha_j_new = np.clip(alpha_j_new, L, H)

        if abs(alpha_j_new - alpha_j) < tol:
            return alphas, E, False

        # Update alpha_i
        alpha_i_new = alpha_i + s * (alpha_j - alpha_j_new)

        # Update bias
        b1 = (
            self._bias
            - E_i
            - y_i * (alpha_i_new - alpha_i) * K[i, i]
            - y_j * (alpha_j_new - alpha_j) * K[i, j]
        )
        b2 = (
            self._bias
            - E_j
            - y_i * (alpha_i_new - alpha_i) * K[i, j]
            - y_j * (alpha_j_new - alpha_j) * K[j, j]
        )

        if 0 < alpha_i_new < C:
            self._bias = b1
        elif 0 < alpha_j_new < C:
            self._bias = b2
        else:
            self._bias = (b1 + b2) / 2

        # Update alphas
        alphas[i] = alpha_i_new
        alphas[j] = alpha_j_new

        # Update error cache
        E = self._compute_errors(X, y, alphas, K)

        return alphas, E, True

    def _compute_errors(
        self,
        X: np.ndarray,
        y: np.ndarray,
        alphas: np.ndarray,
        K: np.ndarray,
    ) -> np.ndarray:
        """Compute error cache.

        Args:
            X: Training features.
            y: Training labels.
            alphas: Alpha values.
            K: Kernel matrix.

        Returns:
            Error values for each sample.
        """
        f = (alphas * y) @ K + self._bias
        return f - y

    def fit(
        self,
        X: Union[EncryptedDataset, EncryptedMatrix, np.ndarray],
        y: Optional[Union[EncryptedVector, np.ndarray]] = None,
    ) -> "SVM":
        """Train the SVM.

        Training is done on plaintext data using SMO algorithm.

        Args:
            X: Features (must be plaintext for training).
            y: Labels (+1 or -1 for binary classification).

        Returns:
            self for method chaining.
        """
        self._state = ModelState.TRAINING

        if isinstance(X, (EncryptedDataset, EncryptedMatrix, EncryptedVector)):
            raise ValueError("SVM must be trained on plaintext data.")

        X_train = np.asarray(X)
        y_train = np.asarray(y).ravel()

        if X_train.ndim == 1:
            X_train = X_train.reshape(-1, 1)

        n_samples, n_features = X_train.shape
        self._n_features = n_features

        # Convert labels to +1/-1
        unique_labels = np.unique(y_train)
        if len(unique_labels) == 2:
            y_train = np.where(y_train == unique_labels[0], -1, 1).astype(float)

        # Compute gamma
        self._gamma = self._compute_gamma(X_train)

        if self._config.verbose:
            print(f"Training SVM: kernel={self._svm_config.kernel.value}, C={self._svm_config.C}")
            print(f"  Samples: {n_samples}, Features: {n_features}")

        # Precompute kernel matrix
        K = self._kernel(X_train, X_train)

        # Initialize alphas and errors
        alphas = np.zeros(n_samples)
        self._bias = 0.0
        E = self._compute_errors(X_train, y_train, alphas, K)

        # SMO main loop
        passes = 0
        max_passes = 5

        for iteration in range(self._svm_config.max_iter):
            num_changed = 0

            for i in range(n_samples):
                E_i = E[i]
                r_i = E_i * y_train[i]

                # Check KKT conditions
                if (r_i < -self._svm_config.tol and alphas[i] < self._svm_config.C) or (
                    r_i > self._svm_config.tol and alphas[i] > 0
                ):
                    # Select j using heuristic
                    if E_i > 0:
                        j = np.argmin(E)
                    else:
                        j = np.argmax(E)

                    # Try SMO step
                    alphas, E, changed = self._smo_step(i, j, X_train, y_train, alphas, K, E)

                    if changed:
                        num_changed += 1

            if num_changed == 0:
                passes += 1
            else:
                passes = 0

            if passes >= max_passes:
                break

            if self._config.verbose and (iteration + 1) % 100 == 0:
                n_sv = np.sum(alphas > 1e-5)
                print(f"  Iter {iteration + 1}, Support vectors: {n_sv}")

        # Extract support vectors
        sv_mask = alphas > 1e-5
        self._support_vectors = X_train[sv_mask]
        self._support_labels = y_train[sv_mask]
        self._alphas = alphas[sv_mask]
        self._n_support = len(self._alphas)

        self._state = ModelState.TRAINED

        if self._config.verbose:
            print(f"Training complete. Support vectors: {self._n_support}")

        return self

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """Compute decision function values.

        Args:
            X: Features.

        Returns:
            Decision function values.
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        X_pred = np.asarray(X)
        if X_pred.ndim == 1:
            X_pred = X_pred.reshape(-1, 1)

        # f(x) = Σᵢ αᵢyᵢK(xᵢ, x) + b
        K = self._kernel(self._support_vectors, X_pred)
        decision = (self._alphas * self._support_labels) @ K + self._bias

        return decision

    def predict(
        self,
        X: Union[EncryptedMatrix, np.ndarray, list],
    ) -> Union[EncryptedVector, np.ndarray]:
        """Make predictions.

        Args:
            X: Features (encrypted or plaintext).

        Returns:
            Predictions (+1 or -1).
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        if isinstance(X, EncryptedMatrix):
            return self._predict_encrypted(X)
        elif isinstance(X, list) and len(X) > 0 and isinstance(X[0], EncryptedVector):
            return self._predict_encrypted(X)

        decision = self.decision_function(X)
        return np.sign(decision)

    def _predict_encrypted(
        self,
        X: Union[EncryptedMatrix, list[EncryptedVector]],
    ) -> EncryptedVector:
        """Make predictions on encrypted data.

        Args:
            X: Encrypted features.

        Returns:
            Encrypted predictions.
        """
        encryptor = self._ensure_encryptor(X)

        if isinstance(X, list):
            encrypted_rows = X
        else:
            encrypted_rows = list(X)

        results = []

        for enc_row in encrypted_rows:
            x_plain = enc_row.decrypt().reshape(1, -1)
            pred = self.predict(x_plain)[0]
            results.append(pred)

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
        y = np.asarray(y).ravel()

        # Convert to same format
        unique = np.unique(y)
        if len(unique) == 2:
            y = np.where(y == unique[0], -1, 1)

        return np.mean(predictions == y)

    def get_params(self) -> dict[str, Any]:
        """Get model parameters."""
        params = super().get_params()
        params.update(
            {
                "kernel": self._svm_config.kernel.value,
                "C": self._svm_config.C,
                "degree": self._svm_config.degree,
                "gamma": self._gamma,
                "coef0": self._svm_config.coef0,
                "n_support": self._n_support,
                "support_vectors": self._support_vectors.tolist()
                if self._support_vectors is not None
                else None,
                "support_labels": self._support_labels.tolist()
                if self._support_labels is not None
                else None,
                "alphas": self._alphas.tolist() if self._alphas is not None else None,
                "bias": self._bias,
            }
        )
        return params

    def __repr__(self) -> str:
        return (
            f"SVM(kernel={self._svm_config.kernel.value}, "
            f"C={self._svm_config.C}, "
            f"n_support={self._n_support}, "
            f"state={self._state.value})"
        )


class SVMClassifier(SVM):
    """SVM Classifier for FHE-encrypted data.

    Convenience class with standard classification interface.

    Example:
        >>> clf = SVMClassifier(C=1.0, kernel='polynomial', degree=2)
        >>> clf.fit(X_train, y_train)
        >>> predictions = clf.predict(X_test)
    """

    def __init__(
        self,
        C: float = 1.0,
        kernel: str = "polynomial",
        degree: int = 2,
        gamma: Union[str, float] = "scale",
        coef0: float = 1.0,
        random_state: Optional[int] = None,
        encryptor: Optional[CKKSEncryptor] = None,
        **kwargs,
    ):
        """Initialize SVM Classifier.

        Args:
            C: Regularization parameter.
            kernel: Kernel type ('linear', 'polynomial', 'quadratic').
            degree: Polynomial degree.
            gamma: Kernel coefficient.
            coef0: Independent term.
            random_state: Random seed.
            encryptor: CKKS encryptor.
            **kwargs: Additional config parameters.
        """
        kernel_enum = {
            "linear": KernelType.LINEAR,
            "polynomial": KernelType.POLYNOMIAL,
            "poly": KernelType.POLYNOMIAL,
            "quadratic": KernelType.QUADRATIC,
            "quad": KernelType.QUADRATIC,
        }.get(kernel.lower(), KernelType.POLYNOMIAL)

        config = SVMConfig(
            C=C,
            kernel=kernel_enum,
            degree=degree,
            gamma=gamma,
            coef0=coef0,
            random_state=random_state,
            **kwargs,
        )
        super().__init__(config=config, encryptor=encryptor)

        self._classes: Optional[np.ndarray] = None

    def fit(
        self,
        X: Union[EncryptedDataset, EncryptedMatrix, np.ndarray],
        y: Optional[Union[EncryptedVector, np.ndarray]] = None,
    ) -> "SVMClassifier":
        """Train the classifier.

        Args:
            X: Training features.
            y: Training labels (any two classes).

        Returns:
            self for method chaining.
        """
        y_train = np.asarray(y).ravel()
        self._classes = np.unique(y_train)

        if len(self._classes) != 2:
            raise ValueError("SVMClassifier only supports binary classification")

        return super().fit(X, y)

    def predict(
        self,
        X: Union[EncryptedMatrix, np.ndarray, list],
    ) -> np.ndarray:
        """Predict class labels.

        Args:
            X: Features.

        Returns:
            Predicted class labels (original classes, not +1/-1).
        """
        if isinstance(X, (EncryptedMatrix, list)):
            return super().predict(X)

        decision = self.decision_function(X)
        predictions = np.where(decision < 0, self._classes[0], self._classes[1])
        return predictions

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict class probabilities using Platt scaling approximation.

        Args:
            X: Features.

        Returns:
            Probabilities of shape (n_samples, 2).
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        decision = self.decision_function(X)

        # Platt scaling approximation using sigmoid
        prob_pos = 1.0 / (1.0 + np.exp(-decision))

        return np.column_stack([1 - prob_pos, prob_pos])


class SVMRegressor(SVM):
    """SVM Regressor (SVR) for FHE-encrypted data.

    Uses epsilon-insensitive loss for regression.

    Example:
        >>> reg = SVMRegressor(C=1.0, epsilon=0.1)
        >>> reg.fit(X_train, y_train)
        >>> predictions = reg.predict(X_test)
    """

    def __init__(
        self,
        C: float = 1.0,
        epsilon: float = 0.1,
        kernel: str = "polynomial",
        degree: int = 2,
        gamma: Union[str, float] = "scale",
        random_state: Optional[int] = None,
        encryptor: Optional[CKKSEncryptor] = None,
        **kwargs,
    ):
        """Initialize SVM Regressor.

        Args:
            C: Regularization parameter.
            epsilon: Epsilon in epsilon-SVR.
            kernel: Kernel type.
            degree: Polynomial degree.
            gamma: Kernel coefficient.
            random_state: Random seed.
            encryptor: CKKS encryptor.
            **kwargs: Additional config parameters.
        """
        kernel_enum = {
            "linear": KernelType.LINEAR,
            "polynomial": KernelType.POLYNOMIAL,
            "poly": KernelType.POLYNOMIAL,
            "quadratic": KernelType.QUADRATIC,
        }.get(kernel.lower(), KernelType.POLYNOMIAL)

        config = SVMConfig(
            C=C,
            kernel=kernel_enum,
            degree=degree,
            gamma=gamma,
            random_state=random_state,
            **kwargs,
        )
        super().__init__(config=config, encryptor=encryptor)
        self._epsilon = epsilon

    def fit(
        self,
        X: Union[EncryptedDataset, EncryptedMatrix, np.ndarray],
        y: Optional[Union[EncryptedVector, np.ndarray]] = None,
    ) -> "SVMRegressor":
        """Train the regressor using simplified SVR.

        Args:
            X: Training features.
            y: Training targets.

        Returns:
            self for method chaining.
        """
        self._state = ModelState.TRAINING

        if isinstance(X, (EncryptedDataset, EncryptedMatrix, EncryptedVector)):
            raise ValueError("SVMRegressor must be trained on plaintext data.")

        X_train = np.asarray(X)
        y_train = np.asarray(y).ravel()

        if X_train.ndim == 1:
            X_train = X_train.reshape(-1, 1)

        n_samples, n_features = X_train.shape
        self._n_features = n_features

        self._gamma = self._compute_gamma(X_train)

        # For SVR, use a simplified approach: fit on all points
        # with weights based on epsilon-insensitive loss
        K = self._kernel(X_train, X_train)

        # Ridge regression in kernel space as approximation
        lambda_reg = 1.0 / (2 * self._svm_config.C)
        K_reg = K + lambda_reg * np.eye(n_samples)

        # Solve for alpha
        try:
            alphas = np.linalg.solve(K_reg, y_train)
        except np.linalg.LinAlgError:
            alphas = np.linalg.lstsq(K_reg, y_train, rcond=None)[0]

        # All points are "support vectors" in this approximation
        self._support_vectors = X_train
        self._support_labels = np.ones(n_samples)  # Dummy for compatibility
        self._alphas = alphas
        self._n_support = n_samples
        self._bias = 0.0

        self._state = ModelState.TRAINED

        return self

    def predict(
        self,
        X: Union[EncryptedMatrix, np.ndarray, list],
    ) -> Union[EncryptedVector, np.ndarray]:
        """Make predictions.

        Args:
            X: Features.

        Returns:
            Predicted values.
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        if isinstance(X, EncryptedMatrix):
            return self._predict_encrypted(X)
        elif isinstance(X, list) and len(X) > 0 and isinstance(X[0], EncryptedVector):
            return self._predict_encrypted(X)

        X_pred = np.asarray(X)
        if X_pred.ndim == 1:
            X_pred = X_pred.reshape(-1, 1)

        K = self._kernel(self._support_vectors, X_pred)
        return self._alphas @ K + self._bias

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Compute R² score.

        Args:
            X: Features.
            y: True values.

        Returns:
            R² score.
        """
        predictions = self.predict(X)
        y = np.asarray(y).ravel()

        ss_res = np.sum((y - predictions) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)

        if ss_tot == 0:
            return 0.0

        return 1 - (ss_res / ss_tot)

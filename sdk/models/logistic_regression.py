"""Logistic regression model with FHE support.

This module implements logistic regression for binary classification
on encrypted data using polynomial approximations of the sigmoid function.
"""

from enum import Enum
from typing import Optional, Union

import numpy as np

from ..encryption.ckks_wrapper import (
    CKKSEncryptor,
    EncryptedMatrix,
    EncryptedVector,
)
from ..utils.data_loader import EncryptedDataset
from .base import BaseFHEModel, FHELevel, ModelConfig, ModelState


class SigmoidApproximation(Enum):
    """Polynomial approximation methods for sigmoid function.

    In FHE, we cannot compute exp() directly, so we use polynomial
    approximations of sigmoid: σ(x) = 1 / (1 + exp(-x))
    """

    # Linear approximation: σ(x) ≈ 0.5 + 0.25x
    # Fast but less accurate, good for |x| < 2
    LINEAR = "linear"

    # Degree-3 polynomial: σ(x) ≈ 0.5 + 0.197x - 0.004x³
    # Good balance of accuracy and depth
    DEGREE3 = "degree3"

    # Degree-5 polynomial for higher accuracy
    # σ(x) ≈ 0.5 + 0.197x - 0.004x³ + 0.0001x⁵
    DEGREE5 = "degree5"

    # Minimax polynomial optimized for [-8, 8] range
    MINIMAX = "minimax"


class LogisticRegression(BaseFHEModel):
    """Logistic Regression model for encrypted binary classification.

    This model performs logistic regression on CKKS-encrypted data
    using polynomial approximations of the sigmoid function for
    FHE-compatible computation.

    The model learns: P(y=1|x) = σ(X @ w + b)

    Where σ is approximated by a polynomial for FHE computation.

    Example:
        >>> from sdk import SecureDataLoader, FHEModel
        >>> loader = SecureDataLoader()
        >>> encrypted = loader.encrypt(df, target_column="label")
        >>> model = FHEModel.LogisticRegression(n_epochs=100)
        >>> model.fit(encrypted)
        >>> probs = model.predict_proba(encrypted.X)

    Attributes:
        weights: Model weights (plaintext after training).
        bias: Model bias term (plaintext after training).
        sigmoid_approx: Sigmoid approximation method used.
    """

    fhe_level = FHELevel.PARTIAL

    # Polynomial coefficients for sigmoid approximations
    SIGMOID_COEFFS = {
        SigmoidApproximation.LINEAR: [0.5, 0.25],
        SigmoidApproximation.DEGREE3: [0.5, 0.197, 0.0, -0.004],
        SigmoidApproximation.DEGREE5: [0.5, 0.197, 0.0, -0.004, 0.0, 0.0001],
        # Minimax coefficients optimized for [-8, 8]
        SigmoidApproximation.MINIMAX: [0.5, 0.1971, 0.0, -0.0044, 0.0, 0.0001],
    }

    def __init__(
        self,
        learning_rate: float = 0.1,
        n_epochs: int = 100,
        batch_size: Optional[int] = None,
        verbose: bool = False,
        early_stopping_patience: Optional[int] = None,
        tolerance: float = 1e-4,
        regularization: float = 0.0,
        sigmoid_approx: SigmoidApproximation = SigmoidApproximation.DEGREE3,
        threshold: float = 0.5,
        encryptor: Optional[CKKSEncryptor] = None,
    ):
        """Initialize Logistic Regression model.

        Args:
            learning_rate: Step size for gradient descent.
            n_epochs: Number of training epochs.
            batch_size: Samples per batch (None = full batch).
            verbose: Whether to print training progress.
            early_stopping_patience: Epochs without improvement before stopping.
            tolerance: Minimum loss improvement for early stopping.
            regularization: L2 regularization strength.
            sigmoid_approx: Polynomial approximation for sigmoid.
            threshold: Classification threshold (default 0.5).
            encryptor: Optional CKKS encryptor.
        """
        config = ModelConfig(
            learning_rate=learning_rate,
            n_epochs=n_epochs,
            batch_size=batch_size,
            verbose=verbose,
            early_stopping_patience=early_stopping_patience,
            tolerance=tolerance,
        )
        super().__init__(config=config, encryptor=encryptor)
        self._regularization = regularization
        self._sigmoid_approx = sigmoid_approx
        self._threshold = threshold

    @property
    def sigmoid_approx(self) -> SigmoidApproximation:
        """Get sigmoid approximation method."""
        return self._sigmoid_approx

    @property
    def threshold(self) -> float:
        """Get classification threshold."""
        return self._threshold

    def _initialize_weights(self, n_features: int) -> None:
        """Initialize model weights with small random values."""
        scale = np.sqrt(2.0 / (n_features + 1))
        self._weights = np.random.randn(n_features) * scale
        self._bias = 0.0
        self._n_features = n_features

    def _sigmoid(self, x: np.ndarray) -> np.ndarray:
        """Compute true sigmoid for plaintext training."""
        # Clip to avoid overflow
        x = np.clip(x, -500, 500)
        return 1.0 / (1.0 + np.exp(-x))

    def _sigmoid_polynomial(self, x: np.ndarray) -> np.ndarray:
        """Compute polynomial approximation of sigmoid.

        This is what would be computed on encrypted data.
        """
        coeffs = self.SIGMOID_COEFFS[self._sigmoid_approx]
        result = np.zeros_like(x)

        for i, coeff in enumerate(coeffs):
            if coeff != 0:
                result += coeff * (x**i)

        # Clip to [0, 1] for numerical stability
        return np.clip(result, 0.0, 1.0)

    def _compute_loss_and_gradients(
        self,
        X_plain: np.ndarray,
        y_plain: np.ndarray,
        use_polynomial: bool = False,
    ) -> tuple[float, np.ndarray, float]:
        """Compute binary cross-entropy loss and gradients.

        Args:
            X_plain: Feature matrix (n_samples, n_features).
            y_plain: Binary target vector (n_samples,).
            use_polynomial: If True, use polynomial sigmoid approximation.

        Returns:
            Tuple of (loss, weight_gradients, bias_gradient).
        """
        n_samples = X_plain.shape[0]

        # Forward pass: compute logits
        logits = X_plain @ self._weights + self._bias

        # Compute probabilities
        if use_polynomial:
            probs = self._sigmoid_polynomial(logits)
        else:
            probs = self._sigmoid(logits)

        # Clip probs for numerical stability in log
        eps = 1e-7
        probs_clipped = np.clip(probs, eps, 1 - eps)

        # Binary cross-entropy loss
        loss = -np.mean(y_plain * np.log(probs_clipped) + (1 - y_plain) * np.log(1 - probs_clipped))

        # Add L2 regularization to loss
        if self._regularization > 0:
            loss += 0.5 * self._regularization * np.sum(self._weights**2)

        # Gradients
        errors = probs - y_plain
        dw = (1 / n_samples) * (X_plain.T @ errors)
        if self._regularization > 0:
            dw += self._regularization * self._weights
        db = (1 / n_samples) * np.sum(errors)

        return loss, dw, db

    def fit(
        self,
        X: Union[EncryptedDataset, EncryptedMatrix],
        y: Optional[EncryptedVector] = None,
    ) -> "LogisticRegression":
        """Train the model on encrypted data.

        Training uses gradient descent with binary cross-entropy loss.
        Data is temporarily decrypted for gradient computation in a
        trusted environment.

        Args:
            X: Encrypted features (EncryptedDataset or EncryptedMatrix).
            y: Encrypted binary target (0 or 1).

        Returns:
            self for method chaining.

        Raises:
            ValueError: If target is missing or not binary.
        """
        # Extract X and y
        if isinstance(X, EncryptedDataset):
            if X.y is None:
                raise ValueError(
                    "EncryptedDataset must include target (y). "
                    "Use encrypt(df, target_column='col') when encrypting."
                )
            encrypted_y = X.y
            encrypted_X = X.X
            n_features = X.n_features
        else:
            if y is None:
                raise ValueError("Target y is required when X is EncryptedMatrix")
            encrypted_y = y
            encrypted_X = X
            n_features = X.shape[1]

        # Get encryptor
        encryptor = self._ensure_encryptor(encrypted_X)

        # Initialize weights
        self._initialize_weights(n_features)
        self._state = ModelState.TRAINING

        # Decrypt data for training (in trusted environment)
        X_plain = encryptor.decrypt_matrix(encrypted_X)
        y_plain = encryptor.decrypt_vector(encrypted_y)

        # Validate binary target (after denormalization it should be ~0 or ~1)
        unique_vals = np.unique(np.round(y_plain))
        if len(unique_vals) > 2:
            # Normalize y to [0, 1] if needed
            y_min, y_max = y_plain.min(), y_plain.max()
            if y_min != y_max:
                y_plain = (y_plain - y_min) / (y_max - y_min)

        # Training loop
        best_loss = float("inf")
        patience_counter = 0

        for epoch in range(self._config.n_epochs):
            # Compute loss and gradients
            loss, dw, db = self._compute_loss_and_gradients(X_plain, y_plain)

            # Update weights
            self._weights -= self._config.learning_rate * dw
            self._bias -= self._config.learning_rate * db

            # Record history
            self._history.add_epoch(loss)

            # Verbose output
            if self._config.verbose and (epoch + 1) % 10 == 0:
                acc = self._compute_accuracy(X_plain, y_plain)
                print(
                    f"Epoch {epoch + 1}/{self._config.n_epochs}, "
                    f"Loss: {loss:.6f}, Accuracy: {acc:.4f}"
                )

            # Early stopping
            if self._config.early_stopping_patience is not None:
                if loss < best_loss - self._config.tolerance:
                    best_loss = loss
                    patience_counter = 0
                else:
                    patience_counter += 1

                if patience_counter >= self._config.early_stopping_patience:
                    if self._config.verbose:
                        print(f"Early stopping at epoch {epoch + 1}")
                    break

        self._state = ModelState.TRAINED
        return self

    def _compute_accuracy(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> float:
        """Compute classification accuracy."""
        probs = self._sigmoid(X @ self._weights + self._bias)
        predictions = (probs >= self._threshold).astype(int)
        y_binary = (y >= 0.5).astype(int)
        return np.mean(predictions == y_binary)

    def predict_proba(
        self,
        X: Union[EncryptedMatrix, EncryptedVector],
    ) -> EncryptedVector:
        """Predict class probabilities on encrypted data.

        Uses polynomial sigmoid approximation for FHE computation.

        Args:
            X: Encrypted features.

        Returns:
            Encrypted probability predictions.

        Raises:
            RuntimeError: If model is not fitted.
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        encryptor = self._ensure_encryptor(X)
        coeffs = self.SIGMOID_COEFFS[self._sigmoid_approx]

        if isinstance(X, EncryptedVector):
            # Single sample
            weighted = X.ciphertext * self._weights.tolist()
            logit = weighted.sum() + self._bias

            # Apply polynomial sigmoid
            # result = c0 + c1*x + c2*x² + c3*x³ + ...
            prob = coeffs[0]
            x_power = logit
            for i in range(1, len(coeffs)):
                if coeffs[i] != 0:
                    prob = prob + coeffs[i] * x_power
                if i < len(coeffs) - 1:
                    x_power = x_power * logit

            return EncryptedVector(prob, (1,))

        # Multiple samples
        all_probs = []
        for enc_row in X:
            weighted = enc_row.ciphertext * self._weights.tolist()
            logit = weighted.sum() + self._bias

            # Decrypt to apply polynomial (in production would be FHE)
            logit_plain = logit.decrypt()[0]
            prob = self._sigmoid_polynomial(np.array([logit_plain]))[0]
            all_probs.append(prob)

        return encryptor.encrypt_vector(all_probs)

    def predict(
        self,
        X: Union[EncryptedMatrix, EncryptedVector],
    ) -> EncryptedVector:
        """Predict class labels on encrypted data.

        Args:
            X: Encrypted features.

        Returns:
            Encrypted class predictions (0 or 1).

        Raises:
            RuntimeError: If model is not fitted.
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        encryptor = self._ensure_encryptor(X)

        # Get probabilities
        probs_enc = self.predict_proba(X)
        probs = encryptor.decrypt_vector(probs_enc)

        # Apply threshold
        predictions = (probs >= self._threshold).astype(float)

        return encryptor.encrypt_vector(predictions.tolist())

    def predict_proba_plaintext(self, X: np.ndarray) -> np.ndarray:
        """Predict probabilities on plaintext data.

        Args:
            X: Feature matrix.

        Returns:
            Probability predictions.
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        if X.ndim == 1:
            X = X.reshape(1, -1)

        logits = X @ self._weights + self._bias
        return self._sigmoid(logits)

    def predict_plaintext(self, X: np.ndarray) -> np.ndarray:
        """Predict class labels on plaintext data.

        Args:
            X: Feature matrix.

        Returns:
            Class predictions (0 or 1).
        """
        probs = self.predict_proba_plaintext(X)
        return (probs >= self._threshold).astype(int)

    def score(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> float:
        """Compute accuracy score on plaintext data.

        Args:
            X: Feature matrix.
            y: True labels (0 or 1).

        Returns:
            Classification accuracy.
        """
        predictions = self.predict_plaintext(X)
        y_binary = (y >= 0.5).astype(int)
        return np.mean(predictions == y_binary)

    def get_params(self) -> dict:
        """Get model parameters as dictionary."""
        params = super().get_params()
        params["sigmoid_approx"] = self._sigmoid_approx.value
        params["threshold"] = self._threshold
        return params

    def __repr__(self) -> str:
        state = self._state.value
        lr = self._config.learning_rate
        approx = self._sigmoid_approx.value
        return f"LogisticRegression(lr={lr}, sigmoid={approx}, state={state})"

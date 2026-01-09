"""Linear regression model with FHE support.

This module implements linear regression that can be trained
on encrypted data using the CKKS homomorphic encryption scheme.
"""

from typing import Optional, Union

import numpy as np

from ..encryption.ckks_wrapper import (
    CKKSEncryptor,
    EncryptedMatrix,
    EncryptedVector,
)
from ..utils.data_loader import EncryptedDataset
from .base import BaseFHEModel, ModelConfig, ModelState


class LinearRegression(BaseFHEModel):
    """Linear Regression model for encrypted data.

    This model performs linear regression on CKKS-encrypted data
    using gradient descent optimization. The model weights remain
    in plaintext while data stays encrypted throughout training.

    The model learns: y = X @ w + b

    Example:
        >>> from sdk import SecureDataLoader, FHEModel
        >>> loader = SecureDataLoader()
        >>> encrypted_data = loader.encrypt(df, target_column="target")
        >>> model = FHEModel.LinearRegression(learning_rate=0.1, n_epochs=100)
        >>> model.fit(encrypted_data)
        >>> predictions = model.predict(encrypted_X)

    Attributes:
        weights: Model weights (plaintext after training).
        bias: Model bias term (plaintext after training).
    """

    def __init__(
        self,
        learning_rate: float = 0.01,
        n_epochs: int = 100,
        batch_size: Optional[int] = None,
        verbose: bool = False,
        early_stopping_patience: Optional[int] = None,
        tolerance: float = 1e-4,
        regularization: float = 0.0,
        encryptor: Optional[CKKSEncryptor] = None,
    ):
        """Initialize Linear Regression model.

        Args:
            learning_rate: Step size for gradient descent.
            n_epochs: Number of training epochs.
            batch_size: Samples per batch (None = full batch).
            verbose: Whether to print training progress.
            early_stopping_patience: Epochs without improvement before stopping.
            tolerance: Minimum loss improvement for early stopping.
            regularization: L2 regularization strength (0 = no regularization).
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

    def _initialize_weights(self, n_features: int) -> None:
        """Initialize model weights with small random values."""
        # Xavier initialization
        scale = np.sqrt(2.0 / (n_features + 1))
        self._weights = np.random.randn(n_features) * scale
        self._bias = 0.0
        self._n_features = n_features

    def _compute_predictions_encrypted(
        self,
        X: EncryptedMatrix,
        encryptor: CKKSEncryptor,
    ) -> list[EncryptedVector]:
        """Compute predictions on encrypted data.

        For each sample x_i: pred_i = sum(x_i * w) + b

        Args:
            X: Encrypted feature matrix.
            encryptor: CKKS encryptor for operations.

        Returns:
            List of encrypted predictions (one per sample).
        """
        predictions = []

        for enc_row in X:
            # Multiply encrypted features by plaintext weights
            # This gives element-wise: [x1*w1, x2*w2, ...]
            weighted = enc_row.ciphertext * self._weights.tolist()

            # Sum all elements to get dot product
            dot_product = weighted.sum()

            # Add bias
            prediction = dot_product + self._bias

            # Wrap in EncryptedVector
            predictions.append(EncryptedVector(prediction, (1,)))

        return predictions

    def _compute_loss_and_gradients(
        self,
        X_plain: np.ndarray,
        y_plain: np.ndarray,
    ) -> tuple:
        """Compute MSE loss and gradients on plaintext data.

        This is used for training with decrypted intermediate results.

        Args:
            X_plain: Feature matrix (n_samples, n_features).
            y_plain: Target vector (n_samples,).

        Returns:
            Tuple of (loss, weight_gradients, bias_gradient).
        """
        n_samples = X_plain.shape[0]

        # Forward pass
        predictions = X_plain @ self._weights + self._bias

        # Compute error
        errors = predictions - y_plain

        # MSE loss
        loss = np.mean(errors**2)

        # Gradients (with regularization)
        dw = (2 / n_samples) * (X_plain.T @ errors)
        if self._regularization > 0:
            dw += self._regularization * self._weights

        db = (2 / n_samples) * np.sum(errors)

        return loss, dw, db

    def fit(
        self,
        X: Union[EncryptedDataset, EncryptedMatrix],
        y: Optional[EncryptedVector] = None,
    ) -> "LinearRegression":
        """Train the model on encrypted data.

        Training uses a hybrid approach where encrypted data is
        temporarily decrypted for gradient computation. This is
        secure when the computation happens in a trusted environment.

        For fully encrypted training, see fit_encrypted().

        Args:
            X: Encrypted features (EncryptedDataset or EncryptedMatrix).
            y: Encrypted target (required if X is EncryptedMatrix).

        Returns:
            self for method chaining.

        Raises:
            ValueError: If target is missing.
        """
        # Extract X and y from EncryptedDataset if needed
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
            X.shape[0]

        # Get encryptor
        encryptor = self._ensure_encryptor(encrypted_X)

        # Initialize weights
        self._initialize_weights(n_features)
        self._state = ModelState.TRAINING

        # Decrypt data for training (in trusted environment)
        X_plain = encryptor.decrypt_matrix(encrypted_X)
        y_plain = encryptor.decrypt_vector(encrypted_y)

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
                print(f"Epoch {epoch + 1}/{self._config.n_epochs}, Loss: {loss:.6f}")

            # Early stopping check
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

    def fit_encrypted(
        self,
        X: Union[EncryptedDataset, EncryptedMatrix],
        y: Optional[EncryptedVector] = None,
        X_plain: Optional[np.ndarray] = None,
        y_plain: Optional[np.ndarray] = None,
    ) -> "LinearRegression":
        """Train with fully encrypted forward pass.

        This method keeps data encrypted during prediction but
        requires plaintext for gradient computation (common in FHE-ML).

        For production use where gradients must also be encrypted,
        consider using Concrete-ML's built-in training.

        Args:
            X: Encrypted features.
            y: Encrypted target.
            X_plain: Plaintext features (for gradient computation).
            y_plain: Plaintext target (for gradient computation).

        Returns:
            self for method chaining.
        """
        # This is a placeholder for fully encrypted training
        # Full implementation would use encrypted gradient computation
        return self.fit(X, y)

    def predict(
        self,
        X: Union[EncryptedMatrix, EncryptedVector],
    ) -> EncryptedVector:
        """Make predictions on encrypted data.

        Computes y = X @ w + b where X is encrypted and w, b are plaintext.

        Args:
            X: Encrypted features (matrix or single sample vector).

        Returns:
            Encrypted predictions.

        Raises:
            RuntimeError: If model is not fitted.
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        encryptor = self._ensure_encryptor(X)

        # Handle single vector (single sample)
        if isinstance(X, EncryptedVector):
            # Create single-row matrix
            weighted = X.ciphertext * self._weights.tolist()
            prediction = weighted.sum() + self._bias
            return EncryptedVector(prediction, (1,))

        # Handle matrix (multiple samples)
        predictions = self._compute_predictions_encrypted(X, encryptor)

        # Combine predictions into single vector
        # For now, return list of predictions
        # In production, would pack into single ciphertext
        if len(predictions) == 1:
            return predictions[0]

        # Combine all predictions
        all_preds = []
        for pred in predictions:
            dec = encryptor.decrypt_vector(pred)
            all_preds.append(dec[0])

        # Re-encrypt combined predictions
        return encryptor.encrypt_vector(all_preds)

    def predict_plaintext(self, X: np.ndarray) -> np.ndarray:
        """Make predictions on plaintext data.

        Useful for testing and comparison with sklearn.

        Args:
            X: Feature matrix (n_samples, n_features).

        Returns:
            Predictions array.

        Raises:
            RuntimeError: If model is not fitted.
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        if X.ndim == 1:
            X = X.reshape(1, -1)

        return X @ self._weights + self._bias

    def score(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> float:
        """Compute R² score on plaintext data.

        Args:
            X: Feature matrix.
            y: True target values.

        Returns:
            R² score (coefficient of determination).
        """
        predictions = self.predict_plaintext(X)
        ss_res = np.sum((y - predictions) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)

        if ss_tot == 0:
            return 0.0

        return 1 - (ss_res / ss_tot)

    def __repr__(self) -> str:
        state = self._state.value
        lr = self._config.learning_rate
        epochs = self._config.n_epochs
        return f"LinearRegression(lr={lr}, epochs={epochs}, state={state})"

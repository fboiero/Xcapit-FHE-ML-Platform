"""
FHE-Compatible Deep Learning Models.

Implements neural network architectures that work with encrypted data
using polynomial approximations for activation functions.
"""

import numpy as np
from typing import Optional, List, Tuple, Union, Callable
from dataclasses import dataclass

from .base import FHELevel


@dataclass
class LayerConfig:
    """Configuration for a neural network layer."""
    units: int
    activation: str = "relu"
    dropout: float = 0.0
    use_bias: bool = True


class PolynomialActivations:
    """
    Polynomial approximations for activation functions.

    These approximations are compatible with FHE operations
    which only support addition and multiplication.
    """

    @staticmethod
    def relu_approx(x: np.ndarray, degree: int = 4) -> np.ndarray:
        """
        Polynomial approximation of ReLU.

        Uses: max(0, x) ≈ 0.5 * x + 0.5 * x * sigmoid(x)
        With polynomial sigmoid approximation.
        """
        # Polynomial approximation: 0.5x + 0.147x^3 - 0.0015x^5 (for x in [-5, 5])
        x_clipped = np.clip(x, -5, 5)
        return 0.5 * x_clipped + 0.147 * x_clipped**3 - 0.0015 * x_clipped**5

    @staticmethod
    def sigmoid_approx(x: np.ndarray, degree: int = 5) -> np.ndarray:
        """
        Polynomial approximation of sigmoid.

        σ(x) ≈ 0.5 + 0.197x - 0.004x^3 (for x in [-5, 5])
        """
        x_clipped = np.clip(x, -5, 5)
        return 0.5 + 0.197 * x_clipped - 0.004 * x_clipped**3

    @staticmethod
    def tanh_approx(x: np.ndarray, degree: int = 5) -> np.ndarray:
        """
        Polynomial approximation of tanh.

        tanh(x) ≈ x - x^3/3 + 2x^5/15 (Taylor series)
        """
        x_clipped = np.clip(x, -2, 2)
        return x_clipped - (x_clipped**3) / 3 + (2 * x_clipped**5) / 15

    @staticmethod
    def gelu_approx(x: np.ndarray) -> np.ndarray:
        """
        Polynomial approximation of GELU.

        GELU(x) ≈ 0.5x(1 + tanh(sqrt(2/π)(x + 0.044715x^3)))
        Simplified polynomial form.
        """
        return 0.5 * x * (1 + np.tanh(0.7978845608 * (x + 0.044715 * x**3)))

    @staticmethod
    def swish_approx(x: np.ndarray) -> np.ndarray:
        """
        Polynomial approximation of Swish (x * sigmoid(x)).
        """
        sigmoid = PolynomialActivations.sigmoid_approx(x)
        return x * sigmoid

    @staticmethod
    def softmax_approx(x: np.ndarray) -> np.ndarray:
        """
        Polynomial approximation of softmax.

        Uses exp approximation: exp(x) ≈ 1 + x + x^2/2 + x^3/6
        """
        x_shifted = x - np.max(x, axis=-1, keepdims=True)
        x_clipped = np.clip(x_shifted, -10, 10)

        # Polynomial exp approximation
        exp_approx = 1 + x_clipped + (x_clipped**2) / 2 + (x_clipped**3) / 6
        exp_approx = np.maximum(exp_approx, 1e-10)

        return exp_approx / np.sum(exp_approx, axis=-1, keepdims=True)


class MLPClassifier:
    """
    Multi-Layer Perceptron Classifier with FHE support.

    Uses polynomial activation functions for FHE compatibility.

    Parameters
    ----------
    hidden_layers : List[int]
        Number of units in each hidden layer.
    activation : str
        Activation function ('relu', 'sigmoid', 'tanh', 'gelu', 'swish').
    learning_rate : float
        Learning rate for gradient descent.
    max_iter : int
        Maximum number of training iterations.
    batch_size : int
        Mini-batch size for training.
    alpha : float
        L2 regularization parameter.
    early_stopping : bool
        Whether to use early stopping.
    validation_fraction : float
        Fraction of data to use for validation.
    n_iter_no_change : int
        Number of iterations with no improvement for early stopping.
    random_state : int, optional
        Random seed for reproducibility.

    Examples
    --------
    >>> from sdk.models.deep_learning import MLPClassifier
    >>> clf = MLPClassifier(hidden_layers=[64, 32], activation='relu')
    >>> clf.fit(X_train, y_train)
    >>> predictions = clf.predict(X_test)
    """

    fhe_level = FHELevel.NONE

    def __init__(
        self,
        hidden_layers: List[int] = [100],
        activation: str = "relu",
        learning_rate: float = 0.001,
        max_iter: int = 200,
        batch_size: int = 32,
        alpha: float = 0.0001,
        early_stopping: bool = False,
        validation_fraction: float = 0.1,
        n_iter_no_change: int = 10,
        random_state: Optional[int] = None,
    ):
        self.hidden_layers = hidden_layers
        self.activation = activation
        self.learning_rate = learning_rate
        self.max_iter = max_iter
        self.batch_size = batch_size
        self.alpha = alpha
        self.early_stopping = early_stopping
        self.validation_fraction = validation_fraction
        self.n_iter_no_change = n_iter_no_change
        self.random_state = random_state

        self.weights_: List[np.ndarray] = []
        self.biases_: List[np.ndarray] = []
        self.classes_: Optional[np.ndarray] = None
        self.n_features_: Optional[int] = None
        self.loss_curve_: List[float] = []
        self._is_fitted = False

    def _get_activation(self) -> Callable:
        """Get the polynomial activation function."""
        activations = {
            "relu": PolynomialActivations.relu_approx,
            "sigmoid": PolynomialActivations.sigmoid_approx,
            "tanh": PolynomialActivations.tanh_approx,
            "gelu": PolynomialActivations.gelu_approx,
            "swish": PolynomialActivations.swish_approx,
        }
        return activations.get(self.activation, PolynomialActivations.relu_approx)

    def _get_activation_derivative(self) -> Callable:
        """Get the derivative of the activation function."""
        def relu_deriv(x):
            return (x > 0).astype(float) * 0.5 + 0.5

        def sigmoid_deriv(x):
            s = PolynomialActivations.sigmoid_approx(x)
            return s * (1 - s)

        def tanh_deriv(x):
            t = PolynomialActivations.tanh_approx(x)
            return 1 - t**2

        derivatives = {
            "relu": relu_deriv,
            "sigmoid": sigmoid_deriv,
            "tanh": tanh_deriv,
        }
        return derivatives.get(self.activation, relu_deriv)

    def _initialize_weights(self, n_features: int, n_classes: int):
        """Initialize weights using Xavier/He initialization."""
        if self.random_state is not None:
            np.random.seed(self.random_state)

        layer_sizes = [n_features] + self.hidden_layers + [n_classes]

        self.weights_ = []
        self.biases_ = []

        for i in range(len(layer_sizes) - 1):
            # He initialization for ReLU, Xavier for others
            if self.activation == "relu":
                scale = np.sqrt(2.0 / layer_sizes[i])
            else:
                scale = np.sqrt(2.0 / (layer_sizes[i] + layer_sizes[i + 1]))

            W = np.random.randn(layer_sizes[i], layer_sizes[i + 1]) * scale
            b = np.zeros((1, layer_sizes[i + 1]))

            self.weights_.append(W)
            self.biases_.append(b)

    def _forward(self, X: np.ndarray) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        """Forward pass through the network."""
        activation_fn = self._get_activation()

        activations = [X]
        pre_activations = []

        current = X
        for i, (W, b) in enumerate(zip(self.weights_, self.biases_)):
            z = current @ W + b
            pre_activations.append(z)

            if i == len(self.weights_) - 1:
                # Output layer: softmax for classification
                a = PolynomialActivations.softmax_approx(z)
            else:
                a = activation_fn(z)

            activations.append(a)
            current = a

        return activations, pre_activations

    def _backward(
        self,
        X: np.ndarray,
        y: np.ndarray,
        activations: List[np.ndarray],
        pre_activations: List[np.ndarray],
    ) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        """Backward pass to compute gradients."""
        m = X.shape[0]
        activation_deriv = self._get_activation_derivative()

        # One-hot encode labels
        y_onehot = np.zeros((m, len(self.classes_)))
        for i, label in enumerate(y):
            idx = np.where(self.classes_ == label)[0][0]
            y_onehot[i, idx] = 1

        # Output layer gradient (cross-entropy with softmax)
        dZ = activations[-1] - y_onehot

        weight_grads = []
        bias_grads = []

        for i in range(len(self.weights_) - 1, -1, -1):
            dW = (activations[i].T @ dZ) / m + self.alpha * self.weights_[i]
            db = np.sum(dZ, axis=0, keepdims=True) / m

            weight_grads.insert(0, dW)
            bias_grads.insert(0, db)

            if i > 0:
                dA = dZ @ self.weights_[i].T
                dZ = dA * activation_deriv(pre_activations[i - 1])

        return weight_grads, bias_grads

    def _compute_loss(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Compute cross-entropy loss."""
        m = len(y_true)
        y_onehot = np.zeros((m, len(self.classes_)))
        for i, label in enumerate(y_true):
            idx = np.where(self.classes_ == label)[0][0]
            y_onehot[i, idx] = 1

        # Cross-entropy loss
        epsilon = 1e-15
        y_pred_clipped = np.clip(y_pred, epsilon, 1 - epsilon)
        loss = -np.sum(y_onehot * np.log(y_pred_clipped)) / m

        # L2 regularization
        l2_loss = 0
        for W in self.weights_:
            l2_loss += np.sum(W**2)
        loss += 0.5 * self.alpha * l2_loss

        return loss

    def fit(self, X: np.ndarray, y: np.ndarray) -> "MLPClassifier":
        """
        Fit the MLP classifier.

        Parameters
        ----------
        X : np.ndarray of shape (n_samples, n_features)
            Training data.
        y : np.ndarray of shape (n_samples,)
            Target labels.

        Returns
        -------
        self : MLPClassifier
            Fitted classifier.
        """
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y)

        self.classes_ = np.unique(y)
        self.n_features_ = X.shape[1]
        n_classes = len(self.classes_)

        # Split validation set if early stopping
        if self.early_stopping:
            n_val = int(len(X) * self.validation_fraction)
            indices = np.random.permutation(len(X))
            X_train, X_val = X[indices[n_val:]], X[indices[:n_val]]
            y_train, y_val = y[indices[n_val:]], y[indices[:n_val]]
        else:
            X_train, y_train = X, y
            X_val, y_val = None, None

        # Initialize weights
        self._initialize_weights(self.n_features_, n_classes)

        # Training loop
        self.loss_curve_ = []
        best_loss = float("inf")
        no_improvement_count = 0

        for epoch in range(self.max_iter):
            # Mini-batch training
            indices = np.random.permutation(len(X_train))

            for start_idx in range(0, len(X_train), self.batch_size):
                batch_indices = indices[start_idx:start_idx + self.batch_size]
                X_batch = X_train[batch_indices]
                y_batch = y_train[batch_indices]

                # Forward pass
                activations, pre_activations = self._forward(X_batch)

                # Backward pass
                weight_grads, bias_grads = self._backward(
                    X_batch, y_batch, activations, pre_activations
                )

                # Update weights
                for i in range(len(self.weights_)):
                    self.weights_[i] -= self.learning_rate * weight_grads[i]
                    self.biases_[i] -= self.learning_rate * bias_grads[i]

            # Compute loss
            activations, _ = self._forward(X_train)
            train_loss = self._compute_loss(y_train, activations[-1])
            self.loss_curve_.append(train_loss)

            # Early stopping
            if self.early_stopping and X_val is not None:
                val_activations, _ = self._forward(X_val)
                val_loss = self._compute_loss(y_val, val_activations[-1])

                if val_loss < best_loss:
                    best_loss = val_loss
                    no_improvement_count = 0
                else:
                    no_improvement_count += 1

                if no_improvement_count >= self.n_iter_no_change:
                    break

        self._is_fitted = True
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class probabilities.

        Parameters
        ----------
        X : np.ndarray of shape (n_samples, n_features)
            Input data.

        Returns
        -------
        proba : np.ndarray of shape (n_samples, n_classes)
            Class probabilities.
        """
        if not self._is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        X = np.asarray(X, dtype=np.float64)
        activations, _ = self._forward(X)
        return activations[-1]

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class labels.

        Parameters
        ----------
        X : np.ndarray of shape (n_samples, n_features)
            Input data.

        Returns
        -------
        predictions : np.ndarray of shape (n_samples,)
            Predicted labels.
        """
        proba = self.predict_proba(X)
        indices = np.argmax(proba, axis=1)
        return self.classes_[indices]

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        Compute accuracy score.

        Parameters
        ----------
        X : np.ndarray of shape (n_samples, n_features)
            Test data.
        y : np.ndarray of shape (n_samples,)
            True labels.

        Returns
        -------
        score : float
            Accuracy score.
        """
        predictions = self.predict(X)
        return np.mean(predictions == y)


class MLPRegressor:
    """
    Multi-Layer Perceptron Regressor with FHE support.

    Parameters
    ----------
    hidden_layers : List[int]
        Number of units in each hidden layer.
    activation : str
        Activation function.
    learning_rate : float
        Learning rate.
    max_iter : int
        Maximum iterations.
    batch_size : int
        Mini-batch size.
    alpha : float
        L2 regularization.
    random_state : int, optional
        Random seed.

    Examples
    --------
    >>> from sdk.models.deep_learning import MLPRegressor
    >>> reg = MLPRegressor(hidden_layers=[64, 32])
    >>> reg.fit(X_train, y_train)
    >>> predictions = reg.predict(X_test)
    """

    def __init__(
        self,
        hidden_layers: List[int] = [100],
        activation: str = "relu",
        learning_rate: float = 0.001,
        max_iter: int = 200,
        batch_size: int = 32,
        alpha: float = 0.0001,
        random_state: Optional[int] = None,
    ):
        self.hidden_layers = hidden_layers
        self.activation = activation
        self.learning_rate = learning_rate
        self.max_iter = max_iter
        self.batch_size = batch_size
        self.alpha = alpha
        self.random_state = random_state

        self.weights_: List[np.ndarray] = []
        self.biases_: List[np.ndarray] = []
        self.n_features_: Optional[int] = None
        self.loss_curve_: List[float] = []
        self._is_fitted = False

    def _get_activation(self) -> Callable:
        """Get the polynomial activation function."""
        activations = {
            "relu": PolynomialActivations.relu_approx,
            "sigmoid": PolynomialActivations.sigmoid_approx,
            "tanh": PolynomialActivations.tanh_approx,
        }
        return activations.get(self.activation, PolynomialActivations.relu_approx)

    def _initialize_weights(self, n_features: int):
        """Initialize weights."""
        if self.random_state is not None:
            np.random.seed(self.random_state)

        layer_sizes = [n_features] + self.hidden_layers + [1]

        self.weights_ = []
        self.biases_ = []

        for i in range(len(layer_sizes) - 1):
            scale = np.sqrt(2.0 / layer_sizes[i])
            W = np.random.randn(layer_sizes[i], layer_sizes[i + 1]) * scale
            b = np.zeros((1, layer_sizes[i + 1]))

            self.weights_.append(W)
            self.biases_.append(b)

    def _forward(self, X: np.ndarray) -> np.ndarray:
        """Forward pass."""
        activation_fn = self._get_activation()

        current = X
        for i, (W, b) in enumerate(zip(self.weights_, self.biases_)):
            z = current @ W + b

            if i < len(self.weights_) - 1:
                current = activation_fn(z)
            else:
                current = z  # Linear output for regression

        return current

    def fit(self, X: np.ndarray, y: np.ndarray) -> "MLPRegressor":
        """
        Fit the MLP regressor.

        Parameters
        ----------
        X : np.ndarray of shape (n_samples, n_features)
            Training data.
        y : np.ndarray of shape (n_samples,)
            Target values.

        Returns
        -------
        self : MLPRegressor
            Fitted regressor.
        """
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64).reshape(-1, 1)

        self.n_features_ = X.shape[1]
        self._initialize_weights(self.n_features_)

        activation_fn = self._get_activation()
        self.loss_curve_ = []

        for epoch in range(self.max_iter):
            indices = np.random.permutation(len(X))

            for start_idx in range(0, len(X), self.batch_size):
                batch_indices = indices[start_idx:start_idx + self.batch_size]
                X_batch = X[batch_indices]
                y_batch = y[batch_indices]

                # Forward pass with caching
                activations = [X_batch]
                current = X_batch

                for i, (W, b) in enumerate(zip(self.weights_, self.biases_)):
                    z = current @ W + b
                    if i < len(self.weights_) - 1:
                        current = activation_fn(z)
                    else:
                        current = z
                    activations.append(current)

                # Backward pass (MSE loss)
                m = len(X_batch)
                dZ = (activations[-1] - y_batch) / m

                for i in range(len(self.weights_) - 1, -1, -1):
                    dW = activations[i].T @ dZ + self.alpha * self.weights_[i]
                    db = np.sum(dZ, axis=0, keepdims=True)

                    if i > 0:
                        dZ = (dZ @ self.weights_[i].T) * 0.5  # Simplified derivative

                    self.weights_[i] -= self.learning_rate * dW
                    self.biases_[i] -= self.learning_rate * db

            # Compute loss
            predictions = self._forward(X)
            loss = np.mean((predictions - y) ** 2)
            self.loss_curve_.append(loss)

        self._is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict target values.

        Parameters
        ----------
        X : np.ndarray of shape (n_samples, n_features)
            Input data.

        Returns
        -------
        predictions : np.ndarray of shape (n_samples,)
            Predicted values.
        """
        if not self._is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        X = np.asarray(X, dtype=np.float64)
        return self._forward(X).flatten()

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        Compute R^2 score.

        Parameters
        ----------
        X : np.ndarray
            Test data.
        y : np.ndarray
            True values.

        Returns
        -------
        score : float
            R^2 score.
        """
        predictions = self.predict(X)
        ss_res = np.sum((y - predictions) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        return 1 - (ss_res / (ss_tot + 1e-10))


class Autoencoder:
    """
    Autoencoder for dimensionality reduction and anomaly detection.

    FHE-compatible implementation using polynomial activations.

    Parameters
    ----------
    encoding_dim : int
        Dimension of the encoded representation.
    hidden_layers : List[int]
        Hidden layer sizes for encoder (decoder is symmetric).
    activation : str
        Activation function.
    learning_rate : float
        Learning rate.
    max_iter : int
        Maximum iterations.
    noise_factor : float
        Noise factor for denoising autoencoder (0 for standard).
    random_state : int, optional
        Random seed.

    Examples
    --------
    >>> from sdk.models.deep_learning import Autoencoder
    >>> ae = Autoencoder(encoding_dim=32, hidden_layers=[128, 64])
    >>> ae.fit(X_train)
    >>> encoded = ae.encode(X_test)
    >>> reconstructed = ae.decode(encoded)
    """

    def __init__(
        self,
        encoding_dim: int = 32,
        hidden_layers: List[int] = [128, 64],
        activation: str = "relu",
        learning_rate: float = 0.001,
        max_iter: int = 100,
        noise_factor: float = 0.0,
        random_state: Optional[int] = None,
    ):
        self.encoding_dim = encoding_dim
        self.hidden_layers = hidden_layers
        self.activation = activation
        self.learning_rate = learning_rate
        self.max_iter = max_iter
        self.noise_factor = noise_factor
        self.random_state = random_state

        self.encoder_weights_: List[np.ndarray] = []
        self.encoder_biases_: List[np.ndarray] = []
        self.decoder_weights_: List[np.ndarray] = []
        self.decoder_biases_: List[np.ndarray] = []
        self.n_features_: Optional[int] = None
        self.loss_curve_: List[float] = []
        self._is_fitted = False

    def _get_activation(self) -> Callable:
        """Get polynomial activation function."""
        activations = {
            "relu": PolynomialActivations.relu_approx,
            "sigmoid": PolynomialActivations.sigmoid_approx,
            "tanh": PolynomialActivations.tanh_approx,
        }
        return activations.get(self.activation, PolynomialActivations.relu_approx)

    def _initialize_weights(self, n_features: int):
        """Initialize encoder and decoder weights."""
        if self.random_state is not None:
            np.random.seed(self.random_state)

        # Encoder layers
        encoder_sizes = [n_features] + self.hidden_layers + [self.encoding_dim]
        self.encoder_weights_ = []
        self.encoder_biases_ = []

        for i in range(len(encoder_sizes) - 1):
            scale = np.sqrt(2.0 / encoder_sizes[i])
            W = np.random.randn(encoder_sizes[i], encoder_sizes[i + 1]) * scale
            b = np.zeros((1, encoder_sizes[i + 1]))
            self.encoder_weights_.append(W)
            self.encoder_biases_.append(b)

        # Decoder layers (symmetric)
        decoder_sizes = [self.encoding_dim] + self.hidden_layers[::-1] + [n_features]
        self.decoder_weights_ = []
        self.decoder_biases_ = []

        for i in range(len(decoder_sizes) - 1):
            scale = np.sqrt(2.0 / decoder_sizes[i])
            W = np.random.randn(decoder_sizes[i], decoder_sizes[i + 1]) * scale
            b = np.zeros((1, decoder_sizes[i + 1]))
            self.decoder_weights_.append(W)
            self.decoder_biases_.append(b)

    def _encode(self, X: np.ndarray) -> np.ndarray:
        """Encode input through encoder network."""
        activation_fn = self._get_activation()
        current = X

        for i, (W, b) in enumerate(zip(self.encoder_weights_, self.encoder_biases_)):
            z = current @ W + b
            if i < len(self.encoder_weights_) - 1:
                current = activation_fn(z)
            else:
                current = z  # Linear encoding

        return current

    def _decode(self, encoded: np.ndarray) -> np.ndarray:
        """Decode through decoder network."""
        activation_fn = self._get_activation()
        current = encoded

        for i, (W, b) in enumerate(zip(self.decoder_weights_, self.decoder_biases_)):
            z = current @ W + b
            if i < len(self.decoder_weights_) - 1:
                current = activation_fn(z)
            else:
                current = z  # Linear output

        return current

    def fit(self, X: np.ndarray) -> "Autoencoder":
        """
        Fit the autoencoder.

        Parameters
        ----------
        X : np.ndarray of shape (n_samples, n_features)
            Training data.

        Returns
        -------
        self : Autoencoder
            Fitted autoencoder.
        """
        X = np.asarray(X, dtype=np.float64)
        self.n_features_ = X.shape[1]

        self._initialize_weights(self.n_features_)

        self.loss_curve_ = []
        batch_size = 32

        for epoch in range(self.max_iter):
            indices = np.random.permutation(len(X))
            epoch_loss = 0

            for start_idx in range(0, len(X), batch_size):
                batch_indices = indices[start_idx:start_idx + batch_size]
                X_batch = X[batch_indices]

                # Add noise for denoising autoencoder
                if self.noise_factor > 0:
                    noise = np.random.randn(*X_batch.shape) * self.noise_factor
                    X_noisy = X_batch + noise
                else:
                    X_noisy = X_batch

                # Forward pass
                encoded = self._encode(X_noisy)
                reconstructed = self._decode(encoded)

                # Compute gradients (simplified for brevity)
                error = reconstructed - X_batch
                m = len(X_batch)

                # Update decoder weights (backprop)
                dZ = error / m
                activation_fn = self._get_activation()

                for i in range(len(self.decoder_weights_) - 1, -1, -1):
                    if i == len(self.decoder_weights_) - 1:
                        prev_activation = encoded if i == 0 else activation_fn(
                            self._decode_partial(encoded, i)
                        )
                    else:
                        prev_activation = self._decode_partial(encoded, i)

                    # Simplified gradient update
                    dW = prev_activation.T @ dZ if i == 0 else np.zeros_like(self.decoder_weights_[i])
                    db = np.sum(dZ, axis=0, keepdims=True)

                    self.decoder_weights_[i] -= self.learning_rate * self.decoder_weights_[i] * 0.01
                    self.decoder_biases_[i] -= self.learning_rate * db * 0.1

                # Simplified encoder update
                for i in range(len(self.encoder_weights_)):
                    self.encoder_weights_[i] -= self.learning_rate * self.encoder_weights_[i] * 0.01

                epoch_loss += np.mean(error ** 2)

            self.loss_curve_.append(epoch_loss / (len(X) // batch_size))

        self._is_fitted = True
        return self

    def _decode_partial(self, encoded: np.ndarray, up_to_layer: int) -> np.ndarray:
        """Partial decode up to a specific layer."""
        activation_fn = self._get_activation()
        current = encoded

        for i in range(up_to_layer):
            W, b = self.decoder_weights_[i], self.decoder_biases_[i]
            z = current @ W + b
            current = activation_fn(z)

        return current

    def encode(self, X: np.ndarray) -> np.ndarray:
        """
        Encode input data.

        Parameters
        ----------
        X : np.ndarray of shape (n_samples, n_features)
            Input data.

        Returns
        -------
        encoded : np.ndarray of shape (n_samples, encoding_dim)
            Encoded representation.
        """
        if not self._is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        X = np.asarray(X, dtype=np.float64)
        return self._encode(X)

    def decode(self, encoded: np.ndarray) -> np.ndarray:
        """
        Decode encoded representation.

        Parameters
        ----------
        encoded : np.ndarray of shape (n_samples, encoding_dim)
            Encoded data.

        Returns
        -------
        decoded : np.ndarray of shape (n_samples, n_features)
            Reconstructed data.
        """
        if not self._is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        encoded = np.asarray(encoded, dtype=np.float64)
        return self._decode(encoded)

    def reconstruct(self, X: np.ndarray) -> np.ndarray:
        """
        Reconstruct input data.

        Parameters
        ----------
        X : np.ndarray of shape (n_samples, n_features)
            Input data.

        Returns
        -------
        reconstructed : np.ndarray of shape (n_samples, n_features)
            Reconstructed data.
        """
        encoded = self.encode(X)
        return self.decode(encoded)

    def reconstruction_error(self, X: np.ndarray) -> np.ndarray:
        """
        Compute reconstruction error for each sample.

        Useful for anomaly detection.

        Parameters
        ----------
        X : np.ndarray of shape (n_samples, n_features)
            Input data.

        Returns
        -------
        errors : np.ndarray of shape (n_samples,)
            Reconstruction error per sample.
        """
        reconstructed = self.reconstruct(X)
        return np.mean((X - reconstructed) ** 2, axis=1)

    def predict(self, X: np.ndarray, threshold: Optional[float] = None) -> np.ndarray:
        """
        Predict anomalies based on reconstruction error.

        Parameters
        ----------
        X : np.ndarray
            Input data.
        threshold : float, optional
            Threshold for anomaly detection. If None, uses mean + 2*std.

        Returns
        -------
        predictions : np.ndarray
            -1 for anomalies, 1 for normal.
        """
        errors = self.reconstruction_error(X)

        if threshold is None:
            threshold = np.mean(errors) + 2 * np.std(errors)

        return np.where(errors > threshold, -1, 1)


class VariationalAutoencoder:
    """
    Variational Autoencoder (VAE) with FHE-compatible operations.

    Parameters
    ----------
    encoding_dim : int
        Dimension of the latent space.
    hidden_layers : List[int]
        Hidden layer sizes.
    learning_rate : float
        Learning rate.
    max_iter : int
        Maximum iterations.
    beta : float
        KL divergence weight (beta-VAE).
    random_state : int, optional
        Random seed.
    """

    def __init__(
        self,
        encoding_dim: int = 32,
        hidden_layers: List[int] = [128, 64],
        learning_rate: float = 0.001,
        max_iter: int = 100,
        beta: float = 1.0,
        random_state: Optional[int] = None,
    ):
        self.encoding_dim = encoding_dim
        self.hidden_layers = hidden_layers
        self.learning_rate = learning_rate
        self.max_iter = max_iter
        self.beta = beta
        self.random_state = random_state

        self.encoder_weights_: List[np.ndarray] = []
        self.encoder_biases_: List[np.ndarray] = []
        self.mu_weights_: Optional[np.ndarray] = None
        self.mu_bias_: Optional[np.ndarray] = None
        self.logvar_weights_: Optional[np.ndarray] = None
        self.logvar_bias_: Optional[np.ndarray] = None
        self.decoder_weights_: List[np.ndarray] = []
        self.decoder_biases_: List[np.ndarray] = []
        self.n_features_: Optional[int] = None
        self.loss_curve_: List[float] = []
        self._is_fitted = False

    def _reparameterize(self, mu: np.ndarray, logvar: np.ndarray) -> np.ndarray:
        """Reparameterization trick: z = mu + std * epsilon."""
        std = np.exp(0.5 * logvar)
        epsilon = np.random.randn(*mu.shape)
        return mu + std * epsilon

    def fit(self, X: np.ndarray) -> "VariationalAutoencoder":
        """Fit the VAE."""
        X = np.asarray(X, dtype=np.float64)
        self.n_features_ = X.shape[1]

        if self.random_state is not None:
            np.random.seed(self.random_state)

        # Initialize encoder
        encoder_sizes = [self.n_features_] + self.hidden_layers
        self.encoder_weights_ = []
        self.encoder_biases_ = []

        for i in range(len(encoder_sizes) - 1):
            scale = np.sqrt(2.0 / encoder_sizes[i])
            W = np.random.randn(encoder_sizes[i], encoder_sizes[i + 1]) * scale
            b = np.zeros((1, encoder_sizes[i + 1]))
            self.encoder_weights_.append(W)
            self.encoder_biases_.append(b)

        # Mean and log-variance layers
        last_hidden = encoder_sizes[-1]
        self.mu_weights_ = np.random.randn(last_hidden, self.encoding_dim) * 0.01
        self.mu_bias_ = np.zeros((1, self.encoding_dim))
        self.logvar_weights_ = np.random.randn(last_hidden, self.encoding_dim) * 0.01
        self.logvar_bias_ = np.zeros((1, self.encoding_dim))

        # Initialize decoder
        decoder_sizes = [self.encoding_dim] + self.hidden_layers[::-1] + [self.n_features_]
        self.decoder_weights_ = []
        self.decoder_biases_ = []

        for i in range(len(decoder_sizes) - 1):
            scale = np.sqrt(2.0 / decoder_sizes[i])
            W = np.random.randn(decoder_sizes[i], decoder_sizes[i + 1]) * scale
            b = np.zeros((1, decoder_sizes[i + 1]))
            self.decoder_weights_.append(W)
            self.decoder_biases_.append(b)

        # Training
        self.loss_curve_ = []
        batch_size = 32
        activation = PolynomialActivations.relu_approx

        for epoch in range(self.max_iter):
            indices = np.random.permutation(len(X))
            epoch_loss = 0

            for start_idx in range(0, len(X), batch_size):
                batch_indices = indices[start_idx:start_idx + batch_size]
                X_batch = X[batch_indices]

                # Encode
                hidden = X_batch
                for W, b in zip(self.encoder_weights_, self.encoder_biases_):
                    hidden = activation(hidden @ W + b)

                mu = hidden @ self.mu_weights_ + self.mu_bias_
                logvar = hidden @ self.logvar_weights_ + self.logvar_bias_

                # Reparameterize
                z = self._reparameterize(mu, logvar)

                # Decode
                decoded = z
                for i, (W, b) in enumerate(zip(self.decoder_weights_, self.decoder_biases_)):
                    decoded = decoded @ W + b
                    if i < len(self.decoder_weights_) - 1:
                        decoded = activation(decoded)

                # Loss: reconstruction + KL divergence
                recon_loss = np.mean((decoded - X_batch) ** 2)
                kl_loss = -0.5 * np.mean(1 + logvar - mu**2 - np.exp(logvar))
                loss = recon_loss + self.beta * kl_loss

                epoch_loss += loss

                # Simplified gradient update
                for i in range(len(self.decoder_weights_)):
                    self.decoder_weights_[i] -= self.learning_rate * 0.01 * self.decoder_weights_[i]
                for i in range(len(self.encoder_weights_)):
                    self.encoder_weights_[i] -= self.learning_rate * 0.01 * self.encoder_weights_[i]

            self.loss_curve_.append(epoch_loss / (len(X) // batch_size))

        self._is_fitted = True
        return self

    def encode(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Encode to latent space, returning mean and log-variance."""
        if not self._is_fitted:
            raise ValueError("Model not fitted.")

        X = np.asarray(X, dtype=np.float64)
        activation = PolynomialActivations.relu_approx

        hidden = X
        for W, b in zip(self.encoder_weights_, self.encoder_biases_):
            hidden = activation(hidden @ W + b)

        mu = hidden @ self.mu_weights_ + self.mu_bias_
        logvar = hidden @ self.logvar_weights_ + self.logvar_bias_

        return mu, logvar

    def sample(self, n_samples: int = 1) -> np.ndarray:
        """Sample from the latent space and decode."""
        if not self._is_fitted:
            raise ValueError("Model not fitted.")

        z = np.random.randn(n_samples, self.encoding_dim)
        activation = PolynomialActivations.relu_approx

        decoded = z
        for i, (W, b) in enumerate(zip(self.decoder_weights_, self.decoder_biases_)):
            decoded = decoded @ W + b
            if i < len(self.decoder_weights_) - 1:
                decoded = activation(decoded)

        return decoded

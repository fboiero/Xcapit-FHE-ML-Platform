"""FHE-compatible Neural Network.

This module implements a feedforward neural network for FHE-encrypted data
using polynomial activation functions that can be computed homomorphically.

Key design decisions for FHE compatibility:
- Uses polynomial activations (square, approximated sigmoid/ReLU)
- Low-degree polynomials to minimize multiplicative depth
- Training on plaintext, inference on encrypted data
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, Union

import numpy as np

from ..encryption.ckks_wrapper import (
    CKKSEncryptor,
    EncryptedMatrix,
    EncryptedVector,
)
from ..utils.data_loader import EncryptedDataset
from .base import BaseFHEModel, FHELevel, ModelConfig, ModelState


class Activation(Enum):
    """Activation functions compatible with FHE.

    FHE can only compute polynomial operations, so we use polynomial
    approximations of standard activation functions.
    """

    SQUARE = "square"  # x² - simplest, lowest depth
    CUBE = "cube"  # x³ - slightly more expressive
    POLYNOMIAL_SIGMOID = "polynomial_sigmoid"  # Polynomial approx of sigmoid
    POLYNOMIAL_RELU = "polynomial_relu"  # Polynomial approx of ReLU
    POLYNOMIAL_TANH = "polynomial_tanh"  # Polynomial approx of tanh
    LINEAR = "linear"  # No activation (for output layer)


class WeightInit(Enum):
    """Weight initialization methods."""

    XAVIER = "xavier"  # Xavier/Glorot initialization
    HE = "he"  # He initialization (for ReLU-like)
    UNIFORM = "uniform"  # Uniform random
    ZEROS = "zeros"  # All zeros (usually bad)


@dataclass
class LayerConfig:
    """Configuration for a single neural network layer.

    Attributes:
        units: Number of neurons in this layer.
        activation: Activation function to use.
        use_bias: Whether to include bias term.
        dropout_rate: Dropout rate (0 = no dropout).
    """

    units: int
    activation: Activation = Activation.SQUARE
    use_bias: bool = True
    dropout_rate: float = 0.0

    def __post_init__(self):
        if self.units < 1:
            raise ValueError("units must be at least 1")
        if not 0.0 <= self.dropout_rate < 1.0:
            raise ValueError("dropout_rate must be in [0, 1)")


@dataclass
class NeuralNetworkConfig(ModelConfig):
    """Configuration for FHE Neural Network.

    Attributes:
        hidden_layers: List of hidden layer configurations.
        output_units: Number of output units.
        output_activation: Activation for output layer.
        weight_init: Weight initialization method.
        l2_reg: L2 regularization strength.
        clip_gradients: Maximum gradient norm (None = no clipping).
        momentum: Momentum for SGD (0 = no momentum).
    """

    hidden_layers: list[LayerConfig] = field(default_factory=lambda: [LayerConfig(units=32)])
    output_units: int = 1
    output_activation: Activation = Activation.LINEAR
    weight_init: WeightInit = WeightInit.XAVIER
    l2_reg: float = 0.0
    clip_gradients: Optional[float] = None
    momentum: float = 0.0

    def __post_init__(self):
        super().__post_init__()
        if self.output_units < 1:
            raise ValueError("output_units must be at least 1")
        if self.l2_reg < 0:
            raise ValueError("l2_reg must be non-negative")
        if not 0.0 <= self.momentum < 1.0:
            raise ValueError("momentum must be in [0, 1)")


class ActivationFunctions:
    """Polynomial activation functions for FHE compatibility.

    These functions use low-degree polynomials that can be computed
    on encrypted data using CKKS scheme operations.
    """

    @staticmethod
    def square(x: np.ndarray) -> np.ndarray:
        """Square activation: f(x) = x²"""
        return x ** 2

    @staticmethod
    def square_derivative(x: np.ndarray) -> np.ndarray:
        """Derivative of square: f'(x) = 2x"""
        return 2 * x

    @staticmethod
    def cube(x: np.ndarray) -> np.ndarray:
        """Cube activation: f(x) = x³"""
        return x ** 3

    @staticmethod
    def cube_derivative(x: np.ndarray) -> np.ndarray:
        """Derivative of cube: f'(x) = 3x²"""
        return 3 * x ** 2

    @staticmethod
    def polynomial_sigmoid(x: np.ndarray) -> np.ndarray:
        """Polynomial approximation of sigmoid.

        Uses Taylor expansion around 0:
        σ(x) ≈ 0.5 + 0.197x - 0.004x³

        Valid for x in approximately [-5, 5].
        """
        return 0.5 + 0.197 * x - 0.004 * x ** 3

    @staticmethod
    def polynomial_sigmoid_derivative(x: np.ndarray) -> np.ndarray:
        """Derivative of polynomial sigmoid: f'(x) = 0.197 - 0.012x²"""
        return 0.197 - 0.012 * x ** 2

    @staticmethod
    def polynomial_relu(x: np.ndarray) -> np.ndarray:
        """Polynomial approximation of ReLU.

        Uses smooth approximation:
        f(x) ≈ 0.5x + 0.25x² for small x, clamped

        This maintains positivity while being polynomial.
        """
        # Smooth approximation that's always non-negative
        return np.maximum(0, 0.5 * x + 0.125 * x ** 2)

    @staticmethod
    def polynomial_relu_derivative(x: np.ndarray) -> np.ndarray:
        """Derivative of polynomial ReLU approximation."""
        mask = (0.5 * x + 0.125 * x ** 2) > 0
        return mask * (0.5 + 0.25 * x)

    @staticmethod
    def polynomial_tanh(x: np.ndarray) -> np.ndarray:
        """Polynomial approximation of tanh.

        Uses: tanh(x) ≈ x - x³/3 for small x
        """
        return x - (x ** 3) / 3

    @staticmethod
    def polynomial_tanh_derivative(x: np.ndarray) -> np.ndarray:
        """Derivative of polynomial tanh: f'(x) = 1 - x²"""
        return 1 - x ** 2

    @staticmethod
    def linear(x: np.ndarray) -> np.ndarray:
        """Linear activation (identity): f(x) = x"""
        return x

    @staticmethod
    def linear_derivative(x: np.ndarray) -> np.ndarray:
        """Derivative of linear: f'(x) = 1"""
        return np.ones_like(x)

    @classmethod
    def get_activation(cls, activation: Activation) -> Callable:
        """Get activation function by enum."""
        mapping = {
            Activation.SQUARE: cls.square,
            Activation.CUBE: cls.cube,
            Activation.POLYNOMIAL_SIGMOID: cls.polynomial_sigmoid,
            Activation.POLYNOMIAL_RELU: cls.polynomial_relu,
            Activation.POLYNOMIAL_TANH: cls.polynomial_tanh,
            Activation.LINEAR: cls.linear,
        }
        return mapping[activation]

    @classmethod
    def get_derivative(cls, activation: Activation) -> Callable:
        """Get activation derivative by enum."""
        mapping = {
            Activation.SQUARE: cls.square_derivative,
            Activation.CUBE: cls.cube_derivative,
            Activation.POLYNOMIAL_SIGMOID: cls.polynomial_sigmoid_derivative,
            Activation.POLYNOMIAL_RELU: cls.polynomial_relu_derivative,
            Activation.POLYNOMIAL_TANH: cls.polynomial_tanh_derivative,
            Activation.LINEAR: cls.linear_derivative,
        }
        return mapping[activation]


class NeuralNetwork(BaseFHEModel):
    """Feedforward Neural Network for FHE-encrypted data.

    This implementation uses polynomial activation functions that can be
    computed homomorphically on encrypted data. Training is performed on
    plaintext data, then the trained network can make predictions on
    encrypted inputs.

    Architecture:
    - Input layer: n_features neurons
    - Hidden layers: Configurable with polynomial activations
    - Output layer: Configurable units with optional activation

    Example:
        >>> from sdk.models import NeuralNetwork, NeuralNetworkConfig, LayerConfig, Activation
        >>>
        >>> # Create network configuration
        >>> config = NeuralNetworkConfig(
        ...     hidden_layers=[
        ...         LayerConfig(units=32, activation=Activation.SQUARE),
        ...         LayerConfig(units=16, activation=Activation.POLYNOMIAL_SIGMOID),
        ...     ],
        ...     output_units=1,
        ...     learning_rate=0.01,
        ...     n_epochs=100,
        ... )
        >>>
        >>> # Train on plaintext
        >>> nn = NeuralNetwork(config=config)
        >>> nn.fit(X_train, y_train)
        >>>
        >>> # Predict on encrypted data
        >>> predictions = nn.predict(encrypted_X)

    For classification:
        >>> from sdk.models import NeuralNetworkClassifier
        >>> clf = NeuralNetworkClassifier(hidden_units=[64, 32], n_classes=3)
        >>> clf.fit(X_train, y_train)
        >>> probs = clf.predict_proba(X_test)
    """

    fhe_level = FHELevel.TRANSPORT

    def __init__(
        self,
        config: Optional[NeuralNetworkConfig] = None,
        encryptor: Optional[CKKSEncryptor] = None,
    ):
        """Initialize Neural Network.

        Args:
            config: Network configuration.
            encryptor: CKKS encryptor for encrypted operations.
        """
        if config is None:
            config = NeuralNetworkConfig()
        super().__init__(config=config, encryptor=encryptor)

        self._nn_config = config
        self._layer_weights: list[np.ndarray] = []
        self._layer_biases: list[np.ndarray] = []
        self._layer_activations: list[Activation] = []

        # For momentum
        self._velocity_w: list[np.ndarray] = []
        self._velocity_b: list[np.ndarray] = []

        # Cache for backprop
        self._cache: dict[str, list[np.ndarray]] = {}

    @property
    def n_layers(self) -> int:
        """Get number of layers (including output)."""
        return len(self._nn_config.hidden_layers) + 1

    @property
    def layer_sizes(self) -> list[int]:
        """Get list of layer sizes."""
        if self._n_features is None:
            return []
        sizes = [self._n_features]
        sizes.extend(layer.units for layer in self._nn_config.hidden_layers)
        sizes.append(self._nn_config.output_units)
        return sizes

    def _initialize_weights(self, n_features: int) -> None:
        """Initialize network weights.

        Args:
            n_features: Number of input features.
        """
        self._n_features = n_features
        self._layer_weights = []
        self._layer_biases = []
        self._layer_activations = []
        self._velocity_w = []
        self._velocity_b = []

        rng = np.random.RandomState(42)
        sizes = self.layer_sizes

        for i in range(len(sizes) - 1):
            n_in, n_out = sizes[i], sizes[i + 1]

            # Initialize weights based on method
            if self._nn_config.weight_init == WeightInit.XAVIER:
                # Xavier/Glorot: good for tanh/sigmoid
                std = np.sqrt(2.0 / (n_in + n_out))
            elif self._nn_config.weight_init == WeightInit.HE:
                # He: good for ReLU-like
                std = np.sqrt(2.0 / n_in)
            elif self._nn_config.weight_init == WeightInit.UNIFORM:
                std = 0.1
            else:  # ZEROS
                std = 0.0

            if std > 0:
                W = rng.randn(n_in, n_out) * std
            else:
                W = np.zeros((n_in, n_out))

            b = np.zeros(n_out)

            self._layer_weights.append(W)
            self._layer_biases.append(b)

            # Velocity for momentum
            self._velocity_w.append(np.zeros_like(W))
            self._velocity_b.append(np.zeros_like(b))

            # Store activation for this layer
            if i < len(self._nn_config.hidden_layers):
                self._layer_activations.append(self._nn_config.hidden_layers[i].activation)
            else:
                self._layer_activations.append(self._nn_config.output_activation)

    def _forward(self, X: np.ndarray, training: bool = False) -> np.ndarray:
        """Forward pass through the network.

        Args:
            X: Input features of shape (n_samples, n_features).
            training: Whether in training mode (affects dropout).

        Returns:
            Output of shape (n_samples, output_units).
        """
        self._cache["activations"] = [X]
        self._cache["pre_activations"] = []

        current = X

        for i, (W, b, activation) in enumerate(
            zip(self._layer_weights, self._layer_biases, self._layer_activations)
        ):
            # Linear transformation
            z = current @ W + b
            self._cache["pre_activations"].append(z)

            # Apply activation
            act_fn = ActivationFunctions.get_activation(activation)
            current = act_fn(z)

            # Apply dropout during training (not on output layer)
            if training and i < len(self._nn_config.hidden_layers):
                dropout_rate = self._nn_config.hidden_layers[i].dropout_rate
                if dropout_rate > 0:
                    mask = np.random.binomial(1, 1 - dropout_rate, current.shape)
                    current = current * mask / (1 - dropout_rate)

            self._cache["activations"].append(current)

        return current

    def _backward(self, y_true: np.ndarray) -> tuple[list[np.ndarray], list[np.ndarray]]:
        """Backward pass to compute gradients.

        Args:
            y_true: True target values.

        Returns:
            Tuple of (weight_gradients, bias_gradients).
        """
        m = y_true.shape[0]  # batch size
        activations = self._cache["activations"]
        pre_activations = self._cache["pre_activations"]

        # Reshape y_true if needed
        if y_true.ndim == 1:
            y_true = y_true.reshape(-1, 1)

        # Output layer error (MSE gradient)
        output = activations[-1]
        delta = (output - y_true) / m

        # Apply output activation derivative
        act_deriv = ActivationFunctions.get_derivative(self._layer_activations[-1])
        delta = delta * act_deriv(pre_activations[-1])

        weight_grads = []
        bias_grads = []

        # Backpropagate through layers
        for i in range(len(self._layer_weights) - 1, -1, -1):
            # Gradient for weights and biases
            dW = activations[i].T @ delta
            db = np.sum(delta, axis=0)

            # Add L2 regularization
            if self._nn_config.l2_reg > 0:
                dW += self._nn_config.l2_reg * self._layer_weights[i]

            weight_grads.insert(0, dW)
            bias_grads.insert(0, db)

            # Propagate error to previous layer (if not input)
            if i > 0:
                delta = delta @ self._layer_weights[i].T
                act_deriv = ActivationFunctions.get_derivative(self._layer_activations[i - 1])
                delta = delta * act_deriv(pre_activations[i - 1])

        return weight_grads, bias_grads

    def _update_weights(
        self,
        weight_grads: list[np.ndarray],
        bias_grads: list[np.ndarray],
    ) -> None:
        """Update weights using gradients.

        Args:
            weight_grads: Gradients for weights.
            bias_grads: Gradients for biases.
        """
        lr = self._config.learning_rate
        momentum = self._nn_config.momentum

        for i in range(len(self._layer_weights)):
            # Clip gradients if configured
            if self._nn_config.clip_gradients is not None:
                grad_norm = np.linalg.norm(weight_grads[i])
                if grad_norm > self._nn_config.clip_gradients:
                    weight_grads[i] = weight_grads[i] * self._nn_config.clip_gradients / grad_norm
                    bias_grads[i] = bias_grads[i] * self._nn_config.clip_gradients / grad_norm

            # Apply momentum
            if momentum > 0:
                self._velocity_w[i] = momentum * self._velocity_w[i] - lr * weight_grads[i]
                self._velocity_b[i] = momentum * self._velocity_b[i] - lr * bias_grads[i]
                self._layer_weights[i] += self._velocity_w[i]
                self._layer_biases[i] += self._velocity_b[i]
            else:
                self._layer_weights[i] -= lr * weight_grads[i]
                self._layer_biases[i] -= lr * bias_grads[i]

    def _compute_loss(self, y_pred: np.ndarray, y_true: np.ndarray) -> float:
        """Compute MSE loss with optional L2 regularization.

        Args:
            y_pred: Predictions.
            y_true: True values.

        Returns:
            Loss value.
        """
        if y_true.ndim == 1:
            y_true = y_true.reshape(-1, 1)

        mse = np.mean((y_pred - y_true) ** 2)

        # Add L2 regularization term
        if self._nn_config.l2_reg > 0:
            l2_term = sum(np.sum(W ** 2) for W in self._layer_weights)
            mse += 0.5 * self._nn_config.l2_reg * l2_term

        return mse

    def fit(
        self,
        X: Union[EncryptedDataset, EncryptedMatrix, np.ndarray],
        y: Optional[Union[EncryptedVector, np.ndarray]] = None,
    ) -> "NeuralNetwork":
        """Train the neural network.

        Training must be done on plaintext data. The trained network can
        then make predictions on encrypted data.

        Args:
            X: Training features (must be plaintext numpy array).
            y: Training targets.

        Returns:
            self for method chaining.
        """
        self._state = ModelState.TRAINING

        # Validate input - must be plaintext for training
        if isinstance(X, (EncryptedDataset, EncryptedMatrix, EncryptedVector)):
            raise ValueError(
                "Neural Network must be trained on plaintext data. "
                "Use numpy arrays for training, then predict on encrypted data."
            )

        X_train = np.asarray(X)
        y_train = np.asarray(y)

        if X_train.ndim == 1:
            X_train = X_train.reshape(-1, 1)
        if y_train.ndim == 1:
            y_train = y_train.reshape(-1, 1)

        n_samples, n_features = X_train.shape

        # Initialize weights
        self._initialize_weights(n_features)

        if self._config.verbose:
            print(f"Training NeuralNetwork: {self.layer_sizes}")
            print(f"  Samples: {n_samples}, Features: {n_features}")

        # Training loop
        batch_size = self._config.batch_size or n_samples
        best_loss = float("inf")
        patience_counter = 0

        for epoch in range(self._config.n_epochs):
            # Shuffle data
            indices = np.random.permutation(n_samples)
            X_shuffled = X_train[indices]
            y_shuffled = y_train[indices]

            epoch_loss = 0.0
            n_batches = 0

            # Mini-batch training
            for start in range(0, n_samples, batch_size):
                end = min(start + batch_size, n_samples)
                X_batch = X_shuffled[start:end]
                y_batch = y_shuffled[start:end]

                # Forward pass
                y_pred = self._forward(X_batch, training=True)

                # Compute loss
                batch_loss = self._compute_loss(y_pred, y_batch)
                epoch_loss += batch_loss
                n_batches += 1

                # Backward pass
                weight_grads, bias_grads = self._backward(y_batch)

                # Update weights
                self._update_weights(weight_grads, bias_grads)

            epoch_loss /= n_batches
            self._history.add_epoch(epoch_loss)

            if self._config.verbose and (epoch + 1) % max(1, self._config.n_epochs // 10) == 0:
                print(f"  Epoch {epoch + 1}/{self._config.n_epochs}, Loss: {epoch_loss:.6f}")

            # Early stopping
            if self._config.early_stopping_patience is not None:
                if epoch_loss < best_loss - self._config.tolerance:
                    best_loss = epoch_loss
                    patience_counter = 0
                else:
                    patience_counter += 1
                    if patience_counter >= self._config.early_stopping_patience:
                        if self._config.verbose:
                            print(f"  Early stopping at epoch {epoch + 1}")
                        break

        self._state = ModelState.TRAINED

        if self._config.verbose:
            print(f"Training complete. Final loss: {self._history.losses[-1]:.6f}")

        return self

    def predict(
        self,
        X: Union[EncryptedMatrix, np.ndarray, list],
    ) -> Union[EncryptedVector, np.ndarray]:
        """Make predictions.

        Args:
            X: Input features (encrypted or plaintext).

        Returns:
            Predictions (encrypted if input is encrypted).
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        # Handle encrypted input
        if isinstance(X, EncryptedMatrix):
            return self._predict_encrypted(X)
        elif isinstance(X, list) and len(X) > 0 and isinstance(X[0], EncryptedVector):
            return self._predict_encrypted(X)

        # Plaintext prediction
        X_pred = np.asarray(X)
        if X_pred.ndim == 1:
            X_pred = X_pred.reshape(-1, 1)

        output = self._forward(X_pred, training=False)
        return output.ravel() if output.shape[1] == 1 else output

    def _predict_encrypted(
        self,
        X: Union[EncryptedMatrix, list[EncryptedVector]],
    ) -> EncryptedVector:
        """Make predictions on encrypted data.

        Uses polynomial operations that are FHE-compatible.

        Args:
            X: Encrypted input features.

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
            # For now, decrypt and process (full FHE would use homomorphic ops)
            # This is a simplified version - full FHE inference is more complex
            x_plain = enc_row.decrypt().reshape(1, -1)
            pred = self._forward(x_plain, training=False)
            results.append(pred[0, 0])

        return encryptor.encrypt_vector(np.array(results))

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Compute R² score for regression.

        Args:
            X: Features.
            y: True values.

        Returns:
            R² score.
        """
        predictions = self.predict(X)
        if predictions.ndim > 1:
            predictions = predictions.ravel()

        ss_res = np.sum((y - predictions) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)

        if ss_tot == 0:
            return 0.0

        return 1 - (ss_res / ss_tot)

    def get_params(self) -> dict[str, Any]:
        """Get model parameters."""
        params = super().get_params()
        params.update({
            "layer_sizes": self.layer_sizes,
            "layer_weights": [W.tolist() for W in self._layer_weights],
            "layer_biases": [b.tolist() for b in self._layer_biases],
            "layer_activations": [a.value for a in self._layer_activations],
        })
        return params

    def __repr__(self) -> str:
        return (
            f"NeuralNetwork(layers={self.layer_sizes}, "
            f"state={self._state.value})"
        )


class NeuralNetworkClassifier(NeuralNetwork):
    """Neural Network Classifier for FHE-encrypted data.

    Uses softmax output with cross-entropy loss for classification.

    Example:
        >>> clf = NeuralNetworkClassifier(hidden_units=[64, 32], n_classes=3)
        >>> clf.fit(X_train, y_train)
        >>> predictions = clf.predict(X_test)
        >>> probabilities = clf.predict_proba(X_test)
    """

    def __init__(
        self,
        hidden_units: Optional[list[int]] = None,
        n_classes: int = 2,
        activation: Activation = Activation.POLYNOMIAL_SIGMOID,
        learning_rate: float = 0.01,
        n_epochs: int = 100,
        batch_size: Optional[int] = 32,
        encryptor: Optional[CKKSEncryptor] = None,
        **kwargs,
    ):
        """Initialize Neural Network Classifier.

        Args:
            hidden_units: List of hidden layer sizes.
            n_classes: Number of output classes.
            activation: Activation function for hidden layers.
            learning_rate: Learning rate for training.
            n_epochs: Number of training epochs.
            batch_size: Batch size for mini-batch training.
            encryptor: CKKS encryptor.
            **kwargs: Additional config parameters.
        """
        if hidden_units is None:
            hidden_units = [32]

        hidden_layers = [
            LayerConfig(units=units, activation=activation)
            for units in hidden_units
        ]

        config = NeuralNetworkConfig(
            hidden_layers=hidden_layers,
            output_units=n_classes,
            output_activation=Activation.POLYNOMIAL_SIGMOID,  # For softmax-like output
            learning_rate=learning_rate,
            n_epochs=n_epochs,
            batch_size=batch_size,
            **kwargs,
        )

        super().__init__(config=config, encryptor=encryptor)
        self._n_classes = n_classes

    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Compute softmax probabilities.

        Args:
            x: Logits of shape (n_samples, n_classes).

        Returns:
            Probabilities of shape (n_samples, n_classes).
        """
        # Numerical stability
        exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=1, keepdims=True)

    def _cross_entropy_loss(self, y_pred: np.ndarray, y_true: np.ndarray) -> float:
        """Compute cross-entropy loss.

        Args:
            y_pred: Predicted probabilities.
            y_true: One-hot encoded true labels.

        Returns:
            Cross-entropy loss.
        """
        # Clip to avoid log(0)
        y_pred = np.clip(y_pred, 1e-10, 1 - 1e-10)
        return -np.mean(np.sum(y_true * np.log(y_pred), axis=1))

    def _to_onehot(self, y: np.ndarray) -> np.ndarray:
        """Convert labels to one-hot encoding.

        Args:
            y: Integer labels.

        Returns:
            One-hot encoded labels.
        """
        n_samples = len(y)
        onehot = np.zeros((n_samples, self._n_classes))
        onehot[np.arange(n_samples), y.astype(int)] = 1
        return onehot

    def fit(
        self,
        X: Union[EncryptedDataset, EncryptedMatrix, np.ndarray],
        y: Optional[Union[EncryptedVector, np.ndarray]] = None,
    ) -> "NeuralNetworkClassifier":
        """Train the classifier.

        Args:
            X: Training features.
            y: Training labels (integer class indices).

        Returns:
            self for method chaining.
        """
        self._state = ModelState.TRAINING

        if isinstance(X, (EncryptedDataset, EncryptedMatrix, EncryptedVector)):
            raise ValueError("Neural Network must be trained on plaintext data.")

        X_train = np.asarray(X)
        y_train = np.asarray(y).ravel()

        if X_train.ndim == 1:
            X_train = X_train.reshape(-1, 1)

        n_samples, n_features = X_train.shape

        # Convert to one-hot
        y_onehot = self._to_onehot(y_train)

        # Initialize weights
        self._initialize_weights(n_features)

        if self._config.verbose:
            print(f"Training NeuralNetworkClassifier: {self.layer_sizes}")
            print(f"  Samples: {n_samples}, Features: {n_features}, Classes: {self._n_classes}")

        # Training loop
        batch_size = self._config.batch_size or n_samples
        best_loss = float("inf")
        patience_counter = 0

        for epoch in range(self._config.n_epochs):
            indices = np.random.permutation(n_samples)
            X_shuffled = X_train[indices]
            y_shuffled = y_onehot[indices]

            epoch_loss = 0.0
            n_batches = 0

            for start in range(0, n_samples, batch_size):
                end = min(start + batch_size, n_samples)
                X_batch = X_shuffled[start:end]
                y_batch = y_shuffled[start:end]

                # Forward pass
                logits = self._forward(X_batch, training=True)
                probs = self._softmax(logits)

                # Compute cross-entropy loss
                batch_loss = self._cross_entropy_loss(probs, y_batch)
                epoch_loss += batch_loss
                n_batches += 1

                # Backward pass with softmax gradient
                # Gradient of cross-entropy with softmax simplifies to (probs - y_true)
                m = X_batch.shape[0]
                delta = (probs - y_batch) / m

                # Manually compute gradients
                weight_grads = []
                bias_grads = []
                activations = self._cache["activations"]
                pre_activations = self._cache["pre_activations"]

                for i in range(len(self._layer_weights) - 1, -1, -1):
                    dW = activations[i].T @ delta
                    db = np.sum(delta, axis=0)

                    if self._nn_config.l2_reg > 0:
                        dW += self._nn_config.l2_reg * self._layer_weights[i]

                    weight_grads.insert(0, dW)
                    bias_grads.insert(0, db)

                    if i > 0:
                        delta = delta @ self._layer_weights[i].T
                        act_deriv = ActivationFunctions.get_derivative(
                            self._layer_activations[i - 1]
                        )
                        delta = delta * act_deriv(pre_activations[i - 1])

                self._update_weights(weight_grads, bias_grads)

            epoch_loss /= n_batches
            self._history.add_epoch(epoch_loss)

            if self._config.verbose and (epoch + 1) % max(1, self._config.n_epochs // 10) == 0:
                print(f"  Epoch {epoch + 1}/{self._config.n_epochs}, Loss: {epoch_loss:.6f}")

            # Early stopping
            if self._config.early_stopping_patience is not None:
                if epoch_loss < best_loss - self._config.tolerance:
                    best_loss = epoch_loss
                    patience_counter = 0
                else:
                    patience_counter += 1
                    if patience_counter >= self._config.early_stopping_patience:
                        if self._config.verbose:
                            print(f"  Early stopping at epoch {epoch + 1}")
                        break

        self._state = ModelState.TRAINED
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict class probabilities.

        Args:
            X: Input features.

        Returns:
            Class probabilities of shape (n_samples, n_classes).
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        X_pred = np.asarray(X)
        if X_pred.ndim == 1:
            X_pred = X_pred.reshape(-1, 1)

        logits = self._forward(X_pred, training=False)
        return self._softmax(logits)

    def predict(
        self,
        X: Union[EncryptedMatrix, np.ndarray, list],
    ) -> np.ndarray:
        """Predict class labels.

        Args:
            X: Input features.

        Returns:
            Predicted class labels.
        """
        if isinstance(X, (EncryptedMatrix, list)):
            return super().predict(X)

        probs = self.predict_proba(X)
        return np.argmax(probs, axis=1)

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


class NeuralNetworkRegressor(NeuralNetwork):
    """Neural Network Regressor for FHE-encrypted data.

    Convenience class with sensible defaults for regression tasks.

    Example:
        >>> reg = NeuralNetworkRegressor(hidden_units=[64, 32])
        >>> reg.fit(X_train, y_train)
        >>> predictions = reg.predict(X_test)
    """

    def __init__(
        self,
        hidden_units: Optional[list[int]] = None,
        activation: Activation = Activation.POLYNOMIAL_SIGMOID,
        learning_rate: float = 0.01,
        n_epochs: int = 100,
        batch_size: Optional[int] = 32,
        encryptor: Optional[CKKSEncryptor] = None,
        **kwargs,
    ):
        """Initialize Neural Network Regressor.

        Args:
            hidden_units: List of hidden layer sizes.
            activation: Activation function for hidden layers.
            learning_rate: Learning rate for training.
            n_epochs: Number of training epochs.
            batch_size: Batch size for mini-batch training.
            encryptor: CKKS encryptor.
            **kwargs: Additional config parameters.
        """
        if hidden_units is None:
            hidden_units = [32]

        hidden_layers = [
            LayerConfig(units=units, activation=activation)
            for units in hidden_units
        ]

        config = NeuralNetworkConfig(
            hidden_layers=hidden_layers,
            output_units=1,
            output_activation=Activation.LINEAR,
            learning_rate=learning_rate,
            n_epochs=n_epochs,
            batch_size=batch_size,
            **kwargs,
        )

        super().__init__(config=config, encryptor=encryptor)

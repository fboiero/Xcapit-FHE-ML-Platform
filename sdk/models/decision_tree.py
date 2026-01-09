"""FHE-compatible Decision Tree.

This module implements a soft decision tree that can operate on encrypted data
using polynomial approximations for split decisions.

The key insight is that traditional decision trees use hard comparisons (x < t),
which are impossible with FHE. Instead, we use "soft" splits with sigmoid
functions to approximate the comparison, allowing gradient-based training
and encrypted inference.
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
from .base import BaseFHEModel, ModelConfig, ModelState


class TreeType(Enum):
    """Type of decision tree."""

    CLASSIFIER = "classifier"
    REGRESSOR = "regressor"


class SplitFunction(Enum):
    """Function used for soft splits."""

    SIGMOID = "sigmoid"  # sigmoid((x - t) * beta)
    TANH = "tanh"  # tanh((x - t) * beta)


@dataclass
class TreeConfig(ModelConfig):
    """Configuration for soft decision tree.

    Attributes:
        max_depth: Maximum depth of the tree.
        tree_type: Whether this is a classifier or regressor.
        split_function: Function used for soft splits.
        temperature: Sharpness of soft splits (higher = sharper).
        n_classes: Number of classes (for classifier).
        regularization: L2 regularization strength.
    """

    max_depth: int = 3
    tree_type: TreeType = TreeType.REGRESSOR
    split_function: SplitFunction = SplitFunction.SIGMOID
    temperature: float = 1.0
    n_classes: int = 2
    regularization: float = 0.01

    def __post_init__(self):
        super().__post_init__()
        if self.max_depth < 1:
            raise ValueError("max_depth must be at least 1")
        if self.temperature <= 0:
            raise ValueError("temperature must be positive")


class DecisionTree(BaseFHEModel):
    """Soft Decision Tree for FHE-encrypted data.

    This implementation uses a differentiable soft decision tree where:
    - Each internal node has a learned feature index, threshold, and temperature
    - Split decisions use sigmoid approximation: sigmoid((x[feature] - threshold) * beta)
    - Leaf nodes contain prediction values
    - The final prediction is a weighted sum of all leaf predictions

    For a tree of depth d, there are:
    - 2^d - 1 internal nodes
    - 2^d leaf nodes

    The tree computes predictions as:
        y = sum(path_probability[leaf] * leaf_value[leaf])

    where path_probability is the product of soft split decisions along the path.

    Example:
        >>> config = TreeConfig(max_depth=3, learning_rate=0.1)
        >>> tree = DecisionTree(config=config)
        >>> tree.fit(X_train, y_train)
        >>> predictions = tree.predict(encrypted_X_test)

    Attributes:
        feature_indices: Feature index for each internal node.
        thresholds: Split threshold for each internal node.
        temperatures: Split sharpness for each internal node.
        leaf_values: Prediction value at each leaf.
    """

    def __init__(
        self,
        config: Optional[TreeConfig] = None,
        encryptor: Optional[CKKSEncryptor] = None,
    ):
        """Initialize Decision Tree.

        Args:
            config: Tree configuration.
            encryptor: CKKS encryptor for operations.
        """
        if config is None:
            config = TreeConfig()
        super().__init__(config=config, encryptor=encryptor)

        self._tree_config = config
        self._n_internal_nodes = 2**config.max_depth - 1
        self._n_leaves = 2**config.max_depth

        # Tree parameters (initialized during fit)
        self._feature_indices: Optional[np.ndarray] = None
        self._thresholds: Optional[np.ndarray] = None
        self._temperatures: Optional[np.ndarray] = None
        self._leaf_values: Optional[np.ndarray] = None

    @property
    def max_depth(self) -> int:
        """Get maximum tree depth."""
        return self._tree_config.max_depth

    @property
    def n_internal_nodes(self) -> int:
        """Get number of internal nodes."""
        return self._n_internal_nodes

    @property
    def n_leaves(self) -> int:
        """Get number of leaf nodes."""
        return self._n_leaves

    @property
    def feature_indices(self) -> Optional[np.ndarray]:
        """Get feature indices for internal nodes."""
        return self._feature_indices

    @property
    def thresholds(self) -> Optional[np.ndarray]:
        """Get thresholds for internal nodes."""
        return self._thresholds

    @property
    def leaf_values(self) -> Optional[np.ndarray]:
        """Get prediction values at leaves."""
        return self._leaf_values

    def _initialize_tree(self, n_features: int, y_mean: float = 0.0) -> None:
        """Initialize tree parameters.

        Args:
            n_features: Number of input features.
            y_mean: Mean of target variable for leaf initialization.
        """
        self._n_features = n_features

        # Random feature selection for each internal node
        self._feature_indices = np.random.randint(0, n_features, size=self._n_internal_nodes)

        # Initialize thresholds near 0 (will be learned)
        self._thresholds = np.random.randn(self._n_internal_nodes) * 0.1

        # Initialize temperatures
        self._temperatures = np.ones(self._n_internal_nodes) * self._tree_config.temperature

        # Initialize leaf values around target mean
        self._leaf_values = np.random.randn(self._n_leaves) * 0.1 + y_mean

    def _soft_sigmoid(self, x: np.ndarray, beta: float = 1.0) -> np.ndarray:
        """Compute soft sigmoid for split decisions.

        Uses polynomial approximation compatible with FHE:
        sigmoid(x) approx 0.5 + 0.197x - 0.004x^3

        Args:
            x: Input values.
            beta: Temperature scaling.

        Returns:
            Soft split probabilities in [0, 1].
        """
        z = np.clip(x * beta, -5, 5)  # Prevent overflow
        # Polynomial approximation
        return 0.5 + 0.197 * z - 0.004 * (z**3)

    def _compute_path_probabilities(
        self,
        X: np.ndarray,
    ) -> np.ndarray:
        """Compute probability of reaching each leaf for all samples.

        Args:
            X: Input features of shape (n_samples, n_features).

        Returns:
            Path probabilities of shape (n_samples, n_leaves).
        """
        n_samples = X.shape[0]
        depth = self._tree_config.max_depth

        # Initialize with root probability = 1
        # We'll track probability of reaching each node
        node_probs = np.zeros((n_samples, self._n_internal_nodes + self._n_leaves))
        node_probs[:, 0] = 1.0  # Root node

        # Process each level of the tree
        for level in range(depth):
            start_idx = 2**level - 1
            end_idx = 2 ** (level + 1) - 1

            for node_idx in range(start_idx, end_idx):
                # Get split parameters for this node
                feature_idx = self._feature_indices[node_idx]
                threshold = self._thresholds[node_idx]
                temp = self._temperatures[node_idx]

                # Compute soft split probability
                x_feature = X[:, feature_idx]
                split_prob = self._soft_sigmoid(x_feature - threshold, temp)

                # Left child probability (x < threshold)
                left_child = 2 * node_idx + 1
                # Right child probability (x >= threshold)
                right_child = 2 * node_idx + 2

                parent_prob = node_probs[:, node_idx]

                if left_child < self._n_internal_nodes:
                    # Left child is internal node
                    node_probs[:, left_child] = parent_prob * (1 - split_prob)
                    node_probs[:, right_child] = parent_prob * split_prob
                else:
                    # Children are leaves - store in leaf array portion
                    leaf_left = left_child - self._n_internal_nodes
                    leaf_right = right_child - self._n_internal_nodes

                    # Map to leaf indices
                    node_probs[:, self._n_internal_nodes + leaf_left] = parent_prob * (
                        1 - split_prob
                    )
                    node_probs[:, self._n_internal_nodes + leaf_right] = parent_prob * split_prob

        # Extract leaf probabilities
        leaf_probs = node_probs[:, self._n_internal_nodes :]
        return leaf_probs

    def _compute_predictions(
        self,
        path_probs: np.ndarray,
    ) -> np.ndarray:
        """Compute predictions from path probabilities.

        Args:
            path_probs: Probability of reaching each leaf (n_samples, n_leaves).

        Returns:
            Predictions of shape (n_samples,).
        """
        # Weighted sum of leaf values
        predictions = path_probs @ self._leaf_values
        return predictions

    def _compute_gradients(
        self,
        X: np.ndarray,
        y: np.ndarray,
        path_probs: np.ndarray,
        predictions: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Compute gradients for tree parameters.

        Args:
            X: Input features (n_samples, n_features).
            y: Target values (n_samples,).
            path_probs: Leaf probabilities (n_samples, n_leaves).
            predictions: Current predictions (n_samples,).

        Returns:
            Tuple of (threshold_grads, temp_grads, leaf_grads).
        """
        n_samples = X.shape[0]
        errors = predictions - y  # (n_samples,)

        # Gradient for leaf values (simple: error * path_prob)
        # d(loss)/d(leaf_value[l]) = (1/n) * sum_i 2 * error_i * path_prob[i, l]
        leaf_grads = (2.0 / n_samples) * (path_probs.T @ errors)
        leaf_grads += self._tree_config.regularization * self._leaf_values

        # For thresholds and temperatures, we need gradient through soft sigmoid
        # This is more complex - use numerical approximation for simplicity
        threshold_grads = np.zeros(self._n_internal_nodes)
        temp_grads = np.zeros(self._n_internal_nodes)

        eps = 1e-5
        for node_idx in range(self._n_internal_nodes):
            # Numerical gradient for threshold
            orig_thresh = self._thresholds[node_idx]

            self._thresholds[node_idx] = orig_thresh + eps
            path_probs_plus = self._compute_path_probabilities(X)
            pred_plus = self._compute_predictions(path_probs_plus)
            loss_plus = np.mean((pred_plus - y) ** 2)

            self._thresholds[node_idx] = orig_thresh - eps
            path_probs_minus = self._compute_path_probabilities(X)
            pred_minus = self._compute_predictions(path_probs_minus)
            loss_minus = np.mean((pred_minus - y) ** 2)

            threshold_grads[node_idx] = (loss_plus - loss_minus) / (2 * eps)
            self._thresholds[node_idx] = orig_thresh

        return threshold_grads, temp_grads, leaf_grads

    def fit(
        self,
        X: Union[EncryptedDataset, EncryptedMatrix, np.ndarray],
        y: Optional[Union[EncryptedVector, np.ndarray]] = None,
    ) -> "DecisionTree":
        """Train the decision tree on data.

        For encrypted data, training happens on plaintext (model owner side),
        and the trained model can then make predictions on encrypted data.

        Args:
            X: Features (encrypted or plaintext).
            y: Target values (encrypted or plaintext).

        Returns:
            self for method chaining.
        """
        self._state = ModelState.TRAINING

        # Handle different input types
        if isinstance(X, EncryptedDataset):
            # For training, we need plaintext data
            raise ValueError(
                "Decision trees must be trained on plaintext data. "
                "Use numpy arrays for training, then predict on encrypted data."
            )
        elif isinstance(X, (EncryptedMatrix, EncryptedVector)):
            raise ValueError(
                "Decision trees must be trained on plaintext data. "
                "Use numpy arrays for training, then predict on encrypted data."
            )

        X_train = np.asarray(X)
        y_train = np.asarray(y)

        if X_train.ndim == 1:
            X_train = X_train.reshape(-1, 1)

        n_samples, n_features = X_train.shape

        # Initialize tree
        y_mean = np.mean(y_train)
        self._initialize_tree(n_features, y_mean)

        if self._config.verbose:
            print(f"Training DecisionTree: {n_samples} samples, {n_features} features")
            print(f"Tree depth: {self.max_depth}, Leaves: {self.n_leaves}")

        # Training loop
        best_loss = float("inf")
        patience_counter = 0

        for epoch in range(self._config.n_epochs):
            # Forward pass
            path_probs = self._compute_path_probabilities(X_train)
            predictions = self._compute_predictions(path_probs)

            # Compute loss
            mse_loss = np.mean((predictions - y_train) ** 2)
            reg_loss = 0.5 * self._tree_config.regularization * np.sum(self._leaf_values**2)
            total_loss = mse_loss + reg_loss

            self._history.add_epoch(total_loss, mse=mse_loss)

            if self._config.verbose and epoch % 10 == 0:
                print(f"Epoch {epoch}: loss={total_loss:.6f}, mse={mse_loss:.6f}")

            # Early stopping check
            if self._config.early_stopping_patience:
                if total_loss < best_loss - self._config.tolerance:
                    best_loss = total_loss
                    patience_counter = 0
                else:
                    patience_counter += 1
                    if patience_counter >= self._config.early_stopping_patience:
                        if self._config.verbose:
                            print(f"Early stopping at epoch {epoch}")
                        break

            # Compute gradients
            thresh_grads, temp_grads, leaf_grads = self._compute_gradients(
                X_train, y_train, path_probs, predictions
            )

            # Update parameters
            self._thresholds -= self._config.learning_rate * thresh_grads
            self._leaf_values -= self._config.learning_rate * leaf_grads

        self._state = ModelState.TRAINED

        if self._config.verbose:
            print(f"Training complete. Final loss: {self._history.losses[-1]:.6f}")

        return self

    def predict(
        self,
        X: Union[EncryptedMatrix, np.ndarray, list],
    ) -> Union[EncryptedVector, np.ndarray]:
        """Make predictions on data.

        Args:
            X: Features (encrypted or plaintext).

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

        path_probs = self._compute_path_probabilities(X_pred)
        predictions = self._compute_predictions(path_probs)

        return predictions

    def _predict_encrypted(
        self,
        X: Union[EncryptedMatrix, list[EncryptedVector]],
    ) -> EncryptedVector:
        """Make predictions on encrypted data.

        Uses polynomial operations compatible with FHE.

        Args:
            X: Encrypted features.

        Returns:
            Encrypted predictions.
        """
        encryptor = self._ensure_encryptor(X)

        if isinstance(X, list):
            encrypted_rows = X
        else:
            encrypted_rows = X

        results = []

        for enc_row in encrypted_rows:
            # For each sample, compute prediction using polynomial operations
            # This is a simplified version - full implementation would be more efficient

            # Decrypt for now (in production, use FHE polynomial evaluation)
            # This is a limitation - full FHE tree traversal needs more work
            x_plain = enc_row.decrypt()

            # Compute path probabilities (using polynomial sigmoid)
            path_probs = self._compute_path_probabilities(x_plain.reshape(1, -1))
            pred = self._compute_predictions(path_probs)[0]

            # Re-encrypt result
            results.append(pred)

        # Encrypt final result
        return encryptor.encrypt_vector(np.array(results))

    def get_params(self) -> dict[str, Any]:
        """Get model parameters as dictionary."""
        params = super().get_params()
        params.update(
            {
                "max_depth": self._tree_config.max_depth,
                "tree_type": self._tree_config.tree_type.value,
                "feature_indices": self._feature_indices.tolist()
                if self._feature_indices is not None
                else None,
                "thresholds": self._thresholds.tolist() if self._thresholds is not None else None,
                "temperatures": self._temperatures.tolist()
                if self._temperatures is not None
                else None,
                "leaf_values": self._leaf_values.tolist()
                if self._leaf_values is not None
                else None,
            }
        )
        return params

    def set_params(self, params: dict[str, Any]) -> None:
        """Set model parameters from dictionary."""
        super().set_params(params)
        if params.get("feature_indices") is not None:
            self._feature_indices = np.array(params["feature_indices"])
        if params.get("thresholds") is not None:
            self._thresholds = np.array(params["thresholds"])
        if params.get("temperatures") is not None:
            self._temperatures = np.array(params["temperatures"])
        if params.get("leaf_values") is not None:
            self._leaf_values = np.array(params["leaf_values"])

    def __repr__(self) -> str:
        return (
            f"DecisionTree(depth={self.max_depth}, leaves={self.n_leaves}, "
            f"state={self._state.value})"
        )


class DecisionTreeClassifier(DecisionTree):
    """Decision Tree Classifier for FHE-encrypted data.

    Extends DecisionTree with softmax leaf outputs for classification.
    """

    def __init__(
        self,
        config: Optional[TreeConfig] = None,
        encryptor: Optional[CKKSEncryptor] = None,
    ):
        """Initialize Decision Tree Classifier.

        Args:
            config: Tree configuration.
            encryptor: CKKS encryptor for operations.
        """
        if config is None:
            config = TreeConfig(tree_type=TreeType.CLASSIFIER)
        else:
            config.tree_type = TreeType.CLASSIFIER

        super().__init__(config=config, encryptor=encryptor)

        self._n_classes = config.n_classes
        # Override leaf values to be class probabilities
        self._leaf_class_probs: Optional[np.ndarray] = None

    def _initialize_tree(self, n_features: int, y_mean: float = 0.0) -> None:
        """Initialize tree for classification."""
        super()._initialize_tree(n_features, y_mean)

        # Initialize leaf class probabilities
        self._leaf_class_probs = np.random.randn(self._n_leaves, self._n_classes) * 0.1

    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Compute softmax for class probabilities."""
        exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=-1, keepdims=True)

    def predict_proba(
        self,
        X: Union[EncryptedMatrix, np.ndarray],
    ) -> np.ndarray:
        """Predict class probabilities.

        Args:
            X: Features.

        Returns:
            Class probabilities of shape (n_samples, n_classes).
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        X_pred = np.asarray(X)
        if X_pred.ndim == 1:
            X_pred = X_pred.reshape(-1, 1)

        path_probs = self._compute_path_probabilities(X_pred)

        # Weighted combination of leaf class probabilities
        # (n_samples, n_leaves) @ (n_leaves, n_classes) = (n_samples, n_classes)
        logits = path_probs @ self._leaf_class_probs
        probs = self._softmax(logits)

        return probs

    def predict(
        self,
        X: Union[EncryptedMatrix, np.ndarray, list],
    ) -> np.ndarray:
        """Predict class labels.

        Args:
            X: Features.

        Returns:
            Predicted class labels.
        """
        probs = self.predict_proba(X)
        return np.argmax(probs, axis=1)


class DecisionTreeRegressor(DecisionTree):
    """Decision Tree Regressor for FHE-encrypted data.

    Alias for DecisionTree with regressor configuration.
    """

    def __init__(
        self,
        config: Optional[TreeConfig] = None,
        encryptor: Optional[CKKSEncryptor] = None,
    ):
        """Initialize Decision Tree Regressor.

        Args:
            config: Tree configuration.
            encryptor: CKKS encryptor for operations.
        """
        if config is None:
            config = TreeConfig(tree_type=TreeType.REGRESSOR)
        else:
            config.tree_type = TreeType.REGRESSOR

        super().__init__(config=config, encryptor=encryptor)

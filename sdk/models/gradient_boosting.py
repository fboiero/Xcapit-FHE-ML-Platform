"""FHE-compatible Gradient Boosting.

This module implements Gradient Boosting ensemble for FHE-encrypted data,
using soft decision trees as weak learners that are trained sequentially
to minimize a differentiable loss function.

Key design decisions for FHE compatibility:
- Uses soft decision trees with polynomial splits
- Training on plaintext, inference on encrypted data
- Supports regression (MSE) and classification (log loss)
"""

from dataclasses import dataclass
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
from .decision_tree import DecisionTree, DecisionTreeRegressor, TreeConfig


class LossFunction(Enum):
    """Loss functions for gradient boosting."""

    MSE = "mse"  # Mean Squared Error (regression)
    MAE = "mae"  # Mean Absolute Error (regression)
    HUBER = "huber"  # Huber loss (robust regression)
    LOG_LOSS = "log_loss"  # Binary cross-entropy (classification)
    EXPONENTIAL = "exponential"  # Exponential loss (AdaBoost-like)


@dataclass
class GradientBoostingConfig(ModelConfig):
    """Configuration for Gradient Boosting.

    Attributes:
        n_estimators: Number of boosting stages (trees).
        max_depth: Maximum depth of individual trees.
        learning_rate: Shrinkage parameter (0 < lr <= 1).
        subsample: Fraction of samples for fitting each tree.
        max_features: Features to consider per tree (sqrt, log2, float, int, None).
        min_samples_split: Minimum samples to split a node.
        loss: Loss function to optimize.
        huber_delta: Delta parameter for Huber loss.
        validation_fraction: Fraction for early stopping validation.
        n_iter_no_change: Iterations without improvement for early stopping.
        random_state: Random seed for reproducibility.
    """

    n_estimators: int = 100
    max_depth: int = 3
    learning_rate: float = 0.1
    subsample: float = 1.0
    max_features: Union[str, int, float, None] = None
    min_samples_split: int = 2
    loss: LossFunction = LossFunction.MSE
    huber_delta: float = 1.0
    validation_fraction: float = 0.1
    n_iter_no_change: Optional[int] = None
    random_state: Optional[int] = None

    def __post_init__(self):
        super().__post_init__()
        if self.n_estimators < 1:
            raise ValueError("n_estimators must be at least 1")
        if self.max_depth < 1:
            raise ValueError("max_depth must be at least 1")
        if not 0 < self.learning_rate <= 1:
            raise ValueError("learning_rate must be in (0, 1]")
        if not 0 < self.subsample <= 1:
            raise ValueError("subsample must be in (0, 1]")
        if not 0 < self.validation_fraction < 1:
            raise ValueError("validation_fraction must be in (0, 1)")


class LossFunctions:
    """Loss functions and their gradients for gradient boosting."""

    @staticmethod
    def mse_loss(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Mean Squared Error loss."""
        return np.mean((y_true - y_pred) ** 2)

    @staticmethod
    def mse_negative_gradient(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        """Negative gradient of MSE (residuals)."""
        return y_true - y_pred

    @staticmethod
    def mae_loss(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Mean Absolute Error loss."""
        return np.mean(np.abs(y_true - y_pred))

    @staticmethod
    def mae_negative_gradient(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        """Negative gradient of MAE (sign of residuals)."""
        return np.sign(y_true - y_pred)

    @staticmethod
    def huber_loss(y_true: np.ndarray, y_pred: np.ndarray, delta: float = 1.0) -> float:
        """Huber loss (robust to outliers)."""
        residual = y_true - y_pred
        abs_residual = np.abs(residual)
        quadratic = np.minimum(abs_residual, delta)
        linear = abs_residual - quadratic
        return np.mean(0.5 * quadratic**2 + delta * linear)

    @staticmethod
    def huber_negative_gradient(
        y_true: np.ndarray, y_pred: np.ndarray, delta: float = 1.0
    ) -> np.ndarray:
        """Negative gradient of Huber loss."""
        residual = y_true - y_pred
        return np.where(np.abs(residual) <= delta, residual, delta * np.sign(residual))

    @staticmethod
    def log_loss(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Binary cross-entropy loss."""
        # Clip to avoid log(0)
        y_pred = np.clip(y_pred, 1e-10, 1 - 1e-10)
        return -np.mean(y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred))

    @staticmethod
    def log_loss_negative_gradient(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        """Negative gradient of log loss."""
        # Clip to avoid division by zero
        y_pred = np.clip(y_pred, 1e-10, 1 - 1e-10)
        return y_true - y_pred

    @staticmethod
    def exponential_loss(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Exponential loss (AdaBoost)."""
        # y_true should be in {-1, 1}
        return np.mean(np.exp(-y_true * y_pred))

    @staticmethod
    def exponential_negative_gradient(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        """Negative gradient of exponential loss."""
        return y_true * np.exp(-y_true * y_pred)

    @classmethod
    def get_loss_function(cls, loss: LossFunction) -> Callable:
        """Get loss function by enum."""
        mapping = {
            LossFunction.MSE: cls.mse_loss,
            LossFunction.MAE: cls.mae_loss,
            LossFunction.HUBER: cls.huber_loss,
            LossFunction.LOG_LOSS: cls.log_loss,
            LossFunction.EXPONENTIAL: cls.exponential_loss,
        }
        return mapping[loss]

    @classmethod
    def get_negative_gradient(cls, loss: LossFunction) -> Callable:
        """Get negative gradient function by enum."""
        mapping = {
            LossFunction.MSE: cls.mse_negative_gradient,
            LossFunction.MAE: cls.mae_negative_gradient,
            LossFunction.HUBER: cls.huber_negative_gradient,
            LossFunction.LOG_LOSS: cls.log_loss_negative_gradient,
            LossFunction.EXPONENTIAL: cls.exponential_negative_gradient,
        }
        return mapping[loss]


class GradientBoosting(BaseFHEModel):
    """Gradient Boosting ensemble for FHE-encrypted data.

    This implementation trains soft decision trees sequentially, where each
    tree fits the negative gradient (pseudo-residuals) of the loss function.
    The final prediction is the sum of all tree predictions scaled by the
    learning rate.

    Key features:
    - Sequential training of weak learners
    - Shrinkage (learning rate) for regularization
    - Stochastic gradient boosting (subsampling)
    - Early stopping with validation set
    - FHE compatible using soft decision trees

    Example:
        >>> from sdk.models import GradientBoosting, GradientBoostingConfig
        >>> config = GradientBoostingConfig(n_estimators=100, max_depth=3)
        >>> gb = GradientBoosting(config=config)
        >>> gb.fit(X_train, y_train)
        >>> predictions = gb.predict(X_test)

    For classification:
        >>> from sdk.models import GradientBoostingClassifier
        >>> clf = GradientBoostingClassifier(n_estimators=100)
        >>> clf.fit(X_train, y_train)
        >>> probs = clf.predict_proba(X_test)
    """

    fhe_level = FHELevel.TRANSPORT

    def __init__(
        self,
        config: Optional[GradientBoostingConfig] = None,
        encryptor: Optional[CKKSEncryptor] = None,
    ):
        """Initialize Gradient Boosting.

        Args:
            config: Boosting configuration.
            encryptor: CKKS encryptor for encrypted operations.
        """
        if config is None:
            config = GradientBoostingConfig()
        super().__init__(config=config, encryptor=encryptor)

        self._gb_config = config
        self._trees: list[DecisionTree] = []
        self._feature_subsets: list[Optional[np.ndarray]] = []
        self._initial_prediction: float = 0.0
        self._train_losses: list[float] = []
        self._val_losses: list[float] = []
        self._n_features: int = 0
        self._rng = np.random.RandomState(config.random_state)

    @property
    def n_estimators(self) -> int:
        """Get number of estimators."""
        return len(self._trees)

    @property
    def n_estimators_target(self) -> int:
        """Get target number of estimators."""
        return self._gb_config.n_estimators

    @property
    def trees(self) -> list[DecisionTree]:
        """Get list of trained trees."""
        return self._trees

    @property
    def feature_importances_(self) -> Optional[np.ndarray]:
        """Get feature importances based on usage across all trees.

        Returns:
            Array of shape (n_features,) with importance scores.
        """
        if not self.is_fitted:
            return None

        importances = np.zeros(self._n_features)

        for tree, features in zip(self._trees, self._feature_subsets):
            tree_importance = np.zeros(self._n_features)

            if tree.feature_indices is not None:
                for feat_idx in tree.feature_indices:
                    if features is not None:
                        original_idx = features[feat_idx]
                    else:
                        original_idx = feat_idx
                    tree_importance[original_idx] += 1

            # Weight by learning rate
            importances += tree_importance * self._gb_config.learning_rate

        # Normalize
        if importances.sum() > 0:
            importances /= importances.sum()

        return importances

    def _get_max_features(self, n_features: int) -> int:
        """Determine number of features to use for each tree."""
        max_features = self._gb_config.max_features

        if max_features is None:
            return n_features
        elif isinstance(max_features, str):
            if max_features == "sqrt":
                return max(1, int(np.sqrt(n_features)))
            elif max_features == "log2":
                return max(1, int(np.log2(n_features)))
            else:
                raise ValueError(f"Unknown max_features string: {max_features}")
        elif isinstance(max_features, float):
            return max(1, int(max_features * n_features))
        elif isinstance(max_features, int):
            return min(max_features, n_features)
        else:
            raise ValueError(f"Invalid max_features type: {type(max_features)}")

    def _compute_initial_prediction(self, y: np.ndarray) -> float:
        """Compute initial prediction (base value).

        For MSE, this is the mean. For classification, it's the log-odds.

        Args:
            y: Target values.

        Returns:
            Initial prediction value.
        """
        if self._gb_config.loss == LossFunction.LOG_LOSS:
            # Log-odds for binary classification
            p = np.clip(np.mean(y), 1e-10, 1 - 1e-10)
            return np.log(p / (1 - p))
        elif self._gb_config.loss == LossFunction.EXPONENTIAL:
            return 0.0
        else:
            # Mean for regression
            return np.mean(y)

    def _raw_to_proba(self, raw_predictions: np.ndarray) -> np.ndarray:
        """Convert raw predictions to probabilities.

        Args:
            raw_predictions: Raw model output.

        Returns:
            Probabilities in [0, 1].
        """
        # Sigmoid transformation
        return 1.0 / (1.0 + np.exp(-raw_predictions))

    def fit(
        self,
        X: Union[EncryptedDataset, EncryptedMatrix, np.ndarray],
        y: Optional[Union[EncryptedVector, np.ndarray]] = None,
    ) -> "GradientBoosting":
        """Train the Gradient Boosting ensemble.

        Training is done on plaintext data. The trained ensemble can then
        make predictions on encrypted data.

        Args:
            X: Features (must be plaintext for training).
            y: Target values.

        Returns:
            self for method chaining.
        """
        self._state = ModelState.TRAINING

        # Validate input
        if isinstance(X, (EncryptedDataset, EncryptedMatrix, EncryptedVector)):
            raise ValueError(
                "Gradient Boosting must be trained on plaintext data. "
                "Use numpy arrays for training, then predict on encrypted data."
            )

        X_train = np.asarray(X)
        y_train = np.asarray(y).ravel()

        if X_train.ndim == 1:
            X_train = X_train.reshape(-1, 1)

        n_samples, n_features = X_train.shape
        self._n_features = n_features

        # Split for early stopping if configured
        X_val, y_val = None, None
        if self._gb_config.n_iter_no_change is not None:
            n_val = int(n_samples * self._gb_config.validation_fraction)
            indices = self._rng.permutation(n_samples)
            val_indices = indices[:n_val]
            train_indices = indices[n_val:]

            X_val = X_train[val_indices]
            y_val = y_train[val_indices]
            X_train = X_train[train_indices]
            y_train = y_train[train_indices]
            n_samples = len(train_indices)

        n_max_features = self._get_max_features(n_features)

        if self._config.verbose:
            print(f"Training GradientBoosting: {self._gb_config.n_estimators} trees")
            print(f"  Samples: {n_samples}, Features: {n_features}")
            print(f"  Max depth: {self._gb_config.max_depth}")
            print(f"  Learning rate: {self._gb_config.learning_rate}")
            print(f"  Loss: {self._gb_config.loss.value}")

        # Initialize predictions
        self._initial_prediction = self._compute_initial_prediction(y_train)
        current_predictions = np.full(n_samples, self._initial_prediction)

        if X_val is not None:
            val_predictions = np.full(len(y_val), self._initial_prediction)

        # Get loss functions
        loss_fn = LossFunctions.get_loss_function(self._gb_config.loss)
        neg_gradient_fn = LossFunctions.get_negative_gradient(self._gb_config.loss)

        # Initialize
        self._trees = []
        self._feature_subsets = []
        self._train_losses = []
        self._val_losses = []

        best_val_loss = float("inf")
        no_improvement_count = 0

        # Training loop
        for i in range(self._gb_config.n_estimators):
            # Compute negative gradient (pseudo-residuals)
            if self._gb_config.loss == LossFunction.HUBER:
                residuals = neg_gradient_fn(
                    y_train, current_predictions, self._gb_config.huber_delta
                )
            else:
                residuals = neg_gradient_fn(y_train, current_predictions)

            # Subsample if configured
            if self._gb_config.subsample < 1.0:
                n_subsample = int(n_samples * self._gb_config.subsample)
                sample_indices = self._rng.choice(n_samples, size=n_subsample, replace=False)
                X_sample = X_train[sample_indices]
                residuals_sample = residuals[sample_indices]
            else:
                X_sample = X_train
                residuals_sample = residuals
                sample_indices = None

            # Feature subsampling
            if n_max_features < n_features:
                feature_subset = self._rng.choice(n_features, size=n_max_features, replace=False)
                feature_subset.sort()
                X_subset = X_sample[:, feature_subset]
            else:
                feature_subset = None
                X_subset = X_sample

            # Create and train tree on residuals
            tree_config = TreeConfig(
                max_depth=self._gb_config.max_depth,
                learning_rate=self._config.learning_rate,
                n_epochs=self._config.n_epochs,
                verbose=False,
            )

            tree = DecisionTreeRegressor(config=tree_config, encryptor=self._encryptor)
            tree.fit(X_subset, residuals_sample)

            # Update predictions
            if feature_subset is not None:
                tree_pred = tree.predict(X_train[:, feature_subset])
            else:
                tree_pred = tree.predict(X_train)

            current_predictions += self._gb_config.learning_rate * tree_pred

            # Store tree
            self._trees.append(tree)
            self._feature_subsets.append(feature_subset)

            # Compute training loss
            if self._gb_config.loss == LossFunction.LOG_LOSS:
                proba = self._raw_to_proba(current_predictions)
                train_loss = loss_fn(y_train, proba)
            elif self._gb_config.loss == LossFunction.HUBER:
                train_loss = loss_fn(y_train, current_predictions, self._gb_config.huber_delta)
            else:
                train_loss = loss_fn(y_train, current_predictions)

            self._train_losses.append(train_loss)

            # Validation loss for early stopping
            if X_val is not None:
                if feature_subset is not None:
                    val_tree_pred = tree.predict(X_val[:, feature_subset])
                else:
                    val_tree_pred = tree.predict(X_val)

                val_predictions += self._gb_config.learning_rate * val_tree_pred

                if self._gb_config.loss == LossFunction.LOG_LOSS:
                    val_proba = self._raw_to_proba(val_predictions)
                    val_loss = loss_fn(y_val, val_proba)
                elif self._gb_config.loss == LossFunction.HUBER:
                    val_loss = loss_fn(y_val, val_predictions, self._gb_config.huber_delta)
                else:
                    val_loss = loss_fn(y_val, val_predictions)

                self._val_losses.append(val_loss)

                # Early stopping check
                if val_loss < best_val_loss - self._config.tolerance:
                    best_val_loss = val_loss
                    no_improvement_count = 0
                else:
                    no_improvement_count += 1
                    if no_improvement_count >= self._gb_config.n_iter_no_change:
                        if self._config.verbose:
                            print(f"  Early stopping at iteration {i + 1}")
                        break

            if self._config.verbose and (i + 1) % max(1, self._gb_config.n_estimators // 10) == 0:
                msg = f"  Iter {i + 1}/{self._gb_config.n_estimators}, Train loss: {train_loss:.6f}"
                if X_val is not None:
                    msg += f", Val loss: {val_loss:.6f}"
                print(msg)

        self._state = ModelState.TRAINED

        if self._config.verbose:
            print(f"Training complete. Final train loss: {self._train_losses[-1]:.6f}")

        return self

    def _predict_raw(self, X: np.ndarray) -> np.ndarray:
        """Get raw predictions (before transformation).

        Args:
            X: Features.

        Returns:
            Raw predictions.
        """
        X_pred = np.asarray(X)
        if X_pred.ndim == 1:
            X_pred = X_pred.reshape(-1, 1)

        predictions = np.full(X_pred.shape[0], self._initial_prediction)

        for tree, features in zip(self._trees, self._feature_subsets):
            if features is not None:
                X_subset = X_pred[:, features]
            else:
                X_subset = X_pred

            predictions += self._gb_config.learning_rate * tree.predict(X_subset)

        return predictions

    def predict(
        self,
        X: Union[EncryptedMatrix, np.ndarray, list],
    ) -> Union[EncryptedVector, np.ndarray]:
        """Make predictions.

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

        return self._predict_raw(X)

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
            pred = self._predict_raw(x_plain)[0]
            results.append(pred)

        return encryptor.encrypt_vector(np.array(results))

    def staged_predict(self, X: np.ndarray) -> np.ndarray:
        """Generate predictions at each stage.

        Args:
            X: Features.

        Yields:
            Predictions at each stage.
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        X_pred = np.asarray(X)
        if X_pred.ndim == 1:
            X_pred = X_pred.reshape(-1, 1)

        predictions = np.full(X_pred.shape[0], self._initial_prediction)

        for tree, features in zip(self._trees, self._feature_subsets):
            if features is not None:
                X_subset = X_pred[:, features]
            else:
                X_subset = X_pred

            predictions = predictions + self._gb_config.learning_rate * tree.predict(X_subset)
            yield predictions.copy()

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Compute R² score for regression.

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

    def get_params(self) -> dict[str, Any]:
        """Get model parameters."""
        params = super().get_params()
        params.update(
            {
                "n_estimators": self.n_estimators,
                "n_estimators_target": self.n_estimators_target,
                "max_depth": self._gb_config.max_depth,
                "learning_rate": self._gb_config.learning_rate,
                "loss": self._gb_config.loss.value,
                "initial_prediction": self._initial_prediction,
                "train_losses": self._train_losses,
                "val_losses": self._val_losses,
                "n_features": self._n_features,
                "feature_subsets": [
                    fs.tolist() if fs is not None else None for fs in self._feature_subsets
                ],
                "trees": [tree.get_params() for tree in self._trees],
            }
        )
        return params

    def __repr__(self) -> str:
        return (
            f"GradientBoosting(n_estimators={self.n_estimators}/{self.n_estimators_target}, "
            f"max_depth={self._gb_config.max_depth}, "
            f"state={self._state.value})"
        )


class GradientBoostingClassifier(GradientBoosting):
    """Gradient Boosting Classifier for FHE-encrypted data.

    Uses log loss (binary cross-entropy) for binary classification.
    Predictions are converted to probabilities using sigmoid.

    Example:
        >>> clf = GradientBoostingClassifier(n_estimators=100, max_depth=3)
        >>> clf.fit(X_train, y_train)
        >>> predictions = clf.predict(X_test)
        >>> probabilities = clf.predict_proba(X_test)
    """

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 3,
        learning_rate: float = 0.1,
        subsample: float = 1.0,
        max_features: Union[str, int, float, None] = None,
        n_iter_no_change: Optional[int] = None,
        random_state: Optional[int] = None,
        encryptor: Optional[CKKSEncryptor] = None,
        **kwargs,
    ):
        """Initialize Gradient Boosting Classifier.

        Args:
            n_estimators: Number of boosting stages.
            max_depth: Maximum depth of trees.
            learning_rate: Shrinkage parameter.
            subsample: Fraction of samples per tree.
            max_features: Features to consider per tree.
            n_iter_no_change: Early stopping patience.
            random_state: Random seed.
            encryptor: CKKS encryptor.
            **kwargs: Additional config parameters.
        """
        config = GradientBoostingConfig(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            subsample=subsample,
            max_features=max_features,
            loss=LossFunction.LOG_LOSS,
            n_iter_no_change=n_iter_no_change,
            random_state=random_state,
            **kwargs,
        )
        super().__init__(config=config, encryptor=encryptor)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict class probabilities.

        Args:
            X: Features.

        Returns:
            Probabilities of shape (n_samples, 2).
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        raw_predictions = self._predict_raw(X)
        proba_pos = self._raw_to_proba(raw_predictions)

        # Return probabilities for both classes
        return np.column_stack([1 - proba_pos, proba_pos])

    def predict(
        self,
        X: Union[EncryptedMatrix, np.ndarray, list],
    ) -> np.ndarray:
        """Predict class labels.

        Args:
            X: Features.

        Returns:
            Predicted class labels (0 or 1).
        """
        if isinstance(X, (EncryptedMatrix, list)):
            return super().predict(X)

        proba = self.predict_proba(X)
        return (proba[:, 1] >= 0.5).astype(int)

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

    def staged_predict_proba(self, X: np.ndarray):
        """Generate probability predictions at each stage.

        Args:
            X: Features.

        Yields:
            Probabilities at each stage.
        """
        for raw_predictions in self.staged_predict(X):
            proba_pos = self._raw_to_proba(raw_predictions)
            yield np.column_stack([1 - proba_pos, proba_pos])


class GradientBoostingRegressor(GradientBoosting):
    """Gradient Boosting Regressor for FHE-encrypted data.

    Uses MSE loss by default. Also supports MAE and Huber loss.

    Example:
        >>> reg = GradientBoostingRegressor(n_estimators=100, max_depth=3)
        >>> reg.fit(X_train, y_train)
        >>> predictions = reg.predict(X_test)
    """

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 3,
        learning_rate: float = 0.1,
        subsample: float = 1.0,
        max_features: Union[str, int, float, None] = None,
        loss: str = "mse",
        n_iter_no_change: Optional[int] = None,
        random_state: Optional[int] = None,
        encryptor: Optional[CKKSEncryptor] = None,
        **kwargs,
    ):
        """Initialize Gradient Boosting Regressor.

        Args:
            n_estimators: Number of boosting stages.
            max_depth: Maximum depth of trees.
            learning_rate: Shrinkage parameter.
            subsample: Fraction of samples per tree.
            max_features: Features to consider per tree.
            loss: Loss function ('mse', 'mae', 'huber').
            n_iter_no_change: Early stopping patience.
            random_state: Random seed.
            encryptor: CKKS encryptor.
            **kwargs: Additional config parameters.
        """
        loss_enum = {
            "mse": LossFunction.MSE,
            "mae": LossFunction.MAE,
            "huber": LossFunction.HUBER,
        }.get(loss, LossFunction.MSE)

        config = GradientBoostingConfig(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            subsample=subsample,
            max_features=max_features,
            loss=loss_enum,
            n_iter_no_change=n_iter_no_change,
            random_state=random_state,
            **kwargs,
        )
        super().__init__(config=config, encryptor=encryptor)

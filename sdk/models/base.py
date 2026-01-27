"""Base class for FHE models.

This module provides the abstract base class for all FHE-compatible
machine learning models in the Xcapit FHE-ML SDK.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Union

import numpy as np

from ..encryption.ckks_wrapper import (
    CKKSEncryptor,
    EncryptedMatrix,
    EncryptedVector,
)
from ..utils.data_loader import EncryptedDataset


class ModelState(Enum):
    """Model lifecycle states."""

    INITIALIZED = "initialized"
    TRAINING = "training"
    TRAINED = "trained"
    FAILED = "failed"


@dataclass
class TrainingHistory:
    """Container for training metrics history.

    Attributes:
        losses: Loss value at each epoch.
        epochs: Number of epochs completed.
        metrics: Additional metrics per epoch.
    """

    losses: list[float] = field(default_factory=list)
    epochs: int = 0
    metrics: dict[str, list[float]] = field(default_factory=dict)

    def add_epoch(self, loss: float, **kwargs) -> None:
        """Record metrics for an epoch."""
        self.losses.append(loss)
        self.epochs += 1
        for key, value in kwargs.items():
            if key not in self.metrics:
                self.metrics[key] = []
            self.metrics[key].append(value)


@dataclass
class ModelConfig:
    """Configuration for FHE model training.

    Attributes:
        learning_rate: Step size for gradient descent.
        n_epochs: Number of training epochs.
        batch_size: Samples per batch (None = full batch).
        verbose: Whether to print training progress.
        early_stopping_patience: Epochs without improvement before stopping.
        tolerance: Minimum loss improvement for early stopping.
    """

    learning_rate: float = 0.01
    n_epochs: int = 100
    batch_size: Optional[int] = None
    verbose: bool = False
    early_stopping_patience: Optional[int] = None
    tolerance: float = 1e-4

    def __post_init__(self):
        if self.learning_rate <= 0:
            raise ValueError("learning_rate must be positive")
        if self.n_epochs <= 0:
            raise ValueError("n_epochs must be positive")


class BaseFHEModel(ABC):
    """Abstract base class for FHE-compatible ML models.

    This class defines the interface that all FHE models must implement,
    following a scikit-learn-like API for familiarity.

    Attributes:
        config: Model training configuration.
        state: Current model state.
        history: Training history with losses and metrics.
    """

    def __init__(
        self,
        config: Optional[ModelConfig] = None,
        encryptor: Optional[CKKSEncryptor] = None,
    ):
        """Initialize base model.

        Args:
            config: Training configuration.
            encryptor: CKKS encryptor for operations.
        """
        self._config = config or ModelConfig()
        self._encryptor = encryptor
        self._state = ModelState.INITIALIZED
        self._history = TrainingHistory()
        self._weights: Optional[np.ndarray] = None
        self._bias: Optional[float] = None
        self._n_features: Optional[int] = None

    @property
    def config(self) -> ModelConfig:
        """Get model configuration."""
        return self._config

    @property
    def state(self) -> ModelState:
        """Get current model state."""
        return self._state

    @property
    def history(self) -> TrainingHistory:
        """Get training history."""
        return self._history

    @property
    def is_fitted(self) -> bool:
        """Check if model has been trained."""
        return self._state == ModelState.TRAINED

    @property
    def weights(self) -> Optional[np.ndarray]:
        """Get model weights (None if not fitted)."""
        return self._weights

    @property
    def bias(self) -> Optional[float]:
        """Get model bias (None if not fitted)."""
        return self._bias

    @property
    def n_features(self) -> Optional[int]:
        """Get number of features (None if not fitted)."""
        return self._n_features

    def _ensure_encryptor(
        self,
        encrypted_data: Union[EncryptedDataset, EncryptedMatrix],
    ) -> CKKSEncryptor:
        """Ensure we have an encryptor, getting from data if needed."""
        if self._encryptor is not None:
            return self._encryptor

        # Try to get encryptor from encrypted data context
        if isinstance(encrypted_data, EncryptedDataset):
            # Get context from first row
            ctx = encrypted_data.X[0].ciphertext.context()
        else:
            ctx = encrypted_data[0].ciphertext.context()

        from ..encryption.context_manager import FHEContextManager

        manager = FHEContextManager()
        manager._context = ctx
        self._encryptor = CKKSEncryptor(manager)
        return self._encryptor

    @abstractmethod
    def fit(
        self,
        X: Union[EncryptedDataset, EncryptedMatrix],
        y: Optional[EncryptedVector] = None,
    ) -> "BaseFHEModel":
        """Train the model on encrypted data.

        Args:
            X: Encrypted features (EncryptedDataset or EncryptedMatrix).
            y: Encrypted target (optional if X is EncryptedDataset with y).

        Returns:
            self for method chaining.
        """
        pass

    @abstractmethod
    def predict(
        self,
        X: Union[EncryptedMatrix, EncryptedVector],
    ) -> EncryptedVector:
        """Make predictions on encrypted data.

        Args:
            X: Encrypted features.

        Returns:
            Encrypted predictions.
        """
        pass

    def fit_predict(
        self,
        X: Union[EncryptedDataset, EncryptedMatrix],
        y: Optional[EncryptedVector] = None,
    ) -> EncryptedVector:
        """Fit model and return predictions on training data.

        Args:
            X: Encrypted features.
            y: Encrypted target.

        Returns:
            Encrypted predictions on training data.
        """
        self.fit(X, y)
        if isinstance(X, EncryptedDataset):
            return self.predict(X.X)
        return self.predict(X)

    def get_params(self) -> dict[str, Any]:
        """Get model parameters as dictionary."""
        return {
            "weights": self._weights.tolist() if self._weights is not None else None,
            "bias": self._bias,
            "n_features": self._n_features,
            "state": self._state.value,
            "config": {
                "learning_rate": self._config.learning_rate,
                "n_epochs": self._config.n_epochs,
            },
        }

    def set_params(self, params: dict[str, Any]) -> None:
        """Set model parameters from dictionary."""
        if params.get("weights") is not None:
            self._weights = np.array(params["weights"])
        if params.get("bias") is not None:
            self._bias = params["bias"]
        if params.get("n_features") is not None:
            self._n_features = params["n_features"]
        if params.get("state") is not None:
            self._state = ModelState(params["state"])

    def __repr__(self) -> str:
        name = self.__class__.__name__
        return f"{name}(state={self._state.value}, features={self._n_features})"


class FHEModel:
    """Factory class for creating FHE models.

    Provides a namespace for accessing different model types,
    similar to how sklearn organizes models.

    Example:
        >>> model = FHEModel.LinearRegression()
        >>> model.fit(encrypted_data)
    """

    @staticmethod
    def LinearRegression(**kwargs) -> "BaseFHEModel":
        """Create a Linear Regression model.

        Args:
            **kwargs: Arguments passed to LinearRegression constructor.

        Returns:
            LinearRegression model instance.
        """
        from .linear_regression import LinearRegression

        return LinearRegression(**kwargs)

    @staticmethod
    def LogisticRegression(**kwargs) -> "BaseFHEModel":
        """Create a Logistic Regression model.

        Args:
            **kwargs: Arguments passed to LogisticRegression constructor.

        Returns:
            LogisticRegression model instance.
        """
        from .logistic_regression import LogisticRegression

        return LogisticRegression(**kwargs)

    @staticmethod
    def DecisionTree(**kwargs) -> "BaseFHEModel":
        """Create a Decision Tree model.

        Args:
            **kwargs: Arguments passed to DecisionTree constructor.

        Returns:
            DecisionTree model instance.
        """
        from .decision_tree import DecisionTree

        return DecisionTree(**kwargs)

    @staticmethod
    def DecisionTreeClassifier(**kwargs) -> "BaseFHEModel":
        """Create a Decision Tree Classifier.

        Args:
            **kwargs: Arguments passed to DecisionTreeClassifier constructor.

        Returns:
            DecisionTreeClassifier model instance.
        """
        from .decision_tree import DecisionTreeClassifier

        return DecisionTreeClassifier(**kwargs)

    @staticmethod
    def DecisionTreeRegressor(**kwargs) -> "BaseFHEModel":
        """Create a Decision Tree Regressor.

        Args:
            **kwargs: Arguments passed to DecisionTreeRegressor constructor.

        Returns:
            DecisionTreeRegressor model instance.
        """
        from .decision_tree import DecisionTreeRegressor

        return DecisionTreeRegressor(**kwargs)

    @staticmethod
    def KMeans(**kwargs) -> "BaseFHEModel":
        """Create a K-Means clustering model.

        Args:
            **kwargs: Arguments passed to KMeans constructor.

        Returns:
            KMeans model instance.
        """
        from .kmeans import KMeans

        return KMeans(**kwargs)

    @staticmethod
    def MiniBatchKMeans(**kwargs) -> "BaseFHEModel":
        """Create a Mini-batch K-Means clustering model.

        Args:
            **kwargs: Arguments passed to MiniBatchKMeans constructor.

        Returns:
            MiniBatchKMeans model instance.
        """
        from .kmeans import MiniBatchKMeans

        return MiniBatchKMeans(**kwargs)

    @staticmethod
    def RandomForest(**kwargs) -> "BaseFHEModel":
        """Create a Random Forest model.

        Args:
            **kwargs: Arguments passed to RandomForest constructor.

        Returns:
            RandomForest model instance.
        """
        from .random_forest import RandomForest

        return RandomForest(**kwargs)

    @staticmethod
    def RandomForestClassifier(**kwargs) -> "BaseFHEModel":
        """Create a Random Forest Classifier.

        Args:
            **kwargs: Arguments passed to RandomForestClassifier constructor.

        Returns:
            RandomForestClassifier model instance.
        """
        from .random_forest import RandomForestClassifier

        return RandomForestClassifier(**kwargs)

    @staticmethod
    def RandomForestRegressor(**kwargs) -> "BaseFHEModel":
        """Create a Random Forest Regressor.

        Args:
            **kwargs: Arguments passed to RandomForestRegressor constructor.

        Returns:
            RandomForestRegressor model instance.
        """
        from .random_forest import RandomForestRegressor

        return RandomForestRegressor(**kwargs)

    @staticmethod
    def NeuralNetwork(**kwargs) -> "BaseFHEModel":
        """Create a Neural Network model.

        Args:
            **kwargs: Arguments passed to NeuralNetwork constructor.

        Returns:
            NeuralNetwork model instance.
        """
        from .neural_network import NeuralNetwork

        return NeuralNetwork(**kwargs)

    @staticmethod
    def NeuralNetworkClassifier(**kwargs) -> "BaseFHEModel":
        """Create a Neural Network Classifier.

        Args:
            **kwargs: Arguments passed to NeuralNetworkClassifier constructor.

        Returns:
            NeuralNetworkClassifier model instance.
        """
        from .neural_network import NeuralNetworkClassifier

        return NeuralNetworkClassifier(**kwargs)

    @staticmethod
    def NeuralNetworkRegressor(**kwargs) -> "BaseFHEModel":
        """Create a Neural Network Regressor.

        Args:
            **kwargs: Arguments passed to NeuralNetworkRegressor constructor.

        Returns:
            NeuralNetworkRegressor model instance.
        """
        from .neural_network import NeuralNetworkRegressor

        return NeuralNetworkRegressor(**kwargs)

    @staticmethod
    def GradientBoosting(**kwargs) -> "BaseFHEModel":
        """Create a Gradient Boosting model.

        Args:
            **kwargs: Arguments passed to GradientBoosting constructor.

        Returns:
            GradientBoosting model instance.
        """
        from .gradient_boosting import GradientBoosting

        return GradientBoosting(**kwargs)

    @staticmethod
    def GradientBoostingClassifier(**kwargs) -> "BaseFHEModel":
        """Create a Gradient Boosting Classifier.

        Args:
            **kwargs: Arguments passed to GradientBoostingClassifier constructor.

        Returns:
            GradientBoostingClassifier model instance.
        """
        from .gradient_boosting import GradientBoostingClassifier

        return GradientBoostingClassifier(**kwargs)

    @staticmethod
    def GradientBoostingRegressor(**kwargs) -> "BaseFHEModel":
        """Create a Gradient Boosting Regressor.

        Args:
            **kwargs: Arguments passed to GradientBoostingRegressor constructor.

        Returns:
            GradientBoostingRegressor model instance.
        """
        from .gradient_boosting import GradientBoostingRegressor

        return GradientBoostingRegressor(**kwargs)

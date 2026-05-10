"""Base model for FHE-ML models."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import numpy as np

from ..encryption.ckks_wrapper import CKKSEncryptor, EncryptedMatrix


class FHELevel(Enum):
    """Level of FHE support for a model.

    - NONE: no encryption at any stage.
    - TRANSPORT: data encrypted in transit and at rest, but decrypted before
      computation (training and inference operate on plaintext).
    - PARTIAL: some operations run on encrypted data (e.g., single-sample
      inference) but not all paths are fully homomorphic.
    - FULL: training or inference can operate entirely on encrypted data
      without decryption (e.g., CKKS dot product for linear models).
    """

    NONE = "none"
    TRANSPORT = "transport"
    PARTIAL = "partial"
    FULL = "full"


class ModelState(Enum):
    """Model lifecycle state."""

    INITIALIZED = "initialized"
    TRAINING = "training"
    TRAINED = "trained"
    FAILED = "failed"


@dataclass
class ModelConfig:
    """Training configuration."""

    learning_rate: float = 0.01
    n_epochs: int = 100
    batch_size: Optional[int] = None
    verbose: bool = False
    early_stopping_patience: Optional[int] = None
    tolerance: float = 1e-4

    def __post_init__(self):
        """Validate base config. Subclass configs call super().__post_init__()."""
        if self.learning_rate <= 0:
            raise ValueError(f"learning_rate must be positive, got {self.learning_rate}")
        if self.n_epochs < 1:
            raise ValueError(f"n_epochs must be >= 1, got {self.n_epochs}")


@dataclass
class TrainingHistory:
    """Records training metrics per epoch."""

    losses: list[float] = field(default_factory=list)
    metrics: dict[str, list[float]] = field(default_factory=dict)

    def add_epoch(self, loss: float = 0.0, **kwargs: float):
        self.losses.append(loss)
        for key, value in kwargs.items():
            self.metrics.setdefault(key, []).append(value)

    @property
    def best_loss(self) -> float:
        return min(self.losses) if self.losses else float("inf")


class BaseFHEModel:
    """Abstract base for FHE-compatible models."""

    fhe_level: FHELevel = FHELevel.NONE

    def __init__(
        self,
        config: Optional[ModelConfig] = None,
        encryptor: Optional[CKKSEncryptor] = None,
    ):
        self._config = config or ModelConfig()
        self._encryptor = encryptor
        self._state = ModelState.INITIALIZED
        self._history = TrainingHistory()
        self._weights = None
        self._bias = None

    @property
    def is_fitted(self) -> bool:
        return self._state == ModelState.TRAINED

    @property
    def weights(self) -> Optional[np.ndarray]:
        return self._weights

    @property
    def bias(self) -> Optional[float]:
        return self._bias

    def _ensure_encryptor(self, X) -> CKKSEncryptor:
        """Get encryptor from model or from data."""
        if self._encryptor is not None:
            return self._encryptor
        if isinstance(X, EncryptedMatrix) and X.encryptor is not None:
            return X.encryptor
        raise ValueError("No encryptor available. Pass encryptor to model or data loader.")

    def fit(self, X, y=None):
        raise NotImplementedError

    def predict(self, X):
        raise NotImplementedError

"""Base model for FHE-ML models."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import numpy as np

from ..encryption.ckks_wrapper import CKKSEncryptor, EncryptedMatrix, EncryptedVector


class FHELevel(Enum):
    """Level of FHE support."""
    NONE = "none"
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


@dataclass
class TrainingHistory:
    """Records training metrics per epoch."""
    losses: list[float] = field(default_factory=list)

    def add_epoch(self, loss: float):
        self.losses.append(loss)

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

"""Differential Privacy module for the Xcapit FHE-ML SDK.

Provides production-grade differential privacy primitives including noise
mechanisms, privacy budget accounting, data privatization, and DP-SGD
training utilities.

Modules:
    mechanisms: Core DP mechanisms (Laplace, Gaussian, Exponential).
    accountant: Privacy budget tracking with composition theorems and RDP.
    dp_data_loader: Privacy-preserving data loading with optional FHE.
    dp_training: DP-SGD for private model training.

Example:
    >>> from sdk.privacy import GaussianMechanism, PrivacyAccountant
    >>> mechanism = GaussianMechanism(epsilon=1.0, delta=1e-5)
    >>> accountant = PrivacyAccountant(total_epsilon=10.0)
    >>> accountant.step(mechanism)
    True
"""

from __future__ import annotations

from .accountant import PrivacyAccountant, PrivacyBudget
from .dp_data_loader import DPDataLoader, PrivateDataset, SubsampledMechanism
from .dp_training import (
    DPSGDConfig,
    DPSGDTrainer,
    DPTrainer,
    DPTrainingConfig,
    GradientClipper,
)
from .mechanisms import (
    DPMechanism,
    ExponentialMechanism,
    GaussianMechanism,
    LaplaceMechanism,
    NoiseCalibrator,
)

__all__: list[str] = [
    # Mechanisms
    "DPMechanism",
    "LaplaceMechanism",
    "GaussianMechanism",
    "ExponentialMechanism",
    "NoiseCalibrator",
    # Accountant
    "PrivacyBudget",
    "PrivacyAccountant",
    # Data loader
    "DPDataLoader",
    "PrivateDataset",
    "SubsampledMechanism",
    # Training
    "DPTrainer",
    "DPTrainingConfig",
    "GradientClipper",
    "DPSGDConfig",
    "DPSGDTrainer",
]

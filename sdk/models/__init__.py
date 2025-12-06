"""FHE-compatible ML models.

This module provides machine learning models that can be trained
and used for inference on encrypted data.
"""

from .base import (
    BaseFHEModel,
    FHEModel,
    ModelConfig,
    ModelState,
    TrainingHistory,
)
from .linear_regression import LinearRegression
from .logistic_regression import LogisticRegression, SigmoidApproximation

__all__ = [
    "BaseFHEModel",
    "FHEModel",
    "LinearRegression",
    "LogisticRegression",
    "ModelConfig",
    "ModelState",
    "SigmoidApproximation",
    "TrainingHistory",
]

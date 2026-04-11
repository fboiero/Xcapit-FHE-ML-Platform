"""Evaluation module for FHE-ML models.

Provides metrics, cross-validation, hyperparameter tuning,
model interpretation, and specialised FHE/privacy/fairness metrics.
"""

from .advanced_metrics import FairnessMetrics, FHEMetrics, PrivacyMetrics
from .cross_validation import CrossValidator
from .hyperparameter_tuning import GridSearchCV, RandomSearchCV
from .interpretation import ModelInterpreter
from .metrics import (
    ClassificationMetrics,
    ClusteringMetrics,
    MetricCalculator,
    MetricType,
    RegressionMetrics,
)

__all__ = [
    "MetricType",
    "RegressionMetrics",
    "ClassificationMetrics",
    "ClusteringMetrics",
    "MetricCalculator",
    "CrossValidator",
    "GridSearchCV",
    "RandomSearchCV",
    "ModelInterpreter",
    "PrivacyMetrics",
    "FairnessMetrics",
    "FHEMetrics",
]

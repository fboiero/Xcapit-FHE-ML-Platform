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
from .decision_tree import (
    DecisionTree,
    DecisionTreeClassifier,
    DecisionTreeRegressor,
    SplitFunction,
    TreeConfig,
    TreeType,
)
from .kmeans import (
    InitMethod,
    KMeans,
    KMeansConfig,
    MiniBatchKMeans,
)
from .linear_regression import LinearRegression
from .logistic_regression import LogisticRegression, SigmoidApproximation

__all__ = [
    # Base
    "BaseFHEModel",
    "FHEModel",
    "ModelConfig",
    "ModelState",
    "TrainingHistory",
    # Linear models
    "LinearRegression",
    "LogisticRegression",
    "SigmoidApproximation",
    # Decision trees
    "DecisionTree",
    "DecisionTreeClassifier",
    "DecisionTreeRegressor",
    "TreeConfig",
    "TreeType",
    "SplitFunction",
    # Clustering
    "KMeans",
    "MiniBatchKMeans",
    "KMeansConfig",
    "InitMethod",
]

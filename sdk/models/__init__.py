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
from .random_forest import (
    AggregationMethod,
    RandomForest,
    RandomForestClassifier,
    RandomForestConfig,
    RandomForestRegressor,
)
from .neural_network import (
    Activation,
    ActivationFunctions,
    LayerConfig,
    NeuralNetwork,
    NeuralNetworkClassifier,
    NeuralNetworkConfig,
    NeuralNetworkRegressor,
    WeightInit,
)
from .gradient_boosting import (
    GradientBoosting,
    GradientBoostingClassifier,
    GradientBoostingConfig,
    GradientBoostingRegressor,
    LossFunction,
    LossFunctions,
)
from .svm import (
    KernelType,
    SVM,
    SVMClassifier,
    SVMConfig,
    SVMRegressor,
)
from .naive_bayes import (
    BernoulliNaiveBayes,
    GaussianNaiveBayes,
    MultinomialNaiveBayes,
    NaiveBayesConfig,
)
from .pca import (
    PCA,
    PCAConfig,
)
from .ensemble import (
    StackingClassifier,
    VotingClassifier,
    VotingRegressor,
    VotingType,
)

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
    # Random Forest
    "RandomForest",
    "RandomForestClassifier",
    "RandomForestRegressor",
    "RandomForestConfig",
    "AggregationMethod",
    # Neural Network
    "NeuralNetwork",
    "NeuralNetworkClassifier",
    "NeuralNetworkRegressor",
    "NeuralNetworkConfig",
    "LayerConfig",
    "Activation",
    "ActivationFunctions",
    "WeightInit",
    # Gradient Boosting
    "GradientBoosting",
    "GradientBoostingClassifier",
    "GradientBoostingRegressor",
    "GradientBoostingConfig",
    "LossFunction",
    "LossFunctions",
    # Clustering
    "KMeans",
    "MiniBatchKMeans",
    "KMeansConfig",
    "InitMethod",
    # SVM
    "SVM",
    "SVMClassifier",
    "SVMRegressor",
    "SVMConfig",
    "KernelType",
    # Naive Bayes
    "GaussianNaiveBayes",
    "MultinomialNaiveBayes",
    "BernoulliNaiveBayes",
    "NaiveBayesConfig",
    # PCA
    "PCA",
    "PCAConfig",
    # Ensemble
    "VotingClassifier",
    "VotingRegressor",
    "StackingClassifier",
    "VotingType",
]

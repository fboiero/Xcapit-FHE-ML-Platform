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
from .anomaly_detection import (
    AnomalyConfig,
    AnomalyMethod,
    EllipticEnvelope,
    EllipticEnvelopeConfig,
    IsolationForest,
    IsolationForestConfig,
    LocalOutlierFactor,
    LOFConfig,
    OneClassSVM,
    OneClassSVMConfig,
)
from .time_series import (
    ARIMA,
    ARIMAConfig,
    ExponentialSmoothing,
    ExponentialSmoothingConfig,
    ProphetConfig,
    ProphetLike,
    SeasonalityMode,
    SimpleMovingAverage,
    TrendMode,
)
from .regularization import (
    ElasticNet,
    ElasticNetConfig,
    Lasso,
    LassoConfig,
    RegularizationType,
    Ridge,
    RidgeClassifier,
    RidgeConfig,
    SGDRegressor,
)
from .feature_selection import (
    RFE,
    RFEConfig,
    ScoreFunc,
    SelectFromModel,
    SelectKBest,
    SelectKBestConfig,
    SelectPercentile,
    VarianceThreshold,
    VarianceThresholdConfig,
    chi2,
    f_classif,
    f_regression,
    mutual_info_classif,
    mutual_info_regression,
)
from .deep_learning import (
    MLPClassifier,
    MLPRegressor,
    Autoencoder,
    VariationalAutoencoder,
    PolynomialActivations,
)
from .clustering import (
    DBSCAN,
    AgglomerativeClustering,
    SpectralClustering,
    MeanShift,
    GaussianMixture,
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
    # Anomaly Detection
    "IsolationForest",
    "IsolationForestConfig",
    "OneClassSVM",
    "OneClassSVMConfig",
    "LocalOutlierFactor",
    "LOFConfig",
    "EllipticEnvelope",
    "EllipticEnvelopeConfig",
    "AnomalyMethod",
    "AnomalyConfig",
    # Time Series
    "ARIMA",
    "ARIMAConfig",
    "ExponentialSmoothing",
    "ExponentialSmoothingConfig",
    "SimpleMovingAverage",
    "ProphetLike",
    "ProphetConfig",
    "SeasonalityMode",
    "TrendMode",
    # Regularization
    "Ridge",
    "RidgeConfig",
    "Lasso",
    "LassoConfig",
    "ElasticNet",
    "ElasticNetConfig",
    "RidgeClassifier",
    "SGDRegressor",
    "RegularizationType",
    # Feature Selection
    "VarianceThreshold",
    "VarianceThresholdConfig",
    "SelectKBest",
    "SelectKBestConfig",
    "SelectPercentile",
    "RFE",
    "RFEConfig",
    "SelectFromModel",
    "ScoreFunc",
    "f_classif",
    "f_regression",
    "chi2",
    "mutual_info_classif",
    "mutual_info_regression",
    # Deep Learning
    "MLPClassifier",
    "MLPRegressor",
    "Autoencoder",
    "VariationalAutoencoder",
    "PolynomialActivations",
    # Advanced Clustering
    "DBSCAN",
    "AgglomerativeClustering",
    "SpectralClustering",
    "MeanShift",
    "GaussianMixture",
]

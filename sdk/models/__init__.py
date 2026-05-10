"""FHE-ML models — privacy-preserving machine learning.

Quick start::

    from sdk.models import LinearRegression, FHELevel

    model = LinearRegression()
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    print(model.fhe_level)  # FHELevel.FULL

All models follow the scikit-learn fit/predict interface and declare an
``fhe_level`` indicating their encryption support:

- ``FHELevel.FULL``: inference on encrypted data (LinearRegression).
- ``FHELevel.PARTIAL``: some paths encrypted (LogisticRegression).
- ``FHELevel.TRANSPORT``: data encrypted in transit, decrypted for compute.
- ``FHELevel.NONE``: no encryption.
"""

# Base classes and enums
from .anomaly_detection import EllipticEnvelope, IsolationForest, LocalOutlierFactor, OneClassSVM
from .base import BaseFHEModel, FHELevel, ModelConfig, ModelState, TrainingHistory
from .calibration import CalibratedClassifierCV, IsotonicRegression, TemperatureScaling
from .clustering import (
    DBSCAN,
    AgglomerativeClustering,
    GaussianMixture,
    MeanShift,
    SpectralClustering,
)
from .decision_tree import DecisionTree, DecisionTreeClassifier, DecisionTreeRegressor
from .deep_learning import Autoencoder, MLPClassifier, MLPRegressor, VariationalAutoencoder
from .ensemble import StackingClassifier, VotingClassifier, VotingRegressor
from .feature_selection import (
    RFE,
    SelectFromModel,
    SelectKBest,
    SelectPercentile,
    VarianceThreshold,
)
from .gradient_boosting import (
    GradientBoosting,
    GradientBoostingClassifier,
    GradientBoostingRegressor,
)
from .kmeans import KMeans, MiniBatchKMeans

# --- Core models (ordered by FHE support level) ---
# FHE FULL — genuine encrypted inference
from .linear_regression import LinearRegression

# FHE PARTIAL — partial encrypted paths
from .logistic_regression import LogisticRegression
from .multioutput import (
    ClassifierChain,
    MultiOutputClassifier,
    MultiOutputRegressor,
    RegressorChain,
)
from .naive_bayes import BernoulliNaiveBayes, GaussianNaiveBayes, MultinomialNaiveBayes

# FHE TRANSPORT — encrypted in transit, plaintext compute
from .neural_network import NeuralNetwork, NeuralNetworkClassifier, NeuralNetworkRegressor

# FHE NONE — standard ML (no encryption)
from .pca import PCA
from .random_forest import RandomForest, RandomForestClassifier, RandomForestRegressor
from .regularization import ElasticNet, Lasso, Ridge, RidgeClassifier, SGDRegressor
from .svm import SVM, SVMClassifier, SVMRegressor
from .time_series import ARIMA, ExponentialSmoothing, ProphetLike, SimpleMovingAverage

__all__ = [
    # Base
    "BaseFHEModel",
    "FHELevel",
    "ModelConfig",
    "ModelState",
    "TrainingHistory",
    # Core models
    "LinearRegression",
    "LogisticRegression",
    "NeuralNetwork",
    "NeuralNetworkClassifier",
    "NeuralNetworkRegressor",
    "SVM",
    "SVMClassifier",
    "SVMRegressor",
    "KMeans",
    "MiniBatchKMeans",
    "DecisionTree",
    "DecisionTreeClassifier",
    "DecisionTreeRegressor",
    "RandomForest",
    "RandomForestClassifier",
    "RandomForestRegressor",
    "GradientBoosting",
    "GradientBoostingClassifier",
    "GradientBoostingRegressor",
    "PCA",
    "GaussianNaiveBayes",
    "MultinomialNaiveBayes",
    "BernoulliNaiveBayes",
    "IsolationForest",
    "OneClassSVM",
    "LocalOutlierFactor",
    "EllipticEnvelope",
    "ARIMA",
    "ExponentialSmoothing",
    "ProphetLike",
    "SimpleMovingAverage",
    "Ridge",
    "Lasso",
    "ElasticNet",
    "RidgeClassifier",
    "SGDRegressor",
    "DBSCAN",
    "AgglomerativeClustering",
    "MeanShift",
    "SpectralClustering",
    "GaussianMixture",
    "VotingClassifier",
    "VotingRegressor",
    "StackingClassifier",
    "MultiOutputClassifier",
    "MultiOutputRegressor",
    "ClassifierChain",
    "RegressorChain",
    "CalibratedClassifierCV",
    "IsotonicRegression",
    "TemperatureScaling",
    "SelectKBest",
    "SelectFromModel",
    "RFE",
    "VarianceThreshold",
    "SelectPercentile",
    "MLPClassifier",
    "MLPRegressor",
    "Autoencoder",
    "VariationalAutoencoder",
]

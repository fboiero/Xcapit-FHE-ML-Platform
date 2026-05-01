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
from .base import BaseFHEModel, FHELevel, ModelConfig, ModelState, TrainingHistory

# --- Core models (ordered by FHE support level) ---

# FHE FULL — genuine encrypted inference
from .linear_regression import LinearRegression

# FHE PARTIAL — partial encrypted paths
from .logistic_regression import LogisticRegression

# FHE TRANSPORT — encrypted in transit, plaintext compute
from .neural_network import NeuralNetwork, NeuralNetworkClassifier, NeuralNetworkRegressor
from .svm import SVM, SVMClassifier, SVMRegressor
from .kmeans import KMeans, MiniBatchKMeans
from .decision_tree import DecisionTree, DecisionTreeClassifier, DecisionTreeRegressor
from .random_forest import RandomForest, RandomForestClassifier, RandomForestRegressor
from .gradient_boosting import GradientBoosting, GradientBoostingClassifier, GradientBoostingRegressor

# FHE NONE — standard ML (no encryption)
from .pca import PCA
from .naive_bayes import GaussianNaiveBayes, MultinomialNaiveBayes, BernoulliNaiveBayes
from .anomaly_detection import IsolationForest, OneClassSVM, LocalOutlierFactor, EllipticEnvelope
from .time_series import ARIMA, ExponentialSmoothing, ProphetLike, SimpleMovingAverage
from .regularization import Ridge, Lasso, ElasticNet, RidgeClassifier, SGDRegressor
from .clustering import DBSCAN, AgglomerativeClustering, MeanShift, SpectralClustering, GaussianMixture
from .ensemble import VotingClassifier, VotingRegressor, StackingClassifier
from .multioutput import MultiOutputClassifier, MultiOutputRegressor, ClassifierChain, RegressorChain
from .calibration import CalibratedClassifierCV, IsotonicRegression, TemperatureScaling
from .feature_selection import SelectKBest, SelectFromModel, RFE, VarianceThreshold, SelectPercentile
from .deep_learning import MLPClassifier, MLPRegressor, Autoencoder, VariationalAutoencoder

__all__ = [
    # Base
    "BaseFHEModel", "FHELevel", "ModelConfig", "ModelState", "TrainingHistory",
    # Core models
    "LinearRegression", "LogisticRegression",
    "NeuralNetwork", "NeuralNetworkClassifier", "NeuralNetworkRegressor",
    "SVM", "SVMClassifier", "SVMRegressor",
    "KMeans", "MiniBatchKMeans",
    "DecisionTree", "DecisionTreeClassifier", "DecisionTreeRegressor",
    "RandomForest", "RandomForestClassifier", "RandomForestRegressor",
    "GradientBoosting", "GradientBoostingClassifier", "GradientBoostingRegressor",
    "PCA",
    "GaussianNaiveBayes", "MultinomialNaiveBayes", "BernoulliNaiveBayes",
    "IsolationForest", "OneClassSVM", "LocalOutlierFactor", "EllipticEnvelope",
    "ARIMA", "ExponentialSmoothing", "ProphetLike", "SimpleMovingAverage",
    "Ridge", "Lasso", "ElasticNet", "RidgeClassifier", "SGDRegressor",
    "DBSCAN", "AgglomerativeClustering", "MeanShift", "SpectralClustering", "GaussianMixture",
    "VotingClassifier", "VotingRegressor", "StackingClassifier",
    "MultiOutputClassifier", "MultiOutputRegressor", "ClassifierChain", "RegressorChain",
    "CalibratedClassifierCV", "IsotonicRegression", "TemperatureScaling",
    "SelectKBest", "SelectFromModel", "RFE", "VarianceThreshold", "SelectPercentile",
    "MLPClassifier", "MLPRegressor", "Autoencoder", "VariationalAutoencoder",
]

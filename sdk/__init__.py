"""Xcapit FHE-ML SDK - Privacy-preserving machine learning.

This SDK provides tools for training machine learning models
on encrypted data using Fully Homomorphic Encryption (FHE).

Example:
    >>> from xcapit_fhe import SecureDataLoader
    >>> loader = SecureDataLoader()
    >>> encrypted_data = loader.encrypt(df)
"""

from .blockchain import (
    NETWORK_CONFIGS,
    BlockchainConnector,
    ModelRegistryClient,
    Network,
    NetworkConfig,
)
from .encryption import (
    CKKSEncryptor,
    CKKSParameters,
    EncryptedMatrix,
    EncryptedVector,
    FHEContextManager,
    SecurityLevel,
)
from .models import (
    BaseFHEModel,
    # Decision Trees
    DecisionTree,
    DecisionTreeClassifier,
    DecisionTreeRegressor,
    FHEModel,
    InitMethod,
    # Clustering
    KMeans,
    KMeansConfig,
    LinearRegression,
    LogisticRegression,
    MiniBatchKMeans,
    ModelConfig,
    ModelState,
    SigmoidApproximation,
    SplitFunction,
    TreeConfig,
    TreeType,
    # Random Forest
    AggregationMethod,
    RandomForest,
    RandomForestClassifier,
    RandomForestConfig,
    RandomForestRegressor,
    # Neural Network
    Activation,
    ActivationFunctions,
    LayerConfig,
    NeuralNetwork,
    NeuralNetworkClassifier,
    NeuralNetworkConfig,
    NeuralNetworkRegressor,
    WeightInit,
    # Gradient Boosting
    GradientBoosting,
    GradientBoostingClassifier,
    GradientBoostingConfig,
    GradientBoostingRegressor,
    LossFunction,
    LossFunctions,
)
from .utils import (
    EncryptedDataset,
    SecureDataLoader,
    ValidationError,
    check_fhe_compatibility,
)
from .preprocessing import (
    # Pipeline
    PreprocessingPipeline,
    create_standard_pipeline,
    create_categorical_pipeline,
    # Scalers
    StandardScaler,
    MinMaxScaler,
    RobustScaler,
    # Encoders
    OneHotEncoder,
    OrdinalEncoder,
    # Handlers
    MissingValueHandler,
    OutlierHandler,
    FeatureSelector,
)

__version__ = "0.2.0"

__all__ = [
    # Encryption
    "CKKSEncryptor",
    "CKKSParameters",
    "EncryptedMatrix",
    "EncryptedVector",
    "FHEContextManager",
    "SecurityLevel",
    # Utils
    "EncryptedDataset",
    "SecureDataLoader",
    "ValidationError",
    "check_fhe_compatibility",
    # Models - Base
    "BaseFHEModel",
    "FHEModel",
    "ModelConfig",
    "ModelState",
    # Models - Linear
    "LinearRegression",
    "LogisticRegression",
    "SigmoidApproximation",
    # Models - Decision Trees
    "DecisionTree",
    "DecisionTreeClassifier",
    "DecisionTreeRegressor",
    "TreeConfig",
    "TreeType",
    "SplitFunction",
    # Models - Random Forest
    "RandomForest",
    "RandomForestClassifier",
    "RandomForestRegressor",
    "RandomForestConfig",
    "AggregationMethod",
    # Models - Neural Network
    "NeuralNetwork",
    "NeuralNetworkClassifier",
    "NeuralNetworkRegressor",
    "NeuralNetworkConfig",
    "LayerConfig",
    "Activation",
    "ActivationFunctions",
    "WeightInit",
    # Models - Gradient Boosting
    "GradientBoosting",
    "GradientBoostingClassifier",
    "GradientBoostingRegressor",
    "GradientBoostingConfig",
    "LossFunction",
    "LossFunctions",
    # Models - Clustering
    "KMeans",
    "MiniBatchKMeans",
    "KMeansConfig",
    "InitMethod",
    # Blockchain
    "BlockchainConnector",
    "ModelRegistryClient",
    "NetworkConfig",
    "Network",
    "NETWORK_CONFIGS",
    # Preprocessing
    "PreprocessingPipeline",
    "create_standard_pipeline",
    "create_categorical_pipeline",
    "StandardScaler",
    "MinMaxScaler",
    "RobustScaler",
    "OneHotEncoder",
    "OrdinalEncoder",
    "MissingValueHandler",
    "OutlierHandler",
    "FeatureSelector",
    # Version
    "__version__",
]

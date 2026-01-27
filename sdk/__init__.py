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
    # SVM
    KernelType,
    SVM,
    SVMClassifier,
    SVMConfig,
    SVMRegressor,
    # Naive Bayes
    BernoulliNaiveBayes,
    GaussianNaiveBayes,
    MultinomialNaiveBayes,
    NaiveBayesConfig,
    # PCA
    PCA,
    PCAConfig,
    # Ensemble
    StackingClassifier,
    VotingClassifier,
    VotingRegressor,
    VotingType,
    # Anomaly Detection
    IsolationForest,
    IsolationForestConfig,
    OneClassSVM,
    OneClassSVMConfig,
    LocalOutlierFactor,
    LOFConfig,
    EllipticEnvelope,
    EllipticEnvelopeConfig,
    AnomalyMethod,
    # Time Series
    ARIMA,
    ARIMAConfig,
    ExponentialSmoothing,
    ExponentialSmoothingConfig,
    SimpleMovingAverage,
    ProphetLike,
    ProphetConfig,
    SeasonalityMode,
    TrendMode,
    # Regularization
    Ridge,
    RidgeConfig,
    Lasso,
    LassoConfig,
    ElasticNet,
    ElasticNetConfig,
    RidgeClassifier,
    SGDRegressor,
    # Feature Selection
    VarianceThreshold,
    SelectKBest,
    SelectPercentile,
    RFE,
    SelectFromModel,
    f_classif,
    f_regression,
    chi2,
    mutual_info_classif,
    mutual_info_regression,
)
from .utils import (
    EncryptedDataset,
    SecureDataLoader,
    ValidationError,
    check_fhe_compatibility,
)
from .evaluation import (
    # Metrics
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
    mean_squared_error,
    mean_absolute_error,
    r2_score,
    root_mean_squared_error,
    # Cross-validation
    cross_val_score,
    cross_val_predict,
    cross_validate,
    learning_curve,
    KFold,
    StratifiedKFold,
    LeaveOneOut,
    TimeSeriesSplit,
    GroupKFold,
    RepeatedKFold,
    train_test_split,
    GridSearchCV,
    # Hyperparameter tuning
    RandomizedSearchCV,
    BayesianOptimization,
    HalvingRandomSearchCV,
    # Model interpretation
    PermutationImportance,
    SHAPApproximation,
    PartialDependence,
    IndividualConditionalExpectation,
    FeatureInteraction,
    explain_prediction,
)
from .persistence import (
    save_model,
    load_model,
    ModelSerializer,
    ModelFormat,
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

__version__ = "0.4.0"

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
    # Models - SVM
    "SVM",
    "SVMClassifier",
    "SVMRegressor",
    "SVMConfig",
    "KernelType",
    # Models - Naive Bayes
    "GaussianNaiveBayes",
    "MultinomialNaiveBayes",
    "BernoulliNaiveBayes",
    "NaiveBayesConfig",
    # Models - PCA
    "PCA",
    "PCAConfig",
    # Models - Ensemble
    "VotingClassifier",
    "VotingRegressor",
    "StackingClassifier",
    "VotingType",
    # Models - Anomaly Detection
    "IsolationForest",
    "IsolationForestConfig",
    "OneClassSVM",
    "OneClassSVMConfig",
    "LocalOutlierFactor",
    "LOFConfig",
    "EllipticEnvelope",
    "EllipticEnvelopeConfig",
    "AnomalyMethod",
    # Models - Time Series
    "ARIMA",
    "ARIMAConfig",
    "ExponentialSmoothing",
    "ExponentialSmoothingConfig",
    "SimpleMovingAverage",
    "ProphetLike",
    "ProphetConfig",
    "SeasonalityMode",
    "TrendMode",
    # Models - Regularization
    "Ridge",
    "RidgeConfig",
    "Lasso",
    "LassoConfig",
    "ElasticNet",
    "ElasticNetConfig",
    "RidgeClassifier",
    "SGDRegressor",
    # Models - Feature Selection
    "VarianceThreshold",
    "SelectKBest",
    "SelectPercentile",
    "RFE",
    "SelectFromModel",
    "f_classif",
    "f_regression",
    "chi2",
    "mutual_info_classif",
    "mutual_info_regression",
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
    # Evaluation - Metrics
    "accuracy_score",
    "precision_score",
    "recall_score",
    "f1_score",
    "roc_auc_score",
    "confusion_matrix",
    "classification_report",
    "mean_squared_error",
    "mean_absolute_error",
    "r2_score",
    "root_mean_squared_error",
    # Evaluation - Cross-validation
    "cross_val_score",
    "cross_val_predict",
    "cross_validate",
    "learning_curve",
    "KFold",
    "StratifiedKFold",
    "LeaveOneOut",
    "TimeSeriesSplit",
    "GroupKFold",
    "RepeatedKFold",
    "train_test_split",
    "GridSearchCV",
    # Evaluation - Hyperparameter Tuning
    "RandomizedSearchCV",
    "BayesianOptimization",
    "HalvingRandomSearchCV",
    # Evaluation - Model Interpretation
    "PermutationImportance",
    "SHAPApproximation",
    "PartialDependence",
    "IndividualConditionalExpectation",
    "FeatureInteraction",
    "explain_prediction",
    # Persistence
    "save_model",
    "load_model",
    "ModelSerializer",
    "ModelFormat",
    # Version
    "__version__",
]

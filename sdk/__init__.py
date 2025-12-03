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
from .ensemble import (
    AdaBoostClassifier,
    BaggingClassifier,
    BaggingRegressor,
    StackingRegressor,
    get_ensemble_feature_importances,
)
from .ensemble import (
    StackingClassifier as StackingClassifierNew,  # noqa: F401
)
from .ensemble import (
    VotingClassifier as VotingClassifierNew,  # noqa: F401
)
from .ensemble import (
    VotingRegressor as VotingRegressorNew,  # noqa: F401
)
from .evaluation import (
    BayesianOptimization,
    FeatureInteraction,
    GridSearchCV,
    GroupKFold,
    HalvingRandomSearchCV,
    IndividualConditionalExpectation,
    KFold,
    LeaveOneOut,
    PartialDependence,
    # Model interpretation
    PermutationImportance,
    # Hyperparameter tuning
    RandomizedSearchCV,
    RepeatedKFold,
    SHAPApproximation,
    StratifiedKFold,
    TimeSeriesSplit,
    # Metrics
    accuracy_score,
    adjusted_rand_score,
    balanced_accuracy_score,
    brier_score_loss,
    calinski_harabasz_score,
    classification_report,
    cohen_kappa_score,
    confusion_matrix,
    cross_val_predict,
    # Cross-validation
    cross_val_score,
    cross_validate,
    davies_bouldin_score,
    explain_prediction,
    f1_score,
    learning_curve,
    # Advanced metrics
    matthews_corrcoef,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
    root_mean_squared_error,
    silhouette_score,
    train_test_split,
)
from .feature_engineering import (
    Binarizer,
    FunctionTransformer,
    InteractionFeatures,
    KBinsDiscretizer,
    PolynomialFeatures,
    PowerTransformer,
    QuantileTransformer,
    TargetEncoder,
)
from .feature_engineering import (
    OneHotEncoder as OneHotEncoderNew,  # noqa: F401
)
from .feature_engineering import (
    OrdinalEncoder as OrdinalEncoderNew,  # noqa: F401
)
from .feature_selection import (
    RFE as RFENew,  # noqa: F401
)
from .feature_selection import (
    RFECV,
)
from .feature_selection import (
    SelectFromModel as SelectFromModelNew,  # noqa: F401
)
from .feature_selection import (
    SelectKBest as SelectKBestNew,  # noqa: F401
)
from .feature_selection import (
    SelectPercentile as SelectPercentileNew,  # noqa: F401
)
from .feature_selection import (
    VarianceThreshold as VarianceThresholdNew,  # noqa: F401
)
from .feature_selection import (
    f_classif as f_classif_new,  # noqa: F401
)
from .feature_selection import (
    f_regression as f_regression_new,  # noqa: F401
)
from .feature_selection import (
    mutual_info_classif as mutual_info_classif_new,  # noqa: F401
)
from .impute import (
    IterativeImputer,
    KNNImputer,
    MissingIndicator,
    SimpleImputer,
)
from .model_selection import (
    GridSearchCV as GridSearchCVNew,  # noqa: F401
)
from .model_selection import (
    KFold as KFoldNew,  # noqa: F401
)
from .model_selection import (
    LeaveOneOut as LeaveOneOutNew,  # noqa: F401
)
from .model_selection import (
    ParameterGrid,
    ParameterSampler,
    ShuffleSplit,
)
from .model_selection import (
    RandomizedSearchCV as RandomizedSearchCVNew,  # noqa: F401
)
from .model_selection import (
    StratifiedKFold as StratifiedKFoldNew,  # noqa: F401
)
from .model_selection import (
    cross_val_score as cross_val_score_new,  # noqa: F401
)
from .model_selection import (
    cross_validate as cross_validate_new,  # noqa: F401
)
from .model_selection import (
    train_test_split as train_test_split_new,  # noqa: F401
)
from .models import (
    # Time Series
    ARIMA,
    # PCA
    PCA,
    RFE,
    SVM,
    # Neural Network
    Activation,
    ActivationFunctions,
    # Random Forest
    AggregationMethod,
    AnomalyMethod,
    ARIMAConfig,
    BaseFHEModel,
    # Naive Bayes
    BernoulliNaiveBayes,
    CalibratedClassifierCV,
    # Calibration
    CalibrationConfig,
    CalibrationMethod,
    ClassifierChain,
    # Decision Trees
    DecisionTree,
    DecisionTreeClassifier,
    DecisionTreeRegressor,
    ElasticNet,
    ElasticNetConfig,
    EllipticEnvelope,
    EllipticEnvelopeConfig,
    ExponentialSmoothing,
    ExponentialSmoothingConfig,
    FHEModel,
    GaussianNaiveBayes,
    # Gradient Boosting
    GradientBoosting,
    GradientBoostingClassifier,
    GradientBoostingConfig,
    GradientBoostingRegressor,
    InitMethod,
    # Anomaly Detection
    IsolationForest,
    IsolationForestConfig,
    IsotonicRegression,
    # SVM
    KernelType,
    # Clustering
    KMeans,
    KMeansConfig,
    Lasso,
    LassoConfig,
    LayerConfig,
    LinearRegression,
    LocalOutlierFactor,
    LOFConfig,
    LogisticRegression,
    LossFunction,
    LossFunctions,
    MiniBatchKMeans,
    ModelConfig,
    ModelState,
    MultiLabelBinarizer,
    MultinomialNaiveBayes,
    # Multi-output
    MultiOutputClassifier,
    MultiOutputRegressor,
    NaiveBayesConfig,
    NeuralNetwork,
    NeuralNetworkClassifier,
    NeuralNetworkConfig,
    NeuralNetworkRegressor,
    OneClassSVM,
    OneClassSVMConfig,
    PCAConfig,
    ProphetConfig,
    ProphetLike,
    RandomForest,
    RandomForestClassifier,
    RandomForestConfig,
    RandomForestRegressor,
    RegressorChain,
    # Regularization
    Ridge,
    RidgeClassifier,
    RidgeConfig,
    SeasonalityMode,
    SelectFromModel,
    SelectKBest,
    SelectPercentile,
    SGDRegressor,
    SigmoidApproximation,
    SigmoidCalibration,
    SimpleMovingAverage,
    SplitFunction,
    # Ensemble
    StackingClassifier,
    SVMClassifier,
    SVMConfig,
    SVMRegressor,
    TemperatureScaling,
    TreeConfig,
    TreeType,
    TrendMode,
    # Feature Selection
    VarianceThreshold,
    VotingClassifier,
    VotingRegressor,
    VotingType,
    WeightInit,
    calibration_curve,
    chi2,
    f_classif,
    f_regression,
    mutual_info_classif,
    mutual_info_regression,
)
from .outlier import (
    EllipticEnvelope as EllipticEnvelopeNew,  # noqa: F401
)
from .outlier import (
    IsolationForest as IsolationForestNew,  # noqa: F401
)
from .outlier import (
    LocalOutlierFactor as LocalOutlierFactorNew,  # noqa: F401
)
from .outlier import (
    OneClassSVM as OneClassSVMNew,  # noqa: F401
)
from .outlier import (
    detect_outliers_dbscan,
    detect_outliers_iqr,
    detect_outliers_mad,
    detect_outliers_zscore,
    get_outlier_scores,
)
from .persistence import (
    ModelFormat,
    ModelSerializer,
    load_model,
    save_model,
)
from .pipeline import (
    ColumnTransformer,
    FeatureUnion,
    Pipeline,
    TransformedTargetRegressor,
    make_pipeline,
    make_union,
)
from .preprocessing import (
    MinMaxScaler,
    # Encoders
    OneHotEncoder,
    OrdinalEncoder,
    RobustScaler,
    # Scalers
    StandardScaler,
)
from .utils import (
    EncryptedDataset,
    SecureDataLoader,
    ValidationError,
    check_fhe_compatibility,
)
from .validation import (
    ColumnSchema,
    CustomConstraint,
    DataSchema,
    # Validators
    DatasetValidator,
    InRange,
    InSet,
    IsEmail,
    IsPositive,
    IsType,
    IsURL,
    MatchesRegex,
    MaxLength,
    MinLength,
    NotEmpty,
    # Constraints
    NotNull,
    ValidationResult,
    infer_schema,
    validate_features,
    validate_labels,
    validate_sample_weights,
)
from .validation import (
    ValidationError as DataValidationError,
)

__version__ = "0.7.0"

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
    "StandardScaler",
    "MinMaxScaler",
    "RobustScaler",
    "OneHotEncoder",
    "OrdinalEncoder",
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
    # Pipeline
    "Pipeline",
    "FeatureUnion",
    "ColumnTransformer",
    "make_pipeline",
    "make_union",
    "TransformedTargetRegressor",
    # Calibration
    "CalibrationConfig",
    "CalibrationMethod",
    "IsotonicRegression",
    "SigmoidCalibration",
    "TemperatureScaling",
    "CalibratedClassifierCV",
    "calibration_curve",
    # Multi-output
    "MultiOutputClassifier",
    "MultiOutputRegressor",
    "ClassifierChain",
    "RegressorChain",
    "MultiLabelBinarizer",
    # Advanced metrics
    "matthews_corrcoef",
    "cohen_kappa_score",
    "brier_score_loss",
    "balanced_accuracy_score",
    "silhouette_score",
    "calinski_harabasz_score",
    "davies_bouldin_score",
    "adjusted_rand_score",
    # Feature Selection (new)
    "RFECV",
    # Model Selection (new)
    "ShuffleSplit",
    "ParameterGrid",
    "ParameterSampler",
    # Imputers
    "SimpleImputer",
    "KNNImputer",
    "IterativeImputer",
    "MissingIndicator",
    # Ensemble (new)
    "StackingRegressor",
    "BaggingClassifier",
    "BaggingRegressor",
    "AdaBoostClassifier",
    "get_ensemble_feature_importances",
    # Outlier detection (new)
    "detect_outliers_zscore",
    "detect_outliers_iqr",
    "detect_outliers_mad",
    "detect_outliers_dbscan",
    "get_outlier_scores",
    # Validation (new)
    "DataSchema",
    "ColumnSchema",
    "ValidationResult",
    "DataValidationError",
    "NotNull",
    "NotEmpty",
    "InRange",
    "InSet",
    "MatchesRegex",
    "MinLength",
    "MaxLength",
    "IsType",
    "IsPositive",
    "IsEmail",
    "IsURL",
    "CustomConstraint",
    "DatasetValidator",
    "validate_features",
    "validate_labels",
    "validate_sample_weights",
    "infer_schema",
    # Feature engineering (new)
    "PolynomialFeatures",
    "InteractionFeatures",
    "KBinsDiscretizer",
    "Binarizer",
    "FunctionTransformer",
    "TargetEncoder",
    "QuantileTransformer",
    "PowerTransformer",
]

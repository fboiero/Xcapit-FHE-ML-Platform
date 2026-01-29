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

from .feature_selection import (
    VarianceThreshold as VarianceThresholdNew,
    SelectKBest as SelectKBestNew,
    SelectPercentile as SelectPercentileNew,
    SelectFromModel as SelectFromModelNew,
    RFE as RFENew,
    RFECV,
    f_classif as f_classif_new,
    f_regression as f_regression_new,
    mutual_info_classif as mutual_info_classif_new,
)

from .model_selection import (
    KFold as KFoldNew,
    StratifiedKFold as StratifiedKFoldNew,
    LeaveOneOut as LeaveOneOutNew,
    ShuffleSplit,
    train_test_split as train_test_split_new,
    cross_val_score as cross_val_score_new,
    cross_validate as cross_validate_new,
    ParameterGrid,
    ParameterSampler,
    GridSearchCV as GridSearchCVNew,
    RandomizedSearchCV as RandomizedSearchCVNew,
)

from .impute import (
    SimpleImputer,
    KNNImputer,
    IterativeImputer,
    MissingIndicator,
)

from .ensemble import (
    VotingClassifier as VotingClassifierNew,
    VotingRegressor as VotingRegressorNew,
    StackingClassifier as StackingClassifierNew,
    StackingRegressor,
    BaggingClassifier,
    BaggingRegressor,
    AdaBoostClassifier,
    get_ensemble_feature_importances,
)

from .outlier import (
    IsolationForest as IsolationForestNew,
    LocalOutlierFactor as LocalOutlierFactorNew,
    EllipticEnvelope as EllipticEnvelopeNew,
    OneClassSVM as OneClassSVMNew,
    detect_outliers_zscore,
    detect_outliers_iqr,
    detect_outliers_mad,
    detect_outliers_dbscan,
    get_outlier_scores,
)

from .validation import (
    DataSchema,
    ColumnSchema,
    ValidationResult,
    ValidationError as DataValidationError,
    # Constraints
    NotNull,
    NotEmpty,
    InRange,
    InSet,
    MatchesRegex,
    MinLength,
    MaxLength,
    IsType,
    IsPositive,
    IsEmail,
    IsURL,
    CustomConstraint,
    # Validators
    DatasetValidator,
    validate_features,
    validate_labels,
    validate_sample_weights,
    infer_schema,
)

from .feature_engineering import (
    PolynomialFeatures,
    InteractionFeatures,
    KBinsDiscretizer,
    Binarizer,
    FunctionTransformer,
    TargetEncoder,
    OrdinalEncoder as OrdinalEncoderNew,
    OneHotEncoder as OneHotEncoderNew,
    QuantileTransformer,
    PowerTransformer,
)
from .preprocessing import (
    # Scalers
    StandardScaler,
    MinMaxScaler,
    RobustScaler,
    # Encoders
    OneHotEncoder,
    OrdinalEncoder,
)

from .pipeline import (
    Pipeline,
    FeatureUnion,
    ColumnTransformer,
    make_pipeline,
    make_union,
    TransformedTargetRegressor,
)

from .models import (
    # Calibration
    CalibrationConfig,
    CalibrationMethod,
    IsotonicRegression,
    SigmoidCalibration,
    TemperatureScaling,
    CalibratedClassifierCV,
    calibration_curve,
    # Multi-output
    MultiOutputClassifier,
    MultiOutputRegressor,
    ClassifierChain,
    RegressorChain,
    MultiLabelBinarizer,
)

from .evaluation import (
    # Advanced metrics
    matthews_corrcoef,
    cohen_kappa_score,
    brier_score_loss,
    balanced_accuracy_score,
    silhouette_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    adjusted_rand_score,
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

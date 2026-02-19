"""Model Evaluation Module.

This module provides utilities for evaluating FHE machine learning models:
- Classification metrics (accuracy, precision, recall, F1, ROC-AUC)
- Regression metrics (MSE, MAE, R², RMSE)
- Cross-validation
- Confusion matrix
"""

from .advanced_metrics import (
    adjusted_rand_score,
    balanced_accuracy_score,
    brier_score_loss,
    calinski_harabasz_score,
    cohen_kappa_score,
    davies_bouldin_score,
    hamming_loss,
    hinge_loss,
    # Classification
    matthews_corrcoef,
    # Regression
    max_error,
    mean_squared_log_error,
    median_absolute_error,
    normalized_mutual_info_score,
    # Clustering
    silhouette_score,
    zero_one_loss,
)
from .cross_validation import (
    GridSearchCV,
    GroupKFold,
    KFold,
    LeaveOneOut,
    RepeatedKFold,
    StratifiedKFold,
    TimeSeriesSplit,
    cross_val_predict,
    cross_val_score,
    cross_validate,
    learning_curve,
    train_test_split,
)
from .hyperparameter_tuning import (
    BayesianOptimization,
    HalvingRandomSearchCV,
    ParameterSampler,
    RandomizedSearchCV,
    SearchResult,
)
from .interpretation import (
    FeatureInteraction,
    IndividualConditionalExpectation,
    PartialDependence,
    PermutationImportance,
    SHAPApproximation,
    explain_prediction,
)
from .metrics import (
    # Classification metrics
    accuracy_score,
    classification_report,
    confusion_matrix,
    explained_variance_score,
    f1_score,
    # Multi-class
    log_loss,
    mean_absolute_error,
    mean_absolute_percentage_error,
    # Regression metrics
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
    root_mean_squared_error,
)

__all__ = [
    # Classification
    "accuracy_score",
    "precision_score",
    "recall_score",
    "f1_score",
    "roc_auc_score",
    "confusion_matrix",
    "classification_report",
    "log_loss",
    # Regression
    "mean_squared_error",
    "mean_absolute_error",
    "r2_score",
    "root_mean_squared_error",
    "mean_absolute_percentage_error",
    "explained_variance_score",
    # Cross-validation
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
    # Hyperparameter tuning
    "RandomizedSearchCV",
    "BayesianOptimization",
    "HalvingRandomSearchCV",
    "ParameterSampler",
    "SearchResult",
    # Model interpretation
    "PermutationImportance",
    "SHAPApproximation",
    "PartialDependence",
    "IndividualConditionalExpectation",
    "FeatureInteraction",
    "explain_prediction",
    # Advanced metrics - Classification
    "matthews_corrcoef",
    "cohen_kappa_score",
    "brier_score_loss",
    "balanced_accuracy_score",
    "hamming_loss",
    "zero_one_loss",
    "hinge_loss",
    # Advanced metrics - Regression
    "max_error",
    "median_absolute_error",
    "mean_squared_log_error",
    # Advanced metrics - Clustering
    "silhouette_score",
    "calinski_harabasz_score",
    "davies_bouldin_score",
    "adjusted_rand_score",
    "normalized_mutual_info_score",
]

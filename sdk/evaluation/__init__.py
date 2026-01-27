"""Model Evaluation Module.

This module provides utilities for evaluating FHE machine learning models:
- Classification metrics (accuracy, precision, recall, F1, ROC-AUC)
- Regression metrics (MSE, MAE, R², RMSE)
- Cross-validation
- Confusion matrix
"""

from .metrics import (
    # Classification metrics
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
    # Regression metrics
    mean_squared_error,
    mean_absolute_error,
    r2_score,
    root_mean_squared_error,
    mean_absolute_percentage_error,
    explained_variance_score,
    # Multi-class
    log_loss,
)

from .cross_validation import (
    cross_val_score,
    cross_val_predict,
    KFold,
    StratifiedKFold,
    train_test_split,
    GridSearchCV,
)

from .hyperparameter_tuning import (
    BayesianOptimization,
    HalvingRandomSearchCV,
    ParameterSampler,
    RandomizedSearchCV,
    SearchResult,
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
    "KFold",
    "StratifiedKFold",
    "train_test_split",
    "GridSearchCV",
    # Hyperparameter tuning
    "RandomizedSearchCV",
    "BayesianOptimization",
    "HalvingRandomSearchCV",
    "ParameterSampler",
    "SearchResult",
]

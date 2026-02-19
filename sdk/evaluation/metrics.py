"""Evaluation metrics for FHE machine learning models.

This module provides metrics for evaluating classification and regression models.
"""

from typing import Optional, Union

import numpy as np

# =============================================================================
# Classification Metrics
# =============================================================================


def accuracy_score(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    normalize: bool = True,
) -> float:
    """Compute accuracy classification score.

    Args:
        y_true: Ground truth labels.
        y_pred: Predicted labels.
        normalize: If True, return fraction of correctly classified samples.

    Returns:
        Accuracy score.

    Example:
        >>> accuracy_score([0, 1, 1, 0], [0, 1, 0, 0])
        0.75
    """
    y_true = np.asarray(y_true).ravel()
    y_pred = np.asarray(y_pred).ravel()

    correct = np.sum(y_true == y_pred)

    if normalize:
        return correct / len(y_true)
    return correct


def precision_score(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    pos_label: Union[int, str] = 1,
    average: str = "binary",
    zero_division: float = 0.0,
) -> Union[float, np.ndarray]:
    """Compute precision score.

    Precision = TP / (TP + FP)

    Args:
        y_true: Ground truth labels.
        y_pred: Predicted labels.
        pos_label: Positive class label for binary classification.
        average: 'binary', 'micro', 'macro', 'weighted', or None.
        zero_division: Value to return when there is a zero division.

    Returns:
        Precision score(s).

    Example:
        >>> precision_score([0, 1, 1, 0], [0, 1, 0, 1])
        0.5
    """
    y_true = np.asarray(y_true).ravel()
    y_pred = np.asarray(y_pred).ravel()

    if average == "binary":
        tp = np.sum((y_true == pos_label) & (y_pred == pos_label))
        fp = np.sum((y_true != pos_label) & (y_pred == pos_label))

        if tp + fp == 0:
            return zero_division
        return tp / (tp + fp)

    classes = np.unique(np.concatenate([y_true, y_pred]))
    precisions = []
    supports = []

    for c in classes:
        tp = np.sum((y_true == c) & (y_pred == c))
        fp = np.sum((y_true != c) & (y_pred == c))
        precisions.append(tp / (tp + fp) if tp + fp > 0 else zero_division)
        supports.append(np.sum(y_true == c))

    precisions = np.array(precisions)
    supports = np.array(supports)

    if average == "micro":
        tp_sum = sum(np.sum((y_true == c) & (y_pred == c)) for c in classes)
        fp_sum = sum(np.sum((y_true != c) & (y_pred == c)) for c in classes)
        return tp_sum / (tp_sum + fp_sum) if tp_sum + fp_sum > 0 else zero_division
    elif average == "macro":
        return np.mean(precisions)
    elif average == "weighted":
        return np.average(precisions, weights=supports)
    else:
        return precisions


def recall_score(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    pos_label: Union[int, str] = 1,
    average: str = "binary",
    zero_division: float = 0.0,
) -> Union[float, np.ndarray]:
    """Compute recall score.

    Recall = TP / (TP + FN)

    Args:
        y_true: Ground truth labels.
        y_pred: Predicted labels.
        pos_label: Positive class label for binary classification.
        average: 'binary', 'micro', 'macro', 'weighted', or None.
        zero_division: Value to return when there is a zero division.

    Returns:
        Recall score(s).

    Example:
        >>> recall_score([0, 1, 1, 0], [0, 1, 0, 1])
        0.5
    """
    y_true = np.asarray(y_true).ravel()
    y_pred = np.asarray(y_pred).ravel()

    if average == "binary":
        tp = np.sum((y_true == pos_label) & (y_pred == pos_label))
        fn = np.sum((y_true == pos_label) & (y_pred != pos_label))

        if tp + fn == 0:
            return zero_division
        return tp / (tp + fn)

    classes = np.unique(np.concatenate([y_true, y_pred]))
    recalls = []
    supports = []

    for c in classes:
        tp = np.sum((y_true == c) & (y_pred == c))
        fn = np.sum((y_true == c) & (y_pred != c))
        recalls.append(tp / (tp + fn) if tp + fn > 0 else zero_division)
        supports.append(np.sum(y_true == c))

    recalls = np.array(recalls)
    supports = np.array(supports)

    if average == "micro":
        tp_sum = sum(np.sum((y_true == c) & (y_pred == c)) for c in classes)
        fn_sum = sum(np.sum((y_true == c) & (y_pred != c)) for c in classes)
        return tp_sum / (tp_sum + fn_sum) if tp_sum + fn_sum > 0 else zero_division
    elif average == "macro":
        return np.mean(recalls)
    elif average == "weighted":
        return np.average(recalls, weights=supports)
    else:
        return recalls


def f1_score(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    pos_label: Union[int, str] = 1,
    average: str = "binary",
    zero_division: float = 0.0,
) -> Union[float, np.ndarray]:
    """Compute F1 score (harmonic mean of precision and recall).

    F1 = 2 * (precision * recall) / (precision + recall)

    Args:
        y_true: Ground truth labels.
        y_pred: Predicted labels.
        pos_label: Positive class label for binary classification.
        average: 'binary', 'micro', 'macro', 'weighted', or None.
        zero_division: Value to return when there is a zero division.

    Returns:
        F1 score(s).

    Example:
        >>> f1_score([0, 1, 1, 0], [0, 1, 0, 0])
        0.6666...
    """
    prec = precision_score(y_true, y_pred, pos_label, average, zero_division)
    rec = recall_score(y_true, y_pred, pos_label, average, zero_division)

    if isinstance(prec, np.ndarray):
        denom = prec + rec
        f1 = np.where(denom > 0, 2 * prec * rec / denom, zero_division)
        return f1

    if prec + rec == 0:
        return zero_division
    return 2 * prec * rec / (prec + rec)


def confusion_matrix(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    labels: Optional[list] = None,
    normalize: Optional[str] = None,
) -> np.ndarray:
    """Compute confusion matrix.

    Args:
        y_true: Ground truth labels.
        y_pred: Predicted labels.
        labels: List of labels to index the matrix.
        normalize: 'true', 'pred', 'all', or None.

    Returns:
        Confusion matrix of shape (n_classes, n_classes).

    Example:
        >>> confusion_matrix([0, 1, 1, 0], [0, 1, 0, 0])
        array([[2, 0],
               [1, 1]])
    """
    y_true = np.asarray(y_true).ravel()
    y_pred = np.asarray(y_pred).ravel()

    if labels is None:
        labels = np.unique(np.concatenate([y_true, y_pred]))

    n_labels = len(labels)
    label_to_idx = {label: i for i, label in enumerate(labels)}

    cm = np.zeros((n_labels, n_labels), dtype=int)

    for t, p in zip(y_true, y_pred):
        if t in label_to_idx and p in label_to_idx:
            cm[label_to_idx[t], label_to_idx[p]] += 1

    if normalize == "true":
        cm = cm.astype(float) / cm.sum(axis=1, keepdims=True)
    elif normalize == "pred":
        cm = cm.astype(float) / cm.sum(axis=0, keepdims=True)
    elif normalize == "all":
        cm = cm.astype(float) / cm.sum()

    return cm


def roc_auc_score(
    y_true: np.ndarray,
    y_score: np.ndarray,
    multi_class: str = "raise",
) -> float:
    """Compute Area Under the ROC Curve (AUC).

    Args:
        y_true: True binary labels.
        y_score: Target scores (probabilities for positive class).
        multi_class: How to handle multi-class ('raise', 'ovr', 'ovo').

    Returns:
        AUC score.

    Example:
        >>> roc_auc_score([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8])
        0.75
    """
    y_true = np.asarray(y_true).ravel()
    y_score = np.asarray(y_score).ravel()

    # Check if binary
    unique = np.unique(y_true)
    if len(unique) != 2 and multi_class == "raise":
        raise ValueError("ROC AUC requires binary classification or multi_class setting")

    # Compute AUC using Mann-Whitney U statistic
    pos_mask = y_true == unique[-1]  # Assume last class is positive
    neg_mask = ~pos_mask

    pos_scores = y_score[pos_mask]
    neg_scores = y_score[neg_mask]

    if len(pos_scores) == 0 or len(neg_scores) == 0:
        return 0.5

    # Count pairs where positive has higher score
    n_pairs = len(pos_scores) * len(neg_scores)
    n_correct = 0

    for p in pos_scores:
        n_correct += np.sum(neg_scores < p)
        n_correct += 0.5 * np.sum(neg_scores == p)

    return n_correct / n_pairs


def log_loss(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    eps: float = 1e-15,
    normalize: bool = True,
) -> float:
    """Compute log loss (cross-entropy loss).

    Args:
        y_true: True labels (can be multi-class).
        y_pred: Predicted probabilities.
        eps: Small value to clip probabilities.
        normalize: Whether to return mean loss.

    Returns:
        Log loss value.

    Example:
        >>> log_loss([0, 0, 1, 1], [[0.9, 0.1], [0.8, 0.2], [0.3, 0.7], [0.1, 0.9]])
        0.1738...
    """
    y_true = np.asarray(y_true).ravel()
    y_pred = np.asarray(y_pred)

    # If y_pred is 1D (binary), reshape to 2D
    if y_pred.ndim == 1:
        y_pred = np.column_stack([1 - y_pred, y_pred])

    # Clip probabilities
    y_pred = np.clip(y_pred, eps, 1 - eps)

    # One-hot encode y_true if needed
    n_samples = len(y_true)
    n_classes = y_pred.shape[1]

    y_true_onehot = np.zeros((n_samples, n_classes))
    for i, label in enumerate(y_true):
        if 0 <= label < n_classes:
            y_true_onehot[i, int(label)] = 1

    # Compute cross-entropy
    loss = -np.sum(y_true_onehot * np.log(y_pred))

    if normalize:
        return loss / n_samples
    return loss


def classification_report(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    labels: Optional[list] = None,
    target_names: Optional[list] = None,
    output_dict: bool = False,
) -> Union[str, dict]:
    """Build a text report showing main classification metrics.

    Args:
        y_true: Ground truth labels.
        y_pred: Predicted labels.
        labels: Labels to include in report.
        target_names: Display names for labels.
        output_dict: If True, return dict instead of string.

    Returns:
        Classification report as string or dict.

    Example:
        >>> print(classification_report([0, 1, 1, 0], [0, 1, 0, 0]))
                      precision    recall  f1-score   support
        ...
    """
    y_true = np.asarray(y_true).ravel()
    y_pred = np.asarray(y_pred).ravel()

    if labels is None:
        labels = np.unique(np.concatenate([y_true, y_pred]))

    if target_names is None:
        target_names = [str(label) for label in labels]

    report = {}

    for label, name in zip(labels, target_names):
        prec = precision_score(y_true, y_pred, pos_label=label, average="binary")
        rec = recall_score(y_true, y_pred, pos_label=label, average="binary")
        f1 = f1_score(y_true, y_pred, pos_label=label, average="binary")
        support = np.sum(y_true == label)

        report[name] = {
            "precision": prec,
            "recall": rec,
            "f1-score": f1,
            "support": int(support),
        }

    # Macro average
    report["macro avg"] = {
        "precision": precision_score(y_true, y_pred, average="macro"),
        "recall": recall_score(y_true, y_pred, average="macro"),
        "f1-score": f1_score(y_true, y_pred, average="macro"),
        "support": len(y_true),
    }

    # Weighted average
    report["weighted avg"] = {
        "precision": precision_score(y_true, y_pred, average="weighted"),
        "recall": recall_score(y_true, y_pred, average="weighted"),
        "f1-score": f1_score(y_true, y_pred, average="weighted"),
        "support": len(y_true),
    }

    report["accuracy"] = accuracy_score(y_true, y_pred)

    if output_dict:
        return report

    # Format as string
    headers = ["precision", "recall", "f1-score", "support"]
    longest_name = max(len(name) for name in target_names + ["macro avg", "weighted avg"])
    name_width = max(longest_name, 15)

    lines = [" " * name_width + "  " + "  ".join(f"{h:>10}" for h in headers)]
    lines.append("")

    for name in target_names:
        values = report[name]
        line = f"{name:>{name_width}}  "
        line += f"{values['precision']:>10.2f}  "
        line += f"{values['recall']:>10.2f}  "
        line += f"{values['f1-score']:>10.2f}  "
        line += f"{values['support']:>10}"
        lines.append(line)

    lines.append("")
    lines.append(
        f"{'accuracy':>{name_width}}  {'':>10}  {'':>10}  {report['accuracy']:>10.2f}  {len(y_true):>10}"
    )

    for avg in ["macro avg", "weighted avg"]:
        values = report[avg]
        line = f"{avg:>{name_width}}  "
        line += f"{values['precision']:>10.2f}  "
        line += f"{values['recall']:>10.2f}  "
        line += f"{values['f1-score']:>10.2f}  "
        line += f"{values['support']:>10}"
        lines.append(line)

    return "\n".join(lines)


# =============================================================================
# Regression Metrics
# =============================================================================


def mean_squared_error(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    squared: bool = True,
) -> float:
    """Compute Mean Squared Error.

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.
        squared: If True, return MSE; if False, return RMSE.

    Returns:
        MSE or RMSE.

    Example:
        >>> mean_squared_error([3, -0.5, 2], [2.5, 0.0, 2])
        0.4166...
    """
    y_true = np.asarray(y_true).ravel()
    y_pred = np.asarray(y_pred).ravel()

    mse = np.mean((y_true - y_pred) ** 2)

    if squared:
        return mse
    return np.sqrt(mse)


def root_mean_squared_error(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> float:
    """Compute Root Mean Squared Error.

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.

    Returns:
        RMSE.

    Example:
        >>> root_mean_squared_error([3, -0.5, 2], [2.5, 0.0, 2])
        0.6454...
    """
    return mean_squared_error(y_true, y_pred, squared=False)


def mean_absolute_error(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> float:
    """Compute Mean Absolute Error.

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.

    Returns:
        MAE.

    Example:
        >>> mean_absolute_error([3, -0.5, 2], [2.5, 0.0, 2])
        0.5
    """
    y_true = np.asarray(y_true).ravel()
    y_pred = np.asarray(y_pred).ravel()

    return np.mean(np.abs(y_true - y_pred))


def r2_score(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> float:
    """Compute R² (coefficient of determination).

    R² = 1 - SS_res / SS_tot

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.

    Returns:
        R² score. Best possible is 1.0, can be negative.

    Example:
        >>> r2_score([3, -0.5, 2, 7], [2.5, 0.0, 2, 8])
        0.9486...
    """
    y_true = np.asarray(y_true).ravel()
    y_pred = np.asarray(y_pred).ravel()

    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)

    if ss_tot == 0:
        return 0.0

    return 1 - (ss_res / ss_tot)


def mean_absolute_percentage_error(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    eps: float = 1e-10,
) -> float:
    """Compute Mean Absolute Percentage Error.

    MAPE = mean(|y_true - y_pred| / |y_true|) * 100

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.
        eps: Small value to avoid division by zero.

    Returns:
        MAPE as percentage.

    Example:
        >>> mean_absolute_percentage_error([3, -0.5, 2], [2.5, 0.0, 2])
        33.33...
    """
    y_true = np.asarray(y_true).ravel()
    y_pred = np.asarray(y_pred).ravel()

    return 100 * np.mean(np.abs((y_true - y_pred) / (np.abs(y_true) + eps)))


def explained_variance_score(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> float:
    """Compute explained variance score.

    Best possible score is 1.0, lower is worse.

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.

    Returns:
        Explained variance score.

    Example:
        >>> explained_variance_score([3, -0.5, 2, 7], [2.5, 0.0, 2, 8])
        0.9571...
    """
    y_true = np.asarray(y_true).ravel()
    y_pred = np.asarray(y_pred).ravel()

    y_diff = y_true - y_pred
    var_residual = np.var(y_diff)
    var_true = np.var(y_true)

    if var_true == 0:
        return 0.0

    return 1 - (var_residual / var_true)

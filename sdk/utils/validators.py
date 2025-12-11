"""Data validation utilities.

This module provides validation functions for input data
to ensure compatibility with FHE operations.
"""

from typing import Optional, Union

import numpy as np
import pandas as pd


class ValidationError(Exception):
    """Raised when data validation fails."""

    pass


def validate_numeric_data(
    data: Union[pd.DataFrame, np.ndarray],
    allow_nan: bool = False,
    allow_inf: bool = False,
) -> None:
    """Validate that data contains only valid numeric values.

    Args:
        data: Input data to validate.
        allow_nan: Whether to allow NaN values.
        allow_inf: Whether to allow infinite values.

    Raises:
        ValidationError: If validation fails.
    """
    if isinstance(data, pd.DataFrame):
        arr = data.values
    else:
        arr = np.asarray(data)

    # Check for non-numeric types
    if not np.issubdtype(arr.dtype, np.number):
        raise ValidationError(f"Data must be numeric, got dtype: {arr.dtype}")

    # Check for NaN
    if not allow_nan and np.any(np.isnan(arr)):
        nan_count = np.sum(np.isnan(arr))
        raise ValidationError(
            f"Data contains {nan_count} NaN values. "
            "Use allow_nan=True to permit or preprocess data."
        )

    # Check for infinity
    if not allow_inf and np.any(np.isinf(arr)):
        inf_count = np.sum(np.isinf(arr))
        raise ValidationError(
            f"Data contains {inf_count} infinite values. "
            "Use allow_inf=True to permit or preprocess data."
        )


def validate_data_shape(
    data: Union[pd.DataFrame, np.ndarray],
    min_samples: int = 1,
    min_features: int = 1,
    max_features: Optional[int] = None,
) -> None:
    """Validate data shape constraints.

    Args:
        data: Input data to validate.
        min_samples: Minimum required samples.
        min_features: Minimum required features.
        max_features: Maximum allowed features (related to FHE slot limit).

    Raises:
        ValidationError: If shape constraints are violated.
    """
    if isinstance(data, pd.DataFrame):
        n_samples, n_features = data.shape
    else:
        arr = np.asarray(data)
        if arr.ndim == 1:
            n_samples, n_features = len(arr), 1
        elif arr.ndim == 2:
            n_samples, n_features = arr.shape
        else:
            raise ValidationError(f"Data must be 1D or 2D, got {arr.ndim}D array")

    if n_samples < min_samples:
        raise ValidationError(f"Data must have at least {min_samples} samples, got {n_samples}")

    if n_features < min_features:
        raise ValidationError(f"Data must have at least {min_features} features, got {n_features}")

    if max_features is not None and n_features > max_features:
        raise ValidationError(
            f"Data has {n_features} features, exceeding maximum of {max_features} (FHE slot limit)"
        )


def validate_feature_range(
    data: Union[pd.DataFrame, np.ndarray],
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
) -> None:
    """Validate that feature values are within expected range.

    Args:
        data: Input data to validate.
        min_value: Minimum allowed value.
        max_value: Maximum allowed value.

    Raises:
        ValidationError: If values are out of range.
    """
    if isinstance(data, pd.DataFrame):
        arr = data.values
    else:
        arr = np.asarray(data)

    if min_value is not None:
        actual_min = np.min(arr)
        if actual_min < min_value:
            raise ValidationError(f"Data contains value {actual_min} below minimum {min_value}")

    if max_value is not None:
        actual_max = np.max(arr)
        if actual_max > max_value:
            raise ValidationError(f"Data contains value {actual_max} above maximum {max_value}")


def validate_target(
    target: Union[pd.Series, np.ndarray],
    n_samples: int,
    task_type: str = "regression",
) -> None:
    """Validate target variable for ML task.

    Args:
        target: Target variable.
        n_samples: Expected number of samples (must match features).
        task_type: Type of ML task ("regression" or "classification").

    Raises:
        ValidationError: If target is invalid.
    """
    if isinstance(target, pd.Series):
        arr = target.values
    else:
        arr = np.asarray(target)

    if arr.ndim != 1:
        raise ValidationError(f"Target must be 1D, got {arr.ndim}D array")

    if len(arr) != n_samples:
        raise ValidationError(
            f"Target length {len(arr)} doesn't match number of samples {n_samples}"
        )

    if task_type == "classification":
        unique_values = np.unique(arr)
        if len(unique_values) < 2:
            raise ValidationError("Classification target must have at least 2 classes")


def check_fhe_compatibility(
    data: Union[pd.DataFrame, np.ndarray],
    max_slots: int = 4096,
) -> dict:
    """Check data compatibility with FHE constraints.

    Returns a dict with compatibility info and warnings.

    Args:
        data: Input data to check.
        max_slots: Maximum FHE slots available.

    Returns:
        Dict with keys:
            - compatible: bool
            - warnings: list of warning messages
            - stats: dict with data statistics
    """
    if isinstance(data, pd.DataFrame):
        arr = data.values
        n_samples, n_features = data.shape
    else:
        arr = np.asarray(data)
        if arr.ndim == 1:
            n_samples, n_features = len(arr), 1
        else:
            n_samples, n_features = arr.shape

    warnings: list[str] = []
    compatible = True

    # Check slot limit
    if n_features > max_slots:
        compatible = False
        warnings.append(f"Features ({n_features}) exceed max slots ({max_slots})")

    # Check for non-numeric
    if not np.issubdtype(arr.dtype, np.number):
        compatible = False
        warnings.append(f"Non-numeric dtype: {arr.dtype}")

    # Check for NaN/Inf
    if np.any(np.isnan(arr)):
        compatible = False
        warnings.append(f"Contains {np.sum(np.isnan(arr))} NaN values")

    if np.any(np.isinf(arr)):
        compatible = False
        warnings.append(f"Contains {np.sum(np.isinf(arr))} infinite values")

    # Value range warnings
    data_min = float(np.min(arr)) if np.issubdtype(arr.dtype, np.number) else None
    data_max = float(np.max(arr)) if np.issubdtype(arr.dtype, np.number) else None

    if data_min is not None and data_max is not None:
        value_range = data_max - data_min
        if value_range > 1e6:
            warnings.append(
                f"Large value range ({value_range:.2e}). "
                "Consider normalization for better precision."
            )

    return {
        "compatible": compatible,
        "warnings": warnings,
        "stats": {
            "n_samples": n_samples,
            "n_features": n_features,
            "min_value": data_min,
            "max_value": data_max,
            "dtype": str(arr.dtype),
        },
    }

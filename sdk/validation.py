"""
Data validation utilities for FHE-ML SDK.

Provides schema validation, data type checks, and constraint validation:
- DataSchema: Define and validate data schemas
- ColumnValidator: Validate individual columns
- DataFrameValidator: Validate entire datasets
- Constraint classes: Range, Regex, Unique, NotNull, etc.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import numpy as np

# =============================================================================
# Validation Results
# =============================================================================


@dataclass
class ValidationError:
    """Represents a single validation error."""

    column: Optional[str]
    row: Optional[int]
    constraint: str
    message: str
    value: Any = None

    def __str__(self) -> str:
        location = []
        if self.column:
            location.append(f"column='{self.column}'")
        if self.row is not None:
            location.append(f"row={self.row}")
        loc_str = f" [{', '.join(location)}]" if location else ""
        return f"{self.constraint}{loc_str}: {self.message}"


@dataclass
class ValidationResult:
    """Result of a validation check."""

    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return self.is_valid

    def add_error(self, error: ValidationError) -> None:
        """Add an error."""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: ValidationError) -> None:
        """Add a warning (doesn't affect validity)."""
        self.warnings.append(warning)

    def merge(self, other: ValidationResult) -> ValidationResult:
        """Merge another validation result."""
        return ValidationResult(
            is_valid=self.is_valid and other.is_valid,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
            summary={**self.summary, **other.summary},
        )

    def __str__(self) -> str:
        status = "VALID" if self.is_valid else "INVALID"
        lines = [f"Validation Result: {status}"]
        if self.errors:
            lines.append(f"  Errors ({len(self.errors)}):")
            for err in self.errors[:10]:  # Show first 10
                lines.append(f"    - {err}")
            if len(self.errors) > 10:
                lines.append(f"    ... and {len(self.errors) - 10} more")
        if self.warnings:
            lines.append(f"  Warnings ({len(self.warnings)}):")
            for warn in self.warnings[:5]:
                lines.append(f"    - {warn}")
        return "\n".join(lines)


# =============================================================================
# Constraints
# =============================================================================


class Constraint(ABC):
    """Base class for validation constraints."""

    name: str = "constraint"

    @abstractmethod
    def validate(self, value: Any, column: Optional[str] = None) -> Optional[ValidationError]:
        """
        Validate a single value.

        Returns None if valid, ValidationError otherwise.
        """
        pass

    def validate_array(
        self, values: np.ndarray, column: Optional[str] = None
    ) -> List[ValidationError]:
        """Validate an array of values."""
        errors = []
        for i, value in enumerate(values):
            error = self.validate(value, column)
            if error:
                error.row = i
                errors.append(error)
        return errors


class NotNull(Constraint):
    """Value must not be null/NaN."""

    name = "not_null"

    def validate(self, value: Any, column: Optional[str] = None) -> Optional[ValidationError]:
        is_null = (
            value is None
            or (isinstance(value, float) and np.isnan(value))
            or (isinstance(value, str) and value.strip() == "")
        )
        if is_null:
            return ValidationError(
                column=column,
                row=None,
                constraint=self.name,
                message="Value cannot be null or empty",
                value=value,
            )
        return None


class NotEmpty(Constraint):
    """String must not be empty."""

    name = "not_empty"

    def validate(self, value: Any, column: Optional[str] = None) -> Optional[ValidationError]:
        if isinstance(value, str) and len(value.strip()) == 0:
            return ValidationError(
                column=column,
                row=None,
                constraint=self.name,
                message="String cannot be empty",
                value=value,
            )
        return None


class InRange(Constraint):
    """Numeric value must be within range."""

    name = "in_range"

    def __init__(
        self,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        inclusive: bool = True,
    ):
        self.min_value = min_value
        self.max_value = max_value
        self.inclusive = inclusive

    def validate(self, value: Any, column: Optional[str] = None) -> Optional[ValidationError]:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return None  # Let NotNull handle this

        try:
            num = float(value)
        except (TypeError, ValueError):
            return ValidationError(
                column=column,
                row=None,
                constraint=self.name,
                message=f"Value is not numeric: {value}",
                value=value,
            )

        if self.inclusive:
            if self.min_value is not None and num < self.min_value:
                return ValidationError(
                    column=column,
                    row=None,
                    constraint=self.name,
                    message=f"Value {num} is below minimum {self.min_value}",
                    value=value,
                )
            if self.max_value is not None and num > self.max_value:
                return ValidationError(
                    column=column,
                    row=None,
                    constraint=self.name,
                    message=f"Value {num} is above maximum {self.max_value}",
                    value=value,
                )
        else:
            if self.min_value is not None and num <= self.min_value:
                return ValidationError(
                    column=column,
                    row=None,
                    constraint=self.name,
                    message=f"Value {num} must be greater than {self.min_value}",
                    value=value,
                )
            if self.max_value is not None and num >= self.max_value:
                return ValidationError(
                    column=column,
                    row=None,
                    constraint=self.name,
                    message=f"Value {num} must be less than {self.max_value}",
                    value=value,
                )

        return None


class InSet(Constraint):
    """Value must be in allowed set."""

    name = "in_set"

    def __init__(self, allowed_values: Set[Any], case_sensitive: bool = True):
        self.allowed_values = allowed_values
        self.case_sensitive = case_sensitive
        if not case_sensitive:
            self._normalized = {str(v).lower() if isinstance(v, str) else v for v in allowed_values}
        else:
            self._normalized = allowed_values

    def validate(self, value: Any, column: Optional[str] = None) -> Optional[ValidationError]:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return None

        check_value = value
        if not self.case_sensitive and isinstance(value, str):
            check_value = value.lower()

        if check_value not in self._normalized:
            return ValidationError(
                column=column,
                row=None,
                constraint=self.name,
                message=f"Value '{value}' not in allowed set",
                value=value,
            )
        return None


class MatchesRegex(Constraint):
    """String must match regex pattern."""

    name = "matches_regex"

    def __init__(self, pattern: str, flags: int = 0):
        self.pattern = pattern
        self.regex = re.compile(pattern, flags)

    def validate(self, value: Any, column: Optional[str] = None) -> Optional[ValidationError]:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return None

        if not isinstance(value, str):
            value = str(value)

        if not self.regex.match(value):
            return ValidationError(
                column=column,
                row=None,
                constraint=self.name,
                message=f"Value '{value}' does not match pattern '{self.pattern}'",
                value=value,
            )
        return None


class MinLength(Constraint):
    """String must have minimum length."""

    name = "min_length"

    def __init__(self, min_length: int):
        self.min_length = min_length

    def validate(self, value: Any, column: Optional[str] = None) -> Optional[ValidationError]:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return None

        if len(str(value)) < self.min_length:
            return ValidationError(
                column=column,
                row=None,
                constraint=self.name,
                message=f"Value length {len(str(value))} is below minimum {self.min_length}",
                value=value,
            )
        return None


class MaxLength(Constraint):
    """String must have maximum length."""

    name = "max_length"

    def __init__(self, max_length: int):
        self.max_length = max_length

    def validate(self, value: Any, column: Optional[str] = None) -> Optional[ValidationError]:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return None

        if len(str(value)) > self.max_length:
            return ValidationError(
                column=column,
                row=None,
                constraint=self.name,
                message=f"Value length {len(str(value))} exceeds maximum {self.max_length}",
                value=value,
            )
        return None


class IsType(Constraint):
    """Value must be of specific type."""

    name = "is_type"

    TYPE_MAPPING = {
        "int": (int, np.integer),
        "float": (float, np.floating),
        "numeric": (int, float, np.integer, np.floating),
        "str": (str,),
        "bool": (bool, np.bool_),
        "datetime": (datetime,),
    }

    def __init__(self, dtype: Union[str, type]):
        self.dtype = dtype
        if isinstance(dtype, str):
            self.expected_types = self.TYPE_MAPPING.get(dtype, (type(dtype),))
        else:
            self.expected_types = (dtype,)

    def validate(self, value: Any, column: Optional[str] = None) -> Optional[ValidationError]:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return None

        if not isinstance(value, self.expected_types):
            return ValidationError(
                column=column,
                row=None,
                constraint=self.name,
                message=f"Value type {type(value).__name__} does not match expected {self.dtype}",
                value=value,
            )
        return None


class IsPositive(Constraint):
    """Numeric value must be positive."""

    name = "is_positive"

    def __init__(self, allow_zero: bool = False):
        self.allow_zero = allow_zero

    def validate(self, value: Any, column: Optional[str] = None) -> Optional[ValidationError]:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return None

        try:
            num = float(value)
        except (TypeError, ValueError):
            return None  # Let IsType handle this

        if self.allow_zero:
            if num < 0:
                return ValidationError(
                    column=column,
                    row=None,
                    constraint=self.name,
                    message=f"Value {num} must be non-negative",
                    value=value,
                )
        else:
            if num <= 0:
                return ValidationError(
                    column=column,
                    row=None,
                    constraint=self.name,
                    message=f"Value {num} must be positive",
                    value=value,
                )
        return None


class IsEmail(Constraint):
    """Value must be valid email format."""

    name = "is_email"
    EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    def validate(self, value: Any, column: Optional[str] = None) -> Optional[ValidationError]:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return None

        if not isinstance(value, str) or not self.EMAIL_REGEX.match(value):
            return ValidationError(
                column=column,
                row=None,
                constraint=self.name,
                message=f"Invalid email format: '{value}'",
                value=value,
            )
        return None


class IsURL(Constraint):
    """Value must be valid URL format."""

    name = "is_url"
    URL_REGEX = re.compile(
        r"^https?://"
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
        r"localhost|"
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
        r"(?::\d+)?"
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    def validate(self, value: Any, column: Optional[str] = None) -> Optional[ValidationError]:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return None

        if not isinstance(value, str) or not self.URL_REGEX.match(value):
            return ValidationError(
                column=column,
                row=None,
                constraint=self.name,
                message=f"Invalid URL format: '{value}'",
                value=value,
            )
        return None


class CustomConstraint(Constraint):
    """Custom validation function."""

    def __init__(self, func: Callable[[Any], bool], name: str = "custom", message: str = ""):
        self.name = name
        self.func = func
        self.message = message

    def validate(self, value: Any, column: Optional[str] = None) -> Optional[ValidationError]:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return None

        if not self.func(value):
            return ValidationError(
                column=column,
                row=None,
                constraint=self.name,
                message=self.message or f"Custom validation failed for value: {value}",
                value=value,
            )
        return None


# =============================================================================
# Column Schema
# =============================================================================


@dataclass
class ColumnSchema:
    """Schema definition for a single column."""

    name: str
    dtype: Optional[str] = None  # Expected data type
    nullable: bool = True
    constraints: List[Constraint] = field(default_factory=list)
    description: str = ""

    def validate(self, values: np.ndarray) -> ValidationResult:
        """Validate column values."""
        result = ValidationResult(is_valid=True)

        # Check for nulls if not nullable
        if not self.nullable:
            not_null = NotNull()
            errors = not_null.validate_array(values, self.name)
            for error in errors:
                result.add_error(error)

        # Check type if specified
        if self.dtype:
            type_constraint = IsType(self.dtype)
            for i, value in enumerate(values):
                if value is not None and not (isinstance(value, float) and np.isnan(value)):
                    error = type_constraint.validate(value, self.name)
                    if error:
                        error.row = i
                        result.add_error(error)

        # Apply all constraints
        for constraint in self.constraints:
            errors = constraint.validate_array(values, self.name)
            for error in errors:
                result.add_error(error)

        return result


# =============================================================================
# Data Schema
# =============================================================================


@dataclass
class DataSchema:
    """
    Schema definition for a dataset.

    Examples
    --------
    >>> schema = DataSchema(
    ...     columns=[
    ...         ColumnSchema("id", dtype="int", nullable=False),
    ...         ColumnSchema("name", dtype="str", nullable=False,
    ...                      constraints=[MinLength(1), MaxLength(100)]),
    ...         ColumnSchema("age", dtype="int", nullable=True,
    ...                      constraints=[InRange(0, 150)]),
    ...         ColumnSchema("email", dtype="str",
    ...                      constraints=[IsEmail()]),
    ...     ]
    ... )
    >>> result = schema.validate(data)
    """

    columns: List[ColumnSchema] = field(default_factory=list)
    strict: bool = True  # Fail on unknown columns
    min_rows: Optional[int] = None
    max_rows: Optional[int] = None

    def __post_init__(self):
        self._column_map = {col.name: col for col in self.columns}

    def add_column(self, column: ColumnSchema) -> DataSchema:
        """Add a column schema."""
        self.columns.append(column)
        self._column_map[column.name] = column
        return self

    def get_column(self, name: str) -> Optional[ColumnSchema]:
        """Get column schema by name."""
        return self._column_map.get(name)

    def validate(
        self,
        data: Union[np.ndarray, Dict[str, np.ndarray]],
        column_names: Optional[List[str]] = None,
    ) -> ValidationResult:
        """
        Validate data against schema.

        Parameters
        ----------
        data : array or dict
            Data to validate. If array, column_names must be provided.
        column_names : list of str, optional
            Column names if data is array.

        Returns
        -------
        result : ValidationResult
            Validation result.
        """
        result = ValidationResult(is_valid=True)

        # Convert to dict format
        if isinstance(data, np.ndarray):
            if column_names is None:
                column_names = [f"col_{i}" for i in range(data.shape[1])]
            data_dict = {name: data[:, i] for i, name in enumerate(column_names)}
        else:
            data_dict = data
            column_names = list(data.keys())

        # Check row count
        if data_dict:
            n_rows = len(list(data_dict.values())[0])
            if self.min_rows is not None and n_rows < self.min_rows:
                result.add_error(
                    ValidationError(
                        column=None,
                        row=None,
                        constraint="min_rows",
                        message=f"Dataset has {n_rows} rows, minimum is {self.min_rows}",
                    )
                )
            if self.max_rows is not None and n_rows > self.max_rows:
                result.add_error(
                    ValidationError(
                        column=None,
                        row=None,
                        constraint="max_rows",
                        message=f"Dataset has {n_rows} rows, maximum is {self.max_rows}",
                    )
                )

        # Check for missing columns
        schema_columns = set(self._column_map.keys())
        data_columns = set(column_names)

        missing = schema_columns - data_columns
        for col in missing:
            col_schema = self._column_map[col]
            if not col_schema.nullable:
                result.add_error(
                    ValidationError(
                        column=col,
                        row=None,
                        constraint="required_column",
                        message=f"Required column '{col}' is missing",
                    )
                )

        # Check for unknown columns
        if self.strict:
            unknown = data_columns - schema_columns
            for col in unknown:
                result.add_warning(
                    ValidationError(
                        column=col,
                        row=None,
                        constraint="unknown_column",
                        message=f"Unknown column '{col}' not in schema",
                    )
                )

        # Validate each column
        for col_name, values in data_dict.items():
            col_schema = self._column_map.get(col_name)
            if col_schema:
                col_result = col_schema.validate(np.asarray(values))
                result = result.merge(col_result)

        result.summary = {
            "n_rows": n_rows if data_dict else 0,
            "n_columns": len(column_names),
            "n_errors": len(result.errors),
            "n_warnings": len(result.warnings),
        }

        return result


# =============================================================================
# Dataset Validator
# =============================================================================


class DatasetValidator:
    """
    High-level dataset validator with common checks.

    Examples
    --------
    >>> validator = DatasetValidator()
    >>> validator.add_check("no_duplicates", lambda df: len(df) == len(set(map(tuple, df))))
    >>> result = validator.validate(X)
    """

    def __init__(self):
        self.checks: List[Tuple[str, Callable]] = []

    def add_check(self, name: str, check_func: Callable[[np.ndarray], bool]) -> DatasetValidator:
        """Add a custom check function."""
        self.checks.append((name, check_func))
        return self

    def check_no_missing(self) -> DatasetValidator:
        """Add check for no missing values."""

        def check(X):
            return not np.any(np.isnan(X.astype(float)))

        self.checks.append(("no_missing", check))
        return self

    def check_no_duplicates(self) -> DatasetValidator:
        """Add check for no duplicate rows."""

        def check(X):
            return len(X) == len(np.unique(X, axis=0))

        self.checks.append(("no_duplicates", check))
        return self

    def check_finite(self) -> DatasetValidator:
        """Add check for finite values."""

        def check(X):
            return np.all(np.isfinite(X.astype(float)))

        self.checks.append(("finite_values", check))
        return self

    def check_shape(
        self,
        min_rows: Optional[int] = None,
        max_rows: Optional[int] = None,
        min_cols: Optional[int] = None,
        max_cols: Optional[int] = None,
    ) -> DatasetValidator:
        """Add check for dataset shape."""

        def check(X):
            n_rows, n_cols = X.shape
            if min_rows is not None and n_rows < min_rows:
                return False
            if max_rows is not None and n_rows > max_rows:
                return False
            if min_cols is not None and n_cols < min_cols:
                return False
            if max_cols is not None and n_cols > max_cols:
                return False
            return True

        self.checks.append(("valid_shape", check))
        return self

    def validate(self, X: np.ndarray) -> ValidationResult:
        """Run all validation checks."""
        X = np.asarray(X)
        result = ValidationResult(is_valid=True)

        for name, check_func in self.checks:
            try:
                passed = check_func(X)
                if not passed:
                    result.add_error(
                        ValidationError(
                            column=None,
                            row=None,
                            constraint=name,
                            message=f"Check '{name}' failed",
                        )
                    )
            except Exception as e:
                result.add_error(
                    ValidationError(
                        column=None,
                        row=None,
                        constraint=name,
                        message=f"Check '{name}' raised error: {e}",
                    )
                )

        return result


# =============================================================================
# Utility Functions
# =============================================================================


def validate_features(
    X: np.ndarray,
    n_features: Optional[int] = None,
    allow_nan: bool = False,
    allow_inf: bool = False,
) -> ValidationResult:
    """
    Validate feature matrix.

    Parameters
    ----------
    X : array-like
        Feature matrix.
    n_features : int, optional
        Expected number of features.
    allow_nan : bool, default=False
        Whether to allow NaN values.
    allow_inf : bool, default=False
        Whether to allow infinite values.

    Returns
    -------
    result : ValidationResult
    """
    X = np.asarray(X)
    result = ValidationResult(is_valid=True)

    # Check dimensions
    if X.ndim != 2:
        result.add_error(
            ValidationError(
                column=None,
                row=None,
                constraint="dimensions",
                message=f"Expected 2D array, got {X.ndim}D",
            )
        )
        return result

    # Check feature count
    if n_features is not None and X.shape[1] != n_features:
        result.add_error(
            ValidationError(
                column=None,
                row=None,
                constraint="n_features",
                message=f"Expected {n_features} features, got {X.shape[1]}",
            )
        )

    # Check for NaN
    if not allow_nan:
        nan_mask = np.isnan(X)
        if np.any(nan_mask):
            nan_count = np.sum(nan_mask)
            result.add_error(
                ValidationError(
                    column=None,
                    row=None,
                    constraint="no_nan",
                    message=f"Found {nan_count} NaN values",
                )
            )

    # Check for infinite
    if not allow_inf:
        inf_mask = np.isinf(X)
        if np.any(inf_mask):
            inf_count = np.sum(inf_mask)
            result.add_error(
                ValidationError(
                    column=None,
                    row=None,
                    constraint="no_inf",
                    message=f"Found {inf_count} infinite values",
                )
            )

    return result


def validate_labels(
    y: np.ndarray,
    n_samples: Optional[int] = None,
    n_classes: Optional[int] = None,
    class_labels: Optional[Set[Any]] = None,
) -> ValidationResult:
    """
    Validate label array.

    Parameters
    ----------
    y : array-like
        Labels.
    n_samples : int, optional
        Expected number of samples.
    n_classes : int, optional
        Expected number of classes.
    class_labels : set, optional
        Expected class labels.

    Returns
    -------
    result : ValidationResult
    """
    y = np.asarray(y)
    result = ValidationResult(is_valid=True)

    # Check dimensions
    if y.ndim != 1:
        result.add_error(
            ValidationError(
                column=None,
                row=None,
                constraint="dimensions",
                message=f"Expected 1D array, got {y.ndim}D",
            )
        )
        return result

    # Check sample count
    if n_samples is not None and len(y) != n_samples:
        result.add_error(
            ValidationError(
                column=None,
                row=None,
                constraint="n_samples",
                message=f"Expected {n_samples} samples, got {len(y)}",
            )
        )

    # Check class count
    unique_labels = np.unique(y)
    if n_classes is not None and len(unique_labels) != n_classes:
        result.add_error(
            ValidationError(
                column=None,
                row=None,
                constraint="n_classes",
                message=f"Expected {n_classes} classes, got {len(unique_labels)}",
            )
        )

    # Check class labels
    if class_labels is not None:
        unexpected = set(unique_labels) - class_labels
        if unexpected:
            result.add_error(
                ValidationError(
                    column=None,
                    row=None,
                    constraint="class_labels",
                    message=f"Unexpected class labels: {unexpected}",
                )
            )

    return result


def validate_sample_weights(
    sample_weight: np.ndarray,
    n_samples: int,
) -> ValidationResult:
    """Validate sample weights."""
    sample_weight = np.asarray(sample_weight)
    result = ValidationResult(is_valid=True)

    if len(sample_weight) != n_samples:
        result.add_error(
            ValidationError(
                column=None,
                row=None,
                constraint="length",
                message=f"Sample weight length {len(sample_weight)} != {n_samples}",
            )
        )

    if np.any(sample_weight < 0):
        result.add_error(
            ValidationError(
                column=None,
                row=None,
                constraint="non_negative",
                message="Sample weights must be non-negative",
            )
        )

    return result


def infer_schema(
    data: Union[np.ndarray, Dict[str, np.ndarray]],
    column_names: Optional[List[str]] = None,
) -> DataSchema:
    """
    Infer schema from data.

    Parameters
    ----------
    data : array or dict
        Data to analyze.
    column_names : list, optional
        Column names if data is array.

    Returns
    -------
    schema : DataSchema
        Inferred schema.
    """
    if isinstance(data, np.ndarray):
        if column_names is None:
            column_names = [f"col_{i}" for i in range(data.shape[1])]
        data_dict = {name: data[:, i] for i, name in enumerate(column_names)}
    else:
        data_dict = data

    columns = []
    for name, values in data_dict.items():
        values = np.asarray(values)

        # Infer dtype
        if np.issubdtype(values.dtype, np.integer):
            dtype = "int"
        elif np.issubdtype(values.dtype, np.floating):
            dtype = "float"
        elif np.issubdtype(values.dtype, np.str_) or values.dtype == object:
            dtype = "str"
        else:
            dtype = "numeric"

        # Check nullable
        nullable = np.any(np.isnan(values.astype(float))) if dtype in ["int", "float"] else False

        # Infer constraints
        constraints = []
        if dtype in ["int", "float"]:
            min_val = np.nanmin(values)
            max_val = np.nanmax(values)
            constraints.append(InRange(min_val, max_val))

        columns.append(
            ColumnSchema(
                name=name,
                dtype=dtype,
                nullable=nullable,
                constraints=constraints,
            )
        )

    return DataSchema(columns=columns)

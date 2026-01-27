"""
Tests for the data validation module.
"""

import numpy as np
import pytest

from sdk.validation import (
    DataSchema,
    ColumnSchema,
    ValidationResult,
    ValidationError,
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


class TestConstraints:
    """Tests for individual constraint classes."""

    def test_not_null(self):
        """Test NotNull constraint."""
        constraint = NotNull()

        assert constraint.validate(5) is True
        assert constraint.validate("hello") is True
        assert constraint.validate(None) is False
        assert constraint.validate(np.nan) is False

    def test_not_empty(self):
        """Test NotEmpty constraint."""
        constraint = NotEmpty()

        assert constraint.validate("hello") is True
        assert constraint.validate([1, 2, 3]) is True
        assert constraint.validate("") is False
        assert constraint.validate([]) is False
        assert constraint.validate(None) is False

    def test_in_range(self):
        """Test InRange constraint."""
        constraint = InRange(min_value=0, max_value=100)

        assert constraint.validate(50) is True
        assert constraint.validate(0) is True
        assert constraint.validate(100) is True
        assert constraint.validate(-1) is False
        assert constraint.validate(101) is False

    def test_in_range_open_bounds(self):
        """Test InRange with open bounds."""
        # Only min
        constraint_min = InRange(min_value=0)
        assert constraint_min.validate(1000) is True
        assert constraint_min.validate(-1) is False

        # Only max
        constraint_max = InRange(max_value=100)
        assert constraint_max.validate(-1000) is True
        assert constraint_max.validate(101) is False

    def test_in_set(self):
        """Test InSet constraint."""
        constraint = InSet(values=["A", "B", "C"])

        assert constraint.validate("A") is True
        assert constraint.validate("B") is True
        assert constraint.validate("D") is False
        assert constraint.validate(None) is False

    def test_matches_regex(self):
        """Test MatchesRegex constraint."""
        constraint = MatchesRegex(pattern=r"^\d{3}-\d{4}$")

        assert constraint.validate("123-4567") is True
        assert constraint.validate("12-34567") is False
        assert constraint.validate("abc-defg") is False

    def test_min_length(self):
        """Test MinLength constraint."""
        constraint = MinLength(length=3)

        assert constraint.validate("hello") is True
        assert constraint.validate("abc") is True
        assert constraint.validate("ab") is False
        assert constraint.validate([1, 2, 3]) is True
        assert constraint.validate([1]) is False

    def test_max_length(self):
        """Test MaxLength constraint."""
        constraint = MaxLength(length=5)

        assert constraint.validate("hello") is True
        assert constraint.validate("hi") is True
        assert constraint.validate("toolong") is False

    def test_is_type(self):
        """Test IsType constraint."""
        constraint_int = IsType(expected_type=int)
        constraint_str = IsType(expected_type=str)

        assert constraint_int.validate(42) is True
        assert constraint_int.validate("42") is False
        assert constraint_str.validate("hello") is True
        assert constraint_str.validate(42) is False

    def test_is_positive(self):
        """Test IsPositive constraint."""
        constraint = IsPositive()

        assert constraint.validate(5) is True
        assert constraint.validate(0.1) is True
        assert constraint.validate(0) is False
        assert constraint.validate(-1) is False

    def test_is_email(self):
        """Test IsEmail constraint."""
        constraint = IsEmail()

        assert constraint.validate("user@example.com") is True
        assert constraint.validate("user.name@domain.co.uk") is True
        assert constraint.validate("invalid-email") is False
        assert constraint.validate("@no-user.com") is False

    def test_is_url(self):
        """Test IsURL constraint."""
        constraint = IsURL()

        assert constraint.validate("https://example.com") is True
        assert constraint.validate("http://localhost:8080/path") is True
        assert constraint.validate("not-a-url") is False
        assert constraint.validate("ftp://files.com") is True

    def test_custom_constraint(self):
        """Test CustomConstraint with custom function."""

        def is_even(value):
            return value % 2 == 0

        constraint = CustomConstraint(validator=is_even, message="Value must be even")

        assert constraint.validate(4) is True
        assert constraint.validate(3) is False


class TestColumnSchema:
    """Tests for ColumnSchema."""

    def test_column_schema_basic(self):
        """Test basic column schema creation."""
        schema = ColumnSchema(
            name="age",
            dtype="int",
            nullable=False,
            constraints=[InRange(min_value=0, max_value=150)],
        )

        assert schema.name == "age"
        assert schema.dtype == "int"
        assert schema.nullable is False
        assert len(schema.constraints) == 1

    def test_column_schema_validation(self):
        """Test column schema validation."""
        schema = ColumnSchema(
            name="email",
            dtype="str",
            nullable=False,
            constraints=[IsEmail()],
        )

        result = schema.validate("user@example.com")
        assert result.is_valid is True

        result = schema.validate("invalid-email")
        assert result.is_valid is False

    def test_column_schema_nullable(self):
        """Test nullable column schema."""
        schema = ColumnSchema(
            name="optional_field",
            dtype="str",
            nullable=True,
            constraints=[MinLength(length=1)],
        )

        result = schema.validate(None)
        assert result.is_valid is True

        result = schema.validate("value")
        assert result.is_valid is True


class TestDataSchema:
    """Tests for DataSchema."""

    def test_data_schema_creation(self):
        """Test data schema creation."""
        columns = [
            ColumnSchema(name="id", dtype="int", nullable=False),
            ColumnSchema(name="name", dtype="str", nullable=False),
            ColumnSchema(name="age", dtype="int", nullable=True),
        ]
        schema = DataSchema(columns=columns)

        assert len(schema.columns) == 3

    def test_data_schema_validation(self):
        """Test data schema validation with array data."""
        columns = [
            ColumnSchema(
                name="value",
                dtype="float",
                nullable=False,
                constraints=[InRange(min_value=0, max_value=100)],
            ),
        ]
        schema = DataSchema(columns=columns)

        # Valid data
        data = np.array([[50], [25], [75]])
        result = schema.validate(data, column_names=["value"])
        assert result.is_valid is True

        # Invalid data (out of range)
        data_invalid = np.array([[50], [150], [75]])
        result = schema.validate(data_invalid, column_names=["value"])
        assert result.is_valid is False

    def test_strict_mode(self):
        """Test strict mode (all columns must be in schema)."""
        columns = [ColumnSchema(name="a", dtype="int")]
        schema = DataSchema(columns=columns, strict=True)

        # With extra column
        data = np.array([[1, 2]])
        result = schema.validate(data, column_names=["a", "b"])
        assert result.is_valid is False

        # Without strict mode
        schema_non_strict = DataSchema(columns=columns, strict=False)
        result = schema_non_strict.validate(data, column_names=["a", "b"])
        assert result.is_valid is True


class TestValidationResult:
    """Tests for ValidationResult."""

    def test_valid_result(self):
        """Test valid result creation."""
        result = ValidationResult(is_valid=True)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_invalid_result_with_errors(self):
        """Test invalid result with errors."""
        errors = [
            ValidationError(column="age", message="Value out of range", value=-5),
            ValidationError(column="email", message="Invalid email format", value="bad"),
        ]
        result = ValidationResult(is_valid=False, errors=errors)

        assert result.is_valid is False
        assert len(result.errors) == 2

    def test_result_summary(self):
        """Test result summary generation."""
        errors = [ValidationError(column="test", message="Error", value=None)]
        result = ValidationResult(is_valid=False, errors=errors)

        summary = result.summary()

        assert "test" in summary
        assert "Error" in summary


class TestDatasetValidator:
    """Tests for DatasetValidator."""

    def test_validator_with_schema(self):
        """Test validator with schema."""
        columns = [
            ColumnSchema(
                name="feature1",
                dtype="float",
                nullable=False,
                constraints=[InRange(min_value=0, max_value=1)],
            ),
            ColumnSchema(
                name="feature2",
                dtype="float",
                nullable=False,
                constraints=[InRange(min_value=0, max_value=1)],
            ),
        ]
        schema = DataSchema(columns=columns)
        validator = DatasetValidator(schema=schema)

        # Valid data
        X = np.array([[0.5, 0.5], [0.3, 0.7], [0.1, 0.9]])
        result = validator.validate(X, column_names=["feature1", "feature2"])
        assert result.is_valid is True

        # Invalid data
        X_invalid = np.array([[0.5, 1.5], [0.3, 0.7]])
        result = validator.validate(X_invalid, column_names=["feature1", "feature2"])
        assert result.is_valid is False


class TestValidationFunctions:
    """Tests for validation helper functions."""

    def test_validate_features(self):
        """Test validate_features function."""
        # Valid features
        X = np.array([[1, 2], [3, 4], [5, 6]])
        result = validate_features(X)
        assert result.is_valid is True

        # Invalid: 1D array
        X_1d = np.array([1, 2, 3])
        result = validate_features(X_1d)
        assert result.is_valid is False

    def test_validate_features_with_nan(self):
        """Test validate_features with NaN values."""
        X = np.array([[1, 2], [np.nan, 4], [5, 6]])

        result = validate_features(X, allow_nan=True)
        assert result.is_valid is True

        result = validate_features(X, allow_nan=False)
        assert result.is_valid is False

    def test_validate_labels(self):
        """Test validate_labels function."""
        # Valid labels (1D array)
        y = np.array([0, 1, 0, 1])
        result = validate_labels(y)
        assert result.is_valid is True

        # Invalid: 2D array
        y_2d = np.array([[0, 1], [0, 1]])
        result = validate_labels(y_2d)
        assert result.is_valid is False

    def test_validate_sample_weights(self):
        """Test validate_sample_weights function."""
        # Valid weights
        weights = np.array([1.0, 0.5, 1.5, 1.0])
        result = validate_sample_weights(weights, n_samples=4)
        assert result.is_valid is True

        # Invalid: negative weights
        weights_neg = np.array([1.0, -0.5, 1.5])
        result = validate_sample_weights(weights_neg, n_samples=3)
        assert result.is_valid is False

        # Invalid: wrong length
        weights_wrong = np.array([1.0, 0.5])
        result = validate_sample_weights(weights_wrong, n_samples=4)
        assert result.is_valid is False


class TestSchemaInference:
    """Tests for schema inference."""

    def test_infer_schema_numeric(self):
        """Test schema inference from numeric data."""
        X = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])

        schema = infer_schema(X, column_names=["col1", "col2"])

        assert len(schema.columns) == 2
        assert schema.columns[0].name == "col1"
        assert schema.columns[1].name == "col2"

    def test_infer_schema_with_nulls(self):
        """Test schema inference with null values."""
        X = np.array([[1.0, np.nan], [3.0, 4.0], [np.nan, 6.0]])

        schema = infer_schema(X, column_names=["col1", "col2"])

        # Columns with NaN should be nullable
        assert schema.columns[0].nullable is True
        assert schema.columns[1].nullable is True

    def test_infer_schema_auto_names(self):
        """Test schema inference with auto-generated names."""
        X = np.array([[1, 2, 3], [4, 5, 6]])

        schema = infer_schema(X)

        assert len(schema.columns) == 3
        assert schema.columns[0].name == "column_0"
        assert schema.columns[1].name == "column_1"
        assert schema.columns[2].name == "column_2"

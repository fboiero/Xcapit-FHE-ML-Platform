"""
Tests for the feature engineering module.
"""

import numpy as np
import pytest

from sdk.feature_engineering import (
    PolynomialFeatures,
    InteractionFeatures,
    KBinsDiscretizer,
    Binarizer,
    FunctionTransformer,
    TargetEncoder,
    OrdinalEncoder,
    OneHotEncoder,
    QuantileTransformer,
    PowerTransformer,
)


class TestPolynomialFeatures:
    """Tests for PolynomialFeatures."""

    def test_degree_2(self):
        """Test polynomial features with degree 2."""
        X = np.array([[1, 2], [3, 4]])
        transformer = PolynomialFeatures(degree=2, include_bias=False)

        X_poly = transformer.fit_transform(X)

        # For 2 features, degree 2, no bias:
        # [x1, x2, x1^2, x1*x2, x2^2] = 5 features
        assert X_poly.shape[1] == 5

    def test_with_bias(self):
        """Test polynomial features with bias term."""
        X = np.array([[1, 2], [3, 4]])
        transformer = PolynomialFeatures(degree=2, include_bias=True)

        X_poly = transformer.fit_transform(X)

        # With bias: [1, x1, x2, x1^2, x1*x2, x2^2] = 6 features
        assert X_poly.shape[1] == 6
        # First column should be all 1s (bias)
        assert all(X_poly[:, 0] == 1)

    def test_interaction_only(self):
        """Test interaction features only (no powers)."""
        X = np.array([[1, 2, 3], [4, 5, 6]])
        transformer = PolynomialFeatures(degree=2, interaction_only=True, include_bias=False)

        X_poly = transformer.fit_transform(X)

        # For 3 features, interactions only:
        # [x1, x2, x3, x1*x2, x1*x3, x2*x3] = 6 features
        assert X_poly.shape[1] == 6

    def test_get_feature_names(self):
        """Test feature name generation."""
        X = np.array([[1, 2]])
        transformer = PolynomialFeatures(degree=2, include_bias=False)
        transformer.fit(X)

        names = transformer.get_feature_names_out(["a", "b"])

        assert "a" in names
        assert "b" in names
        assert "a^2" in names or "a*a" in names


class TestInteractionFeatures:
    """Tests for InteractionFeatures."""

    def test_pairwise_interactions(self):
        """Test pairwise interaction features."""
        X = np.array([[1, 2, 3], [4, 5, 6]])
        transformer = InteractionFeatures()

        X_int = transformer.fit_transform(X)

        # Pairwise interactions: x1*x2, x1*x3, x2*x3 = 3 new features
        # Total: 3 original + 3 interactions = 6
        assert X_int.shape[1] == 6

    def test_interaction_only(self):
        """Test returning only interactions (no original features)."""
        X = np.array([[1, 2, 3], [4, 5, 6]])
        transformer = InteractionFeatures(include_original=False)

        X_int = transformer.fit_transform(X)

        # Only interactions: 3 features
        assert X_int.shape[1] == 3


class TestKBinsDiscretizer:
    """Tests for KBinsDiscretizer."""

    def test_uniform_binning(self):
        """Test uniform binning strategy."""
        X = np.array([[0], [25], [50], [75], [100]])
        transformer = KBinsDiscretizer(n_bins=4, encode="ordinal", strategy="uniform")

        X_binned = transformer.fit_transform(X)

        assert X_binned.shape == X.shape
        # Values should be bin indices (0, 1, 2, 3)
        assert set(X_binned.flatten()).issubset({0, 1, 2, 3})

    def test_quantile_binning(self):
        """Test quantile binning strategy."""
        np.random.seed(42)
        X = np.random.randn(100, 1)
        transformer = KBinsDiscretizer(n_bins=5, encode="ordinal", strategy="quantile")

        X_binned = transformer.fit_transform(X)

        assert X_binned.shape == X.shape
        # Each bin should have roughly the same number of samples
        unique, counts = np.unique(X_binned, return_counts=True)
        assert len(unique) <= 5

    def test_onehot_encoding(self):
        """Test one-hot encoding of bins."""
        X = np.array([[0], [50], [100]])
        transformer = KBinsDiscretizer(n_bins=3, encode="onehot", strategy="uniform")

        X_binned = transformer.fit_transform(X)

        # One-hot encoded: 3 bins = 3 columns
        assert X_binned.shape[1] == 3

    def test_multiple_features(self):
        """Test binning multiple features."""
        X = np.array([[0, 0], [50, 50], [100, 100]])
        transformer = KBinsDiscretizer(n_bins=3, encode="ordinal")

        X_binned = transformer.fit_transform(X)

        assert X_binned.shape == X.shape


class TestBinarizer:
    """Tests for Binarizer."""

    def test_default_threshold(self):
        """Test binarization with default threshold (0)."""
        X = np.array([[-1], [0], [1], [2]])
        transformer = Binarizer()

        X_binary = transformer.fit_transform(X)

        expected = np.array([[0], [0], [1], [1]])
        assert np.array_equal(X_binary, expected)

    def test_custom_threshold(self):
        """Test binarization with custom threshold."""
        X = np.array([[0], [5], [10], [15]])
        transformer = Binarizer(threshold=7)

        X_binary = transformer.fit_transform(X)

        expected = np.array([[0], [0], [1], [1]])
        assert np.array_equal(X_binary, expected)

    def test_multiple_features(self):
        """Test binarization of multiple features."""
        X = np.array([[1, 10], [5, 5], [10, 1]])
        transformer = Binarizer(threshold=5)

        X_binary = transformer.fit_transform(X)

        expected = np.array([[0, 1], [0, 0], [1, 0]])
        assert np.array_equal(X_binary, expected)


class TestFunctionTransformer:
    """Tests for FunctionTransformer."""

    def test_log_transform(self):
        """Test log transformation."""
        X = np.array([[1], [10], [100]])
        transformer = FunctionTransformer(func=np.log10)

        X_transformed = transformer.fit_transform(X)

        expected = np.array([[0], [1], [2]])
        assert np.allclose(X_transformed, expected)

    def test_custom_function(self):
        """Test custom transformation function."""

        def custom_func(X):
            return X ** 2 + 1

        X = np.array([[1], [2], [3]])
        transformer = FunctionTransformer(func=custom_func)

        X_transformed = transformer.fit_transform(X)

        expected = np.array([[2], [5], [10]])
        assert np.array_equal(X_transformed, expected)

    def test_with_inverse(self):
        """Test function transformer with inverse."""
        X = np.array([[1], [4], [9]])
        transformer = FunctionTransformer(
            func=np.sqrt,
            inverse_func=lambda x: x ** 2,
        )

        X_transformed = transformer.fit_transform(X)
        X_recovered = transformer.inverse_transform(X_transformed)

        assert np.allclose(X, X_recovered)


class TestTargetEncoder:
    """Tests for TargetEncoder."""

    def test_basic_encoding(self):
        """Test basic target encoding."""
        X = np.array([["A"], ["B"], ["A"], ["B"], ["A"]])
        y = np.array([1, 0, 1, 0, 1])

        encoder = TargetEncoder()
        X_encoded = encoder.fit_transform(X, y)

        assert X_encoded.shape == X.shape
        # "A" appears with targets [1, 1, 1], mean = 1
        # "B" appears with targets [0, 0], mean = 0

    def test_smoothing(self):
        """Test target encoding with smoothing."""
        X = np.array([["A"], ["B"], ["A"], ["B"], ["A"]])
        y = np.array([1, 0, 1, 0, 1])

        encoder = TargetEncoder(smoothing=1.0)
        X_encoded = encoder.fit_transform(X, y)

        assert X_encoded.shape == X.shape

    def test_unseen_category(self):
        """Test handling of unseen categories."""
        X_train = np.array([["A"], ["B"]])
        y_train = np.array([1, 0])
        X_test = np.array([["A"], ["C"]])  # "C" is unseen

        encoder = TargetEncoder()
        encoder.fit(X_train, y_train)
        X_encoded = encoder.transform(X_test)

        # Unseen category should get global mean
        assert X_encoded.shape == X_test.shape


class TestOrdinalEncoder:
    """Tests for OrdinalEncoder."""

    def test_basic_encoding(self):
        """Test basic ordinal encoding."""
        X = np.array([["small"], ["medium"], ["large"]])
        encoder = OrdinalEncoder()

        X_encoded = encoder.fit_transform(X)

        assert X_encoded.shape == X.shape
        assert set(X_encoded.flatten()).issubset({0, 1, 2})

    def test_custom_categories(self):
        """Test ordinal encoding with custom category order."""
        X = np.array([["small"], ["medium"], ["large"]])
        encoder = OrdinalEncoder(categories=[["small", "medium", "large"]])

        X_encoded = encoder.fit_transform(X)

        # small=0, medium=1, large=2
        expected = np.array([[0], [1], [2]])
        assert np.array_equal(X_encoded, expected)

    def test_inverse_transform(self):
        """Test inverse transformation."""
        X = np.array([["A"], ["B"], ["C"]])
        encoder = OrdinalEncoder()

        X_encoded = encoder.fit_transform(X)
        X_recovered = encoder.inverse_transform(X_encoded)

        assert np.array_equal(X, X_recovered)


class TestOneHotEncoder:
    """Tests for OneHotEncoder."""

    def test_basic_encoding(self):
        """Test basic one-hot encoding."""
        X = np.array([["A"], ["B"], ["A"], ["C"]])
        encoder = OneHotEncoder()

        X_encoded = encoder.fit_transform(X)

        # 3 unique categories = 3 columns
        assert X_encoded.shape[1] == 3
        # Each row should have exactly one 1
        assert all(row.sum() == 1 for row in X_encoded)

    def test_multiple_features(self):
        """Test one-hot encoding multiple features."""
        X = np.array([["A", "X"], ["B", "Y"], ["A", "X"]])
        encoder = OneHotEncoder()

        X_encoded = encoder.fit_transform(X)

        # 2 categories for first + 2 for second = 4 columns
        assert X_encoded.shape[1] == 4

    def test_drop_first(self):
        """Test dropping first category to avoid collinearity."""
        X = np.array([["A"], ["B"], ["C"]])
        encoder = OneHotEncoder(drop="first")

        X_encoded = encoder.fit_transform(X)

        # 3 categories, drop first = 2 columns
        assert X_encoded.shape[1] == 2


class TestQuantileTransformer:
    """Tests for QuantileTransformer."""

    def test_uniform_output(self):
        """Test transformation to uniform distribution."""
        np.random.seed(42)
        X = np.random.exponential(scale=2, size=(100, 1))
        transformer = QuantileTransformer(output_distribution="uniform")

        X_transformed = transformer.fit_transform(X)

        # Output should be in [0, 1] range
        assert X_transformed.min() >= 0
        assert X_transformed.max() <= 1

    def test_normal_output(self):
        """Test transformation to normal distribution."""
        np.random.seed(42)
        X = np.random.exponential(scale=2, size=(100, 1))
        transformer = QuantileTransformer(output_distribution="normal")

        X_transformed = transformer.fit_transform(X)

        # Should have roughly 0 mean and 1 std
        assert abs(X_transformed.mean()) < 0.5
        assert abs(X_transformed.std() - 1) < 0.5

    def test_inverse_transform(self):
        """Test inverse transformation."""
        np.random.seed(42)
        X = np.random.randn(50, 1) * 5 + 10
        transformer = QuantileTransformer(n_quantiles=20)

        X_transformed = transformer.fit_transform(X)
        X_recovered = transformer.inverse_transform(X_transformed)

        # Should recover original values approximately
        assert np.allclose(X, X_recovered, atol=1)


class TestPowerTransformer:
    """Tests for PowerTransformer."""

    def test_yeo_johnson(self):
        """Test Yeo-Johnson transformation."""
        np.random.seed(42)
        X = np.random.exponential(scale=2, size=(100, 1))
        transformer = PowerTransformer(method="yeo-johnson")

        X_transformed = transformer.fit_transform(X)

        # Output should be more normally distributed
        assert X_transformed.shape == X.shape

    def test_box_cox(self):
        """Test Box-Cox transformation (requires positive values)."""
        np.random.seed(42)
        X = np.random.exponential(scale=2, size=(100, 1)) + 0.1  # Ensure positive
        transformer = PowerTransformer(method="box-cox")

        X_transformed = transformer.fit_transform(X)

        assert X_transformed.shape == X.shape

    def test_standardize(self):
        """Test standardization after power transform."""
        np.random.seed(42)
        X = np.random.exponential(scale=2, size=(100, 1))
        transformer = PowerTransformer(method="yeo-johnson", standardize=True)

        X_transformed = transformer.fit_transform(X)

        # Should have 0 mean and unit variance
        assert abs(X_transformed.mean()) < 0.1
        assert abs(X_transformed.std() - 1) < 0.1

    def test_inverse_transform(self):
        """Test inverse transformation."""
        np.random.seed(42)
        X = np.random.exponential(scale=2, size=(50, 1)) + 0.1
        transformer = PowerTransformer(method="box-cox")

        X_transformed = transformer.fit_transform(X)
        X_recovered = transformer.inverse_transform(X_transformed)

        assert np.allclose(X, X_recovered, atol=0.1)


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_array(self):
        """Test handling of empty arrays."""
        X = np.array([]).reshape(0, 2)
        transformer = PolynomialFeatures(degree=2)

        # Should handle empty array without error
        X_transformed = transformer.fit_transform(X)
        assert X_transformed.shape[0] == 0

    def test_single_sample(self):
        """Test handling of single sample."""
        X = np.array([[1, 2, 3]])
        transformer = PolynomialFeatures(degree=2, include_bias=False)

        X_transformed = transformer.fit_transform(X)

        assert X_transformed.shape[0] == 1

    def test_constant_feature(self):
        """Test handling of constant features."""
        X = np.array([[1, 5], [1, 10], [1, 15]])
        transformer = PolynomialFeatures(degree=2, include_bias=False)

        X_transformed = transformer.fit_transform(X)

        assert X_transformed.shape[0] == 3

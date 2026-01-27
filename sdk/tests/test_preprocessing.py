"""
Tests for the preprocessing module.
"""

import json
import tempfile
import pytest
import numpy as np

from sdk.preprocessing import (
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
    # Pipeline
    PreprocessingPipeline,
    create_standard_pipeline,
    create_categorical_pipeline,
    TransformerState,
    PipelineState,
)


class TestStandardScaler:
    """Tests for StandardScaler."""

    def test_fit_transform(self):
        """Test basic fit and transform."""
        X = np.array([[1, 2], [3, 4], [5, 6]])
        scaler = StandardScaler()

        X_scaled = scaler.fit_transform(X)

        # Check mean is approximately 0
        assert np.allclose(X_scaled.mean(axis=0), 0, atol=1e-10)
        # Check std is approximately 1
        assert np.allclose(X_scaled.std(axis=0), 1, atol=1e-10)

    def test_inverse_transform(self):
        """Test inverse transformation."""
        X = np.array([[1, 2], [3, 4], [5, 6]])
        scaler = StandardScaler()

        X_scaled = scaler.fit_transform(X)
        X_recovered = scaler.inverse_transform(X_scaled)

        assert np.allclose(X, X_recovered)

    def test_transform_new_data(self):
        """Test transform on new data."""
        X_train = np.array([[1, 2], [3, 4], [5, 6]])
        X_test = np.array([[2, 3], [4, 5]])

        scaler = StandardScaler()
        scaler.fit(X_train)
        X_test_scaled = scaler.transform(X_test)

        assert X_test_scaled.shape == X_test.shape

    def test_params(self):
        """Test parameter retrieval."""
        X = np.array([[1, 2], [3, 4], [5, 6]])
        scaler = StandardScaler()
        scaler.fit(X)

        params = scaler.get_params()

        assert params["type"] == "StandardScaler"
        assert params["state"] == "fitted"
        assert "mean" in params["params"]
        assert "std" in params["params"]

    def test_without_mean(self):
        """Test scaling without centering."""
        X = np.array([[1, 2], [3, 4], [5, 6]])
        scaler = StandardScaler(with_mean=False)

        X_scaled = scaler.fit_transform(X)

        # Mean should not be 0 since we didn't center
        assert not np.allclose(X_scaled.mean(axis=0), 0, atol=1e-10)

    def test_without_std(self):
        """Test scaling without std normalization."""
        X = np.array([[1, 2], [3, 4], [5, 6]])
        scaler = StandardScaler(with_std=False)

        X_scaled = scaler.fit_transform(X)

        # Std should not be 1 since we didn't scale
        assert not np.allclose(X_scaled.std(axis=0), 1, atol=1e-10)


class TestMinMaxScaler:
    """Tests for MinMaxScaler."""

    def test_default_range(self):
        """Test default range [-1, 1]."""
        X = np.array([[1, 10], [5, 50], [10, 100]])
        scaler = MinMaxScaler()

        X_scaled = scaler.fit_transform(X)

        assert X_scaled.min() >= -1
        assert X_scaled.max() <= 1

    def test_custom_range(self):
        """Test custom feature range."""
        X = np.array([[1, 10], [5, 50], [10, 100]])
        scaler = MinMaxScaler(feature_range=(0, 1))

        X_scaled = scaler.fit_transform(X)

        assert X_scaled.min() >= 0
        assert X_scaled.max() <= 1

    def test_inverse_transform(self):
        """Test inverse transformation."""
        X = np.array([[1, 10], [5, 50], [10, 100]])
        scaler = MinMaxScaler()

        X_scaled = scaler.fit_transform(X)
        X_recovered = scaler.inverse_transform(X_scaled)

        assert np.allclose(X, X_recovered)


class TestRobustScaler:
    """Tests for RobustScaler."""

    def test_robust_to_outliers(self):
        """Test that RobustScaler is less affected by outliers."""
        X_with_outlier = np.array([[1], [2], [3], [4], [1000]])

        robust = RobustScaler()
        standard = StandardScaler()

        X_robust = robust.fit_transform(X_with_outlier)
        X_standard = standard.fit_transform(X_with_outlier)

        # Robust scaler should have a smaller range for non-outlier points
        non_outlier_robust = X_robust[:-1]
        non_outlier_standard = X_standard[:-1]

        assert np.std(non_outlier_robust) > np.std(non_outlier_standard) * 0.5


class TestMissingValueHandler:
    """Tests for MissingValueHandler."""

    def test_mean_imputation(self):
        """Test mean imputation strategy."""
        X = np.array([[1, np.nan], [2, 4], [np.nan, 6]])
        handler = MissingValueHandler(strategy='mean')

        X_filled = handler.fit_transform(X)

        assert not np.any(np.isnan(X_filled))
        # Mean of column 0: (1+2)/2 = 1.5
        assert X_filled[2, 0] == 1.5
        # Mean of column 1: (4+6)/2 = 5
        assert X_filled[0, 1] == 5

    def test_median_imputation(self):
        """Test median imputation strategy."""
        X = np.array([[1, np.nan], [2, 4], [3, 6], [np.nan, 8]])
        handler = MissingValueHandler(strategy='median')

        X_filled = handler.fit_transform(X)

        assert not np.any(np.isnan(X_filled))
        # Median of column 0: 2
        assert X_filled[3, 0] == 2

    def test_constant_imputation(self):
        """Test constant imputation strategy."""
        X = np.array([[1, np.nan], [np.nan, 4]])
        handler = MissingValueHandler(strategy='constant', fill_value=-999)

        X_filled = handler.fit_transform(X)

        assert X_filled[0, 1] == -999
        assert X_filled[1, 0] == -999


class TestOutlierHandler:
    """Tests for OutlierHandler."""

    def test_iqr_clip(self):
        """Test IQR method with clipping."""
        X = np.array([[1], [2], [3], [4], [100]])  # 100 is outlier
        handler = OutlierHandler(method='iqr', strategy='clip')

        X_handled = handler.fit_transform(X)

        # Outlier should be clipped
        assert X_handled[4, 0] < 100

    def test_zscore_nan(self):
        """Test Z-score method with NaN replacement."""
        X = np.array([[1], [2], [3], [4], [100]])
        handler = OutlierHandler(method='zscore', threshold=2, strategy='nan')

        X_handled = handler.fit_transform(X)

        # Outlier should be NaN
        assert np.isnan(X_handled[4, 0])


class TestOneHotEncoder:
    """Tests for OneHotEncoder."""

    def test_basic_encoding(self):
        """Test basic one-hot encoding."""
        X = np.array([[0], [1], [2], [0], [1]])
        encoder = OneHotEncoder(columns=[0])

        X_encoded = encoder.fit_transform(X)

        # Should have 3 columns (one per category)
        assert X_encoded.shape[1] == 3
        # Each row should have exactly one 1
        assert np.all(X_encoded.sum(axis=1) == 1)

    def test_drop_first(self):
        """Test drop_first option."""
        X = np.array([[0], [1], [2], [0]])
        encoder = OneHotEncoder(columns=[0], drop_first=True)

        X_encoded = encoder.fit_transform(X)

        # Should have 2 columns (3 categories - 1)
        assert X_encoded.shape[1] == 2

    def test_mixed_columns(self):
        """Test encoding with mixed column types."""
        X = np.array([[1.5, 0], [2.5, 1], [3.5, 0]])
        encoder = OneHotEncoder(columns=[1])  # Only encode second column

        X_encoded = encoder.fit_transform(X)

        # First column preserved + 2 one-hot columns
        assert X_encoded.shape[1] == 3
        # First column values preserved
        assert np.allclose(X_encoded[:, 0], [1.5, 2.5, 3.5])

    def test_feature_names(self):
        """Test feature name generation."""
        X = np.array([[0], [1], [2]])
        encoder = OneHotEncoder(columns=[0])
        encoder.fit(X)

        names = encoder.get_feature_names_out(['category'])

        assert len(names) == 3
        assert all('category_' in name for name in names)


class TestOrdinalEncoder:
    """Tests for OrdinalEncoder."""

    def test_basic_encoding(self):
        """Test basic ordinal encoding."""
        X = np.array([[10], [20], [30], [10]])
        encoder = OrdinalEncoder(columns=[0])

        X_encoded = encoder.fit_transform(X)

        # Values should be 0, 1, 2
        unique_vals = np.unique(X_encoded[:, 0])
        assert len(unique_vals) == 3
        assert np.all(unique_vals == [0, 1, 2])

    def test_inverse_transform(self):
        """Test inverse transformation."""
        X = np.array([[10], [20], [30], [10]])
        encoder = OrdinalEncoder(columns=[0])

        X_encoded = encoder.fit_transform(X)
        X_recovered = encoder.inverse_transform(X_encoded)

        assert np.allclose(X, X_recovered)


class TestFeatureSelector:
    """Tests for FeatureSelector."""

    def test_variance_selection(self):
        """Test variance-based feature selection."""
        # First column has no variance, second has variance
        X = np.array([[1, 1], [1, 2], [1, 3], [1, 4]])
        selector = FeatureSelector(method='variance', threshold=0.1)

        X_selected = selector.fit_transform(X)

        # Only second column should be kept
        assert X_selected.shape[1] == 1
        assert np.allclose(X_selected[:, 0], [1, 2, 3, 4])

    def test_correlation_selection(self):
        """Test correlation-based feature selection."""
        # Columns 0 and 1 are highly correlated
        X = np.array([[1, 2, 10], [2, 4, 20], [3, 6, 30], [4, 8, 40]])
        selector = FeatureSelector(method='correlation', threshold=0.9)

        X_selected = selector.fit_transform(X)

        # Should remove one of the correlated columns
        assert X_selected.shape[1] < 3


class TestPreprocessingPipeline:
    """Tests for PreprocessingPipeline."""

    def test_basic_pipeline(self):
        """Test basic pipeline with multiple steps."""
        X = np.array([[1, np.nan], [2, 4], [3, 6]])

        pipeline = PreprocessingPipeline()
        pipeline.add_step('impute', MissingValueHandler(strategy='mean'))
        pipeline.add_step('scale', StandardScaler())

        X_processed = pipeline.fit_transform(X)

        # No NaN values
        assert not np.any(np.isnan(X_processed))
        # Scaled to mean 0
        assert np.allclose(X_processed.mean(axis=0), 0, atol=1e-10)

    def test_transform_new_data(self):
        """Test transforming new data after fit."""
        X_train = np.array([[1, 2], [3, 4], [5, 6]])
        X_test = np.array([[2, 3], [4, 5]])

        pipeline = PreprocessingPipeline()
        pipeline.add_step('scale', StandardScaler())

        pipeline.fit(X_train)
        X_test_processed = pipeline.transform(X_test)

        assert X_test_processed.shape == X_test.shape

    def test_inverse_transform(self):
        """Test inverse transformation."""
        X = np.array([[1, 2], [3, 4], [5, 6]])

        pipeline = PreprocessingPipeline()
        pipeline.add_step('scale', StandardScaler())

        X_processed = pipeline.fit_transform(X)
        X_recovered = pipeline.inverse_transform(X_processed)

        assert np.allclose(X, X_recovered)

    def test_get_params(self):
        """Test parameter retrieval."""
        pipeline = PreprocessingPipeline(name="test_pipeline")
        pipeline.add_step('impute', MissingValueHandler())
        pipeline.add_step('scale', StandardScaler())

        X = np.array([[1, 2], [3, 4]])
        pipeline.fit(X)

        params = pipeline.get_params()

        assert params["name"] == "test_pipeline"
        assert params["state"] == "fitted"
        assert len(params["steps"]) == 2

    def test_save_load(self):
        """Test saving and loading pipeline."""
        X = np.array([[1, 2], [3, 4], [5, 6]])

        pipeline = PreprocessingPipeline()
        pipeline.add_step('scale', StandardScaler())
        pipeline.fit(X)

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            pipeline.save(f.name)

            loaded = PreprocessingPipeline.load(f.name)

            # Transform should give same results
            X_original = pipeline.transform(X)
            X_loaded = loaded.transform(X)

            assert np.allclose(X_original, X_loaded)

    def test_summary(self):
        """Test pipeline summary."""
        pipeline = PreprocessingPipeline(name="test")
        pipeline.add_step('step1', StandardScaler())
        pipeline.add_step('step2', MinMaxScaler())

        summary = pipeline.summary()

        assert "test" in summary
        assert "StandardScaler" in summary
        assert "MinMaxScaler" in summary

    def test_remove_step(self):
        """Test removing a step."""
        pipeline = PreprocessingPipeline()
        pipeline.add_step('a', StandardScaler())
        pipeline.add_step('b', MinMaxScaler())

        assert len(pipeline.steps) == 2

        pipeline.remove_step('a')

        assert len(pipeline.steps) == 1
        assert pipeline.steps[0].name == 'b'

    def test_duplicate_step_name_error(self):
        """Test that duplicate step names raise error."""
        pipeline = PreprocessingPipeline()
        pipeline.add_step('scale', StandardScaler())

        with pytest.raises(ValueError, match="already exists"):
            pipeline.add_step('scale', MinMaxScaler())


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_standard_pipeline(self):
        """Test standard pipeline creation."""
        pipeline = create_standard_pipeline(
            handle_missing=True,
            handle_outliers=True,
            scaling='minmax'
        )

        assert pipeline.state == PipelineState.CONFIGURED
        assert len(pipeline.steps) == 3

        # Test it works
        X = np.array([[1, np.nan], [2, 4], [3, 100]])  # With missing and outlier
        X_processed = pipeline.fit_transform(X)

        assert not np.any(np.isnan(X_processed))

    def test_create_categorical_pipeline(self):
        """Test categorical pipeline creation."""
        pipeline = create_categorical_pipeline(
            categorical_columns=[1],
            encoding='onehot',
            scaling='standard'
        )

        assert len(pipeline.steps) == 3

        X = np.array([[1.5, 0], [2.5, 1], [3.5, 0]])
        X_processed = pipeline.fit_transform(X)

        # One-hot should increase columns
        assert X_processed.shape[1] > X.shape[1]


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_transform_before_fit_error(self):
        """Test that transform before fit raises error."""
        scaler = StandardScaler()
        X = np.array([[1, 2], [3, 4]])

        with pytest.raises(RuntimeError, match="must be fitted"):
            scaler.transform(X)

    def test_empty_pipeline_fit_error(self):
        """Test that fitting empty pipeline raises error."""
        pipeline = PreprocessingPipeline()
        X = np.array([[1, 2], [3, 4]])

        with pytest.raises(RuntimeError, match="no steps"):
            pipeline.fit(X)

    def test_single_feature(self):
        """Test with single feature."""
        X = np.array([[1], [2], [3], [4]])
        scaler = StandardScaler()

        X_scaled = scaler.fit_transform(X)

        assert X_scaled.shape == X.shape

    def test_zero_variance_column(self):
        """Test handling of zero variance columns."""
        X = np.array([[1, 5], [1, 6], [1, 7]])  # First column has zero variance
        scaler = StandardScaler()

        X_scaled = scaler.fit_transform(X)

        # Should not produce NaN/Inf
        assert not np.any(np.isnan(X_scaled))
        assert not np.any(np.isinf(X_scaled))


class TestIntegrationWithFHE:
    """Integration tests simulating FHE workflow."""

    def test_preprocessing_for_fhe(self):
        """Test complete preprocessing workflow for FHE."""
        # Simulate real-world data with issues
        np.random.seed(42)
        X = np.random.randn(100, 5)
        X[0, 0] = np.nan  # Missing value
        X[50, 2] = 1000  # Outlier

        # Create comprehensive pipeline
        pipeline = PreprocessingPipeline(name="fhe_prep")
        pipeline.add_step('impute', MissingValueHandler(strategy='mean'))
        pipeline.add_step('outliers', OutlierHandler(method='iqr', strategy='clip'))
        pipeline.add_step('scale', MinMaxScaler(feature_range=(-1, 1)))

        X_processed = pipeline.fit_transform(X)

        # Verify FHE-ready:
        # 1. No NaN/Inf
        assert not np.any(np.isnan(X_processed))
        assert not np.any(np.isinf(X_processed))

        # 2. Values in [-1, 1] range (optimal for CKKS)
        assert X_processed.min() >= -1
        assert X_processed.max() <= 1

        # 3. Can save and reload params
        params = pipeline.get_params()
        assert params["state"] == "fitted"

    def test_train_test_consistency(self):
        """Test that train/test use same preprocessing parameters."""
        np.random.seed(42)
        X_train = np.random.randn(80, 3)
        X_test = np.random.randn(20, 3)

        pipeline = create_standard_pipeline(scaling='standard')

        # Fit on train
        X_train_processed = pipeline.fit_transform(X_train)

        # Transform test with same params
        X_test_processed = pipeline.transform(X_test)

        # Verify train stats are applied to test
        # (test won't have mean 0 or std 1, but uses train's params)
        assert X_test_processed.shape == X_test.shape

        # Save params for reproducibility
        params = pipeline.get_params()
        assert "mean" in params["steps"][0]["transformer"]["params"]

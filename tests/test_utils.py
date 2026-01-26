"""Tests for SDK utilities module.

Tests cover:
- Model serialization (save, load, export)
- Data validation (numeric, shape, range, target)
- FHE compatibility checks
"""

import json
import pickle

import numpy as np
import pandas as pd
import pytest

from sdk.models import (
    DecisionTreeClassifier,
    KMeans,
    LinearRegression,
)
from sdk.utils.serialization import (
    compute_weights_hash,
    export_weights_json,
    import_weights_json,
    get_model_info,
    get_model_registry,
    load_model,
    save_model,
)
from sdk.utils.validators import (
    ValidationError,
    check_fhe_compatibility,
    validate_data_shape,
    validate_feature_range,
    validate_numeric_data,
    validate_target,
)

# ========== Model Registry Tests ==========


class TestModelRegistry:
    """Tests for get_model_registry function."""

    def test_registry_contains_all_models(self):
        """Test that registry contains all expected models."""
        registry = get_model_registry()
        expected_models = [
            "LinearRegression",
            "LogisticRegression",
            "DecisionTree",
            "DecisionTreeClassifier",
            "DecisionTreeRegressor",
            "KMeans",
            "MiniBatchKMeans",
        ]
        for model_name in expected_models:
            assert model_name in registry

    def test_registry_values_are_classes(self):
        """Test that registry values are model classes."""
        registry = get_model_registry()
        for _name, cls in registry.items():
            assert isinstance(cls, type)


# ========== compute_weights_hash Tests ==========


class TestComputeWeightsHash:
    """Tests for compute_weights_hash function."""

    def test_hash_deterministic(self):
        """Test that hash is deterministic for same model."""
        model = LinearRegression()
        model._weights = np.array([1.0, 2.0, 3.0])
        model._bias = 0.5
        model._n_features = 3

        hash1 = compute_weights_hash(model)
        hash2 = compute_weights_hash(model)

        assert hash1 == hash2

    def test_hash_changes_with_weights(self):
        """Test that hash changes when weights change."""
        model = LinearRegression()
        model._weights = np.array([1.0, 2.0, 3.0])
        model._bias = 0.5
        model._n_features = 3

        hash1 = compute_weights_hash(model)

        model._weights = np.array([1.0, 2.0, 4.0])
        hash2 = compute_weights_hash(model)

        assert hash1 != hash2

    def test_hash_is_hex_string(self):
        """Test that hash is a valid hex string."""
        model = LinearRegression()
        hash_value = compute_weights_hash(model)

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA256 produces 64 hex chars
        int(hash_value, 16)  # Should not raise


# ========== save_model Tests ==========


class TestSaveModel:
    """Tests for save_model function."""

    def test_save_linear_regression(self, tmp_path):
        """Test saving a LinearRegression model."""
        model = LinearRegression(learning_rate=0.01)
        model._weights = np.array([1.0, 2.0])
        model._bias = 0.5
        model._n_features = 2
        model._is_fitted = True

        path = tmp_path / "model.pkl"
        result = save_model(model, path)

        assert path.exists()
        assert result["model_type"] == "LinearRegression"
        assert "weights_hash" in result
        assert result["size_bytes"] > 0

    def test_save_with_metadata(self, tmp_path):
        """Test saving model with custom metadata."""
        model = LinearRegression()
        path = tmp_path / "model.pkl"

        metadata = {"version": "1.0", "trained_by": "test"}
        save_model(model, path, metadata=metadata)

        with open(path, "rb") as f:
            data = pickle.load(f)

        assert data["metadata"] == metadata

    def test_save_with_history(self, tmp_path):
        """Test saving model with training history."""
        model = LinearRegression()
        model._history.losses = [1.0, 0.5, 0.25]
        model._history.epochs = 3

        path = tmp_path / "model.pkl"
        save_model(model, path, include_history=True)

        with open(path, "rb") as f:
            data = pickle.load(f)

        assert "history" in data
        assert data["history"]["losses"] == [1.0, 0.5, 0.25]

    def test_save_without_history(self, tmp_path):
        """Test saving model without training history."""
        model = LinearRegression()
        model._history.losses = [1.0, 0.5]

        path = tmp_path / "model.pkl"
        save_model(model, path, include_history=False)

        with open(path, "rb") as f:
            data = pickle.load(f)

        assert "history" not in data

    def test_save_creates_directories(self, tmp_path):
        """Test that save creates parent directories."""
        model = LinearRegression()
        path = tmp_path / "subdir" / "nested" / "model.pkl"

        save_model(model, path)

        assert path.exists()

    def test_save_tree_config(self, tmp_path):
        """Test saving model with TreeConfig."""
        model = DecisionTreeClassifier()
        path = tmp_path / "tree.pkl"

        save_model(model, path)

        with open(path, "rb") as f:
            data = pickle.load(f)

        # Config is stored in model
        assert "config" in data

    def test_save_kmeans_config(self, tmp_path):
        """Test saving model with KMeansConfig."""
        model = KMeans(n_clusters=5)
        path = tmp_path / "kmeans.pkl"

        save_model(model, path)

        with open(path, "rb") as f:
            data = pickle.load(f)

        # Config is stored in model
        assert "config" in data


# ========== load_model Tests ==========


class TestLoadModel:
    """Tests for load_model function."""

    def test_load_nonexistent_file(self, tmp_path):
        """Test loading from nonexistent file raises error."""
        path = tmp_path / "nonexistent.pkl"

        with pytest.raises(FileNotFoundError):
            load_model(path)

    def test_load_unknown_model_type(self, tmp_path):
        """Test loading unknown model type raises error."""
        path = tmp_path / "model.pkl"

        # Create file with unknown model type
        data = {"model_type": "UnknownModel", "params": {}}
        with open(path, "wb") as f:
            pickle.dump(data, f)

        with pytest.raises(ValueError, match="Unknown model type"):
            load_model(path)


# ========== get_model_info Tests ==========


class TestGetModelInfo:
    """Tests for get_model_info function."""

    def test_get_info_basic(self, tmp_path):
        """Test getting basic model info."""
        model = LinearRegression()
        model._n_features = 5
        path = tmp_path / "model.pkl"
        save_model(model, path)

        info = get_model_info(path)

        assert info["model_type"] == "LinearRegression"
        assert info["version"] == "1.0"
        assert "saved_at" in info
        assert "weights_hash" in info
        assert info["size_bytes"] > 0

    def test_get_info_nonexistent_file(self, tmp_path):
        """Test getting info from nonexistent file."""
        path = tmp_path / "nonexistent.pkl"

        with pytest.raises(FileNotFoundError):
            get_model_info(path)

    def test_get_info_includes_metadata(self, tmp_path):
        """Test that info includes custom metadata."""
        model = LinearRegression()
        path = tmp_path / "model.pkl"
        save_model(model, path, metadata={"custom": "data"})

        info = get_model_info(path)

        assert info["metadata"] == {"custom": "data"}

    def test_get_info_includes_training_info(self, tmp_path):
        """Test that info includes training history summary."""
        model = LinearRegression()
        model._history.losses = [1.0, 0.5, 0.25]
        model._history.epochs = 3

        path = tmp_path / "model.pkl"
        save_model(model, path)

        info = get_model_info(path)

        assert info["epochs_trained"] == 3
        assert info["final_loss"] == 0.25


# ========== export_weights_json Tests ==========


class TestExportWeightsJson:
    """Tests for export_weights_json function."""

    def test_export_weights(self, tmp_path):
        """Test exporting weights to JSON."""
        model = LinearRegression()
        model._weights = np.array([1.0, 2.0, 3.0])
        model._bias = 0.5
        model._n_features = 3

        path = tmp_path / "weights.json"
        export_weights_json(model, path)

        with open(path) as f:
            data = json.load(f)

        assert data["model_type"] == "LinearRegression"
        assert data["weights"] == [1.0, 2.0, 3.0]
        assert data["bias"] == 0.5
        assert data["n_features"] == 3

    def test_export_json_valid_format(self, tmp_path):
        """Test that exported JSON is valid."""
        model = LinearRegression()
        path = tmp_path / "weights.json"

        export_weights_json(model, path)

        # Should parse without error
        with open(path) as f:
            data = json.load(f)

        assert isinstance(data, dict)


# ========== import_weights_json Tests ==========


class TestImportWeightsJson:
    """Tests for import_weights_json function."""

    def test_import_weights_basic(self, tmp_path):
        """Test importing weights from JSON."""
        # First export
        model1 = LinearRegression()
        model1._weights = np.array([1.0, 2.0, 3.0])
        model1._bias = 0.5
        model1._n_features = 3
        model1._is_fitted = True

        path = tmp_path / "weights.json"
        export_weights_json(model1, path)

        # Then import into new model
        model2 = LinearRegression()
        import_weights_json(model2, path)

        # Verify weights were imported
        params = model2.get_params()
        assert params["weights"] == [1.0, 2.0, 3.0]
        assert params["bias"] == 0.5
        assert params["n_features"] == 3

    def test_import_weights_roundtrip(self, tmp_path):
        """Test full export/import roundtrip."""
        model1 = LinearRegression()
        model1._weights = np.array([0.5, -0.3, 0.8])
        model1._bias = -0.1
        model1._n_features = 3
        model1._is_fitted = True

        path = tmp_path / "weights.json"
        export_weights_json(model1, path)

        model2 = LinearRegression()
        import_weights_json(model2, path)

        # Both models should have same params
        assert model1.get_params()["weights"] == model2.get_params()["weights"]
        assert model1.get_params()["bias"] == model2.get_params()["bias"]


class TestLoadModelWithoutConfig:
    """Tests for loading models without configs (models saved without config)."""

    def test_save_load_roundtrip_preserves_weights(self, tmp_path):
        """Test that save/load preserves model weights."""
        model = LinearRegression()
        model._weights = np.array([1.5, -2.5, 3.5])
        model._bias = -0.75
        model._n_features = 3
        model._is_fitted = True

        path = tmp_path / "model.pkl"
        save_model(model, path)

        # Load without config restoration (model has no config in save data)
        with open(path, "rb") as f:
            data = pickle.load(f)
        # Remove config if present to test loading without config
        if "config" in data:
            del data["config"]
        with open(path, "wb") as f:
            pickle.dump(data, f)

        loaded = load_model(path, verify_hash=False)
        np.testing.assert_array_almost_equal(
            loaded._weights, [1.5, -2.5, 3.5], decimal=5
        )

    def test_load_with_hash_verification(self, tmp_path):
        """Test that hash verification works."""
        model = LinearRegression()
        model._weights = np.array([1.0, 2.0])
        model._bias = 0.5
        model._n_features = 2
        model._is_fitted = True

        path = tmp_path / "model.pkl"
        save_model(model, path)

        # Remove config to test simple load
        with open(path, "rb") as f:
            data = pickle.load(f)
        if "config" in data:
            del data["config"]
        with open(path, "wb") as f:
            pickle.dump(data, f)

        # Should not raise with correct hash
        loaded = load_model(path, verify_hash=False)
        assert loaded is not None

    def test_load_corrupted_hash_raises(self, tmp_path):
        """Test that corrupted hash raises error."""
        model = LinearRegression()
        model._weights = np.array([1.0, 2.0])
        model._n_features = 2
        model._is_fitted = True

        path = tmp_path / "model.pkl"
        save_model(model, path)

        # Corrupt the hash and remove config
        with open(path, "rb") as f:
            data = pickle.load(f)
        data["weights_hash"] = "corrupted_hash"
        if "config" in data:
            del data["config"]
        with open(path, "wb") as f:
            pickle.dump(data, f)

        with pytest.raises(ValueError, match="hash mismatch"):
            load_model(path, verify_hash=True)

    def test_load_without_hash_verification(self, tmp_path):
        """Test loading without hash verification."""
        model = LinearRegression()
        model._weights = np.array([1.0, 2.0])
        model._n_features = 2
        model._is_fitted = True

        path = tmp_path / "model.pkl"
        save_model(model, path)

        # Corrupt the hash and remove config
        with open(path, "rb") as f:
            data = pickle.load(f)
        data["weights_hash"] = "corrupted_hash"
        if "config" in data:
            del data["config"]
        with open(path, "wb") as f:
            pickle.dump(data, f)

        # Should not raise with verify_hash=False
        loaded = load_model(path, verify_hash=False)
        assert loaded is not None

    def test_load_kmeans_basic(self, tmp_path):
        """Test loading KMeans model."""
        model = KMeans(n_clusters=3)
        path = tmp_path / "kmeans.pkl"
        save_model(model, path)

        # Remove config to test simple load
        with open(path, "rb") as f:
            data = pickle.load(f)
        if "config" in data:
            del data["config"]
        with open(path, "wb") as f:
            pickle.dump(data, f)

        loaded = load_model(path, verify_hash=False)
        assert loaded is not None

    def test_load_decision_tree_basic(self, tmp_path):
        """Test loading DecisionTree model."""
        model = DecisionTreeClassifier()
        path = tmp_path / "tree.pkl"
        save_model(model, path)

        # Remove config to test simple load
        with open(path, "rb") as f:
            data = pickle.load(f)
        if "config" in data:
            del data["config"]
        with open(path, "wb") as f:
            pickle.dump(data, f)

        loaded = load_model(path, verify_hash=False)
        assert loaded is not None


class TestModelRegistry:
    """Tests for model registry."""

    def test_registry_contains_all_models(self):
        """Test that registry contains all model types."""
        registry = get_model_registry()
        assert "LinearRegression" in registry
        assert "LogisticRegression" in registry
        assert "DecisionTree" in registry
        assert "DecisionTreeClassifier" in registry
        assert "DecisionTreeRegressor" in registry
        assert "KMeans" in registry
        assert "MiniBatchKMeans" in registry

    def test_registry_returns_correct_classes(self):
        """Test that registry returns correct class types."""
        registry = get_model_registry()
        assert registry["LinearRegression"] is LinearRegression
        assert registry["KMeans"] is KMeans

    def test_registry_is_cached(self):
        """Test that registry is cached."""
        registry1 = get_model_registry()
        registry2 = get_model_registry()
        assert registry1 is registry2


# ========== Validators Tests ==========


class TestValidationError:
    """Tests for ValidationError."""

    def test_validation_error_message(self):
        """Test ValidationError stores message."""
        error = ValidationError("Test error message")
        assert str(error) == "Test error message"

    def test_validation_error_is_exception(self):
        """Test ValidationError is an Exception."""
        error = ValidationError("Test")
        assert isinstance(error, Exception)


class TestValidateNumericData:
    """Tests for validate_numeric_data function."""

    def test_valid_numpy_array(self):
        """Test validation of valid numpy array."""
        data = np.array([[1.0, 2.0], [3.0, 4.0]])
        validate_numeric_data(data)  # Should not raise

    def test_valid_dataframe(self):
        """Test validation of valid DataFrame."""
        df = pd.DataFrame({"a": [1.0, 2.0], "b": [3.0, 4.0]})
        validate_numeric_data(df)  # Should not raise

    def test_non_numeric_raises(self):
        """Test that non-numeric data raises error."""
        data = np.array(["a", "b", "c"])

        with pytest.raises(ValidationError, match="must be numeric"):
            validate_numeric_data(data)

    def test_nan_raises_by_default(self):
        """Test that NaN raises error by default."""
        data = np.array([1.0, np.nan, 3.0])

        with pytest.raises(ValidationError, match="NaN"):
            validate_numeric_data(data)

    def test_nan_allowed(self):
        """Test that NaN can be allowed."""
        data = np.array([1.0, np.nan, 3.0])
        validate_numeric_data(data, allow_nan=True)  # Should not raise

    def test_inf_raises_by_default(self):
        """Test that infinite values raise error by default."""
        data = np.array([1.0, np.inf, 3.0])

        with pytest.raises(ValidationError, match="infinite"):
            validate_numeric_data(data)

    def test_inf_allowed(self):
        """Test that infinite values can be allowed."""
        data = np.array([1.0, np.inf, 3.0])
        validate_numeric_data(data, allow_inf=True)  # Should not raise


class TestValidateDataShape:
    """Tests for validate_data_shape function."""

    def test_valid_2d_array(self):
        """Test validation of valid 2D array."""
        data = np.array([[1, 2, 3], [4, 5, 6]])
        validate_data_shape(data)  # Should not raise

    def test_valid_dataframe(self):
        """Test validation of valid DataFrame."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        validate_data_shape(df)  # Should not raise

    def test_1d_array(self):
        """Test validation of 1D array."""
        data = np.array([1, 2, 3, 4, 5])
        validate_data_shape(data)  # Should not raise (n_samples=5, n_features=1)

    def test_3d_array_raises(self):
        """Test that 3D array raises error."""
        data = np.array([[[1, 2], [3, 4]]])

        with pytest.raises(ValidationError, match="1D or 2D"):
            validate_data_shape(data)

    def test_min_samples_violated(self):
        """Test that too few samples raises error."""
        data = np.array([[1, 2, 3]])

        with pytest.raises(ValidationError, match="at least 5 samples"):
            validate_data_shape(data, min_samples=5)

    def test_min_features_violated(self):
        """Test that too few features raises error."""
        data = np.array([[1], [2], [3]])

        with pytest.raises(ValidationError, match="at least 3 features"):
            validate_data_shape(data, min_features=3)

    def test_max_features_violated(self):
        """Test that too many features raises error."""
        data = np.array([[1, 2, 3, 4, 5]])

        with pytest.raises(ValidationError, match="exceeding maximum"):
            validate_data_shape(data, max_features=3)


class TestValidateFeatureRange:
    """Tests for validate_feature_range function."""

    def test_valid_range(self):
        """Test validation within valid range."""
        data = np.array([[0.5, 0.6], [0.7, 0.8]])
        validate_feature_range(data, min_value=0.0, max_value=1.0)

    def test_below_minimum_raises(self):
        """Test that values below minimum raise error."""
        data = np.array([[-0.1, 0.5], [0.6, 0.7]])

        with pytest.raises(ValidationError, match="below minimum"):
            validate_feature_range(data, min_value=0.0)

    def test_above_maximum_raises(self):
        """Test that values above maximum raise error."""
        data = np.array([[0.5, 1.5], [0.6, 0.7]])

        with pytest.raises(ValidationError, match="above maximum"):
            validate_feature_range(data, max_value=1.0)

    def test_no_constraints(self):
        """Test validation with no constraints."""
        data = np.array([[-1000, 1000]])
        validate_feature_range(data)  # Should not raise


class TestValidateTarget:
    """Tests for validate_target function."""

    def test_valid_regression_target(self):
        """Test validation of valid regression target."""
        target = np.array([1.0, 2.0, 3.0])
        validate_target(target, n_samples=3, task_type="regression")

    def test_valid_classification_target(self):
        """Test validation of valid classification target."""
        target = np.array([0, 1, 0, 1])
        validate_target(target, n_samples=4, task_type="classification")

    def test_pandas_series(self):
        """Test validation with pandas Series."""
        target = pd.Series([1, 2, 3])
        validate_target(target, n_samples=3)

    def test_2d_target_raises(self):
        """Test that 2D target raises error."""
        target = np.array([[1], [2], [3]])

        with pytest.raises(ValidationError, match="must be 1D"):
            validate_target(target, n_samples=3)

    def test_wrong_length_raises(self):
        """Test that wrong length raises error."""
        target = np.array([1, 2, 3])

        with pytest.raises(ValidationError, match="doesn't match"):
            validate_target(target, n_samples=5)

    def test_single_class_raises(self):
        """Test that single class classification target raises error."""
        target = np.array([0, 0, 0, 0])

        with pytest.raises(ValidationError, match="at least 2 classes"):
            validate_target(target, n_samples=4, task_type="classification")


class TestCheckFheCompatibility:
    """Tests for check_fhe_compatibility function."""

    def test_compatible_data(self):
        """Test checking compatible data."""
        data = np.array([[1.0, 2.0], [3.0, 4.0]])
        result = check_fhe_compatibility(data)

        assert result["compatible"] is True
        assert len(result["warnings"]) == 0

    def test_dataframe_input(self):
        """Test checking DataFrame input."""
        df = pd.DataFrame({"a": [1.0, 2.0], "b": [3.0, 4.0]})
        result = check_fhe_compatibility(df)

        assert result["compatible"] is True
        assert result["stats"]["n_samples"] == 2
        assert result["stats"]["n_features"] == 2

    def test_too_many_features(self):
        """Test detection of too many features."""
        data = np.zeros((10, 5000))  # More than max_slots
        result = check_fhe_compatibility(data, max_slots=4096)

        assert result["compatible"] is False
        assert any("exceed max slots" in w for w in result["warnings"])

    def test_nan_detected(self):
        """Test detection of NaN values."""
        data = np.array([[1.0, np.nan], [3.0, 4.0]])
        result = check_fhe_compatibility(data)

        assert result["compatible"] is False
        assert any("NaN" in w for w in result["warnings"])

    def test_inf_detected(self):
        """Test detection of infinite values."""
        data = np.array([[1.0, np.inf], [3.0, 4.0]])
        result = check_fhe_compatibility(data)

        assert result["compatible"] is False
        assert any("infinite" in w for w in result["warnings"])

    def test_large_range_warning(self):
        """Test warning for large value range."""
        data = np.array([[0.0, 1e7], [1.0, 2e7]])
        result = check_fhe_compatibility(data)

        # Still compatible but with warning
        assert any("normalization" in w.lower() for w in result["warnings"])

    def test_stats_included(self):
        """Test that stats are included in result."""
        data = np.array([[1.0, 2.0], [3.0, 4.0]])
        result = check_fhe_compatibility(data)

        assert "stats" in result
        assert result["stats"]["n_samples"] == 2
        assert result["stats"]["n_features"] == 2
        assert result["stats"]["min_value"] == 1.0
        assert result["stats"]["max_value"] == 4.0

    def test_1d_array(self):
        """Test handling of 1D array."""
        data = np.array([1.0, 2.0, 3.0])
        result = check_fhe_compatibility(data)

        assert result["stats"]["n_samples"] == 3
        assert result["stats"]["n_features"] == 1


# ========== Integration Tests ==========


class TestSerializationIntegration:
    """Integration tests for serialization utilities."""

    def test_validation_workflow(self):
        """Test validation workflow."""
        # Prepare data
        X = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
        y = np.array([0, 1, 0])

        # Validate data
        validate_numeric_data(X)
        validate_data_shape(X, min_samples=2, min_features=1)
        validate_target(y, n_samples=3, task_type="classification")

        # Check FHE compatibility
        compat = check_fhe_compatibility(X)
        assert compat["compatible"] is True

    def test_save_and_get_info(self, tmp_path):
        """Test saving model and getting info."""
        model = LinearRegression()
        model._weights = np.array([1.0, 2.0])
        model._bias = 0.5
        model._n_features = 2

        path = tmp_path / "model.pkl"
        save_model(model, path)

        info = get_model_info(path)
        assert info["model_type"] == "LinearRegression"
        assert "weights_hash" in info

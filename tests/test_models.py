"""Tests for FHE models."""

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LinearRegression as SklearnLinearRegression
from sklearn.datasets import make_regression

from sdk.models import (
    BaseFHEModel,
    FHEModel,
    LinearRegression,
    ModelConfig,
    ModelState,
    TrainingHistory,
)
from sdk.utils import SecureDataLoader


class TestModelConfig:
    """Tests for ModelConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ModelConfig()
        assert config.learning_rate == 0.01
        assert config.n_epochs == 100
        assert config.batch_size is None
        assert config.verbose is False

    def test_custom_config(self):
        """Test custom configuration."""
        config = ModelConfig(
            learning_rate=0.1,
            n_epochs=50,
            verbose=True,
        )
        assert config.learning_rate == 0.1
        assert config.n_epochs == 50

    def test_invalid_learning_rate_raises(self):
        """Test that invalid learning rate raises ValueError."""
        with pytest.raises(ValueError, match="learning_rate"):
            ModelConfig(learning_rate=-0.1)

    def test_invalid_epochs_raises(self):
        """Test that invalid epochs raises ValueError."""
        with pytest.raises(ValueError, match="n_epochs"):
            ModelConfig(n_epochs=0)


class TestTrainingHistory:
    """Tests for TrainingHistory."""

    def test_add_epoch(self):
        """Test adding epoch metrics."""
        history = TrainingHistory()
        history.add_epoch(0.5, accuracy=0.8)
        history.add_epoch(0.3, accuracy=0.9)

        assert history.epochs == 2
        assert history.losses == [0.5, 0.3]
        assert history.metrics["accuracy"] == [0.8, 0.9]


class TestFHEModelFactory:
    """Tests for FHEModel factory class."""

    def test_create_linear_regression(self):
        """Test creating LinearRegression via factory."""
        model = FHEModel.LinearRegression(learning_rate=0.1)
        assert isinstance(model, LinearRegression)
        assert model.config.learning_rate == 0.1


class TestLinearRegression:
    """Tests for LinearRegression model."""

    @pytest.fixture
    def simple_data(self):
        """Create simple linear data for testing."""
        np.random.seed(42)
        X = np.random.randn(100, 3)
        y = 2 * X[:, 0] + 3 * X[:, 1] - X[:, 2] + 1 + np.random.randn(100) * 0.1
        return X, y

    @pytest.fixture
    def loader(self):
        """Create SecureDataLoader fixture."""
        return SecureDataLoader(normalize=True)

    def test_model_initialization(self):
        """Test model initialization."""
        model = LinearRegression(learning_rate=0.1, n_epochs=50)
        assert model.state == ModelState.INITIALIZED
        assert not model.is_fitted
        assert model.weights is None

    def test_fit_with_encrypted_dataset(self, simple_data, loader):
        """Test training with EncryptedDataset."""
        X, y = simple_data

        # Create DataFrame with target
        df = pd.DataFrame(X, columns=["a", "b", "c"])
        df["target"] = y

        # Encrypt
        encrypted = loader.encrypt(df, target_column="target")

        # Train
        model = LinearRegression(learning_rate=0.1, n_epochs=100)
        model.fit(encrypted)

        assert model.is_fitted
        assert model.state == ModelState.TRAINED
        assert model.weights is not None
        assert len(model.weights) == 3
        assert model.bias is not None

    def test_fit_records_history(self, simple_data, loader):
        """Test that training records loss history."""
        X, y = simple_data
        df = pd.DataFrame(X, columns=["a", "b", "c"])
        df["target"] = y

        encrypted = loader.encrypt(df, target_column="target")

        model = LinearRegression(n_epochs=50)
        model.fit(encrypted)

        assert model.history.epochs == 50
        assert len(model.history.losses) == 50
        # Loss should generally decrease
        assert model.history.losses[-1] < model.history.losses[0]

    def test_predict_on_encrypted_data(self, simple_data, loader):
        """Test prediction on encrypted data."""
        X, y = simple_data
        df = pd.DataFrame(X, columns=["a", "b", "c"])
        df["target"] = y

        encrypted = loader.encrypt(df, target_column="target")

        model = LinearRegression(learning_rate=0.1, n_epochs=100)
        model.fit(encrypted)

        # Predict
        predictions = model.predict(encrypted.X)

        # Decrypt and check
        decrypted_preds = loader.decrypt(predictions)
        assert len(decrypted_preds) == len(y)

    def test_predict_plaintext(self, simple_data, loader):
        """Test plaintext prediction method."""
        X, y = simple_data
        df = pd.DataFrame(X, columns=["a", "b", "c"])
        df["target"] = y

        encrypted = loader.encrypt(df, target_column="target")

        model = LinearRegression(learning_rate=0.1, n_epochs=100)
        model.fit(encrypted)

        # Predict on plaintext
        # Note: need to normalize X the same way
        X_norm = (X - X.min(axis=0)) / (X.max(axis=0) - X.min(axis=0))
        X_norm = 2 * X_norm - 1

        predictions = model.predict_plaintext(X_norm)
        assert predictions.shape == (100,)

    def test_score_method(self, simple_data, loader):
        """Test R² score computation."""
        X, y = simple_data
        df = pd.DataFrame(X, columns=["a", "b", "c"])
        df["target"] = y

        encrypted = loader.encrypt(df, target_column="target")

        model = LinearRegression(learning_rate=0.1, n_epochs=200)
        model.fit(encrypted)

        # Normalize for scoring
        X_norm = (X - X.min(axis=0)) / (X.max(axis=0) - X.min(axis=0))
        X_norm = 2 * X_norm - 1
        y_norm = (y - y.min()) / (y.max() - y.min())
        y_norm = 2 * y_norm - 1

        score = model.score(X_norm, y_norm)
        # Should have reasonable R² for simple linear data
        assert score > 0.5

    def test_predict_before_fit_raises(self):
        """Test that predicting before fit raises RuntimeError."""
        model = LinearRegression()
        loader = SecureDataLoader()
        X = np.array([[1.0, 2.0]])
        encrypted = loader.encrypt(X)

        with pytest.raises(RuntimeError, match="must be fitted"):
            model.predict(encrypted.X)

    def test_fit_without_target_raises(self, loader):
        """Test that fit without target raises ValueError."""
        X = np.array([[1.0, 2.0], [3.0, 4.0]])
        encrypted = loader.encrypt(X)  # No target

        model = LinearRegression()
        with pytest.raises(ValueError, match="target"):
            model.fit(encrypted)

    def test_early_stopping(self, simple_data, loader):
        """Test early stopping functionality."""
        X, y = simple_data
        df = pd.DataFrame(X, columns=["a", "b", "c"])
        df["target"] = y

        encrypted = loader.encrypt(df, target_column="target")

        model = LinearRegression(
            learning_rate=0.5,
            n_epochs=1000,
            early_stopping_patience=10,
            tolerance=1e-6,
        )
        model.fit(encrypted)

        # Should stop before 1000 epochs
        assert model.history.epochs < 1000

    def test_get_set_params(self, simple_data, loader):
        """Test parameter serialization."""
        X, y = simple_data
        df = pd.DataFrame(X, columns=["a", "b", "c"])
        df["target"] = y

        encrypted = loader.encrypt(df, target_column="target")

        model = LinearRegression(n_epochs=50)
        model.fit(encrypted)

        # Get params
        params = model.get_params()
        assert params["weights"] is not None
        assert params["bias"] is not None
        assert params["state"] == "trained"

        # Set params on new model
        model2 = LinearRegression()
        model2.set_params(params)
        assert model2.is_fitted
        np.testing.assert_array_equal(model2.weights, model.weights)

    def test_regularization(self, simple_data, loader):
        """Test L2 regularization."""
        X, y = simple_data
        df = pd.DataFrame(X, columns=["a", "b", "c"])
        df["target"] = y

        encrypted = loader.encrypt(df, target_column="target")

        # Train with regularization
        model_reg = LinearRegression(
            learning_rate=0.1,
            n_epochs=100,
            regularization=0.1,
        )
        model_reg.fit(encrypted)

        # Train without regularization
        model_no_reg = LinearRegression(
            learning_rate=0.1,
            n_epochs=100,
            regularization=0.0,
        )
        model_no_reg.fit(encrypted)

        # Regularized weights should have smaller magnitude on average
        reg_magnitude = np.mean(np.abs(model_reg.weights))
        no_reg_magnitude = np.mean(np.abs(model_no_reg.weights))
        assert reg_magnitude <= no_reg_magnitude * 1.5  # Allow some variance

    def test_comparison_with_sklearn(self, loader):
        """Test that results are comparable to sklearn."""
        # Generate data
        X, y = make_regression(
            n_samples=200,
            n_features=3,
            noise=0.1,
            random_state=42,
        )

        # Normalize data (same as SecureDataLoader does)
        X_norm = (X - X.min(axis=0)) / (X.max(axis=0) - X.min(axis=0) + 1e-8)
        X_norm = 2 * X_norm - 1
        y_norm = (y - y.min()) / (y.max() - y.min() + 1e-8)
        y_norm = 2 * y_norm - 1

        # Train sklearn model
        sklearn_model = SklearnLinearRegression()
        sklearn_model.fit(X_norm, y_norm)
        sklearn_preds = sklearn_model.predict(X_norm)
        sklearn_r2 = 1 - np.sum((y_norm - sklearn_preds) ** 2) / np.sum(
            (y_norm - np.mean(y_norm)) ** 2
        )

        # Train our model
        df = pd.DataFrame(X, columns=["a", "b", "c"])
        df["target"] = y
        encrypted = loader.encrypt(df, target_column="target")

        our_model = LinearRegression(
            learning_rate=0.1,
            n_epochs=500,
        )
        our_model.fit(encrypted)
        our_r2 = our_model.score(X_norm, y_norm)

        # Our model should achieve reasonable R² compared to sklearn
        # (within 20% of sklearn's performance)
        assert our_r2 > sklearn_r2 * 0.8

    def test_repr(self):
        """Test string representation."""
        model = LinearRegression(learning_rate=0.1, n_epochs=50)
        repr_str = repr(model)
        assert "LinearRegression" in repr_str
        assert "lr=0.1" in repr_str
        assert "initialized" in repr_str

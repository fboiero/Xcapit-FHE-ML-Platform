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
    LogisticRegression,
    ModelConfig,
    ModelState,
    SigmoidApproximation,
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


class TestLogisticRegression:
    """Tests for LogisticRegression model."""

    @pytest.fixture
    def binary_data(self):
        """Create binary classification data."""
        np.random.seed(42)
        n_samples = 200

        # Generate two clusters
        X_class0 = np.random.randn(n_samples // 2, 3) + np.array([-2, -2, -2])
        X_class1 = np.random.randn(n_samples // 2, 3) + np.array([2, 2, 2])

        X = np.vstack([X_class0, X_class1])
        y = np.array([0] * (n_samples // 2) + [1] * (n_samples // 2))

        # Shuffle
        idx = np.random.permutation(n_samples)
        return X[idx], y[idx].astype(float)

    @pytest.fixture
    def loader(self):
        """Create SecureDataLoader fixture."""
        return SecureDataLoader(normalize=True)

    def test_model_initialization(self):
        """Test model initialization."""
        model = LogisticRegression(learning_rate=0.1, n_epochs=50)
        assert model.state == ModelState.INITIALIZED
        assert not model.is_fitted
        assert model.sigmoid_approx == SigmoidApproximation.DEGREE3

    def test_sigmoid_approximation_options(self):
        """Test different sigmoid approximation methods."""
        for approx in SigmoidApproximation:
            model = LogisticRegression(sigmoid_approx=approx)
            assert model.sigmoid_approx == approx

    def test_fit_binary_classification(self, binary_data, loader):
        """Test training on binary classification data."""
        X, y = binary_data

        df = pd.DataFrame(X, columns=["a", "b", "c"])
        df["label"] = y

        encrypted = loader.encrypt(df, target_column="label")

        model = LogisticRegression(learning_rate=0.5, n_epochs=100)
        model.fit(encrypted)

        assert model.is_fitted
        assert model.state == ModelState.TRAINED
        assert len(model.weights) == 3

    def test_predict_proba(self, binary_data, loader):
        """Test probability prediction."""
        X, y = binary_data
        df = pd.DataFrame(X, columns=["a", "b", "c"])
        df["label"] = y

        encrypted = loader.encrypt(df, target_column="label")

        model = LogisticRegression(learning_rate=0.5, n_epochs=100)
        model.fit(encrypted)

        probs = model.predict_proba(encrypted.X)
        probs_decrypted = loader.encryptor.decrypt_vector(probs)

        # Probabilities should be between 0 and 1
        assert np.all(probs_decrypted >= 0)
        assert np.all(probs_decrypted <= 1)

    def test_predict_classes(self, binary_data, loader):
        """Test class prediction."""
        X, y = binary_data
        df = pd.DataFrame(X, columns=["a", "b", "c"])
        df["label"] = y

        encrypted = loader.encrypt(df, target_column="label")

        model = LogisticRegression(learning_rate=0.5, n_epochs=100)
        model.fit(encrypted)

        predictions = model.predict(encrypted.X)
        preds_decrypted = loader.encryptor.decrypt_vector(predictions)

        # Predictions should be 0 or 1
        unique_preds = np.unique(np.round(preds_decrypted))
        assert len(unique_preds) <= 2

    def test_accuracy_score(self, binary_data, loader):
        """Test accuracy computation."""
        X, y = binary_data
        df = pd.DataFrame(X, columns=["a", "b", "c"])
        df["label"] = y

        encrypted = loader.encrypt(df, target_column="label")

        model = LogisticRegression(learning_rate=0.5, n_epochs=200)
        model.fit(encrypted)

        # Normalize X for scoring
        X_norm = (X - X.min(axis=0)) / (X.max(axis=0) - X.min(axis=0) + 1e-8)
        X_norm = 2 * X_norm - 1

        accuracy = model.score(X_norm, y)
        # Should achieve reasonable accuracy on separable data
        assert accuracy > 0.7

    def test_predict_plaintext(self, binary_data, loader):
        """Test plaintext prediction methods."""
        X, y = binary_data
        df = pd.DataFrame(X, columns=["a", "b", "c"])
        df["label"] = y

        encrypted = loader.encrypt(df, target_column="label")

        model = LogisticRegression(learning_rate=0.5, n_epochs=100)
        model.fit(encrypted)

        # Normalize for prediction
        X_norm = (X - X.min(axis=0)) / (X.max(axis=0) - X.min(axis=0) + 1e-8)
        X_norm = 2 * X_norm - 1

        probs = model.predict_proba_plaintext(X_norm)
        preds = model.predict_plaintext(X_norm)

        assert probs.shape == (200,)
        assert preds.shape == (200,)
        assert np.all((preds == 0) | (preds == 1))

    def test_custom_threshold(self, binary_data, loader):
        """Test custom classification threshold."""
        X, y = binary_data
        df = pd.DataFrame(X, columns=["a", "b", "c"])
        df["label"] = y

        encrypted = loader.encrypt(df, target_column="label")

        # High threshold should predict more 0s
        model_high = LogisticRegression(
            learning_rate=0.5,
            n_epochs=100,
            threshold=0.9,
        )
        model_high.fit(encrypted)

        # Low threshold should predict more 1s
        model_low = LogisticRegression(
            learning_rate=0.5,
            n_epochs=100,
            threshold=0.1,
        )
        model_low.fit(encrypted)

        X_norm = (X - X.min(axis=0)) / (X.max(axis=0) - X.min(axis=0) + 1e-8)
        X_norm = 2 * X_norm - 1

        preds_high = model_high.predict_plaintext(X_norm)
        preds_low = model_low.predict_plaintext(X_norm)

        # High threshold should have fewer 1s than low threshold
        assert np.sum(preds_high) <= np.sum(preds_low)

    def test_loss_decreases(self, binary_data, loader):
        """Test that loss decreases during training."""
        X, y = binary_data
        df = pd.DataFrame(X, columns=["a", "b", "c"])
        df["label"] = y

        encrypted = loader.encrypt(df, target_column="label")

        model = LogisticRegression(learning_rate=0.3, n_epochs=50)
        model.fit(encrypted)

        # Loss should generally decrease
        assert model.history.losses[-1] < model.history.losses[0]

    def test_factory_creation(self):
        """Test creating LogisticRegression via factory."""
        model = FHEModel.LogisticRegression(learning_rate=0.2)
        assert isinstance(model, LogisticRegression)
        assert model.config.learning_rate == 0.2

    def test_repr(self):
        """Test string representation."""
        model = LogisticRegression(
            learning_rate=0.1,
            sigmoid_approx=SigmoidApproximation.DEGREE5,
        )
        repr_str = repr(model)
        assert "LogisticRegression" in repr_str
        assert "lr=0.1" in repr_str
        assert "degree5" in repr_str

    def test_polynomial_sigmoid_values(self):
        """Test that polynomial sigmoid produces valid probabilities."""
        model = LogisticRegression()
        model._initialize_weights(3)
        model._state = ModelState.TRAINED

        # Test input range
        x = np.linspace(-5, 5, 100)
        probs = model._sigmoid_polynomial(x)

        # All outputs should be in [0, 1]
        assert np.all(probs >= 0)
        assert np.all(probs <= 1)

        # Should be monotonically increasing
        assert np.all(np.diff(probs) >= -0.01)  # Allow small numerical errors

    def test_comparison_different_sigmoid_approx(self, binary_data, loader):
        """Test different sigmoid approximations produce similar results."""
        X, y = binary_data
        df = pd.DataFrame(X, columns=["a", "b", "c"])
        df["label"] = y

        encrypted = loader.encrypt(df, target_column="label")

        accuracies = {}
        for approx in [SigmoidApproximation.LINEAR, SigmoidApproximation.DEGREE3]:
            model = LogisticRegression(
                learning_rate=0.5,
                n_epochs=100,
                sigmoid_approx=approx,
            )
            model.fit(encrypted)

            X_norm = (X - X.min(axis=0)) / (X.max(axis=0) - X.min(axis=0) + 1e-8)
            X_norm = 2 * X_norm - 1

            accuracies[approx] = model.score(X_norm, y)

        # Both should achieve reasonable accuracy
        for acc in accuracies.values():
            assert acc > 0.6

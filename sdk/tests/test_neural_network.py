"""Tests for Neural Network FHE implementation."""

import numpy as np
import pytest
from sklearn.datasets import make_classification, make_regression
from sklearn.model_selection import train_test_split


class TestActivationFunctions:
    """Tests for polynomial activation functions."""

    def test_square_activation(self):
        """Test square activation."""
        from sdk.models.neural_network import ActivationFunctions

        x = np.array([-2, -1, 0, 1, 2])
        result = ActivationFunctions.square(x)
        expected = np.array([4, 1, 0, 1, 4])
        np.testing.assert_array_equal(result, expected)

    def test_square_derivative(self):
        """Test square derivative."""
        from sdk.models.neural_network import ActivationFunctions

        x = np.array([-2, -1, 0, 1, 2])
        result = ActivationFunctions.square_derivative(x)
        expected = np.array([-4, -2, 0, 2, 4])
        np.testing.assert_array_equal(result, expected)

    def test_polynomial_sigmoid(self):
        """Test polynomial sigmoid approximation."""
        from sdk.models.neural_network import ActivationFunctions

        x = np.array([0])
        result = ActivationFunctions.polynomial_sigmoid(x)
        # At x=0, sigmoid ≈ 0.5
        assert np.isclose(result[0], 0.5, atol=0.01)

    def test_polynomial_sigmoid_range(self):
        """Test polynomial sigmoid stays in valid range for small x."""
        from sdk.models.neural_network import ActivationFunctions

        x = np.linspace(-2, 2, 100)
        result = ActivationFunctions.polynomial_sigmoid(x)
        # Should be monotonically increasing
        assert np.all(np.diff(result) >= 0)

    def test_polynomial_tanh(self):
        """Test polynomial tanh approximation."""
        from sdk.models.neural_network import ActivationFunctions

        x = np.array([0])
        result = ActivationFunctions.polynomial_tanh(x)
        # At x=0, tanh = 0
        assert np.isclose(result[0], 0.0)

    def test_linear_activation(self):
        """Test linear activation (identity)."""
        from sdk.models.neural_network import ActivationFunctions

        x = np.array([-1, 0, 1, 5])
        result = ActivationFunctions.linear(x)
        np.testing.assert_array_equal(result, x)

    def test_get_activation(self):
        """Test getting activation by enum."""
        from sdk.models.neural_network import Activation, ActivationFunctions

        for act in Activation:
            func = ActivationFunctions.get_activation(act)
            assert callable(func)

    def test_get_derivative(self):
        """Test getting derivative by enum."""
        from sdk.models.neural_network import Activation, ActivationFunctions

        for act in Activation:
            func = ActivationFunctions.get_derivative(act)
            assert callable(func)


class TestLayerConfig:
    """Tests for LayerConfig."""

    def test_default_config(self):
        """Test default layer configuration."""
        from sdk.models.neural_network import Activation, LayerConfig

        layer = LayerConfig(units=32)
        assert layer.units == 32
        assert layer.activation == Activation.SQUARE
        assert layer.use_bias is True
        assert layer.dropout_rate == 0.0

    def test_invalid_units(self):
        """Test validation of units."""
        from sdk.models.neural_network import LayerConfig

        with pytest.raises(ValueError, match="units must be at least 1"):
            LayerConfig(units=0)

    def test_invalid_dropout(self):
        """Test validation of dropout rate."""
        from sdk.models.neural_network import LayerConfig

        with pytest.raises(ValueError, match="dropout_rate must be in"):
            LayerConfig(units=32, dropout_rate=1.0)


class TestNeuralNetworkConfig:
    """Tests for NeuralNetworkConfig."""

    def test_default_config(self):
        """Test default network configuration."""
        from sdk.models.neural_network import NeuralNetworkConfig

        config = NeuralNetworkConfig()
        assert len(config.hidden_layers) == 1
        assert config.hidden_layers[0].units == 32
        assert config.output_units == 1
        assert config.l2_reg == 0.0

    def test_invalid_output_units(self):
        """Test validation of output_units."""
        from sdk.models.neural_network import NeuralNetworkConfig

        with pytest.raises(ValueError, match="output_units must be at least 1"):
            NeuralNetworkConfig(output_units=0)

    def test_invalid_l2_reg(self):
        """Test validation of l2_reg."""
        from sdk.models.neural_network import NeuralNetworkConfig

        with pytest.raises(ValueError, match="l2_reg must be non-negative"):
            NeuralNetworkConfig(l2_reg=-0.1)


class TestNeuralNetwork:
    """Tests for NeuralNetwork base class."""

    @pytest.fixture
    def regression_data(self):
        """Generate regression data."""
        np.random.seed(42)
        X, y = make_regression(
            n_samples=100, n_features=5, n_informative=3, noise=0.1, random_state=42
        )
        # Scale y to smaller range
        y = (y - y.mean()) / y.std()
        return train_test_split(X, y, test_size=0.2, random_state=42)

    def test_basic_fit(self, regression_data):
        """Test basic fitting."""
        from sdk.models.neural_network import LayerConfig, NeuralNetwork, NeuralNetworkConfig

        X_train, X_test, y_train, y_test = regression_data

        config = NeuralNetworkConfig(
            hidden_layers=[LayerConfig(units=16)],
            n_epochs=50,
            learning_rate=0.01,
        )
        nn = NeuralNetwork(config=config)
        nn.fit(X_train, y_train)

        assert nn.is_fitted
        assert nn.n_layers == 2  # 1 hidden + 1 output

    def test_predict(self, regression_data):
        """Test prediction."""
        from sdk.models.neural_network import LayerConfig, NeuralNetwork, NeuralNetworkConfig

        X_train, X_test, y_train, y_test = regression_data

        config = NeuralNetworkConfig(
            hidden_layers=[LayerConfig(units=16)],
            n_epochs=50,
        )
        nn = NeuralNetwork(config=config)
        nn.fit(X_train, y_train)

        predictions = nn.predict(X_test)
        assert predictions.shape == (len(X_test),)

    def test_multiple_hidden_layers(self, regression_data):
        """Test network with multiple hidden layers."""
        from sdk.models.neural_network import (
            Activation,
            LayerConfig,
            NeuralNetwork,
            NeuralNetworkConfig,
        )

        X_train, X_test, y_train, y_test = regression_data

        config = NeuralNetworkConfig(
            hidden_layers=[
                LayerConfig(units=32, activation=Activation.SQUARE),
                LayerConfig(units=16, activation=Activation.POLYNOMIAL_SIGMOID),
                LayerConfig(units=8, activation=Activation.POLYNOMIAL_TANH),
            ],
            n_epochs=30,
        )
        nn = NeuralNetwork(config=config)
        nn.fit(X_train, y_train)

        assert nn.is_fitted
        assert nn.n_layers == 4  # 3 hidden + 1 output
        assert nn.layer_sizes == [5, 32, 16, 8, 1]

    def test_training_history(self, regression_data):
        """Test that training history is recorded."""
        from sdk.models.neural_network import LayerConfig, NeuralNetwork, NeuralNetworkConfig

        X_train, _, y_train, _ = regression_data

        config = NeuralNetworkConfig(
            hidden_layers=[LayerConfig(units=16)],
            n_epochs=20,
        )
        nn = NeuralNetwork(config=config)
        nn.fit(X_train, y_train)

        assert len(nn.history.losses) == 20
        # Loss should generally decrease
        assert nn.history.losses[-1] < nn.history.losses[0]

    def test_early_stopping(self, regression_data):
        """Test early stopping."""
        from sdk.models.neural_network import LayerConfig, NeuralNetwork, NeuralNetworkConfig

        X_train, _, y_train, _ = regression_data

        config = NeuralNetworkConfig(
            hidden_layers=[LayerConfig(units=16)],
            n_epochs=1000,  # Large number
            early_stopping_patience=5,
            tolerance=1e-6,
        )
        nn = NeuralNetwork(config=config)
        nn.fit(X_train, y_train)

        # Should stop before 1000 epochs
        assert len(nn.history.losses) < 1000

    def test_l2_regularization(self, regression_data):
        """Test L2 regularization."""
        from sdk.models.neural_network import LayerConfig, NeuralNetwork, NeuralNetworkConfig

        X_train, _, y_train, _ = regression_data

        config = NeuralNetworkConfig(
            hidden_layers=[LayerConfig(units=16)],
            n_epochs=50,
            l2_reg=0.01,
        )
        nn = NeuralNetwork(config=config)
        nn.fit(X_train, y_train)

        # Check weights are smaller with regularization
        max_weight = max(np.max(np.abs(W)) for W in nn._layer_weights)
        assert max_weight < 10  # Weights should be reasonably bounded

    def test_momentum(self, regression_data):
        """Test training with momentum."""
        from sdk.models.neural_network import LayerConfig, NeuralNetwork, NeuralNetworkConfig

        X_train, _, y_train, _ = regression_data

        config = NeuralNetworkConfig(
            hidden_layers=[LayerConfig(units=16)],
            n_epochs=50,
            momentum=0.9,
        )
        nn = NeuralNetwork(config=config)
        nn.fit(X_train, y_train)

        assert nn.is_fitted

    def test_mini_batch_training(self, regression_data):
        """Test mini-batch training."""
        from sdk.models.neural_network import LayerConfig, NeuralNetwork, NeuralNetworkConfig

        X_train, _, y_train, _ = regression_data

        config = NeuralNetworkConfig(
            hidden_layers=[LayerConfig(units=16)],
            n_epochs=50,
            batch_size=16,
        )
        nn = NeuralNetwork(config=config)
        nn.fit(X_train, y_train)

        assert nn.is_fitted

    def test_get_params(self, regression_data):
        """Test getting model parameters."""
        from sdk.models.neural_network import LayerConfig, NeuralNetwork, NeuralNetworkConfig

        X_train, _, y_train, _ = regression_data

        config = NeuralNetworkConfig(
            hidden_layers=[LayerConfig(units=8)],
            n_epochs=10,
        )
        nn = NeuralNetwork(config=config)
        nn.fit(X_train, y_train)

        params = nn.get_params()
        assert "layer_weights" in params
        assert "layer_biases" in params
        assert "layer_sizes" in params
        assert params["layer_sizes"] == [5, 8, 1]


class TestNeuralNetworkClassifier:
    """Tests for NeuralNetworkClassifier."""

    @pytest.fixture
    def classification_data(self):
        """Generate classification data."""
        X, y = make_classification(
            n_samples=100,
            n_features=5,
            n_informative=3,
            n_redundant=1,
            n_classes=2,
            random_state=42,
        )
        return train_test_split(X, y, test_size=0.2, random_state=42)

    def test_binary_classification(self, classification_data):
        """Test binary classification."""
        from sdk.models.neural_network import NeuralNetworkClassifier

        X_train, X_test, y_train, y_test = classification_data

        clf = NeuralNetworkClassifier(
            hidden_units=[16],
            n_classes=2,
            n_epochs=50,
        )
        clf.fit(X_train, y_train)

        predictions = clf.predict(X_test)
        assert predictions.shape == (len(X_test),)
        assert set(predictions).issubset({0, 1})

    def test_predict_proba(self, classification_data):
        """Test probability prediction."""
        from sdk.models.neural_network import NeuralNetworkClassifier

        X_train, X_test, y_train, y_test = classification_data

        clf = NeuralNetworkClassifier(
            hidden_units=[16],
            n_classes=2,
            n_epochs=50,
        )
        clf.fit(X_train, y_train)

        proba = clf.predict_proba(X_test)
        assert proba.shape == (len(X_test), 2)
        # Probabilities should sum to 1
        np.testing.assert_array_almost_equal(proba.sum(axis=1), np.ones(len(X_test)))

    def test_accuracy_score(self, classification_data):
        """Test accuracy score computation."""
        from sdk.models.neural_network import NeuralNetworkClassifier

        X_train, X_test, y_train, y_test = classification_data

        clf = NeuralNetworkClassifier(
            hidden_units=[32, 16],
            n_classes=2,
            n_epochs=100,
        )
        clf.fit(X_train, y_train)

        accuracy = clf.score(X_test, y_test)
        assert 0.0 <= accuracy <= 1.0
        # Should achieve reasonable accuracy
        assert accuracy > 0.4

    def test_multiclass_classification(self):
        """Test multi-class classification."""
        from sdk.models.neural_network import NeuralNetworkClassifier

        X, y = make_classification(
            n_samples=150,
            n_features=5,
            n_informative=3,
            n_classes=3,
            n_clusters_per_class=1,
            random_state=42,
        )
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        clf = NeuralNetworkClassifier(
            hidden_units=[32],
            n_classes=3,
            n_epochs=100,
        )
        clf.fit(X_train, y_train)

        predictions = clf.predict(X_test)
        assert set(predictions).issubset({0, 1, 2})

        proba = clf.predict_proba(X_test)
        assert proba.shape == (len(X_test), 3)


class TestNeuralNetworkRegressor:
    """Tests for NeuralNetworkRegressor."""

    @pytest.fixture
    def regression_data(self):
        """Generate regression data."""
        np.random.seed(42)
        X, y = make_regression(
            n_samples=100, n_features=5, n_informative=3, noise=0.1, random_state=42
        )
        y = (y - y.mean()) / y.std()
        return train_test_split(X, y, test_size=0.2, random_state=42)

    def test_basic_regression(self, regression_data):
        """Test basic regression."""
        from sdk.models.neural_network import NeuralNetworkRegressor

        X_train, X_test, y_train, y_test = regression_data

        reg = NeuralNetworkRegressor(
            hidden_units=[32],
            n_epochs=100,
        )
        reg.fit(X_train, y_train)

        predictions = reg.predict(X_test)
        assert predictions.shape == (len(X_test),)

    def test_r2_score(self, regression_data):
        """Test R² score computation."""
        from sdk.models.neural_network import NeuralNetworkRegressor

        X_train, X_test, y_train, y_test = regression_data

        reg = NeuralNetworkRegressor(
            hidden_units=[32, 16],
            n_epochs=200,
            learning_rate=0.01,
        )
        reg.fit(X_train, y_train)

        r2 = reg.score(X_test, y_test)
        # Should be better than random baseline
        assert r2 > 0

    def test_convenience_init(self, regression_data):
        """Test convenience initialization."""
        from sdk.models.neural_network import Activation, NeuralNetworkRegressor

        X_train, _, y_train, _ = regression_data

        reg = NeuralNetworkRegressor(
            hidden_units=[16, 8],
            activation=Activation.POLYNOMIAL_TANH,
            learning_rate=0.005,
            n_epochs=50,
            batch_size=16,
        )
        reg.fit(X_train, y_train)

        assert reg.is_fitted
        assert reg.layer_sizes == [5, 16, 8, 1]


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_predict_before_fit(self):
        """Test prediction before fitting raises error."""
        from sdk.models.neural_network import NeuralNetworkClassifier

        clf = NeuralNetworkClassifier(hidden_units=[16])
        X = np.random.randn(10, 5)

        with pytest.raises(RuntimeError, match="must be fitted"):
            clf.predict(X)

    def test_encrypted_training_not_supported(self):
        """Test that encrypted training raises appropriate error."""
        from sdk.models.neural_network import NeuralNetworkRegressor

        reg = NeuralNetworkRegressor(hidden_units=[16])

        class FakeEncrypted:
            pass

        with pytest.raises((ValueError, TypeError, AttributeError)):
            reg.fit(FakeEncrypted(), np.array([1, 2, 3]))

    def test_single_feature(self):
        """Test with single feature."""
        from sdk.models.neural_network import NeuralNetworkRegressor

        np.random.seed(42)
        X = np.random.randn(50, 1)
        y = 2 * X.ravel() + 1

        reg = NeuralNetworkRegressor(
            hidden_units=[8],
            n_epochs=100,
        )
        reg.fit(X, y)

        predictions = reg.predict(X)
        assert predictions.shape == (50,)

    def test_repr(self):
        """Test string representation."""
        from sdk.models.neural_network import LayerConfig, NeuralNetwork, NeuralNetworkConfig

        config = NeuralNetworkConfig(hidden_layers=[LayerConfig(units=32), LayerConfig(units=16)])
        nn = NeuralNetwork(config=config)

        repr_str = repr(nn)
        assert "NeuralNetwork" in repr_str


class TestWeightInitialization:
    """Tests for weight initialization methods."""

    def test_xavier_init(self):
        """Test Xavier initialization."""
        from sdk.models.neural_network import (
            LayerConfig,
            NeuralNetwork,
            NeuralNetworkConfig,
            WeightInit,
        )

        config = NeuralNetworkConfig(
            hidden_layers=[LayerConfig(units=100)],
            weight_init=WeightInit.XAVIER,
            n_epochs=1,
        )
        nn = NeuralNetwork(config=config)

        X = np.random.randn(10, 50)
        y = np.random.randn(10)
        nn.fit(X, y)

        # Check weight magnitudes are reasonable for Xavier
        for W in nn._layer_weights:
            std = np.std(W)
            # Xavier should give roughly sqrt(2/(fan_in + fan_out))
            assert 0.01 < std < 1.0

    def test_he_init(self):
        """Test He initialization."""
        from sdk.models.neural_network import (
            LayerConfig,
            NeuralNetwork,
            NeuralNetworkConfig,
            WeightInit,
        )

        config = NeuralNetworkConfig(
            hidden_layers=[LayerConfig(units=100)],
            weight_init=WeightInit.HE,
            n_epochs=1,
        )
        nn = NeuralNetwork(config=config)

        X = np.random.randn(10, 50)
        y = np.random.randn(10)
        nn.fit(X, y)

        # Check weight magnitudes
        for W in nn._layer_weights:
            std = np.std(W)
            assert 0.01 < std < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

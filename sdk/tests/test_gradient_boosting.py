"""Tests for Gradient Boosting FHE implementation."""

import numpy as np
import pytest
from sklearn.datasets import make_classification, make_regression
from sklearn.model_selection import train_test_split


class TestLossFunctions:
    """Tests for loss functions."""

    def test_mse_loss(self):
        """Test MSE loss."""
        from sdk.models.gradient_boosting import LossFunctions

        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.0, 2.0, 3.0])
        loss = LossFunctions.mse_loss(y_true, y_pred)
        assert loss == 0.0

        y_pred = np.array([2.0, 3.0, 4.0])
        loss = LossFunctions.mse_loss(y_true, y_pred)
        assert loss == 1.0

    def test_mse_negative_gradient(self):
        """Test MSE negative gradient (residuals)."""
        from sdk.models.gradient_boosting import LossFunctions

        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([0.5, 2.5, 2.5])
        grad = LossFunctions.mse_negative_gradient(y_true, y_pred)
        expected = np.array([0.5, -0.5, 0.5])
        np.testing.assert_array_almost_equal(grad, expected)

    def test_mae_loss(self):
        """Test MAE loss."""
        from sdk.models.gradient_boosting import LossFunctions

        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([2.0, 3.0, 4.0])
        loss = LossFunctions.mae_loss(y_true, y_pred)
        assert loss == 1.0

    def test_mae_negative_gradient(self):
        """Test MAE negative gradient."""
        from sdk.models.gradient_boosting import LossFunctions

        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([0.0, 3.0, 2.0])
        grad = LossFunctions.mae_negative_gradient(y_true, y_pred)
        expected = np.array([1.0, -1.0, 1.0])
        np.testing.assert_array_equal(grad, expected)

    def test_log_loss(self):
        """Test log loss."""
        from sdk.models.gradient_boosting import LossFunctions

        y_true = np.array([1.0, 0.0])
        y_pred = np.array([0.9, 0.1])
        loss = LossFunctions.log_loss(y_true, y_pred)
        assert loss < 0.2  # Should be small for good predictions

        y_pred = np.array([0.1, 0.9])
        loss = LossFunctions.log_loss(y_true, y_pred)
        assert loss > 2.0  # Should be large for bad predictions

    def test_huber_loss(self):
        """Test Huber loss."""
        from sdk.models.gradient_boosting import LossFunctions

        y_true = np.array([1.0, 2.0])
        y_pred = np.array([1.0, 2.0])
        loss = LossFunctions.huber_loss(y_true, y_pred)
        assert loss == 0.0

    def test_get_loss_function(self):
        """Test getting loss function by enum."""
        from sdk.models.gradient_boosting import LossFunction, LossFunctions

        for loss in LossFunction:
            func = LossFunctions.get_loss_function(loss)
            assert callable(func)

    def test_get_negative_gradient(self):
        """Test getting negative gradient by enum."""
        from sdk.models.gradient_boosting import LossFunction, LossFunctions

        for loss in LossFunction:
            func = LossFunctions.get_negative_gradient(loss)
            assert callable(func)


class TestGradientBoostingConfig:
    """Tests for GradientBoostingConfig."""

    def test_default_config(self):
        """Test default configuration."""
        from sdk.models.gradient_boosting import GradientBoostingConfig

        config = GradientBoostingConfig()
        assert config.n_estimators == 100
        assert config.max_depth == 3
        assert config.learning_rate == 0.1
        assert config.subsample == 1.0

    def test_invalid_n_estimators(self):
        """Test validation of n_estimators."""
        from sdk.models.gradient_boosting import GradientBoostingConfig

        with pytest.raises(ValueError, match="n_estimators must be at least 1"):
            GradientBoostingConfig(n_estimators=0)

    def test_invalid_learning_rate(self):
        """Test validation of learning_rate."""
        from sdk.models.gradient_boosting import GradientBoostingConfig

        with pytest.raises(ValueError, match="learning_rate must be in"):
            GradientBoostingConfig(learning_rate=0)

        with pytest.raises(ValueError, match="learning_rate must be in"):
            GradientBoostingConfig(learning_rate=1.5)

    def test_invalid_subsample(self):
        """Test validation of subsample."""
        from sdk.models.gradient_boosting import GradientBoostingConfig

        with pytest.raises(ValueError, match="subsample must be in"):
            GradientBoostingConfig(subsample=0)

        with pytest.raises(ValueError, match="subsample must be in"):
            GradientBoostingConfig(subsample=1.5)


class TestGradientBoosting:
    """Tests for GradientBoosting base class."""

    @pytest.fixture
    def regression_data(self):
        """Generate regression data."""
        np.random.seed(42)
        X, y = make_regression(
            n_samples=100, n_features=5, n_informative=3, noise=0.5, random_state=42
        )
        y = (y - y.mean()) / y.std()
        return train_test_split(X, y, test_size=0.2, random_state=42)

    def test_basic_fit(self, regression_data):
        """Test basic fitting."""
        from sdk.models.gradient_boosting import GradientBoosting, GradientBoostingConfig

        X_train, X_test, y_train, y_test = regression_data

        config = GradientBoostingConfig(n_estimators=10, max_depth=2, random_state=42)
        gb = GradientBoosting(config=config)
        gb.fit(X_train, y_train)

        assert gb.is_fitted
        assert gb.n_estimators == 10

    def test_predict(self, regression_data):
        """Test prediction."""
        from sdk.models.gradient_boosting import GradientBoosting, GradientBoostingConfig

        X_train, X_test, y_train, y_test = regression_data

        config = GradientBoostingConfig(n_estimators=20, max_depth=3, random_state=42)
        gb = GradientBoosting(config=config)
        gb.fit(X_train, y_train)

        predictions = gb.predict(X_test)
        assert predictions.shape == (len(X_test),)

    def test_train_loss_decreases(self, regression_data):
        """Test that training loss decreases."""
        from sdk.models.gradient_boosting import GradientBoosting, GradientBoostingConfig

        X_train, _, y_train, _ = regression_data

        config = GradientBoostingConfig(
            n_estimators=50, max_depth=3, learning_rate=0.1, random_state=42
        )
        gb = GradientBoosting(config=config)
        gb.fit(X_train, y_train)

        # Loss should generally decrease
        assert gb._train_losses[-1] < gb._train_losses[0]

    def test_learning_rate_effect(self, regression_data):
        """Test that learning rate affects training."""
        from sdk.models.gradient_boosting import GradientBoosting, GradientBoostingConfig

        X_train, _, y_train, _ = regression_data

        # Small learning rate
        config_small = GradientBoostingConfig(
            n_estimators=20, max_depth=2, learning_rate=0.01, random_state=42
        )
        gb_small = GradientBoosting(config=config_small)
        gb_small.fit(X_train, y_train)

        # Large learning rate
        config_large = GradientBoostingConfig(
            n_estimators=20, max_depth=2, learning_rate=0.5, random_state=42
        )
        gb_large = GradientBoosting(config=config_large)
        gb_large.fit(X_train, y_train)

        # Larger learning rate should have lower loss after same iterations
        assert gb_large._train_losses[-1] < gb_small._train_losses[-1]

    def test_subsample(self, regression_data):
        """Test stochastic gradient boosting (subsampling)."""
        from sdk.models.gradient_boosting import GradientBoosting, GradientBoostingConfig

        X_train, _, y_train, _ = regression_data

        config = GradientBoostingConfig(
            n_estimators=20, max_depth=2, subsample=0.8, random_state=42
        )
        gb = GradientBoosting(config=config)
        gb.fit(X_train, y_train)

        assert gb.is_fitted

    def test_feature_subsampling(self, regression_data):
        """Test feature subsampling."""
        from sdk.models.gradient_boosting import GradientBoosting, GradientBoostingConfig

        X_train, _, y_train, _ = regression_data

        config = GradientBoostingConfig(
            n_estimators=10, max_depth=2, max_features="sqrt", random_state=42
        )
        gb = GradientBoosting(config=config)
        gb.fit(X_train, y_train)

        # Check feature subsets were used
        for fs in gb._feature_subsets:
            if fs is not None:
                assert len(fs) == int(np.sqrt(X_train.shape[1]))

    def test_feature_importances(self, regression_data):
        """Test feature importances."""
        from sdk.models.gradient_boosting import GradientBoosting, GradientBoostingConfig

        X_train, _, y_train, _ = regression_data

        config = GradientBoostingConfig(n_estimators=20, max_depth=3, random_state=42)
        gb = GradientBoosting(config=config)
        gb.fit(X_train, y_train)

        importances = gb.feature_importances_
        assert importances is not None
        assert len(importances) == X_train.shape[1]
        assert np.isclose(importances.sum(), 1.0)

    def test_staged_predict(self, regression_data):
        """Test staged predictions."""
        from sdk.models.gradient_boosting import GradientBoosting, GradientBoostingConfig

        X_train, X_test, y_train, _ = regression_data

        config = GradientBoostingConfig(n_estimators=10, max_depth=2, random_state=42)
        gb = GradientBoosting(config=config)
        gb.fit(X_train, y_train)

        staged_preds = list(gb.staged_predict(X_test))
        assert len(staged_preds) == 10

        # Final staged prediction should match predict()
        np.testing.assert_array_almost_equal(staged_preds[-1], gb.predict(X_test))

    def test_get_params(self, regression_data):
        """Test getting model parameters."""
        from sdk.models.gradient_boosting import GradientBoosting, GradientBoostingConfig

        X_train, _, y_train, _ = regression_data

        config = GradientBoostingConfig(n_estimators=5, max_depth=2, random_state=42)
        gb = GradientBoosting(config=config)
        gb.fit(X_train, y_train)

        params = gb.get_params()
        assert params["n_estimators"] == 5
        assert params["max_depth"] == 2
        assert "trees" in params
        assert "train_losses" in params


class TestGradientBoostingClassifier:
    """Tests for GradientBoostingClassifier."""

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
        from sdk.models.gradient_boosting import GradientBoostingClassifier

        X_train, X_test, y_train, y_test = classification_data

        clf = GradientBoostingClassifier(n_estimators=20, max_depth=3, random_state=42)
        clf.fit(X_train, y_train)

        predictions = clf.predict(X_test)
        assert predictions.shape == (len(X_test),)
        assert set(predictions).issubset({0, 1})

    def test_predict_proba(self, classification_data):
        """Test probability prediction."""
        from sdk.models.gradient_boosting import GradientBoostingClassifier

        X_train, X_test, y_train, y_test = classification_data

        clf = GradientBoostingClassifier(n_estimators=20, max_depth=3, random_state=42)
        clf.fit(X_train, y_train)

        proba = clf.predict_proba(X_test)
        assert proba.shape == (len(X_test), 2)
        # Probabilities should sum to 1
        np.testing.assert_array_almost_equal(proba.sum(axis=1), np.ones(len(X_test)))
        # Probabilities should be in [0, 1]
        assert np.all(proba >= 0) and np.all(proba <= 1)

    def test_accuracy_score(self, classification_data):
        """Test accuracy score computation."""
        from sdk.models.gradient_boosting import GradientBoostingClassifier

        X_train, X_test, y_train, y_test = classification_data

        clf = GradientBoostingClassifier(
            n_estimators=50, max_depth=3, learning_rate=0.1, random_state=42
        )
        clf.fit(X_train, y_train)

        accuracy = clf.score(X_test, y_test)
        assert 0.0 <= accuracy <= 1.0
        # Should achieve reasonable accuracy
        assert accuracy > 0.5

    def test_staged_predict_proba(self, classification_data):
        """Test staged probability predictions."""
        from sdk.models.gradient_boosting import GradientBoostingClassifier

        X_train, X_test, y_train, _ = classification_data

        clf = GradientBoostingClassifier(n_estimators=10, max_depth=2, random_state=42)
        clf.fit(X_train, y_train)

        staged_proba = list(clf.staged_predict_proba(X_test))
        assert len(staged_proba) == 10

        # All should have shape (n_samples, 2)
        for proba in staged_proba:
            assert proba.shape == (len(X_test), 2)


class TestGradientBoostingRegressor:
    """Tests for GradientBoostingRegressor."""

    @pytest.fixture
    def regression_data(self):
        """Generate regression data."""
        np.random.seed(42)
        X, y = make_regression(
            n_samples=100, n_features=5, n_informative=3, noise=0.5, random_state=42
        )
        y = (y - y.mean()) / y.std()
        return train_test_split(X, y, test_size=0.2, random_state=42)

    def test_basic_regression(self, regression_data):
        """Test basic regression."""
        from sdk.models.gradient_boosting import GradientBoostingRegressor

        X_train, X_test, y_train, y_test = regression_data

        reg = GradientBoostingRegressor(n_estimators=50, max_depth=3, random_state=42)
        reg.fit(X_train, y_train)

        predictions = reg.predict(X_test)
        assert predictions.shape == (len(X_test),)

    def test_r2_score(self, regression_data):
        """Test R² score computation."""
        from sdk.models.gradient_boosting import GradientBoostingRegressor

        X_train, X_test, y_train, y_test = regression_data

        reg = GradientBoostingRegressor(
            n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42
        )
        reg.fit(X_train, y_train)

        r2 = reg.score(X_test, y_test)
        # Should be better than random baseline
        assert r2 > 0

    def test_mae_loss(self, regression_data):
        """Test with MAE loss."""
        from sdk.models.gradient_boosting import GradientBoostingRegressor

        X_train, X_test, y_train, _ = regression_data

        reg = GradientBoostingRegressor(n_estimators=30, max_depth=3, loss="mae", random_state=42)
        reg.fit(X_train, y_train)

        predictions = reg.predict(X_test)
        assert predictions.shape == (len(X_test),)

    def test_huber_loss(self, regression_data):
        """Test with Huber loss."""
        from sdk.models.gradient_boosting import GradientBoostingRegressor

        X_train, X_test, y_train, _ = regression_data

        reg = GradientBoostingRegressor(n_estimators=30, max_depth=3, loss="huber", random_state=42)
        reg.fit(X_train, y_train)

        predictions = reg.predict(X_test)
        assert predictions.shape == (len(X_test),)


class TestEarlyStopping:
    """Tests for early stopping."""

    def test_early_stopping_regression(self):
        """Test early stopping for regression."""
        from sdk.models.gradient_boosting import GradientBoostingRegressor

        np.random.seed(42)
        X, y = make_regression(n_samples=100, n_features=5, noise=0.5, random_state=42)
        y = (y - y.mean()) / y.std()

        reg = GradientBoostingRegressor(
            n_estimators=500,  # Large number
            max_depth=3,
            n_iter_no_change=10,
            random_state=42,
        )
        reg.fit(X, y)

        # Should stop before 500
        assert reg.n_estimators < 500

    def test_early_stopping_classification(self):
        """Test early stopping for classification."""
        from sdk.models.gradient_boosting import GradientBoostingClassifier

        X, y = make_classification(n_samples=100, n_features=5, random_state=42)

        clf = GradientBoostingClassifier(
            n_estimators=500, max_depth=3, n_iter_no_change=10, random_state=42
        )
        clf.fit(X, y)

        # Should stop before 500
        assert clf.n_estimators < 500


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_predict_before_fit(self):
        """Test prediction before fitting raises error."""
        from sdk.models.gradient_boosting import GradientBoostingClassifier

        clf = GradientBoostingClassifier(n_estimators=10)
        X = np.random.randn(10, 5)

        with pytest.raises(RuntimeError, match="must be fitted"):
            clf.predict(X)

    def test_encrypted_training_not_supported(self):
        """Test that encrypted training raises appropriate error."""
        from sdk.models.gradient_boosting import GradientBoostingRegressor

        reg = GradientBoostingRegressor(n_estimators=10)

        class FakeEncrypted:
            pass

        with pytest.raises((ValueError, TypeError, AttributeError)):
            reg.fit(FakeEncrypted(), np.array([1, 2, 3]))

    def test_single_feature(self):
        """Test with single feature."""
        from sdk.models.gradient_boosting import GradientBoostingRegressor

        np.random.seed(42)
        X = np.random.randn(50, 1)
        y = 2 * X.ravel() + 1 + 0.1 * np.random.randn(50)

        reg = GradientBoostingRegressor(n_estimators=20, max_depth=2, random_state=42)
        reg.fit(X, y)

        predictions = reg.predict(X)
        assert predictions.shape == (50,)

    def test_repr(self):
        """Test string representation."""
        from sdk.models.gradient_boosting import (
            GradientBoosting,
            GradientBoostingConfig,
        )

        config = GradientBoostingConfig(n_estimators=100, max_depth=3)
        gb = GradientBoosting(config=config)

        repr_str = repr(gb)
        assert "GradientBoosting" in repr_str
        assert "n_estimators=0/100" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

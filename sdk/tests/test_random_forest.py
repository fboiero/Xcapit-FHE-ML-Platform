"""Tests for Random Forest FHE implementation."""

import numpy as np
import pytest
from sklearn.datasets import make_classification, make_regression
from sklearn.model_selection import train_test_split


class TestRandomForestConfig:
    """Tests for RandomForestConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        from sdk.models.random_forest import RandomForestConfig

        config = RandomForestConfig()
        assert config.n_estimators == 10
        assert config.max_depth == 3
        assert config.max_features == 'sqrt'
        assert config.bootstrap is True
        assert config.bootstrap_ratio == 1.0

    def test_invalid_n_estimators(self):
        """Test validation of n_estimators."""
        from sdk.models.random_forest import RandomForestConfig

        with pytest.raises(ValueError, match="n_estimators must be at least 1"):
            RandomForestConfig(n_estimators=0)

    def test_invalid_max_depth(self):
        """Test validation of max_depth."""
        from sdk.models.random_forest import RandomForestConfig

        with pytest.raises(ValueError, match="max_depth must be at least 1"):
            RandomForestConfig(max_depth=0)

    def test_invalid_bootstrap_ratio(self):
        """Test validation of bootstrap_ratio."""
        from sdk.models.random_forest import RandomForestConfig

        with pytest.raises(ValueError, match="bootstrap_ratio must be in"):
            RandomForestConfig(bootstrap_ratio=0)

        with pytest.raises(ValueError, match="bootstrap_ratio must be in"):
            RandomForestConfig(bootstrap_ratio=1.5)


class TestRandomForest:
    """Tests for RandomForest base class."""

    @pytest.fixture
    def regression_data(self):
        """Generate regression data."""
        X, y = make_regression(
            n_samples=100,
            n_features=10,
            n_informative=5,
            noise=0.1,
            random_state=42
        )
        return train_test_split(X, y, test_size=0.2, random_state=42)

    def test_basic_fit(self, regression_data):
        """Test basic fitting."""
        from sdk.models.random_forest import RandomForest, RandomForestConfig

        X_train, X_test, y_train, y_test = regression_data

        config = RandomForestConfig(n_estimators=5, max_depth=2, random_state=42)
        forest = RandomForest(config=config)
        forest.fit(X_train, y_train)

        assert forest.is_fitted
        assert len(forest.trees) == 5

    def test_predict(self, regression_data):
        """Test prediction."""
        from sdk.models.random_forest import RandomForest, RandomForestConfig

        X_train, X_test, y_train, y_test = regression_data

        config = RandomForestConfig(n_estimators=5, max_depth=3, random_state=42)
        forest = RandomForest(config=config)
        forest.fit(X_train, y_train)

        predictions = forest.predict(X_test)
        assert predictions.shape == (len(X_test),)

    def test_feature_importances(self, regression_data):
        """Test feature importances computation."""
        from sdk.models.random_forest import RandomForest, RandomForestConfig

        X_train, X_test, y_train, y_test = regression_data

        config = RandomForestConfig(n_estimators=5, max_depth=3, random_state=42)
        forest = RandomForest(config=config)
        forest.fit(X_train, y_train)

        importances = forest.feature_importances_
        assert importances is not None
        assert len(importances) == X_train.shape[1]
        assert np.isclose(importances.sum(), 1.0)  # Should sum to 1

    def test_max_features_sqrt(self, regression_data):
        """Test sqrt max_features."""
        from sdk.models.random_forest import RandomForest, RandomForestConfig

        X_train, _, y_train, _ = regression_data

        config = RandomForestConfig(
            n_estimators=3,
            max_features='sqrt',
            random_state=42
        )
        forest = RandomForest(config=config)
        forest.fit(X_train, y_train)

        # Check that each tree uses sqrt(n_features) features
        expected = int(np.sqrt(X_train.shape[1]))
        for subset in forest._feature_subsets:
            assert len(subset) == expected

    def test_max_features_log2(self, regression_data):
        """Test log2 max_features."""
        from sdk.models.random_forest import RandomForest, RandomForestConfig

        X_train, _, y_train, _ = regression_data

        config = RandomForestConfig(
            n_estimators=3,
            max_features='log2',
            random_state=42
        )
        forest = RandomForest(config=config)
        forest.fit(X_train, y_train)

        expected = int(np.log2(X_train.shape[1]))
        for subset in forest._feature_subsets:
            assert len(subset) == expected

    def test_max_features_float(self, regression_data):
        """Test float max_features (fraction)."""
        from sdk.models.random_forest import RandomForest, RandomForestConfig

        X_train, _, y_train, _ = regression_data

        config = RandomForestConfig(
            n_estimators=3,
            max_features=0.5,
            random_state=42
        )
        forest = RandomForest(config=config)
        forest.fit(X_train, y_train)

        expected = int(0.5 * X_train.shape[1])
        for subset in forest._feature_subsets:
            assert len(subset) == expected

    def test_max_features_int(self, regression_data):
        """Test int max_features."""
        from sdk.models.random_forest import RandomForest, RandomForestConfig

        X_train, _, y_train, _ = regression_data

        config = RandomForestConfig(
            n_estimators=3,
            max_features=4,
            random_state=42
        )
        forest = RandomForest(config=config)
        forest.fit(X_train, y_train)

        for subset in forest._feature_subsets:
            assert len(subset) == 4

    def test_no_bootstrap(self, regression_data):
        """Test training without bootstrap."""
        from sdk.models.random_forest import RandomForest, RandomForestConfig

        X_train, _, y_train, _ = regression_data

        config = RandomForestConfig(
            n_estimators=3,
            bootstrap=False,
            random_state=42
        )
        forest = RandomForest(config=config)
        forest.fit(X_train, y_train)

        assert forest.is_fitted

    def test_get_params(self, regression_data):
        """Test getting model parameters."""
        from sdk.models.random_forest import RandomForest, RandomForestConfig

        X_train, _, y_train, _ = regression_data

        config = RandomForestConfig(n_estimators=3, max_depth=2, random_state=42)
        forest = RandomForest(config=config)
        forest.fit(X_train, y_train)

        params = forest.get_params()
        assert params["n_estimators"] == 3
        assert params["max_depth"] == 2
        assert "trees" in params
        assert len(params["trees"]) == 3


class TestRandomForestClassifier:
    """Tests for RandomForestClassifier."""

    @pytest.fixture
    def classification_data(self):
        """Generate classification data."""
        X, y = make_classification(
            n_samples=100,
            n_features=10,
            n_informative=5,
            n_redundant=2,
            n_classes=2,
            random_state=42
        )
        return train_test_split(X, y, test_size=0.2, random_state=42)

    def test_basic_classification(self, classification_data):
        """Test basic classification."""
        from sdk.models.random_forest import RandomForestClassifier

        X_train, X_test, y_train, y_test = classification_data

        clf = RandomForestClassifier(
            n_estimators=5,
            max_depth=3,
            random_state=42
        )
        clf.fit(X_train, y_train)

        predictions = clf.predict(X_test)
        assert predictions.shape == (len(X_test),)
        assert set(predictions).issubset({0, 1})

    def test_predict_proba(self, classification_data):
        """Test probability prediction."""
        from sdk.models.random_forest import RandomForestClassifier

        X_train, X_test, y_train, y_test = classification_data

        clf = RandomForestClassifier(
            n_estimators=5,
            max_depth=3,
            n_classes=2,
            random_state=42
        )
        clf.fit(X_train, y_train)

        proba = clf.predict_proba(X_test)
        assert proba.shape == (len(X_test), 2)
        assert np.allclose(proba.sum(axis=1), 1.0)  # Should sum to 1

    def test_score(self, classification_data):
        """Test accuracy score computation."""
        from sdk.models.random_forest import RandomForestClassifier

        X_train, X_test, y_train, y_test = classification_data

        clf = RandomForestClassifier(
            n_estimators=10,
            max_depth=4,
            random_state=42
        )
        clf.fit(X_train, y_train)

        accuracy = clf.score(X_test, y_test)
        assert 0.0 <= accuracy <= 1.0
        # Random Forest should achieve reasonable accuracy on simple data
        assert accuracy > 0.5

    def test_multiclass(self):
        """Test multi-class classification."""
        from sdk.models.random_forest import RandomForestClassifier

        X, y = make_classification(
            n_samples=100,
            n_features=10,
            n_informative=5,
            n_classes=3,
            n_clusters_per_class=1,
            random_state=42
        )
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        clf = RandomForestClassifier(
            n_estimators=10,
            max_depth=3,
            n_classes=3,
            random_state=42
        )
        clf.fit(X_train, y_train)

        predictions = clf.predict(X_test)
        assert set(predictions).issubset({0, 1, 2})

        proba = clf.predict_proba(X_test)
        assert proba.shape == (len(X_test), 3)


class TestRandomForestRegressor:
    """Tests for RandomForestRegressor."""

    @pytest.fixture
    def regression_data(self):
        """Generate regression data."""
        X, y = make_regression(
            n_samples=100,
            n_features=10,
            n_informative=5,
            noise=0.1,
            random_state=42
        )
        return train_test_split(X, y, test_size=0.2, random_state=42)

    def test_basic_regression(self, regression_data):
        """Test basic regression."""
        from sdk.models.random_forest import RandomForestRegressor

        X_train, X_test, y_train, y_test = regression_data

        reg = RandomForestRegressor(
            n_estimators=10,
            max_depth=4,
            random_state=42
        )
        reg.fit(X_train, y_train)

        predictions = reg.predict(X_test)
        assert predictions.shape == (len(X_test),)

    def test_score(self, regression_data):
        """Test R² score computation."""
        from sdk.models.random_forest import RandomForestRegressor

        X_train, X_test, y_train, y_test = regression_data

        reg = RandomForestRegressor(
            n_estimators=20,
            max_depth=5,
            random_state=42
        )
        reg.fit(X_train, y_train)

        r2 = reg.score(X_test, y_test)
        # R² should be reasonable for well-fitting model
        assert r2 > 0  # At least better than mean baseline

    def test_convenience_init(self, regression_data):
        """Test convenience initialization with kwargs."""
        from sdk.models.random_forest import RandomForestRegressor

        X_train, X_test, y_train, y_test = regression_data

        reg = RandomForestRegressor(
            n_estimators=5,
            max_depth=2,
            max_features='log2',
            bootstrap=False,
            random_state=123
        )
        reg.fit(X_train, y_train)

        assert reg.is_fitted
        assert reg.n_estimators == 5


class TestAggregationMethods:
    """Tests for different aggregation methods."""

    @pytest.fixture
    def data(self):
        """Generate test data."""
        X, y = make_regression(
            n_samples=100,
            n_features=5,
            noise=0.1,
            random_state=42
        )
        return train_test_split(X, y, test_size=0.2, random_state=42)

    def test_average_aggregation(self, data):
        """Test average aggregation."""
        from sdk.models.random_forest import (
            AggregationMethod,
            RandomForest,
            RandomForestConfig,
        )

        X_train, X_test, y_train, _ = data

        config = RandomForestConfig(
            n_estimators=5,
            aggregation=AggregationMethod.AVERAGE,
            random_state=42
        )
        forest = RandomForest(config=config)
        forest.fit(X_train, y_train)

        predictions = forest.predict(X_test)
        assert predictions is not None

    def test_weighted_aggregation(self, data):
        """Test weighted aggregation."""
        from sdk.models.random_forest import (
            AggregationMethod,
            RandomForest,
            RandomForestConfig,
        )

        X_train, X_test, y_train, _ = data

        config = RandomForestConfig(
            n_estimators=5,
            aggregation=AggregationMethod.WEIGHTED,
            random_state=42
        )
        forest = RandomForest(config=config)
        forest.fit(X_train, y_train)

        # Check that weights are computed
        assert forest._tree_weights is not None
        assert np.isclose(forest._tree_weights.sum(), 1.0)

        predictions = forest.predict(X_test)
        assert predictions is not None


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_predict_before_fit(self):
        """Test prediction before fitting raises error."""
        from sdk.models.random_forest import RandomForestClassifier

        clf = RandomForestClassifier(n_estimators=3)
        X = np.random.randn(10, 5)

        with pytest.raises(RuntimeError, match="must be fitted"):
            clf.predict(X)

    def test_encrypted_training_not_supported(self):
        """Test that encrypted training raises appropriate error."""
        from sdk.models.random_forest import RandomForestRegressor

        reg = RandomForestRegressor(n_estimators=3)

        # This should fail since we can't train on encrypted data
        # We simulate an encrypted-like object
        class FakeEncrypted:
            pass

        with pytest.raises((ValueError, TypeError, AttributeError)):
            reg.fit(FakeEncrypted(), np.array([1, 2, 3]))

    def test_single_feature(self):
        """Test with single feature."""
        from sdk.models.random_forest import RandomForestRegressor

        X = np.random.randn(50, 1)
        y = 2 * X.ravel() + 1

        reg = RandomForestRegressor(
            n_estimators=5,
            max_depth=2,
            max_features=None,  # Use all (1) feature
            random_state=42
        )
        reg.fit(X, y)

        predictions = reg.predict(X)
        assert predictions.shape == (50,)

    def test_repr(self):
        """Test string representation."""
        from sdk.models.random_forest import RandomForest, RandomForestConfig

        config = RandomForestConfig(n_estimators=10, max_depth=5)
        forest = RandomForest(config=config)

        repr_str = repr(forest)
        assert "RandomForest" in repr_str
        assert "n_estimators=10" in repr_str
        assert "max_depth=5" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

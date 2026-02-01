"""Tests for new SDK models: Anomaly Detection, Time Series, Regularization, Feature Selection."""

import numpy as np
import pytest


class TestAnomalyDetection:
    """Tests for anomaly detection models."""

    @pytest.fixture
    def normal_data(self):
        """Generate normal data with some outliers."""
        np.random.seed(42)
        # Normal data
        X_normal = np.random.randn(100, 5)
        # Outliers
        X_outliers = np.random.randn(10, 5) * 5 + 10
        X = np.vstack([X_normal, X_outliers])
        y = np.array([1] * 100 + [-1] * 10)
        return X, y

    def test_isolation_forest_fit_predict(self, normal_data):
        """Test Isolation Forest fit and predict."""
        from sdk.models.anomaly_detection import IsolationForest

        X, y_true = normal_data

        model = IsolationForest(n_estimators=50, contamination=0.1, random_state=42)
        model.fit(X)

        predictions = model.predict(X)
        assert predictions.shape == (110,)
        assert set(predictions) == {-1, 1}

        # Check that most normal points are predicted as inliers
        normal_preds = predictions[:100]
        assert np.mean(normal_preds == 1) > 0.8

    def test_isolation_forest_decision_function(self, normal_data):
        """Test Isolation Forest decision function."""
        from sdk.models.anomaly_detection import IsolationForest

        X, _ = normal_data

        model = IsolationForest(n_estimators=50, random_state=42)
        model.fit(X)

        scores = model.decision_function(X)
        assert scores.shape == (110,)

        # Outliers should have lower scores
        normal_scores = scores[:100]
        outlier_scores = scores[100:]
        assert np.mean(normal_scores) > np.mean(outlier_scores)

    def test_one_class_svm_fit_predict(self, normal_data):
        """Test One-Class SVM fit and predict."""
        from sdk.models.anomaly_detection import OneClassSVM

        X, _ = normal_data
        X_train = X[:100]  # Train only on normal data

        model = OneClassSVM(kernel="polynomial", nu=0.1, random_state=42)
        model.fit(X_train)

        predictions = model.predict(X)
        assert predictions.shape == (110,)

    def test_local_outlier_factor(self, normal_data):
        """Test Local Outlier Factor."""
        from sdk.models.anomaly_detection import LocalOutlierFactor

        X, _ = normal_data

        model = LocalOutlierFactor(n_neighbors=10, contamination=0.1)
        model.fit(X[:100])  # Train on normal data

        predictions = model.predict(X)
        assert predictions.shape == (110,)

    def test_elliptic_envelope(self, normal_data):
        """Test Elliptic Envelope."""
        from sdk.models.anomaly_detection import EllipticEnvelope

        X, _ = normal_data

        model = EllipticEnvelope(contamination=0.1, random_state=42)
        model.fit(X)

        predictions = model.predict(X)
        assert predictions.shape == (110,)

        # Check Mahalanobis distance
        mahal = model.mahalanobis(X)
        assert mahal.shape == (110,)


class TestTimeSeries:
    """Tests for time series models."""

    @pytest.fixture
    def time_series_data(self):
        """Generate simple time series data."""
        np.random.seed(42)
        n = 100
        t = np.arange(n)
        # Trend + seasonality + noise
        y = 0.1 * t + 5 * np.sin(2 * np.pi * t / 12) + np.random.randn(n) * 0.5
        return y

    def test_arima_fit_predict(self, time_series_data):
        """Test ARIMA fit and predict."""
        from sdk.models.time_series import ARIMA

        y = time_series_data

        model = ARIMA(p=2, d=1, q=1)
        model.fit(y)

        forecast = model.predict(steps=10)
        assert forecast.shape == (10,)
        assert not np.any(np.isnan(forecast))

    def test_arima_with_confidence_intervals(self, time_series_data):
        """Test ARIMA with confidence intervals."""
        from sdk.models.time_series import ARIMA

        y = time_series_data

        model = ARIMA(p=1, d=1, q=0)
        model.fit(y)

        forecast, conf_int = model.predict(steps=5, return_conf_int=True)
        assert forecast.shape == (5,)
        assert conf_int.shape == (5, 2)
        # Lower bound should be less than upper bound
        assert np.all(conf_int[:, 0] < conf_int[:, 1])

    def test_exponential_smoothing(self, time_series_data):
        """Test Exponential Smoothing."""
        from sdk.models.time_series import ExponentialSmoothing

        y = time_series_data

        model = ExponentialSmoothing(trend="add", seasonal="add", seasonal_period=12)
        model.fit(y)

        forecast = model.predict(steps=12)
        assert forecast.shape == (12,)

    def test_simple_moving_average(self, time_series_data):
        """Test Simple Moving Average."""
        from sdk.models.time_series import SimpleMovingAverage

        y = time_series_data

        model = SimpleMovingAverage(window=5)
        model.fit(y)

        forecast = model.predict(steps=10)
        assert forecast.shape == (10,)

    def test_prophet_like(self, time_series_data):
        """Test Prophet-like model."""
        from sdk.models.time_series import ProphetLike

        y = time_series_data

        model = ProphetLike(
            yearly_seasonality=True,
            weekly_seasonality=False,
        )
        model.fit(y)

        forecast = model.predict(steps=10)
        assert forecast.shape == (10,)


class TestRegularization:
    """Tests for regularized linear models."""

    @pytest.fixture
    def regression_data(self):
        """Generate regression data."""
        np.random.seed(42)
        n, p = 100, 20
        X = np.random.randn(n, p)
        # True coefficients (sparse)
        true_coef = np.zeros(p)
        true_coef[:5] = [1, -2, 3, -4, 5]
        y = X @ true_coef + np.random.randn(n) * 0.5
        return X, y, true_coef

    def test_ridge_fit_predict(self, regression_data):
        """Test Ridge regression."""
        from sdk.models.regularization import Ridge

        X, y, _ = regression_data

        model = Ridge(alpha=1.0)
        model.fit(X, y)

        predictions = model.predict(X)
        assert predictions.shape == y.shape

        score = model.score(X, y)
        assert 0 < score <= 1

    def test_ridge_regularization_effect(self, regression_data):
        """Test that Ridge regularization shrinks coefficients."""
        from sdk.models.regularization import Ridge

        X, y, _ = regression_data

        model_low = Ridge(alpha=0.1)
        model_low.fit(X, y)

        model_high = Ridge(alpha=100.0)
        model_high.fit(X, y)

        # Higher alpha should result in smaller coefficients
        assert np.linalg.norm(model_high.coef_) < np.linalg.norm(model_low.coef_)

    def test_lasso_fit_predict(self, regression_data):
        """Test Lasso regression."""
        from sdk.models.regularization import Lasso

        X, y, _ = regression_data

        model = Lasso(alpha=0.1, max_iter=1000)
        model.fit(X, y)

        predictions = model.predict(X)
        assert predictions.shape == y.shape

    def test_lasso_sparsity(self, regression_data):
        """Test that Lasso produces sparse solutions."""
        from sdk.models.regularization import Lasso

        X, y, _ = regression_data

        model = Lasso(alpha=0.5, max_iter=1000)
        model.fit(X, y)

        # Count near-zero coefficients
        n_zeros = np.sum(np.abs(model.coef_) < 0.01)
        assert n_zeros > 5  # Should have some zeros

    def test_elastic_net_fit_predict(self, regression_data):
        """Test Elastic Net regression."""
        from sdk.models.regularization import ElasticNet

        X, y, _ = regression_data

        model = ElasticNet(alpha=0.1, l1_ratio=0.5, max_iter=1000)
        model.fit(X, y)

        predictions = model.predict(X)
        assert predictions.shape == y.shape

    def test_ridge_classifier(self, regression_data):
        """Test Ridge Classifier."""
        from sdk.models.regularization import RidgeClassifier

        X, _, _ = regression_data
        y = (X[:, 0] > 0).astype(int)

        model = RidgeClassifier(alpha=1.0)
        model.fit(X, y)

        predictions = model.predict(X)
        assert predictions.shape == y.shape
        assert set(predictions) <= {0, 1}

    def test_sgd_regressor(self, regression_data):
        """Test SGD Regressor."""
        from sdk.models.regularization import SGDRegressor

        X, y, _ = regression_data

        model = SGDRegressor(
            loss="squared_error",
            penalty="l2",
            max_iter=1000,
            random_state=42,
        )
        model.fit(X, y)

        predictions = model.predict(X)
        assert predictions.shape == y.shape


class TestFeatureSelection:
    """Tests for feature selection methods."""

    @pytest.fixture
    def feature_data(self):
        """Generate data with informative and noise features."""
        np.random.seed(42)
        n = 100

        # Informative features
        X_info = np.random.randn(n, 5)
        y = (X_info[:, 0] + X_info[:, 1] - X_info[:, 2] > 0).astype(int)

        # Noise features
        X_noise = np.random.randn(n, 10)

        X = np.hstack([X_info, X_noise])
        return X, y

    def test_variance_threshold(self, feature_data):
        """Test VarianceThreshold."""
        from sdk.models.feature_selection import VarianceThreshold

        X, _ = feature_data

        # Add a constant feature
        X_with_constant = np.hstack([X, np.ones((len(X), 1))])

        selector = VarianceThreshold(threshold=0.0)
        X_selected = selector.fit_transform(X_with_constant)

        # Constant feature should be removed
        assert X_selected.shape[1] == X.shape[1]

    def test_select_k_best(self, feature_data):
        """Test SelectKBest."""
        from sdk.models.feature_selection import SelectKBest

        X, y = feature_data

        selector = SelectKBest(score_func="f_classif", k=5)
        X_selected = selector.fit_transform(X, y)

        assert X_selected.shape == (100, 5)

        # Check that informative features have higher scores
        scores = selector.scores_
        assert np.mean(scores[:5]) > np.mean(scores[5:])

    def test_select_percentile(self, feature_data):
        """Test SelectPercentile."""
        from sdk.models.feature_selection import SelectPercentile

        X, y = feature_data

        selector = SelectPercentile(percentile=30)
        X_selected = selector.fit_transform(X, y)

        # Should select about 30% of features
        assert X_selected.shape[1] <= 5

    def test_f_classif_scores(self, feature_data):
        """Test f_classif score function."""
        from sdk.models.feature_selection import f_classif

        X, y = feature_data

        scores, pvalues = f_classif(X, y)
        assert scores.shape == (15,)
        assert np.all(scores >= 0)

    def test_f_regression_scores(self):
        """Test f_regression score function."""
        from sdk.models.feature_selection import f_regression

        np.random.seed(42)
        X = np.random.randn(100, 10)
        y = X[:, 0] + 2 * X[:, 1] + np.random.randn(100) * 0.1

        scores, _ = f_regression(X, y)
        assert scores.shape == (10,)

        # First two features should have highest scores
        top_2 = np.argsort(scores)[-2:]
        assert 0 in top_2
        assert 1 in top_2

    def test_chi2_scores(self, feature_data):
        """Test chi2 score function."""
        from sdk.models.feature_selection import chi2

        X, y = feature_data
        X_positive = np.abs(X)  # chi2 requires non-negative

        scores, _ = chi2(X_positive, y)
        assert scores.shape == (15,)

    def test_mutual_info_classif(self, feature_data):
        """Test mutual information for classification."""
        from sdk.models.feature_selection import mutual_info_classif

        X, y = feature_data

        mi_scores = mutual_info_classif(X, y)
        assert mi_scores.shape == (15,)
        assert np.all(mi_scores >= 0)


class TestHyperparameterTuning:
    """Tests for hyperparameter tuning methods."""

    @pytest.fixture
    def simple_classifier(self):
        """Simple classifier for testing."""
        from sdk.models.regularization import RidgeClassifier

        return RidgeClassifier

    @pytest.fixture
    def classification_data(self):
        """Generate classification data."""
        np.random.seed(42)
        X = np.random.randn(100, 5)
        y = (X[:, 0] + X[:, 1] > 0).astype(int)
        return X, y

    def test_randomized_search_cv(self, simple_classifier, classification_data):
        """Test RandomizedSearchCV."""
        from sdk.evaluation.hyperparameter_tuning import RandomizedSearchCV

        X, y = classification_data

        param_dist = {
            "alpha": {"type": "log_uniform", "low": 0.01, "high": 10.0},
        }

        search = RandomizedSearchCV(
            simple_classifier(),
            param_dist,
            n_iter=5,
            cv=3,
            random_state=42,
        )
        search.fit(X, y)

        assert search.best_params_ is not None
        assert search.best_score_ is not None
        assert search.best_estimator_ is not None

    def test_parameter_sampler(self):
        """Test ParameterSampler."""
        from sdk.evaluation.hyperparameter_tuning import ParameterSampler

        param_dist = {
            "alpha": {"type": "uniform", "low": 0.1, "high": 1.0},
            "max_iter": {"type": "int_uniform", "low": 100, "high": 500},
            "solver": ["auto", "svd"],
        }

        sampler = ParameterSampler(param_dist, n_iter=10, random_state=42)
        samples = list(sampler)

        assert len(samples) == 10
        for params in samples:
            assert 0.1 <= params["alpha"] <= 1.0
            assert 100 <= params["max_iter"] <= 500
            assert params["solver"] in ["auto", "svd"]

    def test_bayesian_optimization(self, simple_classifier, classification_data):
        """Test BayesianOptimization."""
        from sdk.evaluation.hyperparameter_tuning import BayesianOptimization

        X, y = classification_data

        param_bounds = {
            "alpha": (0.01, 10.0, "log"),
        }

        opt = BayesianOptimization(
            simple_classifier(),
            param_bounds,
            n_iter=10,
            n_initial_points=3,
            cv=3,
            random_state=42,
        )
        opt.fit(X, y)

        assert opt.best_params_ is not None
        assert opt.best_score_ is not None

    def test_halving_random_search(self, simple_classifier, classification_data):
        """Test HalvingRandomSearchCV."""
        from sdk.evaluation.hyperparameter_tuning import HalvingRandomSearchCV

        X, y = classification_data

        param_dist = {
            "alpha": {"type": "log_uniform", "low": 0.01, "high": 10.0},
        }

        search = HalvingRandomSearchCV(
            simple_classifier(),
            param_dist,
            n_candidates=10,
            factor=2,
            min_resources=20,
            cv=3,
            random_state=42,
        )
        search.fit(X, y)

        assert search.best_params_ is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

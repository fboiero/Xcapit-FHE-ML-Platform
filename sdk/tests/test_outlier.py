"""
Tests for the outlier detection module.
"""

import numpy as np
import pytest

from sdk.outlier import (
    IsolationForest,
    LocalOutlierFactor,
    EllipticEnvelope,
    OneClassSVM,
    detect_outliers_zscore,
    detect_outliers_iqr,
    detect_outliers_mad,
    detect_outliers_dbscan,
    get_outlier_scores,
)


def create_test_data_with_outliers():
    """Create test data with known outliers."""
    np.random.seed(42)
    # Normal data
    normal = np.random.randn(100, 2) * 0.5 + np.array([5, 5])
    # Outliers
    outliers = np.array([[0, 0], [10, 10], [-5, 15], [15, -5]])
    return np.vstack([normal, outliers])


class TestIsolationForest:
    """Tests for IsolationForest."""

    def test_fit_predict(self):
        """Test basic fit and predict."""
        X = create_test_data_with_outliers()
        clf = IsolationForest(n_estimators=50, contamination=0.05)

        clf.fit(X)
        predictions = clf.predict(X)

        assert len(predictions) == len(X)
        assert set(predictions).issubset({-1, 1})  # -1 for outliers, 1 for inliers

    def test_fit_predict_combined(self):
        """Test fit_predict method."""
        X = create_test_data_with_outliers()
        clf = IsolationForest(n_estimators=50, contamination=0.05)

        predictions = clf.fit_predict(X)

        assert len(predictions) == len(X)

    def test_score_samples(self):
        """Test anomaly score calculation."""
        X = create_test_data_with_outliers()
        clf = IsolationForest(n_estimators=50, contamination=0.05)

        clf.fit(X)
        scores = clf.score_samples(X)

        assert len(scores) == len(X)
        # Outliers should have lower (more negative) scores
        # Last 4 samples are outliers

    def test_decision_function(self):
        """Test decision function."""
        X = create_test_data_with_outliers()
        clf = IsolationForest(n_estimators=50)

        clf.fit(X)
        decisions = clf.decision_function(X)

        assert len(decisions) == len(X)

    def test_get_params(self):
        """Test parameter retrieval."""
        clf = IsolationForest(n_estimators=100, contamination=0.1)

        params = clf.get_params()

        assert params["n_estimators"] == 100
        assert params["contamination"] == 0.1


class TestLocalOutlierFactor:
    """Tests for LocalOutlierFactor."""

    def test_fit_predict(self):
        """Test basic fit and predict."""
        X = create_test_data_with_outliers()
        clf = LocalOutlierFactor(n_neighbors=20, contamination=0.05)

        predictions = clf.fit_predict(X)

        assert len(predictions) == len(X)
        assert set(predictions).issubset({-1, 1})

    def test_novelty_mode(self):
        """Test novelty detection mode."""
        X_train = np.random.randn(50, 2) * 0.5 + np.array([5, 5])
        X_test = np.array([[0, 0], [5, 5], [10, 10]])

        clf = LocalOutlierFactor(n_neighbors=10, novelty=True)
        clf.fit(X_train)
        predictions = clf.predict(X_test)

        assert len(predictions) == len(X_test)

    def test_negative_outlier_factor(self):
        """Test negative outlier factor scores."""
        X = create_test_data_with_outliers()
        clf = LocalOutlierFactor(n_neighbors=20)

        clf.fit_predict(X)
        nof = clf.negative_outlier_factor_

        assert len(nof) == len(X)
        # Outliers should have more negative scores


class TestEllipticEnvelope:
    """Tests for EllipticEnvelope."""

    def test_fit_predict(self):
        """Test basic fit and predict."""
        X = create_test_data_with_outliers()
        clf = EllipticEnvelope(contamination=0.05)

        clf.fit(X)
        predictions = clf.predict(X)

        assert len(predictions) == len(X)
        assert set(predictions).issubset({-1, 1})

    def test_decision_function(self):
        """Test decision function (Mahalanobis distance)."""
        X = create_test_data_with_outliers()
        clf = EllipticEnvelope(contamination=0.05)

        clf.fit(X)
        decisions = clf.decision_function(X)

        assert len(decisions) == len(X)

    def test_mahalanobis_distances(self):
        """Test Mahalanobis distance calculation."""
        X = create_test_data_with_outliers()
        clf = EllipticEnvelope()

        clf.fit(X)
        distances = clf.mahalanobis(X)

        assert len(distances) == len(X)
        # Outliers should have larger distances


class TestOneClassSVM:
    """Tests for OneClassSVM."""

    def test_fit_predict(self):
        """Test basic fit and predict."""
        X = create_test_data_with_outliers()
        clf = OneClassSVM(kernel="rbf", nu=0.05)

        clf.fit(X)
        predictions = clf.predict(X)

        assert len(predictions) == len(X)
        assert set(predictions).issubset({-1, 1})

    def test_different_kernels(self):
        """Test with different kernel types."""
        X = create_test_data_with_outliers()

        for kernel in ["linear", "rbf", "poly"]:
            clf = OneClassSVM(kernel=kernel, nu=0.1)
            clf.fit(X)
            predictions = clf.predict(X)

            assert len(predictions) == len(X)

    def test_decision_function(self):
        """Test decision function."""
        X = create_test_data_with_outliers()
        clf = OneClassSVM(kernel="rbf")

        clf.fit(X)
        decisions = clf.decision_function(X)

        assert len(decisions) == len(X)


class TestStatisticalDetection:
    """Tests for statistical outlier detection functions."""

    def test_zscore_detection(self):
        """Test Z-score based outlier detection."""
        # Normal data with clear outliers
        data = np.concatenate([
            np.random.randn(100) * 0.5,  # Normal data
            np.array([10, -10, 15])  # Outliers
        ])
        X = data.reshape(-1, 1)

        outliers = detect_outliers_zscore(X, threshold=3.0)

        assert len(outliers) == len(X)
        assert outliers.dtype == bool
        # Should detect at least some outliers
        assert sum(outliers) > 0

    def test_iqr_detection(self):
        """Test IQR based outlier detection."""
        data = np.concatenate([
            np.random.randn(100) * 0.5,
            np.array([10, -10])
        ])
        X = data.reshape(-1, 1)

        outliers = detect_outliers_iqr(X, multiplier=1.5)

        assert len(outliers) == len(X)
        assert outliers.dtype == bool

    def test_mad_detection(self):
        """Test MAD (Median Absolute Deviation) based outlier detection."""
        data = np.concatenate([
            np.random.randn(100) * 0.5,
            np.array([10, -10])
        ])
        X = data.reshape(-1, 1)

        outliers = detect_outliers_mad(X, threshold=3.0)

        assert len(outliers) == len(X)
        assert outliers.dtype == bool

    def test_dbscan_detection(self):
        """Test DBSCAN based outlier detection."""
        X = create_test_data_with_outliers()

        outliers = detect_outliers_dbscan(X, eps=0.5, min_samples=5)

        assert len(outliers) == len(X)
        assert outliers.dtype == bool


class TestOutlierScores:
    """Tests for get_outlier_scores function."""

    def test_isolation_forest_scores(self):
        """Test outlier scores with IsolationForest."""
        X = create_test_data_with_outliers()

        scores = get_outlier_scores(X, method="isolation_forest", n_estimators=50)

        assert len(scores) == len(X)
        # Scores should be between 0 and 1 (normalized)
        assert all(0 <= s <= 1 for s in scores)

    def test_lof_scores(self):
        """Test outlier scores with LOF."""
        X = create_test_data_with_outliers()

        scores = get_outlier_scores(X, method="lof", n_neighbors=20)

        assert len(scores) == len(X)

    def test_zscore_scores(self):
        """Test outlier scores with Z-score method."""
        X = create_test_data_with_outliers()

        scores = get_outlier_scores(X, method="zscore")

        assert len(scores) == len(X)

    def test_invalid_method(self):
        """Test that invalid method raises error."""
        X = create_test_data_with_outliers()

        with pytest.raises(ValueError):
            get_outlier_scores(X, method="invalid_method")


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_single_sample(self):
        """Test with a single sample (should handle gracefully)."""
        X = np.array([[1, 2]])
        clf = IsolationForest(n_estimators=10)

        # Should fit without error
        clf.fit(X)

    def test_high_dimensionality(self):
        """Test with high-dimensional data."""
        np.random.seed(42)
        X = np.random.randn(100, 50)  # 50 features

        clf = IsolationForest(n_estimators=50)
        clf.fit(X)
        predictions = clf.predict(X)

        assert len(predictions) == len(X)

    def test_contamination_bounds(self):
        """Test contamination parameter bounds."""
        X = create_test_data_with_outliers()

        # Valid contamination
        clf = IsolationForest(contamination=0.1)
        clf.fit(X)

        # Auto contamination
        clf_auto = IsolationForest(contamination="auto")
        clf_auto.fit(X)

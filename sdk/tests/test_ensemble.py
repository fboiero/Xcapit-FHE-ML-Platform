"""
Tests for the ensemble module.
"""

import numpy as np
import pytest

from sdk.ensemble import (
    VotingClassifier,
    VotingRegressor,
    StackingClassifier,
    StackingRegressor,
    BaggingClassifier,
    BaggingRegressor,
    AdaBoostClassifier,
    get_ensemble_feature_importances,
)


# Mock estimator for testing
class MockClassifier:
    """Mock classifier for testing ensemble methods."""

    def __init__(self, prediction=1, proba=None):
        self.prediction = prediction
        self.proba = proba or [0.3, 0.7]
        self._is_fitted = False
        self.classes_ = np.array([0, 1])
        self.feature_importances_ = None

    def fit(self, X, y):
        self._is_fitted = True
        self.feature_importances_ = np.ones(X.shape[1]) / X.shape[1]
        return self

    def predict(self, X):
        return np.full(len(X), self.prediction)

    def predict_proba(self, X):
        return np.tile(self.proba, (len(X), 1))


class MockRegressor:
    """Mock regressor for testing ensemble methods."""

    def __init__(self, prediction=1.0):
        self.prediction = prediction
        self._is_fitted = False
        self.feature_importances_ = None

    def fit(self, X, y):
        self._is_fitted = True
        self.feature_importances_ = np.ones(X.shape[1]) / X.shape[1]
        return self

    def predict(self, X):
        return np.full(len(X), self.prediction)


class TestVotingClassifier:
    """Tests for VotingClassifier."""

    def test_hard_voting(self):
        """Test hard voting with majority vote."""
        estimators = [
            ("clf1", MockClassifier(prediction=0)),
            ("clf2", MockClassifier(prediction=1)),
            ("clf3", MockClassifier(prediction=1)),
        ]
        X = np.array([[1, 2], [3, 4], [5, 6]])
        y = np.array([0, 1, 1])

        clf = VotingClassifier(estimators=estimators, voting="hard")
        clf.fit(X, y)
        predictions = clf.predict(X)

        # Majority vote: 2 votes for 1, 1 vote for 0 -> prediction should be 1
        assert all(p == 1 for p in predictions)

    def test_soft_voting(self):
        """Test soft voting with averaged probabilities."""
        estimators = [
            ("clf1", MockClassifier(proba=[0.9, 0.1])),
            ("clf2", MockClassifier(proba=[0.4, 0.6])),
            ("clf3", MockClassifier(proba=[0.3, 0.7])),
        ]
        X = np.array([[1, 2], [3, 4]])
        y = np.array([0, 1])

        clf = VotingClassifier(estimators=estimators, voting="soft")
        clf.fit(X, y)
        proba = clf.predict_proba(X)

        # Average proba for class 0: (0.9 + 0.4 + 0.3) / 3 ≈ 0.533
        # Average proba for class 1: (0.1 + 0.6 + 0.7) / 3 ≈ 0.467
        assert proba.shape == (2, 2)

    def test_weighted_voting(self):
        """Test weighted voting."""
        estimators = [
            ("clf1", MockClassifier(prediction=0)),
            ("clf2", MockClassifier(prediction=1)),
        ]
        weights = [3, 1]  # clf1 has 3x more weight
        X = np.array([[1, 2]])
        y = np.array([0])

        clf = VotingClassifier(estimators=estimators, voting="hard", weights=weights)
        clf.fit(X, y)
        predictions = clf.predict(X)

        # clf1 (pred=0) has weight 3, clf2 (pred=1) has weight 1 -> prediction should be 0
        assert predictions[0] == 0

    def test_get_params(self):
        """Test parameter retrieval."""
        estimators = [("clf1", MockClassifier())]
        clf = VotingClassifier(estimators=estimators)

        params = clf.get_params()

        assert "voting" in params
        assert "estimators" in params


class TestVotingRegressor:
    """Tests for VotingRegressor."""

    def test_average_prediction(self):
        """Test averaged predictions."""
        estimators = [
            ("reg1", MockRegressor(prediction=1.0)),
            ("reg2", MockRegressor(prediction=2.0)),
            ("reg3", MockRegressor(prediction=3.0)),
        ]
        X = np.array([[1, 2], [3, 4]])
        y = np.array([1.5, 2.5])

        reg = VotingRegressor(estimators=estimators)
        reg.fit(X, y)
        predictions = reg.predict(X)

        # Average: (1.0 + 2.0 + 3.0) / 3 = 2.0
        assert all(np.isclose(p, 2.0) for p in predictions)

    def test_weighted_average(self):
        """Test weighted average predictions."""
        estimators = [
            ("reg1", MockRegressor(prediction=1.0)),
            ("reg2", MockRegressor(prediction=3.0)),
        ]
        weights = [1, 3]
        X = np.array([[1, 2]])
        y = np.array([2.0])

        reg = VotingRegressor(estimators=estimators, weights=weights)
        reg.fit(X, y)
        predictions = reg.predict(X)

        # Weighted average: (1.0 * 1 + 3.0 * 3) / 4 = 10 / 4 = 2.5
        assert np.isclose(predictions[0], 2.5)


class TestStackingClassifier:
    """Tests for StackingClassifier."""

    def test_stacking_fit_predict(self):
        """Test stacking fit and predict."""
        estimators = [
            ("clf1", MockClassifier(prediction=0)),
            ("clf2", MockClassifier(prediction=1)),
        ]
        final_estimator = MockClassifier(prediction=1)

        X = np.array([[1, 2], [3, 4], [5, 6], [7, 8], [9, 10]])
        y = np.array([0, 1, 0, 1, 0])

        clf = StackingClassifier(
            estimators=estimators,
            final_estimator=final_estimator,
            cv=2,
        )
        clf.fit(X, y)
        predictions = clf.predict(X)

        assert len(predictions) == len(X)

    def test_stacking_with_passthrough(self):
        """Test stacking with passthrough (original features included)."""
        estimators = [("clf1", MockClassifier())]
        final_estimator = MockClassifier()

        X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
        y = np.array([0, 1, 0, 1])

        clf = StackingClassifier(
            estimators=estimators,
            final_estimator=final_estimator,
            passthrough=True,
            cv=2,
        )
        clf.fit(X, y)
        predictions = clf.predict(X)

        assert len(predictions) == len(X)


class TestStackingRegressor:
    """Tests for StackingRegressor."""

    def test_stacking_regressor(self):
        """Test stacking regressor fit and predict."""
        estimators = [
            ("reg1", MockRegressor(prediction=1.0)),
            ("reg2", MockRegressor(prediction=2.0)),
        ]
        final_estimator = MockRegressor(prediction=1.5)

        X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
        y = np.array([1.0, 2.0, 3.0, 4.0])

        reg = StackingRegressor(
            estimators=estimators,
            final_estimator=final_estimator,
            cv=2,
        )
        reg.fit(X, y)
        predictions = reg.predict(X)

        assert len(predictions) == len(X)


class TestBaggingClassifier:
    """Tests for BaggingClassifier."""

    def test_bagging_fit_predict(self):
        """Test bagging fit and predict."""
        X = np.array([[1, 2], [3, 4], [5, 6], [7, 8], [9, 10]])
        y = np.array([0, 1, 0, 1, 0])

        clf = BaggingClassifier(
            estimator=MockClassifier(prediction=1),
            n_estimators=5,
            max_samples=0.8,
        )
        clf.fit(X, y)
        predictions = clf.predict(X)

        assert len(predictions) == len(X)
        assert clf.n_estimators == 5

    def test_bagging_feature_sampling(self):
        """Test bagging with feature sampling."""
        X = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]])
        y = np.array([0, 1, 0, 1])

        clf = BaggingClassifier(
            estimator=MockClassifier(),
            n_estimators=3,
            max_features=0.5,
        )
        clf.fit(X, y)
        predictions = clf.predict(X)

        assert len(predictions) == len(X)


class TestBaggingRegressor:
    """Tests for BaggingRegressor."""

    def test_bagging_regressor(self):
        """Test bagging regressor fit and predict."""
        X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
        y = np.array([1.0, 2.0, 3.0, 4.0])

        reg = BaggingRegressor(
            estimator=MockRegressor(prediction=2.0),
            n_estimators=5,
        )
        reg.fit(X, y)
        predictions = reg.predict(X)

        assert len(predictions) == len(X)


class TestAdaBoostClassifier:
    """Tests for AdaBoostClassifier."""

    def test_adaboost_fit_predict(self):
        """Test AdaBoost fit and predict."""
        X = np.array([[1, 2], [3, 4], [5, 6], [7, 8], [9, 10]])
        y = np.array([0, 1, 0, 1, 0])

        clf = AdaBoostClassifier(
            estimator=MockClassifier(prediction=1),
            n_estimators=5,
            learning_rate=1.0,
        )
        clf.fit(X, y)
        predictions = clf.predict(X)

        assert len(predictions) == len(X)
        assert clf.n_estimators == 5

    def test_adaboost_predict_proba(self):
        """Test AdaBoost predict_proba."""
        X = np.array([[1, 2], [3, 4], [5, 6]])
        y = np.array([0, 1, 0])

        clf = AdaBoostClassifier(
            estimator=MockClassifier(),
            n_estimators=3,
        )
        clf.fit(X, y)
        proba = clf.predict_proba(X)

        assert proba.shape[0] == len(X)
        assert proba.shape[1] == 2  # Binary classification


class TestEnsembleFeatureImportances:
    """Tests for get_ensemble_feature_importances."""

    def test_feature_importances(self):
        """Test feature importance aggregation."""
        X = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        y = np.array([0, 1, 0])

        estimators = [
            ("clf1", MockClassifier()),
            ("clf2", MockClassifier()),
        ]
        clf = VotingClassifier(estimators=estimators)
        clf.fit(X, y)

        importances = get_ensemble_feature_importances(clf)

        assert len(importances) == X.shape[1]
        assert np.isclose(sum(importances), 1.0)  # Should sum to 1

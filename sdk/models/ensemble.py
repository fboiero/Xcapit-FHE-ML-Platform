"""Ensemble methods for combining multiple FHE models.

This module provides voting and stacking ensembles that combine
predictions from multiple different model types.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Union
import numpy as np

from ..encryption.ckks_wrapper import (
    CKKSEncryptor,
    EncryptedMatrix,
    EncryptedVector,
)
from ..utils.data_loader import EncryptedDataset
from .base import BaseFHEModel, ModelConfig, ModelState


class VotingType(Enum):
    """Types of voting for classification."""

    HARD = "hard"  # Majority vote
    SOFT = "soft"  # Average probabilities


@dataclass
class VotingConfig(ModelConfig):
    """Configuration for Voting Ensemble."""

    voting: VotingType = VotingType.SOFT
    weights: Optional[list[float]] = None


class VotingClassifier(BaseFHEModel):
    """Voting Classifier for combining multiple FHE classifiers.

    Combines predictions from multiple classifiers using voting:
    - Hard voting: majority class wins
    - Soft voting: average predicted probabilities

    Example:
        >>> from sdk.models import (
        ...     VotingClassifier, LogisticRegression,
        ...     RandomForestClassifier, GradientBoostingClassifier
        ... )
        >>>
        >>> clf1 = LogisticRegression()
        >>> clf2 = RandomForestClassifier(n_estimators=10)
        >>> clf3 = GradientBoostingClassifier(n_estimators=10)
        >>>
        >>> ensemble = VotingClassifier(
        ...     estimators=[('lr', clf1), ('rf', clf2), ('gb', clf3)],
        ...     voting='soft'
        ... )
        >>> ensemble.fit(X_train, y_train)
        >>> predictions = ensemble.predict(X_test)
    """

    def __init__(
        self,
        estimators: list[tuple[str, BaseFHEModel]],
        voting: str = "soft",
        weights: Optional[list[float]] = None,
        encryptor: Optional[CKKSEncryptor] = None,
    ):
        """Initialize Voting Classifier.

        Args:
            estimators: List of (name, estimator) tuples.
            voting: 'hard' or 'soft'.
            weights: Sequence of weights for each estimator.
            encryptor: CKKS encryptor.
        """
        voting_type = VotingType.HARD if voting == "hard" else VotingType.SOFT
        config = VotingConfig(voting=voting_type, weights=weights)
        super().__init__(config=config, encryptor=encryptor)

        self._voting_config = config
        self.estimators = estimators
        self.named_estimators_: dict[str, BaseFHEModel] = {}
        self._classes: Optional[np.ndarray] = None

    @property
    def classes_(self) -> Optional[np.ndarray]:
        """Get unique classes."""
        return self._classes

    def fit(
        self,
        X: Union[EncryptedDataset, EncryptedMatrix, np.ndarray],
        y: Optional[Union[EncryptedVector, np.ndarray]] = None,
    ) -> "VotingClassifier":
        """Fit all estimators.

        Args:
            X: Training features.
            y: Training labels.

        Returns:
            self for method chaining.
        """
        self._state = ModelState.TRAINING

        if isinstance(X, (EncryptedDataset, EncryptedMatrix, EncryptedVector)):
            raise ValueError("VotingClassifier must be trained on plaintext data.")

        X_train = np.asarray(X)
        y_train = np.asarray(y).ravel()

        self._classes = np.unique(y_train)
        self._n_features = X_train.shape[1]

        if self._config.verbose:
            print(f"Training VotingClassifier with {len(self.estimators)} estimators")

        # Fit each estimator
        self.named_estimators_ = {}
        for name, estimator in self.estimators:
            if self._config.verbose:
                print(f"  Fitting {name}...")

            estimator.fit(X_train, y_train)
            self.named_estimators_[name] = estimator

        self._state = ModelState.TRAINED

        if self._config.verbose:
            print("Training complete.")

        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict class probabilities.

        Args:
            X: Features.

        Returns:
            Averaged probabilities of shape (n_samples, n_classes).
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        X_pred = np.asarray(X)
        if X_pred.ndim == 1:
            X_pred = X_pred.reshape(-1, 1)

        # Collect probabilities from all estimators
        all_probs = []
        for name, estimator in self.estimators:
            if hasattr(estimator, "predict_proba"):
                probs = estimator.predict_proba(X_pred)
            else:
                # Convert predictions to one-hot
                preds = estimator.predict(X_pred)
                probs = np.zeros((len(X_pred), len(self._classes)))
                for i, p in enumerate(preds):
                    idx = np.where(self._classes == p)[0]
                    if len(idx) > 0:
                        probs[i, idx[0]] = 1.0
            all_probs.append(probs)

        # Average with weights
        weights = self._voting_config.weights
        if weights is None:
            weights = np.ones(len(self.estimators))
        weights = np.array(weights) / sum(weights)

        avg_probs = np.zeros_like(all_probs[0])
        for probs, weight in zip(all_probs, weights):
            avg_probs += weight * probs

        return avg_probs

    def predict(
        self,
        X: Union[EncryptedMatrix, np.ndarray, list],
    ) -> np.ndarray:
        """Predict class labels.

        Args:
            X: Features.

        Returns:
            Predicted class labels.
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        if isinstance(X, (EncryptedMatrix, list)):
            return self._predict_encrypted(X)

        X_pred = np.asarray(X)
        if X_pred.ndim == 1:
            X_pred = X_pred.reshape(-1, 1)

        if self._voting_config.voting == VotingType.SOFT:
            # Soft voting: use averaged probabilities
            probs = self.predict_proba(X_pred)
            return self._classes[np.argmax(probs, axis=1)]
        else:
            # Hard voting: majority vote
            predictions = np.zeros((len(X_pred), len(self.estimators)))

            for i, (name, estimator) in enumerate(self.estimators):
                preds = estimator.predict(X_pred)
                # Convert to class indices
                for j, p in enumerate(preds):
                    idx = np.where(self._classes == p)[0]
                    if len(idx) > 0:
                        predictions[j, i] = idx[0]

            # Majority vote
            from scipy import stats
            majority, _ = stats.mode(predictions, axis=1, keepdims=False)
            return self._classes[majority.astype(int)]

    def _predict_encrypted(
        self,
        X: Union[EncryptedMatrix, list[EncryptedVector]],
    ) -> EncryptedVector:
        """Make predictions on encrypted data."""
        encryptor = self._ensure_encryptor(X)
        encrypted_rows = list(X) if not isinstance(X, list) else X

        results = []
        for enc_row in encrypted_rows:
            x_plain = enc_row.decrypt().reshape(1, -1)
            pred = self.predict(x_plain)[0]
            pred_idx = np.where(self._classes == pred)[0][0]
            results.append(pred_idx)

        return encryptor.encrypt_vector(np.array(results))

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Compute accuracy score.

        Args:
            X: Features.
            y: True labels.

        Returns:
            Accuracy score.
        """
        predictions = self.predict(X)
        return np.mean(predictions == y)

    def get_params(self) -> dict[str, Any]:
        """Get model parameters."""
        params = super().get_params()
        params.update({
            "voting": self._voting_config.voting.value,
            "weights": self._voting_config.weights,
            "estimators": [(name, est.get_params()) for name, est in self.estimators],
            "classes": self._classes.tolist() if self._classes is not None else None,
        })
        return params

    def __repr__(self) -> str:
        names = [name for name, _ in self.estimators]
        return f"VotingClassifier(estimators={names}, voting={self._voting_config.voting.value})"


class VotingRegressor(BaseFHEModel):
    """Voting Regressor for combining multiple FHE regressors.

    Averages predictions from multiple regressors.

    Example:
        >>> from sdk.models import (
        ...     VotingRegressor, LinearRegression,
        ...     RandomForestRegressor, GradientBoostingRegressor
        ... )
        >>>
        >>> reg1 = LinearRegression()
        >>> reg2 = RandomForestRegressor(n_estimators=10)
        >>> reg3 = GradientBoostingRegressor(n_estimators=10)
        >>>
        >>> ensemble = VotingRegressor(
        ...     estimators=[('lr', reg1), ('rf', reg2), ('gb', reg3)],
        ...     weights=[1, 2, 2]
        ... )
        >>> ensemble.fit(X_train, y_train)
        >>> predictions = ensemble.predict(X_test)
    """

    def __init__(
        self,
        estimators: list[tuple[str, BaseFHEModel]],
        weights: Optional[list[float]] = None,
        encryptor: Optional[CKKSEncryptor] = None,
    ):
        """Initialize Voting Regressor.

        Args:
            estimators: List of (name, estimator) tuples.
            weights: Sequence of weights for each estimator.
            encryptor: CKKS encryptor.
        """
        config = VotingConfig(weights=weights)
        super().__init__(config=config, encryptor=encryptor)

        self._voting_config = config
        self.estimators = estimators
        self.named_estimators_: dict[str, BaseFHEModel] = {}

    def fit(
        self,
        X: Union[EncryptedDataset, EncryptedMatrix, np.ndarray],
        y: Optional[Union[EncryptedVector, np.ndarray]] = None,
    ) -> "VotingRegressor":
        """Fit all estimators.

        Args:
            X: Training features.
            y: Training targets.

        Returns:
            self for method chaining.
        """
        self._state = ModelState.TRAINING

        if isinstance(X, (EncryptedDataset, EncryptedMatrix, EncryptedVector)):
            raise ValueError("VotingRegressor must be trained on plaintext data.")

        X_train = np.asarray(X)
        y_train = np.asarray(y).ravel()

        self._n_features = X_train.shape[1]

        if self._config.verbose:
            print(f"Training VotingRegressor with {len(self.estimators)} estimators")

        self.named_estimators_ = {}
        for name, estimator in self.estimators:
            if self._config.verbose:
                print(f"  Fitting {name}...")

            estimator.fit(X_train, y_train)
            self.named_estimators_[name] = estimator

        self._state = ModelState.TRAINED
        return self

    def predict(
        self,
        X: Union[EncryptedMatrix, np.ndarray, list],
    ) -> np.ndarray:
        """Predict target values.

        Args:
            X: Features.

        Returns:
            Averaged predictions.
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        if isinstance(X, (EncryptedMatrix, list)):
            return self._predict_encrypted(X)

        X_pred = np.asarray(X)
        if X_pred.ndim == 1:
            X_pred = X_pred.reshape(-1, 1)

        # Collect predictions from all estimators
        all_preds = []
        for name, estimator in self.estimators:
            preds = estimator.predict(X_pred)
            all_preds.append(preds)

        all_preds = np.array(all_preds)

        # Weighted average
        weights = self._voting_config.weights
        if weights is None:
            return np.mean(all_preds, axis=0)
        else:
            weights = np.array(weights) / sum(weights)
            return np.average(all_preds, axis=0, weights=weights)

    def _predict_encrypted(
        self,
        X: Union[EncryptedMatrix, list[EncryptedVector]],
    ) -> EncryptedVector:
        """Make predictions on encrypted data."""
        encryptor = self._ensure_encryptor(X)
        encrypted_rows = list(X) if not isinstance(X, list) else X

        results = []
        for enc_row in encrypted_rows:
            x_plain = enc_row.decrypt().reshape(1, -1)
            pred = self.predict(x_plain)[0]
            results.append(pred)

        return encryptor.encrypt_vector(np.array(results))

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Compute R² score.

        Args:
            X: Features.
            y: True values.

        Returns:
            R² score.
        """
        predictions = self.predict(X)
        y = np.asarray(y).ravel()

        ss_res = np.sum((y - predictions) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)

        if ss_tot == 0:
            return 0.0

        return 1 - (ss_res / ss_tot)

    def get_params(self) -> dict[str, Any]:
        """Get model parameters."""
        params = super().get_params()
        params.update({
            "weights": self._voting_config.weights,
            "estimators": [(name, est.get_params()) for name, est in self.estimators],
        })
        return params

    def __repr__(self) -> str:
        names = [name for name, _ in self.estimators]
        return f"VotingRegressor(estimators={names})"


class StackingClassifier(BaseFHEModel):
    """Stacking Classifier that combines base classifiers with a meta-classifier.

    Base classifiers make predictions, which are then used as features
    for a meta-classifier (final estimator).

    Example:
        >>> from sdk.models import (
        ...     StackingClassifier, LogisticRegression,
        ...     RandomForestClassifier, DecisionTreeClassifier
        ... )
        >>>
        >>> base = [
        ...     ('rf', RandomForestClassifier(n_estimators=10)),
        ...     ('dt', DecisionTreeClassifier())
        ... ]
        >>> meta = LogisticRegression()
        >>>
        >>> stacking = StackingClassifier(estimators=base, final_estimator=meta)
        >>> stacking.fit(X_train, y_train)
        >>> predictions = stacking.predict(X_test)
    """

    def __init__(
        self,
        estimators: list[tuple[str, BaseFHEModel]],
        final_estimator: BaseFHEModel,
        cv: int = 5,
        stack_method: str = "predict_proba",
        passthrough: bool = False,
        encryptor: Optional[CKKSEncryptor] = None,
    ):
        """Initialize Stacking Classifier.

        Args:
            estimators: List of (name, estimator) tuples for base layer.
            final_estimator: Meta-classifier.
            cv: Number of CV folds for base predictions.
            stack_method: 'predict' or 'predict_proba'.
            passthrough: Whether to pass original features to meta-classifier.
            encryptor: CKKS encryptor.
        """
        super().__init__(encryptor=encryptor)

        self.estimators = estimators
        self.final_estimator = final_estimator
        self.cv = cv
        self.stack_method = stack_method
        self.passthrough = passthrough
        self._classes: Optional[np.ndarray] = None

    def fit(
        self,
        X: Union[EncryptedDataset, EncryptedMatrix, np.ndarray],
        y: Optional[Union[EncryptedVector, np.ndarray]] = None,
    ) -> "StackingClassifier":
        """Fit base estimators and meta-classifier.

        Args:
            X: Training features.
            y: Training labels.

        Returns:
            self for method chaining.
        """
        self._state = ModelState.TRAINING

        if isinstance(X, (EncryptedDataset, EncryptedMatrix, EncryptedVector)):
            raise ValueError("StackingClassifier must be trained on plaintext data.")

        X_train = np.asarray(X)
        y_train = np.asarray(y).ravel()

        self._classes = np.unique(y_train)
        self._n_features = X_train.shape[1]

        if self._config.verbose:
            print(f"Training StackingClassifier with {len(self.estimators)} base estimators")

        # Generate meta-features using cross-validation
        from ..evaluation import KFold
        kf = KFold(n_splits=self.cv)

        meta_features = []

        for name, estimator in self.estimators:
            # Cross-validated predictions for this estimator
            cv_preds = np.zeros((len(X_train), len(self._classes)))

            for train_idx, val_idx in kf.split(X_train):
                # Clone estimator
                import copy
                est = copy.deepcopy(estimator)

                # Fit on training fold
                est.fit(X_train[train_idx], y_train[train_idx])

                # Predict on validation fold
                if self.stack_method == "predict_proba" and hasattr(est, "predict_proba"):
                    preds = est.predict_proba(X_train[val_idx])
                else:
                    preds_raw = est.predict(X_train[val_idx])
                    preds = np.zeros((len(val_idx), len(self._classes)))
                    for i, p in enumerate(preds_raw):
                        idx = np.where(self._classes == p)[0]
                        if len(idx) > 0:
                            preds[i, idx[0]] = 1.0

                cv_preds[val_idx] = preds

            meta_features.append(cv_preds)

        # Concatenate meta-features
        X_meta = np.hstack(meta_features)

        if self.passthrough:
            X_meta = np.hstack([X_train, X_meta])

        # Fit final estimator on meta-features
        self.final_estimator.fit(X_meta, y_train)

        # Refit base estimators on full data
        for name, estimator in self.estimators:
            estimator.fit(X_train, y_train)

        self._state = ModelState.TRAINED
        return self

    def _get_meta_features(self, X: np.ndarray) -> np.ndarray:
        """Generate meta-features from base estimators."""
        meta_features = []

        for name, estimator in self.estimators:
            if self.stack_method == "predict_proba" and hasattr(estimator, "predict_proba"):
                preds = estimator.predict_proba(X)
            else:
                preds_raw = estimator.predict(X)
                preds = np.zeros((len(X), len(self._classes)))
                for i, p in enumerate(preds_raw):
                    idx = np.where(self._classes == p)[0]
                    if len(idx) > 0:
                        preds[i, idx[0]] = 1.0
            meta_features.append(preds)

        X_meta = np.hstack(meta_features)

        if self.passthrough:
            X_meta = np.hstack([X, X_meta])

        return X_meta

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict class probabilities."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        X_pred = np.asarray(X)
        if X_pred.ndim == 1:
            X_pred = X_pred.reshape(-1, 1)

        X_meta = self._get_meta_features(X_pred)

        if hasattr(self.final_estimator, "predict_proba"):
            return self.final_estimator.predict_proba(X_meta)
        else:
            preds = self.final_estimator.predict(X_meta)
            probs = np.zeros((len(X_pred), len(self._classes)))
            for i, p in enumerate(preds):
                idx = np.where(self._classes == p)[0]
                if len(idx) > 0:
                    probs[i, idx[0]] = 1.0
            return probs

    def predict(
        self,
        X: Union[EncryptedMatrix, np.ndarray, list],
    ) -> np.ndarray:
        """Predict class labels."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        if isinstance(X, (EncryptedMatrix, list)):
            encryptor = self._ensure_encryptor(X)
            encrypted_rows = list(X) if not isinstance(X, list) else X
            results = []
            for enc_row in encrypted_rows:
                x_plain = enc_row.decrypt().reshape(1, -1)
                pred = self.predict(x_plain)[0]
                pred_idx = np.where(self._classes == pred)[0][0]
                results.append(pred_idx)
            return encryptor.encrypt_vector(np.array(results))

        X_pred = np.asarray(X)
        if X_pred.ndim == 1:
            X_pred = X_pred.reshape(-1, 1)

        X_meta = self._get_meta_features(X_pred)
        return self.final_estimator.predict(X_meta)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Compute accuracy score."""
        predictions = self.predict(X)
        return np.mean(predictions == y)

    def __repr__(self) -> str:
        names = [name for name, _ in self.estimators]
        return f"StackingClassifier(estimators={names}, final={self.final_estimator.__class__.__name__})"

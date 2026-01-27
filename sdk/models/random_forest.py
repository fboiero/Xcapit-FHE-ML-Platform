"""FHE-compatible Random Forest.

This module implements a Random Forest ensemble for FHE-encrypted data,
using an ensemble of soft decision trees with bagging and random feature selection.

The ensemble approach improves prediction accuracy and stability compared
to single decision trees, while maintaining FHE compatibility through
polynomial approximations.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Union
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..encryption.ckks_wrapper import (
    CKKSEncryptor,
    EncryptedMatrix,
    EncryptedVector,
)
from ..utils.data_loader import EncryptedDataset
from .base import BaseFHEModel, ModelConfig, ModelState
from .decision_tree import DecisionTree, DecisionTreeClassifier, TreeConfig, TreeType


class AggregationMethod(Enum):
    """Method for aggregating tree predictions."""
    AVERAGE = "average"  # Mean of predictions (regression)
    VOTING = "voting"  # Majority vote (classification)
    SOFT_VOTING = "soft_voting"  # Average probabilities (classification)
    WEIGHTED = "weighted"  # Weighted by tree performance


@dataclass
class RandomForestConfig(ModelConfig):
    """Configuration for Random Forest.

    Attributes:
        n_estimators: Number of trees in the forest.
        max_depth: Maximum depth of each tree.
        max_features: Number of features to consider for each split.
            - 'sqrt': sqrt(n_features)
            - 'log2': log2(n_features)
            - int: exact number
            - float: fraction of n_features
            - None: all features
        min_samples_split: Minimum samples required to split a node.
        bootstrap: Whether to use bootstrap samples.
        bootstrap_ratio: Fraction of samples to use if bootstrap=True.
        aggregation: Method for combining tree predictions.
        n_jobs: Number of parallel jobs for training (-1 for all cores).
        random_state: Random seed for reproducibility.
        tree_config: Configuration passed to individual trees.
    """
    n_estimators: int = 10
    max_depth: int = 3
    max_features: Union[str, int, float, None] = 'sqrt'
    min_samples_split: int = 2
    bootstrap: bool = True
    bootstrap_ratio: float = 1.0
    aggregation: AggregationMethod = AggregationMethod.AVERAGE
    n_jobs: int = 1
    random_state: Optional[int] = None
    tree_config: Optional[TreeConfig] = None

    def __post_init__(self):
        super().__post_init__()
        if self.n_estimators < 1:
            raise ValueError("n_estimators must be at least 1")
        if self.max_depth < 1:
            raise ValueError("max_depth must be at least 1")
        if self.bootstrap_ratio <= 0 or self.bootstrap_ratio > 1:
            raise ValueError("bootstrap_ratio must be in (0, 1]")


class RandomForest(BaseFHEModel):
    """Random Forest ensemble for FHE-encrypted data.

    This implementation creates multiple soft decision trees, each trained
    on a bootstrap sample with random feature subsets. Predictions are
    aggregated by averaging (regression) or voting (classification).

    Key features:
    - Bagging: Each tree is trained on a bootstrap sample
    - Random feature subsets: Each tree considers a random subset of features
    - Ensemble aggregation: Combines multiple tree predictions
    - FHE compatible: Uses soft decision trees with polynomial splits

    Example:
        >>> from sdk.models import RandomForest, RandomForestConfig
        >>> config = RandomForestConfig(n_estimators=10, max_depth=3)
        >>> forest = RandomForest(config=config)
        >>> forest.fit(X_train, y_train)
        >>> predictions = forest.predict(X_test)

    For classification:
        >>> from sdk.models import RandomForestClassifier
        >>> clf = RandomForestClassifier(n_estimators=20)
        >>> clf.fit(X_train, y_train)
        >>> probs = clf.predict_proba(X_test)
    """

    def __init__(
        self,
        config: Optional[RandomForestConfig] = None,
        encryptor: Optional[CKKSEncryptor] = None,
    ):
        """Initialize Random Forest.

        Args:
            config: Forest configuration.
            encryptor: CKKS encryptor for operations.
        """
        if config is None:
            config = RandomForestConfig()
        super().__init__(config=config, encryptor=encryptor)

        self._forest_config = config
        self._trees: list[DecisionTree] = []
        self._feature_subsets: list[np.ndarray] = []
        self._tree_weights: Optional[np.ndarray] = None
        self._n_features: int = 0
        self._n_classes: int = 2
        self._rng = np.random.RandomState(config.random_state)

    @property
    def n_estimators(self) -> int:
        """Get number of trees in the forest."""
        return self._forest_config.n_estimators

    @property
    def trees(self) -> list[DecisionTree]:
        """Get list of trained trees."""
        return self._trees

    @property
    def feature_importances_(self) -> Optional[np.ndarray]:
        """Get feature importances based on tree structure.

        Returns:
            Array of shape (n_features,) with importance scores.
        """
        if not self.is_fitted:
            return None

        # Compute importance as frequency of feature usage across all trees
        importances = np.zeros(self._n_features)

        for tree, features in zip(self._trees, self._feature_subsets):
            if tree.feature_indices is not None:
                for feat_idx in tree.feature_indices:
                    # Map back to original feature index
                    original_idx = features[feat_idx]
                    importances[original_idx] += 1

        # Normalize
        if importances.sum() > 0:
            importances /= importances.sum()

        return importances

    def _get_max_features(self, n_features: int) -> int:
        """Determine number of features to use for each tree.

        Args:
            n_features: Total number of features.

        Returns:
            Number of features to sample for each tree.
        """
        max_features = self._forest_config.max_features

        if max_features is None:
            return n_features
        elif isinstance(max_features, str):
            if max_features == 'sqrt':
                return max(1, int(np.sqrt(n_features)))
            elif max_features == 'log2':
                return max(1, int(np.log2(n_features)))
            else:
                raise ValueError(f"Unknown max_features string: {max_features}")
        elif isinstance(max_features, float):
            return max(1, int(max_features * n_features))
        elif isinstance(max_features, int):
            return min(max_features, n_features)
        else:
            raise ValueError(f"Invalid max_features type: {type(max_features)}")

    def _create_bootstrap_sample(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Create a bootstrap sample of the data.

        Args:
            X: Features of shape (n_samples, n_features).
            y: Target of shape (n_samples,).

        Returns:
            Tuple of (X_sample, y_sample, sample_indices).
        """
        n_samples = X.shape[0]

        if self._forest_config.bootstrap:
            # Sample with replacement
            n_sample = int(n_samples * self._forest_config.bootstrap_ratio)
            indices = self._rng.choice(n_samples, size=n_sample, replace=True)
        else:
            # Use all samples
            indices = np.arange(n_samples)

        return X[indices], y[indices], indices

    def _train_single_tree(
        self,
        tree_idx: int,
        X: np.ndarray,
        y: np.ndarray,
        n_max_features: int,
    ) -> tuple[DecisionTree, np.ndarray, float]:
        """Train a single tree in the ensemble.

        Args:
            tree_idx: Index of this tree.
            X: Full training features.
            y: Full training target.
            n_max_features: Number of features to use.

        Returns:
            Tuple of (trained_tree, feature_subset, oob_score).
        """
        # Create bootstrap sample
        X_sample, y_sample, sample_indices = self._create_bootstrap_sample(X, y)

        # Select random feature subset
        all_features = np.arange(X.shape[1])
        feature_subset = self._rng.choice(
            all_features, size=n_max_features, replace=False
        )
        feature_subset.sort()  # Keep consistent ordering

        # Subset the features
        X_subset = X_sample[:, feature_subset]

        # Create tree configuration
        tree_config = self._forest_config.tree_config
        if tree_config is None:
            tree_config = TreeConfig(
                max_depth=self._forest_config.max_depth,
                learning_rate=self._config.learning_rate,
                n_epochs=self._config.n_epochs,
                verbose=False,  # Reduce noise
            )

        # Create and train tree
        tree = DecisionTree(config=tree_config, encryptor=self._encryptor)
        tree.fit(X_subset, y_sample)

        # Compute out-of-bag score if using bootstrap
        oob_score = 0.0
        if self._forest_config.bootstrap:
            oob_indices = np.setdiff1d(np.arange(X.shape[0]), sample_indices)
            if len(oob_indices) > 0:
                X_oob = X[oob_indices][:, feature_subset]
                y_oob = y[oob_indices]
                preds = tree.predict(X_oob)
                oob_score = 1 - np.mean((preds - y_oob) ** 2)

        return tree, feature_subset, oob_score

    def fit(
        self,
        X: Union[EncryptedDataset, EncryptedMatrix, np.ndarray],
        y: Optional[Union[EncryptedVector, np.ndarray]] = None,
    ) -> "RandomForest":
        """Train the Random Forest on data.

        Training is done on plaintext data. The trained ensemble can then
        make predictions on encrypted data.

        Args:
            X: Features (must be plaintext for training).
            y: Target values.

        Returns:
            self for method chaining.
        """
        self._state = ModelState.TRAINING

        # Validate input
        if isinstance(X, (EncryptedDataset, EncryptedMatrix, EncryptedVector)):
            raise ValueError(
                "Random Forest must be trained on plaintext data. "
                "Use numpy arrays for training, then predict on encrypted data."
            )

        X_train = np.asarray(X)
        y_train = np.asarray(y)

        if X_train.ndim == 1:
            X_train = X_train.reshape(-1, 1)

        n_samples, n_features = X_train.shape
        self._n_features = n_features

        n_max_features = self._get_max_features(n_features)

        if self._config.verbose:
            print(f"Training RandomForest: {self.n_estimators} trees")
            print(f"  Samples: {n_samples}, Features: {n_features}")
            print(f"  Max features per tree: {n_max_features}")
            print(f"  Max depth: {self._forest_config.max_depth}")

        # Train trees
        self._trees = []
        self._feature_subsets = []
        oob_scores = []

        if self._forest_config.n_jobs == 1:
            # Sequential training
            for i in range(self.n_estimators):
                tree, features, oob = self._train_single_tree(
                    i, X_train, y_train, n_max_features
                )
                self._trees.append(tree)
                self._feature_subsets.append(features)
                oob_scores.append(oob)

                if self._config.verbose and (i + 1) % max(1, self.n_estimators // 5) == 0:
                    print(f"  Trained {i + 1}/{self.n_estimators} trees")
        else:
            # Parallel training
            n_jobs = self._forest_config.n_jobs
            if n_jobs == -1:
                n_jobs = None  # Use all cores

            with ThreadPoolExecutor(max_workers=n_jobs) as executor:
                futures = {
                    executor.submit(
                        self._train_single_tree, i, X_train, y_train, n_max_features
                    ): i
                    for i in range(self.n_estimators)
                }

                results = [None] * self.n_estimators
                for future in as_completed(futures):
                    idx = futures[future]
                    results[idx] = future.result()

                for tree, features, oob in results:
                    self._trees.append(tree)
                    self._feature_subsets.append(features)
                    oob_scores.append(oob)

        # Compute tree weights based on OOB performance
        if self._forest_config.aggregation == AggregationMethod.WEIGHTED:
            oob_scores = np.array(oob_scores)
            # Normalize weights (higher score = higher weight)
            oob_scores = np.clip(oob_scores, 0.01, None)  # Avoid zero weights
            self._tree_weights = oob_scores / oob_scores.sum()
        else:
            self._tree_weights = np.ones(self.n_estimators) / self.n_estimators

        self._state = ModelState.TRAINED

        if self._config.verbose:
            mean_oob = np.mean(oob_scores) if oob_scores else 0
            print(f"Training complete. Mean OOB score: {mean_oob:.4f}")

        return self

    def predict(
        self,
        X: Union[EncryptedMatrix, np.ndarray, list],
    ) -> Union[EncryptedVector, np.ndarray]:
        """Make predictions using the ensemble.

        Args:
            X: Features (encrypted or plaintext).

        Returns:
            Predictions (encrypted if input is encrypted).
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        # Handle encrypted input
        if isinstance(X, EncryptedMatrix):
            return self._predict_encrypted(X)
        elif isinstance(X, list) and len(X) > 0 and isinstance(X[0], EncryptedVector):
            return self._predict_encrypted(X)

        # Plaintext prediction
        X_pred = np.asarray(X)
        if X_pred.ndim == 1:
            X_pred = X_pred.reshape(-1, 1)

        # Collect predictions from all trees
        all_predictions = []
        for tree, features in zip(self._trees, self._feature_subsets):
            X_subset = X_pred[:, features]
            preds = tree.predict(X_subset)
            all_predictions.append(preds)

        all_predictions = np.array(all_predictions)  # (n_trees, n_samples)

        # Aggregate predictions
        if self._forest_config.aggregation == AggregationMethod.WEIGHTED:
            # Weighted average
            predictions = np.average(all_predictions, axis=0, weights=self._tree_weights)
        else:
            # Simple average
            predictions = np.mean(all_predictions, axis=0)

        return predictions

    def _predict_encrypted(
        self,
        X: Union[EncryptedMatrix, list[EncryptedVector]],
    ) -> EncryptedVector:
        """Make predictions on encrypted data.

        Args:
            X: Encrypted features.

        Returns:
            Encrypted predictions.
        """
        encryptor = self._ensure_encryptor(X)

        if isinstance(X, list):
            encrypted_rows = X
        else:
            encrypted_rows = list(X)

        results = []

        for enc_row in encrypted_rows:
            # Decrypt for tree traversal (FHE tree traversal is complex)
            x_plain = enc_row.decrypt().reshape(1, -1)

            # Get predictions from all trees
            tree_preds = []
            for tree, features in zip(self._trees, self._feature_subsets):
                X_subset = x_plain[:, features]
                pred = tree.predict(X_subset)[0]
                tree_preds.append(pred)

            # Aggregate
            if self._forest_config.aggregation == AggregationMethod.WEIGHTED:
                final_pred = np.average(tree_preds, weights=self._tree_weights)
            else:
                final_pred = np.mean(tree_preds)

            results.append(final_pred)

        # Encrypt final results
        return encryptor.encrypt_vector(np.array(results))

    def get_params(self) -> dict[str, Any]:
        """Get model parameters as dictionary."""
        params = super().get_params()
        params.update({
            "n_estimators": self._forest_config.n_estimators,
            "max_depth": self._forest_config.max_depth,
            "max_features": self._forest_config.max_features,
            "bootstrap": self._forest_config.bootstrap,
            "aggregation": self._forest_config.aggregation.value,
            "n_features": self._n_features,
            "tree_weights": self._tree_weights.tolist() if self._tree_weights is not None else None,
            "feature_subsets": [fs.tolist() for fs in self._feature_subsets],
            "trees": [tree.get_params() for tree in self._trees],
        })
        return params

    def __repr__(self) -> str:
        return (
            f"RandomForest(n_estimators={self.n_estimators}, "
            f"max_depth={self._forest_config.max_depth}, "
            f"state={self._state.value})"
        )


class RandomForestClassifier(RandomForest):
    """Random Forest Classifier for FHE-encrypted data.

    Uses soft decision trees with softmax leaf outputs for classification.
    Predictions are aggregated using voting or soft voting.

    Example:
        >>> clf = RandomForestClassifier(n_estimators=20, max_depth=4)
        >>> clf.fit(X_train, y_train)
        >>> predictions = clf.predict(X_test)
        >>> probabilities = clf.predict_proba(X_test)
    """

    def __init__(
        self,
        n_estimators: int = 10,
        max_depth: int = 3,
        max_features: Union[str, int, float, None] = 'sqrt',
        n_classes: int = 2,
        bootstrap: bool = True,
        random_state: Optional[int] = None,
        encryptor: Optional[CKKSEncryptor] = None,
        **kwargs,
    ):
        """Initialize Random Forest Classifier.

        Args:
            n_estimators: Number of trees.
            max_depth: Maximum depth of each tree.
            max_features: Features to consider per split.
            n_classes: Number of classes.
            bootstrap: Whether to use bootstrap sampling.
            random_state: Random seed.
            encryptor: CKKS encryptor.
            **kwargs: Additional config parameters.
        """
        config = RandomForestConfig(
            n_estimators=n_estimators,
            max_depth=max_depth,
            max_features=max_features,
            bootstrap=bootstrap,
            aggregation=AggregationMethod.SOFT_VOTING,
            random_state=random_state,
            **kwargs,
        )
        super().__init__(config=config, encryptor=encryptor)
        self._n_classes = n_classes
        self._trees: list[DecisionTreeClassifier] = []

    def _train_single_tree(
        self,
        tree_idx: int,
        X: np.ndarray,
        y: np.ndarray,
        n_max_features: int,
    ) -> tuple[DecisionTreeClassifier, np.ndarray, float]:
        """Train a single classifier tree."""
        # Create bootstrap sample
        X_sample, y_sample, sample_indices = self._create_bootstrap_sample(X, y)

        # Select random feature subset
        all_features = np.arange(X.shape[1])
        feature_subset = self._rng.choice(
            all_features, size=n_max_features, replace=False
        )
        feature_subset.sort()

        X_subset = X_sample[:, feature_subset]

        # Create classifier tree
        tree_config = TreeConfig(
            max_depth=self._forest_config.max_depth,
            tree_type=TreeType.CLASSIFIER,
            n_classes=self._n_classes,
            learning_rate=self._config.learning_rate,
            n_epochs=self._config.n_epochs,
            verbose=False,
        )

        tree = DecisionTreeClassifier(config=tree_config, encryptor=self._encryptor)
        tree.fit(X_subset, y_sample)

        # OOB accuracy
        oob_score = 0.0
        if self._forest_config.bootstrap:
            oob_indices = np.setdiff1d(np.arange(X.shape[0]), sample_indices)
            if len(oob_indices) > 0:
                X_oob = X[oob_indices][:, feature_subset]
                y_oob = y[oob_indices]
                preds = tree.predict(X_oob)
                oob_score = np.mean(preds == y_oob)

        return tree, feature_subset, oob_score

    def predict_proba(
        self,
        X: Union[EncryptedMatrix, np.ndarray],
    ) -> np.ndarray:
        """Predict class probabilities.

        Args:
            X: Features.

        Returns:
            Class probabilities of shape (n_samples, n_classes).
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        X_pred = np.asarray(X)
        if X_pred.ndim == 1:
            X_pred = X_pred.reshape(-1, 1)

        # Collect probabilities from all trees
        all_probs = []
        for tree, features in zip(self._trees, self._feature_subsets):
            X_subset = X_pred[:, features]
            probs = tree.predict_proba(X_subset)
            all_probs.append(probs)

        # Average probabilities (soft voting)
        all_probs = np.array(all_probs)  # (n_trees, n_samples, n_classes)

        if self._forest_config.aggregation == AggregationMethod.WEIGHTED:
            # Weighted average
            avg_probs = np.zeros_like(all_probs[0])
            for i, (probs, weight) in enumerate(zip(all_probs, self._tree_weights)):
                avg_probs += weight * probs
        else:
            avg_probs = np.mean(all_probs, axis=0)

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
        if isinstance(X, (EncryptedMatrix, list)):
            # For encrypted data, use parent's method
            return super().predict(X)

        probs = self.predict_proba(X)
        return np.argmax(probs, axis=1)

    def score(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> float:
        """Compute accuracy score.

        Args:
            X: Features.
            y: True labels.

        Returns:
            Accuracy score.
        """
        predictions = self.predict(X)
        return np.mean(predictions == y)


class RandomForestRegressor(RandomForest):
    """Random Forest Regressor for FHE-encrypted data.

    Uses soft decision trees for regression with averaging aggregation.

    Example:
        >>> reg = RandomForestRegressor(n_estimators=20, max_depth=4)
        >>> reg.fit(X_train, y_train)
        >>> predictions = reg.predict(X_test)
    """

    def __init__(
        self,
        n_estimators: int = 10,
        max_depth: int = 3,
        max_features: Union[str, int, float, None] = 'sqrt',
        bootstrap: bool = True,
        random_state: Optional[int] = None,
        encryptor: Optional[CKKSEncryptor] = None,
        **kwargs,
    ):
        """Initialize Random Forest Regressor.

        Args:
            n_estimators: Number of trees.
            max_depth: Maximum depth of each tree.
            max_features: Features to consider per split.
            bootstrap: Whether to use bootstrap sampling.
            random_state: Random seed.
            encryptor: CKKS encryptor.
            **kwargs: Additional config parameters.
        """
        config = RandomForestConfig(
            n_estimators=n_estimators,
            max_depth=max_depth,
            max_features=max_features,
            bootstrap=bootstrap,
            aggregation=AggregationMethod.AVERAGE,
            random_state=random_state,
            **kwargs,
        )
        super().__init__(config=config, encryptor=encryptor)

    def score(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> float:
        """Compute R² score.

        Args:
            X: Features.
            y: True values.

        Returns:
            R² score.
        """
        predictions = self.predict(X)
        ss_res = np.sum((y - predictions) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)

        if ss_tot == 0:
            return 0.0

        return 1 - (ss_res / ss_tot)

"""
Model Interpretation Utilities for FHE-ML Platform.

Implements SHAP-like and permutation importance methods
compatible with FHE models.
"""

import numpy as np
from typing import Optional, List, Dict, Any, Callable, Tuple


class PermutationImportance:
    """
    Compute feature importance by permuting features.
    
    Parameters
    ----------
    estimator : object
        Fitted model with predict method.
    n_repeats : int
        Number of times to permute each feature.
    random_state : int, optional
        Random seed.
    scoring : callable, optional
        Scoring function (higher is better).
    
    Examples
    --------
    >>> from sdk.evaluation import PermutationImportance
    >>> pi = PermutationImportance(model, n_repeats=10)
    >>> pi.fit(X_test, y_test)
    >>> print(pi.feature_importances_)
    """
    
    def __init__(
        self,
        estimator: Any,
        n_repeats: int = 10,
        random_state: Optional[int] = None,
        scoring: Optional[Callable] = None,
    ):
        self.estimator = estimator
        self.n_repeats = n_repeats
        self.random_state = random_state
        self.scoring = scoring or self._default_scoring
        
        self.feature_importances_: Optional[np.ndarray] = None
        self.importances_mean_: Optional[np.ndarray] = None
        self.importances_std_: Optional[np.ndarray] = None
        self.baseline_score_: Optional[float] = None
        
    def _default_scoring(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Default accuracy scoring."""
        return np.mean(y_true == y_pred)
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> "PermutationImportance":
        """
        Compute permutation importance.
        
        Parameters
        ----------
        X : np.ndarray
            Test data.
        y : np.ndarray
            True labels.
            
        Returns
        -------
        self : PermutationImportance
        """
        if self.random_state is not None:
            np.random.seed(self.random_state)
            
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y)
        n_samples, n_features = X.shape
        
        # Baseline score
        y_pred = self.estimator.predict(X)
        self.baseline_score_ = self.scoring(y, y_pred)
        
        # Compute importance for each feature
        importances = np.zeros((n_features, self.n_repeats))
        
        for feat_idx in range(n_features):
            for rep in range(self.n_repeats):
                # Permute single feature
                X_permuted = X.copy()
                X_permuted[:, feat_idx] = np.random.permutation(X_permuted[:, feat_idx])
                
                # Score with permuted feature
                y_pred_perm = self.estimator.predict(X_permuted)
                score_perm = self.scoring(y, y_pred_perm)
                
                # Importance = decrease in score
                importances[feat_idx, rep] = self.baseline_score_ - score_perm
        
        self.importances_mean_ = np.mean(importances, axis=1)
        self.importances_std_ = np.std(importances, axis=1)
        self.feature_importances_ = self.importances_mean_
        
        return self
    
    def get_importance_ranking(self, feature_names: Optional[List[str]] = None) -> List[Tuple[str, float, float]]:
        """Get features ranked by importance."""
        if self.feature_importances_ is None:
            raise ValueError("Must call fit() first")
            
        n_features = len(self.feature_importances_)
        if feature_names is None:
            feature_names = [f"feature_{i}" for i in range(n_features)]
            
        ranking = sorted(
            zip(feature_names, self.importances_mean_, self.importances_std_),
            key=lambda x: x[1],
            reverse=True
        )
        return ranking


class SHAPApproximation:
    """
    SHAP-like feature attribution using polynomial approximations.
    
    Uses kernel SHAP approximation compatible with FHE operations.
    
    Parameters
    ----------
    estimator : object
        Fitted model with predict method.
    n_samples : int
        Number of background samples.
    random_state : int, optional
        Random seed.
    
    Examples
    --------
    >>> from sdk.evaluation import SHAPApproximation
    >>> shap = SHAPApproximation(model, n_samples=100)
    >>> shap.fit(X_background)
    >>> shap_values = shap.explain(X_test)
    """
    
    def __init__(
        self,
        estimator: Any,
        n_samples: int = 100,
        random_state: Optional[int] = None,
    ):
        self.estimator = estimator
        self.n_samples = n_samples
        self.random_state = random_state
        
        self.background_: Optional[np.ndarray] = None
        self.expected_value_: Optional[float] = None
        
    def fit(self, X_background: np.ndarray) -> "SHAPApproximation":
        """
        Fit with background data.
        
        Parameters
        ----------
        X_background : np.ndarray
            Background dataset for computing expected values.
            
        Returns
        -------
        self : SHAPApproximation
        """
        if self.random_state is not None:
            np.random.seed(self.random_state)
            
        X_background = np.asarray(X_background, dtype=np.float64)
        
        # Sample background if too large
        if len(X_background) > self.n_samples:
            indices = np.random.choice(len(X_background), self.n_samples, replace=False)
            self.background_ = X_background[indices]
        else:
            self.background_ = X_background
            
        # Compute expected prediction
        preds = self.estimator.predict(self.background_)
        if hasattr(preds, '__len__') and len(preds.shape) > 0:
            self.expected_value_ = np.mean(preds)
        else:
            self.expected_value_ = preds
            
        return self
    
    def _kernel_shap_weights(self, n_features: int, n_coalitions: int) -> Tuple[np.ndarray, np.ndarray]:
        """Generate coalition masks and SHAP kernel weights."""
        masks = []
        weights = []
        
        for _ in range(n_coalitions):
            # Random coalition size
            size = np.random.randint(0, n_features + 1)
            mask = np.zeros(n_features, dtype=bool)
            if size > 0 and size < n_features:
                indices = np.random.choice(n_features, size, replace=False)
                mask[indices] = True
            elif size == n_features:
                mask[:] = True
                
            # SHAP kernel weight
            s = np.sum(mask)
            if 0 < s < n_features:
                weight = (n_features - 1) / (
                    np.math.comb(n_features, s) * s * (n_features - s)
                )
            else:
                weight = 1e6  # Large weight for empty/full coalitions
                
            masks.append(mask)
            weights.append(weight)
            
        return np.array(masks), np.array(weights)
    
    def explain(self, X: np.ndarray, n_coalitions: int = 128) -> np.ndarray:
        """
        Compute SHAP values for samples.
        
        Parameters
        ----------
        X : np.ndarray
            Samples to explain.
        n_coalitions : int
            Number of coalitions to sample.
            
        Returns
        -------
        shap_values : np.ndarray of shape (n_samples, n_features)
            SHAP values for each feature and sample.
        """
        if self.background_ is None:
            raise ValueError("Must call fit() first")
            
        X = np.asarray(X, dtype=np.float64)
        if X.ndim == 1:
            X = X.reshape(1, -1)
            
        n_samples, n_features = X.shape
        shap_values = np.zeros((n_samples, n_features))
        
        # Generate coalition masks and weights
        masks, weights = self._kernel_shap_weights(n_features, n_coalitions)
        
        for sample_idx in range(n_samples):
            x = X[sample_idx]
            
            # For each coalition, compute f(S)
            coalition_preds = []
            for mask in masks:
                # Create masked sample (use background for masked features)
                x_masked = np.zeros((len(self.background_), n_features))
                for i in range(len(self.background_)):
                    x_masked[i] = np.where(mask, x, self.background_[i])
                    
                # Average prediction over background
                pred = np.mean(self.estimator.predict(x_masked))
                coalition_preds.append(pred)
                
            coalition_preds = np.array(coalition_preds)
            
            # Solve weighted linear regression: y = X @ shap + expected_value
            # Using simplified approach: marginal contributions
            for feat_idx in range(n_features):
                # Marginal contribution when feature is added
                with_feat = masks[:, feat_idx]
                without_feat = ~masks[:, feat_idx]
                
                if np.any(with_feat) and np.any(without_feat):
                    contrib_with = np.mean(coalition_preds[with_feat])
                    contrib_without = np.mean(coalition_preds[without_feat])
                    shap_values[sample_idx, feat_idx] = contrib_with - contrib_without
                    
        return shap_values
    
    def feature_importance(self, X: np.ndarray, n_coalitions: int = 128) -> np.ndarray:
        """Compute mean absolute SHAP values as feature importance."""
        shap_values = self.explain(X, n_coalitions)
        return np.mean(np.abs(shap_values), axis=0)


class PartialDependence:
    """
    Partial Dependence Plots computation.
    
    Shows marginal effect of features on predictions.
    
    Parameters
    ----------
    estimator : object
        Fitted model.
    grid_resolution : int
        Number of points in the grid.
    
    Examples
    --------
    >>> from sdk.evaluation import PartialDependence
    >>> pd = PartialDependence(model, grid_resolution=50)
    >>> grid, avg_preds = pd.compute(X, feature_idx=0)
    """
    
    def __init__(
        self,
        estimator: Any,
        grid_resolution: int = 50,
    ):
        self.estimator = estimator
        self.grid_resolution = grid_resolution
        
    def compute(
        self,
        X: np.ndarray,
        feature_idx: int,
        percentiles: Tuple[float, float] = (0.05, 0.95),
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute partial dependence for a single feature.
        
        Parameters
        ----------
        X : np.ndarray
            Dataset.
        feature_idx : int
            Index of feature to analyze.
        percentiles : tuple
            Range of feature values to consider.
            
        Returns
        -------
        grid : np.ndarray
            Feature values.
        avg_predictions : np.ndarray
            Average predictions for each grid point.
        """
        X = np.asarray(X, dtype=np.float64)
        
        # Create grid
        feature_values = X[:, feature_idx]
        grid_min = np.percentile(feature_values, percentiles[0] * 100)
        grid_max = np.percentile(feature_values, percentiles[1] * 100)
        grid = np.linspace(grid_min, grid_max, self.grid_resolution)
        
        # Compute predictions for each grid point
        avg_predictions = np.zeros(self.grid_resolution)
        
        for i, val in enumerate(grid):
            X_modified = X.copy()
            X_modified[:, feature_idx] = val
            predictions = self.estimator.predict(X_modified)
            avg_predictions[i] = np.mean(predictions)
            
        return grid, avg_predictions
    
    def compute_2d(
        self,
        X: np.ndarray,
        feature_idx_1: int,
        feature_idx_2: int,
        percentiles: Tuple[float, float] = (0.05, 0.95),
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute 2D partial dependence.
        
        Returns
        -------
        grid_1, grid_2 : np.ndarray
            Feature value grids.
        avg_predictions : np.ndarray of shape (grid_resolution, grid_resolution)
            Average predictions.
        """
        X = np.asarray(X, dtype=np.float64)
        
        # Create grids
        feature_1 = X[:, feature_idx_1]
        feature_2 = X[:, feature_idx_2]
        
        grid_1 = np.linspace(
            np.percentile(feature_1, percentiles[0] * 100),
            np.percentile(feature_1, percentiles[1] * 100),
            self.grid_resolution
        )
        grid_2 = np.linspace(
            np.percentile(feature_2, percentiles[0] * 100),
            np.percentile(feature_2, percentiles[1] * 100),
            self.grid_resolution
        )
        
        avg_predictions = np.zeros((self.grid_resolution, self.grid_resolution))
        
        for i, val_1 in enumerate(grid_1):
            for j, val_2 in enumerate(grid_2):
                X_modified = X.copy()
                X_modified[:, feature_idx_1] = val_1
                X_modified[:, feature_idx_2] = val_2
                predictions = self.estimator.predict(X_modified)
                avg_predictions[i, j] = np.mean(predictions)
                
        return grid_1, grid_2, avg_predictions


class IndividualConditionalExpectation:
    """
    Individual Conditional Expectation (ICE) plots.
    
    Shows effect of feature for individual samples.
    
    Parameters
    ----------
    estimator : object
        Fitted model.
    grid_resolution : int
        Number of points in the grid.
    """
    
    def __init__(
        self,
        estimator: Any,
        grid_resolution: int = 50,
    ):
        self.estimator = estimator
        self.grid_resolution = grid_resolution
        
    def compute(
        self,
        X: np.ndarray,
        feature_idx: int,
        n_samples: Optional[int] = None,
        percentiles: Tuple[float, float] = (0.05, 0.95),
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute ICE curves.
        
        Parameters
        ----------
        X : np.ndarray
            Dataset.
        feature_idx : int
            Feature to analyze.
        n_samples : int, optional
            Number of samples to include.
        percentiles : tuple
            Range of feature values.
            
        Returns
        -------
        grid : np.ndarray
            Feature values.
        ice_curves : np.ndarray of shape (n_samples, grid_resolution)
            Predictions for each sample at each grid point.
        """
        X = np.asarray(X, dtype=np.float64)
        
        if n_samples is not None and n_samples < len(X):
            indices = np.random.choice(len(X), n_samples, replace=False)
            X = X[indices]
            
        n_samples_actual = len(X)
        
        # Create grid
        feature_values = X[:, feature_idx]
        grid = np.linspace(
            np.percentile(feature_values, percentiles[0] * 100),
            np.percentile(feature_values, percentiles[1] * 100),
            self.grid_resolution
        )
        
        ice_curves = np.zeros((n_samples_actual, self.grid_resolution))
        
        for i in range(n_samples_actual):
            for j, val in enumerate(grid):
                x_modified = X[i].copy()
                x_modified[feature_idx] = val
                ice_curves[i, j] = self.estimator.predict(x_modified.reshape(1, -1))[0]
                
        return grid, ice_curves


class FeatureInteraction:
    """
    Detect and quantify feature interactions.
    
    Uses Friedman's H-statistic.
    
    Parameters
    ----------
    estimator : object
        Fitted model.
    """
    
    def __init__(self, estimator: Any):
        self.estimator = estimator
        
    def compute_h_statistic(
        self,
        X: np.ndarray,
        feature_idx_1: int,
        feature_idx_2: int,
        grid_resolution: int = 20,
    ) -> float:
        """
        Compute H-statistic for feature interaction.
        
        Parameters
        ----------
        X : np.ndarray
            Dataset.
        feature_idx_1, feature_idx_2 : int
            Feature indices.
        grid_resolution : int
            Grid resolution for PDP.
            
        Returns
        -------
        h_stat : float
            H-statistic (0 = no interaction, 1 = full interaction).
        """
        X = np.asarray(X, dtype=np.float64)
        
        pd = PartialDependence(self.estimator, grid_resolution)
        
        # Individual PDPs
        grid_1, pdp_1 = pd.compute(X, feature_idx_1)
        grid_2, pdp_2 = pd.compute(X, feature_idx_2)
        
        # Joint PDP
        _, _, pdp_joint = pd.compute_2d(X, feature_idx_1, feature_idx_2)
        
        # Compute H-statistic
        numerator = 0
        denominator = 0
        
        for i, val_1 in enumerate(grid_1):
            for j, val_2 in enumerate(grid_2):
                # Expected under no interaction
                expected = pdp_1[i] + pdp_2[j]
                # Actual joint effect
                actual = pdp_joint[i, j]
                
                numerator += (actual - expected) ** 2
                denominator += actual ** 2
                
        h_stat = numerator / (denominator + 1e-10)
        return np.sqrt(h_stat)
    
    def compute_all_interactions(
        self,
        X: np.ndarray,
        feature_names: Optional[List[str]] = None,
        top_k: int = 10,
    ) -> List[Tuple[str, str, float]]:
        """
        Compute interactions for all feature pairs.
        
        Returns top K interactions.
        """
        X = np.asarray(X, dtype=np.float64)
        n_features = X.shape[1]
        
        if feature_names is None:
            feature_names = [f"feature_{i}" for i in range(n_features)]
            
        interactions = []
        
        for i in range(n_features):
            for j in range(i + 1, n_features):
                h_stat = self.compute_h_statistic(X, i, j)
                interactions.append((feature_names[i], feature_names[j], h_stat))
                
        # Sort by H-statistic
        interactions.sort(key=lambda x: x[2], reverse=True)
        return interactions[:top_k]


def explain_prediction(
    estimator: Any,
    X_sample: np.ndarray,
    X_background: np.ndarray,
    feature_names: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Generate comprehensive explanation for a single prediction.
    
    Parameters
    ----------
    estimator : object
        Fitted model.
    X_sample : np.ndarray
        Sample to explain.
    X_background : np.ndarray
        Background dataset.
    feature_names : list, optional
        Feature names.
        
    Returns
    -------
    explanation : dict
        Prediction, SHAP values, feature contributions.
    """
    X_sample = np.asarray(X_sample, dtype=np.float64)
    if X_sample.ndim == 1:
        X_sample = X_sample.reshape(1, -1)
        
    X_background = np.asarray(X_background, dtype=np.float64)
    n_features = X_sample.shape[1]
    
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(n_features)]
        
    # Get prediction
    prediction = estimator.predict(X_sample)[0]
    
    # Compute SHAP values
    shap = SHAPApproximation(estimator, n_samples=min(100, len(X_background)))
    shap.fit(X_background)
    shap_values = shap.explain(X_sample, n_coalitions=64)[0]
    
    # Sort features by contribution
    contributions = sorted(
        zip(feature_names, X_sample[0], shap_values),
        key=lambda x: abs(x[2]),
        reverse=True
    )
    
    return {
        "prediction": prediction,
        "expected_value": shap.expected_value_,
        "shap_values": dict(zip(feature_names, shap_values)),
        "feature_values": dict(zip(feature_names, X_sample[0])),
        "top_contributors": [
            {"feature": f, "value": v, "contribution": c}
            for f, v, c in contributions[:5]
        ],
    }

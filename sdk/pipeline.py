"""
FHE-compatible ML Pipelines.

Provides sklearn-style Pipeline and FeatureUnion for composing
transformers and models that work with encrypted data.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np


class PipelineStepType(Enum):
    """Types of pipeline steps."""

    TRANSFORMER = "transformer"
    ESTIMATOR = "estimator"
    FEATURE_UNION = "feature_union"


@dataclass
class PipelineStep:
    """A single step in a pipeline."""

    name: str
    transformer: Any
    step_type: PipelineStepType = PipelineStepType.TRANSFORMER


class Pipeline:
    """
    FHE-compatible Pipeline for chaining transformers and estimators.

    Similar to sklearn.pipeline.Pipeline but designed for FHE operations.

    Example:
        >>> from xcapit_fhe import Pipeline, StandardScaler, LogisticRegression
        >>> pipe = Pipeline([
        ...     ('scaler', StandardScaler()),
        ...     ('classifier', LogisticRegression())
        ... ])
        >>> pipe.fit(X_train, y_train)
        >>> predictions = pipe.predict(X_test)
    """

    def __init__(
        self,
        steps: List[Tuple[str, Any]],
        memory: Optional[str] = None,
        verbose: bool = False,
    ):
        """
        Initialize pipeline.

        Args:
            steps: List of (name, transformer/estimator) tuples
            memory: Optional caching directory (not used in FHE mode)
            verbose: Print progress during fit/transform
        """
        self.steps = []
        self.named_steps = {}
        self.memory = memory
        self.verbose = verbose
        self._fitted = False

        for name, transformer in steps:
            self._validate_step(name, transformer)
            self.steps.append(PipelineStep(name=name, transformer=transformer))
            self.named_steps[name] = transformer

    def _validate_step(self, name: str, transformer: Any) -> None:
        """Validate a pipeline step."""
        if not isinstance(name, str):
            raise TypeError(f"Step name must be string, got {type(name)}")

        if name in self.named_steps:
            raise ValueError(f"Duplicate step name: {name}")

        # Check for required methods
        if not (hasattr(transformer, "fit") or hasattr(transformer, "transform")):
            raise TypeError(f"Step '{name}' must have fit() or transform() method")

    def _is_transformer(self, step: PipelineStep) -> bool:
        """Check if step is a transformer (not final estimator)."""
        return hasattr(step.transformer, "transform")

    def _is_estimator(self, step: PipelineStep) -> bool:
        """Check if step is an estimator with predict."""
        return hasattr(step.transformer, "predict")

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None, **fit_params) -> "Pipeline":
        """
        Fit the pipeline.

        Sequentially fit and transform all steps except the last,
        then fit the last step.

        Args:
            X: Training data
            y: Target values (optional)
            **fit_params: Parameters passed to fit methods

        Returns:
            self
        """
        Xt = X

        # Fit and transform all steps except the last
        for i, step in enumerate(self.steps[:-1]):
            if self.verbose:
                print(f"Fitting step {i + 1}/{len(self.steps)}: {step.name}")

            # Get fit_params for this step
            step_params = self._filter_params(fit_params, step.name)

            if hasattr(step.transformer, "fit_transform"):
                Xt = step.transformer.fit_transform(Xt, y, **step_params)
            else:
                step.transformer.fit(Xt, y, **step_params)
                if hasattr(step.transformer, "transform"):
                    Xt = step.transformer.transform(Xt)

        # Fit the last step
        if self.steps:
            last_step = self.steps[-1]
            if self.verbose:
                print(f"Fitting final step: {last_step.name}")

            step_params = self._filter_params(fit_params, last_step.name)
            last_step.transformer.fit(Xt, y, **step_params)

        self._fitted = True
        return self

    def _filter_params(self, params: Dict, step_name: str) -> Dict:
        """Filter parameters for a specific step."""
        prefix = f"{step_name}__"
        return {k[len(prefix) :]: v for k, v in params.items() if k.startswith(prefix)}

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Transform data through all transformers.

        Args:
            X: Data to transform

        Returns:
            Transformed data
        """
        if not self._fitted:
            raise RuntimeError("Pipeline must be fitted before transform")

        Xt = X
        for step in self.steps:
            if hasattr(step.transformer, "transform"):
                Xt = step.transformer.transform(Xt)

        return Xt

    def fit_transform(
        self, X: np.ndarray, y: Optional[np.ndarray] = None, **fit_params
    ) -> np.ndarray:
        """Fit and transform in one step."""
        return self.fit(X, y, **fit_params).transform(X)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Transform and predict.

        Args:
            X: Data to predict

        Returns:
            Predictions from final estimator
        """
        if not self._fitted:
            raise RuntimeError("Pipeline must be fitted before predict")

        Xt = X

        # Transform through all steps except the last
        for step in self.steps[:-1]:
            if hasattr(step.transformer, "transform"):
                Xt = step.transformer.transform(Xt)

        # Predict with the last step
        if self.steps and hasattr(self.steps[-1].transformer, "predict"):
            return self.steps[-1].transformer.predict(Xt)

        raise AttributeError("Final step does not have predict method")

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict class probabilities."""
        if not self._fitted:
            raise RuntimeError("Pipeline must be fitted before predict_proba")

        Xt = X
        for step in self.steps[:-1]:
            if hasattr(step.transformer, "transform"):
                Xt = step.transformer.transform(Xt)

        if self.steps and hasattr(self.steps[-1].transformer, "predict_proba"):
            return self.steps[-1].transformer.predict_proba(Xt)

        raise AttributeError("Final step does not have predict_proba method")

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Score the pipeline."""
        if not self._fitted:
            raise RuntimeError("Pipeline must be fitted before score")

        Xt = X
        for step in self.steps[:-1]:
            if hasattr(step.transformer, "transform"):
                Xt = step.transformer.transform(Xt)

        if self.steps and hasattr(self.steps[-1].transformer, "score"):
            return self.steps[-1].transformer.score(Xt, y)

        raise AttributeError("Final step does not have score method")

    def get_params(self, deep: bool = True) -> Dict[str, Any]:
        """Get pipeline parameters."""
        params = {
            "memory": self.memory,
            "verbose": self.verbose,
            "steps": [(s.name, s.transformer) for s in self.steps],
        }

        if deep:
            for step in self.steps:
                if hasattr(step.transformer, "get_params"):
                    step_params = step.transformer.get_params(deep=True)
                    for key, value in step_params.items():
                        params[f"{step.name}__{key}"] = value

        return params

    def set_params(self, **params) -> "Pipeline":
        """Set pipeline parameters."""
        for key, value in params.items():
            if "__" in key:
                step_name, param_name = key.split("__", 1)
                if step_name in self.named_steps:
                    if hasattr(self.named_steps[step_name], "set_params"):
                        self.named_steps[step_name].set_params(**{param_name: value})
            elif key == "memory":
                self.memory = value
            elif key == "verbose":
                self.verbose = value

        return self

    def __len__(self) -> int:
        """Return number of steps."""
        return len(self.steps)

    def __getitem__(self, key: Union[int, str]) -> Any:
        """Get step by index or name."""
        if isinstance(key, int):
            return self.steps[key].transformer
        return self.named_steps[key]


class FeatureUnion:
    """
    FHE-compatible FeatureUnion for concatenating transformer outputs.

    Similar to sklearn.pipeline.FeatureUnion but designed for FHE operations.

    Example:
        >>> from xcapit_fhe import FeatureUnion, PCA, SelectKBest
        >>> union = FeatureUnion([
        ...     ('pca', PCA(n_components=5)),
        ...     ('select', SelectKBest(k=10))
        ... ])
        >>> X_combined = union.fit_transform(X)
    """

    def __init__(
        self,
        transformer_list: List[Tuple[str, Any]],
        n_jobs: Optional[int] = None,
        transformer_weights: Optional[Dict[str, float]] = None,
        verbose: bool = False,
    ):
        """
        Initialize FeatureUnion.

        Args:
            transformer_list: List of (name, transformer) tuples
            n_jobs: Number of parallel jobs (not used in FHE mode)
            transformer_weights: Optional weights for each transformer
            verbose: Print progress
        """
        self.transformer_list = []
        self.named_transformers = {}
        self.n_jobs = n_jobs
        self.transformer_weights = transformer_weights or {}
        self.verbose = verbose
        self._fitted = False

        for name, transformer in transformer_list:
            if not isinstance(name, str):
                raise TypeError(f"Transformer name must be string, got {type(name)}")

            if name in self.named_transformers:
                raise ValueError(f"Duplicate transformer name: {name}")

            self.transformer_list.append((name, transformer))
            self.named_transformers[name] = transformer

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None, **fit_params) -> "FeatureUnion":
        """Fit all transformers."""
        for i, (name, transformer) in enumerate(self.transformer_list):
            if self.verbose:
                print(f"Fitting transformer {i + 1}/{len(self.transformer_list)}: {name}")

            step_params = {
                k.split("__", 1)[1]: v for k, v in fit_params.items() if k.startswith(f"{name}__")
            }

            transformer.fit(X, y, **step_params)

        self._fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Transform and concatenate outputs."""
        if not self._fitted:
            raise RuntimeError("FeatureUnion must be fitted before transform")

        outputs = []
        for name, transformer in self.transformer_list:
            Xt = transformer.transform(X)

            # Apply weight if specified
            weight = self.transformer_weights.get(name, 1.0)
            if weight != 1.0:
                Xt = Xt * weight

            outputs.append(Xt)

        return np.hstack(outputs)

    def fit_transform(
        self, X: np.ndarray, y: Optional[np.ndarray] = None, **fit_params
    ) -> np.ndarray:
        """Fit and transform in one step."""
        return self.fit(X, y, **fit_params).transform(X)

    def get_feature_names_out(self, input_features: Optional[List[str]] = None) -> List[str]:
        """Get output feature names."""
        names = []
        for name, transformer in self.transformer_list:
            if hasattr(transformer, "get_feature_names_out"):
                trans_names = transformer.get_feature_names_out(input_features)
                names.extend([f"{name}__{n}" for n in trans_names])
            elif hasattr(transformer, "n_components"):
                names.extend([f"{name}_{i}" for i in range(transformer.n_components)])
        return names

    def get_params(self, deep: bool = True) -> Dict[str, Any]:
        """Get parameters."""
        params = {
            "n_jobs": self.n_jobs,
            "transformer_weights": self.transformer_weights,
            "verbose": self.verbose,
            "transformer_list": self.transformer_list,
        }

        if deep:
            for name, transformer in self.transformer_list:
                if hasattr(transformer, "get_params"):
                    for key, value in transformer.get_params(deep=True).items():
                        params[f"{name}__{key}"] = value

        return params

    def set_params(self, **params) -> "FeatureUnion":
        """Set parameters."""
        for key, value in params.items():
            if "__" in key:
                name, param_name = key.split("__", 1)
                if name in self.named_transformers:
                    if hasattr(self.named_transformers[name], "set_params"):
                        self.named_transformers[name].set_params(**{param_name: value})
            elif key == "transformer_weights":
                self.transformer_weights = value

        return self


class ColumnTransformer:
    """
    FHE-compatible ColumnTransformer for applying different transformers to columns.

    Example:
        >>> from xcapit_fhe import ColumnTransformer, StandardScaler, OneHotEncoder
        >>> ct = ColumnTransformer([
        ...     ('num', StandardScaler(), [0, 1, 2]),
        ...     ('cat', OneHotEncoder(), [3, 4])
        ... ])
        >>> X_transformed = ct.fit_transform(X)
    """

    def __init__(
        self,
        transformers: List[Tuple[str, Any, Union[List[int], List[str], slice]]],
        remainder: str = "drop",
        sparse_threshold: float = 0.3,
        n_jobs: Optional[int] = None,
        transformer_weights: Optional[Dict[str, float]] = None,
        verbose: bool = False,
    ):
        """
        Initialize ColumnTransformer.

        Args:
            transformers: List of (name, transformer, columns) tuples
            remainder: 'drop' or 'passthrough' for unspecified columns
            sparse_threshold: Not used in FHE mode
            n_jobs: Number of parallel jobs (not used)
            transformer_weights: Optional weights
            verbose: Print progress
        """
        self.transformers = transformers
        self.remainder = remainder
        self.sparse_threshold = sparse_threshold
        self.n_jobs = n_jobs
        self.transformer_weights = transformer_weights or {}
        self.verbose = verbose
        self._fitted = False
        self._n_features = None
        self._remainder_cols = None

    def _get_column_indices(
        self, columns: Union[List[int], List[str], slice], X: np.ndarray
    ) -> List[int]:
        """Convert column specification to indices."""
        if isinstance(columns, slice):
            return list(range(*columns.indices(X.shape[1])))
        elif isinstance(columns, list):
            if all(isinstance(c, int) for c in columns):
                return columns
            # Assume column names - not supported in basic numpy
            raise ValueError("Column names not supported without DataFrame")
        return list(columns)

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> "ColumnTransformer":
        """Fit all transformers."""
        self._n_features = X.shape[1]
        all_cols = set(range(self._n_features))
        used_cols = set()

        for name, transformer, columns in self.transformers:
            if self.verbose:
                print(f"Fitting transformer: {name}")

            col_indices = self._get_column_indices(columns, X)
            used_cols.update(col_indices)

            X_subset = X[:, col_indices]
            transformer.fit(X_subset, y)

        # Determine remainder columns
        self._remainder_cols = sorted(all_cols - used_cols)

        self._fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Transform data."""
        if not self._fitted:
            raise RuntimeError("ColumnTransformer must be fitted before transform")

        outputs = []

        for name, transformer, columns in self.transformers:
            col_indices = self._get_column_indices(columns, X)
            X_subset = X[:, col_indices]

            Xt = transformer.transform(X_subset)

            weight = self.transformer_weights.get(name, 1.0)
            if weight != 1.0:
                Xt = Xt * weight

            outputs.append(Xt)

        # Handle remainder
        if self.remainder == "passthrough" and self._remainder_cols:
            outputs.append(X[:, self._remainder_cols])

        return np.hstack(outputs) if outputs else np.empty((X.shape[0], 0))

    def fit_transform(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> np.ndarray:
        """Fit and transform."""
        return self.fit(X, y).transform(X)

    def get_params(self, deep: bool = True) -> Dict[str, Any]:
        """Get parameters."""
        return {
            "transformers": self.transformers,
            "remainder": self.remainder,
            "sparse_threshold": self.sparse_threshold,
            "n_jobs": self.n_jobs,
            "transformer_weights": self.transformer_weights,
            "verbose": self.verbose,
        }


def make_pipeline(*steps, memory: Optional[str] = None, verbose: bool = False) -> Pipeline:
    """
    Convenience function to create a Pipeline with auto-generated names.

    Example:
        >>> from xcapit_fhe import make_pipeline, StandardScaler, LogisticRegression
        >>> pipe = make_pipeline(StandardScaler(), LogisticRegression())
    """
    named_steps = []
    name_counts = {}

    for step in steps:
        # Generate name from class name
        name = step.__class__.__name__.lower()

        # Handle duplicates
        if name in name_counts:
            name_counts[name] += 1
            name = f"{name}_{name_counts[name]}"
        else:
            name_counts[name] = 0

        named_steps.append((name, step))

    return Pipeline(named_steps, memory=memory, verbose=verbose)


def make_union(*transformers, n_jobs: Optional[int] = None, verbose: bool = False) -> FeatureUnion:
    """
    Convenience function to create a FeatureUnion with auto-generated names.

    Example:
        >>> from xcapit_fhe import make_union, PCA, SelectKBest
        >>> union = make_union(PCA(n_components=5), SelectKBest(k=10))
    """
    named_transformers = []
    name_counts = {}

    for transformer in transformers:
        name = transformer.__class__.__name__.lower()

        if name in name_counts:
            name_counts[name] += 1
            name = f"{name}_{name_counts[name]}"
        else:
            name_counts[name] = 0

        named_transformers.append((name, transformer))

    return FeatureUnion(named_transformers, n_jobs=n_jobs, verbose=verbose)


class TransformedTargetRegressor:
    """
    Meta-regressor that transforms the target variable.

    Example:
        >>> from xcapit_fhe import TransformedTargetRegressor, LinearRegression
        >>> import numpy as np
        >>> model = TransformedTargetRegressor(
        ...     regressor=LinearRegression(),
        ...     func=np.log1p,
        ...     inverse_func=np.expm1
        ... )
    """

    def __init__(
        self,
        regressor: Any,
        transformer: Optional[Any] = None,
        func: Optional[Callable] = None,
        inverse_func: Optional[Callable] = None,
        check_inverse: bool = True,
    ):
        """
        Initialize TransformedTargetRegressor.

        Args:
            regressor: The regressor to use
            transformer: Transformer for the target (with fit/transform/inverse_transform)
            func: Function to transform target
            inverse_func: Function to inverse transform predictions
            check_inverse: Check that transform is invertible
        """
        self.regressor = regressor
        self.transformer = transformer
        self.func = func
        self.inverse_func = inverse_func
        self.check_inverse = check_inverse
        self._fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray, **fit_params) -> "TransformedTargetRegressor":
        """Fit the regressor on transformed target."""
        # Transform y
        if self.transformer is not None:
            y_transformed = self.transformer.fit_transform(y.reshape(-1, 1)).ravel()
        elif self.func is not None:
            y_transformed = self.func(y)
        else:
            y_transformed = y

        # Fit regressor
        self.regressor.fit(X, y_transformed, **fit_params)

        self._fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict and inverse transform."""
        if not self._fitted:
            raise RuntimeError("Must fit before predict")

        y_pred_transformed = self.regressor.predict(X)

        # Inverse transform
        if self.transformer is not None:
            return self.transformer.inverse_transform(y_pred_transformed.reshape(-1, 1)).ravel()
        elif self.inverse_func is not None:
            return self.inverse_func(y_pred_transformed)

        return y_pred_transformed

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Score on original scale."""
        y_pred = self.predict(X)
        # R² score
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        return 1 - (ss_res / ss_tot)

    def get_params(self, deep: bool = True) -> Dict[str, Any]:
        """Get parameters."""
        params = {
            "regressor": self.regressor,
            "transformer": self.transformer,
            "func": self.func,
            "inverse_func": self.inverse_func,
            "check_inverse": self.check_inverse,
        }

        if deep and hasattr(self.regressor, "get_params"):
            for key, value in self.regressor.get_params(deep=True).items():
                params[f"regressor__{key}"] = value

        return params


__all__ = [
    "Pipeline",
    "FeatureUnion",
    "ColumnTransformer",
    "make_pipeline",
    "make_union",
    "TransformedTargetRegressor",
    "PipelineStep",
    "PipelineStepType",
]

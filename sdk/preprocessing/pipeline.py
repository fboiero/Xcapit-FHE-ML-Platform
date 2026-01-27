"""
FHE-Compatible Preprocessing Pipeline

A pipeline class for chaining multiple preprocessing transformations
before FHE encryption.
"""

import json
from dataclasses import dataclass, field
from typing import Optional, Union, Any
from enum import Enum
import numpy as np

from .transformers import (
    BaseTransformer,
    TransformerState,
    StandardScaler,
    MinMaxScaler,
    RobustScaler,
    OneHotEncoder,
    OrdinalEncoder,
    MissingValueHandler,
    OutlierHandler,
    FeatureSelector
)


class PipelineState(Enum):
    """State of the pipeline in its lifecycle."""
    EMPTY = "empty"
    CONFIGURED = "configured"
    FITTED = "fitted"


@dataclass
class PipelineStep:
    """A single step in the preprocessing pipeline."""
    name: str
    transformer: BaseTransformer
    columns: Optional[list] = None  # Apply only to specific columns (None = all)


class PreprocessingPipeline:
    """
    Chain multiple preprocessing transformations for FHE data preparation.

    The pipeline executes transformers in order and stores all parameters
    for reproducibility and inverse transformation.

    Example
    -------
    ```python
    from sdk.preprocessing import PreprocessingPipeline, StandardScaler, MissingValueHandler

    # Create pipeline
    pipeline = PreprocessingPipeline()
    pipeline.add_step('impute', MissingValueHandler(strategy='mean'))
    pipeline.add_step('scale', StandardScaler())

    # Fit and transform
    X_processed = pipeline.fit_transform(X_train)

    # Transform new data with same parameters
    X_test_processed = pipeline.transform(X_test)

    # Get parameters for storage
    params = pipeline.get_params()
    ```
    """

    def __init__(self, name: str = "preprocessing_pipeline"):
        self.name = name
        self.steps: list[PipelineStep] = []
        self.state = PipelineState.EMPTY
        self._input_shape: Optional[tuple] = None
        self._output_shape: Optional[tuple] = None
        self._feature_names_in: Optional[list] = None
        self._feature_names_out: Optional[list] = None

    def add_step(
        self,
        name: str,
        transformer: BaseTransformer,
        columns: Optional[list] = None
    ) -> 'PreprocessingPipeline':
        """
        Add a transformation step to the pipeline.

        Parameters
        ----------
        name : str
            Unique name for this step.
        transformer : BaseTransformer
            Transformer instance to apply.
        columns : list[int], optional
            Column indices to apply this transformer to.
            If None, applies to all columns.

        Returns
        -------
        self : PreprocessingPipeline
            Returns self for method chaining.
        """
        # Check for duplicate names
        existing_names = [s.name for s in self.steps]
        if name in existing_names:
            raise ValueError(f"Step name '{name}' already exists in pipeline")

        self.steps.append(PipelineStep(name=name, transformer=transformer, columns=columns))
        self.state = PipelineState.CONFIGURED
        return self

    def remove_step(self, name: str) -> 'PreprocessingPipeline':
        """Remove a step from the pipeline by name."""
        self.steps = [s for s in self.steps if s.name != name]
        if len(self.steps) == 0:
            self.state = PipelineState.EMPTY
        return self

    def get_step(self, name: str) -> Optional[PipelineStep]:
        """Get a step by name."""
        for step in self.steps:
            if step.name == name:
                return step
        return None

    def fit(
        self,
        X: np.ndarray,
        y: Optional[np.ndarray] = None,
        feature_names: Optional[list] = None
    ) -> 'PreprocessingPipeline':
        """
        Fit all transformers in the pipeline.

        Parameters
        ----------
        X : np.ndarray
            Training data.
        y : np.ndarray, optional
            Target values (passed to transformers that need it).
        feature_names : list, optional
            Names of input features.

        Returns
        -------
        self : PreprocessingPipeline
            Fitted pipeline.
        """
        if len(self.steps) == 0:
            raise RuntimeError("Pipeline has no steps. Add steps before fitting.")

        X = self._validate_input(X)
        self._input_shape = X.shape
        self._feature_names_in = feature_names or [f"feature_{i}" for i in range(X.shape[1])]

        # Fit each transformer sequentially, transforming data as we go
        X_current = X.copy()

        for step in self.steps:
            if step.columns is not None:
                # Fit only on specified columns
                X_subset = X_current[:, step.columns]
                step.transformer.fit(X_subset, y)
                # Transform for next step
                X_transformed = step.transformer.transform(X_subset)
                X_current = self._replace_columns(X_current, X_transformed, step.columns)
            else:
                # Fit on all columns
                step.transformer.fit(X_current, y)
                X_current = step.transformer.transform(X_current)

        self._output_shape = X_current.shape
        self._update_feature_names()
        self.state = PipelineState.FITTED
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Apply all transformations in the pipeline.

        Parameters
        ----------
        X : np.ndarray
            Data to transform.

        Returns
        -------
        X_transformed : np.ndarray
            Transformed data ready for FHE encryption.
        """
        self._check_fitted()
        X = self._validate_input(X)
        X_current = X.copy()

        for step in self.steps:
            if step.columns is not None:
                X_subset = X_current[:, step.columns]
                X_transformed = step.transformer.transform(X_subset)
                X_current = self._replace_columns(X_current, X_transformed, step.columns)
            else:
                X_current = step.transformer.transform(X_current)

        return X_current

    def fit_transform(
        self,
        X: np.ndarray,
        y: Optional[np.ndarray] = None,
        feature_names: Optional[list] = None
    ) -> np.ndarray:
        """Fit and transform in one step."""
        return self.fit(X, y, feature_names).transform(X)

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """
        Reverse all transformations in the pipeline.

        Note: Not all transformers support inverse_transform.

        Parameters
        ----------
        X : np.ndarray
            Transformed data.

        Returns
        -------
        X_original : np.ndarray
            Data in original scale.
        """
        self._check_fitted()
        X = self._validate_input(X)
        X_current = X.copy()

        # Apply inverse transforms in reverse order
        for step in reversed(self.steps):
            if step.columns is not None:
                # This is complex for column-specific transforms after shape changes
                # For now, only support full-column inverse transforms
                raise NotImplementedError(
                    "inverse_transform not supported for column-specific transforms"
                )
            else:
                X_current = step.transformer.inverse_transform(X_current)

        return X_current

    def get_params(self) -> dict:
        """
        Get all pipeline parameters for serialization.

        Returns
        -------
        params : dict
            Complete pipeline configuration and learned parameters.
        """
        return {
            "name": self.name,
            "state": self.state.value,
            "input_shape": list(self._input_shape) if self._input_shape else None,
            "output_shape": list(self._output_shape) if self._output_shape else None,
            "feature_names_in": self._feature_names_in,
            "feature_names_out": self._feature_names_out,
            "steps": [
                {
                    "name": step.name,
                    "columns": step.columns,
                    "transformer": step.transformer.get_params()
                }
                for step in self.steps
            ]
        }

    def save(self, path: str) -> None:
        """Save pipeline parameters to JSON file."""
        with open(path, 'w') as f:
            json.dump(self.get_params(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> 'PreprocessingPipeline':
        """Load pipeline from JSON file."""
        with open(path, 'r') as f:
            params = json.load(f)
        return cls.from_params(params)

    @classmethod
    def from_params(cls, params: dict) -> 'PreprocessingPipeline':
        """
        Reconstruct pipeline from saved parameters.

        Note: This creates transformers in fitted state with saved parameters.
        """
        pipeline = cls(name=params.get("name", "loaded_pipeline"))
        pipeline._input_shape = tuple(params["input_shape"]) if params.get("input_shape") else None
        pipeline._output_shape = tuple(params["output_shape"]) if params.get("output_shape") else None
        pipeline._feature_names_in = params.get("feature_names_in")
        pipeline._feature_names_out = params.get("feature_names_out")

        # Reconstruct transformers
        transformer_classes = {
            "StandardScaler": StandardScaler,
            "MinMaxScaler": MinMaxScaler,
            "RobustScaler": RobustScaler,
            "OneHotEncoder": OneHotEncoder,
            "OrdinalEncoder": OrdinalEncoder,
            "MissingValueHandler": MissingValueHandler,
            "OutlierHandler": OutlierHandler,
            "FeatureSelector": FeatureSelector,
        }

        for step_params in params.get("steps", []):
            transformer_type = step_params["transformer"]["type"]
            if transformer_type not in transformer_classes:
                raise ValueError(f"Unknown transformer type: {transformer_type}")

            # Create transformer and restore state
            transformer = transformer_classes[transformer_type]()
            transformer.state = TransformerState.FITTED
            transformer._params = step_params["transformer"]["params"]
            transformer.name = step_params["transformer"]["name"]

            # Restore specific attributes from params
            cls._restore_transformer_attributes(transformer, transformer._params)

            pipeline.steps.append(PipelineStep(
                name=step_params["name"],
                transformer=transformer,
                columns=step_params.get("columns")
            ))

        pipeline.state = PipelineState.FITTED if params.get("state") == "fitted" else PipelineState.CONFIGURED
        return pipeline

    @staticmethod
    def _restore_transformer_attributes(transformer: BaseTransformer, params: dict):
        """Restore specific attributes to transformer from params."""
        if isinstance(transformer, (StandardScaler,)):
            transformer._mean = np.array(params.get("mean", []))
            transformer._std = np.array(params.get("std", []))
        elif isinstance(transformer, MinMaxScaler):
            transformer._min = np.array(params.get("min", []))
            transformer._max = np.array(params.get("max", []))
            transformer._data_range = np.array(params.get("data_range", []))
            transformer.feature_range = tuple(params.get("feature_range", (-1, 1)))
        elif isinstance(transformer, RobustScaler):
            transformer._center = np.array(params.get("center", []))
            transformer._scale = np.array(params.get("scale", []))
        elif isinstance(transformer, MissingValueHandler):
            transformer._fill_values = np.array(params.get("fill_values", []))
            transformer.strategy = params.get("strategy", "mean")
        elif isinstance(transformer, OutlierHandler):
            transformer._lower_bounds = np.array(params.get("lower_bounds", []))
            transformer._upper_bounds = np.array(params.get("upper_bounds", []))
        elif isinstance(transformer, FeatureSelector):
            transformer._selected_indices = params.get("selected_indices", [])
            transformer._n_features_in = params.get("n_features_in", 0)

    def get_feature_names_out(self) -> list:
        """Get output feature names after all transformations."""
        self._check_fitted()
        return self._feature_names_out.copy() if self._feature_names_out else []

    def summary(self) -> str:
        """Get a human-readable summary of the pipeline."""
        lines = [
            f"PreprocessingPipeline: {self.name}",
            f"State: {self.state.value}",
            f"Steps: {len(self.steps)}",
            "-" * 40
        ]

        for i, step in enumerate(self.steps):
            cols = f"columns={step.columns}" if step.columns else "all columns"
            lines.append(f"  {i+1}. {step.name}: {step.transformer.__class__.__name__} ({cols})")

        if self._input_shape:
            lines.append("-" * 40)
            lines.append(f"Input shape: {self._input_shape}")
            lines.append(f"Output shape: {self._output_shape}")

        return "\n".join(lines)

    def _validate_input(self, X: np.ndarray) -> np.ndarray:
        """Validate and convert input to numpy array."""
        if not isinstance(X, np.ndarray):
            X = np.array(X)
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        return X.astype(np.float64)

    def _check_fitted(self):
        """Raise error if pipeline is not fitted."""
        if self.state != PipelineState.FITTED:
            raise RuntimeError("Pipeline must be fitted before transform")

    def _replace_columns(
        self,
        X: np.ndarray,
        X_new: np.ndarray,
        columns: list
    ) -> np.ndarray:
        """Replace specific columns in X with X_new values."""
        X_result = X.copy()
        for i, col_idx in enumerate(columns):
            if i < X_new.shape[1]:
                X_result[:, col_idx] = X_new[:, i]
        return X_result

    def _update_feature_names(self):
        """Update output feature names based on transformations."""
        names = self._feature_names_in.copy() if self._feature_names_in else []

        for step in self.steps:
            if hasattr(step.transformer, 'get_feature_names_out'):
                try:
                    names = step.transformer.get_feature_names_out(names)
                except Exception:
                    pass  # Keep previous names if method fails
            elif isinstance(step.transformer, FeatureSelector):
                indices = step.transformer.get_support()
                names = [names[i] for i in indices if i < len(names)]

        self._feature_names_out = names


# Convenience function to create common preprocessing pipelines
def create_standard_pipeline(
    handle_missing: bool = True,
    handle_outliers: bool = False,
    scaling: str = 'standard'
) -> PreprocessingPipeline:
    """
    Create a standard preprocessing pipeline for FHE.

    Parameters
    ----------
    handle_missing : bool, default=True
        Add missing value imputation step.
    handle_outliers : bool, default=False
        Add outlier handling step.
    scaling : str, default='standard'
        Scaling method: 'standard', 'minmax', 'robust', or 'none'.

    Returns
    -------
    pipeline : PreprocessingPipeline
        Configured (but not fitted) pipeline.

    Example
    -------
    ```python
    pipeline = create_standard_pipeline(scaling='minmax')
    X_processed = pipeline.fit_transform(X_train)
    ```
    """
    pipeline = PreprocessingPipeline(name="standard_fhe_pipeline")

    if handle_missing:
        pipeline.add_step('impute', MissingValueHandler(strategy='mean'))

    if handle_outliers:
        pipeline.add_step('outliers', OutlierHandler(method='iqr', strategy='clip'))

    if scaling == 'standard':
        pipeline.add_step('scale', StandardScaler())
    elif scaling == 'minmax':
        pipeline.add_step('scale', MinMaxScaler(feature_range=(-1, 1)))
    elif scaling == 'robust':
        pipeline.add_step('scale', RobustScaler())
    elif scaling != 'none':
        raise ValueError(f"Unknown scaling method: {scaling}")

    return pipeline


def create_categorical_pipeline(
    categorical_columns: list,
    encoding: str = 'onehot',
    scaling: str = 'standard'
) -> PreprocessingPipeline:
    """
    Create a pipeline that handles categorical features.

    Parameters
    ----------
    categorical_columns : list[int]
        Indices of categorical columns.
    encoding : str, default='onehot'
        Encoding method: 'onehot' or 'ordinal'.
    scaling : str, default='standard'
        Scaling method for numeric features.

    Returns
    -------
    pipeline : PreprocessingPipeline
        Configured pipeline for mixed data types.
    """
    pipeline = PreprocessingPipeline(name="categorical_fhe_pipeline")

    # Handle missing values first
    pipeline.add_step('impute', MissingValueHandler(strategy='most_frequent'))

    # Encode categoricals
    if encoding == 'onehot':
        pipeline.add_step('encode', OneHotEncoder(columns=categorical_columns))
    else:
        pipeline.add_step('encode', OrdinalEncoder(columns=categorical_columns))

    # Scale all features
    if scaling == 'standard':
        pipeline.add_step('scale', StandardScaler())
    elif scaling == 'minmax':
        pipeline.add_step('scale', MinMaxScaler(feature_range=(-1, 1)))

    return pipeline

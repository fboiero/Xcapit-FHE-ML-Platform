"""
FHE-Compatible Preprocessing Module

This module provides preprocessing transformers and pipelines optimized
for use with Fully Homomorphic Encryption (FHE) machine learning.

Key Features:
- Scalers optimized for CKKS encryption (StandardScaler, MinMaxScaler, RobustScaler)
- Categorical encoders (OneHotEncoder, OrdinalEncoder)
- Missing value and outlier handling
- Feature selection
- Pipeline composition for chaining transformations

Example Usage:
    ```python
    from sdk.preprocessing import PreprocessingPipeline, StandardScaler, MissingValueHandler
    from sdk.utils.data_loader import SecureDataLoader

    # Create preprocessing pipeline
    pipeline = PreprocessingPipeline()
    pipeline.add_step('impute', MissingValueHandler(strategy='mean'))
    pipeline.add_step('scale', StandardScaler())

    # Preprocess data
    X_processed = pipeline.fit_transform(X_train)

    # Then encrypt for FHE
    loader = SecureDataLoader(normalize=False)  # Already normalized by pipeline
    encrypted = loader.encrypt(X_processed, y_train)

    # For new data, use same preprocessing
    X_test_processed = pipeline.transform(X_test)
    ```

Quick Start with Standard Pipeline:
    ```python
    from sdk.preprocessing import create_standard_pipeline

    pipeline = create_standard_pipeline(
        handle_missing=True,
        handle_outliers=False,
        scaling='minmax'  # Best for FHE: scales to [-1, 1]
    )
    X_processed = pipeline.fit_transform(X_train)
    ```
"""

from .transformers import (
    # Base classes
    BaseTransformer,
    TransformerState,
    TransformerParams,

    # Scalers
    StandardScaler,
    MinMaxScaler,
    RobustScaler,

    # Encoders
    OneHotEncoder,
    OrdinalEncoder,

    # Data quality handlers
    MissingValueHandler,
    OutlierHandler,

    # Feature selection
    FeatureSelector,
)

from .pipeline import (
    PreprocessingPipeline,
    PipelineState,
    PipelineStep,

    # Convenience functions
    create_standard_pipeline,
    create_categorical_pipeline,
)

__all__ = [
    # Base
    'BaseTransformer',
    'TransformerState',
    'TransformerParams',

    # Scalers
    'StandardScaler',
    'MinMaxScaler',
    'RobustScaler',

    # Encoders
    'OneHotEncoder',
    'OrdinalEncoder',

    # Handlers
    'MissingValueHandler',
    'OutlierHandler',

    # Feature selection
    'FeatureSelector',

    # Pipeline
    'PreprocessingPipeline',
    'PipelineState',
    'PipelineStep',

    # Convenience
    'create_standard_pipeline',
    'create_categorical_pipeline',
]

__version__ = '1.0.0'

"""
Data Preprocessing Utilities for FHE-ML Platform.

Provides scalers, encoders, imputers, and transformers
compatible with encrypted data operations.
"""

from .scalers import (
    StandardScaler,
    MinMaxScaler,
    MaxAbsScaler,
    RobustScaler,
    Normalizer,
)

from .encoders import (
    LabelEncoder,
    OneHotEncoder,
    OrdinalEncoder,
    TargetEncoder,
)

from .imputers import (
    SimpleImputer,
    KNNImputer,
    IterativeImputer,
)

from .transformers import (
    PolynomialFeatures,
    PowerTransformer,
    QuantileTransformer,
    FunctionTransformer,
)

__all__ = [
    # Scalers
    "StandardScaler",
    "MinMaxScaler",
    "MaxAbsScaler",
    "RobustScaler",
    "Normalizer",
    # Encoders
    "LabelEncoder",
    "OneHotEncoder",
    "OrdinalEncoder",
    "TargetEncoder",
    # Imputers
    "SimpleImputer",
    "KNNImputer",
    "IterativeImputer",
    # Transformers
    "PolynomialFeatures",
    "PowerTransformer",
    "QuantileTransformer",
    "FunctionTransformer",
]

"""
Data Preprocessing Utilities for FHE-ML Platform.

Provides scalers, encoders, imputers, and transformers
compatible with encrypted data operations.
"""

from .encoders import (
    LabelEncoder,
    OneHotEncoder,
    OrdinalEncoder,
    TargetEncoder,
)
from .imputers import (
    IterativeImputer,
    KNNImputer,
    SimpleImputer,
)
from .scalers import (
    MaxAbsScaler,
    MinMaxScaler,
    Normalizer,
    RobustScaler,
    StandardScaler,
)
from .transformers import (
    FunctionTransformer,
    PolynomialFeatures,
    PowerTransformer,
    QuantileTransformer,
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

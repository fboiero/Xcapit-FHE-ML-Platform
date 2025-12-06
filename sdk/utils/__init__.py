"""Utility functions for FHE-ML SDK."""

from .data_loader import (
    EncryptedDataset,
    SecureDataLoader,
)
from .validators import (
    ValidationError,
    check_fhe_compatibility,
    validate_data_shape,
    validate_feature_range,
    validate_numeric_data,
    validate_target,
)
from .serialization import (
    save_model,
    load_model,
    get_model_info,
    export_weights_json,
    import_weights_json,
    compute_weights_hash,
)

__all__ = [
    # Data loading
    "EncryptedDataset",
    "SecureDataLoader",
    # Validation
    "ValidationError",
    "check_fhe_compatibility",
    "validate_data_shape",
    "validate_feature_range",
    "validate_numeric_data",
    "validate_target",
    # Serialization
    "save_model",
    "load_model",
    "get_model_info",
    "export_weights_json",
    "import_weights_json",
    "compute_weights_hash",
]

"""Utility functions for FHE-ML SDK."""

from .data_loader import (
    EncryptedDataset,
    SecureDataLoader,
)
from .serialization import (
    compute_weights_hash,
    export_weights_json,
    get_model_info,
    import_weights_json,
    load_model,
    save_model,
)
from .validators import (
    ValidationError,
    check_fhe_compatibility,
    validate_data_shape,
    validate_feature_range,
    validate_numeric_data,
    validate_target,
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

"""Xcapit FHE-ML SDK - Privacy-preserving machine learning.

This SDK provides tools for training machine learning models
on encrypted data using Fully Homomorphic Encryption (FHE).

Example:
    >>> from xcapit_fhe import SecureDataLoader
    >>> loader = SecureDataLoader()
    >>> encrypted_data = loader.encrypt(df)
"""

from .encryption import (
    CKKSEncryptor,
    CKKSParameters,
    EncryptedMatrix,
    EncryptedVector,
    FHEContextManager,
    SecurityLevel,
)
from .utils import (
    EncryptedDataset,
    SecureDataLoader,
    ValidationError,
    check_fhe_compatibility,
)
from .models import (
    BaseFHEModel,
    FHEModel,
    LinearRegression,
    LogisticRegression,
    ModelConfig,
    ModelState,
    SigmoidApproximation,
)

__version__ = "0.1.0"

__all__ = [
    # Encryption
    "CKKSEncryptor",
    "CKKSParameters",
    "EncryptedMatrix",
    "EncryptedVector",
    "FHEContextManager",
    "SecurityLevel",
    # Utils
    "EncryptedDataset",
    "SecureDataLoader",
    "ValidationError",
    "check_fhe_compatibility",
    # Models
    "BaseFHEModel",
    "FHEModel",
    "LinearRegression",
    "LogisticRegression",
    "ModelConfig",
    "ModelState",
    "SigmoidApproximation",
    # Version
    "__version__",
]

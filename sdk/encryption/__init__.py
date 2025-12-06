"""Encryption module for FHE operations.

This module provides CKKS encryption capabilities for
privacy-preserving machine learning.
"""

from .context_manager import (
    CKKSParameters,
    FHEContextManager,
    SecurityLevel,
)
from .ckks_wrapper import (
    CKKSEncryptor,
    EncryptedMatrix,
    EncryptedVector,
)

__all__ = [
    "CKKSParameters",
    "FHEContextManager",
    "SecurityLevel",
    "CKKSEncryptor",
    "EncryptedMatrix",
    "EncryptedVector",
]

"""Encryption module for FHE operations.

This module provides CKKS encryption capabilities for
privacy-preserving machine learning.
"""

from .ckks_wrapper import (
    CKKSEncryptor,
    EncryptedMatrix,
    EncryptedVector,
)
from .context_manager import (
    CKKSParameters,
    FHEContextManager,
    SecurityLevel,
)
from .optimized_engine import (
    PROFILE_CONFIGS,
    ContextPool,
    EncryptionStats,
    LazyEncryptedVector,
    OptimizationProfile,
    OptimizedFHEEngine,
    ProfileConfig,
)

__all__ = [
    # Core
    "CKKSParameters",
    "FHEContextManager",
    "SecurityLevel",
    "CKKSEncryptor",
    "EncryptedMatrix",
    "EncryptedVector",
    # Optimized Engine
    "OptimizedFHEEngine",
    "OptimizationProfile",
    "ProfileConfig",
    "ContextPool",
    "LazyEncryptedVector",
    "EncryptionStats",
    "PROFILE_CONFIGS",
]

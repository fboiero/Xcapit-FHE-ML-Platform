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
from .optimized_engine import (
    OptimizedFHEEngine,
    OptimizationProfile,
    ProfileConfig,
    ContextPool,
    LazyEncryptedVector,
    EncryptionStats,
    PROFILE_CONFIGS,
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

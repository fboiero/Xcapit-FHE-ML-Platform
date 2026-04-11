"""Multi-Party Computation (MPC) module for the Xcapit FHE-ML SDK.

Provides secure key distribution, model aggregation, and threshold
decryption without requiring a trusted central party.

Components
----------
SecretSharer
    Shamir's Secret Sharing — split secrets into K-of-N shares.
MaskGenerator
    Low-level pairwise mask and seed generation utilities.
SecureAggregator
    Pairwise-masking protocol for private vector summation.
ThresholdDecryptor
    Threshold decryption requiring K-of-N key-share holders.
KeyCeremony
    Distributed key generation ceremony orchestrator.
MPCProtocol
    High-level orchestrator combining all three primitives for
    consortium model training workflows.
"""

from .secret_sharing import SAFE_PRIME, SecretSharer
from .secure_aggregation import MaskGenerator, MPCProtocol, SecureAggregator
from .threshold import KeyCeremony, ThresholdDecryptor

__all__ = [
    "KeyCeremony",
    "MaskGenerator",
    "MPCProtocol",
    "SAFE_PRIME",
    "SecretSharer",
    "SecureAggregator",
    "ThresholdDecryptor",
]

"""Xcapit FHE-ML SDK.

Privacy-preserving machine learning toolkit with:
- FHE (Fully Homomorphic Encryption) via TenSEAL CKKS
- ZKP (Zero-Knowledge Proofs) for verifiable contributions
- MPC (Multi-Party Computation) for secure aggregation
- DP (Differential Privacy) for formal privacy guarantees
"""

__version__ = "0.7.0"

# ── Crypto modules (always available — pure Python + numpy) ──────────────

from sdk.zkp import ZKProver, ZKVerifier, PedersenCommitment  # noqa: E402
from sdk.mpc import SecretSharer, SecureAggregator, ThresholdDecryptor  # noqa: E402
from sdk.privacy import (  # noqa: E402
    LaplaceMechanism,
    GaussianMechanism,
    PrivacyAccountant,
    GradientClipper,
    DPDataLoader,
)

# ── FHE modules (require tenseal) ───────────────────────────────────────

try:
    from sdk.encryption.context_manager import CKKSParameters, SecurityLevel
    from sdk.encryption.ckks_wrapper import CKKSEncryptor
    from sdk.utils.data_loader import SecureDataLoader
except ImportError:
    CKKSParameters = None  # type: ignore[assignment,misc]
    SecurityLevel = None  # type: ignore[assignment,misc]
    CKKSEncryptor = None  # type: ignore[assignment,misc]
    SecureDataLoader = None  # type: ignore[assignment,misc]

# ── Blockchain modules (require web3) ───────────────────────────────────

try:
    from sdk.blockchain.connector import BlockchainConnector, Network
except ImportError:
    BlockchainConnector = None  # type: ignore[assignment,misc]
    Network = None  # type: ignore[assignment,misc]

__all__ = [
    # Version
    "__version__",
    # ZKP
    "ZKProver",
    "ZKVerifier",
    "PedersenCommitment",
    # MPC
    "SecretSharer",
    "SecureAggregator",
    "ThresholdDecryptor",
    # Differential Privacy
    "LaplaceMechanism",
    "GaussianMechanism",
    "PrivacyAccountant",
    "GradientClipper",
    "DPDataLoader",
    # FHE (optional)
    "CKKSParameters",
    "SecurityLevel",
    "CKKSEncryptor",
    "SecureDataLoader",
    # Blockchain (optional)
    "BlockchainConnector",
    "Network",
]

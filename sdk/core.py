"""
Core SDK imports for demos and notebooks.

This module provides a simplified import path that avoids
complex dependencies for quick demos.
"""

# FHE Encryption
# Blockchain
from .blockchain import (
    ARBITRUM_SEPOLIA_CONTRACTS,
    NETWORK_CONFIGS,
    BlockchainConnector,
    GovernanceClient,
    ModelRegistryClient,
    Network,
    NetworkConfig,
    get_contracts,
)
from .encryption import (
    CKKSEncryptor,
    CKKSParameters,
    EncryptedMatrix,
    EncryptedVector,
    FHEContextManager,
    SecurityLevel,
)

# Core models
from .models.base import (
    BaseFHEModel,
    FHEModel,
    ModelConfig,
    ModelState,
)
from .models.decision_tree import (
    DecisionTree,
    DecisionTreeClassifier,
    DecisionTreeRegressor,
    SplitFunction,
    TreeConfig,
    TreeType,
)
from .models.kmeans import (
    InitMethod,
    KMeans,
    KMeansConfig,
    MiniBatchKMeans,
)
from .models.linear_regression import LinearRegression
from .models.logistic_regression import LogisticRegression, SigmoidApproximation

# Data loading
from .utils import (
    EncryptedDataset,
    SecureDataLoader,
)

__all__ = [
    # Encryption
    "CKKSEncryptor",
    "CKKSParameters",
    "FHEContextManager",
    "EncryptedMatrix",
    "EncryptedVector",
    "SecurityLevel",
    # Models
    "BaseFHEModel",
    "FHEModel",
    "ModelConfig",
    "ModelState",
    "LinearRegression",
    "LogisticRegression",
    "SigmoidApproximation",
    "DecisionTree",
    "DecisionTreeClassifier",
    "DecisionTreeRegressor",
    "TreeConfig",
    "TreeType",
    "SplitFunction",
    "KMeans",
    "KMeansConfig",
    "MiniBatchKMeans",
    "InitMethod",
    # Data
    "SecureDataLoader",
    "EncryptedDataset",
    # Blockchain
    "BlockchainConnector",
    "Network",
    "GovernanceClient",
    "ModelRegistryClient",
    "NetworkConfig",
    "NETWORK_CONFIGS",
    "ARBITRUM_SEPOLIA_CONTRACTS",
    "get_contracts",
]

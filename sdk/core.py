"""
Core SDK imports for demos and notebooks.

This module provides a simplified import path that avoids
complex dependencies for quick demos.
"""

# FHE Encryption
from .encryption import (
    CKKSEncryptor,
    CKKSParameters,
    FHEContextManager,
    EncryptedMatrix,
    EncryptedVector,
    SecurityLevel,
)

# Core models
from .models.base import (
    BaseFHEModel,
    FHEModel,
    ModelConfig,
    ModelState,
)
from .models.linear_regression import LinearRegression
from .models.logistic_regression import LogisticRegression, SigmoidApproximation
from .models.decision_tree import (
    DecisionTree,
    DecisionTreeClassifier,
    DecisionTreeRegressor,
    TreeConfig,
    TreeType,
    SplitFunction,
)
from .models.kmeans import (
    KMeans,
    KMeansConfig,
    MiniBatchKMeans,
    InitMethod,
)

# Data loading
from .utils import (
    SecureDataLoader,
    EncryptedDataset,
)

# Blockchain
from .blockchain import (
    BlockchainConnector,
    Network,
    GovernanceClient,
    ModelRegistryClient,
    NetworkConfig,
    NETWORK_CONFIGS,
    ARBITRUM_SEPOLIA_CONTRACTS,
    get_contracts,
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

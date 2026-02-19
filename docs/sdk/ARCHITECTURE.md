# SDK Architecture

This document explains the internal architecture and design decisions of the Xcapit FHE-ML SDK.

## Overview

The SDK enables machine learning on encrypted data using Fully Homomorphic Encryption (FHE). The key challenge is that traditional ML operations (comparisons, non-linear functions) don't work directly on encrypted data. The SDK solves this through polynomial approximations and soft variants of algorithms.

```
┌─────────────────────────────────────────────────────────────────┐
│                         Application                              │
├─────────────────────────────────────────────────────────────────┤
│  SecureDataLoader  │  FHEModel  │  CLI  │  GovernanceClient     │
├─────────────────────────────────────────────────────────────────┤
│          Models Layer (LinearReg, LogisticReg, Tree, KMeans)    │
├─────────────────────────────────────────────────────────────────┤
│                    Encryption Layer (CKKS)                       │
├─────────────────────────────────────────────────────────────────┤
│                      TenSEAL / SEAL                              │
└─────────────────────────────────────────────────────────────────┘
```

## Core Design Principles

### 1. Privacy by Default

All data operations assume encrypted inputs. The SDK never requires raw data exposure.

```python
# Data stays encrypted throughout the pipeline
encrypted_data = loader.encrypt(raw_data)
model.fit(encrypted_data)  # Training on encrypted data
predictions = model.predict(encrypted_data)  # Encrypted predictions
```

### 2. Familiar API

The SDK mirrors scikit-learn's API for easy adoption:

```python
# Same interface as sklearn
model = LinearRegression()
model.fit(X, y)
predictions = model.predict(X)
```

### 3. Configurable Security/Performance Trade-offs

Users can choose their security level and optimization profile:

```python
# High security, slower
ctx = FHEContextManager(security_level=SecurityLevel.BITS_256)

# Fast inference
engine = OptimizedFHEEngine(profile=OptimizationProfile.FAST)
```

## Encryption Layer

### CKKS Scheme

The SDK uses the CKKS (Cheon-Kim-Kim-Song) scheme, which supports:
- **Approximate arithmetic**: Real number computations on encrypted data
- **SIMD operations**: Parallel operations on encrypted vectors
- **Rescaling**: Manage noise growth after multiplications

```
┌──────────────────────────────────────────────────────┐
│                    CKKS Parameters                    │
├──────────────────────────────────────────────────────┤
│  poly_modulus_degree: 8192 (slots = 4096)            │
│  coeff_mod_bit_sizes: [60, 40, 40, 60]               │
│  scale: 2^40                                          │
│  security_level: 128-bit                              │
└──────────────────────────────────────────────────────┘
```

### Key Components

**FHEContextManager**: Creates and manages encryption contexts

```python
class FHEContextManager:
    def create_context(self) -> ts.Context:
        # Generate public/secret keys
        # Configure CKKS parameters
        # Return ready-to-use context
```

**EncryptedVector**: Wrapper with metadata

```python
class EncryptedVector:
    data: ts.CKKSVector      # Encrypted data
    shape: tuple             # Original shape
    context_id: str          # For key management
    created_at: datetime     # Audit trail

    def __add__(self, other): ...  # Homomorphic add
    def __mul__(self, other): ...  # Homomorphic multiply
    def dot(self, other): ...      # Dot product
```

**OptimizedFHEEngine**: Performance optimization

```python
class OptimizedFHEEngine:
    # Context pooling for thread safety
    context_pool: ContextPool

    # Lazy evaluation for operation fusion
    def encrypt_lazy(self, data) -> LazyEncryptedVector:
        # Defer encryption until needed
        # Fuse multiple operations
```

### Optimization Profiles

| Profile | Poly Degree | Scale | Batch Size | Use Case |
|---------|-------------|-------|------------|----------|
| FAST | 4096 | 20-bit | 64 | Inference |
| BALANCED | 8192 | 40-bit | 32 | General |
| PRECISE | 16384 | 40-bit | 16 | High accuracy |
| MEMORY_EFFICIENT | 4096 | 20-bit | 8 | Limited RAM |
| THROUGHPUT | 8192 | 40-bit | 64 | Batch processing |

## Models Layer

### The FHE Challenge

Standard ML operations that don't work on encrypted data:
- **Comparisons**: `if x > threshold` (branching)
- **Non-linear functions**: `sigmoid(x)`, `relu(x)`
- **Division**: Not supported in CKKS

### Solutions Implemented

#### 1. Linear Regression

**No modifications needed** - Linear operations work directly:

```python
# Standard: y = X @ w + b
# FHE: y_enc = X_enc @ w + b  (same formula)

class LinearRegression:
    def fit(self, X_enc, y_enc):
        for epoch in range(epochs):
            # Forward pass (encrypted)
            pred = X_enc.dot(self.weights) + self.bias

            # Gradient computation (on encrypted data)
            error = pred - y_enc
            gradient = X_enc.T.dot(error) / n_samples

            # Update weights (plaintext)
            self.weights -= lr * gradient.decrypt()
```

#### 2. Logistic Regression - Polynomial Sigmoid

**Problem**: `sigmoid(x) = 1 / (1 + exp(-x))` requires exp and division.

**Solution**: Polynomial approximation

```python
class SigmoidApproximation(Enum):
    LINEAR = "linear"      # σ(x) ≈ 0.5 + 0.25x
    DEGREE3 = "degree3"    # σ(x) ≈ 0.5 + 0.197x - 0.004x³
    DEGREE5 = "degree5"    # More accurate, higher degree
    MINIMAX = "minimax"    # Optimal polynomial (Chebyshev)

def sigmoid_poly(x, approximation):
    if approximation == SigmoidApproximation.DEGREE3:
        # Polynomial that can be computed homomorphically
        return 0.5 + 0.197 * x - 0.004 * x * x * x
```

**Trade-off**: Higher degree = more accurate but slower (more multiplications = more noise)

#### 3. Decision Tree - Soft Splits

**Problem**: `if feature[i] <= threshold` requires comparison.

**Solution**: Replace hard splits with sigmoid-based soft splits

```
Hard split:                    Soft split:
       /\                           /\
      /  \                     σ((x-t)/τ)
     /    \                        │
   x≤t    x>t                 [0, 1] continuous
```

```python
class SoftDecisionTree:
    def split_probability(self, x, threshold, temperature):
        # Soft split using sigmoid approximation
        # temperature controls sharpness
        return sigmoid_poly((x - threshold) / temperature)

    def predict(self, X):
        # Traverse all paths with probabilities
        # Weight leaf predictions by path probability
        left_prob = self.split_probability(X[:, feature], threshold, temp)
        right_prob = 1 - left_prob

        return left_prob * left_prediction + right_prob * right_prediction
```

#### 4. KMeans - Soft Assignments

**Problem**: `argmin(distances)` requires comparison.

**Solution**: Softmax-based soft assignments

```python
class SoftKMeans:
    def assign_clusters(self, X, centroids, temperature):
        # Compute distances to all centroids
        distances = compute_distances(X, centroids)

        # Soft assignment using softmax (polynomial approximation)
        # Instead of hard argmin, use probability distribution
        weights = softmax_poly(-distances / temperature)

        return weights  # Shape: (n_samples, n_clusters)

    def update_centroids(self, X, weights):
        # Weighted average (works on encrypted data)
        return weights.T @ X / weights.sum(axis=0)
```

### Model Configuration

```python
@dataclass
class ModelConfig:
    learning_rate: float = 0.01
    epochs: int = 100
    batch_size: int = 32
    early_stopping: bool = True
    patience: int = 10
    regularization: float = 0.0

@dataclass
class TreeConfig:
    max_depth: int = 5
    split_function: SplitFunction = SplitFunction.SIGMOID
    temperature: float = 1.0
    min_samples_leaf: int = 1
```

## Blockchain Layer

### Purpose

- **Audit Trail**: Record model training events
- **Verification**: Prove model integrity
- **Governance**: Multi-party consortium management

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    GovernanceClient                      │
│                    ModelRegistryClient                   │
├─────────────────────────────────────────────────────────┤
│                   BlockchainConnector                    │
├─────────────────────────────────────────────────────────┤
│                       Web3.py                            │
├─────────────────────────────────────────────────────────┤
│              Arbitrum / Ethereum Network                 │
└─────────────────────────────────────────────────────────┘
```

### Smart Contracts

**ModelRegistry.sol**: Track model versions

```solidity
struct Model {
    address owner;
    bytes32 weightsHash;
    string metadata;
    uint256 timestamp;
    bool verified;
}

function registerModel(bytes32 modelId, bytes32 weightsHash, string metadata);
function verifyModel(bytes32 modelId, bytes32 expectedHash) returns (bool);
```

**ConsortiumGovernance.sol**: Multi-party coordination

```solidity
struct Consortium {
    string name;
    address[] members;
    mapping(address => uint256) contributions;
    Proposal[] proposals;
}

function createProposal(uint256 consortiumId, ProposalType type, bytes data);
function vote(uint256 consortiumId, uint256 proposalId, bool support);
function executeProposal(uint256 consortiumId, uint256 proposalId);
```

## CLI Architecture

```
cli/
├── __init__.py          # Argument parser setup
├── utils.py             # Helper functions
└── commands/
    ├── encryption.py    # init, encrypt, decrypt
    ├── training.py      # train
    ├── prediction.py    # predict
    ├── blockchain.py    # blockchain subcommands
    ├── api_keys.py      # api-key subcommands
    ├── benchmark.py     # benchmark
    └── info.py          # info, version
```

### Command Flow

```
User Input → Parser → Command Handler → SDK Functions → Output

Example:
$ xcapit-fhe train --model logistic-regression --data enc.bin

1. Parser extracts: model="logistic-regression", data="enc.bin"
2. cmd_train() loads encrypted data
3. Creates LogisticRegression model
4. Calls model.fit(encrypted_data)
5. Saves model to output file
```

## Monitoring & Metrics

### Thread-Safe Metrics Collection

```python
class MetricsCollector:
    _metrics: dict  # Thread-safe storage
    _lock: Lock

    def increment(self, name, value=1): ...
    def gauge(self, name, value): ...
    def histogram(self, name, value): ...

    @contextmanager
    def timer(self, name):
        start = time.time()
        yield
        self.histogram(f"{name}_ms", (time.time() - start) * 1000)
```

### Predefined Metrics

```python
# API metrics
METRIC_API_REQUESTS = "api.requests"
METRIC_API_LATENCY = "api.latency_ms"

# Model metrics
METRIC_MODEL_TRAININGS = "model.trainings"
METRIC_MODEL_PREDICTIONS = "model.predictions"

# Encryption metrics
METRIC_ENCRYPTION_OPS = "encryption.operations"
METRIC_ENCRYPTION_TIME = "encryption.time_ms"
```

## Error Handling

### Custom Exceptions

```python
class ValidationError(Exception):
    """Data validation failed"""

class EncryptionError(Exception):
    """Encryption operation failed"""

class BlockchainError(Exception):
    """Blockchain interaction failed"""
```

### Validation Chain

```python
def check_fhe_compatibility(X, y=None):
    validate_numeric_data(X)      # Must be numeric
    validate_data_shape(X)        # Must be 2D
    validate_feature_range(X)     # Values in reasonable range
    if y is not None:
        validate_target(y)        # Target compatibility
```

## Testing Strategy

### Test Categories

1. **Unit Tests**: Individual components
   - `test_encryption.py`: CKKS operations
   - `test_models.py`: Model training/prediction

2. **Integration Tests**: End-to-end workflows
   - `test_fhe_integration.py`: Full encrypted ML pipeline

3. **Blockchain Tests**: Smart contract interactions
   - `test_governance_client.py`: Consortium operations

### Test Fixtures

```python
@pytest.fixture
def fhe_context():
    """Shared encryption context for tests"""
    ctx_manager = FHEContextManager(SecurityLevel.BITS_128)
    return ctx_manager.create_context()

@pytest.fixture
def sample_encrypted_data(fhe_context):
    """Sample encrypted dataset"""
    X = np.random.randn(100, 10)
    return encrypt(X, fhe_context)
```

## Future Considerations

### Planned Enhancements

1. **Multi-Key FHE**: Different parties with different keys
2. **Ensemble Methods**: Combine multiple FHE models
3. **GPU Acceleration**: CUDA support for faster operations
4. **Scheme Switching**: Support BGV/TFHE for specific operations

### Scalability

```
Current Limits:
- Vector size: ~4096 elements per ciphertext
- Multiplication depth: ~5-10 levels
- Memory: ~300KB per encrypted vector

Optimization Paths:
- Batch packing: Multiple values per ciphertext
- Lazy evaluation: Defer operations, fuse when possible
- Context pooling: Reuse expensive context creation
```

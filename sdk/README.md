# Xcapit FHE-ML SDK

Privacy-preserving machine learning using Fully Homomorphic Encryption (FHE).

Train and run ML models on encrypted data without ever exposing the underlying information.

## Features

- **4 ML Models**: LinearRegression, LogisticRegression, DecisionTree, KMeans
- **CKKS Encryption**: 128/192/256-bit security levels via TenSEAL
- **Blockchain Audit**: Arbitrum integration for model verification
- **CLI Tool**: Command-line interface for all operations
- **scikit-learn API**: Familiar `fit()`, `predict()` interface

## Installation

```bash
# From the project root
pip install -e .

# Or install dependencies directly
pip install tenseal numpy web3
```

## Quick Start

### 1. Basic Encryption and Training

```python
import numpy as np
from sdk import (
    FHEContextManager,
    SecurityLevel,
    LinearRegression,
    ModelConfig,
)

# Create encryption context
ctx_manager = FHEContextManager(security_level=SecurityLevel.BITS_128)
context = ctx_manager.create_context()

# Prepare data
X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
y = np.array([3, 7, 11, 15])

# Train model (data encrypted internally)
model = LinearRegression()
config = ModelConfig(learning_rate=0.01, epochs=100)
model.fit(X, y, config=config)

# Predict
predictions = model.predict(X)
print(f"Predictions: {predictions}")
```

### 2. Using SecureDataLoader

```python
import pandas as pd
from sdk import SecureDataLoader, LogisticRegression

# Load and encrypt data
loader = SecureDataLoader()
df = pd.read_csv("data.csv")

encrypted_dataset = loader.load_and_encrypt(
    df,
    target_column="label",
    normalize=True
)

# Train on encrypted data
model = LogisticRegression()
model.fit(encrypted_dataset.X, encrypted_dataset.y)

# Predict
predictions = model.predict(encrypted_dataset.X)
```

### 3. CLI Usage

```bash
# Initialize FHE context
xcapit-fhe init --security-level 128 --output context.bin

# Encrypt data
xcapit-fhe encrypt --input data.csv --context context.bin --output encrypted.bin

# Train model
xcapit-fhe train --model linear-regression --data encrypted.bin --output model.bin

# Make predictions
xcapit-fhe predict --model model.bin --data encrypted.bin --output predictions.csv
```

## Models

### LinearRegression

Gradient descent on encrypted data for regression tasks.

```python
from sdk import LinearRegression, ModelConfig

model = LinearRegression()
config = ModelConfig(
    learning_rate=0.01,
    epochs=100,
    batch_size=32,
    early_stopping=True,
    patience=10
)
model.fit(X, y, config=config)
```

**Parameters:**
- `learning_rate`: Step size for gradient descent (default: 0.01)
- `epochs`: Number of training iterations (default: 100)
- `regularization`: L2 regularization strength (default: 0.0)

### LogisticRegression

Binary classification with polynomial sigmoid approximations.

```python
from sdk import LogisticRegression, SigmoidApproximation

model = LogisticRegression(
    sigmoid_approximation=SigmoidApproximation.DEGREE3
)
model.fit(X, y)
probabilities = model.predict_proba(X)
```

**Sigmoid Approximations:**
- `LINEAR`: Fast but less accurate
- `DEGREE3`: Good balance (recommended)
- `DEGREE5`: More accurate, slower
- `MINIMAX`: Optimal polynomial approximation

### DecisionTree

Soft decision trees using sigmoid splits for FHE compatibility.

```python
from sdk import DecisionTreeClassifier, TreeConfig, SplitFunction

config = TreeConfig(
    max_depth=5,
    split_function=SplitFunction.SIGMOID,
    temperature=1.0
)
model = DecisionTreeClassifier(config=config)
model.fit(X, y)
```

**Parameters:**
- `max_depth`: Maximum tree depth (default: 5)
- `split_function`: SIGMOID or TANH
- `temperature`: Controls split softness (lower = sharper)

### KMeans

Soft clustering with differentiable assignments.

```python
from sdk import KMeans, KMeansConfig, InitMethod

config = KMeansConfig(
    n_clusters=3,
    init_method=InitMethod.KMEANS_PLUS_PLUS,
    max_iterations=100,
    temperature=1.0
)
model = KMeans(config=config)
model.fit(X)
labels = model.predict(X)
centroids = model.cluster_centers_
```

**Initialization Methods:**
- `RANDOM`: Random centroid selection
- `KMEANS_PLUS_PLUS`: Smart initialization (recommended)
- `UNIFORM`: Uniform distribution

## Encryption

### Security Levels

```python
from sdk import FHEContextManager, SecurityLevel

# 128-bit security (fastest)
ctx = FHEContextManager(security_level=SecurityLevel.BITS_128)

# 192-bit security (balanced)
ctx = FHEContextManager(security_level=SecurityLevel.BITS_192)

# 256-bit security (most secure)
ctx = FHEContextManager(security_level=SecurityLevel.BITS_256)
```

### CKKS Parameters

```python
from sdk import CKKSParameters, CKKSEncryptor

params = CKKSParameters(
    poly_modulus_degree=8192,
    coeff_mod_bit_sizes=[60, 40, 40, 60],
    scale_bits=40
)
encryptor = CKKSEncryptor(params)

# Encrypt vector
encrypted = encryptor.encrypt([1.0, 2.0, 3.0])

# Perform operations on encrypted data
result = encrypted + encrypted  # Homomorphic addition
result = encrypted * 2.0        # Scalar multiplication

# Decrypt
decrypted = encryptor.decrypt(result)
```

### Optimization Profiles

```python
from sdk.encryption import OptimizedFHEEngine, OptimizationProfile

# For inference (fast)
engine = OptimizedFHEEngine(profile=OptimizationProfile.FAST)

# For training (balanced)
engine = OptimizedFHEEngine(profile=OptimizationProfile.BALANCED)

# For high accuracy
engine = OptimizedFHEEngine(profile=OptimizationProfile.PRECISE)

# For limited memory
engine = OptimizedFHEEngine(profile=OptimizationProfile.MEMORY_EFFICIENT)

# For batch processing
engine = OptimizedFHEEngine(profile=OptimizationProfile.THROUGHPUT)
```

## Blockchain Integration

### Register Model on Arbitrum

```python
from sdk import BlockchainConnector, ModelRegistryClient, Network

# Connect to Arbitrum
connector = BlockchainConnector(
    network=Network.ARBITRUM_ONE,
    private_key="your-private-key"
)

# Register model
registry = ModelRegistryClient(connector)
tx_hash = registry.register_model(
    model_id="model-001",
    model_hash="sha256-hash-of-weights",
    metadata={"accuracy": 0.95, "version": "1.0.0"}
)

# Verify model
is_valid = registry.verify_model("model-001", "sha256-hash-of-weights")
```

### Consortium Governance

```python
from sdk.blockchain import GovernanceClient

governance = GovernanceClient(connector)

# Create consortium
consortium_id = governance.create_consortium(
    name="Healthcare ML Consortium",
    description="Privacy-preserving patient risk models"
)

# Add member
governance.add_member(consortium_id, member_address="0x...")

# Submit proposal
proposal_id = governance.submit_proposal(
    consortium_id,
    proposal_type="start_training",
    data={"model_type": "logistic_regression", "epochs": 100}
)

# Vote
governance.vote(consortium_id, proposal_id, vote=True)
```

## Data Quality

Assess data quality while preserving privacy (works on metadata only).

```python
from sdk.quality import DataQualityCalculator, DataProfile

calculator = DataQualityCalculator()

# Create profile from encrypted data metadata
profile = DataProfile(
    record_count=1000,
    feature_count=10,
    null_counts={"age": 5, "income": 12},
    duplicate_count=3,
    last_updated="2025-01-25T10:00:00Z"
)

# Calculate quality score
score = calculator.calculate_score(profile)
print(f"Completeness: {score.completeness}%")
print(f"Uniqueness: {score.uniqueness}%")
print(f"Overall: {score.overall}%")
```

## Utilities

### Model Serialization

```python
from sdk.utils import save_model, load_model, compute_weights_hash

# Save trained model
save_model(model, "model.bin", include_history=True)

# Load model
loaded_model = load_model("model.bin")

# Compute hash for verification
weights_hash = compute_weights_hash(model)
```

### Data Validation

```python
from sdk.utils import check_fhe_compatibility, ValidationError

try:
    check_fhe_compatibility(X, y)
except ValidationError as e:
    print(f"Data not compatible: {e}")
```

## CLI Reference

```bash
# Show help
xcapit-fhe --help

# Initialize context
xcapit-fhe init [--security-level 128|192|256] [--output FILE]

# Encrypt data
xcapit-fhe encrypt --input CSV --context FILE [--normalize] [--output FILE]

# Decrypt data
xcapit-fhe decrypt --input FILE --context FILE [--output CSV]

# Train model
xcapit-fhe train --model TYPE --data FILE [--epochs N] [--lr RATE] [--output FILE]
# Models: linear-regression, logistic-regression, decision-tree, kmeans

# Predict
xcapit-fhe predict --model FILE --data FILE [--output CSV]

# Model info
xcapit-fhe info --model FILE

# Benchmark
xcapit-fhe benchmark [--iterations N]

# Blockchain operations
xcapit-fhe blockchain connect --network NETWORK
xcapit-fhe blockchain register --model FILE --network NETWORK
xcapit-fhe blockchain verify --model-id ID --hash HASH

# API key management
xcapit-fhe api-key create [--permissions LIST] [--rate-limit N]
xcapit-fhe api-key list
xcapit-fhe api-key revoke --key-id ID

# Version
xcapit-fhe version
```

## Performance Tips

1. **Use appropriate security level**: 128-bit is sufficient for most use cases
2. **Batch operations**: Process data in batches for better throughput
3. **Choose right optimization profile**: FAST for inference, BALANCED for training
4. **Normalize data**: Improves numerical stability with encrypted operations
5. **Limit tree depth**: Keep DecisionTree depth <= 5 for performance

## Architecture

```
sdk/
├── encryption/          # CKKS encryption (TenSEAL)
│   ├── context_manager.py
│   ├── ckks_wrapper.py
│   └── optimized_engine.py
├── models/              # FHE-compatible ML models
│   ├── base.py
│   ├── linear_regression.py
│   ├── logistic_regression.py
│   ├── decision_tree.py
│   └── kmeans.py
├── blockchain/          # Arbitrum integration
│   ├── connector.py
│   ├── registry.py
│   └── governance/
├── cli/                 # Command-line interface
├── quality/             # Data quality assessment
├── utils/               # Helpers and serialization
└── monitoring.py        # Logging and metrics
```

## API Reference

### Core Classes

| Class | Description |
|-------|-------------|
| `FHEContextManager` | Manages encryption contexts |
| `CKKSEncryptor` | Encrypt/decrypt operations |
| `SecureDataLoader` | Load and encrypt datasets |
| `LinearRegression` | Linear regression model |
| `LogisticRegression` | Binary classification |
| `DecisionTree` | Soft decision tree |
| `KMeans` | Clustering algorithm |
| `BlockchainConnector` | EVM chain connection |
| `ModelRegistryClient` | On-chain model registry |
| `GovernanceClient` | Consortium governance |

### Enums

| Enum | Values |
|------|--------|
| `SecurityLevel` | BITS_128, BITS_192, BITS_256 |
| `SigmoidApproximation` | LINEAR, DEGREE3, DEGREE5, MINIMAX |
| `SplitFunction` | SIGMOID, TANH |
| `InitMethod` | RANDOM, KMEANS_PLUS_PLUS, UNIFORM |
| `Network` | ARBITRUM_ONE, ARBITRUM_SEPOLIA, ETHEREUM_MAINNET, ETHEREUM_SEPOLIA, LOCAL |
| `OptimizationProfile` | FAST, BALANCED, PRECISE, MEMORY_EFFICIENT, THROUGHPUT |

## License

MIT License - see [LICENSE](../LICENSE) for details.

## Links

- [Main Project](../)
- [API Documentation](../docs/api/)
- [Demo Notebooks](../examples/demos/)
- [Smart Contracts](../contracts/)

# Getting Started

Complete guide for getting started with the Xcapit FHE-ML Platform.

## Prerequisites

- Python 3.9 or higher
- Node.js 18+ (for dashboard)
- Docker (optional, for containerized deployment)

## Installation

### Python SDK

```bash
# Basic installation
pip install xcapit-fhe-ml

# With API support
pip install xcapit-fhe-ml[api]

# With FHE support (includes TenSEAL)
pip install xcapit-fhe-ml tenseal

# Development installation
pip install xcapit-fhe-ml[dev]
```

### TypeScript SDK

```bash
npm install @xcapit/fhe-ml-sdk
# or
yarn add @xcapit/fhe-ml-sdk
```

### From Source

```bash
# Clone the repository
git clone https://github.com/xcapit/fhe-ml-platform.git
cd fhe-ml-platform

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev,api]"
```

## Quick Start

### 1. Initialize FHE Context

```python
from sdk import FHEContextManager, SecurityLevel

# Create encryption context
context = FHEContextManager()
context.generate_context(
    poly_modulus_degree=8192,
    security_level=SecurityLevel.TC128
)
```

### 2. Train a Model

```python
from sdk import LogisticRegression, ModelConfig
import numpy as np

# Prepare your data
X_train = np.array([[1, 2], [2, 3], [3, 4], [4, 5]])
y_train = np.array([0, 0, 1, 1])

# Create and train model
config = ModelConfig(learning_rate=0.1, n_epochs=100)
model = LogisticRegression(config=config)
model._fit_plaintext(X_train, y_train)

# Make predictions
predictions = model._predict_plaintext(X_train)
print(f"Predictions: {predictions}")
```

### 3. Encrypt and Predict

```python
from sdk import CKKSEncryptor

# Setup encryption
encryptor = CKKSEncryptor(context)

# Encrypt input data
encrypted_input = encryptor.encrypt_vector([1.0, 2.0])

# Make encrypted prediction
encrypted_result = model.predict_encrypted(encrypted_input)

# Decrypt result
result = encryptor.decrypt_vector(encrypted_result)
print(f"Decrypted result: {result}")
```

## Using the CLI

The CLI provides a convenient way to work with the platform:

```bash
# Initialize workspace
xcapit-fhe init --output ./workspace

# Encrypt a dataset
xcapit-fhe encrypt -i data.csv -o encrypted.bin -t target_column

# Train a model
xcapit-fhe train -m logistic-regression -d encrypted.bin -o model.bin

# Make predictions
xcapit-fhe predict -m model.bin -i test.bin -o predictions.npy

# Check model info
xcapit-fhe info -m model.bin
```

## Using the REST API

### Start the Server

```bash
# Development mode
uvicorn sdk.api.server:app --reload --port 8000

# Production mode with Docker
docker-compose up api
```

### API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Create a model
curl -X POST http://localhost:8000/models \
  -H "Content-Type: application/json" \
  -d '{"model_type": "logistic_regression"}'

# Train the model
curl -X POST http://localhost:8000/models/{model_id}/train \
  -H "Content-Type: application/json" \
  -d '{"X": [[1,2], [3,4]], "y": [0, 1]}'

# Make predictions
curl -X POST http://localhost:8000/models/{model_id}/predict \
  -H "Content-Type: application/json" \
  -d '{"X": [[1,2]]}'
```

See the [OpenAPI documentation](openapi.yaml) for complete API reference.

## Using TypeScript SDK

```typescript
import { createClient, ModelType } from '@xcapit/fhe-ml-sdk';

// Initialize client
const client = createClient({
  apiUrl: 'https://api.xcapit.io',
  apiKey: process.env.XCAPIT_API_KEY,
});

// Create a model
const model = await client.models.create({
  name: 'My Model',
  type: ModelType.LogisticRegression,
});

// Train the model
await client.models.train({
  modelId: model.id,
  encryptedData: trainingData,
  epochs: 100,
});

// Make predictions
const prediction = await client.predictions.predict({
  modelId: model.id,
  encryptedInput: inputData,
});

console.log('Result:', prediction.result);
```

## Running the Dashboard

```bash
cd dashboard
npm install
npm run dev
```

Access the dashboard at `http://localhost:5173`

## Docker Deployment

```bash
# Production API
docker-compose up api

# Development with hot reload
docker-compose --profile dev up

# Full stack with FHE support
docker-compose --profile fhe up

# Run tests
docker-compose --profile test up
```

## Blockchain Integration

### Deploy Smart Contracts

```bash
# Set deployer private key
export DEPLOYER_PRIVATE_KEY=0x...

# Deploy to Arbitrum testnet
python scripts/deploy_contracts.py --network arbitrum-sepolia

# Deploy to Arbitrum mainnet
python scripts/deploy_contracts.py --network arbitrum-one
```

### Register a Model on Blockchain

```python
from sdk.blockchain import BlockchainConnector

# Connect to blockchain
connector = BlockchainConnector(
    rpc_url="https://arbitrum-sepolia.infura.io/v3/YOUR_KEY",
    private_key="0x...",
    model_registry_address="0x..."
)

# Register model
tx_hash = connector.register_model(
    model_id="model_123",
    model_type="logistic_regression",
    weights_hash="0xabc123..."
)
print(f"Model registered: {tx_hash}")
```

## Consortium (Multi-Party Learning)

```python
# Create a consortium
consortium = await client.consortiums.create({
  name: "Healthcare Research Consortium",
  minVotingQuorum: 60,
  votingDuration: 86400,  # 24 hours
});

# Add members
await client.consortiums.addMember(consortium.id, memberAddress);

# Record data contribution
await client.consortiums.recordContribution({
  consortiumId: consortium.id,
  recordCount: 10000,
  featureCount: 50,
  encryptedData: contributionData,
});

# Start collaborative training
await client.consortiums.startTraining(consortium.id);
```

## Available Models

| Model | Type | Use Case |
|-------|------|----------|
| `LinearRegression` | Regression | Continuous value prediction |
| `LogisticRegression` | Classification | Binary classification |
| `DecisionTreeClassifier` | Classification | Multi-class classification |
| `DecisionTreeRegressor` | Regression | Non-linear regression |
| `KMeans` | Clustering | Data clustering |
| `MiniBatchKMeans` | Clustering | Large-scale clustering |

## Security Levels

| Level | Key Size | Use Case |
|-------|----------|----------|
| `TC128` | 128-bit | Standard security |
| `TC192` | 192-bit | Enhanced security |
| `TC256` | 256-bit | Maximum security |

## Next Steps

- Read the [Architecture Guide](guides/01-architecture.md)
- Explore [ML Models](guides/03-ml-models.md)
- Learn about [FHE Theory](theory/01-homomorphic-encryption.md)
- Review the [API Reference](openapi.yaml)
- Check the [Security Audit](SECURITY_AUDIT_REPORT.md)

## Support

- GitHub Issues: [Report bugs](https://github.com/xcapit/fhe-ml-platform/issues)
- Documentation: [Full docs](https://docs.xcapit.io)
- Demo: [Live demo](https://xcapit-privacy.vercel.app)

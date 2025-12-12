# API Reference

Complete API documentation for Xcapit FHE-ML Platform.

## REST API

The API server provides REST endpoints for privacy-preserving ML operations.

### Base URL

```
http://localhost:8000
```

### Authentication

All endpoints except `/`, `/health`, and `/model-types` require API key authentication.

**Headers:**
```
X-API-Key: your_api_key_here
```

Or query parameter:
```
?api_key=your_api_key_here
```

### Permissions

- `read`: Access model info, predictions, stats
- `write`: Create models, train, delete
- `admin`: Manage API keys

---

## Endpoints

### Health

#### GET /
Basic health check.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2024-01-15T10:30:00"
}
```

#### GET /health/detailed
Detailed health with metrics.

**Response:**
```json
{
  "status": "healthy",
  "checks": {"metrics_collecting": true},
  "uptime_seconds": 3600.5,
  "version": "0.1.0"
}
```

#### GET /metrics
System metrics.

**Response:**
```json
{
  "uptime_seconds": 3600.5,
  "counters": {"api.requests": 150},
  "gauges": {},
  "histograms": {"api.latency_ms": {"count": 100, "avg": 25.5}}
}
```

---

### Models

#### GET /model-types
List available model types.

**Response:**
```json
{
  "model_types": ["linear_regression", "logistic_regression", "decision_tree", "kmeans"]
}
```

#### POST /models
Create a new model.

**Request:**
```json
{
  "model_type": "linear_regression",
  "config": {
    "learning_rate": 0.01,
    "n_epochs": 100
  }
}
```

**Response:**
```json
{
  "model_id": "model_abc123",
  "model_type": "linear_regression",
  "status": "created",
  "created_at": "2024-01-15T10:30:00",
  "config": {"learning_rate": 0.01}
}
```

#### GET /models
List all models.

**Response:**
```json
[
  {
    "model_id": "model_abc123",
    "model_type": "linear_regression",
    "status": "trained",
    "created_at": "2024-01-15T10:30:00"
  }
]
```

#### GET /models/{model_id}
Get model details.

#### DELETE /models/{model_id}
Delete a model.

#### GET /models/{model_id}/params
Get model parameters (weights, bias).

---

### Training

#### POST /models/{model_id}/train
Train a model.

**Request:**
```json
{
  "X": [[1.0, 2.0], [3.0, 4.0]],
  "y": [0.5, 1.5]
}
```

**Response:**
```json
{
  "model_id": "model_abc123",
  "status": "trained",
  "epochs": 100,
  "final_loss": 0.01,
  "metrics": {}
}
```

---

### Prediction

#### POST /models/{model_id}/predict
Make predictions.

**Request:**
```json
{
  "X": [[1.0, 2.0], [3.0, 4.0]]
}
```

**Response:**
```json
{
  "model_id": "model_abc123",
  "predictions": [0.5, 1.5],
  "probabilities": null
}
```

---

### Statistics

#### GET /stats
Get API statistics.

**Response:**
```json
{
  "models": {"total": 5, "trained": 3, "untrained": 2},
  "predictions": {"total": 150},
  "training_runs": {"total": 10, "completed": 8, "failed": 2}
}
```

#### GET /stats/predictions
Get prediction statistics.

---

### Admin

#### POST /admin/api-keys
Create API key (requires admin).

**Request:**
```json
{
  "name": "my-app",
  "permissions": ["read", "write"],
  "rate_limit": 100
}
```

**Response:**
```json
{
  "api_key": "fheml_...",
  "key_hash": "abc123...",
  "name": "my-app"
}
```

#### GET /admin/api-keys
List API keys.

#### DELETE /admin/api-keys/{key_hash}
Revoke API key.

#### GET /auth/me
Get current auth info.

---

## CLI Reference

### Basic Commands

```bash
# Initialize FHE context
xcapit-fhe init -o context.bin

# Encrypt data
xcapit-fhe encrypt data.csv -c context.bin -o encrypted.bin

# Train model
xcapit-fhe train encrypted.bin -c context.bin -m linear -o model.bin

# Predict
xcapit-fhe predict encrypted.bin -c context.bin --model model.bin -o predictions.bin

# Decrypt results
xcapit-fhe decrypt predictions.bin -c context.bin -o results.csv
```

### API Key Management

```bash
# Create API key
xcapit-fhe api-key create --name "production" --permissions "read,write,admin"

# List keys
xcapit-fhe api-key list

# Revoke key
xcapit-fhe api-key revoke abc123...
```

### Blockchain Commands

```bash
# Test connection
xcapit-fhe blockchain connect --network arbitrum-sepolia

# Register model on-chain
xcapit-fhe blockchain register \
  --model model.bin \
  --contract 0x... \
  --private-key 0x...

# Save checkpoint
xcapit-fhe blockchain checkpoint \
  --model model.bin \
  --model-id 0x... \
  --epoch 100 \
  --contract 0x... \
  --private-key 0x...

# Verify model
xcapit-fhe blockchain verify \
  --model-id 0x... \
  --contract 0x...
```

---

## Python SDK

### Encryption

```python
from sdk.encryption import FHEContextManager, CKKSEncryptor
from sdk.utils import SecureDataLoader

# Create context
ctx_manager = FHEContextManager()
ctx_manager.create_context()

# Encrypt data
loader = SecureDataLoader()
encrypted_data = loader.encrypt(df, target_column="target")

# Save context
ctx_bytes = ctx_manager.serialize()
```

### Models

```python
from sdk.models import LinearRegression, LogisticRegression, KMeans

# Linear Regression
model = LinearRegression(learning_rate=0.01, n_epochs=100)
model.fit(encrypted_data)
predictions = model.predict(encrypted_data.X)

# Logistic Regression
model = LogisticRegression(learning_rate=0.01)
model.fit(encrypted_data)
probs = model.predict_proba(encrypted_data.X)

# K-Means Clustering
kmeans = KMeans(n_clusters=3)
kmeans.fit(X)
labels = kmeans.predict(X)
```

### Blockchain

```python
from sdk.blockchain import BlockchainConnector, ModelRegistryClient, Network

# Connect
connector = BlockchainConnector(Network.ARBITRUM_SEPOLIA)
connector.set_account(private_key)
connector.connect()

# Register model
registry = ModelRegistryClient(connector, contract_address)
model_id = registry.register_model("LinearRegression", "1.0.0")

# Save checkpoint
registry.save_checkpoint(model_id, epoch=100, weights=model.weights)
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid/missing API key |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Model/resource not found |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

# Xcapit FHE-ML Platform - API Reference

## Overview

The Xcapit FHE-ML Platform API provides RESTful endpoints for privacy-preserving machine learning using Fully Homomorphic Encryption (FHE). This document covers authentication, endpoints, request/response formats, and error handling.

**Base URL:** `https://apifhe.xcapit.com/api/v2/`

**OpenAPI Docs:** [https://apifhe.xcapit.com/api/v2/docs/](https://apifhe.xcapit.com/api/v2/docs/)

---

## Authentication

The API supports two authentication methods:

### 1. JWT Bearer Token

For user-based authentication with session management.

```bash
# Obtain tokens
curl -X POST https://apifhe.xcapit.com/api/v2/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "your_password"}'

# Response
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}

# Use access token
curl https://apifhe.xcapit.com/api/v2/consortiums/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

#### Token Refresh

```bash
curl -X POST https://apifhe.xcapit.com/api/v2/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "your_refresh_token"}'
```

#### Logout (Token Blacklist)

```bash
curl -X POST https://apifhe.xcapit.com/api/v2/auth/logout/ \
  -H "Authorization: Bearer your_access_token" \
  -H "Content-Type: application/json" \
  -d '{"refresh": "your_refresh_token"}'
```

### 2. API Key

For programmatic access and SDK integration.

```bash
curl https://apifhe.xcapit.com/api/v2/sandbox/sandboxes/ \
  -H "Authorization: ApiKey your_api_key"
```

**Demo API Key:** `demo_xcapit_2024_public_access` (read-only access)

---

## Sandbox Endpoints

The Sandbox module provides isolated testing environments for FHE experiments.

### Create Sandbox

```bash
POST /api/v2/sandbox/sandboxes/

# Request
{
  "name": "Fraud Detection Test",
  "industry": "fintech",
  "description": "Testing fraud detection model"
}

# Response
{
  "id": "sbx_abc123",
  "name": "Fraud Detection Test",
  "industry": "fintech",
  "status": "active",
  "created_at": "2025-01-24T10:00:00Z",
  "expires_at": "2025-01-31T10:00:00Z"
}
```

### List Sandboxes

```bash
GET /api/v2/sandbox/sandboxes/

# Query Parameters
?page=1&page_size=20
?industry=fintech
?status=active
```

### Get Sandbox Details

```bash
GET /api/v2/sandbox/sandboxes/{sandbox_id}/
```

### Delete Sandbox

```bash
DELETE /api/v2/sandbox/sandboxes/{sandbox_id}/
```

---

## Dataset Endpoints

### Generate Synthetic Dataset

```bash
POST /api/v2/sandbox/datasets/generate/

# Request
{
  "sandbox_id": "sbx_abc123",
  "dataset_type": "fraud_transactions",
  "record_count": 10000,
  "features": [
    {"name": "amount", "type": "float", "min": 10, "max": 10000},
    {"name": "hour", "type": "int", "min": 0, "max": 23},
    {"name": "is_international", "type": "bool", "true_ratio": 0.1}
  ]
}

# Response
{
  "id": "ds_xyz789",
  "sandbox_id": "sbx_abc123",
  "name": "fraud_transactions",
  "record_count": 10000,
  "features": [...],
  "created_at": "2025-01-24T10:05:00Z",
  "download_url": "/api/v2/sandbox/datasets/ds_xyz789/download/"
}
```

### Upload Dataset

```bash
POST /api/v2/sandbox/datasets/upload/
Content-Type: multipart/form-data

# Form fields
sandbox_id: sbx_abc123
file: @data.csv
name: my_dataset
encrypt: true
```

### List Datasets

```bash
GET /api/v2/sandbox/datasets/
?sandbox_id=sbx_abc123
```

### Download Dataset

```bash
GET /api/v2/sandbox/datasets/{dataset_id}/download/
```

---

## Experiment Endpoints

### Create Experiment

```bash
POST /api/v2/sandbox/experiments/

# Request
{
  "sandbox_id": "sbx_abc123",
  "name": "Fraud Model v1",
  "experiment_type": "classification",
  "config": {
    "algorithm": "logistic_regression",
    "target_column": "is_fraud",
    "fhe_enabled": true,
    "security_level": 128,
    "epochs": 10
  }
}

# Response
{
  "id": "exp_001",
  "sandbox_id": "sbx_abc123",
  "name": "Fraud Model v1",
  "status": "created",
  "config": {...},
  "created_at": "2025-01-24T10:10:00Z"
}
```

### Run Experiment

```bash
POST /api/v2/sandbox/experiments/{experiment_id}/run/

# Response
{
  "id": "exp_001",
  "status": "running",
  "started_at": "2025-01-24T10:11:00Z",
  "estimated_completion": "2025-01-24T10:15:00Z"
}
```

### Get Experiment Results

```bash
GET /api/v2/sandbox/experiments/{experiment_id}/

# Response
{
  "id": "exp_001",
  "status": "completed",
  "results": {
    "accuracy": 0.9245,
    "auc_roc": 0.9812,
    "precision": 0.8956,
    "recall": 0.9123,
    "f1_score": 0.9038,
    "confusion_matrix": [[1850, 50], [75, 925]],
    "feature_importance": {
      "amount": 0.25,
      "hour": 0.18,
      "is_international": 0.15
    }
  },
  "training_time_seconds": 45.2,
  "completed_at": "2025-01-24T10:15:00Z"
}
```

---

## Consortium Endpoints

### Create Consortium

```bash
POST /api/v2/consortiums/

# Request
{
  "name": "LATAM Fraud Detection Consortium",
  "industry": "fintech",
  "description": "Cross-border fraud detection collaboration",
  "governance_type": "commit_reveal",
  "quorum_percentage": 51,
  "voting_period_hours": 24
}

# Response
{
  "id": "cons_fraud_001",
  "name": "LATAM Fraud Detection Consortium",
  "status": "pending",
  "member_count": 1,
  "created_at": "2025-01-24T10:00:00Z"
}
```

### List Consortiums

```bash
GET /api/v2/consortiums/
?industry=fintech
?status=active
?page=1&page_size=20
```

### Get Consortium Details

```bash
GET /api/v2/consortiums/{consortium_id}/
```

### Invite Member

```bash
POST /api/v2/consortiums/{consortium_id}/invite/

# Request
{
  "email": "partner@company.com",
  "role": "contributor"
}
```

### Submit Contribution

```bash
POST /api/v2/consortiums/{consortium_id}/contributions/

# Request (multipart/form-data)
file: @encrypted_data.bin
encryption_proof: "0x..."
record_count: 5000
```

---

## Governance Endpoints

### Create Proposal

```bash
POST /api/v2/governance/proposals/

# Request
{
  "consortium_id": "cons_fraud_001",
  "title": "Train Fraud Detection Model v2",
  "description": "Proposal to train a new model with updated data",
  "proposal_type": "model_training",
  "config": {
    "algorithm": "random_forest",
    "parameters": {"n_estimators": 100}
  }
}
```

### Submit Vote (Commit Phase)

```bash
POST /api/v2/governance/proposals/{proposal_id}/commit/

# Request
{
  "commitment_hash": "0x3a4b5c..."
}
```

### Reveal Vote

```bash
POST /api/v2/governance/proposals/{proposal_id}/reveal/

# Request
{
  "vote": true,
  "salt": "random_salt_used_in_commitment"
}
```

### Get Proposal Status

```bash
GET /api/v2/governance/proposals/{proposal_id}/
```

---

## Data Quality Endpoints

### Assess Dataset Quality

```bash
POST /api/v2/quality/assess/

# Request
{
  "dataset_id": "ds_xyz789",
  "checks": ["completeness", "consistency", "accuracy", "timeliness"]
}

# Response
{
  "dataset_id": "ds_xyz789",
  "overall_score": 0.92,
  "scores": {
    "completeness": 0.98,
    "consistency": 0.95,
    "accuracy": 0.88,
    "timeliness": 0.87
  },
  "issues": [
    {"field": "phone", "issue": "missing_values", "count": 45},
    {"field": "date", "issue": "format_inconsistency", "count": 12}
  ]
}
```

---

## Marketplace Endpoints

### List Available Models

```bash
GET /api/v2/marketplace/models/
?industry=fintech
?model_type=classification
```

### Get Model Details

```bash
GET /api/v2/marketplace/models/{model_id}/
```

### Purchase/License Model

```bash
POST /api/v2/marketplace/models/{model_id}/license/

# Request
{
  "license_type": "monthly",
  "consortium_id": "cons_fraud_001"
}
```

---

## Error Responses

All errors follow RFC 7807 Problem Details format:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Invalid request data",
    "status": 400,
    "details": {
      "email": ["This field is required"],
      "password": ["Password must be at least 8 characters"]
    }
  }
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `validation_error` | 400 | Request validation failed |
| `authentication_error` | 401 | Invalid or expired credentials |
| `permission_denied` | 403 | Insufficient permissions |
| `not_found` | 404 | Resource not found |
| `rate_limit_exceeded` | 429 | Too many requests |
| `internal_error` | 500 | Server error |

---

## Rate Limiting

API requests are rate limited per API key:

| Tier | Requests/minute | Requests/day |
|------|-----------------|--------------|
| Free | 60 | 1,000 |
| Professional | 300 | 10,000 |
| Enterprise | 1,000 | Unlimited |

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1706097600
```

---

## Pagination

List endpoints support pagination:

```
?page=1&page_size=50
```

- Maximum `page_size`: 200
- Default `page_size`: 50

Response format:

```json
{
  "count": 150,
  "next": "https://apifhe.xcapit.com/api/v2/consortiums/?page=2",
  "previous": null,
  "results": [...]
}
```

---

## Filtering and Ordering

### Filtering

```
?status=active
?industry=fintech
?created_at__gte=2025-01-01
?search=fraud
```

### Ordering

```
?ordering=-created_at
?ordering=name
```

---

## FHE Security Levels

The API supports three security levels for FHE operations:

| Level | Bits | Use Case |
|-------|------|----------|
| 128 | 128-bit | Standard security (default) |
| 192 | 192-bit | High security |
| 256 | 256-bit | Maximum security (slower) |

Specify in experiment config:

```json
{
  "fhe_enabled": true,
  "security_level": 128
}
```

---

## Supported Industries

| Industry | Code | Description |
|----------|------|-------------|
| Financial Services | `fintech` | Banking, payments, fraud detection |
| Healthcare | `healthcare` | Patient data, clinical trials |
| Insurance | `insurance` | Claims, risk assessment |
| Government | `government` | Public services, citizen data |
| Retail | `retail` | Customer analytics, churn prediction |

---

## Supported Algorithms

| Algorithm | Type | FHE Support |
|-----------|------|-------------|
| Logistic Regression | Classification | Full |
| Linear Regression | Regression | Full |
| Decision Tree | Classification | Partial |
| Random Forest | Classification | Partial |
| K-Means | Clustering | Partial |
| Neural Network | Both | Limited |

---

## Webhooks

Configure webhooks to receive real-time notifications:

```bash
POST /api/v2/webhooks/

# Request
{
  "url": "https://your-server.com/webhook",
  "events": ["experiment.completed", "proposal.approved", "contribution.received"],
  "secret": "your_webhook_secret"
}
```

Webhook payload:

```json
{
  "event": "experiment.completed",
  "timestamp": "2025-01-24T10:15:00Z",
  "data": {
    "experiment_id": "exp_001",
    "status": "completed",
    "accuracy": 0.9245
  },
  "signature": "sha256=..."
}
```

---

## SDKs

Official SDKs are available for:

- **Python**: `pip install xcapit-fhe`
- **JavaScript**: `npm install @xcapit/fhe-sdk`

### Python Example

```python
from xcapit import XcapitClient

client = XcapitClient(api_key="your_api_key")

# Create sandbox
sandbox = client.sandbox.create(
    name="Test",
    industry="fintech"
)

# Generate dataset
dataset = client.datasets.generate(
    sandbox_id=sandbox.id,
    dataset_type="fraud_transactions",
    record_count=10000
)

# Train model
experiment = client.experiments.create(
    sandbox_id=sandbox.id,
    name="Fraud Model",
    algorithm="logistic_regression",
    target="is_fraud",
    fhe_enabled=True
)

result = experiment.run()
print(f"Accuracy: {result.accuracy}")
```

---

## Support

- **Documentation**: https://docs.xcapit.com
- **API Status**: https://status.xcapit.com
- **Support Email**: support@xcapit.com
- **GitHub Issues**: https://github.com/xcapit/fhe-ml-platform/issues

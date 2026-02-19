# API Reference

Complete reference for the Xcapit FHE-ML Platform REST API.

## Base URL

```
Production: https://api.xcapit.com/v1
Development: http://localhost:8000
```

## Authentication

All protected endpoints require an API key:

```bash
curl -H "X-API-Key: your-api-key" https://api.xcapit.com/v1/models
```

## Endpoints

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-12-13T21:28:15.547081"
}
```

---

### Models

#### List Models

```http
GET /models
```

**Headers:** `X-API-Key: required`

**Response:**
```json
{
  "models": [
    {
      "id": "model-uuid",
      "type": "linear_regression",
      "created_at": "2025-12-13T10:00:00Z",
      "status": "trained"
    }
  ]
}
```

#### Create Model

```http
POST /models
```

**Headers:** `X-API-Key: required`

**Body:**
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
  "model_id": "uuid",
  "status": "created"
}
```

#### Get Model

```http
GET /models/{model_id}
```

**Response:**
```json
{
  "id": "model-uuid",
  "type": "linear_regression",
  "config": {...},
  "metrics": {...},
  "created_at": "2025-12-13T10:00:00Z"
}
```

#### Train Model

```http
POST /models/{model_id}/train
```

**Body:**
```json
{
  "X": [[1, 2], [3, 4], [5, 6]],
  "y": [1, 2, 3],
  "encrypted": false
}
```

**Response:**
```json
{
  "status": "training_complete",
  "metrics": {
    "loss": 0.001,
    "r2_score": 0.99
  }
}
```

#### Predict

```http
POST /models/{model_id}/predict
```

**Body:**
```json
{
  "X": [[1, 2], [3, 4]],
  "encrypted": true
}
```

**Response:**
```json
{
  "predictions": [1.5, 3.5],
  "encrypted": false
}
```

---

### Encryption

#### Generate Keys

```http
POST /encryption/keys
```

**Body:**
```json
{
  "scheme": "ckks",
  "poly_modulus_degree": 8192,
  "precision": 40
}
```

**Response:**
```json
{
  "public_key_id": "pk-uuid",
  "context_id": "ctx-uuid"
}
```

#### Encrypt Data

```http
POST /encryption/encrypt
```

**Body:**
```json
{
  "data": [[1.0, 2.0], [3.0, 4.0]],
  "public_key_id": "pk-uuid"
}
```

---

### Governance

#### List Consortiums

```http
GET /governance/consortiums
```

#### Create Proposal

```http
POST /governance/proposals
```

**Body:**
```json
{
  "consortium_id": "uuid",
  "title": "Add new model type",
  "description": "Proposal to add Random Forest",
  "type": "model_addition"
}
```

#### Vote on Proposal

```http
POST /governance/proposals/{proposal_id}/vote
```

**Body:**
```json
{
  "vote": "approve",
  "weight": 1
}
```

---

### Compliance

#### Get Compliance Status

```http
GET /compliance/status
```

**Response:**
```json
{
  "frameworks": {
    "gdpr": {"compliant": true, "score": 95},
    "hipaa": {"compliant": true, "score": 92},
    "soc2": {"compliant": true, "score": 88}
  }
}
```

#### Run Compliance Check

```http
POST /compliance/check
```

**Body:**
```json
{
  "framework": "gdpr",
  "model_id": "uuid"
}
```

---

### Data Quality

#### Analyze Data

```http
POST /quality/analyze
```

**Body:**
```json
{
  "data": {...},
  "checks": ["completeness", "consistency", "validity"]
}
```

**Response:**
```json
{
  "overall_score": 0.95,
  "dimensions": {
    "completeness": 0.98,
    "consistency": 0.92,
    "validity": 0.95
  },
  "issues": []
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {}
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Invalid or missing API key |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 422 | Invalid request body |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

## Rate Limits

| Tier | Requests/min | Requests/day |
|------|--------------|--------------|
| Free | 60 | 1,000 |
| Pro | 300 | 10,000 |
| Enterprise | Unlimited | Unlimited |

## SDKs

- [Python SDK](../getting-started.md#python-sdk)
- [TypeScript SDK](../getting-started.md#typescript-sdk)

## OpenAPI Specification

Full OpenAPI 3.0 spec available at:
- `/docs` - Swagger UI
- `/openapi.json` - JSON spec
- `/redoc` - ReDoc UI

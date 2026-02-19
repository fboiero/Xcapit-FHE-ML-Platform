# JSONField Schemas Documentation

This document describes the expected structure of JSONFields used throughout the Xcapit FHE-ML Platform.

## Table of Contents
- [Governance](#governance)
  - [Proposal.data](#proposaldata)
  - [RewardDistribution.distributions](#rewarddistributiondistributions)
- [Data Quality](#data-quality)
  - [QualityRule.condition](#qualityrulecondition)
- [Sandbox](#sandbox)
  - [SyntheticDataset.features](#syntheticdatasetfeatures)
  - [Experiment.config](#experimentconfig)
- [Federated](#federated)
  - [FederatedModel.config](#federatedmodelconfig)

---

## Governance

### Proposal.data

Schema varies by `proposal_type`. All schemas enforce `additionalProperties: false`.

#### add_member
```json
{
  "company_email": "new@company.com",
  "role": "contributor",
  "message": "Welcome to the consortium!"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `company_email` | string (email) | Yes | Email of company to invite |
| `role` | enum | No | `contributor` (default), `admin`, `observer` |
| `message` | string | No | Invitation message (max 500 chars) |

#### remove_member
```json
{
  "company_id": "123e4567-e89b-12d3-a456-426614174000",
  "reason": "Inactivity for 6 months"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `company_id` | string (uuid) | Yes | ID of company to remove |
| `reason` | string | No | Reason for removal (max 500 chars) |

#### distribute_rewards
```json
{
  "amount": 1000.0,
  "currency": "ETH",
  "distribution_method": "contribution_weighted"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `amount` | number | Yes | Total amount (>= 0) |
| `currency` | enum | Yes | `ETH`, `USDC`, `DAI` |
| `distribution_method` | enum | No | `equal`, `contribution_weighted` (default), `custom` |
| `custom_weights` | object | No | Company ID to weight mapping (for `custom` method) |

#### start_training
```json
{
  "model_type": "logistic_regression",
  "epochs": 100,
  "learning_rate": 0.01,
  "batch_size": 64
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model_type` | enum | No | `logistic_regression`, `linear_regression`, `decision_tree`, `kmeans` |
| `epochs` | integer | No | 1-1000 (default: 10) |
| `learning_rate` | number | No | 0.0001-1.0 (default: 0.01) |
| `batch_size` | integer | No | 1-10000 (default: 32) |

#### update_config
```json
{
  "config_key": "voting_duration",
  "config_value": 604800,
  "reason": "Extended for complex proposals"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `config_key` | enum | Yes | `voting_duration`, `min_voting_quorum`, `model_config`, `privacy_budget` |
| `config_value` | any | Yes | New value |
| `reason` | string | No | Change reason (max 500 chars) |

#### dissolve
```json
{
  "reason": "Project completed, all goals achieved",
  "distribute_remaining_funds": true
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `reason` | string | Yes | Dissolution reason (10-1000 chars) |
| `distribute_remaining_funds` | boolean | No | Default: true |

---

### RewardDistribution.distributions

Array of distribution records:

```json
[
  {
    "company_id": "123e4567-e89b-12d3-a456-426614174000",
    "amount": 500.0,
    "contribution_weight": 0.5,
    "tx_hash": "0x1234567890abcdef..."
  }
]
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `company_id` | string (uuid) | Yes | Receiving company ID |
| `amount` | number | Yes | Amount distributed (>= 0) |
| `contribution_weight` | number | No | Weight used (0-1) |
| `tx_hash` | string | No | Blockchain transaction hash |

---

## Data Quality

### QualityRule.condition

Defines when a quality rule is triggered:

#### Threshold operators
```json
{
  "operator": ">=",
  "value": 80
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `operator` | enum | Yes | `>=`, `<=`, `>`, `<`, `==`, `!=` |
| `value` | number | Yes | Comparison value |

#### Range operator
```json
{
  "operator": "between",
  "min_value": 0,
  "max_value": 100
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `operator` | enum | Yes | `between` |
| `min_value` | number | Yes | Range minimum |
| `max_value` | number | Yes | Range maximum |

#### List operators
```json
{
  "operator": "in",
  "value": [1, 2, 3]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `operator` | enum | Yes | `in`, `not_in` |
| `value` | array | Yes | List of valid values |

---

## Sandbox

### SyntheticDataset.features

Array of feature definitions:

```json
[
  {"name": "amount", "type": "float", "min": 0, "max": 10000},
  {"name": "category", "type": "category", "values": ["A", "B", "C"]},
  {"name": "is_fraud", "type": "bool", "true_ratio": 0.02}
]
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Feature name |
| `type` | enum | Yes | `float`, `int`, `category`, `bool` |
| `min` | number | No | Minimum value (for numeric types) |
| `max` | number | No | Maximum value (for numeric types) |
| `values` | array | No | Possible values (for category type) |
| `true_ratio` | number | No | Probability of true (for bool type) |

### Experiment.config

Configuration varies by `experiment_type`:

#### Training
```json
{
  "epochs": 100,
  "learning_rate": 0.01,
  "batch_size": 64,
  "validation_split": 0.2
}
```

#### Clustering
```json
{
  "n_clusters": 5,
  "n_samples": 1000,
  "algorithm": "kmeans"
}
```

#### Encryption Benchmark
```json
{
  "security_level": 128,
  "operations": ["add", "multiply"]
}
```

---

## Federated

### FederatedModel.config

Training and deployment configuration:

```json
{
  "learning_rate": 0.01,
  "batch_size": 32,
  "rounds": 10,
  "min_participants": 3,
  "encryption": {
    "scheme": "CKKS",
    "security_level": 128
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `learning_rate` | number | No | Default: 0.01 |
| `batch_size` | integer | No | Default: 32 |
| `rounds` | integer | No | Federated rounds (default: 10) |
| `min_participants` | integer | No | Minimum nodes required |
| `encryption` | object | No | FHE configuration |

---

## Validation

All schemas are validated at the serializer level using `JSONSchemaValidator`:

```python
from apps.core.validators import JSONSchemaValidator, PROPOSAL_DATA_SCHEMAS

class ProposalSerializer(serializers.ModelSerializer):
    data = serializers.JSONField(
        validators=[JSONSchemaValidator(PROPOSAL_DATA_SCHEMAS["add_member"])]
    )
```

For proposal-type-specific validation, use `ProposalDataField`:

```python
from apps.core.validators.json_schemas import ProposalDataField

class ProposalSerializer(serializers.ModelSerializer):
    data = ProposalDataField()  # Auto-validates based on proposal_type
```

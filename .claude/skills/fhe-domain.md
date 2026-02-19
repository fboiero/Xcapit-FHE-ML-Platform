# FHE Domain Knowledge

## CKKS Scheme Overview

The platform uses TenSEAL's CKKS (Cheon-Kim-Kim-Song) scheme for approximate arithmetic on encrypted data. CKKS enables:
- Addition and multiplication on ciphertexts
- Approximate results (suitable for ML, not exact arithmetic)
- SIMD-style batching (encrypt multiple values in one ciphertext)

## Security Levels

| Level | Config Key | Use Case |
|-------|-----------|----------|
| 128-bit | `FHE_SECURITY_LEVEL=128` | Default, general use |
| 192-bit | `FHE_SECURITY_LEVEL=192` | Financial data |
| 256-bit | `FHE_SECURITY_LEVEL=256` | Maximum security (government, military) |

## Supported ML Models

- **LinearRegression** — Encrypted linear regression
- **LogisticRegression** — Encrypted logistic regression (sigmoid approximation)
- **DecisionTree** — Encrypted decision tree (polynomial approximation)
- **KMeans** — Encrypted K-means clustering

## Data Flow

```
Client                          Server
  │                                │
  ├─── Generate keys ──────────►  │
  │    (public + secret)          │
  │                                │
  ├─── Encrypt data ───────────►  │  (only public key sent)
  │    (with public key)          │
  │                                │
  │                                ├─── Train/Predict on ciphertext
  │                                │    (never sees plaintext)
  │                                │
  │  ◄─── Return encrypted ────── ├
  │       results                  │
  │                                │
  ├─── Decrypt with secret key    │
  │    (client-side only)         │
```

## SDK Structure (`sdk/`)

| Module | Purpose |
|--------|---------|
| `encryption/` | TenSEAL CKKS key generation, encrypt, decrypt |
| `models/` | FHE-aware ML model implementations |
| `blockchain/` | Web3/Arbitrum contract interaction |
| `blockchain/governance/` | DAO governance operations |
| `cli/` | `xcapit-fhe` command-line tool |
| `quality/` | Data quality score calculators |
| `utils/` | Common utilities |
| `monitoring.py` | Metrics collection |

SDK version: 0.2.0 (pure library, no API server)

## Consortium FHE Workflow

1. **Create consortium** — Company creates consortium with ML config
2. **Members join** — Companies join and submit encrypted data contributions
3. **Verify contributions** — ContributionProof records verified (ContributionService)
4. **Train on encrypted data** — FHETrainingService aggregates and trains
5. **Register on blockchain** — TrainingResult registered via Celery task

## Key Django Integration Points

### FHETrainingService (`apps/consortiums/services/training.py`)

```python
# Starts from verified consortium contributions
# Creates TrainingResult records
# Uses @transaction.atomic
# Integrates with Celery for async training
```

### Related Models

- `Consortium` — Training configuration and member management
- `ConsortiumMember` — Company membership with role (owner/admin/member)
- `ContributionProof` — Encrypted data contribution verification
- `TrainingResult` — Training outcome with metrics
- `MLModel` + `ModelVersion` — Trained model artifacts

### Celery Tasks (`apps/consortiums/tasks.py`)

- `register_contribution_blockchain` — Register contribution on-chain
- `register_training_result_blockchain` — Register training result on-chain
- Queue: `blockchain`

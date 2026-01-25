# SDK Tutorials

Step-by-step guides for common use cases with the Xcapit FHE-ML SDK.

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Credit Risk Model (Fintech)](#2-credit-risk-model-fintech)
3. [Patient Risk Prediction (Healthcare)](#3-patient-risk-prediction-healthcare)
4. [Customer Segmentation (Retail)](#4-customer-segmentation-retail)
5. [Fraud Detection (Insurance)](#5-fraud-detection-insurance)
6. [Multi-Party Consortium](#6-multi-party-consortium)

---

## 1. Getting Started

### Installation

```bash
cd Xcapit-FHE-ML-Platform
pip install -e .
```

### Verify Installation

```python
from sdk import __version__, FHEContextManager, SecurityLevel

print(f"SDK Version: {__version__}")

# Test encryption context
ctx = FHEContextManager(security_level=SecurityLevel.BITS_128)
context = ctx.create_context()
print("FHE Context created successfully!")
```

### Your First Encrypted ML Model

```python
import numpy as np
from sdk import LinearRegression, ModelConfig

# Generate sample data
np.random.seed(42)
X = np.random.randn(100, 5)
y = X @ np.array([1, 2, 3, 4, 5]) + np.random.randn(100) * 0.1

# Train model
model = LinearRegression()
config = ModelConfig(learning_rate=0.01, epochs=50)
model.fit(X, y, config=config)

# Evaluate
predictions = model.predict(X)
mse = np.mean((predictions - y) ** 2)
print(f"MSE: {mse:.4f}")
```

---

## 2. Credit Risk Model (Fintech)

Predict loan default risk using encrypted financial data.

### Scenario

A bank wants to predict loan defaults without exposing customer financial data.

### Data Preparation

```python
import pandas as pd
import numpy as np
from sdk import SecureDataLoader, LogisticRegression, SigmoidApproximation

# Simulated financial data
data = {
    'income': np.random.normal(50000, 20000, 1000),
    'debt_ratio': np.random.uniform(0.1, 0.8, 1000),
    'credit_score': np.random.normal(700, 50, 1000),
    'employment_years': np.random.exponential(5, 1000),
    'num_accounts': np.random.poisson(3, 1000),
}
df = pd.DataFrame(data)

# Generate labels (default = 1)
risk_score = (
    -0.00002 * df['income'] +
    2 * df['debt_ratio'] +
    -0.01 * df['credit_score'] +
    -0.1 * df['employment_years']
)
df['default'] = (risk_score > np.median(risk_score)).astype(int)
```

### Encrypt and Train

```python
# Load and encrypt
loader = SecureDataLoader()
dataset = loader.load_and_encrypt(
    df,
    target_column='default',
    normalize=True
)

# Train logistic regression
model = LogisticRegression(
    sigmoid_approximation=SigmoidApproximation.DEGREE3
)
model.fit(dataset.X, dataset.y)

# Predict on encrypted data
predictions = model.predict(dataset.X)
probabilities = model.predict_proba(dataset.X)
```

### Evaluate

```python
from sklearn.metrics import accuracy_score, roc_auc_score

y_true = df['default'].values
accuracy = accuracy_score(y_true, predictions)
auc = roc_auc_score(y_true, probabilities)

print(f"Accuracy: {accuracy:.2%}")
print(f"AUC-ROC: {auc:.4f}")
```

### Register on Blockchain

```python
from sdk import BlockchainConnector, ModelRegistryClient, Network
from sdk.utils import compute_weights_hash

# Connect to Arbitrum testnet
connector = BlockchainConnector(
    network=Network.ARBITRUM_SEPOLIA,
    private_key="your-private-key"
)

# Register model
registry = ModelRegistryClient(connector)
weights_hash = compute_weights_hash(model)

tx_hash = registry.register_model(
    model_id="credit-risk-v1",
    model_hash=weights_hash,
    metadata={
        "accuracy": accuracy,
        "auc": auc,
        "features": list(df.columns[:-1]),
        "version": "1.0.0"
    }
)
print(f"Model registered: {tx_hash}")
```

---

## 3. Patient Risk Prediction (Healthcare)

Predict patient readmission risk while complying with HIPAA.

### Scenario

A hospital consortium wants to build a risk model without sharing PHI (Protected Health Information).

### Data Preparation

```python
import numpy as np
import pandas as pd

# Simulated patient data (de-identified)
np.random.seed(42)
n_patients = 500

data = {
    'age': np.random.normal(65, 15, n_patients).clip(18, 100),
    'bmi': np.random.normal(28, 5, n_patients).clip(15, 50),
    'blood_pressure_systolic': np.random.normal(130, 20, n_patients),
    'blood_glucose': np.random.normal(100, 30, n_patients),
    'cholesterol': np.random.normal(200, 40, n_patients),
    'previous_admissions': np.random.poisson(1, n_patients),
    'medication_count': np.random.poisson(4, n_patients),
}
df = pd.DataFrame(data)

# Risk factors
risk = (
    0.03 * df['age'] +
    0.05 * df['bmi'] +
    0.01 * df['blood_pressure_systolic'] +
    0.02 * df['blood_glucose'] +
    0.5 * df['previous_admissions']
)
df['readmission'] = (risk > np.percentile(risk, 70)).astype(int)
```

### FHE Training Pipeline

```python
from sdk import (
    SecureDataLoader,
    LogisticRegression,
    SigmoidApproximation,
    ModelConfig
)

# Encrypt patient data
loader = SecureDataLoader()
dataset = loader.load_and_encrypt(
    df,
    target_column='readmission',
    normalize=True
)

# Configure model
config = ModelConfig(
    learning_rate=0.01,
    epochs=100,
    batch_size=32,
    early_stopping=True,
    patience=10
)

# Train on encrypted data
model = LogisticRegression(
    sigmoid_approximation=SigmoidApproximation.DEGREE5  # Higher accuracy for medical
)
history = model.fit(dataset.X, dataset.y, config=config)

print(f"Training completed in {len(history.losses)} epochs")
print(f"Final loss: {history.losses[-1]:.4f}")
```

### Compliance Logging

```python
from sdk.monitoring import get_logger, MetricsCollector

logger = get_logger("healthcare.compliance")
metrics = MetricsCollector()

# Log training event (HIPAA audit trail)
logger.info(
    "Model training completed",
    extra={
        "event_type": "model_training",
        "data_encrypted": True,
        "n_records": len(df),
        "model_type": "logistic_regression",
        "hipaa_compliant": True
    }
)

# Record metrics
metrics.increment("models.trained")
metrics.gauge("model.accuracy", accuracy)
```

---

## 4. Customer Segmentation (Retail)

Segment customers using encrypted purchase data with KMeans.

### Scenario

Multiple retailers want to collaborate on customer segmentation without sharing individual purchase histories.

### RFM Analysis

```python
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Simulated RFM data
np.random.seed(42)
n_customers = 1000

data = {
    'recency': np.random.exponential(30, n_customers),  # Days since last purchase
    'frequency': np.random.poisson(5, n_customers) + 1,  # Purchase count
    'monetary': np.random.lognormal(4, 1, n_customers),  # Total spend
}
df = pd.DataFrame(data)
```

### Encrypted Clustering

```python
from sdk import KMeans, KMeansConfig, InitMethod, SecureDataLoader

# Encrypt RFM data
loader = SecureDataLoader()
dataset = loader.load_and_encrypt(df, normalize=True)

# Configure KMeans
config = KMeansConfig(
    n_clusters=4,
    init_method=InitMethod.KMEANS_PLUS_PLUS,
    max_iterations=50,
    temperature=0.5  # Sharper cluster boundaries
)

# Fit on encrypted data
model = KMeans(config=config)
model.fit(dataset.X)

# Get cluster assignments
labels = model.predict(dataset.X)
centroids = model.cluster_centers_
```

### Interpret Segments

```python
# Add labels to original data
df['segment'] = labels

# Analyze segments
segment_profiles = df.groupby('segment').agg({
    'recency': 'mean',
    'frequency': 'mean',
    'monetary': 'mean'
}).round(2)

segment_names = {
    0: "Champions",      # Low recency, high frequency, high monetary
    1: "Loyal",          # Medium recency, high frequency
    2: "At Risk",        # High recency, medium frequency
    3: "Lost"            # High recency, low frequency
}

print("Customer Segments:")
print(segment_profiles)
```

---

## 5. Fraud Detection (Insurance)

Detect fraudulent claims using encrypted claim data.

### Scenario

Insurance companies want to share fraud patterns without exposing claim details.

### Data Preparation

```python
import numpy as np
import pandas as pd

np.random.seed(42)
n_claims = 2000

# Normal claims
normal_claims = {
    'claim_amount': np.random.lognormal(8, 0.5, n_claims),
    'days_to_claim': np.random.exponential(30, n_claims),
    'previous_claims': np.random.poisson(1, n_claims),
    'policy_age_months': np.random.exponential(24, n_claims),
    'claim_description_length': np.random.normal(200, 50, n_claims),
}
df = pd.DataFrame(normal_claims)

# Inject fraud patterns (5% fraud rate)
n_fraud = int(n_claims * 0.05)
fraud_idx = np.random.choice(n_claims, n_fraud, replace=False)
df.loc[fraud_idx, 'claim_amount'] *= 3  # Inflated amounts
df.loc[fraud_idx, 'days_to_claim'] = np.random.uniform(1, 5, n_fraud)  # Quick claims
df.loc[fraud_idx, 'previous_claims'] += 3  # Multiple claims

df['is_fraud'] = 0
df.loc[fraud_idx, 'is_fraud'] = 1
```

### Train Fraud Detector

```python
from sdk import (
    SecureDataLoader,
    DecisionTreeClassifier,
    TreeConfig,
    SplitFunction
)

# Encrypt claim data
loader = SecureDataLoader()
dataset = loader.load_and_encrypt(
    df,
    target_column='is_fraud',
    normalize=True
)

# Decision tree for interpretability
config = TreeConfig(
    max_depth=4,
    split_function=SplitFunction.SIGMOID,
    temperature=0.3
)

model = DecisionTreeClassifier(config=config)
model.fit(dataset.X, dataset.y)

# Predict
predictions = model.predict(dataset.X)
```

### Evaluate and Threshold

```python
from sklearn.metrics import classification_report, confusion_matrix

print(classification_report(df['is_fraud'], predictions))
print("\nConfusion Matrix:")
print(confusion_matrix(df['is_fraud'], predictions))
```

---

## 6. Multi-Party Consortium

Set up a federated learning consortium with governance.

### Create Consortium

```python
from sdk import BlockchainConnector, Network
from sdk.blockchain import GovernanceClient

# Connect as consortium admin
connector = BlockchainConnector(
    network=Network.ARBITRUM_SEPOLIA,
    private_key="admin-private-key"
)

governance = GovernanceClient(connector)

# Create consortium
consortium_id = governance.create_consortium(
    name="Healthcare ML Consortium",
    description="Privacy-preserving patient risk models",
    voting_duration=7 * 24 * 3600,  # 7 days
    min_quorum=0.51  # 51% required
)
print(f"Consortium created: {consortium_id}")
```

### Add Members

```python
# Add hospital members
hospitals = [
    ("0xHospitalA...", "Hospital A"),
    ("0xHospitalB...", "Hospital B"),
    ("0xHospitalC...", "Hospital C"),
]

for address, name in hospitals:
    governance.add_member(
        consortium_id,
        member_address=address,
        role="contributor",
        metadata={"name": name}
    )
    print(f"Added {name}")
```

### Submit Training Proposal

```python
# Hospital A proposes training
proposal_id = governance.submit_proposal(
    consortium_id,
    proposal_type="start_training",
    data={
        "model_type": "logistic_regression",
        "epochs": 100,
        "learning_rate": 0.01,
        "description": "Train readmission risk model v2"
    }
)
print(f"Proposal submitted: {proposal_id}")
```

### Voting Process

```python
# Each member votes
# Hospital A
governance.vote(consortium_id, proposal_id, vote=True)

# Hospital B (different connection)
connector_b = BlockchainConnector(
    network=Network.ARBITRUM_SEPOLIA,
    private_key="hospital-b-private-key"
)
governance_b = GovernanceClient(connector_b)
governance_b.vote(consortium_id, proposal_id, vote=True)

# Check proposal status
proposal = governance.get_proposal(consortium_id, proposal_id)
print(f"Status: {proposal.status}")
print(f"Votes for: {proposal.votes_for}")
print(f"Votes against: {proposal.votes_against}")
```

### Execute Approved Proposal

```python
# After voting period ends and quorum reached
if proposal.status == "approved":
    governance.execute_proposal(consortium_id, proposal_id)
    print("Training initiated!")
```

### Record Data Contributions

```python
# Each hospital contributes encrypted data
from sdk.utils import compute_weights_hash

# Hospital A's contribution
data_hash = compute_weights_hash(hospital_a_encrypted_data)
governance.record_contribution(
    consortium_id,
    data_hash=data_hash,
    record_count=10000,
    metadata={"source": "Hospital A EMR"}
)
```

---

## Best Practices

### 1. Data Preparation

- **Normalize data**: FHE works better with values in [-1, 1] range
- **Handle missing values**: Fill or remove before encryption
- **Feature selection**: Fewer features = faster encrypted operations

### 2. Model Selection

| Task | Recommended Model | Notes |
|------|------------------|-------|
| Regression | LinearRegression | Fast, accurate |
| Binary classification | LogisticRegression (DEGREE3) | Good balance |
| Multi-class | DecisionTree | Soft splits handle multiple classes |
| Clustering | KMeans | Use KMEANS_PLUS_PLUS init |

### 3. Performance

- Start with `SecurityLevel.BITS_128` (fastest)
- Use `OptimizationProfile.FAST` for inference
- Batch process large datasets
- Limit tree depth to 5 or less

### 4. Security

- Never log decrypted data
- Rotate encryption keys periodically
- Use blockchain for audit trails
- Validate data before encryption

---

## Next Steps

- [API Reference](../api/README.md)
- [Architecture Guide](ARCHITECTURE.md)
- [Demo Notebooks](../../examples/demos/)
- [Troubleshooting](TROUBLESHOOTING.md)

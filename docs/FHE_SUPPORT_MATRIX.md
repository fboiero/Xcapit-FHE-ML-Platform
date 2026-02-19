# FHE Support Matrix

> **Last updated:** February 2026

This document describes the actual Fully Homomorphic Encryption (FHE) capabilities of each model in the Xcapit FHE-ML SDK. It reflects the current implementation, not aspirational features.

---

## Support Levels

| Level | Code | Description |
|-------|------|-------------|
| **Full** | `FHELevel.FULL` | Inference computed entirely on encrypted data using CKKS operations. Server never sees plaintext features during prediction. |
| **Partial** | `FHELevel.PARTIAL` | Most inference on encrypted data, but some operations (e.g., sigmoid) require temporary decryption or polynomial approximation with reduced accuracy. |
| **Transport** | `FHELevel.TRANSPORT` | Accepts encrypted input but decrypts internally for computation. Provides data-in-transit and at-rest encryption, **not** computation encryption. The server sees plaintext during inference. |
| **None** | `FHELevel.NONE` | All computation on plaintext. No encrypted inference path. Raises `ValueError` if encrypted data is passed. |

---

## Model Matrix

| Model | Training | Inference | FHE Level | Notes |
|-------|----------|-----------|-----------|-------|
| `LinearRegression` | CKKS gradient descent | CKKS matrix multiply | **Full** | Weights stored in plaintext; features remain encrypted |
| `LogisticRegression` | Decrypts X,y for gradient | Polynomial sigmoid approx | **Partial** | Sigmoid approximation (degree 3/5/minimax) limits accuracy outside [-5, 5] range |
| `DecisionTree` | Plaintext | Decrypts input | Transport | Soft splits defined but inference decrypts (see `decision_tree.py`) |
| `DecisionTreeClassifier` | Plaintext | Decrypts input | Transport | Inherits from DecisionTree |
| `DecisionTreeRegressor` | Plaintext | Decrypts input | Transport | Inherits from DecisionTree |
| `RandomForest` | Plaintext | Decrypts input | Transport | Each tree decrypts; bagging on plaintext predictions |
| `RandomForestClassifier` | Plaintext | Decrypts input | Transport | Inherits from RandomForest |
| `RandomForestRegressor` | Plaintext | Decrypts input | Transport | Inherits from RandomForest |
| `GradientBoosting` | Plaintext | Decrypts input | Transport | Sequential trees trained on plaintext residuals |
| `GradientBoostingClassifier` | Plaintext | Decrypts input | Transport | Inherits from GradientBoosting |
| `GradientBoostingRegressor` | Plaintext | Decrypts input | Transport | Inherits from GradientBoosting |
| `NeuralNetwork` | Plaintext | Decrypts input | Transport | Polynomial activations defined but inference decrypts |
| `NeuralNetworkClassifier` | Plaintext | Decrypts input | Transport | Inherits from NeuralNetwork |
| `NeuralNetworkRegressor` | Plaintext | Decrypts input | Transport | Inherits from NeuralNetwork |
| `SVM` | Plaintext | Decrypts input | Transport | Polynomial kernel FHE-compatible but inference decrypts |
| `KMeans` | Plaintext | Decrypts input | Transport | Soft assignments defined but computed on plaintext |
| `MiniBatchKMeans` | Plaintext | Decrypts input | Transport | Inherits from KMeans |
| `PCA` | Plaintext | Rejects encrypted | None | `ValueError` if encrypted data passed |
| `GaussianNaiveBayes` | Plaintext | Rejects encrypted | None | `ValueError` if encrypted data passed |
| `VotingClassifier` | Plaintext | Plaintext | None | Depends on base estimators |
| `IsolationForest` | Plaintext | Plaintext | None | Statistical method, no FHE path |
| `ARIMA` | Plaintext | Plaintext | None | Time series, no FHE path |
| `ExponentialSmoothing` | Plaintext | Plaintext | None | Time series, no FHE path |
| `MLPClassifier` | Plaintext | Plaintext | None | Deep learning, no FHE path |

---

## What "Transport" Means

Models at the **Transport** level follow this pattern:

1. Accept encrypted input (`EncryptedMatrix` or `EncryptedVector`)
2. **Decrypt the input server-side** for computation
3. Compute predictions in plaintext
4. Re-encrypt the result before returning

This provides:
- **Data-at-rest encryption** (data stored encrypted)
- **Data-in-transit encryption** (data sent/received encrypted)

This does **not** provide:
- **Computation encryption** (the server sees plaintext during inference)

The privacy guarantee depends on trusting the server not to log or exfiltrate the decrypted data.

---

## What "Full" and "Partial" Mean

**Full FHE (LinearRegression):** The server performs matrix multiplication and addition entirely on CKKS ciphertexts. The server never sees plaintext features. The model weights are in plaintext (they are the model's learned parameters, not user data).

**Partial FHE (LogisticRegression):** Most operations are on encrypted data, but the sigmoid function cannot be computed exactly in FHE. Polynomial approximations (degree 3, 5, or minimax) are used. These approximations have reduced accuracy outside the [-5, 5] range. During training, the implementation decrypts X and y for gradient computation.

---

## Programmatic Access

Each model exposes its FHE level as a class attribute:

```python
from sdk.models.linear_regression import LinearRegression
from sdk.models.decision_tree import DecisionTree
from sdk.models.base import FHELevel

assert LinearRegression.fhe_level == FHELevel.FULL
assert DecisionTree.fhe_level == FHELevel.TRANSPORT
```

---

## Roadmap for Improvement

True FHE inference for tree-based models and neural networks requires:

- **Tree models:** Polynomial approximation of comparison operators. Replace hard thresholds `x < t` with smooth sigmoid functions evaluated homomorphically. This is an active research area (oblivious decision trees, TFHE-based comparisons).
- **Neural networks:** Low-degree polynomial activation functions with controlled multiplicative depth. Current TenSEAL/CKKS supports this in theory but the implementation needs to avoid decryption.
- **KMeans:** Replace argmin with FHE-compatible soft assignment using polynomial softmax approximation.

The FHE library evaluation (TenSEAL vs Concrete ML vs OpenFHE) planned for Q1 2026 will determine which improvements are feasible with each library.

---

## Related Documents

- [SDK Models Documentation](guides/03-ml-models.md)
- [ROADMAP.md](../ROADMAP.md) — Q1 2026 includes FHE library evaluation
- [Encryption Theory](theory/) — CKKS scheme details

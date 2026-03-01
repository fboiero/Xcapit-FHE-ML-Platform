# SDK Development

## Package Info

- **Name**: `xcapit-fhe-ml` (import as `sdk`)
- **Version**: `0.7.0`
- **Python**: `>=3.9` (targets 3.9–3.12)
- **License**: AGPL-3.0-or-later
- **CLI**: `xcapit-fhe` entry point

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `tenseal` | `>=0.3.14` | CKKS homomorphic encryption |
| `concrete-ml` | `>=1.5.0` | FHE ML operations |
| `numpy` | `>=1.24.0` | Numerical computation |
| `pandas` | `>=2.0.0` | Data handling |
| `scikit-learn` | `>=1.3.0` | ML algorithms base |
| `web3` | `>=6.0.0` | Blockchain interaction |
| `eth-account` | `>=0.10.0` | Ethereum accounts |

Optional: `dev` (pytest, black, ruff, mypy), `api` (fastapi, uvicorn), `deploy` (py-solc-x).

## Structure

```
sdk/
├── __init__.py              # v0.7.0, exports 200+ symbols
├── core.py                  # Lite imports for demos
├── encryption/              # FHE layer
│   ├── context_manager.py   # FHEContextManager, CKKSParameters, SecurityLevel
│   ├── ckks_wrapper.py      # CKKSEncryptor, EncryptedVector, EncryptedMatrix
│   └── optimized_engine.py  # OptimizedFHEEngine, ContextPool
├── models/                  # 20 model implementations
│   ├── base.py              # BaseFHEModel (ABC), FHEModel (factory)
│   ├── linear_regression.py, logistic_regression.py, decision_tree.py
│   ├── random_forest.py, neural_network.py, gradient_boosting.py
│   ├── kmeans.py, svm.py, naive_bayes.py, pca.py, ensemble.py
│   ├── anomaly_detection.py, time_series.py, regularization.py
│   ├── clustering.py, deep_learning.py, calibration.py, multioutput.py
│   └── feature_selection.py
├── blockchain/              # Arbitrum integration
│   ├── connector.py         # BlockchainConnector, Network
│   ├── registry.py          # ModelRegistryClient
│   └── governance/          # GovernanceClient, ConsortiumInfo
├── evaluation/              # Metrics, cross-validation, SHAP, hyperparameter tuning
├── preprocessing/           # Scalers, encoders, imputers, transformers
├── persistence/             # save_model/load_model (JSON, pickle, gzip)
├── quality/                 # DataQualityCalculator, DataProfile, QualityScore
├── utils/                   # SecureDataLoader, validators, serialization
├── pipeline.py              # Pipeline, FeatureUnion, ColumnTransformer
├── cli/                     # CLI commands (encryption, training, blockchain)
└── tests/                   # ~620 tests
```

## Key Patterns

### BaseFHEModel

All models extend `BaseFHEModel` with `fit()` + `predict()`:

```python
from sdk.models.base import BaseFHEModel, FHELevel, ModelConfig, ModelState

class MyModel(BaseFHEModel):
    fhe_level = FHELevel.FULL  # FULL | PARTIAL | TRANSPORT | NONE

    def fit(self, X, y=None) -> "MyModel":
        self._state = ModelState.TRAINING
        # ... training logic
        self._state = ModelState.TRAINED
        return self

    def predict(self, X):
        ...
```

### FHEModel Factory

```python
model = FHEModel.LinearRegression(learning_rate=0.1)
model = FHEModel.DecisionTree(max_depth=4)
```

### Encryption

```python
from sdk.encryption import FHEContextManager, CKKSEncryptor, SecurityLevel

manager = FHEContextManager()
context = manager.create_context(CKKSParameters(
    poly_modulus_degree=8192, security_level=SecurityLevel.TC128,
))
encryptor = CKKSEncryptor(manager)
encrypted = encryptor.encrypt(data)
```

### Blockchain

```python
from sdk.blockchain import BlockchainConnector, Network, ModelRegistryClient

connector = BlockchainConnector(network=Network.ARBITRUM_SEPOLIA, private_key="0x...")
registry = ModelRegistryClient(connector, contract_address="0x...")
registry.register_model(model_hash, version="1.0.0")
```

### Data Quality

```python
from sdk.quality import DataQualityCalculator, DataProfile

calculator = DataQualityCalculator()
score = calculator.assess_quality(DataProfile(record_count=1000, feature_count=10))
# score.overall, score.completeness, score.consistency, score.uniqueness
```

## CLI Commands

| Command | Purpose |
|---------|---------|
| `xcapit-fhe init` | Initialize FHE context and keys |
| `xcapit-fhe encrypt` | Encrypt CSV data |
| `xcapit-fhe decrypt` | Decrypt data back |
| `xcapit-fhe train` | Train model on encrypted data |
| `xcapit-fhe predict` | Run predictions |
| `xcapit-fhe benchmark` | FHE performance benchmarks |
| `xcapit-fhe blockchain connect/register/verify` | Blockchain operations |
| `xcapit-fhe api-key create/list/revoke` | API key management |

## Test Patterns

```bash
pytest sdk/tests/ -v --tb=short
pytest --cov=sdk --cov-fail-under=90
```

- Classes per component: `TestModelConfig`, `TestModel`, `TestEdgeCases`
- No FHE in tests (plaintext arrays for speed)
- Fixtures: `make_classification`/`make_regression` from sklearn
- Most test files currently skipped in `conftest.py` (need import fixes)

## Coding Rules

- Type hints required on all new code
- Dataclasses for configs, Enums for type-safe constants
- scikit-learn-compatible API (`.fit()`, `.predict()`, `.score()`, `.get_params()`)
- Private attributes: `self._weights`, `self._state`
- Google-style docstrings
- All `__init__.py` must have `__all__` lists
- Linting: ruff (line-length 100), black (line-length 88)

## Known Issues

- Most SDK test files skipped (broken imports, need updating)
- Duplicate directories with spaces exist (artifacts)
- `fhe-domain.md` references SDK v0.2.0 but actual is v0.7.0

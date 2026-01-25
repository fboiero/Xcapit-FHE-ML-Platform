# SDK Troubleshooting Guide

Common issues and solutions when using the Xcapit FHE-ML SDK.

## Installation Issues

### TenSEAL Installation Fails

**Error:**
```
ERROR: Failed building wheel for tenseal
```

**Solution:**
```bash
# Install build dependencies
pip install cmake pybind11

# On macOS
brew install cmake

# On Ubuntu
sudo apt-get install cmake libseal-dev

# Then retry
pip install tenseal
```

### Import Error: No module named 'sdk'

**Error:**
```python
ModuleNotFoundError: No module named 'sdk'
```

**Solution:**
```bash
# Install in development mode from project root
cd Xcapit-FHE-ML-Platform
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/Xcapit-FHE-ML-Platform"
```

---

## Encryption Issues

### Context Creation Fails

**Error:**
```
RuntimeError: SEAL context is not valid
```

**Causes:**
- Invalid CKKS parameters
- Incompatible polynomial degree

**Solution:**
```python
from sdk import FHEContextManager, SecurityLevel

# Use predefined security levels instead of custom parameters
ctx_manager = FHEContextManager(security_level=SecurityLevel.BITS_128)
context = ctx_manager.create_context()
```

### Encryption Too Slow

**Symptoms:**
- Encryption takes minutes for small datasets
- High memory usage

**Solutions:**

1. **Use optimization profiles:**
```python
from sdk.encryption import OptimizedFHEEngine, OptimizationProfile

engine = OptimizedFHEEngine(profile=OptimizationProfile.FAST)
```

2. **Reduce polynomial degree:**
```python
# Lower security but faster
ctx_manager = FHEContextManager(security_level=SecurityLevel.BITS_128)
```

3. **Batch your data:**
```python
# Process in smaller batches
batch_size = 100
for i in range(0, len(data), batch_size):
    batch = data[i:i+batch_size]
    encrypted_batch = encrypt(batch)
```

### Decryption Returns Wrong Values

**Symptoms:**
- Decrypted values are very different from original
- NaN or Inf values after decryption

**Causes:**
- Too many multiplications (noise accumulation)
- Values outside CKKS precision range

**Solutions:**

1. **Normalize input data:**
```python
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_normalized = scaler.fit_transform(X)
# Now values are in reasonable range
```

2. **Use higher precision profile:**
```python
from sdk.encryption import OptimizedFHEEngine, OptimizationProfile

engine = OptimizedFHEEngine(profile=OptimizationProfile.PRECISE)
```

3. **Limit multiplication depth:**
```python
# For decision trees, reduce depth
from sdk import TreeConfig

config = TreeConfig(max_depth=3)  # Instead of 5+
```

---

## Model Training Issues

### Training Loss Not Decreasing

**Symptoms:**
- Loss stays constant or oscillates
- Model predictions are random

**Causes:**
- Learning rate too high or too low
- Data not normalized
- Incorrect label format

**Solutions:**

1. **Adjust learning rate:**
```python
from sdk import ModelConfig

# Try different learning rates
for lr in [0.1, 0.01, 0.001, 0.0001]:
    config = ModelConfig(learning_rate=lr, epochs=50)
    model.fit(X, y, config=config)
    print(f"LR={lr}, Final loss: {model.history.losses[-1]}")
```

2. **Normalize data:**
```python
from sdk import SecureDataLoader

loader = SecureDataLoader()
dataset = loader.load_and_encrypt(df, normalize=True)  # Enable normalization
```

3. **Check label format:**
```python
# For binary classification, labels should be 0 and 1
y = (y > threshold).astype(int)

# For regression, ensure continuous values
y = y.astype(float)
```

### Out of Memory During Training

**Error:**
```
MemoryError: Unable to allocate array
```

**Solutions:**

1. **Reduce batch size:**
```python
config = ModelConfig(batch_size=16)  # Instead of 32 or 64
```

2. **Use memory-efficient profile:**
```python
from sdk.encryption import OptimizedFHEEngine, OptimizationProfile

engine = OptimizedFHEEngine(profile=OptimizationProfile.MEMORY_EFFICIENT)
```

3. **Process data in chunks:**
```python
# Train on subsets
for chunk in np.array_split(X, 10):
    model.partial_fit(chunk, y_chunk)
```

### LogisticRegression Accuracy is ~50%

**Symptoms:**
- Binary classification accuracy around random chance
- Predictions all same class

**Causes:**
- Sigmoid approximation too simple for data
- Class imbalance
- Features not separable

**Solutions:**

1. **Use higher degree approximation:**
```python
from sdk import LogisticRegression, SigmoidApproximation

# Try more accurate approximation
model = LogisticRegression(
    sigmoid_approximation=SigmoidApproximation.DEGREE5
)
```

2. **Handle class imbalance:**
```python
# Oversample minority class or use class weights
from sklearn.utils import class_weight

weights = class_weight.compute_class_weight('balanced', classes=[0, 1], y=y)
# Apply weights in loss calculation
```

3. **Check feature quality:**
```python
# Verify features have predictive power
from sklearn.feature_selection import mutual_info_classif

mi_scores = mutual_info_classif(X, y)
print("Feature importance:", mi_scores)
```

---

## Blockchain Issues

### Connection Refused

**Error:**
```
ConnectionError: HTTPConnectionPool - Max retries exceeded
```

**Causes:**
- Wrong RPC endpoint
- Network issues
- Rate limiting

**Solutions:**

1. **Check network configuration:**
```python
from sdk import BlockchainConnector, Network

# Use correct network
connector = BlockchainConnector(
    network=Network.ARBITRUM_SEPOLIA,  # Not ARBITRUM_ONE for testnet
    rpc_url="https://sepolia-rollup.arbitrum.io/rpc"  # Explicit URL
)
```

2. **Use reliable RPC provider:**
```python
# Use Alchemy or Infura
connector = BlockchainConnector(
    network=Network.ARBITRUM_ONE,
    rpc_url="https://arb-mainnet.g.alchemy.com/v2/YOUR_KEY"
)
```

### Transaction Failed

**Error:**
```
TransactionFailed: execution reverted
```

**Causes:**
- Insufficient gas
- Contract permissions
- Invalid parameters

**Solutions:**

1. **Check gas settings:**
```python
tx_hash = registry.register_model(
    model_id="model-001",
    model_hash=hash,
    gas_limit=500000,  # Increase if needed
    gas_price=None  # Let network estimate
)
```

2. **Verify permissions:**
```python
# Check if address is consortium member
is_member = governance.is_member(consortium_id, my_address)
if not is_member:
    print("Not authorized - request membership first")
```

3. **Validate parameters:**
```python
# Ensure model_id is unique
existing = registry.get_model(model_id)
if existing:
    model_id = f"{model_id}-{int(time.time())}"
```

### Insufficient Funds

**Error:**
```
InsufficientFunds: sender doesn't have enough funds
```

**Solutions:**

1. **Get testnet ETH:**
   - Arbitrum Sepolia: https://faucet.quicknode.com/arbitrum/sepolia
   - Ethereum Sepolia: https://sepoliafaucet.com/

2. **Check balance:**
```python
balance = connector.get_balance()
print(f"Balance: {balance} ETH")
```

---

## CLI Issues

### Command Not Found

**Error:**
```
bash: xcapit-fhe: command not found
```

**Solution:**
```bash
# Ensure package is installed
pip install -e .

# Or run directly
python -m sdk.cli --help
```

### Invalid Model Type

**Error:**
```
Error: Invalid model type 'random-forest'
```

**Supported models:**
- `linear-regression`
- `logistic-regression`
- `decision-tree`
- `kmeans`

```bash
xcapit-fhe train --model logistic-regression --data encrypted.bin
```

### File Format Error

**Error:**
```
Error: Cannot read encrypted file
```

**Causes:**
- Wrong file format
- Corrupted file
- Version mismatch

**Solutions:**

1. **Re-encrypt with current version:**
```bash
xcapit-fhe encrypt --input data.csv --context context.bin --output encrypted.bin
```

2. **Check file integrity:**
```python
import pickle

try:
    with open("encrypted.bin", "rb") as f:
        data = pickle.load(f)
    print("File is valid")
except Exception as e:
    print(f"File corrupted: {e}")
```

---

## Performance Optimization

### Slow Predictions

**Symptoms:**
- Single prediction takes seconds
- Batch prediction is very slow

**Solutions:**

1. **Use context pooling:**
```python
from sdk.encryption import ContextPool

pool = ContextPool(max_contexts=4)
# Contexts are reused across predictions
```

2. **Enable lazy evaluation:**
```python
from sdk.encryption import LazyEncryptedVector

# Operations are fused and executed together
lazy_vec = LazyEncryptedVector(data)
result = (lazy_vec + other) * scalar  # Not executed yet
final = result.evaluate()  # Single optimized execution
```

3. **Batch predictions:**
```python
# Instead of one-by-one
for x in X:
    pred = model.predict([x])  # Slow!

# Do batch
predictions = model.predict(X)  # Fast!
```

### High Memory Usage

**Solutions:**

1. **Clear contexts when done:**
```python
del context
import gc
gc.collect()
```

2. **Use streaming for large datasets:**
```python
# Process chunks
for chunk in pd.read_csv("large.csv", chunksize=1000):
    encrypted_chunk = loader.encrypt(chunk)
    predictions = model.predict(encrypted_chunk)
    save_predictions(predictions)
    del encrypted_chunk  # Free memory
```

---

## Getting Help

### Enable Debug Logging

```python
from sdk.monitoring import setup_logging
import logging

setup_logging(level=logging.DEBUG)
# Now you'll see detailed operation logs
```

### Check SDK Version

```python
from sdk import __version__
print(f"SDK Version: {__version__}")
```

### Report Issues

1. Collect debug information:
```python
import sys
import tenseal
from sdk import __version__

print(f"Python: {sys.version}")
print(f"TenSEAL: {tenseal.__version__}")
print(f"SDK: {__version__}")
```

2. Open issue at: https://github.com/xcapit/privacy-platform/issues

Include:
- Error message (full traceback)
- SDK version
- Code to reproduce
- Expected vs actual behavior

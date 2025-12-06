# Xcapit FHE-ML Platform

Privacy-preserving machine learning platform using Fully Homomorphic Encryption (FHE).

## Quick Start
```bash
pip install xcapit-fhe-ml
```
```python
from xcapit_fhe import FHEModel, SecureDataLoader

loader = SecureDataLoader()
encrypted_data = loader.encrypt(df)

model = FHEModel.LogisticRegression()
model.fit(encrypted_data)
```

## Why Xcapit FHE-ML?

- **Privacy-First**: Train ML models without exposing sensitive data
- **Enterprise-Ready**: Blockchain auditability, compliance built-in
- **Developer-Friendly**: Scikit-learn compatible API
- **Production-Tested**: Built by team behind QuarkID (3.6M users)

## Documentation

- [Getting Started](docs/getting-started.md)
- [API Reference](docs/api-reference.md)
- [Examples](examples/)

## Security

- CKKS encryption scheme (128-bit security)
- Blockchain-verified computation
- LGPD/GDPR compliant by design

## License

Apache 2.0

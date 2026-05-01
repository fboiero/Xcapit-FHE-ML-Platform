# Xcapit FHE-ML: A Multi-Layer Cryptographic Architecture for Privacy-Preserving Data Consortia

**Version**: 1.0 (Draft)
**Date**: May 2026
**Authors**: Xcapit Team

---

## Abstract

We present Xcapit FHE-ML, an open-source platform for privacy-preserving machine learning in multi-party data consortia. Unlike existing approaches that focus on a single cryptographic primitive, our architecture composes four complementary layers — Fully Homomorphic Encryption (FHE), Zero-Knowledge Proofs (ZKP), Multi-Party Computation (MPC), and Differential Privacy (DP) — within a unified framework anchored by on-chain governance via Arbitrum smart contracts.

We describe the architecture, detail each cryptographic layer's implementation, present honest assessments of current capabilities and limitations, and compare with existing approaches. Our contribution is not a new cryptographic primitive but rather the first full-stack, open-source platform that integrates all four layers into a production-oriented system for collaborative ML without data sharing.

**Keywords**: Fully Homomorphic Encryption, Zero-Knowledge Proofs, Multi-Party Computation, Differential Privacy, Federated Learning, Privacy-Preserving Machine Learning, Data Consortium, Blockchain Governance.

---

## 1. Introduction

### 1.1 The Data Consortium Problem

Organizations across banking, healthcare, insurance, and government hold valuable datasets that, if combined, could train significantly better ML models. A fraud detection model trained across three banks sees patterns no single bank can detect alone. A diagnostic model trained across five hospitals achieves accuracy impossible with any single institution's data.

However, regulatory constraints (GDPR, HIPAA, PCI-DSS), competitive concerns, and practical barriers prevent direct data sharing. Existing solutions — data clean rooms, federated learning frameworks, or single-primitive encryption libraries — address parts of the problem but leave gaps:

- **Data clean rooms** require trust in a third-party operator and offer limited ML capabilities.
- **Federated learning** (Google FL, NVFlare) trains on decentralized data but leaks information through model gradients [Zhu et al., 2019].
- **FHE libraries** (Concrete-ML, SEAL) enable computation on encrypted data but don't address governance, auditability, or multi-party coordination.
- **MPC frameworks** (PySyft, MP-SPDZ) provide secure computation but impose high communication overhead and lack integration with ML pipelines.

### 1.2 Our Approach

Xcapit FHE-ML is a **full-stack platform** — not a library — that combines four cryptographic layers, each addressing a distinct threat:

| Layer | Threat Addressed | Primitive |
|-------|------------------|-----------|
| **FHE** | Server sees data in the clear | CKKS homomorphic encryption |
| **ZKP** | Participants claim false data properties | Pedersen commitments + Schnorr proofs |
| **MPC** | Centralized aggregation reveals individual contributions | Shamir secret sharing + secure aggregation |
| **DP** | Trained model memorizes and leaks individual records | Calibrated Laplace/Gaussian noise with RDP accounting |

On-chain governance (Arbitrum smart contracts) provides immutable audit trails, commit-reveal voting, and automated reward distribution — addressing the trust and coordination challenges that purely cryptographic solutions ignore.

### 1.3 Contributions

1. A composable multi-layer architecture where each cryptographic layer can be used independently or in combination.
2. Open-source implementations of all four layers within a production-oriented framework (Django REST backend, React dashboard, Python SDK).
3. An honest assessment of implementation maturity, including which ML models support genuine FHE inference versus transport-only encryption.
4. On-chain governance contracts for consortium management, auditable on Arbitrum.

---

## 2. Architecture

### 2.1 System Overview

```
                                ┌─────────────────────┐
                                │   On-Chain Layer     │
                                │   (Arbitrum)         │
                                │                      │
                                │  ConsortiumGov v2    │
                                │  ModelRegistry v2    │
                                │  CompVerifier v2     │
                                └──────────┬──────────┘
                                           │ audit trail
                                           │ governance
┌──────────────┐    ┌──────────────┐    ┌──┴───────────┐
│  Org A       │    │  Org B       │    │  Platform     │
│              │    │              │    │  Backend      │
│  SDK         │    │  SDK         │    │  (Django)     │
│  ┌────────┐  │    │  ┌────────┐  │    │              │
│  │ FHE    │──┼────┼──│ FHE    │──┼────┤  Encrypted   │
│  │ encrypt│  │    │  │ encrypt│  │    │  aggregation  │
│  └────────┘  │    │  └────────┘  │    │              │
│  ┌────────┐  │    │  ┌────────┐  │    │  ┌────────┐  │
│  │ ZKP    │──┼────┼──│ ZKP    │──┼────┤  │ Verify │  │
│  │ prove  │  │    │  │ prove  │  │    │  │ proofs │  │
│  └────────┘  │    │  └────────┘  │    │  └────────┘  │
│  ┌────────┐  │    │  ┌────────┐  │    │  ┌────────┐  │
│  │ MPC    │──┼────┼──│ MPC    │──┼────┤  │ Shamir │  │
│  │ share  │  │    │  │ share  │  │    │  │ recon  │  │
│  └────────┘  │    │  └────────┘  │    │  └────────┘  │
│  ┌────────┐  │    │  ┌────────┐  │    │  ┌────────┐  │
│  │ DP     │  │    │  │ DP     │  │    │  │ Privacy│  │
│  │ noise  │  │    │  │ noise  │  │    │  │ budget │  │
│  └────────┘  │    │  └────────┘  │    │  └────────┘  │
└──────────────┘    └──────────────┘    └──────────────┘
```

### 2.2 Data Flow in a Consortium Training Round

1. **Consortium formation**: Organizations create a consortium via the platform. Membership, voting rules, and data requirements are registered on-chain via `ConsortiumGovernanceV2`.

2. **Data contribution**: Each organization encrypts its local dataset using CKKS (via the SDK's `CKKSEncryptor`) and generates ZKP commitments proving data properties (size, schema, value ranges) without revealing the data itself.

3. **Proof verification**: The platform verifies ZKP commitments. The `ContributionProof` binds the data hash, encryption parameters, and schema to a Pedersen commitment verified via Schnorr protocol.

4. **Secure aggregation**: MPC distributes the computation. Each party's contribution is split into Shamir shares; aggregation occurs over masked shares without any single party seeing the combined data. The `SecureAggregator` implements pairwise masking per Bonawitz et al. [2017].

5. **Model training**: Depending on the model and FHE level, training occurs on encrypted data (LinearRegression, LogisticRegression) or on securely aggregated plaintext (other models). Differential privacy noise is applied to gradients via `DPSGDTrainer` to prevent memorization.

6. **Result publication**: The trained model is registered on-chain via `ModelRegistryV2`. Its provenance (contributing parties, training parameters, privacy budget consumed) is immutable.

7. **Prediction serving**: For models with FHE FULL support, inference operates directly on encrypted inputs. For others, the model serves predictions on plaintext inputs with transport-layer encryption.

---

## 3. Cryptographic Layers

### 3.1 Fully Homomorphic Encryption (FHE)

**Scheme**: CKKS [Cheon et al., 2017] via TenSEAL [Benaissa et al., 2021].
**Security**: 128-bit, 192-bit, or 256-bit selectable.

#### What CKKS enables

CKKS supports approximate arithmetic on encrypted floating-point vectors, making it suitable for ML inference on linear models. Our `CKKSEncryptor` wraps TenSEAL to provide:

- `encrypt_vector(plaintext) → CKKSVector`: encrypted vector supporting addition and scalar multiplication.
- `encrypt_matrix(plaintext) → [CKKSVector]`: row-wise encryption.
- Homomorphic `+` and `*` between ciphertext and plaintext.

#### Current FHE support by model

| Model | Training | Inference | Notes |
|-------|----------|-----------|-------|
| **Linear Regression** | Plaintext | **Encrypted (FULL)** | Dot product of encrypted input with plaintext weights via CKKS. Only model with genuine end-to-end encrypted inference. |
| **Logistic Regression** | Plaintext | **Partially encrypted** | Single-sample inference uses polynomial approximation of sigmoid over CKKS. Batch inference decrypts. |
| Neural Network | Plaintext | Decrypts before compute | Polynomial activations designed for FHE exist but are not yet wired to encrypted inference. |
| KMeans, SVM, PCA | Plaintext | Decrypts before compute | Architecture supports FHE extension; not yet implemented. |
| All other models | Plaintext | Plaintext with transport encryption | — |

**Honest assessment**: Genuine encrypted inference is limited to linear models. The architecture (model base class, encryption wrapper, FHE level enum) is designed for extension, but most models currently decrypt before computing. Expanding FHE coverage to neural networks via polynomial activations is the primary focus of our roadmap.

#### Performance characteristics

CKKS operations are approximately 1000x slower than plaintext equivalents. A linear regression prediction on a 50-feature encrypted vector takes ~2-5ms versus ~0.005ms in plaintext. This overhead is acceptable for batch inference but not for real-time scoring at scale without hardware acceleration.

### 3.2 Zero-Knowledge Proofs (ZKP)

**Schemes**: Pedersen commitments + Schnorr identification protocol + arithmetic circuits with R1CS export.

#### Pedersen Commitments

Our `PedersenCommitment` operates over a 2048-bit safe prime (RFC 3526, Group 14). The generator `h` is derived via a nothing-up-my-sleeve construction: `h = H(g)^2 mod p`, ensuring no party knows the discrete log relationship between `g` and `h`.

A commitment to value `v` with randomness `r`:

```
C = g^v · h^r mod p
```

The commitment is perfectly hiding (information-theoretically) and computationally binding under the discrete logarithm assumption.

#### Schnorr Proofs

Interactive Schnorr proofs are made non-interactive via Fiat-Shamir heuristic:

1. Prover picks random `k`, computes `R = g^k mod p`.
2. Challenge `c = H(g || Y || R)` where `Y = g^x mod p` is the public key.
3. Response `s = k + c·x mod q`.
4. Verifier checks `g^s ≡ R · Y^c (mod p)`.

Our implementation includes subgroup validation to prevent small-subgroup attacks.

#### Contribution Proofs

`ContributionProof` binds a data contribution to its properties:

- Data hash (SHA-256 of the plaintext).
- Encryption parameters (scheme, security level).
- Schema properties (column count, row count, feature names).

**Limitation**: The current implementation includes blinding factors in the serialized proof. While the proof remains binding and unforgeable, it does not satisfy the zero-knowledge property in the strict sense — a verifier learns the blinding factors. This is flagged for remediation in the crypto hardening phase.

#### Arithmetic Circuits

For more complex proofs, we provide `ArithmeticCircuit` with gates (ADD, MUL, CONST) and export to Rank-1 Constraint System (R1CS) format. This enables integration with external proof systems (Groth16, PLONK) for on-chain verification.

### 3.3 Multi-Party Computation (MPC)

**Scheme**: Shamir Secret Sharing over GF(p) where p is the secp256k1 prime (256-bit).

#### Secret Sharing

`SecretSharer` implements (t, n)-threshold Shamir:

- Share generation: polynomial of degree `t-1` with secret as constant term, evaluated at `n` distinct points.
- Reconstruction: Lagrange interpolation over GF(p) using extended Euclidean algorithm for modular inverse.
- Randomness: `secrets.randbelow()` for cryptographic quality.

This is mathematically standard Shamir — no simplifications.

#### Secure Aggregation

`SecureAggregator` implements the pairwise masking protocol of Bonawitz et al. [2017]:

1. Each pair of parties (i, j) derives a shared mask from a seed.
2. Party i adds mask_ij to its update; party j subtracts mask_ij.
3. The server sums all masked updates; masks cancel out in aggregate.

**Limitation**: Pairwise seeds are currently derived from deterministic strings rather than Diffie-Hellman key exchange. This is acceptable for testing and demonstration but must be replaced with ECDH for production deployment.

#### Threshold Operations

`ThresholdDecryptor` provides threshold encryption where no single party holds the complete key. Key generation uses `KeyCeremony` which distributes shares via Shamir.

**Limitation**: The symmetric encryption uses XOR with iterated SHA-256 keystream rather than AES-GCM. The code explicitly documents this as a non-production implementation. HMAC authentication is genuine.

### 3.4 Differential Privacy (DP)

**Mechanisms**: Laplace, Gaussian, Exponential.
**Accounting**: Renyi Differential Privacy (RDP) composition.

#### Noise Mechanisms

| Mechanism | Formula | Reference |
|-----------|---------|-----------|
| Laplace | `scale = Δf / ε` | Dwork et al., 2006 |
| Gaussian | `σ = Δf · √(2·ln(1.25/δ)) / ε` | Dwork & Roth, Theorem 3.22 |
| Exponential | Utility-based selection with calibrated probabilities | McSherry & Talwar, 2007 |

All mechanisms use cryptographic random number generation (`secrets.randbits(128)` → uniform float via IEEE 754 decomposition).

#### Privacy Accounting

`PrivacyAccountant` tracks cumulative privacy expenditure across multiple mechanism invocations:

- **Basic composition**: ε_total = Σε_i (tight for pure DP).
- **Advanced composition**: ε_total = √(2k·ln(1/δ))·ε + k·ε·(e^ε - 1) (Dwork et al., 2010).
- **RDP composition**: α-Rényi divergence with conversion to (ε, δ)-DP. Covers the Gaussian mechanism; does not include subsampling amplification.

#### DP-SGD Training

`DPSGDTrainer` implements differentially private stochastic gradient descent:

1. **Per-sample gradient clipping**: each sample's gradient is clipped to max norm C.
2. **Noise addition**: Gaussian noise with σ = noise_multiplier · C added to the clipped sum.
3. **Privacy accounting**: each training step consumes privacy budget tracked via RDP.

The implementation is genuine and follows the framework of Abadi et al. [2016]. **One path** in the base `DPTrainer` class uses `np.random.normal()` instead of the cryptographic RNG — flagged for remediation.

---

## 4. On-Chain Governance

### 4.1 Smart Contracts

Three Solidity 0.8.20 contracts deployed on Arbitrum (L2), inheriting OpenZeppelin's `Ownable2Step`, `Pausable`, and `ReentrancyGuard`:

**ConsortiumGovernanceV2** (v2.1.0):
- Membership management (max 100 members per consortium).
- Commit-reveal voting: 60% commit phase, 40% reveal phase. Prevents front-running and vote copying.
- 9 proposal types covering model training, member addition/removal, parameter changes, reward distribution.
- Pull-over-push reward distribution: members claim rewards rather than having them pushed, preventing reentrancy.
- 12 event types for immutable audit trail.

**ModelRegistryV2** (v2.0.0):
- Checkpoint-based model versioning (max 100 per query, paginated).
- Verification by trusted verifiers (owner cannot self-verify).
- Hash-based integrity validation.

**ComputationVerifierV2** (v2.0.0):
- Batch verification of FHE computation results (up to 1,000 per batch).
- O(1) lookup via indexed mappings.
- Audit trail linking computations to model versions and consortium context.

### 4.2 Why Blockchain for Governance

Blockchain addresses a problem that cryptographic protocols alone cannot: **multi-party coordination without a trusted coordinator**. When three competing banks form a fraud detection consortium, none trusts the others to manage voting, reward distribution, or audit logs fairly. Smart contracts provide:

- **Immutability**: audit events cannot be altered retroactively.
- **Transparency**: all governance actions are publicly verifiable.
- **Automation**: reward distribution and voting rules execute deterministically.
- **Dispute resolution**: on-chain records serve as evidence in disagreements.

---

## 5. Comparison with Existing Approaches

| Feature | Xcapit FHE-ML | Zama Concrete-ML | PySyft (OpenMined) | NVFlare (NVIDIA) | Duality | TripleBlind |
|---------|---------------|-------------------|--------------------|------------------|---------|-------------|
| Open source | Yes (AGPL-3.0) | Yes (BSD-3) | Yes (Apache-2.0) | Yes (Apache-2.0) | No | No |
| FHE | CKKS (TenSEAL) | TFHE (custom) | HE (partial) | No | HE | Partial |
| ZKP | Pedersen + Schnorr | No | No | No | No | No |
| MPC | Shamir + Secure Aggregation | No | SPDZ (partial) | No | No | Partial |
| DP | Laplace/Gaussian + RDP + DP-SGD | No | DP (basic) | DP | No | No |
| Blockchain governance | Arbitrum (commit-reveal, rewards) | No | No | No | No | No |
| Full platform (not library) | Yes (SDK + API + Dashboard) | No (library only) | No (library) | Framework | Yes | Yes |
| Multi-tenant SaaS | Yes (4 tiers) | No | No | No | Yes | Yes |
| ML models with genuine FHE | 1-2 (linear family) | 10+ (via TFHE compilation) | N/A | N/A | Unknown | Unknown |

**Key differentiator**: Xcapit FHE-ML is the only open-source project that combines all four cryptographic layers with on-chain governance in a production-oriented platform. However, Zama's Concrete-ML offers significantly deeper FHE support for ML models through TFHE compilation, an area where our platform requires further development.

---

## 6. Limitations and Future Work

We believe honest disclosure of limitations strengthens rather than weakens the platform's credibility.

### 6.1 Current Limitations

| Limitation | Impact | Planned Resolution |
|------------|--------|-------------------|
| FHE inference limited to linear models | Most models decrypt before computing | Polynomial activation integration for neural networks; evaluate migration to Concrete-ML's TFHE compiler |
| 3 models declare invalid FHE level (`TRANSPORT`) | Runtime errors if FHE is requested | Fix enum values and implement transport-only encryption correctly |
| ContributionProof leaks blinding factors | Not truly zero-knowledge | Refactor to exclude blinding factors from serialized proofs |
| MPC seeds not derived from DH key exchange | Pairwise masks predictable to an adversary who knows party indices | Implement ECDH key exchange for seed derivation |
| ThresholdDecryptor uses XOR+SHA256 not AES-GCM | Not production-grade symmetric encryption | Replace with AES-GCM (Go standard library or `cryptography` Python) |
| One DP path uses non-cryptographic PRNG | Noise may be predictable to an adversary who controls the seed | Replace `np.random.normal()` with `secrets`-based Gaussian |
| RDP accounting lacks subsampling amplification | Privacy budget bounds are conservative for DP-SGD with mini-batches | Implement Poisson subsampling amplification per Mironov et al. [2019] |

### 6.2 Roadmap

**Phase 1 — Crypto Hardening** (in progress):
- External cryptographic audit (contracted, awaiting results).
- Fix all limitations marked as production blockers above.
- Add replay protection (nonces + session binding) to Fiat-Shamir transforms.
- KeyCeremony: eliminate in-memory storage of complete secrets.

**Phase 2 — FHE Expansion**:
- Integrate polynomial activations into NeuralNetwork's encrypted inference path.
- Evaluate Concrete-ML's TFHE compiler as an alternative backend for broader model support.
- GPU acceleration for CKKS operations (CUDA-enabled TenSEAL or Lattigo).

**Phase 3 — Scalability**:
- Asynchronous MPC rounds for large consortia (>10 parties).
- FHE parameter optimization (auto-tuning polynomial degree and scale).
- Distributed key generation for ThresholdDecryptor without trusted dealer.

**Phase 4 — On-Chain Verification**:
- ZKP verification directly on-chain (Groth16 verifier contract for R1CS proofs).
- Encrypted model hashes registered via ComputationVerifierV2.
- Cross-chain governance (bridge to Ethereum mainnet for higher-value consortia).

---

## 7. Conclusion

Xcapit FHE-ML demonstrates that composing multiple cryptographic layers in a single platform is both feasible and valuable for multi-party ML. Our architecture is not the deepest implementation of any single primitive — Zama's Concrete-ML offers better FHE coverage, MP-SPDZ offers more MPC protocols, and dedicated DP libraries offer tighter accounting bounds.

Our contribution is in the **composition**: by integrating FHE, ZKP, MPC, and DP with on-chain governance, we address the full spectrum of threats in a data consortium — from data-in-use confidentiality (FHE) to contribution integrity (ZKP) to aggregation privacy (MPC) to model memorization (DP) to coordination trust (blockchain).

The platform is open-source (AGPL-3.0), has 2,163 passing tests at 96% coverage, and is deployed as a production-oriented SaaS with multi-tenant support. We invite the research community and industry practitioners to evaluate, extend, and challenge our implementations.

---

## References

- Abadi, M. et al. (2016). Deep Learning with Differential Privacy. *CCS '16*.
- Benaissa, A. et al. (2021). TenSEAL: A Library for Encrypted Tensor Operations Using Homomorphic Encryption. *ICLR Workshop on DPML*.
- Bonawitz, K. et al. (2017). Practical Secure Aggregation for Privacy-Preserving Machine Learning. *CCS '17*.
- Cheon, J.H. et al. (2017). Homomorphic Encryption for Arithmetic of Approximate Numbers. *ASIACRYPT '17*.
- Dwork, C. et al. (2006). Calibrating Noise to Sensitivity in Private Data Analysis. *TCC '06*.
- Dwork, C. & Roth, A. (2014). The Algorithmic Foundations of Differential Privacy. *Foundations and Trends in Theoretical Computer Science*.
- McSherry, F. & Talwar, K. (2007). Mechanism Design via Differential Privacy. *FOCS '07*.
- Mironov, I. et al. (2019). Rényi Differential Privacy of the Sampled Gaussian Mechanism. *arXiv:1702.07476v3*.
- Zhu, L. et al. (2019). Deep Leakage from Gradients. *NeurIPS '19*.

---

## Appendix A: Test Coverage Summary

| Component | Tests | Coverage | Framework |
|-----------|-------|----------|-----------|
| Django backend (13 apps) | 1,968 | 96.23% | pytest |
| Python SDK (MPC, ZKP, DP, encryption) | 195 | — | pytest |
| Security tests (IDOR, SSRF, tenant isolation) | 27 | 100% | pytest |
| Smart contracts (3 v2 contracts) | ~50 | — | Foundry |
| E2E dashboard flows | 28 | — | Playwright |
| Performance / SLO validation | 10 endpoints | — | Locust |
| **Total** | **~2,268** | — | — |

## Appendix B: Repository

- **Source**: https://github.com/xcapit/Xcapit-FHE-ML-Platform (AGPL-3.0)
- **Documentation**: 43+ files, 21 SVG diagrams, 7 Jupyter notebooks
- **CI/CD**: 10 GitHub Actions jobs + GitLab CI mirroring

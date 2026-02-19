# Arquitectura Técnica - Xcapit FHE-ML Platform

## Visión General

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           XCAPIT FHE-ML PLATFORM                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                     │
│  │  Cliente A  │    │  Cliente B  │    │  Cliente C  │                     │
│  │  (Bank)     │    │  (Hospital) │    │  (Fintech)  │                     │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                     │
│         │                  │                  │                             │
│         ▼                  ▼                  ▼                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         SDK (Python/TypeScript)                      │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │   │
│  │  │ FHE Module  │  │ Blockchain  │  │  ML Models  │                  │   │
│  │  │ (TenSEAL)   │  │ (web3.py)   │  │ (sklearn)   │                  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         Backend (Django 5.2)                         │   │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐           │   │
│  │  │Consortiums│ │Governance │ │ ML Models │ │Compliance │           │   │
│  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Arbitrum Blockchain (L2)                          │   │
│  │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐       │   │
│  │  │  Governance V2  │ │ Model Registry  │ │    Verifier     │       │   │
│  │  │   (Voting)      │ │  (Versions)     │ │   (Proofs)      │       │   │
│  │  └─────────────────┘ └─────────────────┘ └─────────────────┘       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Componente 1: FHE (Fully Homomorphic Encryption)

### Biblioteca: TenSEAL

```python
# sdk/encryption/fhe_context.py

import tenseal as ts

class FHEContextManager:
    """Gestiona el contexto de cifrado CKKS."""

    def create_context(
        self,
        poly_modulus_degree: int = 8192,
        coeff_mod_bit_sizes: list = [60, 40, 40, 60],
        scale: float = 2**40
    ) -> ts.Context:
        """
        Crea contexto CKKS para operaciones homomórficas.

        Parámetros de seguridad (128-bit):
        - poly_modulus_degree: 8192 (tamaño del anillo)
        - coeff_mod_bit_sizes: Define profundidad multiplicativa
        - scale: Precisión de números reales
        """
        context = ts.context(
            ts.SCHEME_TYPE.CKKS,
            poly_modulus_degree=poly_modulus_degree,
            coeff_mod_bit_sizes=coeff_mod_bit_sizes
        )
        context.global_scale = scale
        context.generate_galois_keys()  # Para rotaciones
        context.generate_relin_keys()   # Para relinearización
        return context
```

### Flujo de Cifrado

```
┌─────────────────────────────────────────────────────────────────┐
│                    PROCESO DE CIFRADO FHE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. DATOS ORIGINALES (Plaintext)                                │
│     ┌────────────────────────────────────┐                      │
│     │ amount: 523.45                     │                      │
│     │ hour: 14                           │                      │
│     │ distance: 25.3                     │                      │
│     └────────────────────────────────────┘                      │
│                         │                                        │
│                         ▼                                        │
│  2. CODIFICACIÓN (Encode)                                       │
│     ┌────────────────────────────────────┐                      │
│     │ Vector de coeficientes reales      │                      │
│     │ [523.45, 14.0, 25.3, 0, 0, ...]   │                      │
│     └────────────────────────────────────┘                      │
│                         │                                        │
│                         ▼                                        │
│  3. CIFRADO (Encrypt con clave pública)                         │
│     ┌────────────────────────────────────┐                      │
│     │ Ciphertext (4096 coeficientes)     │                      │
│     │ [0x7a3f8c2d, 0x4b6e1a9f, ...]     │                      │
│     └────────────────────────────────────┘                      │
│                         │                                        │
│                         ▼                                        │
│  4. OPERACIONES HOMOMÓRFICAS                                    │
│     ┌────────────────────────────────────┐                      │
│     │ enc_result = enc_a * weight + bias │                      │
│     │ (todo en ciphertext)               │                      │
│     └────────────────────────────────────┘                      │
│                         │                                        │
│                         ▼                                        │
│  5. DESCIFRADO (Solo con clave privada)                         │
│     ┌────────────────────────────────────┐                      │
│     │ result: 0.87 (probabilidad fraude) │                      │
│     └────────────────────────────────────┘                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Modelos ML Soportados

```python
# sdk/models/

class LogisticRegression:
    """Regresión logística sobre datos cifrados."""

    def fit(self, X_encrypted, y_encrypted):
        """
        Entrena usando gradiente descendente homomórfico.

        Operaciones sobre ciphertext:
        1. z = X @ weights + bias
        2. pred = sigmoid_approx(z)  # Aproximación polinomial
        3. gradient = X.T @ (pred - y)
        4. weights -= lr * gradient
        """
        pass

    def predict(self, X_encrypted):
        """Predicción sobre datos cifrados."""
        return sigmoid_approx(X_encrypted @ self.weights + self.bias)


class LinearRegression:
    """Regresión lineal (closed-form o gradiente)."""
    pass


class DecisionTreeApprox:
    """Árbol de decisión aproximado con comparaciones suaves."""
    pass


class KMeansClustering:
    """K-Means sobre datos cifrados."""
    pass
```

---

## Componente 2: Blockchain (Arbitrum)

### Smart Contracts

#### ConsortiumGovernanceV2.sol

```solidity
// contracts/src/v2/ConsortiumGovernanceV2.sol

contract ConsortiumGovernanceV2 {

    // Estructura de un consorcio
    struct Consortium {
        string name;
        address[] members;
        uint256 votingQuorum;      // % requerido (ej: 51)
        uint256 votingDuration;    // segundos (ej: 86400 = 24h)
        bool active;
    }

    // Estructura de una propuesta
    struct Proposal {
        bytes32 id;
        ProposalType proposalType;  // START_TRAINING, ADD_MEMBER, etc.
        uint256 commitDeadline;
        uint256 revealDeadline;
        mapping(address => bytes32) commitments;
        mapping(address => bool) votes;
        mapping(address => bool) revealed;
        uint256 yesVotes;
        uint256 noVotes;
        bool executed;
    }

    // Commit-Reveal Voting
    function commitVote(
        bytes32 proposalId,
        bytes32 commitment  // hash(proposalId + vote + salt)
    ) external onlyMember {
        require(block.timestamp < proposals[proposalId].commitDeadline);
        proposals[proposalId].commitments[msg.sender] = commitment;
    }

    function revealVote(
        bytes32 proposalId,
        bool vote,
        bytes32 salt
    ) external onlyMember {
        require(block.timestamp >= proposals[proposalId].commitDeadline);
        require(block.timestamp < proposals[proposalId].revealDeadline);

        // Verificar commitment
        bytes32 expected = keccak256(abi.encodePacked(proposalId, vote, salt));
        require(expected == proposals[proposalId].commitments[msg.sender]);

        proposals[proposalId].votes[msg.sender] = vote;
        proposals[proposalId].revealed[msg.sender] = true;

        if (vote) {
            proposals[proposalId].yesVotes++;
        } else {
            proposals[proposalId].noVotes++;
        }
    }
}
```

#### ModelRegistryV2.sol

```solidity
// contracts/src/v2/ModelRegistryV2.sol

contract ModelRegistryV2 {

    struct Model {
        bytes32 id;
        bytes32 consortiumId;
        string modelType;           // "LogisticRegression", "LinearRegression"
        bytes32 weightsHash;        // Hash de los pesos del modelo
        uint256 version;
        uint256 accuracy;           // En basis points (9500 = 95.00%)
        uint256 trainedAt;
        address[] contributors;     // Miembros que contribuyeron datos
    }

    function registerModel(
        bytes32 consortiumId,
        string memory modelType,
        bytes32 weightsHash,
        uint256 accuracy,
        address[] memory contributors
    ) external onlyGovernance returns (bytes32) {
        // Solo se puede registrar si la propuesta de training fue aprobada
        require(governance.isProposalExecuted(consortiumId, "START_TRAINING"));

        bytes32 modelId = keccak256(abi.encodePacked(
            consortiumId, modelType, block.timestamp
        ));

        models[modelId] = Model({
            id: modelId,
            consortiumId: consortiumId,
            modelType: modelType,
            weightsHash: weightsHash,
            version: getLatestVersion(consortiumId) + 1,
            accuracy: accuracy,
            trainedAt: block.timestamp,
            contributors: contributors
        });

        emit ModelRegistered(modelId, consortiumId, modelType, accuracy);
        return modelId;
    }
}
```

#### ComputationVerifierV2.sol

```solidity
// contracts/src/v2/ComputationVerifierV2.sol

contract ComputationVerifierV2 {

    struct DataContribution {
        bytes32 consortiumId;
        address contributor;
        bytes32 dataHash;           // SHA256 de los datos cifrados
        uint256 recordCount;
        uint256 featureCount;
        uint256 timestamp;
    }

    function recordContribution(
        bytes32 consortiumId,
        bytes32 dataHash,
        uint256 recordCount,
        uint256 featureCount
    ) external onlyMember(consortiumId) {
        contributions[consortiumId][msg.sender] = DataContribution({
            consortiumId: consortiumId,
            contributor: msg.sender,
            dataHash: dataHash,
            recordCount: recordCount,
            featureCount: featureCount,
            timestamp: block.timestamp
        });

        emit ContributionRecorded(consortiumId, msg.sender, dataHash, recordCount);
    }

    function verifyContribution(
        bytes32 consortiumId,
        address contributor,
        bytes32 expectedHash
    ) external view returns (bool) {
        return contributions[consortiumId][contributor].dataHash == expectedHash;
    }
}
```

### Flujo de Transacciones

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUJO DE GOBERNANZA BLOCKCHAIN                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. CREAR CONSORCIO                                             │
│     ┌────────────────────────────────────────────────────────┐  │
│     │ TX: createConsortium("LatAm Fraud Consortium", [A,B,C])│  │
│     │ Gas: ~150,000                                          │  │
│     │ Event: ConsortiumCreated(id, name, members)            │  │
│     └────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  2. REGISTRAR CONTRIBUCIONES                                    │
│     ┌────────────────────────────────────────────────────────┐  │
│     │ TX (Bank A): recordContribution(id, hash_A, 400, 10)   │  │
│     │ TX (Bank B): recordContribution(id, hash_B, 300, 10)   │  │
│     │ TX (Bank C): recordContribution(id, hash_C, 300, 10)   │  │
│     └────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  3. CREAR PROPUESTA                                             │
│     ┌────────────────────────────────────────────────────────┐  │
│     │ TX: createProposal(consortiumId, START_TRAINING, ...)  │  │
│     │ Event: ProposalCreated(proposalId, type, deadlines)    │  │
│     └────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  4. COMMIT VOTES (24h window)                                   │
│     ┌────────────────────────────────────────────────────────┐  │
│     │ TX (A): commitVote(proposalId, hash(YES + salt_A))     │  │
│     │ TX (B): commitVote(proposalId, hash(YES + salt_B))     │  │
│     │ TX (C): commitVote(proposalId, hash(YES + salt_C))     │  │
│     │ (Votos ocultos - nadie sabe cómo votaron los demás)    │  │
│     └────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  5. REVEAL VOTES (24h window)                                   │
│     ┌────────────────────────────────────────────────────────┐  │
│     │ TX (A): revealVote(proposalId, true, salt_A) → Verified│  │
│     │ TX (B): revealVote(proposalId, true, salt_B) → Verified│  │
│     │ TX (C): revealVote(proposalId, true, salt_C) → Verified│  │
│     │ Result: 3 YES, 0 NO → 100% > 51% → PASSED              │  │
│     └────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  6. EJECUTAR PROPUESTA                                          │
│     ┌────────────────────────────────────────────────────────┐  │
│     │ TX: executeProposal(proposalId)                        │  │
│     │ → Autoriza entrenamiento del modelo                    │  │
│     │ Event: ProposalExecuted(proposalId, result)            │  │
│     └────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  7. REGISTRAR MODELO                                            │
│     ┌────────────────────────────────────────────────────────┐  │
│     │ TX: registerModel(consortiumId, "LogReg", hash, 9450)  │  │
│     │ Event: ModelRegistered(modelId, accuracy=94.50%)       │  │
│     └────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Componente 3: Backend (Django)

### Apps Principales

```
backend_django/apps/
├── consortiums/          # Gestión de consorcios
│   ├── models.py         # Consortium, Membership
│   ├── views.py          # CRUD API
│   └── services.py       # Lógica de negocio
│
├── governance/           # Votación y propuestas
│   ├── models.py         # Proposal, Vote
│   ├── views.py          # Commit/Reveal endpoints
│   └── blockchain.py     # Interacción con smart contracts
│
├── ml_models/            # Modelos de ML
│   ├── models.py         # MLModel, TrainingJob
│   ├── views.py          # Train/Predict API
│   └── fhe_training.py   # Entrenamiento FHE
│
├── data_quality/         # Validación de datos
│   └── assessment.py     # Métricas de calidad
│
├── compliance/           # Cumplimiento regulatorio
│   └── gdpr.py           # GDPR checks
│
└── competitive_insights/ # Análisis competitivo
    └── reports.py        # Generación de reportes
```

### API Endpoints

```yaml
# Consortiums
POST   /api/v1/consortiums/                    # Crear consorcio
GET    /api/v1/consortiums/{id}/               # Obtener detalles
POST   /api/v1/consortiums/{id}/contribute/    # Contribuir datos

# Governance
POST   /api/v1/governance/proposals/           # Crear propuesta
POST   /api/v1/governance/proposals/{id}/commit/   # Commit vote
POST   /api/v1/governance/proposals/{id}/reveal/   # Reveal vote
POST   /api/v1/governance/proposals/{id}/execute/  # Ejecutar

# ML Models
POST   /api/v1/models/train/                   # Iniciar entrenamiento
GET    /api/v1/models/{id}/                    # Obtener modelo
POST   /api/v1/models/{id}/predict/            # Hacer predicción

# Data Quality
POST   /api/v1/data-quality/assess/            # Evaluar calidad
GET    /api/v1/data-quality/report/{id}/       # Obtener reporte
```

---

## Seguridad

### Niveles de Protección

| Capa | Mecanismo | Propósito |
|------|-----------|-----------|
| Datos | FHE (CKKS 128-bit) | Cifrado homomórfico |
| Votación | Commit-Reveal | Prevenir front-running |
| Transacciones | Arbitrum L2 | Inmutabilidad |
| API | JWT + Rate Limiting | Autenticación |
| Secrets | OpenBao (Vault) | Gestión de claves |

### Modelo de Amenazas

```
┌─────────────────────────────────────────────────────────────────┐
│                      MODELO DE AMENAZAS                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  AMENAZA 1: Exposición de datos                                 │
│  ├── Mitigación: FHE - datos siempre cifrados                   │
│  └── Verificación: Auditoría de código TenSEAL                  │
│                                                                  │
│  AMENAZA 2: Front-running en votación                           │
│  ├── Mitigación: Commit-reveal scheme                           │
│  └── Verificación: Tests de smart contracts                     │
│                                                                  │
│  AMENAZA 3: Manipulación de modelo                              │
│  ├── Mitigación: Hash de pesos en blockchain                    │
│  └── Verificación: ComputationVerifier contract                 │
│                                                                  │
│  AMENAZA 4: Acceso no autorizado                                │
│  ├── Mitigación: JWT + RBAC + Membership checks                 │
│  └── Verificación: Penetration testing                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Deployment

### Testnet (Actual)

```yaml
Network: Arbitrum Sepolia
Chain ID: 421614
RPC: https://sepolia-rollup.arbitrum.io/rpc
Explorer: https://sepolia.arbiscan.io

Contracts:
  Governance: 0xda52326d106A91A1F22A0c41Be2dc1F531C01F11
  ModelRegistry: 0x1296cCeF7803Bff51FB690afCFc586E7012417b8
  Verifier: 0xa5f04E0aefe55173C91b949Aa2385f0228dd2921

Backend: Django 5.2 LTS (Docker)
Frontend: React + Vite (Vercel)
```

### Mainnet (Futuro)

```yaml
Network: Arbitrum One
Chain ID: 42161
RPC: https://arb1.arbitrum.io/rpc
Explorer: https://arbiscan.io

Requisitos antes de mainnet:
- [ ] Auditoría externa de smart contracts
- [ ] Penetration testing
- [ ] Multi-sig para admin
- [ ] Timelock para upgrades
- [ ] SOC 2 Type II
```

---

## Referencias

- **TenSEAL**: https://github.com/OpenMined/TenSEAL
- **CKKS Paper**: https://eprint.iacr.org/2016/421
- **Arbitrum Docs**: https://docs.arbitrum.io
- **Commit-Reveal**: https://medium.com/gitcoin/commit-reveal-scheme-on-ethereum-25d1d1a25428

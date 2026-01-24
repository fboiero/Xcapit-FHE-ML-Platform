# Xcapit FHE-ML Platform - Blockchain Services Roadmap

## Overview

Este documento define la evolución de los servicios blockchain para la plataforma Xcapit FHE-ML, desde MVP hasta producción enterprise.

---

## Phase 1: Foundation (Current) ✅

### Contratos Implementados
- [x] ConsortiumGovernanceV2 - Gestión de consorcios y votación
- [x] ModelRegistryV2 - Registro y verificación de modelos ML
- [x] ComputationVerifierV2 - Auditoría de computaciones FHE

### Características
- [x] Security hardening (ReentrancyGuard, Pausable, Ownable2Step)
- [x] Custom errors para eficiencia de gas
- [x] O(1) verification con indexed mappings
- [x] Pull-over-push para distribución de rewards
- [x] 59 tests con fuzz testing

### Target Network
- Arbitrum Sepolia (testnet)

---

## Phase 2: Vault Integration (Q1 2026)

### Objetivos
- [ ] Integración de claves privadas con OpenBao
- [ ] Deployment scripts seguros
- [ ] Firma de transacciones desde backend Django
- [ ] Key rotation support

### Componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                        OpenBao Vault                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ xcapit/blockchain│  │ xcapit/blockchain│  │ xcapit/blockchain│ │
│  │ /deployer       │  │ /consortium-signer│ │ /verifier       │ │
│  │                 │  │                   │  │                 │ │
│  │ private_key     │  │ private_key       │  │ private_key     │ │
│  │ address         │  │ address           │  │ address         │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Django Backend                               │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              apps/blockchain/services.py                     ││
│  │  - BlockchainService (web3.py)                              ││
│  │  - get_signer_from_vault()                                  ││
│  │  - sign_and_send_transaction()                              ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Arbitrum Network                              │
│  ┌─────────────┐ ┌─────────────┐ ┌────────────────────────────┐│
│  │Consortium   │ │ModelRegistry│ │ComputationVerifier         ││
│  │GovernanceV2 │ │V2           │ │V2                          ││
│  └─────────────┘ └─────────────┘ └────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Secret Paths
| Path | Descripción | Keys |
|------|-------------|------|
| `xcapit/blockchain/deployer` | Deploy de contratos | `private_key`, `address` |
| `xcapit/blockchain/consortium-signer` | Operaciones de consorcio | `private_key`, `address` |
| `xcapit/blockchain/verifier` | Verificación de computaciones | `private_key`, `address` |
| `xcapit/blockchain/contracts` | Direcciones deployadas | `governance`, `registry`, `verifier` |
| `xcapit/blockchain/rpc` | RPC endpoints | `arbitrum_url`, `arbitrum_sepolia_url` |

---

## Phase 3: Testnet Deployment (Q2 2026)

### Objetivos
- [ ] Deploy en Arbitrum Sepolia
- [ ] Integration tests end-to-end
- [ ] Monitoring y alertas
- [ ] Gas optimization profiling

### Deployment Checklist
```
[ ] Verificar fondos en deployer wallet
[ ] Deploy ConsortiumGovernanceV2
[ ] Deploy ModelRegistryV2
[ ] Deploy ComputationVerifierV2
[ ] Verificar contratos en Arbiscan
[ ] Configurar trusted verifiers
[ ] Test full workflow:
    [ ] Create consortium
    [ ] Add members
    [ ] Record contributions
    [ ] Create & execute proposal
    [ ] Allocate & withdraw rewards
    [ ] Register model
    [ ] Save checkpoints
    [ ] Register computations
    [ ] Verify outputs
```

### Monitoring
- [ ] Grafana dashboard para métricas on-chain
- [ ] Alertas para eventos críticos (Paused, OwnershipTransferred)
- [ ] Gas cost tracking

---

## Phase 4: Mainnet Beta (Q3 2026)

### Objetivos
- [ ] Deploy en Arbitrum One
- [ ] Auditoría de seguridad externa
- [ ] Multi-sig para ownership
- [ ] Rate limiting en backend

### Security Hardening
- [ ] Auditoría por firma reconocida (Trail of Bits, OpenZeppelin, etc.)
- [ ] Bug bounty program
- [ ] Timelock para operaciones admin
- [ ] Multi-sig wallet (Gnosis Safe) para ownership

### Contratos Adicionales (si necesario)
```solidity
// TimelockController para operaciones admin con delay
contract XcapitTimelock is TimelockController { ... }

// Multi-sig integration
contract XcapitGovernanceMultisig { ... }
```

---

## Phase 5: Production & Scale (Q4 2026)

### Objetivos
- [ ] Proxy patterns para upgradability
- [ ] Cross-chain support (Optimism, Base)
- [ ] Advanced governance (quadratic voting)
- [ ] Token incentives (opcional)

### Upgradability Pattern
```
┌─────────────────────────────────────────────────────────────────┐
│                    Proxy Architecture                            │
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │   Proxy     │───▶│Implementation│    │ProxyAdmin           │ │
│  │(UUPS/Trans.)│    │V2            │    │(TimelockController) │ │
│  └─────────────┘    └─────────────┘    └─────────────────────┘ │
│        │                                         │              │
│        │            ┌─────────────┐              │              │
│        │            │Implementation│◀────────────┘              │
│        └───────────▶│V3 (upgrade) │                             │
│                     └─────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

### Cross-Chain Support
- Arbitrum One (primary)
- Optimism (secondary)
- Base (secondary)
- Bridge contracts para sincronización de estado

---

## Phase 6: Enterprise Features (2027)

### Objetivos
- [ ] Private/permissioned chains option
- [ ] Compliance reporting on-chain
- [ ] SLA guarantees con staking
- [ ] DAO governance para plataforma

### Enterprise Contracts
```solidity
// Compliance reporting
contract ComplianceRegistry {
    // GDPR/LGPD data access logs
    // Audit trail export
    // Regulatory reporting
}

// SLA enforcement
contract SLAEnforcement {
    // Uptime guarantees
    // Performance metrics
    // Penalty/reward distribution
}

// Platform DAO
contract XcapitDAO {
    // Protocol governance
    // Fee structure voting
    // Feature proposals
}
```

---

## Technical Decisions

### Why Arbitrum?
1. **Low gas costs** - 10-100x cheaper que Ethereum mainnet
2. **EVM compatible** - Mismo tooling (Foundry, Hardhat)
3. **Security** - Inherits Ethereum security via rollup
4. **Ecosystem** - DeFi y tooling maduro

### Why Not ZK Rollups?
- Complejidad adicional sin beneficio claro para nuestro caso
- Arbitrum Nitro suficiente para throughput esperado
- Opcionalidad futura: podemos migrar si necesario

### Solidity Version: 0.8.20
- Stable y well-tested
- Compatible con OpenZeppelin v5
- Sin breaking changes recientes

---

## Metrics & KPIs

### Phase 2-3 (Testnet)
| Metric | Target |
|--------|--------|
| Test coverage | >90% |
| Gas per operation | <500k |
| Deployment success | 100% |
| Integration test pass | 100% |

### Phase 4-5 (Mainnet)
| Metric | Target |
|--------|--------|
| Uptime | 99.9% |
| Transaction success rate | >99% |
| Average confirmation time | <30s |
| Monthly active consortiums | >10 |

### Phase 6 (Enterprise)
| Metric | Target |
|--------|--------|
| Enterprise clients | >5 |
| TVL in rewards pool | >$100k |
| Daily transactions | >1000 |

---

## Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Smart contract bug | Medium | Critical | Audits, extensive testing, bug bounty |
| Private key compromise | Low | Critical | Vault integration, multi-sig, key rotation |
| Network congestion | Medium | Medium | Gas estimation, retry logic, L2 fallback |
| Regulatory changes | Low | High | Compliance-first design, legal review |
| Bridge exploit (cross-chain) | Low | High | Delay cross-chain until Phase 6, use proven bridges |

---

## Resources

### Documentation
- [Foundry Book](https://book.getfoundry.sh/)
- [Arbitrum Docs](https://docs.arbitrum.io/)
- [OpenZeppelin Contracts](https://docs.openzeppelin.com/contracts/)

### Tools
- Foundry (forge, cast, anvil)
- Arbiscan API
- The Graph (indexing)
- Tenderly (debugging)

### Team Allocation
| Role | Phase 2-3 | Phase 4-5 | Phase 6 |
|------|-----------|-----------|---------|
| Smart Contract Dev | 1 | 1-2 | 2 |
| Backend Integration | 1 | 1 | 1 |
| Security Auditor | External | External | Internal + External |
| DevOps | 0.5 | 1 | 1 |

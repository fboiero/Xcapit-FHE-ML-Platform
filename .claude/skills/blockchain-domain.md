# Blockchain Domain Knowledge

## Network Configuration

| Environment | Network | Chain ID | Config Key |
|-------------|---------|----------|------------|
| Testnet | Arbitrum Sepolia | 421614 | `BLOCKCHAIN_ENV=testnet` |
| Mainnet | Arbitrum One | 42161 | `BLOCKCHAIN_ENV=mainnet` |

Contract addresses stored in `config/settings.py` under `BLOCKCHAIN_*` keys.

## Smart Contracts (`contracts/src/v2/`)

| Contract | Purpose |
|----------|---------|
| `ConsortiumGovernance.sol` | Member management, proposal creation, voting |
| `ModelRegistry.sol` | Model versioning, on-chain verification hashes |
| `ComputationVerifier.sol` | Zero-knowledge proof verification |

### Development (Foundry)

```bash
cd contracts
forge build           # Compile contracts
forge test -vvv       # Run tests with verbosity
forge coverage        # Coverage report
```

## Django Blockchain Services (`apps/blockchain/`)

### Service Classes (`services.py`)

| Service | Responsibility |
|---------|----------------|
| `BlockchainService` | Base Web3 connection, transaction management |
| `ConsortiumService` | Consortium contract interactions |
| `ModelRegistryService` | Model registration and verification |
| `ComputationVerifierService` | Proof submission and verification |

### Key Management (`secrets.py`)

- Production: OpenBao/Vault integration via `hvac` SDK
- Development: Environment variables
- Private keys NEVER stored in code or config files

### Resilience (`resilience.py`)

- Retry logic with exponential backoff (tenacity)
- Circuit breaker for blockchain RPC failures
- Graceful degradation when blockchain is unavailable

## Celery Integration

Blockchain operations are async via Celery tasks (`apps/consortiums/tasks.py`):

```python
# Queue: "blockchain"
register_contribution_blockchain.delay(contribution_id)
register_training_result_blockchain.delay(training_result_id)
```

Celery routing in `config/settings.py`:
```python
CELERY_TASK_ROUTES = {
    "apps.consortiums.tasks.register_*_blockchain": {"queue": "blockchain"},
}
```

## Audit Trail Pattern

Every significant operation gets blockchain registration:
1. Consortium creation → on-chain consortium record
2. Member contribution → on-chain contribution proof
3. Training completion → on-chain training result hash
4. Model versioning → on-chain model hash

## Coverage Note

`blockchain/services.py` is at 67% coverage due to Web3 mocking complexity. These tests require careful mocking of blockchain RPC responses and transaction receipts.

# Smart Contracts

## Foundry Setup

| Setting | Value |
|---------|-------|
| Solidity | `0.8.20` (fixed pragma) |
| EVM | `cancun` (Arbitrum) |
| Optimizer | 200 runs (1000 in production profile) |
| Fuzz | 256 runs (100 in CI) |
| Libs | OpenZeppelin, forge-std |

```bash
cd contracts
forge build          # Compile
forge test -vvv      # Run tests
forge coverage       # Coverage report
forge fmt            # Format
```

## Contracts (`contracts/src/v2/`)

All inherit `Ownable2Step`, `Pausable`, `ReentrancyGuard`. Custom errors (gas-efficient).

### ModelRegistryV2

On-chain registry for FHE-ML model verification.

| Function | Access | Purpose |
|----------|--------|---------|
| `registerModel(modelType, version)` | anyone | Register model → `bytes32 modelId` |
| `saveCheckpoint(modelId, epoch, weightsHash, metricsHash)` | owner/authorized | Save training checkpoint |
| `startTraining(modelId, datasetHash)` | owner/authorized | Start training run |
| `completeTraining(modelId, runIndex, totalEpochs, finalWeightsHash)` | owner/authorized | Complete training |
| `verifyModel(modelId)` | trustedVerifier | Mark verified (not own model) |
| `verifyCheckpoint(modelId, epoch, weightsHash)` | view | O(1) verification |

### ComputationVerifierV2

Audit trail for FHE computation proofs.

| Function | Access | Purpose |
|----------|--------|---------|
| `registerComputation(modelId, inputHash, outputHash, proofHash)` | anyone | Register computation |
| `registerBatch(modelId, inputHashes[], outputHashes[])` | anyone | Batch with Merkle root (max 1000) |
| `verifyOutput(modelId, inputHash, outputHash)` | view | O(1) output verification |

### ConsortiumGovernanceV2

DAO-style governance with commit-reveal voting.

| Function | Access | Purpose |
|----------|--------|---------|
| `createConsortium(name, quorum, votingDuration, modelConfigHash)` | anyone | Create consortium |
| `addMember(consortiumId, newMember)` | owner | Add member (max 100) |
| `recordContribution(consortiumId, recordCount, featureCount, dataHash, checksumHash)` | member | Record data contribution |
| `createProposal(consortiumId, proposalType, data)` | member | Create proposal (7 types) |
| `commitVote(proposalId, commitHash)` | member | Commit hidden vote (60% of duration) |
| `revealVote(proposalId, support, salt)` | voter | Reveal vote (40% of duration) |
| `executeProposal(proposalId)` | anyone | Execute after deadline |
| `allocateRewards(consortiumId)` | owner + payable | Distribute ETH by weight |
| `withdrawRewards(consortiumId)` | member | Pull-pattern withdrawal |

Proposal types: `AddMember`, `RemoveMember`, `ChangeModel`, `StartTraining`, `DistributeRewards`, `UpdateConfig`, `Dissolve`.

## Deployment

Network: **Arbitrum Sepolia** (chain 421614).

| Contract | Address |
|----------|---------|
| ConsortiumGovernanceV2 | `0xda52326d106A91A1F22A0c41Be2dc1F531C01F11` |
| ModelRegistryV2 | `0x1296cCeF7803Bff51FB690afCFc586E7012417b8` |
| ComputationVerifierV2 | `0xa5f04E0aefe55173C91b949Aa2385f0228dd2921` |

```bash
forge script script/Deploy.s.sol --rpc-url $ARBITRUM_SEPOLIA_RPC_URL --broadcast --verify
```

## Test Patterns

| File | Coverage |
|------|----------|
| `ModelRegistryV2.t.sol` | Registration, checkpoints, training, verification, fuzz |
| `ComputationVerifierV2.t.sol` | Computation, batch, O(1) verification, fuzz |
| `ConsortiumGovernanceV2.t.sol` | CRUD, voting, rewards, audit trail, fuzz |
| `SecurityEdgeCases.t.sol` | Reentrancy, Sybil, timing, DoS, rounding |

```solidity
// Revert tests
vm.expectRevert(abi.encodeWithSelector(ModelRegistryV2.Unauthorized.selector, user1));

// Fuzz tests
function testFuzz_RegisterModel(string memory modelType) public {
    vm.assume(bytes(modelType).length > 0);
}

// Time manipulation
vm.warp(block.timestamp + 40 minutes);

// Impersonation
vm.prank(attacker);
```

## Django Integration

`backend_django/apps/blockchain/services.py`:

```
BlockchainService (base)
  ├── ConsortiumService        → ConsortiumGovernanceV2
  ├── ModelRegistryService     → ModelRegistryV2
  └── ComputationVerifierService → ComputationVerifierV2
```

- ABI from Foundry artifacts (`contracts/out/`)
- Web3 lazy-init, PoA middleware for Arbitrum
- Private keys from OpenBao/Vault (never in code)
- Circuit breaker + retry (3 connect, 2 send)
- Blockchain writes via Celery tasks (`blockchain` queue)
- Read operations are synchronous view calls

## Security

- **Reentrancy**: `ReentrancyGuard` + pull-over-push for rewards
- **Access**: `Ownable2Step`, trusted verifier system
- **DoS**: `MAX_MEMBERS=100`, `MAX_BATCH_SIZE=1000`
- **Vote manipulation**: Commit-reveal + contribution-weighted voting
- **Emergency**: `Pausable` on all contracts
- **Gas**: Custom errors, `unchecked` counters, `via_ir` optimizer

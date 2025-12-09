# Smart Contract Security Audit Report

**Client:** Client
**Contract:** src/v2/ModelRegistryV2.sol
**Auditor:** MIESC Security
**Date:** 2026-01-24
**Version:** 4.3.7

---

## Executive Summary

This security audit was conducted by MIESC Security on behalf of Client to evaluate the security posture of src/v2/ModelRegistryV2.sol.

### Audit Scope

| Item | Details |
|------|---------|
| Repository | Local Analysis |
| Commit | N/A |
| Files Analyzed | 1 |
| Lines of Code | N/A |
| Audit Duration | N/A |

### Key Findings

| Severity | Count | Status |
|----------|-------|--------|
| Critical | 0 | ✅ None Found |
| High | 0 | ✅ None Found |
| Medium | 1 | ℹ️ 1 Issue |
| Low | 2 | ℹ️ 2 Issues |
| Informational | 2 | ℹ️ 2 Issues |

### Overall Risk Assessment

**Risk Level:** LOW

**LOW RISK**: Minor issues were identified that should be addressed to improve code quality and security posture.


---

## Tools Execution Summary

**Total Tools Executed:** 4 | **Success:** 3 | **Failed:** 1

| Tool | Status | Duration | Findings | Layer |
|------|--------|----------|----------|-------|

| slither | ✅ Success | N/A | 5 | Layer 1: Static Analysis |

| aderyn | ⚠️ Error | N/A | 0 | Layer 1: Static Analysis |

| solhint | ✅ Success | N/A | 0 | Layer 1: Static Analysis |

| mythril | ✅ Success | N/A | 0 | Layer 3: Symbolic Execution |


---

## Layer Coverage Analysis

MIESC employs a 9-layer defense-in-depth approach. The following table shows the coverage achieved in this audit:

| Layer | Tools Executed | Success | Failed | Findings | Status |
|-------|----------------|---------|--------|----------|--------|

| Layer 1: Static Analysis | slither, aderyn, solhint | 2 | 1 | 5 | ⚠️ Partial |

| Layer 3: Symbolic Execution | mythril | 1 | 0 | 0 | ✅ Complete |


---

## Findings


### F-001. incorrect-equality

| Property | Value |
|----------|-------|
| Severity | medium |
| Category | incorrect-equality |
| Location | ModelRegistryV2.sol:154 (modelExists) |
| Status | open |
| Tool | slither |

#### Description

[ModelRegistryV2.modelExists(bytes32)](../../../../../../private/var/folders/38/s7h03tpx0h98shwqgy4_c7lw0000gq/T/miesc_slither_j3i0u6x4/ModelRegistryV2.sol#L154-L157) uses a dangerous strict equality:
	- [models[modelId].createdAt == 0](../../../../../../private/var/folders/38/s7h03tpx0h98shwqgy4_c7lw0000gq/T/miesc_slither_j3i0u6x4/ModelRegistryV2.sol#L155)


#### Impact

Limited financial impact or requires specific conditions to exploit.

#### Proof of Concept

```solidity
// No PoC provided
```

#### Recommendation

Review and fix the vulnerability

#### References



---


### F-002. missing-zero-check

| Property | Value |
|----------|-------|
| Severity | low |
| Category | missing-zero-check |
| Location | lib/openzeppelin-contracts/contracts/access/Ownable2Step.sol:43 (newOwner) |
| Status | open |
| Tool | slither |

#### Description

[Ownable2Step.transferOwnership(address).newOwner](lib/openzeppelin-contracts/contracts/access/Ownable2Step.sol#L43) lacks a zero-check on :
		- [_pendingOwner = newOwner](lib/openzeppelin-contracts/contracts/access/Ownable2Step.sol#L44)


#### Impact

Minor impact on contract functionality or gas efficiency.

#### Proof of Concept

```solidity
// No PoC provided
```

#### Recommendation

Review and fix the vulnerability

#### References



---


### F-003. timestamp

| Property | Value |
|----------|-------|
| Severity | low |
| Category | SC08: Bad Randomness / Front-Running |
| Location | ModelRegistryV2.sol:491 (isAuthorized) |
| Status | open |
| Tool | slither |

#### Description

[ModelRegistryV2.isAuthorized(bytes32,address)](../../../../../../private/var/folders/38/s7h03tpx0h98shwqgy4_c7lw0000gq/T/miesc_slither_j3i0u6x4/ModelRegistryV2.sol#L491-L493) uses timestamp for comparisons
	Dangerous comparisons:
	- [models[modelId].owner == addr || authorized[modelId][addr]](../../../../../../private/var/folders/38/s7h03tpx0h98shwqgy4_c7lw0000gq/T/miesc_slither_j3i0u6x4/ModelRegistryV2.sol#L492)


#### Impact

Minor impact on contract functionality or gas efficiency.

#### Proof of Concept

```solidity
// No PoC provided
```

#### Recommendation

Review and fix the vulnerability

#### References



---


### F-004. assembly

| Property | Value |
|----------|-------|
| Severity | info |
| Category | assembly |
| Location | lib/openzeppelin-contracts/contracts/utils/StorageSlot.sol:66 (getAddressSlot) |
| Status | open |
| Tool | slither |

#### Description

[StorageSlot.getAddressSlot(bytes32)](lib/openzeppelin-contracts/contracts/utils/StorageSlot.sol#L66-L70) uses assembly
	- [INLINE ASM](lib/openzeppelin-contracts/contracts/utils/StorageSlot.sol#L67-L69)


#### Impact

Informational finding for code quality improvement.

#### Proof of Concept

```solidity
// No PoC provided
```

#### Recommendation

Review and fix the vulnerability

#### References



---


### F-005. assembly

| Property | Value |
|----------|-------|
| Severity | info |
| Category | assembly |
| Location | lib/openzeppelin-contracts/contracts/utils/StorageSlot.sol:102 (getInt256Slot) |
| Status | open |
| Tool | slither |

#### Description

[StorageSlot.getInt256Slot(bytes32)](lib/openzeppelin-contracts/contracts/utils/StorageSlot.sol#L102-L106) uses assembly
	- [INLINE ASM](lib/openzeppelin-contracts/contracts/utils/StorageSlot.sol#L103-L105)


#### Impact

Informational finding for code quality improvement.

#### Proof of Concept

```solidity
// No PoC provided
```

#### Recommendation

Review and fix the vulnerability

#### References



---







---

## Methodology

This audit employed MIESC's 9-layer defense-in-depth methodology:

| Layer | Category | Tools Used |
|-------|----------|------------|
| 1 | Static Analysis | slither, aderyn, solhint |
| 2 | Dynamic Testing | echidna, medusa, foundry |
| 3 | Symbolic Execution | mythril, manticore, halmos |
| 4 | Formal Verification | certora, smtchecker |
| 5 | Property Testing | propertygpt |
| 6 | AI/LLM Analysis | smartllm, gptscan, llmsmartaudit |
| 7 | Pattern Recognition | dagnn, smartbugs_ml |
| 8 | DeFi Security | defi, mev_detector |
| 9 | Advanced Detection | gas_analyzer, threat_model |

### Audit Process

1. **Code Review**: Manual inspection of smart contract source code
2. **Automated Analysis**: Multi-tool scanning across 9 security layers
3. **AI Correlation**: Cross-tool finding correlation and false positive reduction
4. **Verification**: Manual verification of all findings
5. **Remediation Review**: Review of fixes (if applicable)

---

## Compliance Mapping

### SWC Registry

| SWC ID | Title | Status |
|--------|-------|--------|


### OWASP Smart Contract Top 10

| ID | Category | Findings |
|----|----------|----------|


---

## Appendix A: Tool Outputs



---

## Appendix B: Files Analyzed

| File | Lines | Findings |
|------|-------|----------|

| src/v2/ModelRegistryV2.sol | N/A | 5 |


---

## Disclaimer

This audit report is provided "as is" with no guarantees of completeness or accuracy. The auditors have made every effort to identify security vulnerabilities, but cannot guarantee that all issues have been found. Smart contract security is an evolving field, and new vulnerabilities may be discovered after this audit. The client is responsible for addressing the findings and conducting additional security measures as appropriate.



---

**Powered by [MIESC](https://github.com/fboiero/MIESC)** - Multi-layer Intelligent Evaluation for Smart Contracts

*Report generated: 2026-01-24 18:15:10*
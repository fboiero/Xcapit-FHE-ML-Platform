"""Zero-Knowledge Proof module for the Xcapit FHE-ML SDK.

Enables consortium members to prove they contributed valid data without
revealing the data itself.  Proofs can be verified off-chain or serialized
for submission to an on-chain verifier contract on Arbitrum.

Key components:

- :class:`ZKProver` -- High-level API for creating zero-knowledge proofs.
- :class:`ZKVerifier` -- High-level API for verifying proofs.
- :class:`PedersenCommitment` -- Pedersen commitment scheme (g^v * h^r mod p).
- :class:`SchnorrProof` -- Schnorr identification protocol (Fiat-Shamir).
- :class:`ContributionProof` -- Prove data contribution properties.
- :class:`OnChainProof` -- Proof container for on-chain submission.
- :class:`ProofSerializer` -- Serialize proofs for smart contracts.
- :class:`ArithmeticCircuit` -- Circuit representation for range/sum checks.
- :class:`Gate` / :class:`Wire` -- Circuit building blocks.
"""

from .circuits import ArithmeticCircuit, Gate, Wire
from .on_chain import OnChainProof, ProofSerializer
from .proofs import (
    ContributionProof,
    PedersenCommitment,
    SchnorrProof,
    ZKProver,
    ZKVerifier,
)

__all__ = [
    "ZKProver",
    "ZKVerifier",
    "PedersenCommitment",
    "SchnorrProof",
    "ContributionProof",
    "OnChainProof",
    "ProofSerializer",
    "ArithmeticCircuit",
    "Gate",
    "Wire",
]

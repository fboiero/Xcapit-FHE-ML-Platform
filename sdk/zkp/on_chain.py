"""Prepare ZK proofs for on-chain verification.

Provides serialization and encoding utilities to transform off-chain
zero-knowledge proofs into formats suitable for submission to Solidity
smart contracts deployed on EVM-compatible networks (e.g. Arbitrum).

Key components:

- :class:`OnChainProof` — Immutable container for a proof prepared for
  on-chain submission, including the proof hash, serialized data,
  verifier inputs, and creation timestamp.
- :class:`ProofSerializer` — Serializes proof dictionaries to compact
  byte representations and generates Solidity-compatible calldata
  dictionaries for smart contract function calls.

Only Python stdlib is used (``hashlib``, ``json``, ``struct``).
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any, Dict

# ============================================================================
# OnChainProof dataclass
# ============================================================================


@dataclass(frozen=True)
class OnChainProof:
    """A zero-knowledge proof prepared for on-chain verification.

    This is an immutable container holding all data needed to submit a
    proof to a Solidity verifier contract.

    Attributes:
        proof_hash: SHA-256 hash of the serialized proof (32 bytes, hex).
            Used as the unique on-chain identifier for the proof.
        proof_data: The serialized proof payload (hex-encoded bytes).
            Contains commitments, Schnorr responses, and blinding factors.
        verifier_inputs: Public inputs required by the on-chain verifier.
            These are the values the smart contract needs to reconstruct
            the verification equation.
        timestamp: Unix timestamp (seconds since epoch) of proof creation.
    """

    proof_hash: str
    proof_data: str
    verifier_inputs: Dict[str, Any]
    timestamp: int

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the on-chain proof to a plain dictionary.

        Returns:
            Dictionary suitable for JSON serialization or storage.
        """
        return {
            "proof_hash": self.proof_hash,
            "proof_data": self.proof_data,
            "verifier_inputs": self.verifier_inputs,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> OnChainProof:
        """Reconstruct an on-chain proof from a dictionary.

        Args:
            data: Dictionary with keys ``proof_hash``, ``proof_data``,
                ``verifier_inputs``, and ``timestamp``.

        Returns:
            Reconstructed ``OnChainProof`` instance.

        Raises:
            KeyError: If required fields are missing.
            TypeError: If field types are wrong.
        """
        return cls(
            proof_hash=str(data["proof_hash"]),
            proof_data=str(data["proof_data"]),
            verifier_inputs=dict(data["verifier_inputs"]),
            timestamp=int(data["timestamp"]),
        )


# ============================================================================
# ProofSerializer
# ============================================================================


class ProofSerializer:
    """Serialize ZK proofs for smart contract submission.

    Transforms proof dictionaries (produced by :class:`ZKProver`,
    :class:`ContributionProof`, etc.) into compact byte representations
    and Solidity-compatible calldata.

    The serialization format is deterministic: the same proof always
    produces the same byte output, which is critical for on-chain
    verification of proof hashes.

    Example::

        from sdk.zkp import ZKProver
        from sdk.zkp.on_chain import ProofSerializer

        prover = ZKProver("member-42")
        proof = prover.prove_contribution(data_bytes)

        serializer = ProofSerializer()
        raw_bytes = serializer.serialize(proof)
        calldata = serializer.to_solidity_calldata(proof)
    """

    @staticmethod
    def serialize(proof: Dict[str, Any]) -> bytes:
        """Serialize a proof dictionary to a deterministic byte sequence.

        The proof is serialized as canonical JSON (sorted keys, no extra
        whitespace) encoded as UTF-8.  This produces a deterministic
        output suitable for hashing and on-chain storage.

        Args:
            proof: Proof dictionary from any of the ZKP proof generators.

        Returns:
            Deterministic byte representation of the proof.
        """
        canonical = json.dumps(proof, sort_keys=True, separators=(",", ":"), default=str)
        return canonical.encode("utf-8")

    @staticmethod
    def _compute_proof_hash(serialized: bytes) -> str:
        """Compute the SHA-256 hash of serialized proof bytes.

        Args:
            serialized: Output of :meth:`serialize`.

        Returns:
            Hex-encoded 32-byte hash string.
        """
        return hashlib.sha256(serialized).hexdigest()

    @staticmethod
    def _extract_verifier_inputs(proof: Dict[str, Any]) -> Dict[str, Any]:
        """Extract public inputs needed by the on-chain verifier.

        Collects all information the smart contract needs to verify the
        proof without access to private witness data.

        Args:
            proof: Original proof dictionary.

        Returns:
            Dictionary of public verifier inputs.
        """
        verifier_inputs: Dict[str, Any] = {}

        # Public inputs from the proof (e.g. data_hash, n_samples, n_features).
        if "public_inputs" in proof:
            verifier_inputs["public_inputs"] = proof["public_inputs"]

        # Commitments are public.
        if "commitments" in proof:
            verifier_inputs["commitments"] = proof["commitments"]

        # Binding challenge (can be recomputed by verifier).
        if "binding_challenge" in proof:
            verifier_inputs["binding_challenge"] = proof["binding_challenge"]

        # Proof type and version for routing.
        if "proof_type" in proof:
            verifier_inputs["proof_type"] = proof["proof_type"]
        if "version" in proof:
            verifier_inputs["version"] = proof["version"]

        # Contributor / prover identity.
        if "contributor_id" in proof:
            verifier_inputs["contributor_id"] = proof["contributor_id"]
        elif "prover_id" in proof:
            verifier_inputs["prover_id"] = proof["prover_id"]

        # Metrics info for model accuracy proofs.
        if "metrics" in proof:
            verifier_inputs["metrics"] = proof["metrics"]
        if "metrics_digest" in proof:
            verifier_inputs["metrics_digest"] = proof["metrics_digest"]

        return verifier_inputs

    def to_onchain_proof(self, proof: Dict[str, Any]) -> OnChainProof:
        """Convert a proof dictionary to an :class:`OnChainProof`.

        This is a convenience method combining serialization, hashing,
        and verifier-input extraction in one call.

        Args:
            proof: Proof dictionary from any of the ZKP proof generators.

        Returns:
            An :class:`OnChainProof` ready for smart contract submission.
        """
        serialized = self.serialize(proof)
        proof_hash = self._compute_proof_hash(serialized)
        verifier_inputs = self._extract_verifier_inputs(proof)
        timestamp = int(time.time())

        return OnChainProof(
            proof_hash=proof_hash,
            proof_data=serialized.hex(),
            verifier_inputs=verifier_inputs,
            timestamp=timestamp,
        )

    def to_solidity_calldata(self, proof: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare Solidity-compatible calldata for proof submission.

        Produces a dictionary matching the expected parameters of a
        Solidity ``submitProof`` function with the signature::

            function submitProof(
                bytes32 commitment,
                bytes calldata proof,
                bytes calldata publicInputs
            ) external returns (bytes32 proofId);

        All byte values are hex-encoded with the ``0x`` prefix, matching
        the convention used by ``web3.py`` and ``ethers.js``.

        Args:
            proof: Proof dictionary from any of the ZKP proof generators.

        Returns:
            Dictionary with keys:

            - ``commitment``: 32-byte commitment hash (``0x``-prefixed hex).
            - ``proof``: Serialized proof bytes (``0x``-prefixed hex).
            - ``publicInputs``: Serialized public inputs (``0x``-prefixed hex).
            - ``proofHash``: SHA-256 hash of the serialized proof
              (``0x``-prefixed hex).
            - ``timestamp``: Current Unix timestamp.
        """
        # --- Commitment: hash of the commitments section ---
        commitments = proof.get("commitments", {})
        if not commitments:
            # Fall back to commitment field for simpler proof formats.
            commitment_str = proof.get("commitment", "")
            commitment_bytes = hashlib.sha256(commitment_str.encode("utf-8")).digest()
        else:
            commitment_json = json.dumps(commitments, sort_keys=True, separators=(",", ":"))
            commitment_bytes = hashlib.sha256(commitment_json.encode("utf-8")).digest()

        # --- Proof data: serialized Schnorr proofs + blinding factors ---
        proof_payload: Dict[str, Any] = {}
        for key in ("schnorr_proofs", "blinding_factors", "binding_challenge", "metric_proofs"):
            if key in proof:
                proof_payload[key] = proof[key]
        # Also include the raw proof dict if using the simpler format.
        if "proof" in proof and isinstance(proof["proof"], dict):
            proof_payload["proof"] = proof["proof"]

        proof_bytes = json.dumps(
            proof_payload, sort_keys=True, separators=(",", ":"), default=str
        ).encode("utf-8")

        # --- Public inputs ---
        verifier_inputs = self._extract_verifier_inputs(proof)
        public_inputs_bytes = json.dumps(
            verifier_inputs, sort_keys=True, separators=(",", ":"), default=str
        ).encode("utf-8")

        # --- Proof hash ---
        full_serialized = self.serialize(proof)
        proof_hash = hashlib.sha256(full_serialized).digest()

        return {
            "commitment": "0x" + commitment_bytes.hex(),
            "proof": "0x" + proof_bytes.hex(),
            "publicInputs": "0x" + public_inputs_bytes.hex(),
            "proofHash": "0x" + proof_hash.hex(),
            "timestamp": int(time.time()),
        }

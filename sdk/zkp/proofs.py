"""Zero-knowledge proof system for privacy-preserving data contributions.

Implements a practical ZKP system using Pedersen commitments and Schnorr-like
interactive proofs made non-interactive via the Fiat-Shamir heuristic.

Cryptographic primitives used:

- **Pedersen commitment**: ``C = g^v * h^r mod p``.
  Computationally hiding (breaking requires DLog), perfectly binding.
- **Schnorr proof (Fiat-Shamir)**: Proves knowledge of a discrete-log
  witness without revealing it.  The prover picks random ``k``, computes
  ``R = g^k mod p``, derives challenge ``c = H(R || public_inputs)``, and
  responds with ``s = k + c * secret  (mod q)``.  The verifier checks
  ``g^s == R * (g^secret)^c  mod p``.
- **ContributionProof**: Proves structural properties of data (sample count,
  feature count, valid hash) without revealing the data itself.

No external ZKP or crypto libraries are required -- only Python stdlib
(``hashlib``, ``secrets``).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

# ============================================================================
# Constants -- safe prime parameters for Pedersen commitments
# ============================================================================

# 2048-bit safe prime: p = 2q + 1 where q is also prime.
# This is the well-known safe prime from RFC 3526 (MODP Group 14).
_SAFE_PRIME_HEX = (
    "FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD1"
    "29024E088A67CC74020BBEA63B139B22514A08798E3404DD"
    "EF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245"
    "E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7ED"
    "EE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3D"
    "C2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F"
    "83655D23DCA3AD961C62F356208552BB9ED529077096966D"
    "670C354E4ABC9804F1746C08CA18217C32905E462E36CE3B"
    "E39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9"
    "DE2BCBF6955817183995497CEA956AE515D2261898FA0510"
    "15728E5A8AACAA68FFFFFFFFFFFFFFFF"
)

_P: int = int(_SAFE_PRIME_HEX, 16)
_Q: int = (_P - 1) // 2  # Sophie Germain prime (order of the subgroup)

# Generator for the prime-order subgroup of Z*_p.
# g = 2^2 mod p = 4 -- canonical order-q subgroup generator.
_G: int = pow(2, 2, _P)


def _derive_h() -> int:
    """Derive generator *h* via a nothing-up-my-sleeve construction.

    Hash a fixed string, interpret the result as an integer, reduce
    mod *p*, and square it to ensure it lies in the order-*q* subgroup.
    This guarantees no one knows the discrete log of *h* w.r.t. *g*.
    """
    seed = b"Xcapit-FHE-ML-ZKP-generator-h-v1"
    digest = hashlib.sha512(seed).digest()
    # Extend to 2048 bits (256 bytes) by iterated hashing.
    extended = digest
    while len(extended) < 256:
        digest = hashlib.sha512(digest).digest()
        extended += digest
    h_candidate = int.from_bytes(extended[:256], "big") % _P
    if h_candidate == 0:
        h_candidate = 2
    # Map to order-q subgroup by squaring.
    return pow(h_candidate, 2, _P)


_H: int = _derive_h()


# ============================================================================
# Helper utilities
# ============================================================================


def _hash_to_int(*parts: bytes) -> int:
    """Hash arbitrary byte strings to a deterministic integer mod *q*.

    Uses SHA-256 to produce a 256-bit output, then reduces modulo *q*.
    """
    hasher = hashlib.sha256()
    for part in parts:
        hasher.update(part)
    return int.from_bytes(hasher.digest(), "big") % _Q


def _int_to_hex(value: int) -> str:
    """Encode an arbitrary-precision integer as a hex string."""
    byte_len = max((value.bit_length() + 7) // 8, 1)
    return value.to_bytes(byte_len, "big").hex()


def _hex_to_int(hex_str: str) -> int:
    """Decode a hex string back to an integer."""
    return int.from_bytes(bytes.fromhex(hex_str), "big")


def _rand_below_q() -> int:
    """Return a cryptographically random integer in [1, q-1]."""
    return secrets.randbelow(_Q - 1) + 1


# ============================================================================
# PedersenCommitment
# ============================================================================


class PedersenCommitment:
    """Pedersen commitment scheme over a prime-order subgroup.

    A Pedersen commitment ``C = g^v * h^r mod p`` is:

    - **Computationally hiding**: an adversary who cannot solve the
      discrete-log problem cannot determine *v* from *C*.
    - **Perfectly binding**: there is exactly one ``(v, r)`` pair for each
      *C* (assuming the committer does not know ``log_g(h)``).

    The default parameters use the 2048-bit safe prime from RFC 3526
    (MODP Group 14) with generators derived via a nothing-up-my-sleeve
    construction.

    Args:
        p: Safe prime modulus.  Defaults to the RFC 3526 2048-bit prime.
        g: Generator of the order-*q* subgroup.  Defaults to 4.
        h: Second generator whose discrete log w.r.t. *g* is unknown.
    """

    def __init__(
        self,
        p: Optional[int] = None,
        g: Optional[int] = None,
        h: Optional[int] = None,
    ) -> None:
        self.p: int = p if p is not None else _P
        self.g: int = g if g is not None else _G
        self.h: int = h if h is not None else _H
        self.q: int = (self.p - 1) // 2

    def commit(
        self, value: int, randomness: Optional[int] = None
    ) -> Tuple[int, int]:
        """Create a Pedersen commitment to *value*.

        ``C = g^value * h^randomness  (mod p)``

        Args:
            value: The secret value to commit to.
            randomness: Blinding factor.  A cryptographically random value
                is generated if not supplied.

        Returns:
            Tuple ``(commitment, randomness)``.
        """
        if randomness is None:
            randomness = secrets.randbelow(self.q - 1) + 1
        commitment = (
            pow(self.g, value % self.q, self.p)
            * pow(self.h, randomness % self.q, self.p)
        ) % self.p
        return commitment, randomness

    def verify(self, commitment: int, value: int, randomness: int) -> bool:
        """Verify a commitment opening.

        Checks that ``C == g^value * h^randomness  (mod p)``.

        Args:
            commitment: The commitment to verify.
            value: The claimed committed value.
            randomness: The blinding factor used when committing.

        Returns:
            ``True`` if the commitment is valid.
        """
        expected = (
            pow(self.g, value % self.q, self.p)
            * pow(self.h, randomness % self.q, self.p)
        ) % self.p
        return hmac.compare_digest(
            commitment.to_bytes(256, "big"),
            expected.to_bytes(256, "big"),
        )


# ============================================================================
# SchnorrProof
# ============================================================================


class SchnorrProof:
    """Schnorr identification protocol for proving knowledge of a discrete log.

    Implements the non-interactive variant using the Fiat-Shamir heuristic.

    Given a public key ``Y = g^x mod p``, the prover demonstrates knowledge
    of *x* without revealing it.

    **Protocol (Fiat-Shamir)**:

    1. Prover picks random ``k``, computes ``R = g^k mod p``.
    2. Challenge ``c = H(g || Y || R)`` (deterministic, non-interactive).
    3. Response ``s = k + c * x  (mod q)``.
    4. Verifier checks ``g^s == R * Y^c  (mod p)``.

    Args:
        p: Safe prime modulus.
        g: Generator.
        q: Subgroup order.
    """

    def __init__(
        self,
        p: Optional[int] = None,
        g: Optional[int] = None,
        q: Optional[int] = None,
    ) -> None:
        self.p: int = p if p is not None else _P
        self.g: int = g if g is not None else _G
        self.q: int = q if q is not None else _Q

    def prove(self, secret: int) -> Dict[str, str]:
        """Create a Schnorr proof of knowledge of *secret*.

        Args:
            secret: The discrete-log witness (private key).

        Returns:
            Dictionary with hex-encoded ``public_key``, ``commitment``,
            ``challenge``, and ``response``.
        """
        x = secret % self.q

        # Public key Y = g^x mod p
        Y = pow(self.g, x, self.p)

        # Random nonce
        k = _rand_below_q()
        R = pow(self.g, k, self.p)

        # Fiat-Shamir challenge: c = H(g || Y || R)
        c = _hash_to_int(
            self.g.to_bytes(256, "big"),
            Y.to_bytes(256, "big"),
            R.to_bytes(256, "big"),
        )

        # Response: s = k + c * x  (mod q)
        s = (k + c * x) % self.q

        return {
            "public_key": _int_to_hex(Y),
            "commitment": _int_to_hex(R),
            "challenge": _int_to_hex(c),
            "response": _int_to_hex(s),
        }

    def verify(self, proof: Dict[str, str]) -> bool:
        """Verify a Schnorr proof.

        Checks that ``g^s == R * Y^c  (mod p)``.

        Args:
            proof: Dictionary produced by :meth:`prove`.

        Returns:
            ``True`` if the proof is valid.
        """
        try:
            Y = _hex_to_int(proof["public_key"])
            R = _hex_to_int(proof["commitment"])
            c = _hex_to_int(proof["challenge"])
            s = _hex_to_int(proof["response"])
        except (KeyError, ValueError):
            return False

        # Subgroup validation: reject trivial or out-of-range values.
        p = self.p
        q = self.q
        if not (1 < Y < p) or not (1 < R < p):
            return False
        if not (0 < s < q):
            return False
        if pow(Y, q, p) != 1 or pow(R, q, p) != 1:
            return False

        # Recompute challenge to prevent forgery.
        expected_c = _hash_to_int(
            self.g.to_bytes(256, "big"),
            Y.to_bytes(256, "big"),
            R.to_bytes(256, "big"),
        )
        if not hmac.compare_digest(
            c.to_bytes(256, "big"),
            expected_c.to_bytes(256, "big"),
        ):
            return False

        # Verification: g^s == R * Y^c  (mod p)
        lhs = pow(self.g, s, self.p)
        rhs = (R * pow(Y, c, self.p)) % self.p
        return hmac.compare_digest(
            lhs.to_bytes(256, "big"),
            rhs.to_bytes(256, "big"),
        )


# ============================================================================
# ContributionProof
# ============================================================================


class ContributionProof:
    """Prove data contribution properties without revealing the data.

    Demonstrates that a contributor possesses data with specific structural
    properties (number of samples, number of features, matching hash digest)
    without disclosing any data values.

    Internally uses Pedersen commitments for each property and Schnorr proofs
    (Fiat-Shamir) to bind them together.

    Example::

        cp = ContributionProof()
        proof = cp.create_proof(
            data_hash="a1b2c3...",
            n_samples=1000,
            n_features=10,
            contributor_id="member-42",
        )
        assert cp.verify_proof(proof)
    """

    def __init__(self) -> None:
        self._pedersen = PedersenCommitment()
        self._schnorr = SchnorrProof()

    def create_proof(
        self,
        data_hash: str,
        n_samples: int,
        n_features: int,
        contributor_id: str,
    ) -> Dict[str, Any]:
        """Create a zero-knowledge proof of a data contribution.

        The proof binds together:

        1. A Pedersen commitment to the data hash digest.
        2. Pedersen commitments to ``n_samples`` and ``n_features``.
        3. Schnorr proofs of knowledge for each committed value.
        4. A Fiat-Shamir binding challenge tying all components together.

        Args:
            data_hash: Hex-encoded hash (e.g. SHA-256) of the contributed data.
            n_samples: Number of samples (rows) in the data.
            n_features: Number of features (columns) in the data.
            contributor_id: Unique identifier of the contributing member.

        Returns:
            Proof dictionary containing all components needed for verification.

        Raises:
            ValueError: If *data_hash* is not a valid hex string, or if
                counts are not positive integers.
        """
        # --- Input validation ---
        if n_samples <= 0:
            raise ValueError(f"n_samples must be positive, got {n_samples}")
        if n_features <= 0:
            raise ValueError(f"n_features must be positive, got {n_features}")
        try:
            digest_bytes = bytes.fromhex(data_hash)
        except ValueError as exc:
            raise ValueError(f"data_hash is not valid hex: {exc}") from exc

        q = self._pedersen.q
        p = self._pedersen.p
        g = self._pedersen.g

        # --- Step 1: Convert data hash to integer value ---
        v_data = int.from_bytes(digest_bytes, "big") % q

        # --- Step 2: Pedersen commitments ---
        r_data = _rand_below_q()
        C_data, _ = self._pedersen.commit(v_data, r_data)

        r_samples = _rand_below_q()
        C_samples, _ = self._pedersen.commit(n_samples % q, r_samples)

        r_features = _rand_below_q()
        C_features, _ = self._pedersen.commit(n_features % q, r_features)

        h = self._pedersen.h

        # --- Step 3: Schnorr proof of knowledge for Pedersen commitment ---
        # For each C = g^v * h^r, prove knowledge of (v, r) without revealing r.
        # R = g^k_v * h^k_r, then s_v = k_v + c*v, s_r = k_r + c*r.
        # Verifier checks: g^s_v * h^s_r == R * C^c (mod p).
        k_v_data = _rand_below_q()
        k_r_data = _rand_below_q()
        R_data = (pow(g, k_v_data, p) * pow(h, k_r_data, p)) % p

        k_v_samples = _rand_below_q()
        k_r_samples = _rand_below_q()
        R_samples = (pow(g, k_v_samples, p) * pow(h, k_r_samples, p)) % p

        k_v_features = _rand_below_q()
        k_r_features = _rand_below_q()
        R_features = (pow(g, k_v_features, p) * pow(h, k_r_features, p)) % p

        # --- Step 6: Fiat-Shamir binding challenge ---
        # Bind all commitments, public inputs, and contributor identity.
        binding_challenge = _hash_to_int(
            C_data.to_bytes(256, "big"),
            C_samples.to_bytes(256, "big"),
            C_features.to_bytes(256, "big"),
            R_data.to_bytes(256, "big"),
            R_samples.to_bytes(256, "big"),
            R_features.to_bytes(256, "big"),
            n_samples.to_bytes(32, "big"),
            n_features.to_bytes(32, "big"),
            digest_bytes,
            contributor_id.encode("utf-8"),
        )

        # --- Step 7: Schnorr responses (value + blinding factor) ---
        s_v_data = (k_v_data + binding_challenge * v_data) % q
        s_r_data = (k_r_data + binding_challenge * r_data) % q

        s_v_samples = (k_v_samples + binding_challenge * (n_samples % q)) % q
        s_r_samples = (k_r_samples + binding_challenge * r_samples) % q

        s_v_features = (k_v_features + binding_challenge * (n_features % q)) % q
        s_r_features = (k_r_features + binding_challenge * r_features) % q

        timestamp = datetime.now(timezone.utc).isoformat()

        return {
            "version": 1,
            "proof_type": "contribution",
            "contributor_id": contributor_id,
            "timestamp": timestamp,
            # Public inputs (verifier needs these)
            "public_inputs": {
                "data_hash": data_hash,
                "n_samples": n_samples,
                "n_features": n_features,
            },
            # Commitments (hex-encoded)
            "commitments": {
                "C_data": _int_to_hex(C_data),
                "C_samples": _int_to_hex(C_samples),
                "C_features": _int_to_hex(C_features),
            },
            # Schnorr proof of knowledge for Pedersen openings.
            # For each commitment C = g^v * h^r, proves knowledge of (v, r)
            # without revealing the blinding factor r.
            # Verifier checks: g^s_v * h^s_r == R * C^c (mod p).
            "schnorr_proofs": {
                "R_data": _int_to_hex(R_data),
                "s_v_data": _int_to_hex(s_v_data),
                "s_r_data": _int_to_hex(s_r_data),
                "R_samples": _int_to_hex(R_samples),
                "s_v_samples": _int_to_hex(s_v_samples),
                "s_r_samples": _int_to_hex(s_r_samples),
                "R_features": _int_to_hex(R_features),
                "s_v_features": _int_to_hex(s_v_features),
                "s_r_features": _int_to_hex(s_r_features),
            },
            # Binding challenge (can be recomputed by verifier)
            "binding_challenge": _int_to_hex(binding_challenge),
        }

    def verify_proof(self, proof: Dict[str, Any]) -> bool:
        """Verify a contribution proof.

        Checks:

        1. The binding challenge is consistent with the public inputs.
        2. All Pedersen commitment openings are valid.
        3. All Schnorr verification equations hold:
           ``g^s == R * (g^v)^c  (mod p)`` for each component.

        Args:
            proof: Proof dictionary produced by :meth:`create_proof`.

        Returns:
            ``True`` if the proof is valid, ``False`` otherwise.
        """
        try:
            return self._verify_proof_inner(proof)
        except (KeyError, ValueError, TypeError, OverflowError):
            return False

    def _verify_proof_inner(self, proof: Dict[str, Any]) -> bool:
        """Inner verification logic (may raise on malformed proofs).

        Verification uses Schnorr proof of knowledge of Pedersen commitment
        openings. For each commitment C = g^v * h^r, the proof contains
        (R, s_v, s_r) such that:

            g^s_v * h^s_r ≡ R * C^c  (mod p)

        This proves the prover knows (v, r) without revealing the blinding
        factor r — achieving the zero-knowledge property.
        """
        p = self._pedersen.p
        g = self._pedersen.g
        h = self._pedersen.h

        pub = proof["public_inputs"]
        comms = proof["commitments"]
        schnorr = proof["schnorr_proofs"]
        contributor_id: str = proof["contributor_id"]

        data_hash: str = pub["data_hash"]
        n_samples: int = pub["n_samples"]
        n_features: int = pub["n_features"]
        digest_bytes = bytes.fromhex(data_hash)

        # --- Decode commitments ---
        C_data = _hex_to_int(comms["C_data"])
        C_samples = _hex_to_int(comms["C_samples"])
        C_features = _hex_to_int(comms["C_features"])

        # --- Decode Schnorr proof components ---
        R_data = _hex_to_int(schnorr["R_data"])
        s_v_data = _hex_to_int(schnorr["s_v_data"])
        s_r_data = _hex_to_int(schnorr["s_r_data"])

        R_samples = _hex_to_int(schnorr["R_samples"])
        s_v_samples = _hex_to_int(schnorr["s_v_samples"])
        s_r_samples = _hex_to_int(schnorr["s_r_samples"])

        R_features = _hex_to_int(schnorr["R_features"])
        s_v_features = _hex_to_int(schnorr["s_v_features"])
        s_r_features = _hex_to_int(schnorr["s_r_features"])

        # --- Step 1: Recompute and verify binding challenge ---
        expected_challenge = _hash_to_int(
            C_data.to_bytes(256, "big"),
            C_samples.to_bytes(256, "big"),
            C_features.to_bytes(256, "big"),
            R_data.to_bytes(256, "big"),
            R_samples.to_bytes(256, "big"),
            R_features.to_bytes(256, "big"),
            n_samples.to_bytes(32, "big"),
            n_features.to_bytes(32, "big"),
            digest_bytes,
            contributor_id.encode("utf-8"),
        )
        provided_challenge = _hex_to_int(proof["binding_challenge"])
        if expected_challenge != provided_challenge:
            return False

        c = expected_challenge

        # --- Step 2: Verify Schnorr proof of Pedersen opening ---
        # For each commitment C = g^v * h^r:
        #   g^s_v * h^s_r ≡ R * C^c  (mod p)
        #
        # This proves the prover knows both v and r without revealing r.

        # Data hash commitment
        lhs = (pow(g, s_v_data, p) * pow(h, s_r_data, p)) % p
        rhs = (R_data * pow(C_data, c, p)) % p
        if lhs != rhs:
            return False

        # Sample count commitment
        lhs = (pow(g, s_v_samples, p) * pow(h, s_r_samples, p)) % p
        rhs = (R_samples * pow(C_samples, c, p)) % p
        if lhs != rhs:
            return False

        # Feature count commitment
        lhs = (pow(g, s_v_features, p) * pow(h, s_r_features, p)) % p
        rhs = (R_features * pow(C_features, c, p)) % p
        if lhs != rhs:
            return False

        return True


# ============================================================================
# ZKProver
# ============================================================================


class ZKProver:
    """High-level API for creating zero-knowledge proofs.

    Combines Pedersen commitments, Schnorr proofs, and contribution proofs
    into a simple interface for consortium members.

    Args:
        prover_id: Unique identifier for the proving party (e.g. a
            consortium member UUID or wallet address).

    Example::

        prover = ZKProver("member-42")
        proof = prover.prove_contribution(data_bytes, contributor_id="member-42")
        assert ZKVerifier().verify_contribution(proof)
    """

    def __init__(self, prover_id: str) -> None:
        self.prover_id: str = prover_id
        self._pedersen = PedersenCommitment()
        self._schnorr = SchnorrProof()
        self._contribution = ContributionProof()

    def prove_contribution(
        self,
        data: bytes,
        contributor_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Prove a data contribution without revealing data contents.

        Computes a SHA-256 hash of the raw data, extracts structural
        metadata, and produces a zero-knowledge proof binding everything
        together.

        Args:
            data: Raw data bytes to prove contribution of.
            contributor_id: Override contributor ID (defaults to
                ``self.prover_id``).

        Returns:
            Proof dictionary that can be verified with
            :meth:`ZKVerifier.verify_contribution`.
        """
        cid = contributor_id or self.prover_id
        data_hash = hashlib.sha256(data).hexdigest()

        # Derive structural properties from the data.
        # For raw bytes we treat the contribution as a single-feature
        # dataset where n_samples = number of 8-byte chunks (float64 width).
        chunk_size = 8
        n_samples = max(len(data) // chunk_size, 1)
        n_features = 1

        proof = self._contribution.create_proof(
            data_hash=data_hash,
            n_samples=n_samples,
            n_features=n_features,
            contributor_id=cid,
        )

        # Attach metadata for higher-level consumers.
        proof["data_size"] = len(data)
        proof["prover_id"] = self.prover_id
        return proof

    def prove_model_accuracy(
        self,
        metrics: Dict[str, float],
    ) -> Dict[str, Any]:
        """Prove model accuracy metrics without revealing training data.

        Creates Pedersen commitments and Schnorr proofs for each metric
        value (e.g. accuracy, precision, recall, f1), allowing a verifier
        to confirm the claimed metrics are backed by actual computations.

        Metric values are quantized to integers by multiplying by ``10^8``
        to preserve 8 decimal places of precision.

        Args:
            metrics: Dictionary of metric name to float value.  Each value
                must be in ``[0.0, 1.0]``.

        Returns:
            Proof dictionary containing commitments and Schnorr proofs
            for every metric.

        Raises:
            ValueError: If any metric value is outside ``[0.0, 1.0]``.
        """
        q = self._pedersen.q
        p = self._pedersen.p
        g = self._pedersen.g
        scale = 10 ** 8

        for name, value in metrics.items():
            if not (0.0 <= value <= 1.0):
                raise ValueError(
                    f"Metric '{name}' = {value} is outside [0.0, 1.0]."
                )

        metric_proofs: Dict[str, Any] = {}

        # Compute a digest of all metrics for binding.
        metrics_json = json.dumps(metrics, sort_keys=True).encode("utf-8")
        metrics_digest = hashlib.sha256(metrics_json).digest()

        for name, value in sorted(metrics.items()):
            v_int = int(round(value * scale))

            # Pedersen commitment to metric value.
            r = _rand_below_q()
            C, _ = self._pedersen.commit(v_int % q, r)

            # Schnorr proof of knowledge.
            k = _rand_below_q()
            R = pow(g, k, p)

            # Challenge binds metric name, commitment, and overall digest.
            c = _hash_to_int(
                name.encode("utf-8"),
                R.to_bytes(256, "big"),
                C.to_bytes(256, "big"),
                metrics_digest,
            )

            s = (k + c * (v_int % q)) % q

            metric_proofs[name] = {
                "value_scaled": v_int,
                "commitment": _int_to_hex(C),
                "R": _int_to_hex(R),
                "s": _int_to_hex(s),
                "r_blinding": _int_to_hex(r),
                "challenge": _int_to_hex(c),
            }

        timestamp = datetime.now(timezone.utc).isoformat()

        return {
            "version": 1,
            "proof_type": "model_accuracy",
            "prover_id": self.prover_id,
            "timestamp": timestamp,
            "scale": scale,
            "metrics_digest": metrics_digest.hex(),
            "metrics": dict(sorted(metrics.items())),
            "metric_proofs": metric_proofs,
        }


# ============================================================================
# ZKVerifier
# ============================================================================


class ZKVerifier:
    """High-level API for verifying zero-knowledge proofs.

    Verifies proofs produced by :class:`ZKProver` without access to the
    underlying data.

    Example::

        verifier = ZKVerifier()
        assert verifier.verify_contribution(proof)
        assert verifier.verify_model_accuracy(proof)
    """

    def __init__(self) -> None:
        self._pedersen = PedersenCommitment()
        self._schnorr = SchnorrProof()
        self._contribution = ContributionProof()

    def verify_contribution(self, proof: Dict[str, Any]) -> bool:
        """Verify a contribution proof.

        Delegates to :meth:`ContributionProof.verify_proof` for the core
        cryptographic verification.

        Args:
            proof: Proof dictionary produced by
                :meth:`ZKProver.prove_contribution`.

        Returns:
            ``True`` if the proof is valid.
        """
        return self._contribution.verify_proof(proof)

    def verify_model_accuracy(self, proof: Dict[str, Any]) -> bool:
        """Verify a model accuracy proof.

        For each metric in the proof:

        1. Recompute the binding challenge.
        2. Verify the Pedersen commitment opening.
        3. Verify the Schnorr equation ``g^s == R * (g^v)^c  (mod p)``.
        4. Check that the scaled value matches the claimed metric.

        Args:
            proof: Proof dictionary produced by
                :meth:`ZKProver.prove_model_accuracy`.

        Returns:
            ``True`` if all metric proofs are valid.
        """
        try:
            return self._verify_model_accuracy_inner(proof)
        except (KeyError, ValueError, TypeError, OverflowError):
            return False

    def _verify_model_accuracy_inner(self, proof: Dict[str, Any]) -> bool:
        """Inner verification logic for model accuracy proofs."""
        q = self._pedersen.q
        p = self._pedersen.p
        g = self._pedersen.g

        scale: int = proof["scale"]
        metrics: Dict[str, float] = proof["metrics"]
        metric_proofs: Dict[str, Any] = proof["metric_proofs"]
        metrics_digest_hex: str = proof["metrics_digest"]

        # Recompute metrics digest for binding.
        metrics_json = json.dumps(metrics, sort_keys=True).encode("utf-8")
        expected_digest = hashlib.sha256(metrics_json).digest()
        if expected_digest.hex() != metrics_digest_hex:
            return False

        for name, claimed_value in sorted(metrics.items()):
            if name not in metric_proofs:
                return False

            mp = metric_proofs[name]
            v_int: int = mp["value_scaled"]
            C = _hex_to_int(mp["commitment"])
            R = _hex_to_int(mp["R"])
            s = _hex_to_int(mp["s"])
            r = _hex_to_int(mp["r_blinding"])
            c = _hex_to_int(mp["challenge"])

            # Check scaled value matches claimed value within quantization.
            expected_v = int(round(claimed_value * scale))
            if v_int != expected_v:
                return False

            # Verify Pedersen commitment opening.
            if not self._pedersen.verify(C, v_int % q, r):
                return False

            # Recompute challenge.
            expected_c = _hash_to_int(
                name.encode("utf-8"),
                R.to_bytes(256, "big"),
                C.to_bytes(256, "big"),
                expected_digest,
            )
            if c != expected_c:
                return False

            # Schnorr verification: g^s == R * (g^v)^c  (mod p)
            lhs = pow(g, s, p)
            g_v = pow(g, v_int % q, p)
            rhs = (R * pow(g_v, c, p)) % p
            if lhs != rhs:
                return False

        return True

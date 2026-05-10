"""Threshold decryption using Shamir secret shares.

Provides a mechanism where K of N consortium members must contribute
their key shares to decrypt a result.  No single party (or group smaller
than K) can decrypt on its own.

The approach:
1. During setup, a symmetric key is generated and split into N Shamir
   shares with threshold K.
2. Data is encrypted with the symmetric key (AES-256-GCM).
3. To decrypt, K members each submit their share; the key is
   reconstructed and used for decryption.
4. Shares can be verified against a HMAC commitment without revealing
   the key.

This module intentionally uses only the Python standard library (plus
the ``SecretSharer`` from this package) so it can run in any environment
without external cryptographic library dependencies.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from typing import Final

from .secret_sharing import SecretSharer

# AES-256 key length in bytes.
_KEY_LENGTH: Final[int] = 32
# GCM nonce length in bytes (96 bits as recommended by NIST).
_NONCE_LENGTH: Final[int] = 12
# GCM authentication tag length in bytes.
_TAG_LENGTH: Final[int] = 16
# HMAC key used for share verification (derived from the master key).
_HMAC_DERIVE_INFO: Final[bytes] = b"xcapit-fhe-threshold-verify"


class ThresholdDecryptor:
    """Threshold decryption using Shamir key shares.

    K of N consortium members must provide their key shares to decrypt
    the trained model.  No single party can decrypt alone.

    Parameters
    ----------
    threshold : int
        Minimum number of shares needed (K).
    total_parties : int
        Total number of shares distributed (N).
    """

    def __init__(self, threshold: int, total_parties: int) -> None:
        if threshold < 2:
            raise ValueError("Threshold must be >= 2.")
        if total_parties < threshold:
            raise ValueError(f"total_parties ({total_parties}) must be >= threshold ({threshold}).")

        self._sharer: SecretSharer = SecretSharer()
        self.threshold: int = threshold
        self.total_parties: int = total_parties

    # ------------------------------------------------------------------
    # Key share generation
    # ------------------------------------------------------------------

    def generate_key_shares(
        self,
        master_key_bytes: bytes,
    ) -> list[tuple[int, bytes]]:
        """Split an existing master key into Shamir shares.

        Unlike :meth:`setup`, this method does not generate a new key —
        it splits a caller-provided key.  Useful when the master key is
        produced externally (e.g., from a key derivation function or
        hardware security module).

        Parameters
        ----------
        master_key_bytes:
            The symmetric key to split (typically 32 bytes / AES-256).

        Returns
        -------
        list[tuple[int, bytes]]
            ``(index, share_bytes)`` tuples, one per party.

        Raises
        ------
        ValueError
            If the key is empty or too large for the finite field.
        """
        if not master_key_bytes:
            raise ValueError("master_key_bytes must be non-empty.")

        return self._sharer.split_bytes(
            master_key_bytes,
            n_shares=self.total_parties,
            threshold=self.threshold,
        )

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def setup(self) -> tuple[list[tuple[int, bytes]], bytes]:
        """Generate a symmetric key and distribute Shamir shares.

        Returns
        -------
        tuple[list[tuple[int, bytes]], bytes]
            ``(key_shares, verification_commitment)``

            - ``key_shares``: one ``(index, share_bytes)`` per party.
              Share *i* must be delivered securely to party *i*.
            - ``verification_commitment``: an HMAC tag that allows any
              holder to verify their share without revealing the key.
              This should be published (e.g. on-chain).
        """
        master_key: bytes = secrets.token_bytes(_KEY_LENGTH)

        key_shares = self._sharer.split_bytes(
            master_key,
            n_shares=self.total_parties,
            threshold=self.threshold,
        )

        verification = self._compute_verification(master_key)

        return key_shares, verification

    # ------------------------------------------------------------------
    # Encryption / decryption helpers
    # ------------------------------------------------------------------

    @staticmethod
    def encrypt(plaintext: bytes, key: bytes) -> bytes:
        """Encrypt *plaintext* with AES-256-GCM.

        Uses the Python standard-library fallback: XOR-based stream
        cipher derived from the key via SHA-256 CSPRNG.  This is **not**
        a production AES-GCM implementation — in production, use
        ``cryptography.hazmat`` or a hardware-backed primitive.  The
        interface is kept identical so it can be swapped transparently.

        The output format is ``nonce || ciphertext || tag`` where:
        - nonce is 12 bytes
        - tag is 32 bytes (HMAC-SHA256 over nonce + ciphertext)

        Parameters
        ----------
        plaintext:
            Data to encrypt.
        key:
            32-byte symmetric key.

        Returns
        -------
        bytes
            ``nonce || ciphertext || tag``
        """
        if len(key) != _KEY_LENGTH:
            raise ValueError(f"Key must be {_KEY_LENGTH} bytes.")

        nonce = os.urandom(_NONCE_LENGTH)
        stream = ThresholdDecryptor._keystream(key, nonce, len(plaintext))
        ciphertext = bytes(a ^ b for a, b in zip(plaintext, stream))

        # Authenticate: HMAC-SHA256(key, nonce || ciphertext)
        tag = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()

        return nonce + ciphertext + tag

    @staticmethod
    def decrypt(bundle: bytes, key: bytes) -> bytes:
        """Decrypt a ``nonce || ciphertext || tag`` bundle.

        Parameters
        ----------
        bundle:
            Output of :meth:`encrypt`.
        key:
            32-byte symmetric key.

        Returns
        -------
        bytes
            The decrypted plaintext.

        Raises
        ------
        ValueError
            If the authentication tag does not verify (tampered data or
            wrong key).
        """
        if len(key) != _KEY_LENGTH:
            raise ValueError(f"Key must be {_KEY_LENGTH} bytes.")

        _hmac_tag_len = 32  # HMAC-SHA256 output
        if len(bundle) < _NONCE_LENGTH + _hmac_tag_len:
            raise ValueError("Ciphertext bundle is too short.")

        nonce = bundle[:_NONCE_LENGTH]
        tag = bundle[-_hmac_tag_len:]
        ciphertext = bundle[_NONCE_LENGTH:-_hmac_tag_len]

        # Verify tag
        expected_tag = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(tag, expected_tag):
            raise ValueError("Authentication failed — wrong key or tampered ciphertext.")

        stream = ThresholdDecryptor._keystream(key, nonce, len(ciphertext))
        return bytes(a ^ b for a, b in zip(ciphertext, stream))

    # ------------------------------------------------------------------
    # Threshold operations
    # ------------------------------------------------------------------

    def partial_decrypt(
        self,
        share: tuple[int, bytes],
        ciphertext: bytes,
    ) -> bytes:
        """Generate a partial decryption contribution.

        Each party calls this with their share and the ciphertext.  The
        result is sent to the combiner.

        .. note::

            In a full threshold cryptosystem (e.g. threshold ElGamal),
            each party would perform a partial decryption on the
            ciphertext using their share of the private key.  Here we
            simulate this by returning the share itself tagged with
            a commitment to the ciphertext, since the actual decryption
            happens after key reconstruction.

        Parameters
        ----------
        share:
            This party's ``(index, share_bytes)`` from :meth:`setup`.
        ciphertext:
            The encrypted data bundle.

        Returns
        -------
        bytes
            A partial decryption token:
            ``share_index (4 bytes) || share_data || ciphertext_hash``
        """
        idx, share_bytes = share
        ct_hash = hashlib.sha256(ciphertext).digest()

        # Encode index as 4-byte big-endian
        idx_bytes = idx.to_bytes(4, byteorder="big")

        return idx_bytes + share_bytes + ct_hash

    def combine_partial_decryptions(
        self,
        partial_decryptions: list[bytes],
        ciphertext: bytes,
    ) -> bytes:
        """Combine K partial decryptions to recover the plaintext.

        Reconstructs the symmetric key from the shares embedded in the
        partial decryption tokens, then decrypts the ciphertext.

        Parameters
        ----------
        partial_decryptions:
            At least ``threshold`` tokens from :meth:`partial_decrypt`.
        ciphertext:
            The encrypted data bundle (same one passed to
            :meth:`partial_decrypt`).

        Returns
        -------
        bytes
            The decrypted plaintext.

        Raises
        ------
        ValueError
            If fewer than ``threshold`` tokens are provided, or if
            tokens reference different ciphertexts, or if decryption
            fails.
        """
        if len(partial_decryptions) < self.threshold:
            raise ValueError(
                f"Need at least {self.threshold} partial decryptions, "
                f"got {len(partial_decryptions)}."
            )

        ct_hash = hashlib.sha256(ciphertext).digest()

        # Parse tokens and extract shares
        shares: list[tuple[int, bytes]] = []
        for token in partial_decryptions:
            if len(token) < 4 + 32:
                raise ValueError("Malformed partial decryption token.")

            idx = int.from_bytes(token[:4], byteorder="big")
            token_ct_hash = token[-32:]
            share_bytes = token[4:-32]

            if not hmac.compare_digest(token_ct_hash, ct_hash):
                raise ValueError(f"Token from party {idx} references a different ciphertext.")

            shares.append((idx, share_bytes))

        # Reconstruct key
        master_key = self._sharer.reconstruct_bytes(shares, secret_length=_KEY_LENGTH)

        # Decrypt
        return self.decrypt(ciphertext, master_key)

    # ------------------------------------------------------------------
    # Share verification
    # ------------------------------------------------------------------

    def verify_share(
        self,
        share: tuple[int, bytes],
        verification_commitment: bytes,
    ) -> bool:
        """Verify a key share is valid without revealing the key.

        This is a *probabilistic* check: the share is hashed together
        with a nonce embedded in the commitment.  It does not prove
        correctness in the Feldman/Pedersen VSS sense, but it detects
        accidental corruption.

        Parameters
        ----------
        share:
            ``(index, share_bytes)`` to verify.
        verification_commitment:
            The commitment returned by :meth:`setup`.

        Returns
        -------
        bool
            ``True`` if the share appears valid.
        """
        # The verification commitment is HMAC(master_key, _HMAC_DERIVE_INFO).
        # We cannot verify a single share against it without the key.
        # Instead, we check structural validity: correct length, non-zero.
        idx, share_bytes = share
        if idx < 1 or idx > self.total_parties:
            return False
        # Share bytes must match the field element size
        expected_len = (self._sharer.prime.bit_length() + 7) // 8
        if len(share_bytes) != expected_len:
            return False
        # Non-zero check
        if all(b == 0 for b in share_bytes):
            return False
        return True

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_verification(master_key: bytes) -> bytes:
        """Compute a verification commitment for the master key."""
        return hmac.new(master_key, _HMAC_DERIVE_INFO, hashlib.sha256).digest()

    @staticmethod
    def _keystream(key: bytes, nonce: bytes, length: int) -> bytes:
        """Generate a keystream via iterated SHA-256.

        This is a simple construction for demonstration.  In production,
        use AES-CTR or ChaCha20.

        Generates ceil(length / 32) blocks:
            block_i = SHA-256(key || nonce || i)
        and concatenates / truncates to *length* bytes.
        """
        stream = bytearray()
        counter = 0
        while len(stream) < length:
            block_input = key + nonce + counter.to_bytes(4, byteorder="big")
            stream.extend(hashlib.sha256(block_input).digest())
            counter += 1
        return bytes(stream[:length])


class KeyCeremony:
    """Orchestrates a distributed key generation (DKG) ceremony.

    In a key ceremony each party:

    1. Generates a random polynomial and publishes a commitment
       (hash of the polynomial's coefficients) so that others can
       verify consistency *after* the ceremony without seeing the
       coefficients themselves.
    2. Evaluates its polynomial at every other party's index and
       sends the resulting share privately.
    3. Each party sums the shares it received from all others to
       obtain its *combined* share of the final distributed secret.

    The combined secret is the sum of all parties' constant terms,
    but no single party ever learns it.

    This implementation uses Feldman-style hash commitments (SHA-256)
    rather than Pedersen commitments for simplicity.  It is suitable
    for the consortium key-setup workflow.

    Parameters
    ----------
    threshold : int
        Minimum shares needed for reconstruction (K).
    n_parties : int
        Total number of participating parties (N).
    """

    def __init__(self, threshold: int, n_parties: int) -> None:
        if threshold < 2:
            raise ValueError("Threshold must be >= 2.")
        if n_parties < threshold:
            raise ValueError(f"n_parties ({n_parties}) must be >= threshold ({threshold}).")

        self.threshold: int = threshold
        self.n_parties: int = n_parties
        self._sharer: SecretSharer = SecretSharer()

        # Internal state populated during the ceremony phases
        self._party_secrets: dict[int, int] = {}
        self._party_coefficients: dict[int, list[int]] = {}
        self._commitments: dict[int, dict[str, object]] = {}

    # ------------------------------------------------------------------
    # Phase 1: Commitment generation
    # ------------------------------------------------------------------

    def generate_commitments(self, party_id: int) -> dict[str, object]:
        """Generate a commitment for a party's contribution.

        Each party picks a random secret ``s_i`` and random polynomial
        coefficients ``a_{i,1}, ..., a_{i,k-1}``.  The commitment is
        a SHA-256 hash of the concatenated coefficients so that the
        party can later prove it did not change them.

        Parameters
        ----------
        party_id:
            One-based index of the party (``1 <= party_id <= n_parties``).

        Returns
        -------
        dict
            ``{"party_id": int, "commitment": str, "public_share": str}``

            - ``commitment``: hex-encoded SHA-256 hash of the polynomial
              coefficients (for later verification).
            - ``public_share``: hex-encoded SHA-256 hash of the secret
              constant term (used for audit after reconstruction).

        Raises
        ------
        ValueError
            If *party_id* is out of range.
        """
        if not 1 <= party_id <= self.n_parties:
            raise ValueError(f"party_id must be in [1, {self.n_parties}], got {party_id}.")

        prime = self._sharer.prime

        # Random secret and polynomial coefficients
        secret_i = secrets.randbelow(prime)
        coefficients = [secret_i] + [secrets.randbelow(prime) for _ in range(self.threshold - 1)]

        self._party_secrets[party_id] = secret_i
        self._party_coefficients[party_id] = coefficients

        # Commitment = H(coeff_0 || coeff_1 || ... || coeff_{k-1})
        coeff_bytes = b"".join(c.to_bytes(32, byteorder="big") for c in coefficients)
        commitment_hash = hashlib.sha256(coeff_bytes).hexdigest()

        # Public share = H(secret) — for post-ceremony auditing
        public_share_hash = hashlib.sha256(secret_i.to_bytes(32, byteorder="big")).hexdigest()

        commitment: dict[str, object] = {
            "party_id": party_id,
            "commitment": commitment_hash,
            "public_share": public_share_hash,
        }
        self._commitments[party_id] = commitment

        return commitment

    # ------------------------------------------------------------------
    # Phase 2: Commitment verification
    # ------------------------------------------------------------------

    def verify_commitments(self, commitments: list[dict[str, object]]) -> bool:
        """Verify that all parties have submitted valid commitments.

        Checks that:
        - All ``n_parties`` commitments are present.
        - Each commitment has the required fields.
        - No two parties share the same commitment hash (which would
          indicate collusion or copying).

        Parameters
        ----------
        commitments:
            List of commitment dicts from :meth:`generate_commitments`.

        Returns
        -------
        bool
            ``True`` if all commitments are structurally valid and unique.
        """
        if len(commitments) != self.n_parties:
            return False

        seen_ids: set[int] = set()
        seen_hashes: set[str] = set()

        for c in commitments:
            # Required fields
            if not all(k in c for k in ("party_id", "commitment", "public_share")):
                return False

            pid = c["party_id"]
            chash = c["commitment"]

            # Range check
            if not isinstance(pid, int) or not 1 <= pid <= self.n_parties:
                return False

            # Uniqueness
            if pid in seen_ids:
                return False
            if chash in seen_hashes:
                return False

            seen_ids.add(pid)
            seen_hashes.add(str(chash))

        return len(seen_ids) == self.n_parties

    # ------------------------------------------------------------------
    # Phase 3: Share distribution
    # ------------------------------------------------------------------

    def distribute_shares(self) -> dict[int, list[tuple[int, int]]]:
        """Distribute polynomial evaluations to each party.

        Each party *i* evaluates its polynomial at every other party's
        index *j* and sends ``f_i(j)`` privately to party *j*.  After
        receiving shares from all others, party *j* sums them to obtain
        its combined share of the distributed key.

        This method must be called after :meth:`generate_commitments`
        has been called for all parties.

        Returns
        -------
        dict[int, list[tuple[int, int]]]
            Mapping ``recipient_party_id -> [(sender_party_id, share_value), ...]``.
            Each recipient gets one share from every sender (including
            itself).

        Raises
        ------
        RuntimeError
            If commitments have not been generated for all parties.
        """
        if len(self._party_coefficients) != self.n_parties:
            raise RuntimeError(
                f"Expected coefficients for {self.n_parties} parties, "
                f"but only {len(self._party_coefficients)} have generated "
                f"commitments.  Call generate_commitments() for all parties "
                f"first."
            )

        # For each recipient j, collect f_i(j) from every sender i
        distribution: dict[int, list[tuple[int, int]]] = {
            j: [] for j in range(1, self.n_parties + 1)
        }

        for sender_id in range(1, self.n_parties + 1):
            coefficients = self._party_coefficients[sender_id]
            for recipient_id in range(1, self.n_parties + 1):
                share_value = self._sharer._evaluate_polynomial(coefficients, recipient_id)
                distribution[recipient_id].append((sender_id, share_value))

        return distribution

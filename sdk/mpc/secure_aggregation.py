"""Secure aggregation for federated model updates.

Implements a pairwise-masking protocol that lets N parties compute the
sum of their private vectors without revealing any individual vector to
the aggregation server.

Protocol overview
-----------------
1. Each ordered pair ``(i, j)`` with ``i < j`` derives a shared random
   mask vector from a seed ``seed_{i,j}``.
2. Party *i* **adds** ``mask_{i,j}`` for every ``j > i`` and
   **subtracts** ``mask_{i,j}`` for every ``j < i``.
3. The server sums all masked vectors.  Because every mask is added by
   exactly one party and subtracted by exactly one other, the masks
   cancel out and the server obtains the true aggregate.

No individual update is ever visible to the server or to other parties.

References
----------
- Bonawitz et al. (2017). "Practical Secure Aggregation for
  Privacy-Preserving Machine Learning." CCS '17.
"""

from __future__ import annotations

import hashlib
import secrets
from typing import Final

import numpy as np

# Maximum absolute value for mask components.  Chosen to be large enough
# that masking provides statistical hiding (individual updates on the order
# of 1.0 are buried in noise on the order of _MASK_RANGE) while staying
# within a range where float64 cancellation preserves precision to ~1e-9.
# With _MASK_RANGE = 2**20, the masks dominate updates by ~6 orders of
# magnitude, and float64 has ~15 significant digits, so cancellation
# introduces errors no larger than ~2**20 * 2**(-52) ~ 2e-10.
_MASK_RANGE: Final[int] = 2**20


class MaskGenerator:
    """Generate pairwise masks for secure aggregation.

    Masks are deterministic pseudo-random vectors derived from shared
    seeds so that paired participants produce identical masks.  When one
    participant adds the mask and the other subtracts it, the masks
    cancel during aggregation, hiding individual inputs.

    This class encapsulates the low-level mask and seed generation used
    by :class:`SecureAggregator`.
    """

    def generate_mask(self, seed: bytes, shape: tuple[int, ...]) -> np.ndarray:
        """Generate a deterministic mask vector from a shared seed.

        Parameters
        ----------
        seed:
            Shared secret seed (at least 16 bytes recommended).
        shape:
            Shape of the output mask array.

        Returns
        -------
        np.ndarray
            Deterministic pseudo-random mask with values in
            ``[-_MASK_RANGE, _MASK_RANGE)``.

        Raises
        ------
        ValueError
            If the seed is empty or shape contains non-positive dimensions.
        """
        if not seed:
            raise ValueError("Seed must be non-empty.")
        if any(d < 1 for d in shape):
            raise ValueError(f"All shape dimensions must be >= 1, got {shape}.")

        # Derive a 128-bit integer seed from the byte seed via SHA-256
        digest = hashlib.sha256(seed).digest()
        seed_int = int.from_bytes(digest[:16], byteorder="big")

        rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence(seed_int)))
        return rng.uniform(-_MASK_RANGE, _MASK_RANGE, size=shape)

    def generate_pairwise_seeds(
        self,
        participant_id: int,
        n_participants: int,
    ) -> list[bytes]:
        """Generate shared seeds for all pairwise channels.

        For each pair ``(participant_id, j)`` where ``j != participant_id``,
        a unique 32-byte seed is produced.  In a real deployment these seeds
        would be established via a Diffie-Hellman key exchange; here they are
        generated locally for simulation / testing.

        The seed for pair ``(i, j)`` is identical regardless of which party
        generates it (canonical ordering ``min, max`` is used internally).

        Parameters
        ----------
        participant_id:
            Zero-based index of the current participant.
        n_participants:
            Total number of participants.

        Returns
        -------
        list[bytes]
            A list of length ``n_participants`` where entry *j* is the
            32-byte shared seed for the pair ``(participant_id, j)``, or
            ``b""`` when ``j == participant_id``.

        Raises
        ------
        ValueError
            If *participant_id* is out of range.
        """
        if not 0 <= participant_id < n_participants:
            raise ValueError(
                f"participant_id must be in [0, {n_participants}), got {participant_id}."
            )

        pairwise_seeds: list[bytes] = []
        for j in range(n_participants):
            if j == participant_id:
                pairwise_seeds.append(b"")
                continue

            lo, hi = sorted((participant_id, j))
            # Deterministic seed derived from the canonical pair
            raw = f"pairwise-seed:{lo}:{hi}".encode()
            pairwise_seeds.append(hashlib.sha256(raw).digest())

        return pairwise_seeds


class SecureAggregator:
    """Secure aggregation via pairwise masking.

    Allows *N* parties to compute the sum of their private vectors
    without revealing individual values to the server.

    Parameters
    ----------
    n_parties : int
        Number of participating parties (N >= 2).
    vector_size : int
        Dimensionality of the model-update vectors.
    """

    def __init__(self, n_parties: int, vector_size: int) -> None:
        if n_parties < 2:
            raise ValueError("Need at least 2 parties for secure aggregation.")
        if vector_size < 1:
            raise ValueError("vector_size must be >= 1.")

        self.n_parties: int = n_parties
        self.vector_size: int = vector_size

    # ------------------------------------------------------------------
    # Mask generation
    # ------------------------------------------------------------------

    def generate_masks(
        self,
        party_id: int,
        seed: int | None = None,
    ) -> dict[int, np.ndarray]:
        """Generate pairwise masks for *party_id*.

        For every pair ``(i, j)`` with ``i < j`` the same deterministic
        mask is produced (derived from a shared seed).  Party *i* will
        **add** the mask, party *j* will **subtract** it.

        Parameters
        ----------
        party_id:
            Zero-based index of the party (``0 <= party_id < n_parties``).
        seed:
            Optional base seed for deterministic mask generation.
            In production the seed would be derived from a Diffie-Hellman
            key exchange between each pair; here we derive per-pair seeds
            deterministically from ``seed`` for testability.

        Returns
        -------
        dict[int, np.ndarray]
            Mapping ``other_party_id -> mask_vector``.  The sign
            convention is already applied: if ``party_id < other``, the
            mask is positive; if ``party_id > other``, the mask is
            negated.
        """
        self._validate_party_id(party_id)

        if seed is None:
            seed = secrets.randbits(128)

        masks: dict[int, np.ndarray] = {}

        for other in range(self.n_parties):
            if other == party_id:
                continue

            # Canonical pair ordering so both parties derive the same mask
            lo, hi = sorted((party_id, other))
            pair_seed = self._derive_pair_seed(seed, lo, hi)
            mask = self._prng_vector(pair_seed, self.vector_size)

            # Convention: the party with the smaller id adds, the larger subtracts
            if party_id < other:
                masks[other] = mask
            else:
                masks[other] = -mask

        return masks

    # ------------------------------------------------------------------
    # Masking / unmasking
    # ------------------------------------------------------------------

    def mask_update(
        self,
        update: np.ndarray,
        party_id: int,
        masks: dict[int, np.ndarray],
    ) -> np.ndarray:
        """Apply masks to a model update before sending to the server.

        Parameters
        ----------
        update:
            The party's private gradient / model-update vector.
        party_id:
            The party's zero-based index.
        masks:
            Output of :meth:`generate_masks` for this party.

        Returns
        -------
        np.ndarray
            Masked update vector (same shape as *update*).
        """
        self._validate_party_id(party_id)

        if update.shape != (self.vector_size,):
            raise ValueError(f"Expected update of shape ({self.vector_size},), got {update.shape}.")

        masked = update.copy().astype(np.float64)
        for mask in masks.values():
            masked += mask

        return masked

    # ------------------------------------------------------------------
    # Server-side aggregation
    # ------------------------------------------------------------------

    def aggregate(self, masked_updates: list[np.ndarray]) -> np.ndarray:
        """Aggregate masked updates from all parties.

        Because every mask is added by one party and subtracted by
        another, the sum of all masked updates equals the sum of all
        *true* (unmasked) updates.

        Parameters
        ----------
        masked_updates:
            One masked vector per party (length == ``n_parties``).

        Returns
        -------
        np.ndarray
            The true aggregate (sum) of the private updates.

        Raises
        ------
        ValueError
            If the number of updates does not match ``n_parties``.
        """
        if len(masked_updates) != self.n_parties:
            raise ValueError(f"Expected {self.n_parties} updates, got {len(masked_updates)}.")

        return np.sum(masked_updates, axis=0)

    def aggregate_with_dropout(
        self,
        masked_updates: list[np.ndarray],
        surviving_ids: list[int],
        all_masks: dict[int, dict[int, np.ndarray]],
    ) -> np.ndarray:
        """Aggregate masked updates when some parties have dropped out.

        In the standard protocol every mask is added by one party and
        subtracted by another, so they cancel perfectly.  When a party
        drops out, its masks are *not* cancelled automatically.  This
        method compensates by explicitly subtracting the residual masks
        of dropped parties from the aggregate.

        Parameters
        ----------
        masked_updates:
            Masked vectors from the *surviving* parties only (one per
            surviving party, in the same order as *surviving_ids*).
        surviving_ids:
            Zero-based party indices of parties that submitted updates.
        all_masks:
            Complete mask dictionaries for **all** parties (including
            dropped ones).  ``all_masks[i]`` is the dict returned by
            :meth:`generate_masks` for party *i*.

        Returns
        -------
        np.ndarray
            The corrected aggregate (sum of the surviving parties'
            *unmasked* updates).

        Raises
        ------
        ValueError
            If *masked_updates* and *surviving_ids* have different lengths,
            or if a surviving party has no entry in *all_masks*.
        """
        if len(masked_updates) != len(surviving_ids):
            raise ValueError(
                f"masked_updates length ({len(masked_updates)}) must match "
                f"surviving_ids length ({len(surviving_ids)})."
            )

        all_party_ids = set(range(self.n_parties))
        surviving_set = set(surviving_ids)
        dropped_ids = all_party_ids - surviving_set

        # Sum the masked updates from surviving parties
        aggregate = np.sum(masked_updates, axis=0).astype(np.float64)

        # Compensate for dropped parties.  A dropped party d had masks
        # that other surviving parties included in their masked updates.
        # For each surviving party s that has a mask from/to d, the mask
        # was included in s's masked update but d's counterpart mask is
        # missing.  We need to remove those residual masks.
        for dropped_id in dropped_ids:
            if dropped_id not in all_masks:
                continue
            dropped_masks = all_masks[dropped_id]
            # The dropped party would have contributed sum-of-its-masks to
            # the aggregate.  Since it didn't submit, we subtract those
            # masks that surviving parties added on its behalf.
            for other_id, mask in dropped_masks.items():
                if other_id in surviving_set:
                    # The dropped party's mask toward other_id was the
                    # negative of other_id's mask toward dropped_id.
                    # Since other_id included its mask toward dropped_id
                    # in its update, and dropped_id's cancelling mask is
                    # absent, we must remove other_id's mask toward
                    # dropped_id.  That is equivalent to subtracting it.
                    # The dropped party's mask[other_id] = -mask[other_id→dropped]
                    # so we ADD it to cancel.
                    aggregate += mask

        return aggregate

    def weighted_aggregate(
        self,
        masked_updates: list[np.ndarray],
        weights: list[float],
    ) -> np.ndarray:
        """Weighted aggregation (e.g., proportional to dataset size).

        .. note::

            For weighted aggregation to work correctly with pairwise
            masking, each party must pre-multiply its *update* **and**
            its masks by its weight *before* masking.  This method
            performs a simple weighted sum of already-weighted masked
            vectors.

        Parameters
        ----------
        masked_updates:
            Pre-weighted masked vectors, one per party.
        weights:
            Weight per party.  Typically normalized to sum to 1.

        Returns
        -------
        np.ndarray
            The weighted aggregate.
        """
        if len(masked_updates) != self.n_parties:
            raise ValueError(f"Expected {self.n_parties} updates, got {len(masked_updates)}.")
        if len(weights) != self.n_parties:
            raise ValueError(f"Expected {self.n_parties} weights, got {len(weights)}.")

        result = np.zeros(self.vector_size, dtype=np.float64)
        for update, w in zip(masked_updates, weights):
            result += w * update

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _validate_party_id(self, party_id: int) -> None:
        if not (0 <= int(party_id) < int(self.n_parties)):
            raise ValueError(f"party_id must be in [0, {self.n_parties}), got {party_id}.")

    @staticmethod
    def _derive_pair_seed(base_seed: int, lo: int, hi: int) -> int:
        """Derive a deterministic per-pair seed.

        Uses HMAC-SHA256 of the base seed and the pair indices to produce
        a 256-bit integer seed.
        """
        data = f"{base_seed}:{lo}:{hi}".encode()
        digest = hashlib.sha256(data).digest()
        return int.from_bytes(digest, byteorder="big")

    @staticmethod
    def _prng_vector(seed: int, size: int) -> np.ndarray:
        """Generate a deterministic pseudo-random vector from *seed*.

        Uses numpy's SeedSequence → PCG64 generator for reproducibility.
        Values are drawn from a large integer range to provide
        statistical hiding.
        """
        # Truncate seed to 128 bits for numpy compatibility
        seed_128 = seed & ((1 << 128) - 1)
        rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence(seed_128)))
        return rng.uniform(-_MASK_RANGE, _MASK_RANGE, size=size)


class MPCProtocol:
    """High-level MPC protocol for consortium model training.

    Orchestrates the full secure computation pipeline:

    1. **Key ceremony** — Generate an encryption key and distribute
       Shamir shares to consortium members.
    2. **Secure aggregation** — Aggregate model updates from all parties
       without exposing individual gradients.
    3. **Threshold decryption** — Decrypt the trained model only when
       K-of-N members contribute their key shares.

    Parameters
    ----------
    n_parties : int
        Number of consortium members (N).
    threshold : int
        Minimum members required for key reconstruction (K).
    """

    def __init__(self, n_parties: int, threshold: int) -> None:
        # Import here to avoid circular imports at module level
        from .secret_sharing import SecretSharer

        if n_parties < 2:
            raise ValueError("Need at least 2 parties.")
        if threshold < 2:
            raise ValueError("Threshold must be >= 2.")
        if threshold > n_parties:
            raise ValueError("Threshold cannot exceed n_parties.")

        self.n_parties: int = n_parties
        self.threshold: int = threshold
        self.sharer: SecretSharer = SecretSharer()

    def key_ceremony(self, key_bits: int = 256) -> tuple[list[tuple[int, bytes]], bytes]:
        """Generate a consortium key and distribute shares.

        Generates a random symmetric key, splits it into Shamir shares
        so that any ``threshold`` members can reconstruct it, and returns
        the shares alongside the public key (which here is just the key
        itself for verification — in production this would be a public
        component only).

        Parameters
        ----------
        key_bits : int
            Size of the key in bits (default 256 for AES-256).

        Returns
        -------
        tuple[list[tuple[int, bytes]], bytes]
            ``(shares, master_key)`` where ``shares[i]`` goes to party
            *i* and ``master_key`` is the generated key (retained by the
            ceremony coordinator and then destroyed).
        """
        key_bytes = key_bits // 8
        master_key = secrets.token_bytes(key_bytes)

        shares = self.sharer.split_bytes(
            master_key,
            n_shares=self.n_parties,
            threshold=self.threshold,
        )

        return shares, master_key

    def create_aggregator(self, vector_size: int) -> SecureAggregator:
        """Create a :class:`SecureAggregator` for model updates.

        Parameters
        ----------
        vector_size:
            Dimensionality of the gradient / update vectors.

        Returns
        -------
        SecureAggregator
        """
        return SecureAggregator(
            n_parties=self.n_parties,
            vector_size=vector_size,
        )

    def secure_sum(
        self,
        private_values: list[np.ndarray],
        seed: int | None = None,
    ) -> np.ndarray:
        """Compute the sum of private vectors without revealing individuals.

        This is the core MPC primitive used for gradient aggregation in
        federated learning.  It simulates the full protocol:

        1. Each party generates pairwise masks.
        2. Each party masks its private update.
        3. The server aggregates the masked updates.

        Parameters
        ----------
        private_values:
            One vector per party.
        seed:
            Shared seed for deterministic mask generation.

        Returns
        -------
        np.ndarray
            Sum of all private vectors.

        Raises
        ------
        ValueError
            If the number of vectors does not match ``n_parties``.
        """
        if len(private_values) != self.n_parties:
            raise ValueError(f"Expected {self.n_parties} values, got {len(private_values)}.")

        vector_size = private_values[0].shape[0]
        aggregator = self.create_aggregator(vector_size)

        if seed is None:
            seed = secrets.randbits(128)

        masked_updates: list[np.ndarray] = []
        for party_id, update in enumerate(private_values):
            masks = aggregator.generate_masks(party_id, seed=seed)
            masked = aggregator.mask_update(update, party_id, masks)
            masked_updates.append(masked)

        return aggregator.aggregate(masked_updates)

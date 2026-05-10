"""Tests for the MPC module: secret sharing, secure aggregation, threshold decryption."""

from __future__ import annotations

import itertools
import secrets

import numpy as np
import pytest

from sdk.mpc import (
    SAFE_PRIME,
    KeyCeremony,
    MaskGenerator,
    MPCProtocol,
    SecretSharer,
    SecureAggregator,
    ThresholdDecryptor,
)

# =====================================================================
# SecretSharer
# =====================================================================

class TestSecretSharer:
    """Tests for Shamir's Secret Sharing."""

    def setup_method(self) -> None:
        self.sharer = SecretSharer()

    # --- split / reconstruct (integer) ---

    def test_split_and_reconstruct_basic(self) -> None:
        secret = 42
        shares = self.sharer.split(secret, n_shares=5, threshold=3)
        assert len(shares) == 5
        assert self.sharer.reconstruct(shares[:3]) == secret

    def test_reconstruct_with_more_than_threshold(self) -> None:
        secret = 999999
        shares = self.sharer.split(secret, n_shares=5, threshold=3)
        assert self.sharer.reconstruct(shares[:4]) == secret
        assert self.sharer.reconstruct(shares) == secret

    def test_reconstruct_with_different_subsets(self) -> None:
        secret = 123456789012345678901234567890
        shares = self.sharer.split(secret, n_shares=6, threshold=3)
        # Different 3-element subsets should all reconstruct correctly
        assert self.sharer.reconstruct([shares[0], shares[2], shares[4]]) == secret
        assert self.sharer.reconstruct([shares[1], shares[3], shares[5]]) == secret
        assert self.sharer.reconstruct([shares[0], shares[3], shares[5]]) == secret

    def test_reconstruct_threshold_2(self) -> None:
        secret = 7
        shares = self.sharer.split(secret, n_shares=10, threshold=2)
        assert self.sharer.reconstruct(shares[:2]) == secret

    def test_split_secret_zero(self) -> None:
        shares = self.sharer.split(0, n_shares=3, threshold=2)
        assert self.sharer.reconstruct(shares[:2]) == 0

    def test_insufficient_shares_gives_wrong_result(self) -> None:
        """K-1 shares should not reconstruct the original secret."""
        secret = 42
        shares = self.sharer.split(secret, n_shares=5, threshold=3)
        # Using only 2 of the required 3 shares
        result = self.sharer.reconstruct(shares[:2])
        assert result != secret

    def test_128_bit_secret(self) -> None:
        """A 128-bit secret should split and reconstruct correctly."""
        secret = (1 << 128) - 7  # large 128-bit value
        shares = self.sharer.split(secret, n_shares=5, threshold=3)
        assert self.sharer.reconstruct(shares[:3]) == secret

    def test_split_large_secret(self) -> None:
        # Just below the prime
        secret = SAFE_PRIME - 1
        shares = self.sharer.split(secret, n_shares=5, threshold=3)
        assert self.sharer.reconstruct(shares[:3]) == secret

    # --- split_bytes / reconstruct_bytes ---

    def test_split_and_reconstruct_bytes(self) -> None:
        key = b"\xde\xad\xbe\xef" * 4  # 16 bytes
        shares = self.sharer.split_bytes(key, n_shares=5, threshold=3)
        assert len(shares) == 5
        result = self.sharer.reconstruct_bytes(shares[:3], secret_length=16)
        assert result == key

    def test_split_bytes_32_byte_key(self) -> None:
        key = bytes(range(32))
        shares = self.sharer.split_bytes(key, n_shares=4, threshold=2)
        result = self.sharer.reconstruct_bytes(shares[:2], secret_length=32)
        assert result == key

    def test_split_bytes_different_subsets(self) -> None:
        key = b"secret_key_12345"
        shares = self.sharer.split_bytes(key, n_shares=5, threshold=3)
        r1 = self.sharer.reconstruct_bytes([shares[0], shares[1], shares[2]], secret_length=len(key))
        r2 = self.sharer.reconstruct_bytes([shares[2], shares[3], shares[4]], secret_length=len(key))
        assert r1 == key
        assert r2 == key

    # --- validation ---

    def test_split_negative_secret_raises(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            self.sharer.split(-1, 5, 3)

    def test_split_secret_too_large_raises(self) -> None:
        with pytest.raises(ValueError, match="less than the prime"):
            self.sharer.split(SAFE_PRIME, 5, 3)

    def test_split_threshold_1_raises(self) -> None:
        with pytest.raises(ValueError, match="Threshold must be >= 2"):
            self.sharer.split(42, 5, 1)

    def test_split_n_less_than_threshold_raises(self) -> None:
        with pytest.raises(ValueError, match="n_shares.*must be >= threshold"):
            self.sharer.split(42, 2, 5)

    def test_reconstruct_too_few_shares_raises(self) -> None:
        with pytest.raises(ValueError, match="at least 2"):
            self.sharer.reconstruct([(1, 100)])

    def test_split_bytes_too_large_raises(self) -> None:
        # 33 bytes > 256-bit prime
        big_key = b"\xff" * 33
        with pytest.raises(ValueError, match="too large"):
            self.sharer.split_bytes(big_key, 5, 3)

    # --- custom prime ---

    def test_custom_small_prime(self) -> None:
        sharer = SecretSharer(prime=1000003)
        secret = 500000
        shares = sharer.split(secret, n_shares=5, threshold=3)
        assert sharer.reconstruct(shares[:3]) == secret

    # --- mod_inverse ---

    def test_mod_inverse_basic(self) -> None:
        p = 1000003
        for a in [1, 2, 7, 999, 500001]:
            inv = SecretSharer._mod_inverse(a, p)
            assert (a * inv) % p == 1

    def test_mod_inverse_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="Zero"):
            SecretSharer._mod_inverse(0, 1000003)


# =====================================================================
# SecureAggregator
# =====================================================================

class TestSecureAggregator:
    """Tests for secure aggregation via pairwise masking."""

    def test_masks_cancel_out(self) -> None:
        n_parties = 4
        vector_size = 20
        seed = 12345
        agg = SecureAggregator(n_parties, vector_size)

        rng = np.random.default_rng(0)
        private = [rng.standard_normal(vector_size) for _ in range(n_parties)]
        true_sum = np.sum(private, axis=0)

        masked = []
        for pid in range(n_parties):
            masks = agg.generate_masks(pid, seed=seed)
            m = agg.mask_update(private[pid], pid, masks)
            masked.append(m)

        result = agg.aggregate(masked)
        np.testing.assert_allclose(result, true_sum, atol=1e-6)

    def test_masks_cancel_2_parties(self) -> None:
        agg = SecureAggregator(2, 5)
        v0 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        v1 = np.array([10.0, 20.0, 30.0, 40.0, 50.0])

        m0 = agg.generate_masks(0, seed=99)
        m1 = agg.generate_masks(1, seed=99)

        masked0 = agg.mask_update(v0, 0, m0)
        masked1 = agg.mask_update(v1, 1, m1)

        result = agg.aggregate([masked0, masked1])
        np.testing.assert_allclose(result, v0 + v1, atol=1e-6)

    def test_masks_cancel_many_parties(self) -> None:
        for n in [3, 5, 7, 10]:
            agg = SecureAggregator(n, 8)
            rng = np.random.default_rng(n)
            private = [rng.standard_normal(8) for _ in range(n)]
            true_sum = np.sum(private, axis=0)
            seed = 42

            masked = []
            for pid in range(n):
                masks = agg.generate_masks(pid, seed=seed)
                m = agg.mask_update(private[pid], pid, masks)
                masked.append(m)

            result = agg.aggregate(masked)
            np.testing.assert_allclose(result, true_sum, atol=1e-6)

    def test_weighted_aggregate(self) -> None:
        agg = SecureAggregator(3, 4)
        updates = [
            np.array([1.0, 2.0, 3.0, 4.0]),
            np.array([5.0, 6.0, 7.0, 8.0]),
            np.array([9.0, 10.0, 11.0, 12.0]),
        ]
        weights = [0.5, 0.3, 0.2]
        result = agg.weighted_aggregate(updates, weights)
        expected = 0.5 * updates[0] + 0.3 * updates[1] + 0.2 * updates[2]
        np.testing.assert_allclose(result, expected)

    def test_masked_values_hide_inputs(self) -> None:
        """Masked vectors should differ from the original private inputs."""
        agg = SecureAggregator(3, 10)
        rng = np.random.default_rng(0)
        private = [rng.standard_normal(10) for _ in range(3)]
        seed = 42

        for pid in range(3):
            masks = agg.generate_masks(pid, seed=seed)
            masked = agg.mask_update(private[pid], pid, masks)
            # The masked value should differ significantly from the input
            assert not np.allclose(masked, private[pid], atol=1.0)

    def test_different_seeds_different_masks(self) -> None:
        """Different base seeds produce different mask vectors."""
        agg = SecureAggregator(2, 10)
        masks_a = agg.generate_masks(0, seed=100)
        masks_b = agg.generate_masks(0, seed=200)
        assert not np.array_equal(masks_a[1], masks_b[1])

    def test_wrong_number_of_updates_raises(self) -> None:
        agg = SecureAggregator(3, 5)
        with pytest.raises(ValueError, match="Expected 3"):
            agg.aggregate([np.zeros(5), np.zeros(5)])

    def test_wrong_vector_shape_raises(self) -> None:
        agg = SecureAggregator(2, 5)
        masks = agg.generate_masks(0, seed=1)
        with pytest.raises(ValueError, match="Expected update of shape"):
            agg.mask_update(np.zeros(10), 0, masks)

    def test_invalid_party_id_raises(self) -> None:
        agg = SecureAggregator(3, 5)
        with pytest.raises(ValueError, match="party_id"):
            agg.generate_masks(5, seed=1)

    def test_too_few_parties_raises(self) -> None:
        with pytest.raises(ValueError, match="at least 2"):
            SecureAggregator(1, 5)

    def test_invalid_vector_size_raises(self) -> None:
        with pytest.raises(ValueError, match="vector_size"):
            SecureAggregator(3, 0)

    def test_aggregate_with_dropout(self) -> None:
        """When a party drops out, masks must be compensated."""
        n_parties = 4
        vector_size = 10
        seed = 55
        agg = SecureAggregator(n_parties, vector_size)

        rng = np.random.default_rng(7)
        private = [rng.standard_normal(vector_size) for _ in range(n_parties)]

        # Generate all masks
        all_masks: dict[int, dict[int, np.ndarray]] = {}
        for pid in range(n_parties):
            all_masks[pid] = agg.generate_masks(pid, seed=seed)

        # Party 2 drops out — only parties 0, 1, 3 submit
        surviving_ids = [0, 1, 3]
        masked_updates = []
        for pid in surviving_ids:
            masked = agg.mask_update(private[pid], pid, all_masks[pid])
            masked_updates.append(masked)

        result = agg.aggregate_with_dropout(masked_updates, surviving_ids, all_masks)
        expected = np.sum([private[i] for i in surviving_ids], axis=0)
        np.testing.assert_allclose(result, expected, atol=1e-6)

    def test_aggregate_with_dropout_mismatched_lengths_raises(self) -> None:
        agg = SecureAggregator(3, 5)
        with pytest.raises(ValueError, match="must match"):
            agg.aggregate_with_dropout(
                [np.zeros(5)],
                [0, 1],
                {},
            )


# =====================================================================
# MaskGenerator
# =====================================================================

class TestMaskGenerator:
    """Tests for the MaskGenerator helper class."""

    def setup_method(self) -> None:
        self.gen = MaskGenerator()

    def test_generate_mask_deterministic(self) -> None:
        seed = b"test-seed-1234567890"
        shape = (10,)
        mask1 = self.gen.generate_mask(seed, shape)
        mask2 = self.gen.generate_mask(seed, shape)
        np.testing.assert_array_equal(mask1, mask2)

    def test_generate_mask_different_seeds(self) -> None:
        shape = (10,)
        mask1 = self.gen.generate_mask(b"seed-a", shape)
        mask2 = self.gen.generate_mask(b"seed-b", shape)
        assert not np.array_equal(mask1, mask2)

    def test_generate_mask_shape(self) -> None:
        mask = self.gen.generate_mask(b"seed", (5, 3))
        assert mask.shape == (5, 3)

    def test_generate_mask_empty_seed_raises(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            self.gen.generate_mask(b"", (5,))

    def test_generate_mask_invalid_shape_raises(self) -> None:
        with pytest.raises(ValueError, match="dimensions must be >= 1"):
            self.gen.generate_mask(b"seed", (0,))

    def test_generate_pairwise_seeds(self) -> None:
        seeds = self.gen.generate_pairwise_seeds(0, 3)
        assert len(seeds) == 3
        assert seeds[0] == b""  # self-seed is empty
        assert len(seeds[1]) == 32
        assert len(seeds[2]) == 32

    def test_pairwise_seeds_symmetric(self) -> None:
        """Pair (i,j) and (j,i) should get the same seed."""
        seeds_0 = self.gen.generate_pairwise_seeds(0, 3)
        seeds_1 = self.gen.generate_pairwise_seeds(1, 3)
        assert seeds_0[1] == seeds_1[0]

    def test_pairwise_seeds_invalid_id_raises(self) -> None:
        with pytest.raises(ValueError, match="participant_id"):
            self.gen.generate_pairwise_seeds(5, 3)


# =====================================================================
# ThresholdDecryptor
# =====================================================================

class TestThresholdDecryptor:
    """Tests for threshold decryption."""

    def test_setup_creates_correct_shares(self) -> None:
        """setup() generates exactly N shares."""
        td = ThresholdDecryptor(threshold=3, total_parties=5)
        key_shares, verification = td.setup()
        assert len(key_shares) == 5
        # Each share should have a valid index (1-based) and non-empty bytes
        for idx, share_bytes in key_shares:
            assert 1 <= idx <= 5
            assert len(share_bytes) > 0

    def test_encrypt_decrypt_roundtrip(self) -> None:
        key = bytes(range(32))
        plaintext = b"Hello, consortium!"
        ciphertext = ThresholdDecryptor.encrypt(plaintext, key)
        assert ciphertext != plaintext
        decrypted = ThresholdDecryptor.decrypt(ciphertext, key)
        assert decrypted == plaintext

    def test_decrypt_wrong_key_raises(self) -> None:
        key = bytes(range(32))
        wrong_key = bytes(range(1, 33))
        ciphertext = ThresholdDecryptor.encrypt(b"secret", key)
        with pytest.raises(ValueError, match="Authentication failed"):
            ThresholdDecryptor.decrypt(ciphertext, wrong_key)

    def test_encrypt_requires_32_byte_key(self) -> None:
        with pytest.raises(ValueError, match="Key must be 32 bytes"):
            ThresholdDecryptor.encrypt(b"data", b"short_key")

    def test_setup_and_threshold_decrypt(self) -> None:
        td = ThresholdDecryptor(threshold=3, total_parties=5)
        key_shares, verification = td.setup()
        assert len(key_shares) == 5

        # Reconstruct key to encrypt
        sharer = SecretSharer()
        master_key = sharer.reconstruct_bytes(key_shares[:3], secret_length=32)
        plaintext = b"Trained model weights go here."
        ciphertext = td.encrypt(plaintext, master_key)

        # Each party creates a partial decryption
        partials = [td.partial_decrypt(share, ciphertext) for share in key_shares[:3]]

        # Combine
        decrypted = td.combine_partial_decryptions(partials, ciphertext)
        assert decrypted == plaintext

    def test_threshold_decrypt_different_subsets(self) -> None:
        td = ThresholdDecryptor(threshold=3, total_parties=5)
        key_shares, _ = td.setup()

        sharer = SecretSharer()
        master_key = sharer.reconstruct_bytes(key_shares[:3], secret_length=32)
        plaintext = b"Another secret message."
        ciphertext = td.encrypt(plaintext, master_key)

        # Use shares 2, 3, 4 (different subset)
        partials = [td.partial_decrypt(key_shares[i], ciphertext) for i in [1, 2, 3]]
        decrypted = td.combine_partial_decryptions(partials, ciphertext)
        assert decrypted == plaintext

    def test_too_few_partials_raises(self) -> None:
        td = ThresholdDecryptor(threshold=3, total_parties=5)
        with pytest.raises(ValueError, match="Need at least 3"):
            td.combine_partial_decryptions([b"x" * 40, b"y" * 40], b"ciphertext")

    def test_verify_share(self) -> None:
        td = ThresholdDecryptor(threshold=2, total_parties=3)
        key_shares, verification = td.setup()
        for share in key_shares:
            assert td.verify_share(share, verification) is True

    def test_verify_share_bad_index(self) -> None:
        td = ThresholdDecryptor(threshold=2, total_parties=3)
        _, verification = td.setup()
        assert td.verify_share((0, b"\x01" * 32), verification) is False
        assert td.verify_share((100, b"\x01" * 32), verification) is False

    def test_invalid_threshold_raises(self) -> None:
        with pytest.raises(ValueError, match="Threshold must be >= 2"):
            ThresholdDecryptor(threshold=1, total_parties=3)

    def test_total_less_than_threshold_raises(self) -> None:
        with pytest.raises(ValueError, match="total_parties.*must be >= threshold"):
            ThresholdDecryptor(threshold=5, total_parties=3)

    def test_short_ciphertext_raises(self) -> None:
        with pytest.raises(ValueError, match="too short"):
            ThresholdDecryptor.decrypt(b"short", bytes(32))


# =====================================================================
# MPCProtocol
# =====================================================================

class TestMPCProtocol:
    """Tests for the high-level MPC protocol."""

    def test_key_ceremony(self) -> None:
        protocol = MPCProtocol(n_parties=5, threshold=3)
        shares, master_key = protocol.key_ceremony()
        assert len(shares) == 5
        assert len(master_key) == 32

        # Verify reconstruction
        sharer = SecretSharer()
        reconstructed = sharer.reconstruct_bytes(shares[:3], secret_length=32)
        assert reconstructed == master_key

    def test_secure_sum_equals_true_sum(self) -> None:
        protocol = MPCProtocol(n_parties=4, threshold=2)
        rng = np.random.default_rng(42)
        values = [rng.standard_normal(16) for _ in range(4)]
        true_sum = np.sum(values, axis=0)
        result = protocol.secure_sum(values, seed=100)
        np.testing.assert_allclose(result, true_sum, atol=1e-6)

    def test_secure_sum_wrong_party_count_raises(self) -> None:
        protocol = MPCProtocol(n_parties=3, threshold=2)
        with pytest.raises(ValueError, match="Expected 3"):
            protocol.secure_sum([np.zeros(5), np.zeros(5)])

    def test_create_aggregator(self) -> None:
        protocol = MPCProtocol(n_parties=3, threshold=2)
        agg = protocol.create_aggregator(vector_size=10)
        assert isinstance(agg, SecureAggregator)
        assert agg.n_parties == 3
        assert agg.vector_size == 10

    def test_invalid_params_raises(self) -> None:
        with pytest.raises(ValueError, match="at least 2 parties"):
            MPCProtocol(n_parties=1, threshold=1)
        with pytest.raises(ValueError, match="Threshold must be >= 2"):
            MPCProtocol(n_parties=3, threshold=1)
        with pytest.raises(ValueError, match="Threshold cannot exceed"):
            MPCProtocol(n_parties=3, threshold=5)


# =====================================================================
# Integration
# =====================================================================

class TestMPCIntegration:
    """End-to-end integration tests."""

    def test_full_consortium_workflow(self) -> None:
        """Simulate a complete consortium training round."""
        n_parties = 4
        threshold = 3

        # 1. Setup: key ceremony
        protocol = MPCProtocol(n_parties=n_parties, threshold=threshold)
        key_shares, master_key = protocol.key_ceremony()

        # 2. Each party trains locally and produces a gradient
        rng = np.random.default_rng(0)
        gradients = [rng.standard_normal(50) for _ in range(n_parties)]
        true_aggregate = np.sum(gradients, axis=0)

        # 3. Secure aggregation
        aggregate = protocol.secure_sum(gradients, seed=7)
        np.testing.assert_allclose(aggregate, true_aggregate, atol=1e-6)

        # 4. Encrypt the aggregate with the consortium key
        td = ThresholdDecryptor(threshold=threshold, total_parties=n_parties)
        aggregate_bytes = aggregate.tobytes()
        ciphertext = td.encrypt(aggregate_bytes, master_key)

        # 5. Threshold decryption (3 of 4 parties)
        [td.partial_decrypt(key_shares[i], ciphertext) for i in [0, 1, 3]]

        # We need the partial decryptions to reconstruct the key and decrypt
        # The combine method does this internally
        # But first we need shares from the original key_ceremony shares
        sharer = SecretSharer()
        reconstructed_key = sharer.reconstruct_bytes(
            [key_shares[i] for i in [0, 1, 3]],
            secret_length=32,
        )
        assert reconstructed_key == master_key

        decrypted_bytes = td.decrypt(ciphertext, reconstructed_key)
        decrypted_aggregate = np.frombuffer(decrypted_bytes, dtype=np.float64)
        np.testing.assert_allclose(decrypted_aggregate, aggregate, atol=1e-12)

    def test_key_share_reconstruction_is_deterministic(self) -> None:
        """Any K-subset of shares must reconstruct the same key."""

        sharer = SecretSharer()
        key = b"\x42" * 32
        shares = sharer.split_bytes(key, n_shares=7, threshold=4)

        # Try several 4-element subsets
        for combo in list(itertools.combinations(range(7), 4))[:10]:
            subset = [shares[i] for i in combo]
            result = sharer.reconstruct_bytes(subset, secret_length=32)
            assert result == key, f"Failed for subset {combo}"


# =====================================================================
# ThresholdDecryptor.generate_key_shares
# =====================================================================

class TestGenerateKeyShares:
    """Tests for ThresholdDecryptor.generate_key_shares."""

    def test_generate_and_reconstruct(self) -> None:
        td = ThresholdDecryptor(threshold=3, total_parties=5)
        key = secrets.token_bytes(32)
        shares = td.generate_key_shares(key)
        assert len(shares) == 5

        sharer = SecretSharer()
        reconstructed = sharer.reconstruct_bytes(shares[:3], secret_length=32)
        assert reconstructed == key

    def test_empty_key_raises(self) -> None:
        td = ThresholdDecryptor(threshold=2, total_parties=3)
        with pytest.raises(ValueError, match="non-empty"):
            td.generate_key_shares(b"")


# =====================================================================
# KeyCeremony
# =====================================================================

class TestKeyCeremony:
    """Tests for distributed key generation ceremony."""

    def test_full_ceremony(self) -> None:
        """Run a complete DKG ceremony with 4 parties, threshold 3."""
        n_parties = 4
        threshold = 3
        ceremony = KeyCeremony(threshold=threshold, n_parties=n_parties)

        # Phase 1: Each party generates commitments
        commitments = []
        for pid in range(1, n_parties + 1):
            c = ceremony.generate_commitments(pid)
            commitments.append(c)
            assert "commitment" in c
            assert "public_share" in c
            assert c["party_id"] == pid

        # Phase 2: Verify commitments
        assert ceremony.verify_commitments(commitments) is True

        # Phase 3: Distribute shares
        distribution = ceremony.distribute_shares()
        assert len(distribution) == n_parties

        # Each party should receive n_parties shares (one from each sender)
        for pid in range(1, n_parties + 1):
            assert len(distribution[pid]) == n_parties

    def test_verify_commitments_wrong_count(self) -> None:
        ceremony = KeyCeremony(threshold=2, n_parties=3)
        assert ceremony.verify_commitments([]) is False

    def test_verify_commitments_missing_fields(self) -> None:
        ceremony = KeyCeremony(threshold=2, n_parties=2)
        ceremony.generate_commitments(1)
        ceremony.generate_commitments(2)
        bad_commitments = [{"party_id": 1}, {"party_id": 2}]
        assert ceremony.verify_commitments(bad_commitments) is False

    def test_verify_commitments_duplicate_ids(self) -> None:
        ceremony = KeyCeremony(threshold=2, n_parties=2)
        c1 = ceremony.generate_commitments(1)
        ceremony.generate_commitments(2)
        assert ceremony.verify_commitments([c1, c1]) is False

    def test_distribute_before_commitments_raises(self) -> None:
        ceremony = KeyCeremony(threshold=2, n_parties=3)
        ceremony.generate_commitments(1)
        # Only 1 of 3 parties committed
        with pytest.raises(RuntimeError, match="Expected coefficients"):
            ceremony.distribute_shares()

    def test_invalid_party_id_raises(self) -> None:
        ceremony = KeyCeremony(threshold=2, n_parties=3)
        with pytest.raises(ValueError, match="party_id"):
            ceremony.generate_commitments(0)
        with pytest.raises(ValueError, match="party_id"):
            ceremony.generate_commitments(4)

    def test_invalid_params_raises(self) -> None:
        with pytest.raises(ValueError, match="Threshold must be >= 2"):
            KeyCeremony(threshold=1, n_parties=3)
        with pytest.raises(ValueError, match="n_parties.*must be >= threshold"):
            KeyCeremony(threshold=5, n_parties=3)

    def test_combined_shares_reconstruct_distributed_secret(self) -> None:
        """Verify that combined shares can reconstruct the sum of all secrets."""
        n_parties = 3
        threshold = 2
        ceremony = KeyCeremony(threshold=threshold, n_parties=n_parties)

        for pid in range(1, n_parties + 1):
            ceremony.generate_commitments(pid)

        distribution = ceremony.distribute_shares()

        # Each party sums the shares it receives
        prime = ceremony._sharer.prime
        combined_shares: list[tuple[int, int]] = []
        for recipient_id in range(1, n_parties + 1):
            total = sum(val for _, val in distribution[recipient_id]) % prime
            combined_shares.append((recipient_id, total))

        # The distributed secret is the sum of all individual secrets
        expected_secret = sum(ceremony._party_secrets.values()) % prime

        # Reconstruct from any threshold-size subset
        reconstructed = SecretSharer._lagrange_interpolation(
            combined_shares[:threshold], prime
        )
        assert reconstructed == expected_secret

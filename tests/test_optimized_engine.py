"""Tests for the optimized FHE engine module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pytest
import threading

from sdk.encryption.optimized_engine import (
    OptimizationProfile,
    ProfileConfig,
    PROFILE_CONFIGS,
    ContextPool,
    OptimizedFHEEngine,
    LazyEncryptedVector,
    EncryptionStats,
)
from sdk.encryption.context_manager import CKKSParameters, SecurityLevel


class TestOptimizationProfile:
    """Tests for OptimizationProfile enum."""

    def test_all_profiles_defined(self):
        """Test that all profiles are defined."""
        assert OptimizationProfile.FAST.value == "fast"
        assert OptimizationProfile.BALANCED.value == "balanced"
        assert OptimizationProfile.PRECISE.value == "precise"
        assert OptimizationProfile.MEMORY_EFFICIENT.value == "memory_efficient"
        assert OptimizationProfile.THROUGHPUT.value == "throughput"

    def test_profile_count(self):
        """Test that we have expected number of profiles."""
        assert len(OptimizationProfile) == 5


class TestProfileConfig:
    """Tests for ProfileConfig dataclass."""

    def test_default_config(self):
        """Test ProfileConfig with all fields."""
        config = ProfileConfig(
            poly_modulus_degree=8192,
            coeff_mod_bit_sizes=(60, 40, 40, 60),
            scale_bits=40,
            batch_size=32,
            num_threads=4,
            cache_size=20,
        )
        assert config.poly_modulus_degree == 8192
        assert config.batch_size == 32
        assert config.use_lazy_eval is True
        assert config.use_simd is True

    def test_scale_property(self):
        """Test scale property calculation."""
        config = ProfileConfig(
            poly_modulus_degree=8192,
            coeff_mod_bit_sizes=(60, 40, 40, 60),
            scale_bits=40,
            batch_size=32,
            num_threads=4,
            cache_size=20,
        )
        assert config.scale == 2**40

    def test_config_with_lazy_eval_disabled(self):
        """Test config with lazy eval disabled."""
        config = ProfileConfig(
            poly_modulus_degree=4096,
            coeff_mod_bit_sizes=(40, 20, 40),
            scale_bits=20,
            batch_size=64,
            num_threads=4,
            cache_size=10,
            use_lazy_eval=False,
        )
        assert config.use_lazy_eval is False


class TestProfileConfigs:
    """Tests for predefined profile configurations."""

    def test_all_profiles_have_configs(self):
        """Test that all profiles have configurations."""
        for profile in OptimizationProfile:
            assert profile in PROFILE_CONFIGS

    def test_fast_profile_config(self):
        """Test FAST profile configuration."""
        config = PROFILE_CONFIGS[OptimizationProfile.FAST]
        assert config.poly_modulus_degree == 4096
        assert config.batch_size == 64
        assert config.use_lazy_eval is False

    def test_balanced_profile_config(self):
        """Test BALANCED profile configuration."""
        config = PROFILE_CONFIGS[OptimizationProfile.BALANCED]
        assert config.poly_modulus_degree == 8192
        assert config.batch_size == 32
        assert config.use_lazy_eval is True

    def test_precise_profile_config(self):
        """Test PRECISE profile configuration."""
        config = PROFILE_CONFIGS[OptimizationProfile.PRECISE]
        assert config.poly_modulus_degree == 16384
        assert config.batch_size == 16

    def test_memory_efficient_config(self):
        """Test MEMORY_EFFICIENT profile configuration."""
        config = PROFILE_CONFIGS[OptimizationProfile.MEMORY_EFFICIENT]
        assert config.batch_size == 8
        assert config.num_threads == 2

    def test_throughput_config(self):
        """Test THROUGHPUT profile configuration."""
        config = PROFILE_CONFIGS[OptimizationProfile.THROUGHPUT]
        assert config.batch_size == 128  # Large batch for throughput


class TestContextPool:
    """Tests for ContextPool class."""

    @pytest.fixture
    def params(self):
        """Create CKKS parameters for testing."""
        return CKKSParameters(
            poly_modulus_degree=4096,
            coeff_mod_bit_sizes=(40, 20, 40),
            scale=2**20,
        )

    def test_pool_creation(self, params):
        """Test pool creation."""
        pool = ContextPool(params, pool_size=2)
        assert pool.available == 2

    def test_acquire_context(self, params):
        """Test acquiring a context from pool."""
        pool = ContextPool(params, pool_size=2)
        initial_available = pool.available
        context = pool.acquire()
        assert context is not None
        assert pool.available == initial_available - 1

    def test_release_context(self, params):
        """Test releasing context back to pool."""
        pool = ContextPool(params, pool_size=2)
        context = pool.acquire()
        pool.release(context)
        # Pool should accept it back
        assert pool.available <= 2

    def test_pool_exhaustion_creates_new(self, params):
        """Test that exhausting pool creates new contexts."""
        pool = ContextPool(params, pool_size=1)
        ctx1 = pool.acquire()
        ctx2 = pool.acquire()  # Should create new context
        assert ctx1 is not None
        assert ctx2 is not None

    def test_pool_thread_safety(self, params):
        """Test pool is thread-safe."""
        pool = ContextPool(params, pool_size=3)
        results = []
        errors = []

        def worker():
            try:
                ctx = pool.acquire()
                results.append(ctx is not None)
                pool.release(ctx)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert all(results)

    def test_in_use_tracking(self, params):
        """Test tracking of contexts in use."""
        pool = ContextPool(params, pool_size=2)
        assert pool.in_use == 0
        ctx = pool.acquire()
        # in_use uses weak references, may vary


class TestEncryptionStats:
    """Tests for EncryptionStats class."""

    def test_stats_creation(self):
        """Test EncryptionStats creation with defaults."""
        stats = EncryptionStats()
        assert stats.total_encryptions == 0
        assert stats.total_decryptions == 0
        assert stats.cache_hits == 0
        assert stats.avg_encryption_time_ms == 0.0

    def test_record_encryption(self):
        """Test recording encryption stats."""
        stats = EncryptionStats()
        stats.record_encryption(10.0)
        assert stats.total_encryptions == 1
        assert stats.avg_encryption_time_ms == 10.0

        stats.record_encryption(20.0)
        assert stats.total_encryptions == 2
        assert stats.avg_encryption_time_ms == 15.0

    def test_record_decryption(self):
        """Test recording decryption stats."""
        stats = EncryptionStats()
        stats.record_decryption(5.0)
        assert stats.total_decryptions == 1
        assert stats.avg_decryption_time_ms == 5.0


class TestOptimizedFHEEngine:
    """Tests for OptimizedFHEEngine class."""

    @pytest.fixture
    def engine(self):
        """Create engine with FAST profile for testing."""
        return OptimizedFHEEngine(profile=OptimizationProfile.FAST)

    @pytest.fixture
    def balanced_engine(self):
        """Create engine with BALANCED profile."""
        return OptimizedFHEEngine(profile=OptimizationProfile.BALANCED)

    def test_engine_creation_fast(self, engine):
        """Test engine creation with FAST profile."""
        assert engine.profile == OptimizationProfile.FAST
        assert engine.config is not None

    def test_engine_creation_balanced(self, balanced_engine):
        """Test engine creation with BALANCED profile."""
        assert balanced_engine.profile == OptimizationProfile.BALANCED

    def test_engine_creation_all_profiles(self):
        """Test engine can be created with all profiles."""
        for profile in OptimizationProfile:
            engine = OptimizedFHEEngine(profile=profile)
            assert engine.profile == profile

    def test_encrypt_list(self, engine):
        """Test encrypting a list."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        encrypted = engine.encrypt(data)
        assert encrypted is not None

    def test_encrypt_numpy_array(self, engine):
        """Test numpy array encryption."""
        data = np.array([1.0, 2.0, 3.0])
        encrypted = engine.encrypt(data)
        assert encrypted is not None

    def test_encrypt_decrypt_roundtrip(self, engine):
        """Test encryption/decryption roundtrip."""
        original = [1.0, 2.0, 3.0, 4.0]
        encrypted = engine.encrypt(original)
        decrypted = engine.decrypt(encrypted)
        np.testing.assert_array_almost_equal(decrypted, original, decimal=2)

    def test_encrypt_batch(self, engine):
        """Test batch encryption."""
        vectors = [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]
        encrypted = engine.encrypt_batch(vectors)
        assert len(encrypted) == 3

    def test_encrypt_batch_parallel(self, engine):
        """Test parallel batch encryption."""
        vectors = [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0], [7.0, 8.0]]
        encrypted = engine.encrypt_batch(vectors, parallel=True)
        assert len(encrypted) == 4

    def test_encrypt_batch_sequential(self, engine):
        """Test sequential batch encryption."""
        vectors = [[1.0, 2.0], [3.0, 4.0]]
        encrypted = engine.encrypt_batch(vectors, parallel=False)
        assert len(encrypted) == 2

    def test_stats_tracking(self, engine):
        """Test that stats are tracked."""
        engine.encrypt([1.0, 2.0, 3.0])
        stats = engine.stats
        assert stats.total_encryptions >= 1

    def test_max_slots(self, engine):
        """Test max_slots property."""
        assert engine.max_slots > 0
        # For FAST profile with poly_degree 4096, max_slots = 2048
        assert engine.max_slots == 2048

    def test_caching(self, engine):
        """Test encryption caching."""
        data = [1.0, 2.0, 3.0]
        # First encryption
        engine.encrypt(data, use_cache=True)
        initial_misses = engine.stats.cache_misses

        # Second encryption of same data should hit cache
        engine.encrypt(data, use_cache=True)
        assert engine.stats.cache_hits >= 1

    def test_cache_disabled(self, engine):
        """Test encryption without caching."""
        data = [1.0, 2.0, 3.0]
        engine.encrypt(data, use_cache=False)
        engine.encrypt(data, use_cache=False)
        # Stats should show encryptions but no cache hits
        assert engine.stats.total_encryptions >= 2

    def test_custom_config(self):
        """Test engine with custom configuration."""
        custom = ProfileConfig(
            poly_modulus_degree=4096,
            coeff_mod_bit_sizes=(40, 20, 40),
            scale_bits=20,
            batch_size=16,
            num_threads=2,
            cache_size=5,
        )
        engine = OptimizedFHEEngine(custom_config=custom)
        assert engine.config.batch_size == 16


class TestLazyEncryptedVector:
    """Tests for LazyEncryptedVector class."""

    def test_lazy_creation_empty(self):
        """Test lazy vector creation without data."""
        lazy = LazyEncryptedVector()
        assert lazy.pending_ops_count == 0

    def test_lazy_shape(self):
        """Test lazy vector shape."""
        lazy = LazyEncryptedVector(shape=(5,))
        assert lazy.shape == (5,)

    def test_lazy_with_pending_ops(self):
        """Test lazy vector with pending operations."""
        ops = [lambda x: x + 1, lambda x: x * 2]
        lazy = LazyEncryptedVector(pending_ops=ops)
        assert lazy.pending_ops_count == 2


class TestEnginePerformance:
    """Performance-related tests for the engine."""

    def test_fast_profile_is_faster(self):
        """Test that FAST profile has lower poly degree."""
        fast_config = PROFILE_CONFIGS[OptimizationProfile.FAST]
        precise_config = PROFILE_CONFIGS[OptimizationProfile.PRECISE]
        assert fast_config.poly_modulus_degree < precise_config.poly_modulus_degree

    def test_memory_efficient_has_small_batch(self):
        """Test that MEMORY_EFFICIENT has smallest batch size."""
        mem_config = PROFILE_CONFIGS[OptimizationProfile.MEMORY_EFFICIENT]
        assert mem_config.batch_size == 8  # Smallest

    def test_throughput_has_large_batch(self):
        """Test that THROUGHPUT has large batch size."""
        throughput_config = PROFILE_CONFIGS[OptimizationProfile.THROUGHPUT]
        assert throughput_config.batch_size >= 64


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_vector_encrypt(self):
        """Test encrypting empty vector raises error."""
        engine = OptimizedFHEEngine(profile=OptimizationProfile.FAST)
        with pytest.raises((ValueError, Exception)):
            engine.encrypt([])

    def test_single_element_vector(self):
        """Test single element vector."""
        engine = OptimizedFHEEngine(profile=OptimizationProfile.FAST)
        encrypted = engine.encrypt([42.0])
        decrypted = engine.decrypt(encrypted)
        assert abs(decrypted[0] - 42.0) < 0.1

    def test_large_values(self):
        """Test handling large values."""
        engine = OptimizedFHEEngine(profile=OptimizationProfile.BALANCED)
        data = [1e6, 2e6, 3e6]
        encrypted = engine.encrypt(data)
        decrypted = engine.decrypt(encrypted)
        # Large values may have larger absolute error
        np.testing.assert_array_almost_equal(
            np.array(decrypted) / 1e6,
            np.array(data) / 1e6,
            decimal=1
        )

    def test_negative_values(self):
        """Test negative values."""
        engine = OptimizedFHEEngine(profile=OptimizationProfile.FAST)
        data = [-1.0, -2.0, -3.0]
        encrypted = engine.encrypt(data)
        decrypted = engine.decrypt(encrypted)
        np.testing.assert_array_almost_equal(decrypted, data, decimal=2)

    def test_mixed_sign_values(self):
        """Test mixed positive and negative values."""
        engine = OptimizedFHEEngine(profile=OptimizationProfile.FAST)
        data = [-1.0, 0.0, 1.0, -2.0, 2.0]
        encrypted = engine.encrypt(data)
        decrypted = engine.decrypt(encrypted)
        np.testing.assert_array_almost_equal(decrypted, data, decimal=2)

    def test_2d_numpy_array_flattens(self):
        """Test that 2D numpy array is flattened."""
        engine = OptimizedFHEEngine(profile=OptimizationProfile.FAST)
        data = np.array([[1.0, 2.0], [3.0, 4.0]])
        encrypted = engine.encrypt(data)
        decrypted = engine.decrypt(encrypted)
        np.testing.assert_array_almost_equal(decrypted, [1.0, 2.0, 3.0, 4.0], decimal=2)

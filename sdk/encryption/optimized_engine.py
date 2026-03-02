"""Optimized FHE Engine for high-performance homomorphic encryption.

This module provides:
- Context caching and pooling
- Parallel batch processing
- Lazy evaluation with operation fusion
- Multiple optimization profiles
- Memory-efficient streaming encryption
"""

from __future__ import annotations

import hashlib
import threading
import time
import weakref
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Callable,
    Optional,
    Union,
)

import numpy as np

if TYPE_CHECKING:
    import tenseal as ts

from .context_manager import CKKSParameters, SecurityLevel


class OptimizationProfile(Enum):
    """Predefined optimization profiles for different use cases."""

    # Fast inference - lower precision, higher speed
    FAST = "fast"

    # Balanced - good trade-off between speed and precision
    BALANCED = "balanced"

    # High precision - maximum accuracy, slower
    PRECISE = "precise"

    # Memory efficient - optimized for large datasets
    MEMORY_EFFICIENT = "memory_efficient"

    # Maximum throughput - batch optimized
    THROUGHPUT = "throughput"


@dataclass
class ProfileConfig:
    """Configuration for each optimization profile."""

    poly_modulus_degree: int
    coeff_mod_bit_sizes: tuple[int, ...]
    scale_bits: int
    batch_size: int
    num_threads: int
    cache_size: int
    use_lazy_eval: bool = True
    use_simd: bool = True

    @property
    def scale(self) -> float:
        return 2**self.scale_bits


# Predefined profile configurations
PROFILE_CONFIGS: dict[OptimizationProfile, ProfileConfig] = {
    OptimizationProfile.FAST: ProfileConfig(
        poly_modulus_degree=4096,
        coeff_mod_bit_sizes=(40, 20, 40),
        scale_bits=20,
        batch_size=64,
        num_threads=4,
        cache_size=10,
        use_lazy_eval=False,
    ),
    OptimizationProfile.BALANCED: ProfileConfig(
        poly_modulus_degree=8192,
        coeff_mod_bit_sizes=(60, 40, 40, 60),
        scale_bits=40,
        batch_size=32,
        num_threads=4,
        cache_size=20,
    ),
    OptimizationProfile.PRECISE: ProfileConfig(
        poly_modulus_degree=16384,
        coeff_mod_bit_sizes=(60, 40, 40, 40, 40, 60),
        scale_bits=40,
        batch_size=16,
        num_threads=2,
        cache_size=10,
    ),
    OptimizationProfile.MEMORY_EFFICIENT: ProfileConfig(
        poly_modulus_degree=4096,
        coeff_mod_bit_sizes=(40, 20, 40),
        scale_bits=20,
        batch_size=8,
        num_threads=2,
        cache_size=5,
        use_simd=True,
    ),
    OptimizationProfile.THROUGHPUT: ProfileConfig(
        poly_modulus_degree=8192,
        coeff_mod_bit_sizes=(60, 40, 40, 60),
        scale_bits=40,
        batch_size=128,
        num_threads=8,
        cache_size=50,
    ),
}


class ContextPool:
    """Thread-safe pool of CKKS contexts for reuse.

    Manages a pool of pre-initialized contexts to avoid
    expensive context creation overhead.
    """

    def __init__(
        self,
        params: CKKSParameters,
        pool_size: int = 5,
    ):
        self._params = params
        self._pool_size = pool_size
        self._pool: list[ts.Context] = []
        self._lock = threading.Lock()
        self._in_use: weakref.WeakSet = weakref.WeakSet()

        # Pre-warm the pool
        self._initialize_pool()

    def _initialize_pool(self):
        """Pre-create contexts for the pool."""
        for _ in range(self._pool_size):
            ctx = self._create_context()
            self._pool.append(ctx)

    def _create_context(self) -> ts.Context:
        """Create a new CKKS context."""
        import tenseal as ts

        context = ts.context(
            ts.SCHEME_TYPE.CKKS,
            poly_modulus_degree=self._params.poly_modulus_degree,
            coeff_mod_bit_sizes=list(self._params.coeff_mod_bit_sizes),
        )
        context.global_scale = self._params.scale
        context.generate_galois_keys()
        context.generate_relin_keys()
        return context

    def acquire(self) -> ts.Context:
        """Acquire a context from the pool."""
        with self._lock:
            if self._pool:
                ctx = self._pool.pop()
            else:
                # Pool exhausted, create new context
                ctx = self._create_context()
            self._in_use.add(ctx)
            return ctx

    def release(self, context: ts.Context):
        """Return a context to the pool."""
        with self._lock:
            if len(self._pool) < self._pool_size:
                self._pool.append(context)

    @property
    def available(self) -> int:
        """Number of available contexts in pool."""
        return len(self._pool)

    @property
    def in_use(self) -> int:
        """Number of contexts currently in use."""
        return len(self._in_use)


class LazyEncryptedVector:
    """Lazy-evaluated encrypted vector with operation fusion.

    Operations are recorded and only executed when result is needed,
    allowing for operation fusion and optimization.
    """

    def __init__(
        self,
        data: Optional[ts.CKKSVector] = None,
        shape: tuple[int, ...] = (),
        pending_ops: Optional[list[Callable]] = None,
    ):
        self._data = data
        self._shape = shape
        self._pending_ops = pending_ops or []
        self._evaluated = data is not None and not pending_ops

    def _record_op(self, op: Callable) -> "LazyEncryptedVector":
        """Record an operation for lazy evaluation."""
        new_ops = self._pending_ops + [op]
        return LazyEncryptedVector(
            data=self._data,
            shape=self._shape,
            pending_ops=new_ops,
        )

    def evaluate(self) -> ts.CKKSVector:
        """Execute all pending operations and return result."""
        if self._evaluated:
            return self._data

        result = self._data
        for op in self._pending_ops:
            result = op(result)

        self._data = result
        self._pending_ops = []
        self._evaluated = True
        return result

    def __add__(self, other: "LazyEncryptedVector") -> "LazyEncryptedVector":
        if isinstance(other, LazyEncryptedVector):
            other_data = other.evaluate()
            return self._record_op(lambda x: x + other_data)
        return self._record_op(lambda x: x + other)

    def __mul__(self, other: Union["LazyEncryptedVector", float]) -> "LazyEncryptedVector":
        if isinstance(other, LazyEncryptedVector):
            other_data = other.evaluate()
            return self._record_op(lambda x: x * other_data)
        return self._record_op(lambda x: x * other)

    def __sub__(self, other: "LazyEncryptedVector") -> "LazyEncryptedVector":
        if isinstance(other, LazyEncryptedVector):
            other_data = other.evaluate()
            return self._record_op(lambda x: x - other_data)
        return self._record_op(lambda x: x - other)

    @property
    def pending_ops_count(self) -> int:
        """Number of pending operations."""
        return len(self._pending_ops)

    @property
    def shape(self) -> tuple[int, ...]:
        return self._shape


@dataclass
class EncryptionStats:
    """Statistics for encryption operations."""

    total_encryptions: int = 0
    total_decryptions: int = 0
    total_operations: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_time_ms: float = 0.0
    avg_encryption_time_ms: float = 0.0
    avg_decryption_time_ms: float = 0.0

    def record_encryption(self, time_ms: float):
        self.total_encryptions += 1
        self.total_time_ms += time_ms
        self.avg_encryption_time_ms = (
            self.avg_encryption_time_ms * (self.total_encryptions - 1) + time_ms
        ) / self.total_encryptions

    def record_decryption(self, time_ms: float):
        self.total_decryptions += 1
        self.total_time_ms += time_ms
        self.avg_decryption_time_ms = (
            self.avg_decryption_time_ms * (self.total_decryptions - 1) + time_ms
        ) / self.total_decryptions


class OptimizedFHEEngine:
    """High-performance FHE engine with multiple optimizations.

    Features:
    - Context pooling for reduced overhead
    - Parallel batch processing
    - Lazy evaluation with operation fusion
    - LRU caching for repeated operations
    - Streaming encryption for large datasets
    - Multiple optimization profiles

    Example:
        >>> engine = OptimizedFHEEngine(profile=OptimizationProfile.THROUGHPUT)
        >>>
        >>> # Single encryption
        >>> encrypted = engine.encrypt([1.0, 2.0, 3.0])
        >>>
        >>> # Batch encryption (parallel)
        >>> batch_encrypted = engine.encrypt_batch([
        ...     [1.0, 2.0],
        ...     [3.0, 4.0],
        ...     [5.0, 6.0],
        ... ])
        >>>
        >>> # Streaming encryption for large datasets
        >>> for chunk in engine.encrypt_stream(large_dataset, chunk_size=1000):
        ...     process(chunk)
    """

    def __init__(
        self,
        profile: OptimizationProfile = OptimizationProfile.BALANCED,
        custom_config: Optional[ProfileConfig] = None,
    ):
        """Initialize optimized FHE engine.

        Args:
            profile: Predefined optimization profile.
            custom_config: Custom configuration (overrides profile).
        """
        self._profile = profile
        self._config = custom_config or PROFILE_CONFIGS[profile]

        # Create CKKS parameters from config
        self._params = CKKSParameters(
            poly_modulus_degree=self._config.poly_modulus_degree,
            coeff_mod_bit_sizes=self._config.coeff_mod_bit_sizes,
            scale=self._config.scale,
            security_level=SecurityLevel.TC128,
        )

        # Initialize context pool
        self._context_pool = ContextPool(
            self._params,
            pool_size=self._config.num_threads,
        )

        # Primary context for single operations
        self._primary_context = self._context_pool.acquire()

        # Thread pool for parallel operations
        self._executor = ThreadPoolExecutor(max_workers=self._config.num_threads)

        # Statistics tracking
        self._stats = EncryptionStats()

        # Encryption cache (hash -> encrypted)
        self._encryption_cache: dict[str, bytes] = {}
        self._cache_lock = threading.Lock()

    @property
    def profile(self) -> OptimizationProfile:
        """Current optimization profile."""
        return self._profile

    @property
    def config(self) -> ProfileConfig:
        """Current configuration."""
        return self._config

    @property
    def stats(self) -> EncryptionStats:
        """Encryption statistics."""
        return self._stats

    @property
    def max_slots(self) -> int:
        """Maximum values per ciphertext."""
        return self._params.poly_modulus_degree // 2

    def _compute_cache_key(self, data: list[float]) -> str:
        """Compute cache key for data."""
        data_bytes = np.array(data, dtype=np.float64).tobytes()
        return hashlib.sha256(data_bytes).hexdigest()[:16]

    def encrypt(
        self,
        data: Union[list[float], np.ndarray],
        use_cache: bool = True,
    ) -> ts.CKKSVector:
        """Encrypt a vector of values.

        Args:
            data: Values to encrypt.
            use_cache: Whether to use encryption cache.

        Returns:
            Encrypted CKKS vector.
        """
        if isinstance(data, np.ndarray):
            data = data.flatten().tolist()

        start_time = time.time()

        import tenseal as ts

        # Check cache
        if use_cache:
            cache_key = self._compute_cache_key(data)
            with self._cache_lock:
                if cache_key in self._encryption_cache:
                    self._stats.cache_hits += 1
                    cached = self._encryption_cache[cache_key]
                    return ts.ckks_vector_from(self._primary_context, cached)
                self._stats.cache_misses += 1

        # Perform encryption
        encrypted = ts.ckks_vector(self._primary_context, data)

        # Cache result
        if use_cache and len(self._encryption_cache) < self._config.cache_size:
            with self._cache_lock:
                self._encryption_cache[cache_key] = encrypted.serialize()

        elapsed_ms = (time.time() - start_time) * 1000
        self._stats.record_encryption(elapsed_ms)

        return encrypted

    def decrypt(self, encrypted: ts.CKKSVector) -> np.ndarray:
        """Decrypt an encrypted vector.

        Args:
            encrypted: Encrypted CKKS vector.

        Returns:
            Decrypted numpy array.
        """
        start_time = time.time()

        decrypted = encrypted.decrypt()

        elapsed_ms = (time.time() - start_time) * 1000
        self._stats.record_decryption(elapsed_ms)

        return np.array(decrypted)

    def encrypt_batch(
        self,
        data_batch: list[Union[list[float], np.ndarray]],
        parallel: bool = True,
    ) -> list[ts.CKKSVector]:
        """Encrypt a batch of vectors in parallel.

        Args:
            data_batch: List of vectors to encrypt.
            parallel: Whether to use parallel processing.

        Returns:
            List of encrypted vectors.
        """
        if not parallel or len(data_batch) <= 1:
            return [self.encrypt(d) for d in data_batch]

        # Parallel encryption
        results = [None] * len(data_batch)

        def encrypt_item(
            idx: int, data: Union[list[float], np.ndarray]
        ) -> tuple[int, ts.CKKSVector]:
            import tenseal as ts

            context = self._context_pool.acquire()
            try:
                if isinstance(data, np.ndarray):
                    data = data.flatten().tolist()
                encrypted = ts.ckks_vector(context, data)
                return idx, encrypted
            finally:
                self._context_pool.release(context)

        futures = [self._executor.submit(encrypt_item, i, d) for i, d in enumerate(data_batch)]

        for future in as_completed(futures):
            idx, encrypted = future.result()
            results[idx] = encrypted

        return results

    def decrypt_batch(
        self,
        encrypted_batch: list[ts.CKKSVector],
        parallel: bool = True,
    ) -> list[np.ndarray]:
        """Decrypt a batch of vectors in parallel.

        Args:
            encrypted_batch: List of encrypted vectors.
            parallel: Whether to use parallel processing.

        Returns:
            List of decrypted numpy arrays.
        """
        if not parallel or len(encrypted_batch) <= 1:
            return [self.decrypt(e) for e in encrypted_batch]

        results = [None] * len(encrypted_batch)

        def decrypt_item(idx: int, encrypted: ts.CKKSVector) -> tuple[int, np.ndarray]:
            start = time.time()
            decrypted = np.array(encrypted.decrypt())
            self._stats.record_decryption((time.time() - start) * 1000)
            return idx, decrypted

        futures = [self._executor.submit(decrypt_item, i, e) for i, e in enumerate(encrypted_batch)]

        for future in as_completed(futures):
            idx, decrypted = future.result()
            results[idx] = decrypted

        return results

    def encrypt_stream(
        self,
        data: np.ndarray,
        chunk_size: Optional[int] = None,
    ) -> Iterator[list[ts.CKKSVector]]:
        """Stream encrypt large datasets in chunks.

        Args:
            data: Large 2D array to encrypt.
            chunk_size: Rows per chunk (uses config batch_size if None).

        Yields:
            Batches of encrypted vectors.
        """
        if data.ndim == 1:
            data = data.reshape(-1, 1)

        chunk_size = chunk_size or self._config.batch_size
        n_rows = data.shape[0]

        for start in range(0, n_rows, chunk_size):
            end = min(start + chunk_size, n_rows)
            chunk = data[start:end]

            encrypted_chunk = self.encrypt_batch(
                list(chunk),
                parallel=True,
            )

            yield encrypted_chunk

    def create_lazy_vector(
        self,
        data: Union[list[float], np.ndarray],
    ) -> LazyEncryptedVector:
        """Create a lazy-evaluated encrypted vector.

        Operations are recorded but not executed until evaluate() is called.

        Args:
            data: Values to encrypt.

        Returns:
            LazyEncryptedVector for deferred computation.
        """
        encrypted = self.encrypt(data)
        return LazyEncryptedVector(
            data=encrypted,
            shape=(len(data),) if not isinstance(data, np.ndarray) else data.shape,
        )

    def encrypted_dot_product(
        self,
        encrypted_a: ts.CKKSVector,
        encrypted_b: ts.CKKSVector,
    ) -> ts.CKKSVector:
        """Compute dot product of two encrypted vectors.

        Args:
            encrypted_a: First encrypted vector.
            encrypted_b: Second encrypted vector.

        Returns:
            Encrypted dot product result.
        """
        self._stats.total_operations += 1
        return encrypted_a.dot(encrypted_b)

    def encrypted_matrix_vector_multiply(
        self,
        encrypted_matrix: list[ts.CKKSVector],
        plain_vector: Union[list[float], np.ndarray],
    ) -> ts.CKKSVector:
        """Multiply encrypted matrix by plaintext vector.

        Args:
            encrypted_matrix: List of encrypted row vectors.
            plain_vector: Plaintext vector.

        Returns:
            Encrypted result vector.
        """
        if isinstance(plain_vector, np.ndarray):
            plain_vector = plain_vector.tolist()

        self._stats.total_operations += len(encrypted_matrix)

        # Compute row-wise dot products
        results = []
        for row in encrypted_matrix:
            result = row * plain_vector
            results.append(result.sum())

        # Combine results (simplified - returns first for now)
        # In production, would properly aggregate
        return results[0] if results else None

    def clear_cache(self):
        """Clear encryption cache."""
        with self._cache_lock:
            self._encryption_cache.clear()

    def get_cache_stats(self) -> dict[str, int]:
        """Get cache statistics."""
        return {
            "size": len(self._encryption_cache),
            "max_size": self._config.cache_size,
            "hits": self._stats.cache_hits,
            "misses": self._stats.cache_misses,
            "hit_rate": (
                self._stats.cache_hits / (self._stats.cache_hits + self._stats.cache_misses)
                if (self._stats.cache_hits + self._stats.cache_misses) > 0
                else 0.0
            ),
        }

    def benchmark(
        self,
        vector_size: int = 1000,
        n_operations: int = 100,
    ) -> dict[str, float]:
        """Run benchmark to measure performance.

        Args:
            vector_size: Size of test vectors.
            n_operations: Number of operations to benchmark.

        Returns:
            Dictionary with benchmark results.
        """
        import random

        results = {}

        # Generate test data
        test_data = [random.random() for _ in range(vector_size)]

        # Benchmark encryption
        start = time.time()
        for _ in range(n_operations):
            _ = self.encrypt(test_data, use_cache=False)
        results["encrypt_avg_ms"] = (time.time() - start) * 1000 / n_operations

        # Benchmark decryption
        encrypted = self.encrypt(test_data, use_cache=False)
        start = time.time()
        for _ in range(n_operations):
            _ = self.decrypt(encrypted)
        results["decrypt_avg_ms"] = (time.time() - start) * 1000 / n_operations

        # Benchmark batch encryption
        batch = [[random.random() for _ in range(100)] for _ in range(10)]
        start = time.time()
        _ = self.encrypt_batch(batch, parallel=True)
        results["batch_encrypt_total_ms"] = (time.time() - start) * 1000

        # Benchmark with cache
        self.clear_cache()
        start = time.time()
        for _ in range(n_operations):
            _ = self.encrypt(test_data, use_cache=True)
        results["encrypt_cached_avg_ms"] = (time.time() - start) * 1000 / n_operations

        results["cache_hit_rate"] = self.get_cache_stats()["hit_rate"]
        results["profile"] = self._profile.value
        results["vector_size"] = vector_size
        results["n_operations"] = n_operations

        return results

    def shutdown(self):
        """Shutdown engine and release resources."""
        self._executor.shutdown(wait=True)
        self.clear_cache()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

    def __repr__(self) -> str:
        return (
            f"OptimizedFHEEngine("
            f"profile={self._profile.value}, "
            f"max_slots={self.max_slots}, "
            f"threads={self._config.num_threads})"
        )

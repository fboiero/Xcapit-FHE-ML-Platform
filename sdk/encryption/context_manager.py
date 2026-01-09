"""FHE context management utilities.

This module provides management of CKKS encryption contexts,
including parameter configuration, serialization, and context lifecycle.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import tenseal as ts


class SecurityLevel(Enum):
    """Security levels for CKKS encryption."""

    TC128 = 128  # 128-bit security (default, recommended)
    TC192 = 192  # 192-bit security
    TC256 = 256  # 256-bit security


@dataclass
class CKKSParameters:
    """Configuration parameters for CKKS encryption scheme.

    Attributes:
        poly_modulus_degree: Polynomial modulus degree (power of 2).
            Higher values = more computation depth but slower.
            Common values: 4096, 8192, 16384.
        coeff_mod_bit_sizes: Coefficient modulus bit sizes.
            Determines precision and multiplication depth.
        scale: Scaling factor for encoding (2^scale_bits).
            Affects precision of encrypted computations.
        security_level: Target security level in bits.
    """

    poly_modulus_degree: int = 8192
    coeff_mod_bit_sizes: tuple = (60, 40, 40, 60)
    scale: float = 2**40
    security_level: SecurityLevel = SecurityLevel.TC128

    def __post_init__(self):
        """Validate parameters after initialization."""
        valid_degrees = {1024, 2048, 4096, 8192, 16384, 32768}
        if self.poly_modulus_degree not in valid_degrees:
            raise ValueError(
                f"poly_modulus_degree must be one of {valid_degrees}, "
                f"got {self.poly_modulus_degree}"
            )

        if not self.coeff_mod_bit_sizes:
            raise ValueError("coeff_mod_bit_sizes cannot be empty")

        if self.scale <= 0:
            raise ValueError("scale must be positive")


class FHEContextManager:
    """Manages CKKS encryption context lifecycle.

    This class handles creation, configuration, and serialization of
    TenSEAL CKKS contexts for homomorphic encryption operations.

    Example:
        >>> manager = FHEContextManager()
        >>> context = manager.create_context()
        >>> # Use context for encryption...
        >>> serialized = manager.serialize()
        >>> # Later, restore context
        >>> manager.load(serialized)
    """

    # Default parameters optimized for ML workloads
    DEFAULT_PARAMS = CKKSParameters(
        poly_modulus_degree=8192,
        coeff_mod_bit_sizes=(60, 40, 40, 60),
        scale=2**40,
        security_level=SecurityLevel.TC128,
    )

    def __init__(self, params: Optional[CKKSParameters] = None):
        """Initialize context manager with given parameters.

        Args:
            params: CKKS parameters. Uses defaults if not provided.
        """
        self._params = params or self.DEFAULT_PARAMS
        self._context: Optional[ts.Context] = None
        self._secret_key: Optional[bytes] = None

    @property
    def params(self) -> CKKSParameters:
        """Get current CKKS parameters."""
        return self._params

    @property
    def context(self) -> Optional[ts.Context]:
        """Get the TenSEAL context (None if not created)."""
        return self._context

    @property
    def is_initialized(self) -> bool:
        """Check if context has been created."""
        return self._context is not None

    def create_context(
        self,
        generate_galois_keys: bool = True,
        generate_relin_keys: bool = True,
    ) -> ts.Context:
        """Create a new CKKS encryption context.

        Args:
            generate_galois_keys: Generate keys for rotation operations.
                Required for vector operations in ML.
            generate_relin_keys: Generate keys for relinearization.
                Required for multiplication operations.

        Returns:
            Configured TenSEAL CKKS context.
        """
        self._context = ts.context(
            ts.SCHEME_TYPE.CKKS,
            poly_modulus_degree=self._params.poly_modulus_degree,
            coeff_mod_bit_sizes=list(self._params.coeff_mod_bit_sizes),
        )

        self._context.global_scale = self._params.scale

        if generate_galois_keys:
            self._context.generate_galois_keys()

        if generate_relin_keys:
            self._context.generate_relin_keys()

        return self._context

    def make_context_public(self) -> None:
        """Remove secret key from context, making it public.

        After calling this, the context can only encrypt/compute,
        not decrypt. Useful for sending to untrusted parties.
        """
        if not self.is_initialized:
            raise RuntimeError("Context not initialized. Call create_context() first.")

        # Save secret key before making public
        self._secret_key = self._context.secret_key().serialize()
        self._context.make_context_public()

    def serialize(self, include_secret_key: bool = True) -> bytes:
        """Serialize context to bytes for storage/transmission.

        Args:
            include_secret_key: Whether to include secret key.
                Set False for sharing with untrusted parties.

        Returns:
            Serialized context as bytes.
        """
        if not self.is_initialized:
            raise RuntimeError("Context not initialized. Call create_context() first.")

        if not include_secret_key:
            # Create a copy without secret key
            public_ctx = self._context.copy()
            public_ctx.make_context_public()
            return public_ctx.serialize()

        # TenSEAL requires explicit flag to save secret key
        return self._context.serialize(save_secret_key=True)

    def load(self, serialized: bytes) -> ts.Context:
        """Load context from serialized bytes.

        Args:
            serialized: Serialized context bytes.

        Returns:
            Loaded TenSEAL context.
        """
        self._context = ts.context_from(serialized)
        return self._context

    def save_to_file(self, path: str, include_secret_key: bool = True) -> None:
        """Save context to file.

        Args:
            path: File path to save context.
            include_secret_key: Whether to include secret key.
        """
        serialized = self.serialize(include_secret_key=include_secret_key)
        with open(path, "wb") as f:
            f.write(serialized)

    def load_from_file(self, path: str) -> ts.Context:
        """Load context from file.

        Args:
            path: File path to load context from.

        Returns:
            Loaded TenSEAL context.
        """
        with open(path, "rb") as f:
            serialized = f.read()
        return self.load(serialized)

    def get_max_slots(self) -> int:
        """Get maximum number of slots available for SIMD operations.

        In CKKS, poly_modulus_degree/2 values can be packed into
        a single ciphertext (SIMD batching).

        Returns:
            Maximum number of slots.
        """
        return self._params.poly_modulus_degree // 2

    def __repr__(self) -> str:
        status = "initialized" if self.is_initialized else "not initialized"
        return (
            f"FHEContextManager("
            f"poly_degree={self._params.poly_modulus_degree}, "
            f"scale=2^{int(self._params.scale).bit_length() - 1}, "
            f"status={status})"
        )

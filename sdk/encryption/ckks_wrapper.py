"""CKKS encryption scheme wrapper.

This module provides high-level encryption/decryption operations
using the CKKS homomorphic encryption scheme via TenSEAL.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

import numpy as np

if TYPE_CHECKING:
    import tenseal as ts

from .context_manager import CKKSParameters, FHEContextManager


class EncryptedVector:
    """Wrapper for encrypted CKKS vectors with metadata.

    This class wraps TenSEAL CKKSVector and provides additional
    functionality for ML operations.
    """

    def __init__(self, ciphertext: ts.CKKSVector, shape: tuple):
        """Initialize encrypted vector.

        Args:
            ciphertext: TenSEAL CKKSVector.
            shape: Original shape of the data.
        """
        self._ciphertext = ciphertext
        self._shape = shape

    @property
    def ciphertext(self) -> ts.CKKSVector:
        """Get underlying TenSEAL ciphertext."""
        return self._ciphertext

    @property
    def shape(self) -> tuple:
        """Get original shape of encrypted data."""
        return self._shape

    def serialize(self) -> bytes:
        """Serialize encrypted vector to bytes."""
        return self._ciphertext.serialize()

    @classmethod
    def deserialize(
        cls,
        data: bytes,
        context: ts.Context,
        shape: tuple,
    ) -> "EncryptedVector":
        """Deserialize encrypted vector from bytes.

        Args:
            data: Serialized ciphertext bytes.
            context: TenSEAL context for deserialization.
            shape: Original shape of the data.

        Returns:
            EncryptedVector instance.
        """
        import tenseal as ts

        ciphertext = ts.ckks_vector_from(context, data)
        return cls(ciphertext, shape)

    def __add__(self, other: "EncryptedVector") -> "EncryptedVector":
        """Add two encrypted vectors."""
        result = self._ciphertext + other._ciphertext
        return EncryptedVector(result, self._shape)

    def __sub__(self, other: "EncryptedVector") -> "EncryptedVector":
        """Subtract two encrypted vectors."""
        result = self._ciphertext - other._ciphertext
        return EncryptedVector(result, self._shape)

    def __mul__(self, other: Union["EncryptedVector", float]) -> "EncryptedVector":
        """Multiply encrypted vector by scalar or another vector."""
        if isinstance(other, EncryptedVector):
            result = self._ciphertext * other._ciphertext
        else:
            result = self._ciphertext * other
        return EncryptedVector(result, self._shape)

    def __neg__(self) -> "EncryptedVector":
        """Negate encrypted vector."""
        result = -self._ciphertext
        return EncryptedVector(result, self._shape)

    def dot(self, other: "EncryptedVector") -> "EncryptedVector":
        """Compute dot product with another encrypted vector."""
        result = self._ciphertext.dot(other._ciphertext)
        return EncryptedVector(result, (1,))

    def sum(self) -> "EncryptedVector":
        """Sum all elements in the encrypted vector."""
        result = self._ciphertext.sum()
        return EncryptedVector(result, (1,))

    def __repr__(self) -> str:
        return f"EncryptedVector(shape={self._shape})"


class EncryptedMatrix:
    """Wrapper for encrypted matrices (list of encrypted row vectors)."""

    def __init__(self, rows: list[EncryptedVector], shape: tuple):
        """Initialize encrypted matrix.

        Args:
            rows: List of EncryptedVector rows.
            shape: Original matrix shape (n_rows, n_cols).
        """
        self._rows = rows
        self._shape = shape

    @property
    def rows(self) -> list[EncryptedVector]:
        """Get encrypted rows."""
        return self._rows

    @property
    def shape(self) -> tuple:
        """Get original matrix shape."""
        return self._shape

    def serialize(self) -> dict:
        """Serialize encrypted matrix to a dict of bytes.

        Returns:
            Dict with serialized rows and metadata.
        """
        return {
            "rows": [row.serialize() for row in self._rows],
            "row_shapes": [row.shape for row in self._rows],
            "shape": self._shape,
        }

    @classmethod
    def deserialize(
        cls,
        data: dict,
        context: ts.Context,
    ) -> "EncryptedMatrix":
        """Deserialize encrypted matrix from dict.

        Args:
            data: Dict with serialized rows and metadata.
            context: TenSEAL context for deserialization.

        Returns:
            EncryptedMatrix instance.
        """
        rows = []
        for row_bytes, row_shape in zip(data["rows"], data["row_shapes"]):
            row = EncryptedVector.deserialize(row_bytes, context, row_shape)
            rows.append(row)
        return cls(rows, data["shape"])

    def __getitem__(self, idx: int) -> EncryptedVector:
        """Get row by index."""
        return self._rows[idx]

    def __len__(self) -> int:
        """Get number of rows."""
        return len(self._rows)

    def __iter__(self):
        """Iterate over rows."""
        return iter(self._rows)

    def __repr__(self) -> str:
        return f"EncryptedMatrix(shape={self._shape})"


class CKKSEncryptor:
    """High-level interface for CKKS encryption/decryption.

    This class provides a simple API for encrypting numpy arrays
    and pandas DataFrames using the CKKS scheme.

    Example:
        >>> encryptor = CKKSEncryptor()
        >>> encrypted = encryptor.encrypt_vector([1.0, 2.0, 3.0])
        >>> decrypted = encryptor.decrypt_vector(encrypted)
    """

    def __init__(
        self,
        context_manager: Optional[FHEContextManager] = None,
        params: Optional[CKKSParameters] = None,
    ):
        """Initialize CKKS encryptor.

        Args:
            context_manager: Pre-configured context manager.
                If None, creates new one with given params.
            params: CKKS parameters (used only if context_manager is None).
        """
        if context_manager is not None:
            self._context_manager = context_manager
        else:
            self._context_manager = FHEContextManager(params)

        if not self._context_manager.is_initialized:
            self._context_manager.create_context()

    @property
    def context(self) -> ts.Context:
        """Get TenSEAL context."""
        return self._context_manager.context

    @property
    def context_manager(self) -> FHEContextManager:
        """Get context manager."""
        return self._context_manager

    @property
    def max_slots(self) -> int:
        """Get maximum number of values per ciphertext."""
        return self._context_manager.get_max_slots()

    def encrypt_vector(
        self,
        data: Union[list[float], np.ndarray],
    ) -> EncryptedVector:
        """Encrypt a 1D vector of values.

        Args:
            data: List or numpy array of float values.

        Returns:
            EncryptedVector containing the encrypted data.

        Raises:
            ValueError: If data exceeds maximum slot count.
        """
        if isinstance(data, np.ndarray):
            data = data.flatten().tolist()

        if len(data) > self.max_slots:
            raise ValueError(
                f"Data length {len(data)} exceeds max slots {self.max_slots}. "
                "Consider using encrypt_matrix for larger data."
            )

        import tenseal as ts

        ciphertext = ts.ckks_vector(self.context, data)
        return EncryptedVector(ciphertext, (len(data),))

    def decrypt_vector(self, encrypted: EncryptedVector) -> np.ndarray:
        """Decrypt an encrypted vector.

        Args:
            encrypted: EncryptedVector to decrypt.

        Returns:
            Numpy array of decrypted values.
        """
        decrypted = encrypted.ciphertext.decrypt()
        return np.array(decrypted[: encrypted.shape[0]])

    def encrypt_matrix(
        self,
        data: Union[list[list[float]], np.ndarray],
    ) -> EncryptedMatrix:
        """Encrypt a 2D matrix (row-wise encryption).

        Each row is encrypted as a separate ciphertext, allowing
        for efficient row-wise operations common in ML.

        Args:
            data: 2D list or numpy array.

        Returns:
            EncryptedMatrix containing encrypted rows.
        """
        if isinstance(data, list):
            data = np.array(data)

        if data.ndim != 2:
            raise ValueError(f"Expected 2D array, got {data.ndim}D")

        n_rows, n_cols = data.shape

        if n_cols > self.max_slots:
            raise ValueError(f"Row length {n_cols} exceeds max slots {self.max_slots}.")

        encrypted_rows = []
        for row in data:
            enc_row = self.encrypt_vector(row)
            encrypted_rows.append(enc_row)

        return EncryptedMatrix(encrypted_rows, (n_rows, n_cols))

    def decrypt_matrix(self, encrypted: EncryptedMatrix) -> np.ndarray:
        """Decrypt an encrypted matrix.

        Args:
            encrypted: EncryptedMatrix to decrypt.

        Returns:
            Numpy array of decrypted values.
        """
        decrypted_rows = []
        for enc_row in encrypted.rows:
            dec_row = self.decrypt_vector(enc_row)
            decrypted_rows.append(dec_row)

        return np.vstack(decrypted_rows)

    def encrypt_scalar(self, value: float) -> EncryptedVector:
        """Encrypt a single scalar value.

        Args:
            value: Scalar float value.

        Returns:
            EncryptedVector containing the scalar.
        """
        return self.encrypt_vector([value])

    def decrypt_scalar(self, encrypted: EncryptedVector) -> float:
        """Decrypt a scalar value.

        Args:
            encrypted: EncryptedVector containing scalar.

        Returns:
            Decrypted float value.
        """
        return float(self.decrypt_vector(encrypted)[0])

    def __repr__(self) -> str:
        return f"CKKSEncryptor(max_slots={self.max_slots})"

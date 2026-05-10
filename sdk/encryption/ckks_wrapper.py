"""CKKS encryption wrapper around TenSEAL."""

from typing import Union

import numpy as np
import tenseal as ts

from .context_manager import CKKSParameters


class EncryptedVector:
    """Wrapper around a TenSEAL CKKS vector."""

    def __init__(self, ciphertext: ts.CKKSVector, shape: tuple):
        self.ciphertext = ciphertext
        self.shape = shape

    def decrypt(self, encryptor: "CKKSEncryptor" = None) -> np.ndarray:
        return np.array(self.ciphertext.decrypt())

    def serialize(self) -> bytes:
        return self.ciphertext.serialize()

    def __len__(self):
        return self.shape[0]


class EncryptedMatrix:
    """A list of EncryptedVectors representing a matrix."""

    def __init__(self, rows: list[EncryptedVector], shape: tuple):
        self._rows = rows
        self._shape = shape

    @property
    def shape(self):
        return self._shape

    @property
    def encryptor(self):
        return getattr(self, "_encryptor", None)

    @encryptor.setter
    def encryptor(self, value):
        self._encryptor = value

    def __iter__(self):
        return iter(self._rows)

    def __len__(self):
        return len(self._rows)

    def __getitem__(self, idx):
        return self._rows[idx]


class CKKSEncryptor:
    """CKKS encryption/decryption operations."""

    def __init__(self, params: CKKSParameters):
        self.params = params
        self.context = params.create_context()

    def encrypt_vector(self, data: Union[list, np.ndarray]) -> EncryptedVector:
        if isinstance(data, np.ndarray):
            data = data.tolist()
        ct = ts.ckks_vector(self.context, data)
        return EncryptedVector(ct, (len(data),))

    def encrypt_matrix(self, data: np.ndarray) -> EncryptedMatrix:
        rows = []
        for i in range(data.shape[0]):
            row_ct = ts.ckks_vector(self.context, data[i].tolist())
            rows.append(EncryptedVector(row_ct, (data.shape[1],)))
        matrix = EncryptedMatrix(rows, data.shape)
        matrix.encryptor = self
        return matrix

    def decrypt_vector(self, encrypted: EncryptedVector) -> np.ndarray:
        return np.array(encrypted.ciphertext.decrypt())

    def decrypt_matrix(self, encrypted: EncryptedMatrix) -> np.ndarray:
        rows = []
        for row in encrypted:
            rows.append(np.array(row.ciphertext.decrypt()))
        return np.array(rows)

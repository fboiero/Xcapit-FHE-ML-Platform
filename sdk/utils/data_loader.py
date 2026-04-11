"""Secure data loader — encrypts DataFrames with CKKS."""

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from ..encryption.ckks_wrapper import CKKSEncryptor, EncryptedMatrix, EncryptedVector
from ..encryption.context_manager import CKKSParameters


@dataclass
class EncryptedDataset:
    """Encrypted feature matrix and target vector."""
    X: EncryptedMatrix
    y: Optional[EncryptedVector]
    n_features: int
    n_samples: int
    feature_names: list[str]


class SecureDataLoader:
    """Loads and encrypts data using CKKS scheme."""

    def __init__(
        self,
        params: Optional[CKKSParameters] = None,
        normalize: bool = True,
    ):
        if params is None:
            params = CKKSParameters()
        self.params = params
        self.normalize = normalize
        self.encryptor = CKKSEncryptor(params)
        self._mean = None
        self._std = None

    def encrypt(
        self,
        df: pd.DataFrame,
        target_column: Optional[str] = None,
    ) -> EncryptedDataset:
        """Encrypt a DataFrame.

        Args:
            df: Input data.
            target_column: Name of target column (excluded from features).

        Returns:
            EncryptedDataset with encrypted X and optional y.
        """
        if target_column and target_column in df.columns:
            feature_cols = [c for c in df.columns if c != target_column]
            X = df[feature_cols].values.astype(np.float64)
            y = df[target_column].values.astype(np.float64)
        else:
            X = df.values.astype(np.float64)
            y = None
            feature_cols = list(df.columns)

        if self.normalize:
            self._mean = X.mean(axis=0)
            self._std = X.std(axis=0)
            self._std[self._std == 0] = 1.0
            X = (X - self._mean) / self._std

        enc_X = self.encryptor.encrypt_matrix(X)
        enc_y = self.encryptor.encrypt_vector(y) if y is not None else None

        return EncryptedDataset(
            X=enc_X,
            y=enc_y,
            n_features=X.shape[1],
            n_samples=X.shape[0],
            feature_names=feature_cols,
        )

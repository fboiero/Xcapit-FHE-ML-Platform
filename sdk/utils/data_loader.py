"""Secure data loading utilities.

This module provides the SecureDataLoader class, the primary interface
for encrypting and decrypting data in the Xcapit FHE-ML SDK.
"""

from dataclasses import dataclass
from typing import Optional, Union

import numpy as np
import pandas as pd

from ..encryption.ckks_wrapper import (
    CKKSEncryptor,
    EncryptedMatrix,
    EncryptedVector,
)
from ..encryption.context_manager import CKKSParameters, FHEContextManager


@dataclass
class EncryptedDataset:
    """Container for encrypted dataset with metadata.

    Attributes:
        X: Encrypted feature matrix.
        y: Encrypted target vector (optional).
        feature_names: Original column names.
        n_samples: Number of samples.
        n_features: Number of features.
        normalization_params: Parameters used for normalization.
    """

    X: EncryptedMatrix
    y: Optional[EncryptedVector]
    feature_names: list[str]
    n_samples: int
    n_features: int
    normalization_params: Optional[dict] = None

    def __repr__(self) -> str:
        has_y = "with" if self.y is not None else "without"
        return (
            f"EncryptedDataset("
            f"samples={self.n_samples}, "
            f"features={self.n_features}, "
            f"{has_y} target)"
        )


class SecureDataLoader:
    """High-level interface for encrypting datasets.

    SecureDataLoader provides a simple API for encrypting pandas DataFrames
    and numpy arrays for use with FHE-ML models.

    Example:
        >>> loader = SecureDataLoader()
        >>> encrypted_data = loader.encrypt(df)
        >>> # Train model on encrypted_data...
        >>> result = loader.decrypt(encrypted_prediction)

    Attributes:
        encryption_scheme: Encryption scheme name (currently only "CKKS").
    """

    SUPPORTED_SCHEMES = {"CKKS"}

    def __init__(
        self,
        encryption_scheme: str = "CKKS",
        params: Optional[CKKSParameters] = None,
        normalize: bool = True,
    ):
        """Initialize SecureDataLoader.

        Args:
            encryption_scheme: Encryption scheme to use. Currently only "CKKS".
            params: Custom CKKS parameters. Uses optimized defaults if None.
            normalize: Whether to normalize data before encryption.
                Normalization improves FHE computation accuracy.
        """
        if encryption_scheme not in self.SUPPORTED_SCHEMES:
            raise ValueError(
                f"Unsupported encryption scheme: {encryption_scheme}. "
                f"Supported: {self.SUPPORTED_SCHEMES}"
            )

        self._scheme = encryption_scheme
        self._normalize = normalize
        self._context_manager = FHEContextManager(params)
        self._context_manager.create_context()
        self._encryptor = CKKSEncryptor(self._context_manager)
        self._normalization_params: dict = {}

    @property
    def encryption_scheme(self) -> str:
        """Get the encryption scheme name."""
        return self._scheme

    @property
    def encryptor(self) -> CKKSEncryptor:
        """Get the underlying encryptor."""
        return self._encryptor

    @property
    def context_manager(self) -> FHEContextManager:
        """Get the context manager."""
        return self._context_manager

    def _normalize_data(
        self,
        data: np.ndarray,
        fit: bool = True,
    ) -> tuple[np.ndarray, dict]:
        """Normalize data to [-1, 1] range for better FHE precision.

        Args:
            data: Input data array.
            fit: If True, compute normalization params. If False, use stored.

        Returns:
            Tuple of (normalized_data, normalization_params).
        """
        if fit:
            min_vals = data.min(axis=0)
            max_vals = data.max(axis=0)
            # Avoid division by zero
            ranges = max_vals - min_vals
            ranges[ranges == 0] = 1.0

            self._normalization_params = {
                "min": min_vals,
                "max": max_vals,
                "range": ranges,
            }

        params = self._normalization_params
        # Normalize to [0, 1] then to [-1, 1]
        normalized = (data - params["min"]) / params["range"]
        normalized = 2 * normalized - 1

        return normalized, params

    def _denormalize_data(
        self,
        data: np.ndarray,
        params: Optional[dict] = None,
    ) -> np.ndarray:
        """Reverse normalization to original scale.

        Args:
            data: Normalized data array.
            params: Normalization parameters. Uses stored if None.

        Returns:
            Data in original scale.
        """
        if params is None:
            params = self._normalization_params

        if not params:
            return data

        # Reverse [-1, 1] to [0, 1] to original
        denormalized = (data + 1) / 2
        denormalized = denormalized * params["range"] + params["min"]

        return denormalized

    def encrypt(
        self,
        data: Union[pd.DataFrame, np.ndarray],
        target_column: Optional[str] = None,
    ) -> EncryptedDataset:
        """Encrypt a dataset for FHE-ML operations.

        Args:
            data: Input data as DataFrame or numpy array.
            target_column: Name of target column (for DataFrames).
                If provided, will be encrypted separately as y.

        Returns:
            EncryptedDataset containing encrypted features and target.

        Raises:
            ValueError: If data is empty or has invalid shape.
        """
        # Handle DataFrame input
        if isinstance(data, pd.DataFrame):
            feature_names = list(data.columns)

            if target_column is not None:
                if target_column not in data.columns:
                    raise ValueError(f"Target column '{target_column}' not found")
                y_data = data[target_column].values.astype(np.float64)
                X_data = data.drop(columns=[target_column]).values.astype(np.float64)
                feature_names.remove(target_column)
            else:
                X_data = data.values.astype(np.float64)
                y_data = None
        else:
            # Handle numpy array input
            X_data = np.asarray(data, dtype=np.float64)
            if X_data.ndim == 1:
                X_data = X_data.reshape(-1, 1)
            y_data = None
            feature_names = [f"feature_{i}" for i in range(X_data.shape[1])]

        if X_data.size == 0:
            raise ValueError("Input data is empty")

        n_samples, n_features = X_data.shape

        # Normalize if enabled
        norm_params = None
        if self._normalize:
            X_data, norm_params = self._normalize_data(X_data, fit=True)
            if y_data is not None:
                # Store y normalization separately
                y_min, y_max = y_data.min(), y_data.max()
                y_range = y_max - y_min if y_max != y_min else 1.0
                y_data = 2 * (y_data - y_min) / y_range - 1
                norm_params["y_min"] = y_min
                norm_params["y_max"] = y_max
                norm_params["y_range"] = y_range

        # Encrypt features
        encrypted_X = self._encryptor.encrypt_matrix(X_data)

        # Encrypt target if provided
        encrypted_y = None
        if y_data is not None:
            encrypted_y = self._encryptor.encrypt_vector(y_data)

        return EncryptedDataset(
            X=encrypted_X,
            y=encrypted_y,
            feature_names=feature_names,
            n_samples=n_samples,
            n_features=n_features,
            normalization_params=norm_params,
        )

    def encrypt_features(
        self,
        data: Union[pd.DataFrame, np.ndarray],
    ) -> EncryptedMatrix:
        """Encrypt only features (no target).

        Convenience method for encrypting prediction inputs.

        Args:
            data: Input features as DataFrame or numpy array.

        Returns:
            EncryptedMatrix of features.
        """
        if isinstance(data, pd.DataFrame):
            data = data.values.astype(np.float64)
        else:
            data = np.asarray(data, dtype=np.float64)

        if data.ndim == 1:
            data = data.reshape(1, -1)

        if self._normalize and self._normalization_params:
            data, _ = self._normalize_data(data, fit=False)

        return self._encryptor.encrypt_matrix(data)

    def decrypt(
        self,
        encrypted: Union[EncryptedVector, EncryptedMatrix],
        denormalize: bool = True,
    ) -> np.ndarray:
        """Decrypt encrypted data back to plaintext.

        Args:
            encrypted: Encrypted vector or matrix.
            denormalize: Whether to reverse normalization.

        Returns:
            Decrypted numpy array.
        """
        if isinstance(encrypted, EncryptedMatrix):
            result = self._encryptor.decrypt_matrix(encrypted)
        else:
            result = self._encryptor.decrypt_vector(encrypted)

        if denormalize and self._normalize and self._normalization_params:
            # Check if this looks like y data (1D)
            if result.ndim == 1 and "y_min" in self._normalization_params:
                params = self._normalization_params
                result = (result + 1) / 2 * params["y_range"] + params["y_min"]
            elif result.ndim == 2:
                result = self._denormalize_data(result)

        return result

    def decrypt_prediction(
        self,
        encrypted: EncryptedVector,
        denormalize: bool = True,
    ) -> np.ndarray:
        """Decrypt model prediction output.

        Args:
            encrypted: Encrypted prediction vector.
            denormalize: Whether to reverse target normalization.

        Returns:
            Decrypted prediction values.
        """
        result = self._encryptor.decrypt_vector(encrypted)

        if denormalize and self._normalize:
            params = self._normalization_params
            if params and "y_min" in params:
                result = (result + 1) / 2 * params["y_range"] + params["y_min"]

        return result

    def get_public_context(self) -> bytes:
        """Get serialized public context (no secret key).

        Use this to share context with untrusted parties who
        only need to perform computations.

        Returns:
            Serialized public context bytes.
        """
        return self._context_manager.serialize(include_secret_key=False)

    def __repr__(self) -> str:
        norm = "normalized" if self._normalize else "raw"
        return f"SecureDataLoader(scheme={self._scheme}, mode={norm})"

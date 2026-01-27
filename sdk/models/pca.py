"""FHE-compatible Principal Component Analysis (PCA).

This module implements PCA for dimensionality reduction that can be
applied to FHE-encrypted data using matrix operations.

Key design decisions for FHE compatibility:
- Uses eigendecomposition on covariance matrix (plaintext training)
- Transform is just matrix multiplication (FHE-friendly)
- Inverse transform supported for reconstruction
"""

from dataclasses import dataclass
from typing import Any, Optional, Union

import numpy as np

from ..encryption.ckks_wrapper import (
    CKKSEncryptor,
    EncryptedMatrix,
    EncryptedVector,
)
from ..utils.data_loader import EncryptedDataset
from .base import BaseFHEModel, ModelConfig, ModelState


@dataclass
class PCAConfig(ModelConfig):
    """Configuration for PCA.

    Attributes:
        n_components: Number of components to keep.
            - int: exact number
            - float in (0, 1): fraction of variance to keep
            - None: keep all components
        whiten: Whether to whiten the components.
        svd_solver: Solver to use ('full', 'auto').
        random_state: Random seed for reproducibility.
    """

    n_components: Optional[Union[int, float]] = None
    whiten: bool = False
    svd_solver: str = "full"
    random_state: Optional[int] = None

    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.n_components, float):
            if not 0 < self.n_components < 1:
                raise ValueError("n_components as float must be in (0, 1)")


class PCA(BaseFHEModel):
    """Principal Component Analysis for FHE-encrypted data.

    PCA is used for dimensionality reduction by projecting data onto
    the directions of maximum variance. The transform operation is
    FHE-friendly as it only requires matrix multiplication.

    Training (fit) must be done on plaintext data to compute the
    principal components. Transform can then be applied to encrypted data.

    Example:
        >>> from sdk.models import PCA
        >>> pca = PCA(n_components=2)
        >>> pca.fit(X_train)
        >>> X_reduced = pca.transform(X_test)

        >>> # With variance ratio
        >>> pca = PCA(n_components=0.95)  # Keep 95% of variance
        >>> pca.fit(X_train)

        >>> # Full pipeline
        >>> X_reduced = pca.fit_transform(X_train)
        >>> X_reconstructed = pca.inverse_transform(X_reduced)
    """

    def __init__(
        self,
        n_components: Optional[Union[int, float]] = None,
        whiten: bool = False,
        encryptor: Optional[CKKSEncryptor] = None,
    ):
        """Initialize PCA.

        Args:
            n_components: Number of components to keep.
            whiten: Whether to whiten components.
            encryptor: CKKS encryptor.
        """
        config = PCAConfig(n_components=n_components, whiten=whiten)
        super().__init__(config=config, encryptor=encryptor)

        self._pca_config = config
        self._components: Optional[np.ndarray] = None  # Principal components
        self._mean: Optional[np.ndarray] = None  # Feature means
        self._explained_variance: Optional[np.ndarray] = None
        self._explained_variance_ratio: Optional[np.ndarray] = None
        self._singular_values: Optional[np.ndarray] = None
        self._n_components: Optional[int] = None
        self._n_samples: int = 0

    @property
    def components_(self) -> Optional[np.ndarray]:
        """Get principal components (loadings)."""
        return self._components

    @property
    def explained_variance_(self) -> Optional[np.ndarray]:
        """Get variance explained by each component."""
        return self._explained_variance

    @property
    def explained_variance_ratio_(self) -> Optional[np.ndarray]:
        """Get ratio of variance explained by each component."""
        return self._explained_variance_ratio

    @property
    def mean_(self) -> Optional[np.ndarray]:
        """Get per-feature mean."""
        return self._mean

    @property
    def n_components_(self) -> Optional[int]:
        """Get number of components."""
        return self._n_components

    def fit(
        self,
        X: Union[EncryptedDataset, EncryptedMatrix, np.ndarray],
        y: Optional[Union[EncryptedVector, np.ndarray]] = None,
    ) -> "PCA":
        """Fit PCA to data.

        Args:
            X: Training data (must be plaintext).
            y: Ignored, present for API compatibility.

        Returns:
            self for method chaining.
        """
        self._state = ModelState.TRAINING

        if isinstance(X, (EncryptedDataset, EncryptedMatrix, EncryptedVector)):
            raise ValueError("PCA must be fitted on plaintext data.")

        X_train = np.asarray(X)
        if X_train.ndim == 1:
            X_train = X_train.reshape(-1, 1)

        n_samples, n_features = X_train.shape
        self._n_samples = n_samples
        self._n_features = n_features

        if self._config.verbose:
            print(f"Fitting PCA: {n_samples} samples, {n_features} features")

        # Center the data
        self._mean = X_train.mean(axis=0)
        X_centered = X_train - self._mean

        # Compute covariance matrix
        cov = X_centered.T @ X_centered / (n_samples - 1)

        # Eigendecomposition
        eigenvalues, eigenvectors = np.linalg.eigh(cov)

        # Sort by eigenvalue (descending)
        idx = np.argsort(eigenvalues)[::-1]
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]

        # Determine number of components
        n_components = self._pca_config.n_components

        if n_components is None:
            self._n_components = min(n_samples, n_features)
        elif isinstance(n_components, float):
            # Variance ratio
            cumsum = np.cumsum(eigenvalues) / eigenvalues.sum()
            self._n_components = np.searchsorted(cumsum, n_components) + 1
            self._n_components = min(self._n_components, min(n_samples, n_features))
        else:
            self._n_components = min(n_components, min(n_samples, n_features))

        if self._config.verbose:
            print(f"  Keeping {self._n_components} components")

        # Keep top components
        self._components = eigenvectors[:, :self._n_components].T
        self._explained_variance = eigenvalues[:self._n_components]
        self._explained_variance_ratio = self._explained_variance / eigenvalues.sum()
        self._singular_values = np.sqrt(eigenvalues[:self._n_components] * (n_samples - 1))

        self._state = ModelState.TRAINED

        if self._config.verbose:
            total_var = self._explained_variance_ratio.sum()
            print(f"  Total variance explained: {total_var:.4f}")

        return self

    def transform(
        self,
        X: Union[EncryptedMatrix, np.ndarray, list],
    ) -> Union[EncryptedVector, np.ndarray]:
        """Apply dimensionality reduction.

        Args:
            X: Data to transform.

        Returns:
            Transformed data with reduced dimensions.
        """
        if not self.is_fitted:
            raise RuntimeError("PCA must be fitted before transform")

        if isinstance(X, EncryptedMatrix):
            return self._transform_encrypted(X)
        elif isinstance(X, list) and len(X) > 0 and isinstance(X[0], EncryptedVector):
            return self._transform_encrypted(X)

        X_array = np.asarray(X)
        if X_array.ndim == 1:
            X_array = X_array.reshape(-1, 1)

        # Center and project
        X_centered = X_array - self._mean
        X_transformed = X_centered @ self._components.T

        # Whiten if requested
        if self._pca_config.whiten:
            X_transformed /= np.sqrt(self._explained_variance)

        return X_transformed

    def _transform_encrypted(
        self,
        X: Union[EncryptedMatrix, list[EncryptedVector]],
    ) -> np.ndarray:
        """Transform encrypted data.

        For now, decrypts and transforms (full FHE would use homomorphic ops).
        """
        if isinstance(X, list):
            encrypted_rows = X
        else:
            encrypted_rows = list(X)

        results = []
        for enc_row in encrypted_rows:
            x_plain = enc_row.decrypt().reshape(1, -1)
            x_transformed = self.transform(x_plain)
            results.append(x_transformed[0])

        return np.array(results)

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """Transform data back to original space.

        Args:
            X: Transformed data.

        Returns:
            Data in original space.
        """
        if not self.is_fitted:
            raise RuntimeError("PCA must be fitted before inverse_transform")

        X_array = np.asarray(X)
        if X_array.ndim == 1:
            X_array = X_array.reshape(-1, 1)

        # Un-whiten if necessary
        if self._pca_config.whiten:
            X_array = X_array * np.sqrt(self._explained_variance)

        # Project back and add mean
        return X_array @ self._components + self._mean

    def fit_transform(
        self,
        X: Union[EncryptedDataset, EncryptedMatrix, np.ndarray],
        y: Optional[Union[EncryptedVector, np.ndarray]] = None,
    ) -> np.ndarray:
        """Fit and transform in one step.

        Args:
            X: Training data.
            y: Ignored.

        Returns:
            Transformed data.
        """
        return self.fit(X, y).transform(X)

    def predict(
        self,
        X: Union[EncryptedMatrix, np.ndarray, list],
    ) -> Union[EncryptedVector, np.ndarray]:
        """Alias for transform (for API compatibility)."""
        return self.transform(X)

    def score(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> float:
        """Compute reconstruction score (negative MSE).

        Higher is better (less reconstruction error).

        Args:
            X: Data to score.
            y: Ignored.

        Returns:
            Negative mean squared reconstruction error.
        """
        X_array = np.asarray(X)
        X_transformed = self.transform(X_array)
        X_reconstructed = self.inverse_transform(X_transformed)

        mse = np.mean((X_array - X_reconstructed) ** 2)
        return -mse

    def get_covariance(self) -> np.ndarray:
        """Compute covariance matrix from components.

        Returns:
            Estimated covariance matrix.
        """
        if not self.is_fitted:
            raise RuntimeError("PCA must be fitted first")

        return self._components.T @ np.diag(self._explained_variance) @ self._components

    def get_precision(self) -> np.ndarray:
        """Compute precision matrix (inverse of covariance).

        Returns:
            Estimated precision matrix.
        """
        cov = self.get_covariance()
        return np.linalg.pinv(cov)

    def get_params(self) -> dict[str, Any]:
        """Get model parameters."""
        params = super().get_params()
        params.update({
            "n_components": self._n_components,
            "n_features": self._n_features,
            "components": self._components.tolist() if self._components is not None else None,
            "mean": self._mean.tolist() if self._mean is not None else None,
            "explained_variance": self._explained_variance.tolist() if self._explained_variance is not None else None,
            "explained_variance_ratio": self._explained_variance_ratio.tolist() if self._explained_variance_ratio is not None else None,
            "whiten": self._pca_config.whiten,
        })
        return params

    @classmethod
    def from_params(cls, params: dict) -> "PCA":
        """Reconstruct PCA from saved parameters.

        Args:
            params: Saved parameters.

        Returns:
            Reconstructed PCA model.
        """
        pca = cls(n_components=params.get("n_components"), whiten=params.get("whiten", False))

        pca._n_components = params.get("n_components")
        pca._n_features = params.get("n_features")
        pca._components = np.array(params["components"]) if params.get("components") else None
        pca._mean = np.array(params["mean"]) if params.get("mean") else None
        pca._explained_variance = np.array(params["explained_variance"]) if params.get("explained_variance") else None
        pca._explained_variance_ratio = np.array(params["explained_variance_ratio"]) if params.get("explained_variance_ratio") else None

        if pca._components is not None:
            pca._state = ModelState.TRAINED

        return pca

    def __repr__(self) -> str:
        n_comp = self._n_components or self._pca_config.n_components
        return f"PCA(n_components={n_comp}, whiten={self._pca_config.whiten}, state={self._state.value})"

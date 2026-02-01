"""
Categorical Encoders for FHE-ML Platform.

Implements encoding transformations for categorical data.
"""

from typing import Any, Dict, List, Optional, Union

import numpy as np


class LabelEncoder:
    """
    Encode target labels with values between 0 and n_classes-1.

    Examples
    --------
    >>> from sdk.preprocessing import LabelEncoder
    >>> le = LabelEncoder()
    >>> le.fit(['cat', 'dog', 'cat', 'bird'])
    >>> le.transform(['dog', 'cat'])
    array([1, 0])
    """

    def __init__(self):
        self.classes_: Optional[np.ndarray] = None
        self._class_to_idx: Dict[Any, int] = {}
        self._is_fitted = False

    def fit(self, y: Union[np.ndarray, List]) -> "LabelEncoder":
        """
        Fit label encoder.

        Parameters
        ----------
        y : array-like of shape (n_samples,)
            Target values.

        Returns
        -------
        self : LabelEncoder
            Fitted encoder.
        """
        y = np.asarray(y)
        self.classes_ = np.unique(y)
        self._class_to_idx = {c: i for i, c in enumerate(self.classes_)}
        self._is_fitted = True
        return self

    def transform(self, y: Union[np.ndarray, List]) -> np.ndarray:
        """
        Transform labels to normalized encoding.

        Parameters
        ----------
        y : array-like
            Target values.

        Returns
        -------
        y_encoded : np.ndarray
            Encoded labels.
        """
        if not self._is_fitted:
            raise ValueError("Encoder not fitted. Call fit() first.")

        y = np.asarray(y)
        return np.array([self._class_to_idx[v] for v in y])

    def fit_transform(self, y: Union[np.ndarray, List]) -> np.ndarray:
        """Fit and transform in one step."""
        return self.fit(y).transform(y)

    def inverse_transform(self, y: np.ndarray) -> np.ndarray:
        """
        Transform labels back to original encoding.

        Parameters
        ----------
        y : np.ndarray
            Encoded labels.

        Returns
        -------
        y_original : np.ndarray
            Original labels.
        """
        if not self._is_fitted:
            raise ValueError("Encoder not fitted. Call fit() first.")

        return self.classes_[y]


class OneHotEncoder:
    """
    Encode categorical features as one-hot numeric array.

    Parameters
    ----------
    sparse : bool
        Return sparse matrix (not implemented, always dense).
    drop : str or None
        Drop one category ('first', 'if_binary', None).
    handle_unknown : str
        How to handle unknown categories ('error', 'ignore').

    Examples
    --------
    >>> from sdk.preprocessing import OneHotEncoder
    >>> enc = OneHotEncoder()
    >>> enc.fit([['cat'], ['dog'], ['bird']])
    >>> enc.transform([['cat'], ['bird']])
    array([[1., 0., 0.],
           [0., 1., 0.]])
    """

    def __init__(
        self,
        sparse: bool = False,
        drop: Optional[str] = None,
        handle_unknown: str = "error",
    ):
        self.sparse = sparse
        self.drop = drop
        self.handle_unknown = handle_unknown

        self.categories_: List[np.ndarray] = []
        self.n_features_in_: Optional[int] = None
        self._drop_idx_: List[Optional[int]] = []
        self._is_fitted = False

    def fit(self, X: np.ndarray, y=None) -> "OneHotEncoder":
        """
        Fit the encoder.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Data to fit.

        Returns
        -------
        self : OneHotEncoder
            Fitted encoder.
        """
        X = np.asarray(X)
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        self.n_features_in_ = X.shape[1]
        self.categories_ = []
        self._drop_idx_ = []

        for i in range(self.n_features_in_):
            cats = np.unique(X[:, i])
            self.categories_.append(cats)

            if self.drop == "first":
                self._drop_idx_.append(0)
            elif self.drop == "if_binary" and len(cats) == 2:
                self._drop_idx_.append(0)
            else:
                self._drop_idx_.append(None)

        self._is_fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Transform data to one-hot encoding.

        Parameters
        ----------
        X : array-like
            Data to transform.

        Returns
        -------
        X_encoded : np.ndarray
            One-hot encoded data.
        """
        if not self._is_fitted:
            raise ValueError("Encoder not fitted. Call fit() first.")

        X = np.asarray(X)
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        n_samples = X.shape[0]
        encoded_parts = []

        for i in range(self.n_features_in_):
            cats = self.categories_[i]
            n_cats = len(cats)
            drop_idx = self._drop_idx_[i]

            # Create one-hot matrix for this feature
            feature_encoded = np.zeros((n_samples, n_cats))

            for j, val in enumerate(X[:, i]):
                idx = np.where(cats == val)[0]
                if len(idx) > 0:
                    feature_encoded[j, idx[0]] = 1
                elif self.handle_unknown == "error":
                    raise ValueError(f"Unknown category: {val}")
                # If 'ignore', leave as zeros

            # Drop category if specified
            if drop_idx is not None:
                feature_encoded = np.delete(feature_encoded, drop_idx, axis=1)

            encoded_parts.append(feature_encoded)

        return np.hstack(encoded_parts)

    def fit_transform(self, X: np.ndarray, y=None) -> np.ndarray:
        """Fit and transform in one step."""
        return self.fit(X, y).transform(X)

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """
        Convert one-hot encoding back to original.

        Parameters
        ----------
        X : np.ndarray
            One-hot encoded data.

        Returns
        -------
        X_original : np.ndarray
            Original categorical data.
        """
        if not self._is_fitted:
            raise ValueError("Encoder not fitted. Call fit() first.")

        n_samples = X.shape[0]
        result = []
        col_idx = 0

        for i in range(self.n_features_in_):
            cats = self.categories_[i]
            drop_idx = self._drop_idx_[i]
            n_cats = len(cats) - (1 if drop_idx is not None else 0)

            feature_encoded = X[:, col_idx : col_idx + n_cats]
            col_idx += n_cats

            # Find which category is active
            feature_result = []
            for j in range(n_samples):
                active_idx = np.argmax(feature_encoded[j])
                if drop_idx is not None and active_idx >= drop_idx:
                    active_idx += 1
                if np.sum(feature_encoded[j]) == 0 and drop_idx is not None:
                    active_idx = drop_idx
                feature_result.append(cats[active_idx])

            result.append(feature_result)

        return np.array(result).T

    def get_feature_names_out(self, input_features: Optional[List[str]] = None) -> List[str]:
        """Get output feature names."""
        if not self._is_fitted:
            raise ValueError("Encoder not fitted. Call fit() first.")

        if input_features is None:
            input_features = [f"x{i}" for i in range(self.n_features_in_)]

        names = []
        for i, cats in enumerate(self.categories_):
            drop_idx = self._drop_idx_[i]
            for j, cat in enumerate(cats):
                if drop_idx is not None and j == drop_idx:
                    continue
                names.append(f"{input_features[i]}_{cat}")

        return names


class OrdinalEncoder:
    """
    Encode categorical features as ordinal integers.

    Parameters
    ----------
    categories : 'auto' or list of arrays
        Categories for each feature.
    handle_unknown : str
        How to handle unknown categories.

    Examples
    --------
    >>> from sdk.preprocessing import OrdinalEncoder
    >>> enc = OrdinalEncoder()
    >>> enc.fit([['low'], ['medium'], ['high']])
    >>> enc.transform([['medium'], ['low']])
    array([[1.],
           [0.]])
    """

    def __init__(
        self,
        categories: str = "auto",
        handle_unknown: str = "error",
    ):
        self.categories = categories
        self.handle_unknown = handle_unknown

        self.categories_: List[np.ndarray] = []
        self.n_features_in_: Optional[int] = None
        self._is_fitted = False

    def fit(self, X: np.ndarray, y=None) -> "OrdinalEncoder":
        """Fit the encoder."""
        X = np.asarray(X)
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        self.n_features_in_ = X.shape[1]

        if self.categories == "auto":
            self.categories_ = [np.unique(X[:, i]) for i in range(self.n_features_in_)]
        else:
            self.categories_ = [np.asarray(c) for c in self.categories]

        self._is_fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Transform data to ordinal encoding."""
        if not self._is_fitted:
            raise ValueError("Encoder not fitted. Call fit() first.")

        X = np.asarray(X)
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        n_samples = X.shape[0]
        result = np.zeros((n_samples, self.n_features_in_), dtype=np.float64)

        for i in range(self.n_features_in_):
            cats = self.categories_[i]
            cat_to_idx = {c: j for j, c in enumerate(cats)}

            for j, val in enumerate(X[:, i]):
                if val in cat_to_idx:
                    result[j, i] = cat_to_idx[val]
                elif self.handle_unknown == "error":
                    raise ValueError(f"Unknown category: {val}")
                else:
                    result[j, i] = -1

        return result

    def fit_transform(self, X: np.ndarray, y=None) -> np.ndarray:
        """Fit and transform in one step."""
        return self.fit(X, y).transform(X)

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """Convert ordinal encoding back to original."""
        if not self._is_fitted:
            raise ValueError("Encoder not fitted. Call fit() first.")

        X = np.asarray(X, dtype=int)
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        n_samples = X.shape[0]
        result = np.empty((n_samples, self.n_features_in_), dtype=object)

        for i in range(self.n_features_in_):
            cats = self.categories_[i]
            for j in range(n_samples):
                idx = X[j, i]
                if 0 <= idx < len(cats):
                    result[j, i] = cats[idx]
                else:
                    result[j, i] = None

        return result


class TargetEncoder:
    """
    Encode categorical features using target mean.

    Also known as mean encoding or likelihood encoding.

    Parameters
    ----------
    smoothing : float
        Smoothing factor for regularization.
    min_samples_leaf : int
        Minimum samples to use category mean.

    Examples
    --------
    >>> from sdk.preprocessing import TargetEncoder
    >>> enc = TargetEncoder(smoothing=1.0)
    >>> enc.fit(X_cat, y)
    >>> X_encoded = enc.transform(X_cat)
    """

    def __init__(
        self,
        smoothing: float = 1.0,
        min_samples_leaf: int = 1,
    ):
        self.smoothing = smoothing
        self.min_samples_leaf = min_samples_leaf

        self.encodings_: List[Dict[Any, float]] = []
        self.global_mean_: Optional[float] = None
        self.n_features_in_: Optional[int] = None
        self._is_fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "TargetEncoder":
        """
        Fit the target encoder.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Categorical features.
        y : array-like of shape (n_samples,)
            Target values.

        Returns
        -------
        self : TargetEncoder
            Fitted encoder.
        """
        X = np.asarray(X)
        y = np.asarray(y, dtype=np.float64)

        if X.ndim == 1:
            X = X.reshape(-1, 1)

        self.n_features_in_ = X.shape[1]
        self.global_mean_ = np.mean(y)
        self.encodings_ = []

        for i in range(self.n_features_in_):
            encoding = {}
            categories = np.unique(X[:, i])

            for cat in categories:
                mask = X[:, i] == cat
                n_samples = np.sum(mask)

                if n_samples >= self.min_samples_leaf:
                    cat_mean = np.mean(y[mask])
                    # Smoothed mean: (n * cat_mean + smoothing * global_mean) / (n + smoothing)
                    smoothed = (n_samples * cat_mean + self.smoothing * self.global_mean_) / (
                        n_samples + self.smoothing
                    )
                    encoding[cat] = smoothed
                else:
                    encoding[cat] = self.global_mean_

            self.encodings_.append(encoding)

        self._is_fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Transform categorical features using target encoding.

        Parameters
        ----------
        X : array-like
            Categorical features.

        Returns
        -------
        X_encoded : np.ndarray
            Target encoded features.
        """
        if not self._is_fitted:
            raise ValueError("Encoder not fitted. Call fit() first.")

        X = np.asarray(X)
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        n_samples = X.shape[0]
        result = np.zeros((n_samples, self.n_features_in_), dtype=np.float64)

        for i in range(self.n_features_in_):
            encoding = self.encodings_[i]
            for j in range(n_samples):
                val = X[j, i]
                result[j, i] = encoding.get(val, self.global_mean_)

        return result

    def fit_transform(self, X: np.ndarray, y: np.ndarray) -> np.ndarray:
        """Fit and transform in one step."""
        return self.fit(X, y).transform(X)

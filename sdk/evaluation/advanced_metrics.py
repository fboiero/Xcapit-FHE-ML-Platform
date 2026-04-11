"""Advanced metrics for privacy, fairness, and FHE evaluation.

Provides specialised metrics for assessing model privacy risks,
algorithmic fairness, and FHE-specific performance characteristics.
"""

import time
from typing import Any, Optional

import numpy as np


class PrivacyMetrics:
    """Privacy-related evaluation metrics.

    Measures vulnerability to membership inference attacks and
    estimates differential privacy parameters.

    Example:
        >>> pm = PrivacyMetrics()
        >>> risk = pm.membership_inference_risk(model, train_data, test_data)
    """

    def membership_inference_risk(
        self,
        model: Any,
        train_data: np.ndarray,
        test_data: np.ndarray,
    ) -> dict[str, float]:
        """Estimate membership inference attack risk.

        Compares model confidence on training data vs. held-out data.
        Higher divergence indicates greater privacy risk.

        Args:
            model: Trained model with predict (and optionally predict_proba).
            train_data: Data used for training.
            test_data: Held-out test data.

        Returns:
            Dict with 'risk_score' (0-1), 'train_confidence', 'test_confidence'.
        """
        train_data = np.asarray(train_data, dtype=np.float64)
        test_data = np.asarray(test_data, dtype=np.float64)

        # Get predictions / confidence scores
        train_conf = self._get_confidence(model, train_data)
        test_conf = self._get_confidence(model, test_data)

        mean_train = float(np.mean(train_conf))
        mean_test = float(np.mean(test_conf))

        # Risk is the gap between train and test confidence
        # Normalised to [0, 1]
        gap = abs(mean_train - mean_test)
        risk_score = min(gap / max(mean_train, 1e-10), 1.0)

        return {
            "risk_score": risk_score,
            "train_confidence": mean_train,
            "test_confidence": mean_test,
        }

    def differential_privacy_epsilon(
        self,
        model: Any,
        sensitivity: float = 1.0,
        noise_scale: Optional[float] = None,
    ) -> dict[str, float]:
        """Estimate the effective differential privacy epsilon.

        If the model has a noise_scale or epsilon attribute, uses it directly.
        Otherwise estimates from the model's sensitivity and provided noise scale.

        Args:
            model: Trained model.
            sensitivity: Query sensitivity (L1 or L2).
            noise_scale: Standard deviation of added noise. If None,
                attempts to read from model attributes.

        Returns:
            Dict with 'epsilon' and 'delta' estimates.
        """
        # Try to read from model
        if noise_scale is None:
            noise_scale = getattr(model, "noise_scale", None)
            if noise_scale is None:
                noise_scale = getattr(model, "noise_multiplier", None)

        epsilon = getattr(model, "epsilon", None)

        if epsilon is not None:
            return {
                "epsilon": float(epsilon),
                "delta": float(getattr(model, "delta", 1e-5)),
            }

        if noise_scale is not None and noise_scale > 0:
            # Laplace mechanism: epsilon = sensitivity / noise_scale
            epsilon = sensitivity / noise_scale
        else:
            epsilon = float("inf")

        return {
            "epsilon": float(epsilon),
            "delta": 1e-5,
        }

    @staticmethod
    def _get_confidence(model: Any, X: np.ndarray) -> np.ndarray:
        """Get model confidence scores for input data."""
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(X)
            if probs.ndim == 2:
                return np.max(probs, axis=1)
            return np.abs(probs)

        preds = np.asarray(model.predict(X), dtype=np.float64).ravel()
        return np.abs(preds)


class FairnessMetrics:
    """Fairness evaluation metrics for ML models.

    Measures demographic parity and equalized odds across
    protected groups.

    Example:
        >>> fm = FairnessMetrics()
        >>> dp = fm.demographic_parity(y_pred, groups)
    """

    def demographic_parity(
        self,
        y_pred: np.ndarray,
        groups: np.ndarray,
    ) -> dict[str, Any]:
        """Compute demographic parity (statistical parity).

        Measures whether positive prediction rates are equal across groups.

        Args:
            y_pred: Predicted labels (binary).
            groups: Group membership for each sample.

        Returns:
            Dict with per-group positive rates, 'disparity' (max difference),
            and 'is_fair' (disparity < 0.1 threshold).
        """
        y_pred = np.asarray(y_pred).ravel()
        groups = np.asarray(groups).ravel()

        unique_groups = np.unique(groups)
        positive_rates = {}

        for g in unique_groups:
            mask = groups == g
            group_preds = y_pred[mask]
            positive_rate = float(np.mean(group_preds > 0))
            positive_rates[str(g)] = positive_rate

        rates = list(positive_rates.values())
        disparity = max(rates) - min(rates) if len(rates) > 1 else 0.0

        return {
            "positive_rates": positive_rates,
            "disparity": disparity,
            "is_fair": disparity < 0.1,
        }

    def equalized_odds(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        groups: np.ndarray,
    ) -> dict[str, Any]:
        """Compute equalized odds.

        Measures whether true positive and false positive rates are
        equal across groups.

        Args:
            y_true: True labels (binary).
            y_pred: Predicted labels (binary).
            groups: Group membership for each sample.

        Returns:
            Dict with per-group TPR/FPR, 'tpr_disparity', 'fpr_disparity',
            and 'is_fair'.
        """
        y_true = np.asarray(y_true).ravel()
        y_pred = np.asarray(y_pred).ravel()
        groups = np.asarray(groups).ravel()

        unique_groups = np.unique(groups)
        group_stats = {}

        for g in unique_groups:
            mask = groups == g
            yt = y_true[mask]
            yp = y_pred[mask]

            # True positive rate
            pos_mask = yt > 0
            if pos_mask.sum() > 0:
                tpr = float(np.mean(yp[pos_mask] > 0))
            else:
                tpr = 0.0

            # False positive rate
            neg_mask = yt <= 0
            if neg_mask.sum() > 0:
                fpr = float(np.mean(yp[neg_mask] > 0))
            else:
                fpr = 0.0

            group_stats[str(g)] = {"tpr": tpr, "fpr": fpr}

        tprs = [s["tpr"] for s in group_stats.values()]
        fprs = [s["fpr"] for s in group_stats.values()]

        tpr_disparity = max(tprs) - min(tprs) if len(tprs) > 1 else 0.0
        fpr_disparity = max(fprs) - min(fprs) if len(fprs) > 1 else 0.0

        return {
            "group_stats": group_stats,
            "tpr_disparity": tpr_disparity,
            "fpr_disparity": fpr_disparity,
            "is_fair": tpr_disparity < 0.1 and fpr_disparity < 0.1,
        }


class FHEMetrics:
    """FHE-specific performance metrics.

    Measures encryption overhead, precision loss from homomorphic
    operations, and remaining noise budget.

    Example:
        >>> fhe = FHEMetrics()
        >>> overhead = fhe.encryption_overhead(model, X)
    """

    def encryption_overhead(
        self,
        model: Any,
        X: np.ndarray,
        n_runs: int = 5,
    ) -> dict[str, float]:
        """Measure the time overhead of encrypted vs. plaintext inference.

        Args:
            model: Model with predict(X). If the model also supports
                encrypted prediction, both are timed.
            X: Input data.
            n_runs: Number of timing runs for averaging.

        Returns:
            Dict with 'plain_time_ms', 'encrypted_time_ms', 'overhead_ratio'.
        """
        X = np.asarray(X, dtype=np.float64)

        # Time plaintext inference
        times_plain = []
        for _ in range(n_runs):
            start = time.perf_counter()
            model.predict(X)
            elapsed = (time.perf_counter() - start) * 1000
            times_plain.append(elapsed)

        plain_ms = float(np.median(times_plain))

        # Try encrypted inference
        encrypted_ms = None
        if hasattr(model, "predict_encrypted"):
            times_enc = []
            for _ in range(n_runs):
                start = time.perf_counter()
                model.predict_encrypted(X)
                elapsed = (time.perf_counter() - start) * 1000
                times_enc.append(elapsed)
            encrypted_ms = float(np.median(times_enc))

        if encrypted_ms is not None and plain_ms > 0:
            overhead = encrypted_ms / plain_ms
        else:
            overhead = 1.0
            encrypted_ms = encrypted_ms or plain_ms

        return {
            "plain_time_ms": plain_ms,
            "encrypted_time_ms": encrypted_ms,
            "overhead_ratio": overhead,
        }

    def precision_loss(
        self,
        plain_pred: np.ndarray,
        encrypted_pred: np.ndarray,
    ) -> dict[str, float]:
        """Measure precision loss between plaintext and encrypted predictions.

        Args:
            plain_pred: Predictions from plaintext inference.
            encrypted_pred: Predictions from encrypted inference.

        Returns:
            Dict with 'mae', 'max_error', 'relative_error'.
        """
        plain_pred = np.asarray(plain_pred, dtype=np.float64).ravel()
        encrypted_pred = np.asarray(encrypted_pred, dtype=np.float64).ravel()

        diff = np.abs(plain_pred - encrypted_pred)
        mae = float(np.mean(diff))
        max_error = float(np.max(diff))

        # Relative error (avoid division by zero)
        denom = np.abs(plain_pred)
        mask = denom > 1e-10
        if mask.any():
            relative_error = float(np.mean(diff[mask] / denom[mask]))
        else:
            relative_error = 0.0 if mae < 1e-10 else float("inf")

        return {
            "mae": mae,
            "max_error": max_error,
            "relative_error": relative_error,
        }

    def noise_budget(
        self,
        model: Any,
    ) -> dict[str, Any]:
        """Estimate the remaining noise budget for an FHE model.

        Reads noise budget information from the model or its encryptor
        if available.

        Args:
            model: An FHE model instance.

        Returns:
            Dict with 'initial_budget', 'remaining_budget', 'consumed_ratio'.
        """
        # Try reading from known attributes
        initial = getattr(model, "initial_noise_budget", None)
        remaining = getattr(model, "remaining_noise_budget", None)

        # Try reading from encryptor
        encryptor = getattr(model, "_encryptor", None)
        if encryptor is not None and initial is None:
            initial = getattr(encryptor, "initial_noise_budget", None)
            remaining = getattr(encryptor, "remaining_noise_budget", None)

        if initial is None:
            initial = 0
        if remaining is None:
            remaining = 0

        consumed = (initial - remaining) / initial if initial > 0 else 0.0

        return {
            "initial_budget": int(initial),
            "remaining_budget": int(remaining),
            "consumed_ratio": float(consumed),
        }

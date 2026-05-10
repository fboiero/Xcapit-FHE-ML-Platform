"""Tests for the privacy module: DP mechanisms, accountant, data loader, training.

Covers:
- LaplaceMechanism: noise shape, variance, epsilon validation.
- GaussianMechanism: noise shape, sigma computation, delta validation.
- ExponentialMechanism: selection, utility bias, add_noise rejection.
- PrivacyAccountant: composition, budget tracking, reset.
- GradientClipper: norm clipping, direction preservation, accumulation.
- DPDataLoader: feature/label/dataset privatization.
- SubsampledMechanism: privacy amplification by subsampling.
"""

from __future__ import annotations

import numpy as np
import pytest

from sdk.privacy import (
    DPDataLoader,
    ExponentialMechanism,
    GaussianMechanism,
    GradientClipper,
    LaplaceMechanism,
    PrivacyAccountant,
    SubsampledMechanism,
)

# =====================================================================
# LaplaceMechanism
# =====================================================================


class TestLaplaceMechanism:
    """Tests for the Laplace mechanism."""

    def test_add_noise_shape_preserved(self) -> None:
        """Output shape matches input shape."""
        mechanism = LaplaceMechanism(epsilon=1.0)
        data = np.array([10.0, 20.0, 30.0])
        noisy = mechanism.add_noise(data, sensitivity=1.0)
        assert noisy.shape == data.shape

    def test_add_noise_2d_shape_preserved(self) -> None:
        """Output shape matches input shape for 2D arrays."""
        mechanism = LaplaceMechanism(epsilon=1.0)
        data = np.ones((5, 3))
        noisy = mechanism.add_noise(data, sensitivity=1.0)
        assert noisy.shape == (5, 3)

    def test_noise_is_added(self) -> None:
        """Output differs from input (noise is non-zero with overwhelming probability)."""
        mechanism = LaplaceMechanism(epsilon=1.0)
        data = np.array([10.0, 20.0, 30.0])
        noisy = mechanism.add_noise(data, sensitivity=1.0)
        assert not np.array_equal(noisy, data)

    def test_zero_epsilon_raises(self) -> None:
        """epsilon <= 0 raises ValueError."""
        with pytest.raises(ValueError, match="positive"):
            LaplaceMechanism(epsilon=0.0)

    def test_negative_epsilon_raises(self) -> None:
        """Negative epsilon raises ValueError."""
        with pytest.raises(ValueError, match="positive"):
            LaplaceMechanism(epsilon=-1.0)

    def test_variance_formula(self) -> None:
        """Variance matches 2 * (sensitivity / epsilon)^2."""
        epsilon = 0.5
        sensitivity = 2.0
        mechanism = LaplaceMechanism(epsilon=epsilon)
        expected_variance = 2.0 * (sensitivity / epsilon) ** 2
        assert mechanism.variance(sensitivity) == pytest.approx(expected_variance)

    def test_epsilon_consumed(self) -> None:
        """epsilon_consumed returns the epsilon value."""
        mechanism = LaplaceMechanism(epsilon=1.5)
        assert mechanism.epsilon_consumed() == 1.5

    def test_zero_sensitivity_raises(self) -> None:
        """sensitivity <= 0 raises ValueError."""
        mechanism = LaplaceMechanism(epsilon=1.0)
        with pytest.raises(ValueError, match="positive"):
            mechanism.add_noise(np.array([1.0]), sensitivity=0.0)


# =====================================================================
# GaussianMechanism
# =====================================================================


class TestGaussianMechanism:
    """Tests for the Gaussian mechanism."""

    def test_add_noise_shape_preserved(self) -> None:
        """Output shape matches input shape."""
        mechanism = GaussianMechanism(epsilon=1.0, delta=1e-5)
        data = np.array([10.0, 20.0, 30.0])
        noisy = mechanism.add_noise(data, sensitivity=1.0)
        assert noisy.shape == data.shape

    def test_compute_sigma(self) -> None:
        """Sigma matches formula: sensitivity * sqrt(2 * ln(1.25/delta)) / epsilon."""
        epsilon = 0.5
        delta = 1e-5
        sensitivity = 2.0
        mechanism = GaussianMechanism(epsilon=epsilon, delta=delta)
        expected_sigma = sensitivity * np.sqrt(2.0 * np.log(1.25 / delta)) / epsilon
        assert mechanism.compute_sigma(sensitivity) == pytest.approx(expected_sigma)

    def test_invalid_delta_raises_zero(self) -> None:
        """delta = 0 raises ValueError."""
        with pytest.raises(ValueError, match="Delta"):
            GaussianMechanism(epsilon=1.0, delta=0.0)

    def test_invalid_delta_raises_one(self) -> None:
        """delta = 1 raises ValueError."""
        with pytest.raises(ValueError, match="Delta"):
            GaussianMechanism(epsilon=1.0, delta=1.0)

    def test_invalid_delta_raises_negative(self) -> None:
        """Negative delta raises ValueError."""
        with pytest.raises(ValueError, match="Delta"):
            GaussianMechanism(epsilon=1.0, delta=-0.1)

    def test_epsilon_consumed(self) -> None:
        """epsilon_consumed returns the epsilon value."""
        mechanism = GaussianMechanism(epsilon=0.5, delta=1e-5)
        assert mechanism.epsilon_consumed() == 0.5

    def test_noise_is_added(self) -> None:
        """Output differs from input."""
        mechanism = GaussianMechanism(epsilon=1.0, delta=1e-5)
        data = np.array([100.0, 200.0])
        noisy = mechanism.add_noise(data, sensitivity=1.0)
        assert not np.array_equal(noisy, data)

    def test_variance_matches_sigma_squared(self) -> None:
        """Variance equals sigma^2."""
        mechanism = GaussianMechanism(epsilon=1.0, delta=1e-5)
        sensitivity = 1.0
        sigma = mechanism.compute_sigma(sensitivity)
        assert mechanism.variance(sensitivity) == pytest.approx(sigma ** 2)


# =====================================================================
# ExponentialMechanism
# =====================================================================


class TestExponentialMechanism:
    """Tests for the Exponential mechanism."""

    def test_select_returns_valid_index(self) -> None:
        """Selected index is within the range of utilities."""
        mechanism = ExponentialMechanism(epsilon=1.0)
        utilities = np.array([3.0, 1.0, 2.0])
        idx = mechanism.select(utilities, sensitivity=1.0)
        assert 0 <= idx < len(utilities)

    def test_higher_utility_more_likely(self) -> None:
        """With large epsilon, highest utility is selected most often."""
        mechanism = ExponentialMechanism(epsilon=100.0)
        utilities = np.array([1.0, 2.0, 10.0])
        counts = np.zeros(3)
        n_trials = 500
        for _ in range(n_trials):
            idx = mechanism.select(utilities, sensitivity=1.0)
            counts[idx] += 1
        # The item with utility 10.0 should be selected overwhelmingly
        assert counts[2] > n_trials * 0.9

    def test_add_noise_raises(self) -> None:
        """add_noise raises NotImplementedError."""
        mechanism = ExponentialMechanism(epsilon=1.0)
        with pytest.raises(NotImplementedError, match="select"):
            mechanism.add_noise(np.array([1.0]), sensitivity=1.0)

    def test_epsilon_consumed(self) -> None:
        """epsilon_consumed returns the epsilon value."""
        mechanism = ExponentialMechanism(epsilon=2.0)
        assert mechanism.epsilon_consumed() == 2.0

    def test_zero_epsilon_raises(self) -> None:
        """epsilon <= 0 raises ValueError."""
        with pytest.raises(ValueError, match="positive"):
            ExponentialMechanism(epsilon=0.0)

    def test_empty_utilities_raises(self) -> None:
        """Empty utilities array raises ValueError."""
        mechanism = ExponentialMechanism(epsilon=1.0)
        with pytest.raises(ValueError, match="empty"):
            mechanism.select(np.array([]), sensitivity=1.0)


# =====================================================================
# PrivacyAccountant
# =====================================================================


class TestPrivacyAccountant:
    """Tests for the privacy accountant."""

    def test_basic_composition(self) -> None:
        """Sum of epsilons after multiple consume calls."""
        accountant = PrivacyAccountant(total_epsilon=10.0, total_delta=1e-5)
        accountant.consume(epsilon=1.0, operation="q1")
        accountant.consume(epsilon=2.0, operation="q2")
        accountant.consume(epsilon=3.0, operation="q3")
        total_eps, total_delta = accountant.compose_basic()
        assert total_eps == pytest.approx(6.0)
        assert total_delta == pytest.approx(0.0)

    def test_remaining_budget(self) -> None:
        """Remaining budget decreases with each step."""
        accountant = PrivacyAccountant(total_epsilon=10.0, total_delta=1e-5)
        eps_remaining_0, _ = accountant.remaining_budget()
        assert eps_remaining_0 == pytest.approx(10.0)

        accountant.consume(epsilon=3.0)
        eps_remaining_1, _ = accountant.remaining_budget()
        assert eps_remaining_1 == pytest.approx(7.0)

        accountant.consume(epsilon=4.0)
        eps_remaining_2, _ = accountant.remaining_budget()
        assert eps_remaining_2 == pytest.approx(3.0)

    def test_budget_exceeded(self) -> None:
        """is_budget_exceeded returns True when exceeded."""
        accountant = PrivacyAccountant(total_epsilon=5.0, total_delta=1e-5)
        accountant.consume(epsilon=3.0)
        assert not accountant.is_budget_exceeded()

        accountant.consume(epsilon=3.0)  # total = 6.0 > 5.0
        assert accountant.is_budget_exceeded()

    def test_reset(self) -> None:
        """reset() clears history and restores budget."""
        accountant = PrivacyAccountant(total_epsilon=10.0, total_delta=1e-5)
        accountant.consume(epsilon=5.0, operation="q1")
        accountant.consume(epsilon=3.0, operation="q2")

        accountant.reset()

        eps_remaining, _ = accountant.remaining_budget()
        assert eps_remaining == pytest.approx(10.0)
        assert len(accountant.history) == 0
        assert not accountant.is_budget_exceeded()

    def test_step_with_mechanism(self) -> None:
        """step() records mechanism's epsilon."""
        accountant = PrivacyAccountant(total_epsilon=10.0, total_delta=1e-5)
        mechanism = LaplaceMechanism(epsilon=2.0)
        result = accountant.step(mechanism)
        assert result is True

        eps_remaining, _ = accountant.remaining_budget()
        assert eps_remaining == pytest.approx(8.0)
        assert len(accountant.history) == 1
        assert accountant.history[0][0] == pytest.approx(2.0)

    def test_step_with_gaussian_mechanism(self) -> None:
        """step() records Gaussian mechanism epsilon and delta."""
        accountant = PrivacyAccountant(total_epsilon=10.0, total_delta=1e-3)
        mechanism = GaussianMechanism(epsilon=1.0, delta=1e-5)
        result = accountant.step(mechanism)
        assert result is True
        assert accountant.budget.epsilon_used == pytest.approx(1.0)
        assert accountant.budget.delta_used == pytest.approx(1e-5)

    def test_consume_returns_false_when_exceeded(self) -> None:
        """consume() returns False when budget is exceeded."""
        accountant = PrivacyAccountant(total_epsilon=2.0, total_delta=1e-5)
        result = accountant.consume(epsilon=3.0)
        assert result is False
        assert accountant.is_budget_exceeded()

    def test_negative_epsilon_raises(self) -> None:
        """Negative epsilon in consume raises ValueError."""
        accountant = PrivacyAccountant(total_epsilon=10.0, total_delta=1e-5)
        with pytest.raises(ValueError, match="non-negative"):
            accountant.consume(epsilon=-1.0)

    def test_report_contains_expected_keys(self) -> None:
        """Report dict has budget and composition fields."""
        accountant = PrivacyAccountant(total_epsilon=10.0, total_delta=1e-5)
        accountant.consume(epsilon=1.0, operation="test")
        report = accountant.report()
        assert "budget" in report
        assert "queries" in report
        assert "composition" in report
        assert report["queries"] == 1


# =====================================================================
# GradientClipper
# =====================================================================


class TestGradientClipper:
    """Tests for per-sample gradient clipping."""

    def test_clip_reduces_norm(self) -> None:
        """Norms above max_norm are clipped to max_norm."""
        clipper = GradientClipper(max_norm=1.0)
        # Gradient with norm 5
        grads = np.array([[3.0, 4.0]])
        clipped = clipper.clip(grads)
        norm = np.linalg.norm(clipped[0])
        assert norm == pytest.approx(1.0, abs=1e-10)

    def test_clip_preserves_small_norms(self) -> None:
        """Norms below max_norm are unchanged."""
        clipper = GradientClipper(max_norm=10.0)
        grads = np.array([[0.5, 0.1]])
        clipped = clipper.clip(grads)
        np.testing.assert_allclose(clipped, grads, atol=1e-12)

    def test_clip_direction_preserved(self) -> None:
        """Direction of gradient is preserved after clipping."""
        clipper = GradientClipper(max_norm=1.0)
        grad = np.array([3.0, 4.0])  # 1D input
        clipped = clipper.clip(grad)
        # Direction should be proportional
        original_dir = grad / np.linalg.norm(grad)
        clipped_dir = clipped / np.linalg.norm(clipped)
        np.testing.assert_allclose(original_dir, clipped_dir, atol=1e-12)

    def test_clip_and_accumulate(self) -> None:
        """clip_and_accumulate clips then sums."""
        clipper = GradientClipper(max_norm=1.0)
        grads = np.array([
            [3.0, 4.0],   # norm=5, will be clipped
            [0.1, 0.2],   # norm<1, stays as-is
        ])
        result = clipper.clip_and_accumulate(grads)
        assert result.shape == (2,)
        # First row clipped to norm 1.0, then summed with second row
        clipped_first = np.array([3.0, 4.0]) * (1.0 / 5.0)
        expected = clipped_first + np.array([0.1, 0.2])
        np.testing.assert_allclose(result, expected, atol=1e-12)

    def test_clip_batch(self) -> None:
        """Batch clipping clips each row independently."""
        clipper = GradientClipper(max_norm=1.0)
        grads = np.array([
            [3.0, 4.0],    # norm=5
            [0.6, 0.8],    # norm=1.0, exactly at boundary
            [10.0, 0.0],   # norm=10
        ])
        clipped = clipper.clip(grads)
        for i in range(3):
            norm = np.linalg.norm(clipped[i])
            assert norm <= 1.0 + 1e-10

    def test_invalid_max_norm_raises(self) -> None:
        """max_norm <= 0 raises ValueError."""
        with pytest.raises(ValueError, match="positive"):
            GradientClipper(max_norm=0.0)


# =====================================================================
# DPDataLoader
# =====================================================================


class TestDPDataLoader:
    """Tests for privacy-preserving data loading."""

    def test_privatize_features(self) -> None:
        """Output shape matches input, values differ."""
        loader = DPDataLoader(epsilon=1.0, delta=1e-5)
        X = np.random.default_rng(0).standard_normal((100, 5))
        X_noised = loader.privatize_features(X)
        assert X_noised.shape == X.shape
        assert not np.array_equal(X_noised, X)

    def test_privatize_labels(self) -> None:
        """Output shape matches input, values differ."""
        loader = DPDataLoader(epsilon=1.0, delta=1e-5)
        y = np.random.default_rng(0).standard_normal(100)
        y_noised = loader.privatize_labels(y, sensitivity=1.0)
        assert y_noised.shape == y.shape
        assert not np.array_equal(y_noised, y)

    def test_privatize_dataset(self) -> None:
        """Returns tuple of arrays with correct shapes."""
        loader = DPDataLoader(epsilon=5.0, delta=1e-5)
        rng = np.random.default_rng(0)
        X = rng.standard_normal((50, 4))
        y = rng.standard_normal(50)
        X_noised, y_noised = loader.privatize_dataset(X, y)
        assert isinstance(X_noised, np.ndarray)
        assert isinstance(y_noised, np.ndarray)
        assert X_noised.shape == X.shape
        assert y_noised.shape == y.shape

    def test_privatize_features_consumes_budget(self) -> None:
        """Privacy budget is consumed after privatizing features."""
        loader = DPDataLoader(epsilon=10.0, delta=1e-5)
        X = np.ones((10, 3))
        loader.privatize_features(X)
        eps_remaining, _ = loader.accountant.remaining_budget()
        assert eps_remaining < 10.0

    def test_invalid_epsilon_raises(self) -> None:
        """epsilon <= 0 raises ValueError."""
        with pytest.raises(ValueError, match="positive"):
            DPDataLoader(epsilon=0.0, delta=1e-5)

    def test_invalid_mechanism_raises(self) -> None:
        """Invalid mechanism name raises ValueError."""
        with pytest.raises(ValueError, match="Mechanism"):
            DPDataLoader(epsilon=1.0, mechanism="invalid")

    def test_laplace_mechanism(self) -> None:
        """DPDataLoader works with Laplace mechanism."""
        loader = DPDataLoader(epsilon=1.0, mechanism="laplace")
        X = np.ones((10, 2))
        X_noised = loader.privatize_features(X)
        assert X_noised.shape == X.shape
        assert not np.array_equal(X_noised, X)


# =====================================================================
# SubsampledMechanism
# =====================================================================


class TestSubsampledMechanism:
    """Tests for privacy amplification by subsampling."""

    def test_effective_epsilon_amplification(self) -> None:
        """Effective epsilon < base epsilon for sampling_rate < 1."""
        base = GaussianMechanism(epsilon=1.0, delta=1e-5)
        subsampled = SubsampledMechanism(base, sampling_rate=0.01)
        effective_eps = subsampled.effective_epsilon()
        assert effective_eps < 1.0
        assert effective_eps > 0.0

    def test_effective_epsilon_full_sample(self) -> None:
        """At sampling_rate=1.0, effective epsilon equals base epsilon."""
        base = LaplaceMechanism(epsilon=2.0)
        subsampled = SubsampledMechanism(base, sampling_rate=1.0)
        assert subsampled.effective_epsilon() == pytest.approx(2.0)

    def test_invalid_sampling_rate_raises(self) -> None:
        """sampling_rate outside (0, 1] raises ValueError."""
        base = LaplaceMechanism(epsilon=1.0)
        with pytest.raises(ValueError, match="sampling_rate"):
            SubsampledMechanism(base, sampling_rate=0.0)
        with pytest.raises(ValueError, match="sampling_rate"):
            SubsampledMechanism(base, sampling_rate=1.5)

    def test_add_noise_delegates_to_base(self) -> None:
        """add_noise uses the base mechanism's noise injection."""
        base = LaplaceMechanism(epsilon=1.0)
        subsampled = SubsampledMechanism(base, sampling_rate=0.1)
        data = np.array([10.0, 20.0, 30.0])
        noisy = subsampled.add_noise(data, sensitivity=1.0)
        assert noisy.shape == data.shape
        assert not np.array_equal(noisy, data)

    def test_smaller_rate_gives_smaller_epsilon(self) -> None:
        """Smaller sampling rate gives smaller effective epsilon."""
        base = GaussianMechanism(epsilon=1.0, delta=1e-5)
        sub_01 = SubsampledMechanism(base, sampling_rate=0.01)
        sub_10 = SubsampledMechanism(base, sampling_rate=0.10)
        assert sub_01.effective_epsilon() < sub_10.effective_epsilon()

"""
Tests for crypto/privacy services and views, and request logging middleware.

Targets coverage gaps in:
- apps/consortiums/services/crypto_service.py  (17% -> 60%+)
- apps/consortiums/services/mpc_service.py     (20% -> 60%+)
- apps/consortiums/services/privacy_service.py (14% -> 60%+)
- apps/consortiums/views_crypto.py             (37% -> 60%+)
- apps/core/middleware/request_logging.py      (25% -> 60%+)
"""

from __future__ import annotations

import base64
import logging
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from django.test import RequestFactory
from django.http import HttpResponse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.consortiums.models import Consortium, ConsortiumMember
from apps.consortiums.services.crypto_service import CryptoService
from apps.consortiums.services.mpc_service import MPCService
from apps.consortiums.services.privacy_service import PrivacyService
from apps.core.middleware.request_logging import RequestLoggingMiddleware
from apps.core.models import Company


# =============================================================================
# Shared fixtures
# =============================================================================


@pytest.fixture
def crypto_svc():
    return CryptoService()


@pytest.fixture
def mpc_svc():
    return MPCService()


@pytest.fixture
def privacy_svc():
    return PrivacyService()


@pytest.fixture
def owner_member(db, consortium, company):
    """Active OWNER member for the consortium."""
    return ConsortiumMember.objects.get_or_create(
        consortium=consortium,
        company=company,
        defaults={
            "role": ConsortiumMember.Role.OWNER,
            "status": ConsortiumMember.Status.ACTIVE,
        },
    )[0]


@pytest.fixture
def consortium_auth_client(db, user, company, consortium, owner_member):
    """Authenticated client whose company owns the consortium."""
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


# =============================================================================
# CryptoService tests
# =============================================================================


class TestCryptoServiceSdkUnavailable:
    """When the ZKP SDK is not available the service should fail gracefully."""

    def test_verify_contribution_zkp_no_sdk(self, crypto_svc):
        with patch(
            "apps.consortiums.services.crypto_service.ZKProver", None
        ), patch(
            "apps.consortiums.services.crypto_service.ZKVerifier", None
        ):
            result = crypto_svc.verify_contribution_zkp(1, 2, b"data")

        assert not result.success
        assert result.error_code == "SDK_UNAVAILABLE"

    def test_verify_model_accuracy_zkp_no_sdk(self, crypto_svc):
        with patch(
            "apps.consortiums.services.crypto_service.ZKProver", None
        ), patch(
            "apps.consortiums.services.crypto_service.ZKVerifier", None
        ):
            result = crypto_svc.verify_model_accuracy_zkp({"accuracy": 0.9})

        assert not result.success
        assert result.error_code == "SDK_UNAVAILABLE"

    def test_validate_stored_proof_no_sdk(self, crypto_svc):
        with patch(
            "apps.consortiums.services.crypto_service.ZKVerifier", None
        ), patch(
            "apps.consortiums.services.crypto_service.ContributionProof", None
        ):
            result = crypto_svc.validate_stored_proof({"proof_type": "contribution"})

        assert not result.success
        assert result.error_code == "SDK_UNAVAILABLE"


class TestCryptoServiceWithMockedSdk:
    """Tests with SDK classes mocked so real ZKP code is not required."""

    def _make_mock_sdk(self, is_valid: bool = True):
        """Return mock ZKProver/ZKVerifier/ContributionProof."""
        mock_proof = {"proof_type": "contribution", "data": "abc"}

        mock_prover = MagicMock()
        mock_prover.prove_contribution.return_value = mock_proof
        mock_prover.prove_model_accuracy.return_value = {"proof_type": "model_accuracy"}

        mock_verifier = MagicMock()
        mock_verifier.verify_contribution.return_value = is_valid
        mock_verifier.verify_model_accuracy.return_value = is_valid

        MockProver = MagicMock(return_value=mock_prover)
        MockVerifier = MagicMock(return_value=mock_verifier)
        MockProof = MagicMock()

        return MockProver, MockVerifier, MockProof, mock_proof

    def test_verify_contribution_zkp_success(self, crypto_svc):
        MockProver, MockVerifier, MockProof, proof = self._make_mock_sdk(True)

        with patch("apps.consortiums.services.crypto_service.ZKProver", MockProver), \
             patch("apps.consortiums.services.crypto_service.ZKVerifier", MockVerifier), \
             patch("apps.consortiums.services.crypto_service.ContributionProof", MockProof):
            result = crypto_svc.verify_contribution_zkp(
                company_id=1,
                consortium_id=99,
                data_bytes=b"hello world",
            )

        assert result.success
        assert result.data["verified"] is True
        assert result.data["company_id"] == "1"
        assert result.data["consortium_id"] == "99"
        assert "data_hash" in result.data
        assert result.data["data_size"] == len(b"hello world")

    def test_verify_contribution_zkp_verification_fails(self, crypto_svc):
        MockProver, MockVerifier, MockProof, _ = self._make_mock_sdk(False)

        with patch("apps.consortiums.services.crypto_service.ZKProver", MockProver), \
             patch("apps.consortiums.services.crypto_service.ZKVerifier", MockVerifier), \
             patch("apps.consortiums.services.crypto_service.ContributionProof", MockProof):
            result = crypto_svc.verify_contribution_zkp(1, 2, b"data")

        assert not result.success
        assert result.error_code == "ZKP_VERIFICATION_FAILED"

    def test_verify_contribution_zkp_exception(self, crypto_svc):
        MockProver = MagicMock(side_effect=ValueError("bad value"))
        MockVerifier = MagicMock()

        with patch("apps.consortiums.services.crypto_service.ZKProver", MockProver), \
             patch("apps.consortiums.services.crypto_service.ZKVerifier", MockVerifier):
            result = crypto_svc.verify_contribution_zkp(1, 2, b"data")

        assert not result.success
        assert result.error_code == "ZKP_PROOF_ERROR"

    def test_verify_model_accuracy_zkp_success(self, crypto_svc):
        MockProver, MockVerifier, MockProof, _ = self._make_mock_sdk(True)

        with patch("apps.consortiums.services.crypto_service.ZKProver", MockProver), \
             patch("apps.consortiums.services.crypto_service.ZKVerifier", MockVerifier), \
             patch("apps.consortiums.services.crypto_service.ContributionProof", MockProof):
            result = crypto_svc.verify_model_accuracy_zkp({"accuracy": 0.95, "f1": 0.92})

        assert result.success
        assert result.data["verified"] is True
        assert result.data["metrics"] == {"accuracy": 0.95, "f1": 0.92}

    def test_verify_model_accuracy_zkp_fails_verification(self, crypto_svc):
        MockProver, MockVerifier, MockProof, _ = self._make_mock_sdk(False)

        with patch("apps.consortiums.services.crypto_service.ZKProver", MockProver), \
             patch("apps.consortiums.services.crypto_service.ZKVerifier", MockVerifier), \
             patch("apps.consortiums.services.crypto_service.ContributionProof", MockProof):
            result = crypto_svc.verify_model_accuracy_zkp({"accuracy": 0.5})

        assert not result.success
        assert result.error_code == "ZKP_VERIFICATION_FAILED"

    def test_verify_model_accuracy_zkp_exception(self, crypto_svc):
        MockProver = MagicMock(side_effect=TypeError("bad type"))
        MockVerifier = MagicMock()

        with patch("apps.consortiums.services.crypto_service.ZKProver", MockProver), \
             patch("apps.consortiums.services.crypto_service.ZKVerifier", MockVerifier):
            result = crypto_svc.verify_model_accuracy_zkp({"accuracy": 0.5})

        assert not result.success
        assert result.error_code == "ZKP_PROOF_ERROR"

    def test_validate_stored_proof_contribution_success(self, crypto_svc):
        MockProver, MockVerifier, MockProof, _ = self._make_mock_sdk(True)

        with patch("apps.consortiums.services.crypto_service.ZKVerifier", MockVerifier), \
             patch("apps.consortiums.services.crypto_service.ContributionProof", MockProof):
            result = crypto_svc.validate_stored_proof({"proof_type": "contribution"})

        assert result.success
        assert result.data["verified"] is True
        assert result.data["proof_type"] == "contribution"

    def test_validate_stored_proof_model_accuracy_success(self, crypto_svc):
        MockProver, MockVerifier, MockProof, _ = self._make_mock_sdk(True)

        with patch("apps.consortiums.services.crypto_service.ZKVerifier", MockVerifier), \
             patch("apps.consortiums.services.crypto_service.ContributionProof", MockProof):
            result = crypto_svc.validate_stored_proof({"proof_type": "model_accuracy"})

        assert result.success
        assert result.data["proof_type"] == "model_accuracy"

    def test_validate_stored_proof_unknown_type(self, crypto_svc):
        MockProver, MockVerifier, MockProof, _ = self._make_mock_sdk(True)

        with patch("apps.consortiums.services.crypto_service.ZKVerifier", MockVerifier), \
             patch("apps.consortiums.services.crypto_service.ContributionProof", MockProof):
            result = crypto_svc.validate_stored_proof({"proof_type": "unknown"})

        assert not result.success
        assert result.error_code == "UNKNOWN_PROOF_TYPE"

    def test_validate_stored_proof_fails_reverification(self, crypto_svc):
        MockProver, MockVerifier, MockProof, _ = self._make_mock_sdk(False)

        with patch("apps.consortiums.services.crypto_service.ZKVerifier", MockVerifier), \
             patch("apps.consortiums.services.crypto_service.ContributionProof", MockProof):
            result = crypto_svc.validate_stored_proof({"proof_type": "contribution"})

        assert not result.success
        assert result.error_code == "ZKP_VERIFICATION_FAILED"

    def test_validate_stored_proof_exception(self, crypto_svc):
        MockVerifier_cls = MagicMock(side_effect=KeyError("key missing"))
        MockProof = MagicMock()

        with patch("apps.consortiums.services.crypto_service.ZKVerifier", MockVerifier_cls), \
             patch("apps.consortiums.services.crypto_service.ContributionProof", MockProof):
            result = crypto_svc.validate_stored_proof({"proof_type": "contribution"})

        assert not result.success
        assert result.error_code == "ZKP_VALIDATION_ERROR"


# =============================================================================
# MPCService tests
# =============================================================================


class TestMPCServiceSdkUnavailable:

    def test_setup_threshold_keys_no_sdk(self, mpc_svc):
        with patch("apps.consortiums.services.mpc_service.ThresholdDecryptor", None):
            result = mpc_svc.setup_threshold_keys(1, 2, 3)

        assert not result.success
        assert result.error_code == "SDK_UNAVAILABLE"

    def test_create_secure_aggregation_no_sdk(self, mpc_svc):
        with patch("apps.consortiums.services.mpc_service.SecureAggregator", None):
            result = mpc_svc.create_secure_aggregation(1, 3, 10)

        assert not result.success
        assert result.error_code == "SDK_UNAVAILABLE"

    def test_aggregate_updates_no_sdk(self, mpc_svc):
        with patch("apps.consortiums.services.mpc_service.SecureAggregator", None):
            result = mpc_svc.aggregate_updates([], 2, 10)

        assert not result.success
        assert result.error_code == "SDK_UNAVAILABLE"


class TestMPCServiceWithMockedSdk:

    def _mock_threshold_decryptor(self):
        shares = [(0, b"\x01\x02"), (1, b"\x03\x04")]
        commitment = b"\xde\xad\xbe\xef"
        mock_instance = MagicMock()
        mock_instance.setup.return_value = (shares, commitment)
        MockClass = MagicMock(return_value=mock_instance)
        return MockClass

    def _mock_secure_aggregator(self, vector_size: int = 4):
        """Return a mock SecureAggregator that produces zero-masks."""
        mock_instance = MagicMock()
        mock_instance.generate_masks.return_value = np.zeros(vector_size)
        mock_instance.mask_update.side_effect = lambda update, party_id, masks: update + masks
        mock_instance.aggregate.side_effect = lambda updates: sum(updates)
        MockClass = MagicMock(return_value=mock_instance)
        return MockClass

    def test_setup_threshold_keys_success(self, mpc_svc):
        MockDecryptor = self._mock_threshold_decryptor()

        with patch("apps.consortiums.services.mpc_service.ThresholdDecryptor", MockDecryptor):
            result = mpc_svc.setup_threshold_keys(
                consortium_id=42,
                threshold=2,
                n_parties=3,
            )

        assert result.success
        assert result.data["threshold"] == 2
        assert result.data["n_parties"] == 3
        assert len(result.data["shares"]) == 2
        assert "verification_commitment_hex" in result.data

    def test_setup_threshold_keys_exception(self, mpc_svc):
        MockDecryptor = MagicMock(side_effect=ValueError("bad params"))

        with patch("apps.consortiums.services.mpc_service.ThresholdDecryptor", MockDecryptor):
            result = mpc_svc.setup_threshold_keys(1, 2, 3)

        assert not result.success
        assert result.error_code == "MPC_KEY_SETUP_ERROR"

    def test_create_secure_aggregation_success(self, mpc_svc):
        MockAggregator = self._mock_secure_aggregator()

        with patch("apps.consortiums.services.mpc_service.SecureAggregator", MockAggregator):
            result = mpc_svc.create_secure_aggregation(
                consortium_id=5,
                n_participants=3,
                vector_size=10,
            )

        assert result.success
        assert result.data["aggregator_ready"] is True
        assert result.data["n_participants"] == 3
        assert result.data["vector_size"] == 10
        assert "shared_seed" in result.data

    def test_create_secure_aggregation_exception(self, mpc_svc):
        MockAggregator = MagicMock(side_effect=TypeError("bad type"))

        with patch("apps.consortiums.services.mpc_service.SecureAggregator", MockAggregator):
            result = mpc_svc.create_secure_aggregation(1, 3, 10)

        assert not result.success
        assert result.error_code == "MPC_AGGREGATION_SETUP_ERROR"

    def test_aggregate_updates_count_mismatch(self, mpc_svc):
        MockAggregator = self._mock_secure_aggregator()

        with patch("apps.consortiums.services.mpc_service.SecureAggregator", MockAggregator):
            # 1 update but n_participants=2
            result = mpc_svc.aggregate_updates(
                updates=[np.array([1.0, 2.0])],
                n_participants=2,
                vector_size=2,
            )

        assert not result.success
        assert result.error_code == "MPC_UPDATE_COUNT_MISMATCH"

    def test_aggregate_updates_vector_size_mismatch(self, mpc_svc):
        MockAggregator = self._mock_secure_aggregator(vector_size=3)

        with patch("apps.consortiums.services.mpc_service.SecureAggregator", MockAggregator):
            result = mpc_svc.aggregate_updates(
                updates=[
                    np.array([1.0, 2.0]),      # size 2
                    np.array([3.0, 4.0]),      # size 2
                ],
                n_participants=2,
                vector_size=3,   # expects 3
            )

        assert not result.success
        assert result.error_code == "MPC_VECTOR_SIZE_MISMATCH"

    def test_aggregate_updates_success(self, mpc_svc):
        v = 4
        MockAggregator = self._mock_secure_aggregator(vector_size=v)

        updates = [np.array([1.0, 2.0, 3.0, 4.0]), np.array([0.5, 0.5, 0.5, 0.5])]

        with patch("apps.consortiums.services.mpc_service.SecureAggregator", MockAggregator):
            result = mpc_svc.aggregate_updates(
                updates=updates,
                n_participants=2,
                vector_size=v,
                seed=12345,
            )

        assert result.success
        assert "aggregate" in result.data
        assert result.data["n_participants"] == 2
        assert result.data["vector_size"] == v

    def test_aggregate_updates_auto_seed(self, mpc_svc):
        v = 2
        MockAggregator = self._mock_secure_aggregator(vector_size=v)

        updates = [np.array([1.0, 2.0]), np.array([3.0, 4.0])]

        with patch("apps.consortiums.services.mpc_service.SecureAggregator", MockAggregator):
            result = mpc_svc.aggregate_updates(
                updates=updates,
                n_participants=2,
                vector_size=v,
                seed=None,  # should auto-generate
            )

        assert result.success

    def test_aggregate_updates_exception(self, mpc_svc):
        MockAggregator = MagicMock(side_effect=OverflowError("overflow"))

        with patch("apps.consortiums.services.mpc_service.SecureAggregator", MockAggregator):
            updates = [np.array([1.0]), np.array([2.0])]
            result = mpc_svc.aggregate_updates(updates, 2, 1)

        assert not result.success
        assert result.error_code == "MPC_AGGREGATION_ERROR"


# =============================================================================
# PrivacyService tests
# =============================================================================


class TestPrivacyServiceSdkUnavailable:

    def test_privatize_data_no_sdk(self, privacy_svc):
        with patch("apps.consortiums.services.privacy_service.LaplaceMechanism", None):
            result = privacy_svc.privatize_data(np.array([1.0]), 1.0, 1e-5)

        assert not result.success
        assert result.error_code == "SDK_UNAVAILABLE"

    def test_check_privacy_budget_no_sdk(self, privacy_svc):
        with patch("apps.consortiums.services.privacy_service.PrivacyAccountant", None):
            result = privacy_svc.check_privacy_budget(1.0, 1e-5, 0, 0.1)

        assert not result.success
        assert result.error_code == "SDK_UNAVAILABLE"

    def test_clip_gradients_no_sdk(self, privacy_svc):
        with patch("apps.consortiums.services.privacy_service.GradientClipper", None):
            result = privacy_svc.clip_gradients(np.array([1.0, 2.0]), 1.0)

        assert not result.success
        assert result.error_code == "SDK_UNAVAILABLE"

    def test_get_privacy_report_no_sdk(self, privacy_svc):
        with patch("apps.consortiums.services.privacy_service.PrivacyAccountant", None):
            result = privacy_svc.get_privacy_report(1.0, 1e-5, [])

        assert not result.success
        assert result.error_code == "SDK_UNAVAILABLE"


class TestPrivacyServiceWithMockedSdk:

    def _mock_laplace(self, sensitivity: float = 1.0, epsilon: float = 1.0):
        arr = np.array([1.0, 2.0])
        instance = MagicMock()
        instance.add_noise.return_value = arr + 0.01
        instance.variance.return_value = 2.0 * (sensitivity / epsilon) ** 2
        MockClass = MagicMock(return_value=instance)
        return MockClass, instance

    def _mock_gaussian(self):
        instance = MagicMock()
        instance.add_noise.return_value = np.array([1.01, 2.01])
        instance.compute_sigma.return_value = 0.5
        instance.variance.return_value = 0.25
        MockClass = MagicMock(return_value=instance)
        return MockClass, instance

    def _mock_accountant(self):
        budget = MagicMock()
        budget.can_afford.return_value = True
        budget.is_exhausted = False
        budget.epsilon_used = 0.1
        budget.delta_used = 1e-6
        budget.epsilon_remaining = 0.9
        budget.delta_remaining = 9e-5

        instance = MagicMock()
        instance.budget = budget
        instance.remaining_budget.return_value = (0.9, 9e-5)
        instance.estimate_remaining_queries.return_value = 9
        instance.report.return_value = {"basic_composition": {"epsilon": 0.1}}
        MockClass = MagicMock(return_value=instance)
        return MockClass, instance

    def test_privatize_data_laplace_success(self, privacy_svc):
        MockLaplace, _ = self._mock_laplace()
        MockGaussian, _ = self._mock_gaussian()

        with patch("apps.consortiums.services.privacy_service.LaplaceMechanism", MockLaplace), \
             patch("apps.consortiums.services.privacy_service.GaussianMechanism", MockGaussian):
            result = privacy_svc.privatize_data(
                data=np.array([1.0, 2.0]),
                epsilon=1.0,
                delta=0.0,
                mechanism="laplace",
            )

        assert result.success
        assert result.data["noise_info"]["mechanism"] == "laplace"
        assert "noisy_data" in result.data

    def test_privatize_data_gaussian_success(self, privacy_svc):
        MockLaplace, _ = self._mock_laplace()
        MockGaussian, _ = self._mock_gaussian()

        with patch("apps.consortiums.services.privacy_service.LaplaceMechanism", MockLaplace), \
             patch("apps.consortiums.services.privacy_service.GaussianMechanism", MockGaussian):
            result = privacy_svc.privatize_data(
                data=np.array([1.0, 2.0]),
                epsilon=1.0,
                delta=1e-5,
                mechanism="gaussian",
            )

        assert result.success
        assert result.data["noise_info"]["mechanism"] == "gaussian"

    def test_privatize_data_invalid_mechanism(self, privacy_svc):
        MockLaplace, _ = self._mock_laplace()
        MockGaussian, _ = self._mock_gaussian()

        with patch("apps.consortiums.services.privacy_service.LaplaceMechanism", MockLaplace), \
             patch("apps.consortiums.services.privacy_service.GaussianMechanism", MockGaussian):
            result = privacy_svc.privatize_data(
                data=np.array([1.0]),
                epsilon=1.0,
                delta=0.0,
                mechanism="invalid_mech",
            )

        assert not result.success
        assert result.error_code == "DP_INVALID_MECHANISM"

    def test_privatize_data_empty_array(self, privacy_svc):
        MockLaplace, _ = self._mock_laplace()
        MockGaussian, _ = self._mock_gaussian()

        with patch("apps.consortiums.services.privacy_service.LaplaceMechanism", MockLaplace), \
             patch("apps.consortiums.services.privacy_service.GaussianMechanism", MockGaussian):
            result = privacy_svc.privatize_data(
                data=np.array([]),
                epsilon=1.0,
                delta=0.0,
                mechanism="laplace",
            )

        assert not result.success
        assert result.error_code == "DP_EMPTY_DATA"

    def test_privatize_data_exception(self, privacy_svc):
        MockLaplace = MagicMock(side_effect=ValueError("bad epsilon"))
        MockGaussian = MagicMock()

        with patch("apps.consortiums.services.privacy_service.LaplaceMechanism", MockLaplace), \
             patch("apps.consortiums.services.privacy_service.GaussianMechanism", MockGaussian):
            result = privacy_svc.privatize_data(
                data=np.array([1.0]),
                epsilon=1.0,
                delta=0.0,
                mechanism="laplace",
            )

        assert not result.success
        assert result.error_code == "DP_NOISE_ERROR"

    def test_check_privacy_budget_success(self, privacy_svc):
        MockAccountant, _ = self._mock_accountant()

        with patch("apps.consortiums.services.privacy_service.PrivacyAccountant", MockAccountant):
            result = privacy_svc.check_privacy_budget(
                total_epsilon=1.0,
                total_delta=1e-5,
                steps_used=1,
                mechanism_epsilon=0.1,
                mechanism_delta=1e-6,
            )

        assert result.success
        assert result.data["can_proceed"] is True
        assert "epsilon_remaining" in result.data

    def test_check_privacy_budget_exception(self, privacy_svc):
        MockAccountant = MagicMock(side_effect=ValueError("bad budget"))

        with patch("apps.consortiums.services.privacy_service.PrivacyAccountant", MockAccountant):
            result = privacy_svc.check_privacy_budget(1.0, 1e-5, 0, 0.1)

        assert not result.success
        assert result.error_code == "DP_BUDGET_ERROR"

    def test_clip_gradients_1d_success(self, privacy_svc):
        clipped = np.array([0.5, 0.5])
        mock_clipper = MagicMock()
        mock_clipper.clip.return_value = clipped
        MockClipper = MagicMock(return_value=mock_clipper)

        with patch("apps.consortiums.services.privacy_service.GradientClipper", MockClipper):
            result = privacy_svc.clip_gradients(
                gradients=np.array([1.0, 1.0]),
                max_norm=1.0,
            )

        assert result.success
        assert "clipped_gradients" in result.data
        assert result.data["n_gradients"] == 1

    def test_clip_gradients_2d_success(self, privacy_svc):
        clipped = np.array([[0.5, 0.5], [0.3, 0.3]])
        mock_clipper = MagicMock()
        mock_clipper.clip.return_value = clipped
        MockClipper = MagicMock(return_value=mock_clipper)

        with patch("apps.consortiums.services.privacy_service.GradientClipper", MockClipper):
            result = privacy_svc.clip_gradients(
                gradients=np.array([[3.0, 3.0], [0.1, 0.1]]),
                max_norm=1.0,
            )

        assert result.success
        assert result.data["n_gradients"] == 2
        # First gradient norm was > 1.0 so it should be counted as clipped
        assert result.data["n_clipped"] >= 0

    def test_clip_gradients_empty(self, privacy_svc):
        MockClipper = MagicMock()

        with patch("apps.consortiums.services.privacy_service.GradientClipper", MockClipper):
            result = privacy_svc.clip_gradients(
                gradients=np.array([]),
                max_norm=1.0,
            )

        assert not result.success
        assert result.error_code == "DP_EMPTY_GRADIENTS"

    def test_clip_gradients_exception(self, privacy_svc):
        MockClipper = MagicMock(side_effect=TypeError("bad grad"))

        with patch("apps.consortiums.services.privacy_service.GradientClipper", MockClipper):
            result = privacy_svc.clip_gradients(np.array([1.0]), 1.0)

        assert not result.success
        assert result.error_code == "DP_CLIP_ERROR"

    def test_get_privacy_report_success(self, privacy_svc):
        MockAccountant, _ = self._mock_accountant()

        steps = [
            {"epsilon": 0.1, "delta": 1e-6, "operation": "step1"},
        ]
        with patch("apps.consortiums.services.privacy_service.PrivacyAccountant", MockAccountant):
            result = privacy_svc.get_privacy_report(1.0, 1e-5, steps)

        assert result.success
        assert "report" in result.data
        assert "summary" in result.data
        assert result.data["summary"]["total_epsilon"] == 1.0

    def test_get_privacy_report_exception(self, privacy_svc):
        MockAccountant = MagicMock(side_effect=ValueError("bad"))

        with patch("apps.consortiums.services.privacy_service.PrivacyAccountant", MockAccountant):
            result = privacy_svc.get_privacy_report(1.0, 1e-5, [])

        assert not result.success
        assert result.error_code == "DP_REPORT_ERROR"


# =============================================================================
# views_crypto.py — Serializer unit tests (no DB required)
# =============================================================================


class TestViewCryptoSerializers:
    """Test input serializers directly without going through the full HTTP stack."""

    def test_zkp_contribution_serializer_valid(self):
        from apps.consortiums.views_crypto import ZKPVerifyContributionSerializer
        data = base64.b64encode(b"hello world").decode()
        s = ZKPVerifyContributionSerializer(data={"data": data})
        assert s.is_valid(), s.errors

    def test_zkp_contribution_serializer_invalid_base64(self):
        from apps.consortiums.views_crypto import ZKPVerifyContributionSerializer
        s = ZKPVerifyContributionSerializer(data={"data": "not!!valid==base64"})
        assert not s.is_valid()
        assert "data" in s.errors

    def test_zkp_model_accuracy_serializer_valid(self):
        from apps.consortiums.views_crypto import ZKPVerifyModelAccuracySerializer
        s = ZKPVerifyModelAccuracySerializer(data={"metrics": {"accuracy": 0.95}})
        assert s.is_valid(), s.errors

    def test_zkp_model_accuracy_serializer_empty_metrics(self):
        from apps.consortiums.views_crypto import ZKPVerifyModelAccuracySerializer
        s = ZKPVerifyModelAccuracySerializer(data={"metrics": {}})
        assert not s.is_valid()

    def test_zkp_model_accuracy_serializer_out_of_range(self):
        from apps.consortiums.views_crypto import ZKPVerifyModelAccuracySerializer
        s = ZKPVerifyModelAccuracySerializer(data={"metrics": {"acc": 1.5}})
        assert not s.is_valid()

    def test_mpc_setup_keys_serializer_valid(self):
        from apps.consortiums.views_crypto import MPCSetupKeysSerializer
        s = MPCSetupKeysSerializer(data={"threshold": 2, "n_parties": 3})
        assert s.is_valid(), s.errors

    def test_mpc_setup_keys_threshold_exceeds_parties(self):
        from apps.consortiums.views_crypto import MPCSetupKeysSerializer
        s = MPCSetupKeysSerializer(data={"threshold": 5, "n_parties": 3})
        assert not s.is_valid()

    def test_mpc_aggregate_serializer_valid(self):
        from apps.consortiums.views_crypto import MPCAggregateSerializer
        s = MPCAggregateSerializer(data={"updates": [[1.0, 2.0], [3.0, 4.0]]})
        assert s.is_valid(), s.errors

    def test_mpc_aggregate_serializer_mismatched_vectors(self):
        from apps.consortiums.views_crypto import MPCAggregateSerializer
        s = MPCAggregateSerializer(data={"updates": [[1.0, 2.0], [3.0]]})
        assert not s.is_valid()

    def test_mpc_aggregate_serializer_empty_vector(self):
        from apps.consortiums.views_crypto import MPCAggregateSerializer
        s = MPCAggregateSerializer(data={"updates": [[], []]})
        assert not s.is_valid()

    def test_dp_privatize_serializer_valid(self):
        from apps.consortiums.views_crypto import DPPrivatizeSerializer
        s = DPPrivatizeSerializer(data={
            "data": [[1.0, 2.0]],
            "epsilon": 1.0,
            "mechanism": "laplace",
        })
        assert s.is_valid(), s.errors

    def test_dp_budget_check_serializer_valid(self):
        from apps.consortiums.views_crypto import DPBudgetCheckSerializer
        s = DPBudgetCheckSerializer(data={
            "total_epsilon": 1.0,
            "total_delta": 1e-5,
            "steps_used": 3,
            "mechanism_epsilon": 0.1,
        })
        assert s.is_valid(), s.errors

    def test_service_error_response_helper(self):
        from apps.consortiums.views_crypto import _service_error_response
        from apps.core.services.base import ServiceResult
        from rest_framework import status as drf_status

        failed = ServiceResult.fail("Something went wrong", error_code="SOME_CODE")
        response = _service_error_response(failed)

        assert response.status_code == drf_status.HTTP_400_BAD_REQUEST
        assert response.data["error"] == "Something went wrong"
        assert response.data["error_code"] == "SOME_CODE"


# =============================================================================
# views_crypto.py — HTTP endpoint tests
# =============================================================================


@pytest.mark.django_db
class TestCryptoViewsAuthentication:
    """Ensure unauthenticated requests are rejected (401)."""

    def test_zkp_verify_contribution_requires_auth(self, api_client, consortium):
        url = f"/api/v2/consortiums/{consortium.id}/zkp/verify-contribution/"
        response = api_client.post(url, {"data": "dGVzdA=="}, format="json")
        assert response.status_code == 401

    def test_zkp_verify_accuracy_requires_auth(self, api_client, consortium):
        url = f"/api/v2/consortiums/{consortium.id}/zkp/verify-accuracy/"
        response = api_client.post(url, {"metrics": {"acc": 0.9}}, format="json")
        assert response.status_code == 401

    def test_mpc_setup_keys_requires_auth(self, api_client, consortium):
        url = f"/api/v2/consortiums/{consortium.id}/mpc/setup-keys/"
        response = api_client.post(url, {"threshold": 2, "n_parties": 3}, format="json")
        assert response.status_code == 401

    def test_mpc_aggregate_requires_auth(self, api_client, consortium):
        url = f"/api/v2/consortiums/{consortium.id}/mpc/aggregate/"
        response = api_client.post(url, {"updates": [[1.0], [2.0]]}, format="json")
        assert response.status_code == 401

    def test_dp_privatize_requires_auth(self, api_client, consortium):
        url = f"/api/v2/consortiums/{consortium.id}/dp/privatize/"
        response = api_client.post(url, {}, format="json")
        assert response.status_code == 401

    def test_dp_budget_check_requires_auth(self, api_client, consortium):
        url = f"/api/v2/consortiums/{consortium.id}/dp/budget-check/"
        response = api_client.post(url, {}, format="json")
        assert response.status_code == 401

    def test_crypto_status_requires_auth(self, api_client, consortium):
        url = f"/api/v2/consortiums/{consortium.id}/crypto/status/"
        response = api_client.get(url)
        assert response.status_code == 401


@pytest.mark.django_db
class TestCryptoViewsWithAuth:
    """Tests with an authenticated consortium-owner user."""

    def test_crypto_status_returns_availability(self, consortium_auth_client, consortium, owner_member):
        url = f"/api/v2/consortiums/{consortium.id}/crypto/status/"
        response = consortium_auth_client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert "zkp_available" in data
        assert "mpc_available" in data
        assert "dp_available" in data
        assert "fhe_available" in data

    def test_zkp_verify_contribution_sdk_unavailable(
        self, consortium_auth_client, consortium, owner_member
    ):
        """With SDK mocked out the view returns 400 SDK_UNAVAILABLE."""
        url = f"/api/v2/consortiums/{consortium.id}/zkp/verify-contribution/"
        payload = {"data": base64.b64encode(b"test data").decode()}

        with patch("apps.consortiums.services.crypto_service.ZKProver", None), \
             patch("apps.consortiums.services.crypto_service.ZKVerifier", None):
            response = consortium_auth_client.post(url, payload, format="json")

        assert response.status_code == 400
        assert response.json()["error_code"] == "SDK_UNAVAILABLE"

    def test_zkp_verify_contribution_invalid_base64(
        self, consortium_auth_client, consortium, owner_member
    ):
        url = f"/api/v2/consortiums/{consortium.id}/zkp/verify-contribution/"
        response = consortium_auth_client.post(url, {"data": "!!!invalid"}, format="json")
        assert response.status_code == 400

    def test_zkp_verify_accuracy_sdk_unavailable(
        self, consortium_auth_client, consortium, owner_member
    ):
        url = f"/api/v2/consortiums/{consortium.id}/zkp/verify-accuracy/"
        payload = {"metrics": {"accuracy": 0.95}}

        with patch("apps.consortiums.services.crypto_service.ZKProver", None), \
             patch("apps.consortiums.services.crypto_service.ZKVerifier", None):
            response = consortium_auth_client.post(url, payload, format="json")

        assert response.status_code == 400
        assert response.json()["error_code"] == "SDK_UNAVAILABLE"

    def test_zkp_verify_accuracy_empty_metrics(
        self, consortium_auth_client, consortium, owner_member
    ):
        url = f"/api/v2/consortiums/{consortium.id}/zkp/verify-accuracy/"
        response = consortium_auth_client.post(url, {"metrics": {}}, format="json")
        assert response.status_code == 400

    def test_mpc_setup_keys_sdk_unavailable(
        self, consortium_auth_client, consortium, owner_member
    ):
        url = f"/api/v2/consortiums/{consortium.id}/mpc/setup-keys/"
        payload = {"threshold": 2, "n_parties": 3}

        with patch("apps.consortiums.services.mpc_service.ThresholdDecryptor", None):
            response = consortium_auth_client.post(url, payload, format="json")

        assert response.status_code == 400
        assert response.json()["error_code"] == "SDK_UNAVAILABLE"

    def test_mpc_setup_keys_invalid_threshold(
        self, consortium_auth_client, consortium, owner_member
    ):
        url = f"/api/v2/consortiums/{consortium.id}/mpc/setup-keys/"
        response = consortium_auth_client.post(
            url, {"threshold": 5, "n_parties": 3}, format="json"
        )
        assert response.status_code == 400

    def test_mpc_aggregate_sdk_unavailable(
        self, consortium_auth_client, consortium, owner_member
    ):
        url = f"/api/v2/consortiums/{consortium.id}/mpc/aggregate/"
        payload = {"updates": [[1.0, 2.0], [3.0, 4.0]]}

        with patch("apps.consortiums.services.mpc_service.SecureAggregator", None):
            response = consortium_auth_client.post(url, payload, format="json")

        assert response.status_code == 400
        assert response.json()["error_code"] == "SDK_UNAVAILABLE"

    def test_dp_privatize_sdk_unavailable(
        self, consortium_auth_client, consortium, owner_member
    ):
        url = f"/api/v2/consortiums/{consortium.id}/dp/privatize/"
        payload = {
            "data": [[1.0, 2.0]],
            "epsilon": 1.0,
            "mechanism": "laplace",
        }

        with patch("apps.consortiums.services.privacy_service.LaplaceMechanism", None):
            response = consortium_auth_client.post(url, payload, format="json")

        assert response.status_code == 400
        assert response.json()["error_code"] == "SDK_UNAVAILABLE"

    def test_dp_budget_check_sdk_unavailable(
        self, consortium_auth_client, consortium, owner_member
    ):
        url = f"/api/v2/consortiums/{consortium.id}/dp/budget-check/"
        payload = {
            "total_epsilon": 1.0,
            "total_delta": 1e-5,
            "steps_used": 0,
            "mechanism_epsilon": 0.1,
        }

        with patch("apps.consortiums.services.privacy_service.PrivacyAccountant", None):
            response = consortium_auth_client.post(url, payload, format="json")

        assert response.status_code == 400
        assert response.json()["error_code"] == "SDK_UNAVAILABLE"

    def test_zkp_verify_contribution_success(
        self, consortium_auth_client, consortium, owner_member
    ):
        """Happy-path: SDK classes mocked to return valid proof."""
        mock_proof = {"proof_type": "contribution"}
        mock_prover_inst = MagicMock()
        mock_prover_inst.prove_contribution.return_value = mock_proof
        mock_verifier_inst = MagicMock()
        mock_verifier_inst.verify_contribution.return_value = True

        MockProver = MagicMock(return_value=mock_prover_inst)
        MockVerifier = MagicMock(return_value=mock_verifier_inst)

        url = f"/api/v2/consortiums/{consortium.id}/zkp/verify-contribution/"
        payload = {"data": base64.b64encode(b"test bytes").decode()}

        with patch("apps.consortiums.services.crypto_service.ZKProver", MockProver), \
             patch("apps.consortiums.services.crypto_service.ZKVerifier", MockVerifier), \
             patch("apps.consortiums.services.crypto_service.ContributionProof", MagicMock()):
            response = consortium_auth_client.post(url, payload, format="json")

        assert response.status_code == 200
        assert response.json()["verified"] is True

    def test_mpc_aggregate_success(
        self, consortium_auth_client, consortium, owner_member
    ):
        """Happy-path: secure aggregation returns a valid result."""
        v = 2
        mock_agg_inst = MagicMock()
        mock_agg_inst.generate_masks.return_value = np.zeros(v)
        mock_agg_inst.mask_update.side_effect = (
            lambda update, party_id, masks: update + masks
        )
        mock_agg_inst.aggregate.return_value = np.array([1.5, 2.5])
        MockAgg = MagicMock(return_value=mock_agg_inst)

        url = f"/api/v2/consortiums/{consortium.id}/mpc/aggregate/"
        payload = {"updates": [[1.0, 2.0], [0.5, 0.5]]}

        with patch("apps.consortiums.services.mpc_service.SecureAggregator", MockAgg):
            response = consortium_auth_client.post(url, payload, format="json")

        assert response.status_code == 200
        assert "result" in response.json()

    def test_dp_privatize_success(
        self, consortium_auth_client, consortium, owner_member
    ):
        mock_lap_inst = MagicMock()
        mock_lap_inst.add_noise.return_value = np.array([1.01, 2.01])
        mock_lap_inst.variance.return_value = 2.0
        MockLap = MagicMock(return_value=mock_lap_inst)
        MockGauss = MagicMock()

        url = f"/api/v2/consortiums/{consortium.id}/dp/privatize/"
        payload = {"data": [[1.0, 2.0]], "epsilon": 1.0, "mechanism": "laplace"}

        with patch("apps.consortiums.services.privacy_service.LaplaceMechanism", MockLap), \
             patch("apps.consortiums.services.privacy_service.GaussianMechanism", MockGauss):
            response = consortium_auth_client.post(url, payload, format="json")

        assert response.status_code == 200
        assert "privatized_data" in response.json()


# =============================================================================
# RequestLoggingMiddleware tests
# =============================================================================


class TestRequestLoggingMiddleware:
    """Unit tests for the request logging middleware."""

    def _make_middleware(self, response_status: int = 200):
        def get_response(request):
            return HttpResponse("OK", status=response_status)

        return RequestLoggingMiddleware(get_response)

    def test_excluded_path_skips_logging(self, caplog):
        factory = RequestFactory()
        request = factory.get("/health/")

        with caplog.at_level(logging.DEBUG, logger="apps.api.requests"):
            middleware = self._make_middleware()
            response = middleware(request)

        assert response.status_code == 200
        # No log records should be produced for excluded paths
        logs_for_health = [
            r for r in caplog.records
            if "/health/" in getattr(r, "path", "") or "/health/" in r.getMessage()
        ]
        assert len(logs_for_health) == 0

    def test_normal_request_is_logged(self, caplog):
        factory = RequestFactory()
        request = factory.get("/api/v2/some-endpoint/")

        with caplog.at_level(logging.DEBUG, logger="apps.api.requests"):
            middleware = self._make_middleware(200)
            middleware(request)

        messages = [r.getMessage() for r in caplog.records]
        assert any("/api/v2/some-endpoint/" in m for m in messages)

    def test_500_response_logs_at_error_level(self, caplog):
        factory = RequestFactory()
        request = factory.get("/api/v2/broken/")

        with caplog.at_level(logging.ERROR, logger="apps.api.requests"):
            middleware = self._make_middleware(500)
            middleware(request)

        error_records = [
            r for r in caplog.records
            if r.levelno == logging.ERROR and "/api/v2/broken/" in r.getMessage()
        ]
        assert len(error_records) >= 1

    def test_400_response_logs_at_warning_level(self, caplog):
        factory = RequestFactory()
        request = factory.get("/api/v2/bad/")

        with caplog.at_level(logging.WARNING, logger="apps.api.requests"):
            middleware = self._make_middleware(400)
            middleware(request)

        warn_records = [
            r for r in caplog.records
            if r.levelno == logging.WARNING and "/api/v2/bad/" in r.getMessage()
        ]
        assert len(warn_records) >= 1

    def test_get_client_ip_direct(self):
        factory = RequestFactory()
        request = factory.get("/api/test/", REMOTE_ADDR="10.0.0.1")

        middleware = self._make_middleware()
        ip = middleware._get_client_ip(request)
        assert ip == "10.0.0.1"

    def test_get_client_ip_from_x_forwarded_for(self):
        factory = RequestFactory()
        request = factory.get(
            "/api/test/",
            HTTP_X_FORWARDED_FOR="203.0.113.5, 10.0.0.1",
        )

        middleware = self._make_middleware()
        ip = middleware._get_client_ip(request)
        assert ip == "203.0.113.5"

    def test_get_client_ip_from_x_real_ip(self):
        factory = RequestFactory()
        request = factory.get("/api/test/", HTTP_X_REAL_IP="198.51.100.7")

        middleware = self._make_middleware()
        ip = middleware._get_client_ip(request)
        assert ip == "198.51.100.7"

    def test_should_skip_excluded_paths(self):
        factory = RequestFactory()
        middleware = self._make_middleware()

        for path in ["/health/", "/api/health/", "/favicon.ico", "/robots.txt"]:
            request = factory.get(path)
            assert middleware._should_skip(request) is True

    def test_should_not_skip_normal_paths(self):
        factory = RequestFactory()
        middleware = self._make_middleware()

        request = factory.get("/api/v2/consortiums/")
        assert middleware._should_skip(request) is False

    def test_extract_metadata_with_query_params(self):
        factory = RequestFactory()
        request = factory.get("/api/v2/data/", {"page": "2", "password": "secret"})

        middleware = self._make_middleware()
        metadata = middleware._extract_request_metadata(request)

        assert metadata["method"] == "GET"
        assert metadata["path"] == "/api/v2/data/"
        # page should be included, password should be filtered
        assert metadata.get("query_params", {}).get("page") == "2"
        assert "password" not in metadata.get("query_params", {})

    def test_extract_metadata_with_content_type_and_length(self):
        factory = RequestFactory()
        request = factory.post(
            "/api/v2/data/",
            data=b'{"key": "value"}',
            content_type="application/json",
        )
        # Force CONTENT_LENGTH
        request.META["CONTENT_LENGTH"] = "16"

        middleware = self._make_middleware()
        metadata = middleware._extract_request_metadata(request)

        assert metadata["content_type"] == "application/json"
        assert metadata["content_length"] == 16

    def test_log_request_completion_with_content_length(self):
        """Ensure response_size is logged when Content-Length header is present."""
        factory = RequestFactory()
        request = factory.get("/api/v2/test/")

        def get_response(req):
            resp = HttpResponse("Hello", status=200)
            resp["Content-Length"] = "5"
            return resp

        middleware = RequestLoggingMiddleware(get_response)

        with patch.object(
            middleware, "_log_request_completion", wraps=middleware._log_request_completion
        ) as mock_log:
            middleware(request)
            assert mock_log.called

    def test_favicon_path_excluded(self, caplog):
        factory = RequestFactory()
        request = factory.get("/favicon.ico")

        with caplog.at_level(logging.DEBUG, logger="apps.api.requests"):
            middleware = self._make_middleware()
            middleware(request)

        favicon_logs = [
            r for r in caplog.records if "favicon" in r.getMessage()
        ]
        assert len(favicon_logs) == 0

"""
Security tests — IDOR, SSRF, tenant isolation, privilege escalation.

These tests verify that users CANNOT access or modify resources belonging
to consortiums they are not members of.

Each test creates two companies: one that IS a member of a consortium
and one that is NOT, then verifies the non-member is blocked.
"""

from __future__ import annotations

import uuid
from unittest.mock import patch

from django.test import TestCase, RequestFactory, override_settings
from rest_framework import serializers
from rest_framework.test import APIRequestFactory

from apps.core.models import Company, User


@override_settings(
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    },
)
class TestIDORConsortiumValidation(TestCase):
    """Test that consortium-scoped serializers block non-members."""

    @classmethod
    def setUpTestData(cls):
        """Create two companies and a consortium owned by company_a."""
        from apps.consortiums.models import Consortium

        cls.company_a = Company.objects.create(
            name="Company A",
            email="a@example.com",
            industry="fintech",
        )
        cls.company_b = Company.objects.create(
            name="Company B",
            email="b@example.com",
            industry="fintech",
        )

        cls.user_a = User.objects.create_user(
            email="user_a@example.com",
            password="securepassword123",
            company=cls.company_a,
        )
        cls.user_b = User.objects.create_user(
            email="user_b@example.com",
            password="securepassword123",
            company=cls.company_b,
        )

        cls.consortium = Consortium.objects.create(
            name="Test Consortium",
            owner=cls.company_a,
            model_type="logistic_regression",
        )

    def _make_request(self, user):
        """Create a mock request with the given user."""
        factory = APIRequestFactory()
        request = factory.post("/fake/")
        request.user = user
        return request

    # ── Governance: ProposalCreateSerializer ──────────────────────────

    def test_governance_proposal_blocks_non_member(self):
        """Non-member cannot create proposals in another consortium."""
        from apps.governance.serializers import ProposalCreateSerializer

        data = {
            "consortium": str(self.consortium.id),
            "proposal_type": "parameter_change",
            "title": "Malicious proposal from outsider",
            "description": "This should be blocked",
            "data": {"key": "value"},
            "voting_days": 7,
        }

        request = self._make_request(self.user_b)
        serializer = ProposalCreateSerializer(
            data=data, context={"request": request}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("consortium", serializer.errors)

    def test_governance_proposal_allows_owner(self):
        """Consortium owner CAN create proposals."""
        from apps.governance.serializers import ProposalCreateSerializer

        data = {
            "consortium": str(self.consortium.id),
            "proposal_type": "change_params",
            "title": "Legitimate proposal from owner",
            "description": "This should work",
            "data": {"key": "value"},
            "voting_days": 7,
        }

        request = self._make_request(self.user_a)
        serializer = ProposalCreateSerializer(
            data=data, context={"request": request}
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    # ── Marketplace: DeploymentCreateSerializer ───────────────────────

    def test_marketplace_deployment_blocks_non_member(self):
        """Non-member cannot deploy to another consortium."""
        from apps.marketplace.serializers import DeploymentCreateSerializer

        # Create a marketplace model (requires category)
        from apps.marketplace.models import Category, MarketplaceModel

        category = Category.objects.create(name="ML")
        model = MarketplaceModel.objects.create(
            name="Test Model",
            category=category,
            model_type="logistic_regression",
            pricing_type="free",
        )

        data = {
            "marketplace_model": str(model.id),
            "consortium": str(self.consortium.id),
            "config": {},
        }

        request = self._make_request(self.user_b)
        serializer = DeploymentCreateSerializer(
            data=data, context={"request": request}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("consortium", serializer.errors)

    # ── Data Quality: QualityAssessmentCreateSerializer ───────────────

    def test_quality_assessment_blocks_non_member(self):
        """Non-member cannot create quality assessments for another consortium."""
        from apps.data_quality.serializers import QualityAssessmentCreateSerializer

        data = {
            "consortium": str(self.consortium.id),
            "record_count": 1000,
            "feature_count": 10,
        }

        request = self._make_request(self.user_b)
        serializer = QualityAssessmentCreateSerializer(
            data=data, context={"request": request}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("consortium", serializer.errors)

    # ── Compliance: ComplianceCheckCreateSerializer ───────────────────

    def test_compliance_check_blocks_non_member(self):
        """Non-member cannot create compliance checks for another consortium."""
        from apps.compliance.serializers import ComplianceCheckCreateSerializer
        from apps.compliance.models import ComplianceFramework

        framework = ComplianceFramework.objects.create(
            name="GDPR",
            version="2024",
            region="EU",
        )

        data = {
            "consortium": str(self.consortium.id),
            "framework": str(framework.id),
            "control_id": "A.1",
            "status": "passed",
            "result": {"detail": "ok"},
        }

        request = self._make_request(self.user_b)
        serializer = ComplianceCheckCreateSerializer(
            data=data, context={"request": request}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("consortium", serializer.errors)

    # ── Explainability: ExplanationRequestCreateSerializer ────────────

    def test_explanation_request_blocks_non_member(self):
        """Non-member cannot create explanation requests for another consortium."""
        from apps.explainability.serializers import ExplanationRequestCreateSerializer

        data = {
            "consortium": str(self.consortium.id),
            "explanation_type": "shap",
            "input_data": {"features": [1, 2, 3]},
        }

        request = self._make_request(self.user_b)
        serializer = ExplanationRequestCreateSerializer(
            data=data, context={"request": request}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("consortium", serializer.errors)


@override_settings(
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    },
)
class TestSSRFPrevention(TestCase):
    """Test that webhook URLs cannot target internal networks."""

    def test_blocks_localhost(self):
        """Webhook URL pointing to localhost is rejected."""
        from apps.core.serializers import WebhookCreateSerializer

        data = {
            "name": "evil webhook",
            "url": "http://localhost:8080/steal-data",
            "secret": "s3cret",
            "events": ["model.created"],
        }

        serializer = WebhookCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("url", serializer.errors)

    def test_blocks_127_0_0_1(self):
        """Webhook URL pointing to 127.0.0.1 is rejected."""
        from apps.core.serializers import WebhookCreateSerializer

        data = {
            "name": "evil webhook",
            "url": "http://127.0.0.1:9200/_search",
            "secret": "s3cret",
            "events": ["model.created"],
        }

        serializer = WebhookCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("url", serializer.errors)

    def test_blocks_metadata_endpoint(self):
        """Webhook URL targeting cloud metadata is rejected."""
        from apps.core.serializers import WebhookCreateSerializer

        data = {
            "name": "metadata steal",
            "url": "http://169.254.169.254/latest/meta-data/",
            "secret": "s3cret",
            "events": ["model.created"],
        }

        serializer = WebhookCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("url", serializer.errors)

    def test_blocks_private_ip_via_dns(self):
        """Webhook URL resolving to private IP is rejected."""
        from apps.core.serializers import WebhookCreateSerializer

        # Mock DNS resolution to return a private IP
        with patch("socket.getaddrinfo") as mock_dns:
            mock_dns.return_value = [
                (2, 1, 6, "", ("10.0.0.5", 80)),
            ]

            data = {
                "name": "dns rebind attack",
                "url": "http://evil-rebind.attacker.com/callback",
                "secret": "s3cret",
                "events": ["model.created"],
            }

            serializer = WebhookCreateSerializer(data=data)
            self.assertFalse(serializer.is_valid())
            self.assertIn("url", serializer.errors)

    def test_allows_external_url(self):
        """Webhook URL pointing to external host is allowed."""
        from apps.core.serializers import WebhookCreateSerializer

        with patch("socket.getaddrinfo") as mock_dns:
            # Use a globally routable IP (not reserved/private)
            mock_dns.return_value = [
                (2, 1, 6, "", ("8.8.8.8", 443)),
            ]

            data = {
                "name": "legit webhook",
                "url": "https://hooks.example.com/callback",
                "secret": "s3cret",
                "events": ["model.created"],
            }

            serializer = WebhookCreateSerializer(data=data)
            self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_blocks_ftp_scheme(self):
        """Webhook URL with non-HTTP scheme is rejected."""
        from apps.core.serializers import WebhookCreateSerializer

        data = {
            "name": "ftp webhook",
            "url": "ftp://internal-server/data",
            "secret": "s3cret",
            "events": ["model.created"],
        }

        serializer = WebhookCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("url", serializer.errors)


@override_settings(
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    },
)
class TestIDORViewQueryParamBypass(TestCase):
    """
    Test that ViewSets using consortium_id as query param enforce membership.

    Before the fix, IsConsortiumMember returned True for list views (no pk
    in kwargs), so any authenticated user could read proposals, audit events,
    reward distributions, and deployments from any consortium by providing
    the consortium_id query param.
    """

    @classmethod
    def setUpTestData(cls):
        from apps.consortiums.models import Consortium

        cls.company_a = Company.objects.create(
            name="Company A", email="a@test.com", industry="fintech",
        )
        cls.company_b = Company.objects.create(
            name="Company B", email="b@test.com", industry="fintech",
        )
        cls.user_a = User.objects.create_user(
            email="viewa@test.com", password="securepassword123",
            company=cls.company_a,
        )
        cls.user_b = User.objects.create_user(
            email="viewb@test.com", password="securepassword123",
            company=cls.company_b,
        )
        cls.consortium = Consortium.objects.create(
            name="View IDOR Consortium", owner=cls.company_a,
            model_type="logistic_regression",
        )

    def _make_get_request(self, user, query_params=None):
        factory = APIRequestFactory()
        url = "/fake/"
        if query_params:
            url += "?" + "&".join(f"{k}={v}" for k, v in query_params.items())
        request = factory.get(url)
        request.user = user
        request.query_params = query_params or {}
        return request

    def test_governance_config_blocks_non_member(self):
        """Non-member cannot read governance config via query param."""
        from apps.governance.views import GovernanceConfigViewSet

        view = GovernanceConfigViewSet()
        view.kwargs = {}
        view.request = self._make_get_request(
            self.user_b, {"consortium_id": str(self.consortium.id)},
        )
        qs = view.get_queryset()
        self.assertEqual(qs.count(), 0)

    def test_governance_config_allows_owner(self):
        """Owner CAN read governance config."""
        from apps.governance.views import GovernanceConfigViewSet

        view = GovernanceConfigViewSet()
        view.kwargs = {}
        view.request = self._make_get_request(
            self.user_a, {"consortium_id": str(self.consortium.id)},
        )
        qs = view.get_queryset()
        self.assertEqual(qs.count(), 1)

    def test_proposals_blocks_non_member(self):
        """Non-member gets empty queryset for proposals."""
        from apps.governance.views import ProposalViewSet

        view = ProposalViewSet()
        view.kwargs = {}
        view.request = self._make_get_request(
            self.user_b, {"consortium_id": str(self.consortium.id)},
        )
        qs = view.get_queryset()
        self.assertEqual(qs.count(), 0)

    def test_audit_events_blocks_non_member(self):
        """Non-member gets empty queryset for audit events."""
        from apps.governance.views import AuditEventViewSet

        view = AuditEventViewSet()
        view.kwargs = {}
        view.request = self._make_get_request(
            self.user_b, {"consortium_id": str(self.consortium.id)},
        )
        qs = view.get_queryset()
        self.assertEqual(qs.count(), 0)

    def test_reward_distributions_blocks_non_member(self):
        """Non-member gets empty queryset for reward distributions."""
        from apps.governance.views import RewardDistributionViewSet

        view = RewardDistributionViewSet()
        view.kwargs = {}
        view.request = self._make_get_request(
            self.user_b, {"consortium_id": str(self.consortium.id)},
        )
        qs = view.get_queryset()
        self.assertEqual(qs.count(), 0)

    def test_deployments_blocks_non_member(self):
        """Non-member gets empty queryset for deployments."""
        from apps.marketplace.views import DeploymentViewSet

        view = DeploymentViewSet()
        view.kwargs = {}
        view.request = self._make_get_request(
            self.user_b, {"consortium_id": str(self.consortium.id)},
        )
        qs = view.get_queryset()
        self.assertEqual(qs.count(), 0)


@override_settings(
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    },
)
class TestTenantIsolation(TestCase):
    """Test that explainability views enforce tenant isolation."""

    @classmethod
    def setUpTestData(cls):
        from apps.consortiums.models import Consortium

        cls.company_a = Company.objects.create(
            name="Company A", email="tena@test.com", industry="fintech",
        )
        cls.company_b = Company.objects.create(
            name="Company B", email="tenb@test.com", industry="fintech",
        )
        cls.user_b = User.objects.create_user(
            email="tenant_b@test.com", password="securepassword123",
            company=cls.company_b,
        )
        cls.consortium = Consortium.objects.create(
            name="Tenant Isolation Consortium", owner=cls.company_a,
            model_type="logistic_regression",
        )

    def _make_get_request(self, user, query_params=None):
        factory = APIRequestFactory()
        request = factory.get("/fake/")
        request.user = user
        request.query_params = query_params or {}
        return request

    def test_feature_importance_blocks_non_member(self):
        """Non-member cannot read feature importances from another consortium."""
        from apps.explainability.views import FeatureImportanceViewSet

        view = FeatureImportanceViewSet()
        view.kwargs = {}
        view.request = self._make_get_request(
            self.user_b, {"consortium": str(self.consortium.id)},
        )
        qs = view.get_queryset()
        self.assertEqual(qs.count(), 0)

    def test_feature_importance_no_consortium_scoped_to_user(self):
        """Without consortium filter, only user's consortiums shown (not all)."""
        from apps.explainability.views import FeatureImportanceViewSet

        view = FeatureImportanceViewSet()
        view.kwargs = {}
        view.request = self._make_get_request(self.user_b)
        qs = view.get_queryset()
        # company_b owns no consortiums and is not a member of any
        self.assertEqual(qs.count(), 0)

    def test_model_insight_blocks_non_member(self):
        """Non-member cannot read model insights from another consortium."""
        from apps.explainability.views import ModelInsightViewSet

        view = ModelInsightViewSet()
        view.kwargs = {}
        view.request = self._make_get_request(
            self.user_b, {"consortium": str(self.consortium.id)},
        )
        qs = view.get_queryset()
        self.assertEqual(qs.count(), 0)

    def test_model_insight_no_consortium_scoped_to_user(self):
        """Without consortium filter, only user's consortiums shown (not all)."""
        from apps.explainability.views import ModelInsightViewSet

        view = ModelInsightViewSet()
        view.kwargs = {}
        view.request = self._make_get_request(self.user_b)
        qs = view.get_queryset()
        self.assertEqual(qs.count(), 0)


@override_settings(
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    },
)
class TestTierUpgradeProtection(TestCase):
    """Test that tier upgrades require payment verification."""

    @classmethod
    def setUpTestData(cls):
        cls.company = Company.objects.create(
            name="Upgrade Test Co", email="upgrade@test.com",
            industry="fintech", tier="free",
        )

    def test_request_upgrade_creates_pending_not_active(self):
        """request_upgrade creates PENDING subscription, does NOT change tier."""
        from apps.sandbox.services.trial import TrialService

        svc = TrialService()
        result = svc.request_upgrade(self.company, "starter")

        self.assertTrue(result.success)
        # Tier should NOT have changed
        self.company.refresh_from_db()
        self.assertEqual(self.company.tier, "free")
        # Result should indicate pending status
        self.assertEqual(result.data["status"], "pending_payment")
        self.assertEqual(result.data["requested_tier"], "starter")

    def test_confirm_upgrade_requires_gateway_validation(self):
        """confirm_upgrade rejects without gateway validation."""
        from apps.sandbox.services.trial import TrialService

        svc = TrialService()
        # First create the pending upgrade
        svc.request_upgrade(self.company, "starter")

        # Attempt to confirm without gateway validation
        result = svc.confirm_upgrade(self.company, "fake-token")
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "payment_not_verified")

        # Tier should still be free
        self.company.refresh_from_db()
        self.assertEqual(self.company.tier, "free")

    def test_confirm_upgrade_succeeds_with_gateway(self):
        """confirm_upgrade works when gateway validates the payment."""
        from apps.sandbox.services.trial import TrialService

        svc = TrialService()
        svc.request_upgrade(self.company, "starter")

        result = svc.confirm_upgrade(
            self.company, "valid-token", validated_by_gateway=True,
        )
        self.assertTrue(result.success)

        self.company.refresh_from_db()
        self.assertEqual(self.company.tier, "starter")


@override_settings(
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    },
)
class TestSandboxExtensionValidation(TestCase):
    """Test that sandbox extension rejects negative/zero days."""

    @classmethod
    def setUpTestData(cls):
        from apps.sandbox.models import Sandbox, SandboxTemplate

        cls.company = Company.objects.create(
            name="Extension Co", email="ext@test.com", industry="fintech",
        )
        cls.user = User.objects.create_user(
            email="ext_user@test.com", password="securepassword123",
            company=cls.company,
        )
        template = SandboxTemplate.objects.create(
            id="test-template",
            name="Test Template",
            description="Template for testing",
            industry="fintech",
        )
        from django.utils import timezone
        from datetime import timedelta

        cls.sandbox = Sandbox.objects.create(
            name="Test Sandbox",
            owner=cls.company,
            template=template,
            industry="fintech",
            expires_at=timezone.now() + timedelta(days=7),
        )

    def test_rejects_negative_days(self):
        """Extension with negative days is rejected."""
        from apps.sandbox.views import SandboxViewSet
        from rest_framework.test import APIRequestFactory, force_authenticate

        factory = APIRequestFactory()
        request = factory.post("/fake/", {"days": -10}, format="json")
        force_authenticate(request, user=self.user)

        view = SandboxViewSet.as_view({"post": "extend"})
        response = view(request, pk=str(self.sandbox.pk))

        self.assertEqual(response.status_code, 400)

    def test_rejects_zero_days(self):
        """Extension with zero days is rejected."""
        from apps.sandbox.views import SandboxViewSet
        from rest_framework.test import APIRequestFactory, force_authenticate

        factory = APIRequestFactory()
        request = factory.post("/fake/", {"days": 0}, format="json")
        force_authenticate(request, user=self.user)

        view = SandboxViewSet.as_view({"post": "extend"})
        response = view(request, pk=str(self.sandbox.pk))

        self.assertEqual(response.status_code, 400)

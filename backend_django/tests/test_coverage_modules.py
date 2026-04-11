"""
Tests for modules with <70% coverage.

Target modules:
  - core/cache.py (56% → ~90%)
  - core/services/audit.py (58% → ~90%)
  - core/validators/json_schemas.py (61% → ~90%)
  - core/permissions.py (63% → ~90%)
  - blockchain/services.py (67% → ~80%)
  - consortiums/services/consortium.py (69% → ~90%)
"""

import time
from unittest.mock import MagicMock, Mock, patch

import pytest
from django.core.exceptions import ValidationError
from django.test import RequestFactory
from rest_framework.test import APIRequestFactory

from apps.core.models import Company

pytestmark = pytest.mark.django_db


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
def company(db):
    return Company.objects.create(name="TestCo", email="test@testco.com", industry="technology")


@pytest.fixture
def other_company(db):
    return Company.objects.create(name="OtherCo", email="other@otherco.com", industry="finance")


@pytest.fixture
def user(company):
    from django.contrib.auth import get_user_model

    return get_user_model().objects.create_user(
        email="u@testco.com", password="pass1234", company=company
    )


@pytest.fixture
def other_user(other_company):
    from django.contrib.auth import get_user_model

    return get_user_model().objects.create_user(
        email="u@otherco.com", password="pass1234", company=other_company
    )


@pytest.fixture
def no_company_user(db):
    from django.contrib.auth import get_user_model

    return get_user_model().objects.create_user(
        email="nocompany@t.com", password="pass1234", company=None
    )


@pytest.fixture
def consortium(company):
    from apps.consortiums.models import Consortium

    return Consortium.objects.create(
        name="TestConsortium", owner=company, status="active"
    )


@pytest.fixture
def membership(company, consortium):
    from apps.consortiums.models import ConsortiumMember

    return ConsortiumMember.objects.create(
        company=company,
        consortium=consortium,
        role=ConsortiumMember.Role.OWNER,
        status=ConsortiumMember.Status.ACTIVE,
    )


# ══════════════════════════════════════════════════════════════════════
# CORE/CACHE.PY
# ══════════════════════════════════════════════════════════════════════


class TestLRUMemoryCache:
    def test_get_set(self):
        from apps.core.cache import LRUMemoryCache

        cache = LRUMemoryCache(max_size=10)
        cache.set("k1", "v1", timeout=60)
        assert cache.get("k1") == "v1"

    def test_get_missing(self):
        from apps.core.cache import LRUMemoryCache

        cache = LRUMemoryCache()
        assert cache.get("missing") is None
        assert cache.get("missing", "default") == "default"

    def test_get_expired(self):
        from apps.core.cache import LRUMemoryCache

        cache = LRUMemoryCache()
        cache.set("k", "v", timeout=1)
        # Manually expire
        cache._cache["k"] = ("v", time.time() - 1)
        assert cache.get("k") is None

    def test_set_eviction(self):
        from apps.core.cache import LRUMemoryCache

        cache = LRUMemoryCache(max_size=2)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        assert cache.get("a") is None  # Evicted
        assert cache.get("b") == 2
        assert cache.get("c") == 3

    def test_set_no_timeout(self):
        from apps.core.cache import LRUMemoryCache

        cache = LRUMemoryCache()
        cache.set("k", "v", timeout=0)
        assert cache.get("k") == "v"  # No expiration

    def test_delete(self):
        from apps.core.cache import LRUMemoryCache

        cache = LRUMemoryCache()
        cache.set("k", "v")
        assert cache.delete("k") is True
        assert cache.delete("k") is False
        assert cache.get("k") is None

    def test_clear(self):
        from apps.core.cache import LRUMemoryCache

        cache = LRUMemoryCache()
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert len(cache) == 0

    def test_get_many(self):
        from apps.core.cache import LRUMemoryCache

        cache = LRUMemoryCache()
        cache.set("a", 1)
        cache.set("b", 2)
        result = cache.get_many(["a", "b", "c"])
        assert result == {"a": 1, "b": 2}

    def test_set_many(self):
        from apps.core.cache import LRUMemoryCache

        cache = LRUMemoryCache()
        cache.set_many({"a": 1, "b": 2}, timeout=60)
        assert cache.get("a") == 1
        assert cache.get("b") == 2

    def test_delete_many(self):
        from apps.core.cache import LRUMemoryCache

        cache = LRUMemoryCache()
        cache.set("a", 1)
        cache.set("b", 2)
        cache.delete_many(["a", "b"])
        assert cache.get("a") is None
        assert cache.get("b") is None

    def test_len(self):
        from apps.core.cache import LRUMemoryCache

        cache = LRUMemoryCache()
        assert len(cache) == 0
        cache.set("a", 1)
        assert len(cache) == 1


class TestResilientCache:
    def _make_cache(self, primary_fails=False, circuit_open=False):
        from apps.core.cache import LRUMemoryCache, ResilientCache

        primary = MagicMock()
        if primary_fails:
            primary.get.side_effect = ConnectionError("redis down")
            primary.set.side_effect = ConnectionError("redis down")
            primary.delete.side_effect = ConnectionError("redis down")
            primary.get_many.side_effect = ConnectionError("redis down")
            primary.set_many.side_effect = ConnectionError("redis down")
            primary.delete_many.side_effect = ConnectionError("redis down")
            primary.clear.side_effect = ConnectionError("redis down")

        fallback = LRUMemoryCache()

        # Mock circuit breaker to avoid complex state management
        circuit = MagicMock()
        circuit.is_open = circuit_open
        circuit.state.value = "open" if circuit_open else "closed"
        circuit.get_stats.return_value = {}
        # Make context manager work: __enter__ returns None, __exit__ returns False
        circuit.__enter__ = Mock(return_value=None)
        circuit.__exit__ = Mock(return_value=False)

        return ResilientCache(primary_cache=primary, fallback_cache=fallback, circuit=circuit)

    def test_get_primary_success(self):
        cache = self._make_cache()
        cache._primary.get.return_value = "value"
        result = cache.get("key")
        assert result == "value"
        assert not cache.is_using_fallback

    def test_get_primary_fails(self):
        cache = self._make_cache(primary_fails=True)
        cache._fallback.set("key", "fallback_val")
        result = cache.get("key")
        assert result == "fallback_val"
        assert cache.is_using_fallback

    def test_set_primary_success(self):
        cache = self._make_cache()
        result = cache.set("key", "value", timeout=60)
        assert result is True

    def test_set_primary_fails(self):
        cache = self._make_cache(primary_fails=True)
        result = cache.set("key", "value", timeout=60)
        assert result is True  # Fallback succeeds
        assert cache._fallback.get("key") == "value"

    def test_set_default_timeout(self):
        cache = self._make_cache()
        result = cache.set("key", "value")  # DEFAULT_TIMEOUT sentinel
        assert result is True

    def test_delete_primary_success(self):
        cache = self._make_cache()
        result = cache.delete("key")
        assert result is True  # Primary called via circuit

    def test_delete_primary_fails(self):
        cache = self._make_cache(primary_fails=True)
        cache._fallback.set("key", "value")
        result = cache.delete("key")
        assert result is True  # Fallback delete succeeds

    def test_get_many_primary_success(self):
        cache = self._make_cache()
        cache._primary.get_many.return_value = {"a": 1}
        result = cache.get_many(["a", "b"])
        assert result == {"a": 1}

    def test_get_many_primary_fails(self):
        cache = self._make_cache(primary_fails=True)
        cache._fallback.set("a", 1)
        result = cache.get_many(["a", "b"])
        assert result == {"a": 1}

    def test_set_many_primary_success(self):
        cache = self._make_cache()
        cache._primary.set_many.return_value = []
        result = cache.set_many({"a": 1, "b": 2}, timeout=60)
        assert result == []

    def test_set_many_primary_fails(self):
        cache = self._make_cache(primary_fails=True)
        result = cache.set_many({"a": 1, "b": 2}, timeout=60)
        assert set(result) == {"a", "b"}

    def test_delete_many_primary_success(self):
        cache = self._make_cache()
        cache.delete_many(["a", "b"])
        cache._primary.delete_many.assert_called_once()

    def test_delete_many_primary_fails(self):
        cache = self._make_cache(primary_fails=True)
        cache._fallback.set("a", 1)
        cache.delete_many(["a"])
        assert cache._fallback.get("a") is None

    def test_clear_primary_success(self):
        cache = self._make_cache()
        cache.clear()
        cache._primary.clear.assert_called_once()

    def test_clear_primary_fails(self):
        cache = self._make_cache(primary_fails=True)
        cache._fallback.set("a", 1)
        cache.clear()
        assert len(cache._fallback) == 0

    def test_get_or_set_cached(self):
        cache = self._make_cache()
        cache._primary.get.return_value = "cached"
        result = cache.get_or_set("key", "default")
        assert result == "cached"

    def test_get_or_set_not_cached_value(self):
        cache = self._make_cache()
        cache._primary.get.return_value = None
        result = cache.get_or_set("key", "default_value", timeout=60)
        assert result == "default_value"

    def test_get_or_set_not_cached_callable(self):
        cache = self._make_cache()
        cache._primary.get.return_value = None
        result = cache.get_or_set("key", lambda: "computed", timeout=60)
        assert result == "computed"

    def test_get_stats(self):
        cache = self._make_cache()
        stats = cache.get_stats()
        assert "using_fallback" in stats
        assert "circuit_state" in stats
        assert "fallback_size" in stats

    def test_circuit_open_skips_primary(self):
        cache = self._make_cache(circuit_open=True)
        cache._fallback.set("key", "fallback")
        result = cache.get("key")
        assert result == "fallback"
        cache._primary.get.assert_not_called()


class TestCachedDecorator:
    def test_caches_result(self):
        from apps.core.cache import LRUMemoryCache, ResilientCache, cached

        # Patch resilient_cache
        fallback = LRUMemoryCache()
        test_cache = ResilientCache(
            primary_cache=MagicMock(get=MagicMock(return_value=None), set=MagicMock()),
            fallback_cache=fallback,
        )

        with patch("apps.core.cache.resilient_cache", test_cache):

            @cached("test_prefix", timeout=60)
            def my_func(x):
                return x * 2

            result = my_func(5)
            assert result == 10

    def test_returns_cached_value(self):
        from apps.core.cache import LRUMemoryCache, ResilientCache, cached

        primary = MagicMock()
        primary.get.return_value = "cached_result"
        test_cache = ResilientCache(primary_cache=primary, fallback_cache=LRUMemoryCache())

        with patch("apps.core.cache.resilient_cache", test_cache):

            @cached("prefix", timeout=60)
            def my_func(x):
                return x * 2

            result = my_func(5)
            assert result == "cached_result"

    def test_custom_key_func(self):
        from apps.core.cache import LRUMemoryCache, ResilientCache, cached

        primary = MagicMock()
        primary.get.return_value = None
        test_cache = ResilientCache(primary_cache=primary, fallback_cache=LRUMemoryCache())

        with patch("apps.core.cache.resilient_cache", test_cache):

            @cached("prefix", timeout=60, key_func=lambda x: f"custom:{x}")
            def my_func(x):
                return x * 2

            result = my_func(5)
            assert result == 10

    def test_no_args(self):
        from apps.core.cache import LRUMemoryCache, ResilientCache, cached

        primary = MagicMock()
        primary.get.return_value = None
        test_cache = ResilientCache(primary_cache=primary, fallback_cache=LRUMemoryCache())

        with patch("apps.core.cache.resilient_cache", test_cache):

            @cached("prefix", timeout=60)
            def my_func():
                return 42

            result = my_func()
            assert result == 42

    def test_invalidate(self):
        from apps.core.cache import LRUMemoryCache, ResilientCache, cached

        primary = MagicMock()
        primary.get.return_value = None
        test_cache = ResilientCache(primary_cache=primary, fallback_cache=LRUMemoryCache())

        with patch("apps.core.cache.resilient_cache", test_cache):

            @cached("prefix", timeout=60)
            def my_func(x):
                return x * 2

            my_func(5)
            my_func.invalidate(5)


# ══════════════════════════════════════════════════════════════════════
# CORE/SERVICES/AUDIT.PY
# ══════════════════════════════════════════════════════════════════════


class TestAuditService:
    def _make_context(self, request):
        from apps.core.services.base import ServiceContext

        return ServiceContext.from_request(request)

    def test_log_with_request(self, user):
        from apps.core.services.audit import AuditService

        factory = RequestFactory()
        request = factory.get("/test/")
        request.user = user
        request.META["REMOTE_ADDR"] = "127.0.0.1"

        ctx = self._make_context(request)
        svc = AuditService(ctx)
        svc.log(action="test_action", resource_type="test", resource_id="123")

        from apps.core.models import AuditLog

        assert AuditLog.objects.filter(action="test_action").exists()

    def test_log_without_request(self):
        from apps.core.services.audit import AuditService

        svc = AuditService(None)
        # Should not raise, just skip logging
        svc.log(action="test_action", resource_type="test", resource_id="123")

    def test_log_with_extra_data(self, user):
        from apps.core.services.audit import AuditService

        factory = RequestFactory()
        request = factory.get("/test/")
        request.user = user
        request.META["REMOTE_ADDR"] = "127.0.0.1"

        ctx = self._make_context(request)
        svc = AuditService(ctx)
        svc.log(
            action="test_extra",
            resource_type="test",
            resource_id="456",
            extra_data={"key": "value"},
        )

        from apps.core.models import AuditLog

        log = AuditLog.objects.get(action="test_extra")
        assert log.resource_id == "456"

    def test_log_from_request(self, user):
        from apps.core.services.audit import AuditService

        factory = RequestFactory()
        request = factory.get("/test/")
        request.user = user
        request.META["REMOTE_ADDR"] = "127.0.0.1"

        AuditService.log_from_request(
            request,
            action="class_method_test",
            resource_type="test",
            resource_id="789",
        )

        from apps.core.models import AuditLog

        assert AuditLog.objects.filter(action="class_method_test").exists()


# ══════════════════════════════════════════════════════════════════════
# CORE/VALIDATORS/JSON_SCHEMAS.PY
# ══════════════════════════════════════════════════════════════════════


class TestJSONSchemaValidator:
    def test_valid_proposal_add_member(self):
        from apps.core.validators.json_schemas import JSONSchemaValidator, PROPOSAL_DATA_SCHEMAS

        validator = JSONSchemaValidator(PROPOSAL_DATA_SCHEMAS["add_member"])
        # Should not raise
        validator({"company_email": "test@example.com", "role": "contributor"})

    def test_invalid_proposal_missing_required(self):
        from apps.core.validators.json_schemas import JSONSchemaValidator, PROPOSAL_DATA_SCHEMAS

        validator = JSONSchemaValidator(PROPOSAL_DATA_SCHEMAS["add_member"])
        with pytest.raises(ValidationError):
            validator({"role": "contributor"})  # Missing company_email

    def test_empty_value_not_allowed(self):
        from apps.core.validators.json_schemas import JSONSchemaValidator

        validator = JSONSchemaValidator({"type": "object"})
        with pytest.raises(ValidationError, match="cannot be empty"):
            validator({})

    def test_empty_value_allowed(self):
        from apps.core.validators.json_schemas import JSONSchemaValidator

        validator = JSONSchemaValidator({"type": "object"}, allow_empty=True)
        validator({})  # Should not raise

    def test_quality_rule_condition(self):
        from apps.core.validators.json_schemas import JSONSchemaValidator, QUALITY_RULE_CONDITION_SCHEMA

        validator = JSONSchemaValidator(QUALITY_RULE_CONDITION_SCHEMA)
        validator({"operator": ">=", "value": 0.5})

    def test_quality_rule_condition_between(self):
        from apps.core.validators.json_schemas import JSONSchemaValidator, QUALITY_RULE_CONDITION_SCHEMA

        validator = JSONSchemaValidator(QUALITY_RULE_CONDITION_SCHEMA)
        validator({"operator": "between", "min_value": 0, "max_value": 1})

    def test_quality_rule_condition_in(self):
        from apps.core.validators.json_schemas import JSONSchemaValidator, QUALITY_RULE_CONDITION_SCHEMA

        validator = JSONSchemaValidator(QUALITY_RULE_CONDITION_SCHEMA)
        validator({"operator": "in", "value": [1, 2, 3]})

    def test_basic_validate_object(self):
        from apps.core.validators.json_schemas import JSONSchemaValidator

        validator = JSONSchemaValidator({"type": "object", "required": ["name"]})
        # Force basic validation by clearing compiled validator
        validator._validator = None
        with pytest.raises(ValidationError, match="Missing required field"):
            validator({"other": "data"})

    def test_basic_validate_array(self):
        from apps.core.validators.json_schemas import JSONSchemaValidator

        validator = JSONSchemaValidator({"type": "array"})
        validator._validator = None
        validator([1, 2, 3])  # Should not raise

    def test_basic_validate_wrong_type_object(self):
        from apps.core.validators.json_schemas import JSONSchemaValidator

        validator = JSONSchemaValidator({"type": "object"})
        validator._validator = None
        with pytest.raises(ValidationError, match="Expected object"):
            validator("not an object")

    def test_basic_validate_wrong_type_array(self):
        from apps.core.validators.json_schemas import JSONSchemaValidator

        validator = JSONSchemaValidator({"type": "array"})
        validator._validator = None
        with pytest.raises(ValidationError, match="Expected array"):
            validator("not an array")

    def test_eq(self):
        from apps.core.validators.json_schemas import JSONSchemaValidator

        v1 = JSONSchemaValidator({"type": "object"})
        v2 = JSONSchemaValidator({"type": "object"})
        v3 = JSONSchemaValidator({"type": "array"})
        assert v1 == v2
        assert v1 != v3
        assert v1 != "not a validator"

    def test_hash(self):
        from apps.core.validators.json_schemas import JSONSchemaValidator

        v1 = JSONSchemaValidator({"type": "object"})
        v2 = JSONSchemaValidator({"type": "object"})
        assert hash(v1) == hash(v2)

    def test_reward_distribution_schema(self):
        from apps.core.validators.json_schemas import JSONSchemaValidator, REWARD_DISTRIBUTION_SCHEMA

        validator = JSONSchemaValidator(REWARD_DISTRIBUTION_SCHEMA)
        validator([
            {"company_id": "550e8400-e29b-41d4-a716-446655440000", "amount": 100.0},
        ])

    def test_validate_json_schema_function(self):
        from apps.core.validators.json_schemas import validate_json_schema

        validate_json_schema({"company_email": "a@b.com"}, {
            "type": "object",
            "required": ["company_email"],
            "properties": {"company_email": {"type": "string"}},
        })

    def test_get_proposal_validator_known(self):
        from apps.core.validators.json_schemas import get_proposal_validator

        validator = get_proposal_validator("add_member")
        assert validator is not None

    def test_get_proposal_validator_unknown(self):
        from apps.core.validators.json_schemas import get_proposal_validator

        validator = get_proposal_validator("nonexistent_type")
        assert validator is None


class TestProposalDataField:
    def test_to_internal_value_with_valid_type(self):
        from apps.core.validators.json_schemas import ProposalDataField

        field = ProposalDataField()
        # Simulate serializer parent with initial_data
        parent = Mock()
        parent.initial_data = {"proposal_type": "add_member"}
        field.parent = parent
        field._run_validation = Mock(return_value={"company_email": "a@b.com"})
        # Call directly via the JSON field's method
        result = field.to_internal_value({"company_email": "a@b.com"})
        assert result == {"company_email": "a@b.com"}

    def test_to_internal_value_without_type(self):
        from apps.core.validators.json_schemas import ProposalDataField

        field = ProposalDataField()
        parent = Mock()
        parent.initial_data = {}
        field.parent = parent
        result = field.to_internal_value({"some": "data"})
        assert result == {"some": "data"}

    def test_to_internal_value_invalid_data(self):
        from rest_framework.exceptions import ValidationError as DRFValidationError

        from apps.core.validators.json_schemas import ProposalDataField

        field = ProposalDataField()
        parent = Mock()
        parent.initial_data = {"proposal_type": "add_member"}
        field.parent = parent
        with pytest.raises(DRFValidationError):
            field.to_internal_value({"role": "contributor"})  # Missing company_email


class TestQualityRuleConditionField:
    def test_init_adds_validator(self):
        from apps.core.validators.json_schemas import QualityRuleConditionField

        field = QualityRuleConditionField()
        assert len(field.validators) >= 1


# ══════════════════════════════════════════════════════════════════════
# CORE/PERMISSIONS.PY
# ══════════════════════════════════════════════════════════════════════


class TestPermissions:
    def _make_request(self, user=None):
        request = Mock()
        if user:
            request.user = user
        else:
            request.user = Mock(is_authenticated=False)
        request.data = {}
        request.query_params = {}
        request.method = "GET"
        return request

    def _make_view(self, **kwargs):
        view = Mock(spec=[])  # spec=[] prevents auto-creating attributes
        view.kwargs = kwargs.get("kwargs", {})
        if "required_permissions" in kwargs:
            view.required_permissions = kwargs["required_permissions"]
        return view

    # ── IsCompanyMember ──

    def test_is_company_member_with_company(self, user):
        from apps.core.permissions import IsCompanyMember

        perm = IsCompanyMember()
        request = self._make_request(user)
        assert perm.has_permission(request, self._make_view()) is True

    def test_is_company_member_without_company(self, no_company_user):
        from apps.core.permissions import IsCompanyMember

        perm = IsCompanyMember()
        request = self._make_request(no_company_user)
        assert perm.has_permission(request, self._make_view()) is False

    def test_is_company_member_unauthenticated(self):
        from apps.core.permissions import IsCompanyMember

        perm = IsCompanyMember()
        request = self._make_request()
        assert perm.has_permission(request, self._make_view()) is False

    # ── IsConsortiumMember ──

    def test_is_consortium_member_valid(self, user, consortium, membership):
        from apps.core.permissions import IsConsortiumMember

        perm = IsConsortiumMember()
        request = self._make_request(user)
        view = self._make_view(kwargs={"consortium_id": str(consortium.id)})
        assert perm.has_permission(request, view) is True

    def test_is_consortium_member_not_member(self, other_user, consortium):
        from apps.core.permissions import IsConsortiumMember

        perm = IsConsortiumMember()
        request = self._make_request(other_user)
        view = self._make_view(kwargs={"consortium_id": str(consortium.id)})
        assert perm.has_permission(request, view) is False

    def test_is_consortium_member_no_id(self, user):
        from apps.core.permissions import IsConsortiumMember

        perm = IsConsortiumMember()
        request = self._make_request(user)
        view = self._make_view(kwargs={})
        assert perm.has_permission(request, view) is True  # Defers to view

    def test_is_consortium_member_unauthenticated(self):
        from apps.core.permissions import IsConsortiumMember

        perm = IsConsortiumMember()
        request = self._make_request()
        assert perm.has_permission(request, self._make_view()) is False

    # ── IsConsortiumOwner ──

    def test_is_consortium_owner_valid(self, user, consortium):
        from apps.core.permissions import IsConsortiumOwner

        perm = IsConsortiumOwner()
        request = self._make_request(user)
        view = self._make_view(kwargs={"consortium_id": str(consortium.id)})
        assert perm.has_permission(request, view) is True

    def test_is_consortium_owner_not_owner(self, other_user, consortium):
        from apps.core.permissions import IsConsortiumOwner

        perm = IsConsortiumOwner()
        request = self._make_request(other_user)
        view = self._make_view(kwargs={"consortium_id": str(consortium.id)})
        assert perm.has_permission(request, view) is False

    def test_is_consortium_owner_no_id(self, user):
        from apps.core.permissions import IsConsortiumOwner

        perm = IsConsortiumOwner()
        request = self._make_request(user)
        assert perm.has_permission(request, self._make_view()) is True

    def test_is_consortium_owner_unauthenticated(self):
        from apps.core.permissions import IsConsortiumOwner

        perm = IsConsortiumOwner()
        request = self._make_request()
        assert perm.has_permission(request, self._make_view()) is False

    # ── IsConsortiumAdmin ──

    def test_is_consortium_admin_as_owner(self, user, consortium):
        from apps.core.permissions import IsConsortiumAdmin

        perm = IsConsortiumAdmin()
        request = self._make_request(user)
        view = self._make_view(kwargs={"consortium_id": str(consortium.id)})
        assert perm.has_permission(request, view) is True

    def test_is_consortium_admin_as_admin(self, other_user, consortium, other_company):
        from apps.consortiums.models import ConsortiumMember
        from apps.core.permissions import IsConsortiumAdmin

        ConsortiumMember.objects.create(
            company=other_company,
            consortium=consortium,
            role=ConsortiumMember.Role.ADMIN,
            status=ConsortiumMember.Status.ACTIVE,
        )
        perm = IsConsortiumAdmin()
        request = self._make_request(other_user)
        view = self._make_view(kwargs={"consortium_id": str(consortium.id)})
        assert perm.has_permission(request, view) is True

    def test_is_consortium_admin_not_admin(self, other_user, consortium):
        from apps.core.permissions import IsConsortiumAdmin

        perm = IsConsortiumAdmin()
        request = self._make_request(other_user)
        view = self._make_view(kwargs={"consortium_id": str(consortium.id)})
        assert perm.has_permission(request, view) is False

    def test_is_consortium_admin_unauthenticated(self):
        from apps.core.permissions import IsConsortiumAdmin

        perm = IsConsortiumAdmin()
        request = self._make_request()
        assert perm.has_permission(request, self._make_view()) is False

    def test_is_consortium_admin_no_id(self, user):
        from apps.core.permissions import IsConsortiumAdmin

        perm = IsConsortiumAdmin()
        request = self._make_request(user)
        assert perm.has_permission(request, self._make_view()) is True

    # ── HasAPIKeyPermission ──

    def test_api_key_no_required_perms(self, user):
        from apps.core.permissions import HasAPIKeyPermission

        perm = HasAPIKeyPermission()
        request = self._make_request(user)
        view = self._make_view()
        assert perm.has_permission(request, view) is True

    def test_api_key_valid_perms(self, user):
        from apps.core.permissions import HasAPIKeyPermission

        perm = HasAPIKeyPermission()
        request = self._make_request(user)
        api_key = Mock()
        api_key.has_permission.return_value = True
        request.auth = api_key
        view = self._make_view(required_permissions=["read"])
        assert perm.has_permission(request, view) is True

    def test_api_key_missing_perms(self, user):
        from apps.core.permissions import HasAPIKeyPermission

        perm = HasAPIKeyPermission()
        request = self._make_request(user)
        api_key = Mock()
        api_key.has_permission.return_value = False
        request.auth = api_key
        view = self._make_view(required_permissions=["write"])
        assert perm.has_permission(request, view) is False

    def test_api_key_no_auth(self, user):
        from apps.core.permissions import HasAPIKeyPermission

        perm = HasAPIKeyPermission()
        request = self._make_request(user)
        request.auth = None
        view = self._make_view(required_permissions=["read"])
        assert perm.has_permission(request, view) is False

    # ── IsResourceOwner ──

    def test_resource_owner_via_owner_field(self, user, company):
        from apps.core.permissions import IsResourceOwner

        perm = IsResourceOwner()
        request = self._make_request(user)
        obj = Mock(owner=company)
        assert perm.has_object_permission(request, self._make_view(), obj) is True

    def test_resource_owner_via_company_field(self, user, company):
        from apps.core.permissions import IsResourceOwner

        perm = IsResourceOwner()
        request = self._make_request(user)
        obj = Mock(spec=["company"])
        obj.company = company
        assert perm.has_object_permission(request, self._make_view(), obj) is True

    def test_resource_owner_not_owner(self, user, other_company):
        from apps.core.permissions import IsResourceOwner

        perm = IsResourceOwner()
        request = self._make_request(user)
        obj = Mock(owner=other_company)
        assert perm.has_object_permission(request, self._make_view(), obj) is False

    def test_resource_owner_no_field(self, user):
        from apps.core.permissions import IsResourceOwner

        perm = IsResourceOwner()
        request = self._make_request(user)
        obj = Mock(spec=[])  # No owner or company field
        assert perm.has_object_permission(request, self._make_view(), obj) is False

    def test_resource_owner_unauthenticated(self):
        from apps.core.permissions import IsResourceOwner

        perm = IsResourceOwner()
        request = self._make_request()
        obj = Mock(owner=Mock())
        assert perm.has_object_permission(request, self._make_view(), obj) is False

    # ── ReadOnly ──

    def test_read_only_get(self):
        from apps.core.permissions import ReadOnly

        perm = ReadOnly()
        request = self._make_request()
        request.method = "GET"
        assert perm.has_permission(request, self._make_view()) is True

    def test_read_only_post(self):
        from apps.core.permissions import ReadOnly

        perm = ReadOnly()
        request = self._make_request()
        request.method = "POST"
        assert perm.has_permission(request, self._make_view()) is False

    # ── IsActiveUser ──

    def test_active_user_active(self, user):
        from apps.core.permissions import IsActiveUser

        perm = IsActiveUser()
        request = self._make_request(user)
        assert perm.has_permission(request, self._make_view()) is True

    def test_active_user_unauthenticated(self):
        from apps.core.permissions import IsActiveUser

        perm = IsActiveUser()
        request = self._make_request()
        assert perm.has_permission(request, self._make_view()) is False

    # ── IsVerifiedCompany ──

    def test_verified_company_verified(self, user, company):
        from apps.core.permissions import IsVerifiedCompany

        company.is_verified = True
        company.save()
        perm = IsVerifiedCompany()
        request = self._make_request(user)
        assert perm.has_permission(request, self._make_view()) is True

    def test_verified_company_not_verified(self, user, company):
        from apps.core.permissions import IsVerifiedCompany

        company.is_verified = False
        company.save()
        perm = IsVerifiedCompany()
        request = self._make_request(user)
        assert perm.has_permission(request, self._make_view()) is False

    def test_verified_company_no_company(self, no_company_user):
        from apps.core.permissions import IsVerifiedCompany

        perm = IsVerifiedCompany()
        request = self._make_request(no_company_user)
        assert perm.has_permission(request, self._make_view()) is False

    def test_verified_company_unauthenticated(self):
        from apps.core.permissions import IsVerifiedCompany

        perm = IsVerifiedCompany()
        request = self._make_request()
        assert perm.has_permission(request, self._make_view()) is False


# ══════════════════════════════════════════════════════════════════════
# CONSORTIUMS/SERVICES/CONSORTIUM.PY
# ══════════════════════════════════════════════════════════════════════


class TestConsortiumServiceGetStats:
    def test_get_stats(self, company, consortium, membership):
        from apps.consortiums.models import ContributionProof
        from apps.consortiums.services.consortium import ConsortiumService

        ContributionProof.objects.create(
            company=company,
            consortium=consortium,
            data_hash="hash1",
            record_count=100,
            feature_count=10,
            checksum="chk1",
            verification_status=ContributionProof.VerificationStatus.VERIFIED,
        )

        svc = ConsortiumService()
        result = svc.get_stats(consortium)
        assert result.success
        assert result.data.total_members == 1
        assert result.data.active_members == 1
        assert result.data.total_contributions == 1
        assert result.data.total_records == 100

    def test_get_stats_empty(self, consortium, membership):
        from apps.consortiums.services.consortium import ConsortiumService

        svc = ConsortiumService()
        result = svc.get_stats(consortium)
        assert result.success
        assert result.data.total_contributions == 0
        assert result.data.total_records == 0

    def test_get_stats_with_pending_members(self, company, other_company, consortium, membership):
        from apps.consortiums.models import ConsortiumMember
        from apps.consortiums.services.consortium import ConsortiumService

        ConsortiumMember.objects.create(
            company=other_company,
            consortium=consortium,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.PENDING,
        )

        svc = ConsortiumService()
        result = svc.get_stats(consortium)
        assert result.success
        assert result.data.active_members == 1
        assert result.data.pending_members == 1


class TestConsortiumServiceGetMemberRankings:
    def test_rankings(self, company, other_company, consortium, membership):
        from apps.consortiums.models import ConsortiumMember, ContributionProof
        from apps.consortiums.services.consortium import ConsortiumService

        # Add other company as active member
        ConsortiumMember.objects.create(
            company=other_company,
            consortium=consortium,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )

        # Add contributions
        ContributionProof.objects.create(
            company=company,
            consortium=consortium,
            data_hash="hash1",
            record_count=200,
            feature_count=10,
            checksum="chk1",
            verification_status=ContributionProof.VerificationStatus.VERIFIED,
        )
        ContributionProof.objects.create(
            company=other_company,
            consortium=consortium,
            data_hash="hash2",
            record_count=100,
            feature_count=10,
            checksum="chk2",
            verification_status=ContributionProof.VerificationStatus.VERIFIED,
        )

        svc = ConsortiumService()
        result = svc.get_member_rankings(consortium)
        assert result.success
        assert len(result.data) == 2
        assert result.data[0]["total_records"] == 200  # company first
        assert result.data[1]["total_records"] == 100

    def test_rankings_with_limit(self, company, consortium, membership):
        from apps.consortiums.services.consortium import ConsortiumService

        svc = ConsortiumService()
        result = svc.get_member_rankings(consortium, limit=1)
        assert result.success
        assert len(result.data) <= 1

    def test_rankings_empty(self, consortium, membership):
        from apps.consortiums.services.consortium import ConsortiumService

        svc = ConsortiumService()
        result = svc.get_member_rankings(consortium)
        assert result.success
        assert result.data[0]["total_records"] == 0


# ══════════════════════════════════════════════════════════════════════
# BLOCKCHAIN/SERVICES.PY (additional coverage)
# ══════════════════════════════════════════════════════════════════════


class TestBlockchainServiceConnection:
    def test_is_connected_circuit_open(self):
        from apps.blockchain.services import BlockchainService

        svc = BlockchainService.__new__(BlockchainService)
        svc._web3 = None
        svc._chain_id = None
        svc.network = "arbitrum_sepolia"
        svc._circuit = MagicMock()
        svc._circuit.is_open = True

        assert svc.is_connected() is False

    def test_is_connected_no_web3(self):
        from apps.blockchain.services import BlockchainService

        svc = BlockchainService.__new__(BlockchainService)
        svc._web3 = None
        svc._chain_id = None
        svc.network = "arbitrum_sepolia"
        svc._circuit = MagicMock()
        svc._circuit.is_open = False

        assert svc.is_connected() is False

    def test_is_connected_with_web3(self):
        from apps.blockchain.services import BlockchainService

        svc = BlockchainService.__new__(BlockchainService)
        svc._web3 = MagicMock()
        svc._web3.is_connected.return_value = True
        svc._chain_id = 421614
        svc.network = "arbitrum_sepolia"
        svc._circuit = MagicMock()
        svc._circuit.is_open = False

        assert svc.is_connected() is True

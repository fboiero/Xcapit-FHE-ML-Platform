"""
Tests for the authentication flow: Register, Login, Logout,
ChangePassword, MeView, and APIKeyAuthentication.
"""

import hashlib
import uuid
from datetime import timedelta

import pytest
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.models import APIKey, AuditLog, Company, User


# ── Helpers ──────────────────────────────────────────────────


def _company(**kw):
    defaults = {
        "name": f"Co-{uuid.uuid4().hex[:6]}",
        "email": f"co-{uuid.uuid4().hex[:6]}@example.com",
    }
    defaults.update(kw)
    return Company.objects.create(**defaults)


def _user(company=None, password="StrongPass12345!", **kw):
    defaults = {
        "email": f"u-{uuid.uuid4().hex[:6]}@example.com",
        "first_name": "Test",
        "last_name": "User",
    }
    defaults.update(kw)
    return User.objects.create_user(password=password, company=company, **defaults)


REGISTER_URL = "/api/v2/auth/register/"
LOGIN_URL = "/api/v2/auth/login/"
LOGOUT_URL = "/api/v2/auth/logout/"
CHANGE_PW_URL = "/api/v2/auth/change-password/"
ME_URL = "/api/v2/auth/me/"
CREATE_KEY_URL = "/api/v2/auth/api-keys/create/"


# ══════════════════════════════════════════════════════════════
# TestRegister
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestRegister(TestCase):

    def setUp(self):
        self.client = APIClient()

    def _register_data(self, **overrides):
        data = {
            "email": f"new-{uuid.uuid4().hex[:6]}@example.com",
            "password": "Str0ngP@ssw0rd!",
            "password_confirm": "Str0ngP@ssw0rd!",
            "first_name": "Alice",
            "last_name": "Wonder",
        }
        data.update(overrides)
        return data

    def test_register_success(self):
        data = self._register_data()
        resp = self.client.post(REGISTER_URL, data, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert "tokens" in resp.data
        assert "access" in resp.data["tokens"]
        assert "refresh" in resp.data["tokens"]
        assert resp.data["user"]["email"] == data["email"].lower()

    def test_register_with_company(self):
        data = self._register_data(company_name="Acme Inc", industry="fintech")
        resp = self.client.post(REGISTER_URL, data, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert "trial" in resp.data
        assert resp.data["trial"]["active"] is True
        assert resp.data["trial"]["tier"] == "free"

    def test_register_without_company(self):
        data = self._register_data()
        resp = self.client.post(REGISTER_URL, data, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert "trial" not in resp.data

    def test_register_creates_audit_log(self):
        data = self._register_data()
        self.client.post(REGISTER_URL, data, format="json")
        assert AuditLog.objects.filter(action="user_registered").exists()

    def test_register_duplicate_email(self):
        email = f"dup-{uuid.uuid4().hex[:6]}@example.com"
        _user(email=email)
        data = self._register_data(email=email)
        resp = self.client.post(REGISTER_URL, data, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_password_mismatch(self):
        data = self._register_data(password_confirm="Different1234!")
        resp = self.client.post(REGISTER_URL, data, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_too_short_password_rejected(self):
        """min_length=12 on the serializer field rejects short passwords."""
        data = self._register_data(
            password="Short1!abc",
            password_confirm="Short1!abc",
        )
        resp = self.client.post(REGISTER_URL, data, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_short_password(self):
        data = self._register_data(
            password="Ab1!",
            password_confirm="Ab1!",
        )
        resp = self.client.post(REGISTER_URL, data, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_email_normalized(self):
        data = self._register_data(email="TEST@EXAMPLE.COM")
        resp = self.client.post(REGISTER_URL, data, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["user"]["email"] == "test@example.com"

    def test_register_auto_trial_start(self):
        """Registration with company auto-starts a 14-day trial."""
        data = self._register_data(company_name="TrialCo")
        resp = self.client.post(REGISTER_URL, data, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["trial"]["days_remaining"] >= 13

    def test_register_missing_first_name(self):
        data = self._register_data()
        del data["first_name"]
        resp = self.client.post(REGISTER_URL, data, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


# ══════════════════════════════════════════════════════════════
# TestLogin
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestLogin(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.password = "SecureL0gin!Pass"
        self.user = _user(password=self.password)

    def test_login_success(self):
        resp = self.client.post(
            LOGIN_URL,
            {"email": self.user.email, "password": self.password},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert "tokens" in resp.data
        assert resp.data["user"]["email"] == self.user.email

    def test_login_updates_last_login(self):
        assert self.user.last_login is None
        self.client.post(
            LOGIN_URL,
            {"email": self.user.email, "password": self.password},
            format="json",
        )
        self.user.refresh_from_db()
        assert self.user.last_login is not None

    def test_login_creates_audit_log(self):
        self.client.post(
            LOGIN_URL,
            {"email": self.user.email, "password": self.password},
            format="json",
        )
        assert AuditLog.objects.filter(action="user_logged_in").exists()

    def test_login_wrong_password(self):
        resp = self.client.post(
            LOGIN_URL,
            {"email": self.user.email, "password": "WrongPassword1!"},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_wrong_email(self):
        resp = self.client.post(
            LOGIN_URL,
            {"email": "nonexistent@example.com", "password": self.password},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_inactive_user(self):
        self.user.is_active = False
        self.user.save()
        resp = self.client.post(
            LOGIN_URL,
            {"email": self.user.email, "password": self.password},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_returns_company_id(self):
        co = _company()
        user = _user(company=co, password="CompanyPass123!")
        resp = self.client.post(
            LOGIN_URL,
            {"email": user.email, "password": "CompanyPass123!"},
            format="json",
        )
        assert resp.data["user"]["company_id"] == str(co.id)

    def test_login_no_company_returns_null(self):
        resp = self.client.post(
            LOGIN_URL,
            {"email": self.user.email, "password": self.password},
            format="json",
        )
        assert resp.data["user"]["company_id"] is None


# ══════════════════════════════════════════════════════════════
# TestLogout
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestLogout(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.password = "LogoutPass12345!"
        self.user = _user(password=self.password)

    def test_logout_success(self):
        # Login first
        login_resp = self.client.post(
            LOGIN_URL,
            {"email": self.user.email, "password": self.password},
            format="json",
        )
        tokens = login_resp.data["tokens"]

        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            LOGOUT_URL,
            {"refresh": tokens["refresh"]},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["detail"] == "Logout successful."

    def test_logout_creates_audit_log(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(LOGOUT_URL, {}, format="json")
        assert AuditLog.objects.filter(action="user_logged_out").exists()

    def test_logout_unauthenticated(self):
        resp = self.client.post(LOGOUT_URL, {}, format="json")
        assert resp.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    def test_logout_without_refresh_token(self):
        """Logout should succeed even without refresh token."""
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(LOGOUT_URL, {}, format="json")
        assert resp.status_code == status.HTTP_200_OK


# ══════════════════════════════════════════════════════════════
# TestChangePassword
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestChangePassword(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.old_pw = "OldPassword12345!"
        self.new_pw = "NewStrongPass567!"
        self.user = _user(password=self.old_pw)
        self.client.force_authenticate(user=self.user)

    def test_change_password_success(self):
        resp = self.client.post(
            CHANGE_PW_URL,
            {
                "current_password": self.old_pw,
                "new_password": self.new_pw,
                "new_password_confirm": self.new_pw,
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        self.user.refresh_from_db()
        assert self.user.check_password(self.new_pw) is True

    def test_change_password_wrong_current(self):
        resp = self.client.post(
            CHANGE_PW_URL,
            {
                "current_password": "WrongCurrent1234!",
                "new_password": self.new_pw,
                "new_password_confirm": self.new_pw,
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_change_password_mismatch(self):
        resp = self.client.post(
            CHANGE_PW_URL,
            {
                "current_password": self.old_pw,
                "new_password": self.new_pw,
                "new_password_confirm": "Mismatch12345!",
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_change_password_creates_audit_log(self):
        self.client.post(
            CHANGE_PW_URL,
            {
                "current_password": self.old_pw,
                "new_password": self.new_pw,
                "new_password_confirm": self.new_pw,
            },
            format="json",
        )
        assert AuditLog.objects.filter(action="password_changed").exists()

    def test_change_password_invalidates_tokens(self):
        """After password change all outstanding tokens should be blacklisted."""
        from rest_framework_simplejwt.token_blacklist.models import (
            BlacklistedToken,
            OutstandingToken,
        )
        from rest_framework_simplejwt.tokens import RefreshToken

        # Create a token
        RefreshToken.for_user(self.user)
        outstanding_before = OutstandingToken.objects.filter(user=self.user).count()
        assert outstanding_before >= 1

        self.client.post(
            CHANGE_PW_URL,
            {
                "current_password": self.old_pw,
                "new_password": self.new_pw,
                "new_password_confirm": self.new_pw,
            },
            format="json",
        )
        blacklisted_count = BlacklistedToken.objects.filter(
            token__user=self.user
        ).count()
        assert blacklisted_count >= outstanding_before

    def test_change_password_unauthenticated(self):
        client = APIClient()
        resp = client.post(
            CHANGE_PW_URL,
            {
                "current_password": self.old_pw,
                "new_password": self.new_pw,
                "new_password_confirm": self.new_pw,
            },
            format="json",
        )
        assert resp.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


# ══════════════════════════════════════════════════════════════
# TestMeView
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestMeView(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.co = _company(name="MyCo")
        self.user = _user(
            company=self.co,
            first_name="Jane",
            last_name="Doe",
        )
        self.client.force_authenticate(user=self.user)

    def test_get_profile(self):
        resp = self.client.get(ME_URL)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["email"] == self.user.email
        assert resp.data["first_name"] == "Jane"
        assert resp.data["last_name"] == "Doe"
        assert resp.data["company"]["name"] == "MyCo"

    def test_get_profile_no_company(self):
        user = _user()
        self.client.force_authenticate(user=user)
        resp = self.client.get(ME_URL)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["company"] is None

    def test_patch_first_name(self):
        resp = self.client.patch(ME_URL, {"first_name": "Janet"}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["user"]["first_name"] == "Janet"
        self.user.refresh_from_db()
        assert self.user.first_name == "Janet"

    def test_patch_last_name(self):
        resp = self.client.patch(ME_URL, {"last_name": "Smith"}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["user"]["last_name"] == "Smith"

    def test_patch_both_names(self):
        resp = self.client.patch(
            ME_URL,
            {"first_name": "New", "last_name": "Name"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        self.user.refresh_from_db()
        assert self.user.first_name == "New"
        assert self.user.last_name == "Name"

    def test_patch_ignores_non_allowed_fields(self):
        resp = self.client.patch(
            ME_URL,
            {"email": "hacker@evil.com", "is_staff": True},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        self.user.refresh_from_db()
        assert self.user.email != "hacker@evil.com"
        assert self.user.is_staff is False

    def test_patch_empty_body(self):
        resp = self.client.patch(ME_URL, {}, format="json")
        assert resp.status_code == status.HTTP_200_OK

    def test_get_unauthenticated(self):
        client = APIClient()
        resp = client.get(ME_URL)
        assert resp.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


# ══════════════════════════════════════════════════════════════
# TestAPIKeyAuth
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestAPIKeyAuth(TestCase):
    """
    Tests for the APIKeyAuthentication backend.

    We test the class directly because the test settings may not
    include it in DEFAULT_AUTHENTICATION_CLASSES.
    """

    def setUp(self):
        self.co = _company()
        self.user = _user(company=self.co)

    def _create_key(self, **kw):
        import secrets

        raw = kw.pop("raw_key", None) or secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(raw.encode()).hexdigest()
        defaults = {
            "name": "test-key",
            "key_hash": key_hash,
            "company": self.co,
            "created_by": self.user,
            "prefix": raw[:8],
            "is_active": True,
        }
        defaults.update(kw)
        api_key = APIKey.objects.create(**defaults)
        return api_key, raw

    def _make_request(self, auth_header=""):
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        request = factory.get("/api/v2/health/")
        if auth_header:
            request.META["HTTP_AUTHORIZATION"] = auth_header
        return request

    def test_valid_key_authenticates(self):
        from apps.core.authentication import APIKeyAuthentication

        _, raw = self._create_key()
        auth = APIKeyAuthentication()
        request = self._make_request(f"ApiKey {raw}")
        result = auth.authenticate(request)
        assert result is not None
        user, api_key_obj = result
        assert user == self.user

    def test_invalid_key_rejected(self):
        from apps.core.authentication import APIKeyAuthentication
        from rest_framework.exceptions import AuthenticationFailed

        auth = APIKeyAuthentication()
        request = self._make_request("ApiKey invalid_key_garbage")
        with pytest.raises(AuthenticationFailed):
            auth.authenticate(request)

    def test_expired_key_rejected(self):
        from apps.core.authentication import APIKeyAuthentication
        from rest_framework.exceptions import AuthenticationFailed

        _, raw = self._create_key(
            expires_at=timezone.now() - timedelta(hours=1),
        )
        auth = APIKeyAuthentication()
        request = self._make_request(f"ApiKey {raw}")
        with pytest.raises(AuthenticationFailed, match="expired"):
            auth.authenticate(request)

    def test_inactive_key_rejected(self):
        from apps.core.authentication import APIKeyAuthentication
        from rest_framework.exceptions import AuthenticationFailed

        _, raw = self._create_key(is_active=False)
        auth = APIKeyAuthentication()
        request = self._make_request(f"ApiKey {raw}")
        with pytest.raises(AuthenticationFailed):
            auth.authenticate(request)

    def test_last_used_updated(self):
        from apps.core.authentication import APIKeyAuthentication

        api_key, raw = self._create_key()
        assert api_key.last_used_at is None
        auth = APIKeyAuthentication()
        request = self._make_request(f"ApiKey {raw}")
        auth.authenticate(request)
        api_key.refresh_from_db()
        assert api_key.last_used_at is not None

    def test_wrong_scheme_returns_none(self):
        """Using Bearer instead of ApiKey should return None (not handled)."""
        from apps.core.authentication import APIKeyAuthentication

        _, raw = self._create_key()
        auth = APIKeyAuthentication()
        request = self._make_request(f"Bearer {raw}")
        result = auth.authenticate(request)
        assert result is None

    def test_empty_key_returns_none(self):
        from apps.core.authentication import APIKeyAuthentication

        auth = APIKeyAuthentication()
        request = self._make_request("ApiKey ")
        result = auth.authenticate(request)
        assert result is None

    def test_no_auth_header_returns_none(self):
        from apps.core.authentication import APIKeyAuthentication

        auth = APIKeyAuthentication()
        request = self._make_request("")
        result = auth.authenticate(request)
        assert result is None

    def test_authenticate_header_returns_keyword(self):
        from apps.core.authentication import APIKeyAuthentication

        auth = APIKeyAuthentication()
        request = self._make_request("")
        assert auth.authenticate_header(request) == "ApiKey"


# ══════════════════════════════════════════════════════════════
# TestCreateAPIKeyView
# ══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestCreateAPIKeyView(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.co = _company()
        self.user = _user(company=self.co)
        self.client.force_authenticate(user=self.user)

    def test_create_api_key_success(self):
        resp = self.client.post(
            CREATE_KEY_URL,
            {"name": "prod-key"},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert "key" in resp.data["api_key"]
        assert resp.data["api_key"]["name"] == "prod-key"
        assert resp.data["api_key"]["prefix"]

    def test_create_api_key_no_company(self):
        user = _user()
        self.client.force_authenticate(user=user)
        resp = self.client.post(
            CREATE_KEY_URL,
            {"name": "my-key"},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_api_key_no_name(self):
        resp = self.client.post(
            CREATE_KEY_URL,
            {"name": ""},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_api_key_creates_audit_log(self):
        self.client.post(CREATE_KEY_URL, {"name": "k"}, format="json")
        assert AuditLog.objects.filter(action="api_key_created").exists()

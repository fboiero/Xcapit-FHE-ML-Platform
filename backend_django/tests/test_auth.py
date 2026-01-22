"""
Authentication tests for Xcapit FHE-ML Platform.
"""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

User = get_user_model()


@pytest.mark.django_db
class TestRegistration:
    """Tests for user registration."""

    def test_register_success(self, api_client):
        """Test successful user registration."""
        url = "/api/v2/auth/register/"
        data = {
            "email": "newuser@example.com",
            "password": "securepassword123",
            "password_confirm": "securepassword123",
            "first_name": "New",
            "last_name": "User",
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert "tokens" in response.data
        assert "access" in response.data["tokens"]
        assert "refresh" in response.data["tokens"]
        assert User.objects.filter(email="newuser@example.com").exists()

    def test_register_with_company(self, api_client):
        """Test registration with company creation."""
        url = "/api/v2/auth/register/"
        data = {
            "email": "company@example.com",
            "password": "securepassword123",
            "password_confirm": "securepassword123",
            "first_name": "Company",
            "last_name": "User",
            "company_name": "New Company Inc",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        user = User.objects.get(email="company@example.com")
        assert user.company is not None
        assert user.company.name == "New Company Inc"

    def test_register_password_mismatch(self, api_client):
        """Test registration fails with mismatched passwords."""
        url = "/api/v2/auth/register/"
        data = {
            "email": "test@example.com",
            "password": "password123",
            "password_confirm": "differentpassword",
            "first_name": "Test",
            "last_name": "User",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_duplicate_email(self, api_client, user):
        """Test registration fails with existing email."""
        url = "/api/v2/auth/register/"
        data = {
            "email": user.email,
            "password": "password123",
            "password_confirm": "password123",
            "first_name": "Duplicate",
            "last_name": "User",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_weak_password(self, api_client):
        """Test registration fails with weak password."""
        url = "/api/v2/auth/register/"
        data = {
            "email": "weak@example.com",
            "password": "123",
            "password_confirm": "123",
            "first_name": "Weak",
            "last_name": "Password",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLogin:
    """Tests for user login."""

    def test_login_success(self, api_client, user):
        """Test successful login."""
        url = "/api/v2/auth/login/"
        data = {
            "email": user.email,
            "password": "testpassword123",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "tokens" in response.data
        assert "access" in response.data["tokens"]
        assert "refresh" in response.data["tokens"]
        assert response.data["user"]["email"] == user.email

    def test_login_invalid_credentials(self, api_client, user):
        """Test login fails with invalid credentials."""
        url = "/api/v2/auth/login/"
        data = {
            "email": user.email,
            "password": "wrongpassword",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_nonexistent_user(self, api_client):
        """Test login fails with nonexistent email."""
        url = "/api/v2/auth/login/"
        data = {
            "email": "nonexistent@example.com",
            "password": "password123",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestAuthenticatedEndpoints:
    """Tests for authenticated endpoints."""

    def test_me_endpoint(self, auth_client, user):
        """Test getting current user info."""
        url = "/api/v2/auth/me/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == user.email
        assert response.data["first_name"] == user.first_name

    def test_me_update(self, auth_client, user):
        """Test updating current user info."""
        url = "/api/v2/auth/me/"
        data = {"first_name": "Updated"}

        response = auth_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.first_name == "Updated"

    def test_change_password(self, auth_client, user):
        """Test password change."""
        url = "/api/v2/auth/change-password/"
        data = {
            "current_password": "testpassword123",
            "new_password": "newpassword456",
            "new_password_confirm": "newpassword456",
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.check_password("newpassword456")

    def test_change_password_wrong_current(self, auth_client, user):
        """Test password change fails with wrong current password."""
        url = "/api/v2/auth/change-password/"
        data = {
            "current_password": "wrongpassword",
            "new_password": "newpassword456",
            "new_password_confirm": "newpassword456",
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthenticated_access(self, api_client):
        """Test unauthenticated access is denied."""
        url = "/api/v2/auth/me/"

        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestLogout:
    """Tests for user logout."""

    def test_logout_success(self, auth_client, user):
        """Test successful logout."""
        # First login to get tokens
        login_url = "/api/v2/auth/login/"
        login_data = {
            "email": user.email,
            "password": "testpassword123",
        }
        login_response = auth_client.post(login_url, login_data, format='json')
        refresh_token = login_response.data["tokens"]["refresh"]

        # Then logout
        logout_url = "/api/v2/auth/logout/"
        response = auth_client.post(logout_url, {"refresh": refresh_token}, format='json')

        assert response.status_code == status.HTTP_200_OK

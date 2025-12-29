"""
Pytest configuration and fixtures for Xcapit FHE-ML Platform tests.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.models import Company


User = get_user_model()


@pytest.fixture
def api_client():
    """Return an unauthenticated API client."""
    return APIClient()


@pytest.fixture
def company(db):
    """Create a test company."""
    return Company.objects.create(
        name="Test Company",
        email="test@testcompany.com",
        industry="technology",
    )


@pytest.fixture
def other_company(db):
    """Create another test company."""
    return Company.objects.create(
        name="Other Company",
        email="other@othercompany.com",
        industry="finance",
    )


@pytest.fixture
def user(db, company):
    """Create a test user with company."""
    user = User.objects.create_user(
        email="test@example.com",
        password="testpassword123",
        first_name="Test",
        last_name="User",
        company=company,
    )
    return user


@pytest.fixture
def other_user(db, other_company):
    """Create another test user with different company."""
    user = User.objects.create_user(
        email="other@example.com",
        password="otherpassword123",
        first_name="Other",
        last_name="User",
        company=other_company,
    )
    return user


@pytest.fixture
def admin_user(db, company):
    """Create an admin test user."""
    user = User.objects.create_superuser(
        email="admin@example.com",
        password="adminpassword123",
        first_name="Admin",
        last_name="User",
        company=company,
    )
    return user


@pytest.fixture
def auth_client(api_client, user):
    """Return an authenticated API client."""
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.fixture
def other_auth_client(api_client, other_user):
    """Return an authenticated API client for other user."""
    client = APIClient()
    refresh = RefreshToken.for_user(other_user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


@pytest.fixture
def admin_client(api_client, admin_user):
    """Return an authenticated admin API client."""
    client = APIClient()
    refresh = RefreshToken.for_user(admin_user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


@pytest.fixture
def consortium(db, company):
    """Create a test consortium."""
    from apps.consortiums.models import Consortium

    return Consortium.objects.create(
        name="Test Consortium",
        owner=company,
        status=Consortium.Status.ACTIVE,
        description="Test consortium for unit tests",
    )


@pytest.fixture
def ml_model(db, company, consortium):
    """Create a test ML model."""
    from apps.models.models import MLModel

    return MLModel.objects.create(
        name="Test Model",
        owner=company,
        consortium=consortium,
        model_type=MLModel.ModelType.LOGISTIC_REGRESSION,
        status=MLModel.Status.TRAINED,
        n_features=10,
    )

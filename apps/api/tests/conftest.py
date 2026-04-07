import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_factory():
    def make_user(**kwargs):
        email = kwargs.pop("email", "user@example.com")
        password = kwargs.pop("password", "securepass123")
        return User.objects.create_user(email=email, password=password, **kwargs)

    return make_user

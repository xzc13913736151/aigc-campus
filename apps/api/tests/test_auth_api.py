import pytest
from django.contrib.auth import get_user_model
import yaml

from profiles.models import Profile


User = get_user_model()


@pytest.mark.django_db
def test_register_creates_user_and_profile(api_client):
    response = api_client.post(
        "/api/v1/auth/register/",
        {
            "email": "newuser@example.com",
            "password": "securepass123",
            "full_name": "New User",
            "nickname": "newbie",
        },
        format="json",
    )

    assert response.status_code == 201
    user = User.objects.get(email="newuser@example.com")
    assert Profile.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_login_and_get_current_user(api_client, user_factory):
    user_factory(email="login@example.com", password="securepass123", full_name="Login User")

    login_response = api_client.post(
        "/api/v1/auth/login/",
        {"email": "login@example.com", "password": "securepass123"},
        format="json",
    )

    assert login_response.status_code == 200
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")

    me_response = api_client.get("/api/v1/auth/me/")
    assert me_response.status_code == 200
    assert me_response.data["email"] == "login@example.com"


@pytest.mark.django_db
def test_schema_endpoint_returns_openapi_document(api_client):
    response = api_client.get("/api/schema/")

    assert response.status_code == 200

    schema = yaml.safe_load(response.content)
    assert schema["openapi"].startswith("3.")

    dating_candidate_schema = schema["components"]["schemas"]["DatingCandidate"]
    assert "match_score" in dating_candidate_schema["properties"]

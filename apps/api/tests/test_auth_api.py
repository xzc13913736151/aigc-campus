import re
from unittest.mock import Mock, patch

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings
import yaml

from profiles.models import Profile


User = get_user_model()


@pytest.mark.django_db
def test_request_email_code_sends_message(api_client):
    response = api_client.post(
        "/api/v1/auth/email-code/request/",
        {"email": "newuser@example.com"},
        format="json",
    )

    assert response.status_code == 202
    assert response.data["email"] == "newuser@example.com"
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["newuser@example.com"]
    assert "verification code" in mail.outbox[0].subject.lower()


@pytest.mark.django_db
def test_register_creates_user_and_profile(api_client):
    request_response = api_client.post(
        "/api/v1/auth/email-code/request/",
        {"email": "newuser@example.com"},
        format="json",
    )
    assert request_response.status_code == 202
    verification_code = re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1)

    response = api_client.post(
        "/api/v1/auth/register/",
        {
            "email": "newuser@example.com",
            "password": "securepass123",
            "verification_code": verification_code,
            "full_name": "New User",
            "nickname": "newbie",
        },
        format="json",
    )

    assert response.status_code == 201
    user = User.objects.get(email="newuser@example.com")
    assert user.is_email_verified is True
    assert user.email_verified_at is not None
    assert Profile.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_register_rejects_invalid_verification_code(api_client):
    request_response = api_client.post(
        "/api/v1/auth/email-code/request/",
        {"email": "newuser@example.com"},
        format="json",
    )
    assert request_response.status_code == 202

    response = api_client.post(
        "/api/v1/auth/register/",
        {
            "email": "newuser@example.com",
            "password": "securepass123",
            "verification_code": "000000",
            "full_name": "New User",
            "nickname": "newbie",
        },
        format="json",
    )

    assert response.status_code == 400
    assert "verification_code" in response.data


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
@override_settings(WECHAT_MINIAPP_APPID="wx-test-appid", WECHAT_MINIAPP_SECRET="wx-test-secret")
def test_wechat_login_creates_user_and_profile(api_client):
    with patch("accounts.serializers.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {"openid": "openid-123456"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        response = api_client.post(
            "/api/v1/auth/wechat-login/",
            {"code": "wechat-code-1"},
            format="json",
        )

    assert response.status_code == 200
    user = User.objects.get(wechat_openid="openid-123456")
    assert user.has_usable_password() is False
    assert user.nickname.endswith("123456")
    assert Profile.objects.filter(user=user).exists()
    assert response.data["access"]
    assert response.data["refresh"]
    assert response.data["user"]["id"] == str(user.id)


@pytest.mark.django_db
@override_settings(WECHAT_MINIAPP_APPID="wx-test-appid", WECHAT_MINIAPP_SECRET="wx-test-secret")
def test_wechat_login_reuses_existing_user(api_client):
    user = User.objects.create_user(
        email="wx_existing@wechat.pairup.local",
        password=None,
        nickname="微信用户000001",
        wechat_openid="openid-existing",
    )

    with patch("accounts.serializers.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {"openid": "openid-existing"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        response = api_client.post(
            "/api/v1/auth/wechat-login/",
            {"code": "wechat-code-2"},
            format="json",
        )

    assert response.status_code == 200
    assert User.objects.filter(wechat_openid="openid-existing").count() == 1
    assert response.data["user"]["id"] == str(user.id)


@pytest.mark.django_db
@override_settings(WECHAT_MINIAPP_APPID="wx-test-appid", WECHAT_MINIAPP_SECRET="wx-test-secret")
def test_wechat_login_token_can_access_current_user(api_client):
    with patch("accounts.serializers.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {"openid": "openid-auth-me"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        login_response = api_client.post(
            "/api/v1/auth/wechat-login/",
            {"code": "wechat-code-3"},
            format="json",
        )

    assert login_response.status_code == 200
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")
    me_response = api_client.get("/api/v1/auth/me/")
    assert me_response.status_code == 200
    assert me_response.data["email"].endswith("@wechat.pairup.local")


@pytest.mark.django_db
def test_schema_endpoint_returns_openapi_document(api_client):
    response = api_client.get("/api/schema/")

    assert response.status_code == 200

    schema = yaml.safe_load(response.content)
    assert schema["openapi"].startswith("3.")

    dating_candidate_schema = schema["components"]["schemas"]["DatingCandidate"]
    assert "match_score" in dating_candidate_schema["properties"]

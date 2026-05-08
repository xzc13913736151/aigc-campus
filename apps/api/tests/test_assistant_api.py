import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_assistant_session_create_and_message_reply(user_factory):
    user_factory(email="assistant@example.com", password="securepass123")

    client = APIClient()
    login_response = client.post(
        "/api/v1/auth/login/",
        {"email": "assistant@example.com", "password": "securepass123"},
        format="json",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")

    session_response = client.post(
        "/api/v1/assistant/sessions/",
        {
            "page_type": "forum",
            "context_path": "/pages/forum/index",
        },
        format="json",
    )
    assert session_response.status_code == 201
    assert session_response.data["page_type"] == "forum"

    session_id = session_response.data["id"]
    message_response = client.post(
        f"/api/v1/assistant/sessions/{session_id}/messages/",
        {"body": "帮我想一个校园论坛发帖标题"},
        format="json",
    )
    assert message_response.status_code == 201
    assert message_response.data["user_message"]["role"] == "user"
    assert message_response.data["assistant_message"]["role"] == "assistant"
    assert "论坛页" in message_response.data["assistant_message"]["body"]

    list_response = client.get(f"/api/v1/assistant/sessions/{session_id}/messages/")
    assert list_response.status_code == 200
    assert len(list_response.data) == 2

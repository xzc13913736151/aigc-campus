import pytest
from rest_framework.test import APIClient

from chat.models import ChatThread
from dating.models import DatingMatch, DatingProfile
from moderation.models import Block


@pytest.mark.django_db
def test_blocked_users_are_hidden_from_dating_candidates_and_matches(user_factory):
    user = user_factory(email="dating-user@example.com", password="securepass123")
    blocked = user_factory(email="dating-blocked@example.com", password="securepass123")
    visible = user_factory(email="dating-visible@example.com", password="securepass123")

    DatingProfile.objects.create(user=user, nickname="me", is_visible=True)
    DatingProfile.objects.create(user=blocked, nickname="blocked", is_visible=True)
    DatingProfile.objects.create(user=visible, nickname="visible", is_visible=True)

    Block.objects.create(user=user, blocked_user=blocked, reason="manual block")
    DatingMatch.objects.create(
        user_a=user if str(user.id) < str(blocked.id) else blocked,
        user_b=blocked if str(user.id) < str(blocked.id) else user,
    )
    DatingMatch.objects.create(
        user_a=user if str(user.id) < str(visible.id) else visible,
        user_b=visible if str(user.id) < str(visible.id) else user,
    )

    client = APIClient()
    login_response = client.post(
        "/api/v1/auth/login/",
        {"email": "dating-user@example.com", "password": "securepass123"},
        format="json",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")

    candidates_response = client.get("/api/v1/dating/candidates/")
    assert candidates_response.status_code == 200
    candidate_ids = {item["user"]["id"] for item in candidates_response.data}
    assert str(blocked.id) not in candidate_ids
    assert str(visible.id) in candidate_ids

    matches_response = client.get("/api/v1/dating/matches/")
    assert matches_response.status_code == 200
    counterpart_ids = {item["counterpart"]["id"] for item in matches_response.data if item["counterpart"]}
    assert str(blocked.id) not in counterpart_ids
    assert str(visible.id) in counterpart_ids


@pytest.mark.django_db
def test_blocked_users_cannot_create_or_use_chat(user_factory):
    user = user_factory(email="chat-user@example.com", password="securepass123")
    blocked = user_factory(email="chat-blocked@example.com", password="securepass123")

    Block.objects.create(user=user, blocked_user=blocked, reason="manual block")

    client = APIClient()
    login_response = client.post(
        "/api/v1/auth/login/",
        {"email": "chat-user@example.com", "password": "securepass123"},
        format="json",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")

    create_thread_response = client.post(
        "/api/v1/chat/threads/",
        {"target_user_id": str(blocked.id), "source_type": "dating_match"},
        format="json",
    )
    assert create_thread_response.status_code == 400

    thread = ChatThread.objects.create(
        user_a=user if str(user.id) < str(blocked.id) else blocked,
        user_b=blocked if str(user.id) < str(blocked.id) else user,
    )

    thread_list_response = client.get("/api/v1/chat/threads/")
    assert thread_list_response.status_code == 200
    assert thread_list_response.data == []

    send_message_response = client.post(
        f"/api/v1/chat/threads/{thread.id}/messages/",
        {"body": "hello"},
        format="json",
    )
    assert send_message_response.status_code == 403

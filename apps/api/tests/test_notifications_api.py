import pytest
from rest_framework.test import APIClient

from moderation.models import Block
from notifications.models import Notification
from notifications.services import create_notification


@pytest.mark.django_db
def test_notifications_list_unread_count_and_mark_read(user_factory):
    recipient = user_factory(email="recipient@example.com", password="securepass123")
    actor = user_factory(email="actor@example.com", password="securepass123")

    Notification.objects.create(
        recipient=recipient,
        actor=actor,
        type=Notification.Type.FORUM_COMMENT,
        title="你的帖子收到评论",
        body="有人评论了你的帖子。",
        target_type="forum_post",
        target_id="post-1",
    )
    Notification.objects.create(
        recipient=recipient,
        actor=actor,
        type=Notification.Type.TEAM_APPLICATION_CREATED,
        title="你的组队收到新申请",
        body="有人申请了你的组队。",
        target_type="team_post",
        target_id="post-2",
    )

    client = APIClient()
    login_response = client.post(
        "/api/v1/auth/login/",
        {"email": "recipient@example.com", "password": "securepass123"},
        format="json",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")

    list_response = client.get("/api/v1/notifications/")
    assert list_response.status_code == 200
    assert len(list_response.data) == 2

    unread_response = client.get("/api/v1/notifications/unread-count/")
    assert unread_response.status_code == 200
    assert unread_response.data["unread_count"] == 2

    notification_id = list_response.data[0]["id"]
    mark_one_response = client.patch(
        f"/api/v1/notifications/{notification_id}/",
        {"is_read": True},
        format="json",
    )
    assert mark_one_response.status_code == 200

    mark_all_response = client.post("/api/v1/notifications/mark-all-read/")
    assert mark_all_response.status_code == 200

    final_unread_response = client.get("/api/v1/notifications/unread-count/")
    assert final_unread_response.status_code == 200
    assert final_unread_response.data["unread_count"] == 0


@pytest.mark.django_db
def test_blocked_actor_notifications_are_hidden_and_not_created(user_factory):
    recipient = user_factory(email="blocked-recipient@example.com", password="securepass123")
    actor = user_factory(email="blocked-actor@example.com", password="securepass123")
    visible_actor = user_factory(email="visible-actor@example.com", password="securepass123")

    Block.objects.create(user=recipient, blocked_user=actor, reason="manual block")

    Notification.objects.create(
        recipient=recipient,
        actor=actor,
        type=Notification.Type.FORUM_COMMENT,
        title="Blocked actor notification",
        body="This should be hidden.",
        target_type="forum_post",
        target_id="post-hidden",
    )
    Notification.objects.create(
        recipient=recipient,
        actor=visible_actor,
        type=Notification.Type.FORUM_COMMENT,
        title="Visible actor notification",
        body="This should stay visible.",
        target_type="forum_post",
        target_id="post-visible",
    )

    created = create_notification(
        recipient=recipient,
        actor=actor,
        type=Notification.Type.CHAT_MESSAGE,
        title="Blocked",
        body="Should not be created.",
        target_type="chat_thread",
        target_id="thread-1",
    )
    assert created is None

    client = APIClient()
    login_response = client.post(
        "/api/v1/auth/login/",
        {"email": "blocked-recipient@example.com", "password": "securepass123"},
        format="json",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")

    list_response = client.get("/api/v1/notifications/")
    assert list_response.status_code == 200
    assert len(list_response.data) == 1
    assert list_response.data[0]["title"] == "Visible actor notification"

    unread_response = client.get("/api/v1/notifications/unread-count/")
    assert unread_response.status_code == 200
    assert unread_response.data["unread_count"] == 1

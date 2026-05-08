import pytest
from rest_framework.test import APIClient

from chat.models import ChatMessage, ChatThread
from notifications.models import Notification


@pytest.mark.django_db
def test_chat_thread_creation_message_send_and_read(user_factory):
    sender = user_factory(email="chat-sender@example.com", password="securepass123")
    recipient = user_factory(email="chat-recipient@example.com", password="securepass123")

    sender_client = APIClient()
    recipient_client = APIClient()

    sender_login = sender_client.post(
        "/api/v1/auth/login/",
        {"email": "chat-sender@example.com", "password": "securepass123"},
        format="json",
    )
    recipient_login = recipient_client.post(
        "/api/v1/auth/login/",
        {"email": "chat-recipient@example.com", "password": "securepass123"},
        format="json",
    )

    sender_client.credentials(HTTP_AUTHORIZATION=f"Bearer {sender_login.data['access']}")
    recipient_client.credentials(HTTP_AUTHORIZATION=f"Bearer {recipient_login.data['access']}")

    thread_response = sender_client.post(
        "/api/v1/chat/threads/",
        {"target_user_id": str(recipient.id), "source_type": "dating_match"},
        format="json",
    )
    assert thread_response.status_code == 201

    thread_id = thread_response.data["id"]
    assert ChatThread.objects.filter(id=thread_id).count() == 1

    message_response = sender_client.post(
        f"/api/v1/chat/threads/{thread_id}/messages/",
        {"body": "你好，我们来聊聊吧"},
        format="json",
    )
    assert message_response.status_code == 201
    assert ChatMessage.objects.filter(thread_id=thread_id).count() == 1
    assert Notification.objects.filter(recipient=recipient, type=Notification.Type.CHAT_MESSAGE).count() == 1

    thread_list_response = recipient_client.get("/api/v1/chat/threads/")
    assert thread_list_response.status_code == 200
    assert len(thread_list_response.data) == 1
    assert thread_list_response.data[0]["unread_count"] == 1

    message_list_response = recipient_client.get(f"/api/v1/chat/threads/{thread_id}/messages/")
    assert message_list_response.status_code == 200
    assert len(message_list_response.data["messages"]) == 1

    mark_read_response = recipient_client.post(
        f"/api/v1/chat/threads/{thread_id}/mark-read/",
        {"mark_read": True},
        format="json",
    )
    assert mark_read_response.status_code == 200

    thread_list_after_read = recipient_client.get("/api/v1/chat/threads/")
    assert thread_list_after_read.status_code == 200
    assert thread_list_after_read.data[0]["unread_count"] == 0


@pytest.mark.django_db
def test_chat_message_withdraw_and_thread_hide(user_factory):
    sender = user_factory(email="chat-owner@example.com", password="securepass123")
    recipient = user_factory(email="chat-peer@example.com", password="securepass123")

    sender_client = APIClient()
    recipient_client = APIClient()

    sender_login = sender_client.post(
        "/api/v1/auth/login/",
        {"email": "chat-owner@example.com", "password": "securepass123"},
        format="json",
    )
    recipient_login = recipient_client.post(
        "/api/v1/auth/login/",
        {"email": "chat-peer@example.com", "password": "securepass123"},
        format="json",
    )

    sender_client.credentials(HTTP_AUTHORIZATION=f"Bearer {sender_login.data['access']}")
    recipient_client.credentials(HTTP_AUTHORIZATION=f"Bearer {recipient_login.data['access']}")

    thread_response = sender_client.post(
        "/api/v1/chat/threads/",
        {"target_user_id": str(recipient.id), "source_type": "dating_match"},
        format="json",
    )
    assert thread_response.status_code == 201
    thread_id = thread_response.data["id"]

    message_response = sender_client.post(
        f"/api/v1/chat/threads/{thread_id}/messages/",
        {"body": "I may withdraw this later."},
        format="json",
    )
    assert message_response.status_code == 201
    message_id = message_response.data["id"]

    withdraw_response = sender_client.post(
        f"/api/v1/chat/threads/{thread_id}/messages/{message_id}/withdraw/",
        {"withdraw": True},
        format="json",
    )
    assert withdraw_response.status_code == 200
    assert withdraw_response.data["is_withdrawn"] is True
    assert withdraw_response.data["body"] == "This message was withdrawn."

    hide_response = sender_client.post(
        f"/api/v1/chat/threads/{thread_id}/hide/",
        format="json",
    )
    assert hide_response.status_code == 200

    hidden_list_response = sender_client.get("/api/v1/chat/threads/")
    assert hidden_list_response.status_code == 200
    assert hidden_list_response.data == []

    recipient_list_response = recipient_client.get("/api/v1/chat/threads/")
    assert recipient_list_response.status_code == 200
    assert len(recipient_list_response.data) == 1

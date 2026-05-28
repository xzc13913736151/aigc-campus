from __future__ import annotations

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from notifications.models import Notification
from notifications.services import create_notification

from .models import ChatMessage, ChatThread


def serialize_user_summary(user) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "claw_id": user.claw_id,
        "full_name": user.full_name,
        "nickname": user.nickname,
        "role": user.role,
        "is_email_verified": user.is_email_verified,
        "email_verified_at": user.email_verified_at.isoformat() if user.email_verified_at else None,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
    }


def serialize_chat_message(message: ChatMessage) -> dict:
    sender = message.sender
    return {
        "type": "chat.message",
        "thread_id": str(message.thread_id),
        "message": {
            "id": str(message.id),
            "sender": serialize_user_summary(sender),
            "body": message.body,
            "image_url": message.image.url if message.image else "",
            "is_read": message.is_read,
            "read_at": message.read_at.isoformat() if message.read_at else None,
            "is_withdrawn": message.is_withdrawn,
            "withdrawn_at": message.withdrawn_at.isoformat() if message.withdrawn_at else None,
            "created_at": message.created_at.isoformat(),
            "updated_at": message.updated_at.isoformat(),
        },
    }


def serialize_chat_read(thread: ChatThread, message_ids: list[str], read_at: str) -> dict:
    return {
        "type": "chat.read",
        "thread_id": str(thread.id),
        "message_ids": message_ids,
        "read_at": read_at,
    }


def serialize_thread_snapshot(thread: ChatThread, viewer) -> dict:
    counterpart = thread.user_b if thread.user_a_id == viewer.id else thread.user_a
    last_message = thread.messages.order_by("-created_at").select_related("sender").first()
    unread_count = thread.messages.exclude(sender=viewer).filter(is_read=False).count()
    return {
        "id": str(thread.id),
        "counterpart": serialize_user_summary(counterpart),
        "source_type": thread.source_type,
        "source_id": thread.source_id,
        "last_message": serialize_chat_message(last_message)["message"] if last_message else None,
        "unread_count": unread_count,
        "created_at": thread.created_at.isoformat(),
        "updated_at": thread.updated_at.isoformat(),
    }


def serialize_thread_state(thread: ChatThread, user_id: str, *, online: bool | None = None, is_typing: bool | None = None) -> dict:
    payload: dict[str, object] = {
        "type": "chat.thread_state",
        "thread_id": str(thread.id),
        "user_id": user_id,
    }
    if online is not None:
        payload["online"] = online
    if is_typing is not None:
        payload["is_typing"] = is_typing
    return payload


def push_chat_event(group_name: str, payload: dict) -> None:
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "chat_event",
            "payload": payload,
        },
    )


def push_chat_message(message: ChatMessage) -> None:
    push_chat_event(f"chat_{message.thread_id.hex}", serialize_chat_message(message))


def push_chat_read(thread: ChatThread, message_ids: list[str], read_at: str) -> None:
    if not message_ids:
        return
    push_chat_event(f"chat_{thread.id.hex}", serialize_chat_read(thread, message_ids, read_at))


def push_thread_snapshot(thread: ChatThread) -> None:
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    for viewer in (thread.user_a, thread.user_b):
        async_to_sync(channel_layer.group_send)(
            f"chat_inbox_{viewer.id.hex}",
            {
                "type": "chat_event",
                "payload": {
                    "type": "chat.thread",
                    "thread": serialize_thread_snapshot(thread, viewer),
                },
            },
        )


def push_inbox_thread_state(thread: ChatThread, user_id: str, *, online: bool | None = None, is_typing: bool | None = None) -> None:
    state_payload = serialize_thread_state(thread, user_id, online=online, is_typing=is_typing)
    for viewer in (thread.user_a, thread.user_b):
        push_chat_event(f"chat_inbox_{viewer.id.hex}", state_payload)


def notify_chat_counterpart(thread: ChatThread, message: ChatMessage) -> None:
    counterpart = thread.user_b if thread.user_a_id == message.sender_id else thread.user_a
    sender = message.sender
    sender_name = sender.nickname or sender.full_name or sender.email
    body = f"{sender_name} sent you an image." if message.image else f"{sender_name} sent you a message."
    create_notification(
        recipient=counterpart,
        actor=sender,
        type=Notification.Type.CHAT_MESSAGE,
        title="You have a new message",
        body=body,
        target_type="chat_thread",
        target_id=str(thread.id),
        extra={"thread_id": str(thread.id), "message_id": str(message.id)},
    )

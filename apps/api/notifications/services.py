from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from moderation.services import is_blocked_pair

from .models import Notification
from .serializers import NotificationSerializer


User = get_user_model()


def create_notification(
    *,
    recipient: User,
    type: Notification.Type | str,
    title: str,
    body: str,
    actor: User | None = None,
    target_type: str = "",
    target_id: str = "",
    extra: dict[str, Any] | None = None,
) -> Notification | None:
    if actor and recipient.id == actor.id:
        return None
    if actor and is_blocked_pair(recipient, actor):
        return None

    notification = Notification.objects.create(
        recipient=recipient,
        actor=actor,
        type=type,
        title=title[:120],
        body=body[:280],
        target_type=target_type,
        target_id=target_id,
        extra=extra or {},
    )
    channel_layer = get_channel_layer()
    if channel_layer is not None:
        async_to_sync(channel_layer.group_send)(
            f"notifications_{recipient.id.hex}",
            {
                "type": "notify",
                "payload": NotificationSerializer(notification).data,
            },
        )
    return notification

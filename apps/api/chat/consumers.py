from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils import timezone

from moderation.services import is_blocked_pair

from .models import ChatMessage, ChatThread
from .services import (
    notify_chat_counterpart,
    push_inbox_thread_state,
    push_thread_snapshot,
    serialize_chat_message,
)


class MatchChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close()
            return

        self.thread_id = self.scope["url_route"]["kwargs"]["thread_id"]
        self.thread = await self._get_thread()
        if self.thread is None:
            await self.close()
            return

        self.group_name = f"chat_{self.thread_id.hex}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json({"type": "chat.ready", "thread_id": str(self.thread.id)})
        await self._broadcast_presence(True)

    async def disconnect(self, code):
        if hasattr(self, "group_name"):
            await self._broadcast_presence(False)
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        message_type = content.get("type")

        if message_type == "typing.start":
            await self._broadcast_typing(True)
            return

        if message_type == "typing.stop":
            await self._broadcast_typing(False)
            return

        if message_type != "message.send":
            await self.send_json({"type": "chat.error", "message": "Unsupported action."})
            return

        body = str(content.get("body", "")).strip()
        if not body:
            await self.send_json({"type": "chat.error", "message": "Message body is required."})
            return

        message = await self._create_message(body)
        payload = await self._serialize_message(message)
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat_event",
                "payload": payload,
            },
        )

    async def chat_event(self, event):
        await self.send_json(event["payload"])

    @database_sync_to_async
    def _get_thread(self):
        try:
            thread = ChatThread.objects.select_related("user_a", "user_b").get(id=self.thread_id)
        except ChatThread.DoesNotExist:
            return None

        if self.scope["user"].id not in {thread.user_a_id, thread.user_b_id}:
            return None
        counterpart = thread.user_b if thread.user_a_id == self.scope["user"].id else thread.user_a
        if is_blocked_pair(self.scope["user"], counterpart):
            return None
        return thread

    @database_sync_to_async
    def _create_message(self, body: str):
        message = ChatMessage.objects.create(thread=self.thread, sender=self.scope["user"], body=body)
        self.thread.updated_at = timezone.now()
        self.thread.hidden_for_user_a = False
        self.thread.hidden_for_user_b = False
        self.thread.save(update_fields=["updated_at", "hidden_for_user_a", "hidden_for_user_b"])
        notify_chat_counterpart(self.thread, message)
        push_thread_snapshot(self.thread)
        push_inbox_thread_state(self.thread, str(self.scope["user"].id), is_typing=False)
        return message

    @database_sync_to_async
    def _serialize_message(self, message):
        return serialize_chat_message(message)

    async def _broadcast_presence(self, online: bool):
        payload = {
            "type": "chat.presence",
            "thread_id": str(self.thread.id),
            "user_id": str(self.scope["user"].id),
            "online": online,
        }
        await self.channel_layer.group_send(self.group_name, {"type": "chat_event", "payload": payload})
        await database_sync_to_async(push_inbox_thread_state)(self.thread, str(self.scope["user"].id), online=online)

    async def _broadcast_typing(self, is_typing: bool):
        payload = {
            "type": "chat.typing",
            "thread_id": str(self.thread.id),
            "user_id": str(self.scope["user"].id),
            "is_typing": is_typing,
        }
        await self.channel_layer.group_send(self.group_name, {"type": "chat_event", "payload": payload})
        await database_sync_to_async(push_inbox_thread_state)(self.thread, str(self.scope["user"].id), is_typing=is_typing)


class ChatInboxConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close()
            return

        self.group_name = f"chat_inbox_{self.scope['user'].id.hex}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json({"type": "chat.inbox.ready"})

    async def disconnect(self, code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def chat_event(self, event):
        await self.send_json(event["payload"])

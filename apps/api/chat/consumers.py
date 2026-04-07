from channels.generic.websocket import AsyncJsonWebsocketConsumer


class MatchChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close()
            return
        await self.accept()
        await self.send_json({"type": "chat.ready", "message": "Chat scaffold is connected."})

    async def receive_json(self, content, **kwargs):
        await self.send_json({"type": "chat.placeholder", "payload": content})

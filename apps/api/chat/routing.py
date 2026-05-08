from django.urls import path

from .consumers import ChatInboxConsumer, MatchChatConsumer


websocket_urlpatterns = [
    path("ws/chat/<uuid:thread_id>/", MatchChatConsumer.as_asgi()),
    path("ws/chat/inbox/", ChatInboxConsumer.as_asgi()),
]

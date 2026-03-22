from django.urls import path

from .consumers import MatchChatConsumer


websocket_urlpatterns = [
    path("ws/chat/<uuid:room_id>/", MatchChatConsumer.as_asgi()),
]

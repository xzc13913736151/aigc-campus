from django.urls import path

from .views import (
    ChatMessageListCreateAPIView,
    ChatMessageWithdrawAPIView,
    ChatThreadHideAPIView,
    ChatThreadListCreateAPIView,
    ChatThreadMarkReadAPIView,
)


urlpatterns = [
    path("threads/", ChatThreadListCreateAPIView.as_view(), name="chat-thread-list"),
    path("threads/<uuid:thread_id>/messages/", ChatMessageListCreateAPIView.as_view(), name="chat-message-list"),
    path("threads/<uuid:thread_id>/messages/<uuid:message_id>/withdraw/", ChatMessageWithdrawAPIView.as_view(), name="chat-message-withdraw"),
    path("threads/<uuid:thread_id>/mark-read/", ChatThreadMarkReadAPIView.as_view(), name="chat-thread-mark-read"),
    path("threads/<uuid:thread_id>/hide/", ChatThreadHideAPIView.as_view(), name="chat-thread-hide"),
]

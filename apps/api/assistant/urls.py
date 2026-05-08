from django.urls import path

from .views import AssistantMessageListCreateAPIView, AssistantSessionListCreateAPIView


urlpatterns = [
    path("sessions/", AssistantSessionListCreateAPIView.as_view(), name="assistant-session-list"),
    path("sessions/<uuid:session_id>/messages/", AssistantMessageListCreateAPIView.as_view(), name="assistant-message-list"),
]

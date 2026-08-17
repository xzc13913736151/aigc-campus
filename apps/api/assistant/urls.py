from django.urls import path

from .views import AssistantActionDismissAPIView, AssistantActionExecuteAPIView, AssistantMessageListCreateAPIView, AssistantSessionActionListAPIView, AssistantSessionListCreateAPIView


urlpatterns = [
    path("sessions/", AssistantSessionListCreateAPIView.as_view(), name="assistant-session-list"),
    path("sessions/<uuid:session_id>/messages/", AssistantMessageListCreateAPIView.as_view(), name="assistant-message-list"),
    path("sessions/<uuid:session_id>/actions/", AssistantSessionActionListAPIView.as_view(), name="assistant-session-action-list"),
    path("actions/<uuid:action_id>/execute/", AssistantActionExecuteAPIView.as_view(), name="assistant-action-execute"),
    path("actions/<uuid:action_id>/dismiss/", AssistantActionDismissAPIView.as_view(), name="assistant-action-dismiss"),
]

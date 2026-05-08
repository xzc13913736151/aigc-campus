from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .models import AssistantMessage, AssistantSession
from .serializers import (
    AssistantMessageCreateSerializer,
    AssistantMessageSerializer,
    AssistantSessionCreateSerializer,
    AssistantSessionSerializer,
)
from .services import build_assistant_reply, default_session_title


class AssistantSessionListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AssistantSession.objects.filter(user=self.request.user).prefetch_related("messages")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AssistantSessionCreateSerializer
        return AssistantSessionSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = AssistantSessionSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = AssistantSession.objects.create(
            user=request.user,
            title=serializer.validated_data.get("title") or default_session_title(serializer.validated_data.get("page_type", AssistantSession.PageType.GENERAL)),
            page_type=serializer.validated_data.get("page_type", AssistantSession.PageType.GENERAL),
            context_path=serializer.validated_data.get("context_path", ""),
            context_target_type=serializer.validated_data.get("context_target_type", ""),
            context_target_id=serializer.validated_data.get("context_target_id", ""),
        )
        return Response(AssistantSessionSerializer(session).data, status=status.HTTP_201_CREATED)


class AssistantMessageListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AssistantMessageSerializer

    def get_session(self):
        return get_object_or_404(AssistantSession.objects.prefetch_related("messages"), pk=self.kwargs["session_id"], user=self.request.user)

    def get_queryset(self):
        return AssistantMessage.objects.filter(session=self.get_session())

    def list(self, request, *args, **kwargs):
        serializer = AssistantMessageSerializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        session = self.get_session()
        serializer = AssistantMessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_message = AssistantMessage.objects.create(
            session=session,
            role=AssistantMessage.Role.USER,
            body=serializer.validated_data["body"],
        )
        assistant_message = AssistantMessage.objects.create(
            session=session,
            role=AssistantMessage.Role.ASSISTANT,
            body=build_assistant_reply(session.page_type, serializer.validated_data["body"]),
        )
        if not session.title or session.title == default_session_title(session.page_type):
            session.title = serializer.validated_data["body"][:24]
        session.save()

        return Response(
            {
                "user_message": AssistantMessageSerializer(user_message).data,
                "assistant_message": AssistantMessageSerializer(assistant_message).data,
                "session": AssistantSessionSerializer(session).data,
            },
            status=status.HTTP_201_CREATED,
        )

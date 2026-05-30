from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, parsers, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from moderation.services import get_blocked_user_ids, is_blocked_pair

from .models import ChatMessage, ChatThread
from .serializers import (
    ChatMarkReadSerializer,
    ChatImageMessageCreateSerializer,
    ChatMessageCreateSerializer,
    ChatMessageSerializer,
    ChatMessageWithdrawSerializer,
    ChatThreadCreateSerializer,
    ChatThreadSerializer,
)
from .services import notify_chat_counterpart, push_chat_message, push_chat_read, push_thread_snapshot


User = get_user_model()


def run_best_effort(callback, *args, **kwargs):
    try:
        callback(*args, **kwargs)
    except Exception:
        return


def canonical_thread_users(first, second):
    return (first, second) if str(first.id) < str(second.id) else (second, first)


class ChatThreadListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        blocked_user_ids = get_blocked_user_ids(self.request.user)
        queryset = (
            ChatThread.objects.select_related("user_a", "user_b")
            .prefetch_related("messages__sender")
            .filter(user_a=self.request.user, hidden_for_user_a=False)
            | ChatThread.objects.select_related("user_a", "user_b")
            .prefetch_related("messages__sender")
            .filter(user_b=self.request.user, hidden_for_user_b=False)
        )
        return queryset.exclude(user_a_id__in=blocked_user_ids).exclude(user_b_id__in=blocked_user_ids)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ChatThreadCreateSerializer
        return ChatThreadSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset().order_by("-updated_at")
        serializer = ChatThreadSerializer(queryset, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target = get_object_or_404(User, pk=serializer.validated_data["target_user_id"])
        if is_blocked_pair(request.user, target):
            return Response({"detail": "You cannot start a chat with a blocked user."}, status=status.HTTP_400_BAD_REQUEST)
        user_a, user_b = canonical_thread_users(request.user, target)
        thread, _ = ChatThread.objects.get_or_create(
            user_a=user_a,
            user_b=user_b,
            defaults={
                "source_type": serializer.validated_data.get("source_type", ""),
                "source_id": serializer.validated_data.get("source_id", ""),
            },
        )
        if thread.user_a_id == request.user.id and thread.hidden_for_user_a:
            thread.hidden_for_user_a = False
            thread.save(update_fields=["hidden_for_user_a", "updated_at"])
        if thread.user_b_id == request.user.id and thread.hidden_for_user_b:
            thread.hidden_for_user_b = False
            thread.save(update_fields=["hidden_for_user_b", "updated_at"])
        if serializer.validated_data.get("source_type") and not thread.source_type:
            thread.source_type = serializer.validated_data["source_type"]
            thread.source_id = serializer.validated_data.get("source_id", "")
            thread.save(update_fields=["source_type", "source_id", "updated_at"])

        response_serializer = ChatThreadSerializer(thread, context=self.get_serializer_context())
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class ChatMessageListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_thread(self):
        thread = get_object_or_404(ChatThread.objects.select_related("user_a", "user_b"), pk=self.kwargs["thread_id"])
        if self.request.user.id not in {thread.user_a_id, thread.user_b_id}:
            raise PermissionDenied("You are not a participant in this chat.")
        counterpart = thread.user_b if thread.user_a_id == self.request.user.id else thread.user_a
        if is_blocked_pair(self.request.user, counterpart):
            raise PermissionDenied("This chat is unavailable because one of you has blocked the other.")
        return thread

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ChatMessageCreateSerializer
        return ChatMessageSerializer

    def get_queryset(self):
        return ChatMessage.objects.select_related("sender").filter(thread=self.get_thread())

    def list(self, request, *args, **kwargs):
        thread = self.get_thread()
        queryset = self.get_queryset()
        unread_queryset = queryset.exclude(sender=request.user).filter(is_read=False)
        unread_ids = [str(message.id) for message in unread_queryset]
        read_at = timezone.now()
        unread_queryset.update(is_read=True, read_at=read_at)
        push_chat_read(thread, unread_ids, read_at.isoformat())
        if unread_ids:
            push_thread_snapshot(thread)
        serializer = ChatMessageSerializer(queryset, many=True, context=self.get_serializer_context())
        return Response(
            {
                "thread": ChatThreadSerializer(thread, context=self.get_serializer_context()).data,
                "messages": serializer.data,
            }
        )

    def create(self, request, *args, **kwargs):
        thread = self.get_thread()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = ChatMessage.objects.create(thread=thread, sender=request.user, body=serializer.validated_data["body"])
        thread.updated_at = timezone.now()
        if thread.user_a_id == request.user.id:
            thread.hidden_for_user_a = False
            thread.hidden_for_user_b = False
            thread.save(update_fields=["updated_at", "hidden_for_user_a", "hidden_for_user_b"])
        else:
            thread.hidden_for_user_a = False
            thread.hidden_for_user_b = False
            thread.save(update_fields=["updated_at", "hidden_for_user_a", "hidden_for_user_b"])

        run_best_effort(notify_chat_counterpart, thread, message)
        run_best_effort(push_chat_message, message)

        response_serializer = ChatMessageSerializer(message, context=self.get_serializer_context())
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class ChatImageMessageCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def get_thread(self):
        thread = get_object_or_404(ChatThread.objects.select_related("user_a", "user_b"), pk=self.kwargs["thread_id"])
        if self.request.user.id not in {thread.user_a_id, thread.user_b_id}:
            raise PermissionDenied("You are not a participant in this chat.")
        counterpart = thread.user_b if thread.user_a_id == self.request.user.id else thread.user_a
        if is_blocked_pair(self.request.user, counterpart):
            raise PermissionDenied("This chat is unavailable because one of you has blocked the other.")
        return thread

    def post(self, request, thread_id):
        thread = self.get_thread()
        serializer = ChatImageMessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = ChatMessage.objects.create(thread=thread, sender=request.user, image=serializer.validated_data["image"])
        thread.updated_at = timezone.now()
        thread.hidden_for_user_a = False
        thread.hidden_for_user_b = False
        thread.save(update_fields=["updated_at", "hidden_for_user_a", "hidden_for_user_b"])

        run_best_effort(notify_chat_counterpart, thread, message)
        run_best_effort(push_chat_message, message)
        response_serializer = ChatMessageSerializer(message, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class ChatThreadMarkReadAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, thread_id):
        thread = get_object_or_404(ChatThread.objects.select_related("user_a", "user_b"), pk=thread_id)
        if request.user.id not in {thread.user_a_id, thread.user_b_id}:
            raise PermissionDenied("You are not a participant in this chat.")

        queryset = ChatMessage.objects.filter(thread=thread).exclude(sender=request.user).filter(is_read=False)
        unread_ids = [str(message.id) for message in queryset]
        read_at = timezone.now()
        serializer = ChatMarkReadSerializer(data=request.data, context={"queryset": queryset})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        push_chat_read(thread, unread_ids, read_at.isoformat())
        if unread_ids:
            push_thread_snapshot(thread)
        return Response({"detail": "Messages marked as read."}, status=status.HTTP_200_OK)


class ChatMessageWithdrawAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, thread_id, message_id):
        thread = get_object_or_404(ChatThread.objects.select_related("user_a", "user_b"), pk=thread_id)
        if request.user.id not in {thread.user_a_id, thread.user_b_id}:
            raise PermissionDenied("You are not a participant in this chat.")

        message = get_object_or_404(ChatMessage.objects.select_related("sender"), pk=message_id, thread=thread)
        if message.sender_id != request.user.id:
            raise PermissionDenied("You can only withdraw your own message.")
        serializer = ChatMessageWithdrawSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message.is_withdrawn = True
        message.body = "This message was withdrawn."
        message.withdrawn_at = timezone.now()
        message.save(update_fields=["is_withdrawn", "body", "withdrawn_at", "updated_at"])
        push_chat_message(message)
        push_thread_snapshot(thread)
        return Response(ChatMessageSerializer(message, context={"request": request}).data, status=status.HTTP_200_OK)


class ChatThreadHideAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, thread_id):
        thread = get_object_or_404(ChatThread.objects.select_related("user_a", "user_b"), pk=thread_id)
        if request.user.id not in {thread.user_a_id, thread.user_b_id}:
            raise PermissionDenied("You are not a participant in this chat.")

        if thread.user_a_id == request.user.id:
            thread.hidden_for_user_a = True
            thread.save(update_fields=["hidden_for_user_a", "updated_at"])
        else:
            thread.hidden_for_user_b = True
            thread.save(update_fields=["hidden_for_user_b", "updated_at"])
        return Response({"detail": "Chat thread hidden."}, status=status.HTTP_200_OK)

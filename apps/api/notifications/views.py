from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from moderation.services import get_blocked_user_ids

from .models import Notification
from .serializers import NotificationReadSerializer, NotificationSerializer


class NotificationListAPIView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        blocked_user_ids = get_blocked_user_ids(self.request.user)
        queryset = (
            Notification.objects.select_related("actor", "recipient")
            .filter(recipient=self.request.user)
            .exclude(actor_id__in=blocked_user_ids)
        )
        unread_only = self.request.query_params.get("unread")
        if unread_only in {"1", "true", "yes"}:
            queryset = queryset.filter(is_read=False)
        return queryset


class NotificationDetailAPIView(generics.UpdateAPIView):
    serializer_class = NotificationReadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        blocked_user_ids = get_blocked_user_ids(self.request.user)
        return Notification.objects.filter(recipient=self.request.user).exclude(actor_id__in=blocked_user_ids)


class NotificationUnreadCountAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        blocked_user_ids = get_blocked_user_ids(request.user)
        unread_count = (
            Notification.objects.filter(recipient=request.user, is_read=False)
            .exclude(actor_id__in=blocked_user_ids)
            .count()
        )
        return Response({"unread_count": unread_count}, status=status.HTTP_200_OK)


class NotificationMarkAllReadAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        blocked_user_ids = get_blocked_user_ids(request.user)
        Notification.objects.filter(recipient=request.user, is_read=False).exclude(actor_id__in=blocked_user_ids).update(
            is_read=True,
            read_at=timezone.now(),
        )
        return Response({"detail": "All notifications marked as read."}, status=status.HTTP_200_OK)

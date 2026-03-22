from django.contrib.auth import get_user_model
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied

from .models import Block, Report
from .serializers import BlockSerializer, ReportSerializer


User = get_user_model()


class ReportCreateAPIView(generics.CreateAPIView):
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)


class BlockListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = BlockSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Block.objects.select_related("user", "blocked_user").filter(user=self.request.user)

    def perform_create(self, serializer):
        blocked_user = User.objects.get(pk=self.request.data["blocked_user"])
        if blocked_user.id == self.request.user.id:
            raise PermissionDenied("You cannot block yourself.")
        serializer.save(user=self.request.user, blocked_user=blocked_user)

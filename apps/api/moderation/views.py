from django.contrib.auth import get_user_model
from django.db.models import Count
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Block, ModerationActionLog, Report
from .serializers import (
    AdminReportReviewSerializer,
    AdminReportSerializer,
    BlockSerializer,
    ModerationActionLogSerializer,
    ReportSerializer,
)


User = get_user_model()


class IsAdminRole(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_staff or getattr(user, "role", "") == "admin"))


class ReportCreateAPIView(generics.CreateAPIView):
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)


class AdminReportStatsAPIView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        counts = {
            row["status"]: row["total"]
            for row in Report.objects.values("status").annotate(total=Count("id"))
        }
        data = {
            "all": Report.objects.count(),
            "open": counts.get(Report.Status.OPEN, 0),
            "reviewing": counts.get(Report.Status.REVIEWING, 0),
            "resolved": counts.get(Report.Status.RESOLVED, 0),
            "rejected": counts.get(Report.Status.REJECTED, 0),
        }
        return Response(data)


class AdminReportListAPIView(generics.ListAPIView):
    serializer_class = AdminReportSerializer
    permission_classes = [IsAdminRole]

    def get_queryset(self):
        queryset = Report.objects.select_related("reporter").all()
        status_value = self.request.query_params.get("status")
        if status_value:
            queryset = queryset.filter(status=status_value)
        target_type = self.request.query_params.get("target_type")
        if target_type:
            queryset = queryset.filter(target_type=target_type)
        return queryset


class AdminReportDetailAPIView(generics.RetrieveUpdateAPIView):
    queryset = Report.objects.select_related("reporter").all()
    permission_classes = [IsAdminRole]

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return AdminReportSerializer
        return AdminReportReviewSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class AdminModerationActionLogListAPIView(generics.ListAPIView):
    serializer_class = ModerationActionLogSerializer
    permission_classes = [IsAdminRole]

    def get_queryset(self):
        return ModerationActionLog.objects.select_related("actor", "report").all()[:30]


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


class BlockDeleteAPIView(generics.DestroyAPIView):
    serializer_class = BlockSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Block.objects.select_related("user", "blocked_user").filter(user=self.request.user)

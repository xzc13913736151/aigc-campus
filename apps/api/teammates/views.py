from django.db.models import Q
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError

from notifications.models import Notification
from notifications.services import create_notification

from .models import TeamApplication, TeamPost
from .serializers import (
    TeamApplicationCreateSerializer,
    TeamApplicationReviewSerializer,
    TeamApplicationSerializer,
    TeamPostSerializer,
)


class TeamPostListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = TeamPostSerializer
    queryset = TeamPost.objects.select_related("author")

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        queryset = self.queryset.all()
        query = self.request.query_params.get("q")
        tag = self.request.query_params.get("tag")
        status_filter = self.request.query_params.get("status")

        if query:
            queryset = queryset.filter(Q(title__icontains=query) | Q(summary__icontains=query) | Q(details__icontains=query))
        if tag:
            queryset = queryset.filter(Q(title__icontains=tag) | Q(summary__icontains=tag) | Q(details__icontains=tag))
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class IsTeamPostAuthor(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.author_id == request.user.id


class TeamPostDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TeamPostSerializer
    queryset = TeamPost.objects.select_related("author")

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsTeamPostAuthor()]


class MyTeamPostsAPIView(generics.ListAPIView):
    serializer_class = TeamPostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TeamPost.objects.select_related("author").filter(author=self.request.user)


class TeamApplicationCreateAPIView(generics.CreateAPIView):
    serializer_class = TeamApplicationCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        post = get_object_or_404(TeamPost, pk=self.kwargs["post_id"])
        if post.author_id == self.request.user.id:
            raise PermissionDenied("You cannot apply to your own post.")
        if post.status != TeamPost.Status.OPEN or post.current_size >= post.target_size:
            raise PermissionDenied("This team post is not accepting applications.")
        try:
            serializer.instance = TeamApplication.objects.create(post=post, applicant=self.request.user, **serializer.validated_data)
        except IntegrityError as exc:
            raise ValidationError({"detail": "You have already applied to this team post."}) from exc
        create_notification(
            recipient=post.author,
            actor=self.request.user,
            type=Notification.Type.TEAM_APPLICATION_CREATED,
            title="你的组队收到新申请",
            body=f"{self.request.user.nickname or self.request.user.email} 申请加入《{post.title}》。",
            target_type="team_post",
            target_id=str(post.id),
            extra={"post_id": str(post.id), "application_id": str(serializer.instance.id)},
        )


class MyApplicationsAPIView(generics.ListAPIView):
    serializer_class = TeamApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TeamApplication.objects.select_related("post", "applicant", "post__author").filter(applicant=self.request.user)


class ReceivedApplicationsAPIView(generics.ListAPIView):
    serializer_class = TeamApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TeamApplication.objects.select_related("post", "applicant", "post__author").filter(post__author=self.request.user)


class TeamApplicationReviewAPIView(generics.UpdateAPIView):
    serializer_class = TeamApplicationReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = TeamApplication.objects.select_related("post", "applicant", "post__author")

    def perform_update(self, serializer):
        application = self.get_object()
        if application.post.author_id != self.request.user.id:
            raise PermissionDenied("You can only manage applications for your own post.")
        if application.status != TeamApplication.Status.PENDING:
            raise PermissionDenied("This application has already been reviewed.")

        updated_application = serializer.save()
        post = updated_application.post
        if updated_application.status == TeamApplication.Status.ACCEPTED:
            post.current_size = min(post.current_size + 1, post.target_size)
            if post.current_size >= post.target_size:
                post.status = TeamPost.Status.FILLED
            post.save(update_fields=["current_size", "status", "updated_at"])

        notification_type = (
            Notification.Type.TEAM_APPLICATION_ACCEPTED
            if updated_application.status == TeamApplication.Status.ACCEPTED
            else Notification.Type.TEAM_APPLICATION_REJECTED
        )
        notification_title = "你的组队申请已通过" if updated_application.status == TeamApplication.Status.ACCEPTED else "你的组队申请被拒绝"
        notification_body = (
            f"你申请加入《{post.title}》的请求已通过。"
            if updated_application.status == TeamApplication.Status.ACCEPTED
            else f"你申请加入《{post.title}》的请求被拒绝。"
        )
        create_notification(
            recipient=updated_application.applicant,
            actor=self.request.user,
            type=notification_type,
            title=notification_title,
            body=notification_body,
            target_type="team_post",
            target_id=str(post.id),
            extra={"post_id": str(post.id), "application_id": str(updated_application.id)},
        )
